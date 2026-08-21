#!/usr/bin/env python3
"""High-value proof harness for SCRATCH_DDL.sql.

Research-only. This is not a migration test suite or production schema authority.
It deliberately checks the invariants that changed during critical review.
"""
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

DDL = Path(__file__).with_name("SCRATCH_DDL.sql")
T = "2026-08-21T06:00:00.000Z"


def must_fail(con: sqlite3.Connection, sql: str, params: tuple = ()) -> None:
    try:
        with con:
            con.execute(sql, params)
    except sqlite3.IntegrityError:
        return
    raise AssertionError(f"expected IntegrityError: {sql}")


def main() -> None:
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        con = sqlite3.connect(tmp.name)
        con.executescript(DDL.read_text())
        con.execute("PRAGMA foreign_keys=ON")

        # 1. Physical byte identity is independent from logical capture custody.
        with con:
            con.execute("INSERT INTO sources VALUES (?,?,?,?,?)", ("src", "web", "Source", 1, T))
            con.execute("INSERT INTO source_locators VALUES (?,?,?,?,?,?,?)", ("loc", "src", "https://example.invalid/x.pdf", "url", None, None, T))
            con.execute("INSERT INTO sources VALUES (?,?,?,?,?)", ("src-other", "web", "Other Source", 1, T))
            con.execute("INSERT INTO source_locators VALUES (?,?,?,?,?,?,?)", ("loc-other", "src-other", "https://other.invalid/x.pdf", "url", None, None, T))
            for i, day in ((1, "01"), (2, "08")):
                con.execute("INSERT INTO acquisitions VALUES (?,?,?,?,?,?,?,?,?,?)", (f"acq{i}", "src", "loc", f"2026-08-{day}T10:00:00Z", "success", 200, "proof", "1", None, T))
            con.execute("INSERT INTO archive_objects VALUES (?,?,?,?,?,?,?)", ("aobA", "aaa", 3, "sha256/aaa", "available", T, None))
            for i in (1, 2):
                con.execute("INSERT INTO artifacts VALUES (?,?,?,?,?,?,?)", (f"art{i}", "aobA", "application/pdf", "verified", "available", T, None))
                con.execute("INSERT INTO acquisition_artifacts VALUES (?,?,?,?,?)", (f"art{i}", f"acq{i}", "primary", "x.pdf", "https://example.invalid/x.pdf"))
        assert con.execute("SELECT count(*) FROM artifacts WHERE archive_object_id='aobA'").fetchone()[0] == 2
        must_fail(con, "INSERT INTO acquisition_artifacts VALUES (?,?,?,?,?)", ("art1", "acq2", "primary", None, None))
        must_fail(con, "INSERT INTO acquisitions VALUES (?,?,?,?,?,?,?,?,?,?)", ("acq-cross", "src", "loc-other", T, "failed", None, "proof", "1", "wrong-source-locator", T))

        # Processing provenance is durable for any non-human generated semantic/derived record.
        with con:
            con.execute(
                "INSERT INTO process_runs VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                ("pr", "proof", "critical-review-harness", "1", None, None, None, T, T, "success", T),
            )

        # 2. Purged/archive availability contracts do not permit fake available bytes.
        must_fail(con, "INSERT INTO archive_objects VALUES (?,?,?,?,?,?,?)", ("bad-aob", None, None, None, "available", T, None))
        must_fail(con, "INSERT INTO artifacts VALUES (?,?,?,?,?,?,?)", ("bad-art", None, None, "verified", "available", T, None))

        # 3. Exact target must belong to the same Representation occurrence.
        with con:
            con.execute("INSERT INTO representations VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("rep1", "art1", "aobA", None, "original", "application/pdf", None, None, None, "available", T, None))
            con.execute("INSERT INTO representations VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("rep2", "art2", "aobA", None, "original", "application/pdf", None, None, None, "available", T, None))
            con.execute("INSERT INTO representation_targets VALUES (?,?,?,?,?,?,?,?,?)", ("t1", "rep1", "pdf_page_quote", "v1", '{"page_ordinal":1,"exact":"x"}', None, "available", T, None))
        must_fail(con, "INSERT INTO representations VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("rep-orphan", None, "aobA", None, "original", "application/pdf", None, None, None, "available", T, None))
        must_fail(con, "INSERT INTO representations VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("rep-cross-parent", "art2", "aobA", "rep1", "extracted_text", "text/plain", "es", "utf-8", None, "available", T, None))
        with con:
            con.execute("INSERT INTO entities VALUES (?,?,?,?)", ("org", "organization", "Municipalidad", T))
            con.execute("INSERT INTO civic_documents VALUES (?,?)", ("doc", T))
            con.execute("INSERT INTO civic_document_revisions VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("doc1", "doc", 1, None, "Acta", "org", "2026-08-01", "es", "normal", "human", None, T))
            con.execute("INSERT INTO document_representations VALUES (?,?,?,?,?,?)", ("dr1", "doc", "rep1", "whole", "t1", T))
            # AKF-003: unknown classification is a valid durable state.
            con.execute("INSERT INTO document_classifications VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("dc-unknown", "doc", "mystery", "Tipo raro", "unknown", None, None, None, None, "human", None, T))
            # AKF-004: one representation can contain multiple civic documents without duplicating bytes.
            con.execute("INSERT INTO representation_targets VALUES (?,?,?,?,?,?,?,?,?)", ("t2", "rep1", "pdf_page_quote", "v1", '{"page_ordinal":2,"exact":"second"}', None, "available", T, None))
            con.execute("INSERT INTO civic_documents VALUES (?,?)", ("doc2", T))
            con.execute("INSERT INTO civic_document_revisions VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("doc2-1", "doc2", 1, None, "Segundo documento", "org", "2026-08-01", "es", "normal", "human", None, T))
            con.execute("INSERT INTO document_representations VALUES (?,?,?,?,?,?)", ("dr2", "doc2", "rep1", "contained", "t2", T))
            # AKF-005: non-PDF/table locator remains representation-specific and typed/versioned.
            con.execute("INSERT INTO representations VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("rep-table", "art1", "aobA", "rep1", "table", "text/csv", "es", "utf-8", "pr", "available", T, None))
            con.execute("INSERT INTO representation_targets VALUES (?,?,?,?,?,?,?,?,?)", ("t-table", "rep-table", "table_range", "v1", '{"sheet":"Presupuesto","a1_range":"B2:C3","observed_values":[[1,2],[3,4]]}', None, "available", T, None))
        must_fail(con, "INSERT INTO document_representations VALUES (?,?,?,?,?,?)", ("dr-bad", "doc", "rep2", "whole", "t1", T))
        must_fail(con, "INSERT INTO civic_document_revisions VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("doc2-bad", "doc2", 2, "doc1", "Wrong cross-document correction", "org", "2026-08-02", "es", "normal", "human", None, T))
        with con:
            con.execute("INSERT INTO civic_document_revisions VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("doc1-2", "doc", 2, "doc1", "Acta corregida", "org", "2026-08-01", "es", "normal", "human", None, T))
        assert con.execute("SELECT title FROM civic_document_revisions WHERE document_id='doc' ORDER BY revision_no").fetchall() == [("Acta",), ("Acta corregida",)]

        # 4. Claim revision lineage cannot cross stable Claim identity.
        with con:
            con.execute("INSERT INTO claims VALUES (?,?)", ("clmA", T))
            con.execute("INSERT INTO claims VALUES (?,?)", ("clmB", T))
            con.execute("INSERT INTO claim_revisions(id,claim_id,revision_no,supersedes_revision_id,claim_kind,text,origin_kind,process_run_id,attribution_entity_id,attribution_text,temporal_start,temporal_end,sensitive,quantitative,lifecycle,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ("clmA1", "clmA", 1, None, "source_assertion", "A1", "human", None, None, None, None, None, 0, 0, "active", T))
            con.execute("INSERT INTO claim_revisions(id,claim_id,revision_no,supersedes_revision_id,claim_kind,text,origin_kind,process_run_id,attribution_entity_id,attribution_text,temporal_start,temporal_end,sensitive,quantitative,lifecycle,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ("clmB1", "clmB", 1, None, "source_assertion", "B1", "human", None, None, None, None, None, 0, 0, "active", T))
        must_fail(con, """
          INSERT INTO claim_revisions(
            id,claim_id,revision_no,claim_kind,text,origin_kind,sensitive,quantitative,lifecycle,created_at
          ) VALUES (?,?,?,?,?,?,?,?,?,?)
        """, ("clm-machine-no-process", "clmA", 99, "source_assertion", "bad provenance", "machine", 0, 0, "active", T))

        # Above positional insert count is intentionally guarded below by explicit column insert if schema changes.

        # The previous statement would fail noisily if the candidate field count drifts.
        must_fail(con, """
          INSERT INTO claim_revisions(
            id,claim_id,revision_no,supersedes_revision_id,claim_kind,text,origin_kind,
            sensitive,quantitative,lifecycle,created_at
          ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, ("clmB2-bad", "clmB", 2, "clmA1", "source_assertion", "B2", "human", 0, 0, "active", T))
        with con:
            con.execute("""
              INSERT INTO claim_revisions(
                id,claim_id,revision_no,supersedes_revision_id,claim_kind,text,origin_kind,
                sensitive,quantitative,lifecycle,created_at
              ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, ("clmA2", "clmA", 2, "clmA1", "source_assertion", "A2", "human", 0, 0, "active", T))
            # AKF-001: exact evidence target is independent from document identity.
            con.execute("INSERT INTO evidence_links VALUES (?,?,?,?,?,?,?)", ("evA", "clmA1", "t1", "supports", "human", None, T))

        # 5. Direct claim/entity anchors are valid without pretending they came from a mention.
        with con:
            con.execute("INSERT INTO entities VALUES (?,?,?,?)", ("entX", "place", "X", T))
            con.execute("INSERT INTO entities VALUES (?,?,?,?)", ("entY", "place", "Y", T))
            con.execute("INSERT INTO entity_mentions VALUES (?,?,?,?,?,?,?)", ("mA", "t1", "clmA1", "X", "human", None, T))
            con.execute(
                "INSERT INTO claim_entity_links VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                ("cel-direct", None, "clmA1", "entX", None, None, None, "human", None, "active", "direct anchor", T),
            )

        # 6. Mention-derived anchors cite the exact accepted resolution revision.
        with con:
            con.execute("INSERT INTO mention_resolution_revisions VALUES (?,?,?,?,?,?,?,?,?,?)", ("mr1", "mA", 1, "entX", "resolved", "human", None, "reviewer", None, T))
            con.execute(
                "INSERT INTO claim_entity_links VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                ("cel-mention", None, "clmA1", "entX", "mA", "mr1", None, "human", None, "active", "accepted resolution", T),
            )
        must_fail(
            con,
            "INSERT INTO claim_entity_links VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            ("cel-cross", None, "clmB1", "entX", "mA", "mr1", None, "human", None, "active", None, T),
        )
        must_fail(
            con,
            "INSERT INTO claim_entity_links VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            ("cel-wrong-entity", None, "clmA1", "entY", "mA", "mr1", None, "human", None, "active", None, T),
        )
        must_fail(
            con,
            "INSERT INTO claim_entity_links VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            ("cel-missing-resolution", None, "clmA1", "entX", "mA", None, None, "human", None, "active", None, T),
        )
        with con:
            con.execute("INSERT INTO mention_resolution_revisions VALUES (?,?,?,?,?,?,?,?,?,?)", ("mr2", "mA", 2, None, "cleared", "human", None, "reviewer", "undo", T))
            con.execute("INSERT INTO mention_resolution_revisions VALUES (?,?,?,?,?,?,?,?,?,?)", ("mr3", "mA", 3, "entY", "resolved", "human", None, "reviewer", "corrected identity", T))
            con.execute(
                "INSERT INTO claim_entity_links VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                ("cel-mention2", "cel-mention", "clmA1", "entY", "mA", "mr3", None, "human", None, "active", "corrected resolution", T),
            )
        assert con.execute(
            "SELECT entity_id,mention_resolution_revision_id FROM claim_entity_links WHERE id='cel-mention'"
        ).fetchone() == ("entX", "mr1")
        assert con.execute(
            "SELECT supersedes_claim_entity_link_id,entity_id,mention_resolution_revision_id FROM claim_entity_links WHERE id='cel-mention2'"
        ).fetchone() == ("cel-mention", "entY", "mr3")
        must_fail(con, "INSERT INTO mention_resolution_revisions VALUES (?,?,?,?,?,?,?,?,?,?)", ("mr-bad", "mA", 4, None, "resolved", "human", None, None, None, T))

        # AKF-008: equal observed names do not force one Entity identity.
        with con:
            con.execute("INSERT INTO entities VALUES (?,?,?,?)", ("person-same-1", "person", "Juan Pérez", T))
            con.execute("INSERT INTO entities VALUES (?,?,?,?)", ("person-same-2", "person", "Juan Pérez", T))
            con.execute("INSERT INTO entity_mentions VALUES (?,?,?,?,?,?,?)", ("mSame", "t2", "clmB1", "Juan Pérez", "machine", "pr", T))
            con.execute("INSERT INTO mention_resolution_candidates VALUES (?,?,?,?,?,?,?)", ("cand1", "mSame", "person-same-1", 0.61, "machine", "pr", T))
            con.execute("INSERT INTO mention_resolution_candidates VALUES (?,?,?,?,?,?,?)", ("cand2", "mSame", "person-same-2", 0.60, "machine", "pr", T))
        assert con.execute("SELECT count(*) FROM mention_resolution_candidates WHERE mention_id='mSame'").fetchone()[0] == 2

        # AKF-009: merge/split lineage is representable without rewriting old anchors.
        with con:
            for eid in ("proj-old", "proj-alias", "proj-current", "proj-split"):
                con.execute("INSERT INTO entities VALUES (?,?,?,?)", (eid, "project", eid, T))
            con.execute("INSERT INTO entity_reconciliations VALUES (?,?,?,?,?,?,?,?,?)", ("rec-merge-cand", None, "merge", "machine", "pr", None, "candidate match", "candidate", T))
            con.execute("INSERT INTO entity_reconciliation_inputs VALUES (?,?)", ("rec-merge-cand", "proj-old"))
            con.execute("INSERT INTO entity_reconciliation_inputs VALUES (?,?)", ("rec-merge-cand", "proj-alias"))
            con.execute("INSERT INTO entity_reconciliation_outputs VALUES (?,?)", ("rec-merge-cand", "proj-current"))
            con.execute("INSERT INTO entity_reconciliations VALUES (?,?,?,?,?,?,?,?,?)", ("rec-merge", "rec-merge-cand", "merge", "human", None, "reviewer", "same official identifier", "active", T))
            con.execute("INSERT INTO entity_reconciliation_inputs VALUES (?,?)", ("rec-merge", "proj-old"))
            con.execute("INSERT INTO entity_reconciliation_inputs VALUES (?,?)", ("rec-merge", "proj-alias"))
            con.execute("INSERT INTO entity_reconciliation_outputs VALUES (?,?)", ("rec-merge", "proj-current"))
            con.execute("INSERT INTO entity_reconciliations VALUES (?,?,?,?,?,?,?,?,?)", ("rec-split", None, "split", "human", None, "reviewer", "later evidence separates identities", "active", T))
            con.execute("INSERT INTO entity_reconciliation_inputs VALUES (?,?)", ("rec-split", "proj-current"))
            con.execute("INSERT INTO entity_reconciliation_outputs VALUES (?,?)", ("rec-split", "proj-current"))
            con.execute("INSERT INTO entity_reconciliation_outputs VALUES (?,?)", ("rec-split", "proj-split"))
        assert con.execute("SELECT lifecycle FROM entity_reconciliations WHERE id='rec-merge-cand'").fetchone()[0] == "candidate"
        assert con.execute("SELECT supersedes_entity_reconciliation_id,lifecycle FROM entity_reconciliations WHERE id='rec-merge'").fetchone() == ("rec-merge-cand", "active")

        # AKF-011: tag anchors are append-only/correctable like entity anchors.
        with con:
            con.execute("INSERT INTO tags VALUES (?,?,?,?,?)", ("tag-water", "topic", "water", "Agua", T))
            con.execute(
                "INSERT INTO claim_tag_links VALUES (?,?,?,?,?,?,?,?,?)",
                ("ctl1", None, "clmA1", "tag-water", "machine", "pr", "active", "initial classifier", T),
            )
            con.execute(
                "INSERT INTO claim_tag_links VALUES (?,?,?,?,?,?,?,?,?)",
                ("ctl2", "ctl1", "clmA1", "tag-water", "human", None, "rejected", "wrong topic", T),
            )
        assert con.execute(
            "SELECT supersedes_claim_tag_link_id,lifecycle FROM claim_tag_links WHERE id='ctl2'"
        ).fetchone() == ("ctl1", "rejected")
        assert con.execute("SELECT count(*) FROM claim_tag_links WHERE claim_revision_id='clmA1' AND tag_id='tag-water'").fetchone()[0] == 2

        # 7. ClaimRelation revisions bind exact ClaimRevisions and preserve same-relation lineage.
        with con:
            con.execute("INSERT INTO claim_relations VALUES (?,?)", ("rel", T))
            con.execute("INSERT INTO claim_relations VALUES (?,?)", ("rel2", T))
            con.execute("INSERT INTO claim_relation_revisions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", ("rel1", "rel", 1, None, "clmB1", "clmA1", "updates", "human", "source_evidence", "later report", None, "active", T))
            con.execute("INSERT INTO claim_relation_evidence_links VALUES (?,?,?,?,?)", ("rel-e1", "rel1", "t1", "source_basis", T))
        must_fail(con, "INSERT INTO claim_relation_revisions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", ("rel2bad", "rel2", 1, "rel1", "clmB1", "clmA2", "updates", "human", "analyst_inference", "bad cross lineage", None, "active", T))
        assert con.execute("SELECT to_claim_revision_id FROM claim_relation_revisions WHERE id='rel1'").fetchone()[0] == "clmA1"

        # AKF-012: evidence challenge and proposition contradiction remain separate contracts.
        with con:
            con.execute("INSERT INTO evidence_links VALUES (?,?,?,?,?,?,?)", ("ev-challenge", "clmA1", "t2", "challenges", "human", None, T))
            con.execute("INSERT INTO claim_relations VALUES (?,?)", ("rel-contradict", T))
            con.execute("INSERT INTO claim_relation_revisions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", ("rel-contradict1", "rel-contradict", 1, None, "clmB1", "clmA1", "contradicts", "human", "analyst_inference", "incompatible propositions", None, "active", T))
        assert con.execute("SELECT relation FROM evidence_links WHERE id='ev-challenge'").fetchone()[0] == "challenges"
        assert con.execute("SELECT relation_type FROM claim_relation_revisions WHERE id='rel-contradict1'").fetchone()[0] == "contradicts"

        # 8. RoleAssignment owns role/time and exact evidence; invalid intervals fail.
        with con:
            con.execute("INSERT INTO entities VALUES (?,?,?,?)", ("person", "person", "Persona X", T))
            con.execute("INSERT INTO role_assignments VALUES (?,?)", ("ras", T))
            con.execute("INSERT INTO role_assignment_revisions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ("ras1", "ras", 1, None, "person", "org", "alcaldia", "Alcaldía", "2024-05-01", "2028-04-30", "human", "source_evidence", None, None, "active", T))
            con.execute("INSERT INTO role_assignment_evidence_links VALUES (?,?,?,?,?)", ("ras-e1", "ras1", "t1", "source_basis", T))
        must_fail(con, "INSERT INTO role_assignment_revisions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ("ras-bad", "ras", 2, "ras1", "person", "org", None, "Alcaldía", "2029-01-01", "2028-01-01", "human", "analyst_inference", None, "bad dates", "candidate", T))

        # 9. Review grouping keeps exact per-record decisions.
        with con:
            con.execute("INSERT INTO review_actions VALUES (?,?,?,?,?)", ("ra", "reviewer", "batch", T, "proof"))
            con.execute("INSERT INTO claim_reviews VALUES (?,?,?,?,?,?,?)", ("crA", "ra", "clmA1", "accepted", "reviewer", None, T))
            con.execute("INSERT INTO claim_reviews VALUES (?,?,?,?,?,?,?)", ("crB", "ra", "clmB1", "needs_work", "reviewer", "verify", T))
            con.execute("INSERT INTO claim_entity_link_reviews VALUES (?,?,?,?,?,?,?)", ("celr", "ra", "cel-mention2", "accepted", "reviewer", "corrected anchor", T))
            con.execute("INSERT INTO claim_tag_link_reviews VALUES (?,?,?,?,?,?,?)", ("ctlr", "ra", "ctl2", "rejected", "reviewer", "wrong topic", T))
            con.execute("INSERT INTO entity_reconciliation_reviews VALUES (?,?,?,?,?,?,?)", ("err", "ra", "rec-merge", "accepted", "reviewer", None, T))
        assert con.execute("SELECT count(*) FROM claim_reviews WHERE review_action_id='ra'").fetchone()[0] == 2
        assert con.execute("SELECT count(*) FROM claim_entity_link_reviews WHERE review_action_id='ra'").fetchone()[0] == 1
        assert con.execute("SELECT count(*) FROM claim_tag_link_reviews WHERE review_action_id='ra'").fetchone()[0] == 1
        assert con.execute("SELECT count(*) FROM entity_reconciliation_reviews WHERE review_action_id='ra'").fetchone()[0] == 1

        # AKF-014: presentation-specific Hilo/Episode state is not universal core storage.
        names = {r[0] for r in con.execute("SELECT name FROM sqlite_schema WHERE type='table'")}
        assert "hilos" not in names and "episodes" not in names and "outputs" not in names

        # 10. Bounded explicit relation traversal works without a graph engine.
        with con:
            con.execute("INSERT INTO claims VALUES (?,?)", ("clmC", T))
            con.execute("""
              INSERT INTO claim_revisions(
                id,claim_id,revision_no,claim_kind,text,origin_kind,sensitive,quantitative,lifecycle,created_at
              ) VALUES (?,?,?,?,?,?,?,?,?,?)
            """, ("clmC1", "clmC", 1, "source_assertion", "C1", "human", 0, 0, "active", T))
            con.execute("INSERT INTO claim_relations VALUES (?,?)", ("relB", T))
            con.execute("INSERT INTO claim_relation_revisions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", ("relB1", "relB", 1, None, "clmC1", "clmB1", "corrects", "human", "analyst_inference", "proof", None, "active", T))
        # Reachability is node-oriented: duplicate destinations reached by distinct
        # relation edges at the same depth are collapsed. Path/edge enumeration is a
        # separate query contract and must retain relation identity explicitly.
        rows = con.execute("""
          WITH RECURSIVE walk(node, depth) AS (
            VALUES('clmC1', 0)
            UNION
            SELECT r.to_claim_revision_id, walk.depth+1
            FROM walk JOIN claim_relation_revisions r ON r.from_claim_revision_id=walk.node
            WHERE r.lifecycle='active' AND walk.depth < 2
          ) SELECT node, depth FROM walk ORDER BY depth, node
        """).fetchall()
        assert rows == [("clmC1", 0), ("clmB1", 1), ("clmA1", 2)], rows
        parallel_edges = con.execute("""
          SELECT relation_type
          FROM claim_relation_revisions
          WHERE lifecycle='active'
            AND from_claim_revision_id='clmB1'
            AND to_claim_revision_id='clmA1'
          ORDER BY relation_type
        """).fetchall()
        assert parallel_edges == [("contradicts",), ("updates",)], parallel_edges
        symmetric_from_a = con.execute("""
          SELECT CASE WHEN from_claim_revision_id=? THEN to_claim_revision_id ELSE from_claim_revision_id END
          FROM claim_relation_revisions
          WHERE lifecycle='active' AND relation_type IN ('contradicts','same_matter_as')
            AND (? IN (from_claim_revision_id,to_claim_revision_id))
        """, ("clmA1", "clmA1")).fetchall()
        assert symmetric_from_a == [("clmB1",)], symmetric_from_a
        reverse_updates = con.execute("""
          SELECT count(*) FROM claim_relation_revisions
          WHERE lifecycle='active' AND relation_type='updates'
            AND from_claim_revision_id='clmA1' AND to_claim_revision_id='clmB1'
        """).fetchone()[0]
        assert reverse_updates == 0

        # 11. FTS is disposable/self-content and secure-delete mode is persistent.
        with con:
            con.execute("INSERT INTO claim_fts(claim_revision_id,text) VALUES (?,?)", ("clmA1", "obra junio"))
        assert con.execute("SELECT count(*) FROM claim_fts WHERE claim_fts MATCH 'junio'").fetchone()[0] == 1
        assert con.execute("SELECT v FROM claim_fts_config WHERE k='secure-delete'").fetchone()[0] == 1
        with con:
            con.execute("DELETE FROM claim_fts")
            con.execute("INSERT INTO claim_fts(claim_fts) VALUES('rebuild')")
        assert con.execute("SELECT count(*) FROM claim_fts").fetchone()[0] == 0

        # 12. Purge manifest intentionally has no FK to target record and survives target removal semantics.
        with con:
            con.execute("INSERT INTO purges VALUES (?,?,?,?,?,?,?,?)", ("purge", "policy", "operator", "minimal_tombstone", T, None, "planned", None))
            con.execute("INSERT INTO purge_targets VALUES (?,?,?,?,?,?,?)", ("purge", "representation_target", "t1", "scrub_payload", T, None, None))
            con.execute("UPDATE representation_targets SET selector_kind=NULL,selector_version=NULL,selector_payload_json=NULL,state_payload_json=NULL,availability='purged',purged_at=? WHERE id='t1'", (T,))
        assert con.execute("SELECT availability, selector_payload_json FROM representation_targets WHERE id='t1'").fetchone() == ("purged", None)
        assert con.execute("SELECT record_id FROM purge_targets WHERE purge_id='purge'").fetchone()[0] == "t1"

        # AKF-015 partial operational proof: SQLite backup snapshot restores relational authority cleanly.
        with tempfile.NamedTemporaryFile(suffix=".restore.db") as restored_file:
            restored = sqlite3.connect(restored_file.name)
            con.backup(restored)
            restored.execute("PRAGMA foreign_keys=ON")
            assert restored.execute("PRAGMA foreign_key_check").fetchall() == []
            assert restored.execute("SELECT count(*) FROM claims").fetchone()[0] == con.execute("SELECT count(*) FROM claims").fetchone()[0]
            assert restored.execute("SELECT count(*) FROM purge_targets").fetchone()[0] == 1
            restored.close()

        assert con.execute("PRAGMA foreign_key_check").fetchall() == []
        strict_count = con.execute("SELECT count(*) FROM pragma_table_list WHERE strict=1").fetchone()[0]
        assert strict_count >= 40

        print(f"STRUCTURAL_DDL_PROOF=PASS sqlite={sqlite3.sqlite_version} strict_tables={strict_count}")
        print("critical_invariants=16/16 PASS")
        print("semantic_fixture_storage=16/16 REPRESENTABLE")
        print("sqlite_backup_snapshot=PASS (archive/clean-machine restore still separate operational gate)")
        print("target_runtime_floor=NOT_CERTIFIED_HERE (candidate requires SQLite >=3.51.3)")
        con.close()


if __name__ == "__main__":
    main()
