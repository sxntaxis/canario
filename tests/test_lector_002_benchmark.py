from __future__ import annotations

import csv
import importlib.util
import json
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


def test_partition_is_lossless_stable_and_source_format_agnostic() -> None:
    source = (
        "Header\n"
        "First paragraph has ordinary prose.\n"
        "\n"
        "SE ACUERDA is deliberately just text here.\n"
        "ARTÍCULO I is also deliberately just text.\n"
        "\f"
        "Speaker 00:03:12: transcript-like content.\n"
        "More transcript content.\n"
    )
    first = bench.partition_source(source)
    second = bench.partition_source(source)

    assert "".join(unit.text for unit in first) == source
    assert first == second
    assert [unit.unit_id for unit in first] == [f"U{i:04d}" for i in range(1, len(first) + 1)]
    assert {unit.kind for unit in first} <= {"source", "block", "page", "continuation"}
    assert max(unit.page_end or 0 for unit in first) == 2

    # Changing acta-ish vocabulary without changing generic structure cannot
    # change boundaries. The harness has no acta semantics.
    neutral = source.replace("SE ACUERDA", "X" * len("SE ACUERDA")).replace("ARTÍCULO I", "Y" * len("ARTÍCULO I"))
    assert [(u.char_start, u.char_end, u.kind) for u in first] == [
        (u.char_start, u.char_end, u.kind) for u in bench.partition_source(neutral)
    ]


def test_partition_supports_unpaged_transcript_without_fake_page_semantics() -> None:
    source = "00:00 Person A: hello\n00:12 Person B: response\n\n00:40 Person A: conclusion\n"
    units = bench.partition_source(source)
    assert "".join(unit.text for unit in units) == source
    assert all(unit.page_start is None and unit.page_end is None for unit in units)


def test_prepare_generates_no_truth_and_is_byte_deterministic(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("Paragraph one.\n\nParagraph two.\n", encoding="utf-8")
    first = tmp_path / "a"
    second = tmp_path / "b"

    manifest = bench.prepare(source, first, "fixture")
    bench.prepare(source, second, "fixture")

    assert manifest["truth_generated"] is False
    assert manifest["semantic_model_calls"] == 0
    assert manifest["attention_heuristics_used"] is False
    assert manifest["segmentation_semantics"] == "generic_structure_only"
    assert manifest["evaluator_mode"] == "text_quote:v1"
    assert manifest["page_count"] is None
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


def test_corpus_gate_measures_declared_capabilities_not_document_classes() -> None:
    corpus = Path(__file__).parents[1] / "notebook" / "implementation" / "lector_002_corpus.json"
    status = bench.evaluate_corpus(corpus)
    assert status["declared_capability_gate_ready"] is False
    assert status["certification_scope"] == "declared_capabilities_only"
    assert status["universal_support_claimed"] is False
    assert "representation:paged_text" not in status["missing_capabilities"]
    assert "evidence:text_quote:v1" not in status["missing_capabilities"]
    assert status["deterministic_pending_capabilities"] == []
    assert set(status["deterministically_verified_capabilities"]) == {
        "representation:paged_text",
        "representation:structured_table",
        "representation:timed_media",
        "evidence:text_quote:v1",
        "evidence:table_path",
        "evidence:media_time_span",
    }
    assert set(status["gold_pending_capabilities"]) == {
        "semantic:multi_topic_longform",
        "semantic:attribution",
        "semantic:conditions_exceptions_crossrefs",
        "semantic:structured_values",
    }
    assert status["gold_scope_pending_capabilities"] == []
    assert status["semantic_verified_capabilities"] == []
    assert status["semantic_failed_capabilities"] == []
    assert status["missing_capabilities"] == []
    assert "broad_certification_ready" not in status
    assert "required_case_classes" not in status


def test_corpus_archetypes_are_unregistered_descriptive_metadata(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus.json"
    corpus.write_text(
        json.dumps(
            {
                "version": "test:v1",
                "certification_scope": "declared_capabilities_only",
                "universal_support_claimed": False,
                "required_capabilities": [
                    {
                        "id": "evidence:text_quote:v1",
                        "dimension": "evidence",
                        "description": "exact quote reopens",
                        "verification_mode": "deterministic",
                    }
                ],
                "cases": [
                    {
                        "case_id": "WEIRD-001",
                        "benchmark_archetypes": [
                            "citizen_generated_mixed_packet",
                            "genre-that-did-not-exist-yesterday",
                        ],
                        "covers": ["evidence:text_quote:v1"],
                        "evaluator_mode": "text_quote:v1",
                        "deterministic_verification": {"evidence:text_quote:v1": "passed"},
                        "gold_state": "pending",
                        "adjudication_state": "not_run",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    status = bench.evaluate_corpus(corpus)
    assert status["declared_capability_gate_ready"] is True
    assert status["verified_capabilities"] == ["evidence:text_quote:v1"]
    assert status["gold_pending_capabilities"] == []


def test_corpus_deterministic_capability_requires_explicit_mechanical_pass(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus.json"
    corpus.write_text(
        json.dumps(
            {
                "version": "test:v1",
                "certification_scope": "declared_capabilities_only",
                "universal_support_claimed": False,
                "required_capabilities": [
                    {
                        "id": "evidence:text_quote:v1",
                        "dimension": "evidence",
                        "description": "exact quote reopens",
                        "verification_mode": "deterministic",
                    }
                ],
                "cases": [
                    {
                        "case_id": "TEXT-001",
                        "benchmark_archetypes": ["letter"],
                        "covers": ["evidence:text_quote:v1"],
                        "evaluator_mode": "text_quote:v1",
                        "deterministic_verification": {},
                        "gold_state": "frozen",
                        "adjudication_state": "complete",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    status = bench.evaluate_corpus(corpus)
    assert status["declared_capability_gate_ready"] is False
    assert status["deterministic_pending_capabilities"] == ["evidence:text_quote:v1"]
    assert status["gold_pending_capabilities"] == []
    assert status["verified_capabilities"] == []


def test_corpus_semantic_capability_requires_frozen_gold_and_adjudication(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus.json"
    corpus.write_text(
        json.dumps(
            {
                "version": "test:v1",
                "certification_scope": "declared_capabilities_only",
                "universal_support_claimed": False,
                "required_capabilities": [
                    {
                        "id": "semantic:attribution",
                        "dimension": "semantic_stress",
                        "description": "preserve attributable actor",
                        "verification_mode": "semantic_gold",
                    }
                ],
                "cases": [
                    {
                        "case_id": "TEXT-001",
                        "benchmark_archetypes": ["letter"],
                        "covers": ["semantic:attribution"],
                        "evaluator_mode": "text_quote:v1",
                        "deterministic_verification": {},
                        "gold_state": "pending",
                        "adjudication_state": "not_run",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    status = bench.evaluate_corpus(corpus)
    assert status["declared_capability_gate_ready"] is False
    assert status["deterministically_verified_capabilities"] == []
    assert status["gold_pending_capabilities"] == ["semantic:attribution"]
    assert status["verified_capabilities"] == []


def test_corpus_rejects_legacy_document_class_gate(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus.json"
    corpus.write_text(
        json.dumps(
            {
                "version": "legacy",
                "required_case_classes": ["minutes", "report"],
                "cases": [],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(bench.BenchmarkError, match="document-class broad-certification fields are retired"):
        bench.evaluate_corpus(corpus)


def _typed_paths(tmp_path: Path) -> tuple[Path, Path, Path, Path, Path]:
    return tuple(tmp_path / name for name in (
        "units.csv", "coverage.csv", "truth.csv", "candidates.csv", "assessment.csv"
    ))  # type: ignore[return-value]


def test_typed_table_score_reopens_production_selector_and_computes_metrics(tmp_path: Path) -> None:
    source = tmp_path / "table.json"
    source.write_text(
        json.dumps({
            "format": "canario.structured_table.v1",
            "source_sha256": "0" * 64,
            "sheets": [{
                "name": "Sheet1", "ordinal": 1, "state": "visible", "max_row": 1,
                "max_column": 2, "merged_ranges": [],
                "rows": [[
                    {"address": "A1", "value": {"type": "string", "value": "Item"}, "data_type": "s", "number_format": "General"},
                    {"address": "B1", "value": {"type": "integer", "value": 7}, "data_type": "n", "number_format": "General"},
                ]],
            }],
        }, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    worksheet = tmp_path / "worksheet"
    bench.prepare_table(source, worksheet, "table")
    units, coverage, truth, candidates, assessment = (
        worksheet / "units.csv", worksheet / "coverage.csv", worksheet / "truth.csv",
        worksheet / "candidates.csv", worksheet / "assessment.csv",
    )
    _write_csv(coverage, ["unit_id", "review_state", "notes"], [
        {"unit_id": "1:R1", "review_state": "truth_recorded", "notes": ""}
    ])
    selector = json.dumps({
        "sheet": "Sheet1", "a1_range": "A1:B1", "row_start": 1, "row_end": 1,
        "observed_values": [[
            {"type": "string", "value": "Item"}, {"type": "integer", "value": 7}
        ]],
    })
    _write_csv(truth, ["truth_id", "unit_id", "importance", "proposition", "selector_json", "notes"], [
        {"truth_id": "T1", "unit_id": "1:R1", "importance": "must", "proposition": "Item is 7", "selector_json": selector, "notes": ""}
    ])
    _write_csv(candidates, ["candidate_id", "proposition", "selector_json"], [
        {"candidate_id": "C1", "proposition": "Item is 7", "selector_json": selector}
    ])
    _write_csv(assessment, ["candidate_id", "truth_ids", "verdict", "notes"], [
        {"candidate_id": "C1", "truth_ids": "T1", "verdict": "correct", "notes": ""}
    ])
    metrics = bench.score_typed(source, "table_range:v1", units, coverage, truth, candidates, assessment)
    assert metrics["must_recall"] == 1.0
    assert metrics["relevance_precision"] == 1.0
    assert metrics["evaluator_mode"] == "table_range:v1"


def test_media_prepare_and_score_require_trusted_index(tmp_path: Path) -> None:
    source = tmp_path / "source.mp4"
    source.write_bytes(b"controlled-media")
    digest = bench._sha256_bytes(source.read_bytes())
    index = tmp_path / "media-index.json"
    index.write_bytes(json.dumps({
        "format": "canario.media_index.v1", "source_sha256": digest,
        "duration_us": 2_000_000, "probe": {"format": {"duration": "2.000000"}},
    }, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    worksheet = tmp_path / "worksheet"
    manifest = bench.prepare_media(source, index, worksheet, "media")
    assert manifest["duration_us"] == 2_000_000
    units, coverage, truth, candidates, assessment = (
        worksheet / "units.csv", worksheet / "coverage.csv", worksheet / "truth.csv",
        worksheet / "candidates.csv", worksheet / "assessment.csv",
    )
    _write_csv(coverage, ["unit_id", "review_state", "notes"], [
        {"unit_id": "T0001", "review_state": "truth_recorded", "notes": ""}
    ])
    selector = json.dumps({
        "media_sha256": digest, "duration_us": 2_000_000,
        "start_us": 250_000, "end_us": 750_000,
    })
    _write_csv(truth, ["truth_id", "unit_id", "importance", "proposition", "selector_json", "notes"], [
        {"truth_id": "T1", "unit_id": "T0001", "importance": "must", "proposition": "spoken fact", "selector_json": selector, "notes": ""}
    ])
    _write_csv(candidates, ["candidate_id", "proposition", "selector_json"], [
        {"candidate_id": "C1", "proposition": "spoken fact", "selector_json": selector}
    ])
    _write_csv(assessment, ["candidate_id", "truth_ids", "verdict", "notes"], [
        {"candidate_id": "C1", "truth_ids": "T1", "verdict": "correct", "notes": ""}
    ])
    metrics = bench.score_typed(
        source, "media:v1", units, coverage, truth, candidates, assessment,
        media_index_path=index,
    )
    assert metrics["must_recall"] == 1.0
    assert metrics["evaluator_mode"] == "media:v1"

    bad_index = tmp_path / "bad-index.json"
    bad_index.write_bytes(json.dumps({
        "format": "canario.media_index.v1", "source_sha256": "f" * 64,
        "duration_us": 2_000_000, "probe": {"format": {"duration": "2.000000"}},
    }, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    with pytest.raises(bench.BenchmarkError, match="does not describe"):
        bench.prepare_media(source, bad_index, tmp_path / "bad", "media")

    bad_duration_index = tmp_path / "bad-duration-index.json"
    bad_duration_index.write_bytes(json.dumps({
        "format": "canario.media_index.v1", "source_sha256": digest,
        "duration_us": 3_000_000, "probe": {"format": {"duration": "2.000000"}},
    }, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    with pytest.raises(bench.BenchmarkError, match="duration_us disagrees"):
        bench.prepare_media(source, bad_duration_index, tmp_path / "bad-duration", "media")

    wrong_duration = selector.replace("2000000", "3000000")
    _write_csv(truth, ["truth_id", "unit_id", "importance", "proposition", "selector_json", "notes"], [
        {"truth_id": "T1", "unit_id": "T0001", "importance": "must", "proposition": "spoken fact", "selector_json": wrong_duration, "notes": ""}
    ])
    with pytest.raises(bench.BenchmarkError, match="untrusted duration"):
        bench.score_typed(
            source, "media:v1", units, coverage, truth, candidates, assessment,
            media_index_path=index,
        )


def _semantic_corpus(tmp_path: Path, *, state: str, result_sha256: str | None, covered: bool = True) -> Path:
    capability = "semantic:attribution"
    case = {
        "case_id": "TEXT-001",
        "benchmark_archetypes": ["letter"],
        "covers": [capability] if covered else ["evidence:text_quote:v1"],
        "scope_capabilities": [],
        "evaluator_mode": "text_quote:v1",
        "gold_scope_state": "frozen",
        "gold_state": "frozen",
        "adjudication_state": "complete",
        "semantic_verification": {capability: {"state": state, "result_sha256": result_sha256}},
        "deterministic_verification": {},
    }
    value = {
        "version": "test:v5",
        "certification_scope": "declared_capabilities_only",
        "universal_support_claimed": False,
        "threshold_policy_state": "frozen",
        "required_capabilities": ([{
            "id": capability,
            "dimension": "semantic_stress",
            "description": "attribution",
            "verification_mode": "semantic_gold",
        }] if covered else [
            {"id": capability, "dimension": "semantic_stress", "description": "attribution", "verification_mode": "semantic_gold"},
            {"id": "evidence:text_quote:v1", "dimension": "evidence", "description": "quote", "verification_mode": "deterministic"},
        ]),
        "cases": [case],
    }
    path = tmp_path / f"{state}-{covered}.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_semantic_not_run_and_failed_are_not_verified(tmp_path: Path) -> None:
    pending = bench.evaluate_corpus(_semantic_corpus(tmp_path, state="not_run", result_sha256=None))
    assert pending["semantic_verified_capabilities"] == []
    assert pending["evaluation_pending_capabilities"] == ["semantic:attribution"]
    failed = bench.evaluate_corpus(_semantic_corpus(tmp_path, state="failed", result_sha256="a" * 64))
    assert failed["semantic_failed_capabilities"] == ["semantic:attribution"]
    assert failed["semantic_verified_capabilities"] == []
    passed = bench.evaluate_corpus(_semantic_corpus(tmp_path, state="passed", result_sha256="b" * 64))
    assert passed["semantic_verified_capabilities"] == ["semantic:attribution"]


def test_semantic_result_digest_is_required_and_case_must_cover_capability(tmp_path: Path) -> None:
    with pytest.raises(bench.BenchmarkError, match="requires result_sha256"):
        bench.evaluate_corpus(_semantic_corpus(tmp_path, state="passed", result_sha256=None))
    with pytest.raises(bench.BenchmarkError, match="verifies semantic capability it does not cover"):
        bench.evaluate_corpus(_semantic_corpus(tmp_path, state="not_run", result_sha256=None, covered=False))


def _scoped_text_files(tmp_path: Path, *, selected: list[str] = ["U1"], capabilities: list[str] = ["semantic:attribution"]):
    source = tmp_path / "source.txt"
    source.write_text("A proposition.\nB context.", encoding="utf-8")
    units = tmp_path / "units.csv"
    _write_csv(units, ["unit_id"], [{"unit_id": item} for item in ["U1", "U2"]])
    scope = tmp_path / "gold_scope.json"
    bench.write_gold_scope(scope, bench.create_gold_scope(
        case_id="TEXT-001",
        source_sha256=bench._sha256_bytes(source.read_bytes()),
        units_sha256=bench._unit_file_sha256(units),
        unit_ids=selected,
        selection_kind="full_source_order",
        selection_policy="test",
        semantic_capabilities=capabilities,
    ))
    coverage = tmp_path / "coverage.csv"
    _write_csv(coverage, ["unit_id", "review_state"], [
        {"unit_id": "U1", "review_state": "truth_recorded"},
        {"unit_id": "U2", "review_state": "unjudged"},
    ])
    truth = tmp_path / "truth.csv"
    _write_csv(truth, ["truth_id", "unit_id", "importance", "proposition", "evidence_quote", "evidence_start", "evidence_end", "capability_ids"], [{
        "truth_id": "T1", "unit_id": "U1", "importance": "must", "proposition": "A proposition.",
        "evidence_quote": "A proposition.", "evidence_start": 0, "evidence_end": 14,
        "capability_ids": "semantic:attribution",
    }])
    candidates = tmp_path / "candidates.csv"
    _write_csv(candidates, ["candidate_id", "proposition", "evidence_quote", "evidence_start", "evidence_end"], [])
    assessment = tmp_path / "assessment.csv"
    _write_csv(assessment, ["candidate_id", "truth_ids", "verdict"], [])
    return source, units, scope, coverage, truth, candidates, assessment


def test_truth_capability_binding_and_scope_metrics(tmp_path: Path) -> None:
    source, units, scope, coverage, truth, candidates, assessment = _scoped_text_files(tmp_path)
    metrics = bench.score(source, units, coverage, truth, candidates, assessment, scope_path=scope)
    assert metrics["semantic_metrics"]["semantic:attribution"]["truths"] == 1
    assert metrics["semantic_metrics"]["semantic:attribution"]["must_recall"] == 0.0
    assert metrics["scope"]["selected_units"] == 1
    assert metrics["scope"]["full_source_recall_claimed"] is True

    rows = _read = []
    _write_csv(truth, ["truth_id", "unit_id", "importance", "proposition", "evidence_quote", "evidence_start", "evidence_end", "capability_ids"], [{
        "truth_id": "T1", "unit_id": "U1", "importance": "must", "proposition": "A proposition.",
        "evidence_quote": "A proposition.", "evidence_start": 0, "evidence_end": 14,
        "capability_ids": "semantic:attribution;semantic:attribution",
    }])
    with pytest.raises(bench.BenchmarkError, match="duplicate capability_ids"):
        bench.score(source, units, coverage, truth, candidates, assessment, scope_path=scope)


def test_scope_rejects_truth_outside_and_noncanonical_binding(tmp_path: Path) -> None:
    source, units, scope, coverage, truth, candidates, assessment = _scoped_text_files(tmp_path)
    _write_csv(truth, ["truth_id", "unit_id", "importance", "proposition", "evidence_quote", "evidence_start", "evidence_end", "capability_ids"], [{
        "truth_id": "T2", "unit_id": "U2", "importance": "must", "proposition": "B context.",
        "evidence_quote": "B context.", "evidence_start": 15, "evidence_end": 25,
        "capability_ids": "semantic:attribution",
    }])
    with pytest.raises(bench.BenchmarkError, match="outside the frozen gold scope"):
        bench.score(source, units, coverage, truth, candidates, assessment, scope_path=scope)


def test_truth_binding_rejects_deterministic_and_noncanonical_ids_and_allows_multiple() -> None:
    semantic = {"semantic:attribution", "semantic:multi_topic_longform"}
    assert bench._parse_capability_ids(
        "semantic:attribution;semantic:multi_topic_longform",
        semantic_capabilities=semantic,
        label="truth T1",
    ) == ["semantic:attribution", "semantic:multi_topic_longform"]
    with pytest.raises(bench.BenchmarkError, match="sorted"):
        bench._parse_capability_ids(
            "semantic:multi_topic_longform;semantic:attribution",
            semantic_capabilities=semantic,
            label="truth T1",
        )
    with pytest.raises(bench.BenchmarkError, match="non-semantic"):
        bench._parse_capability_ids(
            "evidence:text_quote:v1",
            semantic_capabilities=semantic,
            label="truth T1",
        )


def test_scope_identity_change_and_selected_coverage_are_rejected(tmp_path: Path) -> None:
    source, units, scope, coverage, truth, candidates, assessment = _scoped_text_files(tmp_path)
    source.write_text("changed", encoding="utf-8")
    with pytest.raises(bench.BenchmarkError, match="source identity"):
        bench.score(source, units, coverage, truth, candidates, assessment, scope_path=scope)

    source.write_text("A proposition.\nB context.", encoding="utf-8")
    _write_csv(coverage, ["unit_id", "review_state"], [
        {"unit_id": "U1", "review_state": "truth_recorded"},
        {"unit_id": "U2", "review_state": "no_material_truth"},
    ])
    with pytest.raises(bench.BenchmarkError, match="unselected unit"):
        bench.score(source, units, coverage, truth, candidates, assessment, scope_path=scope)


def test_freeze_gold_rejects_empty_semantic_gold(tmp_path: Path) -> None:
    source, units, scope, coverage, truth, candidates, assessment = _scoped_text_files(tmp_path)
    _write_csv(truth, ["truth_id", "unit_id", "importance", "proposition", "evidence_quote", "evidence_start", "evidence_end", "capability_ids"], [])
    _write_csv(coverage, ["unit_id", "review_state"], [
        {"unit_id": "U1", "review_state": "no_material_truth"},
        {"unit_id": "U2", "review_state": "unjudged"},
    ])
    with pytest.raises(bench.BenchmarkError, match="empty semantic-capability gold"):
        bench.freeze_gold(
            case_id="TEXT-001", source_path=source, units_path=units, coverage_path=coverage,
            truth_path=truth, candidates_path=candidates, assessment_path=assessment,
            scope_path=scope, output_path=tmp_path / "gold-manifest.json",
        )


def test_structural_sample_is_stable_for_same_structure() -> None:
    units = [
        {"unit_id": "1:R1", "sheet": "s", "value_type_signature": "string", "formula_present": "false", "merged_structure_intersection": "false"},
        {"unit_id": "1:R2", "sheet": "s", "value_type_signature": "integer", "formula_present": "false", "merged_structure_intersection": "false"},
        {"unit_id": "2:R1", "sheet": "t", "value_type_signature": "number", "formula_present": "true", "merged_structure_intersection": "false"},
    ] * 12
    first = bench.select_structural_table_units(units, "a" * 64)
    second = bench.select_structural_table_units([{**row} for row in units], "a" * 64)
    assert first == second
    assert {item.split(":")[0] for item in first} == {"1", "2"}


def test_needs_adjudication_is_explicit_and_blocks_scoring(tmp_path: Path) -> None:
    source, units, scope, coverage, truth, candidates, assessment = _scoped_text_files(tmp_path)
    _write_csv(coverage, ["unit_id", "review_state"], [
        {"unit_id": "U1", "review_state": "needs_adjudication"},
        {"unit_id": "U2", "review_state": "unjudged"},
    ])
    with pytest.raises(bench.BenchmarkError, match="needs human gold adjudication"):
        bench.score(source, units, coverage, truth, candidates, assessment, scope_path=scope)


def test_review_status_reports_uncertainty_without_semantic_interpretation(tmp_path: Path) -> None:
    source, units, scope, coverage, truth, candidates, assessment = _scoped_text_files(tmp_path)
    _write_csv(coverage, ["unit_id", "review_state"], [
        {"unit_id": "U1", "review_state": "needs_adjudication"},
        {"unit_id": "U2", "review_state": "unjudged"},
    ])
    status = bench.review_status(
        source_path=source,
        units_path=units,
        coverage_path=coverage,
        scope_path=scope,
    )
    assert status["selected_units"] == 1
    assert status["resolved_units"] == 0
    assert status["needs_adjudication_units"] == 1
    assert status["pending_blank_units"] == 0
    assert status["review_complete_for_gold_freeze"] is False
    assert status["semantic_interpretation_performed"] is False


def test_review_status_counts_blank_selected_units_as_pending(tmp_path: Path) -> None:
    source, units, scope, coverage, truth, candidates, assessment = _scoped_text_files(tmp_path)
    _write_csv(coverage, ["unit_id", "review_state"], [
        {"unit_id": "U1", "review_state": ""},
        {"unit_id": "U2", "review_state": "unjudged"},
    ])
    status = bench.review_status(
        source_path=source,
        units_path=units,
        coverage_path=coverage,
        scope_path=scope,
    )
    assert status["pending_blank_units"] == 1
    assert status["needs_adjudication_units"] == 0
    assert status["review_complete_for_gold_freeze"] is False
