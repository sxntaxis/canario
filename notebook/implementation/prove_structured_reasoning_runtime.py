#!/usr/bin/env python3
"""Natural-artifact proof for the first production structured-reasoning consumer.

The proof intentionally requires the already-retained official MTSS workbook from
Canario's Civic Processor Bench. It does not download data and it leaves no civic
bytes in the repository.

Pipeline proved:

official XLSX
-> Depósito custody
-> production StructuredTableProcessor
-> exact retained structured-table bytes/hash
-> production StructuredSQLiteDerivationBackend
-> persisted DerivationRun/Result/lineage
-> production StructuredScalarVerifierBackend + SourceAuthorityScope
-> persisted VerificationRun

A source-independent constant query is also run as a hidden counterfactual control;
it must yield ``insufficient_evidence`` rather than a supported verdict.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from importlib.metadata import version as package_version
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
from canario.deposit.archive import EvidenceArchive
from canario.persistence import ensure_schema_v1, open_writable_v1
from canario.processors import (
    ProcessingRequest,
    ProcessorRegistry,
    StructuredTableProcessor,
    TargetRegistration,
    WorkbenchHost,
    WorkbenchWriter,
)
from canario.reasoning import (
    ReasoningHost,
    ReasoningWriter,
    ScalarVerificationRule,
    StructuredSQLiteDerivationBackend,
    StructuredScalarVerifierBackend,
    VerificationDerivationStep,
    VerificationRequest,
)

EXPECTED_XLSX_SHA256 = "c98451ffdebc7976757a27ccd9a69a56061c16c37bd808b8d3398b3ffcb8608e"
EXPECTED_STRUCTURED_SHA256 = "0357f16c36f458a525715f64856549d22f39947812184b7c21ae5221d0207b4c"
EXPECTED_OPENPYXL_VERSION = "3.1.5"
EXPECTED_FIRST_SHEET_ROWS = 147
EXPECTED_FIRST_SHEET_COLUMNS = 15
T = "2026-08-26T22:00:00.000Z"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()



def validate_mtss_structured_payload(data: bytes) -> dict[str, object]:
    """Re-prove the historical MTSS structural controls on canonical production bytes."""
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SystemExit("MTSS structured Representation is not canonical UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise SystemExit("MTSS structured Representation must be a JSON object")
    if payload.get("format") != "canario.structured_table.v1":
        raise SystemExit("MTSS structured Representation format mismatch")
    if payload.get("source_sha256") != EXPECTED_XLSX_SHA256:
        raise SystemExit("MTSS structured Representation source binding mismatch")
    sheets = payload.get("sheets")
    if not isinstance(sheets, list) or len(sheets) != 1:
        raise SystemExit("MTSS structured Representation must contain exactly one sheet")
    sheet = sheets[0]
    if not isinstance(sheet, dict):
        raise SystemExit("MTSS sheet payload is malformed")
    if sheet.get("name") != "MTSS" or sheet.get("ordinal") != 1:
        raise SystemExit("MTSS sheet identity drift")
    if sheet.get("max_row") != EXPECTED_FIRST_SHEET_ROWS:
        raise SystemExit("MTSS sheet row-count drift")
    if sheet.get("max_column") != EXPECTED_FIRST_SHEET_COLUMNS:
        raise SystemExit("MTSS sheet column-count drift")
    rows = sheet.get("rows")
    if not isinstance(rows, list):
        raise SystemExit("MTSS sheet rows are malformed")
    cells: dict[str, dict[str, object]] = {}
    formula_count = 0
    for row in rows:
        if not isinstance(row, list):
            raise SystemExit("MTSS row payload is malformed")
        for cell in row:
            if not isinstance(cell, dict) or not isinstance(cell.get("address"), str):
                raise SystemExit("MTSS cell payload is malformed")
            cells[cell["address"]] = cell
            if cell.get("data_type") == "f":
                formula_count += 1
    expected_values = {
        "A1": {"type": "string", "value": "Subp."},
        "C1": {"type": "string", "value": "Descripción"},
        "O1": {"type": "string", "value": "% Ejec."},
        "A2": {"type": "integer", "value": 0},
        "C2": {"type": "string", "value": "REMUNERACIONES"},
        "O2": {"type": "number", "value": 0.09557853868871936},
    }
    for address, expected in expected_values.items():
        actual = cells.get(address)
        if actual is None or actual.get("value") != expected:
            raise SystemExit(f"MTSS structured control cell drift at {address}: {actual!r}")
    if formula_count != 0:
        raise SystemExit("MTSS formula-count drift")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--xlsx", type=Path, required=True)
    parser.add_argument("--result", type=Path)
    args = parser.parse_args()

    if package_version("openpyxl") != EXPECTED_OPENPYXL_VERSION:
        raise SystemExit(
            "natural proof requires openpyxl "
            f"{EXPECTED_OPENPYXL_VERSION}, got {package_version('openpyxl')}"
        )
    xlsx = args.xlsx.read_bytes()
    if sha256(xlsx) != EXPECTED_XLSX_SHA256:
        raise SystemExit("natural MTSS XLSX SHA256 mismatch")

    with tempfile.TemporaryDirectory(prefix="canario-structured-natural-") as td:
        root = Path(td)
        db = root / "canario.sqlite3"
        archive = root / "archive"
        ensure_schema_v1(db)
        deposit = DepositWriter(db, archive)
        workbench = WorkbenchWriter(db, archive)

        source = SourceRegistration(new_id("src_"), "web", "MTSS Datos Abiertos", True, T)
        deposit.register_source(source)
        locator = SourceLocatorRegistration(
            new_id("sloc_"),
            source.id,
            "https://datosabiertos.gob.go.cr/dataset/mtss-liquidacion-presupuestaria-enero-2026",
            "http_url",
            T,
        )
        deposit.register_source_locator(locator)
        original_rep = new_id("rep_")
        artifact = CapturedArtifact(
            new_id("art_"),
            new_id("aob_"),
            original_rep,
            xlsx,
            "primary",
            args.xlsx.name,
            locator.locator,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "verified",
            "available",
            None,
            None,
            T,
        )
        observation = AcquisitionObservation(
            new_id("acq_"), source.id, locator.id, T, "success", 200, "natural-proof", "1", None, T
        )
        deposit.record_acquisition(AcquisitionWrite(observation, (artifact,)))

        original_target = new_id("rtgt_")
        workbench.register_target(
            TargetRegistration(original_target, original_rep, "whole", "v1", "{}", T)
        )
        processor_host = WorkbenchHost(
            workbench, ProcessorRegistry((StructuredTableProcessor(),))
        )
        processed = processor_host.run_attempt(
            ProcessingRequest(original_rep, (original_target,), "structured_table")
        )
        if processed.outcome != "success" or len(processed.outputs) != 1:
            raise SystemExit("natural structured-table processor did not produce one successful output")
        structured = processed.outputs[0]
        if structured.content_sha256 != EXPECTED_STRUCTURED_SHA256:
            raise SystemExit(
                "structured Representation drift: "
                f"{structured.content_sha256} != {EXPECTED_STRUCTURED_SHA256}"
            )

        con = open_writable_v1(db)
        try:
            archive_row = con.execute(
                """
                SELECT ao.content_sha256,ao.byte_size,ao.storage_key
                FROM representations r
                JOIN archive_objects ao ON ao.id=r.archive_object_id
                WHERE r.id=?
                """,
                (structured.representation_id,),
            ).fetchone()
        finally:
            con.close()
        if archive_row is None:
            raise SystemExit("MTSS structured Representation has no retained archive bytes")
        structured_digest, structured_size, structured_key = archive_row
        evidence_archive = EvidenceArchive(archive)
        evidence_archive.verify(structured_key, structured_digest, structured_size)
        structured_bytes = evidence_archive.path_for_key(structured_key).read_bytes()
        if sha256(structured_bytes) != EXPECTED_STRUCTURED_SHA256:
            raise SystemExit("retained MTSS structured bytes disagree with Representation identity")
        validate_mtss_structured_payload(structured_bytes)

        structured_target = new_id("rtgt_")
        workbench.register_target(
            TargetRegistration(
                structured_target, structured.representation_id, "whole", "v1", "{}", T
            )
        )

        authority = new_id("sas_")
        con = open_writable_v1(db)
        try:
            with con:
                con.execute(
                    "INSERT INTO source_authority_scopes VALUES (?,?,?,?,?,?,?)",
                    (authority, source.id, "dataset_value", None, None, "Official MTSS workbook values", T),
                )
        finally:
            con.close()

        writer = ReasoningWriter(db, archive)
        host = ReasoningHost(writer)
        sqlite_backend = StructuredSQLiteDerivationBackend()
        sql = "SELECT COUNT(*) AS n FROM sheet_1_rows"
        derivation_request = sqlite_backend.request((structured_target,), sql)
        derivation = host.run_derivation(derivation_request, sqlite_backend)
        if derivation.outcome != "success" or derivation.targets[0].lineage_state != "partial":
            raise SystemExit("natural source-backed Derivation did not persist partial source lineage")

        proposition = f"La hoja MTSS contiene {EXPECTED_FIRST_SHEET_ROWS} filas representadas."
        rule = ScalarVerificationRule.integer(
            proposition,
            EXPECTED_FIRST_SHEET_ROWS,
            program_text=sql,
            derivation_configuration_hash=sqlite_backend.policy.configuration_hash,
        )
        verification_request = VerificationRequest(
            proposition,
            (structured_target,),
            (authority,),
            "explicit_targets",
            "v1",
            "{}",
            (
                VerificationDerivationStep(
                    derivation.derivation_run_id,
                    "consumed",
                    derivation.targets[0].id,
                ),
            ),
            configuration_hash=rule.configuration_hash,
        )
        verification = host.run_verification(
            verification_request, StructuredScalarVerifierBackend(rule)
        )
        if verification.verdict != "supported" or verification.evidence_target_ids != (
            structured_target,
        ):
            raise SystemExit("natural structured Verification did not support the expected proposition")

        constant_sql = f"SELECT {EXPECTED_FIRST_SHEET_ROWS} AS n"
        constant_request = sqlite_backend.request((structured_target,), constant_sql)
        constant = host.run_derivation(constant_request, sqlite_backend)
        if constant.targets[0].lineage_state != "none":
            raise SystemExit("constant-query counterfactual incorrectly acquired source lineage")
        constant_rule = ScalarVerificationRule.integer(
            proposition,
            EXPECTED_FIRST_SHEET_ROWS,
            program_text=constant_sql,
            derivation_configuration_hash=sqlite_backend.policy.configuration_hash,
        )
        constant_verification = VerificationRequest(
            proposition,
            (structured_target,),
            (authority,),
            "explicit_targets",
            "v1",
            "{}",
            (
                VerificationDerivationStep(
                    constant.derivation_run_id,
                    "consumed",
                    constant.targets[0].id,
                ),
            ),
            configuration_hash=constant_rule.configuration_hash,
        )
        abstention = host.run_verification(
            constant_verification, StructuredScalarVerifierBackend(constant_rule)
        )
        if abstention.verdict != "insufficient_evidence":
            raise SystemExit("constant-query counterfactual was allowed to masquerade as evidence")

        con = open_writable_v1(db)
        try:
            result_payload = json.loads(
                con.execute(
                    "SELECT inline_payload_json FROM derivation_results WHERE derivation_run_id=?",
                    (derivation.derivation_run_id,),
                ).fetchone()[0]
            )
            persisted = {
                "derivation_run_id": derivation.derivation_run_id,
                "derivation_result_target_id": derivation.targets[0].id,
                "query_result": result_payload,
                "verification_run_id": verification.verification_run_id,
                "verification_verdict": verification.verdict,
                "verification_evidence_target_ids": list(verification.evidence_target_ids),
                "constant_derivation_run_id": constant.derivation_run_id,
                "constant_lineage_state": constant.targets[0].lineage_state,
                "constant_verification_run_id": abstention.verification_run_id,
                "constant_verdict": abstention.verdict,
            }
        finally:
            con.close()

    report = {
        "format": "canario.structured_reasoning_runtime_natural_proof.v1",
        "status": "PASS",
        "source": {
            "kind": "official_public_xlsx",
            "authority": "Ministerio de Trabajo y Seguridad Social",
            "xlsx_sha256": EXPECTED_XLSX_SHA256,
            "structured_representation_sha256": EXPECTED_STRUCTURED_SHA256,
            "openpyxl_version": EXPECTED_OPENPYXL_VERSION,
            "historical_controls": {
                "sheet": "MTSS",
                "rows": EXPECTED_FIRST_SHEET_ROWS,
                "columns": EXPECTED_FIRST_SHEET_COLUMNS,
                "formula_count": 0,
                "selected_cells": {
                    "A1": "Subp.",
                    "C1": "Descripción",
                    "O1": "% Ejec.",
                    "A2": 0,
                    "C2": "REMUNERACIONES",
                    "O2": 0.09557853868871936,
                },
            },
        },
        "sqlite_runtime": "3.53.4 registered source ID required by production guards",
        "expected_first_sheet_rows": EXPECTED_FIRST_SHEET_ROWS,
        **persisted,
    }
    encoded = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.result is not None:
        args.result.parent.mkdir(parents=True, exist_ok=True)
        args.result.write_text(encoded, encoding="utf-8")
    print("STRUCTURED_REASONING_RUNTIME_NATURAL_PROOF=PASS")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
