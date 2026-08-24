"""Lector semantic-extraction boundary.

The public surface remains intentionally small while LECTOR-001 is in progress.
Backends emit backend-neutral drafts; canonical identity and persistence belong to
ActaKit core code, not to extractors.
"""

from .contracts import (
    ClaimDraft,
    ClaimRelationDraft,
    ClaimRevisionRef,
    EntityAnchorDraft,
    EntityMentionDraft,
    EvidenceDraft,
    RelationBasisDraft,
    ResolutionCandidateDraft,
    SemanticExtractionRequest,
    SemanticExtractor,
    SemanticExtractorDescriptor,
    SemanticInvocation,
    SemanticResult,
    TagAssignmentDraft,
    TargetRef,
)
from .host import LectorContractError, LectorHost
from .locators import SemanticLocatorError, reopen_selector
from .registry import SemanticExtractorRegistry, SemanticExtractorResolutionError
from .writer import (
    LectorIdentityCollision,
    LectorInvariantError,
    LectorWriteError,
    LectorWriter,
    PersistedClaim,
    PersistedClaimRelation,
    SemanticReceipt,
)

__all__ = [
    "LectorContractError",
    "LectorHost",
    "LectorIdentityCollision",
    "LectorInvariantError",
    "LectorWriteError",
    "LectorWriter",
    "PersistedClaim",
    "PersistedClaimRelation",
    "SemanticReceipt",
    "ClaimDraft",
    "ClaimRelationDraft",
    "ClaimRevisionRef",
    "EntityAnchorDraft",
    "EntityMentionDraft",
    "EvidenceDraft",
    "RelationBasisDraft",
    "ResolutionCandidateDraft",
    "SemanticExtractionRequest",
    "SemanticExtractor",
    "SemanticExtractorDescriptor",
    "SemanticExtractorRegistry",
    "SemanticExtractorResolutionError",
    "SemanticInvocation",
    "SemanticLocatorError",
    "SemanticResult",
    "TagAssignmentDraft",
    "TargetRef",
    "reopen_selector",
]
