from __future__ import annotations

import hashlib
import sqlite3
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from actakit.persistence import database
from actakit.persistence.runtime import RuntimeContractError


NO_RUNTIME_CHECK = lambda: None


class PersistenceBootstrapTests(unittest.TestCase):
    def test_production_migration_is_exact_frozen_spec(self):
        repo = Path(__file__).resolve().parents[1]
        frozen = repo / "notebook/research/pre-sql/schema/MIGRATION_0001_SPEC.sql"
        production = repo / "actakit/persistence/migrations/0001.sql"
        frozen_bytes = frozen.read_bytes()
        production_bytes = production.read_bytes()

        self.assertEqual(production_bytes, frozen_bytes)
        self.assertEqual(
            hashlib.sha256(production_bytes).hexdigest(),
            database.MIGRATION_0001_SHA256,
        )

    def test_public_bootstrap_checks_runtime_before_creating_file(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "must-not-exist.sqlite3"
            with mock.patch(
                "actakit.persistence.database.verify_runtime_contract",
                side_effect=RuntimeContractError("uncertified runtime"),
            ):
                with self.assertRaises(RuntimeContractError):
                    database.ensure_schema_v1(path)
            self.assertFalse(path.exists())

    def test_tampered_migration_bytes_fail_before_execution(self):
        with tempfile.TemporaryDirectory() as td:
            tampered = Path(td) / "0001.sql"
            tampered.write_bytes(b"select 1; -- not the frozen migration\n")
            with mock.patch.object(database, "_MIGRATION_0001", tampered):
                with self.assertRaises(database.DatabaseIdentityError):
                    database._load_migration_0001()

    def test_fresh_bootstrap_reopen_and_repeat_are_safe(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "actakit.sqlite3"
            database._ensure_schema_v1(path, NO_RUNTIME_CHECK)

            con = database._open_writable_v1(path, NO_RUNTIME_CHECK)
            try:
                self.assertEqual(
                    database._identity(con),
                    (database.APPLICATION_ID, database.SCHEMA_VERSION),
                )
                first_schema = database._user_schema_objects(con)
            finally:
                con.close()

            # Existing valid v1 is verified, never replayed.
            database._ensure_schema_v1(path, NO_RUNTIME_CHECK)
            con = database._open_writable_v1(path, NO_RUNTIME_CHECK)
            try:
                self.assertEqual(database._user_schema_objects(con), first_schema)
            finally:
                con.close()

    def test_unknown_partial_and_future_databases_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            unknown = root / "unknown.sqlite3"
            con = sqlite3.connect(unknown)
            con.execute("CREATE TABLE foreign_table(id INTEGER PRIMARY KEY)")
            con.commit()
            con.close()
            with self.assertRaises(database.DatabaseIdentityError):
                database._ensure_schema_v1(unknown, NO_RUNTIME_CHECK)

            partial = root / "partial.sqlite3"
            con = sqlite3.connect(partial)
            con.execute(f"PRAGMA application_id={database.APPLICATION_ID}")
            con.close()
            with self.assertRaises(database.DatabaseIdentityError):
                database._ensure_schema_v1(partial, NO_RUNTIME_CHECK)

            future = root / "future.sqlite3"
            con = sqlite3.connect(future)
            con.execute(f"PRAGMA application_id={database.APPLICATION_ID}")
            con.execute("PRAGMA user_version=2")
            con.close()
            with self.assertRaises(database.DatabaseIdentityError):
                database._ensure_schema_v1(future, NO_RUNTIME_CHECK)

    def test_failure_after_identity_markers_rolls_back_schema_and_markers(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "rollback.sqlite3"
            con = database._configure_writable_connection(sqlite3.connect(path))
            try:
                database._assert_fresh_target(con)
                sql = database._load_migration_0001() + "\nSELECT * FROM definitely_missing_table;"
                with self.assertRaises(sqlite3.OperationalError):
                    database._apply_migration_0001(con, sql)

                self.assertEqual(database._identity(con), (0, 0))
                self.assertEqual(database._user_schema_objects(con), [])
                self.assertEqual(
                    con.execute("PRAGMA journal_mode").fetchone()[0].lower(),
                    "wal",
                )
            finally:
                con.close()

    def test_existing_openers_do_not_create_missing_database(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "missing.sqlite3"
            with self.assertRaises(sqlite3.OperationalError):
                database._open_writable_v1(path, NO_RUNTIME_CHECK)
            self.assertFalse(path.exists())
            with self.assertRaises(sqlite3.OperationalError):
                database._open_readonly_v1(path, NO_RUNTIME_CHECK)
            self.assertFalse(path.exists())

    def test_readonly_opener_rejects_writes(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "readonly.sqlite3"
            database._ensure_schema_v1(path, NO_RUNTIME_CHECK)
            con = database._open_readonly_v1(path, NO_RUNTIME_CHECK)
            try:
                self.assertEqual(con.execute("PRAGMA query_only").fetchone()[0], 1)
                self.assertEqual(
                    database._identity(con),
                    (database.APPLICATION_ID, database.SCHEMA_VERSION),
                )
                with self.assertRaises(sqlite3.OperationalError):
                    con.execute("CREATE TABLE unauthorized_write(id INTEGER)")
            finally:
                con.close()


if __name__ == "__main__":
    unittest.main()
