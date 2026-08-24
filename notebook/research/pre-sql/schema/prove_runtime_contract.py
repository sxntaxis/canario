#!/usr/bin/env python3
"""Certify the SQLite runtime contract for the candidate schema.

Research-only. Run this under the exact SQLite library intended for ActaKit.
A version number alone is intentionally insufficient: source ID, compile options,
and functional probes are all checked.
"""
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

TARGET_VERSION = (3, 53, 4)
CERTIFIED_SOURCE_IDS = {
    (3, 53, 4): "2026-07-24 19:02:57 bf7c7f30031888f4e796e429ab3978879485813aaca6f641c7b33e4e09459bcc",
}


def fail(message: str) -> None:
    raise SystemExit(f"RUNTIME_CONTRACT=FAIL {message}")


def main() -> None:
    version = tuple(int(x) for x in sqlite3.sqlite_version.split(".")[:3])
    source_id = sqlite3.connect(":memory:").execute("select sqlite_source_id()").fetchone()[0]
    if version < TARGET_VERSION:
        fail(f"sqlite={sqlite3.sqlite_version} below 3.53.4")
    expected_source = CERTIFIED_SOURCE_IDS.get(version)
    if expected_source is None:
        fail(f"sqlite={sqlite3.sqlite_version} is not yet in certified runtime registry")
    if source_id != expected_source:
        fail(f"source_id mismatch for sqlite={sqlite3.sqlite_version}: {source_id!r}")

    probe = sqlite3.connect(":memory:")
    options = {row[0] for row in probe.execute("pragma compile_options")}
    probe.close()
    if "ENABLE_FTS5" not in options:
        fail("ENABLE_FTS5 missing")
    thread_opts = [x for x in options if x.startswith("THREADSAFE=")]
    if not thread_opts or thread_opts[0] == "THREADSAFE=0":
        fail(f"unsafe thread configuration: {thread_opts or ['missing THREADSAFE']}")
    forbidden = {"OMIT_WAL", "OMIT_FOREIGN_KEY", "OMIT_TRIGGER"}
    present_forbidden = sorted(forbidden & options)
    if present_forbidden:
        fail(f"forbidden compile options present: {present_forbidden}")

    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "runtime-contract.db"
        con = sqlite3.connect(db)
        # Required connection invariants must be settable and observable.
        con.execute("pragma foreign_keys=on")
        if con.execute("pragma foreign_keys").fetchone()[0] != 1:
            fail("foreign_keys could not be enabled")
        if con.execute("pragma journal_mode=wal").fetchone()[0].lower() != "wal":
            fail("WAL mode unavailable")
        con.execute("pragma synchronous=full")
        if con.execute("pragma synchronous").fetchone()[0] != 2:
            fail("synchronous=FULL unavailable")
        con.execute("pragma trusted_schema=off")
        if con.execute("pragma trusted_schema").fetchone()[0] != 0:
            fail("trusted_schema=OFF unavailable")
        con.execute("pragma secure_delete=on")
        if con.execute("pragma secure_delete").fetchone()[0] != 1:
            fail("secure_delete=ON unavailable")

        # Functional foreign-key enforcement, not merely parser support.
        con.executescript("""
          create table parent(id text primary key) strict;
          create table child(id text primary key, parent_id text not null references parent(id)) strict;
        """)
        try:
            con.execute("insert into child values('c','missing')")
        except sqlite3.IntegrityError:
            pass
        else:
            fail("foreign key syntax present but enforcement failed")

        # STRICT must reject a lossy type mismatch.
        con.execute("create table strict_probe(v integer not null) strict")
        try:
            con.execute("insert into strict_probe values('not-an-integer')")
        except sqlite3.IntegrityError:
            pass
        else:
            fail("STRICT type enforcement failed")

        # FTS5 and its persistent secure-delete setting are required by purge policy.
        con.execute("create virtual table fts_probe using fts5(body)")
        con.execute("insert into fts_probe(fts_probe, rank) values('secure-delete', 1)")
        value = con.execute("select v from fts_probe_config where k='secure-delete'").fetchone()
        if value != (1,):
            fail(f"FTS5 secure-delete unavailable: {value!r}")
        con.close()

    print(f"RUNTIME_CONTRACT=PASS sqlite={sqlite3.sqlite_version}")
    print(f"sqlite_source_id={source_id}")
    print("compile_contract=PASS ENABLE_FTS5 THREADSAFE!=0 no_OMIT_WAL/FOREIGN_KEY/TRIGGER")
    print("functional_contract=PASS STRICT FTS5 WAL FK FULL trusted_schema secure_delete")


if __name__ == "__main__":
    main()
