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
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

from canario.lector.locators import SemanticLocatorError, reopen_selector
from canario.processors.targets import TargetContractError, TargetRegistry

PREPARATION_VERSION = "lector-002-reference-text:v2"
TYPED_PREPARATION_VERSION = "lector-002-typed-evidence:v1"
MAX_UNIT_CHARS = 4_000
PREFERRED_SPLIT_CHARS = 2_800

TRUTH_IMPORTANCE = {"must", "material"}
ASSESSMENT_VERDICTS = {"correct", "distorted", "unsupported", "redundant", "overmerged"}
COVERAGE_STATES = {"truth_recorded", "no_material_truth"}


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
        "For every unit, a human records either `truth_recorded` or `no_material_truth` in\n"
        "`coverage.csv`. Each material proposition is added to `truth.csv` with `importance` =\n"
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


def _blank_typed_worksheets(output_dir: Path, manifest: dict[str, object], units: list[dict[str, object]]) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _write_csv(output_dir / "units.csv", list(units[0]) if units else ["unit_id"], units)
    _write_csv(output_dir / "coverage.csv", ["unit_id", "review_state", "notes"],
               ({"unit_id": unit["unit_id"], "review_state": "", "notes": ""} for unit in units))
    _write_csv(output_dir / "truth.csv", ["truth_id", "unit_id", "importance", "proposition", "selector_json", "notes"], ())
    _write_csv(output_dir / "candidates.csv", ["candidate_id", "proposition", "selector_json"], ())
    _write_csv(output_dir / "assessment.csv", ["candidate_id", "truth_ids", "verdict", "notes"], ())
    return manifest


def prepare_table(source_path: Path, output_dir: Path, source_label: str | None = None) -> dict[str, object]:
    """Prepare a blank worksheet over the canonical structured-table derivative."""
    source_bytes = source_path.read_bytes()
    try:
        value = json.loads(source_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BenchmarkError("table-reference mode requires canonical JSON table bytes") from exc
    sheets = value.get("sheets") if isinstance(value, dict) else None
    if not isinstance(sheets, list):
        raise BenchmarkError("table-reference source has no sheets")
    units: list[dict[str, object]] = []
    for sheet in sheets:
        if not isinstance(sheet, dict) or not isinstance(sheet.get("rows"), list):
            raise BenchmarkError("table-reference source has malformed sheet rows")
        for ordinal, _row in enumerate(sheet["rows"], start=1):
            units.append({
                "unit_id": f"{sheet['ordinal']}:R{ordinal}",
                "sheet": sheet["name"],
                "row_start": ordinal,
                "row_end": ordinal,
            })
    manifest = {
        "preparation_version": TYPED_PREPARATION_VERSION,
        "evaluator_mode": "table_range:v1",
        "source_label": source_label or source_path.name,
        "source_sha256": _sha256_bytes(source_bytes),
        "source_bytes": len(source_bytes),
        "review_units": len(units),
        "truth_generated": False,
        "semantic_model_calls": 0,
        "tested_extractor_seen": False,
        "gold_rows": 0,
    }
    return _blank_typed_worksheets(output_dir, manifest, units)


def _load_media_index(source_bytes: bytes, media_index_path: Path) -> dict[str, object]:
    try:
        index = json.loads(media_index_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BenchmarkError("media-reference mode requires a readable canonical media index") from exc
    if not isinstance(index, dict) or index.get("format") != "canario.media_index.v1":
        raise BenchmarkError("media index has an unknown format")
    digest = _sha256_bytes(source_bytes)
    if index.get("source_sha256") != digest:
        raise BenchmarkError("media index does not describe the frozen source bytes")
    duration_us = index.get("duration_us")
    if isinstance(duration_us, bool) or not isinstance(duration_us, int) or duration_us <= 0:
        raise BenchmarkError("media index has no positive integer duration_us")
    return index


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
        evidence_validator(row, f"truth {truth_id!r}")
        truths_by_unit[unit_id].append(truth_id)

    for unit_id, row in coverage.items():
        state = row.get("review_state", "").strip()
        if state not in COVERAGE_STATES:
            raise BenchmarkError(f"unit {unit_id!r} has incomplete/invalid review_state {state!r}")
        has_truth = bool(truths_by_unit[unit_id])
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
    return {
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


def score(
    source_path: Path,
    units_path: Path,
    coverage_path: Path,
    truth_path: Path,
    candidates_path: Path,
    assessment_path: Path,
) -> dict[str, object]:
    source_bytes = source_path.read_bytes()
    try:
        text = source_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BenchmarkError("benchmark source is not UTF-8") from exc

    return _score_rows(
        source_bytes=source_bytes,
        units_path=units_path,
        coverage_path=coverage_path,
        truth_path=truth_path,
        candidates_path=candidates_path,
        assessment_path=assessment_path,
        evidence_validator=lambda row, label: _validate_exact_evidence(text, row, label),
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

    metrics = _score_rows(
        source_bytes=source_bytes,
        units_path=units_path,
        coverage_path=coverage_path,
        truth_path=truth_path,
        candidates_path=candidates_path,
        assessment_path=assessment_path,
        evidence_validator=validate,
    )
    metrics["evaluator_mode"] = mode
    if media_index_path is not None:
        metrics["media_index_sha256"] = _sha256_bytes(media_index_path.read_bytes())
    return metrics


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
        if not isinstance(capability_id, str) or not capability_id:
            raise BenchmarkError("every required capability needs a non-empty id")
        if not isinstance(dimension, str) or not dimension:
            raise BenchmarkError(f"capability {capability_id!r} needs a dimension")
        if not isinstance(description, str) or not description:
            raise BenchmarkError(f"capability {capability_id!r} needs a description")
        required.append(capability_id)
    if len(set(required)) != len(required):
        raise BenchmarkError("required_capabilities contains duplicate ids")

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

        if raw.get("gold_state") not in {"pending", "frozen"}:
            raise BenchmarkError(f"case {case_id!r} has invalid gold_state")
        if raw.get("adjudication_state") not in {"not_run", "incomplete", "complete"}:
            raise BenchmarkError(f"case {case_id!r} has invalid adjudication_state")
        evaluator_mode = raw.get("evaluator_mode")
        if not isinstance(evaluator_mode, str) or not evaluator_mode:
            raise BenchmarkError(f"case {case_id!r} needs evaluator_mode")
        for capability_id in covers:
            by_capability[capability_id].append(raw)

    missing = [capability_id for capability_id, rows in by_capability.items() if not rows]
    gold_pending = [
        capability_id
        for capability_id, rows in by_capability.items()
        if rows and not any(row["gold_state"] == "frozen" for row in rows)
    ]
    adjudication_pending = [
        capability_id
        for capability_id, rows in by_capability.items()
        if rows
        and any(row["gold_state"] == "frozen" for row in rows)
        and not any(
            row["gold_state"] == "frozen" and row["adjudication_state"] == "complete"
            for row in rows
        )
    ]
    verified = [
        capability_id
        for capability_id, rows in by_capability.items()
        if any(
            row["gold_state"] == "frozen" and row["adjudication_state"] == "complete"
            for row in rows
        )
    ]
    gate_ready = not (missing or gold_pending or adjudication_pending)
    return {
        "corpus_version": value.get("version"),
        "certification_scope": "declared_capabilities_only",
        "universal_support_claimed": False,
        "required_capabilities": required,
        "case_count": len(cases),
        "represented_capabilities": [
            capability_id for capability_id, rows in by_capability.items() if rows
        ],
        "missing_capabilities": missing,
        "gold_pending_capabilities": gold_pending,
        "adjudication_pending_capabilities": adjudication_pending,
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
    typed_score_parser.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "corpus-status":
            result = evaluate_corpus(args.corpus)
        elif args.command == "prepare":
            result = prepare(args.source, args.output_dir, args.source_label)
        elif args.command == "prepare-table":
            result = prepare_table(args.source, args.output_dir, args.source_label)
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
            )
        else:
            result = score(
                args.source,
                args.units,
                args.coverage,
                args.truth,
                args.candidates,
                args.assessment,
            )
    except BenchmarkError as exc:
        raise SystemExit(f"LECTOR_002_REFERENCE_ERROR: {exc}") from exc

    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if getattr(args, "output", None):
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
