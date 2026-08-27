"""Shared ClaimRevision control snapshots for Mesa de control."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass

from canario.deposit.ids import validate_id


@dataclass(frozen=True, slots=True)
class ClaimControlSnapshot:
    claim_revision_id: str
    claim_id: str
    revision_no: int
    current: bool
    claim_kind: str
    text: str
    origin_kind: str
    process_run_id: str | None
    attribution_entity_id: str | None
    attribution_text: str | None
    temporal_start: str | None
    temporal_end: str | None
    sensitive: bool
    quantitative: bool
    lifecycle: str
    derivation_result_target_id: str | None
    evidence_link_ids: tuple[str, ...]
    entity_link_ids: tuple[str, ...]
    tag_link_ids: tuple[str, ...]
    snapshot_sha256: str


def _snapshot_payload(
    *,
    claim_revision_id: str,
    claim_id: str,
    revision_no: int,
    claim_kind: str,
    text: str,
    origin_kind: str,
    process_run_id: str | None,
    attribution_entity_id: str | None,
    attribution_text: str | None,
    temporal_start: str | None,
    temporal_end: str | None,
    sensitive: bool,
    quantitative: bool,
    lifecycle: str,
    derivation_result_target_id: str | None,
    evidence_link_ids: tuple[str, ...],
    entity_link_ids: tuple[str, ...],
    tag_link_ids: tuple[str, ...],
) -> dict[str, object]:
    # `current` is intentionally excluded. After a successful mutation the source
    # revision becomes non-current, but an exact replay must still be able to
    # validate the immutable source snapshot it originally consumed.
    return {
        "claim_revision_id": claim_revision_id,
        "claim_id": claim_id,
        "revision_no": revision_no,
        "claim_kind": claim_kind,
        "text": text,
        "origin_kind": origin_kind,
        "process_run_id": process_run_id,
        "attribution_entity_id": attribution_entity_id,
        "attribution_text": attribution_text,
        "temporal_start": temporal_start,
        "temporal_end": temporal_end,
        "sensitive": sensitive,
        "quantitative": quantitative,
        "lifecycle": lifecycle,
        "derivation_result_target_id": derivation_result_target_id,
        "evidence_link_ids": list(evidence_link_ids),
        "entity_link_ids": list(entity_link_ids),
        "tag_link_ids": list(tag_link_ids),
    }


def snapshot_sha256(**kwargs: object) -> str:
    payload = json.dumps(
        _snapshot_payload(**kwargs),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_claim_control_snapshot(
    con: sqlite3.Connection, revision_id: str
) -> ClaimControlSnapshot | None:
    validate_id(revision_id, "clrev_")
    row = con.execute(
        """
        SELECT cr.id,cr.claim_id,cr.revision_no,cr.claim_kind,cr.text,
               cr.origin_kind,cr.process_run_id,
               cr.attribution_entity_id,cr.attribution_text,cr.temporal_start,cr.temporal_end,
               cr.sensitive,cr.quantitative,cr.lifecycle,cr.derivation_result_target_id,
               NOT EXISTS (
                 SELECT 1 FROM claim_revisions successor
                 WHERE successor.supersedes_revision_id=cr.id
               ) AS is_current
        FROM claim_revisions cr
        WHERE cr.id=?
        """,
        (revision_id,),
    ).fetchone()
    if row is None:
        return None

    evidence = tuple(
        item[0]
        for item in con.execute(
            """
            SELECT e.id
            FROM evidence_links e
            WHERE e.claim_revision_id=?
              AND e.lifecycle IN ('candidate','active')
              AND NOT EXISTS (
                SELECT 1 FROM evidence_links successor
                WHERE successor.supersedes_evidence_link_id=e.id
              )
            ORDER BY e.id
            """,
            (revision_id,),
        ).fetchall()
    )
    entities = tuple(
        item[0]
        for item in con.execute(
            """
            SELECT link.id
            FROM claim_entity_links link
            WHERE link.claim_revision_id=?
              AND link.lifecycle IN ('candidate','active')
              AND NOT EXISTS (
                SELECT 1 FROM claim_entity_links successor
                WHERE successor.supersedes_claim_entity_link_id=link.id
              )
            ORDER BY link.id
            """,
            (revision_id,),
        ).fetchall()
    )
    tags = tuple(
        item[0]
        for item in con.execute(
            """
            SELECT link.id
            FROM claim_tag_links link
            WHERE link.claim_revision_id=?
              AND link.lifecycle IN ('candidate','active')
              AND NOT EXISTS (
                SELECT 1 FROM claim_tag_links successor
                WHERE successor.supersedes_claim_tag_link_id=link.id
              )
            ORDER BY link.id
            """,
            (revision_id,),
        ).fetchall()
    )

    kwargs = dict(
        claim_revision_id=row[0],
        claim_id=row[1],
        revision_no=int(row[2]),
        claim_kind=row[3],
        text=row[4],
        origin_kind=row[5],
        process_run_id=row[6],
        attribution_entity_id=row[7],
        attribution_text=row[8],
        temporal_start=row[9],
        temporal_end=row[10],
        sensitive=bool(row[11]),
        quantitative=bool(row[12]),
        lifecycle=row[13],
        derivation_result_target_id=row[14],
        evidence_link_ids=evidence,
        entity_link_ids=entities,
        tag_link_ids=tags,
    )
    return ClaimControlSnapshot(
        **kwargs,
        current=bool(row[15]),
        snapshot_sha256=snapshot_sha256(**kwargs),
    )
