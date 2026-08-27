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
