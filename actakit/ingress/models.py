"""Terrain-neutral DTOs accepted by the ActaKit Inbox boundary.

Connectors construct these values.  They intentionally describe observations and
bytes, not civic documents or Depósito persistence rows.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from actakit.deposit.ids import new_id, utc_now, validate_id, validate_timestamp

CAPTURE_OUTCOMES = frozenset({"success", "partial", "not_found", "failed"})
CAPTURE_ROLES = frozenset({"primary", "attachment", "response_body", "other"})
CONNECTOR_CAPABILITIES = frozenset(
    {"pull", "push", "inventory", "incremental", "checkpointing"}
)
RUN_COVERAGE = frozenset({"unknown", "incremental", "complete_inventory"})

_CONNECTOR_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def _nonempty(value: str, field_name: str) -> str:
    if not value or not value.strip():
        raise ValueError(f"{field_name} must be non-empty")
    return value


def _optional_nonempty(value: str | None, field_name: str) -> str | None:
    if value is not None:
        _nonempty(value, field_name)
    return value


@dataclass(frozen=True, slots=True)
class ConnectorDescriptor:
    """Stable identity/capabilities of one connector implementation."""

    key: str
    version: str
    capabilities: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not _CONNECTOR_KEY_RE.fullmatch(self.key):
            raise ValueError(
                "connector key must be a lowercase package-like token "
                "([a-z0-9._-])"
            )
        _nonempty(self.version, "connector version")
        if not isinstance(self.capabilities, frozenset):
            raise TypeError("connector capabilities must be a frozenset")
        unknown = self.capabilities - CONNECTOR_CAPABILITIES
        if unknown:
            raise ValueError(f"unknown connector capabilities: {sorted(unknown)!r}")


@dataclass(frozen=True, slots=True)
class ObservedLocator:
    """A source-specific place from which an observation was attempted."""

    value: str
    kind: str

    def __post_init__(self) -> None:
        _nonempty(self.value, "locator value")
        _nonempty(self.kind, "locator kind")


@dataclass(frozen=True, slots=True)
class CapturePayload:
    """One byte payload delivered through the Inbox.

    The private IDs are preallocated by the boundary factory so retrying the same
    immutable object is an exact retry at the Depósito writer boundary.  Connector
    code should treat them as implementation details.
    """

    data: bytes
    role: str = "primary"
    observed_filename: str | None = None
    observed_url: str | None = None
    media_type: str | None = None
    language: str | None = None
    charset: str | None = None
    _artifact_id: str = field(default_factory=lambda: new_id("art_"), init=False, repr=False)
    _archive_object_id: str = field(default_factory=lambda: new_id("aob_"), init=False, repr=False)
    _representation_id: str = field(default_factory=lambda: new_id("rep_"), init=False, repr=False)
    _created_at: str = field(default_factory=utc_now, init=False, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.data, bytes):
            raise TypeError("capture payload data must be immutable bytes")
        if self.role not in CAPTURE_ROLES:
            raise ValueError(f"invalid capture payload role: {self.role!r}")
        _optional_nonempty(self.observed_filename, "observed filename")
        _optional_nonempty(self.observed_url, "observed URL")
        _optional_nonempty(self.media_type, "media type")
        _optional_nonempty(self.language, "language")
        _optional_nonempty(self.charset, "charset")
        validate_id(self._artifact_id, "art_")
        validate_id(self._archive_object_id, "aob_")
        validate_id(self._representation_id, "rep_")
        validate_timestamp(self._created_at)


@dataclass(frozen=True, slots=True)
class CaptureEnvelope:
    """The terrain-neutral socket shape delivered by every source connector."""

    observed_at: str
    outcome: str
    payloads: tuple[CapturePayload, ...] = ()
    locator: ObservedLocator | None = None
    http_status: int | None = None
    error_code: str | None = None
    _acquisition_id: str = field(default_factory=lambda: new_id("acq_"), init=False, repr=False)
    _created_at: str = field(default_factory=utc_now, init=False, repr=False)

    def __post_init__(self) -> None:
        validate_timestamp(self.observed_at)
        validate_timestamp(self._created_at)
        validate_id(self._acquisition_id, "acq_")
        if self.outcome not in CAPTURE_OUTCOMES:
            raise ValueError(f"invalid capture outcome: {self.outcome!r}")
        if self.http_status is not None and not 100 <= self.http_status <= 599:
            raise ValueError(f"invalid HTTP status: {self.http_status}")
        _optional_nonempty(self.error_code, "error code")
        if not isinstance(self.payloads, tuple):
            raise TypeError("CaptureEnvelope payloads must be a tuple")
        if not all(isinstance(item, CapturePayload) for item in self.payloads):
            raise TypeError("CaptureEnvelope payloads must contain CapturePayload values")
        if len({item._artifact_id for item in self.payloads}) != len(self.payloads):
            raise ValueError("one CaptureEnvelope cannot reuse an internal payload identity")

    @classmethod
    def now(
        cls,
        *,
        outcome: str,
        payloads: tuple[CapturePayload, ...] = (),
        locator: ObservedLocator | None = None,
        http_status: int | None = None,
        error_code: str | None = None,
    ) -> "CaptureEnvelope":
        return cls(
            utc_now(),
            outcome,
            payloads,
            locator,
            http_status,
            error_code,
        )


@dataclass(frozen=True, slots=True)
class IngressReceipt:
    """Minimal acknowledgement returned to connector code."""

    acquisition_ref: str
    artifact_count: int
    replayed: bool

    def __post_init__(self) -> None:
        validate_id(self.acquisition_ref, "acq_")
        if self.artifact_count < 0:
            raise ValueError("artifact_count cannot be negative")


@dataclass(frozen=True, slots=True)
class ConnectorRunResult:
    """Connector-level run summary; not canonical civic truth."""

    coverage: str
    emitted: int
    next_checkpoint: bytes | None = None

    def __post_init__(self) -> None:
        if self.coverage not in RUN_COVERAGE:
            raise ValueError(f"invalid connector coverage: {self.coverage!r}")
        if self.emitted < 0:
            raise ValueError("connector emitted count cannot be negative")
        if self.next_checkpoint is not None and not isinstance(
            self.next_checkpoint, bytes
        ):
            raise TypeError("connector checkpoints are opaque bytes")
