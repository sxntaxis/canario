"""Atomic, content-addressed evidence byte storage for the Depósito."""

from __future__ import annotations

import hashlib
import os
import secrets
import stat
from dataclasses import dataclass
from pathlib import Path


class ArchiveIntegrityError(RuntimeError):
    """Physical archive bytes do not match their content-addressed identity."""


@dataclass(frozen=True, slots=True)
class StoredObject:
    content_sha256: str
    byte_size: int
    storage_key: str
    created: bool


class EvidenceArchive:
    """Local attached content-addressed storage.

    Final paths are derived only from SHA-256. Newly created files are written and
    fsynced under a temporary name, then atomically linked into the final key.
    """

    def __init__(self, root: str | Path) -> None:
        supplied = Path(root)
        supplied.mkdir(parents=True, exist_ok=True, mode=0o700)
        info = supplied.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise ArchiveIntegrityError("archive root must be a real directory, not a symlink")
        self.root = supplied.resolve()
        self._ensure_directory(self.root / "objects")

    @staticmethod
    def digest(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def key_for_digest(content_sha256: str) -> str:
        if (
            len(content_sha256) != 64
            or content_sha256 != content_sha256.lower()
            or any(ch not in "0123456789abcdef" for ch in content_sha256)
        ):
            raise ValueError("content digest must be 64 lowercase SHA-256 hex characters")
        return f"objects/{content_sha256[:2]}/{content_sha256}.bin"

    def path_for_key(self, storage_key: str) -> Path:
        parts = Path(storage_key).parts
        if len(parts) != 3 or parts[0] != "objects" or parts[1] in {".", ".."}:
            raise ArchiveIntegrityError(f"invalid archive storage key: {storage_key!r}")
        path = self.root.joinpath(*parts)
        if path.parent.parent != self.root / "objects":
            raise ArchiveIntegrityError(f"archive storage key escapes expected layout: {storage_key!r}")
        return path

    def inspect(self, content_sha256: str, byte_size: int) -> StoredObject | None:
        key = self.key_for_digest(content_sha256)
        path = self.path_for_key(key)
        if not path.exists() and not path.is_symlink():
            return None
        self._verify_file(path, content_sha256, byte_size)
        return StoredObject(content_sha256, byte_size, key, False)

    def materialize(self, data: bytes) -> StoredObject:
        content_sha256 = self.digest(data)
        byte_size = len(data)
        key = self.key_for_digest(content_sha256)
        final_path = self.path_for_key(key)
        bucket = final_path.parent
        self._ensure_directory(bucket)

        if final_path.exists() or final_path.is_symlink():
            self._verify_file(final_path, content_sha256, byte_size)
            return StoredObject(content_sha256, byte_size, key, False)

        tmp_path = bucket / f".{content_sha256}.{secrets.token_hex(8)}.tmp"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(tmp_path, flags, 0o600)
        try:
            view = memoryview(data)
            written = 0
            while written < len(view):
                count = os.write(fd, view[written:])
                if count <= 0:
                    raise ArchiveIntegrityError("archive write made no forward progress")
                written += count
            os.fsync(fd)
        finally:
            os.close(fd)

        created = False
        try:
            self._verify_file(tmp_path, content_sha256, byte_size)
            try:
                os.link(tmp_path, final_path, follow_symlinks=False)
                created = True
                self._fsync_directory(bucket)
            except FileExistsError:
                self._verify_file(final_path, content_sha256, byte_size)
        finally:
            try:
                tmp_path.unlink()
            except FileNotFoundError:
                pass
            self._fsync_directory(bucket)

        self._verify_file(final_path, content_sha256, byte_size)
        return StoredObject(content_sha256, byte_size, key, created)

    def remove_if_matches(self, stored: StoredObject) -> bool:
        path = self.path_for_key(stored.storage_key)
        if not path.exists() and not path.is_symlink():
            return False
        self._verify_file(path, stored.content_sha256, stored.byte_size)
        path.unlink()
        self._fsync_directory(path.parent)
        return True

    def verify(self, storage_key: str, content_sha256: str, byte_size: int) -> None:
        expected_key = self.key_for_digest(content_sha256)
        if storage_key != expected_key:
            raise ArchiveIntegrityError(
                f"archive key {storage_key!r} is not canonical for {content_sha256}"
            )
        self._verify_file(self.path_for_key(storage_key), content_sha256, byte_size)

    def _ensure_directory(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise ArchiveIntegrityError(f"archive path component is not a real directory: {path}")

    @staticmethod
    def _fsync_directory(path: Path) -> None:
        flags = os.O_RDONLY
        if hasattr(os, "O_DIRECTORY"):
            flags |= os.O_DIRECTORY
        fd = os.open(path, flags)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    @staticmethod
    def _verify_file(path: Path, expected_sha256: str, expected_size: int) -> None:
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(path, flags)
        except (FileNotFoundError, OSError) as exc:
            raise ArchiveIntegrityError(f"archive object is missing/unopenable: {path}") from exc
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode):
                raise ArchiveIntegrityError(f"archive object is not a regular file: {path}")
            if info.st_size != expected_size:
                raise ArchiveIntegrityError(
                    f"archive size mismatch for {path}: {info.st_size} != {expected_size}"
                )
            digest = hashlib.sha256()
            while True:
                chunk = os.read(fd, 1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
            actual = digest.hexdigest()
            if actual != expected_sha256:
                raise ArchiveIntegrityError(
                    f"archive digest mismatch for {path}: {actual} != {expected_sha256}"
                )
        finally:
            os.close(fd)
