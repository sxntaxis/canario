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

PREPARATION_VERSION = "lector-002-reference-text:v2"
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
        _validate_exact_evidence(text, row, f"truth {truth_id!r}")
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
        _validate_exact_evidence(text, row, f"candidate {candidate_id!r}")

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
    metrics: dict[str, object] = {
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
    return metrics


def evaluate_corpus(corpus_path: Path) -> dict[str, object]:
    """Derive the broad-certification gate from a heterogeneous corpus manifest."""

    try:
        value = json.loads(corpus_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BenchmarkError("corpus manifest is not readable valid JSON") from exc
    if not isinstance(value, dict):
        raise BenchmarkError("corpus manifest must be an object")

    required = value.get("required_case_classes")
    cases = value.get("cases")
    if not isinstance(required, list) or not required or not all(
        isinstance(item, str) and item for item in required
    ):
        raise BenchmarkError("required_case_classes must be a non-empty string list")
    if len(set(required)) != len(required):
        raise BenchmarkError("required_case_classes contains duplicates")
    if not isinstance(cases, list):
        raise BenchmarkError("cases must be a list")

    seen_ids: set[str] = set()
    by_class: dict[str, list[dict[str, object]]] = {case_class: [] for case_class in required}
    for raw in cases:
        if not isinstance(raw, dict):
            raise BenchmarkError("every corpus case must be an object")
        case_id = raw.get("case_id")
        case_class = raw.get("case_class")
        if not isinstance(case_id, str) or not case_id:
            raise BenchmarkError("every corpus case needs a non-empty case_id")
        if case_id in seen_ids:
            raise BenchmarkError(f"duplicate corpus case_id {case_id!r}")
        seen_ids.add(case_id)
        if case_class not in by_class:
            raise BenchmarkError(f"case {case_id!r} uses unregistered class {case_class!r}")
        if raw.get("gold_state") not in {"pending", "frozen"}:
            raise BenchmarkError(f"case {case_id!r} has invalid gold_state")
        if raw.get("adjudication_state") not in {"not_run", "incomplete", "complete"}:
            raise BenchmarkError(f"case {case_id!r} has invalid adjudication_state")
        evaluator_mode = raw.get("evaluator_mode")
        if not isinstance(evaluator_mode, str) or not evaluator_mode:
            raise BenchmarkError(f"case {case_id!r} needs evaluator_mode")
        by_class[case_class].append(raw)

    missing_classes = [case_class for case_class, rows in by_class.items() if not rows]
    gold_pending_classes = [
        case_class
        for case_class, rows in by_class.items()
        if rows and not any(row["gold_state"] == "frozen" for row in rows)
    ]
    adjudication_pending_classes = [
        case_class
        for case_class, rows in by_class.items()
        if rows
        and any(row["gold_state"] == "frozen" for row in rows)
        and not any(
            row["gold_state"] == "frozen" and row["adjudication_state"] == "complete"
            for row in rows
        )
    ]
    broad_ready = not (missing_classes or gold_pending_classes or adjudication_pending_classes)
    return {
        "corpus_version": value.get("version"),
        "required_case_classes": required,
        "case_count": len(cases),
        "missing_case_classes": missing_classes,
        "gold_pending_classes": gold_pending_classes,
        "adjudication_pending_classes": adjudication_pending_classes,
        "broad_certification_ready": broad_ready,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    corpus_parser = subparsers.add_parser("corpus-status", help="derive the heterogeneous broad-certification gate")
    corpus_parser.add_argument("--corpus", type=Path, required=True)

    prepare_parser = subparsers.add_parser("prepare", help="create a deterministic review worksheet")
    prepare_parser.add_argument("--source", type=Path, required=True)
    prepare_parser.add_argument("--output-dir", type=Path, required=True)
    prepare_parser.add_argument("--source-label")

    score_parser = subparsers.add_parser("score", help="validate a completed gold/adjudication set and score it")
    score_parser.add_argument("--source", type=Path, required=True)
    score_parser.add_argument("--units", type=Path, required=True)
    score_parser.add_argument("--coverage", type=Path, required=True)
    score_parser.add_argument("--truth", type=Path, required=True)
    score_parser.add_argument("--candidates", type=Path, required=True)
    score_parser.add_argument("--assessment", type=Path, required=True)
    score_parser.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "corpus-status":
            result = evaluate_corpus(args.corpus)
        elif args.command == "prepare":
            result = prepare(args.source, args.output_dir, args.source_label)
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
