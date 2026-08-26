"""Bounded registries for analytical result selectors and verification profiles."""

from __future__ import annotations

import json
from typing import Callable

from canario.processors.contracts import JSONValue, TargetSnapshot

JsonObject = dict[str, JSONValue]
Validator = Callable[[JsonObject], None]
ResultMaterializer = Callable[[JsonObject, bytes], bytes]
_MAX_JSON_BYTES = 128 * 1024


class ReasoningContractError(ValueError):
    """A registered reasoning payload violated its bounded contract."""


def _object(payload_json: str) -> JsonObject:
    try:
        value = json.loads(payload_json)
    except json.JSONDecodeError as exc:
        raise ReasoningContractError("payload is not valid JSON") from exc
    if not isinstance(value, dict):
        raise ReasoningContractError("payload must be a JSON object")
    return value


def _empty(payload: JsonObject) -> None:
    if payload:
        raise ReasoningContractError("profile/selector must be exactly {}")


def _canonical(payload_json: str, validator: Validator) -> str:
    value = _object(payload_json)
    validator(value)
    try:
        canonical = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ReasoningContractError("payload is not bounded canonical JSON") from exc
    if len(canonical.encode("utf-8")) > _MAX_JSON_BYTES:
        raise ReasoningContractError("payload exceeds the 128 KiB canonical limit")
    return canonical


def _full_result_material(_payload: JsonObject, result_bytes: bytes) -> bytes:
    return result_bytes


class ResultTargetRegistry:
    """Registered selector semantics for exact slices of DerivationResult.

    Validation and materialization are intentionally separate capabilities. Registering a new
    result selector does not authorize a verifier to see the entire result: a narrower selector
    is consumable only when an exact materializer for that kind/version is also registered.
    """

    def __init__(
        self,
        contracts: dict[tuple[str, str], Validator] | None = None,
        *,
        materializers: dict[tuple[str, str], ResultMaterializer] | None = None,
    ) -> None:
        default = {("whole", "v1"): _empty, ("scalar", "v1"): _empty}
        self._contracts = dict(default if contracts is None else contracts)
        self._materializers: dict[tuple[str, str], ResultMaterializer] = {
            ("whole", "v1"): _full_result_material,
            ("scalar", "v1"): _full_result_material,
        }
        if materializers is not None:
            self._materializers.update(materializers)

    def validate(self, kind: str, version: str, payload_json: str) -> str:
        validator = self._contracts.get((kind, version))
        if validator is None:
            raise ReasoningContractError(f"unknown result selector contract: {kind}:{version}")
        return _canonical(payload_json, validator)

    def materialize(
        self, kind: str, version: str, payload_json: str, result_bytes: bytes
    ) -> bytes:
        canonical = self.validate(kind, version, payload_json)
        materializer = self._materializers.get((kind, version))
        if materializer is None:
            raise ReasoningContractError(
                f"no bounded result materializer is registered for {kind}:{version}"
            )
        material = materializer(_object(canonical), result_bytes)
        if not isinstance(material, bytes):
            raise ReasoningContractError("result materializer must return immutable bytes")
        return material


class VerificationProfileRegistry:
    """Registered bounded payloads for verification scope and sufficiency semantics.

    The default `explicit_targets:v1` scope is deliberately weak: exact target membership is
    authoritative, but the empty payload makes no inventory/completeness claim. Deployments that
    need negative/absence proofs must register a richer scope profile rather than treating an empty
    query result as evidence of non-existence.
    """

    def __init__(
        self,
        *,
        scope_contracts: dict[tuple[str, str], Validator] | None = None,
        sufficiency_contracts: dict[tuple[str, str], Validator] | None = None,
    ) -> None:
        self._scope = dict(
            {("explicit_targets", "v1"): _empty}
            if scope_contracts is None
            else scope_contracts
        )
        self._sufficiency = dict(
            {("explicit", "v1"): _empty}
            if sufficiency_contracts is None
            else sufficiency_contracts
        )

    def validate_scope(self, key: str, version: str, payload_json: str) -> str:
        validator = self._scope.get((key, version))
        if validator is None:
            raise ReasoningContractError(f"unknown verification scope profile: {key}:{version}")
        return _canonical(payload_json, validator)

    def validate_sufficiency(self, key: str, version: str, payload_json: str) -> str:
        validator = self._sufficiency.get((key, version))
        if validator is None:
            raise ReasoningContractError(
                f"unknown verification sufficiency profile: {key}:{version}"
            )
        return _canonical(payload_json, validator)


SourceMaterializer = Callable[[TargetSnapshot, bytes, str | None], bytes]


def _whole_material(_target: TargetSnapshot, source_bytes: bytes, _charset: str | None) -> bytes:
    return source_bytes


class SourceMaterializerRegistry:
    """Host-owned materializers for exact source target scopes.

    The default registry intentionally supports only ``whole:v1``. A narrower selector is not
    permission to hand an entire Representation to an analytical/verifier backend. Formats such as
    PDF pages, media spans, or table slices need an explicitly registered materializer that can
    isolate the selected scope without widening it.
    """

    def __init__(
        self, extra_contracts: dict[tuple[str, str], SourceMaterializer] | None = None
    ) -> None:
        self._contracts: dict[tuple[str, str], SourceMaterializer] = {
            ("whole", "v1"): _whole_material
        }
        if extra_contracts is not None:
            self._contracts.update(extra_contracts)

    def materialize(
        self, target: TargetSnapshot, source_bytes: bytes, charset: str | None
    ) -> bytes:
        materializer = self._contracts.get((target.selector_kind, target.selector_version))
        if materializer is None:
            raise ReasoningContractError(
                "no bounded source materializer is registered for "
                f"{target.selector_kind}:{target.selector_version}"
            )
        material = materializer(target, source_bytes, charset)
        if not isinstance(material, bytes):
            raise ReasoningContractError(
                "source materializer must return immutable bytes"
            )
        return material

    def knows(self, kind: str, version: str) -> bool:
        return (kind, version) in self._contracts
