"""Stable opaque Canario record identifiers and canonical timestamps."""

from __future__ import annotations

import re
import secrets
import time
import uuid
from datetime import datetime, timezone

_ID_PREFIX_RE = re.compile(r"^[a-z][a-z0-9_]*_$")
_RFC3339_UTC_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z$"
)


def utc_now() -> str:
    """Return a canonical UTC RFC3339 timestamp with millisecond precision."""

    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def validate_timestamp(value: str) -> str:
    if not _RFC3339_UTC_RE.fullmatch(value):
        raise ValueError(
            "canonical timestamps must be UTC RFC3339 with subsecond precision"
        )
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError(f"invalid canonical timestamp: {value!r}") from exc
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError(f"canonical timestamp is not UTC: {value!r}")
    return value


def new_id(prefix: str, *, unix_ms: int | None = None) -> str:
    """Create a readable-prefix UUIDv7-compatible opaque identifier."""

    if not _ID_PREFIX_RE.fullmatch(prefix):
        raise ValueError(f"invalid record ID prefix: {prefix!r}")
    timestamp_ms = time.time_ns() // 1_000_000 if unix_ms is None else unix_ms
    if not 0 <= timestamp_ms < (1 << 48):
        raise ValueError("UUIDv7 timestamp is outside the 48-bit range")

    rand_a = secrets.randbits(12)
    rand_b = secrets.randbits(62)
    value = (
        (timestamp_ms << 80)
        | (0x7 << 76)
        | (rand_a << 64)
        | (0b10 << 62)
        | rand_b
    )
    return prefix + str(uuid.UUID(int=value))


def validate_id(value: str, prefix: str) -> str:
    if not value.startswith(prefix):
        raise ValueError(f"expected {prefix!r}-prefixed opaque ID: {value!r}")
    raw = value[len(prefix) :]
    try:
        parsed = uuid.UUID(raw)
    except ValueError as exc:
        raise ValueError(f"invalid opaque UUID value: {value!r}") from exc
    if parsed.version != 7 or parsed.variant != uuid.RFC_4122:
        raise ValueError(f"opaque ID is not UUIDv7-compatible: {value!r}")
    return value
