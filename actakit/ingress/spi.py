"""Source Connector SPI and Inbox port.

The SPI deliberately says nothing about HTML, APIs, browsers, filesystems, civic
record types, or transport libraries.  Those are connector-private terrain.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .models import (
    CaptureEnvelope,
    ConnectorDescriptor,
    ConnectorRunResult,
    IngressReceipt,
)


class ConnectorContractError(RuntimeError):
    """A connector violated the terrain-neutral SPI contract."""


@runtime_checkable
class InboxPort(Protocol):
    """The socket every connector is allowed to see."""

    @property
    def connector_descriptor(self) -> ConnectorDescriptor:
        ...

    def accept(self, envelope: CaptureEnvelope) -> IngressReceipt:
        ...


@dataclass(frozen=True, slots=True)
class ConnectorContext:
    """Host-provided connector context.

    The checkpoint is intentionally opaque to ActaKit core.  Persistence of
    checkpoints is not authorized by INGRESS-001; callers may pass/retain one
    externally while the need for durable run/checkpoint storage is proven.
    """

    inbox: InboxPort
    checkpoint: bytes | None = None

    def __post_init__(self) -> None:
        if self.checkpoint is not None and not isinstance(self.checkpoint, bytes):
            raise TypeError("connector checkpoint must be opaque bytes")


@runtime_checkable
class SourceConnector(Protocol):
    """Pluggable producer that terminates at the Inbox boundary."""

    @property
    def descriptor(self) -> ConnectorDescriptor:
        ...

    def run(self, context: ConnectorContext) -> ConnectorRunResult:
        ...


class _CountingInbox:
    """Host-side wrapper used only to verify a connector's run report."""

    def __init__(self, inner: InboxPort) -> None:
        self._inner = inner
        self.accepted = 0

    @property
    def connector_descriptor(self) -> ConnectorDescriptor:
        return self._inner.connector_descriptor

    def accept(self, envelope: CaptureEnvelope) -> IngressReceipt:
        receipt = self._inner.accept(envelope)
        self.accepted += 1
        return receipt


def run_connector(
    connector: SourceConnector,
    inbox: InboxPort,
    *,
    checkpoint: bytes | None = None,
) -> ConnectorRunResult:
    """Run one connector without hiding failures or interpreting its checkpoint."""

    if connector.descriptor != inbox.connector_descriptor:
        raise ConnectorContractError(
            "connector descriptor does not match the Inbox binding"
        )

    capabilities = connector.descriptor.capabilities
    if checkpoint is not None and "checkpointing" not in capabilities:
        raise ConnectorContractError(
            "host supplied a checkpoint to a connector without checkpointing capability"
        )

    counted = _CountingInbox(inbox)
    result = connector.run(ConnectorContext(counted, checkpoint))
    if not isinstance(result, ConnectorRunResult):
        raise ConnectorContractError(
            "connector must return ConnectorRunResult"
        )

    if result.emitted != counted.accepted:
        raise ConnectorContractError(
            "connector run report does not match envelopes accepted by Inbox: "
            f"reported={result.emitted}, accepted={counted.accepted}"
        )
    if result.coverage == "complete_inventory" and "inventory" not in capabilities:
        raise ConnectorContractError(
            "connector reported complete_inventory without inventory capability"
        )
    if result.coverage == "incremental" and "incremental" not in capabilities:
        raise ConnectorContractError(
            "connector reported incremental coverage without incremental capability"
        )
    if result.next_checkpoint is not None and "checkpointing" not in capabilities:
        raise ConnectorContractError(
            "connector returned a checkpoint without checkpointing capability"
        )
    return result
