"""Canonical Depósito custody operations."""

from .archive import ArchiveIntegrityError, EvidenceArchive
from .ids import new_id, utc_now
from .models import (
    AcquisitionObservation,
    AcquisitionWrite,
    CapturedArtifact,
    SourceLocatorRegistration,
    SourceRegistration,
)
from .writer import (
    AcquisitionReceipt,
    ArtifactReceipt,
    DepositInvariantError,
    DepositWriteError,
    DepositWriter,
    IdentityCollisionError,
)

__all__ = [
    "AcquisitionObservation",
    "AcquisitionReceipt",
    "AcquisitionWrite",
    "ArchiveIntegrityError",
    "ArtifactReceipt",
    "CapturedArtifact",
    "DepositInvariantError",
    "DepositWriteError",
    "DepositWriter",
    "EvidenceArchive",
    "IdentityCollisionError",
    "SourceLocatorRegistration",
    "SourceRegistration",
    "new_id",
    "utc_now",
]
