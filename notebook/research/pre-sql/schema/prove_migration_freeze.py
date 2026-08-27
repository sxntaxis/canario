#!/usr/bin/env python3
"""Proof of the proposed migration-0001 physical freeze contract.

Notebook design proof only. It validates bootstrap atomicity, file identity,
connection/open rules, schema inventory and index/query-plan properties. It does
not install a production migration or authorize a cutover.
"""
from __future__ import annotations

import sqlite3
import tempfile
import re
from pathlib import Path

SPEC = Path(__file__).with_name("MIGRATION_0001_SPEC.sql")
APPLICATION_ID = 0x414B4954
SCHEMA_VERSION = 1
TARGET_SQLITE = (3, 53, 4)


def configure_writable_connection(con: sqlite3.Connection) -> sqlite3.Connection:
    con.execute("PRAGMA foreign_keys=ON")
    assert con.execute("PRAGMA journal_mode=WAL").fetchone()[0].lower() == "wal"
    con.execute("PRAGMA synchronous=FULL")
    con.execute("PRAGMA trusted_schema=OFF")
    con.execute("PRAGMA secure_delete=ON")
    con.execute("PRAGMA busy_timeout=5000")
    return con


def open_writable(path: Path) -> sqlite3.Connection:
    return configure_writable_connection(sqlite3.connect(path))


def user_schema_objects(con: sqlite3.Connection) -> list[tuple[str, str]]:
    return con.execute(
        """
        SELECT type,name FROM sqlite_schema
        WHERE name NOT LIKE 'sqlite_%'
        ORDER BY type,name
        """
    ).fetchall()


def assert_fresh_bootstrap_target(con: sqlite3.Connection) -> None:
    assert con.execute("PRAGMA application_id").fetchone()[0] == 0
    assert con.execute("PRAGMA user_version").fetchone()[0] == 0
    assert user_schema_objects(con) == []


def run_bootstrap_transaction(con: sqlite3.Connection, sql: str) -> None:
    # The spec deliberately contains no BEGIN/COMMIT and no connection PRAGMAs.
    # The bootstrap executor owns the transaction around the exact SQL artifact.
    try:
        con.executescript("BEGIN IMMEDIATE;\n" + sql + "\nCOMMIT;\n")
    except Exception:
        if con.in_transaction:
            con.rollback()
        raise


def assert_connection_contract(con: sqlite3.Connection) -> None:
    assert con.execute("PRAGMA application_id").fetchone()[0] == APPLICATION_ID
    assert con.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
    assert con.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert con.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
    assert con.execute("PRAGMA synchronous").fetchone()[0] == 2
    assert con.execute("PRAGMA trusted_schema").fetchone()[0] == 0
    assert con.execute("PRAGMA secure_delete").fetchone()[0] == 1
    assert con.execute("PRAGMA busy_timeout").fetchone()[0] == 5000


def assert_schema_inventory(con: sqlite3.Connection) -> None:
    strict = con.execute("SELECT count(*) FROM pragma_table_list WHERE strict=1").fetchone()[0]
    assert strict == 72, strict
    # 0001 deliberately keeps ordinary rowid tables. WITHOUT ROWID remains a later
    # benchmark-driven optimization; no application contract may depend on rowid.
    without_rowid = con.execute(
        "SELECT count(*) FROM pragma_table_list WHERE strict=1 AND wr=1"
    ).fetchone()[0]
    assert without_rowid == 0, without_rowid
    fts = con.execute(
        "SELECT count(*) FROM pragma_table_list WHERE type='virtual' AND name IN ('claim_fts','representation_fts','document_fts')"
    ).fetchone()[0]
    assert fts == 3, fts
    assert con.execute("SELECT count(*) FROM sqlite_schema WHERE type='trigger'").fetchone()[0] == 0
    assert con.execute("SELECT count(*) FROM sqlite_schema WHERE name='schema_migrations'").fetchone()[0] == 0
    assert con.execute("SELECT count(*) FROM sqlite_schema WHERE lower(sql) LIKE '%json_valid(%'").fetchone()[0] == 0
    assert con.execute("PRAGMA foreign_key_check").fetchall() == []
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    for table in ("claim_fts", "representation_fts", "document_fts"):
        assert con.execute(f"SELECT v FROM {table}_config WHERE k='secure-delete'").fetchone()[0] == 1

    # 0001 intentionally uses no application triggers/cascades. Consequential
    # cross-row/lifecycle operations are validated by core transactions.
    tables = [
        r[0]
        for r in con.execute(
            "SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    ]
    for table in tables:
        for fk in con.execute(f'PRAGMA foreign_key_list("{table}")'):
            assert fk[5] == "NO ACTION" and fk[6] == "NO ACTION", (table, fk)


def enum_values(con: sqlite3.Connection, table: str, column: str) -> set[str]:
    sql = con.execute("SELECT sql FROM sqlite_schema WHERE type='table' AND name=?", (table,)).fetchone()[0]
    match = re.search(
        rf"CHECK\s*\(\s*(?:{re.escape(column)}\s+IS\s+NULL\s+OR\s+)?{re.escape(column)}\s+IN\s*\(([^)]*)\)",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match is not None, (table, column)
    return set(re.findall(r"'([^']+)'", match.group(1)))


def assert_closed_vocabularies(con: sqlite3.Connection) -> None:
    expected = {
        ("sources", "kind"): {"web", "api", "feed", "filesystem", "manual", "other"},
        ("source_authority_scopes", "scope_kind"): {"formal_record", "recorded_speech", "issuer_statement", "reported_statement", "dataset_value", "visual_record", "other"},
        ("acquisitions", "outcome"): {"success", "partial", "not_found", "failed"},
        ("acquisition_artifacts", "role"): {"primary", "attachment", "response_body", "other"},
        ("process_runs", "outcome"): {"success", "partial", "failed"},
        ("derivation_runs", "operation_kind"): {"query", "program", "rule", "other_registered"},
        ("derivation_runs", "program_kind"): {"sql", "expression", "script", "other_registered"},
        ("derivation_runs", "outcome"): {"success", "failed"},
        ("derivation_results", "result_kind"): {"scalar", "table", "structured", "binary", "other_registered"},
        ("derivation_results", "availability"): {"available", "purged"},
        ("derivation_result_targets", "lineage_state"): {"exact", "partial", "unavailable", "none"},
        ("derivation_result_targets", "availability"): {"available", "purged"},
        ("derivation_result_lineage", "lineage_state"): {"exact", "partial"},
        ("verification_runs", "outcome"): {"completed", "failed"},
        ("verification_runs", "verdict"): {"supported", "contradicted", "insufficient_evidence"},
        ("verification_runs", "sufficiency_state"): {"sufficient", "insufficient"},
        ("verification_derivation_steps", "use_state"): {"attempted", "consumed"},
        ("verification_evidence_items", "role"): {"supports", "challenges", "context"},
        ("assessments", "judgment"): {"supported", "contested", "refuted", "unresolved"},
        ("quality_decisions", "decision"): {"accept", "escalate", "quarantine_review"},
        ("archive_objects", "availability"): {"available", "purged"},
        ("artifacts", "availability"): {"available", "restricted", "purged"},
        ("artifacts", "validation_state"): {"pending", "verified", "quarantined", "rejected"},
        ("representations", "kind"): {"original", "extracted_text", "ocr_text", "normalized_text", "table", "page_image", "transcript", "redacted_derivative", "other"},
        ("representations", "availability"): {"available", "restricted", "purged"},
        ("representation_targets", "availability"): {"available", "purged"},
        ("entities", "kind"): {"person", "organization", "place", "project", "legal_instrument", "contract", "program", "other"},
        ("civic_document_revisions", "visibility"): {"normal", "restricted"},
        ("document_classifications", "normalized_type"): {"unknown", "acta", "agenda", "convocatoria", "acuerdo", "resolucion", "oficio", "informe", "dictamen", "presupuesto", "plan", "reglamento_ordenanza", "aviso_publico", "correspondencia", "comunicado_prensa", "contrato", "dataset", "grabacion", "otro"},
        ("document_representations", "occurrence_kind"): {"whole", "contained", "attachment", "other"},
        ("entity_names", "name_kind"): {"official", "alias", "former", "display", "other"},
        ("mention_resolution_revisions", "resolution_state"): {"resolved", "cleared"},
        ("entity_reconciliations", "kind"): {"merge", "split"},
        ("claim_revisions", "claim_kind"): {"source_assertion", "derived_inference", "community_report", "verification_question"},
        ("claim_revisions", "lifecycle"): {"active", "rejected", "retracted", "restricted"},
        ("evidence_links", "relation"): {"supports", "challenges", "contextualizes", "quotes", "mentions"},
        ("claim_relation_revisions", "relation_type"): {"updates", "contradicts", "corrects", "responds_to", "implements", "supersedes", "same_matter_as", "other"},
        ("claim_relation_revisions", "basis_kind"): {"source_evidence", "analyst_inference", "mechanical_identity", "other"},
        ("claim_relation_evidence_links", "basis_role"): {"source_basis", "context"},
        ("role_assignment_evidence_links", "basis_role"): {"source_basis", "context"},
        ("review_actions", "mode"): {"strict", "batch", "supervised"},
        ("purges", "retention_mode"): {"minimal_tombstone", "no_tombstone"},
        ("purges", "outcome"): {"planned", "completed", "partial", "failed"},
        ("purge_targets", "action"): {"delete_record", "scrub_payload", "detach", "delete_bytes"},
        ("purge_targets", "outcome"): {"completed", "failed", "skipped"},
    }
    for key, values in expected.items():
        assert enum_values(con, *key) == values, (key, enum_values(con, *key), values)

    purge_kinds = enum_values(con, "purge_targets", "record_kind")
    required_new_purge_kinds = {
        "derivation_run", "derivation_run_egress", "derivation_result",
        "derivation_result_target", "verification_run", "verification_run_egress", "assessment",
        "claim_revision_action",
    }
    assert required_new_purge_kinds.issubset(purge_kinds), (required_new_purge_kinds - purge_kinds)

    origin = {"machine", "rule", "human"}
    for table in (
        "civic_document_revisions", "document_identifiers", "document_classifications",
        "document_representations", "claim_revisions", "evidence_links", "entity_mentions",
        "entity_names", "entity_identifiers", "mention_resolution_candidates",
        "mention_resolution_revisions", "entity_reconciliations", "claim_entity_links",
        "claim_tag_links", "claim_relation_revisions", "role_assignment_revisions", "assessments",
    ):
        assert enum_values(con, table, "origin_kind") == origin, table

    semantic_lifecycle = {"candidate", "active", "rejected"}
    for table in (
        "document_identifiers", "document_classifications", "document_representations",
        "evidence_links", "entity_names", "entity_identifiers", "entity_reconciliations",
        "claim_entity_links", "claim_tag_links", "claim_relation_revisions",
        "role_assignment_revisions",
    ):
        assert enum_values(con, table, "lifecycle") == semantic_lifecycle, table

    assert enum_values(con, "claim_revision_actions", "action") == {
        "correct", "restrict", "unrestrict", "retract"
    }

    action_sql = con.execute(
        "SELECT sql FROM sqlite_schema WHERE type='table' AND name='claim_revision_actions'"
    ).fetchone()[0]
    assert "review_action_id TEXT UNIQUE REFERENCES review_actions(id)" in action_sql
    assert "action='correct' AND review_action_id IS NOT NULL" in action_sql
    assert "action<>'correct' AND review_action_id IS NULL" in action_sql

    review = {"accepted", "rejected", "needs_work"}
    for table in (
        "claim_reviews", "document_identifier_reviews", "document_classification_reviews",
        "document_representation_reviews", "evidence_link_reviews", "entity_name_reviews",
        "entity_identifier_reviews", "claim_relation_reviews",
        "mention_resolution_candidate_reviews", "claim_entity_link_reviews",
        "claim_tag_link_reviews", "entity_reconciliation_reviews", "role_assignment_reviews",
    ):
        assert enum_values(con, table, "decision") == review, table



def assert_index_inventory(con: sqlite3.Connection) -> None:
    explicit = con.execute(
        "SELECT count(*) FROM sqlite_schema WHERE type='index' AND sql IS NOT NULL"
    ).fetchone()[0]
    assert explicit == 137, explicit

    # Freeze rejects exact duplicate explicit indexes and simple same-predicate
    # prefix redundancy. This is intentionally conservative; planner proof below
    # remains the authority for FK/query coverage.
    tables = [
        r[0]
        for r in con.execute(
            "SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    ]
    exact: list[tuple] = []
    prefix: list[tuple] = []
    for table in tables:
        indexes = []
        for row in con.execute(f'PRAGMA index_list("{table}")'):
            _seq, name, unique, origin, partial = row[:5]
            if origin != "c":
                continue
            cols = tuple(
                r[2]
                for r in con.execute(f'PRAGMA index_xinfo("{name}")')
                if r[5]
            )
            indexes.append((name, unique, partial, cols))
        for i, left in enumerate(indexes):
            for right in indexes[i + 1 :]:
                if left[1:] == right[1:]:
                    exact.append((table, left[0], right[0], left[3]))
                if left[1] == right[1] == 0 and left[2] == right[2] and left[3] and right[3]:
                    if len(left[3]) < len(right[3]) and right[3][: len(left[3])] == left[3]:
                        prefix.append((table, left[0], right[0], left[3], right[3]))
                    elif len(right[3]) < len(left[3]) and left[3][: len(right[3])] == right[3]:
                        prefix.append((table, right[0], left[0], right[3], left[3]))
    assert exact == [], exact
    assert prefix == [], prefix

def assert_no_fk_child_scans(con: sqlite3.Connection) -> int:
    ordinary = [
        r[0]
        for r in con.execute(
            "SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%' AND sql LIKE '%STRICT%'"
        )
    ]
    checked = 0
    for table in ordinary:
        groups: dict[int, list[tuple]] = {}
        for row in con.execute(f'PRAGMA foreign_key_list("{table}")'):
            groups.setdefault(row[0], []).append(row)
        for rows in groups.values():
            rows.sort(key=lambda row: row[1])
            where = " AND ".join(f'"{row[3]}"=?' for row in rows)
            plan = con.execute(
                f'EXPLAIN QUERY PLAN SELECT 1 FROM "{table}" WHERE {where}',
                tuple("probe" for _ in rows),
            ).fetchall()
            details = [row[3] for row in plan]
            assert not any(
                detail == f"SCAN {table}" or detail.startswith(f"SCAN {table} ")
                for detail in details
            ), (table, tuple(row[3] for row in rows), details)
            checked += 1
    return checked


def assert_named_query_indexes(con: sqlite3.Connection) -> None:
    probes = [
        (
            "civic_document_revisions_date_idx",
            "EXPLAIN QUERY PLAN SELECT id FROM civic_document_revisions WHERE document_date=? ORDER BY document_date,document_id",
            ("2026-01-01",),
        ),
        (
            "document_classifications_type_lifecycle_idx",
            "EXPLAIN QUERY PLAN SELECT document_id FROM document_classifications WHERE normalized_type=? AND lifecycle=? ORDER BY document_id,created_at",
            ("acta", "active"),
        ),
        (
            "entity_names_name_lifecycle_idx",
            "EXPLAIN QUERY PLAN SELECT entity_id FROM entity_names WHERE name=? AND lifecycle=? ORDER BY entity_id",
            ("AyA", "active"),
        ),
        (
            "purge_targets_record_idx",
            "EXPLAIN QUERY PLAN SELECT purge_id FROM purge_targets WHERE record_kind=? AND record_id=?",
            ("claim", "clm"),
        ),
        (
            "document_representations_representation_fk_idx",
            "EXPLAIN QUERY PLAN SELECT document_id FROM document_representations WHERE representation_id=?",
            ("rep",),
        ),
        (
            "claim_relation_revisions_from_idx",
            "EXPLAIN QUERY PLAN SELECT to_claim_revision_id FROM claim_relation_revisions WHERE from_claim_revision_id=? AND relation_type=?",
            ("a", "updates"),
        ),
        (
            "derivation_result_lineage_source_target_fk_idx",
            "EXPLAIN QUERY PLAN SELECT derivation_result_target_id FROM derivation_result_lineage WHERE representation_target_id=? AND representation_id=?",
            ("target", "rep"),
        ),
        (
            "verification_derivation_steps_result_target_run_fk_idx",
            "EXPLAIN QUERY PLAN SELECT verification_run_id FROM verification_derivation_steps WHERE derivation_result_target_id=? AND derivation_run_id=?",
            ("drt", "drv"),
        ),
        (
            "assessments_claim_assessor_time_idx",
            "EXPLAIN QUERY PLAN SELECT judgment FROM assessments WHERE claim_revision_id=? AND assessor_key=? ORDER BY created_at DESC,id DESC LIMIT 1",
            ("clm", "assessor"),
        ),
    ]
    for expected, sql, params in probes:
        details = " | ".join(row[3] for row in con.execute(sql, params).fetchall())
        assert expected in details, (expected, details)



def assert_core_write_contracts(con: sqlite3.Connection) -> None:
    """Prove deliberate SQL/core boundary for cross-row write invariants."""
    t0 = "2026-08-21T10:00:00.000Z"
    t1 = "2026-08-21T10:01:00.000Z"
    t2 = "2026-08-21T10:02:00.000Z"

    with con:
        con.execute("INSERT INTO claims VALUES (?,?)", ("clm-freeze", t0))
        con.execute(
            """INSERT INTO claim_revisions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            ("clmr-freeze-1", "clm-freeze", 1, None, "source_assertion", "v1", "human", None, None, None, None, None, None, 0, 0, "active", t0),
        )

    # SQL guarantees identity, same-family predecessor, one successor and uniqueness.
    # Consecutive numbering is deliberately a core pre-commit invariant, not a trigger.
    con.execute("SAVEPOINT revision_gap")
    con.execute(
        """INSERT INTO claim_revisions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("clmr-freeze-3", "clm-freeze", 3, "clmr-freeze-1", "source_assertion", "gap", "human", None, None, None, None, None, None, 0, 0, "active", t1),
    )
    gaps = con.execute(
        """
        SELECT child.id
        FROM claim_revisions child
        JOIN claim_revisions parent ON parent.id=child.supersedes_revision_id
        WHERE child.revision_no <> parent.revision_no + 1
        """
    ).fetchall()
    assert gaps == [("clmr-freeze-3",)], gaps
    con.execute("ROLLBACK TO revision_gap")
    con.execute("RELEASE revision_gap")

    with con:
        con.execute(
            """INSERT INTO claim_revisions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            ("clmr-freeze-2", "clm-freeze", 2, "clmr-freeze-1", "source_assertion", "v2", "human", None, None, None, None, None, None, 0, 0, "active", t1),
        )
    leaves = con.execute(
        """
        SELECT r.id FROM claim_revisions r
        WHERE r.claim_id='clm-freeze'
          AND NOT EXISTS (SELECT 1 FROM claim_revisions s WHERE s.supersedes_revision_id=r.id)
        """
    ).fetchall()
    assert leaves == [("clmr-freeze-2",)], leaves

    # Mention resolution is append-only but intentionally uses monotonically
    # consecutive numbers rather than a supersedes pointer. The next write must
    # be max(revision_no)+1 for the exact mention.
    with con:
        con.execute("INSERT INTO sources VALUES (?,?,?,?,?)", ("src-freeze", "manual", "Freeze proof", 1, t0))
        con.execute("INSERT INTO archive_objects VALUES (?,?,?,?,?,?,?)", ("aob-freeze", "f"*64, 1, "sha256/"+"f"*64, "available", t0, None))
        con.execute("INSERT INTO artifacts VALUES (?,?,?,?,?,?,?)", ("art-freeze", "aob-freeze", "text/plain", "verified", "available", t0, None))
        con.execute("INSERT INTO acquisitions VALUES (?,?,?,?,?,?,?,?,?,?)", ("acq-freeze", "src-freeze", None, t0, "success", None, "proof", "1", None, t0))
        con.execute("INSERT INTO acquisition_artifacts VALUES (?,?,?,?,?)", ("art-freeze", "acq-freeze", "primary", None, None))
        con.execute("INSERT INTO representations VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("rep-freeze", "art-freeze", None, None, "original", "text/plain", "es", "utf-8", None, "available", t0, None))
        con.execute("INSERT INTO representation_targets VALUES (?,?,?,?,?,?,?,?,?)", ("target-freeze", "rep-freeze", "whole", "v1", "{}", None, "available", t0, None))
        con.execute("INSERT INTO entity_mentions VALUES (?,?,?,?,?,?,?)", ("mention-freeze", "target-freeze", None, "X", "human", None, t0))
        con.execute("INSERT INTO entities VALUES (?,?,?,?)", ("ent-freeze", "person", "X", t0))
        con.execute("INSERT INTO mention_resolution_revisions VALUES (?,?,?,?,?,?,?,?,?,?)", ("mrr-freeze-1", "mention-freeze", 1, "ent-freeze", "resolved", "human", None, "reviewer", None, t0))
    next_no = con.execute(
        "SELECT COALESCE(MAX(revision_no),0)+1 FROM mention_resolution_revisions WHERE mention_id=?",
        ("mention-freeze",),
    ).fetchone()[0]
    assert next_no == 2

    # More than one independent active current document classification is legal
    # structurally but invalid operational state; core transaction validation catches it.
    with con:
        con.execute("INSERT INTO civic_documents VALUES (?,?)", ("doc-freeze", t0))
        for n in (1, 2):
            con.execute(
                """INSERT INTO document_classifications VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (f"dc-freeze-{n}", None, "doc-freeze", None, None, "acta", None, None, None, None, None, "human", None, "active", None, t0),
            )
    violations = con.execute(
        """
        SELECT document_id
        FROM document_classifications d
        WHERE lifecycle='active'
          AND NOT EXISTS (
            SELECT 1 FROM document_classifications s
            WHERE s.supersedes_document_classification_id=d.id
          )
        GROUP BY document_id
        HAVING count(*) > 1
        """
    ).fetchall()
    assert violations == [("doc-freeze",)], violations
    with con:
        con.execute("UPDATE document_classifications SET lifecycle='rejected' WHERE id='dc-freeze-2'")
    assert con.execute(
        """
        SELECT document_id FROM document_classifications d
        WHERE lifecycle='active'
          AND NOT EXISTS (SELECT 1 FROM document_classifications s WHERE s.supersedes_document_classification_id=d.id)
        GROUP BY document_id HAVING count(*) > 1
        """
    ).fetchall() == []

    # ProcessRun is terminal provenance, not a job scheduler. Canonical machine/rule
    # outputs may reference only successful or partial runs; failed runs remain audit data.
    with con:
        con.execute("INSERT INTO process_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", ("pr-failed", "extract_claims", "proof", "1", "local_deterministic", None, None, None, t0, t1, "failed", "proof_failed", t1))
        con.execute("INSERT INTO entity_names VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", ("en-failed", None, "ent-freeze", "X machine", "alias", None, None, None, "machine", "pr-failed", "candidate", None, t1))
    bad_process_refs = con.execute(
        """
        SELECT n.id
        FROM entity_names n JOIN process_runs p ON p.id=n.process_run_id
        WHERE n.origin_kind IN ('machine','rule') AND p.outcome NOT IN ('success','partial')
        """
    ).fetchall()
    assert bad_process_refs == [("en-failed",)], bad_process_refs
    with con:
        con.execute("DELETE FROM entity_names WHERE id='en-failed'")

    # Review rows are immutable assessments. A reviewer reverses their own judgment
    # by appending another row; effective per-reviewer state is latest (created_at,id).
    with con:
        con.execute("INSERT INTO claim_reviews VALUES (?,?,?,?,?,?,?)", ("rv-1", None, "clmr-freeze-2", "accepted", "alice", None, t1))
        con.execute("INSERT INTO claim_reviews VALUES (?,?,?,?,?,?,?)", ("rv-2", None, "clmr-freeze-2", "needs_work", "alice", "reconsidered", t2))
        con.execute("INSERT INTO claim_reviews VALUES (?,?,?,?,?,?,?)", ("rv-3", None, "clmr-freeze-2", "accepted", "bob", None, t2))
    latest_alice = con.execute(
        """
        SELECT decision FROM claim_reviews
        WHERE claim_revision_id=? AND reviewer=?
        ORDER BY created_at DESC, id DESC LIMIT 1
        """,
        ("clmr-freeze-2", "alice"),
    ).fetchone()[0]
    assert latest_alice == "needs_work"

    # Operation-level idempotency uses a preallocated stable ID as the retry token.
    # A retry never INSERT OR REPLACEs canonical data: same payload can be recognized;
    # a different payload under the same ID is an explicit collision.
    with con:
        con.execute("INSERT INTO tags VALUES (?,?,?,?,?)", ("tag-retry", "local", "water", "Water", t0))
    try:
        con.execute("INSERT INTO tags VALUES (?,?,?,?,?)", ("tag-retry", "local", "water", "Water", t0))
    except sqlite3.IntegrityError:
        existing = con.execute("SELECT namespace,key,label,created_at FROM tags WHERE id='tag-retry'").fetchone()
        assert existing == ("local", "water", "Water", t0)
    else:
        raise AssertionError("retry unexpectedly duplicated stable identity")
    try:
        con.execute("INSERT INTO tags VALUES (?,?,?,?,?)", ("tag-retry", "local", "roads", "Roads", t0))
    except sqlite3.IntegrityError:
        existing = con.execute("SELECT namespace,key,label,created_at FROM tags WHERE id='tag-retry'").fetchone()
        assert existing != ("local", "roads", "Roads", t0)
    else:
        raise AssertionError("identity collision unexpectedly overwrote canonical data")


def assert_review_query_plan(con: sqlite3.Connection) -> None:
    details = " | ".join(
        row[3]
        for row in con.execute(
            """EXPLAIN QUERY PLAN
            SELECT decision FROM claim_reviews
            WHERE claim_revision_id=? AND reviewer=?
            ORDER BY created_at DESC,id DESC LIMIT 1""",
            ("clm", "reviewer"),
        )
    )
    assert "claim_reviews_claim_reviewer_time_idx" in details, details

def assert_read_only_open(path: Path) -> None:
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.execute("PRAGMA query_only=ON")
    con.execute("PRAGMA trusted_schema=OFF")
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("PRAGMA busy_timeout=5000")
    assert con.execute("PRAGMA query_only").fetchone()[0] == 1
    assert con.execute("PRAGMA trusted_schema").fetchone()[0] == 0
    assert con.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert con.execute("PRAGMA application_id").fetchone()[0] == APPLICATION_ID
    assert con.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
    assert con.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
    try:
        con.execute("CREATE TABLE forbidden_write(id INTEGER)")
    except sqlite3.OperationalError:
        pass
    else:
        raise AssertionError("read-only/query-only authority accepted a write")
    con.close()


def prove_atomic_failure(spec: str, root: Path) -> None:
    path = root / "failed-bootstrap.sqlite3"
    con = open_writable(path)
    assert_fresh_bootstrap_target(con)
    # Fault *after* application_id/user_version were written. Rollback must remove
    # both schema and markers; WAL mode may persist because it was set pre-transaction.
    try:
        run_bootstrap_transaction(con, spec + "\nSELECT * FROM __forced_freeze_failure__;")
    except sqlite3.OperationalError:
        pass
    else:
        raise AssertionError("forced bootstrap failure unexpectedly committed")
    assert not con.in_transaction
    assert con.execute("PRAGMA application_id").fetchone()[0] == 0
    assert con.execute("PRAGMA user_version").fetchone()[0] == 0
    assert user_schema_objects(con) == []
    assert con.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
    con.close()


def prove_wrong_file_rejection(root: Path) -> None:
    path = root / "not-canario.sqlite3"
    con = open_writable(path)
    con.execute("CREATE TABLE unrelated(id INTEGER PRIMARY KEY)")
    con.commit()
    try:
        assert_fresh_bootstrap_target(con)
    except AssertionError:
        pass
    else:
        raise AssertionError("non-empty unknown SQLite file was accepted as fresh ActaKit")
    con.close()


def main() -> None:
    spec = SPEC.read_text()
    lowered = spec.lower()
    assert "begin transaction" not in lowered and "begin immediate" not in lowered and "commit;" not in lowered
    for pragma in ("foreign_keys", "journal_mode", "synchronous", "trusted_schema", "secure_delete", "busy_timeout"):
        assert f"pragma {pragma}" not in lowered, pragma
    assert "json_valid(" not in lowered

    with tempfile.TemporaryDirectory(prefix="canario-freeze-proof-") as td:
        root = Path(td)
        prove_atomic_failure(spec, root)
        prove_wrong_file_rejection(root)

        path = root / "canario.sqlite3"
        con = open_writable(path)
        assert_fresh_bootstrap_target(con)
        run_bootstrap_transaction(con, spec)
        assert_connection_contract(con)
        assert_schema_inventory(con)
        assert_closed_vocabularies(con)
        assert_core_write_contracts(con)
        assert_index_inventory(con)
        fk_count = assert_no_fk_child_scans(con)
        assert_named_query_indexes(con)
        assert_review_query_plan(con)
        con.close()

        # Ordinary writable reopen verifies file identity and re-establishes every
        # connection-local invariant rather than trusting backup/persisted state.
        con = open_writable(path)
        assert_connection_contract(con)
        assert_schema_inventory(con)
        con.close()
        assert_read_only_open(path)

        runtime_tuple = tuple(int(part) for part in sqlite3.sqlite_version.split(".")[:3])
        print(f"MIGRATION_FREEZE_PROOF=PASS sqlite={sqlite3.sqlite_version}")
        print("bootstrap_transaction=PASS")
        print("bootstrap_failure_rollback=PASS markers=0/0 schema=empty journal_mode=wal")
        print("wrong_file_rejection=PASS")
        print("schema_inventory=PASS strict_tables=72 fts_tables=3 app_triggers=0")
        print("closed_vocabularies=PASS")
        print("core_write_contracts=PASS revision_leaf_process_review_idempotency")
        print("rowid_strategy=PASS ordinary_rowid_tables=72 without_rowid=0")
        print("index_inventory=PASS explicit=137 exact_duplicates=0 simple_prefix_redundancy=0")
        print(f"foreign_key_child_plans=PASS checked={fk_count} scans=0")
        print("query_surface_indexes=PASS")
        print("readonly_open_contract=PASS")
        print("sql_json_dependency=ABSENT")
        if runtime_tuple >= TARGET_SQLITE:
            print("target_runtime_repeat=PASS")
        else:
            print("target_runtime_repeat=REQUIRED candidate_requires>=3.53.4")


if __name__ == "__main__":
    main()
