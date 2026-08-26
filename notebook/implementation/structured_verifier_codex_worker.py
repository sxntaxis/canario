#!/usr/bin/env python3
"""Subscription-backed Codex worker for Canario's Phase-D verifier fit bench.

This worker implements only the current subscription-backed Codex reference profile. Metered
OpenAI API, OpenRouter and other provider profiles are architecturally allowed but intentionally
deferred to later adapters; this worker never performs or silently falls back to paid API
execution. Every model call in this profile goes through the official Codex CLI with a dedicated
keyring-backed CODEX_HOME. The model never receives shell/database authority: it emits
schema-constrained SQL plans, the harness executes those plans through the already hardened
SQLite fit-bench executor, and deterministic results are fed back into later model calls as text.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

BASE_DIR = Path(__file__).resolve().parent
FOUNDATION_PATH = BASE_DIR / "structured_reasoning_fit_bench.py"
RESULT_FORMAT = "canario.verifier_codex_worker_result.v1"
CODEX_VERSION_RE = re.compile(r"(?:codex-cli|OpenAI Codex v?)\s*(?P<version>[0-9]+(?:\.[0-9]+){2,3})", re.I)

THUCY_PROMPT_NAMES = (
    "DATA_EXPERT_PROMPT",
    "SCHEMA_EXPERT_PROMPT",
    "SQL_EXPERT_PROMPT",
    "VERIFIER_PROMPT",
)

_STATIC_CODEX_CONFIG_OVERRIDES = (
    'model_reasoning_summary="none"',
    "hide_agent_reasoning=true",
    "show_raw_agent_reasoning=false",
    "project_doc_max_bytes=0",
    "skills.bundled.enabled=false",
    'web_search="disabled"',
    "features.view_image=false",
    "features.shell_tool=false",
    "features.unified_exec=false",
    "features.hooks=false",
    "features.plugins=false",
    "features.apps=false",
    "features.tool_suggest=false",
    "features.image_generation=false",
    "features.browser_use=false",
    "features.browser_use_external=false",
    "features.computer_use=false",
    "features.multi_agent=false",
    "features.multi_agent_v2.enabled=false",
)


class WorkerError(ValueError):
    """The Phase-D worker cannot execute the exact requested contract."""


def _load_foundation():
    spec = importlib.util.spec_from_file_location("canario_structured_reasoning_foundation_phase_d", FOUNDATION_PATH)
    if spec is None or spec.loader is None:
        raise WorkerError("cannot load structured reasoning foundation")
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


def _schema_for_projection(projection_bytes: bytes) -> dict[str, object]:
    projection = foundation.load_projection(projection_bytes)
    sheets = projection.get("sheets")
    if not isinstance(sheets, list):
        raise WorkerError("projection sheets missing")
    tables: list[dict[str, object]] = []
    for raw in sheets:
        if not isinstance(raw, dict):
            raise WorkerError("projection sheet malformed")
        ordinal = int(raw["ordinal"])
        max_column = int(raw["max_column"])
        columns: list[dict[str, object]] = [{"name": "row_index", "kind": "integer", "meaning": "1-based source row"}]
        for column in range(1, max_column + 1):
            prefix = f"c{column}"
            columns.extend(
                [
                    {"name": f"{prefix}_kind", "kind": "text"},
                    {"name": f"{prefix}_text", "kind": "text"},
                    {"name": f"{prefix}_integer", "kind": "integer"},
                    {"name": f"{prefix}_number", "kind": "real"},
                    {"name": f"{prefix}_boolean", "kind": "boolean"},
                    {"name": f"{prefix}_datetime", "kind": "text"},
                    {"name": f"{prefix}_formula", "kind": "text"},
                    {"name": f"{prefix}_address", "kind": "text"},
                    {"name": f"{prefix}_data_type", "kind": "text"},
                    {"name": f"{prefix}_number_format", "kind": "text"},
                ]
            )
        tables.append(
            {
                "table": f"sheet_{ordinal}_rows",
                "sheet_ordinal": ordinal,
                "sheet_name": raw["name"],
                "max_row": int(raw["max_row"]),
                "max_column": max_column,
                "columns": columns,
            }
        )
    return {
        "database": "canario_projection",
        "projection_sha256": _sha256_bytes(projection_bytes),
        "tables": tables,
        "query_rules": {
            "dialect": "SQLite",
            "one_statement": True,
            "read_only_select": True,
            "source_rows_are_1_based": True,
            "typed_value_columns": "use *_integer/*_number/*_text according to represented value kind",
        },
    }


def _source_inventory(projection_bytes: bytes, authority: Mapping[str, object]) -> dict[str, object]:
    return {
        "sources": [
            {
                "name": "canario_projection",
                "kind": "deterministic_relational_projection",
                "projection_sha256": _sha256_bytes(projection_bytes),
                "authority_scope": dict(authority),
            }
        ],
        "other_sources_accessible": False,
    }


def _json_schema_object(properties: Mapping[str, object], required: Sequence[str]) -> dict[str, object]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "properties": dict(properties),
        "required": list(required),
    }


def _planner_schema(max_sql_calls: int) -> dict[str, object]:
    return _json_schema_object(
        {
            "queries": {
                "type": "array",
                "maxItems": max_sql_calls,
                "items": _json_schema_object(
                    {
                        "query_id": {"type": "string", "pattern": r"^Q[1-9][0-9]*$", "maxLength": 16},
                        "purpose": {"type": "string", "maxLength": 600},
                        "sql": {"type": "string", "minLength": 1, "maxLength": 8000},
                    },
                    ("query_id", "purpose", "sql"),
                ),
            },
            "can_finalize_without_sql": {"type": "boolean"},
            "planning_note": {"type": "string", "maxLength": 1200},
        },
        ("queries", "can_finalize_without_sql", "planning_note"),
    )


def _simple_final_schema() -> dict[str, object]:
    return _json_schema_object(
        {
            "verdict": {"type": "string", "enum": ["supported", "contradicted", "insufficient_evidence"]},
            "evidence_sufficiency": {"type": "string", "enum": ["adequate", "inadequate"]},
            "reason": {"type": "string", "maxLength": 4000},
            "cited_query_ids": {"type": "array", "items": {"type": "string", "maxLength": 16}, "maxItems": 16},
        },
        ("verdict", "evidence_sufficiency", "reason", "cited_query_ids"),
    )


def _report_schema(field: str) -> dict[str, object]:
    return _json_schema_object({field: {"type": "string", "maxLength": 12000}}, (field,))


def _thucy_verifier_schema() -> dict[str, object]:
    return _json_schema_object(
        {
            "report": {"type": "string", "maxLength": 16000},
            "verdict": {
                "type": "string",
                "enum": ["VERIFIED", "PARTLY VERIFIED", "PARTLY CONTRADICTED", "CONTRADICTED", "NOT ENOUGH INFO"],
            },
        },
        ("report", "verdict"),
    )


def _probe_schema() -> dict[str, object]:
    return _json_schema_object(
        {"ok": {"type": "boolean"}, "message": {"type": "string", "maxLength": 200}},
        ("ok", "message"),
    )


def _validate_plan(value: Mapping[str, object], max_sql_calls: int) -> list[dict[str, str]]:
    raw_queries = value.get("queries")
    if not isinstance(raw_queries, list) or len(raw_queries) > max_sql_calls:
        raise WorkerError("planner query list violates SQL-call budget")
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for raw in raw_queries:
        if not isinstance(raw, dict):
            raise WorkerError("planner query malformed")
        query_id = raw.get("query_id")
        sql = raw.get("sql")
        purpose = raw.get("purpose")
        if not all(isinstance(item, str) for item in (query_id, sql, purpose)):
            raise WorkerError("planner query fields malformed")
        if not re.fullmatch(r"Q[1-9][0-9]*", str(query_id)) or query_id in seen:
            raise WorkerError("planner query IDs must be unique Q-prefixed integers")
        if not str(sql).strip():
            raise WorkerError("planner SQL cannot be empty")
        seen.add(str(query_id))
        result.append({"query_id": str(query_id), "purpose": str(purpose), "sql": str(sql)})
    return result


def _execute_plan(projection_bytes: bytes, plan: Sequence[Mapping[str, str]]) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for query in plan:
        started = time.monotonic()
        try:
            result = foundation.execute_sqlite(projection_bytes, str(query["sql"]))
        except foundation.QueryRejected as exc:
            events.append(
                {
                    "tool": "execute_sql",
                    "query_id": query["query_id"],
                    "purpose": query["purpose"],
                    "sql": query["sql"],
                    "outcome": "rejected",
                    "error": str(exc),
                    "duration_ms": round((time.monotonic() - started) * 1000.0, 3),
                }
            )
        except Exception as exc:  # fail closed: infrastructure defect is not epistemic insufficiency
            events.append(
                {
                    "tool": "execute_sql",
                    "query_id": query["query_id"],
                    "purpose": query["purpose"],
                    "sql": query["sql"],
                    "outcome": "execution_failed",
                    "error": f"{type(exc).__name__}: {exc}",
                    "duration_ms": round((time.monotonic() - started) * 1000.0, 3),
                }
            )
        else:
            stable_result = {
                key: result[key]
                for key in ("format", "columns", "rows", "row_count", "truncated", "result_sha256")
            }
            events.append(
                {
                    "tool": "execute_sql",
                    "query_id": query["query_id"],
                    "purpose": query["purpose"],
                    "sql": query["sql"],
                    "outcome": "success",
                    "result": stable_result,
                    "duration_ms": round((time.monotonic() - started) * 1000.0, 3),
                }
            )
    return events


def _tool_results_text(events: Sequence[Mapping[str, object]]) -> str:
    return json.dumps(list(events), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def extract_thucy_prompts(thucy_root: Path) -> dict[str, str]:
    source = (thucy_root / "thucy" / "agents.py").read_text(encoding="utf-8")
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
            raise WorkerError(f"Thucy prompt {name} is not a string literal")
        values[name] = value
    missing = [name for name in THUCY_PROMPT_NAMES if name not in values]
    if missing:
        raise WorkerError("cannot extract exact Thucy prompts: " + ", ".join(missing))
    return values


@dataclass(frozen=True, slots=True)
class CodexSubscriptionConfig:
    codex: str
    codex_home: Path
    model: str = "gpt-5.6-terra"
    reasoning_effort: str = "medium"
    qualified_versions: tuple[str, ...] = ("0.149.0",)
    call_timeout_seconds: int = 240
    auth_store_mode: str = "keyring"

    def __post_init__(self) -> None:
        if self.reasoning_effort not in {"none", "low", "medium", "high", "xhigh", "max"}:
            raise WorkerError("unsupported reasoning effort")
        if self.auth_store_mode != "keyring":
            raise WorkerError("Phase-D Codex execution requires keyring auth")
        if not self.model or any(ch.isspace() for ch in self.model):
            raise WorkerError("model must be one Codex model token")
        self._validate_home()
        version = self.probe_version()
        if version not in self.qualified_versions:
            raise WorkerError(f"Codex CLI {version} is outside qualified set {self.qualified_versions}")

    def _validate_home(self) -> None:
        home = self.codex_home.expanduser().resolve()
        if not home.is_absolute() or not home.is_dir():
            raise WorkerError("Codex subscription profile must be an existing absolute directory")
        if os.name == "posix" and (home.stat().st_mode & 0o077):
            raise WorkerError("Codex subscription profile must be private (mode 0700)")
        if home == (Path.home() / ".codex").resolve():
            raise WorkerError("Phase-D requires a dedicated non-default Codex home")
        if (home / "auth.json").exists():
            raise WorkerError("auth.json is forbidden; use keyring-backed Codex authentication")
        if (home / "config.toml").exists():
            raise WorkerError("ambient config.toml is forbidden for benchmark execution")
        skills = home / "skills"
        if skills.is_dir():
            unexpected = [child.name for child in skills.iterdir() if child.name != ".system"]
            if unexpected:
                raise WorkerError("user-installed Codex skills are forbidden for benchmark execution")
        admin_skills = Path("/etc/codex/skills")
        if os.name == "posix" and admin_skills.is_dir():
            try:
                has_admin_skills = any(admin_skills.iterdir())
            except OSError as exc:
                raise WorkerError("cannot verify absence of ambient administrator Codex skills") from exc
            if has_admin_skills:
                raise WorkerError("ambient administrator Codex skills are forbidden for benchmark execution")

    def probe_version(self) -> str:
        run = subprocess.run(
            [self.codex, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=15,
            env={"LC_ALL": "C", "LANG": "C", "PATH": os.environ.get("PATH", os.defpath)},
        )
        match = CODEX_VERSION_RE.search((run.stdout + "\n" + run.stderr).strip())
        if run.returncode != 0 or match is None:
            raise WorkerError("cannot determine Codex CLI version")
        return match.group("version")

    def identity(self) -> dict[str, object]:
        return {
            "execution_venue": "subscription_agent",
            "provider": "openai",
            "model": self.model,
            "reasoning_effort": self.reasoning_effort,
            "codex_version": self.probe_version(),
            "endpoint_profile": "openai_codex_subscription",
            "auth_store": "keyring",
            "per_token_api_billing": False,
            "api_key_used": False,
        }


class CodexSubscriptionRunner:
    def __init__(self, config: CodexSubscriptionConfig, scratch: Path) -> None:
        self.config = config
        self.scratch = scratch
        self.calls: list[dict[str, object]] = []
        self._counter = 0

    def _env(self, call_dir: Path) -> dict[str, str]:
        home = call_dir / "home"
        home.mkdir(mode=0o700, exist_ok=True)
        env = {
            "LC_ALL": "C.UTF-8",
            "LANG": "C.UTF-8",
            "PATH": os.defpath,
            "HOME": str(home),
            "CODEX_HOME": str(self.config.codex_home.resolve()),
            "TMPDIR": str(call_dir),
            "TERM": "dumb",
        }
        for key in ("DBUS_SESSION_BUS_ADDRESS", "XDG_RUNTIME_DIR", "SSL_CERT_FILE", "SSL_CERT_DIR"):
            value = os.environ.get(key)
            if value:
                env[key] = value
        # Current subscription profile deliberately excludes API-key credentials and arbitrary CODEX_* variables.
        # Future metered/provider adapters must be explicit separate profiles; there is no fallback here.
        return env

    def _command(self, call_dir: Path, schema_path: Path, output_path: Path) -> list[str]:
        overrides = (
            f'model_reasoning_effort="{self.config.reasoning_effort}"',
            *_STATIC_CODEX_CONFIG_OVERRIDES,
        )
        return [
            self.config.codex,
            "exec",
            "--strict-config",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--sandbox",
            "read-only",
            "--skip-git-repo-check",
            "--model",
            self.config.model,
            "--output-schema",
            str(schema_path),
            "--output-last-message",
            str(output_path),
            "--cd",
            str(call_dir),
            "-c",
            f'cli_auth_credentials_store="{self.config.auth_store_mode}"',
            *[piece for override in overrides for piece in ("-c", override)],
            "-",
        ]

    def call(self, *, role: str, prompt: str, schema: Mapping[str, object]) -> dict[str, object]:
        self._counter += 1
        call_dir = self.scratch / f"call_{self._counter:04d}_{re.sub(r'[^a-z0-9_-]+', '_', role.lower())[:40]}"
        call_dir.mkdir(mode=0o700)
        schema_path = call_dir / "output-schema.json"
        output_path = call_dir / "result.json"
        schema_path.write_bytes(_canonical_json_bytes(schema))
        command = self._command(call_dir, schema_path, output_path)
        prompt_bytes = prompt.encode("utf-8")
        started = time.monotonic()
        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                cwd=call_dir,
                env=self._env(call_dir),
                start_new_session=(os.name == "posix"),
            )
        except OSError as exc:
            raise WorkerError("cannot execute Codex CLI") from exc
        try:
            _, stderr = process.communicate(prompt_bytes, timeout=self.config.call_timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            if os.name == "posix":
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            else:
                process.kill()
            process.communicate()
            raise WorkerError(f"Codex call timed out for role {role}") from exc
        duration_ms = round((time.monotonic() - started) * 1000.0, 3)
        if process.returncode != 0:
            diagnostic = stderr.decode("utf-8", errors="replace")[-4000:]
            raise WorkerError(f"Codex call failed for role {role}: {diagnostic}")
        if not output_path.is_file():
            raise WorkerError(f"Codex produced no structured output for role {role}")
        output_bytes = output_path.read_bytes()
        try:
            value = json.loads(output_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise WorkerError(f"Codex output was not valid JSON for role {role}") from exc
        if not isinstance(value, dict):
            raise WorkerError(f"Codex output must be an object for role {role}")
        self.calls.append(
            {
                "call_index": self._counter,
                "role": role,
                "prompt_sha256": _sha256_bytes(prompt_bytes),
                "prompt_bytes_egressed": len(prompt_bytes),
                "output_sha256": _sha256_bytes(output_bytes),
                "output_bytes": len(output_bytes),
                "duration_ms": duration_ms,
            }
        )
        return value

    def usage(self) -> dict[str, object]:
        return {
            "billing_mode": "chatgpt_subscription",
            "per_token_api_billing": False,
            "api_key_used": False,
            "subscription_codex_invocations": len(self.calls),
            "prompt_bytes_egressed": sum(int(item["prompt_bytes_egressed"]) for item in self.calls),
            "structured_output_bytes": sum(int(item["output_bytes"]) for item in self.calls),
            "token_usage": "not_exposed_by_certified_codex_cli_contract",
        }


def _simple_planner_prompt(base_prompt: str, schema: Mapping[str, object], max_sql_calls: int) -> str:
    return (
        "You are the planning stage of a bounded civic-record verifier.\n"
        "Use only the supplied relational schema and declared Source Authority. Do not use web knowledge.\n"
        "Propose zero or more read-only SQLite SELECT statements needed to evaluate the claim.\n"
        "Do not invent tables/columns. A tool failure is not evidence that the claim is false or unknowable.\n"
        f"At most {max_sql_calls} SQL statements are allowed.\n\n"
        f"CASE\n{base_prompt}\n"
        f"SCHEMA\n{json.dumps(schema, ensure_ascii=False, sort_keys=True)}\n"
    )


def _simple_final_prompt(base_prompt: str, events: Sequence[Mapping[str, object]]) -> str:
    return (
        "You are the final stage of a bounded civic-record verifier.\n"
        "Return supported only when the bounded evidence supports the exact proposition.\n"
        "Return contradicted only when bounded evidence contradicts it.\n"
        "Return insufficient_evidence when the declared authority/scope cannot decide the proposition.\n"
        "Execution failures or rejected SQL are not themselves evidence insufficiency.\n"
        "Cite only query IDs that actually produced evidence used in the verdict.\n\n"
        f"CASE\n{base_prompt}\n"
        f"EXECUTED QUERY EVENTS\n{_tool_results_text(events)}\n"
    )


def _thucy_wrapper(upstream_prompt: str, role_contract: str, payload: str) -> str:
    return (
        "UPSTREAM THUCY ROLE PROMPT (exact external text; do not reinterpret its provenance):\n"
        "--- BEGIN UPSTREAM PROMPT ---\n"
        f"{upstream_prompt}\n"
        "--- END UPSTREAM PROMPT ---\n\n"
        "CANARIO BENCHMARK RUNTIME ADAPTER:\n"
        f"{role_contract}\n"
        "The adapter changes runtime/tool protocol and bounded scheduling; the upstream role prompt above remains verbatim. "
        "Do not use web knowledge or any source not included below.\n\n"
        f"BOUNDED INPUT\n{payload}\n"
    )


def run_simple_case(
    *,
    runner: CodexSubscriptionRunner,
    base_prompt: str,
    projection_bytes: bytes,
    max_sql_calls: int,
) -> dict[str, object]:
    schema = _schema_for_projection(projection_bytes)
    plan_value = runner.call(
        role="simple_planner",
        prompt=_simple_planner_prompt(base_prompt, schema, max_sql_calls),
        schema=_planner_schema(max_sql_calls),
    )
    plan = _validate_plan(plan_value, max_sql_calls)
    events = _execute_plan(projection_bytes, plan)
    final = runner.call(
        role="simple_final",
        prompt=_simple_final_prompt(base_prompt, events),
        schema=_simple_final_schema(),
    )
    verdict = final.get("verdict")
    sufficiency = final.get("evidence_sufficiency")
    if verdict not in {"supported", "contradicted", "insufficient_evidence"}:
        raise WorkerError("simple verifier returned invalid verdict")
    if sufficiency not in {"adequate", "inadequate"}:
        raise WorkerError("simple verifier returned invalid sufficiency")
    return {
        "raw_verdict": verdict,
        "normalized_verdict": verdict,
        "explicit_sufficiency": True,
        "evidence_sufficiency": sufficiency,
        "report": str(final.get("reason", "")),
        "cited_query_ids": list(final.get("cited_query_ids", [])),
        "tool_events": events,
    }


def build_thucy_shared_context(
    *,
    runner: CodexSubscriptionRunner,
    prompts: Mapping[str, str],
    projection_bytes: bytes,
    authority: Mapping[str, object],
) -> dict[str, str]:
    inventory = _source_inventory(projection_bytes, authority)
    schema = _schema_for_projection(projection_bytes)
    data_value = runner.call(
        role="thucy_data_expert_setup",
        prompt=_thucy_wrapper(
            prompts["DATA_EXPERT_PROMPT"],
            "This is the one-time data-discovery tool invocation for the frozen projection campaign. Return DataReport.report only.",
            json.dumps(inventory, ensure_ascii=False, sort_keys=True),
        ),
        schema=_report_schema("report"),
    )
    schema_payload = {
        "context_hint": "single bounded Canario projection used by all campaign claims",
        "query": "Describe the complete relational schema available for bounded claim verification.",
        "actual_schema": schema,
    }
    schema_value = runner.call(
        role="thucy_schema_expert_setup",
        prompt=_thucy_wrapper(
            prompts["SCHEMA_EXPERT_PROMPT"],
            "This is the one-time schema tool invocation for the frozen projection campaign. The actual inspected schema is supplied below; return SchemaQueryAnswer.answer only.",
            json.dumps(schema_payload, ensure_ascii=False, sort_keys=True),
        ),
        schema=_report_schema("answer"),
    )
    return {"data_report": str(data_value["report"]), "schema_answer": str(schema_value["answer"])}


def run_thucy_case(
    *,
    runner: CodexSubscriptionRunner,
    prompts: Mapping[str, str],
    shared: Mapping[str, str],
    base_prompt: str,
    projection_bytes: bytes,
    max_sql_calls: int,
) -> dict[str, object]:
    sql_plan_payload = {
        "claim": base_prompt,
        "schema_info": shared["schema_answer"],
        "max_sql_calls": max_sql_calls,
    }
    plan_value = runner.call(
        role="thucy_sql_expert_plan",
        prompt=_thucy_wrapper(
            prompts["SQL_EXPERT_PROMPT"],
            "The native SQL tool is replaced by a bounded planner/executor loop. At this planning stage return only the SQL statements you need; they will be executed exactly by hardened SQLite and returned to you. Do not claim they ran yet.",
            json.dumps(sql_plan_payload, ensure_ascii=False, sort_keys=True),
        ),
        schema=_planner_schema(max_sql_calls),
    )
    plan = _validate_plan(plan_value, max_sql_calls)
    events = _execute_plan(projection_bytes, plan)
    synth_payload = {
        "claim": base_prompt,
        "schema_info": shared["schema_answer"],
        "executed_query_events": events,
    }
    sql_answer = runner.call(
        role="thucy_sql_expert_synthesis",
        prompt=_thucy_wrapper(
            prompts["SQL_EXPERT_PROMPT"],
            "These are the exact results of your bounded SQL tool calls. Produce the upstream NLQueryAnswer.answer. Include only SQL statements that actually executed successfully and directly support your answer; rejected/failed statements must not be presented as evidence.",
            json.dumps(synth_payload, ensure_ascii=False, sort_keys=True),
        ),
        schema=_report_schema("answer"),
    )
    lead_payload = {
        "user_query": base_prompt,
        "discover_data_sources_tool": {"report": shared["data_report"]},
        "schema_query_tool": {"answer": shared["schema_answer"]},
        "nl_query_tool": {"answer": str(sql_answer["answer"])},
        "runtime_note": "The three bounded tool outputs above are the only accessible evidence in this adapted run.",
    }
    final = runner.call(
        role="thucy_lead_verifier",
        prompt=_thucy_wrapper(
            prompts["VERIFIER_PROMPT"],
            "The bounded runtime has already completed the exact three tool roles and supplies their outputs below. Return the upstream VerificationAnswer fields report and verdict. No further tools or sources are available.",
            json.dumps(lead_payload, ensure_ascii=False, sort_keys=True),
        ),
        schema=_thucy_verifier_schema(),
    )
    raw = str(final.get("verdict"))
    mapping = {
        "VERIFIED": "supported",
        "CONTRADICTED": "contradicted",
        "NOT ENOUGH INFO": "insufficient_evidence",
        "PARTLY VERIFIED": "mixed_or_partial",
        "PARTLY CONTRADICTED": "mixed_or_partial",
    }
    if raw not in mapping:
        raise WorkerError("Thucy-adapted verifier returned invalid verdict")
    return {
        "raw_verdict": raw,
        "normalized_verdict": mapping[raw],
        "explicit_sufficiency": False,
        "evidence_sufficiency": None,
        "report": str(final.get("report", "")),
        "sql_expert_answer": str(sql_answer["answer"]),
        "tool_events": events,
    }


def _base_result(*, system: str | None, case_id: str | None) -> dict[str, object]:
    return {"format": RESULT_FORMAT, "system": system, "case_id": case_id}


def _config_from_request(request: Mapping[str, object]) -> CodexSubscriptionConfig:
    requested_executable = str(request.get("codex") or "codex")
    executable = shutil.which(requested_executable)
    if not executable:
        raise WorkerError("Codex CLI is unavailable")
    executable = str(Path(executable).resolve())
    home = request.get("codex_home")
    if not isinstance(home, str) or not home:
        raise WorkerError("codex_home is required")
    model = str(request.get("model", "gpt-5.6-terra"))
    reasoning_effort = str(request.get("reasoning_effort", "medium"))
    versions = request.get("qualified_codex_versions", ["0.149.0"])
    if not isinstance(versions, list) or not versions or not all(isinstance(item, str) for item in versions):
        raise WorkerError("qualified_codex_versions malformed")
    return CodexSubscriptionConfig(
        codex=executable,
        codex_home=Path(home),
        model=model,
        reasoning_effort=reasoning_effort,
        qualified_versions=tuple(versions),
    )


def run_request(request: Mapping[str, object]) -> dict[str, object]:
    mode = request.get("mode")
    system = str(request.get("system")) if request.get("system") is not None else None
    case_id = str(request.get("case_id")) if request.get("case_id") is not None else None
    started = time.monotonic()
    try:
        config = _config_from_request(request)
    except Exception as exc:
        return {
            **_base_result(system=system, case_id=case_id),
            "status": "execution_failed",
            "error_code": "subscription_profile_unavailable",
            "error": f"{type(exc).__name__}: {exc}",
            "requested_provider": {
                "execution_venue": "subscription_agent",
                "provider": "openai",
                "model": request.get("model", "gpt-5.6-terra"),
                "reasoning_effort": request.get("reasoning_effort", "medium"),
                "per_token_api_billing": False,
                "api_key_used": False,
            },
            "usage": {
                "billing_mode": "chatgpt_subscription",
                "per_token_api_billing": False,
                "api_key_used": False,
                "subscription_codex_invocations": 0,
                "prompt_bytes_egressed": 0,
                "structured_output_bytes": 0,
                "token_usage": "not_exposed_by_certified_codex_cli_contract",
            },
            "model_calls": [],
            "duration_ms": round((time.monotonic() - started) * 1000.0, 3),
        }
    with tempfile.TemporaryDirectory(prefix="canario-phase-d-codex-") as tempdir:
        scratch = Path(tempdir)
        runner = CodexSubscriptionRunner(config, scratch)
        try:
            if mode == "probe":
                probe = runner.call(
                    role="provider_probe",
                    prompt=(
                        "This is a bounded non-semantic provider capability probe. Return ok=true and a short message. "
                        "Do not use tools, shell, web, files, or outside context."
                    ),
                    schema=_probe_schema(),
                )
                completed = probe.get("ok") is True
                return {
                    **_base_result(system=system, case_id=case_id),
                    "status": "completed" if completed else "execution_failed",
                    "probe_pass": completed,
                    "provider": config.identity(),
                    "usage": runner.usage(),
                    "model_calls": runner.calls,
                    "duration_ms": round((time.monotonic() - started) * 1000.0, 3),
                }

            projection_path = request.get("projection_path")
            if not isinstance(projection_path, str):
                raise WorkerError("projection_path is required")
            projection_bytes = Path(projection_path).read_bytes()
            expected_projection = request.get("projection_sha256")
            if expected_projection != _sha256_bytes(projection_bytes):
                raise WorkerError("projection identity mismatch")
            max_sql_calls = int(request.get("max_sql_calls", 6))
            if max_sql_calls <= 0 or max_sql_calls > 12:
                raise WorkerError("max_sql_calls outside bounded range")
            if system == "simple_codex":
                base_prompt = request.get("prompt")
                if not isinstance(base_prompt, str) or not base_prompt:
                    raise WorkerError("case prompt is required")
                result = run_simple_case(
                    runner=runner,
                    base_prompt=base_prompt,
                    projection_bytes=projection_bytes,
                    max_sql_calls=max_sql_calls,
                )
                thucy_prompt_hashes: dict[str, str] = {}
            elif system == "thucy_bounded_codex_runtime_adapted":
                base_prompt = request.get("prompt")
                if not isinstance(base_prompt, str) or not base_prompt:
                    raise WorkerError("case prompt is required")
                thucy_root = request.get("thucy_root")
                if not isinstance(thucy_root, str):
                    raise WorkerError("thucy_root is required for Thucy-adapted execution")
                prompts = extract_thucy_prompts(Path(thucy_root))
                thucy_prompt_hashes = {name: _sha256_text(text) for name, text in prompts.items()}
                shared = request.get("thucy_shared_context")
                if not isinstance(shared, dict) or not all(isinstance(shared.get(k), str) for k in ("data_report", "schema_answer")):
                    raise WorkerError("Thucy shared context missing")
                result = run_thucy_case(
                    runner=runner,
                    prompts=prompts,
                    shared={"data_report": str(shared["data_report"]), "schema_answer": str(shared["schema_answer"])},
                    base_prompt=base_prompt,
                    projection_bytes=projection_bytes,
                    max_sql_calls=max_sql_calls,
                )
            elif system == "thucy_setup_codex":
                thucy_root = request.get("thucy_root")
                authority = request.get("source_authority")
                if not isinstance(thucy_root, str) or not isinstance(authority, dict):
                    raise WorkerError("Thucy setup requires checkout and Source Authority")
                prompts = extract_thucy_prompts(Path(thucy_root))
                thucy_prompt_hashes = {name: _sha256_text(text) for name, text in prompts.items()}
                shared_context = build_thucy_shared_context(
                    runner=runner,
                    prompts=prompts,
                    projection_bytes=projection_bytes,
                    authority=authority,
                )
                return {
                    **_base_result(system=system, case_id=case_id),
                    "status": "completed",
                    "provider": config.identity(),
                    "thucy_prompt_hashes": thucy_prompt_hashes,
                    "shared_context": shared_context,
                    "usage": runner.usage(),
                    "model_calls": runner.calls,
                    "duration_ms": round((time.monotonic() - started) * 1000.0, 3),
                }
            else:
                raise WorkerError(f"unknown system {system!r}")

            events = result.get("tool_events", [])
            rejected = sum(
                1
                for event in events
                if isinstance(event, dict) and event.get("tool") == "execute_sql" and event.get("outcome") == "rejected"
            )
            failed = sum(
                1
                for event in events
                if isinstance(event, dict) and event.get("tool") == "execute_sql" and event.get("outcome") == "execution_failed"
            )
            return {
                **_base_result(system=system, case_id=case_id),
                "status": "completed",
                **result,
                "tool_call_count": len(events),
                "tool_rejection_count": rejected,
                "tool_execution_failure_count": failed,
                "provider": config.identity(),
                "thucy_prompt_hashes": thucy_prompt_hashes,
                "usage": runner.usage(),
                "model_calls": runner.calls,
                "duration_ms": round((time.monotonic() - started) * 1000.0, 3),
            }
        except Exception as exc:
            return {
                **_base_result(system=system, case_id=case_id),
                "status": "execution_failed",
                "error_code": "worker_contract_or_executor_failure",
                "error": f"{type(exc).__name__}: {exc}",
                "provider": config.identity(),
                "usage": runner.usage(),
                "model_calls": runner.calls,
                "duration_ms": round((time.monotonic() - started) * 1000.0, 3),
            }


def main() -> int:
    try:
        request = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"CANARIO_PHASE_D_WORKER_ERROR: invalid request JSON: {exc}")
    if not isinstance(request, dict):
        raise SystemExit("CANARIO_PHASE_D_WORKER_ERROR: request must be an object")
    result = run_request(request)
    sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
