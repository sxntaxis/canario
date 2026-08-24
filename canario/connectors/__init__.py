"""Source-specific Connector SPI implementations.

This package contains terrain adapters.  It is deliberately not a plugin
registry: INGRESS-001 freezes the connector socket, not installation/discovery.
"""

from .esparza import (
    DEFAULT_SECTIONS,
    ESPARZA_CONNECTOR_DESCRIPTOR,
    EsparzaCmsConfig,
    EsparzaCmsConnector,
    EsparzaConnectorError,
    EsparzaFetchError,
    EsparzaRedirectPolicyError,
    EsparzaSection,
    EsparzaSourceStructureError,
)

__all__ = [
    "DEFAULT_SECTIONS",
    "ESPARZA_CONNECTOR_DESCRIPTOR",
    "EsparzaCmsConfig",
    "EsparzaCmsConnector",
    "EsparzaConnectorError",
    "EsparzaFetchError",
    "EsparzaRedirectPolicyError",
    "EsparzaSection",
    "EsparzaSourceStructureError",
]
