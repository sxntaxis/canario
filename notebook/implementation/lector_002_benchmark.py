#!/usr/bin/env python3
"""Deterministic reference-corpus preparation and scoring for LECTOR-002.

This module is intentionally source-format agnostic at the semantic layer.
``prepare`` partitions an exact UTF-8 Representation using only generic textual
structure (page separators, blank-line blocks, and bounded continuations). It
never recognizes acta vocabulary, institutions, decisions, speakers, or other
source-specific semantics. Humans remain responsible for gold propositions and
candidate-to-truth adjudication; ``score`` validates exact evidence reopening and
computes metrics from those explicit judgments.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

from canario.lector.locators import SemanticLocatorError, reopen_selector
from canario.processors.targets import TargetContractError, TargetRegistry
from canario.processors.media import MediaIndexError, validate_media_index

PREPARATION_VERSION = "lector-002-reference-text:v2"
TYPED_PREPARATION_VERSION = "lector-002-typed-evidence:v1"
GOLD_SCOPE_VERSION = "lector-002-gold-scope:v1"
GOLD_PROTOCOL_VERSION = "lector-002-gold-protocol:v1"
MAX_UNIT_CHARS = 4_000
PREFERRED_SPLIT_CHARS = 2_800

TRUTH_IMPORTANCE = {"must", "material"}
ASSESSMENT_VERDICTS = {"correct", "distorted", "unsupported", "redundant", "overmerged"}
COVERAGE_STATES = {"truth_recorded", "no_material_truth"}
HUMAN_REVIEW_STATES = COVERAGE_STATES | {"needs_adjudication"}
SCOPE_COVERAGE_STATES = HUMAN_REVIEW_STATES | {"unjudged"}
SEMANTIC_VERIFICATION_STATES = {"not_run", "passed", "failed"}
SHA256_HEX_LENGTH = 64


class BenchmarkError(ValueError):
    """Benchmark input is malformed or violates an auditable invariant."""


@dataclass(frozen=True)
class LineRecord:
    start_char: int
    end_char: int
    page: int | None
    blank: bool
    has_page_break: bool


@dataclass(frozen=True)
class ReviewUnit:
    unit_id: str
    kind: str
    page_start: int | None
    page_end: int | None
    char_start: int
    char_end: int
    preview: str
    text: str


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def _sha256_json(value: object) -> str:
    return _sha256_bytes(_canonical_json(value))


def _valid_sha256(value: object) -> bool:
    if not isinstance(value, str) or len(value) != SHA256_HEX_LENGTH:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _selected_ids_sha256(unit_ids: Sequence[str]) -> str:
    return _sha256_json(sorted(unit_ids))


def _unit_file_sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _parse_capability_ids(
    value: str, *, semantic_capabilities: set[str], label: str
) -> list[str]:
    ids = [item.strip() for item in value.split(";") if item.strip()]
    if not ids:
        raise BenchmarkError(f"{label} must bind at least one semantic capability")
    if len(ids) != len(set(ids)):
        raise BenchmarkError(f"{label} contains duplicate capability_ids")
    if ids != sorted(ids):
        raise BenchmarkError(f"{label} capability_ids must be in canonical sorted order")
    unknown = sorted(set(ids) - semantic_capabilities)
    if unknown:
        raise BenchmarkError(f"{label} binds undeclared/non-semantic capabilities {unknown}")
    return ids


def create_gold_scope(
    *,
    case_id: str,
    source_sha256: str,
    units_sha256: str,
    unit_ids: Sequence[str],
    selection_kind: str,
    selection_policy: str,
    semantic_capabilities: Sequence[str],
) -> dict[str, object]:
    """Create the immutable, source-bound scope used by future human gold."""
    if selection_kind not in {"full_source_order", "deterministic_structural_sample"}:
        raise BenchmarkError(f"invalid gold scope selection_kind {selection_kind!r}")
    selected = list(unit_ids)
    if len(selected) != len(set(selected)):
        raise BenchmarkError("gold scope selected_unit_ids must be unique")
    if not _valid_sha256(source_sha256) or not _valid_sha256(units_sha256):
        raise BenchmarkError("gold scope requires valid source_sha256 and units_sha256")
    capabilities = sorted(set(semantic_capabilities))
    if not capabilities:
        raise BenchmarkError("gold scope requires semantic capabilities")
    return {
        "version": GOLD_SCOPE_VERSION,
        "case_id": case_id,
        "source_sha256": source_sha256,
        "units_sha256": units_sha256,
        "selection_kind": selection_kind,
        "selection_policy": selection_policy,
        "selected_unit_ids": selected,
        "selected_unit_ids_sha256": _selected_ids_sha256(selected),
        "semantic_capabilities": capabilities,
        "tested_extractor_seen": False,
        "semantic_model_calls": 0,
    }


def write_gold_scope(path: Path, scope: dict[str, object]) -> str:
    if scope.get("version") != GOLD_SCOPE_VERSION:
        raise BenchmarkError("unsupported gold scope version")
    path.write_bytes(_canonical_json(scope))
    return _sha256_bytes(path.read_bytes())


def _load_gold_scope(path: Path, *, source_bytes: bytes, units_path: Path, unit_ids: set[str]) -> dict[str, object]:
    try:
        scope = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BenchmarkError("gold_scope.json is not readable valid JSON") from exc
    if not isinstance(scope, dict) or scope.get("version") != GOLD_SCOPE_VERSION:
        raise BenchmarkError("gold_scope.json has unsupported version")
    if scope.get("source_sha256") != _sha256_bytes(source_bytes):
        raise BenchmarkError("gold scope source identity does not match the frozen source")
    if scope.get("units_sha256") != _unit_file_sha256(units_path):
        raise BenchmarkError("gold scope units identity does not match units.csv")
    selected = scope.get("selected_unit_ids")
    if not isinstance(selected, list) or not all(isinstance(item, str) and item for item in selected):
        raise BenchmarkError("gold scope selected_unit_ids must be a string list")
    if len(selected) != len(set(selected)) or set(selected) - unit_ids:
        raise BenchmarkError("gold scope selects unknown or duplicate units")
    if scope.get("selected_unit_ids_sha256") != _selected_ids_sha256(selected):
        raise BenchmarkError("gold scope selected-unit identity is invalid")
    if scope.get("tested_extractor_seen") is not False or scope.get("semantic_model_calls") != 0:
        raise BenchmarkError("gold scope was not frozen before extractor/model use")
    capabilities = scope.get("semantic_capabilities")
    if not isinstance(capabilities, list) or not capabilities or capabilities != sorted(set(capabilities)):
        raise BenchmarkError("gold scope semantic_capabilities must be sorted and unique")
    return scope


def _visible_line(raw: str) -> str:
    return raw.replace("\f", "").strip()


def _line_records(text: str) -> list[LineRecord]:
    """Record exact line spans without interpreting source-specific content."""

    has_pages = "\f" in text
    records: list[LineRecord] = []
    page = 1
    position = 0
    for raw in text.splitlines(keepends=True):
        end = position + len(raw)
        records.append(
            LineRecord(
                start_char=position,
                end_char=end,
                page=page if has_pages else None,
                blank=not bool(_visible_line(raw)),
                has_page_break="\f" in raw,
            )
        )
        # Form-feed closes the page containing it. The following record belongs
        # to the next page; a trailing form-feed does not invent a review unit.
        page += raw.count("\f")
        position = end
    if position < len(text):
        raw = text[position:]
        records.append(
            LineRecord(
                position,
                len(text),
                page if has_pages else None,
                not bool(_visible_line(raw)),
                "\f" in raw,
            )
        )
    if not records:
        records.append(LineRecord(0, 0, None, True, False))
    return records


def _page_at(records: Sequence[LineRecord], starts: Sequence[int], offset: int) -> int | None:
    if not records:
        return None
    index = bisect.bisect_right(starts, max(0, offset)) - 1
    return records[max(0, index)].page


def _split_oversized_units(
    boundaries: list[int], line_starts: Sequence[int], text_length: int, markers: dict[int, str]
) -> list[int]:
    boundaries = sorted(set(boundaries + [text_length]))
    while True:
        changed = False
        revised: list[int] = []
        for start, end in zip(boundaries, boundaries[1:]):
            revised.append(start)
            if end - start <= MAX_UNIT_CHARS:
                continue
            target = start + PREFERRED_SPLIT_CHARS
            index = bisect.bisect_left(line_starts, target)
            if index >= len(line_starts):
                continue
            split = line_starts[index]
            if start < split < end:
                revised.append(split)
                markers.setdefault(split, "continuation")
                changed = True
        revised.append(boundaries[-1])
        boundaries = sorted(set(revised))
        if not changed:
            return boundaries


def partition_source(text: str) -> list[ReviewUnit]:
    """Losslessly partition text using only generic Representation structure.

    Boundaries are based on explicit page separators, blank-line block starts,
    and bounded continuation splits. Words such as ``ARTÍCULO`` or ``SE ACUERDA``
    have no special meaning here by design.
    """

    records = _line_records(text)
    line_starts = [record.start_char for record in records]
    markers: dict[int, str] = {0: "source"}
    boundaries = [0]

    previous_blank = False
    previous_had_page_break = False
    for record in records:
        if record.start_char != 0 and not record.blank:
            if previous_had_page_break:
                boundaries.append(record.start_char)
                markers[record.start_char] = "page"
            elif previous_blank:
                boundaries.append(record.start_char)
                markers[record.start_char] = "block"
        previous_blank = record.blank
        previous_had_page_break = record.has_page_break

    boundaries = _split_oversized_units(boundaries, line_starts, len(text), markers)
    starts = [record.start_char for record in records]
    units: list[ReviewUnit] = []
    for ordinal, (start, end) in enumerate(zip(boundaries, boundaries[1:]), start=1):
        segment = text[start:end]
        preview = " ".join(segment.replace("\f", " ").split())[:280]
        page_end_offset = max(start, end - 1)
        units.append(
            ReviewUnit(
                unit_id=f"U{ordinal:04d}",
                kind=markers.get(start, "continuation"),
                page_start=_page_at(records, starts, start),
                page_end=_page_at(records, starts, page_end_offset),
                char_start=start,
                char_end=end,
                preview=preview,
                text=segment,
            )
        )

    if "".join(unit.text for unit in units) != text:
        raise BenchmarkError("review units do not losslessly partition the source")
    return units


def _write_csv(path: Path, fieldnames: Sequence[str], rows: Iterable[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def prepare(source_path: Path, output_dir: Path, source_label: str | None = None) -> dict[str, object]:
    """Prepare one exact UTF-8 text Representation for independent gold review.

    This is one evaluator mode in the wider LECTOR-002 corpus. Structured table
    and timed-media evidence require their own typed evaluator modes and must not
    be coerced into this text-offset contract merely to reuse the harness.
    """

    source_bytes = source_path.read_bytes()
    try:
        text = source_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BenchmarkError("text-reference mode requires exact UTF-8 Representation bytes") from exc

    units = partition_source(text)
    output_dir.mkdir(parents=True, exist_ok=True)

    page_count: int | None = None
    if "\f" in text:
        page_count = text.count("\f") + (0 if text.endswith("\f") else 1)

    manifest = {
        "preparation_version": PREPARATION_VERSION,
        "evaluator_mode": "text_quote:v1",
        "source_label": source_label or source_path.name,
        "source_sha256": _sha256_bytes(source_bytes),
        "source_bytes": len(source_bytes),
        "source_characters": len(text),
        "page_count": page_count,
        "review_units": len(units),
        "segmentation_semantics": "generic_structure_only",
        "truth_generated": False,
        "semantic_model_calls": 0,
        "attention_heuristics_used": False,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    unit_fields = [
        "unit_id",
        "kind",
        "page_start",
        "page_end",
        "char_start",
        "char_end",
        "preview",
    ]
    _write_csv(
        output_dir / "units.csv",
        unit_fields,
        ({key: getattr(unit, key) for key in unit_fields} for unit in units),
    )
    _write_csv(
        output_dir / "selected_units.csv",
        unit_fields,
        ({key: getattr(unit, key) for key in unit_fields} for unit in units),
    )
    with (output_dir / "units.jsonl").open("w", encoding="utf-8") as handle:
        for unit in units:
            handle.write(json.dumps(asdict(unit), ensure_ascii=False, sort_keys=True) + "\n")

    # Coverage stays in source order. No content heuristic is allowed to silently
    # reorder completeness review in the canonical gold worksheet.
    _write_csv(
        output_dir / "coverage.csv",
        ["unit_id", "review_state", "notes"],
        ({"unit_id": unit.unit_id, "review_state": "", "notes": ""} for unit in units),
    )
    _write_csv(
        output_dir / "truth.csv",
        [
            "truth_id",
            "unit_id",
            "importance",
            "proposition",
            "evidence_quote",
            "evidence_start",
            "evidence_end",
            "capability_ids",
            "notes",
        ],
        (),
    )
    _write_csv(
        output_dir / "candidates.csv",
        ["candidate_id", "proposition", "evidence_quote", "evidence_start", "evidence_end"],
        (),
    )
    _write_csv(
        output_dir / "assessment.csv",
        ["candidate_id", "truth_ids", "verdict", "notes"],
        (),
    )
    (output_dir / "README.md").write_text(
        "# Canario LECTOR-002 text-reference worksheet\n\n"
        "This worksheet is one case in a heterogeneous reference corpus; it is not a document-\n"
        "type-specific benchmark. `units.csv` follows source order and uses only generic page,\n"
        "blank-line, and bounded-size structure. No acta vocabulary or semantic attention\n"
        "heuristic influences segmentation or coverage. `units.jsonl` contains exact unit text\n"
        "and character offsets.\n\n"
        "For every selected unit, a human records `truth_recorded`, `no_material_truth`, or\n"
        "`needs_adjudication` in `coverage.csv`. Uncertainty is valid: `needs_adjudication` means\n"
        "do not guess; the unit must receive a second review before gold can freeze. Each material\n"
        "proposition is added to `truth.csv` with `importance` =\n"
        "`must` or `material` and an exact quote whose character offsets reopen against the\n"
        "frozen Representation.\n\n"
        "Only after the case gold set is frozen may the tested extractor fill `candidates.csv`.\n"
        "Human adjudication maps candidates in `assessment.csv` to truth IDs. The scorer\n"
        "validates evidence and computes metrics; it does not decide semantic equivalence.\n\n"
        "This evaluator mode covers text_quote:v1 only. Table-range and timed-media cases need\n"
        "their own typed evidence evaluators; they must not be flattened into text merely to\n"
        "make this scorer pass.\n",
        encoding="utf-8",
    )
    return manifest


def _table_unit_rows(value: dict[str, object]) -> list[dict[str, object]]:
    units: list[dict[str, object]] = []
    sheets = value.get("sheets")
    if not isinstance(sheets, list):
        raise BenchmarkError("table-reference source has no sheets")
    for sheet in sheets:
        if not isinstance(sheet, dict) or not isinstance(sheet.get("rows"), list):
            raise BenchmarkError("table-reference source has malformed sheet rows")
        sheet_name = sheet.get("name")
        ordinal = sheet.get("ordinal")
        if not isinstance(sheet_name, str) or not isinstance(ordinal, int):
            raise BenchmarkError("table-reference sheet identity is malformed")
        merged_ranges = sheet.get("merged_ranges", [])
        if not isinstance(merged_ranges, list):
            raise BenchmarkError("table-reference merged_ranges must be a list")
        for row_number, row in enumerate(sheet["rows"], start=1):
            if not isinstance(row, list):
                raise BenchmarkError("table-reference row must be a list")
            cells = [cell for cell in row if isinstance(cell, dict) and cell.get("value") is not None]
            types = sorted(
                str(cell.get("value", {}).get("type", "unknown"))
                for cell in cells
                if isinstance(cell.get("value"), dict)
            )
            formulas = any(
                isinstance(cell.get("value"), dict) and cell["value"].get("type") == "formula"
                for cell in cells
            )
            merged = any(
                isinstance(item, str) and _range_contains_row(item, row_number)
                for item in merged_ranges
            )
            units.append({
                "unit_id": f"{ordinal}:R{row_number}",
                "sheet": sheet_name,
                "row_start": row_number,
                "row_end": row_number,
                "non_empty_cell_count": len(cells),
                "value_type_signature": ";".join(types),
                "formula_present": str(formulas).lower(),
                "merged_structure_intersection": str(merged).lower(),
                "cells_json": json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            })
    return units


def _range_contains_row(cell_range: str, row_number: int) -> bool:
    # Structural-only parsing: this reads coordinates, never cell text.
    import re

    numbers = [int(item) for item in re.findall(r"\d+", cell_range)]
    return bool(numbers) and min(numbers) <= row_number <= max(numbers)


def select_structural_table_units(units: Sequence[dict[str, object]], source_sha256: str) -> list[str]:
    """Select a stable structural sample without inspecting labels or candidates."""
    if len(units) <= 32:
        return [str(unit["unit_id"]) for unit in units]
    selected: set[str] = set()
    by_sheet: dict[str, list[dict[str, object]]] = {}
    for unit in units:
        by_sheet.setdefault(str(unit["sheet"]), []).append(unit)
    for sheet_units in by_sheet.values():
        selected.add(str(sheet_units[0]["unit_id"]))
        selected.add(str(sheet_units[-1]["unit_id"]))
    for field, expected in (
        ("value_type_signature", None),
        ("formula_present", "true"),
        ("merged_structure_intersection", "true"),
    ):
        candidates = [unit for unit in units if (expected is None or unit[field] == expected)]
        if field == "value_type_signature":
            candidates = [
                min(group, key=lambda item: str(item["unit_id"]))
                for signature in sorted({str(item[field]) for item in candidates})
                for group in [[item for item in candidates if item[field] == signature]]
            ]
        if candidates:
            selected.add(str(min(candidates, key=lambda item: str(item["unit_id"]))["unit_id"]))
    for shape in sorted({unit.get("non_empty_cell_count") for unit in units}):
        candidates = [unit for unit in units if unit.get("non_empty_cell_count") == shape]
        if candidates:
            selected.add(str(min(candidates, key=lambda item: str(item["unit_id"]))["unit_id"]))
    digest_seed = bytes.fromhex(source_sha256)
    ranked = sorted(
        (unit for unit in units if str(unit["unit_id"]) not in selected),
        key=lambda unit: hashlib.sha256(digest_seed + str(unit["unit_id"]).encode("utf-8")).hexdigest(),
    )
    target = max(24, len(selected))
    selected.update(str(unit["unit_id"]) for unit in ranked[: max(0, target - len(selected))])
    return [str(unit["unit_id"]) for unit in units if str(unit["unit_id"]) in selected]


def _blank_typed_worksheets(
    output_dir: Path,
    manifest: dict[str, object],
    units: list[dict[str, object]],
    selected_unit_ids: set[str] | None = None,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _write_csv(output_dir / "units.csv", list(units[0]) if units else ["unit_id"], units)
    selected = units if selected_unit_ids is None else [
        unit for unit in units if str(unit["unit_id"]) in selected_unit_ids
    ]
    _write_csv(output_dir / "selected_units.csv", list(units[0]) if units else ["unit_id"], selected)
    _write_csv(output_dir / "coverage.csv", ["unit_id", "review_state", "notes"],
               ({"unit_id": unit["unit_id"], "review_state": "" if selected_unit_ids is None or unit["unit_id"] in selected_unit_ids else "unjudged", "notes": ""} for unit in units))
    _write_csv(output_dir / "truth.csv", ["truth_id", "unit_id", "importance", "proposition", "selector_json", "capability_ids", "notes"], ())
    _write_csv(output_dir / "candidates.csv", ["candidate_id", "proposition", "selector_json"], ())
    _write_csv(output_dir / "assessment.csv", ["candidate_id", "truth_ids", "verdict", "notes"], ())
    return manifest


def prepare_table(
    source_path: Path,
    output_dir: Path,
    source_label: str | None = None,
    case_id: str = "",
) -> dict[str, object]:
    """Prepare a blank worksheet over the canonical structured-table derivative."""
    source_bytes = source_path.read_bytes()
    try:
        value = json.loads(source_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BenchmarkError("table-reference mode requires canonical JSON table bytes") from exc
    sheets = value.get("sheets") if isinstance(value, dict) else None
    if not isinstance(sheets, list):
        raise BenchmarkError("table-reference source has no sheets")
    units = _table_unit_rows(value)
    source_sha256 = _sha256_bytes(source_bytes)
    selected = select_structural_table_units(units, source_sha256)
    manifest = {
        "preparation_version": TYPED_PREPARATION_VERSION,
        "evaluator_mode": "table_range:v1",
        "source_label": source_label or source_path.name,
        "source_sha256": _sha256_bytes(source_bytes),
        "source_bytes": len(source_bytes),
        "review_units": len(units),
        "selected_units": len(selected),
        "selection_kind": "deterministic_structural_sample" if len(selected) < len(units) else "full_source_order",
        "selection_policy": "lector-002-structural-sample:v1",
        "truth_generated": False,
        "semantic_model_calls": 0,
        "tested_extractor_seen": False,
        "gold_rows": 0,
    }
    result = _blank_typed_worksheets(output_dir, manifest, units, set(selected))
    scope = create_gold_scope(
        case_id=case_id,
        source_sha256=source_sha256,
        units_sha256=_unit_file_sha256(output_dir / "units.csv"),
        unit_ids=selected,
        selection_kind=str(manifest["selection_kind"]),
        selection_policy=str(manifest["selection_policy"]),
        semantic_capabilities=["semantic:structured_values"],
    )
    result["gold_scope"] = scope
    write_gold_scope(output_dir / "gold_scope.json", scope)
    return result


def prepare_full_scope(
    source_path: Path,
    units_path: Path,
    output_path: Path,
    case_id: str,
    semantic_capabilities: Sequence[str],
    selection_policy: str,
) -> dict[str, object]:
    source_bytes = source_path.read_bytes()
    units = _unique_rows(_read_csv(units_path), "unit_id", "units.csv")
    scope = create_gold_scope(
        case_id=case_id,
        source_sha256=_sha256_bytes(source_bytes),
        units_sha256=_unit_file_sha256(units_path),
        unit_ids=list(units),
        selection_kind="full_source_order",
        selection_policy=selection_policy,
        semantic_capabilities=semantic_capabilities,
    )
    write_gold_scope(output_path, scope)
    return scope


def _load_media_index(source_bytes: bytes, media_index_path: Path) -> dict[str, object]:
    try:
        index_bytes = media_index_path.read_bytes()
    except OSError as exc:
        raise BenchmarkError("media-reference mode requires a readable canonical media index") from exc
    try:
        return validate_media_index(source_bytes, index_bytes)
    except MediaIndexError as exc:
        raise BenchmarkError(f"media-reference mode rejected media index: {exc}") from exc


def prepare_media(
    source_path: Path,
    media_index_path: Path,
    output_dir: Path,
    source_label: str | None = None,
) -> dict[str, object]:
    """Prepare full-duration blank windows from a trusted canonical media index."""
    source_bytes = source_path.read_bytes()
    media_index = _load_media_index(source_bytes, media_index_path)
    duration_us = int(media_index["duration_us"])
    step = 10_000_000
    units = []
    start = 0
    ordinal = 1
    while start < duration_us:
        end = min(duration_us, start + step)
        units.append({"unit_id": f"T{ordinal:04d}", "start_us": start, "end_us": end})
        start, ordinal = end, ordinal + 1
    manifest = {
        "preparation_version": TYPED_PREPARATION_VERSION,
        "evaluator_mode": "media:v1",
        "source_label": source_label or source_path.name,
        "source_sha256": _sha256_bytes(source_bytes),
        "media_index_sha256": _sha256_bytes(media_index_path.read_bytes()),
        "source_bytes": len(source_bytes),
        "duration_us": duration_us,
        "review_units": len(units),
        "segmentation_semantics": "uniform_mechanical_windows_only",
        "truth_generated": False,
        "semantic_model_calls": 0,
        "tested_extractor_seen": False,
        "transcript_generated": False,
        "gold_rows": 0,
    }
    return _blank_typed_worksheets(output_dir, manifest, units)


def validate_typed_evidence(mode: str, source_bytes: bytes, selector_json: str, *, charset: str | None = "utf-8") -> None:
    """Use the production locator registry for typed benchmark evidence."""
    kind = "table_range" if mode == "table_range:v1" else "media" if mode == "media:v1" else mode
    try:
        canonical = TargetRegistry().validate(kind, "v1", selector_json)
        reopen_selector(kind, "v1", canonical, source_bytes=source_bytes, charset=charset)
    except (TargetContractError, SemanticLocatorError) as exc:
        raise BenchmarkError(f"typed evidence does not reopen: {exc}") from exc


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _unique_rows(rows: Sequence[dict[str, str]], key: str, label: str) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        value = row.get(key, "").strip()
        if not value:
            raise BenchmarkError(f"{label} contains an empty {key}")
        if value in result:
            raise BenchmarkError(f"{label} contains duplicate {key} {value!r}")
        result[value] = row
    return result


def _validate_exact_evidence(text: str, row: dict[str, str], label: str) -> None:
    quote = row.get("evidence_quote", "")
    if not quote:
        raise BenchmarkError(f"{label} has no exact evidence_quote")
    try:
        start = int(row.get("evidence_start", ""))
        end = int(row.get("evidence_end", ""))
    except ValueError as exc:
        raise BenchmarkError(f"{label} has non-integer evidence offsets") from exc
    if start < 0 or end <= start or end > len(text):
        raise BenchmarkError(f"{label} evidence offsets are outside the frozen source")
    if text[start:end] != quote:
        raise BenchmarkError(f"{label} evidence quote does not reopen exact source text")


def _ratio(numerator: int, denominator: int) -> float | None:
    return None if denominator == 0 else numerator / denominator


def _score_rows(
    *,
    source_bytes: bytes,
    units_path: Path,
    coverage_path: Path,
    truth_path: Path,
    candidates_path: Path,
    assessment_path: Path,
    evidence_validator,
    scope: dict[str, object] | None = None,
) -> dict[str, object]:
    units = _unique_rows(_read_csv(units_path), "unit_id", "units.csv")
    coverage = _unique_rows(_read_csv(coverage_path), "unit_id", "coverage.csv")
    if set(coverage) != set(units):
        missing = sorted(set(units) - set(coverage))
        extra = sorted(set(coverage) - set(units))
        raise BenchmarkError(f"coverage unit mismatch; missing={missing}, extra={extra}")

    truths = _unique_rows(_read_csv(truth_path), "truth_id", "truth.csv")
    truths_by_unit: dict[str, list[str]] = {unit_id: [] for unit_id in units}
    for truth_id, row in truths.items():
        unit_id = row.get("unit_id", "").strip()
        if unit_id not in units:
            raise BenchmarkError(f"truth {truth_id!r} references unknown unit {unit_id!r}")
        importance = row.get("importance", "").strip()
        if importance not in TRUTH_IMPORTANCE:
            raise BenchmarkError(f"truth {truth_id!r} has invalid importance {importance!r}")
        if not row.get("proposition", "").strip():
            raise BenchmarkError(f"truth {truth_id!r} has empty proposition")
        if scope is not None:
            semantic_capabilities = set(str(item) for item in scope["semantic_capabilities"])
            capability_ids = _parse_capability_ids(
                row.get("capability_ids", ""),
                semantic_capabilities=semantic_capabilities,
                label=f"truth {truth_id!r}",
            )
            row["_capability_ids"] = capability_ids
            if unit_id not in set(str(item) for item in scope["selected_unit_ids"]):
                raise BenchmarkError(f"truth {truth_id!r} is outside the frozen gold scope")
        evidence_validator(row, f"truth {truth_id!r}")
        truths_by_unit[unit_id].append(truth_id)

    for unit_id, row in coverage.items():
        state = row.get("review_state", "").strip()
        allowed_states = SCOPE_COVERAGE_STATES if scope is not None else COVERAGE_STATES
        if state not in allowed_states:
            raise BenchmarkError(f"unit {unit_id!r} has incomplete/invalid review_state {state!r}")
        if scope is not None and unit_id not in set(str(item) for item in scope["selected_unit_ids"]):
            if state != "unjudged":
                raise BenchmarkError(f"unselected unit {unit_id!r} must remain unjudged")
            continue
        has_truth = bool(truths_by_unit[unit_id])
        if state == "needs_adjudication":
            raise BenchmarkError(
                f"unit {unit_id!r} still needs human gold adjudication before freeze/scoring"
            )
        if state == "truth_recorded" and not has_truth:
            raise BenchmarkError(f"unit {unit_id!r} says truth_recorded but has no truth row")
        if state == "no_material_truth" and has_truth:
            raise BenchmarkError(f"unit {unit_id!r} says no_material_truth but has truth rows")

    candidates = _unique_rows(_read_csv(candidates_path), "candidate_id", "candidates.csv")
    for candidate_id, row in candidates.items():
        if not row.get("proposition", "").strip():
            raise BenchmarkError(f"candidate {candidate_id!r} has empty proposition")
        evidence_validator(row, f"candidate {candidate_id!r}")

    assessments = _unique_rows(_read_csv(assessment_path), "candidate_id", "assessment.csv")
    if set(assessments) != set(candidates):
        missing = sorted(set(candidates) - set(assessments))
        extra = sorted(set(assessments) - set(candidates))
        raise BenchmarkError(f"assessment candidate mismatch; missing={missing}, extra={extra}")

    covered_truths: set[str] = set()
    verdict_counts = {verdict: 0 for verdict in sorted(ASSESSMENT_VERDICTS)}
    for candidate_id, row in assessments.items():
        verdict = row.get("verdict", "").strip()
        if verdict not in ASSESSMENT_VERDICTS:
            raise BenchmarkError(f"candidate {candidate_id!r} has invalid verdict {verdict!r}")
        truth_ids = [value.strip() for value in row.get("truth_ids", "").split(";") if value.strip()]
        unknown = [truth_id for truth_id in truth_ids if truth_id not in truths]
        if unknown:
            raise BenchmarkError(f"candidate {candidate_id!r} references unknown truths {unknown}")
        if verdict == "unsupported" and truth_ids:
            raise BenchmarkError(f"unsupported candidate {candidate_id!r} must not map to truth")
        if verdict in {"correct", "distorted", "redundant"} and not truth_ids:
            raise BenchmarkError(f"{verdict} candidate {candidate_id!r} must map to truth")
        if verdict == "correct" and len(truth_ids) != 1:
            raise BenchmarkError(f"correct candidate {candidate_id!r} must map to exactly one truth")
        if verdict == "overmerged" and len(truth_ids) < 2:
            raise BenchmarkError(f"overmerged candidate {candidate_id!r} must map to at least two truths")
        if verdict == "correct":
            covered_truths.add(truth_ids[0])
        verdict_counts[verdict] += 1

    truth_counts = {
        importance: sum(1 for row in truths.values() if row["importance"].strip() == importance)
        for importance in sorted(TRUTH_IMPORTANCE)
    }
    covered_counts = {
        importance: sum(
            1
            for truth_id, row in truths.items()
            if row["importance"].strip() == importance and truth_id in covered_truths
        )
        for importance in sorted(TRUTH_IMPORTANCE)
    }
    candidate_total = len(candidates)
    result = {
        "source_sha256": _sha256_bytes(source_bytes),
        "review_units": len(units),
        "truths": len(truths),
        "candidates": candidate_total,
        "truth_counts": truth_counts,
        "covered_truth_counts": covered_counts,
        "must_recall": _ratio(covered_counts["must"], truth_counts["must"]),
        "material_recall": _ratio(covered_counts["material"], truth_counts["material"]),
        "relevance_precision": _ratio(verdict_counts["correct"], candidate_total),
        "unsupported_rate": _ratio(verdict_counts["unsupported"], candidate_total),
        "redundant_rate": _ratio(verdict_counts["redundant"], candidate_total),
        "overmerge_rate": _ratio(verdict_counts["overmerged"], candidate_total),
        "distorted_rate": _ratio(verdict_counts["distorted"], candidate_total),
        "verdict_counts": verdict_counts,
        "uncovered_truth_ids": sorted(set(truths) - covered_truths),
        "evidence_reopens": True,
        "semantic_matching_automated": False,
    }
    if scope is not None:
        selected_unit_ids = set(str(item) for item in scope["selected_unit_ids"])
        semantic_metrics: dict[str, dict[str, object]] = {}
        for capability_id in scope["semantic_capabilities"]:
            cap = str(capability_id)
            cap_truths = {
                truth_id: row
                for truth_id, row in truths.items()
                if cap in row.get("_capability_ids", [])
            }
            # A scope-wide capability measures the full selected scope without
            # asking a reviewer to repeat that label on every proposition.
            if cap == "semantic:multi_topic_longform":
                cap_truths = {truth_id: row for truth_id, row in truths.items() if row["unit_id"] in selected_unit_ids}
            cap_covered = set(cap_truths) & covered_truths
            must_total = sum(row["importance"].strip() == "must" for row in cap_truths.values())
            material_total = sum(row["importance"].strip() == "material" for row in cap_truths.values())
            semantic_metrics[cap] = {
                "truths": len(cap_truths),
                "must_truths": must_total,
                "material_truths": material_total,
                "covered_truths": len(cap_covered),
                "must_recall": _ratio(sum(cap_truths[item]["importance"].strip() == "must" for item in cap_covered), must_total),
                "material_recall": _ratio(sum(cap_truths[item]["importance"].strip() == "material" for item in cap_covered), material_total),
                "distorted_count": sum(
                    1 for assessment in assessments.values()
                    if assessment.get("verdict", "").strip() == "distorted"
                    and set(item.strip() for item in assessment.get("truth_ids", "").split(";") if item.strip()) & set(cap_truths)
                ),
            }
        result["semantic_metrics"] = semantic_metrics
        result["scope"] = {
            "total_prepared_units": len(units),
            "selected_units": len(selected_unit_ids),
            "selection_kind": scope["selection_kind"],
            "selection_fraction": _ratio(len(selected_unit_ids), len(units)),
            "full_source_recall_claimed": scope["selection_kind"] == "full_source_order",
            "gold_scope_version": scope["version"],
        }
    return result


def score(
    source_path: Path,
    units_path: Path,
    coverage_path: Path,
    truth_path: Path,
    candidates_path: Path,
    assessment_path: Path,
    *,
    scope_path: Path | None = None,
) -> dict[str, object]:
    source_bytes = source_path.read_bytes()
    try:
        text = source_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BenchmarkError("benchmark source is not UTF-8") from exc

    scope = _load_gold_scope(scope_path, source_bytes=source_bytes, units_path=units_path, unit_ids=set(_unique_rows(_read_csv(units_path), "unit_id", "units.csv"))) if scope_path else None
    return _score_rows(
        source_bytes=source_bytes,
        units_path=units_path,
        coverage_path=coverage_path,
        truth_path=truth_path,
        candidates_path=candidates_path,
        assessment_path=assessment_path,
        evidence_validator=lambda row, label: _validate_exact_evidence(text, row, label),
        scope=scope,
    )


def score_typed(
    source_path: Path,
    mode: str,
    units_path: Path,
    coverage_path: Path,
    truth_path: Path,
    candidates_path: Path,
    assessment_path: Path,
    *,
    media_index_path: Path | None = None,
    scope_path: Path | None = None,
) -> dict[str, object]:
    if mode not in {"table_range:v1", "media:v1"}:
        raise BenchmarkError("typed score mode must be table_range:v1 or media:v1")
    source_bytes = source_path.read_bytes()
    trusted_media: dict[str, object] | None = None
    if mode == "media:v1":
        if media_index_path is None:
            raise BenchmarkError("media:v1 scoring requires --media-index")
        trusted_media = _load_media_index(source_bytes, media_index_path)

    def validate(row: dict[str, str], label: str) -> None:
        selector = row.get("selector_json", "").strip()
        if not selector:
            raise BenchmarkError(f"{label} has no selector_json")
        if trusted_media is not None:
            try:
                payload = json.loads(selector)
            except json.JSONDecodeError as exc:
                raise BenchmarkError(f"{label} selector_json is invalid JSON") from exc
            if not isinstance(payload, dict):
                raise BenchmarkError(f"{label} selector_json must be an object")
            if payload.get("media_sha256") != trusted_media["source_sha256"]:
                raise BenchmarkError(f"{label} media selector uses the wrong retained-byte digest")
            if payload.get("duration_us") != trusted_media["duration_us"]:
                raise BenchmarkError(f"{label} media selector uses an untrusted duration")
        validate_typed_evidence(mode, source_bytes, selector, charset="utf-8" if mode == "table_range:v1" else None)

    scope = _load_gold_scope(scope_path, source_bytes=source_bytes, units_path=units_path, unit_ids=set(_unique_rows(_read_csv(units_path), "unit_id", "units.csv"))) if scope_path else None
    metrics = _score_rows(
        source_bytes=source_bytes,
        units_path=units_path,
        coverage_path=coverage_path,
        truth_path=truth_path,
        candidates_path=candidates_path,
        assessment_path=assessment_path,
        evidence_validator=validate,
        scope=scope,
    )
    metrics["evaluator_mode"] = mode
    if media_index_path is not None:
        metrics["media_index_sha256"] = _sha256_bytes(media_index_path.read_bytes())
    return metrics


def review_status(
    *,
    source_path: Path,
    units_path: Path,
    coverage_path: Path,
    scope_path: Path,
) -> dict[str, object]:
    """Report mechanical human-review progress without interpreting source content."""
    source_bytes = source_path.read_bytes()
    units = _unique_rows(_read_csv(units_path), "unit_id", "units.csv")
    scope = _load_gold_scope(
        scope_path,
        source_bytes=source_bytes,
        units_path=units_path,
        unit_ids=set(units),
    )
    coverage = _unique_rows(_read_csv(coverage_path), "unit_id", "coverage.csv")
    if set(coverage) != set(units):
        missing = sorted(set(units) - set(coverage))
        extra = sorted(set(coverage) - set(units))
        raise BenchmarkError(f"coverage unit mismatch; missing={missing}, extra={extra}")

    selected = set(str(item) for item in scope["selected_unit_ids"])
    counts = {
        "truth_recorded": 0,
        "no_material_truth": 0,
        "needs_adjudication": 0,
        "pending_blank": 0,
        "unjudged_nonselected": 0,
    }
    for unit_id, row in coverage.items():
        state = row.get("review_state", "").strip()
        if unit_id not in selected:
            if state != "unjudged":
                raise BenchmarkError(f"unselected unit {unit_id!r} must remain unjudged")
            counts["unjudged_nonselected"] += 1
            continue
        if state == "":
            counts["pending_blank"] += 1
            continue
        if state not in HUMAN_REVIEW_STATES:
            raise BenchmarkError(f"selected unit {unit_id!r} has invalid human review_state {state!r}")
        counts[state] += 1

    resolved = counts["truth_recorded"] + counts["no_material_truth"]
    return {
        "case_id": scope["case_id"],
        "gold_scope_sha256": _sha256_bytes(scope_path.read_bytes()),
        "selected_units": len(selected),
        "resolved_units": resolved,
        "truth_recorded_units": counts["truth_recorded"],
        "no_material_truth_units": counts["no_material_truth"],
        "needs_adjudication_units": counts["needs_adjudication"],
        "pending_blank_units": counts["pending_blank"],
        "unjudged_nonselected_units": counts["unjudged_nonselected"],
        "review_complete_for_gold_freeze": (
            counts["needs_adjudication"] == 0 and counts["pending_blank"] == 0
        ),
        "semantic_interpretation_performed": False,
    }


REVIEW_NOTES_FIELDS = ["unit_id", "rough_human_note", "uncertainty_note", "updated_at_utc"]
IMMUTABLE_PACKET_FILES = (
    "gold_scope.json",
    "manifest.json",
    "truth.csv",
    "candidates.csv",
    "assessment.csv",
    "units.csv",
    "selected_units.csv",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _csv_bytes(fieldnames: Sequence[str], rows: Iterable[dict[str, object]]) -> bytes:
    from io import StringIO

    buffer = StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _packet_source(packet: Path) -> Path:
    for name in ("representation.txt", "source.txt", "representation.json", "table.json"):
        candidate = packet / name
        if candidate.is_file():
            return candidate
    raise BenchmarkError("review packet has no exact text or typed Representation")


def _packet_manifest(packet: Path) -> dict[str, object]:
    path = packet / "manifest.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BenchmarkError("review packet manifest.json is not readable valid JSON") from exc
    if not isinstance(value, dict):
        raise BenchmarkError("review packet manifest.json must be an object")
    if value.get("semantic_model_calls", 0) != 0 or value.get("tested_extractor_seen", False) is not False:
        raise BenchmarkError("review packet records prohibited model or extractor activity")
    return value


def _packet_identity(packet: Path) -> tuple[Path, dict[str, str]]:
    source = _packet_source(packet)
    units_path = packet / "units.csv"
    scope_path = packet / "gold_scope.json"
    coverage_path = packet / "coverage.csv"
    required = [source, units_path, scope_path, coverage_path, packet / "manifest.json"]
    required.extend(packet / name for name in IMMUTABLE_PACKET_FILES if name != "gold_scope.json" and name != "manifest.json")
    missing = [str(path.name) for path in required if not path.is_file()]
    if missing:
        raise BenchmarkError(f"review packet is missing required files: {missing}")
    _packet_manifest(packet)
    units = _unique_rows(_read_csv(units_path), "unit_id", "units.csv")
    _load_gold_scope(scope_path, source_bytes=source.read_bytes(), units_path=units_path, unit_ids=set(units))
    # review_status also protects every non-selected unit before a write is allowed.
    review_status(source_path=source, units_path=units_path, coverage_path=coverage_path, scope_path=scope_path)
    immutable = {name: _sha256_bytes((packet / name).read_bytes()) for name in IMMUTABLE_PACKET_FILES}
    immutable["source"] = _sha256_bytes(source.read_bytes())
    return source, immutable


def _verify_packet_identity(packet: Path, source: Path, immutable: dict[str, str]) -> None:
    if _packet_source(packet) != source:
        raise BenchmarkError("review packet Representation path changed during the session")
    for name, digest in immutable.items():
        path = source if name == "source" else packet / name
        if not path.is_file() or _sha256_bytes(path.read_bytes()) != digest:
            raise BenchmarkError(f"review packet immutable file changed during the session: {name}")


def _load_review_notes(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    return _unique_rows(_read_csv(path), "unit_id", "review_notes.csv")


def _save_review_files(
    packet: Path,
    coverage_rows: Sequence[dict[str, str]],
    notes: dict[str, dict[str, str]],
    *,
    backup_created: bool,
) -> bool:
    if not backup_created:
        backup_root = packet / ".review-backups"
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_dir = backup_root / stamp
        suffix = 1
        while backup_dir.exists():
            backup_dir = backup_root / f"{stamp}-{suffix}"
            suffix += 1
        backup_dir.mkdir(parents=True, exist_ok=False)
        shutil.copy2(packet / "coverage.csv", backup_dir / "coverage.csv")
        notes_path = packet / "review_notes.csv"
        if notes_path.exists():
            shutil.copy2(notes_path, backup_dir / "review_notes.csv")
        backup_created = True
    coverage_fields = list(coverage_rows[0]) if coverage_rows else ["unit_id", "review_state", "notes"]
    _atomic_write_bytes(packet / "coverage.csv", _csv_bytes(coverage_fields, coverage_rows))
    if notes:
        _atomic_write_bytes(packet / "review_notes.csv", _csv_bytes(REVIEW_NOTES_FIELDS, notes.values()))
    elif (packet / "review_notes.csv").exists():
        _atomic_write_bytes(packet / "review_notes.csv", _csv_bytes(REVIEW_NOTES_FIELDS, ()))
    return backup_created


def _format_typed_row(unit: dict[str, str]) -> str:
    try:
        cells = json.loads(unit.get("cells_json", "[]"))
    except json.JSONDecodeError:
        cells = unit.get("cells_json", "")
    payload = {
        "hoja": unit.get("sheet", ""),
        "fila": unit.get("row_start", ""),
        "celdas": cells,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False)


def _load_display_units(
    packet: Path, source: Path, scope: dict[str, object]
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    units_by_id = _unique_rows(_read_csv(packet / "units.csv"), "unit_id", "units.csv")
    all_units = list(units_by_id.values())
    selected_ids = set(str(item) for item in scope["selected_unit_ids"])
    selected = [row for row in all_units if row["unit_id"] in selected_ids]
    if source.suffix.lower() == ".json":
        for row in all_units:
            if not row.get("cells_json"):
                raise BenchmarkError("typed review packet unit is missing exact cells_json")
    return all_units, selected


def _render_unit(unit: dict[str, str], source: Path, *, context: bool = False) -> str:
    if source.suffix.lower() == ".json":
        prefix = "CONTEXTO" if context else "FILA SELECCIONADA"
        return f"[{prefix}]\n{_format_typed_row(unit)}"
    try:
        text = source.read_bytes().decode("utf-8")
        start = int(unit["char_start"])
        end = int(unit["char_end"])
    except (UnicodeDecodeError, KeyError, ValueError) as exc:
        raise BenchmarkError("text review unit has invalid exact offsets") from exc
    prefix = "CONTEXTO" if context else "FRAGMENTO SELECCIONADO"
    return f"[{prefix}]\n{text[start:end]}"


def _print_progress(status: dict[str, object], output_fn) -> None:
    output_fn(
        f"Progreso: {status['resolved_units']} resueltas · "
        f"{status['needs_adjudication_units']} dudosas · "
        f"{status['pending_blank_units']} pendientes"
    )


def run_human_review(
    packet: Path,
    *,
    session_size: int = 5,
    start_unit: str | None = None,
    read_only: bool = False,
    input_fn=input,
    output_fn=print,
) -> dict[str, object]:
    """Run a presentation-only human review session over one unpacked packet."""
    if not packet.is_dir() or packet.name.endswith(".tar.gz"):
        raise BenchmarkError("human-review requires an unpacked packet directory")
    if session_size < 1:
        raise BenchmarkError("session-size must be positive")
    source, immutable = _packet_identity(packet)
    scope = _load_gold_scope(
        packet / "gold_scope.json",
        source_bytes=source.read_bytes(),
        units_path=packet / "units.csv",
        unit_ids=set(_unique_rows(_read_csv(packet / "units.csv"), "unit_id", "units.csv")),
    )
    all_units, selected = _load_display_units(packet, source, scope)
    all_unit_ids = [row["unit_id"] for row in all_units]
    selected_by_id = {row["unit_id"]: row for row in selected}
    coverage_rows = _read_csv(packet / "coverage.csv")
    coverage_by_id = _unique_rows(coverage_rows, "unit_id", "coverage.csv")
    notes = _load_review_notes(packet / "review_notes.csv")
    selected_ids = [row["unit_id"] for row in selected]
    if start_unit is not None:
        if start_unit not in selected_by_id:
            raise BenchmarkError(f"unknown selected unit {start_unit!r}")
        cursor = selected_ids.index(start_unit)
    else:
        cursor = next(
            (index for index, unit_id in enumerate(selected_ids) if coverage_by_id[unit_id].get("review_state", "") == ""),
            0,
        )
    decisions = 0
    backup_created = False

    while selected:
        if cursor >= len(selected):
            cursor = 0
        unit_id = selected_ids[cursor]
        unit = selected_by_id[unit_id]
        status = review_status(
            source_path=source,
            units_path=packet / "units.csv",
            coverage_path=packet / "coverage.csv",
            scope_path=packet / "gold_scope.json",
        )
        output_fn(f"\nCaso: {scope['case_id']}\nUnidad: {cursor + 1} de {len(selected)}")
        _print_progress(status, output_fn)
        output_fn("\n" + _render_unit(unit, source))
        output_fn("\n¿Qué harías con este fragmento?\n1. Sí, aquí hay algo importante para registrar\n2. No, aquí no hay nada importante para registrar\n3. No estoy seguro\n4. Dejarlo para después\nq. Guardar y salir\n?. Ayuda")
        command = input_fn("> ").strip().lower()
        if command in {"q", "quit", "salir"}:
            break
        if command in {"?", "help", "ayuda"}:
            output_fn("Controles: 1/y material, 2/n no material, 3/u no seguro, 4/s saltar, b anterior, c contexto, r repetir, q salir, x cancelar.")
            continue
        if command in {"r", "redisplay"}:
            continue
        if command in {"c", "contexto"}:
            current_all_index = all_unit_ids.index(unit_id)
            context_rows: list[dict[str, str]] = []
            if current_all_index > 0:
                context_rows.append(all_units[current_all_index - 1])
            if current_all_index + 1 < len(all_units):
                context_rows.append(all_units[current_all_index + 1])
            if not context_rows:
                output_fn("No hay una unidad vecina disponible para contexto.")
            else:
                for context_row in context_rows:
                    output_fn(_render_unit(context_row, source, context=True))
            continue
        if command in {"x", "cancelar"}:
            output_fn("Sesión cancelada. No se guarda la unidad actual.")
            break
        if command in {"b", "anterior"}:
            cursor = (cursor - 1) % len(selected)
            continue
        if command in {"4", "s", "skip", "saltar"}:
            decisions += 1
            cursor = (cursor + 1) % len(selected)
        elif command in {"1", "y", "si", "sí"}:
            note = "" if read_only else input_fn("En tus palabras, ¿qué dice/pasa aquí?\n(No tiene que sonar formal.)\n> ")
            decisions += 1
            if not read_only:
                _verify_packet_identity(packet, source, immutable)
                coverage_by_id[unit_id]["review_state"] = "truth_recorded"
                notes[unit_id] = {"unit_id": unit_id, "rough_human_note": note, "uncertainty_note": "", "updated_at_utc": _utc_now()}
                backup_created = _save_review_files(packet, list(coverage_by_id.values()), notes, backup_created=backup_created)
            cursor = (cursor + 1) % len(selected)
        elif command in {"2", "n", "no"}:
            decisions += 1
            if not read_only:
                _verify_packet_identity(packet, source, immutable)
                coverage_by_id[unit_id]["review_state"] = "no_material_truth"
                notes.pop(unit_id, None)
                backup_created = _save_review_files(packet, list(coverage_by_id.values()), notes, backup_created=backup_created)
            cursor = (cursor + 1) % len(selected)
        elif command in {"3", "u", "duda", "no estoy seguro"}:
            output_fn("Está bien no estar seguro. No adivines.")
            uncertainty = "" if read_only else input_fn("¿Qué te genera duda? (opcional)\n> ")
            decisions += 1
            if not read_only:
                _verify_packet_identity(packet, source, immutable)
                coverage_by_id[unit_id]["review_state"] = "needs_adjudication"
                notes[unit_id] = {"unit_id": unit_id, "rough_human_note": "", "uncertainty_note": uncertainty, "updated_at_utc": _utc_now()}
                backup_created = _save_review_files(packet, list(coverage_by_id.values()), notes, backup_created=backup_created)
            cursor = (cursor + 1) % len(selected)
        else:
            output_fn("No entendí ese control. Usa ? para ver las opciones.")
            continue
        if decisions >= session_size:
            output_fn("\nSesión terminada. Puedes continuar después con el mismo paquete.")
            break
        if not read_only:
            _print_progress(
                review_status(
                    source_path=source,
                    units_path=packet / "units.csv",
                    coverage_path=packet / "coverage.csv",
                    scope_path=packet / "gold_scope.json",
                ),
                output_fn,
            )
    _verify_packet_identity(packet, source, immutable)
    return review_status(
        source_path=source,
        units_path=packet / "units.csv",
        coverage_path=packet / "coverage.csv",
        scope_path=packet / "gold_scope.json",
    )


def freeze_gold(
    *,
    case_id: str,
    source_path: Path,
    units_path: Path,
    coverage_path: Path,
    truth_path: Path,
    candidates_path: Path,
    assessment_path: Path,
    scope_path: Path,
    output_path: Path,
    threshold_policy_state: str = "not_frozen",
) -> dict[str, object]:
    """Validate a future human gold set without creating or interpreting truths."""
    if threshold_policy_state not in {"not_frozen", "counts_inspected", "frozen"}:
        raise BenchmarkError("invalid threshold policy state")
    scope = _load_gold_scope(
        scope_path,
        source_bytes=source_path.read_bytes(),
        units_path=units_path,
        unit_ids=set(_unique_rows(_read_csv(units_path), "unit_id", "units.csv")),
    )
    if scope["case_id"] not in {"", case_id}:
        raise BenchmarkError("gold scope case_id does not match freeze case")
    metrics = score(source_path, units_path, coverage_path, truth_path, candidates_path, assessment_path, scope_path=scope_path)
    if metrics["candidates"] != 0 or metrics["semantic_matching_automated"] is not False:
        raise BenchmarkError("gold freeze cannot include candidate output or automated semantic matching")
    truths = _unique_rows(_read_csv(truth_path), "truth_id", "truth.csv")
    if not truths:
        raise BenchmarkError("cannot freeze empty semantic-capability gold")
    scope_capabilities = [str(item) for item in scope["semantic_capabilities"]]
    for capability_id in scope_capabilities:
        if capability_id == "semantic:multi_topic_longform":
            continue
        if not any(capability_id in row.get("capability_ids", "").split(";") for row in truths.values()):
            raise BenchmarkError(f"cannot freeze semantic capability {capability_id!r} with zero gold truths")
    manifest = {
        "format": GOLD_PROTOCOL_VERSION,
        "case_id": case_id,
        "source_sha256": _sha256_bytes(source_path.read_bytes()),
        "units_sha256": _unit_file_sha256(units_path),
        "gold_scope_sha256": _sha256_bytes(scope_path.read_bytes()),
        "coverage_sha256": _sha256_bytes(coverage_path.read_bytes()),
        "truth_sha256": _sha256_bytes(truth_path.read_bytes()),
        "truth_row_count": len(truths),
        "semantic_capability_truth_counts": metrics.get("semantic_metrics", {}),
        "reviewer_authority": "human",
        "tested_extractor_seen": False,
        "semantic_model_assistance": False,
        "threshold_policy_state": threshold_policy_state,
        "freeze_timestamp": None,
    }
    output_path.write_bytes(_canonical_json(manifest))
    return manifest


def evaluate_corpus(corpus_path: Path) -> dict[str, object]:
    """Derive readiness for the benchmark's explicitly declared capability targets.

    Capabilities are benchmark stress dimensions, not an ontology of civic record
    types. A finite reference corpus can prove coverage only for the capabilities it
    names; this function must never imply universal document/media support.
    """

    try:
        value = json.loads(corpus_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BenchmarkError("corpus manifest is not readable valid JSON") from exc
    if not isinstance(value, dict):
        raise BenchmarkError("corpus manifest must be an object")

    if "required_case_classes" in value or "broad_certification_state" in value:
        raise BenchmarkError(
            "document-class broad-certification fields are retired; use declared capability targets"
        )
    if value.get("certification_scope") != "declared_capabilities_only":
        raise BenchmarkError("certification_scope must be 'declared_capabilities_only'")
    if value.get("universal_support_claimed") is not False:
        raise BenchmarkError("universal_support_claimed must be false")

    required_raw = value.get("required_capabilities")
    cases = value.get("cases")
    if not isinstance(required_raw, list) or not required_raw:
        raise BenchmarkError("required_capabilities must be a non-empty list")
    if not isinstance(cases, list):
        raise BenchmarkError("cases must be a list")

    required: list[str] = []
    for raw in required_raw:
        if not isinstance(raw, dict):
            raise BenchmarkError("every required capability must be an object")
        capability_id = raw.get("id")
        dimension = raw.get("dimension")
        description = raw.get("description")
        verification_mode = raw.get("verification_mode")
        if not isinstance(capability_id, str) or not capability_id:
            raise BenchmarkError("every required capability needs a non-empty id")
        if not isinstance(dimension, str) or not dimension:
            raise BenchmarkError(f"capability {capability_id!r} needs a dimension")
        if not isinstance(description, str) or not description:
            raise BenchmarkError(f"capability {capability_id!r} needs a description")
        if verification_mode not in {"deterministic", "semantic_gold"}:
            raise BenchmarkError(
                f"capability {capability_id!r} needs verification_mode deterministic|semantic_gold"
            )
        required.append(capability_id)
    if len(set(required)) != len(required):
        raise BenchmarkError("required_capabilities contains duplicate ids")
    capability_modes = {raw["id"]: raw["verification_mode"] for raw in required_raw}

    seen_ids: set[str] = set()
    by_capability: dict[str, list[dict[str, object]]] = {
        capability_id: [] for capability_id in required
    }
    for raw in cases:
        if not isinstance(raw, dict):
            raise BenchmarkError("every corpus case must be an object")
        case_id = raw.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            raise BenchmarkError("every corpus case needs a non-empty case_id")
        if case_id in seen_ids:
            raise BenchmarkError(f"duplicate corpus case_id {case_id!r}")
        seen_ids.add(case_id)

        # Archetypes are descriptive benchmark metadata only. There is deliberately
        # no registry to which a case must conform.
        if "case_class" in raw:
            raise BenchmarkError(
                f"case {case_id!r} uses retired case_class; use optional benchmark_archetypes"
            )
        archetypes = raw.get("benchmark_archetypes", [])
        if not isinstance(archetypes, list) or not all(
            isinstance(item, str) and item for item in archetypes
        ):
            raise BenchmarkError(f"case {case_id!r} benchmark_archetypes must be a string list")

        covers = raw.get("covers")
        if not isinstance(covers, list) or not covers or not all(
            isinstance(item, str) and item for item in covers
        ):
            raise BenchmarkError(f"case {case_id!r} needs a non-empty covers list")
        if len(set(covers)) != len(covers):
            raise BenchmarkError(f"case {case_id!r} covers contains duplicates")
        unknown = sorted(set(covers) - set(required))
        if unknown:
            raise BenchmarkError(
                f"case {case_id!r} covers undeclared capabilities {unknown}; add targets explicitly"
            )

        deterministic_verification = raw.get("deterministic_verification", {})
        if not isinstance(deterministic_verification, dict):
            raise BenchmarkError(f"case {case_id!r} deterministic_verification must be an object")
        for capability_id, state in deterministic_verification.items():
            if capability_id not in covers:
                raise BenchmarkError(
                    f"case {case_id!r} verifies capability {capability_id!r} it does not cover"
                )
            if state not in {"not_run", "passed", "failed"}:
                raise BenchmarkError(
                    f"case {case_id!r} has invalid deterministic state for {capability_id!r}"
                )
        if raw.get("gold_state") not in {"pending", "frozen"}:
            raise BenchmarkError(f"case {case_id!r} has invalid gold_state")
        if raw.get("adjudication_state") not in {"not_run", "incomplete", "complete"}:
            raise BenchmarkError(f"case {case_id!r} has invalid adjudication_state")
        evaluator_mode = raw.get("evaluator_mode")
        if not isinstance(evaluator_mode, str) or not evaluator_mode:
            raise BenchmarkError(f"case {case_id!r} needs evaluator_mode")
        semantic_covered = {
            capability_id for capability_id in covers if capability_modes.get(capability_id) == "semantic_gold"
        }
        semantic_verification_raw = raw.get("semantic_verification", {})
        if isinstance(semantic_verification_raw, dict) and set(semantic_verification_raw) - set(covers):
            raise BenchmarkError(f"case {case_id!r} verifies semantic capability it does not cover")
        if semantic_covered:
            gold_scope_state = raw.get("gold_scope_state", "pending")
            if gold_scope_state not in {"pending", "frozen"}:
                raise BenchmarkError(f"case {case_id!r} has invalid gold_scope_state")
            scope_capabilities = raw.get("scope_capabilities", [])
            if not isinstance(scope_capabilities, list) or len(scope_capabilities) != len(set(scope_capabilities)):
                raise BenchmarkError(f"case {case_id!r} scope_capabilities must be a unique list")
            if set(scope_capabilities) - semantic_covered:
                raise BenchmarkError(f"case {case_id!r} has scope capability it does not cover")
            semantic_verification = semantic_verification_raw
            if not isinstance(semantic_verification, dict):
                raise BenchmarkError(f"case {case_id!r} semantic_verification must be an object")
            if set(semantic_verification) - semantic_covered:
                raise BenchmarkError(f"case {case_id!r} verifies semantic capability it does not cover")
            for capability_id in semantic_covered:
                entry = semantic_verification.get(capability_id, {"state": "not_run", "result_sha256": None})
                if not isinstance(entry, dict) or entry.get("state") not in SEMANTIC_VERIFICATION_STATES:
                    raise BenchmarkError(f"case {case_id!r} has invalid semantic verification for {capability_id!r}")
                state = entry["state"]
                digest = entry.get("result_sha256")
                if state == "not_run" and digest is not None:
                    raise BenchmarkError(f"case {case_id!r} not_run semantic verification must have null result_sha256")
                if state in {"passed", "failed"} and not _valid_sha256(digest):
                    raise BenchmarkError(f"case {case_id!r} {state} semantic verification requires result_sha256")
        for capability_id in covers:
            by_capability[capability_id].append(raw)

    missing = [capability_id for capability_id, rows in by_capability.items() if not rows]
    deterministic_failed = [
        capability_id
        for capability_id, rows in by_capability.items()
        if capability_modes[capability_id] == "deterministic"
        and rows
        and not any(
            row.get("deterministic_verification", {}).get(capability_id) == "passed"
            for row in rows
        )
        and any(
            row.get("deterministic_verification", {}).get(capability_id) == "failed"
            for row in rows
        )
    ]
    deterministic_pending = [
        capability_id
        for capability_id, rows in by_capability.items()
        if capability_modes[capability_id] == "deterministic"
        and rows
        and capability_id not in deterministic_failed
        and not any(
            row.get("deterministic_verification", {}).get(capability_id) == "passed"
            for row in rows
        )
    ]
    gold_pending = [
        capability_id
        for capability_id, rows in by_capability.items()
        if capability_modes[capability_id] == "semantic_gold"
        and rows
        and not any(row.get("gold_scope_state", "pending") == "frozen" and row["gold_state"] == "frozen" for row in rows)
    ]
    gold_scope_pending = [
        capability_id
        for capability_id, rows in by_capability.items()
        if capability_modes[capability_id] == "semantic_gold"
        and rows
        and not any(row.get("gold_scope_state", "pending") == "frozen" for row in rows)
    ]
    adjudication_pending = [
        capability_id
        for capability_id, rows in by_capability.items()
        if capability_modes[capability_id] == "semantic_gold"
        and rows
        and any(row["gold_state"] == "frozen" for row in rows)
        and not any(
            row["gold_state"] == "frozen" and row["adjudication_state"] == "complete"
            for row in rows
        )
    ]
    deterministically_verified = [
        capability_id
        for capability_id, rows in by_capability.items()
        if capability_modes[capability_id] == "deterministic"
        and any(
            row.get("deterministic_verification", {}).get(capability_id) == "passed"
            for row in rows
        )
    ]
    semantic_failed = [
        capability_id
        for capability_id, rows in by_capability.items()
        if capability_modes[capability_id] == "semantic_gold"
        and any(
            row.get("gold_scope_state") == "frozen"
            and row["gold_state"] == "frozen"
            and row["adjudication_state"] == "complete"
            and row.get("semantic_verification", {}).get(capability_id, {}).get("state") == "failed"
            for row in rows
        )
    ]
    evaluation_pending = [
        capability_id
        for capability_id, rows in by_capability.items()
        if capability_modes[capability_id] == "semantic_gold"
        and rows
        and any(row.get("gold_scope_state") == "frozen" and row["gold_state"] == "frozen" for row in rows)
        and not any(
            row.get("gold_scope_state") == "frozen"
            and row["gold_state"] == "frozen"
            and row["adjudication_state"] == "complete"
            and row.get("semantic_verification", {}).get(capability_id, {}).get("state") in {"passed", "failed"}
            for row in rows
        )
    ]
    semantic_verified = [
        capability_id
        for capability_id, rows in by_capability.items()
        if capability_modes[capability_id] == "semantic_gold"
        and any(
            row["gold_state"] == "frozen" and row["adjudication_state"] == "complete"
            and row.get("gold_scope_state") == "frozen"
            and row.get("semantic_verification", {}).get(capability_id, {}).get("state") == "passed"
            and _valid_sha256(row.get("semantic_verification", {}).get(capability_id, {}).get("result_sha256"))
            and value.get("threshold_policy_state") == "frozen"
            for row in rows
        )
    ]
    verified_set = set(deterministically_verified + semantic_verified)
    verified = [capability_id for capability_id in required if capability_id in verified_set]
    gate_ready = not (
        missing
        or deterministic_failed
        or deterministic_pending
        or gold_scope_pending
        or gold_pending
        or adjudication_pending
        or evaluation_pending
        or semantic_failed
        or set(semantic_verified) != {
            capability_id for capability_id, mode in capability_modes.items() if mode == "semantic_gold"
        }
    )
    return {
        "corpus_version": value.get("version"),
        "certification_scope": "declared_capabilities_only",
        "universal_support_claimed": False,
        "required_capabilities": required,
        "verification_modes": capability_modes,
        "case_count": len(cases),
        "represented_capabilities": [
            capability_id for capability_id, rows in by_capability.items() if rows
        ],
        "missing_capabilities": missing,
        "deterministic_failed_capabilities": deterministic_failed,
        "deterministic_pending_capabilities": deterministic_pending,
        "gold_scope_pending_capabilities": gold_scope_pending,
        "gold_pending_capabilities": gold_pending,
        "adjudication_pending_capabilities": adjudication_pending,
        "evaluation_pending_capabilities": evaluation_pending,
        "semantic_failed_capabilities": semantic_failed,
        "deterministically_verified_capabilities": deterministically_verified,
        "semantic_verified_capabilities": semantic_verified,
        "verified_capabilities": verified,
        "declared_capability_gate_ready": gate_ready,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    corpus_parser = subparsers.add_parser("corpus-status", help="derive declared-capability benchmark readiness")
    corpus_parser.add_argument("--corpus", type=Path, required=True)

    prepare_parser = subparsers.add_parser("prepare", help="create a deterministic review worksheet")
    prepare_parser.add_argument("--source", type=Path, required=True)
    prepare_parser.add_argument("--output-dir", type=Path, required=True)
    prepare_parser.add_argument("--source-label")
    table_parser = subparsers.add_parser("prepare-table", help="create a blank structured-table worksheet")
    table_parser.add_argument("--source", type=Path, required=True)
    table_parser.add_argument("--output-dir", type=Path, required=True)
    table_parser.add_argument("--source-label")
    table_parser.add_argument("--case-id", default="")
    scope_parser = subparsers.add_parser("prepare-scope", help="freeze a full-source gold scope")
    scope_parser.add_argument("--source", type=Path, required=True)
    scope_parser.add_argument("--units", type=Path, required=True)
    scope_parser.add_argument("--output", type=Path, required=True)
    scope_parser.add_argument("--case-id", required=True)
    scope_parser.add_argument("--semantic-capability", action="append", required=True)
    scope_parser.add_argument("--selection-policy", required=True)
    review_parser = subparsers.add_parser("review-status", help="report human gold-review progress without semantic interpretation")
    review_parser.add_argument("--source", type=Path, required=True)
    review_parser.add_argument("--units", type=Path, required=True)
    review_parser.add_argument("--coverage", type=Path, required=True)
    review_parser.add_argument("--scope", type=Path, required=True)
    human_parser = subparsers.add_parser("human-review", help="run the local uncertainty-safe human review helper")
    human_parser.add_argument("--packet", type=Path, required=True)
    human_parser.add_argument("--session-size", type=int, default=5)
    human_parser.add_argument("--start-unit")
    human_parser.add_argument("--read-only", action="store_true")
    media_parser = subparsers.add_parser("prepare-media", help="create a blank timed-media worksheet")
    media_parser.add_argument("--source", type=Path, required=True)
    media_parser.add_argument("--media-index", type=Path, required=True)
    media_parser.add_argument("--output-dir", type=Path, required=True)
    media_parser.add_argument("--source-label")

    score_parser = subparsers.add_parser("score", help="validate a completed gold/adjudication set and score it")
    score_parser.add_argument("--source", type=Path, required=True)
    score_parser.add_argument("--units", type=Path, required=True)
    score_parser.add_argument("--coverage", type=Path, required=True)
    score_parser.add_argument("--truth", type=Path, required=True)
    score_parser.add_argument("--candidates", type=Path, required=True)
    score_parser.add_argument("--assessment", type=Path, required=True)
    score_parser.add_argument("--scope", type=Path)
    score_parser.add_argument("--output", type=Path)
    typed_score_parser = subparsers.add_parser(
        "score-typed", help="validate and score table/media gold using production locator semantics"
    )
    typed_score_parser.add_argument("--source", type=Path, required=True)
    typed_score_parser.add_argument("--mode", choices=("table_range:v1", "media:v1"), required=True)
    typed_score_parser.add_argument("--media-index", type=Path)
    typed_score_parser.add_argument("--units", type=Path, required=True)
    typed_score_parser.add_argument("--coverage", type=Path, required=True)
    typed_score_parser.add_argument("--truth", type=Path, required=True)
    typed_score_parser.add_argument("--candidates", type=Path, required=True)
    typed_score_parser.add_argument("--assessment", type=Path, required=True)
    typed_score_parser.add_argument("--scope", type=Path)
    typed_score_parser.add_argument("--output", type=Path)
    freeze_parser = subparsers.add_parser("freeze-gold", help="validate and freeze a completed human gold set")
    freeze_parser.add_argument("--case-id", required=True)
    freeze_parser.add_argument("--source", type=Path, required=True)
    freeze_parser.add_argument("--units", type=Path, required=True)
    freeze_parser.add_argument("--coverage", type=Path, required=True)
    freeze_parser.add_argument("--truth", type=Path, required=True)
    freeze_parser.add_argument("--candidates", type=Path, required=True)
    freeze_parser.add_argument("--assessment", type=Path, required=True)
    freeze_parser.add_argument("--scope", type=Path, required=True)
    freeze_parser.add_argument("--output", type=Path, required=True)
    freeze_parser.add_argument("--threshold-policy-state", choices=("not_frozen", "counts_inspected", "frozen"), default="not_frozen")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "corpus-status":
            result = evaluate_corpus(args.corpus)
        elif args.command == "prepare":
            result = prepare(args.source, args.output_dir, args.source_label)
        elif args.command == "prepare-table":
            result = prepare_table(args.source, args.output_dir, args.source_label, args.case_id)
        elif args.command == "prepare-scope":
            result = prepare_full_scope(
                args.source,
                args.units,
                args.output,
                args.case_id,
                args.semantic_capability,
                args.selection_policy,
            )
        elif args.command == "review-status":
            result = review_status(
                source_path=args.source,
                units_path=args.units,
                coverage_path=args.coverage,
                scope_path=args.scope,
            )
        elif args.command == "human-review":
            result = run_human_review(
                args.packet,
                session_size=args.session_size,
                start_unit=args.start_unit,
                read_only=args.read_only,
            )
        elif args.command == "prepare-media":
            result = prepare_media(args.source, args.media_index, args.output_dir, args.source_label)
        elif args.command == "score-typed":
            result = score_typed(
                args.source,
                args.mode,
                args.units,
                args.coverage,
                args.truth,
                args.candidates,
                args.assessment,
                media_index_path=args.media_index,
                scope_path=args.scope,
            )
        elif args.command == "freeze-gold":
            result = freeze_gold(
                case_id=args.case_id,
                source_path=args.source,
                units_path=args.units,
                coverage_path=args.coverage,
                truth_path=args.truth,
                candidates_path=args.candidates,
                assessment_path=args.assessment,
                scope_path=args.scope,
                output_path=args.output,
                threshold_policy_state=args.threshold_policy_state,
            )
        else:
            result = score(
                args.source,
                args.units,
                args.coverage,
                args.truth,
                args.candidates,
                args.assessment,
                scope_path=args.scope,
            )
    except BenchmarkError as exc:
        raise SystemExit(f"LECTOR_002_REFERENCE_ERROR: {exc}") from exc

    if args.command == "human-review":
        print(
            f"Estado: {result['resolved_units']} resueltas · "
            f"{result['needs_adjudication_units']} dudosas · "
            f"{result['pending_blank_units']} pendientes"
        )
        return 0
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if getattr(args, "output", None):
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
