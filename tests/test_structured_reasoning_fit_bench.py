from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
from decimal import Decimal
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).parents[1] / "notebook" / "implementation" / "structured_reasoning_fit_bench.py"
SPEC = importlib.util.spec_from_file_location("structured_reasoning_fit_bench", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
bench = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = bench
SPEC.loader.exec_module(bench)


def _structured_source() -> bytes:
    value = {
        "format": "canario.structured_table.v1",
        "source_sha256": "a" * 64,
        "sheets": [
            {
                "name": "Alpha",
                "ordinal": 1,
                "state": "visible",
                "max_row": 3,
                "max_column": 4,
                "merged_ranges": ["A1:B1"],
                "rows": [
                    [
                        {"address": "A1", "value": {"type": "string", "value": "code"}, "data_type": "s", "number_format": "General"},
                        {"address": "B1", "value": {"type": "string", "value": "label"}, "data_type": "s", "number_format": "General"},
                        {"address": "C1", "value": {"type": "string", "value": "value"}, "data_type": "s", "number_format": "General"},
                        {"address": "D1", "value": None, "data_type": "n", "number_format": "General"},
                    ],
                    [
                        {"address": "A2", "value": {"type": "string", "value": "x"}, "data_type": "s", "number_format": "General"},
                        {"address": "B2", "value": {"type": "boolean", "value": True}, "data_type": "b", "number_format": "General"},
                        {"address": "C2", "value": {"type": "number", "value": 12.5}, "data_type": "n", "number_format": "0.00"},
                        {"address": "D2", "value": {"type": "datetime", "value": "2026-08-26T00:00:00"}, "data_type": "d", "number_format": "yyyy-mm-dd"},
                    ],
                    [
                        {"address": "A3", "value": {"type": "string", "value": "y"}, "data_type": "s", "number_format": "General"},
                        {"address": "B3", "value": {"type": "integer", "value": 7}, "data_type": "n", "number_format": "0"},
                        {"address": "C3", "value": {"type": "formula", "value": "=B3*2"}, "data_type": "f", "number_format": "0"},
                        {"address": "D3", "value": {"type": "error", "value": "#DIV/0!"}, "data_type": "e", "number_format": "General"},
                    ],
                ],
            },
            {
                "name": "Beta",
                "ordinal": 2,
                "state": "visible",
                "max_row": 2,
                "max_column": 2,
                "merged_ranges": [],
                "rows": [
                    [
                        {"address": "A1", "value": {"type": "string", "value": "x"}, "data_type": "s", "number_format": "General"},
                        {"address": "B1", "value": {"type": "integer", "value": 2}, "data_type": "n", "number_format": "0"},
                    ],
                    [
                        {"address": "A2", "value": {"type": "string", "value": "z"}, "data_type": "s", "number_format": "General"},
                        {"address": "B2", "value": {"type": "integer", "value": 3}, "data_type": "n", "number_format": "0"},
                    ],
                ],
            },
        ],
    }
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def test_projection_is_deterministic_and_preserves_all_scalar_lineage() -> None:
    source = _structured_source()
    first, manifest_a = bench.build_projection(source)
    second, manifest_b = bench.build_projection(source)
    assert first == second
    assert manifest_a == manifest_b
    assert manifest_a["source_representation_sha256"] == bench._sha256_bytes(source)
    assert manifest_a["sheet_count"] == 2
    assert manifest_a["row_count"] == 5
    assert manifest_a["cell_count"] == 16
    assert manifest_a["formula_count"] == 1
    projection = bench.load_projection(first)
    assert [sheet["name"] for sheet in projection["sheets"]] == ["Alpha", "Beta"]
    cells = {cell["address"] + f"@{cell['sheet_ordinal']}": cell for cell in projection["cells"]}
    assert cells["A1@1"]["value"] == {"kind": "string", "text": "code"}
    assert cells["B2@1"]["value"] == {"kind": "boolean", "value": True}
    assert cells["C2@1"]["value"] == {"kind": "number", "decimal": "12.5"}
    assert cells["B3@1"]["value"] == {"kind": "integer", "decimal": "7"}
    assert cells["C3@1"]["value"] == {"kind": "formula", "text": "=B3*2"}
    assert cells["D2@1"]["value"] == {"kind": "datetime", "text": "2026-08-26T00:00:00"}
    assert cells["D3@1"]["value"] == {"kind": "error", "text": "#DIV/0!"}
    assert cells["D1@1"]["value"] == {"kind": "blank"}
    assert cells["C2@1"]["number_format"] == "0.00"
    assert projection["sheets"][0]["merged_ranges"] == ["A1:B1"]


def test_projection_rejects_wrong_format_and_expected_digest_drift(tmp_path: Path) -> None:
    with pytest.raises(bench.FitBenchError, match="source must be"):
        bench.build_projection(b'{"format":"other"}')
    projection, _ = bench.build_projection(_structured_source())
    with pytest.raises(bench.FitBenchError, match="projection SHA-256 mismatch"):
        bench.load_projection(projection, expected_sha256="f" * 64)
    source = tmp_path / "source.json"
    source.write_bytes(_structured_source())
    with pytest.raises(bench.FitBenchError, match="source Representation SHA-256 mismatch"):
        bench.main(
            [
                "project-table",
                "--source",
                str(source),
                "--output",
                str(tmp_path / "projection.json"),
                "--manifest",
                str(tmp_path / "manifest.json"),
                "--expected-source-sha256",
                "f" * 64,
            ]
        )


def test_projection_digest_changes_when_source_changes() -> None:
    source = _structured_source()
    first, _ = bench.build_projection(source)
    value = json.loads(source)
    value["sheets"][0]["rows"][1][2]["value"]["value"] = 12.75
    changed = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    second, _ = bench.build_projection(changed)
    assert bench._sha256_bytes(first) != bench._sha256_bytes(second)


def test_sqlite_executor_allows_bounded_select_and_preserves_result_types() -> None:
    projection, _ = bench.build_projection(_structured_source())
    result = bench.execute_sqlite(
        projection,
        "SELECT row_index,c1_text,c3_number FROM sheet_1_rows WHERE row_index=2",
    )
    assert result["engine"] == "sqlite"
    assert result["columns"] == ["row_index", "c1_text", "c3_number"]
    assert result["rows"][0][0] == {"type": "integer", "value": "2"}
    assert result["rows"][0][1] == {"type": "string", "value": "x"}
    assert result["rows"][0][2]["type"] == "number"
    assert result["security"]["canonical_database_opened"] is False


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO sheet_1_rows(row_index) VALUES(99)",
        "UPDATE sheet_1_rows SET c1_text='bad' WHERE row_index=2",
        "DELETE FROM sheet_1_rows",
        "CREATE TABLE pwned(x)",
        "DROP TABLE sheet_1_rows",
        "ATTACH DATABASE '/tmp/pwn.db' AS pwn",
        "DETACH DATABASE main",
        "PRAGMA writable_schema=ON",
        "SELECT load_extension('/tmp/nope')",
        "SELECT 1; SELECT 2",
    ],
)
def test_sqlite_executor_rejects_untrusted_write_escape_surfaces(sql: str) -> None:
    projection, _ = bench.build_projection(_structured_source())
    with pytest.raises(bench.QueryRejected):
        bench.execute_sqlite(projection, sql)


def test_sqlite_executor_terminates_runaway_and_bounds_results() -> None:
    projection, _ = bench.build_projection(_structured_source())
    tiny = bench.QueryLimits(
        max_rows=1,
        max_bytes=500,
        timeout_ms=100,
        sqlite_progress_ops=10,
        sqlite_progress_callbacks=10,
    )
    with pytest.raises(bench.QueryRejected):
        bench.execute_sqlite(projection, "SELECT row_index FROM sheet_1_rows ORDER BY row_index", limits=tiny)
    aliases = ",".join(f"sheet_1_rows t{i}" for i in range(14))
    with pytest.raises(bench.QueryRejected, match="execution budget|wall-clock"):
        bench.execute_sqlite(
            projection,
            f"SELECT COUNT(*) AS n FROM {aliases}",
            limits=tiny,
        )


def test_sqlite_result_digest_is_stable_excluding_runtime_measurements() -> None:
    projection, _ = bench.build_projection(_structured_source())
    first = bench.execute_sqlite(projection, "SELECT COUNT(*) AS n FROM sheet_1_rows")
    second = bench.execute_sqlite(projection, "SELECT COUNT(*) AS n FROM sheet_1_rows")
    assert first["result_sha256"] == second["result_sha256"]
    assert first["rows"] == second["rows"]


def test_duckdb_process_budget_separates_query_from_trusted_bootstrap() -> None:
    limits = bench.QueryLimits(
        timeout_ms=2_000,
        duckdb_bootstrap_grace_ms=30_000,
        duckdb_process_overhead_ms=5_000,
    )
    assert limits.timeout_ms == 2_000
    assert limits.duckdb_bootstrap_grace_ms == 30_000
    assert limits.duckdb_process_overhead_ms == 5_000
    assert bench.duckdb_process_timeout_ms(limits, query_count=1) == 37_000
    assert bench.duckdb_process_timeout_ms(limits, query_count=7) == 49_000


def test_duckdb_corpus_runner_batches_all_executable_cases_once(monkeypatch: pytest.MonkeyPatch) -> None:
    projection, _ = bench.build_projection(_structured_source())
    corpus = bench.build_esparza_query_corpus(projection)
    by_id = {str(case["case_id"]): case for case in corpus["cases"]}
    calls: list[list[tuple[str, str]]] = []

    def fake_batch(
        projection_bytes: bytes,
        queries: list[tuple[str, str]],
        *,
        duckdb_python: Path,
        limits: bench.QueryLimits,
        bwrap: Path,
    ) -> dict[str, object]:
        assert projection_bytes == projection
        calls.append(list(queries))
        results = []
        for query_id, _sql in queries:
            expected = by_id[query_id]["expected"]
            results.append(
                {
                    "query_id": query_id,
                    "result": {
                        "format": bench.RESULT_FORMAT,
                        "engine": "duckdb",
                        "columns": expected["columns"],
                        "rows": expected["rows"],
                        "row_count": len(expected["rows"]),
                        "truncated": False,
                        "result_sha256": "0" * 64,
                        "query_duration_ms": 1.0,
                    },
                }
            )
        return {
            "format": "canario.duckdb_query_batch_result.v1",
            "engine": "duckdb",
            "runtime": {"version": "test"},
            "security": {"query_timeout_ms": limits.timeout_ms},
            "bootstrap_duration_ms": 5.0,
            "projection_materializations": 1,
            "duration_ms": 10.0,
            "query_count": len(results),
            "queries": results,
        }

    monkeypatch.setattr(bench, "execute_duckdb_batch_sandboxed", fake_batch)
    run = bench.run_query_corpus(
        corpus,
        projection,
        engine="duckdb",
        duckdb_python=Path("/tmp/fake-duckdb-python"),
    )
    assert len(calls) == 1
    assert len(calls[0]) == run["summary"]["executable_cases"]
    assert run["summary"]["all_executable_passed"] is True
    assert run["engine_session"]["status"] == "completed"
    assert run["engine_session"]["query_count"] == len(calls[0])
    assert run["engine_session"]["projection_materializations"] == 1


def test_independent_corpus_has_all_required_semantic_distinctions() -> None:
    projection, _ = bench.build_projection(_structured_source())
    corpus = bench.build_esparza_query_corpus(projection)
    validated = bench.validate_query_corpus(corpus, projection)
    kinds = {case["kind"] for case in corpus["cases"]}
    assert validated["case_count"] == 10
    assert {
        "explicit_lookup",
        "filter",
        "aggregation",
        "grouping",
        "ordering_top_k",
        "window_rank",
        "numerical_composition",
        "cross_sheet_join",
        "bounded_absence",
        "insufficient_evidence",
    } <= kinds
    assert corpus["engine_outputs_used_as_oracle"] is False
    cross_sheet = next(case for case in corpus["cases"] if case["kind"] == "cross_sheet_join")
    if cross_sheet["portable_sql"] is not None:
        assert cross_sheet["required_evidence"]
    run = bench.run_query_corpus(corpus, projection, engine="sqlite")
    assert run["summary"]["all_executable_passed"] is True
    assert run["summary"]["semantic_only"] >= 1
    insufficient = next(case for case in corpus["cases"] if case["kind"] == "insufficient_evidence")
    assert insufficient["expected_semantics"] == "insufficient_evidence"
    assert insufficient["execution_failure_expected"] is False
    absence = next(case for case in corpus["cases"] if case["kind"] == "bounded_absence")
    assert absence["bounded_scope"]["does_not_exist_in_reality"] is False


def test_query_corpus_rejects_projection_drift_and_insufficient_as_failure() -> None:
    projection, _ = bench.build_projection(_structured_source())
    corpus = bench.build_esparza_query_corpus(projection)
    drifted = dict(corpus)
    drifted["projection_sha256"] = "f" * 64
    with pytest.raises(bench.FitBenchError, match="projection identity mismatch"):
        bench.validate_query_corpus(drifted, projection)
    broken = json.loads(json.dumps(corpus))
    broken["cases"][-1]["execution_failure_expected"] = True
    with pytest.raises(bench.FitBenchError, match="cannot be encoded as execution failure"):
        bench.validate_query_corpus(broken, projection)


def test_planner_handoff_is_frozen_from_corpus_not_engine_output() -> None:
    projection, _ = bench.build_projection(_structured_source())
    corpus = bench.build_esparza_query_corpus(projection)
    handoff = bench.planner_verifier_cases_from_corpus(corpus)
    assert handoff["format"] == bench.PLANNER_CASES_FORMAT
    assert handoff["projection_sha256"] == bench._sha256_bytes(projection)
    assert len(handoff["cases"]) == 10
    assert all("resource_budget" in case for case in handoff["cases"])


def test_external_csv_projection_requires_explicit_schema_and_encoding() -> None:
    source = b"provider,line,value\nA,1,10.5\nB,2,20.0\n"
    spec = {
        "format": bench.EXTERNAL_CSV_SPEC_FORMAT,
        "dataset_id": "public-test",
        "encoding": "utf-8",
        "delimiter": ",",
        "has_header": True,
        "columns": [
            {"name": "provider", "source_index": 0, "kind": "string"},
            {"name": "line", "source_index": 1, "kind": "integer"},
            {"name": "value", "source_index": 2, "kind": "number"},
        ],
    }
    projection, manifest = bench.build_external_csv_projection(source, spec)
    value = bench.load_projection(projection)
    assert value["source_representation_format"] == "external_csv"
    assert manifest["row_count"] == 2
    assert value["external_columns"][2]["name"] == "value"
    assert "external_transform_spec_sha256" in value
    assert "external_source_spec_sha256" not in value
    bound = dict(spec)
    bound["expected_source_sha256"] = bench._sha256_bytes(source)
    bound["expected_row_count"] = 2
    bound["notes"] = "verification-only prose must not alter projection identity"
    bound_projection, bound_manifest = bench.build_external_csv_projection(source, bound)
    assert bound_projection == projection
    assert bound_manifest["external_transform_spec_sha256"] == manifest["external_transform_spec_sha256"]
    assert bound_manifest["external_validation_spec_sha256"] != manifest["external_validation_spec_sha256"]
    prose_only = dict(bound)
    prose_only["notes"] = "different prose"
    prose_projection, prose_manifest = bench.build_external_csv_projection(source, prose_only)
    assert prose_projection == projection
    assert prose_manifest["external_validation_spec_sha256"] == bound_manifest["external_validation_spec_sha256"]
    remapped = json.loads(json.dumps(spec))
    remapped["columns"][2]["name"] = "amount"
    remapped_projection, remapped_manifest = bench.build_external_csv_projection(source, remapped)
    assert remapped_projection != projection
    assert remapped_manifest["external_transform_spec_sha256"] != manifest["external_transform_spec_sha256"]
    wrong_sha = dict(bound)
    wrong_sha["expected_source_sha256"] = "f" * 64
    with pytest.raises(bench.FitBenchError, match="SHA-256"):
        bench.build_external_csv_projection(source, wrong_sha)
    wrong_rows = dict(bound)
    wrong_rows["expected_row_count"] = 3
    with pytest.raises(bench.FitBenchError, match="row count"):
        bench.build_external_csv_projection(source, wrong_rows)
    bad = dict(spec)
    bad["encoding"] = "ascii"
    with pytest.raises(bench.FitBenchError, match="explicit encoding"):
        bench.build_external_csv_projection("á,x,1\n".encode(), bad)


def test_prior_art_selection_is_deterministic_and_byte_bound() -> None:
    dataset = json.dumps([{"id": f"C{i}"} for i in range(20)], sort_keys=True).encode()
    first = bench.deterministic_prior_art_case_ids(dataset, count=5)
    second = bench.deterministic_prior_art_case_ids(dataset, count=5)
    assert first == second
    changed = json.dumps([{"id": f"C{i}"} for i in range(21)], sort_keys=True).encode()
    assert bench.deterministic_prior_art_case_ids(changed, count=5) != first


def test_cross_engine_comparison_tolerates_only_small_numeric_representation_delta() -> None:
    left = {
        "columns": ["x"],
        "rows": [[{"type": "number", "value": "1.0"}]],
    }
    right = {
        "columns": ["x"],
        "rows": [[{"type": "number", "value": "1.0000000000001"}]],
    }
    assert bench.compare_results(left, right)["agree"] is True
    far = {
        "columns": ["x"],
        "rows": [[{"type": "number", "value": "1.1"}]],
    }
    assert bench.compare_results(left, far)["agree"] is False


def _duckdb_python() -> Path | None:
    value = os.environ.get("CANARIO_DUCKDB_PYTHON")
    return Path(value) if value else None


@pytest.mark.skipif(_duckdb_python() is None, reason="DuckDB bench venv is an explicit local certification lane")
def test_duckdb_sandbox_select_and_escape_rejection() -> None:
    python = _duckdb_python()
    assert python is not None
    projection, _ = bench.build_projection(_structured_source())
    selected = bench.execute_duckdb_sandboxed(
        projection,
        "SELECT COUNT(*) AS n FROM sheet_1_rows",
        duckdb_python=python,
    )
    assert selected["engine"] == "duckdb"
    assert selected["security"]["network_namespace"] == "unshared"
    assert selected["security"]["canonical_database_mounted"] is False
    assert str(selected["security"]["lock_configuration"]).lower() in {"true", "1"}
    assert selected["security"]["query_timeout_ms"] == bench.DEFAULT_TIMEOUT_MS
    assert selected["security"]["process_timeout_ms"] > selected["security"]["query_timeout_ms"]
    for sql in (
        "CREATE TABLE bad(x INTEGER)",
        "COPY (SELECT 1) TO '/tmp/out.csv'",
        "SELECT * FROM read_csv('/etc/passwd')",
        "ATTACH '/tmp/bad.db' AS bad",
        "INSTALL httpfs",
        "LOAD httpfs",
        "CREATE SECRET x (TYPE S3, KEY_ID 'a', SECRET 'b')",
        "SELECT 1; SELECT 2",
    ):
        with pytest.raises(bench.QueryRejected):
            bench.execute_duckdb_sandboxed(projection, sql, duckdb_python=python)


@pytest.mark.skipif(_duckdb_python() is None, reason="DuckDB bench venv is an explicit local certification lane")
def test_duckdb_batch_materializes_projection_once_and_keeps_per_query_budget() -> None:
    python = _duckdb_python()
    assert python is not None
    projection, _ = bench.build_projection(_structured_source())
    limits = bench.QueryLimits(
        timeout_ms=2_000,
        duckdb_bootstrap_grace_ms=30_000,
        duckdb_process_overhead_ms=5_000,
    )
    batch = bench.execute_duckdb_batch_sandboxed(
        projection,
        [
            ("q1", "SELECT COUNT(*) AS n FROM sheet_1_rows"),
            ("q2", "SELECT c1_text FROM sheet_1_rows WHERE row_index=2"),
        ],
        duckdb_python=python,
        limits=limits,
    )
    assert batch["format"] == "canario.duckdb_query_batch_result.v1"
    assert batch["query_count"] == 2
    assert batch["projection_materializations"] == 1
    assert [item["query_id"] for item in batch["queries"]] == ["q1", "q2"]
    assert batch["queries"][0]["result"]["rows"][0][0] == {"type": "integer", "value": "3"}
    assert batch["queries"][0]["result"]["query_watchdog_fired"] is False
    assert batch["security"]["query_timeout_ms"] == 2_000
    assert batch["security"]["process_timeout_ms"] == 39_000
    assert batch["bootstrap_duration_ms"] >= 0

    tiny = bench.QueryLimits(
        timeout_ms=50,
        duckdb_bootstrap_grace_ms=30_000,
        duckdb_process_overhead_ms=5_000,
    )
    with pytest.raises(bench.QueryRejected, match="execution budget|sandbox rejected"):
        bench.execute_duckdb_sandboxed(
            projection,
            "SELECT SUM(sin(i+j)) FROM range(1000000) a(i), range(1000000) b(j)",
            duckdb_python=python,
            limits=tiny,
        )


def test_inec_scale_corpus_uses_frozen_column_contract_and_independent_oracle() -> None:
    source = (
        "NUMERO_PROCEDIMIENTO,OBJETO_CONTRACTUAL,LINEA,COD_BIEN_SERVICIO,ENCARGADO_PROVEDURIA,PROVEEDOR_ADJU,MONTO_ADJUDICADO,NUMERO_CONTRATO\n"
        "P1,Objeto A,1,C1,Officer A,Provider A,CRC 10,K1\n"
        "P1,Objeto A,2,C2,Officer A,Provider B,CRC 20,K1\n"
        "P2,Objeto B,5,C3,Officer B,Provider A,CRC 30,K2\n"
    ).encode("cp1252")
    spec = {
        "format": bench.EXTERNAL_CSV_SPEC_FORMAT,
        "dataset_id": "CR-INEC-PURCHASES-2016-2021",
        "encoding": "cp1252",
        "delimiter": ",",
        "has_header": True,
        "expected_header": [
            "NUMERO_PROCEDIMIENTO",
            "OBJETO_CONTRACTUAL",
            "LINEA",
            "COD_BIEN_SERVICIO",
            "ENCARGADO_PROVEDURIA",
            "PROVEEDOR_ADJU",
            "MONTO_ADJUDICADO",
            "NUMERO_CONTRATO",
        ],
        "columns": [
            {"name": "numero_procedimiento", "source_index": 0, "kind": "string"},
            {"name": "objeto_contractual", "source_index": 1, "kind": "string"},
            {"name": "linea", "source_index": 2, "kind": "integer"},
            {"name": "cod_bien_servicio", "source_index": 3, "kind": "string"},
            {"name": "encargado_proveduria", "source_index": 4, "kind": "string"},
            {"name": "proveedor_adju", "source_index": 5, "kind": "string"},
            {"name": "monto_adjudicado_raw", "source_index": 6, "kind": "string"},
            {"name": "numero_contrato", "source_index": 7, "kind": "string"},
        ],
    }
    projection, _ = bench.build_external_csv_projection(source, spec)
    corpus = bench.build_inec_scale_corpus(projection)
    assert corpus["engine_outputs_used_as_oracle"] is False
    assert len(corpus["cases"]) == 7
    top = next(case for case in corpus["cases"] if case["case_id"] == "INEC-Q2-PROVIDER-GROUP")
    assert top["expected"]["rows"][0] == [
        {"type": "string", "value": "Provider A"},
        {"type": "integer", "value": "2"},
    ]


def test_external_csv_header_mismatch_fails_closed() -> None:
    source = b"a,b\n1,2\n"
    spec = {
        "format": bench.EXTERNAL_CSV_SPEC_FORMAT,
        "dataset_id": "x",
        "encoding": "utf-8",
        "delimiter": ",",
        "has_header": True,
        "expected_header": ["wrong", "b"],
        "columns": [
            {"name": "a", "source_index": 0, "kind": "string"},
            {"name": "b", "source_index": 1, "kind": "string"},
        ],
    }
    with pytest.raises(bench.FitBenchError, match="header does not match"):
        bench.build_external_csv_projection(source, spec)


def test_scitab_lane_is_mechanical_and_preserves_claim_label_without_semantic_conversion() -> None:
    dataset = json.dumps(
        [
            {
                "paper": "p",
                "paper_id": "P1",
                "table_cpation": "caption",
                "table_column_names": ["Metric", "Value"],
                "table_content_values": [["A", "10"], ["B", "20"]],
                "id": f"C{i}",
                "claim": f"claim {i}",
                "label": "supports" if i % 2 == 0 else "refutes",
                "table_id": f"T{i}",
            }
            for i in range(8)
        ],
        sort_keys=True,
    ).encode()
    lane = bench.prepare_scitab_lane(dataset, count=3)
    assert len(lane["selected_case_ids"]) == 3
    assert [case["case_id"] for case in lane["cases"]] == lane["selected_case_ids"]
    assert all(case["label"] in {"supports", "refutes"} for case in lane["cases"])
    for case in lane["cases"]:
        projection = bench.load_projection(case["projection_bytes"].encode("utf-8"))
        assert projection["source_representation_format"] == "external_scitab_case"
        assert projection["external_metadata"]["claim"] == case["claim"]
