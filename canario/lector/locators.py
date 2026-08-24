"""Runtime reopening for selector proposals emitted by semantic extractors."""

from __future__ import annotations

import json
from typing import Any


class SemanticLocatorError(ValueError):
    """A semantic evidence selector cannot be reopened against exact input bytes."""


def _decode_text(source_bytes: bytes, charset: str | None) -> str:
    encoding = charset or "utf-8"
    try:
        return source_bytes.decode(encoding)
    except (LookupError, UnicodeDecodeError) as exc:
        raise SemanticLocatorError(
            f"text evidence cannot decode Representation with charset {encoding!r}"
        ) from exc


def _text_quote(payload: dict[str, Any], source_bytes: bytes, charset: str | None) -> None:
    text = _decode_text(source_bytes, charset)
    exact = payload["exact"]
    start = payload.get("start_char")
    end = payload.get("end_char")
    prefix = payload.get("prefix")
    suffix = payload.get("suffix")
    if start is not None:
        assert isinstance(start, int) and isinstance(end, int)
        if end > len(text) or text[start:end] != exact:
            raise SemanticLocatorError("text_quote offsets do not reopen exact source text")
        if prefix is not None and not text[:start].endswith(prefix):
            raise SemanticLocatorError("text_quote prefix does not match exact source context")
        if suffix is not None and not text[end:].startswith(suffix):
            raise SemanticLocatorError("text_quote suffix does not match exact source context")
        return
    starts: list[int] = []
    position = 0
    while True:
        found = text.find(exact, position)
        if found < 0:
            break
        after = found + len(exact)
        if prefix is not None and not text[:found].endswith(prefix):
            position = found + 1
            continue
        if suffix is not None and not text[after:].startswith(suffix):
            position = found + 1
            continue
        starts.append(found)
        position = found + 1
    if len(starts) != 1:
        raise SemanticLocatorError(
            "text_quote without offsets must resolve to exactly one source occurrence"
        )


def _rows_from_table_value(value: Any, table_name: str | None) -> list[Any]:
    if isinstance(value, list):
        return value
    if not isinstance(value, dict):
        raise SemanticLocatorError("table Representation JSON must be an array or object")
    rows = value.get("rows")
    if isinstance(rows, list):
        return rows
    tables = value.get("tables")
    if not isinstance(tables, list) or not tables:
        raise SemanticLocatorError("table Representation JSON has no reopenable rows")
    if table_name is not None:
        matches = [
            item
            for item in tables
            if isinstance(item, dict)
            and item.get("name") == table_name
            and isinstance(item.get("rows"), list)
        ]
        if len(matches) != 1:
            raise SemanticLocatorError(
                "table_name does not resolve to exactly one represented table"
            )
        return matches[0]["rows"]
    if len(tables) != 1 or not isinstance(tables[0], dict) or not isinstance(
        tables[0].get("rows"), list
    ):
        raise SemanticLocatorError(
            "multi-table Representation requires a stable table_name for row reopening"
        )
    return tables[0]["rows"]


def _table_range(payload: dict[str, Any], source_bytes: bytes, charset: str | None) -> None:
    text = _decode_text(source_bytes, charset)
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SemanticLocatorError("table Representation is not valid JSON") from exc
    start = payload.get("row_start")
    end = payload.get("row_end")
    observed = payload.get("observed_values")
    if start is None or end is None or observed is None:
        raise SemanticLocatorError(
            "LECTOR-001 table evidence requires row_start, row_end and observed_values"
        )
    assert isinstance(start, int) and isinstance(end, int)
    rows = _rows_from_table_value(value, payload.get("table_name"))
    selected = rows[start - 1 : end]
    if selected != observed:
        raise SemanticLocatorError(
            "table_range observed values do not reopen exact represented rows"
        )


def reopen_selector(
    selector_kind: str,
    selector_version: str,
    canonical_payload_json: str,
    *,
    source_bytes: bytes,
    charset: str | None,
) -> None:
    """Prove a Lector-created selector against exact Representation bytes."""

    try:
        payload = json.loads(canonical_payload_json)
    except json.JSONDecodeError as exc:
        raise SemanticLocatorError("canonical selector payload is invalid JSON") from exc
    if not isinstance(payload, dict):
        raise SemanticLocatorError("canonical selector payload must be an object")
    key = (selector_kind, selector_version)
    if key == ("text_quote", "v1"):
        _text_quote(payload, source_bytes, charset)
        return
    if key == ("table_range", "v1"):
        _table_range(payload, source_bytes, charset)
        return
    raise SemanticLocatorError(
        f"LECTOR-001 cannot create selector without runtime reopening: {selector_kind}:{selector_version}"
    )
