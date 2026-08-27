"""Canonical human ClaimRevision correction/restriction writes."""

from __future__ import annotations

import sqlite3
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from canario.deposit.ids import new_id, validate_timestamp
from canario.persistence import open_writable_v1

from .contracts import ClaimRevisionControlRequest
from .control import ClaimControlSnapshot, load_claim_control_snapshot

ConnectionFactory = Callable[[Path], sqlite3.Connection]


class ClaimControlWriteError(RuntimeError):
    """A human ClaimRevision control action could not be persisted honestly."""


class ClaimControlInvariantError(ClaimControlWriteError):
    """A ClaimRevision control request violates the bounded mutation contract."""


class ClaimControlIdentityCollision(ClaimControlWriteError):
    """A stable control identity is occupied by different immutable content."""


@dataclass(frozen=True, slots=True)
class ClaimRevisionControlReceipt:
    claim_revision_action_id: str
    claim_id: str
    source_revision_id: str
    result_revision_id: str
    action: str
    request_sha256: str
    evidence_link_ids: tuple[str, ...]
    entity_link_ids: tuple[str, ...]
    tag_link_ids: tuple[str, ...]
    review_action_id: str | None
    claim_review_id: str | None
    replayed: bool


class ClaimControlWriter:
    """Sole core writer for human ClaimRevision correction/lifecycle lineage."""

    def __init__(
        self,
        database_path: str | Path,
        *,
        connection_factory: ConnectionFactory = open_writable_v1,
    ) -> None:
        self.database_path = Path(database_path)
        self._connect = connection_factory

    def record(
        self,
        request: ClaimRevisionControlRequest,
        *,
        created_at: str,
    ) -> ClaimRevisionControlReceipt:
        validate_timestamp(created_at)
        con = self._connect(self.database_path)
        try:
            con.execute("BEGIN IMMEDIATE")
            replay = self._replay_if_present(con, request)
            if replay is not None:
                con.rollback()
                return replay

            if con.execute(
                "SELECT 1 FROM claim_revisions WHERE id=?", (request.result_revision_id,)
            ).fetchone() is not None:
                raise ClaimControlIdentityCollision("result ClaimRevision ID collision")
            if request.review_action_id is not None and con.execute(
                "SELECT 1 FROM review_actions WHERE id=?", (request.review_action_id,)
            ).fetchone() is not None:
                raise ClaimControlIdentityCollision("correction ReviewAction ID collision")

            source = load_claim_control_snapshot(con, request.source_revision_id)
            if source is None:
                raise ClaimControlInvariantError(
                    f"unknown source ClaimRevision: {request.source_revision_id}"
                )
            if not source.current:
                raise ClaimControlInvariantError(
                    "ClaimRevision control may target only the exact current revision"
                )
            if source.snapshot_sha256 != request.expected_snapshot_sha256:
                raise ClaimControlInvariantError(
                    "ClaimRevision control snapshot is stale"
                )

            result_fields, evidence_sources, entity_sources, tag_sources = self._plan(
                con, source, request
            )
            self._insert_result_revision(
                con,
                source,
                request,
                result_fields,
                created_at,
            )
            claim_review_id = self._insert_correction_acceptance(
                con, request, created_at
            )
            con.execute(
                """
                INSERT INTO claim_revision_actions(
                  id,claim_id,source_revision_id,result_revision_id,action,actor,
                  rationale,review_action_id,request_sha256,created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    request.claim_revision_action_id,
                    source.claim_id,
                    source.claim_revision_id,
                    request.result_revision_id,
                    request.action,
                    request.actor,
                    request.rationale,
                    request.review_action_id,
                    request.request_sha256(),
                    created_at,
                ),
            )
            evidence_ids = self._copy_evidence(
                con, request.result_revision_id, evidence_sources, created_at
            )
            entity_ids = self._copy_entity_links(
                con, request.result_revision_id, entity_sources, created_at
            )
            tag_ids = self._copy_tag_links(
                con, request.result_revision_id, tag_sources, created_at
            )
            self._refresh_claim_fts(
                con,
                source.claim_id,
                request.result_revision_id,
                result_fields["text"],
                result_fields["lifecycle"],
            )
            self._validate_result(
                con,
                source,
                request,
                result_fields,
                evidence_sources,
                entity_sources,
                tag_sources,
            )
            self._validate_correction_acceptance(
                con, request, action_created_at=created_at
            )
            con.commit()
            return ClaimRevisionControlReceipt(
                request.claim_revision_action_id,
                source.claim_id,
                source.claim_revision_id,
                request.result_revision_id,
                request.action,
                request.request_sha256(),
                evidence_ids,
                entity_ids,
                tag_ids,
                request.review_action_id,
                claim_review_id,
                False,
            )
        except sqlite3.IntegrityError as exc:
            if con.in_transaction:
                con.rollback()
            raise ClaimControlWriteError(
                f"SQLite rejected ClaimRevision control write: {exc}"
            ) from exc
        except Exception:
            if con.in_transaction:
                con.rollback()
            raise
        finally:
            con.close()

    def _replay_if_present(
        self, con: sqlite3.Connection, request: ClaimRevisionControlRequest
    ) -> ClaimRevisionControlReceipt | None:
        row = con.execute(
            """
            SELECT claim_id,source_revision_id,result_revision_id,action,actor,rationale,
                   review_action_id,request_sha256,created_at
            FROM claim_revision_actions WHERE id=?
            """,
            (request.claim_revision_action_id,),
        ).fetchone()
        if row is None:
            return None
        if (
            row[1] != request.source_revision_id
            or row[2] != request.result_revision_id
            or row[3] != request.action
            or row[4] != request.actor
            or row[5] != request.rationale
            or row[6] != request.review_action_id
            or row[7] != request.request_sha256()
        ):
            raise ClaimControlIdentityCollision("ClaimRevision action ID collision")

        source = load_claim_control_snapshot(con, request.source_revision_id)
        if source is None or source.claim_id != row[0]:
            raise ClaimControlIdentityCollision("ClaimRevision action source identity drift")
        if source.snapshot_sha256 != request.expected_snapshot_sha256:
            raise ClaimControlIdentityCollision("ClaimRevision action source snapshot drift")
        result_fields, evidence_sources, entity_sources, tag_sources = self._plan(
            con, source, request, replay=True
        )
        self._validate_result(
            con,
            source,
            request,
            result_fields,
            evidence_sources,
            entity_sources,
            tag_sources,
        )
        claim_review_id = self._validate_correction_acceptance(
            con, request, action_created_at=row[8]
        )
        evidence_ids, entity_ids, tag_ids = self._result_link_ids(
            con, request.result_revision_id
        )
        return ClaimRevisionControlReceipt(
            request.claim_revision_action_id,
            source.claim_id,
            source.claim_revision_id,
            request.result_revision_id,
            request.action,
            request.request_sha256(),
            evidence_ids,
            entity_ids,
            tag_ids,
            request.review_action_id,
            claim_review_id,
            True,
        )

    @staticmethod
    def _insert_correction_acceptance(
        con: sqlite3.Connection,
        request: ClaimRevisionControlRequest,
        created_at: str,
    ) -> str | None:
        if request.action != "correct":
            return None
        assert request.review_action_id is not None
        con.execute(
            "INSERT INTO review_actions(id,actor,mode,created_at,note) VALUES (?,?,?,?,?)",
            (
                request.review_action_id,
                request.actor,
                "supervised",
                created_at,
                "Accepted as part of human correction",
            ),
        )
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
                request.result_revision_id,
                "accepted",
                request.actor,
                request.rationale,
                created_at,
            ),
        )
        return review_id

    @staticmethod
    def _validate_correction_acceptance(
        con: sqlite3.Connection,
        request: ClaimRevisionControlRequest,
        *,
        action_created_at: str,
    ) -> str | None:
        if request.action != "correct":
            if request.review_action_id is not None:
                raise ClaimControlIdentityCollision(
                    "lifecycle ClaimRevision action unexpectedly has ReviewAction identity"
                )
            return None
        assert request.review_action_id is not None
        action = con.execute(
            "SELECT actor,mode,created_at,note FROM review_actions WHERE id=?",
            (request.review_action_id,),
        ).fetchone()
        expected_action = (
            request.actor,
            "supervised",
            action_created_at,
            "Accepted as part of human correction",
        )
        if action != expected_action:
            raise ClaimControlIdentityCollision("correction ReviewAction payload drift")
        reviews = con.execute(
            """
            SELECT id,claim_revision_id,decision,reviewer,reason,created_at
            FROM claim_reviews WHERE review_action_id=? ORDER BY id
            """,
            (request.review_action_id,),
        ).fetchall()
        if len(reviews) != 1:
            raise ClaimControlIdentityCollision(
                "correction ReviewAction must own exactly one ClaimReview"
            )
        review = reviews[0]
        if review[1:] != (
            request.result_revision_id,
            "accepted",
            request.actor,
            request.rationale,
            action_created_at,
        ):
            raise ClaimControlIdentityCollision("correction ClaimReview payload drift")
        return review[0]

    def _plan(
        self,
        con: sqlite3.Connection,
        source: ClaimControlSnapshot,
        request: ClaimRevisionControlRequest,
        *,
        replay: bool = False,
    ) -> tuple[dict[str, object], tuple[tuple, ...], tuple[tuple, ...], tuple[tuple, ...]]:
        if request.action == "correct":
            if source.claim_kind == "derived_inference":
                raise ClaimControlInvariantError(
                    "derived_inference correction requires a new exact DerivationResultTarget and is outside REVIEW-002"
                )
            if source.lifecycle not in {"active", "restricted"}:
                raise ClaimControlInvariantError(
                    "only active/restricted claims may be corrected"
                )
            assert request.correction is not None
            correction = request.correction
            result = {
                "claim_kind": correction.claim_kind,
                "text": correction.text,
                "attribution_entity_id": correction.attribution_entity_id,
                "attribution_text": correction.attribution_text,
                "temporal_start": correction.temporal_start,
                "temporal_end": correction.temporal_end,
                "sensitive": correction.sensitive,
                "quantitative": correction.quantitative,
                "lifecycle": source.lifecycle,
            }
            source_semantic = (
                source.claim_kind,
                source.text,
                source.attribution_entity_id,
                source.attribution_text,
                source.temporal_start,
                source.temporal_end,
                source.sensitive,
                source.quantitative,
            )
            result_semantic = (
                correction.claim_kind,
                correction.text,
                correction.attribution_entity_id,
                correction.attribution_text,
                correction.temporal_start,
                correction.temporal_end,
                correction.sensitive,
                correction.quantitative,
            )
            if source_semantic == result_semantic:
                raise ClaimControlInvariantError(
                    "correct action must materially change ClaimRevision semantic fields"
                )
            evidence_ids = correction.evidence_link_ids
            entity_ids = correction.entity_link_ids
            tag_ids = correction.tag_link_ids
            self._require_selected_subset(
                evidence_ids, source.evidence_link_ids, "correction evidence"
            )
            self._require_selected_subset(
                entity_ids, source.entity_link_ids, "correction entity links"
            )
            self._require_selected_subset(
                tag_ids, source.tag_link_ids, "correction tag links"
            )
            if not evidence_ids:
                raise ClaimControlInvariantError(
                    "human correction requires at least one exact carried evidence link"
                )
        else:
            result = {
                "claim_kind": source.claim_kind,
                "text": source.text,
                "attribution_entity_id": source.attribution_entity_id,
                "attribution_text": source.attribution_text,
                "temporal_start": source.temporal_start,
                "temporal_end": source.temporal_end,
                "sensitive": source.sensitive,
                "quantitative": source.quantitative,
                "lifecycle": self._target_lifecycle(source.lifecycle, request.action),
            }
            evidence_ids = source.evidence_link_ids
            entity_ids = source.entity_link_ids
            tag_ids = source.tag_link_ids

        evidence_sources = self._load_evidence_sources(con, source, evidence_ids)
        entity_sources = self._load_entity_sources(con, source, entity_ids)
        tag_sources = self._load_tag_sources(con, source, tag_ids)
        if result["lifecycle"] == "active" and not replay:
            # First commit must prove current evidence custody is still usable.
            # Replay validates the immutable historical action/result that already
            # exists; later custody restriction/purge must not retroactively make
            # that persistence retry a different operation.
            self._require_active_evidence_custody(con, evidence_sources)
        if request.action == "correct" and result["claim_kind"] == "source_assertion":
            if not any(
                item[2] == "active" and item[1] in {"supports", "quotes"}
                for item in evidence_sources
            ):
                raise ClaimControlInvariantError(
                    "corrected source_assertion requires active supports/quotes evidence"
                )
        return result, evidence_sources, entity_sources, tag_sources

    @staticmethod
    def _target_lifecycle(source_lifecycle: str, action: str) -> str:
        if action == "restrict":
            if source_lifecycle != "active":
                raise ClaimControlInvariantError("restrict requires an active ClaimRevision")
            return "restricted"
        if action == "unrestrict":
            if source_lifecycle != "restricted":
                raise ClaimControlInvariantError("unrestrict requires a restricted ClaimRevision")
            return "active"
        if action == "retract":
            if source_lifecycle not in {"active", "restricted"}:
                raise ClaimControlInvariantError(
                    "retract requires an active or restricted ClaimRevision"
                )
            return "retracted"
        raise ClaimControlInvariantError(f"unsupported lifecycle action: {action}")

    @staticmethod
    def _require_selected_subset(
        selected: tuple[str, ...], available: tuple[str, ...], label: str
    ) -> None:
        unknown = set(selected) - set(available)
        if unknown:
            raise ClaimControlInvariantError(
                f"{label} contains IDs outside the exact prepared source snapshot"
            )

    @staticmethod
    def _load_evidence_sources(
        con: sqlite3.Connection,
        source: ClaimControlSnapshot,
        ids: tuple[str, ...],
    ) -> tuple[tuple, ...]:
        rows: list[tuple] = []
        for link_id in ids:
            row = con.execute(
                """
                SELECT representation_target_id,relation,lifecycle,rationale
                FROM evidence_links
                WHERE id=? AND claim_revision_id=?
                """,
                (link_id, source.claim_revision_id),
            ).fetchone()
            if row is None:
                raise ClaimControlInvariantError("selected evidence link disappeared")
            rows.append(tuple(row))
        return tuple(rows)

    @staticmethod
    def _require_active_evidence_custody(
        con: sqlite3.Connection, evidence_sources: tuple[tuple, ...]
    ) -> None:
        for target_id, _relation, _lifecycle, _rationale in evidence_sources:
            row = con.execute(
                """
                SELECT t.availability,r.availability,a.availability
                FROM representation_targets t
                JOIN representations r ON r.id=t.representation_id
                JOIN artifacts a ON a.id=r.artifact_id
                WHERE t.id=?
                """,
                (target_id,),
            ).fetchone()
            if row is None:
                raise ClaimControlInvariantError(
                    "selected evidence target no longer has retained custody"
                )
            target_availability, representation_availability, artifact_availability = row
            if (
                target_availability != "available"
                or representation_availability != "available"
                or artifact_availability != "available"
            ):
                raise ClaimControlInvariantError(
                    "active ClaimRevision cannot rely on restricted or purged evidence custody"
                )

    @staticmethod
    def _load_entity_sources(
        con: sqlite3.Connection,
        source: ClaimControlSnapshot,
        ids: tuple[str, ...],
    ) -> tuple[tuple, ...]:
        rows: list[tuple] = []
        for link_id in ids:
            row = con.execute(
                """
                SELECT entity_id,role,lifecycle,rationale
                FROM claim_entity_links
                WHERE id=? AND claim_revision_id=?
                """,
                (link_id, source.claim_revision_id),
            ).fetchone()
            if row is None:
                raise ClaimControlInvariantError("selected entity link disappeared")
            rows.append(tuple(row))
        return tuple(rows)

    @staticmethod
    def _load_tag_sources(
        con: sqlite3.Connection,
        source: ClaimControlSnapshot,
        ids: tuple[str, ...],
    ) -> tuple[tuple, ...]:
        rows: list[tuple] = []
        for link_id in ids:
            row = con.execute(
                """
                SELECT tag_id,lifecycle,rationale
                FROM claim_tag_links
                WHERE id=? AND claim_revision_id=?
                """,
                (link_id, source.claim_revision_id),
            ).fetchone()
            if row is None:
                raise ClaimControlInvariantError("selected tag link disappeared")
            rows.append(tuple(row))
        return tuple(rows)

    @staticmethod
    def _insert_result_revision(
        con: sqlite3.Connection,
        source: ClaimControlSnapshot,
        request: ClaimRevisionControlRequest,
        fields: dict[str, object],
        created_at: str,
    ) -> None:
        con.execute(
            """
            INSERT INTO claim_revisions(
              id,claim_id,revision_no,supersedes_revision_id,claim_kind,text,
              origin_kind,process_run_id,derivation_result_target_id,
              attribution_entity_id,attribution_text,temporal_start,temporal_end,
              sensitive,quantitative,lifecycle,created_at
            ) VALUES (?,?,?,?,?,?, 'human',NULL,?,?,?,?,?,?,?,?,?)
            """,
            (
                request.result_revision_id,
                source.claim_id,
                source.revision_no + 1,
                source.claim_revision_id,
                fields["claim_kind"],
                fields["text"],
                source.derivation_result_target_id,
                fields["attribution_entity_id"],
                fields["attribution_text"],
                fields["temporal_start"],
                fields["temporal_end"],
                int(bool(fields["sensitive"])),
                int(bool(fields["quantitative"])),
                fields["lifecycle"],
                created_at,
            ),
        )

    @staticmethod
    def _copy_evidence(
        con: sqlite3.Connection,
        revision_id: str,
        rows: tuple[tuple, ...],
        created_at: str,
    ) -> tuple[str, ...]:
        ids: list[str] = []
        for target_id, relation, lifecycle, rationale in rows:
            link_id = new_id("evl_")
            con.execute(
                """
                INSERT INTO evidence_links(
                  id,supersedes_evidence_link_id,claim_revision_id,representation_target_id,
                  relation,origin_kind,process_run_id,lifecycle,rationale,created_at
                ) VALUES (?,NULL,?,?,?,'human',NULL,?,?,?)
                """,
                (link_id, revision_id, target_id, relation, lifecycle, rationale, created_at),
            )
            ids.append(link_id)
        return tuple(ids)

    @staticmethod
    def _copy_entity_links(
        con: sqlite3.Connection,
        revision_id: str,
        rows: tuple[tuple, ...],
        created_at: str,
    ) -> tuple[str, ...]:
        ids: list[str] = []
        for entity_id, role, lifecycle, rationale in rows:
            link_id = new_id("clent_")
            con.execute(
                """
                INSERT INTO claim_entity_links(
                  id,supersedes_claim_entity_link_id,claim_revision_id,entity_id,
                  mention_id,mention_resolution_revision_id,role,origin_kind,process_run_id,
                  lifecycle,rationale,created_at
                ) VALUES (?,NULL,?,?,NULL,NULL,?,'human',NULL,?,?,?)
                """,
                (link_id, revision_id, entity_id, role, lifecycle, rationale, created_at),
            )
            ids.append(link_id)
        return tuple(ids)

    @staticmethod
    def _copy_tag_links(
        con: sqlite3.Connection,
        revision_id: str,
        rows: tuple[tuple, ...],
        created_at: str,
    ) -> tuple[str, ...]:
        ids: list[str] = []
        for tag_id, lifecycle, rationale in rows:
            link_id = new_id("cltag_")
            con.execute(
                """
                INSERT INTO claim_tag_links(
                  id,supersedes_claim_tag_link_id,claim_revision_id,tag_id,
                  origin_kind,process_run_id,lifecycle,rationale,created_at
                ) VALUES (?,NULL,?,?,'human',NULL,?,?,?)
                """,
                (link_id, revision_id, tag_id, lifecycle, rationale, created_at),
            )
            ids.append(link_id)
        return tuple(ids)

    @staticmethod
    def _refresh_claim_fts(
        con: sqlite3.Connection,
        claim_id: str,
        result_revision_id: str,
        result_text: object,
        result_lifecycle: object,
    ) -> None:
        # FTS is a derived retrieval surface, not civic history. Rebuild the
        # Claim's entire FTS footprint so a historical active row can never leak
        # text after correction/restriction/retraction. ClaimRevision rows remain
        # append-only in canonical storage.
        con.execute(
            """
            DELETE FROM claim_fts
            WHERE claim_revision_id IN (
              SELECT id FROM claim_revisions WHERE claim_id=?
            )
            """,
            (claim_id,),
        )
        if result_lifecycle == "active":
            con.execute(
                "INSERT INTO claim_fts(claim_revision_id,text) VALUES (?,?)",
                (result_revision_id, str(result_text)),
            )

    def _validate_result(
        self,
        con: sqlite3.Connection,
        source: ClaimControlSnapshot,
        request: ClaimRevisionControlRequest,
        fields: dict[str, object],
        evidence_sources: tuple[tuple, ...],
        entity_sources: tuple[tuple, ...],
        tag_sources: tuple[tuple, ...],
    ) -> None:
        row = con.execute(
            """
            SELECT claim_id,revision_no,supersedes_revision_id,claim_kind,text,origin_kind,
                   process_run_id,derivation_result_target_id,attribution_entity_id,
                   attribution_text,temporal_start,temporal_end,sensitive,quantitative,lifecycle
            FROM claim_revisions WHERE id=?
            """,
            (request.result_revision_id,),
        ).fetchone()
        expected = (
            source.claim_id,
            source.revision_no + 1,
            source.claim_revision_id,
            fields["claim_kind"],
            fields["text"],
            "human",
            None,
            source.derivation_result_target_id,
            fields["attribution_entity_id"],
            fields["attribution_text"],
            fields["temporal_start"],
            fields["temporal_end"],
            int(bool(fields["sensitive"])),
            int(bool(fields["quantitative"])),
            fields["lifecycle"],
        )
        if row != expected:
            raise ClaimControlIdentityCollision("result ClaimRevision payload drift")
        evidence = tuple(
            con.execute(
                """
                SELECT representation_target_id,relation,lifecycle,rationale
                FROM evidence_links WHERE claim_revision_id=? ORDER BY id
                """,
                (request.result_revision_id,),
            ).fetchall()
        )
        entities = tuple(
            con.execute(
                """
                SELECT entity_id,role,lifecycle,rationale
                FROM claim_entity_links WHERE claim_revision_id=? ORDER BY id
                """,
                (request.result_revision_id,),
            ).fetchall()
        )
        tags = tuple(
            con.execute(
                """
                SELECT tag_id,lifecycle,rationale
                FROM claim_tag_links WHERE claim_revision_id=? ORDER BY id
                """,
                (request.result_revision_id,),
            ).fetchall()
        )
        if Counter(evidence) != Counter(evidence_sources):
            raise ClaimControlIdentityCollision("result evidence payload drift")
        if Counter(entities) != Counter(entity_sources):
            raise ClaimControlIdentityCollision("result entity-link payload drift")
        if Counter(tags) != Counter(tag_sources):
            raise ClaimControlIdentityCollision("result tag-link payload drift")

    @staticmethod
    def _result_link_ids(
        con: sqlite3.Connection, revision_id: str
    ) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
        evidence = tuple(
            row[0]
            for row in con.execute(
                "SELECT id FROM evidence_links WHERE claim_revision_id=? ORDER BY id",
                (revision_id,),
            ).fetchall()
        )
        entities = tuple(
            row[0]
            for row in con.execute(
                "SELECT id FROM claim_entity_links WHERE claim_revision_id=? ORDER BY id",
                (revision_id,),
            ).fetchall()
        )
        tags = tuple(
            row[0]
            for row in con.execute(
                "SELECT id FROM claim_tag_links WHERE claim_revision_id=? ORDER BY id",
                (revision_id,),
            ).fetchall()
        )
        return evidence, entities, tags
