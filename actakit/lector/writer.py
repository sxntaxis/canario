"""Canonical persistence for bounded Lector semantic extraction attempts."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from actakit.deposit.archive import EvidenceArchive
from actakit.deposit.ids import new_id, validate_timestamp
from actakit.persistence import open_writable_v1
from actakit.processors.contracts import TargetSnapshot
from actakit.processors.targets import TargetRegistry

from .contracts import (
    ClaimDraft,
    ClaimRelationDraft,
    SemanticExtractionRequest,
    SemanticExtractorDescriptor,
    SemanticInvocation,
    SemanticResult,
    TargetRef,
    SYMMETRIC_RELATION_TYPES,
)
from .locators import reopen_selector

ConnectionFactory = Callable[[Path], sqlite3.Connection]


class LectorWriteError(RuntimeError):
    """A bounded semantic write could not be committed honestly."""


class LectorInvariantError(LectorWriteError):
    """A semantic request/result violated canonical Lector invariants."""


class LectorIdentityCollision(LectorWriteError):
    """A stable ProcessRun identity is occupied by different immutable data."""


@dataclass(frozen=True, slots=True)
class PersistedClaim:
    claim_id: str
    revision_id: str


@dataclass(frozen=True, slots=True)
class PersistedClaimRelation:
    relation_id: str
    revision_id: str


@dataclass(frozen=True, slots=True)
class SemanticReceipt:
    process_run_id: str
    outcome: str
    claims: tuple[PersistedClaim, ...]
    evidence_link_ids: tuple[str, ...]
    mention_ids: tuple[str, ...]
    resolution_candidate_ids: tuple[str, ...]
    tag_link_ids: tuple[str, ...]
    entity_link_ids: tuple[str, ...]
    relations: tuple[PersistedClaimRelation, ...]
    relation_basis_link_ids: tuple[str, ...]
    replayed: bool


@dataclass(frozen=True, slots=True)
class SemanticInputMaterial:
    representation_id: str
    artifact_id: str
    representation_kind: str
    media_type: str
    language: str | None
    charset: str | None
    restricted: bool
    source_bytes: bytes
    scopes: tuple[TargetSnapshot, ...]


class LectorWriter:
    """Sole core writer for Lector ProcessRuns and machine/rule/human semantic rows."""

    def __init__(
        self,
        database_path: str | Path,
        archive_root: str | Path,
        *,
        target_registry: TargetRegistry | None = None,
        connection_factory: ConnectionFactory = open_writable_v1,
    ) -> None:
        self.database_path = Path(database_path)
        self.archive = EvidenceArchive(archive_root)
        self.target_registry = target_registry or TargetRegistry()
        self._connect = connection_factory

    def load_input(self, request: SemanticExtractionRequest) -> SemanticInputMaterial:
        con = self._connect(self.database_path)
        try:
            row = con.execute(
                """
                SELECT r.artifact_id,r.kind,r.media_type,r.language,r.charset,r.availability,
                       a.media_type,a.availability,
                       CASE WHEN r.kind='original' THEN a.archive_object_id ELSE r.archive_object_id END
                FROM representations r
                JOIN artifacts a ON a.id=r.artifact_id
                WHERE r.id=?
                """,
                (request.representation_id,),
            ).fetchone()
            if row is None:
                raise LectorInvariantError(
                    f"unknown retained Representation: {request.representation_id}"
                )
            (
                artifact_id,
                representation_kind,
                rep_media_type,
                language,
                charset,
                rep_availability,
                artifact_media_type,
                artifact_availability,
                archive_object_id,
            ) = row
            if rep_availability == "purged" or artifact_availability == "purged":
                raise LectorInvariantError("purged custody cannot be semantically extracted")
            if archive_object_id is None:
                raise LectorInvariantError("retained Representation has no byte authority")
            media_type = rep_media_type or artifact_media_type
            if media_type is None:
                raise LectorInvariantError("semantic extraction requires a known media type")

            archive_row = con.execute(
                """
                SELECT content_sha256,byte_size,storage_key,availability
                FROM archive_objects WHERE id=?
                """,
                (archive_object_id,),
            ).fetchone()
            if archive_row is None or archive_row[3] != "available":
                raise LectorInvariantError("semantic input ArchiveObject is unavailable")
            digest, size, storage_key, _ = archive_row
            self.archive.verify(storage_key, digest, size)
            source_bytes = self.archive.path_for_key(storage_key).read_bytes()

            scopes: list[TargetSnapshot] = []
            for target_id in request.target_ids:
                target = con.execute(
                    """
                    SELECT representation_id,selector_kind,selector_version,
                           selector_payload_json,availability
                    FROM representation_targets WHERE id=?
                    """,
                    (target_id,),
                ).fetchone()
                if target is None:
                    raise LectorInvariantError(f"unknown RepresentationTarget: {target_id}")
                target_rep, selector_kind, selector_version, payload_json, availability = target
                if target_rep != request.representation_id:
                    raise LectorInvariantError(
                        "semantic target does not belong to requested Representation"
                    )
                if availability != "available":
                    raise LectorInvariantError("purged RepresentationTarget cannot be extracted")
                canonical = self.target_registry.validate(
                    selector_kind, selector_version, payload_json
                )
                scopes.append(
                    TargetSnapshot(
                        target_id,
                        target_rep,
                        selector_kind,
                        selector_version,
                        canonical,
                    )
                )
            return SemanticInputMaterial(
                request.representation_id,
                artifact_id,
                representation_kind,
                media_type,
                language,
                charset,
                rep_availability == "restricted" or artifact_availability == "restricted",
                source_bytes,
                tuple(scopes),
            )
        finally:
            con.close()

    @staticmethod
    def invocation(
        request: SemanticExtractionRequest, material: SemanticInputMaterial
    ) -> SemanticInvocation:
        return SemanticInvocation(
            request,
            material.representation_kind,
            material.media_type,
            material.language,
            material.charset,
            material.source_bytes,
            material.scopes,
        )

    def replay_if_present(
        self, request: SemanticExtractionRequest
    ) -> SemanticReceipt | None:
        con = self._connect(self.database_path)
        try:
            return self._verify_existing_run(con, request, None)
        finally:
            con.close()

    def record_attempt(
        self,
        *,
        request: SemanticExtractionRequest,
        descriptor: SemanticExtractorDescriptor,
        material: SemanticInputMaterial,
        result: SemanticResult,
        started_at: str,
        finished_at: str,
    ) -> SemanticReceipt:
        validate_timestamp(started_at)
        validate_timestamp(finished_at)
        if started_at > finished_at:
            raise LectorInvariantError("ProcessRun started_at cannot exceed finished_at")
        self._validate_attempt(request, descriptor, material, result)

        con = self._connect(self.database_path)
        try:
            replay = self._verify_existing_run(con, request, descriptor)
            if replay is not None:
                return replay

            con.execute("BEGIN IMMEDIATE")
            concurrent = self._verify_existing_run(con, request, descriptor)
            if concurrent is not None:
                con.rollback()
                return concurrent
            self._revalidate_material(con, request, material)
            created_at = finished_at

            self._insert_process_run(
                con, request, descriptor, result, started_at, finished_at, created_at
            )
            for ordinal, scope in enumerate(material.scopes):
                con.execute(
                    """
                    INSERT INTO process_run_inputs(
                      process_run_id,ordinal,representation_id,representation_target_id
                    ) VALUES (?,?,?,?)
                    """,
                    (request.process_run_id, ordinal, material.representation_id, scope.id),
                )

            if descriptor.requires_egress:
                assert result.egress_bytes is not None
                con.execute(
                    """
                    INSERT INTO process_run_egress(
                      process_run_id,bytes_egressed,policy_profile,data_control_profile,
                      request_template_hash,endpoint_profile,created_at
                    ) VALUES (?,?,?,?,?,?,?)
                    """,
                    (
                        request.process_run_id,
                        result.egress_bytes,
                        request.egress.policy_profile,
                        request.egress.data_control_profile,
                        request.egress.request_template_hash,
                        request.egress.endpoint_profile,
                        created_at,
                    ),
                )

            if result.outcome != "failed":
                target_cache: dict[TargetRef, str] = {}
                revision_by_local: dict[str, str] = {}
                for claim in result.claims:
                    claim_id = new_id("clm_")
                    revision_id = new_id("clrev_")
                    con.execute(
                        "INSERT INTO claims(id,created_at) VALUES (?,?)",
                        (claim_id, created_at),
                    )
                    if claim.attribution_entity_id is not None:
                        self._require_entity(con, claim.attribution_entity_id)
                    con.execute(
                        """
                        INSERT INTO claim_revisions(
                          id,claim_id,revision_no,supersedes_revision_id,claim_kind,text,
                          origin_kind,process_run_id,attribution_entity_id,attribution_text,
                          temporal_start,temporal_end,sensitive,quantitative,lifecycle,created_at
                        ) VALUES (?,?,1,NULL,?,?,?,?,?,?,?,?,?,?,?,?)
                        """,
                        (
                            revision_id,
                            claim_id,
                            claim.claim_kind,
                            claim.text,
                            descriptor.origin_kind,
                            request.process_run_id,
                            claim.attribution_entity_id,
                            claim.attribution_text,
                            claim.temporal_start,
                            claim.temporal_end,
                            int(claim.sensitive),
                            int(claim.quantitative),
                            "restricted" if material.restricted else "active",
                            created_at,
                        ),
                    )
                    revision_by_local[claim.local_key] = revision_id
                    self._insert_claim_children(
                        con,
                        request,
                        descriptor,
                        material,
                        claim,
                        revision_id,
                        target_cache,
                        created_at,
                    )

                for relation in result.relations:
                    self._insert_relation(
                        con,
                        request,
                        descriptor,
                        material,
                        relation,
                        revision_by_local,
                        target_cache,
                        created_at,
                    )

            self._validate_committed_run(con, request.process_run_id)
            con.commit()
            receipt = self._receipt(con, request.process_run_id, replayed=False)
            return receipt
        except sqlite3.IntegrityError as exc:
            if con.in_transaction:
                con.rollback()
            raise LectorWriteError(f"SQLite rejected Lector write: {exc}") from exc
        except Exception:
            if con.in_transaction:
                con.rollback()
            raise
        finally:
            con.close()

    def _insert_process_run(
        self,
        con: sqlite3.Connection,
        request: SemanticExtractionRequest,
        descriptor: SemanticExtractorDescriptor,
        result: SemanticResult,
        started_at: str,
        finished_at: str,
        created_at: str,
    ) -> None:
        con.execute(
            """
            INSERT INTO process_runs(
              id,process_kind,implementation,implementation_version,execution_venue,
              configuration_hash,model_provider,model_name,started_at,finished_at,
              outcome,error_code,created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                request.process_run_id,
                self._process_kind(request.capability_key),
                descriptor.key,
                descriptor.implementation_version,
                descriptor.execution_venue,
                request.configuration_hash,
                descriptor.model_provider,
                descriptor.model_name,
                started_at,
                finished_at,
                result.outcome,
                result.error_code,
                created_at,
            ),
        )

    def _insert_claim_children(
        self,
        con: sqlite3.Connection,
        request: SemanticExtractionRequest,
        descriptor: SemanticExtractorDescriptor,
        material: SemanticInputMaterial,
        claim: ClaimDraft,
        revision_id: str,
        target_cache: dict[TargetRef, str],
        created_at: str,
    ) -> None:
        evidence_identities: set[tuple[str, str]] = set()
        for evidence in claim.evidence:
            target_id = self._resolve_target(
                con, evidence.target, material, target_cache, created_at
            )
            identity = (target_id, evidence.relation)
            if identity in evidence_identities:
                raise LectorInvariantError(
                    "claim evidence collapses to duplicate canonical target/relation"
                )
            evidence_identities.add(identity)
            con.execute(
                """
                INSERT INTO evidence_links(
                  id,supersedes_evidence_link_id,claim_revision_id,representation_target_id,
                  relation,origin_kind,process_run_id,lifecycle,rationale,created_at
                ) VALUES (?,NULL,?,?,?,?,?,?,?,?)
                """,
                (
                    new_id("evl_"),
                    revision_id,
                    target_id,
                    evidence.relation,
                    descriptor.origin_kind,
                    request.process_run_id,
                    evidence.lifecycle,
                    evidence.rationale,
                    created_at,
                ),
            )

        mention_identities: set[tuple[str, str]] = set()
        for mention in claim.mentions:
            target_id = self._resolve_target(
                con, mention.target, material, target_cache, created_at
            )
            identity = (mention.observed_text, target_id)
            if identity in mention_identities:
                raise LectorInvariantError(
                    "EntityMention drafts collapse to duplicate canonical occurrence"
                )
            mention_identities.add(identity)
            mention_id = new_id("emn_")
            con.execute(
                """
                INSERT INTO entity_mentions(
                  id,representation_target_id,claim_revision_id,observed_text,
                  origin_kind,process_run_id,created_at
                ) VALUES (?,?,?,?,?,?,?)
                """,
                (
                    mention_id,
                    target_id,
                    revision_id,
                    mention.observed_text,
                    descriptor.origin_kind,
                    request.process_run_id,
                    created_at,
                ),
            )
            for candidate in mention.resolution_candidates:
                self._require_entity(con, candidate.entity_id)
                con.execute(
                    """
                    INSERT INTO mention_resolution_candidates(
                      id,mention_id,entity_id,score,origin_kind,process_run_id,created_at
                    ) VALUES (?,?,?,?,?,?,?)
                    """,
                    (
                        new_id("mrc_"),
                        mention_id,
                        candidate.entity_id,
                        candidate.score,
                        descriptor.origin_kind,
                        request.process_run_id,
                        created_at,
                    ),
                )

        for tag in claim.tags:
            self._require_tag(con, tag.tag_id)
            con.execute(
                """
                INSERT INTO claim_tag_links(
                  id,supersedes_claim_tag_link_id,claim_revision_id,tag_id,origin_kind,
                  process_run_id,lifecycle,rationale,created_at
                ) VALUES (?,NULL,?,?,?,?,?,?,?)
                """,
                (
                    new_id("cltag_"),
                    revision_id,
                    tag.tag_id,
                    descriptor.origin_kind,
                    request.process_run_id,
                    tag.lifecycle,
                    tag.rationale,
                    created_at,
                ),
            )

        for anchor in claim.entity_anchors:
            self._require_entity(con, anchor.entity_id)
            con.execute(
                """
                INSERT INTO claim_entity_links(
                  id,supersedes_claim_entity_link_id,claim_revision_id,entity_id,
                  mention_id,mention_resolution_revision_id,role,origin_kind,process_run_id,
                  lifecycle,rationale,created_at
                ) VALUES (?,NULL,?,?,NULL,NULL,?,?,?,?,?,?)
                """,
                (
                    new_id("clent_"),
                    revision_id,
                    anchor.entity_id,
                    anchor.role,
                    descriptor.origin_kind,
                    request.process_run_id,
                    anchor.lifecycle,
                    anchor.rationale,
                    created_at,
                ),
            )

    def _insert_relation(
        self,
        con: sqlite3.Connection,
        request: SemanticExtractionRequest,
        descriptor: SemanticExtractorDescriptor,
        material: SemanticInputMaterial,
        relation: ClaimRelationDraft,
        revision_by_local: dict[str, str],
        target_cache: dict[TargetRef, str],
        created_at: str,
    ) -> None:
        from_id = revision_by_local[relation.from_claim.local_claim_key]
        to_id = revision_by_local[relation.to_claim.local_claim_key]
        if relation.relation_type in SYMMETRIC_RELATION_TYPES and to_id < from_id:
            from_id, to_id = to_id, from_id
        relation_id = new_id("clrel_")
        revision_id = new_id("clrr_")
        con.execute(
            "INSERT INTO claim_relations(id,created_at) VALUES (?,?)",
            (relation_id, created_at),
        )
        con.execute(
            """
            INSERT INTO claim_relation_revisions(
              id,claim_relation_id,revision_no,supersedes_relation_revision_id,
              from_claim_revision_id,to_claim_revision_id,relation_type,origin_kind,
              basis_kind,rationale,process_run_id,lifecycle,created_at
            ) VALUES (?,?,1,NULL,?,?,?,?,?,?,?,?,?)
            """,
            (
                revision_id,
                relation_id,
                from_id,
                to_id,
                relation.relation_type,
                descriptor.origin_kind,
                relation.basis_kind,
                relation.rationale,
                request.process_run_id,
                relation.lifecycle,
                created_at,
            ),
        )
        basis_identities: set[tuple[str, str]] = set()
        for basis in relation.basis:
            target_id = self._resolve_target(
                con, basis.target, material, target_cache, created_at
            )
            identity = (target_id, basis.basis_role)
            if identity in basis_identities:
                raise LectorInvariantError(
                    "ClaimRelation basis collapses to duplicate canonical target/role"
                )
            basis_identities.add(identity)
            con.execute(
                """
                INSERT INTO claim_relation_evidence_links(
                  id,claim_relation_revision_id,representation_target_id,basis_role,created_at
                ) VALUES (?,?,?,?,?)
                """,
                (new_id("crb_"), revision_id, target_id, basis.basis_role, created_at),
            )

    def _resolve_target(
        self,
        con: sqlite3.Connection,
        ref: TargetRef,
        material: SemanticInputMaterial,
        cache: dict[TargetRef, str],
        created_at: str,
    ) -> str:
        cached = cache.get(ref)
        if cached is not None:
            return cached
        scope_ids = {scope.id for scope in material.scopes}
        scope_triples = {
            (scope.selector_kind, scope.selector_version, scope.selector_payload_json)
            for scope in material.scopes
        }
        whole_authority = any(
            scope.selector_kind == "whole"
            and scope.selector_version == "v1"
            and scope.selector_payload_json == "{}"
            for scope in material.scopes
        )

        if ref.target_id is not None:
            row = con.execute(
                """
                SELECT representation_id,selector_kind,selector_version,
                       selector_payload_json,availability
                FROM representation_targets WHERE id=?
                """,
                (ref.target_id,),
            ).fetchone()
            if row is None or row[0] != material.representation_id or row[4] != "available":
                raise LectorInvariantError("semantic evidence target is unavailable or foreign")
            canonical = self.target_registry.validate(row[1], row[2], row[3])
            triple = (row[1], row[2], canonical)
            if ref.target_id not in scope_ids and not whole_authority and triple not in scope_triples:
                raise LectorInvariantError("semantic evidence target expands ProcessRun input scope")
            cache[ref] = ref.target_id
            return ref.target_id

        assert ref.selector_kind is not None
        assert ref.selector_version is not None
        assert ref.selector_payload_json is not None
        canonical = self.target_registry.validate(
            ref.selector_kind, ref.selector_version, ref.selector_payload_json
        )
        triple = (ref.selector_kind, ref.selector_version, canonical)
        if not whole_authority and triple not in scope_triples:
            raise LectorInvariantError("proposed semantic locator expands ProcessRun input scope")
        reopen_selector(
            ref.selector_kind,
            ref.selector_version,
            canonical,
            source_bytes=material.source_bytes,
            charset=material.charset,
        )
        row = con.execute(
            """
            SELECT id FROM representation_targets
            WHERE representation_id=? AND selector_kind=? AND selector_version=?
              AND selector_payload_json=? AND availability='available'
            ORDER BY created_at,id LIMIT 1
            """,
            (
                material.representation_id,
                ref.selector_kind,
                ref.selector_version,
                canonical,
            ),
        ).fetchone()
        if row is not None:
            cache[ref] = row[0]
            return row[0]
        target_id = new_id("rtgt_")
        con.execute(
            """
            INSERT INTO representation_targets(
              id,representation_id,selector_kind,selector_version,selector_payload_json,
              state_payload_json,availability,created_at,purged_at
            ) VALUES (?,?,?,?,?,NULL,'available',?,NULL)
            """,
            (
                target_id,
                material.representation_id,
                ref.selector_kind,
                ref.selector_version,
                canonical,
                created_at,
            ),
        )
        cache[ref] = target_id
        return target_id

    def _validate_attempt(
        self,
        request: SemanticExtractionRequest,
        descriptor: SemanticExtractorDescriptor,
        material: SemanticInputMaterial,
        result: SemanticResult,
    ) -> None:
        if request.capability_key != descriptor.capability_key:
            raise LectorInvariantError("request capability does not match extractor descriptor")
        if material.representation_kind not in descriptor.input_representation_kinds:
            raise LectorInvariantError("extractor does not support input Representation kind")
        if material.media_type not in descriptor.input_media_types:
            raise LectorInvariantError("extractor does not support input media type")
        scope_kinds = {scope.selector_kind for scope in material.scopes}
        if not scope_kinds.issubset(descriptor.scope_kinds):
            raise LectorInvariantError("extractor does not support requested scope kind")
        if descriptor.max_input_bytes is not None and len(material.source_bytes) > descriptor.max_input_bytes:
            raise LectorInvariantError("semantic input exceeds declared byte limit")
        if descriptor.max_scopes is not None and len(material.scopes) > descriptor.max_scopes:
            raise LectorInvariantError("semantic input exceeds declared scope limit")

        evidence_links = sum(len(claim.evidence) for claim in result.claims)
        mentions = sum(len(claim.mentions) for claim in result.claims)
        candidates = sum(
            len(mention.resolution_candidates)
            for claim in result.claims
            for mention in claim.mentions
        )
        tags = sum(len(claim.tags) for claim in result.claims)
        anchors = sum(len(claim.entity_anchors) for claim in result.claims)
        basis_targets = sum(len(relation.basis) for relation in result.relations)
        limits = (
            (len(result.claims), descriptor.max_claims, "claim"),
            (evidence_links, descriptor.max_evidence_links, "evidence link"),
            (mentions, descriptor.max_mentions, "mention"),
            (candidates, descriptor.max_resolution_candidates, "resolution candidate"),
            (tags, descriptor.max_tag_assignments, "tag assignment"),
            (anchors, descriptor.max_entity_anchors, "entity anchor"),
            (len(result.relations), descriptor.max_relations, "claim relation"),
            (basis_targets, descriptor.max_relation_basis_targets, "relation basis target"),
        )
        for observed, maximum, label in limits:
            if observed > maximum:
                raise LectorInvariantError(
                    f"semantic result exceeds declared {label} limit"
                )

        if descriptor.origin_kind in {"machine", "rule"}:
            if any(claim.attribution_entity_id is not None for claim in result.claims):
                raise LectorInvariantError(
                    "machine/rule extraction cannot directly resolve attribution Entity"
                )
            if any(
                anchor.lifecycle == "active"
                for claim in result.claims
                for anchor in claim.entity_anchors
            ):
                raise LectorInvariantError(
                    "machine/rule direct Entity anchors must remain candidate"
                )
        if descriptor.origin_kind == "machine" and any(
            relation.lifecycle == "active" for relation in result.relations
        ):
            raise LectorInvariantError("machine ClaimRelations must remain candidate")
        if descriptor.origin_kind == "rule" and any(
            relation.lifecycle == "active"
            and relation.basis_kind not in {"source_evidence", "mechanical_identity"}
            for relation in result.relations
        ):
            raise LectorInvariantError(
                "active rule ClaimRelation requires source_evidence or mechanical_identity basis"
            )

        if descriptor.requires_egress:
            if material.restricted:
                raise LectorInvariantError("restricted semantic input cannot egress")
            if not request.egress.allowed:
                raise LectorInvariantError("extractor requires explicit egress authorization")
            if result.egress_bytes is None:
                raise LectorInvariantError("egress extractor must report actual bytes egressed")
        elif result.egress_bytes is not None:
            raise LectorInvariantError("non-egress extractor cannot report egress bytes")

    def _revalidate_material(
        self,
        con: sqlite3.Connection,
        request: SemanticExtractionRequest,
        material: SemanticInputMaterial,
    ) -> None:
        row = con.execute(
            """
            SELECT r.artifact_id,r.availability,a.availability
            FROM representations r JOIN artifacts a ON a.id=r.artifact_id
            WHERE r.id=?
            """,
            (request.representation_id,),
        ).fetchone()
        if row is None or row[0] != material.artifact_id:
            raise LectorInvariantError("semantic input Representation custody changed before commit")
        if row[1] == "purged" or row[2] == "purged":
            raise LectorInvariantError("semantic input custody was purged before commit")
        for scope in material.scopes:
            target = con.execute(
                "SELECT representation_id,availability FROM representation_targets WHERE id=?",
                (scope.id,),
            ).fetchone()
            if target != (material.representation_id, "available"):
                raise LectorInvariantError("ProcessRun target changed before semantic commit")

    def _verify_existing_run(
        self,
        con: sqlite3.Connection,
        request: SemanticExtractionRequest,
        descriptor: SemanticExtractorDescriptor | None,
    ) -> SemanticReceipt | None:
        row = con.execute(
            """
            SELECT process_kind,implementation,implementation_version,execution_venue,
                   configuration_hash,model_provider,model_name,outcome,error_code
            FROM process_runs WHERE id=?
            """,
            (request.process_run_id,),
        ).fetchone()
        if row is None:
            return None
        if row[0] != self._process_kind(request.capability_key) or row[4] != request.configuration_hash:
            raise LectorIdentityCollision(
                f"ProcessRun {request.process_run_id} exists with different immutable capability/configuration"
            )
        if descriptor is not None:
            expected_prefix = (
                self._process_kind(descriptor.capability_key),
                descriptor.key,
                descriptor.implementation_version,
                descriptor.execution_venue,
                request.configuration_hash,
                descriptor.model_provider,
                descriptor.model_name,
            )
            if row[:7] != expected_prefix:
                raise LectorIdentityCollision(
                    f"ProcessRun {request.process_run_id} exists with different immutable descriptor/configuration"
                )
        inputs = con.execute(
            """
            SELECT representation_id,representation_target_id
            FROM process_run_inputs WHERE process_run_id=? ORDER BY ordinal
            """,
            (request.process_run_id,),
        ).fetchall()
        expected_inputs = [(request.representation_id, target_id) for target_id in request.target_ids]
        if inputs != expected_inputs:
            raise LectorIdentityCollision(
                f"ProcessRun {request.process_run_id} exists with different exact input scope"
            )
        egress = con.execute(
            """
            SELECT policy_profile,data_control_profile,request_template_hash,endpoint_profile
            FROM process_run_egress WHERE process_run_id=?
            """,
            (request.process_run_id,),
        ).fetchone()
        if egress is not None:
            expected_egress = (
                request.egress.policy_profile,
                request.egress.data_control_profile,
                request.egress.request_template_hash,
                request.egress.endpoint_profile,
            )
            if egress != expected_egress:
                raise LectorIdentityCollision(
                    f"ProcessRun {request.process_run_id} replay changed egress policy identity"
                )
            if descriptor is not None and not descriptor.requires_egress:
                raise LectorIdentityCollision(
                    "non-egress extractor unexpectedly collided with egress ProcessRun"
                )
        elif descriptor is not None and descriptor.requires_egress:
            raise LectorIdentityCollision("egress ProcessRun is missing egress provenance")

        self._validate_committed_run(con, request.process_run_id)
        return self._receipt(con, request.process_run_id, replayed=True)

    def _receipt(
        self, con: sqlite3.Connection, process_run_id: str, *, replayed: bool
    ) -> SemanticReceipt:
        outcome_row = con.execute(
            "SELECT outcome FROM process_runs WHERE id=?", (process_run_id,)
        ).fetchone()
        assert outcome_row is not None
        claims = tuple(
            PersistedClaim(*row)
            for row in con.execute(
                """
                SELECT claim_id,id FROM claim_revisions
                WHERE process_run_id=? ORDER BY id
                """,
                (process_run_id,),
            ).fetchall()
        )
        relations = tuple(
            PersistedClaimRelation(*row)
            for row in con.execute(
                """
                SELECT claim_relation_id,id FROM claim_relation_revisions
                WHERE process_run_id=? ORDER BY id
                """,
                (process_run_id,),
            ).fetchall()
        )
        def ids(sql: str) -> tuple[str, ...]:
            return tuple(row[0] for row in con.execute(sql, (process_run_id,)).fetchall())

        return SemanticReceipt(
            process_run_id,
            outcome_row[0],
            claims,
            ids("SELECT id FROM evidence_links WHERE process_run_id=? ORDER BY id"),
            ids("SELECT id FROM entity_mentions WHERE process_run_id=? ORDER BY id"),
            ids("SELECT id FROM mention_resolution_candidates WHERE process_run_id=? ORDER BY id"),
            ids("SELECT id FROM claim_tag_links WHERE process_run_id=? ORDER BY id"),
            ids("SELECT id FROM claim_entity_links WHERE process_run_id=? ORDER BY id"),
            relations,
            ids(
                """
                SELECT b.id FROM claim_relation_evidence_links b
                JOIN claim_relation_revisions r ON r.id=b.claim_relation_revision_id
                WHERE r.process_run_id=? ORDER BY b.id
                """
            ),
            replayed,
        )

    def _validate_committed_run(self, con: sqlite3.Connection, process_run_id: str) -> None:
        run = con.execute(
            "SELECT outcome FROM process_runs WHERE id=?", (process_run_id,)
        ).fetchone()
        if run is None:
            raise LectorInvariantError("semantic ProcessRun disappeared before validation")
        input_count = con.execute(
            "SELECT count(*) FROM process_run_inputs WHERE process_run_id=?",
            (process_run_id,),
        ).fetchone()[0]
        if input_count == 0:
            raise LectorInvariantError("semantic ProcessRun must retain exact input scope")

        families = {
            "claim revision": "claim_revisions",
            "evidence link": "evidence_links",
            "entity mention": "entity_mentions",
            "resolution candidate": "mention_resolution_candidates",
            "tag link": "claim_tag_links",
            "entity link": "claim_entity_links",
            "claim relation revision": "claim_relation_revisions",
        }
        family_counts = {
            label: con.execute(
                f"SELECT count(*) FROM {table} WHERE process_run_id=?", (process_run_id,)
            ).fetchone()[0]
            for label, table in families.items()
        }
        if run[0] == "failed" and any(family_counts.values()):
            raise LectorInvariantError("failed semantic ProcessRun cannot retain semantic outputs")

        bad_claim_children = 0
        for table in ("evidence_links", "entity_mentions", "claim_tag_links", "claim_entity_links"):
            bad_claim_children += con.execute(
                f"""
                SELECT count(*) FROM {table} child
                LEFT JOIN claim_revisions cr ON cr.id=child.claim_revision_id
                WHERE child.process_run_id=? AND (cr.id IS NULL OR cr.process_run_id<>?)
                """,
                (process_run_id, process_run_id),
            ).fetchone()[0]
        if bad_claim_children:
            raise LectorInvariantError("semantic child row is detached from this ProcessRun's Claim")

        bad_candidates = con.execute(
            """
            SELECT count(*) FROM mention_resolution_candidates c
            LEFT JOIN entity_mentions m ON m.id=c.mention_id
            WHERE c.process_run_id=? AND (m.id IS NULL OR m.process_run_id<>?)
            """,
            (process_run_id, process_run_id),
        ).fetchone()[0]
        if bad_candidates:
            raise LectorInvariantError("resolution candidate is detached from this ProcessRun's mention")

        bad_relations = con.execute(
            """
            SELECT count(*) FROM claim_relation_revisions r
            LEFT JOIN claim_revisions f ON f.id=r.from_claim_revision_id
            LEFT JOIN claim_revisions t ON t.id=r.to_claim_revision_id
            WHERE r.process_run_id=?
              AND (f.id IS NULL OR t.id IS NULL OR f.process_run_id<>? OR t.process_run_id<>?)
            """,
            (process_run_id, process_run_id, process_run_id),
        ).fetchone()[0]
        if bad_relations:
            raise LectorInvariantError("ClaimRelation endpoints escape this claim_extract ProcessRun")

    @staticmethod
    def _require_entity(con: sqlite3.Connection, entity_id: str) -> None:
        if con.execute("SELECT 1 FROM entities WHERE id=?", (entity_id,)).fetchone() is None:
            raise LectorInvariantError(f"unknown Entity: {entity_id}")

    @staticmethod
    def _require_tag(con: sqlite3.Connection, tag_id: str) -> None:
        if con.execute("SELECT 1 FROM tags WHERE id=?", (tag_id,)).fetchone() is None:
            raise LectorInvariantError(f"unknown Tag: {tag_id}")

    @staticmethod
    def _process_kind(capability_key: str) -> str:
        return f"lector.{capability_key}"
