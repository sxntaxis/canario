"""Backend-neutral contracts for bounded semantic extraction (Lector)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from canario.deposit.ids import new_id, validate_id
from canario.processors.contracts import (
    EgressAuthorization,
    REPRESENTATION_KINDS,
    TargetSnapshot,
    require_nonempty,
    require_token,
    validate_sha256,
)

ORIGIN_KINDS = frozenset({"machine", "rule", "human"})
CLAIM_KINDS = frozenset(
    {"source_assertion", "derived_inference", "community_report", "verification_question"}
)
DRAFT_LINK_LIFECYCLES = frozenset({"candidate", "active"})
EVIDENCE_RELATIONS = frozenset({"supports", "challenges", "contextualizes", "quotes", "mentions"})
RELATION_TYPES = frozenset(
    {
        "updates",
        "contradicts",
        "corrects",
        "responds_to",
        "implements",
        "supersedes",
        "same_matter_as",
        "other",
    }
)
SYMMETRIC_RELATION_TYPES = frozenset({"contradicts", "same_matter_as"})
RELATION_BASIS_KINDS = frozenset(
    {"source_evidence", "analyst_inference", "mechanical_identity", "other"}
)
SEMANTIC_OUTCOMES = frozenset({"success", "partial", "failed"})

_MAX_LOCAL_KEY = 128
_MAX_TEXT = 32 * 1024
_MAX_OBSERVED_TEXT = 4 * 1024
_MAX_RATIONALE = 8 * 1024
_MAX_ROLE = 512
_MAX_TEMPORAL = 128


def _bounded_nonempty(value: str, field_name: str, maximum: int) -> str:
    require_nonempty(value, field_name)
    if len(value) > maximum:
        raise ValueError(f"{field_name} exceeds {maximum} characters")
    return value


def _optional_bounded(value: str | None, field_name: str, maximum: int) -> str | None:
    if value is not None:
        _bounded_nonempty(value, field_name, maximum)
    return value


def _local_key(value: str, field_name: str = "local key") -> str:
    require_token(value, field_name)
    if len(value) > _MAX_LOCAL_KEY:
        raise ValueError(f"{field_name} exceeds {_MAX_LOCAL_KEY} characters")
    return value


def _positive_bound(value: int | None, field_name: str) -> None:
    if value is not None and (
        isinstance(value, bool) or not isinstance(value, int) or value <= 0
    ):
        raise ValueError(f"{field_name} must be a positive integer")


@dataclass(frozen=True, slots=True)
class SemanticExtractorDescriptor:
    """Trusted identity/capability declaration for one curated Lector backend."""

    key: str
    capability_key: str
    implementation_version: str
    origin_kind: str
    execution_venue: str
    input_media_types: frozenset[str]
    input_representation_kinds: frozenset[str]
    scope_kinds: frozenset[str]
    requires_egress: bool = False
    model_provider: str | None = None
    model_name: str | None = None
    max_input_bytes: int | None = None
    max_scopes: int | None = None
    max_claims: int = 1000
    max_evidence_links: int = 10000
    max_mentions: int = 5000
    max_resolution_candidates: int = 10000
    max_tag_assignments: int = 5000
    max_entity_anchors: int = 5000
    max_relations: int = 5000
    max_relation_basis_targets: int = 10000

    def __post_init__(self) -> None:
        require_token(self.key, "extractor key")
        require_token(self.capability_key, "semantic capability key")
        _bounded_nonempty(self.implementation_version, "implementation version", 256)
        if self.origin_kind not in ORIGIN_KINDS:
            raise ValueError(f"invalid semantic origin kind: {self.origin_kind!r}")
        require_token(self.execution_venue, "execution venue")
        if not isinstance(self.input_media_types, frozenset) or not self.input_media_types:
            raise ValueError("input_media_types must be a non-empty frozenset")
        if not all(isinstance(v, str) and v.strip() for v in self.input_media_types):
            raise ValueError("input media types must be non-empty strings")
        if (
            not isinstance(self.input_representation_kinds, frozenset)
            or not self.input_representation_kinds
        ):
            raise ValueError("input_representation_kinds must be a non-empty frozenset")
        if not all(isinstance(v, str) and v.strip() for v in self.input_representation_kinds):
            raise ValueError("input Representation kinds must be non-empty strings")
        unknown_representation_kinds = self.input_representation_kinds - REPRESENTATION_KINDS
        if unknown_representation_kinds:
            raise ValueError(
                "unknown input Representation kinds: "
                f"{sorted(unknown_representation_kinds)!r}"
            )
        if not isinstance(self.scope_kinds, frozenset) or not self.scope_kinds:
            raise ValueError("scope_kinds must be a non-empty frozenset")
        for value in self.scope_kinds:
            require_token(value, "scope kind")
        if not isinstance(self.requires_egress, bool):
            raise TypeError("requires_egress must be boolean")
        if self.model_provider is not None:
            require_token(self.model_provider, "model provider")
        if self.model_name is not None:
            _bounded_nonempty(self.model_name, "model name", 256)
        if (self.model_provider is None) != (self.model_name is None):
            raise ValueError("model provider/name must either both be present or both be absent")
        for name in (
            "max_input_bytes",
            "max_scopes",
            "max_claims",
            "max_evidence_links",
            "max_mentions",
            "max_resolution_candidates",
            "max_tag_assignments",
            "max_entity_anchors",
            "max_relations",
            "max_relation_basis_targets",
        ):
            _positive_bound(getattr(self, name), name)


@dataclass(frozen=True, slots=True)
class SemanticExtractionRequest:
    representation_id: str
    target_ids: tuple[str, ...]
    capability_key: str
    configuration_hash: str | None = None
    egress: EgressAuthorization = field(default_factory=EgressAuthorization.forbidden)
    process_run_id: str = field(default_factory=lambda: new_id("prun_"))

    def __post_init__(self) -> None:
        validate_id(self.representation_id, "rep_")
        validate_id(self.process_run_id, "prun_")
        require_token(self.capability_key, "semantic capability key")
        validate_sha256(self.configuration_hash, "configuration hash")
        if not isinstance(self.target_ids, tuple) or not self.target_ids:
            raise ValueError("target_ids must be a non-empty tuple")
        if len(set(self.target_ids)) != len(self.target_ids):
            raise ValueError("target_ids cannot contain duplicates")
        for target_id in self.target_ids:
            validate_id(target_id, "rtgt_")


@dataclass(frozen=True, slots=True)
class TargetRef:
    """Existing canonical target or selector proposal on the input Representation."""

    target_id: str | None = None
    selector_kind: str | None = None
    selector_version: str | None = None
    selector_payload_json: str | None = None

    def __post_init__(self) -> None:
        existing = self.target_id is not None
        proposed = any(
            value is not None
            for value in (self.selector_kind, self.selector_version, self.selector_payload_json)
        )
        if existing == proposed:
            raise ValueError("TargetRef must be exactly one existing target or selector proposal")
        if existing:
            assert self.target_id is not None
            validate_id(self.target_id, "rtgt_")
            return
        if (
            self.selector_kind is None
            or self.selector_version is None
            or self.selector_payload_json is None
        ):
            raise ValueError("selector proposal requires kind, version and payload")
        require_token(self.selector_kind, "selector kind")
        require_token(self.selector_version, "selector version")
        _bounded_nonempty(self.selector_payload_json, "selector payload", 64 * 1024)

    @classmethod
    def existing(cls, target_id: str) -> "TargetRef":
        return cls(target_id=target_id)

    @classmethod
    def proposed(cls, kind: str, version: str, payload_json: str) -> "TargetRef":
        return cls(
            selector_kind=kind,
            selector_version=version,
            selector_payload_json=payload_json,
        )


@dataclass(frozen=True, slots=True)
class EvidenceDraft:
    target: TargetRef
    relation: str = "supports"
    lifecycle: str = "active"
    rationale: str | None = None

    def __post_init__(self) -> None:
        if self.relation not in EVIDENCE_RELATIONS:
            raise ValueError(f"invalid evidence relation: {self.relation!r}")
        if self.lifecycle not in DRAFT_LINK_LIFECYCLES:
            raise ValueError(f"invalid evidence lifecycle: {self.lifecycle!r}")
        _optional_bounded(self.rationale, "evidence rationale", _MAX_RATIONALE)


@dataclass(frozen=True, slots=True)
class ResolutionCandidateDraft:
    entity_id: str
    score: float | None = None

    def __post_init__(self) -> None:
        validate_id(self.entity_id, "ent_")
        if self.score is not None:
            if isinstance(self.score, bool) or not isinstance(self.score, (int, float)):
                raise TypeError("resolution candidate score must be numeric")
            if not 0.0 <= float(self.score) <= 1.0:
                raise ValueError("resolution candidate score must be within 0..1")


@dataclass(frozen=True, slots=True)
class EntityMentionDraft:
    observed_text: str
    target: TargetRef
    resolution_candidates: tuple[ResolutionCandidateDraft, ...] = ()

    def __post_init__(self) -> None:
        _bounded_nonempty(self.observed_text, "observed entity text", _MAX_OBSERVED_TEXT)
        if not isinstance(self.resolution_candidates, tuple):
            raise TypeError("resolution_candidates must be a tuple")
        entity_ids = [candidate.entity_id for candidate in self.resolution_candidates]
        if len(entity_ids) != len(set(entity_ids)):
            raise ValueError("one mention cannot repeat the same resolution candidate Entity")


@dataclass(frozen=True, slots=True)
class TagAssignmentDraft:
    tag_id: str
    lifecycle: str = "active"
    rationale: str | None = None

    def __post_init__(self) -> None:
        validate_id(self.tag_id, "tag_")
        if self.lifecycle not in DRAFT_LINK_LIFECYCLES:
            raise ValueError(f"invalid tag-link lifecycle: {self.lifecycle!r}")
        _optional_bounded(self.rationale, "tag rationale", _MAX_RATIONALE)


@dataclass(frozen=True, slots=True)
class EntityAnchorDraft:
    entity_id: str
    role: str | None = None
    lifecycle: str = "candidate"
    rationale: str | None = None

    def __post_init__(self) -> None:
        validate_id(self.entity_id, "ent_")
        _optional_bounded(self.role, "entity anchor role", _MAX_ROLE)
        if self.lifecycle not in DRAFT_LINK_LIFECYCLES:
            raise ValueError(f"invalid entity-link lifecycle: {self.lifecycle!r}")
        _optional_bounded(self.rationale, "entity anchor rationale", _MAX_RATIONALE)


@dataclass(frozen=True, slots=True)
class ClaimDraft:
    local_key: str
    claim_kind: str
    text: str
    evidence: tuple[EvidenceDraft, ...]
    mentions: tuple[EntityMentionDraft, ...] = ()
    tags: tuple[TagAssignmentDraft, ...] = ()
    entity_anchors: tuple[EntityAnchorDraft, ...] = ()
    attribution_entity_id: str | None = None
    attribution_text: str | None = None
    temporal_start: str | None = None
    temporal_end: str | None = None
    sensitive: bool = False
    quantitative: bool = False

    def __post_init__(self) -> None:
        _local_key(self.local_key, "claim local key")
        if self.claim_kind not in CLAIM_KINDS:
            raise ValueError(f"invalid claim kind: {self.claim_kind!r}")
        _bounded_nonempty(self.text, "claim text", _MAX_TEXT)
        if not isinstance(self.evidence, tuple) or not self.evidence:
            raise ValueError("every extracted Claim requires at least one EvidenceDraft")
        if not all(isinstance(item, EvidenceDraft) for item in self.evidence):
            raise TypeError("claim evidence must contain EvidenceDraft values")
        if not isinstance(self.mentions, tuple) or not all(
            isinstance(item, EntityMentionDraft) for item in self.mentions
        ):
            raise TypeError("claim mentions must contain EntityMentionDraft values")
        if not isinstance(self.tags, tuple) or not all(
            isinstance(item, TagAssignmentDraft) for item in self.tags
        ):
            raise TypeError("claim tags must contain TagAssignmentDraft values")
        tag_ids = [item.tag_id for item in self.tags]
        if len(tag_ids) != len(set(tag_ids)):
            raise ValueError("one claim cannot repeat the same Tag assignment")
        if not isinstance(self.entity_anchors, tuple) or not all(
            isinstance(item, EntityAnchorDraft) for item in self.entity_anchors
        ):
            raise TypeError("claim entity anchors must contain EntityAnchorDraft values")
        anchor_identities = [(item.entity_id, item.role) for item in self.entity_anchors]
        if len(anchor_identities) != len(set(anchor_identities)):
            raise ValueError("one claim cannot repeat the same direct Entity anchor/role")
        if self.attribution_entity_id is not None:
            validate_id(self.attribution_entity_id, "ent_")
        _optional_bounded(self.attribution_text, "claim attribution text", _MAX_OBSERVED_TEXT)
        _optional_bounded(self.temporal_start, "claim temporal_start", _MAX_TEMPORAL)
        _optional_bounded(self.temporal_end, "claim temporal_end", _MAX_TEMPORAL)
        if (
            self.temporal_start is not None
            and self.temporal_end is not None
            and self.temporal_start > self.temporal_end
        ):
            raise ValueError("claim temporal_start cannot exceed temporal_end")
        if type(self.sensitive) is not bool or type(self.quantitative) is not bool:
            raise TypeError("claim sensitive/quantitative flags must be booleans")
        if self.claim_kind == "source_assertion" and not any(
            item.lifecycle == "active" and item.relation in {"supports", "quotes"}
            for item in self.evidence
        ):
            raise ValueError("source_assertion requires active supports/quotes evidence")


@dataclass(frozen=True, slots=True)
class ClaimRevisionRef:
    """Reference to a ClaimDraft created in the same SemanticResult."""

    local_claim_key: str

    def __post_init__(self) -> None:
        _local_key(self.local_claim_key, "relation claim local key")

    @classmethod
    def local(cls, local_claim_key: str) -> "ClaimRevisionRef":
        return cls(local_claim_key)


@dataclass(frozen=True, slots=True)
class RelationBasisDraft:
    target: TargetRef
    basis_role: str = "source_basis"

    def __post_init__(self) -> None:
        if self.basis_role not in {"source_basis", "context"}:
            raise ValueError(f"invalid relation basis role: {self.basis_role!r}")


@dataclass(frozen=True, slots=True)
class ClaimRelationDraft:
    from_claim: ClaimRevisionRef
    to_claim: ClaimRevisionRef
    relation_type: str
    basis_kind: str
    basis: tuple[RelationBasisDraft, ...] = ()
    rationale: str | None = None
    lifecycle: str = "candidate"

    def __post_init__(self) -> None:
        if self.relation_type not in RELATION_TYPES:
            raise ValueError(f"invalid claim relation type: {self.relation_type!r}")
        if self.basis_kind not in RELATION_BASIS_KINDS:
            raise ValueError(f"invalid relation basis kind: {self.basis_kind!r}")
        if not isinstance(self.basis, tuple) or not all(
            isinstance(item, RelationBasisDraft) for item in self.basis
        ):
            raise TypeError("relation basis must contain RelationBasisDraft values")
        _optional_bounded(self.rationale, "relation rationale", _MAX_RATIONALE)
        if self.lifecycle not in DRAFT_LINK_LIFECYCLES:
            raise ValueError(f"invalid relation lifecycle: {self.lifecycle!r}")
        if self.basis_kind == "source_evidence" and not any(
            item.basis_role == "source_basis" for item in self.basis
        ):
            raise ValueError("source_evidence ClaimRelation requires exact source_basis")
        if self.from_claim.local_claim_key == self.to_claim.local_claim_key:
            raise ValueError("ClaimRelation endpoints must reference distinct claims")
        basis_identities = [(item.target, item.basis_role) for item in self.basis]
        if len(basis_identities) != len(set(basis_identities)):
            raise ValueError("ClaimRelation cannot repeat the same basis target/role")
        if self.lifecycle == "active" and not self.basis and self.rationale is None:
            raise ValueError("active ClaimRelation requires inspectable basis or rationale")


@dataclass(frozen=True, slots=True)
class SemanticResult:
    outcome: str
    claims: tuple[ClaimDraft, ...] = ()
    relations: tuple[ClaimRelationDraft, ...] = ()
    error_code: str | None = None
    egress_bytes: int | None = None

    def __post_init__(self) -> None:
        if self.outcome not in SEMANTIC_OUTCOMES:
            raise ValueError(f"invalid semantic outcome: {self.outcome!r}")
        if not isinstance(self.claims, tuple) or not all(
            isinstance(item, ClaimDraft) for item in self.claims
        ):
            raise TypeError("SemanticResult claims must be a tuple of ClaimDraft")
        claim_keys = [item.local_key for item in self.claims]
        if len(claim_keys) != len(set(claim_keys)):
            raise ValueError("SemanticResult claim local keys must be unique")
        if not isinstance(self.relations, tuple) or not all(
            isinstance(item, ClaimRelationDraft) for item in self.relations
        ):
            raise TypeError("SemanticResult relations must be a tuple of ClaimRelationDraft")
        known_claims = set(claim_keys)
        relation_identities: set[tuple[str, str, str]] = set()
        for relation in self.relations:
            for ref in (relation.from_claim, relation.to_claim):
                if ref.local_claim_key not in known_claims:
                    raise ValueError(
                        f"ClaimRelation references unknown local claim {ref.local_claim_key!r}"
                    )
            left = relation.from_claim.local_claim_key
            right = relation.to_claim.local_claim_key
            if relation.relation_type in SYMMETRIC_RELATION_TYPES and right < left:
                left, right = right, left
            identity = (left, relation.relation_type, right)
            if identity in relation_identities:
                raise ValueError("SemanticResult cannot repeat the same ClaimRelation")
            relation_identities.add(identity)
        for claim in self.claims:
            evidence_identities = [(item.target, item.relation) for item in claim.evidence]
            if len(evidence_identities) != len(set(evidence_identities)):
                raise ValueError(
                    "one claim cannot repeat the same evidence target/relation"
                )
            mention_identities = [(item.observed_text, item.target) for item in claim.mentions]
            if len(mention_identities) != len(set(mention_identities)):
                raise ValueError("one claim cannot repeat the same EntityMention occurrence")
        if self.outcome == "failed":
            if self.claims or self.relations:
                raise ValueError("failed SemanticResult cannot contain semantic outputs")
            if self.error_code is None:
                raise ValueError("failed SemanticResult requires error_code")
        elif self.outcome == "success" and self.error_code is not None:
            raise ValueError("successful SemanticResult cannot carry error_code")
        if self.error_code is not None:
            require_token(self.error_code, "semantic error code")
        if self.egress_bytes is not None and (
            isinstance(self.egress_bytes, bool)
            or not isinstance(self.egress_bytes, int)
            or self.egress_bytes < 0
        ):
            raise ValueError("egress_bytes must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class SemanticInvocation:
    request: SemanticExtractionRequest
    representation_kind: str
    media_type: str
    language: str | None
    charset: str | None
    source_bytes: bytes
    scopes: tuple[TargetSnapshot, ...]

    def __post_init__(self) -> None:
        if self.representation_kind not in REPRESENTATION_KINDS:
            raise ValueError(f"unknown Representation kind: {self.representation_kind!r}")
        require_nonempty(self.media_type, "media type")
        if not isinstance(self.source_bytes, bytes):
            raise TypeError("source_bytes must be immutable bytes")
        if not self.scopes:
            raise ValueError("SemanticInvocation requires at least one exact scope")


@runtime_checkable
class SemanticExtractor(Protocol):
    @property
    def descriptor(self) -> SemanticExtractorDescriptor:
        ...

    def extract(self, invocation: SemanticInvocation) -> SemanticResult:
        ...
