"""Read model for Mesa de control claim supervision."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from canario.deposit.archive import EvidenceArchive
from canario.deposit.ids import validate_id
from canario.lector.locators import reopen_selector
from canario.persistence import open_readonly_v1
from canario.processors.targets import TargetRegistry

from .contracts import ClaimBatch
from .control import ClaimControlSnapshot, load_claim_control_snapshot

ConnectionFactory = Callable[[Path], sqlite3.Connection]


class ReviewReadError(RuntimeError):
    """Review material cannot be resolved safely."""


@dataclass(frozen=True, slots=True)
class ClaimReviewState:
    claim_revision_id: str
    claim_id: str
    revision_no: int
    text: str
    origin_kind: str
    lifecycle: str
    current: bool
    sensitive: bool
    quantitative: bool
    latest_decision: str | None
    latest_reviewer: str | None
    latest_reason: str | None
    latest_reviewed_at: str | None

    @property
    def machine_only(self) -> bool:
        return self.origin_kind in {"machine", "rule"} and self.latest_decision is None

    @property
    def human_reviewed(self) -> bool:
        return self.latest_decision is not None

    @property
    def unreviewed_human(self) -> bool:
        return self.origin_kind == "human" and self.latest_decision is None

    @property
    def strict_ready(self) -> bool:
        return self.current and self.lifecycle == "active" and self.latest_decision == "accepted"


@dataclass(frozen=True, slots=True)
class ClaimRevisionHistoryEntry:
    claim_revision_id: str
    revision_no: int
    text: str
    origin_kind: str
    lifecycle: str
    current: bool
    action: str | None
    actor: str | None
    rationale: str | None
    action_created_at: str | None


@dataclass(frozen=True, slots=True)
class ClaimEvidencePreview:
    evidence_link_id: str
    representation_target_id: str
    representation_id: str
    relation: str
    selector_kind: str
    selector_version: str
    selector_payload_json: str
    media_type: str
    preview: object


@dataclass(frozen=True, slots=True)
class ClaimReviewDetail:
    claim: ClaimReviewState
    evidence: tuple[ClaimEvidencePreview, ...]


class ReviewReader:
    """Bounded read surface for claim review queues and exact evidence reopening."""

    def __init__(
        self,
        database_path: str | Path,
        archive_root: str | Path,
        *,
        target_registry: TargetRegistry | None = None,
        connection_factory: ConnectionFactory = open_readonly_v1,
    ) -> None:
        self.database_path = Path(database_path)
        self.archive = EvidenceArchive(archive_root)
        self.target_registry = target_registry or TargetRegistry()
        self._connect = connection_factory

    def claim_state(self, revision_id: str) -> ClaimReviewState:
        validate_id(revision_id, "clrev_")
        con = self._connect(self.database_path)
        try:
            row = self._claim_state_row(con, revision_id)
            if row is None:
                raise ReviewReadError(f"unknown ClaimRevision: {revision_id}")
            return self._state_from_row(row)
        finally:
            con.close()

    def prepare_claim_control(self, revision_id: str) -> ClaimControlSnapshot:
        validate_id(revision_id, "clrev_")
        con = self._connect(self.database_path)
        try:
            snapshot = load_claim_control_snapshot(con, revision_id)
            if snapshot is None:
                raise ReviewReadError(f"unknown ClaimRevision: {revision_id}")
            if not snapshot.current:
                raise ReviewReadError("ClaimRevision control requires the exact current revision")
            return snapshot
        finally:
            con.close()

    def claim_history(self, claim_id: str) -> tuple[ClaimRevisionHistoryEntry, ...]:
        validate_id(claim_id, "clm_")
        con = self._connect(self.database_path)
        try:
            rows = con.execute(
                """
                SELECT cr.id,cr.revision_no,cr.text,cr.origin_kind,cr.lifecycle,
                       NOT EXISTS (
                         SELECT 1 FROM claim_revisions successor
                         WHERE successor.supersedes_revision_id=cr.id
                       ) AS is_current,
                       action.action,action.actor,action.rationale,action.created_at
                FROM claim_revisions cr
                LEFT JOIN claim_revision_actions action ON action.result_revision_id=cr.id
                WHERE cr.claim_id=?
                ORDER BY cr.revision_no,cr.id
                """,
                (claim_id,),
            ).fetchall()
            if not rows:
                raise ReviewReadError(f"unknown Claim: {claim_id}")
            return tuple(
                ClaimRevisionHistoryEntry(
                    claim_revision_id=row[0],
                    revision_no=int(row[1]),
                    text=row[2],
                    origin_kind=row[3],
                    lifecycle=row[4],
                    current=bool(row[5]),
                    action=row[6],
                    actor=row[7],
                    rationale=row[8],
                    action_created_at=row[9],
                )
                for row in rows
            )
        finally:
            con.close()

    def prepare_claim_batch(
        self,
        representation_id: str,
        *,
        limit: int = 100,
        include_needs_work: bool = True,
    ) -> ClaimBatch:
        validate_id(representation_id, "rep_")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 2_000:
            raise ValueError("claim batch limit must be within 1..2000")
        con = self._connect(self.database_path)
        try:
            if con.execute(
                "SELECT 1 FROM representations WHERE id=?", (representation_id,)
            ).fetchone() is None:
                raise ReviewReadError(f"unknown Representation: {representation_id}")
            rows = con.execute(
                """
                SELECT cr.id
                FROM claim_revisions cr
                WHERE cr.origin_kind IN ('machine','rule')
                  AND cr.lifecycle='active'
                  AND NOT EXISTS (
                    SELECT 1 FROM claim_revisions successor
                    WHERE successor.supersedes_revision_id=cr.id
                  )
                  AND EXISTS (
                    SELECT 1
                    FROM evidence_links e
                    JOIN representation_targets t ON t.id=e.representation_target_id
                    WHERE e.claim_revision_id=cr.id
                      AND t.representation_id=?
                      AND e.lifecycle='active'
                      AND NOT EXISTS (
                        SELECT 1 FROM evidence_links successor
                        WHERE successor.supersedes_evidence_link_id=e.id
                      )
                  )
                ORDER BY cr.created_at, cr.id
                """,
                (representation_id,),
            ).fetchall()
            selected: list[str] = []
            for (revision_id,) in rows:
                state = self._claim_state_row(con, revision_id)
                assert state is not None
                latest_decision = state[8]
                if latest_decision is None or (
                    include_needs_work and latest_decision == "needs_work"
                ):
                    selected.append(revision_id)
                    if len(selected) >= limit:
                        break
            return ClaimBatch(representation_id, tuple(selected))
        finally:
            con.close()

    def open_claim(self, revision_id: str) -> ClaimReviewDetail:
        validate_id(revision_id, "clrev_")
        con = self._connect(self.database_path)
        try:
            row = self._claim_state_row(con, revision_id)
            if row is None:
                raise ReviewReadError(f"unknown ClaimRevision: {revision_id}")
            claim = self._state_from_row(row)
            evidence_rows = con.execute(
                """
                SELECT e.id,e.representation_target_id,t.representation_id,e.relation,
                       t.selector_kind,t.selector_version,t.selector_payload_json,
                       r.artifact_id,r.kind,r.media_type,r.charset,r.availability,
                       a.media_type,a.availability,
                       CASE WHEN r.kind='original' THEN a.archive_object_id ELSE r.archive_object_id END
                FROM evidence_links e
                JOIN representation_targets t ON t.id=e.representation_target_id
                JOIN representations r ON r.id=t.representation_id
                JOIN artifacts a ON a.id=r.artifact_id
                WHERE e.claim_revision_id=?
                  AND e.lifecycle='active'
                  AND NOT EXISTS (
                    SELECT 1 FROM evidence_links successor
                    WHERE successor.supersedes_evidence_link_id=e.id
                  )
                ORDER BY e.id
                """,
                (revision_id,),
            ).fetchall()
            previews: list[ClaimEvidencePreview] = []
            for item in evidence_rows:
                (
                    link_id,
                    target_id,
                    representation_id,
                    relation,
                    selector_kind,
                    selector_version,
                    payload_json,
                    _artifact_id,
                    _rep_kind,
                    rep_media_type,
                    charset,
                    rep_availability,
                    artifact_media_type,
                    artifact_availability,
                    archive_object_id,
                ) = item
                if rep_availability == "purged" or artifact_availability == "purged":
                    raise ReviewReadError("claim evidence bytes have been purged")
                if archive_object_id is None:
                    raise ReviewReadError("claim evidence has no retained byte authority")
                archive_row = con.execute(
                    """
                    SELECT content_sha256,byte_size,storage_key,availability
                    FROM archive_objects WHERE id=?
                    """,
                    (archive_object_id,),
                ).fetchone()
                if archive_row is None or archive_row[3] != "available":
                    raise ReviewReadError("claim evidence ArchiveObject is unavailable")
                digest, size, storage_key, _ = archive_row
                self.archive.verify(storage_key, digest, size)
                source_bytes = self.archive.path_for_key(storage_key).read_bytes()
                canonical = self.target_registry.validate(
                    selector_kind, selector_version, payload_json
                )
                preview = self._preview(
                    selector_kind,
                    selector_version,
                    canonical,
                    source_bytes,
                    charset,
                    digest,
                    size,
                )
                previews.append(
                    ClaimEvidencePreview(
                        link_id,
                        target_id,
                        representation_id,
                        relation,
                        selector_kind,
                        selector_version,
                        canonical,
                        rep_media_type or artifact_media_type or "application/octet-stream",
                        preview,
                    )
                )
            return ClaimReviewDetail(claim, tuple(previews))
        finally:
            con.close()

    def _claim_state_row(self, con: sqlite3.Connection, revision_id: str):
        return con.execute(
            """
            SELECT cr.id,cr.claim_id,cr.revision_no,cr.text,cr.origin_kind,cr.lifecycle,
                   NOT EXISTS (
                     SELECT 1 FROM claim_revisions successor
                     WHERE successor.supersedes_revision_id=cr.id
                   ) AS is_current,
                   cr.sensitive,
                   latest.decision,latest.reviewer,latest.reason,latest.created_at,
                   cr.quantitative
            FROM claim_revisions cr
            LEFT JOIN claim_reviews latest ON latest.id=(
              SELECT r.id
              FROM claim_reviews r
              WHERE r.claim_revision_id=cr.id
              ORDER BY r.created_at DESC,r.id DESC
              LIMIT 1
            )
            WHERE cr.id=?
            """,
            (revision_id,),
        ).fetchone()

    @staticmethod
    def _state_from_row(row) -> ClaimReviewState:
        return ClaimReviewState(
            claim_revision_id=row[0],
            claim_id=row[1],
            revision_no=row[2],
            text=row[3],
            origin_kind=row[4],
            lifecycle=row[5],
            current=bool(row[6]),
            sensitive=bool(row[7]),
            latest_decision=row[8],
            latest_reviewer=row[9],
            latest_reason=row[10],
            latest_reviewed_at=row[11],
            quantitative=bool(row[12]),
        )

    @staticmethod
    def _preview(
        kind: str,
        version: str,
        payload_json: str,
        source_bytes: bytes,
        charset: str | None,
        digest: str,
        size: int,
    ) -> object:
        payload = json.loads(payload_json)
        if (kind, version) == ("whole", "v1"):
            return {"kind": "whole", "content_sha256": digest, "byte_size": size}
        # Lector-created fine-grained selectors have deterministic reopeners. Reopening
        # is the authority check; the preview itself stays bounded to locator material.
        reopen_selector(kind, version, payload_json, source_bytes=source_bytes, charset=charset)
        if (kind, version) == ("text_quote", "v1"):
            return {
                "kind": "text_quote",
                "exact": payload["exact"],
                "prefix": payload.get("prefix"),
                "suffix": payload.get("suffix"),
                "start_char": payload.get("start_char"),
                "end_char": payload.get("end_char"),
            }
        if (kind, version) == ("table_range", "v1"):
            return {
                "kind": "table_range",
                "sheet": payload.get("sheet"),
                "table_name": payload.get("table_name"),
                "a1_range": payload.get("a1_range"),
                "row_start": payload.get("row_start"),
                "row_end": payload.get("row_end"),
                "headers": payload.get("headers"),
                "observed_values": payload.get("observed_values"),
            }
        if (kind, version) == ("media", "v1"):
            return {
                "kind": "media",
                "start_us": payload["start_us"],
                "end_us": payload["end_us"],
                "duration_us": payload["duration_us"],
                "transcript_exact": payload.get("transcript_exact"),
            }
        raise ReviewReadError(f"review cannot reopen selector contract: {kind}:{version}")
