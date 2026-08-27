"""Canonical writes for human claim review actions."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from canario.deposit.ids import new_id, validate_timestamp
from canario.persistence import open_writable_v1

from .contracts import ClaimBatchReviewRequest, ClaimReviewActionRequest

ConnectionFactory = Callable[[Path], sqlite3.Connection]


class ReviewWriteError(RuntimeError):
    """A review action could not be persisted honestly."""


class ReviewInvariantError(ReviewWriteError):
    """A review request violates the bounded review workflow."""


class ReviewIdentityCollision(ReviewWriteError):
    """A stable ReviewAction ID is occupied by different immutable content."""


@dataclass(frozen=True, slots=True)
class ClaimReviewReceipt:
    review_action_id: str
    mode: str
    claim_review_ids: tuple[str, ...]
    claim_revision_ids: tuple[str, ...]
    reviewed_subjects_sha256: str
    replayed: bool


class ReviewWriter:
    """Sole core writer for claim ReviewAction + ClaimReview rows."""

    def __init__(
        self,
        database_path: str | Path,
        *,
        connection_factory: ConnectionFactory = open_writable_v1,
    ) -> None:
        self.database_path = Path(database_path)
        self._connect = connection_factory

    def record_claim_reviews(
        self,
        request: ClaimReviewActionRequest,
        *,
        created_at: str,
    ) -> ClaimReviewReceipt:
        return self._record_claim_reviews(request, created_at=created_at, batch_representation_id=None)

    def _record_claim_reviews(
        self,
        request: ClaimReviewActionRequest,
        *,
        created_at: str,
        batch_representation_id: str | None,
    ) -> ClaimReviewReceipt:
        validate_timestamp(created_at)
        con = self._connect(self.database_path)
        try:
            con.execute("BEGIN IMMEDIATE")
            replay = self._replay_if_present(con, request)
            if replay is not None:
                con.rollback()
                return replay

            for item in request.decisions:
                self._require_current_claim_revision(con, item.claim_revision_id)
                if batch_representation_id is not None and not self._claim_has_current_active_evidence_on_representation(
                    con, item.claim_revision_id, batch_representation_id
                ):
                    raise ReviewInvariantError(
                        "claim batch subject is no longer backed by the prepared Representation"
                    )

            con.execute(
                "INSERT INTO review_actions(id,actor,mode,created_at,note) VALUES (?,?,?,?,?)",
                (request.review_action_id, request.actor, request.mode, created_at, request.note),
            )
            review_ids: list[str] = []
            for item in request.decisions:
                review_id = new_id("clreview_")
                con.execute(
                    """
                    INSERT INTO claim_reviews(
                      id,review_action_id,claim_revision_id,decision,reviewer,reason,created_at
                    ) VALUES (?,?,?,?,?,?,?)
                    """,
                    (
                        review_id,
                        request.review_action_id,
                        item.claim_revision_id,
                        item.decision,
                        request.actor,
                        item.reason,
                        created_at,
                    ),
                )
                review_ids.append(review_id)
            con.commit()
            return self._receipt(con, request.review_action_id, replayed=False)
        except sqlite3.IntegrityError as exc:
            if con.in_transaction:
                con.rollback()
            raise ReviewWriteError(f"SQLite rejected claim review write: {exc}") from exc
        except Exception:
            if con.in_transaction:
                con.rollback()
            raise
        finally:
            con.close()

    def record_claim_batch(
        self,
        request: ClaimBatchReviewRequest,
        *,
        created_at: str,
    ) -> ClaimReviewReceipt:
        # The immutable ClaimBatch fingerprint proves preview membership was not
        # modified by the caller. Current-revision and Representation-evidence
        # checks then run inside the same BEGIN IMMEDIATE as the write.
        receipt = self._record_claim_reviews(
            request.as_action(),
            created_at=created_at,
            batch_representation_id=request.batch.representation_id,
        )
        if receipt.reviewed_subjects_sha256 != self._subject_sha(request.batch.claim_revision_ids):
            raise ReviewInvariantError("persisted claim review membership changed unexpectedly")
        return receipt

    def _replay_if_present(
        self, con: sqlite3.Connection, request: ClaimReviewActionRequest
    ) -> ClaimReviewReceipt | None:
        row = con.execute(
            "SELECT actor,mode,note FROM review_actions WHERE id=?",
            (request.review_action_id,),
        ).fetchone()
        if row is None:
            return None
        if row != (request.actor, request.mode, request.note):
            raise ReviewIdentityCollision("ReviewAction ID collision")
        existing = con.execute(
            """
            SELECT claim_revision_id,decision,reason,reviewer
            FROM claim_reviews WHERE review_action_id=?
            ORDER BY claim_revision_id
            """,
            (request.review_action_id,),
        ).fetchall()
        expected = sorted(
            (item.claim_revision_id, item.decision, item.reason, request.actor)
            for item in request.decisions
        )
        if existing != expected:
            raise ReviewIdentityCollision("ReviewAction decision payload collision")
        return self._receipt(con, request.review_action_id, replayed=True)

    def _require_current_claim_revision(self, con: sqlite3.Connection, revision_id: str) -> None:
        row = con.execute(
            """
            SELECT 1
            FROM claim_revisions current
            WHERE current.id=?
              AND NOT EXISTS (
                SELECT 1 FROM claim_revisions successor
                WHERE successor.supersedes_revision_id=current.id
              )
            """,
            (revision_id,),
        ).fetchone()
        if row is None:
            raise ReviewInvariantError(
                "review actions may target only the exact current ClaimRevision"
            )

    def _claim_has_current_active_evidence_on_representation(
        self, con: sqlite3.Connection, revision_id: str, representation_id: str
    ) -> bool:
        row = con.execute(
            """
            SELECT 1
            FROM evidence_links e
            JOIN representation_targets t ON t.id=e.representation_target_id
            WHERE e.claim_revision_id=?
              AND t.representation_id=?
              AND e.lifecycle='active'
              AND NOT EXISTS (
                SELECT 1 FROM evidence_links successor
                WHERE successor.supersedes_evidence_link_id=e.id
              )
            LIMIT 1
            """,
            (revision_id, representation_id),
        ).fetchone()
        return row is not None

    def _receipt(
        self, con: sqlite3.Connection, review_action_id: str, *, replayed: bool
    ) -> ClaimReviewReceipt:
        row = con.execute(
            "SELECT mode FROM review_actions WHERE id=?", (review_action_id,)
        ).fetchone()
        if row is None:
            raise ReviewInvariantError("committed ReviewAction disappeared")
        reviews = con.execute(
            """
            SELECT id,claim_revision_id
            FROM claim_reviews WHERE review_action_id=?
            ORDER BY claim_revision_id
            """,
            (review_action_id,),
        ).fetchall()
        revision_ids = tuple(item[1] for item in reviews)
        return ClaimReviewReceipt(
            review_action_id,
            row[0],
            tuple(item[0] for item in reviews),
            revision_ids,
            self._subject_sha(revision_ids),
            replayed,
        )

    @staticmethod
    def _subject_sha(revision_ids: tuple[str, ...]) -> str:
        payload = json.dumps(
            sorted(revision_ids), ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()
