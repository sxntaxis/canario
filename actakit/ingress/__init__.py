"""Terrain-neutral source connector boundary (the ActaKit Inbox)."""

from .inbox import DepositInbox, InboxPolicy
from .models import (
    CAPTURE_OUTCOMES,
    CAPTURE_ROLES,
    CONNECTOR_CAPABILITIES,
    RUN_COVERAGE,
    CaptureEnvelope,
    CapturePayload,
    ConnectorDescriptor,
    ConnectorRunResult,
    IngressReceipt,
    ObservedLocator,
)
from .spi import (
    ConnectorContext,
    ConnectorContractError,
    InboxPort,
    SourceConnector,
    run_connector,
)

__all__ = [
    "CAPTURE_OUTCOMES",
    "CAPTURE_ROLES",
    "CONNECTOR_CAPABILITIES",
    "RUN_COVERAGE",
    "CaptureEnvelope",
    "CapturePayload",
    "ConnectorContext",
    "ConnectorContractError",
    "ConnectorDescriptor",
    "ConnectorRunResult",
    "DepositInbox",
    "InboxPolicy",
    "InboxPort",
    "IngressReceipt",
    "ObservedLocator",
    "SourceConnector",
    "run_connector",
]
