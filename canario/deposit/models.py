"""Bounded Depósito write contracts.

These types intentionally stop at acquired custody. They do not model documents,
claims, review, or outputs.
"""

from __future__ import annotations

from dataclasses import dataclass

from .ids import new_id, utc_now, validate_id, validate_timestamp

SOURCE_KINDS = frozenset({"web", "api", "feed", "filesystem", "manual", "other"})
ACQUISITION_OUTCOMES = frozenset({"success", "partial", "not_found", "failed"})
ARTIFACT_ROLES = frozenset({"primary", "attachment", "response_body", "other"})
VALIDATION_STATES = frozenset({"pending", "verified", "quarantined", "rejected"})
RETAINED_AVAILABILITY = frozenset({"available", "restricted"})


def _nonempty(value: str, field: str) -> str:
    if not value or not value.strip():
        raise ValueError(f"{field} must be non-empty")
    return value


def _optional_nonempty(value: str | None, field: str) -> str | None:
    if value is not None:
        _nonempty(value, field)
    return value


@dataclass(frozen=True, slots=True)
class SourceRegistration:
    id: str
    kind: str
    name: str
    active: bool
    created_at: str

    def __post_init__(self) -> None:
        validate_id(self.id, "src_")
        if self.kind not in SOURCE_KINDS:
            raise ValueError(f"invalid source kind: {self.kind!r}")
        if type(self.active) is not bool:
            raise TypeError("Source.active must be a bool")
        _nonempty(self.name, "source name")
        validate_timestamp(self.created_at)

    @classmethod
    def new(cls, *, kind: str, name: str, active: bool = True) -> "SourceRegistration":
        return cls(new_id("src_"), kind, name, active, utc_now())


@dataclass(frozen=True, slots=True)
class SourceLocatorRegistration:
    id: str
    source_id: str
    locator: str
    locator_kind: str
    created_at: str

    def __post_init__(self) -> None:
        validate_id(self.id, "sloc_")
        validate_id(self.source_id, "src_")
        _nonempty(self.locator, "source locator")
        _nonempty(self.locator_kind, "locator kind")
        validate_timestamp(self.created_at)

    @classmethod
    def new(
        cls, *, source_id: str, locator: str, locator_kind: str
    ) -> "SourceLocatorRegistration":
        return cls(new_id("sloc_"), source_id, locator, locator_kind, utc_now())


@dataclass(frozen=True, slots=True)
class AcquisitionObservation:
    id: str
    source_id: str
    source_locator_id: str | None
    observed_at: str
    outcome: str
    http_status: int | None
    adapter_key: str
    adapter_version: str
    error_code: str | None
    created_at: str

    def __post_init__(self) -> None:
        validate_id(self.id, "acq_")
        validate_id(self.source_id, "src_")
        if self.source_locator_id is not None:
            validate_id(self.source_locator_id, "sloc_")
        validate_timestamp(self.observed_at)
        validate_timestamp(self.created_at)
        if self.outcome not in ACQUISITION_OUTCOMES:
            raise ValueError(f"invalid acquisition outcome: {self.outcome!r}")
        if self.http_status is not None and not 100 <= self.http_status <= 599:
            raise ValueError(f"invalid HTTP status: {self.http_status}")
        _nonempty(self.adapter_key, "adapter key")
        _nonempty(self.adapter_version, "adapter version")
        _optional_nonempty(self.error_code, "error code")

    @classmethod
    def new(
        cls,
        *,
        source_id: str,
        source_locator_id: str | None,
        observed_at: str,
        outcome: str,
        adapter_key: str,
        adapter_version: str,
        http_status: int | None = None,
        error_code: str | None = None,
        created_at: str | None = None,
    ) -> "AcquisitionObservation":
        timestamp = utc_now() if created_at is None else created_at
        return cls(
            new_id("acq_"),
            source_id,
            source_locator_id,
            observed_at,
            outcome,
            http_status,
            adapter_key,
            adapter_version,
            error_code,
            timestamp,
        )


@dataclass(frozen=True, slots=True)
class CapturedArtifact:
    artifact_id: str
    archive_object_id: str
    representation_id: str
    data: bytes
    role: str
    observed_filename: str | None
    observed_url: str | None
    media_type: str | None
    validation_state: str
    availability: str
    language: str | None
    charset: str | None
    created_at: str

    def __post_init__(self) -> None:
        validate_id(self.artifact_id, "art_")
        validate_id(self.archive_object_id, "aob_")
        validate_id(self.representation_id, "rep_")
        if not isinstance(self.data, bytes):
            raise TypeError("captured artifact data must be immutable bytes")
        if self.role not in ARTIFACT_ROLES:
            raise ValueError(f"invalid acquisition artifact role: {self.role!r}")
        if self.validation_state not in VALIDATION_STATES:
            raise ValueError(f"invalid Artifact validation state: {self.validation_state!r}")
        if self.availability not in RETAINED_AVAILABILITY:
            raise ValueError(
                "new captured Artifacts must be retained as available or restricted"
            )
        _optional_nonempty(self.observed_filename, "observed filename")
        _optional_nonempty(self.observed_url, "observed URL")
        _optional_nonempty(self.media_type, "media type")
        _optional_nonempty(self.language, "language")
        _optional_nonempty(self.charset, "charset")
        validate_timestamp(self.created_at)

    @classmethod
    def new(
        cls,
        *,
        data: bytes,
        role: str,
        validation_state: str,
        availability: str = "available",
        observed_filename: str | None = None,
        observed_url: str | None = None,
        media_type: str | None = None,
        language: str | None = None,
        charset: str | None = None,
        created_at: str | None = None,
    ) -> "CapturedArtifact":
        timestamp = utc_now() if created_at is None else created_at
        return cls(
            new_id("art_"),
            new_id("aob_"),
            new_id("rep_"),
            data,
            role,
            observed_filename,
            observed_url,
            media_type,
            validation_state,
            availability,
            language,
            charset,
            timestamp,
        )


@dataclass(frozen=True, slots=True)
class AcquisitionWrite:
    observation: AcquisitionObservation
    artifacts: tuple[CapturedArtifact, ...] = ()

    def __post_init__(self) -> None:
        ids = [artifact.artifact_id for artifact in self.artifacts]
        rep_ids = [artifact.representation_id for artifact in self.artifacts]
        aob_ids = [artifact.archive_object_id for artifact in self.artifacts]
        if len(ids) != len(set(ids)):
            raise ValueError("one acquisition operation cannot reuse an Artifact ID")
        if len(rep_ids) != len(set(rep_ids)):
            raise ValueError("one acquisition operation cannot reuse a Representation ID")
        if len(aob_ids) != len(set(aob_ids)):
            raise ValueError("one acquisition operation cannot reuse a candidate ArchiveObject ID")
