from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import unittest
from unittest import mock
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
from canario.processors import TargetRegistration, WorkbenchWriter
from canario.processors.contracts import EgressAuthorization
from canario.reasoning import ReasoningHost, ReasoningWriter, StructuredSQLiteDerivationBackend
from canario.reasoning.contracts import VerificationDescriptor
from canario.reasoning.structured_verifier import (
    CodexStructuredVerifierConfig,
    CodexStructuredVerifierModel,
    PlannedStructuredQuery,
    StructuredFinalDecision,
    StructuredPlannerCall,
    StructuredVerificationRequest,
    StructuredVerifierOrchestrator,
    StructuredVerifierProviderError,
)

NO_RUNTIME_CHECK = lambda: None
T = "2026-08-26T23:50:00.000Z"
COUNT_SQL = "SELECT COUNT(c2_number) AS n FROM sheet_1_rows WHERE c2_number IS NOT NULL"
CONSTANT_SQL = "SELECT 3 AS n"
BAD_SQL = "DELETE FROM sheet_1_rows"


def local_connection(path: Path) -> sqlite3.Connection:
    return database._open_writable_v1(path, NO_RUNTIME_CHECK)


def structured_table_bytes() -> bytes:
    payload = {
        "format": "canario.structured_table.v1",
        "source_sha256": "a" * 64,
        "sheets": [
            {
                "name": "Presupuesto",
                "ordinal": 1,
                "state": "visible",
                "max_row": 4,
                "max_column": 2,
                "merged_ranges": [],
                "rows": [
                    [
                        {"address": "A1", "value": {"type": "string", "value": "Partida"}, "data_type": "s", "number_format": "General"},
                        {"address": "B1", "value": {"type": "string", "value": "Monto"}, "data_type": "s", "number_format": "General"},
                    ],
                    [
                        {"address": "A2", "value": {"type": "string", "value": "A"}, "data_type": "s", "number_format": "General"},
                        {"address": "B2", "value": {"type": "integer", "value": 10}, "data_type": "n", "number_format": "0"},
                    ],
                    [
                        {"address": "A3", "value": {"type": "string", "value": "B"}, "data_type": "s", "number_format": "General"},
                        {"address": "B3", "value": {"type": "integer", "value": 20}, "data_type": "n", "number_format": "0"},
                    ],
                    [
                        {"address": "A4", "value": {"type": "string", "value": "C"}, "data_type": "s", "number_format": "General"},
                        {"address": "B4", "value": {"type": "integer", "value": 12}, "data_type": "n", "number_format": "0"},
                    ],
                ],
            }
        ],
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


class FakeModel:
    def __init__(self, queries, decision=None, *, plan_error=None, final_error=None):
        self.queries = tuple(queries)
        self.decision = decision
        self.plan_error = plan_error
        self.final_error = final_error
        self.plan_calls = 0
        self.final_calls = 0
        self.seen_schema = None
        self.seen_events = None
        self._descriptor = VerificationDescriptor(
            "fixture.structured_planner_verifier",
            "1",
            "subscription_agent",
            True,
            "openai",
            "fixture-model",
            1,
            16_000_000,
        )

    @property
    def descriptor(self):
        return self._descriptor

    @property
    def configuration_hash(self):
        return hashlib.sha256(b"fixture-structured-verifier-v1").hexdigest()

    @property
    def request_template_hash(self):
        return "e" * 64

    @property
    def endpoint_profile(self):
        return "codex_cli"

    def plan(self, *, proposition_text, source_authority, schema, max_queries):
        self.plan_calls += 1
        self.seen_schema = schema
        if self.plan_error:
            raise StructuredVerifierProviderError(self.plan_error, egress_bytes=17, invocations=1)
        return StructuredPlannerCall(self.queries, 101)

    def finalize(self, *, proposition_text, source_authority, events):
        self.final_calls += 1
        self.seen_events = tuple(events)
        if self.final_error:
            raise StructuredVerifierProviderError(self.final_error, egress_bytes=29, invocations=1)
        assert self.decision is not None
        return self.decision


class StructuredVerifierRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / "canario.sqlite3"
        self.archive = self.root / "archive"
        database._ensure_schema_v1(self.db, NO_RUNTIME_CHECK)
        self.deposit = DepositWriter(self.db, self.archive, connection_factory=local_connection)
        self.workbench = WorkbenchWriter(self.db, self.archive, connection_factory=local_connection)
        self.writer = ReasoningWriter(self.db, self.archive, connection_factory=local_connection)
        self.host = ReasoningHost(self.writer)
        self.backend = StructuredSQLiteDerivationBackend(runtime_guard=NO_RUNTIME_CHECK)

        self.source = SourceRegistration(new_id("src_"), "web", "Municipalidad", True, T)
        self.deposit.register_source(self.source)
        locator = SourceLocatorRegistration(
            new_id("sloc_"), self.source.id, "https://example.test/presupuesto.json", "http_url", T
        )
        self.deposit.register_source_locator(locator)
        self.rep = new_id("rep_")
        artifact = CapturedArtifact(
            new_id("art_"), new_id("aob_"), self.rep, structured_table_bytes(), "primary",
            "presupuesto.json", locator.locator, "application/json", "verified", "available",
            "es", "utf-8", T,
        )
        observation = AcquisitionObservation(
            new_id("acq_"), self.source.id, locator.id, T, "success", 200, "fixture", "1", None, T
        )
        self.deposit.record_acquisition(AcquisitionWrite(observation, (artifact,)))
        self.whole = new_id("rtgt_")
        self.workbench.register_target(TargetRegistration(self.whole, self.rep, "whole", "v1", "{}", T))
        self.authority = new_id("sas_")
        con = local_connection(self.db)
        try:
            with con:
                con.execute(
                    "INSERT INTO source_authority_scopes VALUES (?,?,?,?,?,?,?)",
                    (self.authority, self.source.id, "dataset_value", None, None, "bounded fixture dataset", T),
                )
        finally:
            con.close()
        self.egress = EgressAuthorization(
            True,
            "public_civic",
            "chatgpt_personal_operator_enabled",
            "e" * 64,
            "codex_cli",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def request(self, proposition="The bounded dataset has three numeric records", *, max_queries=6):
        return StructuredVerificationRequest(
            proposition, self.whole, (self.authority,), self.egress, max_queries=max_queries
        )

    def con(self):
        return local_connection(self.db)

    def test_supported_path_persists_exact_consumed_derivation_and_total_egress(self):
        model = FakeModel(
            (PlannedStructuredQuery("Q1", "count numeric rows", COUNT_SQL),),
            StructuredFinalDecision("supported", "adequate", ("Q1",), "count matches", 203),
        )
        receipt = StructuredVerifierOrchestrator(self.host, self.backend, model).run(self.request())
        self.assertEqual(receipt.verification.verdict, "supported")
        self.assertEqual(receipt.consumed_query_ids, ("Q1",))
        self.assertEqual(receipt.prompt_bytes_egressed, 304)
        self.assertEqual(receipt.codex_invocations, 2)
        self.assertNotIn("Partida", json.dumps(model.seen_schema))
        self.assertEqual(model.seen_schema["sheet_tables"][0]["sheet_name"], "Presupuesto")
        self.assertEqual(model.seen_events[0]["lineage_state"], "partial")

        con = self.con()
        try:
            run_id = receipt.verification.verification_run_id
            self.assertEqual(
                con.execute(
                    "SELECT outcome,verdict,sufficiency_state,model_provider,model_name "
                    "FROM verification_runs WHERE id=?", (run_id,)
                ).fetchone(),
                ("completed", "supported", "sufficient", "openai", "fixture-model"),
            )
            self.assertEqual(
                con.execute(
                    "SELECT bytes_egressed FROM verification_run_egress WHERE verification_run_id=?",
                    (run_id,),
                ).fetchone(),
                (304,),
            )
            self.assertEqual(
                con.execute(
                    "SELECT use_state FROM verification_derivation_steps WHERE verification_run_id=?",
                    (run_id,),
                ).fetchall(),
                [("consumed",)],
            )
        finally:
            con.close()

    def test_uncited_successful_query_is_attempted_not_consumed(self):
        model = FakeModel(
            (
                PlannedStructuredQuery("Q1", "count", COUNT_SQL),
                PlannedStructuredQuery("Q2", "constant diagnostic", CONSTANT_SQL),
            ),
            StructuredFinalDecision("supported", "adequate", ("Q1",), "Q1 is enough", 20),
        )
        receipt = StructuredVerifierOrchestrator(self.host, self.backend, model).run(self.request())
        con = self.con()
        try:
            self.assertEqual(
                con.execute(
                    "SELECT ordinal,use_state FROM verification_derivation_steps WHERE verification_run_id=? ORDER BY ordinal",
                    (receipt.verification.verification_run_id,),
                ).fetchall(),
                [(0, "consumed"), (1, "attempted")],
            )
        finally:
            con.close()

    def test_source_independent_constant_can_abstain_but_cannot_back_supported_verdict(self):
        planner = (PlannedStructuredQuery("Q1", "constant counterfactual", CONSTANT_SQL),)
        insufficient = FakeModel(
            planner,
            StructuredFinalDecision(
                "insufficient_evidence", "inadequate", ("Q1",), "constant is not source evidence", 30,
                "derivation_not_source_backed",
            ),
        )
        receipt = StructuredVerifierOrchestrator(self.host, self.backend, insufficient).run(self.request())
        self.assertEqual(receipt.verification.verdict, "insufficient_evidence")
        self.assertEqual(insufficient.seen_events[0]["lineage_state"], "none")

        bad = FakeModel(
            planner,
            StructuredFinalDecision("supported", "adequate", ("Q1",), "wrongly trusts constant", 30),
        )
        failed = StructuredVerifierOrchestrator(self.host, self.backend, bad).run(self.request("Another proposition"))
        self.assertEqual(failed.verification.outcome, "failed")
        self.assertEqual(failed.verification.error_code, "final_evidence_not_source_backed")
        con = self.con()
        try:
            self.assertEqual(
                con.execute(
                    "SELECT error_code FROM verification_runs WHERE id=?",
                    (failed.verification.verification_run_id,),
                ).fetchone(),
                ("final_evidence_not_source_backed",),
            )
        finally:
            con.close()

    def test_query_rejection_remains_attempted_technical_fact(self):
        model = FakeModel(
            (
                PlannedStructuredQuery("Q1", "bad write", BAD_SQL),
                PlannedStructuredQuery("Q2", "usable count", COUNT_SQL),
            ),
            StructuredFinalDecision("supported", "adequate", ("Q2",), "uses only successful evidence", 25),
        )
        receipt = StructuredVerifierOrchestrator(self.host, self.backend, model).run(self.request())
        self.assertEqual(model.seen_events[0]["outcome"], "failed")
        self.assertIsNotNone(model.seen_events[0]["error_code"])
        con = self.con()
        try:
            self.assertEqual(
                con.execute(
                    "SELECT use_state FROM verification_derivation_steps WHERE verification_run_id=? ORDER BY ordinal",
                    (receipt.verification.verification_run_id,),
                ).fetchall(),
                [("attempted",), ("consumed",)],
            )
        finally:
            con.close()

    def test_planner_provider_failure_persists_failed_verification_without_derivations(self):
        model = FakeModel((), plan_error="provider_down")
        receipt = StructuredVerifierOrchestrator(self.host, self.backend, model).run(self.request())
        self.assertEqual(receipt.verification.outcome, "failed")
        self.assertEqual(receipt.verification.error_code, "provider_down")
        self.assertEqual(receipt.derivations, ())
        self.assertEqual(model.final_calls, 0)
        con = self.con()
        try:
            run_id = receipt.verification.verification_run_id
            self.assertEqual(
                con.execute("SELECT error_code FROM verification_runs WHERE id=?", (run_id,)).fetchone(),
                ("provider_down",),
            )
            self.assertEqual(
                con.execute("SELECT bytes_egressed FROM verification_run_egress WHERE verification_run_id=?", (run_id,)).fetchone(),
                (17,),
            )
        finally:
            con.close()

    def test_restricted_scope_blocks_before_any_model_call(self):
        con = self.con()
        try:
            with con:
                con.execute("UPDATE artifacts SET availability='restricted' WHERE id=(SELECT artifact_id FROM representations WHERE id=?)", (self.rep,))
        finally:
            con.close()
        model = FakeModel((PlannedStructuredQuery("Q1", "count", COUNT_SQL),))
        with self.assertRaisesRegex(Exception, "restricted Verification scope cannot egress"):
            StructuredVerifierOrchestrator(self.host, self.backend, model).run(self.request())
        self.assertEqual(model.plan_calls, 0)


    def test_egress_template_and_endpoint_are_bound_before_model_call(self):
        model = FakeModel((PlannedStructuredQuery("Q1", "count", COUNT_SQL),))
        bad = EgressAuthorization(
            True, "public_civic", "chatgpt_personal_operator_enabled", "f" * 64, "codex_cli"
        )
        request = StructuredVerificationRequest(
            "The bounded dataset has three numeric records", self.whole, (self.authority,), bad
        )
        with self.assertRaisesRegex(Exception, "template authorization mismatch"):
            StructuredVerifierOrchestrator(self.host, self.backend, model).run(request)
        self.assertEqual(model.plan_calls, 0)

    def test_final_provider_failure_persists_both_model_call_egress(self):
        model = FakeModel(
            (PlannedStructuredQuery("Q1", "count", COUNT_SQL),),
            final_error="provider_down",
        )
        receipt = StructuredVerifierOrchestrator(self.host, self.backend, model).run(self.request())
        self.assertEqual(receipt.verification.outcome, "failed")
        self.assertEqual(receipt.verification.error_code, "provider_down")
        self.assertEqual(receipt.codex_invocations, 2)
        self.assertEqual(receipt.prompt_bytes_egressed, 130)
        con = self.con()
        try:
            self.assertEqual(
                con.execute(
                    "SELECT bytes_egressed FROM verification_run_egress WHERE verification_run_id=?",
                    (receipt.verification.verification_run_id,),
                ).fetchone(),
                (130,),
            )
            self.assertEqual(
                con.execute(
                    "SELECT use_state FROM verification_derivation_steps WHERE verification_run_id=?",
                    (receipt.verification.verification_run_id,),
                ).fetchall(),
                [("attempted",)],
            )
        finally:
            con.close()

    def test_max_query_budget_is_part_of_verification_identity(self):
        model1 = FakeModel(
            (PlannedStructuredQuery("Q1", "count", COUNT_SQL),),
            StructuredFinalDecision("supported", "adequate", ("Q1",), "ok", 10),
        )
        first = StructuredVerifierOrchestrator(self.host, self.backend, model1).run(self.request(max_queries=1))
        model2 = FakeModel(
            (PlannedStructuredQuery("Q1", "count", COUNT_SQL),),
            StructuredFinalDecision("supported", "adequate", ("Q1",), "ok", 10),
        )
        second = StructuredVerifierOrchestrator(self.host, self.backend, model2).run(self.request(max_queries=2))
        con = self.con()
        try:
            hashes = [
                con.execute("SELECT configuration_hash FROM verification_runs WHERE id=?", (item.verification.verification_run_id,)).fetchone()[0]
                for item in (first, second)
            ]
            self.assertNotEqual(hashes[0], hashes[1])
        finally:
            con.close()

    def test_zero_query_plan_can_abstain_without_derivations(self):
        model = FakeModel(
            (),
            StructuredFinalDecision(
                "insufficient_evidence",
                "inadequate",
                (),
                "bounded authority does not establish the proposition",
                33,
                "no_material_query",
            ),
        )
        receipt = StructuredVerifierOrchestrator(self.host, self.backend, model).run(self.request())
        self.assertEqual(receipt.verification.verdict, "insufficient_evidence")
        self.assertEqual(receipt.derivations, ())
        self.assertEqual(receipt.planned_query_ids, ())
        self.assertEqual(receipt.consumed_query_ids, ())
        self.assertEqual(receipt.codex_invocations, 2)
        self.assertEqual(receipt.prompt_bytes_egressed, 134)

    def test_planner_budget_violation_counts_completed_planner_call(self):
        model = FakeModel((
            PlannedStructuredQuery("Q1", "count", COUNT_SQL),
            PlannedStructuredQuery("Q2", "constant", CONSTANT_SQL),
        ))
        receipt = StructuredVerifierOrchestrator(self.host, self.backend, model).run(
            self.request(max_queries=1)
        )
        self.assertEqual(receipt.verification.outcome, "failed")
        self.assertEqual(receipt.verification.error_code, "planner_query_budget_exceeded")
        self.assertEqual(receipt.codex_invocations, 1)
        self.assertEqual(receipt.prompt_bytes_egressed, 101)
        self.assertEqual(receipt.derivations, ())
        self.assertEqual(model.final_calls, 0)

    def test_unknown_final_citation_fails_after_counting_completed_final_call(self):
        model = FakeModel(
            (PlannedStructuredQuery("Q1", "count", COUNT_SQL),),
            StructuredFinalDecision("supported", "adequate", ("QX",), "unknown citation", 37),
        )
        receipt = StructuredVerifierOrchestrator(self.host, self.backend, model).run(self.request())
        self.assertEqual(receipt.verification.outcome, "failed")
        self.assertEqual(receipt.verification.error_code, "final_unknown_query_citation")
        self.assertEqual(receipt.codex_invocations, 2)
        self.assertEqual(receipt.prompt_bytes_egressed, 138)
        con = self.con()
        try:
            self.assertEqual(
                con.execute(
                    "SELECT error_code FROM verification_runs WHERE id=?",
                    (receipt.verification.verification_run_id,),
                ).fetchone(),
                ("final_unknown_query_citation",),
            )
            self.assertEqual(
                con.execute(
                    "SELECT use_state FROM verification_derivation_steps WHERE verification_run_id=?",
                    (receipt.verification.verification_run_id,),
                ).fetchall(),
                [("attempted",)],
            )
        finally:
            con.close()

    def test_citing_failed_query_is_contract_invalid_and_never_evidence(self):
        model = FakeModel(
            (PlannedStructuredQuery("Q1", "forbidden write", BAD_SQL),),
            StructuredFinalDecision("supported", "adequate", ("Q1",), "wrongly cites failure", 41),
        )
        receipt = StructuredVerifierOrchestrator(self.host, self.backend, model).run(self.request())
        self.assertEqual(receipt.verification.outcome, "failed")
        self.assertEqual(receipt.codex_invocations, 2)
        self.assertEqual(receipt.prompt_bytes_egressed, 142)
        con = self.con()
        try:
            run_id = receipt.verification.verification_run_id
            self.assertEqual(
                con.execute(
                    "SELECT count(*) FROM verification_evidence_items WHERE verification_run_id=?",
                    (run_id,),
                ).fetchone(),
                (0,),
            )
        finally:
            con.close()

    def test_preallocated_derivation_ids_fail_closed_if_retry_planner_changes_sql(self):
        req = self.request(max_queries=1)
        first = FakeModel(
            (PlannedStructuredQuery("Q1", "count", COUNT_SQL),),
            StructuredFinalDecision("supported", "adequate", ("Q1",), "ok", 10),
        )
        StructuredVerifierOrchestrator(self.host, self.backend, first).run(req)
        changed = FakeModel(
            (PlannedStructuredQuery("Q1", "changed", CONSTANT_SQL),),
            StructuredFinalDecision("insufficient_evidence", "inadequate", ("Q1",), "changed", 10, "derivation_not_source_backed"),
        )
        with self.assertRaisesRegex(Exception, "different immutable request"):
            StructuredVerifierOrchestrator(self.host, self.backend, changed).run(req)


class StructuredVerifierProofContractTests(unittest.TestCase):
    def test_controlled_phase_d_capture_uses_frozen_manual_source_kind(self):
        import importlib.util

        proof_path = (
            Path(__file__).resolve().parents[1]
            / "notebook"
            / "implementation"
            / "prove_structured_verifier_runtime.py"
        )
        spec = importlib.util.spec_from_file_location(
            "canario_structured_verifier_runtime_proof_contract", proof_path
        )
        assert spec is not None and spec.loader is not None
        proof = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(proof)

        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            db = root / "canario.sqlite3"
            archive = root / "archive"
            database._ensure_schema_v1(db, NO_RUNTIME_CHECK)
            deposit = DepositWriter(db, archive, connection_factory=local_connection)
            workbench = WorkbenchWriter(db, archive, connection_factory=local_connection)
            source_id, _rep_id, _target_id = proof._capture_structured(
                deposit,
                workbench,
                source_name="Phase D controlled proof fixture",
                locator_text="proof://phase-d-controlled",
                data=structured_table_bytes(),
            )
            con = local_connection(db)
            try:
                self.assertEqual(
                    con.execute("SELECT kind FROM sources WHERE id=?", (source_id,)).fetchone(),
                    ("manual",),
                )
            finally:
                con.close()


class CodexStructuredVerifierContractTests(unittest.TestCase):
    def test_config_rejects_metered_or_unsupported_shapes(self):
        with self.assertRaises(ValueError):
            CodexStructuredVerifierConfig("/bin/false", Path("/tmp"), auth_store_mode="file")
        with self.assertRaises(ValueError):
            CodexStructuredVerifierConfig("/bin/false", Path("/tmp"), reasoning_effort="turbo")


    def test_codex_profile_command_and_env_are_isolated_and_api_key_free(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            executable = root / "codex"
            executable.write_text("#!/bin/sh\necho 'codex-cli 0.149.0'\n", encoding="utf-8")
            executable.chmod(0o700)
            home = root / "codex-home"
            home.mkdir(mode=0o700)
            model = CodexStructuredVerifierModel(
                CodexStructuredVerifierConfig(str(executable), home)
            )
            call_dir = root / "call"
            call_dir.mkdir()
            schema = call_dir / "schema.json"
            output = call_dir / "output.json"
            command = model._command(call_dir, schema, output)
            env = model._env(call_dir)
            self.assertIn("--strict-config", command)
            self.assertIn("--ephemeral", command)
            self.assertIn("--ignore-user-config", command)
            self.assertIn("--ignore-rules", command)
            self.assertIn("read-only", command)
            self.assertIn("gpt-5.6-terra", command)
            self.assertTrue(any('model_reasoning_effort="medium"' == item for item in command))
            self.assertEqual(env["CODEX_HOME"], str(home.resolve()))
            self.assertNotIn("OPENAI_API_KEY", env)
            self.assertFalse(any(key.startswith("CODEX_") and key != "CODEX_HOME" for key in env))
            self.assertEqual(model.endpoint_profile, "openai_codex_subscription")
            self.assertEqual(len(model.request_template_hash), 64)
            base_hash = model.configuration_hash
            slower = CodexStructuredVerifierModel(
                CodexStructuredVerifierConfig(str(executable), home, call_timeout_seconds=241)
            )
            self.assertNotEqual(base_hash, slower.configuration_hash)
            final_schema = model._final_schema()
            abstention = final_schema["properties"]["abstention_reason_code"]
            self.assertEqual(abstention["anyOf"][1], {"type": "null"})
            self.assertNotIn("uniqueItems", final_schema["properties"]["cited_query_ids"])


    def test_final_duplicate_citations_are_rejected_locally_without_wire_uniqueitems(self):
        with self.assertRaises(ValueError):
            StructuredFinalDecision(
                "supported", "adequate", ("Q1", "Q1"), "duplicate", 10, None
            )

    def test_codex_nonzero_invalid_json_schema_is_classified_without_stderr_persistence(self):
        class FakeProcess:
            returncode = 1
            pid = 12345
            def communicate(self, _input=None, timeout=None):
                return (b"", b'ERROR invalid_json_schema: Invalid schema for response_format \"codex_output_schema\"')

        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            executable = root / "codex"
            executable.write_text("#!/bin/sh\necho 'codex-cli 0.149.0'\n", encoding="utf-8")
            executable.chmod(0o700)
            home = root / "codex-home"
            home.mkdir(mode=0o700)
            model = CodexStructuredVerifierModel(
                CodexStructuredVerifierConfig(str(executable), home)
            )
            with mock.patch("canario.reasoning.structured_verifier.subprocess.Popen", return_value=FakeProcess()):
                with self.assertRaises(StructuredVerifierProviderError) as caught:
                    model._call("final", "bounded prompt", model._final_schema())
            self.assertEqual(caught.exception.code, "codex_final_invalid_json_schema")
            self.assertEqual(caught.exception.egress_bytes, len("bounded prompt".encode("utf-8")))
            self.assertEqual(caught.exception.invocations, 1)

    def test_provider_error_carries_exact_prompt_egress(self):
        error = StructuredVerifierProviderError("boom", egress_bytes=123)
        self.assertEqual((error.code, error.egress_bytes, error.invocations), ("boom", 123, 0))


if __name__ == "__main__":
    unittest.main()
