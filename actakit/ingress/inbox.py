"""Canonical Inbox implementation backed by the bounded Depósito writer."""

from __future__ import annotations

from dataclasses import dataclass

from actakit.deposit import (
    AcquisitionObservation,
    AcquisitionWrite,
    CapturedArtifact,
    DepositWriter,
    SourceLocatorRegistration,
    SourceRegistration,
)

from .models import (
    CaptureEnvelope,
    ConnectorDescriptor,
    IngressReceipt,
)


@dataclass(frozen=True, slots=True)
class InboxPolicy:
    """Core-owned custody policy applied after the connector boundary."""

    availability: str = "available"
    initial_validation_state: str = "pending"

    def __post_init__(self) -> None:
        if self.availability not in {"available", "restricted"}:
            raise ValueError(
                "Inbox availability policy must retain bytes as available or restricted"
            )
        if self.initial_validation_state not in {"pending", "quarantined"}:
            raise ValueError(
                "Inbox may initialize captured bytes only as pending or quarantined"
            )


class DepositInbox:
    """Bind one connector/source pair to the terrain-neutral Inbox socket.

    Connector code sees only ``InboxPort``.  Source identity, adapter attribution,
    custody validation state, canonical record IDs and Depósito writes are owned
    on this side of the boundary.
    """

    def __init__(
        self,
        writer: DepositWriter,
        source: SourceRegistration,
        connector: ConnectorDescriptor,
        *,
        policy: InboxPolicy | None = None,
    ) -> None:
        if not source.active:
            raise ValueError("Inbox cannot bind an inactive Source")
        self._writer = writer
        self._source = source
        self._connector = connector
        self._policy = policy or InboxPolicy()
        self._writer.register_source(source)

    @property
    def connector_descriptor(self) -> ConnectorDescriptor:
        return self._connector

    def accept(self, envelope: CaptureEnvelope) -> IngressReceipt:
        locator_id = None
        if envelope.locator is not None:
            locator_id = self._writer.register_source_locator(
                SourceLocatorRegistration(
                    # The SourceLocator identity is core-owned.  If the same
                    # locator already exists the Depósito writer reuses it.
                    id=self._new_locator_id(),
                    source_id=self._source.id,
                    locator=envelope.locator.value,
                    locator_kind=envelope.locator.kind,
                    created_at=envelope._created_at,
                )
            )

        observation = AcquisitionObservation(
            id=envelope._acquisition_id,
            source_id=self._source.id,
            source_locator_id=locator_id,
            observed_at=envelope.observed_at,
            outcome=envelope.outcome,
            http_status=envelope.http_status,
            adapter_key=self._connector.key,
            adapter_version=self._connector.version,
            error_code=envelope.error_code,
            created_at=envelope._created_at,
        )

        artifacts = tuple(
            CapturedArtifact(
                artifact_id=item._artifact_id,
                archive_object_id=item._archive_object_id,
                representation_id=item._representation_id,
                data=item.data,
                role=item.role,
                observed_filename=item.observed_filename,
                observed_url=item.observed_url,
                media_type=item.media_type,
                # Connectors may report observations but may not promote their
                # own bytes to verified custody state.
                validation_state=self._policy.initial_validation_state,
                availability=self._policy.availability,
                language=item.language,
                charset=item.charset,
                created_at=item._created_at,
            )
            for item in envelope.payloads
        )

        receipt = self._writer.record_acquisition(
            AcquisitionWrite(observation, artifacts)
        )
        return IngressReceipt(
            acquisition_ref=receipt.acquisition_id,
            artifact_count=len(receipt.artifacts),
            replayed=receipt.replayed,
        )

    @staticmethod
    def _new_locator_id() -> str:
        # Kept behind the Inbox so connector packages never allocate or depend on
        # canonical SourceLocator identity.
        from actakit.deposit import new_id

        return new_id("sloc_")
