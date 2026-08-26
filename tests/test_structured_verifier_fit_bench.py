from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PHASE_PATH = ROOT / "notebook" / "implementation" / "structured_verifier_fit_bench.py"
WORKER_PATH = ROOT / "notebook" / "implementation" / "structured_verifier_codex_worker.py"
FOUNDATION_PATH = ROOT / "notebook" / "implementation" / "structured_reasoning_fit_bench.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


foundation = _load("canario_phase_d_test_foundation", FOUNDATION_PATH)
phase = _load("canario_phase_d_test_harness", PHASE_PATH)
worker = _load("canario_phase_d_test_worker", WORKER_PATH)


def _structured_source() -> bytes:
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
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _fixture():
    projection, _ = foundation.build_projection(_structured_source())
    corpus = foundation.build_esparza_query_corpus(projection)
    foundation.validate_query_corpus(corpus, projection)
    planner = foundation.planner_verifier_cases_from_corpus(corpus)
    cases = phase.build_phase_d_cases(projection, corpus, planner)
    return projection, corpus, planner, cases


def _successful_worker(system: str, verdict: str, *, result=None, sufficiency="adequate", cited_ids=None, sql="SELECT 1"):
    events = []
    if result is not None:
        events.append(
            {
                "tool": "execute_sql",
                "query_id": "Q1",
                "purpose": "proof",
                "sql": sql,
                "outcome": "success",
                "result": result,
            }
        )
    return {
        "format": phase.WORKER_RESULT_FORMAT,
        "status": "completed",
        "system": system,
        "raw_verdict": verdict,
        "normalized_verdict": verdict,
        "explicit_sufficiency": system == phase.SIMPLE_SYSTEM,
        "evidence_sufficiency": sufficiency if system == phase.SIMPLE_SYSTEM else None,
        "report": "",
        "cited_query_ids": cited_ids or [],
        "tool_events": events,
        "tool_rejection_count": 0,
        "tool_execution_failure_count": 0,
        "usage": {
            "billing_mode": "chatgpt_subscription",
            "per_token_api_billing": False,
            "api_key_used": False,
            "subscription_codex_invocations": 2,
            "prompt_bytes_egressed": 100,
            "structured_output_bytes": 20,
        },
        "duration_ms": 5.0,
    }


def test_phase_d_cases_are_deterministic_hidden_balanced_and_subscription_only() -> None:
    projection, corpus, planner, first = _fixture()
    second = phase.build_phase_d_cases(projection, corpus, planner)
    assert phase._canonical_json_bytes(first) == phase._canonical_json_bytes(second)
    assert phase.validate_phase_d_cases(first, projection) == {
        "case_count": 8,
        "expected_verdict_counts": {"supported": 4, "contradicted": 2, "insufficient_evidence": 2},
    }
    visible = phase.model_visible_case(first["cases"][0], first["projection_sha256"])
    assert set(visible) == {"case_id", "claim", "source_authority", "projection_sha256", "resource_budget"}
    serialized = json.dumps(visible)
    assert "expected_verdict" not in serialized
    assert "evidence_obligation" not in serialized
    assert first["model_execution_profile"]["billing_mode"] == "chatgpt_subscription"
    assert first["model_execution_profile"]["per_token_api_billing"] is False
    profile = first["model_execution_profile"]
    assert profile["current_transport_profile"] == "openai_codex_subscription"
    assert profile["current_profile_api_key_required"] is False
    assert profile["current_profile_per_token_api_billing"] is False
    assert profile["automatic_metered_fallback"] is False
    assert profile["future_metered_provider_profiles_allowed"] is True
    assert profile["future_provider_profiles_status"] == "deferred"


def test_phase_d_claims_preserve_bounded_vs_global_scope() -> None:
    _, _, _, cases = _fixture()
    by_id = {case["case_id"]: case for case in cases["cases"]}
    assert by_id["D2-SUPPORTED-AGGREGATE"]["claim"] != by_id["D3-CONTRADICTED-AGGREGATE"]["claim"]
    assert by_id["D7-INSUFFICIENT-GLOBAL-ABSENCE"]["expected_sufficiency"] == "inadequate"
    assert by_id["D8-INSUFFICIENT-GLOBAL-TOTAL"]["source_authority"]["inventory_completeness"] == "not_established_outside_this_workbook"
    assert by_id["D6-SUPPORTED-BOUNDED-ABSENCE"]["expected_verdict"] == "supported"


def test_evidence_obligations_allow_equivalent_query_shapes_for_cross_sheet_and_topk() -> None:
    projection, _, _, cases = _fixture()
    by_id = {case["case_id"]: case for case in cases["cases"]}
    for case_id in ("D4-SUPPORTED-CROSS-SHEET", "D5-CONTRADICTED-TOPK"):
        case = by_id[case_id]
        obligation = case["evidence_obligation"]
        assert obligation["kind"] == "exact_row_value_sets"
        rows = []
        for expected_row in obligation["rows"]:
            rows.append([{"type": "string", "value": "extra"}, *expected_row, {"type": "integer", "value": "999"}])
        alternate = {
            "format": foundation.RESULT_FORMAT,
            "columns": [f"c{i}" for i in range(len(rows[0]))],
            "rows": rows,
            "row_count": len(rows),
            "truncated": False,
            "result_sha256": "x",
        }
        required_tables = obligation["required_tables"]
        sql = "SELECT * FROM " + " JOIN ".join(required_tables) + " ON 1=1"
        worker_result = _successful_worker(
            phase.SIMPLE_SYSTEM,
            case["expected_verdict"],
            result=alternate,
            cited_ids=["Q1"],
            sql=sql,
        )
        assert phase.score_worker_case(case, worker_result, projection)["evidence_retrieved"] is True



def test_bounded_absence_evidence_can_be_proven_across_multiple_successful_queries() -> None:
    projection, _, _, cases = _fixture()
    case = next(item for item in cases["cases"] if item["case_id"] == "D6-SUPPORTED-BOUNDED-ABSENCE")
    obligation = case["evidence_obligation"]
    assert obligation["kind"] == "zero_result_for_each_required_table"
    zero = obligation["value"]
    sentinel = case["counterfactual_mutations"][0]["value"]["text"]
    projection_doc = json.loads(projection)
    sheet_by_table = {
        f"sheet_{sheet['ordinal']}_rows": sheet
        for sheet in projection_doc["sheets"]
    }
    events = []
    for index, table in enumerate(obligation["required_tables"], start=1):
        sheet = sheet_by_table[table]
        predicates = " OR ".join(
            f"c{column}_text={foundation._sql_string_literal(sentinel)}"
            for column in range(1, int(sheet["max_column"]) + 1)
        )
        sql = f"SELECT COUNT(*) AS matches FROM {table} WHERE {predicates}"
        executed = foundation.execute_sqlite(projection, sql)
        events.append(
            {
                "tool": "execute_sql",
                "query_id": f"Q{index}",
                "purpose": "bounded absence proof",
                "sql": sql,
                "outcome": "success",
                "result": {
                    key: executed[key]
                    for key in ("format", "columns", "rows", "row_count", "truncated", "result_sha256")
                },
            }
        )
    result = _successful_worker(phase.SIMPLE_SYSTEM, "supported")
    result["tool_events"] = events
    result["cited_query_ids"] = [event["query_id"] for event in events]
    score = phase.score_worker_case(case, result, projection)
    assert score["evidence_retrieved"] is True
    assert score["evidence_backed_verdict"] is True

    incomplete = dict(result)
    incomplete["tool_events"] = events[:-1]
    incomplete["cited_query_ids"] = [event["query_id"] for event in events[:-1]]
    assert phase.score_worker_case(case, incomplete, projection)["evidence_retrieved"] is False

def test_evidence_scoring_requires_actual_matching_execution() -> None:
    projection, _, _, cases = _fixture()
    case = cases["cases"][1]
    obligation = case["evidence_obligation"]
    expected_value = obligation["value"]
    matching = {
        "format": foundation.RESULT_FORMAT,
        "columns": ["total"],
        "rows": [[expected_value]],
        "row_count": 1,
        "truncated": False,
        "result_sha256": "x",
    }
    good = _successful_worker(
        phase.SIMPLE_SYSTEM,
        "supported",
        result=matching,
        cited_ids=["Q1"],
        sql=f"SELECT SUM(c3_integer) FROM {obligation['required_tables'][0]}",
    )
    scored = phase.score_worker_case(case, good, projection)
    assert scored["verdict_correct"] is True
    assert scored["evidence_retrieved"] is True
    assert scored["evidence_backed_verdict"] is True

    wrong = dict(matching)
    wrong["rows"] = [[{"type": "integer", "value": "999"}]]
    bad = _successful_worker(
        phase.SIMPLE_SYSTEM,
        "supported",
        result=wrong,
        cited_ids=["Q1"],
        sql=f"SELECT SUM(c3_integer) FROM {obligation['required_tables'][0]}",
    )
    assert phase.score_worker_case(case, bad, projection)["evidence_backed_verdict"] is False



def test_evidence_backing_rejects_claim_echo_constant_query_via_hidden_counterfactual() -> None:
    projection, _, _, cases = _fixture()
    case = next(item for item in cases["cases"] if item["case_id"] == "D2-SUPPORTED-AGGREGATE")
    obligation = case["evidence_obligation"]
    asserted = obligation["value"]
    table = obligation["required_tables"][0]
    constant_result = {
        "format": foundation.RESULT_FORMAT,
        "columns": ["total"],
        "rows": [[asserted]],
        "row_count": 1,
        "truncated": False,
        "result_sha256": "constant",
    }
    fake = _successful_worker(
        phase.SIMPLE_SYSTEM,
        "supported",
        result=constant_result,
        cited_ids=["Q1"],
        sql=f"SELECT {asserted['value']} AS total FROM {table} LIMIT 1",
    )
    score = phase.score_worker_case(case, fake, projection)
    assert score["evidence_retrieved"] is True
    assert score["causal_evidence_dependency"] is False
    assert score["evidence_backed_verdict"] is False


def test_real_aggregate_query_is_causally_sensitive_to_hidden_source_perturbation() -> None:
    projection, _, _, cases = _fixture()
    case = next(item for item in cases["cases"] if item["case_id"] == "D2-SUPPORTED-AGGREGATE")
    obligation = case["evidence_obligation"]
    table = obligation["required_tables"][0]
    sql = f"SELECT SUM(c3_number) AS total FROM {table}"
    actual = foundation.execute_sqlite(projection, sql)
    result = _successful_worker(
        phase.SIMPLE_SYSTEM,
        "supported",
        result={key: actual[key] for key in ("format", "columns", "rows", "row_count", "truncated", "result_sha256")},
        cited_ids=["Q1"],
        sql=sql,
    )
    score = phase.score_worker_case(case, result, projection)
    assert score["evidence_retrieved"] is True
    assert score["causal_evidence_dependency"] is True
    assert score["evidence_backed_verdict"] is True

def test_unsupported_query_id_and_thucy_sql_citation_are_separate_failures() -> None:
    projection, _, _, cases = _fixture()
    case = cases["cases"][1]
    obligation = case["evidence_obligation"]
    matching = {
        "format": foundation.RESULT_FORMAT,
        "columns": ["total"],
        "rows": [[obligation["value"]]],
        "row_count": 1,
        "truncated": False,
        "result_sha256": "x",
    }
    simple = _successful_worker(
        phase.SIMPLE_SYSTEM,
        "supported",
        result=matching,
        cited_ids=["Q404"],
        sql=f"SELECT SUM(c3_integer) FROM {obligation['required_tables'][0]}",
    )
    assert phase.score_worker_case(case, simple, projection)["unsupported_query_id_count"] == 1

    thucy = _successful_worker(
        phase.THUCY_SYSTEM,
        "supported",
        result=matching,
        sql=f"SELECT SUM(c3_integer) FROM {obligation['required_tables'][0]}",
    )
    thucy["report"] = "```sql\nSELECT never_executed FROM nowhere\n```"
    score = phase.score_worker_case(case, thucy, projection)
    assert score["unsupported_sql_citation_count"] == 1
    assert score["explicit_sufficiency"] is False


def test_tool_rejection_is_not_epistemic_abstention() -> None:
    projection, _, _, cases = _fixture()
    case = cases["cases"][6]
    result = _successful_worker(phase.SIMPLE_SYSTEM, "insufficient_evidence", sufficiency="inadequate")
    result["tool_events"] = [
        {"tool": "execute_sql", "query_id": "Q1", "sql": "DROP TABLE x", "outcome": "rejected", "error": "forbidden"}
    ]
    result["tool_rejection_count"] = 1
    score = phase.score_worker_case(case, result, projection)
    assert score["verdict_correct"] is True
    assert score["execution_clean"] is False
    aggregate = phase._aggregate_scores([score])
    assert aggregate["tool_rejections"] == 1
    assert aggregate["abstention_recall"] == 1.0


def test_worker_projection_schema_and_sql_plan_stay_on_hardened_sqlite() -> None:
    projection, _, _, _ = _fixture()
    schema = worker._schema_for_projection(projection)
    assert schema["database"] == "canario_projection"
    assert schema["projection_sha256"] == phase._sha256_bytes(projection)
    events = worker._execute_plan(
        projection,
        [{"query_id": "Q1", "purpose": "count", "sql": "SELECT COUNT(*) AS n FROM sheet_1_rows"}],
    )
    assert events[0]["outcome"] == "success"
    assert events[0]["result"]["row_count"] == 1
    rejected = worker._execute_plan(
        projection,
        [{"query_id": "Q1", "purpose": "bad", "sql": "DROP TABLE sheet_1_rows"}],
    )
    assert rejected[0]["outcome"] == "rejected"


def test_thucy_prompts_are_extracted_as_literals_without_importing_package(tmp_path: Path) -> None:
    root = tmp_path / "thucy"
    package = root / "thucy"
    package.mkdir(parents=True)
    (package / "agents.py").write_text(
        "\n".join(f'{name} = "{name}-value"' for name in worker.THUCY_PROMPT_NAMES) + "\n",
        encoding="utf-8",
    )
    values = worker.extract_thucy_prompts(root)
    assert set(values) == set(worker.THUCY_PROMPT_NAMES)
    assert values["VERIFIER_PROMPT"] == "VERIFIER_PROMPT-value"


def test_case_prompt_boundary_excludes_projection_scoped_thucy_setup(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    projection_path = tmp_path / "projection.json"
    projection_bytes = b'{"format":"test-projection"}'
    projection_path.write_bytes(projection_bytes)

    class _Config:
        def identity(self):
            return {
                "execution_venue": "subscription_agent",
                "provider": "openai",
                "model": phase.DEFAULT_MODEL,
                "reasoning_effort": phase.DEFAULT_REASONING_EFFORT,
                "endpoint_profile": "openai_codex_subscription",
                "auth_store": "keyring",
                "per_token_api_billing": False,
                "api_key_used": False,
            }

    class _Runner:
        def __init__(self, config, scratch):
            self.calls = []

        def usage(self):
            return {
                "billing_mode": "chatgpt_subscription",
                "per_token_api_billing": False,
                "api_key_used": False,
                "subscription_codex_invocations": 0,
                "prompt_bytes_egressed": 0,
                "structured_output_bytes": 0,
            }

    monkeypatch.setattr(worker, "_config_from_request", lambda request: _Config())
    monkeypatch.setattr(worker, "CodexSubscriptionRunner", _Runner)
    monkeypatch.setattr(
        worker,
        "extract_thucy_prompts",
        lambda root: {name: f"{name}-value" for name in worker.THUCY_PROMPT_NAMES},
    )
    monkeypatch.setattr(
        worker,
        "build_thucy_shared_context",
        lambda **kwargs: {"data_report": "data", "schema_answer": "schema"},
    )

    common = {
        "projection_path": str(projection_path),
        "projection_sha256": worker._sha256_bytes(projection_bytes),
        "max_sql_calls": 6,
    }
    setup = worker.run_request(
        {
            **common,
            "mode": "setup",
            "system": phase.THUCY_SETUP_SYSTEM,
            "thucy_root": str(tmp_path / "thucy"),
            "source_authority": {"scope": "test"},
        }
    )
    assert setup["status"] == "completed"
    assert setup["shared_context"] == {"data_report": "data", "schema_answer": "schema"}

    case = worker.run_request({**common, "mode": "case", "system": phase.SIMPLE_SYSTEM})
    assert case["status"] == "execution_failed"
    assert case["error"] == "WorkerError: case prompt is required"


def test_codex_environment_is_keyring_subscription_only(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir(mode=0o700)
    monkeypatch.setattr(worker.CodexSubscriptionConfig, "probe_version", lambda self: "0.149.0")
    config = worker.CodexSubscriptionConfig(codex="/usr/bin/codex", codex_home=codex_home)
    runner = worker.CodexSubscriptionRunner(config, tmp_path / "scratch")
    runner.scratch.mkdir()
    call_dir = runner.scratch / "call"
    call_dir.mkdir()
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-cross")
    monkeypatch.setenv("CODEX_UNTRUSTED_OVERRIDE", "must-not-cross")
    env = runner._env(call_dir)
    assert env["CODEX_HOME"] == str(codex_home.resolve())
    assert "OPENAI_API_KEY" not in env
    assert "CODEX_UNTRUSTED_OVERRIDE" not in env
    assert config.identity()["per_token_api_billing"] is False
    assert config.identity()["api_key_used"] is False



def test_codex_profile_validation_fails_structurally_before_model_call(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    request = {
        "mode": "probe",
        "system": phase.SIMPLE_SYSTEM,
        "codex": "/missing/codex",
        "codex_home": str(tmp_path / "missing-home"),
        "model": "gpt-5.6-terra",
        "reasoning_effort": "medium",
        "qualified_codex_versions": ["0.149.0"],
    }
    result = worker.run_request(request)
    assert result["status"] == "execution_failed"
    assert result["error_code"] == "subscription_profile_unavailable"
    assert result["system"] == phase.SIMPLE_SYSTEM
    assert result["usage"]["subscription_codex_invocations"] == 0
    assert result["requested_provider"]["per_token_api_billing"] is False
    assert result["requested_provider"]["api_key_used"] is False


def test_codex_profile_rejects_ambient_admin_skills(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir(mode=0o700)
    admin_skills = tmp_path / "admin-skills"
    admin_skills.mkdir()
    (admin_skills / "ambient.md").write_text("not allowed", encoding="utf-8")
    original_path = worker.Path

    class _PathProxy:
        def __new__(cls, value):
            if value == "/etc/codex/skills":
                return admin_skills
            return original_path(value)

        @classmethod
        def home(cls):
            return original_path.home()

    monkeypatch.setattr(worker, "Path", _PathProxy)
    monkeypatch.setattr(worker.CodexSubscriptionConfig, "probe_version", lambda self: "0.149.0")
    with pytest.raises(worker.WorkerError, match="administrator Codex skills"):
        worker.CodexSubscriptionConfig(codex="/usr/bin/codex", codex_home=codex_home)

def test_codex_command_disables_shell_web_skills_and_uses_structured_output(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir(mode=0o700)
    monkeypatch.setattr(worker.CodexSubscriptionConfig, "probe_version", lambda self: "0.149.0")
    config = worker.CodexSubscriptionConfig(codex="/usr/bin/codex", codex_home=codex_home)
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    runner = worker.CodexSubscriptionRunner(config, scratch)
    call = scratch / "call"
    call.mkdir()
    command = runner._command(call, call / "schema.json", call / "result.json")
    rendered = " ".join(command)
    assert "--output-schema" in command
    assert "--ephemeral" in command
    assert "--ignore-user-config" in command
    assert "features.shell_tool=false" in rendered
    assert "features.unified_exec=false" in rendered
    assert 'web_search="disabled"' in rendered
    assert "skills.bundled.enabled=false" in rendered
    assert "gpt-5.6-terra" in command


def test_subscription_usage_comparison_counts_shared_thucy_setup() -> None:
    projection, _, _, _ = _fixture()
    simple_scores = [
        {
            **phase.score_worker_case(
                {
                    "case_id": "x",
                    "expected_verdict": "insufficient_evidence",
                    "expected_sufficiency": "inadequate",
                    "evidence_required": False,
                    "evidence_obligation": None,
                    "counterfactual_mutations": [],
                },
                _successful_worker(phase.SIMPLE_SYSTEM, "insufficient_evidence", sufficiency="inadequate"),
                projection,
            )
        }
    ]
    aggregate = phase._aggregate_scores(simple_scores)
    assert aggregate["usage"]["subscription_codex_invocations"] == 2
    setup = {
        "usage": {
            "subscription_codex_invocations": 2,
            "prompt_bytes_egressed": 50,
            "structured_output_bytes": 10,
        },
        "duration_ms": 4.0,
    }
    phase._add_shared_usage(aggregate, setup)
    assert aggregate["usage"]["subscription_codex_invocations"] == 4
    assert aggregate["shared_setup_codex_invocations"] == 2


def test_paired_campaign_requires_exact_passing_provider_probe() -> None:
    probe = {
        "format": phase.PROVIDER_PROBE_FORMAT,
        "model": phase.DEFAULT_MODEL,
        "reasoning_effort": phase.DEFAULT_REASONING_EFFORT,
        "pass": True,
        "worker": {
            "status": "completed",
            "provider": {
                "execution_venue": "subscription_agent",
                "provider": "openai",
                "model": phase.DEFAULT_MODEL,
                "reasoning_effort": phase.DEFAULT_REASONING_EFFORT,
                "codex_version": "0.149.0",
                "endpoint_profile": "openai_codex_subscription",
                "auth_store": "keyring",
                "per_token_api_billing": False,
                "api_key_used": False,
            },
        },
    }
    validated = phase.validate_provider_probe_for_campaign(
        probe, model=phase.DEFAULT_MODEL, reasoning_effort=phase.DEFAULT_REASONING_EFFORT
    )
    assert validated["provider"]["api_key_used"] is False
    bad = dict(probe)
    bad["pass"] = False
    with pytest.raises(phase.VerifierFitError, match="passing subscription provider probe"):
        phase.validate_provider_probe_for_campaign(
            bad, model=phase.DEFAULT_MODEL, reasoning_effort=phase.DEFAULT_REASONING_EFFORT
        )


def test_future_metered_profiles_are_deferred_not_architecturally_forbidden() -> None:
    projection, _, _, cases = _fixture()
    profile = cases["model_execution_profile"]
    assert profile["future_metered_provider_profiles_allowed"] is True
    assert profile["future_provider_profiles_status"] == "deferred"
    assert profile["automatic_metered_fallback"] is False


def test_current_phase_d_profile_requires_no_metered_api_runtime_or_agents_sdk() -> None:
    harness_source = PHASE_PATH.read_text(encoding="utf-8")
    worker_source = WORKER_PATH.read_text(encoding="utf-8")
    combined = harness_source + worker_source
    assert "openai-agents" not in combined
    assert "toolbox-core" not in combined
    assert "CANARIO_VERIFIER_API_KEY" not in combined
    assert "os.environ.copy" not in worker_source
    assert "dict(os.environ)" not in worker_source
    assert "from openai import" not in combined
    assert "from agents import" not in combined
