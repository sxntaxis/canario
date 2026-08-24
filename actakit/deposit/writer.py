"""Explicit canonical write operations for the Depósito custody boundary."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from actakit.persistence import open_writable_v1

from .archive import ArchiveIntegrityError, EvidenceArchive, StoredObject
from .models import (
    AcquisitionObservation,
    AcquisitionWrite,
    CapturedArtifact,
    SourceLocatorRegistration,
    SourceRegistration,
)

ConnectionFactory = Callable[[Path], sqlite3.Connection]


class DepositWriteError(RuntimeError):
    """A bounded Depósito write could not be committed honestly."""


class IdentityCollisionError(DepositWriteError):
    """A stable opaque ID already exists with a different immutable payload."""


class DepositInvariantError(DepositWriteError):
    """Cross-row custody requirements are not satisfied."""


@dataclass(frozen=True, slots=True)
class ArtifactReceipt:
    artifact_id: str
    archive_object_id: str
    representation_id: str
    content_sha256: str
    byte_size: int
    storage_key: str


@dataclass(frozen=True, slots=True)
class AcquisitionReceipt:
    acquisition_id: str
    artifacts: tuple[ArtifactReceipt, ...]
    replayed: bool


class DepositWriter:
    """Sole core writer for Source/Acquisition/Artifact original custody."""

    def __init__(
        self,
        database_path: str | Path,
        archive_root: str | Path,
        *,
        connection_factory: ConnectionFactory = open_writable_v1,
    ) -> None:
        self.database_path = Path(database_path)
        self.archive = EvidenceArchive(archive_root)
        self._connect = connection_factory

    def register_source(self, source: SourceRegistration) -> str:
        con = self._connect(self.database_path)
        try:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute(
                "SELECT kind,name,active,created_at FROM sources WHERE id=?",
                (source.id,),
            ).fetchone()
            expected = (source.kind, source.name, int(source.active), source.created_at)
            if row is None:
                con.execute(
                    "INSERT INTO sources(id,kind,name,active,created_at) VALUES (?,?,?,?,?)",
                    (source.id, *expected),
                )
            elif row != expected:
                raise IdentityCollisionError(
                    f"Source {source.id} already exists with different immutable payload"
                )
            con.commit()
            return source.id
        except Exception:
            if con.in_transaction:
                con.rollback()
            raise
        finally:
            con.close()

    def register_source_locator(self, locator: SourceLocatorRegistration) -> str:
        con = self._connect(self.database_path)
        try:
            con.execute("BEGIN IMMEDIATE")
            self._require_source(con, locator.source_id)

            by_id = con.execute(
                "SELECT source_id,locator,locator_kind,created_at FROM source_locators WHERE id=?",
                (locator.id,),
            ).fetchone()
            expected = (
                locator.source_id,
                locator.locator,
                locator.locator_kind,
                locator.created_at,
            )
            if by_id is not None:
                if by_id != expected:
                    raise IdentityCollisionError(
                        f"SourceLocator {locator.id} already exists with different immutable payload"
                    )
                con.commit()
                return locator.id

            existing = con.execute(
                "SELECT id,locator_kind FROM source_locators WHERE source_id=? AND locator=?",
                (locator.source_id, locator.locator),
            ).fetchone()
            if existing is not None:
                existing_id, existing_kind = existing
                if existing_kind != locator.locator_kind:
                    raise DepositInvariantError(
                        "the same Source locator cannot be re-registered with a conflicting locator kind"
                    )
                con.commit()
                return existing_id

            con.execute(
                "INSERT INTO source_locators(id,source_id,locator,locator_kind,created_at) VALUES (?,?,?,?,?)",
                (
                    locator.id,
                    locator.source_id,
                    locator.locator,
                    locator.locator_kind,
                    locator.created_at,
                ),
            )
            con.commit()
            return locator.id
        except Exception:
            if con.in_transaction:
                con.rollback()
            raise
        finally:
            con.close()

    def record_acquisition(self, operation: AcquisitionWrite) -> AcquisitionReceipt:
        con = self._connect(self.database_path)
        materialized: dict[str, StoredObject] = {}
        committed = False
        try:
            self._require_source(con, operation.observation.source_id)
            self._require_locator(con, operation.observation)

            replay = self._verify_existing_acquisition(con, operation)
            if replay is not None:
                return replay

            self._preflight_new_ids(con, operation)
            digest_by_artifact = {
                payload.artifact_id: self.archive.digest(payload.data)
                for payload in operation.artifacts
            }
            first_payload_by_digest: dict[str, CapturedArtifact] = {}
            for payload in operation.artifacts:
                first_payload_by_digest.setdefault(
                    digest_by_artifact[payload.artifact_id], payload
                )

            archive_ids: dict[str, str] = {}
            candidate_ids: dict[str, str] = {}

            for digest, payload in first_payload_by_digest.items():
                size = len(payload.data)

                row = con.execute(
                    """
                    SELECT id,byte_size,storage_key
                    FROM archive_objects
                    WHERE content_sha256=? AND availability='available'
                    """,
                    (digest,),
                ).fetchone()
                if row is not None:
                    object_id, stored_size, storage_key = row
                    if stored_size != size:
                        raise ArchiveIntegrityError(
                            f"ArchiveObject {object_id} size disagrees with SHA-256 identity"
                        )
                    self.archive.verify(storage_key, digest, size)
                    archive_ids[digest] = object_id
                    continue

                candidate_id = payload.archive_object_id
                collision = con.execute(
                    "SELECT 1 FROM archive_objects WHERE id=?",
                    (candidate_id,),
                ).fetchone()
                if collision is not None:
                    raise IdentityCollisionError(
                        f"candidate ArchiveObject ID {candidate_id} is already occupied"
                    )

                stored = self.archive.materialize(payload.data)
                materialized[digest] = stored
                candidate_ids[digest] = candidate_id
                archive_ids[digest] = candidate_id

            con.execute("BEGIN IMMEDIATE")
            self._require_source(con, operation.observation.source_id)
            self._require_locator(con, operation.observation)
            if con.execute(
                "SELECT 1 FROM acquisitions WHERE id=?", (operation.observation.id,)
            ).fetchone():
                raise IdentityCollisionError(
                    f"Acquisition {operation.observation.id} appeared concurrently"
                )
            self._preflight_new_ids(con, operation)

            # Re-check content identity under the write lock. A future multi-client
            # transport may race before BEGIN; the one canonical writer still
            # resolves physical deduplication deterministically here.
            for digest, payload in first_payload_by_digest.items():
                size = len(payload.data)
                row = con.execute(
                    """
                    SELECT id,byte_size,storage_key
                    FROM archive_objects
                    WHERE content_sha256=? AND availability='available'
                    """,
                    (digest,),
                ).fetchone()
                if row is not None:
                    object_id, stored_size, storage_key = row
                    if stored_size != size:
                        raise ArchiveIntegrityError(
                            f"ArchiveObject {object_id} size disagrees with SHA-256 identity"
                        )
                    self.archive.verify(storage_key, digest, size)
                    archive_ids[digest] = object_id
                    continue

                stored = materialized[digest]
                object_id = candidate_ids[digest]
                con.execute(
                    """
                    INSERT INTO archive_objects(
                      id,content_sha256,byte_size,storage_key,availability,created_at,purged_at
                    ) VALUES (?,?,?,?, 'available', ?, NULL)
                    """,
                    (object_id, digest, stored.byte_size, stored.storage_key, operation.observation.created_at),
                )
                archive_ids[digest] = object_id

            self._insert_acquisition(con, operation.observation)
            receipts: list[ArtifactReceipt] = []
            for payload in operation.artifacts:
                digest = digest_by_artifact[payload.artifact_id]
                object_id = archive_ids[digest]
                con.execute(
                    """
                    INSERT INTO artifacts(
                      id,archive_object_id,media_type,validation_state,availability,created_at,purged_at
                    ) VALUES (?,?,?,?,?,?,NULL)
                    """,
                    (
                        payload.artifact_id,
                        object_id,
                        payload.media_type,
                        payload.validation_state,
                        payload.availability,
                        payload.created_at,
                    ),
                )
                con.execute(
                    """
                    INSERT INTO acquisition_artifacts(
                      artifact_id,acquisition_id,role,observed_filename,observed_url
                    ) VALUES (?,?,?,?,?)
                    """,
                    (
                        payload.artifact_id,
                        operation.observation.id,
                        payload.role,
                        payload.observed_filename,
                        payload.observed_url,
                    ),
                )
                con.execute(
                    """
                    INSERT INTO representations(
                      id,artifact_id,archive_object_id,parent_representation_id,kind,
                      media_type,language,charset,process_run_id,availability,created_at,purged_at
                    ) VALUES (?,?,NULL,NULL,'original',?,?,?,NULL,?,?,NULL)
                    """,
                    (
                        payload.representation_id,
                        payload.artifact_id,
                        payload.media_type,
                        payload.language,
                        payload.charset,
                        payload.availability,
                        payload.created_at,
                    ),
                )
                stored = self._archive_row(con, object_id)
                receipts.append(
                    ArtifactReceipt(
                        payload.artifact_id,
                        object_id,
                        payload.representation_id,
                        stored[0],
                        stored[1],
                        stored[2],
                    )
                )

            self._validate_custody(con, operation.observation.id)
            con.commit()
            committed = True
            return AcquisitionReceipt(operation.observation.id, tuple(receipts), False)
        except sqlite3.IntegrityError as exc:
            if con.in_transaction:
                con.rollback()
            raise DepositWriteError(f"SQLite rejected Depósito write: {exc}") from exc
        except Exception:
            if con.in_transaction:
                con.rollback()
            raise
        finally:
            if not committed:
                self._cleanup_unreferenced_materialized(con, materialized)
            con.close()

    @staticmethod
    def _require_source(con: sqlite3.Connection, source_id: str) -> None:
        if con.execute("SELECT 1 FROM sources WHERE id=?", (source_id,)).fetchone() is None:
            raise DepositInvariantError(f"unknown Source: {source_id}")

    @staticmethod
    def _require_locator(con: sqlite3.Connection, observation: AcquisitionObservation) -> None:
        if observation.source_locator_id is None:
            return
        row = con.execute(
            "SELECT source_id FROM source_locators WHERE id=?",
            (observation.source_locator_id,),
        ).fetchone()
        if row is None:
            raise DepositInvariantError(
                f"unknown SourceLocator: {observation.source_locator_id}"
            )
        if row[0] != observation.source_id:
            raise DepositInvariantError(
                "Acquisition SourceLocator does not belong to the Acquisition Source"
            )

    @staticmethod
    def _insert_acquisition(con: sqlite3.Connection, observation: AcquisitionObservation) -> None:
        con.execute(
            """
            INSERT INTO acquisitions(
              id,source_id,source_locator_id,observed_at,outcome,http_status,
              adapter_key,adapter_version,error_code,created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?)
            """,
            (
                observation.id,
                observation.source_id,
                observation.source_locator_id,
                observation.observed_at,
                observation.outcome,
                observation.http_status,
                observation.adapter_key,
                observation.adapter_version,
                observation.error_code,
                observation.created_at,
            ),
        )

    @staticmethod
    def _preflight_new_ids(con: sqlite3.Connection, operation: AcquisitionWrite) -> None:
        for table, values in (
            ("artifacts", [item.artifact_id for item in operation.artifacts]),
            ("representations", [item.representation_id for item in operation.artifacts]),
        ):
            for value in values:
                if con.execute(f"SELECT 1 FROM {table} WHERE id=?", (value,)).fetchone():
                    raise IdentityCollisionError(
                        f"{table[:-1]} ID {value} is already occupied by another operation"
                    )

    def _verify_existing_acquisition(
        self, con: sqlite3.Connection, operation: AcquisitionWrite
    ) -> AcquisitionReceipt | None:
        row = con.execute(
            """
            SELECT source_id,source_locator_id,observed_at,outcome,http_status,
                   adapter_key,adapter_version,error_code,created_at
            FROM acquisitions WHERE id=?
            """,
            (operation.observation.id,),
        ).fetchone()
        if row is None:
            return None
        expected_observation = (
            operation.observation.source_id,
            operation.observation.source_locator_id,
            operation.observation.observed_at,
            operation.observation.outcome,
            operation.observation.http_status,
            operation.observation.adapter_key,
            operation.observation.adapter_version,
            operation.observation.error_code,
            operation.observation.created_at,
        )
        if row != expected_observation:
            raise IdentityCollisionError(
                f"Acquisition {operation.observation.id} exists with different immutable payload"
            )

        rows = con.execute(
            """
            SELECT a.id,a.archive_object_id,a.media_type,a.validation_state,a.availability,a.created_at,
                   aa.role,aa.observed_filename,aa.observed_url,
                   r.id,r.media_type,r.language,r.charset,r.availability,r.created_at,
                   o.content_sha256,o.byte_size,o.storage_key,o.availability
            FROM acquisition_artifacts aa
            JOIN artifacts a ON a.id=aa.artifact_id
            JOIN representations r ON r.artifact_id=a.id AND r.kind='original'
            JOIN archive_objects o ON o.id=a.archive_object_id
            WHERE aa.acquisition_id=?
            ORDER BY a.id
            """,
            (operation.observation.id,),
        ).fetchall()
        if len(rows) != len(operation.artifacts):
            raise IdentityCollisionError(
                f"Acquisition {operation.observation.id} retry has a different Artifact set"
            )
        by_artifact = {row[0]: row for row in rows}
        if set(by_artifact) != {item.artifact_id for item in operation.artifacts}:
            raise IdentityCollisionError(
                f"Acquisition {operation.observation.id} retry changed Artifact identities"
            )

        receipts: list[ArtifactReceipt] = []
        for payload in operation.artifacts:
            stored = by_artifact[payload.artifact_id]
            (
                artifact_id,
                archive_object_id,
                artifact_media_type,
                validation_state,
                artifact_availability,
                artifact_created_at,
                role,
                observed_filename,
                observed_url,
                representation_id,
                representation_media_type,
                language,
                charset,
                representation_availability,
                representation_created_at,
                content_sha256,
                byte_size,
                storage_key,
                archive_availability,
            ) = stored
            digest = self.archive.digest(payload.data)
            expected_key = self.archive.key_for_digest(digest)
            expected_payload = (
                payload.artifact_id,
                payload.media_type,
                payload.validation_state,
                payload.availability,
                payload.created_at,
                payload.role,
                payload.observed_filename,
                payload.observed_url,
                payload.representation_id,
                payload.media_type,
                payload.language,
                payload.charset,
                payload.availability,
                payload.created_at,
                digest,
                len(payload.data),
                expected_key,
                "available",
            )
            actual_payload = (
                artifact_id,
                artifact_media_type,
                validation_state,
                artifact_availability,
                artifact_created_at,
                role,
                observed_filename,
                observed_url,
                representation_id,
                representation_media_type,
                language,
                charset,
                representation_availability,
                representation_created_at,
                content_sha256,
                byte_size,
                storage_key,
                archive_availability,
            )
            if actual_payload != expected_payload:
                raise IdentityCollisionError(
                    f"Acquisition {operation.observation.id} retry changed payload for {payload.artifact_id}"
                )
            self.archive.verify(storage_key, content_sha256, byte_size)
            receipts.append(
                ArtifactReceipt(
                    payload.artifact_id,
                    archive_object_id,
                    payload.representation_id,
                    content_sha256,
                    byte_size,
                    storage_key,
                )
            )
        return AcquisitionReceipt(operation.observation.id, tuple(receipts), True)

    @staticmethod
    def _archive_row(con: sqlite3.Connection, object_id: str) -> tuple[str, int, str]:
        row = con.execute(
            """
            SELECT content_sha256,byte_size,storage_key
            FROM archive_objects WHERE id=? AND availability='available'
            """,
            (object_id,),
        ).fetchone()
        if row is None:
            raise DepositInvariantError(f"retained Artifact lacks available ArchiveObject {object_id}")
        return row

    @staticmethod
    def _validate_custody(con: sqlite3.Connection, acquisition_id: str) -> None:
        violations = con.execute(
            """
            SELECT a.id
            FROM acquisition_artifacts aa
            JOIN artifacts a ON a.id=aa.artifact_id
            LEFT JOIN archive_objects o ON o.id=a.archive_object_id
            WHERE aa.acquisition_id=?
              AND (
                a.availability NOT IN ('available','restricted')
                OR o.id IS NULL
                OR o.availability<>'available'
              )
            """,
            (acquisition_id,),
        ).fetchall()
        if violations:
            raise DepositInvariantError(
                f"retained Artifact/archive availability violation: {violations!r}"
            )

        originals = con.execute(
            """
            SELECT a.id,
                   sum(CASE WHEN r.kind='original' THEN 1 ELSE 0 END) AS original_count,
                   sum(CASE WHEN r.kind<>'original' THEN 1 ELSE 0 END) AS derivative_count
            FROM acquisition_artifacts aa
            JOIN artifacts a ON a.id=aa.artifact_id
            LEFT JOIN representations r ON r.artifact_id=a.id
            WHERE aa.acquisition_id=?
            GROUP BY a.id
            HAVING original_count<>1 OR derivative_count<>0
            """,
            (acquisition_id,),
        ).fetchall()
        if originals:
            raise DepositInvariantError(
                f"new custody Artifact must have exactly one original Representation: {originals!r}"
            )

    def _cleanup_unreferenced_materialized(
        self, con: sqlite3.Connection, materialized: dict[str, StoredObject]
    ) -> None:
        for digest, stored in materialized.items():
            if not stored.created:
                continue
            try:
                referenced = con.execute(
                    """
                    SELECT storage_key FROM archive_objects
                    WHERE content_sha256=? AND availability='available'
                    """,
                    (digest,),
                ).fetchone()
                if referenced is None or referenced[0] != stored.storage_key:
                    self.archive.remove_if_matches(stored)
            except Exception:
                # Compensation must never obscure the primary write failure. A
                # leftover content-addressed orphan is safer than deleting bytes
                # whose reference state cannot be proven here.
                pass
