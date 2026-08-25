"""Registered, bounded RepresentationTarget selector contracts."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Callable

from canario.deposit.ids import validate_id, validate_timestamp

from .contracts import JSONValue, require_token

TargetValidator = Callable[[dict[str, JSONValue]], None]
_A1_RE = re.compile(r"^[A-Z]+[1-9][0-9]*(?::[A-Z]+[1-9][0-9]*)?$")
_MAX_SELECTOR_JSON_BYTES = 64 * 1024
_MAX_SELECTOR_TEXT_CHARS = 16 * 1024
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class TargetContractError(ValueError):
    """A selector is unknown or violates its registered bounded contract."""


def _json_object(payload_json: str) -> dict[str, JSONValue]:
    try:
        value = json.loads(payload_json)
    except json.JSONDecodeError as exc:
        raise TargetContractError("selector payload is not valid JSON") from exc
    if not isinstance(value, dict):
        raise TargetContractError("selector payload must be a JSON object")
    return value


def _only(payload: dict[str, JSONValue], allowed: set[str]) -> None:
    unknown = set(payload) - allowed
    if unknown:
        raise TargetContractError(f"unknown selector fields: {sorted(unknown)!r}")


def _nonempty_string(value: JSONValue, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TargetContractError(f"{field} must be a non-empty string")
    if len(value) > _MAX_SELECTOR_TEXT_CHARS:
        raise TargetContractError(f"{field} exceeds the bounded selector text limit")
    return value


def _validate_whole(payload: dict[str, JSONValue]) -> None:
    if payload:
        raise TargetContractError("whole:v1 selector must be exactly {}")


def _validate_pdf_page_scope(payload: dict[str, JSONValue]) -> None:
    _only(payload, {"page_ordinal", "page_label"})
    ordinal = payload.get("page_ordinal")
    if not isinstance(ordinal, int) or isinstance(ordinal, bool) or ordinal < 1:
        raise TargetContractError("pdf_page:v1 page_ordinal must be a positive integer")
    if "page_label" in payload:
        _nonempty_string(payload["page_label"], "page_label")


def _validate_pdf_page(payload: dict[str, JSONValue]) -> None:
    _only(payload, {"page_ordinal", "exact", "prefix", "suffix", "page_label"})
    ordinal = payload.get("page_ordinal")
    if not isinstance(ordinal, int) or isinstance(ordinal, bool) or ordinal < 1:
        raise TargetContractError("pdf_page_quote:v1 page_ordinal must be a positive integer")
    for key in ("exact", "prefix", "suffix", "page_label"):
        if key in payload:
            _nonempty_string(payload[key], key)


def _validate_text_quote(payload: dict[str, JSONValue]) -> None:
    _only(payload, {"exact", "prefix", "suffix", "start_char", "end_char"})
    _nonempty_string(payload.get("exact"), "exact")
    for key in ("prefix", "suffix"):
        if key in payload:
            _nonempty_string(payload[key], key)
    start = payload.get("start_char")
    end = payload.get("end_char")
    if (start is None) != (end is None):
        raise TargetContractError("text_quote offsets must be both present or both absent")
    if start is not None:
        if any(isinstance(v, bool) or not isinstance(v, int) for v in (start, end)):
            raise TargetContractError("text_quote offsets must be integers")
        assert isinstance(start, int) and isinstance(end, int)
        if start < 0 or end <= start:
            raise TargetContractError("text_quote offsets must satisfy 0 <= start < end")


def _validate_table_range(payload: dict[str, JSONValue]) -> None:
    allowed = {
        "sheet", "table_name", "a1_range", "row_start", "row_end", "headers", "observed_values"
    }
    _only(payload, allowed)
    structural = {"sheet", "table_name", "a1_range", "row_start", "row_end"} & set(payload)
    if not structural:
        raise TargetContractError("table_range:v1 requires at least one structural coordinate")
    for key in ("sheet", "table_name"):
        if key in payload:
            _nonempty_string(payload[key], key)
    if "a1_range" in payload:
        value = _nonempty_string(payload["a1_range"], "a1_range")
        if not _A1_RE.fullmatch(value):
            raise TargetContractError("table_range:v1 a1_range is not a bounded A1 coordinate")
    start = payload.get("row_start")
    end = payload.get("row_end")
    if (start is None) != (end is None):
        raise TargetContractError("table row_start/row_end must be both present or both absent")
    if start is not None:
        if any(isinstance(v, bool) or not isinstance(v, int) for v in (start, end)):
            raise TargetContractError("table row bounds must be integers")
        assert isinstance(start, int) and isinstance(end, int)
        if start < 1 or end < start:
            raise TargetContractError("table row bounds must satisfy 1 <= start <= end")
    if "headers" in payload:
        headers = payload["headers"]
        if (
            not isinstance(headers, list)
            or len(headers) > 256
            or not all(isinstance(v, str) and len(v) <= 4096 for v in headers)
        ):
            raise TargetContractError("headers must be a bounded ordered JSON string array")
    if "observed_values" in payload:
        rows = payload["observed_values"]
        if not isinstance(rows, list) or len(rows) > 256:
            raise TargetContractError("observed_values must be a bounded row array")
        for row in rows:
            if not isinstance(row, list) or len(row) > 64:
                raise TargetContractError("each observed_values row must be a bounded cell array")
            for cell in row:
                if isinstance(cell, (list, dict)):
                    if not isinstance(cell, dict) or set(cell) != {"type", "value"}:
                        raise TargetContractError("typed table cells must contain type and value")
                    if not isinstance(cell["type"], str) or cell["type"] not in {
                        "boolean", "integer", "number", "string", "datetime", "formula"
                    }:
                        raise TargetContractError("typed table cell has an unknown type")
                    if cell["type"] == "string" and (
                        not isinstance(cell["value"], str) or len(cell["value"]) > 4096
                    ):
                        raise TargetContractError("typed table string cell is too long")
                elif isinstance(cell, str) and len(cell) > 4096:
                    raise TargetContractError("observed_values cells must be bounded JSON scalars")


def _validate_media(payload: dict[str, JSONValue]) -> None:
    _only(payload, {
        "media_sha256", "duration_us", "start_us", "end_us", "transcript_target_id",
        "transcript_exact", "transcript_start_char", "transcript_end_char",
    })
    digest = payload.get("media_sha256")
    if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
        raise TargetContractError("media:v1 requires a lowercase media_sha256")
    start = payload.get("start_us")
    end = payload.get("end_us")
    duration = payload.get("duration_us")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in (duration, start, end)):
        raise TargetContractError("media:v1 times must be integer microseconds")
    assert isinstance(duration, int) and isinstance(start, int) and isinstance(end, int)
    if duration <= 0 or start < 0 or end <= start or end > duration:
        raise TargetContractError("media:v1 requires 0 <= start_us < end_us")
    anchor_fields = {
        "transcript_target_id", "transcript_exact", "transcript_start_char", "transcript_end_char"
    }
    present = anchor_fields & set(payload)
    if present and present != anchor_fields:
        raise TargetContractError("media transcript anchor must be complete")
    if present:
        try:
            validate_id(payload["transcript_target_id"], "transcript target")
        except (TypeError, ValueError) as exc:
            raise TargetContractError("media transcript target is invalid") from exc
        _nonempty_string(payload["transcript_exact"], "transcript_exact")
        anchor_start = payload["transcript_start_char"]
        anchor_end = payload["transcript_end_char"]
        if any(isinstance(value, bool) or not isinstance(value, int) for value in (anchor_start, anchor_end)):
            raise TargetContractError("transcript anchor offsets must be integers")
        if anchor_start < 0 or anchor_end <= anchor_start:
            raise TargetContractError("transcript anchor offsets are invalid")


DEFAULT_TARGET_CONTRACTS: dict[tuple[str, str], TargetValidator] = {
    ("whole", "v1"): _validate_whole,
    ("pdf_page", "v1"): _validate_pdf_page_scope,
    ("pdf_page_quote", "v1"): _validate_pdf_page,
    ("text_quote", "v1"): _validate_text_quote,
    ("table_range", "v1"): _validate_table_range,
    ("media", "v1"): _validate_media,
}


@dataclass(frozen=True, slots=True)
class TargetRegistration:
    id: str
    representation_id: str
    selector_kind: str
    selector_version: str
    selector_payload_json: str
    created_at: str

    def __post_init__(self) -> None:
        validate_id(self.id, "rtgt_")
        validate_id(self.representation_id, "rep_")
        require_token(self.selector_kind, "selector kind")
        require_token(self.selector_version, "selector version")
        validate_timestamp(self.created_at)


class TargetRegistry:
    def __init__(self, contracts: dict[tuple[str, str], TargetValidator] | None = None) -> None:
        self._contracts = dict(DEFAULT_TARGET_CONTRACTS if contracts is None else contracts)

    def validate(self, kind: str, version: str, payload_json: str) -> str:
        validator = self._contracts.get((kind, version))
        if validator is None:
            raise TargetContractError(f"unknown selector contract: {kind}:{version}")
        payload = _json_object(payload_json)
        validator(payload)
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        if len(canonical.encode("utf-8")) > _MAX_SELECTOR_JSON_BYTES:
            raise TargetContractError("selector payload exceeds 64 KiB canonical limit")
        return canonical

    def knows(self, kind: str, version: str) -> bool:
        return (kind, version) in self._contracts
