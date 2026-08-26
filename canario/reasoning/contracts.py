"""Typed contracts for bounded analytical derivation and verification."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from canario.deposit.ids import new_id, validate_id
from canario.processors.contracts import (
    EgressAuthorization,
    JSONValue,
    TargetSnapshot,
    require_nonempty,
    require_token,
    validate_sha256,
)

DERIVATION_OPERATION_KINDS = frozenset({"query", "program", "rule", "other_registered"})
DERIVATION_PROGRAM_KINDS = frozenset({"sql", "expression", "script", "other_registered"})
DERIVATION_RESULT_KINDS = frozenset({"scalar", "table", "structured", "binary", "other_registered"})
DERIVATION_OUTCOMES = frozenset({"success", "failed"})
LINEAGE_STATES = frozenset({"exact", "partial", "unavailable", "none"})
VERIFICATION_OUTCOMES = frozenset({"completed", "failed"})
VERDICTS = frozenset({"supported", "contradicted", "insufficient_evidence"})
SUFFICIENCY_STATES = frozenset({"sufficient", "insufficient"})
VERIFICATION_EVIDENCE_ROLES = frozenset({"supports", "challenges", "context"})
DERIVATION_USE_STATES = frozenset({"attempted", "consumed"})
ASSESSMENT_JUDGMENTS = frozenset({"supported", "contested", "refuted", "unresolved"})
ORIGIN_KINDS = frozenset({"machine", "rule", "human"})
EVIDENCE_RELATIONS = frozenset({"supports", "challenges", "contextualizes", "quotes", "mentions"})
LINK_LIFECYCLES = frozenset({"candidate", "active"})
CLAIM_LIFECYCLES = frozenset({"active", "restricted"})


class _NoInlinePayload:
    __slots__ = ()

    def __repr__(self) -> str:
        return "NO_INLINE_PAYLOAD"


NO_INLINE_PAYLOAD = _NoInlinePayload()

_MAX_PROGRAM_CHARS = 1024 * 1024
_MAX_PROPOSITION_CHARS = 64 * 1024
_MAX_RATIONALE_CHARS = 16 * 1024
_MAX_SELECTOR_JSON_CHARS = 128 * 1024
_MAX_PROFILE_JSON_CHARS = 128 * 1024


def _bounded_nonempty(value: str, field_name: str, maximum: int) -> str:
    require_nonempty(value, field_name)
    if len(value) > maximum:
        raise ValueError(f"{field_name} exceeds {maximum} characters")
    return value


def _optional_nonempty(value: str | None, field_name: str) -> str | None:
    if value is not None:
        require_nonempty(value, field_name)
    return value


def _positive_optional(value: int | None, field_name: str) -> None:
    if value is not None and (
        isinstance(value, bool) or not isinstance(value, int) or value <= 0
    ):
        raise ValueError(f"{field_name} must be a positive integer")


@dataclass(frozen=True, slots=True)
class DerivationDescriptor:
    """Trusted identity/capability declaration for one analytical backend."""

    key: str
    implementation_version: str
    execution_venue: str
    executor_key: str
    executor_version: str
    sandbox_profile_key: str
    sandbox_profile_version: str
    operation_kinds: frozenset[str]
    program_kinds: frozenset[str]
    requires_egress: bool = False
    model_provider: str | None = None
    model_name: str | None = None
    executor_source_id: str | None = None
    max_inputs: int | None = None
    max_input_bytes: int | None = None
    max_result_bytes: int | None = None

    def __post_init__(self) -> None:
        require_token(self.key, "derivation implementation key")
        require_nonempty(self.implementation_version, "derivation implementation version")
        require_token(self.execution_venue, "derivation execution venue")
        require_token(self.executor_key, "derivation executor key")
        require_nonempty(self.executor_version, "derivation executor version")
        require_token(self.sandbox_profile_key, "sandbox profile key")
        require_nonempty(self.sandbox_profile_version, "sandbox profile version")
        if not isinstance(self.operation_kinds, frozenset) or not self.operation_kinds:
            raise ValueError("operation_kinds must be a non-empty frozenset")
        if not self.operation_kinds.issubset(DERIVATION_OPERATION_KINDS):
            raise ValueError("derivation descriptor contains an unknown operation kind")
        if not isinstance(self.program_kinds, frozenset) or not self.program_kinds:
            raise ValueError("program_kinds must be a non-empty frozenset")
        if not self.program_kinds.issubset(DERIVATION_PROGRAM_KINDS):
            raise ValueError("derivation descriptor contains an unknown program kind")
        if not isinstance(self.requires_egress, bool):
            raise TypeError("requires_egress must be boolean")
        if self.model_provider is not None:
            require_token(self.model_provider, "model provider")
        if self.model_name is not None:
            require_nonempty(self.model_name, "model name")
        if (self.model_provider is None) != (self.model_name is None):
            raise ValueError("model provider/name must either both be present or both absent")
        _optional_nonempty(self.executor_source_id, "executor source id")
        for field_name in ("max_inputs", "max_input_bytes", "max_result_bytes"):
            _positive_optional(getattr(self, field_name), field_name)


@dataclass(frozen=True, slots=True)
class DerivationRequest:
    input_target_ids: tuple[str, ...]
    operation_kind: str
    program_kind: str
    program_text: str
    configuration_hash: str | None = None
    egress: EgressAuthorization = field(default_factory=EgressAuthorization.forbidden)
    derivation_run_id: str = field(default_factory=lambda: new_id("drun_"))

    def __post_init__(self) -> None:
        validate_id(self.derivation_run_id, "drun_")
        if self.operation_kind not in DERIVATION_OPERATION_KINDS:
            raise ValueError(f"invalid derivation operation kind: {self.operation_kind!r}")
        if self.program_kind not in DERIVATION_PROGRAM_KINDS:
            raise ValueError(f"invalid derivation program kind: {self.program_kind!r}")
        _bounded_nonempty(self.program_text, "derivation program", _MAX_PROGRAM_CHARS)
        validate_sha256(self.configuration_hash, "derivation configuration hash")
        if not isinstance(self.input_target_ids, tuple) or not self.input_target_ids:
            raise ValueError("DerivationRequest requires a non-empty input target tuple")
        if len(set(self.input_target_ids)) != len(self.input_target_ids):
            raise ValueError("DerivationRequest input targets cannot repeat")
        for target_id in self.input_target_ids:
            validate_id(target_id, "rtgt_")


@dataclass(frozen=True, slots=True)
class DerivationInputSnapshot:
    ordinal: int
    target: TargetSnapshot
    representation_kind: str
    media_type: str
    language: str | None
    charset: str | None
    material_bytes: bytes
    restricted: bool

    def __post_init__(self) -> None:
        if isinstance(self.ordinal, bool) or not isinstance(self.ordinal, int) or self.ordinal < 0:
            raise ValueError("derivation input ordinal must be a non-negative integer")
        require_nonempty(self.representation_kind, "representation kind")
        require_nonempty(self.media_type, "media type")
        if not isinstance(self.material_bytes, bytes):
            raise TypeError("derivation bounded material must be immutable bytes")
        if not isinstance(self.restricted, bool):
            raise TypeError("derivation restricted flag must be boolean")


@dataclass(frozen=True, slots=True)
class DerivationInvocation:
    request: DerivationRequest
    inputs: tuple[DerivationInputSnapshot, ...]

    def __post_init__(self) -> None:
        if not self.inputs:
            raise ValueError("DerivationInvocation requires at least one input")
        if tuple(item.ordinal for item in self.inputs) != tuple(range(len(self.inputs))):
            raise ValueError("DerivationInvocation input ordinals must be dense and ordered")


@dataclass(frozen=True, slots=True)
class SourceLineageDraft:
    input_ordinal: int
    representation_target_id: str

    def __post_init__(self) -> None:
        if isinstance(self.input_ordinal, bool) or not isinstance(self.input_ordinal, int) or self.input_ordinal < 0:
            raise ValueError("lineage input ordinal must be a non-negative integer")
        validate_id(self.representation_target_id, "rtgt_")


@dataclass(frozen=True, slots=True)
class DerivationResultTargetDraft:
    selector_kind: str
    selector_version: str
    selector_payload_json: str
    lineage_state: str
    lineage: tuple[SourceLineageDraft, ...] = ()

    def __post_init__(self) -> None:
        require_token(self.selector_kind, "result selector kind")
        require_token(self.selector_version, "result selector version")
        _bounded_nonempty(
            self.selector_payload_json, "result selector payload", _MAX_SELECTOR_JSON_CHARS
        )
        if self.lineage_state not in LINEAGE_STATES:
            raise ValueError(f"invalid result lineage state: {self.lineage_state!r}")
        if not isinstance(self.lineage, tuple) or not all(
            isinstance(item, SourceLineageDraft) for item in self.lineage
        ):
            raise TypeError("result lineage must contain SourceLineageDraft values")
        target_ids = [item.representation_target_id for item in self.lineage]
        if len(target_ids) != len(set(target_ids)):
            raise ValueError("result lineage cannot repeat the same source target")
        if self.lineage_state in {"exact", "partial"} and not self.lineage:
            raise ValueError("exact/partial result target requires source lineage")
        if self.lineage_state in {"unavailable", "none"} and self.lineage:
            raise ValueError("unavailable/none result target cannot fabricate source lineage")


@dataclass(frozen=True, slots=True)
class DerivationOutput:
    result_kind: str
    schema_key: str
    schema_version: str
    targets: tuple[DerivationResultTargetDraft, ...]
    inline_payload: JSONValue | _NoInlinePayload = NO_INLINE_PAYLOAD
    archive_bytes: bytes | None = None

    def __post_init__(self) -> None:
        if self.result_kind not in DERIVATION_RESULT_KINDS:
            raise ValueError(f"invalid derivation result kind: {self.result_kind!r}")
        require_token(self.schema_key, "result schema key")
        require_token(self.schema_version, "result schema version")
        has_inline = self.inline_payload is not NO_INLINE_PAYLOAD
        if has_inline == (self.archive_bytes is not None):
            raise ValueError("DerivationOutput requires exactly one inline payload or archive bytes")
        if self.archive_bytes is not None and not isinstance(self.archive_bytes, bytes):
            raise TypeError("derivation archive result must be immutable bytes")
        if not isinstance(self.targets, tuple) or not self.targets:
            raise ValueError("successful DerivationOutput requires at least one result target")
        if not all(isinstance(target, DerivationResultTargetDraft) for target in self.targets):
            raise TypeError("result targets must contain DerivationResultTargetDraft values")
        selector_ids = [
            (target.selector_kind, target.selector_version, target.selector_payload_json)
            for target in self.targets
        ]
        if len(selector_ids) != len(set(selector_ids)):
            raise ValueError("DerivationOutput cannot repeat the same result selector")


@dataclass(frozen=True, slots=True)
class DerivationExecutionResult:
    outcome: str
    output: DerivationOutput | None = None
    error_code: str | None = None
    egress_bytes: int | None = None

    def __post_init__(self) -> None:
        if self.outcome not in DERIVATION_OUTCOMES:
            raise ValueError(f"invalid derivation outcome: {self.outcome!r}")
        if self.outcome == "success":
            if self.output is None or self.error_code is not None:
                raise ValueError("successful Derivation requires output and no error_code")
        else:
            if self.output is not None or self.error_code is None:
                raise ValueError("failed Derivation requires error_code and no output")
            require_token(self.error_code, "derivation error code")
        if self.egress_bytes is not None and (
            isinstance(self.egress_bytes, bool)
            or not isinstance(self.egress_bytes, int)
            or self.egress_bytes < 0
        ):
            raise ValueError("derivation egress_bytes must be a non-negative integer")


@runtime_checkable
class DerivationBackend(Protocol):
    @property
    def descriptor(self) -> DerivationDescriptor:
        ...

    def derive(self, invocation: DerivationInvocation) -> DerivationExecutionResult:
        ...


@dataclass(frozen=True, slots=True)
class VerificationDescriptor:
    key: str
    implementation_version: str
    execution_venue: str
    requires_egress: bool = False
    model_provider: str | None = None
    model_name: str | None = None
    max_scopes: int | None = None
    max_scope_bytes: int | None = None

    def __post_init__(self) -> None:
        require_token(self.key, "verification implementation key")
        require_nonempty(self.implementation_version, "verification implementation version")
        require_token(self.execution_venue, "verification execution venue")
        if not isinstance(self.requires_egress, bool):
            raise TypeError("requires_egress must be boolean")
        if self.model_provider is not None:
            require_token(self.model_provider, "verification model provider")
        if self.model_name is not None:
            require_nonempty(self.model_name, "verification model name")
        if (self.model_provider is None) != (self.model_name is None):
            raise ValueError("verification model provider/name must both be present or absent")
        _positive_optional(self.max_scopes, "max_scopes")
        _positive_optional(self.max_scope_bytes, "max_scope_bytes")


@dataclass(frozen=True, slots=True)
class VerificationDerivationStep:
    derivation_run_id: str
    use_state: str
    derivation_result_target_id: str | None = None

    def __post_init__(self) -> None:
        validate_id(self.derivation_run_id, "drun_")
        if self.use_state not in DERIVATION_USE_STATES:
            raise ValueError(f"invalid derivation use state: {self.use_state!r}")
        if self.use_state == "attempted":
            if self.derivation_result_target_id is not None:
                raise ValueError("attempted derivation step cannot name a consumed result target")
        else:
            if self.derivation_result_target_id is None:
                raise ValueError("consumed derivation step requires a result target")
            validate_id(self.derivation_result_target_id, "drtgt_")


@dataclass(frozen=True, slots=True)
class VerificationRequest:
    proposition_text: str
    scope_target_ids: tuple[str, ...]
    authority_scope_ids: tuple[str, ...]
    scope_profile_key: str
    scope_profile_version: str
    scope_payload_json: str
    derivation_steps: tuple[VerificationDerivationStep, ...] = ()
    claim_revision_id: str | None = None
    configuration_hash: str | None = None
    egress: EgressAuthorization = field(default_factory=EgressAuthorization.forbidden)
    verification_run_id: str = field(default_factory=lambda: new_id("vrun_"))

    def __post_init__(self) -> None:
        validate_id(self.verification_run_id, "vrun_")
        if self.claim_revision_id is not None:
            validate_id(self.claim_revision_id, "clrev_")
        _bounded_nonempty(self.proposition_text, "verification proposition", _MAX_PROPOSITION_CHARS)
        if not isinstance(self.scope_target_ids, tuple) or not self.scope_target_ids:
            raise ValueError("VerificationRequest requires a non-empty scope target tuple")
        if len(set(self.scope_target_ids)) != len(self.scope_target_ids):
            raise ValueError("verification scope targets cannot repeat")
        for target_id in self.scope_target_ids:
            validate_id(target_id, "rtgt_")
        if not isinstance(self.authority_scope_ids, tuple) or not self.authority_scope_ids:
            raise ValueError("VerificationRequest requires explicit Source Authority scopes")
        if len(set(self.authority_scope_ids)) != len(self.authority_scope_ids):
            raise ValueError("verification authority scopes cannot repeat")
        for scope_id in self.authority_scope_ids:
            validate_id(scope_id, "sas_")
        require_token(self.scope_profile_key, "verification scope profile key")
        require_token(self.scope_profile_version, "verification scope profile version")
        _bounded_nonempty(self.scope_payload_json, "verification scope payload", _MAX_PROFILE_JSON_CHARS)
        if not isinstance(self.derivation_steps, tuple) or not all(
            isinstance(step, VerificationDerivationStep) for step in self.derivation_steps
        ):
            raise TypeError("verification derivation_steps must contain VerificationDerivationStep values")
        validate_sha256(self.configuration_hash, "verification configuration hash")


@dataclass(frozen=True, slots=True)
class VerificationEvidenceDraft:
    scope_ordinal: int
    representation_target_id: str
    role: str

    def __post_init__(self) -> None:
        if isinstance(self.scope_ordinal, bool) or not isinstance(self.scope_ordinal, int) or self.scope_ordinal < 0:
            raise ValueError("verification evidence scope ordinal must be non-negative")
        validate_id(self.representation_target_id, "rtgt_")
        if self.role not in VERIFICATION_EVIDENCE_ROLES:
            raise ValueError(f"invalid verification evidence role: {self.role!r}")


@dataclass(frozen=True, slots=True)
class VerificationExecutionResult:
    outcome: str
    verdict: str | None = None
    sufficiency_state: str | None = None
    sufficiency_profile_key: str | None = None
    sufficiency_profile_version: str | None = None
    sufficiency_payload_json: str | None = None
    abstention_reason_code: str | None = None
    evidence: tuple[VerificationEvidenceDraft, ...] = ()
    error_code: str | None = None
    egress_bytes: int | None = None

    def __post_init__(self) -> None:
        if self.outcome not in VERIFICATION_OUTCOMES:
            raise ValueError(f"invalid verification outcome: {self.outcome!r}")
        if not isinstance(self.evidence, tuple) or not all(
            isinstance(item, VerificationEvidenceDraft) for item in self.evidence
        ):
            raise TypeError("verification evidence must contain VerificationEvidenceDraft values")
        identities = [
            (item.representation_target_id, item.role) for item in self.evidence
        ]
        if len(identities) != len(set(identities)):
            raise ValueError("verification evidence cannot repeat the same target/role")
        if self.outcome == "failed":
            if self.error_code is None:
                raise ValueError("failed Verification requires error_code")
            require_token(self.error_code, "verification error code")
            if any(
                value is not None
                for value in (
                    self.verdict,
                    self.sufficiency_state,
                    self.sufficiency_profile_key,
                    self.sufficiency_profile_version,
                    self.sufficiency_payload_json,
                    self.abstention_reason_code,
                )
            ) or self.evidence:
                raise ValueError("failed Verification cannot carry epistemic result/evidence")
        else:
            if self.error_code is not None:
                raise ValueError("completed Verification cannot carry error_code")
            if self.verdict not in VERDICTS:
                raise ValueError("completed Verification requires a known verdict")
            if self.sufficiency_profile_key is None or self.sufficiency_profile_version is None or self.sufficiency_payload_json is None:
                raise ValueError("completed Verification requires an explicit sufficiency profile/payload")
            require_token(self.sufficiency_profile_key, "sufficiency profile key")
            require_token(self.sufficiency_profile_version, "sufficiency profile version")
            _bounded_nonempty(
                self.sufficiency_payload_json,
                "verification sufficiency payload",
                _MAX_PROFILE_JSON_CHARS,
            )
            if self.verdict in {"supported", "contradicted"}:
                if self.sufficiency_state != "sufficient" or self.abstention_reason_code is not None:
                    raise ValueError("supported/contradicted require sufficient evidence and no abstention")
            else:
                if self.sufficiency_state != "insufficient" or self.abstention_reason_code is None:
                    raise ValueError("insufficient_evidence requires explicit insufficiency and abstention reason")
                require_token(self.abstention_reason_code, "abstention reason code")
        if self.egress_bytes is not None and (
            isinstance(self.egress_bytes, bool)
            or not isinstance(self.egress_bytes, int)
            or self.egress_bytes < 0
        ):
            raise ValueError("verification egress_bytes must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class SourceAuthoritySnapshot:
    id: str
    source_id: str
    scope_kind: str
    valid_from: str | None
    valid_to: str | None
    note: str | None

    def __post_init__(self) -> None:
        validate_id(self.id, "sas_")
        validate_id(self.source_id, "src_")
        require_token(self.scope_kind, "Source Authority scope kind")


@dataclass(frozen=True, slots=True)
class VerificationScopeSnapshot:
    ordinal: int
    target: TargetSnapshot
    representation_kind: str
    media_type: str
    language: str | None
    charset: str | None
    source_id: str
    material_bytes: bytes
    restricted: bool


@dataclass(frozen=True, slots=True)
class ConsumedDerivationSnapshot:
    ordinal: int
    derivation_run_id: str
    result_target_id: str
    result_kind: str
    schema_key: str
    schema_version: str
    material_bytes: bytes
    result_selector_kind: str
    result_selector_version: str
    result_selector_payload_json: str
    lineage_state: str
    source_target_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class VerificationDerivationSnapshot:
    ordinal: int
    derivation_run_id: str
    use_state: str
    implementation_key: str
    implementation_version: str
    configuration_hash: str | None
    executor_key: str
    executor_version: str
    executor_source_id: str | None
    sandbox_profile_key: str
    sandbox_profile_version: str
    operation_kind: str
    program_kind: str
    program_sha256: str
    outcome: str
    error_code: str | None
    consumed_result: ConsumedDerivationSnapshot | None

    def __post_init__(self) -> None:
        if isinstance(self.ordinal, bool) or not isinstance(self.ordinal, int) or self.ordinal < 0:
            raise ValueError("verification derivation ordinal must be non-negative")
        validate_id(self.derivation_run_id, "drun_")
        if self.use_state not in DERIVATION_USE_STATES:
            raise ValueError("verification derivation use_state is invalid")
        require_token(self.implementation_key, "verification derivation implementation key")
        require_nonempty(
            self.implementation_version, "verification derivation implementation version"
        )
        validate_sha256(self.configuration_hash, "verification derivation configuration hash")
        require_token(self.executor_key, "verification derivation executor key")
        require_nonempty(self.executor_version, "verification derivation executor version")
        _optional_nonempty(self.executor_source_id, "verification derivation executor source id")
        require_token(self.sandbox_profile_key, "verification derivation sandbox profile key")
        require_nonempty(
            self.sandbox_profile_version, "verification derivation sandbox profile version"
        )
        if self.operation_kind not in DERIVATION_OPERATION_KINDS:
            raise ValueError("verification derivation operation_kind is invalid")
        if self.program_kind not in DERIVATION_PROGRAM_KINDS:
            raise ValueError("verification derivation program_kind is invalid")
        validate_sha256(self.program_sha256, "verification derivation program SHA")
        if self.outcome not in DERIVATION_OUTCOMES:
            raise ValueError("verification derivation outcome is invalid")
        if self.outcome == "success":
            if self.error_code is not None:
                raise ValueError("successful Verification derivation snapshot cannot carry error")
        else:
            _optional_nonempty(self.error_code, "verification derivation error code")
            if self.error_code is None:
                raise ValueError("failed Verification derivation snapshot requires error code")
        if self.use_state == "attempted" and self.consumed_result is not None:
            raise ValueError("attempted Verification derivation cannot carry consumed result")
        if self.use_state == "consumed":
            if self.outcome != "success":
                raise ValueError("consumed Verification derivation must be successful")
            if self.consumed_result is None:
                raise ValueError("consumed Verification derivation requires consumed result")


@dataclass(frozen=True, slots=True)
class VerificationInvocation:
    request: VerificationRequest
    scopes: tuple[VerificationScopeSnapshot, ...]
    authority_scopes: tuple[SourceAuthoritySnapshot, ...]
    derivations: tuple[VerificationDerivationSnapshot, ...]


@runtime_checkable
class VerificationBackend(Protocol):
    @property
    def descriptor(self) -> VerificationDescriptor:
        ...

    def verify(self, invocation: VerificationInvocation) -> VerificationExecutionResult:
        ...


@dataclass(frozen=True, slots=True)
class DerivedEvidenceDraft:
    representation_target_id: str
    relation: str
    origin_kind: str
    process_run_id: str | None = None
    lifecycle: str = "active"
    rationale: str | None = None
    evidence_link_id: str = field(default_factory=lambda: new_id("evl_"))

    def __post_init__(self) -> None:
        validate_id(self.evidence_link_id, "evl_")
        validate_id(self.representation_target_id, "rtgt_")
        if self.relation not in EVIDENCE_RELATIONS:
            raise ValueError(f"invalid evidence relation: {self.relation!r}")
        if self.origin_kind not in ORIGIN_KINDS:
            raise ValueError(f"invalid evidence origin kind: {self.origin_kind!r}")
        if self.lifecycle not in LINK_LIFECYCLES:
            raise ValueError(f"invalid evidence lifecycle: {self.lifecycle!r}")
        if self.process_run_id is not None:
            validate_id(self.process_run_id, "prun_")
        if self.origin_kind != "human" and self.process_run_id is None:
            raise ValueError("machine/rule EvidenceLink requires ProcessRun provenance")
        if self.rationale is not None:
            _bounded_nonempty(self.rationale, "evidence rationale", _MAX_RATIONALE_CHARS)


@dataclass(frozen=True, slots=True)
class DerivedClaimRequest:
    derivation_result_target_id: str
    text: str
    origin_kind: str
    evidence: tuple[DerivedEvidenceDraft, ...] = ()
    process_run_id: str | None = None
    attribution_entity_id: str | None = None
    attribution_text: str | None = None
    temporal_start: str | None = None
    temporal_end: str | None = None
    sensitive: bool = False
    quantitative: bool = False
    lifecycle: str = "active"
    claim_id: str = field(default_factory=lambda: new_id("clm_"))
    claim_revision_id: str = field(default_factory=lambda: new_id("clrev_"))

    def __post_init__(self) -> None:
        validate_id(self.claim_id, "clm_")
        validate_id(self.claim_revision_id, "clrev_")
        validate_id(self.derivation_result_target_id, "drtgt_")
        _bounded_nonempty(self.text, "derived Claim text", _MAX_PROPOSITION_CHARS)
        if self.origin_kind not in ORIGIN_KINDS:
            raise ValueError(f"invalid Claim origin kind: {self.origin_kind!r}")
        if self.process_run_id is not None:
            validate_id(self.process_run_id, "prun_")
        if self.attribution_entity_id is not None:
            validate_id(self.attribution_entity_id, "ent_")
        if self.attribution_text is not None:
            _bounded_nonempty(self.attribution_text, "Claim attribution text", 4096)
        if self.temporal_start is not None and self.temporal_end is not None and self.temporal_start > self.temporal_end:
            raise ValueError("Claim temporal_start cannot exceed temporal_end")
        if type(self.sensitive) is not bool or type(self.quantitative) is not bool:
            raise TypeError("Claim sensitive/quantitative flags must be booleans")
        if self.lifecycle not in CLAIM_LIFECYCLES:
            raise ValueError(f"invalid derived Claim lifecycle: {self.lifecycle!r}")
        if not isinstance(self.evidence, tuple) or not all(
            isinstance(item, DerivedEvidenceDraft) for item in self.evidence
        ):
            raise TypeError("derived Claim evidence must contain DerivedEvidenceDraft values")
        evidence_ids = [item.evidence_link_id for item in self.evidence]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("derived Claim evidence IDs cannot repeat")


@dataclass(frozen=True, slots=True)
class AssessmentRequest:
    claim_revision_id: str
    judgment: str
    origin_kind: str
    assessor_key: str
    verification_run_id: str | None = None
    policy_key: str | None = None
    policy_version: str | None = None
    rationale: str | None = None
    supersedes_assessment_id: str | None = None
    assessment_id: str = field(default_factory=lambda: new_id("asm_"))

    def __post_init__(self) -> None:
        validate_id(self.assessment_id, "asm_")
        validate_id(self.claim_revision_id, "clrev_")
        if self.supersedes_assessment_id is not None:
            validate_id(self.supersedes_assessment_id, "asm_")
            if self.supersedes_assessment_id == self.assessment_id:
                raise ValueError("Assessment cannot supersede itself")
        if self.judgment not in ASSESSMENT_JUDGMENTS:
            raise ValueError(f"invalid Assessment judgment: {self.judgment!r}")
        if self.origin_kind not in ORIGIN_KINDS:
            raise ValueError(f"invalid Assessment origin kind: {self.origin_kind!r}")
        require_token(self.assessor_key, "assessor key")
        if self.verification_run_id is not None:
            validate_id(self.verification_run_id, "vrun_")
        if (self.policy_key is None) != (self.policy_version is None):
            raise ValueError("Assessment policy key/version must both be present or absent")
        if self.policy_key is not None:
            require_token(self.policy_key, "Assessment policy key")
            require_token(self.policy_version, "Assessment policy version")
        if self.origin_kind != "human" and (
            self.verification_run_id is None or self.policy_key is None
        ):
            raise ValueError("machine/rule Assessment requires VerificationRun and policy")
        if self.rationale is not None:
            _bounded_nonempty(self.rationale, "Assessment rationale", _MAX_RATIONALE_CHARS)
