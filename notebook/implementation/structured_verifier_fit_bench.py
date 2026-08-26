#!/usr/bin/env python3
"""Phase-D structured verifier fit bench for Canario.

This Notebook-only harness compares a deliberately simple Canario verifier loop with a
bounded Thucy protocol adaptation. Both systems use the same subscription-backed Codex CLI,
model, deterministic relational projection, hardened SQLite executor, Source Authority, and
hidden oracle. The current campaign uses the subscription-backed Codex reference profile;
metered API/provider profiles are allowed future adapters but are not part of this campaign.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Mapping, Sequence

BASE_DIR = Path(__file__).resolve().parent
FOUNDATION_PATH = BASE_DIR / "structured_reasoning_fit_bench.py"
WORKER_PATH = BASE_DIR / "structured_verifier_codex_worker.py"

PHASE_D_CASES_FORMAT = "canario.structured_verifier_fit_cases.v2"
WORKER_RESULT_FORMAT = "canario.verifier_codex_worker_result.v1"
PAIRED_RUN_FORMAT = "canario.structured_verifier_paired_run.v2"
SCORE_FORMAT = "canario.structured_verifier_score.v2"
COMPARISON_FORMAT = "canario.structured_verifier_comparison.v2"
PROVIDER_PROBE_FORMAT = "canario.codex_subscription_probe.v1"

THUCY_REPOSITORY = "https://github.com/thucy-ai/thucy"
THUCY_COMMIT = "feaecdb5bd876a09db507ed31e93dc9393940689"
THUCY_AGENTS_BLOB = "e7ca065a05dad6fa8992c87934c8874834f9b4bd"
THUCY_LICENSE_BLOB = "33c7f9f5e7e30d62c9a33f69c137ecaf9172f03a"
THUCY_PYPROJECT_BLOB = "cb8866f911326d07b1af83239f3b3800c4f2be9e"
THUCY_PROMPT_NAMES = (
    "DATA_EXPERT_PROMPT",
    "SCHEMA_EXPERT_PROMPT",
    "SQL_EXPERT_PROMPT",
    "VERIFIER_PROMPT",
)

DEFAULT_MODEL = "gpt-5.6-terra"
DEFAULT_REASONING_EFFORT = "medium"
DEFAULT_QUALIFIED_CODEX_VERSIONS = ("0.149.0",)
DEFAULT_MAX_SQL_CALLS = 6
DEFAULT_WORKER_TIMEOUT_SECONDS = 900
SIMPLE_SYSTEM = "simple_codex"
THUCY_SYSTEM = "thucy_bounded_codex_runtime_adapted"
THUCY_SETUP_SYSTEM = "thucy_setup_codex"


class VerifierFitError(ValueError):
    """Phase-D input/result violates a benchmark invariant."""


def _load_foundation():
    spec = importlib.util.spec_from_file_location("canario_structured_reasoning_foundation_phase_d_parent", FOUNDATION_PATH)
    if spec is None or spec.loader is None:
        raise VerifierFitError("cannot load structured reasoning foundation")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


foundation = _load_foundation()


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise VerifierFitError(f"{path} must contain a JSON object")
    return value


def _write_json(path: Path, value: object) -> str:
    data = _canonical_json_bytes(value)
    path.write_bytes(data)
    return _sha256_bytes(data)


def _typed_scalar_text(value: Mapping[str, object]) -> str:
    kind = value.get("type")
    if kind == "null":
        return "NULL"
    raw = value.get("value")
    if kind == "string":
        return json.dumps(str(raw), ensure_ascii=False)
    if kind == "boolean":
        return "true" if bool(raw) else "false"
    return str(raw)


def _expected_rows(case: Mapping[str, object]) -> list[list[dict[str, object]]]:
    expected = case.get("expected")
    if not isinstance(expected, dict):
        raise VerifierFitError(f"case {case.get('case_id')} has no expected result")
    rows = expected.get("rows")
    if not isinstance(rows, list) or not rows:
        raise VerifierFitError(f"case {case.get('case_id')} expected rows missing")
    normalized: list[list[dict[str, object]]] = []
    for row in rows:
        if not isinstance(row, list):
            raise VerifierFitError("expected result row malformed")
        normalized_row: list[dict[str, object]] = []
        for item in row:
            if not isinstance(item, dict):
                raise VerifierFitError("expected result value malformed")
            normalized_row.append(dict(item))
        normalized.append(normalized_row)
    return normalized


def _first_expected_row(case: Mapping[str, object]) -> list[dict[str, object]]:
    return _expected_rows(case)[0]


def _required_evidence(case: Mapping[str, object]) -> list[dict[str, object]]:
    raw = case.get("required_evidence", [])
    if not isinstance(raw, list):
        raise VerifierFitError("required_evidence must be a list")
    result: list[dict[str, object]] = []
    for item in raw:
        if not isinstance(item, dict):
            raise VerifierFitError("required evidence item malformed")
        result.append(dict(item))
    return result


def _find_case(cases: Sequence[object], case_id: str) -> dict[str, object]:
    for item in cases:
        if isinstance(item, dict) and item.get("case_id") == case_id:
            return dict(item)
    raise VerifierFitError(f"required deterministic case missing: {case_id}")


def _planner_case_map(planner: Mapping[str, object]) -> dict[str, dict[str, object]]:
    cases = planner.get("cases")
    if not isinstance(cases, list):
        raise VerifierFitError("planner handoff cases missing")
    result: dict[str, dict[str, object]] = {}
    for item in cases:
        if not isinstance(item, dict) or not isinstance(item.get("case_id"), str):
            raise VerifierFitError("planner handoff case malformed")
        case_id = str(item["case_id"])
        if case_id in result:
            raise VerifierFitError("planner handoff case IDs must be unique")
        result[case_id] = dict(item)
    return result


def _sheet_column_from_evidence(case: Mapping[str, object]) -> tuple[str, int, int]:
    evidence = _required_evidence(case)
    if not evidence:
        raise VerifierFitError(f"case {case.get('case_id')} needs evidence locators")
    first = evidence[0]
    return str(first.get("sheet_name", f"sheet_{first['sheet_ordinal']}")), int(first["sheet_ordinal"]), int(first["column"])


def _perturb_numeric(value: Mapping[str, object]) -> str:
    if value.get("type") not in {"integer", "number"}:
        raise VerifierFitError("numeric perturbation requires numeric typed result")
    try:
        base = Decimal(str(value.get("value")))
    except InvalidOperation as exc:
        raise VerifierFitError("invalid numeric oracle value") from exc
    delta = Decimal(1) if base == base.to_integral_value() else Decimal("0.01")
    return str(base + delta)


def _extract_absence_sentinel(case: Mapping[str, object]) -> str:
    sql = case.get("portable_sql")
    if not isinstance(sql, str):
        raise VerifierFitError("bounded absence case requires SQL")
    match = re.search(r"WHERE\s+value='((?:''|[^'])*)'", sql, flags=re.IGNORECASE)
    if not match:
        raise VerifierFitError("cannot recover frozen bounded-absence sentinel")
    return match.group(1).replace("''", "'")



def _projection_cell_index(projection: Mapping[str, object]) -> dict[tuple[int, int, int], dict[str, object]]:
    cells = projection.get("cells")
    if not isinstance(cells, list):
        raise VerifierFitError("projection cells missing")
    result: dict[tuple[int, int, int], dict[str, object]] = {}
    for raw in cells:
        if not isinstance(raw, dict):
            raise VerifierFitError("projection cell malformed")
        key = (int(raw["sheet_ordinal"]), int(raw["row"]), int(raw["column"]))
        if key in result:
            raise VerifierFitError("projection cell identity repeated")
        result[key] = raw
    return result


def _numeric_counterfactual(value: Mapping[str, object], *, direction: int = 1) -> dict[str, object]:
    kind = value.get("kind")
    if kind not in {"integer", "number"}:
        raise VerifierFitError("numeric counterfactual requires numeric projection value")
    try:
        current = Decimal(str(value["decimal"]))
    except (KeyError, InvalidOperation) as exc:
        raise VerifierFitError("numeric projection value malformed") from exc
    delta = Decimal("1000000000000") * (Decimal(1) if direction >= 0 else Decimal(-1))
    changed = current + delta
    if kind == "integer":
        return {"kind": "integer", "decimal": str(int(changed))}
    return {"kind": "number", "decimal": format(changed, "f")}


def _mutation_for_locator(
    index: Mapping[tuple[int, int, int], Mapping[str, object]],
    locator: Mapping[str, object],
    new_value: Mapping[str, object],
) -> dict[str, object]:
    key = (int(locator["sheet_ordinal"]), int(locator["row"]), int(locator["column"]))
    if key not in index:
        raise VerifierFitError(f"counterfactual locator does not reopen: {key}")
    return {
        "sheet_ordinal": key[0],
        "row": key[1],
        "column": key[2],
        "value": dict(new_value),
    }


def _apply_counterfactual_mutations(
    projection_bytes: bytes, mutations: Sequence[Mapping[str, object]]
) -> bytes:
    try:
        projection = json.loads(projection_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerifierFitError("projection cannot be decoded for hidden counterfactual proof") from exc
    if not isinstance(projection, dict):
        raise VerifierFitError("counterfactual projection must be an object")
    cells = projection.get("cells")
    if not isinstance(cells, list):
        raise VerifierFitError("counterfactual projection cells missing")
    by_key: dict[tuple[int, int, int], dict[str, object]] = {}
    for raw in cells:
        if isinstance(raw, dict):
            by_key[(int(raw["sheet_ordinal"]), int(raw["row"]), int(raw["column"]))] = raw
    touched: set[tuple[int, int, int]] = set()
    for mutation in mutations:
        key = (int(mutation["sheet_ordinal"]), int(mutation["row"]), int(mutation["column"]))
        cell = by_key.get(key)
        value = mutation.get("value")
        if cell is None or not isinstance(value, dict) or key in touched:
            raise VerifierFitError("counterfactual mutation malformed or repeated")
        if cell.get("value") == value:
            raise VerifierFitError("counterfactual mutation must change source-derived value")
        cell["value"] = dict(value)
        touched.add(key)
    if len(touched) != len(mutations):
        raise VerifierFitError("counterfactual mutation coverage mismatch")
    return _canonical_json_bytes(projection)


def _result_match_obligation(expected: Mapping[str, object], *, required_tables: Sequence[str]) -> dict[str, object]:
    return {"kind": "exact_result", "expected": dict(expected), "required_tables": list(required_tables)}


def _scalar_obligation(value: Mapping[str, object], *, required_tables: Sequence[str]) -> dict[str, object]:
    return {"kind": "contains_scalar", "value": dict(value), "required_tables": list(required_tables)}


def _bounded_absence_obligation(
    zero_value: Mapping[str, object], *, required_tables: Sequence[str]
) -> dict[str, object]:
    return {
        "kind": "zero_result_for_each_required_table",
        "value": dict(zero_value),
        "required_tables": list(required_tables),
    }


def _row_sets_obligation(
    rows: Sequence[Sequence[Mapping[str, object]]],
    *,
    required_tables: Sequence[str],
    exact_row_count: bool = False,
) -> dict[str, object]:
    return {
        "kind": "exact_row_value_sets" if exact_row_count else "contains_row_value_sets",
        "rows": [[dict(item) for item in row] for row in rows],
        "required_tables": list(required_tables),
    }


def _case_record(
    *,
    phase_case_id: str,
    base: Mapping[str, object],
    planner: Mapping[str, object],
    claim: str,
    expected_verdict: str,
    expected_sufficiency: str,
    evidence_required: bool,
    evidence_obligation: Mapping[str, object] | None,
    counterfactual_mutations: Sequence[Mapping[str, object]] = (),
    authority_override: Mapping[str, object] | None = None,
) -> dict[str, object]:
    resource_budget = dict(planner.get("resource_budget", {}))
    resource_budget["max_sql_calls"] = DEFAULT_MAX_SQL_CALLS
    resource_budget["semantic_attempts"] = 1
    return {
        "case_id": phase_case_id,
        "base_case_id": base["case_id"],
        "claim": claim,
        "source_authority": dict(authority_override or planner.get("source_authority", {})),
        "expected_verdict": expected_verdict,
        "expected_sufficiency": expected_sufficiency,
        "evidence_required": evidence_required,
        "evidence_obligation": dict(evidence_obligation) if evidence_obligation is not None else None,
        "counterfactual_mutations": [dict(item) for item in counterfactual_mutations],
        "required_evidence": _required_evidence(base),
        "resource_budget": resource_budget,
    }


def build_phase_d_cases(
    projection_bytes: bytes,
    query_corpus: Mapping[str, object],
    planner_handoff: Mapping[str, object],
) -> dict[str, object]:
    """Build the hidden-oracle Phase-D corpus from the already frozen deterministic cases."""

    foundation.validate_query_corpus(query_corpus, projection_bytes)
    if planner_handoff.get("format") != foundation.PLANNER_CASES_FORMAT:
        raise VerifierFitError("unexpected planner handoff format")
    projection_sha = _sha256_bytes(projection_bytes)
    if planner_handoff.get("projection_sha256") != projection_sha:
        raise VerifierFitError("planner handoff projection identity mismatch")
    query_cases = query_corpus.get("cases")
    if not isinstance(query_cases, list):
        raise VerifierFitError("query corpus cases missing")
    planner_map = _planner_case_map(planner_handoff)
    projection = foundation.load_projection(projection_bytes)
    raw_sheets = projection.get("sheets")
    if not isinstance(raw_sheets, list):
        raise VerifierFitError("projection sheets missing")
    all_sheet_tables = [f"sheet_{int(sheet['ordinal'])}_rows" for sheet in raw_sheets if isinstance(sheet, dict)]

    q1 = _find_case(query_cases, "ESP-Q1-LOOKUP")
    q3 = _find_case(query_cases, "ESP-Q3-AGGREGATE")
    q5 = _find_case(query_cases, "ESP-Q5-TOPK")
    q8 = _find_case(query_cases, "ESP-Q8-CROSS-SHEET")
    q9 = _find_case(query_cases, "ESP-Q9-BOUNDED-ABSENCE")
    q10 = _find_case(query_cases, "ESP-Q10-INSUFFICIENT")

    q1_row = _first_expected_row(q1)
    q1_evidence = _required_evidence(q1)
    if len(q1_evidence) < 2:
        raise VerifierFitError("lookup case needs two evidence refs")
    q1_claim = (
        f"Within the bounded workbook projection, sheet {q1_evidence[0]['sheet_ordinal']} "
        f"row {q1_evidence[0]['row']} has represented string value {_typed_scalar_text(q1_row[0])} "
        f"and represented numeric value {_typed_scalar_text(q1_row[1])}."
    )

    q3_row = _first_expected_row(q3)
    sheet_name, sheet_ordinal, numeric_column = _sheet_column_from_evidence(q3)
    total_text = _typed_scalar_text(q3_row[0])
    q3_supported = (
        f"Within the complete bounded projection of sheet {sheet_ordinal} ({sheet_name}), "
        f"the sum of represented numeric values in column {numeric_column} is {total_text}."
    )
    q3_contradicted = (
        f"Within the complete bounded projection of sheet {sheet_ordinal} ({sheet_name}), "
        f"the sum of represented numeric values in column {numeric_column} is {_perturb_numeric(q3_row[0])}."
    )

    q8_rows = _expected_rows(q8)
    q8_evidence = _required_evidence(q8)
    sheet_groups: list[tuple[int, int]] = []
    for ref in q8_evidence:
        pair = (int(ref["sheet_ordinal"]), int(ref["column"]))
        if pair not in sheet_groups:
            sheet_groups.append(pair)
    if len(sheet_groups) < 2:
        raise VerifierFitError("cross-sheet case needs two source sheet/column groups")
    cross_key = _typed_scalar_text(q8_rows[0][2])
    join_pairs = ", ".join(f"({_typed_scalar_text(row[0])}, {_typed_scalar_text(row[1])})" for row in q8_rows)
    q8_claim = (
        f"Within this complete retained workbook projection, joining sheet {sheet_groups[0][0]} "
        f"column {sheet_groups[0][1]} to sheet {sheet_groups[1][0]} column {sheet_groups[1][1]} "
        f"on the represented string key {cross_key} yields exactly these (left row, right row) pairs: "
        f"[{join_pairs}]."
    )

    q5_rows = _expected_rows(q5)
    q5_evidence = _required_evidence(q5)
    _, q5_sheet, q5_column = _sheet_column_from_evidence(q5)
    impossible_row = max(int(ref["row"]) for ref in q5_evidence) + 1000
    asserted_top_rows: list[str] = []
    for index, row in enumerate(q5_rows):
        row_text = str(impossible_row) if index == 0 else _typed_scalar_text(row[0])
        asserted_top_rows.append(f"({row_text}, {_typed_scalar_text(row[1])})")
    q5_claim = (
        f"Within sheet {q5_sheet}, the three greatest represented numeric values in column {q5_column}, "
        f"ordered by value descending and row ascending for ties, are exactly these (row, value) pairs: "
        f"[{', '.join(asserted_top_rows)}]."
    )

    sentinel = _extract_absence_sentinel(q9)
    q9_claim = (
        f"Within this complete retained workbook projection, the exact string {json.dumps(sentinel, ensure_ascii=False)} "
        "is absent from every represented cell."
    )
    q10_claim = "This retained workbook proves that no other municipal budget modification exists outside this workbook."
    global_total_claim = (
        "This retained workbook proves that the municipality's total spending across all records and all other "
        f"possible budget documents is exactly {total_text}."
    )
    bounded_workbook_authority = {
        "scope": "complete retained workbook projection",
        "inventory_completeness": "complete_within_retained_representation",
        "claim_strength_limit": "may support values/computations inside this workbook only",
    }
    global_authority = {
        "scope": "one retained workbook",
        "inventory_completeness": "not_established_outside_this_workbook",
        "claim_strength_limit": "may support values/computations inside this workbook only",
    }

    cell_index = _projection_cell_index(projection)
    d1_key = (int(q1_evidence[0]["sheet_ordinal"]), int(q1_evidence[0]["row"]), int(q1_evidence[0]["column"]))
    d1_value = cell_index[d1_key].get("value")
    if not isinstance(d1_value, dict) or d1_value.get("kind") != "string":
        raise VerifierFitError("lookup counterfactual requires represented string evidence")
    d1_mutations = [
        _mutation_for_locator(
            cell_index,
            q1_evidence[0],
            {"kind": "string", "text": f"__CANARIO_CF_D1_{projection_sha[:12]}__"},
        )
    ]

    q3_evidence = _required_evidence(q3)
    if not q3_evidence:
        raise VerifierFitError("aggregate counterfactual requires numeric source evidence")
    q3_key = (int(q3_evidence[0]["sheet_ordinal"]), int(q3_evidence[0]["row"]), int(q3_evidence[0]["column"]))
    q3_value = cell_index[q3_key].get("value")
    if not isinstance(q3_value, dict):
        raise VerifierFitError("aggregate counterfactual source value malformed")
    aggregate_mutations = [
        _mutation_for_locator(cell_index, q3_evidence[0], _numeric_counterfactual(q3_value, direction=1))
    ]

    q5_top_row = int(str(q5_rows[0][0]["value"]))
    q5_locator = next(
        (
            ref
            for ref in q5_evidence
            if int(ref["row"]) == q5_top_row and int(ref["column"]) == q5_column
        ),
        None,
    )
    if not isinstance(q5_locator, dict):
        raise VerifierFitError("top-k counterfactual cannot reopen top-row evidence")
    q5_key = (int(q5_locator["sheet_ordinal"]), int(q5_locator["row"]), int(q5_locator["column"]))
    q5_value = cell_index[q5_key].get("value")
    if not isinstance(q5_value, dict):
        raise VerifierFitError("top-k counterfactual source value malformed")
    topk_mutations = [
        _mutation_for_locator(cell_index, q5_locator, _numeric_counterfactual(q5_value, direction=-1))
    ]

    q8_locator = q8_evidence[0]
    q8_key = (int(q8_locator["sheet_ordinal"]), int(q8_locator["row"]), int(q8_locator["column"]))
    q8_value = cell_index[q8_key].get("value")
    if not isinstance(q8_value, dict) or q8_value.get("kind") != "string":
        raise VerifierFitError("cross-sheet counterfactual requires string join evidence")
    cross_sheet_mutations = [
        _mutation_for_locator(
            cell_index,
            q8_locator,
            {"kind": "string", "text": f"__CANARIO_CF_D4_{projection_sha[:12]}__"},
        )
    ]

    first_string_cell = next(
        (
            cell
            for cell in cell_index.values()
            if isinstance(cell.get("value"), dict) and cell["value"].get("kind") == "string"
        ),
        None,
    )
    if not isinstance(first_string_cell, dict):
        raise VerifierFitError("bounded-absence counterfactual needs at least one string cell")
    absence_mutations = [
        {
            "sheet_ordinal": int(first_string_cell["sheet_ordinal"]),
            "row": int(first_string_cell["row"]),
            "column": int(first_string_cell["column"]),
            "value": {"kind": "string", "text": sentinel},
        }
    ]

    cases = [
        _case_record(
            phase_case_id="D1-SUPPORTED-LOOKUP",
            base=q1,
            planner=planner_map[str(q1["case_id"])],
            claim=q1_claim,
            expected_verdict="supported",
            expected_sufficiency="adequate",
            evidence_required=True,
            evidence_obligation=_row_sets_obligation([q1_row], required_tables=[f"sheet_{int(q1_evidence[0]['sheet_ordinal'])}_rows"]),
            counterfactual_mutations=d1_mutations,
            authority_override=bounded_workbook_authority,
        ),
        _case_record(
            phase_case_id="D2-SUPPORTED-AGGREGATE",
            base=q3,
            planner=planner_map[str(q3["case_id"])],
            claim=q3_supported,
            expected_verdict="supported",
            expected_sufficiency="adequate",
            evidence_required=True,
            evidence_obligation=_scalar_obligation(q3_row[0], required_tables=[f"sheet_{sheet_ordinal}_rows"]),
            counterfactual_mutations=aggregate_mutations,
            authority_override=bounded_workbook_authority,
        ),
        _case_record(
            phase_case_id="D3-CONTRADICTED-AGGREGATE",
            base=q3,
            planner=planner_map[str(q3["case_id"])],
            claim=q3_contradicted,
            expected_verdict="contradicted",
            expected_sufficiency="adequate",
            evidence_required=True,
            evidence_obligation=_scalar_obligation(q3_row[0], required_tables=[f"sheet_{sheet_ordinal}_rows"]),
            counterfactual_mutations=aggregate_mutations,
            authority_override=bounded_workbook_authority,
        ),
        _case_record(
            phase_case_id="D4-SUPPORTED-CROSS-SHEET",
            base=q8,
            planner=planner_map[str(q8["case_id"])],
            claim=q8_claim,
            expected_verdict="supported",
            expected_sufficiency="adequate",
            evidence_required=True,
            evidence_obligation=_row_sets_obligation([[row[0], row[1]] for row in q8_rows], required_tables=[f"sheet_{sheet_groups[0][0]}_rows", f"sheet_{sheet_groups[1][0]}_rows"], exact_row_count=True),
            counterfactual_mutations=cross_sheet_mutations,
            authority_override=bounded_workbook_authority,
        ),
        _case_record(
            phase_case_id="D5-CONTRADICTED-TOPK",
            base=q5,
            planner=planner_map[str(q5["case_id"])],
            claim=q5_claim,
            expected_verdict="contradicted",
            expected_sufficiency="adequate",
            evidence_required=True,
            evidence_obligation=_row_sets_obligation(q5_rows, required_tables=[f"sheet_{q5_sheet}_rows"], exact_row_count=True),
            counterfactual_mutations=topk_mutations,
            authority_override=bounded_workbook_authority,
        ),
        _case_record(
            phase_case_id="D6-SUPPORTED-BOUNDED-ABSENCE",
            base=q9,
            planner=planner_map[str(q9["case_id"])],
            claim=q9_claim,
            expected_verdict="supported",
            expected_sufficiency="adequate",
            evidence_required=True,
            evidence_obligation=_bounded_absence_obligation(
                _first_expected_row(q9)[0], required_tables=all_sheet_tables
            ),
            counterfactual_mutations=absence_mutations,
        ),
        _case_record(
            phase_case_id="D7-INSUFFICIENT-GLOBAL-ABSENCE",
            base=q10,
            planner=planner_map[str(q10["case_id"])],
            claim=q10_claim,
            expected_verdict="insufficient_evidence",
            expected_sufficiency="inadequate",
            evidence_required=False,
            evidence_obligation=None,
        ),
        _case_record(
            phase_case_id="D8-INSUFFICIENT-GLOBAL-TOTAL",
            base=q3,
            planner=planner_map[str(q3["case_id"])],
            claim=global_total_claim,
            expected_verdict="insufficient_evidence",
            expected_sufficiency="inadequate",
            evidence_required=False,
            evidence_obligation=None,
            authority_override=global_authority,
        ),
    ]
    return {
        "format": PHASE_D_CASES_FORMAT,
        "projection_sha256": projection_sha,
        "source_query_corpus_sha256": _sha256_bytes(_canonical_json_bytes(query_corpus)),
        "source_planner_handoff_sha256": _sha256_bytes(_canonical_json_bytes(planner_handoff)),
        "case_count": len(cases),
        "gold_visible_to_model": False,
        "model_execution_profile": {
            "current_transport_profile": "openai_codex_subscription",
            "billing_mode": "chatgpt_subscription",
            "per_token_api_billing": False,
            "current_profile_per_token_api_billing": False,
            "current_profile_api_key_required": False,
            "automatic_metered_fallback": False,
            "future_metered_provider_profiles_allowed": True,
            "future_provider_profiles_status": "deferred",
            "default_model": DEFAULT_MODEL,
            "default_reasoning_effort": DEFAULT_REASONING_EFFORT,
            "same_model_both_systems": True,
            "semantic_retries": 0,
        },
        "cases": cases,
    }


def validate_phase_d_cases(cases: Mapping[str, object], projection_bytes: bytes) -> dict[str, object]:
    if cases.get("format") != PHASE_D_CASES_FORMAT:
        raise VerifierFitError("unexpected Phase-D cases format")
    if cases.get("projection_sha256") != _sha256_bytes(projection_bytes):
        raise VerifierFitError("Phase-D projection identity mismatch")
    profile = cases.get("model_execution_profile")
    if not isinstance(profile, dict):
        raise VerifierFitError("Phase-D model execution profile missing")
    expected_profile = {
        "current_transport_profile": "openai_codex_subscription",
        "billing_mode": "chatgpt_subscription",
        "per_token_api_billing": False,
        "current_profile_per_token_api_billing": False,
        "current_profile_api_key_required": False,
        "automatic_metered_fallback": False,
        "future_metered_provider_profiles_allowed": True,
        "future_provider_profiles_status": "deferred",
        "default_model": DEFAULT_MODEL,
        "default_reasoning_effort": DEFAULT_REASONING_EFFORT,
        "same_model_both_systems": True,
        "semantic_retries": 0,
    }
    if profile != expected_profile:
        raise VerifierFitError("Phase-D model execution profile mismatch")
    raw_cases = cases.get("cases")
    if not isinstance(raw_cases, list) or len(raw_cases) != 8:
        raise VerifierFitError("Phase-D corpus must contain exactly eight cases")
    ids: set[str] = set()
    expected_counts = {"supported": 0, "contradicted": 0, "insufficient_evidence": 0}
    for raw in raw_cases:
        if not isinstance(raw, dict):
            raise VerifierFitError("Phase-D case malformed")
        case_id = raw.get("case_id")
        if not isinstance(case_id, str) or not case_id or case_id in ids:
            raise VerifierFitError("Phase-D case IDs must be unique")
        ids.add(case_id)
        verdict = raw.get("expected_verdict")
        if verdict not in expected_counts:
            raise VerifierFitError(f"invalid expected verdict for {case_id}")
        expected_counts[str(verdict)] += 1
        sufficiency = raw.get("expected_sufficiency")
        if sufficiency not in {"adequate", "inadequate"}:
            raise VerifierFitError("invalid expected sufficiency")
        if verdict == "insufficient_evidence" and sufficiency != "inadequate":
            raise VerifierFitError("insufficient evidence must have inadequate sufficiency")
        if verdict != "insufficient_evidence" and sufficiency != "adequate":
            raise VerifierFitError("decisive verdicts require adequate expected sufficiency")
        obligation = raw.get("evidence_obligation")
        mutations = raw.get("counterfactual_mutations")
        if raw.get("evidence_required") is True:
            if not isinstance(obligation, dict) or obligation.get("kind") not in {
                "exact_result", "contains_scalar", "contains_row_value_sets", "exact_row_value_sets",
                "zero_result_for_each_required_table"
            }:
                raise VerifierFitError("evidence-required case needs a typed hidden obligation")
            if not isinstance(mutations, list) or not mutations or not all(isinstance(item, dict) for item in mutations):
                raise VerifierFitError("evidence-required case needs hidden counterfactual mutations")
        elif obligation is not None or mutations not in ([], None):
            raise VerifierFitError("non-evidence case must not carry hidden evidence/counterfactual obligations")
        if not isinstance(raw.get("source_authority"), dict):
            raise VerifierFitError("case requires Source Authority scope")
        budget = raw.get("resource_budget")
        if not isinstance(budget, dict) or int(budget.get("max_sql_calls", 0)) != DEFAULT_MAX_SQL_CALLS:
            raise VerifierFitError("case SQL-call budget mismatch")
    return {"case_count": len(ids), "expected_verdict_counts": expected_counts}


def model_visible_case(case: Mapping[str, object], projection_sha256: str) -> dict[str, object]:
    allowed = {
        "case_id": case["case_id"],
        "claim": case["claim"],
        "source_authority": case["source_authority"],
        "projection_sha256": projection_sha256,
        "resource_budget": case.get("resource_budget", {}),
    }
    forbidden = {
        "expected_verdict",
        "expected_sufficiency",
        "evidence_obligation",
        "required_evidence",
        "counterfactual_mutations",
    }
    if forbidden & set(allowed):
        raise AssertionError("gold leaked into model-visible case")
    return allowed


def render_case_prompt(case: Mapping[str, object], projection_sha256: str) -> str:
    visible = model_visible_case(case, projection_sha256)
    return (
        "Verify exactly one proposition using only the bounded Canario projection evidence supplied through this benchmark.\n"
        "Do not use web knowledge or infer facts outside the declared Source Authority scope.\n"
        "A successful local lookup does not establish global completeness.\n"
        "A rejected/failed query is an execution problem, not evidence that a proposition is unsupported or unknowable.\n\n"
        f"Case ID: {visible['case_id']}\n"
        f"Projection SHA256: {projection_sha256}\n"
        f"Source Authority: {json.dumps(visible['source_authority'], ensure_ascii=False, sort_keys=True)}\n"
        f"Resource budget: {json.dumps(visible['resource_budget'], ensure_ascii=False, sort_keys=True)}\n"
        f"Claim: {visible['claim']}\n"
    )


def _extract_prompt_literals(source: str) -> dict[str, str]:
    tree = ast.parse(source)
    values: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        name = node.targets[0].id
        if name not in THUCY_PROMPT_NAMES:
            continue
        value = ast.literal_eval(node.value)
        if not isinstance(value, str):
            raise VerifierFitError(f"Thucy prompt {name} is not a string literal")
        values[name] = value
    missing = [name for name in THUCY_PROMPT_NAMES if name not in values]
    if missing:
        raise VerifierFitError("Thucy prompt extraction failed: " + ", ".join(missing))
    return values


def verify_thucy_checkout(thucy_root: Path) -> dict[str, object]:
    """Verify exact Thucy source and extract prompt identity without importing/executing it."""

    if not (thucy_root / ".git").exists():
        raise VerifierFitError("Thucy root must be an exact git checkout")
    head = subprocess.check_output(["git", "-C", str(thucy_root), "rev-parse", "HEAD"], text=True).strip()
    if head != THUCY_COMMIT:
        raise VerifierFitError(f"Thucy HEAD mismatch: {head}")
    status = subprocess.check_output(["git", "-C", str(thucy_root), "status", "--short"], text=True)
    if status.strip():
        raise VerifierFitError("Thucy checkout must be clean")
    expected_blobs = {
        "thucy/agents.py": THUCY_AGENTS_BLOB,
        "LICENSE": THUCY_LICENSE_BLOB,
        "pyproject.toml": THUCY_PYPROJECT_BLOB,
    }
    observed: dict[str, str] = {}
    for path, expected in expected_blobs.items():
        blob = subprocess.check_output(["git", "-C", str(thucy_root), "rev-parse", f"HEAD:{path}"], text=True).strip()
        if blob != expected:
            raise VerifierFitError(f"Thucy blob mismatch for {path}")
        observed[path] = blob
    agents_source = (thucy_root / "thucy" / "agents.py").read_text(encoding="utf-8")
    prompts = _extract_prompt_literals(agents_source)
    return {
        "repository": THUCY_REPOSITORY,
        "commit": head,
        "blobs": observed,
        "prompt_sha256": {name: _sha256_text(text) for name, text in prompts.items()},
        "license_metadata_conflict": True,
        "vendoring_authorized": False,
        "source_imported_or_executed": False,
        "runtime_adaptation": "exact prompts/topology translated to subscription-backed Codex CLI orchestration",
    }


def _worker_request(
    *,
    system: str,
    projection_path: Path | None,
    projection_sha256: str | None,
    model: str,
    reasoning_effort: str,
    codex_home: Path,
    codex: str,
    case_id: str | None = None,
    prompt: str | None = None,
    thucy_root: Path | None = None,
    thucy_shared_context: Mapping[str, str] | None = None,
    source_authority: Mapping[str, object] | None = None,
) -> dict[str, object]:
    request: dict[str, object] = {
        "mode": "case" if system not in {"provider_probe", THUCY_SETUP_SYSTEM} else ("probe" if system == "provider_probe" else "setup"),
        "system": SIMPLE_SYSTEM if system == "provider_probe" else system,
        "model": model,
        "reasoning_effort": reasoning_effort,
        "codex_home": str(codex_home),
        "codex": codex,
        "qualified_codex_versions": list(DEFAULT_QUALIFIED_CODEX_VERSIONS),
        "max_sql_calls": DEFAULT_MAX_SQL_CALLS,
    }
    if projection_path is not None:
        request["projection_path"] = str(projection_path)
    if projection_sha256 is not None:
        request["projection_sha256"] = projection_sha256
    if case_id is not None:
        request["case_id"] = case_id
    if prompt is not None:
        request["prompt"] = prompt
    if thucy_root is not None:
        request["thucy_root"] = str(thucy_root)
    if thucy_shared_context is not None:
        request["thucy_shared_context"] = dict(thucy_shared_context)
    if source_authority is not None:
        request["source_authority"] = dict(source_authority)
    return request


def _spawn_worker(*, request: Mapping[str, object], timeout_seconds: int = DEFAULT_WORKER_TIMEOUT_SECONDS) -> dict[str, object]:
    started = time.monotonic()
    process = subprocess.run(
        [sys.executable, str(WORKER_PATH)],
        input=_canonical_json_bytes(request),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_seconds,
        check=False,
        env={"LC_ALL": "C.UTF-8", "LANG": "C.UTF-8", "PATH": os.environ.get("PATH", os.defpath), **{
            key: os.environ[key]
            for key in ("DBUS_SESSION_BUS_ADDRESS", "XDG_RUNTIME_DIR", "SSL_CERT_FILE", "SSL_CERT_DIR")
            if key in os.environ
        }},
    )
    duration_ms = round((time.monotonic() - started) * 1000.0, 3)
    if process.returncode != 0:
        return {
            "format": WORKER_RESULT_FORMAT,
            "status": "execution_failed",
            "system": request.get("system"),
            "case_id": request.get("case_id"),
            "error_code": "worker_process_failed",
            "returncode": process.returncode,
            "stderr": process.stderr.decode("utf-8", errors="replace")[-4000:],
            "parent_duration_ms": duration_ms,
        }
    try:
        payload = json.loads(process.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerifierFitError("worker returned invalid JSON") from exc
    if not isinstance(payload, dict) or payload.get("format") != WORKER_RESULT_FORMAT:
        raise VerifierFitError("worker returned unexpected result format")
    payload.setdefault("parent_duration_ms", duration_ms)
    return payload


def provider_probe(*, codex_home: Path, codex: str, model: str, reasoning_effort: str) -> dict[str, object]:
    request = _worker_request(
        system="provider_probe",
        projection_path=None,
        projection_sha256=None,
        model=model,
        reasoning_effort=reasoning_effort,
        codex_home=codex_home,
        codex=codex,
    )
    result = _spawn_worker(request=request, timeout_seconds=300)
    provider = result.get("provider") if isinstance(result.get("provider"), dict) else {}
    return {
        "format": PROVIDER_PROBE_FORMAT,
        "model": model,
        "reasoning_effort": reasoning_effort,
        "worker": result,
        "pass": (
            result.get("status") == "completed"
            and result.get("probe_pass") is True
            and provider.get("per_token_api_billing") is False
            and provider.get("api_key_used") is False
        ),
    }


def _campaign_setup_authority() -> dict[str, object]:
    return {
        "scope": "one retained deterministic workbook projection",
        "inventory_completeness": "claim_specific; each lead-verifier case receives its exact Source Authority scope",
        "external_sources": "none",
    }


def validate_provider_probe_for_campaign(
    probe: Mapping[str, object], *, model: str, reasoning_effort: str
) -> dict[str, object]:
    if probe.get("format") != PROVIDER_PROBE_FORMAT or probe.get("pass") is not True:
        raise VerifierFitError("paired campaign requires a passing subscription provider probe")
    if probe.get("model") != model or probe.get("reasoning_effort") != reasoning_effort:
        raise VerifierFitError("provider probe model/reasoning does not match paired campaign")
    worker_result = probe.get("worker")
    if not isinstance(worker_result, dict) or worker_result.get("status") != "completed":
        raise VerifierFitError("provider probe worker is not completed")
    provider = worker_result.get("provider")
    if not isinstance(provider, dict):
        raise VerifierFitError("provider probe identity missing")
    required = {
        "execution_venue": "subscription_agent",
        "provider": "openai",
        "model": model,
        "reasoning_effort": reasoning_effort,
        "endpoint_profile": "openai_codex_subscription",
        "auth_store": "keyring",
        "per_token_api_billing": False,
        "api_key_used": False,
    }
    for key, value in required.items():
        if provider.get(key) != value:
            raise VerifierFitError(f"provider probe identity mismatch for {key}")
    return {
        "probe_sha256": _sha256_bytes(_canonical_json_bytes(probe)),
        "provider": dict(provider),
    }


def run_paired_campaign(
    *,
    projection_path: Path,
    cases_doc: Mapping[str, object],
    model: str,
    reasoning_effort: str,
    codex_home: Path,
    codex: str,
    thucy_root: Path,
    provider_probe_doc: Mapping[str, object],
) -> dict[str, object]:
    projection_bytes = projection_path.read_bytes()
    validate_phase_d_cases(cases_doc, projection_bytes)
    profile = cases_doc["model_execution_profile"]
    if not isinstance(profile, dict):
        raise VerifierFitError("validated Phase-D profile unexpectedly missing")
    if model != profile["default_model"] or reasoning_effort != profile["default_reasoning_effort"]:
        raise VerifierFitError("paired campaign must use the frozen Phase-D model/reasoning profile")
    provider_gate = validate_provider_probe_for_campaign(
        provider_probe_doc, model=model, reasoning_effort=reasoning_effort
    )
    thucy_identity = verify_thucy_checkout(thucy_root)
    projection_sha = str(cases_doc["projection_sha256"])

    setup_request = _worker_request(
        system=THUCY_SETUP_SYSTEM,
        projection_path=projection_path,
        projection_sha256=projection_sha,
        model=model,
        reasoning_effort=reasoning_effort,
        codex_home=codex_home,
        codex=codex,
        thucy_root=thucy_root,
        source_authority=_campaign_setup_authority(),
    )
    setup = _spawn_worker(request=setup_request)
    if setup.get("status") != "completed" or not isinstance(setup.get("shared_context"), dict):
        return {
            "format": PAIRED_RUN_FORMAT,
            "status": "environment_or_setup_failed",
            "cases_sha256": _sha256_bytes(_canonical_json_bytes(cases_doc)),
            "projection_sha256": projection_sha,
            "model": model,
            "reasoning_effort": reasoning_effort,
            "billing_mode": "chatgpt_subscription",
            "per_token_api_billing": False,
            "provider_gate": provider_gate,
            "thucy": thucy_identity,
            "thucy_setup": setup,
            "runs": [],
        }
    shared = setup["shared_context"]
    if not isinstance(shared, dict):
        raise VerifierFitError("completed Thucy setup returned malformed shared context")

    raw_cases = cases_doc["cases"]
    if not isinstance(raw_cases, list):
        raise VerifierFitError("validated Phase-D cases unexpectedly missing")
    runs: list[dict[str, object]] = []
    for index, case in enumerate(raw_cases):
        if not isinstance(case, dict):
            raise VerifierFitError("validated Phase-D case unexpectedly malformed")
        order = [SIMPLE_SYSTEM, THUCY_SYSTEM] if index % 2 == 0 else [THUCY_SYSTEM, SIMPLE_SYSTEM]
        system_results: list[dict[str, object]] = []
        for system in order:
            request = _worker_request(
                system=system,
                projection_path=projection_path,
                projection_sha256=projection_sha,
                model=model,
                reasoning_effort=reasoning_effort,
                codex_home=codex_home,
                codex=codex,
                case_id=str(case["case_id"]),
                prompt=render_case_prompt(case, projection_sha),
                thucy_root=thucy_root if system == THUCY_SYSTEM else None,
                thucy_shared_context={"data_report": str(shared["data_report"]), "schema_answer": str(shared["schema_answer"])}
                if system == THUCY_SYSTEM
                else None,
            )
            system_results.append(_spawn_worker(request=request))
        runs.append({"case_id": case["case_id"], "execution_order": order, "systems": system_results})
    return {
        "format": PAIRED_RUN_FORMAT,
        "status": "completed",
        "cases_sha256": _sha256_bytes(_canonical_json_bytes(cases_doc)),
        "projection_sha256": projection_sha,
        "model": model,
        "reasoning_effort": reasoning_effort,
        "billing_mode": "chatgpt_subscription",
        "per_token_api_billing": False,
        "api_key_used": False,
        "provider_gate": provider_gate,
        "thucy": thucy_identity,
        "thucy_setup": setup,
        "one_scored_attempt_per_system_case": True,
        "semantic_retry": False,
        "runs": runs,
    }


def _normalize_sql(sql: str) -> str:
    return " ".join(sql.strip().rstrip(";").split()).lower()


def _sql_blocks(text: str) -> list[str]:
    return [match.group(1).strip() for match in re.finditer(r"```sql\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)]


def _successful_sql_events(worker: Mapping[str, object]) -> list[dict[str, object]]:
    events = worker.get("tool_events", [])
    if not isinstance(events, list):
        return []
    return [
        dict(event)
        for event in events
        if isinstance(event, dict) and event.get("tool") == "execute_sql" and event.get("outcome") == "success"
    ]


def _typed_value_equal(left: Mapping[str, object], right: Mapping[str, object]) -> bool:
    lt = left.get("type")
    rt = right.get("type")
    if lt in {"integer", "number"} and rt in {"integer", "number"}:
        try:
            return Decimal(str(left.get("value"))) == Decimal(str(right.get("value")))
        except InvalidOperation:
            return False
    return dict(left) == dict(right)


def _row_contains_values(row: Sequence[object], expected: Sequence[Mapping[str, object]]) -> bool:
    typed = [item for item in row if isinstance(item, dict)]
    used: set[int] = set()
    for wanted in expected:
        found = None
        for index, actual in enumerate(typed):
            if index not in used and _typed_value_equal(actual, wanted):
                found = index
                break
        if found is None:
            return False
        used.add(found)
    return True


def _result_satisfies_obligation(result: Mapping[str, object], obligation: Mapping[str, object]) -> bool:
    kind = obligation.get("kind")
    if kind == "exact_result":
        expected = obligation.get("expected")
        return isinstance(expected, dict) and foundation.compare_results(result, expected).get("agree") is True
    rows = result.get("rows")
    if not isinstance(rows, list):
        return False
    if kind == "contains_scalar":
        expected = obligation.get("value")
        if not isinstance(expected, dict):
            return False
        return any(
            isinstance(row, list)
            and any(isinstance(item, dict) and _typed_value_equal(item, expected) for item in row)
            for row in rows
        )
    if kind in {"contains_row_value_sets", "exact_row_value_sets"}:
        patterns = obligation.get("rows")
        if not isinstance(patterns, list):
            return False
        if kind == "exact_row_value_sets" and len(rows) != len(patterns):
            return False
        unmatched = [row for row in rows if isinstance(row, list)]
        for pattern in patterns:
            if not isinstance(pattern, list) or not all(isinstance(item, dict) for item in pattern):
                return False
            match_index = next((i for i, row in enumerate(unmatched) if _row_contains_values(row, pattern)), None)
            if match_index is None:
                return False
            unmatched.pop(match_index)
        return True
    return False


def _sql_reads_required_tables(sql: str, obligation: Mapping[str, object]) -> bool:
    required = obligation.get("required_tables", [])
    if not isinstance(required, list) or not all(isinstance(item, str) for item in required):
        return False
    normalized = sql.lower()
    return all(re.search(rf"\b{re.escape(table.lower())}\b", normalized) is not None for table in required)


def _evidence_obligation_match(worker: Mapping[str, object], obligation: Mapping[str, object] | None) -> bool:
    if obligation is None:
        return False
    successful = _successful_sql_events(worker)
    if obligation.get("kind") == "zero_result_for_each_required_table":
        required = obligation.get("required_tables", [])
        zero_value = obligation.get("value")
        if (
            not isinstance(required, list)
            or not required
            or not all(isinstance(item, str) for item in required)
            or not isinstance(zero_value, dict)
        ):
            return False
        covered: set[str] = set()
        scalar_obligation = {"kind": "contains_scalar", "value": zero_value}
        for event in successful:
            result = event.get("result")
            sql = event.get("sql")
            if not isinstance(result, dict) or not isinstance(sql, str):
                continue
            if not _result_satisfies_obligation(result, scalar_obligation):
                continue
            normalized = sql.lower()
            for table in required:
                if re.search(rf"\b{re.escape(table.lower())}\b", normalized) is not None:
                    covered.add(table)
        return covered == set(required)
    for event in successful:
        result = event.get("result")
        sql = event.get("sql")
        if (
            isinstance(result, dict)
            and isinstance(sql, str)
            and _sql_reads_required_tables(sql, obligation)
            and _result_satisfies_obligation(result, obligation)
        ):
            return True
    return False



def _counterfactual_evidence_dependency(
    *,
    case: Mapping[str, object],
    worker: Mapping[str, object],
    projection_bytes: bytes,
) -> bool:
    obligation = case.get("evidence_obligation")
    mutations = case.get("counterfactual_mutations")
    if not isinstance(obligation, dict) or not isinstance(mutations, list) or not mutations:
        return False
    counterfactual = _apply_counterfactual_mutations(
        projection_bytes, [item for item in mutations if isinstance(item, dict)]
    )
    cf_events: list[dict[str, object]] = []
    for event in _successful_sql_events(worker):
        sql = event.get("sql")
        if not isinstance(sql, str):
            continue
        try:
            result = foundation.execute_sqlite(counterfactual, sql)
        except Exception:
            # A query that was successful on the canonical projection but ceases to execute on a
            # type-compatible hidden value perturbation is not accepted as stable evidence.
            return False
        cf_events.append(
            {
                "tool": "execute_sql",
                "query_id": event.get("query_id"),
                "sql": sql,
                "outcome": "success",
                "result": {
                    key: result[key]
                    for key in ("format", "columns", "rows", "row_count", "truncated", "result_sha256")
                },
            }
        )
    synthetic_worker = {"tool_events": cf_events}
    # The original hidden evidence obligation must stop being satisfied after a source-derived
    # fact essential to that proposition is changed. This rejects constant/claim-echo SQL that
    # merely mentions a table while returning the asserted answer.
    return not _evidence_obligation_match(synthetic_worker, obligation)


def _usage_numbers(worker: Mapping[str, object]) -> dict[str, int]:
    usage = worker.get("usage")
    if not isinstance(usage, dict):
        return {"subscription_codex_invocations": 0, "prompt_bytes_egressed": 0, "structured_output_bytes": 0}
    return {
        "subscription_codex_invocations": int(usage.get("subscription_codex_invocations", 0) or 0),
        "prompt_bytes_egressed": int(usage.get("prompt_bytes_egressed", 0) or 0),
        "structured_output_bytes": int(usage.get("structured_output_bytes", 0) or 0),
    }


def score_worker_case(
    case: Mapping[str, object], worker: Mapping[str, object], projection_bytes: bytes
) -> dict[str, object]:
    completed = worker.get("status") == "completed"
    normalized = worker.get("normalized_verdict") if completed else None
    expected_verdict = case["expected_verdict"]
    verdict_correct = completed and normalized == expected_verdict
    obligation = case.get("evidence_obligation")
    evidence_retrieved = _evidence_obligation_match(worker, obligation if isinstance(obligation, dict) else None)
    evidence_required = case.get("evidence_required") is True
    causal_evidence_dependency = (
        _counterfactual_evidence_dependency(case=case, worker=worker, projection_bytes=projection_bytes)
        if evidence_required and evidence_retrieved
        else False
    )
    sql_events = _successful_sql_events(worker)
    report = str(worker.get("report", "")) + "\n" + str(worker.get("sql_expert_answer", ""))
    executed_sql = {_normalize_sql(str(event.get("sql", ""))) for event in sql_events}
    cited_sql = [_normalize_sql(sql) for sql in _sql_blocks(report)]
    unsupported_sql = [sql for sql in cited_sql if sql not in executed_sql]

    cited_ids = worker.get("cited_query_ids", [])
    if not isinstance(cited_ids, list):
        cited_ids = []
    successful_ids = {str(event.get("query_id")) for event in sql_events}
    unsupported_ids = [str(item) for item in cited_ids if str(item) not in successful_ids]

    tool_rejections = int(worker.get("tool_rejection_count", 0) or 0)
    tool_execution_failures = int(worker.get("tool_execution_failure_count", 0) or 0)
    execution_clean = completed and tool_rejections == 0 and tool_execution_failures == 0
    evidence_backed = (
        completed
        and verdict_correct
        and (
            (not evidence_required and expected_verdict == "insufficient_evidence")
            or (evidence_retrieved and causal_evidence_dependency)
        )
        and not unsupported_ids
        and not unsupported_sql
    )
    explicit_sufficiency = worker.get("explicit_sufficiency") is True
    reported_sufficiency = worker.get("evidence_sufficiency")
    sufficiency_correct = explicit_sufficiency and reported_sufficiency == case["expected_sufficiency"]
    usage = _usage_numbers(worker)
    return {
        "case_id": case["case_id"],
        "system": worker.get("system"),
        "completed": completed,
        "execution_clean": execution_clean,
        "expected_verdict": expected_verdict,
        "raw_verdict": worker.get("raw_verdict"),
        "normalized_verdict": normalized,
        "verdict_correct": verdict_correct,
        "evidence_required": evidence_required,
        "successful_sql_calls": len(sql_events),
        "tool_rejections": tool_rejections,
        "tool_execution_failures": tool_execution_failures,
        "evidence_retrieved": evidence_retrieved,
        "causal_evidence_dependency": causal_evidence_dependency,
        "evidence_reopenable": bool(sql_events),
        "evidence_backed_verdict": evidence_backed,
        "unsupported_sql_citation_count": len(unsupported_sql),
        "unsupported_sql_citations": unsupported_sql,
        "unsupported_query_id_count": len(unsupported_ids),
        "unsupported_query_ids": unsupported_ids,
        "expected_sufficiency": case["expected_sufficiency"],
        "reported_sufficiency": reported_sufficiency,
        "explicit_sufficiency": explicit_sufficiency,
        "sufficiency_correct": sufficiency_correct,
        "usage": usage,
        "duration_ms": worker.get("duration_ms"),
        "error_code": worker.get("error_code"),
    }


def _aggregate_scores(scores: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if not scores:
        raise VerifierFitError("cannot aggregate empty score set")
    total = len(scores)
    completed = sum(score.get("completed") is True for score in scores)
    clean = sum(score.get("execution_clean") is True for score in scores)
    correct = sum(score.get("verdict_correct") is True for score in scores)
    evidence_cases = [score for score in scores if score.get("evidence_required") is True]
    evidence_retrieved = sum(score.get("evidence_retrieved") is True for score in evidence_cases)
    evidence_backed = sum(score.get("evidence_backed_verdict") is True for score in scores)
    explicit_sufficiency = sum(score.get("explicit_sufficiency") is True for score in scores)
    sufficiency_correct = sum(score.get("sufficiency_correct") is True for score in scores)
    expected_abstentions = {str(score["case_id"]) for score in scores if score.get("expected_verdict") == "insufficient_evidence"}
    predicted_abstentions = {str(score["case_id"]) for score in scores if score.get("normalized_verdict") == "insufficient_evidence"}
    true_abstentions = expected_abstentions & predicted_abstentions
    precision = len(true_abstentions) / len(predicted_abstentions) if predicted_abstentions else (1.0 if not expected_abstentions else 0.0)
    recall = len(true_abstentions) / len(expected_abstentions) if expected_abstentions else 1.0
    usage = {"subscription_codex_invocations": 0, "prompt_bytes_egressed": 0, "structured_output_bytes": 0}
    duration_ms = 0.0
    tool_rejections = tool_failures = unsupported = unsupported_ids = 0
    for score in scores:
        raw_usage = score.get("usage")
        if isinstance(raw_usage, dict):
            for key in usage:
                usage[key] += int(raw_usage.get(key, 0) or 0)
        if isinstance(score.get("duration_ms"), (int, float)):
            duration_ms += float(score["duration_ms"])
        tool_rejections += int(score.get("tool_rejections", 0) or 0)
        tool_failures += int(score.get("tool_execution_failures", 0) or 0)
        unsupported += int(score.get("unsupported_sql_citation_count", 0) or 0)
        unsupported_ids += int(score.get("unsupported_query_id_count", 0) or 0)
    return {
        "case_count": total,
        "completed": completed,
        "execution_failures": total - completed,
        "execution_clean_cases": clean,
        "verdict_correct": correct,
        "verdict_accuracy": correct / total,
        "evidence_required_cases": len(evidence_cases),
        "evidence_retrieved": evidence_retrieved,
        "evidence_retrieval_recall": evidence_retrieved / len(evidence_cases) if evidence_cases else 1.0,
        "evidence_backed_verdicts": evidence_backed,
        "evidence_backed_verdict_rate": evidence_backed / total,
        "tool_rejections": tool_rejections,
        "tool_execution_failures": tool_failures,
        "unsupported_sql_citations": unsupported,
        "unsupported_query_ids": unsupported_ids,
        "explicit_sufficiency_cases": explicit_sufficiency,
        "explicit_sufficiency_correct": sufficiency_correct,
        "abstention_precision": precision,
        "abstention_recall": recall,
        "usage": usage,
        "duration_ms": duration_ms,
        "billing_mode": "chatgpt_subscription",
        "per_token_api_billing": False,
    }


def _add_shared_usage(aggregate: dict[str, object], setup_worker: Mapping[str, object]) -> None:
    setup_usage = _usage_numbers(setup_worker)
    usage = aggregate.get("usage")
    if not isinstance(usage, dict):
        return
    for key, value in setup_usage.items():
        usage[key] = int(usage.get(key, 0) or 0) + value
    if isinstance(setup_worker.get("duration_ms"), (int, float)):
        aggregate["duration_ms"] = float(aggregate.get("duration_ms", 0.0)) + float(setup_worker["duration_ms"])
    aggregate["shared_setup_codex_invocations"] = setup_usage["subscription_codex_invocations"]


def score_paired_run(
    cases_doc: Mapping[str, object], paired: Mapping[str, object], projection_bytes: bytes
) -> dict[str, object]:
    if paired.get("format") != PAIRED_RUN_FORMAT or paired.get("status") != "completed":
        raise VerifierFitError("paired run is not a completed Phase-D run")
    cases = cases_doc.get("cases")
    runs = paired.get("runs")
    if not isinstance(cases, list) or not isinstance(runs, list) or len(cases) != len(runs):
        raise VerifierFitError("paired run does not match cases")
    by_case = {str(case["case_id"]): case for case in cases if isinstance(case, dict)}
    system_scores: dict[str, list[dict[str, object]]] = {SIMPLE_SYSTEM: [], THUCY_SYSTEM: []}
    for run in runs:
        if not isinstance(run, dict):
            raise VerifierFitError("paired run entry malformed")
        case_id = str(run.get("case_id"))
        case = by_case.get(case_id)
        if case is None:
            raise VerifierFitError("paired run has unknown case")
        systems = run.get("systems")
        if not isinstance(systems, list) or len(systems) != 2:
            raise VerifierFitError("each paired case requires two system runs")
        seen: set[str] = set()
        for worker in systems:
            if not isinstance(worker, dict):
                raise VerifierFitError("worker result malformed")
            system = str(worker.get("system"))
            if system not in system_scores or system in seen:
                raise VerifierFitError("paired run system identity invalid")
            seen.add(system)
            system_scores[system].append(score_worker_case(case, worker, projection_bytes))
    systems_doc: dict[str, object] = {}
    for system, scores in system_scores.items():
        systems_doc[system] = {"cases": scores, "aggregate": _aggregate_scores(scores)}
    thucy_doc = systems_doc[THUCY_SYSTEM]
    if not isinstance(thucy_doc, dict):
        raise VerifierFitError("Thucy score document malformed")
    thucy_aggregate = thucy_doc.get("aggregate")
    if not isinstance(thucy_aggregate, dict):
        raise VerifierFitError("Thucy aggregate score malformed")
    setup = paired.get("thucy_setup")
    if isinstance(setup, dict):
        _add_shared_usage(thucy_aggregate, setup)
    return {
        "format": SCORE_FORMAT,
        "cases_sha256": _sha256_bytes(_canonical_json_bytes(cases_doc)),
        "systems": systems_doc,
    }


def compare_system_scores(score_doc: Mapping[str, object]) -> dict[str, object]:
    if score_doc.get("format") != SCORE_FORMAT:
        raise VerifierFitError("unexpected score format")
    systems = score_doc.get("systems")
    if not isinstance(systems, dict):
        raise VerifierFitError("score systems missing")
    simple = systems.get(SIMPLE_SYSTEM)
    thucy = systems.get(THUCY_SYSTEM)
    if not isinstance(simple, dict) or not isinstance(thucy, dict):
        raise VerifierFitError("both systems required")
    sa = simple.get("aggregate")
    ta = thucy.get("aggregate")
    if not isinstance(sa, dict) or not isinstance(ta, dict):
        raise VerifierFitError("aggregate score missing")
    su = sa.get("usage")
    tu = ta.get("usage")
    if not isinstance(su, dict) or not isinstance(tu, dict):
        raise VerifierFitError("comparison usage measurements missing")
    return {
        "format": COMPARISON_FORMAT,
        "simple": sa,
        THUCY_SYSTEM: ta,
        "deltas_thucy_minus_simple": {
            "verdict_accuracy": float(ta["verdict_accuracy"]) - float(sa["verdict_accuracy"]),
            "evidence_retrieval_recall": float(ta["evidence_retrieval_recall"]) - float(sa["evidence_retrieval_recall"]),
            "evidence_backed_verdict_rate": float(ta["evidence_backed_verdict_rate"]) - float(sa["evidence_backed_verdict_rate"]),
            "abstention_precision": float(ta["abstention_precision"]) - float(sa["abstention_precision"]),
            "abstention_recall": float(ta["abstention_recall"]) - float(sa["abstention_recall"]),
            "subscription_codex_invocations": int(tu["subscription_codex_invocations"]) - int(su["subscription_codex_invocations"]),
            "prompt_bytes_egressed": int(tu["prompt_bytes_egressed"]) - int(su["prompt_bytes_egressed"]),
            "duration_ms": float(ta["duration_ms"]) - float(sa["duration_ms"]),
        },
        "billing_mode": "chatgpt_subscription",
        "per_token_api_billing": False,
        "decision": "MEASUREMENT_ONLY__DESIGN_AGENT_MUST_INTERPRET",
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build-cases")
    build.add_argument("--projection", type=Path, required=True)
    build.add_argument("--query-corpus", type=Path, required=True)
    build.add_argument("--planner-handoff", type=Path, required=True)
    build.add_argument("--output", type=Path, required=True)

    validate = sub.add_parser("validate-cases")
    validate.add_argument("--projection", type=Path, required=True)
    validate.add_argument("--cases", type=Path, required=True)

    probe = sub.add_parser("provider-probe")
    probe.add_argument("--codex-home", type=Path, required=True)
    probe.add_argument("--codex", default="codex")
    probe.add_argument("--model", default=DEFAULT_MODEL)
    probe.add_argument("--reasoning-effort", choices=("none", "low", "medium", "high", "xhigh", "max"), default=DEFAULT_REASONING_EFFORT)
    probe.add_argument("--output", type=Path, required=True)

    verify = sub.add_parser("verify-thucy")
    verify.add_argument("--thucy-root", type=Path, required=True)

    run = sub.add_parser("run-paired")
    run.add_argument("--projection", type=Path, required=True)
    run.add_argument("--cases", type=Path, required=True)
    run.add_argument("--codex-home", type=Path, required=True)
    run.add_argument("--codex", default="codex")
    run.add_argument("--model", default=DEFAULT_MODEL)
    run.add_argument("--reasoning-effort", choices=("none", "low", "medium", "high", "xhigh", "max"), default=DEFAULT_REASONING_EFFORT)
    run.add_argument("--thucy-root", type=Path, required=True)
    run.add_argument("--provider-probe", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)

    score = sub.add_parser("score")
    score.add_argument("--projection", type=Path, required=True)
    score.add_argument("--cases", type=Path, required=True)
    score.add_argument("--paired-run", type=Path, required=True)
    score.add_argument("--output", type=Path, required=True)

    compare = sub.add_parser("compare")
    compare.add_argument("--score", type=Path, required=True)
    compare.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "build-cases":
        projection = args.projection.read_bytes()
        cases = build_phase_d_cases(projection, _load_json(args.query_corpus), _load_json(args.planner_handoff))
        summary = validate_phase_d_cases(cases, projection)
        digest = _write_json(args.output, cases)
        result: object = {"cases_sha256": digest, **summary}
    elif args.command == "validate-cases":
        result = validate_phase_d_cases(_load_json(args.cases), args.projection.read_bytes())
    elif args.command == "provider-probe":
        result = provider_probe(
            codex_home=args.codex_home,
            codex=args.codex,
            model=args.model,
            reasoning_effort=args.reasoning_effort,
        )
        _write_json(args.output, result)
    elif args.command == "verify-thucy":
        result = verify_thucy_checkout(args.thucy_root)
    elif args.command == "run-paired":
        result = run_paired_campaign(
            projection_path=args.projection,
            cases_doc=_load_json(args.cases),
            model=args.model,
            reasoning_effort=args.reasoning_effort,
            codex_home=args.codex_home,
            codex=args.codex,
            thucy_root=args.thucy_root,
            provider_probe_doc=_load_json(args.provider_probe),
        )
        _write_json(args.output, result)
    elif args.command == "score":
        result = score_paired_run(
            _load_json(args.cases), _load_json(args.paired_run), args.projection.read_bytes()
        )
        _write_json(args.output, result)
    elif args.command == "compare":
        result = compare_system_scores(_load_json(args.score))
        _write_json(args.output, result)
    else:
        raise AssertionError(args.command)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
