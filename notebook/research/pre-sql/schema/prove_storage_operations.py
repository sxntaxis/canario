#!/usr/bin/env python3
"""Operational proof for archive/FTS/backup/purge boundaries of the SQLite candidate.

Research-only. This is deliberately not production migration or storage code.
It proves the candidate's operational shape on the available SQLite runtime, then
reports target-runtime certification separately.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import tempfile
from pathlib import Path

DDL = Path(__file__).with_name("SCRATCH_DDL.sql")
T = "2026-08-21T07:00:00.000Z"
APPLICATION_ID = 0x414B4954
SCHEMA_VERSION = 1
TARGET_SQLITE = (3, 53, 4)
SENTINEL = "purgesentinelzxqv987654"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def storage_key(data: bytes) -> str:
    h = digest(data)
    return f"objects/{h[:2]}/{h}.bin"


def write_object(root: Path, data: bytes) -> tuple[str, str]:
    key = storage_key(data)
    p = root / key
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return key, digest(data)


def configure_writable_connection(con: sqlite3.Connection) -> sqlite3.Connection:
    # Connection PRAGMAs are runtime state, not backup payload. Every writable
    # authority connection must establish them explicitly, including restore.
    con.execute("PRAGMA foreign_keys=ON")
    assert con.execute("PRAGMA journal_mode=WAL").fetchone()[0].lower() == "wal"
    con.execute("PRAGMA synchronous=FULL")
    con.execute("PRAGMA trusted_schema=OFF")
    con.execute("PRAGMA secure_delete=ON")
    con.execute("PRAGMA busy_timeout=5000")
    return con


def open_db(path: Path) -> sqlite3.Connection:
    return configure_writable_connection(sqlite3.connect(path))


def assert_db_identity(con: sqlite3.Connection) -> None:
    assert con.execute("PRAGMA application_id").fetchone()[0] == APPLICATION_ID
    assert con.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
    assert con.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert con.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
    assert con.execute("PRAGMA synchronous").fetchone()[0] == 2
    assert con.execute("PRAGMA trusted_schema").fetchone()[0] == 0
    assert con.execute("PRAGMA secure_delete").fetchone()[0] == 1
    assert con.execute("PRAGMA busy_timeout").fetchone()[0] == 5000


def referenced_archive_objects(con: sqlite3.Connection) -> list[tuple[str, str, str, int]]:
    return con.execute(
        """
        WITH refs(id) AS (
          SELECT archive_object_id FROM artifacts
          WHERE availability IN ('available','restricted') AND archive_object_id IS NOT NULL
          UNION
          SELECT archive_object_id FROM representations
          WHERE availability IN ('available','restricted') AND kind<>'original' AND archive_object_id IS NOT NULL
        )
        SELECT o.id,o.storage_key,o.content_sha256,o.byte_size
        FROM refs r JOIN archive_objects o ON o.id=r.id
        WHERE o.availability='available'
        ORDER BY o.id
        """
    ).fetchall()


def assert_archive_integrity(con: sqlite3.Connection, archive_root: Path) -> None:
    for oid, key, expected_hash, expected_size in referenced_archive_objects(con):
        p = archive_root / key
        data = p.read_bytes()
        assert len(data) == expected_size, (oid, len(data), expected_size)
        assert digest(data) == expected_hash, oid


def representation_text(con: sqlite3.Connection, archive_root: Path, rep_id: str) -> str:
    row = con.execute(
        """
        SELECT r.kind,r.media_type,
               CASE WHEN r.kind='original' THEN a.archive_object_id ELSE r.archive_object_id END
        FROM representations r
        JOIN artifacts a ON a.id=r.artifact_id
        WHERE r.id=? AND r.availability IN ('available','restricted')
        """,
        (rep_id,),
    ).fetchone()
    assert row is not None, rep_id
    kind, media_type, object_id = row
    assert media_type and (media_type.startswith("text/") or media_type in ("application/json", "text/csv")), (kind, media_type)
    o = con.execute(
        "SELECT storage_key,content_sha256,byte_size FROM archive_objects WHERE id=? AND availability='available'",
        (object_id,),
    ).fetchone()
    assert o is not None, object_id
    key, expected_hash, expected_size = o
    data = (archive_root / key).read_bytes()
    assert digest(data) == expected_hash and len(data) == expected_size
    return data.decode("utf-8")


def rebuild_fts(con: sqlite3.Connection, archive_root: Path) -> None:
    # FTS is disposable: canonical rows/archive bytes are the only rebuild inputs.
    for table in ("claim_fts", "representation_fts", "document_fts"):
        con.execute(f"DELETE FROM {table}")

    for rid, text in con.execute(
        """
        SELECT r.id,r.text
        FROM claim_revisions r
        WHERE r.lifecycle<>'restricted'
          AND NOT EXISTS (SELECT 1 FROM claim_revisions s WHERE s.supersedes_revision_id=r.id)
        ORDER BY r.id
        """
    ):
        con.execute("INSERT INTO claim_fts(claim_revision_id,text) VALUES (?,?)", (rid, text))

    for rid, title in con.execute(
        """
        SELECT r.id,r.title
        FROM civic_document_revisions r
        WHERE r.visibility='normal' AND r.title IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM civic_document_revisions s WHERE s.supersedes_document_revision_id=r.id)
        ORDER BY r.id
        """
    ):
        con.execute("INSERT INTO document_fts(document_revision_id,title) VALUES (?,?)", (rid, title))

    reps = con.execute(
        """
        SELECT id FROM representations
        WHERE availability='available'
          AND media_type IS NOT NULL
          AND (media_type LIKE 'text/%' OR media_type='application/json')
        ORDER BY id
        """
    ).fetchall()
    for (rep_id,) in reps:
        con.execute(
            "INSERT INTO representation_fts(representation_id,text) VALUES (?,?)",
            (rep_id, representation_text(con, archive_root, rep_id)),
        )

    for table in ("claim_fts", "representation_fts", "document_fts"):
        con.execute(f"INSERT INTO {table}({table}) VALUES('integrity-check')")


def assert_fts_coverage(con: sqlite3.Connection, archive_root: Path) -> None:
    expected_claims = {
        r[0]
        for r in con.execute(
            """
            SELECT r.id FROM claim_revisions r
            WHERE r.lifecycle<>'restricted'
              AND NOT EXISTS (SELECT 1 FROM claim_revisions s WHERE s.supersedes_revision_id=r.id)
            """
        )
    }
    actual_claims = {r[0] for r in con.execute("SELECT claim_revision_id FROM claim_fts")}
    assert actual_claims == expected_claims

    expected_docs = {
        r[0]
        for r in con.execute(
            """
            SELECT r.id FROM civic_document_revisions r
            WHERE r.visibility='normal' AND r.title IS NOT NULL
              AND NOT EXISTS (SELECT 1 FROM civic_document_revisions s WHERE s.supersedes_document_revision_id=r.id)
            """
        )
    }
    actual_docs = {r[0] for r in con.execute("SELECT document_revision_id FROM document_fts")}
    assert actual_docs == expected_docs

    expected_reps = {
        r[0]
        for r in con.execute(
            """
            SELECT id FROM representations
            WHERE availability='available' AND media_type IS NOT NULL
              AND (media_type LIKE 'text/%' OR media_type='application/json')
            """
        )
    }
    actual_reps = {r[0] for r in con.execute("SELECT representation_id FROM representation_fts")}
    assert actual_reps == expected_reps
    for rep_id in expected_reps:
        assert representation_text(con, archive_root, rep_id)


def populate(con: sqlite3.Connection, archive_root: Path) -> dict[str, str]:
    keep = b"Preserved civic evidence about the public water system."
    purge = f"Sensitive civic evidence {SENTINEL} scheduled for purge.".encode()
    with con:
        con.execute("PRAGMA wal_autocheckpoint=0")
        con.execute("INSERT INTO sources VALUES (?,?,?,?,?)", ("src-op", "manual", "Operational proof source", 1, T))
        con.execute("INSERT INTO source_locators VALUES (?,?,?,?,?,?,?)", ("loc-op", "src-op", "proof://local", "proof", None, None, T))
        con.execute("INSERT INTO acquisitions VALUES (?,?,?,?,?,?,?,?,?,?)", ("acq-op", "src-op", "loc-op", T, "success", None, "proof", "1", None, T))

        for label, data in (("keep", keep), ("purge", purge)):
            key, h = write_object(archive_root, data)
            oid, aid, rid, tid = f"aob-{label}", f"art-{label}", f"rep-{label}", f"target-{label}"
            con.execute("INSERT INTO archive_objects VALUES (?,?,?,?,?,?,?)", (oid, h, len(data), key, "available", T, None))
            con.execute("INSERT INTO artifacts VALUES (?,?,?,?,?,?,?)", (aid, oid, "text/plain", "verified", "available", T, None))
            con.execute("INSERT INTO acquisition_artifacts VALUES (?,?,?,?,?)", (aid, "acq-op", "attachment", f"{label}.txt", f"proof://{label}.txt"))
            con.execute("INSERT INTO representations VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (rid, aid, None, None, "original", "text/plain", "es", "utf-8", None, "available", T, None))
            text = data.decode()
            selector = json.dumps({"exact": text, "start_char": 0, "end_char": len(text)}, ensure_ascii=False, separators=(",", ":"))
            con.execute("INSERT INTO representation_targets VALUES (?,?,?,?,?,?,?,?,?)", (tid, rid, "text_quote", "v1", selector, None, "available", T, None))
            con.execute("INSERT INTO claims VALUES (?,?)", (f"clm-{label}", T))
            con.execute(
                """INSERT INTO claim_revisions(
                  id,claim_id,revision_no,supersedes_revision_id,claim_kind,text,origin_kind,
                  process_run_id,attribution_entity_id,attribution_text,temporal_start,temporal_end,
                  sensitive,quantitative,lifecycle,created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (f"clmr-{label}", f"clm-{label}", 1, None, "source_assertion", text, "human", None, None, None, None, None, int(label == "purge"), 0, "active", T),
            )
            con.execute("INSERT INTO evidence_links VALUES (?,?,?,?,?,?,?,?,?,?)", (f"ev-{label}", None, f"clmr-{label}", tid, "supports", "human", None, "active", None, T))

        con.execute("INSERT INTO civic_documents VALUES (?,?)", ("doc-keep", T))
        con.execute("INSERT INTO civic_document_revisions VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("docr-keep", "doc-keep", 1, None, "Water system evidence", None, "2026-08-21", "es", "normal", "human", None, T))
        con.execute("INSERT INTO document_representations VALUES (?,?,?,?,?,?,?,?,?,?,?)", ("docrep-keep", None, "doc-keep", "rep-keep", "whole", "target-keep", "human", None, "active", None, T))
        rebuild_fts(con, archive_root)

    assert_db_identity(con)
    assert_archive_integrity(con, archive_root)
    assert_fts_coverage(con, archive_root)
    assert con.execute("SELECT count(*) FROM claim_fts WHERE claim_fts MATCH ?", (SENTINEL,)).fetchone()[0] == 1
    assert con.execute("SELECT count(*) FROM representation_fts WHERE representation_fts MATCH ?", (SENTINEL,)).fetchone()[0] == 1
    return {"keep": keep.decode(), "purge": purge.decode()}


def make_backup(con: sqlite3.Connection, archive_root: Path, backup_root: Path) -> Path:
    backup_root.mkdir(parents=True, exist_ok=True)
    db_backup = backup_root / "actakit.sqlite3"
    dest = open_db(db_backup)
    con.backup(dest)
    dest.close()

    entries = []
    for oid, key, h, size in referenced_archive_objects(con):
        src = archive_root / key
        assert src.exists() and digest(src.read_bytes()) == h and src.stat().st_size == size
        dst = backup_root / "archive" / key
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        entries.append({"archive_object_id": oid, "storage_key": key, "sha256": h, "byte_size": size})
    manifest = {
        "format": "actakit-backup-proof-v1",
        "application_id": APPLICATION_ID,
        "user_version": SCHEMA_VERSION,
        "sqlite_runtime": sqlite3.sqlite_version,
        "archive_objects": entries,
        "fts_authoritative": False,
    }
    (backup_root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return db_backup


def restore_clean_machine(backup_root: Path, restore_root: Path) -> None:
    restore_root.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup_root / "actakit.sqlite3", restore_root / "actakit.sqlite3")
    shutil.copytree(backup_root / "archive", restore_root / "archive")
    manifest = json.loads((backup_root / "manifest.json").read_text())

    con = open_db(restore_root / "actakit.sqlite3")
    assert_db_identity(con)
    assert manifest["application_id"] == APPLICATION_ID and manifest["user_version"] == SCHEMA_VERSION
    assert con.execute("PRAGMA foreign_key_check").fetchall() == []
    assert_archive_integrity(con, restore_root / "archive")

    # Do not trust the backed-up projection. Recreate its content from canonical authority.
    with con:
        rebuild_fts(con, restore_root / "archive")
    assert_fts_coverage(con, restore_root / "archive")
    assert con.execute("SELECT count(*) FROM claim_fts WHERE claim_fts MATCH ?", (SENTINEL,)).fetchone()[0] == 1
    con.close()


def availability_violations(con: sqlite3.Connection) -> list[tuple[str, str]]:
    return con.execute(
        """
        SELECT 'artifact/archive', a.id
        FROM artifacts a JOIN archive_objects o ON o.id=a.archive_object_id
        WHERE a.availability IN ('available','restricted') AND o.availability<>'available'
        UNION ALL
        SELECT 'representation/artifact', r.id
        FROM representations r JOIN artifacts a ON a.id=r.artifact_id
        WHERE r.availability IN ('available','restricted') AND a.availability NOT IN ('available','restricted')
        UNION ALL
        SELECT 'representation/archive', r.id
        FROM representations r JOIN archive_objects o ON o.id=r.archive_object_id
        WHERE r.availability IN ('available','restricted') AND r.kind<>'original' AND o.availability<>'available'
        ORDER BY 1,2
        """
    ).fetchall()


def file_contains(path: Path, needle: bytes) -> bool:
    return path.exists() and needle in path.read_bytes()


def purge_live(con: sqlite3.Connection, db_path: Path, archive_root: Path, backup_root: Path) -> dict[str, object]:
    purge_file = archive_root / con.execute("SELECT storage_key FROM archive_objects WHERE id='aob-purge'").fetchone()[0]
    assert purge_file.exists()

    # Freeze exact content-bearing target/action scope before changing authority.
    targets = [
        ("acquisition_artifact", "art-purge", "scrub_payload"),
        ("representation_target", "target-purge", "scrub_payload"),
        ("evidence_link", "ev-purge", "delete_record"),
        ("claim_revision", "clmr-purge", "delete_record"),
        ("claim", "clm-purge", "delete_record"),
        ("representation", "rep-purge", "detach"),
        ("artifact", "art-purge", "detach"),
        ("archive_object", "aob-purge", "delete_bytes"),
    ]
    with con:
        con.execute("INSERT INTO purges VALUES (?,?,?,?,?,?,?,?)", ("purge-op", "proof", "operator", "minimal_tombstone", T, None, "planned", "backup-scope: pre-purge backup explicitly out of current-authority purge"))
        for kind, rid, action in targets:
            con.execute("INSERT INTO purge_targets VALUES (?,?,?,?,?,?,?)", ("purge-op", kind, rid, action, T, None, None))

    frozen = con.execute("SELECT record_kind,record_id,action FROM purge_targets WHERE purge_id='purge-op' ORDER BY record_kind,record_id,action").fetchall()
    assert frozen == sorted(targets)

    # Canonical/derived data removal in FK-safe order.
    with con:
        con.execute("DELETE FROM evidence_links WHERE id='ev-purge'")
        con.execute("DELETE FROM claim_fts WHERE claim_revision_id='clmr-purge'")
        con.execute("DELETE FROM representation_fts WHERE representation_id='rep-purge'")
        con.execute("DELETE FROM claim_revisions WHERE id='clmr-purge'")
        con.execute("DELETE FROM claims WHERE id='clm-purge'")
        con.execute("UPDATE acquisition_artifacts SET observed_filename=NULL,observed_url=NULL WHERE artifact_id='art-purge'")
        con.execute("UPDATE representation_targets SET selector_kind=NULL,selector_version=NULL,selector_payload_json=NULL,state_payload_json=NULL,availability='purged',purged_at=? WHERE id='target-purge'", (T,))
        con.execute("UPDATE representations SET artifact_id=NULL,archive_object_id=NULL,parent_representation_id=NULL,media_type=NULL,language=NULL,charset=NULL,process_run_id=NULL,availability='purged',purged_at=? WHERE id='rep-purge'", (T,))
        con.execute("UPDATE artifacts SET archive_object_id=NULL,media_type=NULL,availability='purged',purged_at=? WHERE id='art-purge'", (T,))
        con.execute("UPDATE archive_objects SET content_sha256=NULL,byte_size=NULL,storage_key=NULL,availability='purged',purged_at=? WHERE id='aob-purge'", (T,))
        con.execute("UPDATE purge_targets SET executed_at=?,outcome='completed' WHERE purge_id='purge-op'", (T,))
        con.execute("UPDATE purges SET executed_at=?,outcome='completed' WHERE id='purge-op'", (T,))
    purge_file.unlink()

    assert availability_violations(con) == []
    assert con.execute("PRAGMA foreign_key_check").fetchall() == []
    for table in ("claim_fts", "representation_fts", "document_fts"):
        con.execute(f"INSERT INTO {table}({table}) VALUES('integrity-check')")
    assert con.execute("SELECT count(*) FROM claim_fts WHERE claim_fts MATCH ?", (SENTINEL,)).fetchone()[0] == 0
    assert con.execute("SELECT count(*) FROM representation_fts WHERE representation_fts MATCH ?", (SENTINEL,)).fetchone()[0] == 0
    # FTS5 control writes participate in a transaction; close it before WAL/VACUUM maintenance.
    con.commit()

    # Explicit local-file maintenance boundary: truncate WAL, rewrite free pages, truncate again.
    checkpoint1 = con.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
    con.execute("VACUUM")
    checkpoint2 = con.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
    assert checkpoint1[0] == 0 and checkpoint2[0] == 0, (checkpoint1, checkpoint2)

    needle = SENTINEL.encode()
    db_clean = not file_contains(db_path, needle)
    wal_clean = not file_contains(Path(str(db_path) + "-wal"), needle)
    assert db_clean and wal_clean
    assert not purge_file.exists()

    # The pre-purge backup remains deliberately out of scope and must be reported as such.
    backup_uri = (backup_root / "actakit.sqlite3").resolve().as_uri() + "?mode=ro"
    backup_con = sqlite3.connect(backup_uri, uri=True)
    backup_has = backup_con.execute("SELECT count(*) FROM claim_revisions WHERE text LIKE ?", (f"%{SENTINEL}%",)).fetchone()[0] == 1
    backup_con.close()
    manifest = json.loads((backup_root / "manifest.json").read_text())
    backup_archive_has = any(e["archive_object_id"] == "aob-purge" for e in manifest["archive_objects"])
    assert backup_has and backup_archive_has

    return {
        "wal_checkpoint_before_vacuum": checkpoint1,
        "wal_checkpoint_after_vacuum": checkpoint2,
        "current_db_raw_sentinel_absent": db_clean,
        "current_wal_raw_sentinel_absent": wal_clean,
        "archive_bytes_deleted": True,
        "prepurge_backup_scope": "OUT_OF_SCOPE_RETAINS_PREPURGE_MATERIAL",
    }


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="actakit-storage-proof-") as td:
        root = Path(td)
        live = root / "live"
        live.mkdir()
        archive = live / "archive"
        archive.mkdir()
        db_path = live / "actakit.sqlite3"
        con = open_db(db_path)
        con.executescript(DDL.read_text())
        assert_db_identity(con)
        populate(con, archive)

        wal_path = Path(str(db_path) + "-wal")
        pre_purge_wal_contains = file_contains(wal_path, SENTINEL.encode())

        backup_root = root / "backup"
        make_backup(con, archive, backup_root)
        restore_clean_machine(backup_root, root / "restored")
        purge_report = purge_live(con, db_path, archive, backup_root)

        assert_fts_coverage(con, archive)
        assert_archive_integrity(con, archive)
        assert con.execute("PRAGMA foreign_key_check").fetchall() == []
        con.close()

        runtime_tuple = tuple(int(x) for x in sqlite3.sqlite_version.split(".")[:3])
        print(f"STORAGE_OPERATION_PROOF=PASS sqlite={sqlite3.sqlite_version}")
        print("shared_archive_backup_manifest=PASS")
        print("clean_machine_restore_and_fts_rebuild=PASS")
        print("purge_manifest_archive_fts_wal_vacuum=PASS")
        print(f"pre_purge_wal_contained_sentinel={str(pre_purge_wal_contains).lower()}")
        print(f"prepurge_backup_scope={purge_report['prepurge_backup_scope']}")
        if runtime_tuple >= TARGET_SQLITE:
            print("target_runtime_repeat=PASS")
        else:
            print(f"target_runtime_repeat=REQUIRED candidate_requires>={'.'.join(map(str,TARGET_SQLITE))}")


if __name__ == "__main__":
    main()
