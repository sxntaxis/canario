"""Typed contracts for Canario's single-operator claim review workflow."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from canario.deposit.ids import new_id, validate_id

REVIEW_MODES = frozenset({"strict", "batch", "supervised"})
REVIEW_DECISIONS = frozenset({"accepted", "rejected", "needs_work"})
_MAX_ACTOR = 512
_MAX_NOTE = 8 * 1024
_MAX_REASON = 8 * 1024
_MAX_BATCH = 2_000


def _bounded_nonempty(value: str, field_name: str, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if len(value) > maximum:
        raise ValueError(f"{field_name} exceeds {maximum} characters")
    return value


def _optional_bounded(value: str | None, field_name: str, maximum: int) -> str | None:
    if value is not None:
        _bounded_nonempty(value, field_name, maximum)
    return value


@dataclass(frozen=True, slots=True)
class ClaimReviewDraft:
    claim_revision_id: str
    decision: str
    reason: str | None = None

    def __post_init__(self) -> None:
        validate_id(self.claim_revision_id, "clrev_")
        if self.decision not in REVIEW_DECISIONS:
            raise ValueError(f"invalid review decision: {self.decision!r}")
        _optional_bounded(self.reason, "review reason", _MAX_REASON)


@dataclass(frozen=True, slots=True)
class ClaimReviewActionRequest:
    actor: str
    mode: str
    decisions: tuple[ClaimReviewDraft, ...]
    note: str | None = None
    review_action_id: str = field(default_factory=lambda: new_id("ract_"))

    def __post_init__(self) -> None:
        validate_id(self.review_action_id, "ract_")
        _bounded_nonempty(self.actor, "review actor", _MAX_ACTOR)
        if self.mode not in REVIEW_MODES:
            raise ValueError(f"invalid review mode: {self.mode!r}")
        _optional_bounded(self.note, "review note", _MAX_NOTE)
        if not isinstance(self.decisions, tuple) or not self.decisions:
            raise ValueError("review action requires at least one decision")
        if len(self.decisions) > _MAX_BATCH:
            raise ValueError(f"review action exceeds {_MAX_BATCH} claim revisions")
        if not all(isinstance(item, ClaimReviewDraft) for item in self.decisions):
            raise TypeError("review decisions must contain ClaimReviewDraft values")
        ids = [item.claim_revision_id for item in self.decisions]
        if len(ids) != len(set(ids)):
            raise ValueError("one review action cannot repeat a claim revision")


@dataclass(frozen=True, slots=True)
class ClaimBatch:
    representation_id: str
    claim_revision_ids: tuple[str, ...]
    selection_policy_key: str = "current_machine_claims_for_representation"
    selection_policy_version: str = "v1"
    subject_set_sha256: str = ""

    def __post_init__(self) -> None:
        validate_id(self.representation_id, "rep_")
        if not isinstance(self.claim_revision_ids, tuple):
            raise TypeError("claim_revision_ids must be a tuple")
        if len(self.claim_revision_ids) > _MAX_BATCH:
            raise ValueError(f"claim batch exceeds {_MAX_BATCH} claim revisions")
        for revision_id in self.claim_revision_ids:
            validate_id(revision_id, "clrev_")
        if len(self.claim_revision_ids) != len(set(self.claim_revision_ids)):
            raise ValueError("claim batch cannot contain duplicate revisions")
        if self.selection_policy_key != "current_machine_claims_for_representation":
            raise ValueError("unknown claim batch selection policy")
        if self.selection_policy_version != "v1":
            raise ValueError("unknown claim batch selection policy version")
        expected = self.compute_sha256(
            self.representation_id,
            self.claim_revision_ids,
            self.selection_policy_key,
            self.selection_policy_version,
        )
        if not self.subject_set_sha256:
            object.__setattr__(self, "subject_set_sha256", expected)
        elif self.subject_set_sha256 != expected:
            raise ValueError("claim batch subject-set fingerprint mismatch")

    @staticmethod
    def compute_sha256(
        representation_id: str,
        revision_ids: tuple[str, ...],
        policy_key: str,
        policy_version: str,
    ) -> str:
        payload = json.dumps(
            {
                "representation_id": representation_id,
                "claim_revision_ids": list(revision_ids),
                "selection_policy_key": policy_key,
                "selection_policy_version": policy_version,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class BatchDecisionOverride:
    claim_revision_id: str
    decision: str
    reason: str | None = None

    def __post_init__(self) -> None:
        validate_id(self.claim_revision_id, "clrev_")
        if self.decision not in REVIEW_DECISIONS:
            raise ValueError(f"invalid review decision: {self.decision!r}")
        _optional_bounded(self.reason, "review reason", _MAX_REASON)


@dataclass(frozen=True, slots=True)
class ClaimBatchReviewRequest:
    batch: ClaimBatch
    actor: str
    default_decision: str
    exceptions: tuple[BatchDecisionOverride, ...] = ()
    note: str | None = None
    review_action_id: str = field(default_factory=lambda: new_id("ract_"))

    def __post_init__(self) -> None:
        if not isinstance(self.batch, ClaimBatch):
            raise TypeError("batch must be ClaimBatch")
        if not self.batch.claim_revision_ids:
            raise ValueError("cannot review an empty claim batch")
        _bounded_nonempty(self.actor, "review actor", _MAX_ACTOR)
        if self.default_decision not in REVIEW_DECISIONS:
            raise ValueError(f"invalid review decision: {self.default_decision!r}")
        _optional_bounded(self.note, "review note", _MAX_NOTE)
        validate_id(self.review_action_id, "ract_")
        if not isinstance(self.exceptions, tuple):
            raise TypeError("batch exceptions must be a tuple")
        if not all(isinstance(item, BatchDecisionOverride) for item in self.exceptions):
            raise TypeError("batch exceptions must contain BatchDecisionOverride values")
        ids = [item.claim_revision_id for item in self.exceptions]
        if len(ids) != len(set(ids)):
            raise ValueError("batch exceptions cannot repeat a claim revision")
        unknown = set(ids) - set(self.batch.claim_revision_ids)
        if unknown:
            raise ValueError("batch exception references a revision outside the exact batch")

    def as_action(self) -> ClaimReviewActionRequest:
        overrides = {item.claim_revision_id: item for item in self.exceptions}
        decisions = tuple(
            ClaimReviewDraft(
                revision_id,
                overrides[revision_id].decision if revision_id in overrides else self.default_decision,
                overrides[revision_id].reason if revision_id in overrides else None,
            )
            for revision_id in self.batch.claim_revision_ids
        )
        return ClaimReviewActionRequest(
            actor=self.actor,
            mode="batch",
            decisions=decisions,
            note=self.note,
            review_action_id=self.review_action_id,
        )

CLAIM_REVISION_ACTIONS = frozenset({"correct", "restrict", "unrestrict", "retract"})
HUMAN_CORRECTABLE_CLAIM_KINDS = frozenset(
    {"source_assertion", "community_report", "verification_question"}
)
_MAX_CLAIM_TEXT = 32 * 1024
_MAX_TEMPORAL = 128
_MAX_SHA256 = 64


def _sha256(value: str, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != _MAX_SHA256
        or value != value.lower()
        or any(ch not in "0123456789abcdef" for ch in value)
    ):
        raise ValueError(f"{field_name} must be lowercase SHA256 hex")
    return value


def _id_tuple(values: tuple[str, ...], prefix: str, field_name: str) -> None:
    if not isinstance(values, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    for value in values:
        validate_id(value, prefix)
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} cannot contain duplicates")


@dataclass(frozen=True, slots=True)
class HumanClaimCorrection:
    """Complete human-authored semantic replacement for one non-derived ClaimRevision."""

    claim_kind: str
    text: str
    evidence_link_ids: tuple[str, ...]
    entity_link_ids: tuple[str, ...] = ()
    tag_link_ids: tuple[str, ...] = ()
    attribution_entity_id: str | None = None
    attribution_text: str | None = None
    temporal_start: str | None = None
    temporal_end: str | None = None
    sensitive: bool = False
    quantitative: bool = False

    def __post_init__(self) -> None:
        if self.claim_kind not in HUMAN_CORRECTABLE_CLAIM_KINDS:
            raise ValueError(f"invalid human-correctable claim kind: {self.claim_kind!r}")
        _bounded_nonempty(self.text, "corrected claim text", _MAX_CLAIM_TEXT)
        _id_tuple(self.evidence_link_ids, "evl_", "correction evidence_link_ids")
        _id_tuple(self.entity_link_ids, "clent_", "correction entity_link_ids")
        _id_tuple(self.tag_link_ids, "cltag_", "correction tag_link_ids")
        if self.attribution_entity_id is not None:
            validate_id(self.attribution_entity_id, "ent_")
        _optional_bounded(self.attribution_text, "corrected attribution text", 4 * 1024)
        _optional_bounded(self.temporal_start, "corrected temporal_start", _MAX_TEMPORAL)
        _optional_bounded(self.temporal_end, "corrected temporal_end", _MAX_TEMPORAL)
        if (
            self.temporal_start is not None
            and self.temporal_end is not None
            and self.temporal_start > self.temporal_end
        ):
            raise ValueError("corrected temporal_start cannot exceed temporal_end")
        if type(self.sensitive) is not bool or type(self.quantitative) is not bool:
            raise TypeError("corrected sensitive/quantitative flags must be booleans")

    def canonical_payload(self) -> dict[str, object]:
        return {
            "claim_kind": self.claim_kind,
            "text": self.text,
            "evidence_link_ids": list(self.evidence_link_ids),
            "entity_link_ids": list(self.entity_link_ids),
            "tag_link_ids": list(self.tag_link_ids),
            "attribution_entity_id": self.attribution_entity_id,
            "attribution_text": self.attribution_text,
            "temporal_start": self.temporal_start,
            "temporal_end": self.temporal_end,
            "sensitive": self.sensitive,
            "quantitative": self.quantitative,
        }


@dataclass(frozen=True, slots=True)
class ClaimRevisionControlRequest:
    source_revision_id: str
    expected_snapshot_sha256: str
    actor: str
    action: str
    correction: HumanClaimCorrection | None = None
    rationale: str | None = None
    claim_revision_action_id: str = field(default_factory=lambda: new_id("clact_"))
    result_revision_id: str = field(default_factory=lambda: new_id("clrev_"))
    review_action_id: str | None = None

    def __post_init__(self) -> None:
        validate_id(self.source_revision_id, "clrev_")
        validate_id(self.claim_revision_action_id, "clact_")
        validate_id(self.result_revision_id, "clrev_")
        if self.source_revision_id == self.result_revision_id:
            raise ValueError("result revision must differ from source revision")
        _sha256(self.expected_snapshot_sha256, "expected_snapshot_sha256")
        _bounded_nonempty(self.actor, "claim revision actor", _MAX_ACTOR)
        if self.action not in CLAIM_REVISION_ACTIONS:
            raise ValueError(f"invalid claim revision action: {self.action!r}")
        _optional_bounded(self.rationale, "claim revision rationale", _MAX_REASON)
        if self.action == "correct":
            if not isinstance(self.correction, HumanClaimCorrection):
                raise ValueError("correct action requires HumanClaimCorrection")
            if self.review_action_id is None:
                object.__setattr__(self, "review_action_id", new_id("ract_"))
            else:
                validate_id(self.review_action_id, "ract_")
        else:
            if self.correction is not None:
                raise ValueError(f"{self.action} action cannot include correction payload")
            if self.review_action_id is not None:
                raise ValueError(f"{self.action} action cannot include review_action_id")

    def request_sha256(self) -> str:
        payload = json.dumps(
            {
                "source_revision_id": self.source_revision_id,
                "expected_snapshot_sha256": self.expected_snapshot_sha256,
                "actor": self.actor,
                "action": self.action,
                "correction": None if self.correction is None else self.correction.canonical_payload(),
                "rationale": self.rationale,
                "result_revision_id": self.result_revision_id,
                "review_action_id": self.review_action_id,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()
