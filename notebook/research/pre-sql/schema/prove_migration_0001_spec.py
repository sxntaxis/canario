#!/usr/bin/env python3
"""High-value proof harness for MIGRATION_0001_SPEC.sql.

Notebook design proof only. This is not a production migration or cutover test.
It checks the physical invariants proposed for the frozen migration-0001 contract.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
from pathlib import Path

DDL = Path(__file__).with_name("MIGRATION_0001_SPEC.sql")
T = "2026-08-21T06:00:00.000Z"
H_A = "a" * 64
H_B = "b" * 64
H_C = "c" * 64
H_D = "d" * 64


def must_fail(con: sqlite3.Connection, sql: str, params: tuple = ()) -> None:
    try:
        with con:
            con.execute(sql, params)
    except sqlite3.IntegrityError:
        return
    raise AssertionError(f"expected IntegrityError: {sql}")


def _target_row(con: sqlite3.Connection, target_id: str) -> tuple[str, str | None, str | None, str | None, str]:
    row = con.execute(
        """SELECT representation_id,selector_kind,selector_version,selector_payload_json,availability
           FROM representation_targets WHERE id=?""",
        (target_id,),
    ).fetchone()
    if row is None:
        raise AssertionError(f"missing RepresentationTarget {target_id}")
    return row


def selector_contains(con: sqlite3.Connection, outer_id: str, inner_id: str) -> bool:
    """Minimal registered-containment proof used by the 0001 contract harness.

    The production selector registry owns full kind-specific containment. This proof exercises
    the generic identity case and `whole:v1`, which is enough to prove that SQL stores both exact
    targets while core validation, rather than FK shape or arbitrary JSON, owns containment.
    """
    if outer_id == inner_id:
        return True
    outer_rep, outer_kind, outer_version, _outer_payload, outer_availability = _target_row(con, outer_id)
    inner_rep, _inner_kind, _inner_version, _inner_payload, inner_availability = _target_row(con, inner_id)
    if outer_availability != "available" or inner_availability != "available":
        return False
    return outer_rep == inner_rep and (outer_kind, outer_version) == ("whole", "v1")


def derivation_contract_violations(con: sqlite3.Connection) -> list[tuple[str, str]]:
    violations: list[tuple[str, str]] = []
    for run_id, program_text, program_sha in con.execute(
        "SELECT id,program_text,program_sha256 FROM derivation_runs"
    ):
        if hashlib.sha256(program_text.encode("utf-8")).hexdigest() != program_sha:
            violations.append(("program_identity_mismatch", run_id))
    for run_id, outcome, result_count in con.execute(
        """SELECT r.id,r.outcome,count(d.id)
           FROM derivation_runs r LEFT JOIN derivation_results d ON d.derivation_run_id=r.id
           GROUP BY r.id,r.outcome"""
    ):
        expected = 1 if outcome == "success" else 0
        if result_count != expected:
            violations.append(("run_result_cardinality", run_id))

    for result_id, inline_payload, archive_object_id, content_sha, byte_size in con.execute(
        """SELECT id,inline_payload_json,archive_object_id,content_sha256,byte_size
           FROM derivation_results WHERE availability='available'"""
    ):
        if inline_payload is not None:
            payload = inline_payload.encode("utf-8")
            if hashlib.sha256(payload).hexdigest() != content_sha or len(payload) != byte_size:
                violations.append(("result_serialization_identity_mismatch", result_id))
        else:
            archive = con.execute(
                "SELECT availability,content_sha256,byte_size FROM archive_objects WHERE id=?",
                (archive_object_id,),
            ).fetchone()
            if archive is None or archive[0] != "available":
                violations.append(("result_archive_unavailable", result_id))
            elif archive[1] != content_sha or archive[2] != byte_size:
                violations.append(("result_serialization_identity_mismatch", result_id))

    for target_id, lineage_state, availability, result_availability in con.execute(
        """SELECT t.id,t.lineage_state,t.availability,r.availability
           FROM derivation_result_targets t
           JOIN derivation_results r ON r.id=t.derivation_result_id"""
    ):
        count = con.execute(
            "SELECT count(*) FROM derivation_result_lineage WHERE derivation_result_target_id=?",
            (target_id,),
        ).fetchone()[0]
        if availability == "available" and result_availability != "available":
            violations.append(("target_result_unavailable", target_id))
        if availability == "available" and lineage_state in {"exact", "partial"} and count == 0:
            violations.append(("missing_source_lineage", target_id))
        if lineage_state in {"unavailable", "none"} and count != 0:
            violations.append(("forbidden_source_lineage", target_id))

    for target_id, run_id, input_ordinal, source_target_id in con.execute(
        """SELECT derivation_result_target_id,derivation_run_id,input_ordinal,representation_target_id
           FROM derivation_result_lineage"""
    ):
        input_target_id = con.execute(
            """SELECT representation_target_id FROM derivation_run_inputs
               WHERE derivation_run_id=? AND ordinal=?""",
            (run_id, input_ordinal),
        ).fetchone()[0]
        if not selector_contains(con, input_target_id, source_target_id):
            violations.append(("lineage_outside_input_scope", target_id))
    return violations


def verification_contract_violations(con: sqlite3.Connection) -> list[tuple[str, str]]:
    violations: list[tuple[str, str]] = []
    for run_id, claim_revision_id, proposition in con.execute(
        "SELECT id,claim_revision_id,proposition_text FROM verification_runs"
    ):
        if claim_revision_id is not None:
            text = con.execute(
                "SELECT text FROM claim_revisions WHERE id=?", (claim_revision_id,)
            ).fetchone()[0]
            if proposition != text:
                violations.append(("claim_proposition_mismatch", run_id))

        scopes = con.execute(
            """SELECT ordinal,representation_id,representation_target_id
               FROM verification_scope_targets WHERE verification_run_id=? ORDER BY ordinal""",
            (run_id,),
        ).fetchall()
        if not scopes:
            violations.append(("empty_verification_scope", run_id))

        # Each scope Representation comes from a Source whose declared authority is explicit.
        authority_sources = {
            row[0]
            for row in con.execute(
                """SELECT sas.source_id
                   FROM verification_authority_scopes vas
                   JOIN source_authority_scopes sas ON sas.id=vas.source_authority_scope_id
                   WHERE vas.verification_run_id=?""",
                (run_id,),
            )
        }
        for _ordinal, representation_id, target_id in scopes:
            available = con.execute(
                "SELECT availability FROM representation_targets WHERE id=?", (target_id,)
            ).fetchone()[0]
            if available != "available":
                violations.append(("purged_verification_scope", run_id))
            source_id = con.execute(
                """SELECT a.source_id
                   FROM representations r
                   JOIN acquisition_artifacts aa ON aa.artifact_id=r.artifact_id
                   JOIN acquisitions a ON a.id=aa.acquisition_id
                   WHERE r.id=?""",
                (representation_id,),
            ).fetchone()
            if source_id is not None and source_id[0] not in authority_sources:
                violations.append(("missing_source_authority", run_id))

        # Derivation work may not use a terrain broader/different from the declared scope.
        for step_ordinal, derivation_run_id, use_state, result_target_id in con.execute(
            """SELECT ordinal,derivation_run_id,use_state,derivation_result_target_id
               FROM verification_derivation_steps WHERE verification_run_id=?""",
            (run_id,),
        ):
            for representation_id, input_target_id in con.execute(
                """SELECT representation_id,representation_target_id
                   FROM derivation_run_inputs WHERE derivation_run_id=?""",
                (derivation_run_id,),
            ):
                compatible = any(
                    scope_rep == representation_id and selector_contains(con, scope_target, input_target_id)
                    for _scope_ordinal, scope_rep, scope_target in scopes
                )
                if not compatible:
                    violations.append(("derivation_outside_verification_scope", f"{run_id}:{step_ordinal}"))
            if use_state == "consumed":
                row = con.execute(
                    """SELECT t.availability,r.availability
                       FROM derivation_result_targets t
                       JOIN derivation_results r ON r.id=t.derivation_result_id
                       WHERE t.id=?""",
                    (result_target_id,),
                ).fetchone()
                if row != ("available", "available"):
                    violations.append(("consumed_result_unavailable", f"{run_id}:{step_ordinal}"))

        for ordinal, scope_ordinal, evidence_target_id in con.execute(
            """SELECT ordinal,scope_ordinal,representation_target_id
               FROM verification_evidence_items WHERE verification_run_id=?""",
            (run_id,),
        ):
            scope_target_id = con.execute(
                """SELECT representation_target_id FROM verification_scope_targets
                   WHERE verification_run_id=? AND ordinal=?""",
                (run_id, scope_ordinal),
            ).fetchone()[0]
            if not selector_contains(con, scope_target_id, evidence_target_id):
                violations.append(("evidence_outside_verification_scope", f"{run_id}:{ordinal}"))
    return violations


def derived_claim_evidence_violations(con: sqlite3.Connection) -> list[tuple[str, str]]:
    violations: list[tuple[str, str]] = []
    for claim_revision_id, origin_target_id in con.execute(
        """SELECT id,derivation_result_target_id FROM claim_revisions
           WHERE claim_kind='derived_inference'"""
    ):
        target_state = con.execute(
            """SELECT t.availability,r.availability
               FROM derivation_result_targets t
               JOIN derivation_results r ON r.id=t.derivation_result_id
               WHERE t.id=?""",
            (origin_target_id,),
        ).fetchone()
        if target_state != ("available", "available"):
            violations.append(("derived_origin_unavailable", claim_revision_id))
            continue
        lineage_targets = [
            row[0]
            for row in con.execute(
                """SELECT representation_target_id FROM derivation_result_lineage
                   WHERE derivation_result_target_id=?""",
                (origin_target_id,),
            )
        ]
        for evidence_id, evidence_target_id in con.execute(
            """SELECT e.id,e.representation_target_id FROM evidence_links e
               WHERE e.claim_revision_id=? AND e.relation='supports' AND e.lifecycle='active'
                 AND NOT EXISTS (
                   SELECT 1 FROM evidence_links s WHERE s.supersedes_evidence_link_id=e.id
                 )""",
            (claim_revision_id,),
        ):
            if not any(selector_contains(con, evidence_target_id, lineage_id) for lineage_id in lineage_targets):
                violations.append(("derived_support_not_in_lineage", evidence_id))
    return violations


def assessment_contract_violations(con: sqlite3.Connection) -> list[tuple[str, str]]:
    violations: list[tuple[str, str]] = []
    for child_id, parent_policy, child_policy in con.execute(
        """SELECT c.id,p.policy_key,c.policy_key
           FROM assessments c JOIN assessments p ON p.id=c.supersedes_assessment_id
           WHERE c.supersedes_assessment_id IS NOT NULL"""
    ):
        if (parent_policy is not None or child_policy is not None) and parent_policy != child_policy:
            violations.append(("assessment_policy_lineage_jump", child_id))
    for assessment_id, outcome in con.execute(
        """SELECT a.id,v.outcome FROM assessments a
           JOIN verification_runs v ON v.id=a.verification_run_id"""
    ):
        if outcome != "completed":
            violations.append(("assessment_failed_verification_basis", assessment_id))
    return violations


def assert_new_execution_graph_clean(con: sqlite3.Connection) -> None:
    assert derivation_contract_violations(con) == [], derivation_contract_violations(con)
    assert verification_contract_violations(con) == [], verification_contract_violations(con)
    assert derived_claim_evidence_violations(con) == [], derived_claim_evidence_violations(con)
    assert assessment_contract_violations(con) == [], assessment_contract_violations(con)


def main() -> None:
    ddl_text = DDL.read_text()
    assert "json_valid(" not in ddl_text.lower(), "0001 must not require SQLite JSON SQL functions"
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        con = sqlite3.connect(tmp.name)
        con.executescript(ddl_text)
        con.execute("PRAGMA foreign_keys=ON")

        # 1. Physical byte identity is independent from logical capture custody.
        with con:
            con.execute("INSERT INTO sources VALUES (?,?,?,?,?)", ("src", "web", "Source", 1, T))
            con.execute("INSERT INTO source_locators VALUES (?,?,?,?,?)", ("loc", "src", "https://example.invalid/x.pdf", "url", T))
            con.execute("INSERT INTO sources VALUES (?,?,?,?,?)", ("src-other", "web", "Other Source", 1, T))
            con.execute("INSERT INTO source_locators VALUES (?,?,?,?,?)", ("loc-other", "src-other", "https://other.invalid/x.pdf", "url", T))
            con.execute("INSERT INTO source_authority_scopes VALUES (?,?,?,?,?,?,?)", ("sas-src", "src", "formal_record", None, None, None, T))
            con.execute("INSERT INTO source_authority_scopes VALUES (?,?,?,?,?,?,?)", ("sas-other", "src-other", "formal_record", None, None, None, T))
            for i, day in ((1, "01"), (2, "08")):
                con.execute("INSERT INTO acquisitions VALUES (?,?,?,?,?,?,?,?,?,?)", (f"acq{i}", "src", "loc", f"2026-08-{day}T10:00:00Z", "success", 200, "proof", "1", None, T))
            con.execute("INSERT INTO archive_objects VALUES (?,?,?,?,?,?,?)", ("aobA", H_A, 3, f"sha256/{H_A}", "available", T, None))
            con.execute("INSERT INTO archive_objects VALUES (?,?,?,?,?,?,?)", ("aobTable", H_B, 9, f"sha256/{H_B}", "available", T, None))
            for i in (1, 2):
                con.execute("INSERT INTO artifacts VALUES (?,?,?,?,?,?,?)", (f"art{i}", "aobA", "application/pdf", "verified", "available", T, None))
                con.execute("INSERT INTO acquisition_artifacts VALUES (?,?,?,?,?)", (f"art{i}", f"acq{i}", "primary", "x.pdf", "https://example.invalid/x.pdf"))
        assert con.execute("SELECT count(*) FROM artifacts WHERE archive_object_id='aobA'").fetchone()[0] == 2
        # A second isolated repeated-byte pair is reserved for shared-reference purge proof.
        with con:
            con.execute("INSERT INTO archive_objects VALUES (?,?,?,?,?,?,?)", ("aobShared", H_C, 12, f"sha256/{H_C}", "available", T, None))
            for i in (1, 2):
                con.execute("INSERT INTO artifacts VALUES (?,?,?,?,?,?,?)", (f"artShare{i}", "aobShared", "application/pdf", "verified", "available", T, None))
                con.execute("INSERT INTO acquisition_artifacts VALUES (?,?,?,?,?)", (f"artShare{i}", f"acq{i}", "attachment", f"shared{i}.pdf", "https://example.invalid/shared.pdf"))
                con.execute("INSERT INTO representations VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (f"repShare{i}", f"artShare{i}", None, None, "original", "application/pdf", None, None, None, "available", T, None))
        must_fail(con, "INSERT INTO acquisition_artifacts VALUES (?,?,?,?,?)", ("art1", "acq2", "primary", None, None))
        must_fail(con, "INSERT INTO acquisitions VALUES (?,?,?,?,?,?,?,?,?,?)", ("acq-cross", "src", "loc-other", T, "failed", None, "proof", "1", "wrong-source-locator", T))
        must_fail(con, "INSERT INTO acquisitions VALUES (?,?,?,?,?,?,?,?,?,?)", ("acq-bad-http", "src", "loc", T, "failed", 99, "proof", "1", "bad-http-domain", T))

        # Processing provenance is durable for any non-human generated semantic/derived record.
        with con:
            con.execute(
                "INSERT INTO process_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("pr", "proof", "critical-review-harness", "1", "local_deterministic", None, None, None, T, T, "success", None, T),
            )

        # 2. Purged/archive availability contracts do not permit fake available bytes.
        must_fail(con, "INSERT INTO archive_objects VALUES (?,?,?,?,?,?,?)", ("bad-aob", None, None, None, "available", T, None))
        must_fail(con, "INSERT INTO archive_objects VALUES (?,?,?,?,?,?,?)", ("bad-digest", "not-a-sha256", 4, "sha256/bad", "available", T, None))
        must_fail(con, "INSERT INTO archive_objects VALUES (?,?,?,?,?,?,?)", ("bad-purged-storage", H_D, 4, f"sha256/{H_D}", "purged", T, T))
        with con:
            # Tombstones may retain a digest for audit without reserving those bytes forever.
            con.execute("INSERT INTO archive_objects VALUES (?,?,?,?,?,?,?)", ("aob-old-ddd", H_D, 4, None, "purged", T, T))
            con.execute("INSERT INTO archive_objects VALUES (?,?,?,?,?,?,?)", ("aob-new-ddd", H_D, 4, f"sha256/{H_D}", "available", T, None))
        assert con.execute("SELECT availability FROM archive_objects WHERE content_sha256=? ORDER BY id", (H_D,)).fetchall() == [("available",), ("purged",)]
        must_fail(con, "INSERT INTO artifacts VALUES (?,?,?,?,?,?,?)", ("bad-art", None, None, "verified", "available", T, None))

        # 3. Representation byte authority and exact-target ownership are unambiguous.
        with con:
            # Original Representations inherit physical bytes through Artifact; they never duplicate the pointer.
            con.execute("INSERT INTO representations VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("rep1", "art1", None, None, "original", "application/pdf", None, None, None, "available", T, None))
            con.execute("INSERT INTO representations VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("rep2", "art2", None, None, "original", "application/pdf", None, None, None, "available", T, None))
            con.execute("INSERT INTO representation_targets VALUES (?,?,?,?,?,?,?,?,?)", ("t1", "rep1", "pdf_page_quote", "v1", '{"page_ordinal":1,"exact":"x"}', None, "available", T, None))
            con.execute("INSERT INTO representation_targets VALUES (?,?,?,?,?,?,?,?,?)", ("t-unattempted", "rep1", "pdf_page_quote", "v1", '{"page_ordinal":2,"exact":"y"}', None, "available", T, None))
        # WORKBENCH-001: terminal execution provenance is distinct from exact input scope,
        # typed quality evidence and policy decisions.
        with con:
            con.execute("INSERT INTO process_run_inputs VALUES (?,?,?,?)", ("pr", 0, "rep1", "t1"))
            con.execute(
                "INSERT INTO quality_evidence VALUES (?,?,?,?,?,?,?,?,?,?)",
                ("qe1", "pr", 0, "rep1", "t1", "native.page_text_present", "v1", "true", None, T),
            )
            con.execute(
                "INSERT INTO quality_decisions VALUES (?,?,?,?,?,?,?,?,?,?)",
                ("qd1", "pr", "rep1", "t1", "accept", "reference_document_processing", "v1", "native_text_present", None, T),
            )
            con.execute(
                "INSERT INTO process_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("pr-cloud", "visual_transcribe", "codex-proof", "1", "subscription_agent", None, "openai", "proof-model", T, T, "success", None, T),
            )
            con.execute(
                "INSERT INTO process_run_egress VALUES (?,?,?,?,?,?,?)",
                ("pr-cloud", 123, "public_civic", "operator_enabled", "e" * 64, "codex_cli", T),
            )
            con.execute(
                "INSERT INTO process_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("pr-scope", "proof", "scope-proof", "1", "local_deterministic", None, None, None, T, T, "failed", "scope_failed", T),
            )
        must_fail(con, "INSERT INTO process_run_inputs VALUES (?,?,?,?)", ("pr-scope", 0, "rep2", "t1"))
        must_fail(
            con,
            "INSERT INTO quality_decisions VALUES (?,?,?,?,?,?,?,?,?,?)",
            ("qd-bad", "pr", "rep1", "t1", "escalate", "reference_document_processing", "v1", "needs_ocr", None, T),
        )
        # Quality evidence/decisions must refer to a target that was actually an input of this ProcessRun.
        must_fail(
            con,
            "INSERT INTO quality_evidence VALUES (?,?,?,?,?,?,?,?,?,?)",
            ("qe-unattempted", "pr", 1, "rep1", "t-unattempted", "native.page_text_present", "v1", "true", None, T),
        )
        must_fail(
            con,
            "INSERT INTO quality_decisions VALUES (?,?,?,?,?,?,?,?,?,?)",
            ("qd-unattempted", "pr", "rep1", "t-unattempted", "accept", "reference_document_processing", "v1", "bad_scope", None, T),
        )
        must_fail(
            con,
            "INSERT INTO quality_evidence VALUES (?,?,?,?,?,?,?,?,?,?)",
            ("qe-duplicate-signal", "pr", 1, "rep1", "t1", "native.page_text_present", "v1", "false", None, T),
        )
        must_fail(
            con,
            "INSERT INTO process_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("pr-bad-success", "proof", "proof", "1", "local_deterministic", None, None, None, T, T, "success", "should_be_null", T),
        )
        must_fail(
            con,
            "INSERT INTO process_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("pr-bad-failure", "proof", "proof", "1", "local_deterministic", None, None, None, T, T, "failed", None, T),
        )
        must_fail(
            con,
            "INSERT INTO process_run_egress VALUES (?,?,?,?,?,?,?)",
            ("pr", 1, "public_civic", "operator_enabled", "bad-hash", None, T),
        )
        must_fail(
            con,
            "INSERT INTO process_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("pr-bad-config", "proof", "proof", "1", "local_deterministic", "bad-hash", None, None, T, T, "success", None, T),
        )
        must_fail(
            con,
            "INSERT INTO process_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("pr-half-model", "proof", "proof", "1", "subscription_agent", None, "openai", None, T, T, "success", None, T),
        )
        # Egress-capable runs may fail during local preparation before any source bytes leave
        # the host; zero is therefore a valid actual byte count with policy provenance intact.
        with con:
            con.execute(
                "INSERT INTO process_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("pr-cloud-zero", "visual_transcribe", "codex-proof", "1", "subscription_agent", None, "openai", "proof-model", T, T, "failed", "pre_egress_failure", T),
            )
            con.execute(
                "INSERT INTO process_run_egress VALUES (?,?,?,?,?,?,?)",
                ("pr-cloud-zero", 0, "public_civic", "operator_enabled", "e" * 64, "codex_cli", T),
            )
        must_fail(
            con,
            "INSERT INTO process_run_egress VALUES (?,?,?,?,?,?,?)",
            ("pr-cloud-zero", -1, "public_civic", "operator_enabled", "e" * 64, "codex_cli", T),
        )

        must_fail(con, "INSERT INTO representations VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("rep-original-own-bytes", "art1", "aobA", None, "original", "application/pdf", None, None, None, "available", T, None))
        must_fail(con, "INSERT INTO representations VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("rep-original-second", "art1", None, None, "original", "application/pdf", None, None, None, "available", T, None))
        must_fail(con, "INSERT INTO representations VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("rep-orphan", None, None, None, "original", "application/pdf", None, None, None, "available", T, None))
        must_fail(con, "INSERT INTO representations VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("rep-derived-no-parent", "art1", "aobTable", None, "table", "text/csv", "es", "utf-8", "pr", "available", T, None))
        must_fail(con, "INSERT INTO representations VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("rep-derived-no-process", "art1", "aobTable", "rep1", "table", "text/csv", "es", "utf-8", None, "available", T, None))
        must_fail(con, "INSERT INTO representations VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("rep-cross-parent", "art2", "aobTable", "rep1", "extracted_text", "text/plain", "es", "utf-8", "pr", "available", T, None))
        with con:
            con.execute("INSERT INTO entities VALUES (?,?,?,?)", ("org", "organization", "Municipalidad", T))
            con.execute("INSERT INTO civic_documents VALUES (?,?)", ("doc", T))
            con.execute("INSERT INTO civic_document_revisions VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("doc1", "doc", 1, None, "Acta", "org", "2026-08-01", "es", "normal", "human", None, T))
            con.execute("INSERT INTO document_representations VALUES (?,?,?,?,?,?,?,?,?,?,?)", ("dr1", None, "doc", "rep1", "whole", "t1", "human", None, "active", None, T))
            # AKF-003: unknown classification is a valid durable state.
            con.execute("INSERT INTO document_classifications VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ("dc-unknown", None, "doc", "mystery", "Tipo raro", "unknown", None, None, None, None, None, "human", None, "active", None, T))
            # AKF-004: one representation can contain multiple civic documents without duplicating bytes.
            con.execute("INSERT INTO representation_targets VALUES (?,?,?,?,?,?,?,?,?)", ("t2", "rep1", "pdf_page_quote", "v1", '{"page_ordinal":2,"exact":"second"}', None, "available", T, None))
            con.execute("INSERT INTO civic_documents VALUES (?,?)", ("doc2", T))
            con.execute("INSERT INTO civic_document_revisions VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("doc2-1", "doc2", 1, None, "Segundo documento", "org", "2026-08-01", "es", "normal", "human", None, T))
            con.execute("INSERT INTO document_representations VALUES (?,?,?,?,?,?,?,?,?,?,?)", ("dr2", None, "doc2", "rep1", "contained", "t2", "human", None, "active", None, T))
            # AKF-005: non-PDF/table locator remains representation-specific and typed/versioned.
            con.execute("INSERT INTO representations VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("rep-table", "art1", "aobTable", "rep1", "table", "text/csv", "es", "utf-8", "pr", "available", T, None))
            con.execute("INSERT INTO representation_targets VALUES (?,?,?,?,?,?,?,?,?)", ("t-table", "rep-table", "table_range", "v1", '{"sheet":"Presupuesto","a1_range":"B2:C3","observed_values":[[1,2],[3,4]]}', None, "available", T, None))
            # Whole targets are intentionally broad scopes; exact containment remains a core/selector-registry rule.
            con.execute("INSERT INTO representation_targets VALUES (?,?,?,?,?,?,?,?,?)", ("t-whole", "rep1", "whole", "v1", '{}', None, "available", T, None))
            con.execute("INSERT INTO representation_targets VALUES (?,?,?,?,?,?,?,?,?)", ("t-rep2-whole", "rep2", "whole", "v1", '{}', None, "available", T, None))

        # 3A. First-class analytical execution is distinct from ProcessRun and has exact result lineage.
        program = "SELECT 1 AS value"
        program_sha = hashlib.sha256(program.encode()).hexdigest()
        payload = '{"value":1}'
        payload_sha = hashlib.sha256(payload.encode()).hexdigest()
        with con:
            con.execute(
                "INSERT INTO derivation_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("drv1", "query", "proof-sql", "1", "local_deterministic", None, None, None,
                 "sqlite", sqlite3.sqlite_version, sqlite3.sqlite_source_id() if hasattr(sqlite3, "sqlite_source_id") else None,
                 "hardened-readonly", "v1", "sql", program, program_sha, T, T, "success", None, T),
            )
            con.execute("INSERT INTO derivation_run_inputs VALUES (?,?,?,?)", ("drv1", 0, "rep1", "t1"))
            con.execute(
                "INSERT INTO derivation_results VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("res1", "drv1", "success", "scalar", "canario.scalar.v1", "1", payload, None, payload_sha, len(payload.encode()), "available", T, None),
            )
            con.execute(
                "INSERT INTO derivation_result_targets VALUES (?,?,?,?,?,?,?,?,?,?)",
                ("drt1", "res1", "drv1", "result_value", "v1", '{"field":"value"}', "exact", "available", T, None),
            )
            con.execute(
                "INSERT INTO derivation_result_lineage VALUES (?,?,?,?,?,?,?)",
                ("drt1", "drv1", "exact", 0, "rep1", "t1", T),
            )
            con.execute(
                "INSERT INTO derivation_result_targets VALUES (?,?,?,?,?,?,?,?,?,?)",
                ("drt-none", "res1", "drv1", "result_meta", "v1", '{"field":"note"}', "none", "available", T, None),
            )
            # A failed attempt is durable but cannot own a result.
            con.execute(
                "INSERT INTO derivation_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("drv-fail", "query", "proof-sql", "1", "local_deterministic", None, None, None,
                 "sqlite", sqlite3.sqlite_version, None, "hardened-readonly", "v1", "sql", program, program_sha, T, T, "failed", "query_failed", T),
            )
            con.execute("INSERT INTO derivation_run_inputs VALUES (?,?,?,?)", ("drv-fail", 0, "rep1", "t1"))
            # A second successful run on another custody chain proves owner FKs cannot cross.
            con.execute(
                "INSERT INTO derivation_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("drv2", "query", "proof-sql", "1", "local_deterministic", None, None, None,
                 "sqlite", sqlite3.sqlite_version, None, "hardened-readonly", "v1", "sql", program, program_sha, T, T, "success", None, T),
            )
            con.execute("INSERT INTO derivation_run_inputs VALUES (?,?,?,?)", ("drv2", 0, "rep2", "t-rep2-whole"))
            con.execute(
                "INSERT INTO derivation_results VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("res2", "drv2", "success", "scalar", "canario.scalar.v1", "1", payload, None, payload_sha, len(payload.encode()), "available", T, None),
            )
            con.execute(
                "INSERT INTO derivation_result_targets VALUES (?,?,?,?,?,?,?,?,?,?)",
                ("drt2", "res2", "drv2", "result_value", "v1", '{"field":"value"}', "exact", "available", T, None),
            )
            con.execute(
                "INSERT INTO derivation_result_lineage VALUES (?,?,?,?,?,?,?)",
                ("drt2", "drv2", "exact", 0, "rep2", "t-rep2-whole", T),
            )
            # Same program/scope executed again is a new run identity, not silent reuse.
            con.execute(
                "INSERT INTO derivation_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("drv-rerun", "query", "proof-sql", "1", "local_deterministic", None, None, None,
                 "sqlite", sqlite3.sqlite_version, None, "hardened-readonly", "v1", "sql", program, program_sha, T, T, "success", None, T),
            )
            con.execute("INSERT INTO derivation_run_inputs VALUES (?,?,?,?)", ("drv-rerun", 0, "rep1", "t1"))
            con.execute(
                "INSERT INTO derivation_results VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("res-rerun", "drv-rerun", "success", "scalar", "canario.scalar.v1", "1", payload, None, payload_sha, len(payload.encode()), "available", T, None),
            )
            con.execute(
                "INSERT INTO derivation_result_targets VALUES (?,?,?,?,?,?,?,?,?,?)",
                ("drt-rerun", "res-rerun", "drv-rerun", "result_value", "v1", '{"field":"value"}', "exact", "available", T, None),
            )
            con.execute(
                "INSERT INTO derivation_result_lineage VALUES (?,?,?,?,?,?,?)",
                ("drt-rerun", "drv-rerun", "exact", 0, "rep1", "t1", T),
            )
            # A deliberately wider valid derivation is reserved for verification-scope adversarial proof.
            con.execute(
                "INSERT INTO derivation_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("drv-wide", "query", "proof-sql", "1", "local_deterministic", None, None, None,
                 "sqlite", sqlite3.sqlite_version, None, "hardened-readonly", "v1", "sql", program, program_sha, T, T, "success", None, T),
            )
            con.execute("INSERT INTO derivation_run_inputs VALUES (?,?,?,?)", ("drv-wide", 0, "rep1", "t-whole"))
            con.execute(
                "INSERT INTO derivation_results VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("res-wide", "drv-wide", "success", "scalar", "canario.scalar.v1", "1", payload, None, payload_sha, len(payload.encode()), "available", T, None),
            )
            con.execute(
                "INSERT INTO derivation_result_targets VALUES (?,?,?,?,?,?,?,?,?,?)",
                ("drt-wide", "res-wide", "drv-wide", "result_value", "v1", '{"field":"value"}', "exact", "available", T, None),
            )
            con.execute(
                "INSERT INTO derivation_result_lineage VALUES (?,?,?,?,?,?,?)",
                ("drt-wide", "drv-wide", "exact", 0, "rep1", "t1", T),
            )

        must_fail(con,
            "INSERT INTO derivation_results VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("res-failed", "drv-fail", "success", "scalar", "canario.scalar.v1", "1", payload, None, payload_sha, len(payload.encode()), "available", T, None),
        )
        must_fail(con,
            "INSERT INTO derivation_result_targets VALUES (?,?,?,?,?,?,?,?,?,?)",
            ("drt-cross", "res1", "drv2", "result_value", "v1", '{"field":"value"}', "exact", "available", T, None),
        )
        must_fail(con,
            "INSERT INTO derivation_result_lineage VALUES (?,?,?,?,?,?,?)",
            ("drt-none", "drv1", "exact", 0, "rep1", "t1", T),
        )
        same_program_ids = {row[0] for row in con.execute("SELECT id FROM derivation_runs WHERE program_sha256=?", (program_sha,))}
        assert {"drv1", "drv-rerun"}.issubset(same_program_ids) and "drv1" != "drv-rerun"

        # Cross-row semantic invariants that are intentionally core-validated rather than encoded as triggers.
        con.execute("SAVEPOINT missing_derivation_result")
        con.execute(
            "INSERT INTO derivation_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("drv-no-result", "query", "proof-sql", "1", "local_deterministic", None, None, None,
             "sqlite", sqlite3.sqlite_version, None, "hardened-readonly", "v1", "sql", program, program_sha, T, T, "success", None, T),
        )
        assert ("run_result_cardinality", "drv-no-result") in derivation_contract_violations(con)
        con.execute("ROLLBACK TO missing_derivation_result")
        con.execute("RELEASE missing_derivation_result")

        con.execute("SAVEPOINT bad_derivation_program_identity")
        con.execute("UPDATE derivation_runs SET program_sha256=? WHERE id='drv1'", ("f" * 64,))
        assert ("program_identity_mismatch", "drv1") in derivation_contract_violations(con)
        con.execute("ROLLBACK TO bad_derivation_program_identity")
        con.execute("RELEASE bad_derivation_program_identity")

        con.execute("SAVEPOINT bad_derivation_result_identity")
        con.execute("UPDATE derivation_results SET content_sha256=? WHERE id='res1'", ("f" * 64,))
        assert ("result_serialization_identity_mismatch", "res1") in derivation_contract_violations(con)
        con.execute("ROLLBACK TO bad_derivation_result_identity")
        con.execute("RELEASE bad_derivation_result_identity")

        con.execute("SAVEPOINT bad_derivation_lineage_scope")
        con.execute(
            "INSERT INTO derivation_result_lineage VALUES (?,?,?,?,?,?,?)",
            ("drt1", "drv1", "exact", 0, "rep1", "t2", T),
        )
        assert ("lineage_outside_input_scope", "drt1") in derivation_contract_violations(con)
        con.execute("ROLLBACK TO bad_derivation_lineage_scope")
        con.execute("RELEASE bad_derivation_lineage_scope")
        assert_new_execution_graph_clean(con)

        # Core transaction validation can detect any retained Artifact missing its one original Representation.
        assert con.execute("""
          SELECT a.id
          FROM artifacts a
          WHERE a.availability IN ('available','restricted')
            AND NOT EXISTS (
              SELECT 1 FROM representations r
              WHERE r.artifact_id=a.id AND r.kind='original' AND r.availability IN ('available','restricted')
            )
        """).fetchall() == []
        must_fail(con, "INSERT INTO document_representations VALUES (?,?,?,?,?,?,?,?,?,?,?)", ("dr-bad", None, "doc", "rep2", "whole", "t1", "human", None, "active", None, T))
        must_fail(con, "INSERT INTO civic_document_revisions VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("doc2-bad", "doc2", 2, "doc1", "Wrong cross-document correction", "org", "2026-08-02", "es", "normal", "human", None, T))
        with con:
            con.execute("INSERT INTO civic_document_revisions VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("doc1-2", "doc", 2, "doc1", "Acta corregida", "org", "2026-08-01", "es", "normal", "human", None, T))
        assert con.execute("SELECT title FROM civic_document_revisions WHERE document_id='doc' ORDER BY revision_no").fetchall() == [("Acta",), ("Acta corregida",)]

        # Identity-bearing document metadata/occurrence mappings are correctable without deleting history.
        with con:
            con.execute(
                "INSERT INTO document_identifiers VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                ("did1", None, "doc", "source-id", "ABC-123", "org", "t1", "human", None, "active", "observed identifier", T),
            )
            con.execute(
                "INSERT INTO document_identifiers VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                ("did2", "did1", "doc", "source-id", "ABC-124", "org", "t2", "human", None, "active", "corrected source identifier", T),
            )
            con.execute(
                "INSERT INTO document_classifications VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("dc-resolved", "dc-unknown", "doc", "Resolución", "Resolución administrativa", "resolucion", None, None, None, 1.0, "t1", "human", None, "active", "manual correction", T),
            )
            con.execute(
                "INSERT INTO document_representations VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                ("dr1-corrected", "dr1", "doc", "rep1", "contained", "t1", "human", None, "active", "compound-document correction", T),
            )
        must_fail(
            con,
            "INSERT INTO document_identifiers VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            ("did-branch", "did1", "doc", "source-id", "ABC-125", "org", "t1", "human", None, "active", "branch", T),
        )
        must_fail(
            con,
            "INSERT INTO document_identifiers VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            ("did-cross", "did2", "doc2", "source-id", "ABC-124", "org", "t2", "human", None, "active", "cross-document", T),
        )
        assert con.execute("""
          SELECT id,value FROM document_identifiers d
          WHERE document_id='doc' AND lifecycle='active'
            AND NOT EXISTS (SELECT 1 FROM document_identifiers s WHERE s.supersedes_document_identifier_id=d.id)
        """).fetchall() == [("did2", "ABC-124")]
        assert con.execute("""
          SELECT id,normalized_type FROM document_classifications d
          WHERE document_id='doc' AND lifecycle='active'
            AND NOT EXISTS (SELECT 1 FROM document_classifications s WHERE s.supersedes_document_classification_id=d.id)
        """).fetchall() == [("dc-resolved", "resolucion")]
        assert con.execute("""
          SELECT id,occurrence_kind FROM document_representations d
          WHERE document_id='doc' AND lifecycle='active'
            AND NOT EXISTS (SELECT 1 FROM document_representations s WHERE s.supersedes_document_representation_id=d.id)
        """).fetchall() == [("dr1-corrected", "contained")]

        # Exactly one operative classification leaf per CivicDocument; competing proposals stay candidate.
        current_classification_violations = """
          SELECT document_id
          FROM document_classifications d
          WHERE lifecycle='active'
            AND NOT EXISTS (SELECT 1 FROM document_classifications s WHERE s.supersedes_document_classification_id=d.id)
          GROUP BY document_id HAVING count(*) > 1
        """
        assert con.execute(current_classification_violations).fetchall() == []
        con.execute("SAVEPOINT ambiguous_classification")
        con.execute(
            "INSERT INTO document_classifications VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("dc-conflict", None, "doc", None, None, "informe", None, None, None, None, None, "human", None, "active", "conflicting active root", T),
        )
        assert con.execute(current_classification_violations).fetchall() == [("doc",)]
        con.execute("ROLLBACK TO ambiguous_classification")
        con.execute("RELEASE ambiguous_classification")

        # 4. Claim revision lineage cannot cross stable Claim identity.
        with con:
            con.execute("INSERT INTO claims VALUES (?,?)", ("clmA", T))
            con.execute("INSERT INTO claims VALUES (?,?)", ("clmB", T))
            con.execute("INSERT INTO claim_revisions(id,claim_id,revision_no,supersedes_revision_id,claim_kind,text,origin_kind,process_run_id,attribution_entity_id,attribution_text,temporal_start,temporal_end,sensitive,quantitative,lifecycle,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ("clmA1", "clmA", 1, None, "source_assertion", "A1", "human", None, None, None, None, None, 0, 0, "active", T))
            con.execute("INSERT INTO claim_revisions(id,claim_id,revision_no,supersedes_revision_id,claim_kind,text,origin_kind,process_run_id,attribution_entity_id,attribution_text,temporal_start,temporal_end,sensitive,quantitative,lifecycle,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ("clmB1", "clmB", 1, None, "source_assertion", "B1", "human", None, None, None, None, None, 0, 0, "active", T))
            con.execute("INSERT INTO claims VALUES (?,?)", ("clmDerived", T))
            con.execute(
                """INSERT INTO claim_revisions(
                    id,claim_id,revision_no,supersedes_revision_id,claim_kind,text,origin_kind,
                    process_run_id,derivation_result_target_id,attribution_entity_id,attribution_text,
                    temporal_start,temporal_end,sensitive,quantitative,lifecycle,created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                ("clmDerived1", "clmDerived", 1, None, "derived_inference", "The derived value is one.",
                 "human", None, "drt1", None, None, None, None, 0, 1, "active", T),
            )
            # Supporting source evidence may be broader than the exact lineage target when selector containment proves it.
            con.execute("INSERT INTO evidence_links VALUES (?,?,?,?,?,?,?,?,?,?)", ("ev-derived-support", None, "clmDerived1", "t-whole", "supports", "human", None, "active", "contains exact lineage target t1", T))
            # Independent challenge evidence need not be part of the derivation lineage.
            con.execute("INSERT INTO evidence_links VALUES (?,?,?,?,?,?,?,?,?,?)", ("ev-derived-challenge", None, "clmDerived1", "t2", "challenges", "human", None, "active", "independent challenge", T))

            # A completed verifier binds the exact Claim proposition, bounded scope, authority, consumed derivation and evidence.
            con.execute(
                "INSERT INTO verification_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("vr1", "clmDerived1", "The derived value is one.", "proof-verifier", "1", "local_deterministic",
                 None, None, None, "explicit_targets", "v1", '{"coverage":"fixture"}', T, T, "completed", None,
                 "supported", "sufficient", "proof_sufficiency", "v1", '{"adequate":true}', None, T),
            )
            con.execute("INSERT INTO verification_scope_targets VALUES (?,?,?,?)", ("vr1", 0, "rep1", "t-whole"))
            con.execute("INSERT INTO verification_authority_scopes VALUES (?,?,?)", ("vr1", 0, "sas-src"))
            con.execute("INSERT INTO verification_derivation_steps VALUES (?,?,?,?,?)", ("vr1", 0, "drv1", "consumed", "drt1"))
            con.execute("INSERT INTO verification_evidence_items VALUES (?,?,?,?,?,?)", ("vr1", 0, 0, "rep1", "t1", "supports"))

            # Epistemic insufficiency is a completed result; technical failure has no epistemic verdict.
            con.execute(
                "INSERT INTO verification_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("vr-insuff", None, "No matching record exists.", "proof-verifier", "1", "local_deterministic",
                 None, None, None, "explicit_targets", "v1", '{"coverage":"fixture"}', T, T, "completed", None,
                 "insufficient_evidence", "insufficient", "proof_sufficiency", "v1", '{"adequate":false}', "inventory_incomplete", T),
            )
            con.execute("INSERT INTO verification_scope_targets VALUES (?,?,?,?)", ("vr-insuff", 0, "rep1", "t-whole"))
            con.execute("INSERT INTO verification_authority_scopes VALUES (?,?,?)", ("vr-insuff", 0, "sas-src"))
            con.execute(
                "INSERT INTO verification_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("vr-fail", None, "A tool-dependent proposition.", "proof-verifier", "1", "local_deterministic",
                 None, None, None, "explicit_targets", "v1", '{"coverage":"fixture"}', T, T, "failed", "tool_failed",
                 None, None, None, None, None, None, T),
            )
            con.execute("INSERT INTO verification_scope_targets VALUES (?,?,?,?)", ("vr-fail", 0, "rep1", "t-whole"))
            con.execute("INSERT INTO verification_authority_scopes VALUES (?,?,?)", ("vr-fail", 0, "sas-src"))

            # Review acceptance and truth assessment are orthogonal durable facts.
            con.execute("INSERT INTO review_actions VALUES (?,?,?,?,?)", ("ra-derived", "reviewer", "strict", T, "storage/review proof"))
            con.execute("INSERT INTO claim_reviews VALUES (?,?,?,?,?,?,?)", ("cr-derived", "ra-derived", "clmDerived1", "accepted", "reviewer", "claim representation accepted", T))
            con.execute("INSERT INTO assessments VALUES (?,?,?,?,?,?,?,?,?,?,?)", ("asm-human", None, "clmDerived1", "refuted", "human", "analyst", "vr1", None, None, "review acceptance does not imply truth support", T))
            con.execute("INSERT INTO assessments VALUES (?,?,?,?,?,?,?,?,?,?,?)", ("asm-machine1", None, "clmDerived1", "supported", "machine", "policy-verifier", "vr1", "verification-promotion", "v1", "policy-based machine judgment", T))
            con.execute("INSERT INTO assessments VALUES (?,?,?,?,?,?,?,?,?,?,?)", ("asm-machine2", "asm-machine1", "clmDerived1", "supported", "machine", "policy-verifier", "vr1", "verification-promotion", "v2", "same policy lineage, newer version", T))
        # Derived analytical origin is exact and exclusive to derived_inference Claims.
        must_fail(con, """
          INSERT INTO claim_revisions(
            id,claim_id,revision_no,claim_kind,text,origin_kind,derivation_result_target_id,
            sensitive,quantitative,lifecycle,created_at
          ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, ("clm-source-with-derivation", "clmA", 99, "source_assertion", "bad analytical origin", "human", "drt1", 0, 0, "active", T))
        must_fail(con, """
          INSERT INTO claim_revisions(
            id,claim_id,revision_no,claim_kind,text,origin_kind,
            sensitive,quantitative,lifecycle,created_at
          ) VALUES (?,?,?,?,?,?,?,?,?,?)
        """, ("clm-derived-without-origin", "clmA", 99, "derived_inference", "missing origin", "human", 0, 0, "active", T))

        # Verification execution/epistemic states are closed and non-overlapping.
        must_fail(con,
            "INSERT INTO verification_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("vr-bad-failed-verdict", None, "bad", "proof-verifier", "1", "local_deterministic", None, None, None,
             "explicit_targets", "v1", '{}', T, T, "failed", "tool_failed", "supported", None, None, None, None, None, T),
        )
        must_fail(con,
            "INSERT INTO verification_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("vr-bad-insufficient", None, "bad", "proof-verifier", "1", "local_deterministic", None, None, None,
             "explicit_targets", "v1", '{}', T, T, "completed", None, "insufficient_evidence", "insufficient",
             "proof_sufficiency", "v1", '{}', None, T),
        )
        must_fail(con, "INSERT INTO verification_derivation_steps VALUES (?,?,?,?,?)", ("vr1", 1, "drv1", "attempted", "drt1"))
        must_fail(con, "INSERT INTO verification_derivation_steps VALUES (?,?,?,?,?)", ("vr1", 1, "drv2", "consumed", "drt1"))

        # Core validation catches scope expansion and proposition/evidence mismatches that should not be trigger logic.
        con.execute("SAVEPOINT verification_scope_expansion")
        con.execute(
            "INSERT INTO verification_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("vr-scope-bad", None, "scope test", "proof-verifier", "1", "local_deterministic", None, None, None,
             "explicit_targets", "v1", '{}', T, T, "completed", None, "supported", "sufficient",
             "proof_sufficiency", "v1", '{}', None, T),
        )
        con.execute("INSERT INTO verification_scope_targets VALUES (?,?,?,?)", ("vr-scope-bad", 0, "rep1", "t1"))
        con.execute("INSERT INTO verification_authority_scopes VALUES (?,?,?)", ("vr-scope-bad", 0, "sas-src"))
        con.execute("INSERT INTO verification_derivation_steps VALUES (?,?,?,?,?)", ("vr-scope-bad", 0, "drv-wide", "attempted", None))
        assert ("derivation_outside_verification_scope", "vr-scope-bad:0") in verification_contract_violations(con)
        con.execute("ROLLBACK TO verification_scope_expansion")
        con.execute("RELEASE verification_scope_expansion")

        con.execute("SAVEPOINT verification_evidence_expansion")
        con.execute(
            "INSERT INTO verification_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("vr-evidence-bad", None, "evidence test", "proof-verifier", "1", "local_deterministic", None, None, None,
             "explicit_targets", "v1", '{}', T, T, "completed", None, "supported", "sufficient",
             "proof_sufficiency", "v1", '{}', None, T),
        )
        con.execute("INSERT INTO verification_scope_targets VALUES (?,?,?,?)", ("vr-evidence-bad", 0, "rep1", "t1"))
        con.execute("INSERT INTO verification_authority_scopes VALUES (?,?,?)", ("vr-evidence-bad", 0, "sas-src"))
        con.execute("INSERT INTO verification_evidence_items VALUES (?,?,?,?,?,?)", ("vr-evidence-bad", 0, 0, "rep1", "t2", "supports"))
        assert ("evidence_outside_verification_scope", "vr-evidence-bad:0") in verification_contract_violations(con)
        con.execute("ROLLBACK TO verification_evidence_expansion")
        con.execute("RELEASE verification_evidence_expansion")

        con.execute("SAVEPOINT verification_claim_mismatch")
        con.execute(
            "INSERT INTO verification_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("vr-claim-bad", "clmDerived1", "different proposition", "proof-verifier", "1", "local_deterministic", None, None, None,
             "explicit_targets", "v1", '{}', T, T, "completed", None, "supported", "sufficient",
             "proof_sufficiency", "v1", '{}', None, T),
        )
        con.execute("INSERT INTO verification_scope_targets VALUES (?,?,?,?)", ("vr-claim-bad", 0, "rep1", "t-whole"))
        con.execute("INSERT INTO verification_authority_scopes VALUES (?,?,?)", ("vr-claim-bad", 0, "sas-src"))
        assert ("claim_proposition_mismatch", "vr-claim-bad") in verification_contract_violations(con)
        con.execute("ROLLBACK TO verification_claim_mismatch")
        con.execute("RELEASE verification_claim_mismatch")

        con.execute("SAVEPOINT verification_missing_authority")
        con.execute(
            "INSERT INTO verification_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("vr-authority-bad", None, "authority test", "proof-verifier", "1", "local_deterministic", None, None, None,
             "explicit_targets", "v1", '{}', T, T, "completed", None, "supported", "sufficient",
             "proof_sufficiency", "v1", '{}', None, T),
        )
        con.execute("INSERT INTO verification_scope_targets VALUES (?,?,?,?)", ("vr-authority-bad", 0, "rep1", "t-whole"))
        assert ("missing_source_authority", "vr-authority-bad") in verification_contract_violations(con)
        con.execute("ROLLBACK TO verification_missing_authority")
        con.execute("RELEASE verification_missing_authority")

        # Claim EvidenceLinks remain source evidence and must trace to the selected derivation target for supports.
        con.execute("SAVEPOINT derived_bad_support")
        con.execute("INSERT INTO evidence_links VALUES (?,?,?,?,?,?,?,?,?,?)", ("ev-derived-bad", None, "clmDerived1", "t2", "supports", "human", None, "active", "not in derivation lineage", T))
        assert ("derived_support_not_in_lineage", "ev-derived-bad") in derived_claim_evidence_violations(con)
        con.execute("ROLLBACK TO derived_bad_support")
        con.execute("RELEASE derived_bad_support")

        # Assessment basis is same-Claim, machine/rule promotion requires policy, and policy lineage cannot jump.
        must_fail(con, "INSERT INTO assessments VALUES (?,?,?,?,?,?,?,?,?,?,?)", ("asm-cross-claim", None, "clmB1", "supported", "human", "analyst", "vr1", None, None, None, T))
        must_fail(con, "INSERT INTO assessments VALUES (?,?,?,?,?,?,?,?,?,?,?)", ("asm-machine-no-policy", None, "clmDerived1", "supported", "machine", "policy-verifier", "vr1", None, None, None, T))
        must_fail(con, "INSERT INTO assessments VALUES (?,?,?,?,?,?,?,?,?,?,?)", ("asm-machine-no-verification", None, "clmDerived1", "supported", "machine", "policy-verifier", None, "verification-promotion", "v1", None, T))
        with con:
            con.execute("INSERT INTO assessments VALUES (?,?,?,?,?,?,?,?,?,?,?)", ("asm-policy-parent", None, "clmDerived1", "supported", "machine", "policy-jump-proof", "vr1", "policy-a", "v1", None, T))
        con.execute("SAVEPOINT assessment_policy_jump")
        con.execute("INSERT INTO assessments VALUES (?,?,?,?,?,?,?,?,?,?,?)", ("asm-policy-child-bad", "asm-policy-parent", "clmDerived1", "supported", "machine", "policy-jump-proof", "vr1", "policy-b", "v1", None, T))
        assert ("assessment_policy_lineage_jump", "asm-policy-child-bad") in assessment_contract_violations(con)
        con.execute("ROLLBACK TO assessment_policy_jump")
        con.execute("RELEASE assessment_policy_jump")

        assert con.execute("SELECT decision FROM claim_reviews WHERE claim_revision_id='clmDerived1'").fetchone() == ("accepted",)
        assert con.execute("SELECT judgment FROM assessments WHERE id='asm-human'").fetchone() == ("refuted",)
        assert_new_execution_graph_clean(con)

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
            con.execute("INSERT INTO evidence_links VALUES (?,?,?,?,?,?,?,?,?,?)", ("evA", None, "clmA1", "t1", "supports", "human", None, "active", None, T))
            # A locator/relationship correction supersedes the old EvidenceLink rather than deleting it.
            con.execute("INSERT INTO evidence_links VALUES (?,?,?,?,?,?,?,?,?,?)", ("evA2", "evA", "clmA1", "t2", "supports", "human", None, "active", "corrected exact target", T))
        must_fail(
            con,
            "INSERT INTO evidence_links VALUES (?,?,?,?,?,?,?,?,?,?)",
            ("evA-branch", "evA", "clmA1", "t1", "supports", "human", None, "active", "branch", T),
        )
        must_fail(
            con,
            "INSERT INTO evidence_links VALUES (?,?,?,?,?,?,?,?,?,?)",
            ("evA-cross", "evA2", "clmB1", "t2", "supports", "human", None, "active", "cross-claim correction", T),
        )
        current_support = con.execute("""
          SELECT e.id,e.representation_target_id
          FROM evidence_links e
          JOIN representation_targets t ON t.id=e.representation_target_id
          WHERE e.claim_revision_id='clmA1' AND e.relation='supports' AND e.lifecycle='active'
            AND t.availability='available'
            AND NOT EXISTS (SELECT 1 FROM evidence_links s WHERE s.supersedes_evidence_link_id=e.id)
        """).fetchall()
        assert current_support == [("evA2", "t2")], current_support
        # Revision history is a chain: no second root and no branching successor.
        must_fail(con, """
          INSERT INTO claim_revisions(
            id,claim_id,revision_no,supersedes_revision_id,claim_kind,text,origin_kind,
            sensitive,quantitative,lifecycle,created_at
          ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, ("clmA3-root", "clmA", 3, None, "source_assertion", "bad second root", "human", 0, 0, "active", T))
        must_fail(con, """
          INSERT INTO claim_revisions(
            id,claim_id,revision_no,supersedes_revision_id,claim_kind,text,origin_kind,
            sensitive,quantitative,lifecycle,created_at
          ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, ("clmA3-branch", "clmA", 3, "clmA1", "source_assertion", "bad branch", "human", 0, 0, "active", T))

        # 5. Direct claim/entity anchors are valid without pretending they came from a mention.
        with con:
            con.execute("INSERT INTO entities VALUES (?,?,?,?)", ("entX", "place", "X", T))
            con.execute("INSERT INTO entities VALUES (?,?,?,?)", ("entY", "place", "Y", T))
            con.execute("INSERT INTO entity_mentions VALUES (?,?,?,?,?,?,?)", ("mA", "t1", "clmA1", "X", "human", None, T))
            con.execute(
                "INSERT INTO claim_entity_links VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                ("cel-direct", None, "clmA1", "entX", None, None, None, "human", None, "active", "direct anchor", T),
            )
            con.execute(
                "INSERT INTO entity_names VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("en1", None, "entX", "Lugar X preliminar", "alias", "t1", None, None, "human", None, "active", "observed alias", T),
            )
            con.execute(
                "INSERT INTO entity_names VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("en2", "en1", "entX", "Lugar X", "official", "t2", None, None, "human", None, "active", "corrected name", T),
            )
            con.execute(
                "INSERT INTO entity_identifiers VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                ("ei1", None, "entX", "registry", "X-001", "org", "t1", "human", None, "active", "observed identifier", T),
            )
            con.execute(
                "INSERT INTO entity_identifiers VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                ("ei2", "ei1", "entX", "registry", "X-002", "org", "t2", "human", None, "active", "corrected identifier", T),
            )
        must_fail(
            con,
            "INSERT INTO entity_names VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("en-cross", "en2", "entY", "Y", "official", "t2", None, None, "human", None, "active", "cross-entity", T),
        )
        must_fail(
            con,
            "INSERT INTO entity_identifiers VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            ("ei-cross", "ei2", "entY", "registry", "Y-001", "org", "t2", "human", None, "active", "cross-entity", T),
        )
        assert con.execute("""
          SELECT id,name FROM entity_names n WHERE entity_id='entX' AND lifecycle='active'
            AND NOT EXISTS (SELECT 1 FROM entity_names s WHERE s.supersedes_entity_name_id=n.id)
        """).fetchall() == [("en2", "Lugar X")]
        assert con.execute("""
          SELECT id,value FROM entity_identifiers i WHERE entity_id='entX' AND lifecycle='active'
            AND NOT EXISTS (SELECT 1 FROM entity_identifiers s WHERE s.supersedes_entity_identifier_id=i.id)
        """).fetchall() == [("ei2", "X-002")]

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
            # Source identifiers are themselves attributable/correctable identity evidence.
            con.execute(
                "INSERT INTO entity_identifiers VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                ("pid-old", None, "proj-old", "contract", "C-77", "org", "t1", "human", None, "active", "official contract id", T),
            )
            con.execute(
                "INSERT INTO entity_identifiers VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                ("pid-alias", None, "proj-alias", "contract", "C-77", "org", "t2", "human", None, "active", "official contract id", T),
            )
            con.execute("INSERT INTO entity_reconciliations VALUES (?,?,?,?,?,?,?,?,?)", ("rec-merge-cand", None, "merge", "machine", "pr", None, "candidate match", "candidate", T))
            con.execute("INSERT INTO entity_reconciliation_inputs VALUES (?,?)", ("rec-merge-cand", "proj-old"))
            con.execute("INSERT INTO entity_reconciliation_inputs VALUES (?,?)", ("rec-merge-cand", "proj-alias"))
            con.execute("INSERT INTO entity_reconciliation_outputs VALUES (?,?)", ("rec-merge-cand", "proj-current"))
            con.execute("INSERT INTO entity_reconciliations VALUES (?,?,?,?,?,?,?,?,?)", ("rec-merge", "rec-merge-cand", "merge", "human", None, "reviewer", "same official identifier", "active", T))
            con.execute("INSERT INTO entity_reconciliation_inputs VALUES (?,?)", ("rec-merge", "proj-old"))
            con.execute("INSERT INTO entity_reconciliation_inputs VALUES (?,?)", ("rec-merge", "proj-alias"))
            con.execute("INSERT INTO entity_reconciliation_outputs VALUES (?,?)", ("rec-merge", "proj-current"))
            con.execute("INSERT INTO entity_reconciliation_basis_identifiers VALUES (?,?)", ("rec-merge", "pid-old"))
            con.execute("INSERT INTO entity_reconciliation_basis_identifiers VALUES (?,?)", ("rec-merge", "pid-alias"))
            con.execute("INSERT INTO entity_reconciliations VALUES (?,?,?,?,?,?,?,?,?)", ("rec-split", None, "split", "human", None, "reviewer", "later evidence separates identities", "active", T))
            con.execute("INSERT INTO entity_reconciliation_inputs VALUES (?,?)", ("rec-split", "proj-current"))
            con.execute("INSERT INTO entity_reconciliation_outputs VALUES (?,?)", ("rec-split", "proj-current"))
            con.execute("INSERT INTO entity_reconciliation_outputs VALUES (?,?)", ("rec-split", "proj-split"))
        assert con.execute("SELECT lifecycle FROM entity_reconciliations WHERE id='rec-merge-cand'").fetchone()[0] == "candidate"
        assert con.execute("SELECT supersedes_entity_reconciliation_id,lifecycle FROM entity_reconciliations WHERE id='rec-merge'").fetchone() == ("rec-merge-cand", "active")
        must_fail(con, "INSERT INTO entity_reconciliations VALUES (?,?,?,?,?,?,?,?,?)", ("rec-merge-branch", "rec-merge-cand", "merge", "human", None, "reviewer", "branch must not fork accepted history", "active", T))

        # An operative reconciliation cannot silently continue to rely on an identifier
        # that has since been corrected/rejected. Core validation surfaces the stale basis.
        stale_identifier_basis = """
          SELECT DISTINCT r.id
          FROM entity_reconciliations r
          JOIN entity_reconciliation_basis_identifiers b ON b.reconciliation_id=r.id
          JOIN entity_identifiers i ON i.id=b.entity_identifier_id
          WHERE r.lifecycle='active'
            AND NOT EXISTS (SELECT 1 FROM entity_reconciliations rs WHERE rs.supersedes_entity_reconciliation_id=r.id)
            AND (i.lifecycle<>'active' OR EXISTS (SELECT 1 FROM entity_identifiers s WHERE s.supersedes_entity_identifier_id=i.id))
          ORDER BY r.id
        """
        assert con.execute(stale_identifier_basis).fetchall() == []
        with con:
            con.execute(
                "INSERT INTO entity_identifiers VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                ("pid-old-correction", "pid-old", "proj-old", "contract", "C-88", "org", "t1", "human", None, "active", "source correction", T),
            )
        assert con.execute(stale_identifier_basis).fetchall() == [("rec-merge",)]
        with con:
            con.execute("INSERT INTO entity_reconciliations VALUES (?,?,?,?,?,?,?,?,?)", ("rec-merge-invalidated", "rec-merge", "merge", "human", None, "reviewer", "identifier basis changed; prior merge no longer operative", "rejected", T))
            con.execute("INSERT INTO entity_reconciliation_inputs VALUES (?,?)", ("rec-merge-invalidated", "proj-old"))
            con.execute("INSERT INTO entity_reconciliation_inputs VALUES (?,?)", ("rec-merge-invalidated", "proj-alias"))
            con.execute("INSERT INTO entity_reconciliation_outputs VALUES (?,?)", ("rec-merge-invalidated", "proj-current"))
        assert con.execute(stale_identifier_basis).fetchall() == []

        # Cross-table cardinality is a core transaction invariant: active merge >=2->1,
        # active split 1->>=2. Demonstrate that the validator detects a bad 1->1 merge.
        cardinality_violations = """
          SELECT r.id
          FROM entity_reconciliations r
          WHERE r.lifecycle='active' AND (
            (r.kind='merge' AND (
              (SELECT count(*) FROM entity_reconciliation_inputs i WHERE i.reconciliation_id=r.id) < 2
              OR (SELECT count(*) FROM entity_reconciliation_outputs o WHERE o.reconciliation_id=r.id) <> 1
            ))
            OR
            (r.kind='split' AND (
              (SELECT count(*) FROM entity_reconciliation_inputs i WHERE i.reconciliation_id=r.id) <> 1
              OR (SELECT count(*) FROM entity_reconciliation_outputs o WHERE o.reconciliation_id=r.id) < 2
            ))
          )
          ORDER BY r.id
        """
        assert con.execute(cardinality_violations).fetchall() == []
        con.execute("SAVEPOINT bad_reconciliation")
        con.execute("INSERT INTO entity_reconciliations VALUES (?,?,?,?,?,?,?,?,?)", ("rec-bad-cardinality", None, "merge", "human", None, "reviewer", "invalid 1-to-1 merge", "active", T))
        con.execute("INSERT INTO entity_reconciliation_inputs VALUES (?,?)", ("rec-bad-cardinality", "proj-old"))
        con.execute("INSERT INTO entity_reconciliation_outputs VALUES (?,?)", ("rec-bad-cardinality", "proj-current"))
        assert con.execute(cardinality_violations).fetchall() == [("rec-bad-cardinality",)]
        con.execute("ROLLBACK TO bad_reconciliation")
        con.execute("RELEASE bad_reconciliation")
        assert con.execute(cardinality_violations).fetchall() == []

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
            con.execute("INSERT INTO claim_relation_revisions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", ("rel1-2", "rel", 2, "rel1", "clmB1", "clmA1", "updates", "human", "source_evidence", "corrected basis target", None, "active", T))
            con.execute("INSERT INTO claim_relation_evidence_links VALUES (?,?,?,?,?)", ("rel-e2", "rel1-2", "t2", "source_basis", T))
        must_fail(con, "INSERT INTO claim_relation_revisions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", ("rel2bad", "rel2", 1, "rel1", "clmB1", "clmA2", "updates", "human", "analyst_inference", "bad cross lineage", None, "active", T))
        must_fail(con, "INSERT INTO claim_relation_revisions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", ("rel1-branch", "rel", 3, "rel1", "clmB1", "clmA1", "updates", "human", "analyst_inference", "branch", None, "candidate", T))
        assert con.execute("SELECT to_claim_revision_id FROM claim_relation_revisions WHERE id='rel1'").fetchone()[0] == "clmA1"
        current_rel = con.execute("""
          SELECT r.id, r.basis_kind, e.representation_target_id
          FROM claim_relation_revisions r
          LEFT JOIN claim_relation_evidence_links e
            ON e.claim_relation_revision_id=r.id AND e.basis_role='source_basis'
          WHERE r.claim_relation_id='rel' AND r.lifecycle='active'
            AND NOT EXISTS (
              SELECT 1 FROM claim_relation_revisions s
              WHERE s.supersedes_relation_revision_id=r.id
            )
        """).fetchall()
        assert current_rel == [("rel1-2", "source_evidence", "t2")], current_rel

        # AKF-012: evidence challenge and proposition contradiction remain separate contracts.
        with con:
            con.execute("INSERT INTO evidence_links VALUES (?,?,?,?,?,?,?,?,?,?)", ("ev-challenge", None, "clmA1", "t2", "challenges", "human", None, "active", None, T))
            con.execute("INSERT INTO claim_relations VALUES (?,?)", ("rel-contradict", T))
            con.execute("INSERT INTO claim_relation_revisions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", ("rel-contradict1", "rel-contradict", 1, None, "clmA1", "clmB1", "contradicts", "human", "analyst_inference", "incompatible propositions", None, "active", T))
        assert con.execute("SELECT relation FROM evidence_links WHERE id='ev-challenge'").fetchone()[0] == "challenges"
        assert con.execute("SELECT relation_type FROM claim_relation_revisions WHERE id='rel-contradict1'").fetchone()[0] == "contradicts"
        with con:
            con.execute("INSERT INTO claim_relations VALUES (?,?)", ("rel-reverse-symmetric", T))
        must_fail(
            con,
            "INSERT INTO claim_relation_revisions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("rel-reverse-symmetric-1", "rel-reverse-symmetric", 1, None, "clmB1", "clmA1", "contradicts", "human", "analyst_inference", "reverse duplicate orientation", None, "active", T),
        )

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
            con.execute("INSERT INTO document_identifier_reviews VALUES (?,?,?,?,?,?,?)", ("dir", "ra", "did2", "accepted", "reviewer", "correct identifier", T))
            con.execute("INSERT INTO document_classification_reviews VALUES (?,?,?,?,?,?,?)", ("dcr", "ra", "dc-resolved", "accepted", "reviewer", "correct type", T))
            con.execute("INSERT INTO document_representation_reviews VALUES (?,?,?,?,?,?,?)", ("drr", "ra", "dr1-corrected", "accepted", "reviewer", "correct occurrence", T))
            con.execute("INSERT INTO evidence_link_reviews VALUES (?,?,?,?,?,?,?)", ("evr", "ra", "evA2", "accepted", "reviewer", "locator reopened", T))
            con.execute("INSERT INTO entity_name_reviews VALUES (?,?,?,?,?,?,?)", ("enr", "ra", "en2", "accepted", "reviewer", "name verified", T))
            con.execute("INSERT INTO entity_identifier_reviews VALUES (?,?,?,?,?,?,?)", ("eir", "ra", "ei2", "accepted", "reviewer", "identifier verified", T))
            con.execute("INSERT INTO claim_entity_link_reviews VALUES (?,?,?,?,?,?,?)", ("celr", "ra", "cel-mention2", "accepted", "reviewer", "corrected anchor", T))
            con.execute("INSERT INTO claim_tag_link_reviews VALUES (?,?,?,?,?,?,?)", ("ctlr", "ra", "ctl2", "rejected", "reviewer", "wrong topic", T))
            con.execute("INSERT INTO entity_reconciliation_reviews VALUES (?,?,?,?,?,?,?)", ("err", "ra", "rec-merge", "accepted", "reviewer", None, T))
            con.execute("INSERT INTO claim_relation_reviews VALUES (?,?,?,?,?,?,?)", ("relr", "ra", "rel1-2", "accepted", "reviewer", "basis reopened", T))
        assert con.execute("SELECT count(*) FROM claim_reviews WHERE review_action_id='ra'").fetchone()[0] == 2
        assert con.execute("SELECT count(*) FROM document_identifier_reviews WHERE review_action_id='ra'").fetchone()[0] == 1
        assert con.execute("SELECT count(*) FROM document_classification_reviews WHERE review_action_id='ra'").fetchone()[0] == 1
        assert con.execute("SELECT count(*) FROM document_representation_reviews WHERE review_action_id='ra'").fetchone()[0] == 1
        assert con.execute("SELECT count(*) FROM evidence_link_reviews WHERE review_action_id='ra'").fetchone()[0] == 1
        assert con.execute("SELECT count(*) FROM entity_name_reviews WHERE review_action_id='ra'").fetchone()[0] == 1
        assert con.execute("SELECT count(*) FROM entity_identifier_reviews WHERE review_action_id='ra'").fetchone()[0] == 1
        assert con.execute("SELECT count(*) FROM claim_entity_link_reviews WHERE review_action_id='ra'").fetchone()[0] == 1
        assert con.execute("SELECT count(*) FROM claim_tag_link_reviews WHERE review_action_id='ra'").fetchone()[0] == 1
        assert con.execute("SELECT count(*) FROM entity_reconciliation_reviews WHERE review_action_id='ra'").fetchone()[0] == 1
        assert con.execute("SELECT count(*) FROM claim_relation_reviews WHERE review_action_id='ra'").fetchone()[0] == 1

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
              AND NOT EXISTS (
                SELECT 1 FROM claim_relation_revisions successor
                WHERE successor.supersedes_relation_revision_id=r.id
              )
          ) SELECT node, depth FROM walk ORDER BY depth, node
        """).fetchall()
        assert rows == [("clmC1", 0), ("clmB1", 1), ("clmA1", 2)], rows
        parallel_edges = con.execute("""
          SELECT relation_type
          FROM claim_relation_revisions
          WHERE lifecycle='active'
            AND NOT EXISTS (
              SELECT 1 FROM claim_relation_revisions successor
              WHERE successor.supersedes_relation_revision_id=claim_relation_revisions.id
            )
            AND (
              (from_claim_revision_id='clmA1' AND to_claim_revision_id='clmB1')
              OR
              (from_claim_revision_id='clmB1' AND to_claim_revision_id='clmA1')
            )
          ORDER BY relation_type
        """).fetchall()
        assert parallel_edges == [("contradicts",), ("updates",)], parallel_edges
        symmetric_from_a = con.execute("""
          SELECT CASE WHEN from_claim_revision_id=? THEN to_claim_revision_id ELSE from_claim_revision_id END
          FROM claim_relation_revisions
          WHERE lifecycle='active' AND relation_type IN ('contradicts','same_matter_as')
            AND NOT EXISTS (
              SELECT 1 FROM claim_relation_revisions successor
              WHERE successor.supersedes_relation_revision_id=claim_relation_revisions.id
            )
            AND (? IN (from_claim_revision_id,to_claim_revision_id))
        """, ("clmA1", "clmA1")).fetchall()
        assert symmetric_from_a == [("clmB1",)], symmetric_from_a
        reverse_updates = con.execute("""
          SELECT count(*) FROM claim_relation_revisions
          WHERE lifecycle='active' AND relation_type='updates'
            AND NOT EXISTS (
              SELECT 1 FROM claim_relation_revisions successor
              WHERE successor.supersedes_relation_revision_id=claim_relation_revisions.id
            )
            AND from_claim_revision_id='clmA1' AND to_claim_revision_id='clmB1'
        """).fetchone()[0]
        assert reverse_updates == 0

        # 11. Cross-table availability and shared-byte purge semantics are validated as one operation.
        availability_violations = """
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
          UNION ALL
          SELECT 'target/representation', t.id
          FROM representation_targets t JOIN representations r ON r.id=t.representation_id
          WHERE t.availability='available' AND r.availability NOT IN ('available','restricted')
        """
        assert con.execute(availability_violations).fetchall() == []

        # SQL FKs preserve identity, while the core transaction validator preserves
        # cross-row availability: an active selector cannot point at purged evidence.
        con.execute("SAVEPOINT bad_target_parent")
        con.execute("UPDATE representations SET availability='purged',purged_at=? WHERE id='rep2'", (T,))
        con.execute(
            "INSERT INTO representation_targets VALUES (?,?,?,?,?,?,?,?,?)",
            ("target-bad-parent", "rep2", "whole", "v1", "{}", None, "available", T, None),
        )
        bad_parent_rows = set(con.execute(availability_violations).fetchall())
        assert bad_parent_rows == {
            ("target/representation", "t-rep2-whole"),
            ("target/representation", "target-bad-parent"),
        }, bad_parent_rows
        con.execute("ROLLBACK TO bad_target_parent")
        con.execute("RELEASE bad_target_parent")
        assert con.execute(availability_violations).fetchall() == []

        # A logical purge of one Artifact sharing physical bytes must not claim/delete those bytes.
        with con:
            con.execute("INSERT INTO purges VALUES (?,?,?,?,?,?,?,?)", ("purge-shared-one", "policy", "operator", "minimal_tombstone", T, T, "completed", "physical bytes retained: artShare2 still references aobShared"))
            con.execute("INSERT INTO purge_targets VALUES (?,?,?,?,?,?,?)", ("purge-shared-one", "representation", "repShare1", "detach", T, T, "completed"))
            con.execute("INSERT INTO purge_targets VALUES (?,?,?,?,?,?,?)", ("purge-shared-one", "artifact", "artShare1", "detach", T, T, "completed"))
            con.execute("UPDATE representations SET artifact_id=NULL,media_type=NULL,language=NULL,charset=NULL,availability='purged',purged_at=? WHERE id='repShare1'", (T,))
            con.execute("UPDATE artifacts SET archive_object_id=NULL,media_type=NULL,availability='purged',purged_at=? WHERE id='artShare1'", (T,))
        assert con.execute("SELECT availability FROM archive_objects WHERE id='aobShared'").fetchone()[0] == 'available'
        assert con.execute("SELECT archive_object_id,availability FROM artifacts WHERE id='artShare2'").fetchone() == ('aobShared','available')
        assert con.execute(availability_violations).fetchall() == []

        # Purging the shared ArchiveObject while a retained reference survives is detectable and forbidden by core validation.
        con.execute("SAVEPOINT bad_shared_byte_purge")
        con.execute("UPDATE archive_objects SET content_sha256=NULL,byte_size=NULL,storage_key=NULL,availability='purged',purged_at=? WHERE id='aobShared'", (T,))
        assert con.execute(availability_violations).fetchall() == [('artifact/archive', 'artShare2')]
        con.execute("ROLLBACK TO bad_shared_byte_purge")
        con.execute("RELEASE bad_shared_byte_purge")
        assert con.execute(availability_violations).fetchall() == []

        # 12. FTS is disposable/self-content and secure-delete mode is persistent.
        with con:
            con.execute("INSERT INTO claim_fts(claim_revision_id,text) VALUES (?,?)", ("clmA1", "obra junio"))
        assert con.execute("SELECT count(*) FROM claim_fts WHERE claim_fts MATCH 'junio'").fetchone()[0] == 1
        assert con.execute("SELECT v FROM claim_fts_config WHERE k='secure-delete'").fetchone()[0] == 1
        with con:
            con.execute("DELETE FROM claim_fts")
            con.execute("INSERT INTO claim_fts(claim_fts) VALUES('rebuild')")
        assert con.execute("SELECT count(*) FROM claim_fts").fetchone()[0] == 0

        # 13. Purge lifecycle state is coherent, and the manifest survives target removal semantics.
        must_fail(con, "INSERT INTO purges VALUES (?,?,?,?,?,?,?,?)", ("purge-bad-planned", "policy", "operator", "minimal_tombstone", T, T, "planned", None))
        must_fail(con, "INSERT INTO purges VALUES (?,?,?,?,?,?,?,?)", ("purge-bad-complete", "policy", "operator", "minimal_tombstone", T, None, "completed", None))
        with con:
            con.execute("INSERT INTO purges VALUES (?,?,?,?,?,?,?,?)", ("purge-lifecycle-proof", "policy", "operator", "minimal_tombstone", T, None, "planned", None))
        must_fail(con, "INSERT INTO purge_targets VALUES (?,?,?,?,?,?,?)", ("purge-lifecycle-proof", "claim", "clmA", "delete_record", T, None, "completed"))
        must_fail(con, "INSERT INTO purge_targets VALUES (?,?,?,?,?,?,?)", ("purge-lifecycle-proof", "claim", "clmA", "delete_record", T, T, None))
        purge_completion_violations = """
          SELECT p.id
          FROM purges p
          WHERE p.outcome='completed'
            AND EXISTS (
              SELECT 1 FROM purge_targets t
              WHERE t.purge_id=p.id
                AND (t.outcome IS NULL OR t.outcome='failed')
            )
          ORDER BY p.id
        """
        con.execute("SAVEPOINT bad_completed_purge")
        con.execute("UPDATE purges SET executed_at=?,outcome='completed' WHERE id='purge-lifecycle-proof'", (T,))
        con.execute("INSERT INTO purge_targets VALUES (?,?,?,?,?,?,?)", ("purge-lifecycle-proof", "claim", "clmA", "delete_record", T, None, None))
        assert con.execute(purge_completion_violations).fetchall() == [("purge-lifecycle-proof",)]
        con.execute("ROLLBACK TO bad_completed_purge")
        con.execute("RELEASE bad_completed_purge")
        assert con.execute(purge_completion_violations).fetchall() == []
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
            assert restored.execute("SELECT count(*) FROM purge_targets").fetchone()[0] == con.execute("SELECT count(*) FROM purge_targets").fetchone()[0]
            restored.close()

        assert con.execute("PRAGMA foreign_key_check").fetchall() == []
        strict_count = con.execute("SELECT count(*) FROM pragma_table_list WHERE strict=1").fetchone()[0]
        assert strict_count == 71
        fts_count = con.execute(
            "SELECT count(*) FROM pragma_table_list WHERE type='virtual' AND name IN ('claim_fts','representation_fts','document_fts')"
        ).fetchone()[0]
        assert fts_count == 3
        assert con.execute("PRAGMA application_id").fetchone()[0] == 0x414B4954
        assert con.execute("PRAGMA user_version").fetchone()[0] == 1

        print(f"MIGRATION_0001_SPEC_PROOF=PASS sqlite={sqlite3.sqlite_version} strict_tables={strict_count} fts_tables={fts_count}")
        print("critical_invariants=16/16 PASS")
        print("semantic_fixture_storage=16/16 REPRESENTABLE")
        print("sqlite_backup_snapshot=PASS (archive/clean-machine restore still separate operational gate)")
        print("target_runtime_floor=NOT_CERTIFIED_HERE (candidate requires SQLite >=3.53.4)")
        con.close()


if __name__ == "__main__":
    main()
