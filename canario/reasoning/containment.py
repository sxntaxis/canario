"""Conservative registered containment for source RepresentationTarget selectors."""

from __future__ import annotations

import json
import re

from canario.processors.contracts import TargetSnapshot
from canario.processors.targets import TargetRegistry

_A1 = re.compile(r"^([A-Z]+)([1-9][0-9]*)(?::([A-Z]+)([1-9][0-9]*))?$")


def _column_number(value: str) -> int:
    result = 0
    for char in value:
        result = result * 26 + (ord(char) - ord("A") + 1)
    return result


def _a1_bounds(value: str) -> tuple[int, int, int, int] | None:
    match = _A1.fullmatch(value)
    if match is None:
        return None
    c1, r1, c2, r2 = match.groups()
    start_col = _column_number(c1)
    start_row = int(r1)
    end_col = _column_number(c2 or c1)
    end_row = int(r2 or r1)
    if end_col < start_col or end_row < start_row:
        return None
    return start_col, start_row, end_col, end_row


def _table_contains(outer: dict, inner: dict) -> bool:
    for field in ("sheet", "table_name"):
        if field in outer and inner.get(field) != outer[field]:
            return False
    if "a1_range" in outer:
        if "a1_range" not in inner:
            return False
        ob = _a1_bounds(outer["a1_range"])
        ib = _a1_bounds(inner["a1_range"])
        if ob is None or ib is None:
            return False
        if not (ob[0] <= ib[0] and ob[1] <= ib[1] and ob[2] >= ib[2] and ob[3] >= ib[3]):
            return False
    if "row_start" in outer:
        if "row_start" not in inner:
            return False
        if outer["row_start"] > inner["row_start"] or outer["row_end"] < inner["row_end"]:
            return False
    # Headers/observed values are evidence-strengthening payload, not structural scope authority.
    return any(key in outer for key in ("sheet", "table_name", "a1_range", "row_start"))


def contains(
    outer: TargetSnapshot,
    inner: TargetSnapshot,
    *,
    registry: TargetRegistry | None = None,
) -> bool:
    """Return True only when the registered selector semantics prove containment.

    Unknown/cross-Representation relationships fail closed. This intentionally prefers false
    negatives to widening evidence scope by guesswork.
    """

    registry = registry or TargetRegistry()
    outer_payload = registry.validate(
        outer.selector_kind, outer.selector_version, outer.selector_payload_json
    )
    inner_payload = registry.validate(
        inner.selector_kind, inner.selector_version, inner.selector_payload_json
    )
    if outer.representation_id != inner.representation_id:
        return False
    if outer.id == inner.id:
        return True
    if (outer.selector_kind, outer.selector_version) == ("whole", "v1"):
        return True

    op = json.loads(outer_payload)
    ip = json.loads(inner_payload)
    outer_key = (outer.selector_kind, outer.selector_version)
    inner_key = (inner.selector_kind, inner.selector_version)

    if outer_key == ("pdf_page", "v1"):
        return inner_key in {("pdf_page", "v1"), ("pdf_page_quote", "v1")} and (
            op.get("page_ordinal") == ip.get("page_ordinal")
        )
    if outer_key == ("pdf_page_quote", "v1"):
        return inner_key == outer_key and outer_payload == inner_payload
    if outer_key == ("text_quote", "v1") and inner_key == outer_key:
        if "start_char" in op and "start_char" in ip:
            return op["start_char"] <= ip["start_char"] and op["end_char"] >= ip["end_char"]
        return outer_payload == inner_payload
    if outer_key == ("table_range", "v1") and inner_key == outer_key:
        return _table_contains(op, ip)
    if outer_key == ("media", "v1") and inner_key == outer_key:
        return (
            op.get("media_sha256") == ip.get("media_sha256")
            and op.get("duration_us") == ip.get("duration_us")
            and op.get("start_us") <= ip.get("start_us")
            and op.get("end_us") >= ip.get("end_us")
        )
    return False
