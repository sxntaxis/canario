#!/usr/bin/env python3
"""Exact-profile proof for the first production structured planner/verifier runtime.

The proof has two distinct lanes:

1. a controlled replay of four already-certified Phase-D case semantics (D1/D2/D3/D8)
   through the production ``StructuredVerifierOrchestrator`` and hardened SQLite backend;
2. one natural official MTSS proposition after the production XLSX -> structured-table path.

This is not a new quality benchmark and does not rerun the Thucy challenger. It proves that the
minimum selected decomposition is now represented honestly in durable product records.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
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
from canario.persistence import ensure_schema_v1, open_writable_v1
from canario.processors import (
    ProcessingRequest,
    ProcessorRegistry,
    StructuredTableProcessor,
    TargetRegistration,
    WorkbenchHost,
    WorkbenchWriter,
)
from canario.processors.contracts import EgressAuthorization
from canario.reasoning import (
    CodexStructuredVerifierConfig,
    CodexStructuredVerifierModel,
    ReasoningHost,
    ReasoningWriter,
    StructuredSQLiteDerivationBackend,
    StructuredVerificationRequest,
    StructuredVerifierOrchestrator,
)

ROOT = Path(__file__).resolve().parents[2]
FOUNDATION_PATH = ROOT / "notebook" / "implementation" / "structured_reasoning_fit_bench.py"
PHASE_PATH = ROOT / "notebook" / "implementation" / "structured_verifier_fit_bench.py"
EXPECTED_XLSX_SHA256 = "c98451ffdebc7976757a27ccd9a69a56061c16c37bd808b8d3398b3ffcb8608e"
EXPECTED_STRUCTURED_SHA256 = "0357f16c36f458a525715f64856549d22f39947812184b7c21ae5221d0207b4c"
EXPECTED_OPENPYXL = "3.1.5"
T = "2026-08-27T00:00:00.000Z"
SELECTED_PHASE_CASES = (
    "D1-SUPPORTED-LOOKUP",
    "D2-SUPPORTED-AGGREGATE",
    "D3-CONTRADICTED-AGGREGATE",
    "D8-INSUFFICIENT-GLOBAL-TOTAL",
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load proof dependency: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


foundation = _load("canario_structured_verifier_proof_foundation", FOUNDATION_PATH)
phase = _load("canario_structured_verifier_proof_phase", PHASE_PATH)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _controlled_structured_source() -> bytes:
    value = {
        "format": "canario.structured_table.v1",
        "source_sha256": "1" * 64,
        "sheets": [
            {
                "name": "Alpha",
                "ordinal": 1,
                "state": "visible",
                "max_row": 5,
                "max_column": 3,
                "merged_ranges": [],
                "rows": [
                    [
                        {"address": "A1", "value": {"type": "string", "value": "shared"}, "data_type": "s", "number_format": "General"},
                        {"address": "B1", "value": {"type": "string", "value": "a"}, "data_type": "s", "number_format": "General"},
                        {"address": "C1", "value": {"type": "integer", "value": 10}, "data_type": "n", "number_format": "0"},
                    ],
                    [
                        {"address": "A2", "value": {"type": "string", "value": "k2"}, "data_type": "s", "number_format": "General"},
                        {"address": "B2", "value": {"type": "string", "value": "b"}, "data_type": "s", "number_format": "General"},
                        {"address": "C2", "value": {"type": "integer", "value": 20}, "data_type": "n", "number_format": "0"},
                    ],
                    [
                        {"address": "A3", "value": {"type": "string", "value": "k3"}, "data_type": "s", "number_format": "General"},
                        {"address": "B3", "value": {"type": "string", "value": "c"}, "data_type": "s", "number_format": "General"},
                        {"address": "C3", "value": {"type": "integer", "value": 30}, "data_type": "n", "number_format": "0"},
                    ],
                    [
                        {"address": "A4", "value": {"type": "string", "value": "k4"}, "data_type": "s", "number_format": "General"},
                        {"address": "B4", "value": {"type": "string", "value": "d"}, "data_type": "s", "number_format": "General"},
                        {"address": "C4", "value": {"type": "integer", "value": 40}, "data_type": "n", "number_format": "0"},
                    ],
                    [
                        {"address": "A5", "value": {"type": "string", "value": "k5"}, "data_type": "s", "number_format": "General"},
                        {"address": "B5", "value": {"type": "string", "value": "e"}, "data_type": "s", "number_format": "General"},
                        {"address": "C5", "value": {"type": "integer", "value": 50}, "data_type": "n", "number_format": "0"},
                    ],
                ],
            },
            {
                "name": "Beta",
                "ordinal": 2,
                "state": "visible",
                "max_row": 3,
                "max_column": 2,
                "merged_ranges": [],
                "rows": [
                    [
                        {"address": "A1", "value": {"type": "string", "value": "shared"}, "data_type": "s", "number_format": "General"},
                        {"address": "B1", "value": {"type": "integer", "value": 1}, "data_type": "n", "number_format": "0"},
                    ],
                    [
                        {"address": "A2", "value": {"type": "string", "value": "other"}, "data_type": "s", "number_format": "General"},
                        {"address": "B2", "value": {"type": "integer", "value": 2}, "data_type": "n", "number_format": "0"},
                    ],
                    [
                        {"address": "A3", "value": {"type": "string", "value": "third"}, "data_type": "s", "number_format": "General"},
                        {"address": "B3", "value": {"type": "integer", "value": 3}, "data_type": "n", "number_format": "0"},
                    ],
                ],
            },
        ],
    }
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def _phase_cases(source: bytes) -> dict[str, dict[str, object]]:
    projection, _ = foundation.build_projection(source)
    corpus = foundation.build_esparza_query_corpus(projection)
    foundation.validate_query_corpus(corpus, projection)
    planner = foundation.planner_verifier_cases_from_corpus(corpus)
    cases = phase.build_phase_d_cases(projection, corpus, planner)
    by_id = {str(item["case_id"]): item for item in cases["cases"]}
    return {case_id: by_id[case_id] for case_id in SELECTED_PHASE_CASES}


def _capture_structured(
    deposit: DepositWriter,
    workbench: WorkbenchWriter,
    *,
    source_name: str,
    locator_text: str,
    data: bytes,
) -> tuple[str, str, str]:
    source = SourceRegistration(new_id("src_"), "manual", source_name, True, T)
    deposit.register_source(source)
    locator = SourceLocatorRegistration(new_id("sloc_"), source.id, locator_text, "manual", T)
    deposit.register_source_locator(locator)
    rep = new_id("rep_")
    artifact = CapturedArtifact(
        new_id("art_"), new_id("aob_"), rep, data, "primary", "structured.json",
        locator.locator, "application/json", "verified", "available", "es", "utf-8", T,
    )
    observation = AcquisitionObservation(
        new_id("acq_"), source.id, locator.id, T, "success", None, "proof", "1", None, T
    )
    deposit.record_acquisition(AcquisitionWrite(observation, (artifact,)))
    target = new_id("rtgt_")
    workbench.register_target(TargetRegistration(target, rep, "whole", "v1", "{}", T))
    return source.id, rep, target


def _authority(db: Path, source_id: str, note: str) -> str:
    authority = new_id("sas_")
    con = open_writable_v1(db)
    try:
        with con:
            con.execute(
                "INSERT INTO source_authority_scopes VALUES (?,?,?,?,?,?,?)",
                (authority, source_id, "dataset_value", None, None, note, T),
            )
    finally:
        con.close()
    return authority


def _egress(model: CodexStructuredVerifierModel) -> EgressAuthorization:
    return EgressAuthorization(
        True,
        "public_civic",
        "chatgpt_personal_operator_enabled",
        model.request_template_hash,
        model.endpoint_profile,
    )


def _run_case(
    orchestrator: StructuredVerifierOrchestrator,
    model: CodexStructuredVerifierModel,
    *,
    target_id: str,
    authority_id: str,
    proposition: str,
) -> dict[str, object]:
    receipt = orchestrator.run(
        StructuredVerificationRequest(
            proposition,
            target_id,
            (authority_id,),
            _egress(model),
        )
    )
    return {
        "verification_run_id": receipt.verification.verification_run_id,
        "outcome": receipt.verification.outcome,
        "verdict": receipt.verification.verdict,
        "sufficiency_state": receipt.verification.sufficiency_state,
        "error_code": receipt.verification.error_code,
        "planned_query_ids": list(receipt.planned_query_ids),
        "consumed_query_ids": list(receipt.consumed_query_ids),
        "derivations": [
            {
                "derivation_run_id": item.derivation_run_id,
                "outcome": item.outcome,
                "error_code": item.error_code,
                "result_id": item.result_id,
                "target_ids": [target.id for target in item.targets],
            }
            for item in receipt.derivations
        ],
        "codex_invocations": receipt.codex_invocations,
        "prompt_bytes_egressed": receipt.prompt_bytes_egressed,
    }


def _prepare_mtss(
    db: Path, archive: Path, deposit: DepositWriter, workbench: WorkbenchWriter, xlsx_path: Path
) -> tuple[str, str]:
    if package_version("openpyxl") != EXPECTED_OPENPYXL:
        raise SystemExit(f"expected openpyxl {EXPECTED_OPENPYXL}")
    xlsx = xlsx_path.read_bytes()
    if _sha(xlsx) != EXPECTED_XLSX_SHA256:
        raise SystemExit("MTSS workbook SHA256 mismatch")
    source = SourceRegistration(new_id("src_"), "web", "MTSS Datos Abiertos", True, T)
    deposit.register_source(source)
    locator = SourceLocatorRegistration(
        new_id("sloc_"), source.id,
        "https://datosabiertos.gob.go.cr/dataset/mtss-liquidacion-presupuestaria-enero-2026",
        "http_url", T,
    )
    deposit.register_source_locator(locator)
    rep = new_id("rep_")
    artifact = CapturedArtifact(
        new_id("art_"), new_id("aob_"), rep, xlsx, "primary", xlsx_path.name,
        locator.locator,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "verified", "available", None, None, T,
    )
    observation = AcquisitionObservation(
        new_id("acq_"), source.id, locator.id, T, "success", 200, "natural-proof", "1", None, T
    )
    deposit.record_acquisition(AcquisitionWrite(observation, (artifact,)))
    original_target = new_id("rtgt_")
    workbench.register_target(TargetRegistration(original_target, rep, "whole", "v1", "{}", T))
    processed = WorkbenchHost(workbench, ProcessorRegistry((StructuredTableProcessor(),))).run_attempt(
        ProcessingRequest(rep, (original_target,), "structured_table")
    )
    if processed.outcome != "success" or len(processed.outputs) != 1:
        raise SystemExit("MTSS structured processor failed")
    structured = processed.outputs[0]
    if structured.content_sha256 != EXPECTED_STRUCTURED_SHA256:
        raise SystemExit("MTSS structured Representation SHA256 drift")
    target = new_id("rtgt_")
    workbench.register_target(TargetRegistration(target, structured.representation_id, "whole", "v1", "{}", T))
    return source.id, target


def _persistence_summary(db: Path) -> dict[str, object]:
    con = open_writable_v1(db)
    try:
        verification_rows = con.execute("SELECT count(*) FROM verification_runs").fetchone()[0]
        derivation_rows = con.execute("SELECT count(*) FROM derivation_runs").fetchone()[0]
        consumed_rows = con.execute(
            "SELECT count(*) FROM verification_derivation_steps WHERE use_state='consumed'"
        ).fetchone()[0]
        egress_rows = con.execute(
            "SELECT count(*),coalesce(sum(bytes_egressed),0) FROM verification_run_egress"
        ).fetchone()
        return {
            "verification_runs": verification_rows,
            "derivation_runs": derivation_rows,
            "consumed_steps": consumed_rows,
            "verification_egress_rows": egress_rows[0],
            "total_prompt_bytes_egressed": egress_rows[1],
        }
    finally:
        con.close()


def _build_report(
    args: argparse.Namespace,
    model: CodexStructuredVerifierModel,
    db: Path,
    selected_cases: tuple[str, ...],
    phase_results: list[dict[str, object]],
    mtss_proposition: str | None,
    mtss_result: dict[str, object] | None,
    *,
    status: str,
    failure: dict[str, object] | None,
) -> dict[str, object]:
    natural: dict[str, object] | None = None
    if mtss_result is not None and mtss_proposition is not None:
        natural = {
            "xlsx_sha256": EXPECTED_XLSX_SHA256,
            "structured_representation_sha256": EXPECTED_STRUCTURED_SHA256,
            "proposition": mtss_proposition,
            **mtss_result,
        }
    return {
        "format": "canario.structured_verifier_runtime_proof.v2",
        "status": status,
        "selected_cases": list(selected_cases),
        "profile": {
            "provider": "openai",
            "transport": "official_codex_cli_subscription",
            "model": args.model,
            "reasoning_effort": args.reasoning_effort,
            "endpoint_profile": model.endpoint_profile,
            "configuration_hash": model.configuration_hash,
            "request_template_hash": model.request_template_hash,
            "per_token_api_billing": False,
            "api_key_used": False,
        },
        "phase_d_contract_replay": phase_results,
        "natural_mtss": natural,
        "persistence": _persistence_summary(db),
        "failure": failure,
    }


def _emit_report(result_path: Path | None, report: dict[str, object], *, pass_token: bool) -> None:
    encoded = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if result_path is not None:
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(encoded, encoding="utf-8")
    print(
        "STRUCTURED_VERIFIER_RUNTIME_PROOF=PASS"
        if pass_token
        else "STRUCTURED_VERIFIER_RUNTIME_PROOF=BLOCKED"
    )
    print(encoded, end="")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--xlsx", type=Path, required=True)
    parser.add_argument("--codex-home", type=Path, required=True)
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--model", default="gpt-5.6-terra")
    parser.add_argument("--reasoning-effort", default="medium")
    parser.add_argument(
        "--case",
        action="append",
        choices=(*SELECTED_PHASE_CASES, "MTSS"),
        help="run only the named proof case; repeat for multiple cases; default runs all",
    )
    parser.add_argument("--result", type=Path)
    args = parser.parse_args()
    selected_cases = tuple(args.case) if args.case else (*SELECTED_PHASE_CASES, "MTSS")

    model = CodexStructuredVerifierModel.discover(
        codex_home=args.codex_home,
        codex=args.codex,
        config=CodexStructuredVerifierConfig(
            args.codex,
            args.codex_home,
            args.model,
            args.reasoning_effort,
        ),
    )

    with tempfile.TemporaryDirectory(prefix="canario-structured-verifier-proof-") as tempdir:
        root = Path(tempdir)
        db = root / "canario.sqlite3"
        archive = root / "archive"
        ensure_schema_v1(db)
        deposit = DepositWriter(db, archive)
        workbench = WorkbenchWriter(db, archive)
        writer = ReasoningWriter(db, archive)
        host = ReasoningHost(writer)
        sqlite_backend = StructuredSQLiteDerivationBackend()
        orchestrator = StructuredVerifierOrchestrator(host, sqlite_backend, model)

        phase_results: list[dict[str, object]] = []
        mtss_result: dict[str, object] | None = None
        mtss_proposition: str | None = None

        if any(case_id in selected_cases for case_id in SELECTED_PHASE_CASES):
            controlled_source = _controlled_structured_source()
            controlled_source_id, _rep, controlled_target = _capture_structured(
                deposit,
                workbench,
                source_name="Phase-D controlled structured source",
                locator_text="proof://phase-d-controlled",
                data=controlled_source,
            )
            cases = _phase_cases(controlled_source)
            for case_id in SELECTED_PHASE_CASES:
                if case_id not in selected_cases:
                    continue
                case = cases[case_id]
                authority_note = _canonical(case["source_authority"])
                authority_id = _authority(db, controlled_source_id, authority_note)
                result = _run_case(
                    orchestrator,
                    model,
                    target_id=controlled_target,
                    authority_id=authority_id,
                    proposition=str(case["claim"]),
                )
                result["case_id"] = case_id
                result["expected_verdict"] = case["expected_verdict"]
                result["pass"] = (
                    result["outcome"] == "completed"
                    and result["verdict"] == case["expected_verdict"]
                )
                phase_results.append(result)
                if not result["pass"]:
                    report = _build_report(
                        args,
                        model,
                        db,
                        selected_cases,
                        phase_results,
                        None,
                        None,
                        status="BLOCKED",
                        failure={
                            "case_id": case_id,
                            "expected_verdict": case["expected_verdict"],
                            "observed_outcome": result["outcome"],
                            "observed_verdict": result["verdict"],
                            "error_code": result["error_code"],
                        },
                    )
                    _emit_report(args.result, report, pass_token=False)
                    raise SystemExit(
                        f"Phase-D production replay failed {case_id}: "
                        f"outcome={result['outcome']} verdict={result['verdict']} "
                        f"error_code={result['error_code']} expected={case['expected_verdict']}"
                    )

        if "MTSS" in selected_cases:
            mtss_source, mtss_target = _prepare_mtss(db, archive, deposit, workbench, args.xlsx)
            mtss_authority = _authority(
                db,
                mtss_source,
                _canonical(
                    {
                        "scope": "complete retained MTSS workbook projection",
                        "inventory_completeness": "complete_within_retained_representation",
                        "claim_strength_limit": "may support values/computations inside this workbook only",
                    }
                ),
            )
            mtss_proposition = (
                "Within the retained MTSS workbook projection, sheet MTSS contains exactly "
                "147 represented rows."
            )
            mtss_result = _run_case(
                orchestrator,
                model,
                target_id=mtss_target,
                authority_id=mtss_authority,
                proposition=mtss_proposition,
            )
            if mtss_result["outcome"] != "completed" or mtss_result["verdict"] != "supported":
                report = _build_report(
                    args,
                    model,
                    db,
                    selected_cases,
                    phase_results,
                    mtss_proposition,
                    mtss_result,
                    status="BLOCKED",
                    failure={
                        "case_id": "MTSS",
                        "expected_verdict": "supported",
                        "observed_outcome": mtss_result["outcome"],
                        "observed_verdict": mtss_result["verdict"],
                        "error_code": mtss_result["error_code"],
                    },
                )
                _emit_report(args.result, report, pass_token=False)
                raise SystemExit(
                    "natural MTSS verifier proof failed: "
                    f"outcome={mtss_result['outcome']} verdict={mtss_result['verdict']} "
                    f"error_code={mtss_result['error_code']}"
                )
            if not mtss_result["consumed_query_ids"]:
                report = _build_report(
                    args, model, db, selected_cases, phase_results, mtss_proposition, mtss_result,
                    status="BLOCKED",
                    failure={"case_id": "MTSS", "error_code": "mtss_supported_without_consumed_derivation"},
                )
                _emit_report(args.result, report, pass_token=False)
                raise SystemExit("natural MTSS proof produced supported verdict without consumed Derivation")

        report = _build_report(
            args,
            model,
            db,
            selected_cases,
            phase_results,
            mtss_proposition,
            mtss_result,
            status="PASS",
            failure=None,
        )
    _emit_report(args.result, report, pass_token=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
