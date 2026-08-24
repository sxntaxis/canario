from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).parents[1] / "notebook" / "implementation" / "lector_002_benchmark.py"
SPEC = importlib.util.spec_from_file_location("lector_002_benchmark", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
bench = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = bench
SPEC.loader.exec_module(bench)


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def test_partition_is_lossless_stable_and_keeps_low_triage_units() -> None:
    source = (
        " 1 ACTA DE PRUEBA\n"
        " 2 ARTÍCULO I\n"
        " 3 1- Se conoce una nota sin decisión.\n"
        " 4 SE ACUERDA: Aprobar la solicitud. APROBADO POR UNANIMIDAD.\n"
        "\f 1 ARTÍCULO II\n"
        " 2 Síndica Ana Ejemplo: Un anuncio vecinal sin verbo de decisión.\n"
        "\f"
    )
    first = bench.partition_source(source)
    second = bench.partition_source(source)

    assert "".join(unit.text for unit in first) == source
    assert first == second
    assert [unit.unit_id for unit in first] == [f"U{i:04d}" for i in range(1, len(first) + 1)]
    assert {unit.kind for unit in first} >= {"session", "article", "item", "agreement", "speaker"}
    assert any(unit.triage_score == 0 for unit in first)
    assert max(unit.page_end for unit in first) == 2


def test_prepare_generates_no_truth_and_is_byte_deterministic(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text(" 1 ARTÍCULO I\n 2 SE ACUERDA: Aprobar X.\n\f", encoding="utf-8")
    first = tmp_path / "a"
    second = tmp_path / "b"

    manifest = bench.prepare(source, first, "fixture")
    bench.prepare(source, second, "fixture")

    assert manifest["truth_generated"] is False
    assert manifest["semantic_model_calls"] == 0
    assert manifest["pages"] == 1
    assert (first / "truth.csv").read_text(encoding="utf-8").count("\n") == 1
    for name in ["manifest.json", "units.csv", "units.jsonl", "coverage.csv", "truth.csv"]:
        assert (first / name).read_bytes() == (second / name).read_bytes()


def test_score_requires_complete_human_coverage(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("material fact", encoding="utf-8")
    units = tmp_path / "units.csv"
    coverage = tmp_path / "coverage.csv"
    truth = tmp_path / "truth.csv"
    candidates = tmp_path / "candidates.csv"
    assessment = tmp_path / "assessment.csv"

    _write_csv(units, ["unit_id"], [{"unit_id": "U0001"}])
    _write_csv(coverage, ["unit_id", "review_state"], [{"unit_id": "U0001", "review_state": ""}])
    _write_csv(
        truth,
        ["truth_id", "unit_id", "importance", "proposition", "evidence_quote", "evidence_start", "evidence_end"],
        [],
    )
    _write_csv(
        candidates,
        ["candidate_id", "proposition", "evidence_quote", "evidence_start", "evidence_end"],
        [],
    )
    _write_csv(assessment, ["candidate_id", "truth_ids", "verdict"], [])

    with pytest.raises(bench.BenchmarkError, match="review_state"):
        bench.score(source, units, coverage, truth, candidates, assessment)


def test_score_validates_evidence_and_computes_only_from_adjudication(tmp_path: Path) -> None:
    source_text = "The council approved X. A request for Y was only discussed."
    source = tmp_path / "source.txt"
    source.write_text(source_text, encoding="utf-8")
    units = tmp_path / "units.csv"
    coverage = tmp_path / "coverage.csv"
    truth = tmp_path / "truth.csv"
    candidates = tmp_path / "candidates.csv"
    assessment = tmp_path / "assessment.csv"

    _write_csv(units, ["unit_id"], [{"unit_id": "U0001"}])
    _write_csv(
        coverage,
        ["unit_id", "review_state"],
        [{"unit_id": "U0001", "review_state": "truth_recorded"}],
    )
    quote1 = "The council approved X."
    quote2 = "A request for Y was only discussed."
    _write_csv(
        truth,
        ["truth_id", "unit_id", "importance", "proposition", "evidence_quote", "evidence_start", "evidence_end"],
        [
            {
                "truth_id": "T001",
                "unit_id": "U0001",
                "importance": "must",
                "proposition": "The council approved X.",
                "evidence_quote": quote1,
                "evidence_start": 0,
                "evidence_end": len(quote1),
            },
            {
                "truth_id": "T002",
                "unit_id": "U0001",
                "importance": "material",
                "proposition": "Y was discussed but not approved.",
                "evidence_quote": quote2,
                "evidence_start": source_text.index(quote2),
                "evidence_end": source_text.index(quote2) + len(quote2),
            },
        ],
    )
    _write_csv(
        candidates,
        ["candidate_id", "proposition", "evidence_quote", "evidence_start", "evidence_end"],
        [
            {
                "candidate_id": "C001",
                "proposition": "The council approved X.",
                "evidence_quote": quote1,
                "evidence_start": 0,
                "evidence_end": len(quote1),
            },
            {
                "candidate_id": "C002",
                "proposition": "Y was approved.",
                "evidence_quote": quote2,
                "evidence_start": source_text.index(quote2),
                "evidence_end": source_text.index(quote2) + len(quote2),
            },
        ],
    )
    _write_csv(
        assessment,
        ["candidate_id", "truth_ids", "verdict"],
        [
            {"candidate_id": "C001", "truth_ids": "T001", "verdict": "correct"},
            {"candidate_id": "C002", "truth_ids": "T002", "verdict": "distorted"},
        ],
    )

    metrics = bench.score(source, units, coverage, truth, candidates, assessment)
    assert metrics["must_recall"] == 1.0
    assert metrics["material_recall"] == 0.0
    assert metrics["relevance_precision"] == 0.5
    assert metrics["distorted_rate"] == 0.5
    assert metrics["semantic_matching_automated"] is False


def test_score_rejects_false_exact_quote(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("abc", encoding="utf-8")
    units = tmp_path / "units.csv"
    coverage = tmp_path / "coverage.csv"
    truth = tmp_path / "truth.csv"
    candidates = tmp_path / "candidates.csv"
    assessment = tmp_path / "assessment.csv"

    _write_csv(units, ["unit_id"], [{"unit_id": "U0001"}])
    _write_csv(coverage, ["unit_id", "review_state"], [{"unit_id": "U0001", "review_state": "truth_recorded"}])
    _write_csv(
        truth,
        ["truth_id", "unit_id", "importance", "proposition", "evidence_quote", "evidence_start", "evidence_end"],
        [{"truth_id": "T001", "unit_id": "U0001", "importance": "must", "proposition": "abc", "evidence_quote": "abd", "evidence_start": 0, "evidence_end": 3}],
    )
    _write_csv(candidates, ["candidate_id", "proposition", "evidence_quote", "evidence_start", "evidence_end"], [])
    _write_csv(assessment, ["candidate_id", "truth_ids", "verdict"], [])

    with pytest.raises(bench.BenchmarkError, match="does not reopen"):
        bench.score(source, units, coverage, truth, candidates, assessment)
