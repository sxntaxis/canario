"""Minimum Canario-native structured planner/verifier orchestration.

One VerificationRun owns the model-backed planning + final judgment attempt. Every SQL
program proposed by the planner is executed as its own ordinary local DerivationRun through
``StructuredSQLiteDerivationBackend``. The final persisted Verification marks exactly the
query results cited by the final model as ``consumed``; every other invoked Derivation remains
``attempted``.

This preserves Phase-D's useful decomposition without introducing product role classes,
a multi-agent runtime, hidden SQL execution, or a second persistence graph.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Protocol, Sequence, runtime_checkable

from canario.deposit.ids import new_id, utc_now, validate_id
from canario.processors.contracts import EgressAuthorization, require_nonempty, require_token

from .contracts import (
    DerivationDescriptor,
    DerivationExecutionResult,
    DerivationInvocation,
    VerificationDerivationStep,
    VerificationDescriptor,
    VerificationEvidenceDraft,
    VerificationExecutionResult,
    VerificationRequest,
)
from .host import ReasoningHost
from .structured_sqlite import StructuredSQLiteDerivationBackend, structured_table_schema_summary
from .writer import DerivationReceipt, ReasoningInvariantError, VerificationReceipt

_QUERY_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_CODEX_VERSION_RE = re.compile(
    r"(?:codex-cli|OpenAI Codex v?)\s*(?P<version>[0-9]+(?:\.[0-9]+){2,3})", re.I
)
_MAX_PROMPT_BYTES = 4 * 1024 * 1024
_MAX_REASON = 16 * 1024
_PLANNER_PROMPT_VERSION = "structured_verifier_planner_v1"
_FINAL_PROMPT_VERSION = "structured_verifier_final_v1"
_EXEC_POLICY_VERSION = "structured_verifier_codex_exec_v1"
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

_PLANNER_PROMPT = """You are the bounded SQL planning stage of Canario verification.
Use only the proposition, Source Authority, and deterministic structured-table schema supplied below.
Do not answer the proposition. Do not use outside knowledge, web, shell, files, tools, or hidden data.
Return zero to the stated maximum number of independent read-only SQLite SELECT statements that would
materially help a final verifier decide the proposition. Every SQL statement will be executed by a
separate hardened Canario DerivationRun. Prefer the smallest evidence-producing query set. Do not emit
PRAGMA, EXPLAIN, writes, DDL, ATTACH, subprograms, or comments. Return only data valid under the schema.
"""

_FINAL_PROMPT = """You are the final bounded Canario verifier.
Use only the proposition, Source Authority, and exact executed Derivation events supplied below.
Do not use outside knowledge, web, shell, files, tools, or hidden data. Failed/rejected queries are
technical execution facts, not civic evidence. A supported or contradicted verdict requires at least
one cited successful query whose result is source-backed. Cite only query IDs whose exact results
materially influenced your judgment. If the bounded Source Authority cannot justify the proposition,
return insufficient_evidence even if a source-independent constant happens to match the claim.
Return an explicit evidence-sufficiency axis and only data valid under the schema.
"""


class StructuredVerifierError(RuntimeError):
    """The structured planner/verifier orchestration cannot proceed honestly."""


class StructuredVerifierContractError(StructuredVerifierError):
    """A bounded orchestration contract failed with a durable diagnostic code."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        egress_bytes: int = 0,
        invocations: int = 0,
    ) -> None:
        super().__init__(message)
        require_token(code, "structured verifier contract error code")
        self.code = code
        self.egress_bytes = egress_bytes
        self.invocations = invocations


class StructuredVerifierProviderError(StructuredVerifierError):
    """The qualified model execution profile failed technically."""

    def __init__(self, code: str, *, egress_bytes: int = 0, invocations: int = 0) -> None:
        super().__init__(code)
        self.code = code
        self.egress_bytes = egress_bytes
        self.invocations = invocations


@dataclass(frozen=True, slots=True)
class PlannedStructuredQuery:
    query_id: str
    purpose: str
    sql: str

    def __post_init__(self) -> None:
        if not _QUERY_ID_RE.fullmatch(self.query_id):
            raise ValueError("planned query id is malformed")
        require_nonempty(self.purpose, "planned query purpose")
        require_nonempty(self.sql, "planned SQL")
        if len(self.purpose) > 2048 or len(self.sql) > 64 * 1024:
            raise ValueError("planned query exceeds bounded text limits")


@dataclass(frozen=True, slots=True)
class StructuredPlannerCall:
    queries: tuple[PlannedStructuredQuery, ...]
    prompt_bytes_egressed: int

    def __post_init__(self) -> None:
        if not isinstance(self.queries, tuple) or not all(
            isinstance(item, PlannedStructuredQuery) for item in self.queries
        ):
            raise TypeError("planner queries must be PlannedStructuredQuery values")
        ids = [item.query_id for item in self.queries]
        if len(ids) != len(set(ids)):
            raise ValueError("planner query IDs cannot repeat")
        _nonnegative_int(self.prompt_bytes_egressed, "planner prompt bytes")


@dataclass(frozen=True, slots=True)
class StructuredFinalDecision:
    verdict: str
    evidence_sufficiency: str
    cited_query_ids: tuple[str, ...]
    reason: str
    prompt_bytes_egressed: int
    abstention_reason_code: str | None = None

    def __post_init__(self) -> None:
        if self.verdict not in {"supported", "contradicted", "insufficient_evidence"}:
            raise ValueError("unknown final verifier verdict")
        if self.evidence_sufficiency not in {"adequate", "inadequate"}:
            raise ValueError("unknown evidence sufficiency")
        if not isinstance(self.cited_query_ids, tuple):
            raise TypeError("cited_query_ids must be a tuple")
        if len(self.cited_query_ids) != len(set(self.cited_query_ids)):
            raise ValueError("final verifier cannot cite one query twice")
        for query_id in self.cited_query_ids:
            if not _QUERY_ID_RE.fullmatch(query_id):
                raise ValueError("cited query id is malformed")
        require_nonempty(self.reason, "final verifier reason")
        if len(self.reason) > _MAX_REASON:
            raise ValueError("final verifier reason exceeds bounded limit")
        _nonnegative_int(self.prompt_bytes_egressed, "final prompt bytes")
        if self.verdict in {"supported", "contradicted"}:
            if self.evidence_sufficiency != "adequate":
                raise ValueError("supported/contradicted require adequate evidence")
            if not self.cited_query_ids:
                raise ValueError("supported/contradicted require cited evidence queries")
            if self.abstention_reason_code is not None:
                raise ValueError("supported/contradicted cannot carry abstention reason")
        else:
            if self.evidence_sufficiency != "inadequate":
                raise ValueError("insufficient_evidence requires inadequate evidence")
            if self.abstention_reason_code is None:
                raise ValueError("insufficient_evidence requires abstention reason")
            require_token(self.abstention_reason_code, "abstention reason code")


@dataclass(frozen=True, slots=True)
class StructuredVerificationRequest:
    proposition_text: str
    scope_target_id: str
    authority_scope_ids: tuple[str, ...]
    egress: EgressAuthorization
    max_queries: int = 6
    verification_run_id: str = field(default_factory=lambda: new_id("vrun_"))
    derivation_run_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        require_nonempty(self.proposition_text, "structured verification proposition")
        if len(self.proposition_text) > 64 * 1024:
            raise ValueError("structured verification proposition exceeds bounded limit")
        validate_id(self.scope_target_id, "rtgt_")
        if not isinstance(self.authority_scope_ids, tuple) or not self.authority_scope_ids:
            raise ValueError("structured verification requires Source Authority")
        if len(self.authority_scope_ids) != len(set(self.authority_scope_ids)):
            raise ValueError("Source Authority scope IDs cannot repeat")
        for value in self.authority_scope_ids:
            validate_id(value, "sas_")
        if isinstance(self.max_queries, bool) or not isinstance(self.max_queries, int):
            raise TypeError("max_queries must be integer")
        if not 1 <= self.max_queries <= 6:
            raise ValueError("structured verifier permits 1..6 planned queries")
        validate_id(self.verification_run_id, "vrun_")
        if not isinstance(self.derivation_run_ids, tuple):
            raise TypeError("derivation_run_ids must be a tuple")
        if not self.derivation_run_ids:
            object.__setattr__(
                self,
                "derivation_run_ids",
                tuple(new_id("drun_") for _ in range(self.max_queries)),
            )
        if len(self.derivation_run_ids) != self.max_queries:
            raise ValueError("derivation_run_ids must preallocate exactly max_queries IDs")
        if len(self.derivation_run_ids) != len(set(self.derivation_run_ids)):
            raise ValueError("preallocated DerivationRun IDs cannot repeat")
        for value in self.derivation_run_ids:
            validate_id(value, "drun_")


@dataclass(frozen=True, slots=True)
class StructuredVerificationReceipt:
    verification: VerificationReceipt
    derivations: tuple[DerivationReceipt, ...]
    planned_query_ids: tuple[str, ...]
    consumed_query_ids: tuple[str, ...]
    codex_invocations: int
    prompt_bytes_egressed: int


@runtime_checkable
class StructuredVerifierModel(Protocol):
    @property
    def descriptor(self) -> VerificationDescriptor:
        ...

    @property
    def configuration_hash(self) -> str:
        ...

    @property
    def request_template_hash(self) -> str:
        ...

    @property
    def endpoint_profile(self) -> str:
        ...

    def plan(
        self,
        *,
        proposition_text: str,
        source_authority: Sequence[Mapping[str, object]],
        schema: Mapping[str, object],
        max_queries: int,
    ) -> StructuredPlannerCall:
        ...

    def finalize(
        self,
        *,
        proposition_text: str,
        source_authority: Sequence[Mapping[str, object]],
        events: Sequence[Mapping[str, object]],
    ) -> StructuredFinalDecision:
        ...


class StructuredVerifierOrchestrator:
    """Execute the minimum Phase-D decomposition through production persistence."""

    def __init__(
        self,
        host: ReasoningHost,
        sqlite_backend: StructuredSQLiteDerivationBackend,
        model: StructuredVerifierModel,
    ) -> None:
        self.host = host
        self.writer = host.writer
        self.sqlite_backend = sqlite_backend
        self.model = model

    def run(self, request: StructuredVerificationRequest) -> StructuredVerificationReceipt:
        started_at = utc_now()
        total_egress = 0
        derivation_receipts: list[DerivationReceipt] = []
        planned: tuple[PlannedStructuredQuery, ...] = ()

        # Preflight the exact source/authority/egress boundary before any model call.
        if request.egress.request_template_hash != self.model.request_template_hash:
            raise ReasoningInvariantError("structured verifier egress template authorization mismatch")
        if request.egress.endpoint_profile != self.model.endpoint_profile:
            raise ReasoningInvariantError("structured verifier egress endpoint authorization mismatch")
        preflight = self._verification_request(request, ())
        preflight_invocation = self.writer.load_verification_invocation(preflight)
        self.writer.validate_verification_before_invocation(
            preflight, self.model.descriptor, preflight_invocation
        )
        schema = structured_table_schema_summary(preflight_invocation.scopes[0].material_bytes)
        authority = self._authority_payload(preflight_invocation.authority_scopes)

        planner_returned = False
        try:
            plan_call = self.model.plan(
                proposition_text=request.proposition_text,
                source_authority=authority,
                schema=schema,
                max_queries=request.max_queries,
            )
            total_egress += plan_call.prompt_bytes_egressed
            planner_returned = True
            if len(plan_call.queries) > request.max_queries:
                raise StructuredVerifierContractError("planner_query_budget_exceeded", "planner exceeded query budget")
            planned = plan_call.queries
        except StructuredVerifierProviderError as exc:
            total_egress += exc.egress_bytes
            return self._persist_failed(
                request,
                (),
                started_at,
                exc.code,
                total_egress,
                derivation_receipts,
                (),
                exc.invocations,
            )
        except StructuredVerifierContractError as exc:
            total_egress += exc.egress_bytes
            return self._persist_failed(
                request,
                (),
                started_at,
                exc.code,
                total_egress,
                derivation_receipts,
                (),
                exc.invocations or (1 if planner_returned else 0),
            )
        except (TypeError, ValueError):
            return self._persist_failed(
                request,
                (),
                started_at,
                "planner_output_contract_invalid",
                total_egress,
                derivation_receipts,
                (),
                1,
            )

        for ordinal, query in enumerate(planned):
            base_request = self.sqlite_backend.request((request.scope_target_id,), query.sql)
            derivation_request = type(base_request)(
                base_request.input_target_ids,
                base_request.operation_kind,
                base_request.program_kind,
                base_request.program_text,
                base_request.configuration_hash,
                base_request.egress,
                request.derivation_run_ids[ordinal],
            )
            derivation_receipts.append(
                self.host.run_derivation(derivation_request, self.sqlite_backend)
            )

        context_steps = self._context_steps(derivation_receipts)
        context_request = self._verification_request(request, context_steps)
        context_invocation = self.writer.load_verification_invocation(context_request)
        self.writer.validate_verification_before_invocation(
            context_request, self.model.descriptor, context_invocation
        )
        events = self._events(planned, context_invocation.derivations)

        final_returned = False
        try:
            decision = self.model.finalize(
                proposition_text=request.proposition_text,
                source_authority=authority,
                events=events,
            )
            total_egress += decision.prompt_bytes_egressed
            final_returned = True
            result, final_steps = self._decision_result(decision, planned, context_invocation.derivations)
        except StructuredVerifierProviderError as exc:
            total_egress += exc.egress_bytes
            return self._persist_failed(
                request,
                tuple(
                    VerificationDerivationStep(receipt.derivation_run_id, "attempted")
                    for receipt in derivation_receipts
                ),
                started_at,
                exc.code,
                total_egress,
                derivation_receipts,
                tuple(item.query_id for item in planned),
                1 + exc.invocations,
            )
        except StructuredVerifierContractError as exc:
            total_egress += exc.egress_bytes
            return self._persist_failed(
                request,
                tuple(
                    VerificationDerivationStep(receipt.derivation_run_id, "attempted")
                    for receipt in derivation_receipts
                ),
                started_at,
                exc.code,
                total_egress,
                derivation_receipts,
                tuple(item.query_id for item in planned),
                1 + (exc.invocations or (1 if final_returned else 0)),
            )
        except (TypeError, ValueError):
            return self._persist_failed(
                request,
                tuple(
                    VerificationDerivationStep(receipt.derivation_run_id, "attempted")
                    for receipt in derivation_receipts
                ),
                started_at,
                "final_output_contract_invalid",
                total_egress,
                derivation_receipts,
                tuple(item.query_id for item in planned),
                2,
            )

        final_request = self._verification_request(request, final_steps)
        final_invocation = self.writer.load_verification_invocation(final_request)
        finished_at = utc_now()
        result = VerificationExecutionResult(
            result.outcome,
            result.verdict,
            result.sufficiency_state,
            result.sufficiency_profile_key,
            result.sufficiency_profile_version,
            result.sufficiency_payload_json,
            result.abstention_reason_code,
            result.evidence,
            result.error_code,
            total_egress,
        )
        verification = self.writer.record_verification_attempt(
            request=final_request,
            descriptor=self.model.descriptor,
            invocation=final_invocation,
            result=result,
            started_at=started_at,
            finished_at=finished_at,
        )
        return StructuredVerificationReceipt(
            verification,
            tuple(derivation_receipts),
            tuple(item.query_id for item in planned),
            tuple(decision.cited_query_ids),
            2,
            total_egress,
        )

    def _persist_failed(
        self,
        request: StructuredVerificationRequest,
        steps: tuple[VerificationDerivationStep, ...],
        started_at: str,
        code: str,
        egress_bytes: int,
        derivations: Sequence[DerivationReceipt],
        planned_ids: tuple[str, ...],
        model_calls: int,
    ) -> StructuredVerificationReceipt:
        final_request = self._verification_request(request, steps)
        invocation = self.writer.load_verification_invocation(final_request)
        result = VerificationExecutionResult(
            "failed", error_code=code, egress_bytes=egress_bytes
        )
        verification = self.writer.record_verification_attempt(
            request=final_request,
            descriptor=self.model.descriptor,
            invocation=invocation,
            result=result,
            started_at=started_at,
            finished_at=utc_now(),
        )
        return StructuredVerificationReceipt(
            verification,
            tuple(derivations),
            planned_ids,
            (),
            model_calls,
            egress_bytes,
        )

    def _verification_request(
        self,
        request: StructuredVerificationRequest,
        steps: tuple[VerificationDerivationStep, ...],
    ) -> VerificationRequest:
        return VerificationRequest(
            request.proposition_text,
            (request.scope_target_id,),
            request.authority_scope_ids,
            "explicit_targets",
            "v1",
            "{}",
            steps,
            None,
            self._configuration_hash(request),
            request.egress,
            request.verification_run_id,
        )

    def _configuration_hash(self, request: StructuredVerificationRequest) -> str:
        payload = {
            "format": "canario.structured_verifier_orchestration.v1",
            "model_configuration_hash": self.model.configuration_hash,
            "sqlite_configuration_hash": self.sqlite_backend.policy.configuration_hash,
            "max_queries": request.max_queries,
        }
        return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()

    @staticmethod
    def _context_steps(
        receipts: Sequence[DerivationReceipt],
    ) -> tuple[VerificationDerivationStep, ...]:
        steps: list[VerificationDerivationStep] = []
        for receipt in receipts:
            if receipt.outcome == "success" and len(receipt.targets) == 1:
                steps.append(
                    VerificationDerivationStep(
                        receipt.derivation_run_id, "consumed", receipt.targets[0].id
                    )
                )
            else:
                steps.append(VerificationDerivationStep(receipt.derivation_run_id, "attempted"))
        return tuple(steps)

    @staticmethod
    def _events(
        queries: Sequence[PlannedStructuredQuery], derivations: Sequence[object]
    ) -> tuple[dict[str, object], ...]:
        if len(queries) != len(derivations):
            raise StructuredVerifierContractError("query_derivation_cardinality_mismatch", "query/Derivation cardinality mismatch")
        events: list[dict[str, object]] = []
        for query, step in zip(queries, derivations, strict=True):
            event: dict[str, object] = {
                "query_id": query.query_id,
                "purpose": query.purpose,
                "sql": query.sql,
                "outcome": step.outcome,
                "error_code": step.error_code,
                "program_sha256": step.program_sha256,
            }
            result = step.consumed_result
            if result is not None:
                try:
                    payload = json.loads(result.material_bytes.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise StructuredVerifierContractError("persisted_query_result_malformed", "malformed persisted query result") from exc
                event.update(
                    {
                        "result": payload,
                        "lineage_state": result.lineage_state,
                        "source_target_ids": list(result.source_target_ids),
                    }
                )
            events.append(event)
        return tuple(events)

    @staticmethod
    def _authority_payload(authority: Sequence[object]) -> tuple[dict[str, object], ...]:
        return tuple(
            {
                "source_id": item.source_id,
                "scope_kind": item.scope_kind,
                "valid_from": item.valid_from,
                "valid_to": item.valid_to,
                "note": item.note,
            }
            for item in authority
        )

    @staticmethod
    def _decision_result(
        decision: StructuredFinalDecision,
        queries: Sequence[PlannedStructuredQuery],
        derivations: Sequence[object],
    ) -> tuple[VerificationExecutionResult, tuple[VerificationDerivationStep, ...]]:
        by_id = {query.query_id: (query, step) for query, step in zip(queries, derivations, strict=True)}
        unknown = set(decision.cited_query_ids) - set(by_id)
        if unknown:
            raise StructuredVerifierContractError("final_unknown_query_citation", "final verifier cited unknown query IDs")
        cited = set(decision.cited_query_ids)
        steps: list[VerificationDerivationStep] = []
        source_targets: set[str] = set()
        for query in queries:
            _query, step = by_id[query.query_id]
            if query.query_id in cited:
                result = step.consumed_result
                if step.outcome != "success" or result is None:
                    raise StructuredVerifierContractError("final_unsuccessful_query_citation", "final verifier cited unsuccessful query")
                steps.append(
                    VerificationDerivationStep(
                        step.derivation_run_id, "consumed", result.result_target_id
                    )
                )
                if result.lineage_state in {"exact", "partial"}:
                    source_targets.update(result.source_target_ids)
            else:
                steps.append(VerificationDerivationStep(step.derivation_run_id, "attempted"))

        if decision.verdict in {"supported", "contradicted"} and not source_targets:
            raise StructuredVerifierContractError(
                "final_evidence_not_source_backed",
                "evidence-backed verdict requires cited source-backed Derivation",
            )
        evidence_role = "supports" if decision.verdict == "supported" else "challenges"
        evidence = (
            tuple(
                VerificationEvidenceDraft(0, target_id, evidence_role)
                for target_id in sorted(source_targets)
            )
            if decision.verdict in {"supported", "contradicted"}
            else ()
        )
        return (
            VerificationExecutionResult(
                "completed",
                verdict=decision.verdict,
                sufficiency_state=(
                    "sufficient" if decision.evidence_sufficiency == "adequate" else "insufficient"
                ),
                sufficiency_profile_key="explicit",
                sufficiency_profile_version="v1",
                sufficiency_payload_json="{}",
                abstention_reason_code=decision.abstention_reason_code,
                evidence=evidence,
            ),
            tuple(steps),
        )


@dataclass(frozen=True, slots=True)
class CodexStructuredVerifierConfig:
    codex: str
    codex_home: Path
    model: str = "gpt-5.6-terra"
    reasoning_effort: str = "medium"
    qualified_codex_versions: tuple[str, ...] = ("0.149.0",)
    call_timeout_seconds: int = 240
    auth_store_mode: str = "keyring"

    def __post_init__(self) -> None:
        if self.reasoning_effort not in {"none", "low", "medium", "high", "xhigh", "max"}:
            raise ValueError("unsupported reasoning effort")
        if self.auth_store_mode != "keyring":
            raise ValueError("structured verifier reference profile requires keyring auth")
        if not self.model or any(ch.isspace() for ch in self.model):
            raise ValueError("model must be one Codex model token")
        if not isinstance(self.qualified_codex_versions, tuple) or not self.qualified_codex_versions:
            raise ValueError("qualified Codex versions must be non-empty")
        if isinstance(self.call_timeout_seconds, bool) or self.call_timeout_seconds <= 0:
            raise ValueError("call_timeout_seconds must be positive")


class CodexStructuredVerifierModel:
    """Official Codex CLI reference adapter for the minimum two-call topology."""

    def __init__(self, config: CodexStructuredVerifierConfig) -> None:
        self.config = config
        self._codex = str(Path(config.codex).resolve())
        self._home = config.codex_home.expanduser().resolve()
        self._validate_home()
        self._version = self._probe_version()
        if self._version not in config.qualified_codex_versions:
            raise StructuredVerifierProviderError("codex_version_unqualified")
        self._descriptor = VerificationDescriptor(
            "codex.structured_planner_verifier",
            f"codex-cli-{self._version}+v1",
            "subscription_agent",
            True,
            "openai",
            config.model,
            1,
            16_000_000,
        )

    @classmethod
    def discover(
        cls,
        *,
        codex_home: str | Path,
        config: CodexStructuredVerifierConfig | None = None,
        codex: str = "codex",
    ) -> "CodexStructuredVerifierModel":
        executable = shutil.which(codex)
        if executable is None:
            raise StructuredVerifierProviderError("codex_unavailable")
        chosen = config or CodexStructuredVerifierConfig(executable, Path(codex_home))
        if config is not None and Path(config.codex).resolve() != Path(executable).resolve():
            chosen = CodexStructuredVerifierConfig(
                executable,
                Path(codex_home),
                config.model,
                config.reasoning_effort,
                config.qualified_codex_versions,
                config.call_timeout_seconds,
                config.auth_store_mode,
            )
        return cls(chosen)

    @property
    def descriptor(self) -> VerificationDescriptor:
        return self._descriptor

    @property
    def configuration_hash(self) -> str:
        payload = {
            "format": "canario.structured_codex_verifier_config.v1",
            "model": self.config.model,
            "reasoning_effort": self.config.reasoning_effort,
            "codex_version": self._version,
            "qualified_codex_versions": list(self.config.qualified_codex_versions),
            "auth_store": self.config.auth_store_mode,
            "call_timeout_seconds": self.config.call_timeout_seconds,
            "exec_policy": _EXEC_POLICY_VERSION,
            "planner_prompt_sha256": hashlib.sha256(_PLANNER_PROMPT.encode()).hexdigest(),
            "final_prompt_sha256": hashlib.sha256(_FINAL_PROMPT.encode()).hexdigest(),
            "planner_schema_max6_sha256": hashlib.sha256(
                _canonical_json_bytes(self._planner_schema(6))
            ).hexdigest(),
            "final_schema_sha256": hashlib.sha256(
                _canonical_json_bytes(self._final_schema())
            ).hexdigest(),
            "planner_prompt_version": _PLANNER_PROMPT_VERSION,
            "final_prompt_version": _FINAL_PROMPT_VERSION,
        }
        return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()

    @property
    def request_template_hash(self) -> str:
        return hashlib.sha256(
            (_PLANNER_PROMPT_VERSION + "\0" + _PLANNER_PROMPT + "\0" + _FINAL_PROMPT_VERSION + "\0" + _FINAL_PROMPT).encode("utf-8")
        ).hexdigest()

    @property
    def endpoint_profile(self) -> str:
        return "openai_codex_subscription"

    def plan(
        self,
        *,
        proposition_text: str,
        source_authority: Sequence[Mapping[str, object]],
        schema: Mapping[str, object],
        max_queries: int,
    ) -> StructuredPlannerCall:
        payload = {
            "proposition": proposition_text,
            "source_authority": list(source_authority),
            "schema": schema,
            "max_queries": max_queries,
        }
        value, prompt_bytes = self._call(
            "planner", _PLANNER_PROMPT + "\n\nBOUNDED INPUT\n" + _canonical_json(payload), self._planner_schema(max_queries)
        )
        try:
            raw = value.get("queries")
            if not isinstance(raw, list) or len(raw) > max_queries:
                raise ValueError("planner query list violates budget")
            queries: list[PlannedStructuredQuery] = []
            for item in raw:
                if not isinstance(item, dict) or set(item) != {"query_id", "purpose", "sql"}:
                    raise ValueError("planner query object malformed")
                queries.append(
                    PlannedStructuredQuery(str(item["query_id"]), str(item["purpose"]), str(item["sql"]))
                )
            return StructuredPlannerCall(tuple(queries), prompt_bytes)
        except (TypeError, ValueError) as exc:
            raise StructuredVerifierContractError(
                "planner_output_contract_invalid",
                "planner structured output violates contract",
                egress_bytes=prompt_bytes,
                invocations=1,
            ) from exc

    def finalize(
        self,
        *,
        proposition_text: str,
        source_authority: Sequence[Mapping[str, object]],
        events: Sequence[Mapping[str, object]],
    ) -> StructuredFinalDecision:
        payload = {
            "proposition": proposition_text,
            "source_authority": list(source_authority),
            "executed_derivations": list(events),
        }
        value, prompt_bytes = self._call(
            "final", _FINAL_PROMPT + "\n\nBOUNDED INPUT\n" + _canonical_json(payload), self._final_schema()
        )
        try:
            cited = value.get("cited_query_ids")
            if not isinstance(cited, list) or not all(isinstance(item, str) for item in cited):
                raise ValueError("final cited_query_ids malformed")
            abstention = value.get("abstention_reason_code")
            if abstention is not None and not isinstance(abstention, str):
                raise ValueError("abstention reason malformed")
            return StructuredFinalDecision(
                str(value.get("verdict")),
                str(value.get("evidence_sufficiency")),
                tuple(cited),
                str(value.get("reason", "")),
                prompt_bytes,
                abstention,
            )
        except (TypeError, ValueError) as exc:
            raise StructuredVerifierContractError(
                "final_output_contract_invalid",
                "final structured output violates contract",
                egress_bytes=prompt_bytes,
                invocations=1,
            ) from exc

    def _call(
        self, role: str, prompt: str, schema: Mapping[str, object]
    ) -> tuple[dict[str, object], int]:
        prompt_bytes = prompt.encode("utf-8")
        if len(prompt_bytes) > _MAX_PROMPT_BYTES:
            raise StructuredVerifierContractError("codex_prompt_too_large", "Codex prompt exceeds bounded byte limit")
        with tempfile.TemporaryDirectory(prefix=f"canario-structured-{role}-") as tempdir:
            call_dir = Path(tempdir)
            schema_path = call_dir / "output-schema.json"
            output_path = call_dir / "result.json"
            schema_path.write_bytes(_canonical_json_bytes(schema))
            command = self._command(call_dir, schema_path, output_path)
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
                raise StructuredVerifierProviderError("codex_unavailable") from exc
            try:
                _, stderr = process.communicate(
                    prompt_bytes, timeout=self.config.call_timeout_seconds
                )
            except subprocess.TimeoutExpired as exc:
                if os.name == "posix":
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                else:
                    process.kill()
                process.communicate()
                raise StructuredVerifierProviderError(
                    f"codex_{role}_timeout", egress_bytes=len(prompt_bytes), invocations=1
                ) from exc
            if process.returncode != 0:
                stderr_tail = stderr.decode("utf-8", errors="replace")[-4000:]
                stderr_lower = stderr_tail.lower()
                if "invalid_json_schema" in stderr_lower or "invalid schema for response_format" in stderr_lower:
                    code = f"codex_{role}_invalid_json_schema"
                else:
                    code = f"codex_{role}_failed"
                raise StructuredVerifierProviderError(
                    code, egress_bytes=len(prompt_bytes), invocations=1
                )
            if not output_path.is_file():
                raise StructuredVerifierProviderError(
                    f"codex_{role}_output_missing", egress_bytes=len(prompt_bytes), invocations=1
                )
            try:
                value = json.loads(output_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise StructuredVerifierContractError("codex_structured_output_invalid", "Codex structured output invalid", egress_bytes=len(prompt_bytes), invocations=1) from exc
            if not isinstance(value, dict):
                raise StructuredVerifierContractError("codex_output_not_object", "Codex output must be object", egress_bytes=len(prompt_bytes), invocations=1)
            return value, len(prompt_bytes)

    def _command(self, call_dir: Path, schema: Path, output: Path) -> list[str]:
        overrides = (
            f'model_reasoning_effort="{self.config.reasoning_effort}"',
            *_STATIC_CODEX_CONFIG_OVERRIDES,
        )
        return [
            self._codex,
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
            str(schema),
            "--output-last-message",
            str(output),
            "--cd",
            str(call_dir),
            "-c",
            f'cli_auth_credentials_store="{self.config.auth_store_mode}"',
            *[piece for override in overrides for piece in ("-c", override)],
            "-",
        ]

    def _env(self, call_dir: Path) -> dict[str, str]:
        home = call_dir / "home"
        home.mkdir(mode=0o700)
        env = {
            "LC_ALL": "C.UTF-8",
            "LANG": "C.UTF-8",
            "PATH": os.defpath,
            "HOME": str(home),
            "CODEX_HOME": str(self._home),
            "TMPDIR": str(call_dir),
            "TERM": "dumb",
        }
        for key in ("DBUS_SESSION_BUS_ADDRESS", "XDG_RUNTIME_DIR", "SSL_CERT_FILE", "SSL_CERT_DIR"):
            value = os.environ.get(key)
            if value:
                env[key] = value
        return env

    def _validate_home(self) -> None:
        if not self._home.is_absolute() or not self._home.is_dir():
            raise StructuredVerifierProviderError("codex_home_invalid")
        if os.name == "posix" and (self._home.stat().st_mode & 0o077):
            raise StructuredVerifierProviderError("codex_home_not_private")
        default = (Path.home() / ".codex").resolve()
        if self._home == default:
            raise StructuredVerifierProviderError("codex_home_must_be_dedicated")
        if (self._home / "auth.json").exists() or (self._home / "config.toml").exists():
            raise StructuredVerifierProviderError("codex_home_ambient_config_forbidden")
        skills = self._home / "skills"
        if skills.is_dir() and any(child.name != ".system" for child in skills.iterdir()):
            raise StructuredVerifierProviderError("codex_home_user_skills_forbidden")
        admin_skills = Path("/etc/codex/skills")
        if os.name == "posix" and admin_skills.is_dir():
            try:
                if any(admin_skills.iterdir()):
                    raise StructuredVerifierProviderError("codex_admin_skills_forbidden")
            except OSError as exc:
                raise StructuredVerifierProviderError("codex_admin_skills_unverifiable") from exc

    def _probe_version(self) -> str:
        try:
            run = subprocess.run(
                [self._codex, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=15,
                env={"LC_ALL": "C", "LANG": "C", "PATH": os.environ.get("PATH", os.defpath)},
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise StructuredVerifierProviderError("codex_version_probe_failed") from exc
        match = _CODEX_VERSION_RE.search((run.stdout + "\n" + run.stderr).strip())
        if run.returncode != 0 or match is None:
            raise StructuredVerifierProviderError("codex_version_probe_failed")
        return match.group("version")

    @staticmethod
    def _planner_schema(max_queries: int) -> dict[str, object]:
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "queries": {
                    "type": "array",
                    "maxItems": max_queries,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "query_id": {"type": "string", "pattern": "^[A-Za-z0-9._-]{1,64}$"},
                            "purpose": {"type": "string", "maxLength": 2048},
                            "sql": {"type": "string", "maxLength": 65536},
                        },
                        "required": ["query_id", "purpose", "sql"],
                    },
                }
            },
            "required": ["queries"],
        }

    @staticmethod
    def _final_schema() -> dict[str, object]:
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "verdict": {
                    "type": "string",
                    "enum": ["supported", "contradicted", "insufficient_evidence"],
                },
                "evidence_sufficiency": {"type": "string", "enum": ["adequate", "inadequate"]},
                "cited_query_ids": {
                    "type": "array",
                    "items": {"type": "string", "pattern": "^[A-Za-z0-9._-]{1,64}$"},
                },
                "reason": {"type": "string", "maxLength": _MAX_REASON},
                "abstention_reason_code": {
                    "anyOf": [
                        {"type": "string", "pattern": "^[a-z][a-z0-9_]{0,127}$"},
                        {"type": "null"},
                    ]
                },
            },
            "required": [
                "verdict",
                "evidence_sufficiency",
                "cited_query_ids",
                "reason",
                "abstention_reason_code",
            ],
        }


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _canonical_json_bytes(value: object) -> bytes:
    return _canonical_json(value).encode("utf-8")


def _nonnegative_int(value: int, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
