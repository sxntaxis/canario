from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from io import BytesIO

from openpyxl import Workbook

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
from canario.processors import (
    ProcessingRequest,
    ProcessorRegistry,
    StructuredTableProcessor,
    TargetRegistration,
    WorkbenchHost,
    WorkbenchWriter,
)
from canario.reasoning import (
    AssessmentRequest,
    DerivationRequest,
    DerivedClaimRequest,
    DerivedEvidenceDraft,
    ReasoningHost,
    ReasoningWriter,
    ScalarVerificationRule,
    StructuredSQLiteDerivationBackend,
    StructuredSQLitePolicy,
    StructuredScalarVerifierBackend,
    VerificationDerivationStep,
    VerificationRequest,
)

NO_RUNTIME_CHECK = lambda: None
T = "2026-08-26T21:30:00.000Z"
COUNT_SQL = "SELECT COUNT(c2_number) AS n FROM sheet_1_rows WHERE c2_number IS NOT NULL"


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


class StructuredReasoningRuntimeTests(unittest.TestCase):
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

        self.source = SourceRegistration(new_id("src_"), "web", "Municipalidad", True, T)
        self.deposit.register_source(self.source)
        locator = SourceLocatorRegistration(
            new_id("sloc_"),
            self.source.id,
            "https://example.test/presupuesto.json",
            "http_url",
            T,
        )
        self.deposit.register_source_locator(locator)
        self.rep = new_id("rep_")
        data = structured_table_bytes()
        artifact = CapturedArtifact(
            new_id("art_"),
            new_id("aob_"),
            self.rep,
            data,
            "primary",
            "presupuesto.json",
            locator.locator,
            "application/json",
            "verified",
            "available",
            "es",
            "utf-8",
            T,
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
                    (self.authority, self.source.id, "dataset_value", None, None, None, T),
                )
        finally:
            con.close()
        self.backend = StructuredSQLiteDerivationBackend(runtime_guard=NO_RUNTIME_CHECK)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _run_count(self):
        request = self.backend.request((self.whole,), COUNT_SQL)
        return request, self.host.run_derivation(request, self.backend)

    def test_production_xlsx_processor_feeds_structured_reasoning_backend(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Datos"
        sheet.append(["Nombre", "Monto"])
        sheet.append(["A", 10])
        sheet.append(["B", 20])
        stream = BytesIO()
        workbook.save(stream)
        data = stream.getvalue()

        source = SourceRegistration(new_id("src_"), "manual", "XLSX fixture", True, T)
        self.deposit.register_source(source)
        locator = SourceLocatorRegistration(
            new_id("sloc_"), source.id, "manual://fixture.xlsx", "manual", T
        )
        self.deposit.register_source_locator(locator)
        rep = new_id("rep_")
        artifact = CapturedArtifact(
            new_id("art_"), new_id("aob_"), rep, data, "primary", "fixture.xlsx",
            locator.locator,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "verified", "available", None, None, T,
        )
        observation = AcquisitionObservation(
            new_id("acq_"), source.id, locator.id, T, "success", None, "fixture", "1", None, T
        )
        self.deposit.record_acquisition(AcquisitionWrite(observation, (artifact,)))
        original_target = new_id("rtgt_")
        self.workbench.register_target(TargetRegistration(original_target, rep, "whole", "v1", "{}", T))

        workbench_host = WorkbenchHost(
            self.workbench, ProcessorRegistry((StructuredTableProcessor(),))
        )
        processed = workbench_host.run_attempt(
            ProcessingRequest(rep, (original_target,), "structured_table")
        )
        self.assertEqual(processed.outcome, "success")
        structured_rep = processed.outputs[0].representation_id
        structured_target = new_id("rtgt_")
        self.workbench.register_target(
            TargetRegistration(structured_target, structured_rep, "whole", "v1", "{}", T)
        )

        backend = StructuredSQLiteDerivationBackend(runtime_guard=NO_RUNTIME_CHECK)
        request = backend.request(
            (structured_target,), "SELECT COUNT(c2_number) AS n FROM sheet_1_rows WHERE c2_number IS NOT NULL"
        )
        receipt = self.host.run_derivation(request, backend)
        self.assertEqual(receipt.outcome, "success")
        con = local_connection(self.db)
        try:
            payload = json.loads(
                con.execute(
                    "SELECT inline_payload_json FROM derivation_results WHERE derivation_run_id=?",
                    (request.derivation_run_id,),
                ).fetchone()[0]
            )
            self.assertEqual(payload["rows"], [[{"type": "integer", "value": "2"}]])
        finally:
            con.close()

    def test_sqlite_derivation_persists_source_backed_scalar_and_replays(self):
        request, receipt = self._run_count()
        self.assertEqual(receipt.outcome, "success")
        self.assertEqual(receipt.targets[0].lineage_state, "partial")
        replay = self.host.run_derivation(request, self.backend)
        self.assertTrue(replay.replayed)

        con = local_connection(self.db)
        try:
            self.assertEqual(
                con.execute(
                    "SELECT implementation_key,executor_version,executor_source_id,outcome FROM derivation_runs WHERE id=?",
                    (request.derivation_run_id,),
                ).fetchone()[0:2],
                ("core.structured_sqlite", "3.53.4"),
            )
            payload = json.loads(
                con.execute(
                    "SELECT inline_payload_json FROM derivation_results WHERE derivation_run_id=?",
                    (request.derivation_run_id,),
                ).fetchone()[0]
            )
            self.assertEqual(payload["rows"], [[{"type": "integer", "value": "3"}]])
            self.assertEqual(
                con.execute(
                    "SELECT representation_target_id FROM derivation_result_lineage WHERE derivation_result_target_id=?",
                    (receipt.targets[0].id,),
                ).fetchone(),
                (self.whole,),
            )
        finally:
            con.close()

    def test_forbidden_sql_fails_without_result(self):
        for sql in (
            "DELETE FROM sheet_1_rows",
            "SELECT random()",
            "SELECT 1; SELECT 2",
        ):
            with self.subTest(sql=sql):
                request = self.backend.request((self.whole,), sql)
                receipt = self.host.run_derivation(request, self.backend)
                self.assertEqual(receipt.outcome, "failed")
                self.assertIsNone(receipt.result_id)

    def test_result_bounds_fail_closed(self):
        backend = StructuredSQLiteDerivationBackend(
            policy=StructuredSQLitePolicy(max_rows=2), runtime_guard=NO_RUNTIME_CHECK
        )
        request = backend.request((self.whole,), "SELECT row_index FROM sheet_1_rows")
        receipt = self.host.run_derivation(request, backend)
        self.assertEqual(receipt.outcome, "failed")
        con = local_connection(self.db)
        try:
            self.assertEqual(
                con.execute("SELECT error_code FROM derivation_runs WHERE id=?", (request.derivation_run_id,)).fetchone(),
                ("query_result_too_large",),
            )
        finally:
            con.close()

    def test_scalar_verifier_supports_source_backed_result(self):
        _request, derivation = self._run_count()
        rule = ScalarVerificationRule.integer(
            "La tabla contiene tres montos registrados.",
            3,
            program_text=COUNT_SQL,
            derivation_configuration_hash=self.backend.policy.configuration_hash,
        )
        verifier = StructuredScalarVerifierBackend(rule)
        request = VerificationRequest(
            rule.proposition_text,
            (self.whole,),
            (self.authority,),
            "explicit_targets",
            "v1",
            "{}",
            (VerificationDerivationStep(derivation.derivation_run_id, "consumed", derivation.targets[0].id),),
            configuration_hash=rule.configuration_hash,
        )
        receipt = self.host.run_verification(request, verifier)
        self.assertEqual((receipt.outcome, receipt.verdict), ("completed", "supported"))
        self.assertEqual(receipt.evidence_target_ids, (self.whole,))

    def test_scalar_verifier_contradicts_mismatch(self):
        _request, derivation = self._run_count()
        rule = ScalarVerificationRule.integer(
            "La tabla contiene cuatro montos registrados.",
            4,
            program_text=COUNT_SQL,
            derivation_configuration_hash=self.backend.policy.configuration_hash,
        )
        request = VerificationRequest(
            rule.proposition_text,
            (self.whole,),
            (self.authority,),
            "explicit_targets",
            "v1",
            "{}",
            (VerificationDerivationStep(derivation.derivation_run_id, "consumed", derivation.targets[0].id),),
            configuration_hash=rule.configuration_hash,
        )
        receipt = self.host.run_verification(request, StructuredScalarVerifierBackend(rule))
        self.assertEqual((receipt.outcome, receipt.verdict), ("completed", "contradicted"))

    def test_constant_query_cannot_masquerade_as_source_evidence(self):
        constant_sql = "SELECT 3 AS n"
        derivation_request = self.backend.request((self.whole,), constant_sql)
        derivation = self.host.run_derivation(derivation_request, self.backend)
        self.assertEqual(derivation.targets[0].lineage_state, "none")
        rule = ScalarVerificationRule.integer(
            "La tabla contiene tres montos registrados.",
            3,
            program_text=constant_sql,
            derivation_configuration_hash=self.backend.policy.configuration_hash,
        )
        verification = VerificationRequest(
            rule.proposition_text,
            (self.whole,),
            (self.authority,),
            "explicit_targets",
            "v1",
            "{}",
            (VerificationDerivationStep(derivation.derivation_run_id, "consumed", derivation.targets[0].id),),
            configuration_hash=rule.configuration_hash,
        )
        receipt = self.host.run_verification(verification, StructuredScalarVerifierBackend(rule))
        self.assertEqual(
            (receipt.outcome, receipt.verdict, receipt.sufficiency_state),
            ("completed", "insufficient_evidence", "insufficient"),
        )
        self.assertEqual(receipt.evidence_target_ids, ())

    def test_verifier_rejects_same_value_from_different_program(self):
        _request, derivation = self._run_count()
        rule = ScalarVerificationRule.integer(
            "La tabla contiene tres montos registrados.",
            3,
            program_text="SELECT 3 AS n",
            derivation_configuration_hash=self.backend.policy.configuration_hash,
        )
        verification = VerificationRequest(
            rule.proposition_text,
            (self.whole,),
            (self.authority,),
            "explicit_targets",
            "v1",
            "{}",
            (
                VerificationDerivationStep(
                    derivation.derivation_run_id, "consumed", derivation.targets[0].id
                ),
            ),
            configuration_hash=rule.configuration_hash,
        )
        receipt = self.host.run_verification(
            verification, StructuredScalarVerifierBackend(rule)
        )
        self.assertEqual((receipt.outcome, receipt.verdict), ("failed", None))
        con = local_connection(self.db)
        try:
            self.assertEqual(
                con.execute(
                    "SELECT error_code FROM verification_runs WHERE id=?",
                    (receipt.verification_run_id,),
                ).fetchone(),
                ("derivation_program_mismatch",),
            )
        finally:
            con.close()

    def test_verifier_rule_hash_and_authority_fail_closed(self):
        _request, derivation = self._run_count()
        rule = ScalarVerificationRule.integer(
            "La tabla contiene tres montos registrados.",
            3,
            program_text=COUNT_SQL,
            derivation_configuration_hash=self.backend.policy.configuration_hash,
        )
        bad_hash = VerificationRequest(
            rule.proposition_text,
            (self.whole,),
            (self.authority,),
            "explicit_targets",
            "v1",
            "{}",
            (VerificationDerivationStep(derivation.derivation_run_id, "consumed", derivation.targets[0].id),),
            configuration_hash="f" * 64,
        )
        receipt = self.host.run_verification(bad_hash, StructuredScalarVerifierBackend(rule))
        self.assertEqual((receipt.outcome, receipt.verdict), ("failed", None))

        formal = new_id("sas_")
        con = local_connection(self.db)
        try:
            with con:
                con.execute(
                    "INSERT INTO source_authority_scopes VALUES (?,?,?,?,?,?,?)",
                    (formal, self.source.id, "formal_record", None, None, None, T),
                )
        finally:
            con.close()
        wrong_authority = VerificationRequest(
            rule.proposition_text,
            (self.whole,),
            (formal,),
            "explicit_targets",
            "v1",
            "{}",
            (VerificationDerivationStep(derivation.derivation_run_id, "consumed", derivation.targets[0].id),),
            configuration_hash=rule.configuration_hash,
        )
        receipt = self.host.run_verification(wrong_authority, StructuredScalarVerifierBackend(rule))
        self.assertEqual((receipt.outcome, receipt.verdict), ("failed", None))

    def test_concrete_path_can_promote_claim_and_assessment_explicitly(self):
        _request, derivation = self._run_count()
        rule = ScalarVerificationRule.integer(
            "La tabla contiene tres montos registrados.",
            3,
            program_text=COUNT_SQL,
            derivation_configuration_hash=self.backend.policy.configuration_hash,
        )
        claim = self.writer.promote_derived_claim(
            DerivedClaimRequest(
                derivation.targets[0].id,
                rule.proposition_text,
                "human",
                (DerivedEvidenceDraft(self.whole, "supports", "human"),),
                quantitative=True,
            ),
            created_at=T,
        )
        verification_request = VerificationRequest(
            rule.proposition_text,
            (self.whole,),
            (self.authority,),
            "explicit_targets",
            "v1",
            "{}",
            (VerificationDerivationStep(derivation.derivation_run_id, "consumed", derivation.targets[0].id),),
            claim_revision_id=claim.revision_id,
            configuration_hash=rule.configuration_hash,
        )
        verification = self.host.run_verification(
            verification_request, StructuredScalarVerifierBackend(rule)
        )
        assessment = self.writer.record_assessment(
            AssessmentRequest(
                claim.revision_id,
                "supported",
                "rule",
                "structured_scalar_policy",
                verification.verification_run_id,
                "structured_scalar_policy",
                "1",
            ),
            created_at=T,
        )
        self.assertEqual(assessment.judgment, "supported")


if __name__ == "__main__":
    unittest.main()
