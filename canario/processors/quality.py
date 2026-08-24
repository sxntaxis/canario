"""Typed quality evidence registry and policy decisions for the Workbench."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Callable, Protocol, runtime_checkable

from canario.deposit.ids import new_id, validate_id

from .contracts import (
    JSONValue,
    ProcessorDescriptor,
    ProcessorResult,
    QualitySignal,
    TargetSnapshot,
    require_token,
)

QualityValidator = Callable[[JSONValue], None]
QUALITY_DECISIONS = frozenset({"accept", "escalate", "quarantine_review"})
_MAX_SIGNAL_JSON_BYTES = 8192


class QualityContractError(ValueError):
    """A processor emitted unknown or malformed QualityEvidence."""


def _bool(value: JSONValue) -> None:
    if not isinstance(value, bool):
        raise QualityContractError("quality payload must be boolean")


def _ratio(value: JSONValue) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise QualityContractError("quality ratio must be numeric")
    if not math.isfinite(float(value)) or not 0.0 <= float(value) <= 1.0:
        raise QualityContractError("quality ratio must be finite and within 0..1")


def _nonnegative_int(value: JSONValue) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise QualityContractError("quality count must be a non-negative integer")


def _positive_int_list(value: JSONValue) -> None:
    if not isinstance(value, list) or len(value) > 4096:
        raise QualityContractError("quality page ordinals must be a bounded list")
    if any(isinstance(item, bool) or not isinstance(item, int) or item < 1 for item in value):
        raise QualityContractError("quality page ordinals must be positive integers")
    if value != sorted(set(value)):
        raise QualityContractError("quality page ordinals must be unique and strictly ordered")


def _bounded_string_list(value: JSONValue) -> None:
    if not isinstance(value, list) or len(value) > 64:
        raise QualityContractError("quality string collection must be a bounded list")
    if any(not isinstance(item, str) or len(item) > 512 for item in value):
        raise QualityContractError("quality string collection contains an invalid item")


def _word_confidence_summary(value: JSONValue) -> None:
    if not isinstance(value, dict) or set(value) != {"mean_percent", "word_count"}:
        raise QualityContractError(
            "ocr.word_confidence_summary:v1 requires mean_percent and word_count"
        )
    mean = value["mean_percent"]
    count = value["word_count"]
    if isinstance(mean, bool) or not isinstance(mean, (int, float)):
        raise QualityContractError("mean_percent must be numeric")
    if not math.isfinite(float(mean)) or not 0.0 <= float(mean) <= 100.0:
        raise QualityContractError("mean_percent must be finite and within 0..100")
    _nonnegative_int(count)


DEFAULT_QUALITY_CONTRACTS: dict[tuple[str, str], QualityValidator] = {
    ("core.output_nonempty", "v1"): _bool,
    ("native.page_text_present", "v1"): _bool,
    ("native.page_text_coverage", "v1"): _ratio,
    ("native.replacement_character_ratio", "v1"): _ratio,
    ("native.page_character_count", "v1"): _nonnegative_int,
    ("native.page_raster_image_count", "v1"): _nonnegative_int,
    ("native.selected_page_count", "v1"): _nonnegative_int,
    ("native.empty_page_count", "v1"): _nonnegative_int,
    ("native.empty_page_ordinals", "v1"): _positive_int_list,
    ("native.mixed_page_modes", "v1"): _bool,
    ("ocr.word_confidence_summary", "v1"): _word_confidence_summary,
    ("ocr.page_text_coverage", "v1"): _ratio,
    ("ocr.page_character_count", "v1"): _nonnegative_int,
    ("ocr.selected_page_count", "v1"): _nonnegative_int,
    ("ocr.empty_page_count", "v1"): _nonnegative_int,
    ("ocr.empty_page_ordinals", "v1"): _positive_int_list,
    ("ocr.native_page_count", "v1"): _nonnegative_int,
    ("ocr.ocr_page_count", "v1"): _nonnegative_int,
    ("ocr.ocr_page_ordinals", "v1"): _positive_int_list,
    ("ocr.needs_visual_review", "v1"): _bool,
    ("table.exact_row_count", "v1"): _nonnegative_int,
    ("multimodal.schema_valid", "v1"): _bool,
    ("multimodal.uncertain_span_count", "v1"): _nonnegative_int,
    ("multimodal.uncertain_spans", "v1"): _bounded_string_list,
    ("multimodal.transcription_character_count", "v1"): _nonnegative_int,
    ("multimodal.table_count", "v1"): _nonnegative_int,
    ("multimodal.table_text_coverage", "v1"): _ratio,
}


class QualityRegistry:
    """Explicit composition of bounded signal contracts; never a global mutable registry."""

    def __init__(
        self, contracts: dict[tuple[str, str], QualityValidator] | None = None
    ) -> None:
        self._contracts = dict(
            DEFAULT_QUALITY_CONTRACTS if contracts is None else contracts
        )

    def with_contract(
        self, signal_key: str, version: str, validator: QualityValidator
    ) -> "QualityRegistry":
        require_token(signal_key, "quality signal key")
        require_token(version, "quality signal version")
        contracts = dict(self._contracts)
        key = (signal_key, version)
        if key in contracts:
            raise QualityContractError(f"quality contract already registered: {key!r}")
        contracts[key] = validator
        return QualityRegistry(contracts)

    def validate(self, signal: QualitySignal) -> str:
        validator = self._contracts.get((signal.signal_key, signal.signal_version))
        if validator is None:
            raise QualityContractError(
                f"unknown quality signal contract: {signal.signal_key}:{signal.signal_version}"
            )
        validator(signal.payload)
        try:
            payload_json = json.dumps(
                signal.payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            )
        except (TypeError, ValueError) as exc:
            raise QualityContractError("quality payload is not bounded JSON data") from exc
        if len(payload_json.encode("utf-8")) > _MAX_SIGNAL_JSON_BYTES:
            raise QualityContractError("quality payload exceeds 8 KiB canonical limit")
        return payload_json


@dataclass(frozen=True, slots=True)
class PolicyContext:
    """Runtime capabilities eligible under current source/egress policy."""

    available_capabilities: frozenset[str]

    def __post_init__(self) -> None:
        if not isinstance(self.available_capabilities, frozenset):
            raise TypeError("available_capabilities must be a frozenset")
        for value in self.available_capabilities:
            require_token(value, "available capability")


@dataclass(frozen=True, slots=True)
class QualityDecision:
    target_id: str
    decision: str
    policy_key: str
    policy_version: str
    reason_code: str
    next_capability_key: str | None = None
    id: str = ""

    def __post_init__(self) -> None:
        validate_id(self.target_id, "rtgt_")
        if self.decision not in QUALITY_DECISIONS:
            raise ValueError(f"invalid quality decision: {self.decision!r}")
        require_token(self.policy_key, "policy key")
        require_token(self.policy_version, "policy version")
        require_token(self.reason_code, "quality reason code")
        if self.decision == "escalate":
            if self.next_capability_key is None:
                raise ValueError("ESCALATE requires next_capability_key")
            require_token(self.next_capability_key, "next capability key")
        elif self.next_capability_key is not None:
            raise ValueError("non-ESCALATE decision cannot carry next_capability_key")
        if self.id:
            validate_id(self.id, "qdec_")

    def with_identity(self) -> "QualityDecision":
        if self.id:
            return self
        return QualityDecision(
            self.target_id,
            self.decision,
            self.policy_key,
            self.policy_version,
            self.reason_code,
            self.next_capability_key,
            new_id("qdec_"),
        )


@runtime_checkable
class QualityPolicy(Protocol):
    @property
    def key(self) -> str:
        ...

    @property
    def version(self) -> str:
        ...

    def evaluate(
        self,
        *,
        descriptor: ProcessorDescriptor,
        result: ProcessorResult,
        target: TargetSnapshot,
        evidence: tuple[QualitySignal, ...],
        context: PolicyContext,
    ) -> QualityDecision:
        ...


def _signal_value(
    evidence: tuple[QualitySignal, ...], key: str, version: str = "v1"
) -> JSONValue | None:
    matches = [item.payload for item in evidence if item.signal_key == key and item.signal_version == version]
    if len(matches) > 1:
        raise QualityContractError(f"policy received duplicate signal {key}:{version}")
    return matches[0] if matches else None


class ReferenceEscalationPolicy:
    """Conservative runtime-observable policy proven by the closed processor bench.

    It intentionally does not encode CER/WER or a universal confidence threshold.
    Concrete adapters remain responsible for emitting their namespaced observable
    signals under registered contracts.
    """

    key = "reference_document_processing"
    version = "v1"

    def evaluate(
        self,
        *,
        descriptor: ProcessorDescriptor,
        result: ProcessorResult,
        target: TargetSnapshot,
        evidence: tuple[QualitySignal, ...],
        context: PolicyContext,
    ) -> QualityDecision:
        if result.outcome == "failed":
            return QualityDecision(
                target.id,
                "quarantine_review",
                self.key,
                self.version,
                "processor_failed",
            )

        capability = descriptor.capability_key
        has_material_output = bool(result.outputs)
        if capability == "text_extract":
            present = _signal_value(evidence, "native.page_text_present")
            nonempty = _signal_value(evidence, "core.output_nonempty")
            if present is True and nonempty is True and has_material_output:
                return QualityDecision(
                    target.id, "accept", self.key, self.version, "native_text_present"
                )
            if "ocr" in context.available_capabilities:
                return QualityDecision(
                    target.id,
                    "escalate",
                    self.key,
                    self.version,
                    "native_text_missing_or_suspicious",
                    "ocr",
                )
            return QualityDecision(
                target.id,
                "quarantine_review",
                self.key,
                self.version,
                "ocr_unavailable",
            )

        if capability == "ocr":
            needs_visual = _signal_value(evidence, "ocr.needs_visual_review")
            nonempty = _signal_value(evidence, "core.output_nonempty")
            if needs_visual is False and nonempty is True and has_material_output:
                return QualityDecision(
                    target.id, "accept", self.key, self.version, "ocr_accepted"
                )
            if "visual_transcribe" in context.available_capabilities:
                return QualityDecision(
                    target.id,
                    "escalate",
                    self.key,
                    self.version,
                    "ocr_requires_visual",
                    "visual_transcribe",
                )
            return QualityDecision(
                target.id,
                "quarantine_review",
                self.key,
                self.version,
                "visual_escalation_unavailable",
            )

        if capability == "visual_transcribe":
            schema_valid = _signal_value(evidence, "multimodal.schema_valid")
            uncertain = _signal_value(evidence, "multimodal.uncertain_span_count")
            nonempty = _signal_value(evidence, "core.output_nonempty")
            if schema_valid is True and uncertain == 0 and nonempty is True and has_material_output:
                return QualityDecision(
                    target.id, "accept", self.key, self.version, "visual_transcription_valid"
                )
            return QualityDecision(
                target.id,
                "quarantine_review",
                self.key,
                self.version,
                "visual_transcription_uncertain",
            )

        nonempty = _signal_value(evidence, "core.output_nonempty")
        if nonempty is True and has_material_output:
            return QualityDecision(
                target.id, "accept", self.key, self.version, "generic_output_present"
            )
        return QualityDecision(
            target.id,
            "quarantine_review",
            self.key,
            self.version,
            "no_accepted_policy_rule",
        )
