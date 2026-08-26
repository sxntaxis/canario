from __future__ import annotations

import sqlite3
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from canario.deposit import (
    AcquisitionObservation,
    AcquisitionWrite,
    CapturedArtifact,
    DepositWriter,
    SourceLocatorRegistration,
    SourceRegistration,
    new_id,
)
from canario.persistence import database
from canario.processors import EgressAuthorization, TargetRegistration, WorkbenchWriter
from canario.reasoning import (
    AssessmentRequest,
    DerivationDescriptor,
    DerivationExecutionResult,
    DerivationOutput,
    DerivationRequest,
    DerivationResultTargetDraft,
    DerivedClaimRequest,
    DerivedEvidenceDraft,
    ReasoningContractError,
    ReasoningHost,
    ReasoningIdentityCollision,
    ReasoningInvariantError,
    ReasoningWriter,
    ResultTargetRegistry,
    SourceLineageDraft,
    SourceMaterializerRegistry,
    VerificationDerivationStep,
    VerificationDescriptor,
    VerificationEvidenceDraft,
    VerificationExecutionResult,
    VerificationRequest,
)

NO_RUNTIME_CHECK = lambda: None
T = "2026-08-26T20:30:00.000Z"


def local_connection(path: Path) -> sqlite3.Connection:
    return database._open_writable_v1(path, NO_RUNTIME_CHECK)


class FixtureDerivationBackend:
    def __init__(self, result, *, requires_egress: bool = False):
        self._descriptor = DerivationDescriptor(
            "fixture.derivation",
            "1",
            "local_deterministic" if not requires_egress else "subscription_agent",
            "sqlite_bounded",
            "3.53.4",
            "read_only_projection",
            "1",
            frozenset({"query"}),
            frozenset({"sql"}),
            requires_egress,
            "openai" if requires_egress else None,
            "gpt-test" if requires_egress else None,
            "source-id" if not requires_egress else None,
            8,
            2_000_000,
            2_000_000,
        )
        self.result = result
        self.calls = 0

    @property
    def descriptor(self):
        return self._descriptor

    def derive(self, invocation):
        self.calls += 1
        return self.result(invocation) if callable(self.result) else self.result


class FixtureVerificationBackend:
    def __init__(self, result, *, requires_egress: bool = False):
        self._descriptor = VerificationDescriptor(
            "fixture.verifier",
            "1",
            "local_deterministic" if not requires_egress else "subscription_agent",
            requires_egress,
            "openai" if requires_egress else None,
            "gpt-test" if requires_egress else None,
            8,
            2_000_000,
        )
        self.result = result
        self.calls = 0

    @property
    def descriptor(self):
        return self._descriptor

    def verify(self, invocation):
        self.calls += 1
        return self.result(invocation) if callable(self.result) else self.result


class ReasoningRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / "canario.sqlite3"
        self.archive = self.root / "archive"
        database._ensure_schema_v1(self.db, NO_RUNTIME_CHECK)
        self.deposit = DepositWriter(self.db, self.archive, connection_factory=local_connection)
        self.workbench = WorkbenchWriter(self.db, self.archive, connection_factory=local_connection)
        self.writer = ReasoningWriter(self.db, self.archive, connection_factory=local_connection)
        self.host = ReasoningHost(self.writer)

        self.source1, self.rep1, self.whole1, self.page1, self.page2, self.sas1 = self._source_fixture(
            "Uno", b"%PDF fixture one"
        )
        self.source2, self.rep2, self.whole2, self.other_page, _page2_unused, self.sas2 = self._source_fixture(
            "Dos", b"%PDF fixture two", second_page=False
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _source_fixture(self, name: str, data: bytes, *, second_page: bool = True):
        source = SourceRegistration(new_id("src_"), "web", name, True, T)
        self.deposit.register_source(source)
        locator = SourceLocatorRegistration(
            new_id("sloc_"), source.id, f"https://example.test/{name}.pdf", "http_url", T
        )
        self.deposit.register_source_locator(locator)
        rep_id = new_id("rep_")
        artifact = CapturedArtifact(
            new_id("art_"),
            new_id("aob_"),
            rep_id,
            data,
            "primary",
            f"{name}.pdf",
            locator.locator,
            "application/pdf",
            "verified",
            "available",
            "es",
            None,
            T,
        )
        observation = AcquisitionObservation(
            new_id("acq_"), source.id, locator.id, T, "success", 200, "fixture", "1", None, T
        )
        self.deposit.record_acquisition(AcquisitionWrite(observation, (artifact,)))
        whole = self._target(rep_id, "whole", "{}")
        page1 = self._target(rep_id, "pdf_page", '{"page_ordinal":1}')
        if second_page:
            page2 = self._target(rep_id, "pdf_page", '{"page_ordinal":2}')
        else:
            page2 = None
        sas = new_id("sas_")
        con = local_connection(self.db)
        try:
            with con:
                con.execute(
                    "INSERT INTO source_authority_scopes VALUES (?,?,?,?,?,?,?)",
                    (sas, source.id, "formal_record", None, None, None, T),
                )
        finally:
            con.close()
        return source, rep_id, whole, page1, page2, sas

    def _target(self, rep_id: str, kind: str, payload: str) -> str:
        target_id = new_id("rtgt_")
        self.workbench.register_target(TargetRegistration(target_id, rep_id, kind, "v1", payload, T))
        return target_id

    def _derive(self):
        request = DerivationRequest((self.whole1,), "query", "sql", "SELECT amount FROM projection")
        backend = FixtureDerivationBackend(
            DerivationExecutionResult(
                "success",
                DerivationOutput(
                    "scalar",
                    "canario.scalar",
                    "v1",
                    (
                        DerivationResultTargetDraft(
                            "scalar",
                            "v1",
                            "{}",
                            "exact",
                            (SourceLineageDraft(0, self.page1),),
                        ),
                    ),
                    inline_payload={"value": 42},
                ),
            )
        )
        receipt = self.host.run_derivation(request, backend)
        return request, backend, receipt

    def test_descriptorless_replay_still_rejects_changed_egress_policy_identity(self):
        auth = EgressAuthorization(
            True,
            "public_civic",
            "chatgpt_personal_operator_enabled",
            "a" * 64,
            "codex_cli",
        )
        request = DerivationRequest(
            (self.whole1,),
            "query",
            "sql",
            "SELECT amount FROM projection",
            egress=auth,
        )
        backend = FixtureDerivationBackend(
            DerivationExecutionResult(
                "success",
                DerivationOutput(
                    "scalar",
                    "canario.scalar",
                    "v1",
                    (
                        DerivationResultTargetDraft(
                            "scalar",
                            "v1",
                            "{}",
                            "exact",
                            (SourceLineageDraft(0, self.page1),),
                        ),
                    ),
                    inline_payload={"value": 42},
                ),
                egress_bytes=123,
            ),
            requires_egress=True,
        )
        self.host.run_derivation(request, backend)

        self.assertTrue(self.writer.replay_derivation(request).replayed)
        changed = replace(
            request,
            egress=EgressAuthorization(
                True,
                "public_civic",
                "different_data_control",
                "a" * 64,
                "codex_cli",
            ),
        )
        with self.assertRaises(ReasoningIdentityCollision):
            self.writer.replay_derivation(changed)

    def test_derivation_replay_persists_exact_lineage_and_avoids_second_backend_call(self):
        request, backend, receipt = self._derive()
        self.assertEqual(receipt.outcome, "success")
        self.assertEqual(len(receipt.targets), 1)
        self.assertEqual(backend.calls, 1)
        replay = self.host.run_derivation(request, backend)
        self.assertTrue(replay.replayed)
        self.assertEqual(backend.calls, 1)
        self.assertEqual(replay.targets, receipt.targets)

        con = local_connection(self.db)
        try:
            self.assertEqual(
                con.execute(
                    "SELECT representation_target_id FROM derivation_run_inputs WHERE derivation_run_id=?",
                    (request.derivation_run_id,),
                ).fetchone(),
                (self.whole1,),
            )
            self.assertEqual(
                con.execute(
                    "SELECT representation_target_id FROM derivation_result_lineage WHERE derivation_result_target_id=?",
                    (receipt.targets[0].id,),
                ).fetchone(),
                (self.page1,),
            )
        finally:
            con.close()

        changed = replace(request, program_text="SELECT other FROM projection")
        with self.assertRaises(ReasoningIdentityCollision):
            self.host.run_derivation(changed, backend)

    def test_derivation_rejects_lineage_outside_declared_input(self):
        request = DerivationRequest((self.whole1,), "query", "sql", "SELECT 1")
        backend = FixtureDerivationBackend(
            DerivationExecutionResult(
                "success",
                DerivationOutput(
                    "scalar",
                    "canario.scalar",
                    "v1",
                    (
                        DerivationResultTargetDraft(
                            "scalar",
                            "v1",
                            "{}",
                            "exact",
                            (SourceLineageDraft(0, self.other_page),),
                        ),
                    ),
                    inline_payload=1,
                ),
            )
        )
        with self.assertRaises(ReasoningInvariantError):
            self.host.run_derivation(request, backend)
        con = local_connection(self.db)
        try:
            self.assertEqual(
                con.execute("SELECT count(*) FROM derivation_runs WHERE id=?", (request.derivation_run_id,)).fetchone()[0],
                0,
            )
        finally:
            con.close()

    def test_egress_derivation_is_rejected_before_backend_for_forbidden_request(self):
        backend = FixtureDerivationBackend(
            DerivationExecutionResult("failed", error_code="unused", egress_bytes=0),
            requires_egress=True,
        )
        request = DerivationRequest((self.whole1,), "query", "sql", "SELECT 1")
        with self.assertRaises(ReasoningInvariantError):
            self.host.run_derivation(request, backend)
        self.assertEqual(backend.calls, 0)

    def test_derived_claim_verification_and_machine_assessment_end_to_end(self):
        _request, _backend, derivation = self._derive()
        origin_target = derivation.targets[0].id
        claim_request = DerivedClaimRequest(
            origin_target,
            "El valor derivado es 42.",
            "human",
            evidence=(DerivedEvidenceDraft(self.whole1, "supports", "human"),),
        )
        claim = self.writer.promote_derived_claim(claim_request, created_at=T)
        self.assertFalse(claim.replayed)
        self.assertTrue(self.writer.promote_derived_claim(claim_request, created_at=T).replayed)

        verification_request = VerificationRequest(
            claim_request.text,
            (self.whole1,),
            (self.sas1,),
            "explicit_targets",
            "v1",
            "{}",
            (VerificationDerivationStep(derivation.derivation_run_id, "consumed", origin_target),),
            claim.claim_revision_id if hasattr(claim, "claim_revision_id") else claim.revision_id,
        )
        verifier = FixtureVerificationBackend(
            VerificationExecutionResult(
                "completed",
                "supported",
                "sufficient",
                "explicit",
                "v1",
                "{}",
                evidence=(VerificationEvidenceDraft(0, self.page1, "supports"),),
            )
        )
        verification = self.host.run_verification(verification_request, verifier)
        self.assertEqual(verification.verdict, "supported")
        self.assertEqual(verifier.calls, 1)
        self.assertTrue(self.host.run_verification(verification_request, verifier).replayed)
        self.assertEqual(verifier.calls, 1)

        assessment_request = AssessmentRequest(
            claim.revision_id,
            "supported",
            "rule",
            "reference.verification",
            verification.verification_run_id,
            "reference_assessment",
            "v1",
        )
        assessment = self.writer.record_assessment(assessment_request, created_at=T)
        self.assertEqual(assessment.judgment, "supported")
        self.assertTrue(self.writer.record_assessment(assessment_request, created_at=T).replayed)

    def test_verification_rejects_scope_expansion_and_wrong_authority(self):
        _request, _backend, derivation = self._derive()
        target = derivation.targets[0].id
        wrong_scope = VerificationRequest(
            "ad hoc",
            (self.whole2,),
            (self.sas2,),
            "explicit_targets",
            "v1",
            "{}",
            (VerificationDerivationStep(derivation.derivation_run_id, "consumed", target),),
        )
        with self.assertRaises(ReasoningInvariantError):
            self.writer.load_verification_invocation(wrong_scope)

        wrong_authority = VerificationRequest(
            "ad hoc",
            (self.whole1,),
            (self.sas2,),
            "explicit_targets",
            "v1",
            "{}",
        )
        with self.assertRaises(ReasoningInvariantError):
            self.writer.load_verification_invocation(wrong_authority)

    def test_derived_support_must_overlap_source_contribution_lineage(self):
        _request, _backend, derivation = self._derive()
        claim_request = DerivedClaimRequest(
            derivation.targets[0].id,
            "Derived",
            "human",
            evidence=(DerivedEvidenceDraft(self.page2, "supports", "human"),),
        )
        with self.assertRaises(ReasoningInvariantError):
            self.writer.promote_derived_claim(claim_request, created_at=T)

    def test_assessment_cannot_use_verification_for_different_claim(self):
        _request, _backend, derivation = self._derive()
        claim1 = self.writer.promote_derived_claim(
            DerivedClaimRequest(derivation.targets[0].id, "Claim one", "human"),
            created_at=T,
        )
        claim2 = self.writer.promote_derived_claim(
            DerivedClaimRequest(derivation.targets[0].id, "Claim two", "human"),
            created_at=T,
        )
        vreq = VerificationRequest(
            "Claim one",
            (self.whole1,),
            (self.sas1,),
            "explicit_targets",
            "v1",
            "{}",
            claim_revision_id=claim1.revision_id,
        )
        verifier = FixtureVerificationBackend(
            VerificationExecutionResult(
                "completed", "supported", "sufficient", "explicit", "v1", "{}"
            )
        )
        vr = self.host.run_verification(vreq, verifier)
        bad = AssessmentRequest(
            claim2.revision_id,
            "supported",
            "rule",
            "reference.verification",
            vr.verification_run_id,
            "reference_assessment",
            "v1",
        )
        with self.assertRaises(ReasoningInvariantError):
            self.writer.record_assessment(bad, created_at=T)

    def test_archive_result_reuses_physical_object_without_collapsing_run_identity(self):
        payload = b"large analytical result"
        def make_backend():
            return FixtureDerivationBackend(
                DerivationExecutionResult(
                    "success",
                    DerivationOutput(
                        "binary",
                        "canario.binary",
                        "v1",
                        (
                            DerivationResultTargetDraft(
                                "whole", "v1", "{}", "exact",
                                (SourceLineageDraft(0, self.page1),),
                            ),
                        ),
                        archive_bytes=payload,
                    ),
                )
            )
        first_request = DerivationRequest((self.whole1,), "query", "sql", "SELECT blob FROM p")
        second_request = DerivationRequest((self.whole1,), "query", "sql", "SELECT blob FROM p")
        first = self.host.run_derivation(first_request, make_backend())
        second = self.host.run_derivation(second_request, make_backend())
        self.assertNotEqual(first.derivation_run_id, second.derivation_run_id)
        self.assertNotEqual(first.result_id, second.result_id)
        con = local_connection(self.db)
        try:
            rows = con.execute(
                "SELECT derivation_run_id,archive_object_id FROM derivation_results "
                "WHERE derivation_run_id IN (?,?) ORDER BY derivation_run_id",
                (first.derivation_run_id, second.derivation_run_id),
            ).fetchall()
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0][1], rows[1][1])
        finally:
            con.close()

    def test_inline_json_null_is_a_valid_typed_result(self):
        request = DerivationRequest((self.whole1,), "query", "sql", "SELECT NULL")
        backend = FixtureDerivationBackend(
            DerivationExecutionResult(
                "success",
                DerivationOutput(
                    "scalar",
                    "canario.scalar",
                    "v1",
                    (
                        DerivationResultTargetDraft(
                            "scalar", "v1", "{}", "none", ()
                        ),
                    ),
                    inline_payload=None,
                ),
            )
        )
        receipt = self.host.run_derivation(request, backend)
        con = local_connection(self.db)
        try:
            row = con.execute(
                "SELECT inline_payload_json,content_sha256,byte_size FROM derivation_results "
                "WHERE id=?",
                (receipt.result_id,),
            ).fetchone()
            self.assertEqual(row[0], "null")
            self.assertEqual(row[2], 4)
        finally:
            con.close()

    def test_nontrivial_pdf_page_contains_quote_for_source_lineage(self):
        materializers = SourceMaterializerRegistry(
            {("pdf_page", "v1"): lambda _target, _source, _charset: b"bounded-page-1"}
        )
        writer = ReasoningWriter(
            self.db, self.archive, source_materializers=materializers, connection_factory=local_connection
        )
        host = ReasoningHost(writer)
        quote = self._target(
            self.rep1,
            "pdf_page_quote",
            '{"page_ordinal":1,"exact":"fixture"}',
        )
        request = DerivationRequest((self.page1,), "query", "sql", "SELECT quote")
        def derive(invocation):
            self.assertEqual(invocation.inputs[0].material_bytes, b"bounded-page-1")
            self.assertNotEqual(invocation.inputs[0].material_bytes, b"%PDF fixture one")
            return DerivationExecutionResult(
                "success",
                DerivationOutput(
                    "scalar",
                    "canario.scalar",
                    "v1",
                    (
                        DerivationResultTargetDraft(
                            "scalar", "v1", "{}", "exact",
                            (SourceLineageDraft(0, quote),),
                        ),
                    ),
                    inline_payload="fixture",
                ),
            )

        backend = FixtureDerivationBackend(derive)
        receipt = host.run_derivation(request, backend)
        self.assertEqual(receipt.outcome, "success")

    def test_verifier_receives_source_authority_and_consumed_derivation_material(self):
        _request, _backend, derivation = self._derive()
        target = derivation.targets[0].id
        request = VerificationRequest(
            "ad hoc",
            (self.whole1,),
            (self.sas1,),
            "explicit_targets",
            "v1",
            "{}",
            (VerificationDerivationStep(derivation.derivation_run_id, "consumed", target),),
        )

        def verify(invocation):
            self.assertEqual(invocation.authority_scopes[0].scope_kind, "formal_record")
            self.assertEqual(invocation.authority_scopes[0].source_id, self.source1.id)
            self.assertEqual(invocation.derivations[0].outcome, "success")
            self.assertIsNotNone(invocation.derivations[0].consumed_result)
            self.assertIn(b'"value":42', invocation.derivations[0].consumed_result.material_bytes)
            return VerificationExecutionResult(
                "completed", "supported", "sufficient", "explicit", "v1", "{}",
                evidence=(VerificationEvidenceDraft(0, self.page1, "supports"),),
            )

        receipt = self.host.run_verification(request, FixtureVerificationBackend(verify))
        self.assertEqual(receipt.verdict, "supported")

    def test_failed_verification_has_no_epistemic_verdict_and_insufficient_is_completed(self):
        failed_request = VerificationRequest(
            "ad hoc",
            (self.whole1,),
            (self.sas1,),
            "explicit_targets",
            "v1",
            "{}",
        )
        failed = self.host.run_verification(
            failed_request,
            FixtureVerificationBackend(
                VerificationExecutionResult("failed", error_code="tool_failed")
            ),
        )
        self.assertEqual(failed.outcome, "failed")
        self.assertIsNone(failed.verdict)

        insufficient_request = VerificationRequest(
            "another ad hoc",
            (self.whole1,),
            (self.sas1,),
            "explicit_targets",
            "v1",
            "{}",
        )
        insufficient = self.host.run_verification(
            insufficient_request,
            FixtureVerificationBackend(
                VerificationExecutionResult(
                    "completed",
                    "insufficient_evidence",
                    "insufficient",
                    "explicit",
                    "v1",
                    "{}",
                    abstention_reason_code="missing_coverage",
                )
            ),
        )
        self.assertEqual(insufficient.outcome, "completed")
        self.assertEqual(insufficient.verdict, "insufficient_evidence")

    def test_verification_evidence_must_remain_inside_declared_scope(self):
        materializers = SourceMaterializerRegistry(
            {("pdf_page", "v1"): lambda _target, _source, _charset: b"bounded-page"}
        )
        writer = ReasoningWriter(
            self.db, self.archive, source_materializers=materializers, connection_factory=local_connection
        )
        host = ReasoningHost(writer)
        request = VerificationRequest(
            "ad hoc",
            (self.page1,),
            (self.sas1,),
            "explicit_targets",
            "v1",
            "{}",
        )
        backend = FixtureVerificationBackend(
            VerificationExecutionResult(
                "completed",
                "supported",
                "sufficient",
                "explicit",
                "v1",
                "{}",
                evidence=(VerificationEvidenceDraft(0, self.page2, "supports"),),
            )
        )
        with self.assertRaises(ReasoningInvariantError):
            host.run_verification(request, backend)

    def test_assessment_supersession_cannot_jump_policy_lineage(self):
        _request, _backend, derivation = self._derive()
        claim = self.writer.promote_derived_claim(
            DerivedClaimRequest(derivation.targets[0].id, "Claim", "human"), created_at=T
        )
        vreq = VerificationRequest(
            "Claim",
            (self.whole1,),
            (self.sas1,),
            "explicit_targets",
            "v1",
            "{}",
            claim_revision_id=claim.revision_id,
        )
        vr = self.host.run_verification(
            vreq,
            FixtureVerificationBackend(
                VerificationExecutionResult(
                    "completed", "supported", "sufficient", "explicit", "v1", "{}"
                )
            ),
        )
        first_request = AssessmentRequest(
            claim.revision_id,
            "supported",
            "rule",
            "reference.verification",
            vr.verification_run_id,
            "policy_a",
            "v1",
        )
        first = self.writer.record_assessment(first_request, created_at=T)
        bad = AssessmentRequest(
            claim.revision_id,
            "refuted",
            "rule",
            "reference.verification",
            vr.verification_run_id,
            "policy_b",
            "v2",
            supersedes_assessment_id=first.assessment_id,
        )
        with self.assertRaises(ReasoningInvariantError):
            self.writer.record_assessment(bad, created_at=T)

    def test_derived_claim_from_now_restricted_input_cannot_be_promoted_active(self):
        _request, _backend, derivation = self._derive()
        con = local_connection(self.db)
        try:
            with con:
                artifact_id = con.execute(
                    "SELECT artifact_id FROM representations WHERE id=?", (self.rep1,)
                ).fetchone()[0]
                con.execute("UPDATE artifacts SET availability='restricted' WHERE id=?", (artifact_id,))
                con.execute("UPDATE representations SET availability='restricted' WHERE id=?", (self.rep1,))
        finally:
            con.close()
        active = DerivedClaimRequest(derivation.targets[0].id, "Restricted basis", "human")
        with self.assertRaises(ReasoningInvariantError):
            self.writer.promote_derived_claim(active, created_at=T)
        restricted = replace(active, lifecycle="restricted")
        receipt = self.writer.promote_derived_claim(restricted, created_at=T)
        self.assertEqual(receipt.revision_id, restricted.claim_revision_id)

    def test_duplicate_canonical_result_selectors_are_rejected(self):
        request = DerivationRequest((self.whole1,), "query", "sql", "SELECT 1")
        backend = FixtureDerivationBackend(
            DerivationExecutionResult(
                "success",
                DerivationOutput(
                    "scalar",
                    "canario.scalar",
                    "v1",
                    (
                        DerivationResultTargetDraft("scalar", "v1", "{}", "none"),
                        DerivationResultTargetDraft("scalar", "v1", "{ }", "none"),
                    ),
                    inline_payload=1,
                ),
            )
        )
        with self.assertRaises(ReasoningInvariantError):
            self.host.run_derivation(request, backend)

    def test_failed_derivation_can_be_preserved_as_attempted_verification_step(self):
        derivation_request = DerivationRequest(
            (self.whole1,), "query", "sql", "SELECT missing FROM projection"
        )
        failed_derivation = self.host.run_derivation(
            derivation_request,
            FixtureDerivationBackend(
                DerivationExecutionResult("failed", error_code="invalid_query")
            ),
        )
        self.assertEqual(failed_derivation.outcome, "failed")

        request = VerificationRequest(
            "ad hoc after failed analytical attempt",
            (self.whole1,),
            (self.sas1,),
            "explicit_targets",
            "v1",
            "{}",
            (VerificationDerivationStep(derivation_request.derivation_run_id, "attempted"),),
        )

        def verify(invocation):
            step = invocation.derivations[0]
            self.assertEqual(step.use_state, "attempted")
            self.assertEqual(step.outcome, "failed")
            self.assertEqual(step.error_code, "invalid_query")
            self.assertIsNone(step.consumed_result)
            return VerificationExecutionResult(
                "completed",
                "insufficient_evidence",
                "insufficient",
                "explicit",
                "v1",
                "{}",
                abstention_reason_code="analytical_attempt_failed",
            )

        receipt = self.host.run_verification(request, FixtureVerificationBackend(verify))
        self.assertEqual(receipt.verdict, "insufficient_evidence")

    def test_preallocated_claim_and_assessment_replay_requires_identical_created_at(self):
        _request, _backend, derivation = self._derive()
        claim_request = DerivedClaimRequest(derivation.targets[0].id, "Timestamped claim", "human")
        claim = self.writer.promote_derived_claim(claim_request, created_at=T)
        later = "2026-08-26T20:31:00.000Z"
        with self.assertRaises(ReasoningIdentityCollision):
            self.writer.promote_derived_claim(claim_request, created_at=later)

        assessment_request = AssessmentRequest(
            claim.revision_id, "unresolved", "human", "analyst.fixture"
        )
        self.writer.record_assessment(assessment_request, created_at=T)
        with self.assertRaises(ReasoningIdentityCollision):
            self.writer.record_assessment(assessment_request, created_at=later)

    def test_custom_result_slice_requires_exact_materializer_before_verifier_can_consume_it(self):
        def validate_row(payload):
            if set(payload) != {"row"} or not isinstance(payload["row"], int):
                raise ValueError("row selector requires integer row")

        result_registry = ResultTargetRegistry({("row", "v1"): validate_row})
        writer = ReasoningWriter(
            self.db,
            self.archive,
            result_target_registry=result_registry,
            connection_factory=local_connection,
        )
        host = ReasoningHost(writer)
        request = DerivationRequest((self.whole1,), "query", "sql", "SELECT row FROM projection")
        derivation = host.run_derivation(
            request,
            FixtureDerivationBackend(
                DerivationExecutionResult(
                    "success",
                    DerivationOutput(
                        "table",
                        "canario.test_table",
                        "v1",
                        (
                            DerivationResultTargetDraft(
                                "row",
                                "v1",
                                '{"row":1}',
                                "exact",
                                (SourceLineageDraft(0, self.page1),),
                            ),
                        ),
                        inline_payload={"rows": [[42], [99]]},
                    ),
                )
            ),
        )
        verification = VerificationRequest(
            "ad hoc",
            (self.whole1,),
            (self.sas1,),
            "explicit_targets",
            "v1",
            "{}",
            (
                VerificationDerivationStep(
                    derivation.derivation_run_id, "consumed", derivation.targets[0].id
                ),
            ),
        )
        backend = FixtureVerificationBackend(
            VerificationExecutionResult(
                "completed", "supported", "sufficient", "explicit", "v1", "{}"
            )
        )
        with self.assertRaises(ReasoningContractError):
            host.run_verification(verification, backend)
        self.assertEqual(backend.calls, 0)

    def test_narrow_source_scope_requires_explicit_bounded_materializer_before_backend(self):
        request = DerivationRequest((self.page1,), "query", "sql", "SELECT page")
        backend = FixtureDerivationBackend(
            DerivationExecutionResult("failed", error_code="must_not_run")
        )
        with self.assertRaises(ReasoningContractError):
            self.host.run_derivation(request, backend)
        self.assertEqual(backend.calls, 0)

    def test_noncanonical_verification_profile_payload_is_rejected_before_backend(self):
        request = VerificationRequest(
            "ad hoc",
            (self.whole1,),
            (self.sas1,),
            "explicit_targets",
            "v1",
            "{ }",
        )
        backend = FixtureVerificationBackend(
            VerificationExecutionResult(
                "completed", "supported", "sufficient", "explicit", "v1", "{}"
            )
        )
        with self.assertRaises(ReasoningInvariantError):
            self.host.run_verification(request, backend)
        self.assertEqual(backend.calls, 0)


if __name__ == "__main__":
    unittest.main()
