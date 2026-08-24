#!/usr/bin/env python3
"""Deterministic preparation and scoring harness for the LECTOR-002 civic benchmark.

This module deliberately does *not* decide semantic truth. ``prepare`` partitions an
exact UTF-8 source representation into stable review units and adds mechanical
triage cues only. Humans remain responsible for the gold propositions and for
candidate-to-truth adjudication. ``score`` validates exact evidence reopening and
then computes metrics from those explicit judgments.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

PREPARATION_VERSION = "lector-002-benchmark:v1"
MAX_UNIT_CHARS = 5_000
PREFERRED_SPLIT_CHARS = 3_500

ARTICLE_RE = re.compile(r"^ART[IÍ]CULO\s+([IVXLC]+)\s*$", re.IGNORECASE)
ITEM_RE = re.compile(r"^(\d+)-\s+")
AGREEMENT_RE = re.compile(r"^SE ACUERDA(?:\b|\s*:)|^Se acuerda(?:\b|\s*:)", re.IGNORECASE)
SPEAKER_RE = re.compile(
    r"^(?:Sr\.?|Sra\.?|Señor(?:a)?|Regidor(?:a)?(?:\s+suplente)?|"
    r"Síndic[oa]|Lic\.?|MSc\.?|Prof\.?|Alcalde|Vicealcald[ea]|"
    r"Presidente\s+Municipal)\b[^:\n]{0,120}:",
    re.IGNORECASE,
)
SESSION_CLOSE_RE = re.compile(
    r"^A las .{0,100}\b(?:da por finalizada|finaliza)\b", re.IGNORECASE
)
PRINTED_LINE_NUMBER_RE = re.compile(r"^\s*\d+\s+")
WHITESPACE_RE = re.compile(r"\s+")

# These signals prioritize review; they are not confidence, truth, or acceptance.
TRIAGE_CUES: tuple[tuple[str, re.Pattern[str], int], ...] = (
    (
        "decision",
        re.compile(r"\bSE ACUERDA\b|ACUERDO DEFINITIVAMENTE|\bAPROBAD[OA]\b", re.IGNORECASE),
        5,
    ),
    (
        "vote",
        re.compile(r"\bvotaci[oó]n\b|\bunanimidad\b|\ben firme\b", re.IGNORECASE),
        3,
    ),
    (
        "action",
        re.compile(
            r"\b(?:aprobar|autorizar|trasladar|solicitar|rechazar|designar|nombrar|"
            r"aceptar|modificar|mantener|notificar|instruir)\w*\b",
            re.IGNORECASE,
        ),
        3,
    ),
    (
        "money",
        re.compile(
            r"(?:[¢₡]\s*[\d.]|\bcolones\b|\bpresupuesto\b|\bcanon\b|\bmonto\b|"
            r"transferencia de recursos)",
            re.IGNORECASE,
        ),
        3,
    ),
    (
        "deadline",
        re.compile(
            r"\b(?:plazo|d[ií]as h[aá]biles|fecha l[ií]mite|vencimiento)\b",
            re.IGNORECASE,
        ),
        2,
    ),
    (
        "legal",
        re.compile(
            r"\b(?:ley|reglamento|convenio|contrato|adenda|licitaci[oó]n|recurso|"
            r"contralor[ií]a)\b",
            re.IGNORECASE,
        ),
        2,
    ),
    ("correspondence", re.compile(r"\b(?:oficio|nota)\b", re.IGNORECASE), 1),
    ("request", re.compile(r"\b(?:solicita|solicitud|pide|requiere)\b", re.IGNORECASE), 1),
)

TRUTH_IMPORTANCE = {"must", "material"}
ASSESSMENT_VERDICTS = {"correct", "distorted", "unsupported", "redundant", "overmerged"}
COVERAGE_STATES = {"truth_recorded", "no_material_truth"}


class BenchmarkError(ValueError):
    """Benchmark input is malformed or violates an auditable invariant."""


@dataclass(frozen=True)
class LineRecord:
    start_char: int
    end_char: int
    page: int
    clean: str


@dataclass(frozen=True)
class ReviewUnit:
    unit_id: str
    kind: str
    page_start: int
    page_end: int
    char_start: int
    char_end: int
    article: str
    item: str
    triage_score: int
    cues: tuple[str, ...]
    preview: str
    text: str


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _clean_line(raw: str) -> str:
    visible = raw.replace("\f", "").rstrip("\r\n")
    return PRINTED_LINE_NUMBER_RE.sub("", visible).strip()


def _line_records(text: str) -> list[LineRecord]:
    records: list[LineRecord] = []
    page = 1
    position = 0
    for raw in text.splitlines(keepends=True):
        end = position + len(raw)
        records.append(LineRecord(position, end, page, _clean_line(raw)))
        # pdftotext emits form-feed *after* the page it terminates. Advance only
        # after recording that exact delimiter so a trailing form-feed does not
        # invent an empty next page.
        page += raw.count("\f")
        position = end
    if position < len(text):
        raw = text[position:]
        records.append(LineRecord(position, len(text), page, _clean_line(raw)))
    if not records:
        records.append(LineRecord(0, 0, 1, ""))
    return records


def _marker_kind(clean: str) -> str | None:
    if ARTICLE_RE.match(clean):
        return "article"
    if ITEM_RE.match(clean):
        return "item"
    if AGREEMENT_RE.match(clean):
        return "agreement"
    if SPEAKER_RE.match(clean):
        return "speaker"
    if SESSION_CLOSE_RE.match(clean):
        return "session_close"
    return None


def _page_at(records: Sequence[LineRecord], starts: Sequence[int], offset: int) -> int:
    if not records:
        return 1
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


def _triage(text: str) -> tuple[int, tuple[str, ...]]:
    hits: list[str] = []
    score = 0
    for name, pattern, weight in TRIAGE_CUES:
        if pattern.search(text):
            hits.append(name)
            score += weight
    return score, tuple(hits)


def partition_source(text: str) -> list[ReviewUnit]:
    """Partition the complete source without dropping or rewriting any character."""

    records = _line_records(text)
    line_starts = [record.start_char for record in records]
    markers: dict[int, str] = {0: "session"}
    boundaries = [0]
    for record in records:
        kind = _marker_kind(record.clean)
        if kind is not None and record.start_char != 0:
            boundaries.append(record.start_char)
            markers[record.start_char] = kind
    boundaries = _split_oversized_units(boundaries, line_starts, len(text), markers)

    starts = [record.start_char for record in records]
    units: list[ReviewUnit] = []
    article = ""
    item = ""
    for ordinal, (start, end) in enumerate(zip(boundaries, boundaries[1:]), start=1):
        segment = text[start:end]
        clean_lines = [_clean_line(line) for line in segment.splitlines()]
        lead = next((line for line in clean_lines if line), "")
        article_match = ARTICLE_RE.match(lead)
        if article_match:
            article = article_match.group(1).upper()
            item = ""
        item_match = ITEM_RE.match(lead)
        if item_match:
            item = item_match.group(1)

        score, cues = _triage(segment)
        preview = WHITESPACE_RE.sub(" ", segment).strip()[:280]
        page_end_offset = max(start, end - 1)
        units.append(
            ReviewUnit(
                unit_id=f"U{ordinal:04d}",
                kind=markers.get(start, "continuation"),
                page_start=_page_at(records, starts, start),
                page_end=_page_at(records, starts, page_end_offset),
                char_start=start,
                char_end=end,
                article=article,
                item=item,
                triage_score=score,
                cues=cues,
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
    source_bytes = source_path.read_bytes()
    try:
        text = source_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BenchmarkError("LECTOR-002 reference source must be exact UTF-8 text") from exc

    units = partition_source(text)
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "preparation_version": PREPARATION_VERSION,
        "source_label": source_label or source_path.name,
        "source_sha256": _sha256_bytes(source_bytes),
        "source_bytes": len(source_bytes),
        "source_characters": len(text),
        "pages": text.count("\f") + (0 if text.endswith("\f") else 1),
        "review_units": len(units),
        "truth_generated": False,
        "semantic_model_calls": 0,
        "triage_is_semantic_authority": False,
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
        "article",
        "item",
        "triage_score",
        "cues",
        "preview",
    ]
    _write_csv(
        output_dir / "units.csv",
        unit_fields,
        (
            {
                **{key: getattr(unit, key) for key in unit_fields if key not in {"cues"}},
                "cues": ";".join(unit.cues),
            }
            for unit in units
        ),
    )
    with (output_dir / "units.jsonl").open("w", encoding="utf-8") as handle:
        for unit in units:
            value = asdict(unit)
            value["cues"] = list(unit.cues)
            handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")

    _write_csv(
        output_dir / "coverage.csv",
        ["unit_id", "triage_score", "review_state", "notes"],
        (
            {
                "unit_id": unit.unit_id,
                "triage_score": unit.triage_score,
                "review_state": "",
                "notes": "",
            }
            for unit in sorted(units, key=lambda value: (-value.triage_score, value.unit_id))
        ),
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
        [
            "candidate_id",
            "proposition",
            "evidence_quote",
            "evidence_start",
            "evidence_end",
        ],
        (),
    )
    _write_csv(
        output_dir / "assessment.csv",
        ["candidate_id", "truth_ids", "verdict", "notes"],
        (),
    )
    (output_dir / "README.md").write_text(
        "# LECTOR-002 Acta benchmark worksheet\n\n"
        "`units.csv` orders exact source units for review. `triage_score` is only a mechanical\n"
        "attention aid; it is not confidence and never creates truth. `units.jsonl` contains the\n"
        "lossless exact unit text and character offsets.\n\n"
        "For every unit, a human eventually records either `truth_recorded` or\n"
        "`no_material_truth` in `coverage.csv`. Each material proposition is added to\n"
        "`truth.csv` with `importance` = `must` or `material` and an exact source quote whose\n"
        "character offsets reopen against the frozen source. Multiple truths may point to one\n"
        "unit.\n\n"
        "Only after the gold set is complete should an extractor fill `candidates.csv`. Human\n"
        "adjudication then maps each candidate in `assessment.csv` to truth IDs with one of:\n"
        "`correct`, `distorted`, `unsupported`, `redundant`, `overmerged`. The scorer validates\n"
        "evidence and computes metrics; it does not decide semantic equivalence.\n",
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


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

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
        if args.command == "prepare":
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
        raise SystemExit(f"LECTOR_002_BENCHMARK_ERROR: {exc}") from exc

    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if getattr(args, "output", None):
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
