"""Generic, backend-neutral contracts for Representation processing."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Protocol, TypeAlias, runtime_checkable

from actakit.deposit.ids import new_id, validate_id

_TOKEN_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

PROCESS_OUTCOMES = frozenset({"success", "partial", "failed"})
REPRESENTATION_KINDS = frozenset(
    {
        "original",
        "extracted_text",
        "ocr_text",
        "normalized_text",
        "table",
        "page_image",
        "transcript",
        "redacted_derivative",
        "other",
    }
)

JSONScalar: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONScalar | tuple["JSONValue", ...] | list["JSONValue"] | dict[str, "JSONValue"]


def require_token(value: str, field_name: str) -> str:
    if not _TOKEN_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase package-like token")
    return value


def require_nonempty(value: str, field_name: str) -> str:
    if not value or not value.strip():
        raise ValueError(f"{field_name} must be non-empty")
    return value


def validate_sha256(value: str | None, field_name: str) -> str | None:
    if value is not None and not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be 64 lowercase SHA-256 hex characters")
    return value


@dataclass(frozen=True, slots=True)
class ProcessorDescriptor:
    """Trusted identity and declared capability of one curated processor."""

    key: str
    capability_key: str
    implementation_version: str
    execution_venue: str
    input_media_types: frozenset[str]
    output_kinds: frozenset[str]
    scope_kinds: frozenset[str]
    requires_egress: bool = False
    model_provider: str | None = None
    model_name: str | None = None
    max_input_bytes: int | None = None
    max_scopes: int | None = None

    def __post_init__(self) -> None:
        require_token(self.key, "processor key")
        require_token(self.capability_key, "capability key")
        require_nonempty(self.implementation_version, "implementation version")
        require_token(self.execution_venue, "execution venue")
        if not isinstance(self.input_media_types, frozenset) or not self.input_media_types:
            raise ValueError("input_media_types must be a non-empty frozenset")
        if not all(value and value.strip() for value in self.input_media_types):
            raise ValueError("input media types must be non-empty")
        if not isinstance(self.output_kinds, frozenset):
            raise TypeError("output_kinds must be a frozenset")
        unknown_kinds = self.output_kinds - REPRESENTATION_KINDS
        if unknown_kinds:
            raise ValueError(f"unknown output Representation kinds: {sorted(unknown_kinds)!r}")
        if not isinstance(self.scope_kinds, frozenset) or not self.scope_kinds:
            raise ValueError("scope_kinds must be a non-empty frozenset")
        for kind in self.scope_kinds:
            require_token(kind, "scope kind")
        if self.model_provider is not None:
            require_token(self.model_provider, "model provider")
        if self.model_name is not None:
            require_nonempty(self.model_name, "model name")
        if (self.model_provider is None) != (self.model_name is None):
            raise ValueError("model provider/name must either both be present or both be absent")
        if self.max_input_bytes is not None and self.max_input_bytes <= 0:
            raise ValueError("max_input_bytes must be positive")
        if self.max_scopes is not None and self.max_scopes <= 0:
            raise ValueError("max_scopes must be positive")


@dataclass(frozen=True, slots=True)
class EgressAuthorization:
    """Non-secret host policy authorizing source-byte egress for one request."""

    allowed: bool
    policy_profile: str
    data_control_profile: str
    request_template_hash: str | None = None
    endpoint_profile: str | None = None

    def __post_init__(self) -> None:
        require_token(self.policy_profile, "egress policy profile")
        require_token(self.data_control_profile, "data-control profile")
        validate_sha256(self.request_template_hash, "request template hash")
        if self.endpoint_profile is not None:
            require_token(self.endpoint_profile, "endpoint profile")

    @classmethod
    def forbidden(cls) -> "EgressAuthorization":
        return cls(False, "no_egress", "no_egress")


@dataclass(frozen=True, slots=True)
class ProcessingRequest:
    """Stable canonical attempt request grounded in one retained Representation."""

    representation_id: str
    target_ids: tuple[str, ...]
    capability_key: str
    configuration_hash: str | None = None
    egress: EgressAuthorization = field(default_factory=EgressAuthorization.forbidden)
    process_run_id: str = field(default_factory=lambda: new_id("prun_"))

    def __post_init__(self) -> None:
        validate_id(self.representation_id, "rep_")
        validate_id(self.process_run_id, "prun_")
        require_token(self.capability_key, "capability key")
        validate_sha256(self.configuration_hash, "configuration hash")
        if not isinstance(self.target_ids, tuple) or not self.target_ids:
            raise ValueError("target_ids must be a non-empty tuple")
        if len(set(self.target_ids)) != len(self.target_ids):
            raise ValueError("target_ids cannot contain duplicates")
        for target_id in self.target_ids:
            validate_id(target_id, "rtgt_")


@dataclass(frozen=True, slots=True)
class TargetSnapshot:
    id: str
    representation_id: str
    selector_kind: str
    selector_version: str
    selector_payload_json: str

    def __post_init__(self) -> None:
        validate_id(self.id, "rtgt_")
        validate_id(self.representation_id, "rep_")
        require_token(self.selector_kind, "selector kind")
        require_token(self.selector_version, "selector version")
        require_nonempty(self.selector_payload_json, "selector payload")


@dataclass(frozen=True, slots=True)
class ProcessorInvocation:
    """Immutable bytes/scope view supplied to a Processor implementation."""

    request: ProcessingRequest
    representation_kind: str
    media_type: str
    language: str | None
    charset: str | None
    source_bytes: bytes
    scopes: tuple[TargetSnapshot, ...]

    def __post_init__(self) -> None:
        if self.representation_kind not in REPRESENTATION_KINDS:
            raise ValueError(f"unknown Representation kind: {self.representation_kind!r}")
        require_nonempty(self.media_type, "media type")
        if not isinstance(self.source_bytes, bytes):
            raise TypeError("source_bytes must be immutable bytes")
        if not self.scopes:
            raise ValueError("ProcessorInvocation requires at least one scope")


@dataclass(frozen=True, slots=True)
class DerivativeOutput:
    data: bytes
    kind: str
    media_type: str
    language: str | None = None
    charset: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.data, bytes):
            raise TypeError("derivative data must be immutable bytes")
        if self.kind == "original" or self.kind not in REPRESENTATION_KINDS:
            raise ValueError("processor outputs must be a non-original Representation kind")
        require_nonempty(self.media_type, "output media type")
        if self.language is not None:
            require_nonempty(self.language, "output language")
        if self.charset is not None:
            require_nonempty(self.charset, "output charset")


@dataclass(frozen=True, slots=True)
class QualitySignal:
    target_id: str
    signal_key: str
    signal_version: str
    payload: JSONValue
    interpretation_key: str | None = None

    def __post_init__(self) -> None:
        validate_id(self.target_id, "rtgt_")
        require_token(self.signal_key, "quality signal key")
        require_token(self.signal_version, "quality signal version")
        if self.interpretation_key is not None:
            require_token(self.interpretation_key, "quality interpretation key")


@dataclass(frozen=True, slots=True)
class ProcessorResult:
    outcome: str
    outputs: tuple[DerivativeOutput, ...] = ()
    evidence: tuple[QualitySignal, ...] = ()
    error_code: str | None = None
    diagnostic_codes: tuple[str, ...] = ()
    egress_bytes: int | None = None

    def __post_init__(self) -> None:
        if self.outcome not in PROCESS_OUTCOMES:
            raise ValueError(f"invalid process outcome: {self.outcome!r}")
        if not isinstance(self.outputs, tuple) or not isinstance(self.evidence, tuple):
            raise TypeError("processor outputs/evidence must be tuples")
        if self.outcome == "failed" and self.outputs:
            raise ValueError("failed ProcessRun cannot emit canonical derivative outputs")
        if self.outcome == "success" and self.error_code is not None:
            raise ValueError("successful ProcessRun cannot carry an error_code")
        if self.outcome == "failed" and self.error_code is None:
            raise ValueError("failed ProcessRun requires a bounded error_code")
        if self.error_code is not None:
            require_token(self.error_code, "process error code")
        for code in self.diagnostic_codes:
            require_token(code, "diagnostic code")
        if self.egress_bytes is not None and self.egress_bytes < 0:
            raise ValueError("egress_bytes cannot be negative")


@runtime_checkable
class Processor(Protocol):
    @property
    def descriptor(self) -> ProcessorDescriptor:
        ...

    def process(self, invocation: ProcessorInvocation) -> ProcessorResult:
        ...
