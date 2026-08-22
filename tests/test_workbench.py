from __future__ import annotations

import sqlite3
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

from actakit.deposit import (
    AcquisitionObservation,
    AcquisitionWrite,
    CapturedArtifact,
    DepositWriter,
    SourceLocatorRegistration,
    SourceRegistration,
    new_id,
)
from actakit.persistence import database
from actakit.processors import (
    DerivativeOutput,
    EgressAuthorization,
    PlannedStep,
    ProcessingPlan,
    ProcessingRequest,
    ProcessorContractError,
    ProcessorDescriptor,
    ProcessorRegistry,
    ProcessorResolutionError,
    ProcessorResult,
    QualityContractError,
    QualityDecision,
    QualityRegistry,
    QualitySignal,
    TargetContractError,
    TargetRegistration,
    WorkbenchHost,
    WorkbenchIdentityCollision,
    WorkbenchInvariantError,
    WorkbenchWriter,
)

NO_RUNTIME_CHECK = lambda: None
T = "2026-08-22T12:00:00.000Z"


def local_connection(path: Path) -> sqlite3.Connection:
    return database._open_writable_v1(path, NO_RUNTIME_CHECK)


class FixtureProcessor:
    def __init__(self, descriptor: ProcessorDescriptor, fn):
        self._descriptor = descriptor
        self._fn = fn
        self.calls = 0

    @property
    def descriptor(self) -> ProcessorDescriptor:
        return self._descriptor

    def process(self, invocation):
        self.calls += 1
        return self._fn(invocation)


def descriptor(
    capability: str,
    *,
    key: str | None = None,
    output_kinds: frozenset[str] = frozenset({"extracted_text"}),
    requires_egress: bool = False,
    venue: str = "local_deterministic",
    model: bool = False,
) -> ProcessorDescriptor:
    return ProcessorDescriptor(
        key or f"fixture.{capability}",
        capability,
        "1",
        venue,
        frozenset({"application/pdf"}),
        output_kinds,
        frozenset({"whole", "pdf_page_quote"}),
        requires_egress,
        "openai" if model else None,
        "gpt-test" if model else None,
        5_000_000,
        8,
    )


class WorkbenchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / "actakit.sqlite3"
        self.archive = self.root / "archive"
        database._ensure_schema_v1(self.db, NO_RUNTIME_CHECK)
        self.deposit = DepositWriter(self.db, self.archive, connection_factory=local_connection)
        self.writer = WorkbenchWriter(self.db, self.archive, connection_factory=local_connection)
        self.source = SourceRegistration(new_id("src_"), "web", "Municipalidad", True, T)
        self.deposit.register_source(self.source)
        self.locator = SourceLocatorRegistration(
            new_id("sloc_"), self.source.id, "https://example.test/acta.pdf", "http_url", T
        )
        self.deposit.register_source_locator(self.locator)
        self.rep_id = self._capture(b"%PDF fixture", availability="available")
        self.whole_target = self._target(self.rep_id, "whole", "{}")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _capture(self, data: bytes, *, availability: str) -> str:
        rep_id = new_id("rep_")
        artifact = CapturedArtifact(
            new_id("art_"),
            new_id("aob_"),
            rep_id,
            data,
            "primary",
            "acta.pdf",
            self.locator.locator,
            "application/pdf",
            "verified",
            availability,
            "es",
            None,
            T,
        )
        observation = AcquisitionObservation(
            new_id("acq_"), self.source.id, self.locator.id, T, "success", 200,
            "fixture", "1", None, T,
        )
        self.deposit.record_acquisition(AcquisitionWrite(observation, (artifact,)))
        return rep_id

    def _target(self, rep_id: str, kind: str, payload: str) -> str:
        target_id = new_id("rtgt_")
        self.writer.register_target(TargetRegistration(target_id, rep_id, kind, "v1", payload, T))
        return target_id

    def _con(self):
        return local_connection(self.db)

    def test_contracts_reject_unknown_quality_and_malformed_target(self):
        with self.assertRaises(ValueError):
            ProcessorDescriptor(
                "Bad Key", "text_extract", "1", "local_deterministic",
                frozenset({"application/pdf"}), frozenset(), frozenset({"whole"})
            )
        with self.assertRaises(ValueError):
            ProcessorDescriptor(
                "fixture.empty_outputs", "text_extract", "1", "local_deterministic",
                frozenset({"application/pdf"}), frozenset(), frozenset({"whole"})
            )
        with self.assertRaises(TargetContractError):
            self.writer.register_target(
                TargetRegistration(new_id("rtgt_"), self.rep_id, "whole", "v1", '{"x":1}', T)
            )
        registry = QualityRegistry()
        with self.assertRaises(QualityContractError):
            registry.validate(QualitySignal(self.whole_target, "vendor.magic", "v1", True))
        with self.assertRaises(QualityContractError):
            registry.validate(QualitySignal(self.whole_target, "native.page_text_coverage", "v1", 1.5))
        with self.assertRaises(ValueError):
            QualityDecision(
                self.whole_target, "maybe", "reference_document_processing", "v1", "invalid"
            )


    def test_registry_rejects_unsupported_media_and_scope_before_invocation(self):
        text_only = FixtureProcessor(
            ProcessorDescriptor(
                "fixture.text_only",
                "text_extract",
                "1",
                "local_deterministic",
                frozenset({"text/plain"}),
                frozenset({"extracted_text"}),
                frozenset({"whole"}),
            ),
            lambda inv: self.fail("unsupported media must not invoke processor"),
        )
        host = WorkbenchHost(self.writer, ProcessorRegistry((text_only,)))
        with self.assertRaises(ProcessorResolutionError):
            host.run_attempt(ProcessingRequest(self.rep_id, (self.whole_target,), "text_extract"))
        self.assertEqual(text_only.calls, 0)

        page = self._target(self.rep_id, "pdf_page_quote", '{"page_ordinal":6}')
        whole_only = FixtureProcessor(
            ProcessorDescriptor(
                "fixture.whole_only",
                "text_extract",
                "1",
                "local_deterministic",
                frozenset({"application/pdf"}),
                frozenset({"extracted_text"}),
                frozenset({"whole"}),
            ),
            lambda inv: self.fail("unsupported scope must not invoke processor"),
        )
        scope_host = WorkbenchHost(self.writer, ProcessorRegistry((whole_only,)))
        with self.assertRaises(ProcessorResolutionError):
            scope_host.run_attempt(ProcessingRequest(self.rep_id, (page,), "text_extract"))
        self.assertEqual(whole_only.calls, 0)

    def test_success_persists_scope_evidence_decision_derivative_and_replays_without_invocation(self):
        proc = FixtureProcessor(
            descriptor("text_extract"),
            lambda inv: ProcessorResult(
                "success",
                (DerivativeOutput(b"texto", "extracted_text", "text/plain", "es", "utf-8"),),
                (
                    QualitySignal(inv.scopes[0].id, "native.page_text_present", "v1", True),
                    QualitySignal(inv.scopes[0].id, "core.output_nonempty", "v1", True),
                ),
            ),
        )
        host = WorkbenchHost(self.writer, ProcessorRegistry((proc,)))
        request = ProcessingRequest(self.rep_id, (self.whole_target,), "text_extract")
        receipt = host.run_attempt(request)
        self.assertFalse(receipt.replayed)
        self.assertEqual(receipt.outcome, "success")
        self.assertEqual(receipt.decisions[0].decision, "accept")
        self.assertEqual(proc.calls, 1)

        replay = host.run_attempt(request)
        self.assertTrue(replay.replayed)
        self.assertEqual(proc.calls, 1)
        self.assertEqual(replay.outputs[0].content_sha256, receipt.outputs[0].content_sha256)

        # Canonical retry does not require the historical adapter to remain
        # registered after an upgrade/removal.
        replay_without_adapter = WorkbenchHost(
            self.writer, ProcessorRegistry(())
        ).run_attempt(request)
        self.assertTrue(replay_without_adapter.replayed)
        self.assertEqual(replay_without_adapter.outputs, replay.outputs)

        con = self._con()
        try:
            self.assertEqual(
                con.execute("SELECT outcome FROM process_runs WHERE id=?", (request.process_run_id,)).fetchone(),
                ("success",),
            )
            self.assertEqual(
                con.execute("SELECT decision FROM quality_decisions WHERE process_run_id=?", (request.process_run_id,)).fetchone(),
                ("accept",),
            )
            self.assertEqual(
                con.execute("SELECT representation_target_id FROM process_run_inputs WHERE process_run_id=?", (request.process_run_id,)).fetchone(),
                (self.whole_target,),
            )
            out = con.execute(
                "SELECT parent_representation_id,artifact_id FROM representations WHERE process_run_id=?",
                (request.process_run_id,),
            ).fetchone()
            parent_artifact = con.execute("SELECT artifact_id FROM representations WHERE id=?", (self.rep_id,)).fetchone()[0]
            self.assertEqual(out, (self.rep_id, parent_artifact))
        finally:
            con.close()

    def test_failed_page_scoped_run_survives_without_derivative(self):
        page = self._target(self.rep_id, "pdf_page_quote", '{"page_ordinal":7}')
        proc = FixtureProcessor(
            descriptor("text_extract"),
            lambda inv: ProcessorResult(
                "failed", (), (), "parser_failed", ("malformed_pdf",)
            ),
        )
        host = WorkbenchHost(self.writer, ProcessorRegistry((proc,)))
        request = ProcessingRequest(self.rep_id, (page,), "text_extract")
        receipt = host.run_attempt(request)
        self.assertEqual(receipt.outcome, "failed")
        self.assertEqual(receipt.decisions[0].decision, "quarantine_review")
        self.assertEqual(receipt.outputs, ())
        con = self._con()
        try:
            self.assertEqual(
                con.execute(
                    "SELECT representation_target_id FROM process_run_inputs WHERE process_run_id=?",
                    (request.process_run_id,),
                ).fetchone(),
                (page,),
            )
            self.assertEqual(
                con.execute("SELECT count(*) FROM representations WHERE process_run_id=?", (request.process_run_id,)).fetchone()[0],
                0,
            )
        finally:
            con.close()

    def test_page_scoped_reference_plan_escalates_native_to_ocr_to_subscription_agent(self):
        page = self._target(self.rep_id, "pdf_page_quote", '{"page_ordinal":3}')
        native = FixtureProcessor(
            descriptor("text_extract"),
            lambda inv: ProcessorResult(
                "success", (),
                (QualitySignal(inv.scopes[0].id, "native.page_text_present", "v1", False),),
            ),
        )
        ocr = FixtureProcessor(
            descriptor("ocr", output_kinds=frozenset({"ocr_text"})),
            lambda inv: ProcessorResult(
                "partial",
                (DerivativeOutput(b"ocr draft", "ocr_text", "text/plain", "es", "utf-8"),),
                (
                    QualitySignal(inv.scopes[0].id, "core.output_nonempty", "v1", True),
                    QualitySignal(inv.scopes[0].id, "ocr.needs_visual_review", "v1", True),
                ),
            ),
        )
        visual = FixtureProcessor(
            descriptor(
                "visual_transcribe",
                output_kinds=frozenset({"extracted_text"}),
                requires_egress=True,
                venue="subscription_agent",
                model=True,
            ),
            lambda inv: ProcessorResult(
                "success",
                (DerivativeOutput(b"verified", "extracted_text", "text/plain", "es", "utf-8"),),
                (
                    QualitySignal(inv.scopes[0].id, "multimodal.schema_valid", "v1", True),
                    QualitySignal(inv.scopes[0].id, "multimodal.uncertain_span_count", "v1", 0),
                    QualitySignal(inv.scopes[0].id, "core.output_nonempty", "v1", True),
                ),
                egress_bytes=1234,
            ),
        )
        host = WorkbenchHost(self.writer, ProcessorRegistry((native, ocr, visual)))
        plan = ProcessingPlan(
            self.rep_id,
            (page,),
            (
                PlannedStep.allocate("text_extract"),
                PlannedStep.allocate("ocr"),
                PlannedStep.allocate("visual_transcribe"),
            ),
            EgressAuthorization(True, "public_civic", "chatgpt_personal_operator_enabled", "a" * 64, "codex_cli"),
        )
        receipt = host.run_plan(plan)
        self.assertEqual([a.decisions[0].decision for a in receipt.attempts], ["escalate", "escalate", "accept"])
        self.assertEqual((native.calls, ocr.calls, visual.calls), (1, 1, 1))
        con = self._con()
        try:
            cloud_run = receipt.attempts[-1].process_run_id
            self.assertEqual(
                con.execute(
                    "SELECT bytes_egressed,policy_profile,data_control_profile FROM process_run_egress WHERE process_run_id=?",
                    (cloud_run,),
                ).fetchone(),
                (1234, "public_civic", "chatgpt_personal_operator_enabled"),
            )
            self.assertEqual(
                con.execute("SELECT execution_venue,model_provider,model_name FROM process_runs WHERE id=?", (cloud_run,)).fetchone(),
                ("subscription_agent", "openai", "gpt-test"),
            )
        finally:
            con.close()

    def test_failed_egress_attempt_can_persist_zero_bytes_before_executor_handoff_and_replay(self):
        page = self._target(self.rep_id, "pdf_page_quote", '{"page_ordinal":4}')
        visual = FixtureProcessor(
            descriptor(
                "visual_transcribe",
                output_kinds=frozenset({"transcript"}),
                requires_egress=True,
                venue="subscription_agent",
                model=True,
            ),
            lambda inv: ProcessorResult(
                "failed", error_code="local_render_failed", egress_bytes=0
            ),
        )
        host = WorkbenchHost(self.writer, ProcessorRegistry((visual,)))
        run_id = new_id("prun_")
        auth = EgressAuthorization(
            True,
            "public_civic",
            "chatgpt_personal_operator_enabled",
            "d" * 64,
            "codex_cli",
        )
        request = ProcessingRequest(
            self.rep_id, (page,), "visual_transcribe", None, auth, run_id
        )
        receipt = host.run_attempt(request)
        self.assertEqual(receipt.outcome, "failed")
        self.assertEqual(receipt.decisions[0].decision, "quarantine_review")
        self.assertEqual(visual.calls, 1)

        con = self._con()
        try:
            self.assertEqual(
                con.execute(
                    "SELECT bytes_egressed,policy_profile,data_control_profile,request_template_hash,endpoint_profile "
                    "FROM process_run_egress WHERE process_run_id=?",
                    (run_id,),
                ).fetchone(),
                (0, "public_civic", "chatgpt_personal_operator_enabled", "d" * 64, "codex_cli"),
            )
        finally:
            con.close()

        replay = WorkbenchHost(self.writer, ProcessorRegistry(())).run_attempt(request)
        self.assertTrue(replay.replayed)
        self.assertEqual(visual.calls, 1)

        changed = ProcessingRequest(
            self.rep_id,
            (page,),
            "visual_transcribe",
            None,
            EgressAuthorization(
                True,
                "public_civic",
                "different_data_control",
                "d" * 64,
                "codex_cli",
            ),
            run_id,
        )
        with self.assertRaises(WorkbenchIdentityCollision):
            WorkbenchHost(self.writer, ProcessorRegistry(())).run_attempt(changed)

    def test_restricted_source_never_invokes_egress_processor_and_ends_human_review(self):
        restricted_rep = self._capture(b"%PDF restricted", availability="restricted")
        target = self._target(restricted_rep, "whole", "{}")
        native = FixtureProcessor(
            descriptor("text_extract"),
            lambda inv: ProcessorResult(
                "success", (),
                (QualitySignal(inv.scopes[0].id, "native.page_text_present", "v1", False),),
            ),
        )
        ocr = FixtureProcessor(
            descriptor("ocr", output_kinds=frozenset({"ocr_text"})),
            lambda inv: ProcessorResult(
                "success",
                (DerivativeOutput(b"uncertain", "ocr_text", "text/plain"),),
                (
                    QualitySignal(inv.scopes[0].id, "core.output_nonempty", "v1", True),
                    QualitySignal(inv.scopes[0].id, "ocr.needs_visual_review", "v1", True),
                ),
            ),
        )
        visual = FixtureProcessor(
            descriptor("visual_transcribe", requires_egress=True, venue="subscription_agent", model=True),
            lambda inv: self.fail("restricted material must never reach cloud fixture"),
        )
        host = WorkbenchHost(self.writer, ProcessorRegistry((native, ocr, visual)))
        plan = ProcessingPlan(
            restricted_rep,
            (target,),
            (PlannedStep.allocate("text_extract"), PlannedStep.allocate("ocr"), PlannedStep.allocate("visual_transcribe")),
            EgressAuthorization(True, "public_civic", "chatgpt_personal_operator_enabled"),
        )
        receipt = host.run_plan(plan)
        self.assertEqual(len(receipt.attempts), 2)
        self.assertEqual(receipt.attempts[-1].decisions[0].decision, "quarantine_review")
        self.assertEqual(visual.calls, 0)
        con = self._con()
        try:
            self.assertEqual(con.execute("SELECT count(*) FROM process_run_egress").fetchone()[0], 0)
            ocr_run = receipt.attempts[-1].process_run_id
            self.assertEqual(
                con.execute(
                    "SELECT availability FROM representations WHERE process_run_id=?",
                    (ocr_run,),
                ).fetchone(),
                ("restricted",),
            )
        finally:
            con.close()

    def test_wrong_representation_target_is_rejected_before_invocation(self):
        other_rep = self._capture(b"%PDF other", availability="available")
        other_target = self._target(other_rep, "whole", "{}")
        proc = FixtureProcessor(descriptor("text_extract"), lambda inv: ProcessorResult("success"))
        host = WorkbenchHost(self.writer, ProcessorRegistry((proc,)))
        with self.assertRaises(WorkbenchInvariantError):
            host.run_attempt(ProcessingRequest(self.rep_id, (other_target,), "text_extract"))
        self.assertEqual(proc.calls, 0)

    def test_stable_run_id_collision_fails_and_new_attempt_preserves_distinct_provenance_with_physical_dedup(self):
        proc = FixtureProcessor(
            descriptor("text_extract"),
            lambda inv: ProcessorResult(
                "success",
                (DerivativeOutput(b"same derivative", "extracted_text", "text/plain"),),
                (
                    QualitySignal(inv.scopes[0].id, "native.page_text_present", "v1", True),
                    QualitySignal(inv.scopes[0].id, "core.output_nonempty", "v1", True),
                ),
            ),
        )
        host = WorkbenchHost(self.writer, ProcessorRegistry((proc,)))
        first = ProcessingRequest(self.rep_id, (self.whole_target,), "text_extract")
        first_receipt = host.run_attempt(first)
        changed = replace(first, configuration_hash="b" * 64)
        with self.assertRaises(WorkbenchIdentityCollision):
            host.run_attempt(changed)
        second = ProcessingRequest(self.rep_id, (self.whole_target,), "text_extract")
        second_receipt = host.run_attempt(second)
        self.assertNotEqual(first.process_run_id, second.process_run_id)
        self.assertNotEqual(first_receipt.outputs[0].representation_id, second_receipt.outputs[0].representation_id)
        self.assertEqual(first_receipt.outputs[0].archive_object_id, second_receipt.outputs[0].archive_object_id)

    def test_transaction_failure_rolls_back_rows_and_cleans_new_archive_orphan(self):
        data = b"unique workbench orphan payload"
        digest = self.writer.archive.digest(data)
        proc = FixtureProcessor(
            descriptor("text_extract"),
            lambda inv: ProcessorResult(
                "success",
                (DerivativeOutput(data, "extracted_text", "text/plain"),),
                (
                    QualitySignal(inv.scopes[0].id, "native.page_text_present", "v1", True),
                    QualitySignal(inv.scopes[0].id, "core.output_nonempty", "v1", True),
                ),
            ),
        )
        host = WorkbenchHost(self.writer, ProcessorRegistry((proc,)))
        request = ProcessingRequest(self.rep_id, (self.whole_target,), "text_extract")
        with mock.patch.object(
            self.writer,
            "_validate_committed_attempt",
            side_effect=WorkbenchInvariantError("forced rollback"),
        ):
            with self.assertRaises(WorkbenchInvariantError):
                host.run_attempt(request)
        con = self._con()
        try:
            self.assertEqual(con.execute("SELECT count(*) FROM process_runs WHERE id=?", (request.process_run_id,)).fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT count(*) FROM archive_objects WHERE content_sha256=?", (digest,)).fetchone()[0], 0)
        finally:
            con.close()
        self.assertFalse(self.writer.archive.path_for_key(self.writer.archive.key_for_digest(digest)).exists())


    def test_multiple_targets_preserve_order_and_receive_independent_decisions(self):
        page2 = self._target(self.rep_id, "pdf_page_quote", '{"page_ordinal":2}')
        page5 = self._target(self.rep_id, "pdf_page_quote", '{"page_ordinal":5}')

        def run(inv):
            evidence = []
            for scope in inv.scopes:
                evidence.extend(
                    (
                        QualitySignal(scope.id, "native.page_text_present", "v1", True),
                        QualitySignal(scope.id, "core.output_nonempty", "v1", True),
                    )
                )
            return ProcessorResult(
                "success",
                (DerivativeOutput(b"combined pages", "extracted_text", "text/plain"),),
                tuple(evidence),
            )

        proc = FixtureProcessor(descriptor("text_extract"), run)
        host = WorkbenchHost(self.writer, ProcessorRegistry((proc,)))
        request = ProcessingRequest(self.rep_id, (page5, page2), "text_extract")
        receipt = host.run_attempt(request)
        self.assertEqual([d.target_id for d in receipt.decisions], [page5, page2])
        self.assertEqual([d.decision for d in receipt.decisions], ["accept", "accept"])
        con = self._con()
        try:
            self.assertEqual(
                con.execute(
                    "SELECT representation_target_id FROM process_run_inputs "
                    "WHERE process_run_id=? ORDER BY ordinal",
                    (request.process_run_id,),
                ).fetchall(),
                [(page5,), (page2,)],
            )
        finally:
            con.close()

    def test_reference_policy_never_accepts_text_or_visual_without_material_output_signal(self):
        page = self._target(self.rep_id, "pdf_page_quote", '{"page_ordinal":4}')
        native = FixtureProcessor(
            descriptor("text_extract"),
            lambda inv: ProcessorResult(
                "success", (),
                (
                    QualitySignal(inv.scopes[0].id, "native.page_text_present", "v1", True),
                    QualitySignal(inv.scopes[0].id, "core.output_nonempty", "v1", True),
                ),
            ),
        )
        ocr = FixtureProcessor(
            descriptor("ocr", output_kinds=frozenset({"ocr_text"})),
            lambda inv: ProcessorResult(
                "success",
                (DerivativeOutput(b"fallback", "ocr_text", "text/plain"),),
                (
                    QualitySignal(inv.scopes[0].id, "core.output_nonempty", "v1", True),
                    QualitySignal(inv.scopes[0].id, "ocr.needs_visual_review", "v1", False),
                ),
            ),
        )
        host = WorkbenchHost(self.writer, ProcessorRegistry((native, ocr)))
        plan = ProcessingPlan(
            self.rep_id,
            (page,),
            (PlannedStep.allocate("text_extract"), PlannedStep.allocate("ocr")),
        )
        receipt = host.run_plan(plan)
        self.assertEqual([a.decisions[0].decision for a in receipt.attempts], ["escalate", "accept"])

        visual = FixtureProcessor(
            descriptor(
                "visual_transcribe",
                output_kinds=frozenset({"extracted_text"}),
                requires_egress=True,
                venue="subscription_agent",
                model=True,
            ),
            lambda inv: ProcessorResult(
                "success", (),
                (
                    QualitySignal(inv.scopes[0].id, "multimodal.schema_valid", "v1", True),
                    QualitySignal(inv.scopes[0].id, "multimodal.uncertain_span_count", "v1", 0),
                    QualitySignal(inv.scopes[0].id, "core.output_nonempty", "v1", True),
                ),
                egress_bytes=10,
            ),
        )
        visual_host = WorkbenchHost(self.writer, ProcessorRegistry((visual,)))
        result = visual_host.run_attempt(
            ProcessingRequest(
                self.rep_id,
                (page,),
                "visual_transcribe",
                egress=EgressAuthorization(True, "public_civic", "operator_enabled"),
            )
        )
        self.assertEqual(result.decisions[0].decision, "quarantine_review")

    def test_unauthorized_cloud_processor_is_rejected_before_invocation(self):
        visual = FixtureProcessor(
            descriptor(
                "visual_transcribe",
                requires_egress=True,
                venue="subscription_agent",
                model=True,
            ),
            lambda inv: self.fail("unauthorized cloud processor must not be invoked"),
        )
        host = WorkbenchHost(self.writer, ProcessorRegistry((visual,)))
        with self.assertRaises(ProcessorResolutionError):
            host.run_attempt(
                ProcessingRequest(self.rep_id, (self.whole_target,), "visual_transcribe")
            )
        self.assertEqual(visual.calls, 0)

    def test_duplicate_quality_signal_identity_is_rejected_before_persistence(self):
        proc = FixtureProcessor(
            descriptor("text_extract"),
            lambda inv: ProcessorResult(
                "success",
                (DerivativeOutput(b"text", "extracted_text", "text/plain"),),
                (
                    QualitySignal(inv.scopes[0].id, "native.page_text_present", "v1", True),
                    QualitySignal(inv.scopes[0].id, "native.page_text_present", "v1", False),
                    QualitySignal(inv.scopes[0].id, "core.output_nonempty", "v1", True),
                ),
            ),
        )
        host = WorkbenchHost(self.writer, ProcessorRegistry((proc,)))
        request = ProcessingRequest(self.rep_id, (self.whole_target,), "text_extract")
        with self.assertRaises(ProcessorContractError):
            host.run_attempt(request)
        con = self._con()
        try:
            self.assertEqual(
                con.execute("SELECT count(*) FROM process_runs WHERE id=?", (request.process_run_id,)).fetchone()[0],
                0,
            )
        finally:
            con.close()

    def test_failed_attempt_using_shared_derivative_bytes_never_removes_shared_archive_object(self):
        data = b"shared derivative"
        proc = FixtureProcessor(
            descriptor("text_extract"),
            lambda inv: ProcessorResult(
                "success",
                (DerivativeOutput(data, "extracted_text", "text/plain"),),
                (
                    QualitySignal(inv.scopes[0].id, "native.page_text_present", "v1", True),
                    QualitySignal(inv.scopes[0].id, "core.output_nonempty", "v1", True),
                ),
            ),
        )
        host = WorkbenchHost(self.writer, ProcessorRegistry((proc,)))
        first = host.run_attempt(
            ProcessingRequest(self.rep_id, (self.whole_target,), "text_extract")
        )
        shared = first.outputs[0]
        second_request = ProcessingRequest(self.rep_id, (self.whole_target,), "text_extract")
        with mock.patch.object(
            self.writer,
            "_validate_committed_attempt",
            side_effect=WorkbenchInvariantError("forced rollback"),
        ):
            with self.assertRaises(WorkbenchInvariantError):
                host.run_attempt(second_request)
        self.writer.archive.verify(shared.storage_key, shared.content_sha256, shared.byte_size)
        con = self._con()
        try:
            self.assertEqual(
                con.execute(
                    "SELECT count(*) FROM archive_objects WHERE id=?", (shared.archive_object_id,)
                ).fetchone()[0],
                1,
            )
            self.assertEqual(
                con.execute(
                    "SELECT count(*) FROM process_runs WHERE id=?", (second_request.process_run_id,)
                ).fetchone()[0],
                0,
            )
        finally:
            con.close()

    def test_purged_target_is_rejected(self):
        con = self._con()
        try:
            con.execute(
                """
                UPDATE representation_targets
                SET selector_kind=NULL,selector_version=NULL,selector_payload_json=NULL,
                    state_payload_json=NULL,availability='purged',purged_at=?
                WHERE id=?
                """,
                (T, self.whole_target),
            )
            con.commit()
        finally:
            con.close()
        proc = FixtureProcessor(descriptor("text_extract"), lambda inv: ProcessorResult("success"))
        with self.assertRaises(WorkbenchInvariantError):
            WorkbenchHost(self.writer, ProcessorRegistry((proc,))).run_attempt(
                ProcessingRequest(self.rep_id, (self.whole_target,), "text_extract")
            )
        self.assertEqual(proc.calls, 0)


if __name__ == "__main__":
    unittest.main()
