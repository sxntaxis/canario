"""Open and bootstrap the canonical ActaKit SQLite database."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from typing import Callable
from urllib.parse import quote

from .runtime import verify_runtime_contract

APPLICATION_ID = 0x414B4954  # ASCII "AKIT"
SCHEMA_VERSION = 1
MIGRATION_0001_SHA256 = "cc8bbdb22a62349494004de642ec21b4ef2f9d30f22d33f1cf5cba08ed28e7a3"
_MIGRATION_0001 = Path(__file__).with_name("migrations") / "0001.sql"

RuntimeGuard = Callable[[], None]


class DatabaseIdentityError(RuntimeError):
    """A SQLite file is not a valid authority for the requested ActaKit schema."""


def _load_migration_0001() -> str:
    payload = _MIGRATION_0001.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != MIGRATION_0001_SHA256:
        raise DatabaseIdentityError(
            "migration 0001 bytes do not match the authorized frozen specification: "
            f"{digest}"
        )
    return payload.decode("utf-8")


def _configure_writable_connection(con: sqlite3.Connection) -> sqlite3.Connection:
    con.execute("PRAGMA foreign_keys=ON")
    if con.execute("PRAGMA journal_mode=WAL").fetchone()[0].lower() != "wal":
        raise DatabaseIdentityError("SQLite WAL mode could not be established")
    con.execute("PRAGMA synchronous=FULL")
    con.execute("PRAGMA trusted_schema=OFF")
    con.execute("PRAGMA secure_delete=ON")
    con.execute("PRAGMA busy_timeout=5000")

    expected = {
        "foreign_keys": 1,
        "synchronous": 2,
        "trusted_schema": 0,
        "secure_delete": 1,
        "busy_timeout": 5000,
    }
    for pragma, value in expected.items():
        actual = con.execute(f"PRAGMA {pragma}").fetchone()[0]
        if actual != value:
            raise DatabaseIdentityError(
                f"SQLite connection contract failed: {pragma}={actual!r}, expected {value!r}"
            )
    return con


def _user_schema_objects(con: sqlite3.Connection) -> list[tuple[str, str]]:
    return con.execute(
        """
        SELECT type, name
        FROM sqlite_schema
        WHERE name NOT LIKE 'sqlite_%'
        ORDER BY type, name
        """
    ).fetchall()


def _identity(con: sqlite3.Connection) -> tuple[int, int]:
    return (
        con.execute("PRAGMA application_id").fetchone()[0],
        con.execute("PRAGMA user_version").fetchone()[0],
    )


def _assert_fresh_target(con: sqlite3.Connection) -> None:
    application_id, user_version = _identity(con)
    objects = _user_schema_objects(con)
    if application_id != 0 or user_version != 0 or objects:
        raise DatabaseIdentityError(
            "migration 0001 requires a truly fresh SQLite target; "
            f"application_id={application_id}, user_version={user_version}, "
            f"user_objects={len(objects)}"
        )


def _assert_schema_v1(con: sqlite3.Connection, *, full_integrity: bool) -> None:
    application_id, user_version = _identity(con)
    if application_id != APPLICATION_ID or user_version != SCHEMA_VERSION:
        raise DatabaseIdentityError(
            "not an ActaKit schema-v1 authority: "
            f"application_id={application_id}, user_version={user_version}"
        )

    strict_tables = con.execute(
        "SELECT count(*) FROM pragma_table_list WHERE strict=1"
    ).fetchone()[0]
    if strict_tables != 58:
        raise DatabaseIdentityError(
            f"ActaKit schema-v1 inventory mismatch: strict_tables={strict_tables}"
        )

    fts_tables = con.execute(
        """
        SELECT count(*)
        FROM pragma_table_list
        WHERE type='virtual'
          AND name IN ('claim_fts','representation_fts','document_fts')
        """
    ).fetchone()[0]
    if fts_tables != 3:
        raise DatabaseIdentityError(
            f"ActaKit schema-v1 inventory mismatch: fts_tables={fts_tables}"
        )

    for table in ("claim_fts", "representation_fts", "document_fts"):
        row = con.execute(
            f"SELECT v FROM {table}_config WHERE k='secure-delete'"
        ).fetchone()
        if row != (1,):
            raise DatabaseIdentityError(
                f"ActaKit FTS secure-delete contract failed for {table}: {row!r}"
            )

    if full_integrity:
        fk_errors = con.execute("PRAGMA foreign_key_check").fetchall()
        if fk_errors:
            raise DatabaseIdentityError(
                f"ActaKit foreign-key integrity check failed: {fk_errors[:3]!r}"
            )
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise DatabaseIdentityError(
                f"ActaKit SQLite integrity check failed: {integrity!r}"
            )


def _apply_migration_0001(con: sqlite3.Connection, sql: str) -> None:
    try:
        con.executescript("BEGIN IMMEDIATE;\n" + sql + "\nCOMMIT;\n")
    except Exception:
        if con.in_transaction:
            con.rollback()
        raise


def _ensure_schema_v1(path: Path, runtime_guard: RuntimeGuard) -> None:
    runtime_guard()
    con = _configure_writable_connection(sqlite3.connect(path))
    try:
        application_id, user_version = _identity(con)
        if application_id == APPLICATION_ID and user_version == SCHEMA_VERSION:
            _assert_schema_v1(con, full_integrity=True)
            return

        _assert_fresh_target(con)
        _apply_migration_0001(con, _load_migration_0001())
        _assert_schema_v1(con, full_integrity=True)
    finally:
        con.close()

    # Reopen through a new authority connection. This catches connection-state
    # assumptions that a one-connection bootstrap could hide.
    reopened = _configure_writable_connection(sqlite3.connect(path))
    try:
        _assert_schema_v1(reopened, full_integrity=True)
    finally:
        reopened.close()


def ensure_schema_v1(path: str | Path) -> None:
    """Create or verify the schema-v1 authority at *path*.

    Unknown, partial, foreign, older, or newer schemas fail closed. `0001` is
    replayed only against a truly fresh database.
    """

    _ensure_schema_v1(Path(path), verify_runtime_contract)


def _open_writable_v1(path: Path, runtime_guard: RuntimeGuard) -> sqlite3.Connection:
    runtime_guard()
    con = _configure_writable_connection(
        sqlite3.connect(_database_uri(path, "rw"), uri=True)
    )
    try:
        _assert_schema_v1(con, full_integrity=False)
    except Exception:
        con.close()
        raise
    return con


def open_writable_v1(path: str | Path) -> sqlite3.Connection:
    """Open an existing ActaKit schema-v1 authority for canonical writes."""

    return _open_writable_v1(Path(path), verify_runtime_contract)


def _database_uri(path: Path, mode: str) -> str:
    # URI quoting keeps '?'/'#'/spaces in ordinary POSIX paths from changing
    # SQLite URI semantics. `mode=rw`/`mode=ro` also prevents ordinary openers
    # from creating a new empty authority after a path typo.
    return "file:" + quote(str(path.resolve()), safe="/") + f"?mode={mode}"


def _open_readonly_v1(path: Path, runtime_guard: RuntimeGuard) -> sqlite3.Connection:
    runtime_guard()
    con = sqlite3.connect(_database_uri(path, "ro"), uri=True)
    try:
        con.execute("PRAGMA query_only=ON")
        con.execute("PRAGMA trusted_schema=OFF")
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("PRAGMA busy_timeout=5000")
        if con.execute("PRAGMA query_only").fetchone()[0] != 1:
            raise DatabaseIdentityError("read-only query_only contract failed")
        if con.execute("PRAGMA trusted_schema").fetchone()[0] != 0:
            raise DatabaseIdentityError("read-only trusted_schema contract failed")
        if con.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
            raise DatabaseIdentityError("read-only foreign_keys contract failed")
        _assert_schema_v1(con, full_integrity=False)
    except Exception:
        con.close()
        raise
    return con


def open_readonly_v1(path: str | Path) -> sqlite3.Connection:
    """Open an existing schema-v1 authority without write capability."""

    return _open_readonly_v1(Path(path), verify_runtime_contract)
