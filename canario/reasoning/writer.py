"""Canonical persistence and cross-row validation for Derivation/Verification."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from canario.deposit.archive import ArchiveIntegrityError, EvidenceArchive, StoredObject
from canario.deposit.ids import new_id, validate_timestamp
from canario.persistence import open_writable_v1
from canario.processors.contracts import TargetSnapshot
from canario.processors.targets import TargetRegistry

from .containment import contains
from .contracts import (
    AssessmentRequest,
    ConsumedDerivationSnapshot,
    DerivationDescriptor,
    DerivationExecutionResult,
    DerivationInputSnapshot,
    DerivationInvocation,
    DerivationRequest,
    DerivedClaimRequest,
    VerificationDescriptor,
    VerificationDerivationSnapshot,
    VerificationExecutionResult,
    VerificationInvocation,
    VerificationRequest,
    VerificationScopeSnapshot,
    SourceAuthoritySnapshot,
    NO_INLINE_PAYLOAD,
)
from .registries import (
    ResultTargetRegistry,
    SourceMaterializerRegistry,
    VerificationProfileRegistry,
)

ConnectionFactory = Callable[[Path], sqlite3.Connection]


class ReasoningWriteError(RuntimeError):
    """A bounded analytical/verification write could not be committed honestly."""


class ReasoningInvariantError(ReasoningWriteError):
    """A cross-row reasoning invariant was violated."""


class ReasoningIdentityCollision(ReasoningWriteError):
    """A stable reasoning identity is occupied by different immutable data."""


@dataclass(frozen=True, slots=True)
class DerivationTargetReceipt:
    id: str
    selector_kind: str
    selector_version: str
    selector_payload_json: str
    lineage_state: str


@dataclass(frozen=True, slots=True)
class DerivationReceipt:
    derivation_run_id: str
    outcome: str
    result_id: str | None
    content_sha256: str | None
    byte_size: int | None
    targets: tuple[DerivationTargetReceipt, ...]
    replayed: bool


@dataclass(frozen=True, slots=True)
class VerificationReceipt:
    verification_run_id: str
    outcome: str
    verdict: str | None
    sufficiency_state: str | None
    evidence_target_ids: tuple[str, ...]
    replayed: bool


@dataclass(frozen=True, slots=True)
class DerivedClaimReceipt:
    claim_id: str
    revision_id: str
    evidence_link_ids: tuple[str, ...]
    replayed: bool


@dataclass(frozen=True, slots=True)
class AssessmentReceipt:
    assessment_id: str
    claim_revision_id: str
    judgment: str
    replayed: bool


class ReasoningWriter:
    """Sole canonical writer for the frozen Derivation/Verification execution graph."""

    def __init__(
        self,
        database_path: str | Path,
        archive_root: str | Path,
        *,
        target_registry: TargetRegistry | None = None,
        result_target_registry: ResultTargetRegistry | None = None,
        verification_profiles: VerificationProfileRegistry | None = None,
        source_materializers: SourceMaterializerRegistry | None = None,
        connection_factory: ConnectionFactory = open_writable_v1,
    ) -> None:
        self.database_path = Path(database_path)
        self.archive = EvidenceArchive(archive_root)
        self.target_registry = target_registry or TargetRegistry()
        self.result_target_registry = result_target_registry or ResultTargetRegistry()
        self.verification_profiles = verification_profiles or VerificationProfileRegistry()
        self.source_materializers = source_materializers or SourceMaterializerRegistry()
        self._connect = connection_factory

    # ------------------------------------------------------------------
    # Derivation
    # ------------------------------------------------------------------

    def load_derivation_inputs(self, request: DerivationRequest) -> tuple[DerivationInputSnapshot, ...]:
        con = self._connect(self.database_path)
        try:
            return tuple(
                self._load_input_snapshot(con, target_id, ordinal)
                for ordinal, target_id in enumerate(request.input_target_ids)
            )
        finally:
            con.close()

    @staticmethod
    def derivation_invocation(
        request: DerivationRequest, material: tuple[DerivationInputSnapshot, ...]
    ) -> DerivationInvocation:
        return DerivationInvocation(request, material)

    def replay_derivation(
        self, request: DerivationRequest, descriptor: DerivationDescriptor | None = None
    ) -> DerivationReceipt | None:
        con = self._connect(self.database_path)
        try:
            return self._verify_existing_derivation(con, request, descriptor)
        finally:
            con.close()

    def validate_derivation_before_invocation(
        self,
        request: DerivationRequest,
        descriptor: DerivationDescriptor,
        material: tuple[DerivationInputSnapshot, ...],
    ) -> None:
        if request.operation_kind not in descriptor.operation_kinds:
            raise ReasoningInvariantError("derivation backend does not support operation_kind")
        if request.program_kind not in descriptor.program_kinds:
            raise ReasoningInvariantError("derivation backend does not support program_kind")
        if descriptor.max_inputs is not None and len(material) > descriptor.max_inputs:
            raise ReasoningInvariantError("derivation input count exceeds backend limit")
        total_bytes = sum(len(item.material_bytes) for item in material)
        if descriptor.max_input_bytes is not None and total_bytes > descriptor.max_input_bytes:
            raise ReasoningInvariantError("derivation input bytes exceed backend limit")
        if descriptor.requires_egress:
            if any(item.restricted for item in material):
                raise ReasoningInvariantError("restricted Derivation input cannot egress")
            if not request.egress.allowed:
                raise ReasoningInvariantError("derivation backend requires explicit egress authorization")

    def record_derivation_attempt(
        self,
        *,
        request: DerivationRequest,
        descriptor: DerivationDescriptor,
        material: tuple[DerivationInputSnapshot, ...],
        result: DerivationExecutionResult,
        started_at: str,
        finished_at: str,
    ) -> DerivationReceipt:
        validate_timestamp(started_at)
        validate_timestamp(finished_at)
        if started_at > finished_at:
            raise ReasoningInvariantError("DerivationRun started_at cannot exceed finished_at")
        self.validate_derivation_before_invocation(request, descriptor, material)
        self._validate_derivation_result(descriptor, material, result)

        program_sha = hashlib.sha256(request.program_text.encode("utf-8")).hexdigest()
        inline_payload_json: str | None = None
        result_bytes: bytes | None = None
        stored: StoredObject | None = None
        archive_object_id: str | None = None
        candidate_archive_id: str | None = None
        result_id: str | None = None
        target_rows: list[tuple[str, str, str, str, str, tuple]] = []

        if result.output is not None:
            result_id = new_id("dres_")
            if result.output.inline_payload is not NO_INLINE_PAYLOAD:
                inline_payload_json = self._canonical_json_value(result.output.inline_payload)
                result_bytes = inline_payload_json.encode("utf-8")
            else:
                assert result.output.archive_bytes is not None
                result_bytes = result.output.archive_bytes
            if descriptor.max_result_bytes is not None and len(result_bytes) > descriptor.max_result_bytes:
                raise ReasoningInvariantError("derivation result exceeds backend declared byte limit")
            for target in result.output.targets:
                canonical_selector = self.result_target_registry.validate(
                    target.selector_kind, target.selector_version, target.selector_payload_json
                )
                target_rows.append(
                    (
                        new_id("drtgt_"),
                        target.selector_kind,
                        target.selector_version,
                        canonical_selector,
                        target.lineage_state,
                        target.lineage,
                    )
                )
            canonical_target_ids = [(row[1], row[2], row[3]) for row in target_rows]
            if len(canonical_target_ids) != len(set(canonical_target_ids)):
                raise ReasoningInvariantError("DerivationOutput repeats a canonical result selector")

        con = self._connect(self.database_path)
        committed = False
        try:
            replay = self._verify_existing_derivation(con, request, descriptor)
            if replay is not None:
                return replay

            if result_bytes is not None and inline_payload_json is None:
                digest = self.archive.digest(result_bytes)
                row = con.execute(
                    "SELECT id,byte_size,storage_key FROM archive_objects "
                    "WHERE content_sha256=? AND availability='available'",
                    (digest,),
                ).fetchone()
                if row is not None:
                    archive_object_id = row[0]
                    if row[1] != len(result_bytes):
                        raise ArchiveIntegrityError("ArchiveObject size disagrees with SHA-256 identity")
                    self.archive.verify(row[2], digest, row[1])
                else:
                    stored = self.archive.materialize(result_bytes)
                    candidate_archive_id = new_id("aob_")
                    archive_object_id = candidate_archive_id

            con.execute("BEGIN IMMEDIATE")
            concurrent = self._verify_existing_derivation(con, request, descriptor)
            if concurrent is not None:
                con.rollback()
                return concurrent
            self._revalidate_derivation_inputs(con, request, material)

            if result_bytes is not None and inline_payload_json is None:
                digest = self.archive.digest(result_bytes)
                row = con.execute(
                    "SELECT id,byte_size,storage_key FROM archive_objects "
                    "WHERE content_sha256=? AND availability='available'",
                    (digest,),
                ).fetchone()
                if row is not None:
                    archive_object_id = row[0]
                    if row[1] != len(result_bytes):
                        raise ArchiveIntegrityError("ArchiveObject size disagrees with SHA-256 identity")
                    self.archive.verify(row[2], digest, row[1])
                else:
                    assert stored is not None and candidate_archive_id is not None
                    archive_object_id = candidate_archive_id
                    con.execute(
                        """
                        INSERT INTO archive_objects(
                          id,content_sha256,byte_size,storage_key,availability,created_at,purged_at
                        ) VALUES (?,?,?,?, 'available', ?, NULL)
                        """,
                        (
                            archive_object_id,
                            stored.content_sha256,
                            stored.byte_size,
                            stored.storage_key,
                            finished_at,
                        ),
                    )

            con.execute(
                """
                INSERT INTO derivation_runs(
                  id,operation_kind,implementation_key,implementation_version,execution_venue,
                  configuration_hash,model_provider,model_name,executor_key,executor_version,
                  executor_source_id,sandbox_profile_key,sandbox_profile_version,program_kind,
                  program_text,program_sha256,started_at,finished_at,outcome,error_code,created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    request.derivation_run_id,
                    request.operation_kind,
                    descriptor.key,
                    descriptor.implementation_version,
                    descriptor.execution_venue,
                    request.configuration_hash,
                    descriptor.model_provider,
                    descriptor.model_name,
                    descriptor.executor_key,
                    descriptor.executor_version,
                    descriptor.executor_source_id,
                    descriptor.sandbox_profile_key,
                    descriptor.sandbox_profile_version,
                    request.program_kind,
                    request.program_text,
                    program_sha,
                    started_at,
                    finished_at,
                    result.outcome,
                    result.error_code,
                    finished_at,
                ),
            )
            for item in material:
                con.execute(
                    "INSERT INTO derivation_run_inputs VALUES (?,?,?,?)",
                    (
                        request.derivation_run_id,
                        item.ordinal,
                        item.target.representation_id,
                        item.target.id,
                    ),
                )
            if descriptor.requires_egress:
                assert result.egress_bytes is not None
                con.execute(
                    """
                    INSERT INTO derivation_run_egress(
                      derivation_run_id,bytes_egressed,policy_profile,data_control_profile,
                      request_template_hash,endpoint_profile,created_at
                    ) VALUES (?,?,?,?,?,?,?)
                    """,
                    (
                        request.derivation_run_id,
                        result.egress_bytes,
                        request.egress.policy_profile,
                        request.egress.data_control_profile,
                        request.egress.request_template_hash,
                        request.egress.endpoint_profile,
                        finished_at,
                    ),
                )

            if result.output is not None:
                assert result_id is not None and result_bytes is not None
                digest = hashlib.sha256(result_bytes).hexdigest()
                con.execute(
                    """
                    INSERT INTO derivation_results(
                      id,derivation_run_id,derivation_run_outcome,result_kind,schema_key,
                      schema_version,inline_payload_json,archive_object_id,content_sha256,
                      byte_size,availability,created_at,purged_at
                    ) VALUES (?,?,'success',?,?,?,?,?,?,?,'available',?,NULL)
                    """,
                    (
                        result_id,
                        request.derivation_run_id,
                        result.output.result_kind,
                        result.output.schema_key,
                        result.output.schema_version,
                        inline_payload_json,
                        archive_object_id,
                        digest,
                        len(result_bytes),
                        finished_at,
                    ),
                )
                for target_id, kind, version, payload, lineage_state, lineage in target_rows:
                    con.execute(
                        """
                        INSERT INTO derivation_result_targets(
                          id,derivation_result_id,derivation_run_id,selector_kind,selector_version,
                          selector_payload_json,lineage_state,availability,created_at,purged_at
                        ) VALUES (?,?,?,?,?,?,?,'available',?,NULL)
                        """,
                        (
                            target_id,
                            result_id,
                            request.derivation_run_id,
                            kind,
                            version,
                            payload,
                            lineage_state,
                            finished_at,
                        ),
                    )
                    for source in lineage:
                        source_snapshot = self._load_target_snapshot(con, source.representation_target_id)
                        input_item = self._material_by_ordinal(material, source.input_ordinal)
                        if source_snapshot.representation_id != input_item.target.representation_id or not contains(
                            input_item.target, source_snapshot, registry=self.target_registry
                        ):
                            raise ReasoningInvariantError(
                                "DerivationResult lineage lies outside the declared input scope"
                            )
                        con.execute(
                            """
                            INSERT INTO derivation_result_lineage(
                              derivation_result_target_id,derivation_run_id,lineage_state,input_ordinal,
                              representation_id,representation_target_id,created_at
                            ) VALUES (?,?,?,?,?,?,?)
                            """,
                            (
                                target_id,
                                request.derivation_run_id,
                                lineage_state,
                                source.input_ordinal,
                                source_snapshot.representation_id,
                                source_snapshot.id,
                                finished_at,
                            ),
                        )

            self._validate_committed_derivation(con, request.derivation_run_id)
            con.commit()
            committed = True
            return self._derivation_receipt(con, request.derivation_run_id, replayed=False)
        except sqlite3.IntegrityError as exc:
            if con.in_transaction:
                con.rollback()
            raise ReasoningWriteError(f"SQLite rejected Derivation write: {exc}") from exc
        except Exception:
            if con.in_transaction:
                con.rollback()
            raise
        finally:
            if not committed and stored is not None and stored.created:
                self._cleanup_unreferenced_stored(con, stored)
            con.close()

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------

    def load_verification_invocation(self, request: VerificationRequest) -> VerificationInvocation:
        canonical_scope = self.verification_profiles.validate_scope(
            request.scope_profile_key, request.scope_profile_version, request.scope_payload_json
        )
        if canonical_scope != request.scope_payload_json:
            # Canonical bytes are part of replay identity; callers should use canonical profile JSON.
            raise ReasoningInvariantError("verification scope payload must already be canonical JSON")

        con = self._connect(self.database_path)
        try:
            if request.claim_revision_id is not None:
                claim = con.execute(
                    "SELECT text FROM claim_revisions WHERE id=?",
                    (request.claim_revision_id,),
                ).fetchone()
                if claim is None:
                    raise ReasoningInvariantError("Verification references unknown ClaimRevision")
                if claim[0] != request.proposition_text:
                    raise ReasoningInvariantError(
                        "Verification proposition must equal the exact bound ClaimRevision text"
                    )

            scopes = tuple(
                self._load_scope_snapshot(con, target_id, ordinal)
                for ordinal, target_id in enumerate(request.scope_target_ids)
            )
            authority_scopes = self._load_authority_scopes(con, request, scopes)
            derivations: list[VerificationDerivationSnapshot] = []
            for ordinal, step in enumerate(request.derivation_steps):
                run = con.execute(
                    "SELECT implementation_key,implementation_version,configuration_hash,"
                    "executor_key,executor_version,executor_source_id,sandbox_profile_key,"
                    "sandbox_profile_version,operation_kind,program_kind,program_sha256,outcome,error_code "
                    "FROM derivation_runs WHERE id=?",
                    (step.derivation_run_id,),
                ).fetchone()
                if run is None:
                    raise ReasoningInvariantError("Verification references unknown DerivationRun")
                self._validate_derivation_inside_scope(con, step.derivation_run_id, scopes)
                consumed_result = None
                if step.use_state == "consumed":
                    if run[11] != "success":
                        raise ReasoningInvariantError("Verification cannot consume a failed DerivationRun")
                    assert step.derivation_result_target_id is not None
                    consumed_result = self._load_consumed_derivation(
                        con, ordinal, step.derivation_run_id, step.derivation_result_target_id
                    )
                derivations.append(
                    VerificationDerivationSnapshot(
                        ordinal,
                        step.derivation_run_id,
                        step.use_state,
                        run[0],
                        run[1],
                        run[2],
                        run[3],
                        run[4],
                        run[5],
                        run[6],
                        run[7],
                        run[8],
                        run[9],
                        run[10],
                        run[11],
                        run[12],
                        consumed_result,
                    )
                )
            return VerificationInvocation(request, scopes, authority_scopes, tuple(derivations))
        finally:
            con.close()

    def replay_verification(
        self, request: VerificationRequest, descriptor: VerificationDescriptor | None = None
    ) -> VerificationReceipt | None:
        con = self._connect(self.database_path)
        try:
            return self._verify_existing_verification(con, request, descriptor)
        finally:
            con.close()

    def validate_verification_before_invocation(
        self, request: VerificationRequest, descriptor: VerificationDescriptor, invocation: VerificationInvocation
    ) -> None:
        if descriptor.max_scopes is not None and len(invocation.scopes) > descriptor.max_scopes:
            raise ReasoningInvariantError("verification scope count exceeds backend limit")
        total_bytes = sum(len(scope.material_bytes) for scope in invocation.scopes)
        if descriptor.max_scope_bytes is not None and total_bytes > descriptor.max_scope_bytes:
            raise ReasoningInvariantError("verification scope bytes exceed backend limit")
        if descriptor.requires_egress:
            if any(scope.restricted for scope in invocation.scopes):
                raise ReasoningInvariantError("restricted Verification scope cannot egress")
            if not request.egress.allowed:
                raise ReasoningInvariantError("verification backend requires explicit egress authorization")

    def record_verification_attempt(
        self,
        *,
        request: VerificationRequest,
        descriptor: VerificationDescriptor,
        invocation: VerificationInvocation,
        result: VerificationExecutionResult,
        started_at: str,
        finished_at: str,
    ) -> VerificationReceipt:
        validate_timestamp(started_at)
        validate_timestamp(finished_at)
        if started_at > finished_at:
            raise ReasoningInvariantError("VerificationRun started_at cannot exceed finished_at")
        self.validate_verification_before_invocation(request, descriptor, invocation)
        if descriptor.requires_egress:
            if result.egress_bytes is None:
                raise ReasoningInvariantError("egress verifier must report actual bytes egressed")
        elif result.egress_bytes is not None:
            raise ReasoningInvariantError("non-egress verifier cannot report egress bytes")

        sufficiency_payload: str | None = None
        if result.outcome == "completed":
            assert result.sufficiency_profile_key is not None
            assert result.sufficiency_profile_version is not None
            assert result.sufficiency_payload_json is not None
            sufficiency_payload = self.verification_profiles.validate_sufficiency(
                result.sufficiency_profile_key,
                result.sufficiency_profile_version,
                result.sufficiency_payload_json,
            )
            if sufficiency_payload != result.sufficiency_payload_json:
                raise ReasoningInvariantError(
                    "verification sufficiency payload must already be canonical JSON"
                )

        con = self._connect(self.database_path)
        try:
            replay = self._verify_existing_verification(con, request, descriptor)
            if replay is not None:
                return replay
            con.execute("BEGIN IMMEDIATE")
            concurrent = self._verify_existing_verification(con, request, descriptor)
            if concurrent is not None:
                con.rollback()
                return concurrent

            fresh = self._revalidate_verification_invocation(con, request, invocation)
            evidence_rows: list[tuple[int, int, str, str, str]] = []
            for ordinal, evidence in enumerate(result.evidence):
                if evidence.scope_ordinal >= len(fresh.scopes):
                    raise ReasoningInvariantError("verification evidence names an unknown scope ordinal")
                scope = fresh.scopes[evidence.scope_ordinal]
                target = self._load_target_snapshot(con, evidence.representation_target_id)
                if target.representation_id != scope.target.representation_id or not contains(
                    scope.target, target, registry=self.target_registry
                ):
                    raise ReasoningInvariantError("verification evidence lies outside declared scope")
                evidence_rows.append(
                    (
                        ordinal,
                        evidence.scope_ordinal,
                        target.representation_id,
                        target.id,
                        evidence.role,
                    )
                )

            con.execute(
                """
                INSERT INTO verification_runs(
                  id,claim_revision_id,proposition_text,implementation_key,implementation_version,
                  execution_venue,configuration_hash,model_provider,model_name,scope_profile_key,
                  scope_profile_version,scope_payload_json,started_at,finished_at,outcome,error_code,
                  verdict,sufficiency_state,sufficiency_profile_key,sufficiency_profile_version,
                  sufficiency_payload_json,abstention_reason_code,created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    request.verification_run_id,
                    request.claim_revision_id,
                    request.proposition_text,
                    descriptor.key,
                    descriptor.implementation_version,
                    descriptor.execution_venue,
                    request.configuration_hash,
                    descriptor.model_provider,
                    descriptor.model_name,
                    request.scope_profile_key,
                    request.scope_profile_version,
                    request.scope_payload_json,
                    started_at,
                    finished_at,
                    result.outcome,
                    result.error_code,
                    result.verdict,
                    result.sufficiency_state,
                    result.sufficiency_profile_key,
                    result.sufficiency_profile_version,
                    sufficiency_payload,
                    result.abstention_reason_code,
                    finished_at,
                ),
            )
            for scope in fresh.scopes:
                con.execute(
                    "INSERT INTO verification_scope_targets VALUES (?,?,?,?)",
                    (
                        request.verification_run_id,
                        scope.ordinal,
                        scope.target.representation_id,
                        scope.target.id,
                    ),
                )
            for ordinal, scope_id in enumerate(request.authority_scope_ids):
                con.execute(
                    "INSERT INTO verification_authority_scopes VALUES (?,?,?)",
                    (request.verification_run_id, ordinal, scope_id),
                )
            for ordinal, step in enumerate(request.derivation_steps):
                con.execute(
                    "INSERT INTO verification_derivation_steps VALUES (?,?,?,?,?)",
                    (
                        request.verification_run_id,
                        ordinal,
                        step.derivation_run_id,
                        step.use_state,
                        step.derivation_result_target_id,
                    ),
                )
            for row in evidence_rows:
                con.execute(
                    "INSERT INTO verification_evidence_items VALUES (?,?,?,?,?,?)",
                    (request.verification_run_id, *row),
                )
            if descriptor.requires_egress:
                assert result.egress_bytes is not None
                con.execute(
                    """
                    INSERT INTO verification_run_egress(
                      verification_run_id,bytes_egressed,policy_profile,data_control_profile,
                      request_template_hash,endpoint_profile,created_at
                    ) VALUES (?,?,?,?,?,?,?)
                    """,
                    (
                        request.verification_run_id,
                        result.egress_bytes,
                        request.egress.policy_profile,
                        request.egress.data_control_profile,
                        request.egress.request_template_hash,
                        request.egress.endpoint_profile,
                        finished_at,
                    ),
                )
            self._validate_committed_verification(con, request.verification_run_id)
            con.commit()
            return self._verification_receipt(con, request.verification_run_id, replayed=False)
        except sqlite3.IntegrityError as exc:
            if con.in_transaction:
                con.rollback()
            raise ReasoningWriteError(f"SQLite rejected Verification write: {exc}") from exc
        except Exception:
            if con.in_transaction:
                con.rollback()
            raise
        finally:
            con.close()

    # ------------------------------------------------------------------
    # Explicit Claim promotion and Assessment
    # ------------------------------------------------------------------

    def promote_derived_claim(self, request: DerivedClaimRequest, *, created_at: str) -> DerivedClaimReceipt:
        validate_timestamp(created_at)
        con = self._connect(self.database_path)
        try:
            replay = self._verify_existing_derived_claim(con, request, created_at)
            if replay is not None:
                return replay
            con.execute("BEGIN IMMEDIATE")
            replay = self._verify_existing_derived_claim(con, request, created_at)
            if replay is not None:
                con.rollback()
                return replay

            origin = con.execute(
                """
                SELECT t.derivation_run_id,t.lineage_state,t.availability,r.availability
                FROM derivation_result_targets t
                JOIN derivation_results r ON r.id=t.derivation_result_id
                WHERE t.id=?
                """,
                (request.derivation_result_target_id,),
            ).fetchone()
            if origin is None or origin[2:] != ("available", "available"):
                raise ReasoningInvariantError("derived Claim origin is unavailable")
            derivation_run_id, lineage_state, _, _ = origin
            if request.process_run_id is not None:
                self._require_row(con, "process_runs", request.process_run_id, "ProcessRun")
            if request.attribution_entity_id is not None:
                self._require_row(con, "entities", request.attribution_entity_id, "Entity")

            lineage_targets = tuple(
                self._load_target_snapshot(con, row[0])
                for row in con.execute(
                    "SELECT representation_target_id FROM derivation_result_lineage "
                    "WHERE derivation_result_target_id=? ORDER BY representation_target_id",
                    (request.derivation_result_target_id,),
                )
            )
            if lineage_state in {"exact", "partial"} and not lineage_targets:
                raise ReasoningInvariantError("derived Claim origin is missing required lineage")
            if self._derivation_has_restricted_input(con, derivation_run_id) and request.lifecycle != "restricted":
                raise ReasoningInvariantError("derived Claim from restricted input must remain restricted")

            evidence_rows: list[tuple] = []
            for evidence in request.evidence:
                target = self._load_target_snapshot(con, evidence.representation_target_id)
                if evidence.process_run_id is not None:
                    self._require_row(con, "process_runs", evidence.process_run_id, "ProcessRun")
                if evidence.relation == "supports" and evidence.lifecycle == "active":
                    if not lineage_targets or not any(
                        contains(target, lineage, registry=self.target_registry)
                        for lineage in lineage_targets
                    ):
                        raise ReasoningInvariantError(
                            "active derived supports EvidenceLink must contain real source-contribution lineage"
                        )
                if self._target_is_restricted(con, target.id) and request.lifecycle != "restricted":
                    raise ReasoningInvariantError("Claim with restricted evidence must remain restricted")
                evidence_rows.append(
                    (
                        evidence.evidence_link_id,
                        request.claim_revision_id,
                        target.id,
                        evidence.relation,
                        evidence.origin_kind,
                        evidence.process_run_id,
                        evidence.lifecycle,
                        evidence.rationale,
                        created_at,
                    )
                )

            con.execute("INSERT INTO claims(id,created_at) VALUES (?,?)", (request.claim_id, created_at))
            con.execute(
                """
                INSERT INTO claim_revisions(
                  id,claim_id,revision_no,supersedes_revision_id,claim_kind,text,origin_kind,
                  process_run_id,derivation_result_target_id,attribution_entity_id,attribution_text,
                  temporal_start,temporal_end,sensitive,quantitative,lifecycle,created_at
                ) VALUES (?,?,1,NULL,'derived_inference',?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    request.claim_revision_id,
                    request.claim_id,
                    request.text,
                    request.origin_kind,
                    request.process_run_id,
                    request.derivation_result_target_id,
                    request.attribution_entity_id,
                    request.attribution_text,
                    request.temporal_start,
                    request.temporal_end,
                    int(request.sensitive),
                    int(request.quantitative),
                    request.lifecycle,
                    created_at,
                ),
            )
            for row in evidence_rows:
                con.execute(
                    """
                    INSERT INTO evidence_links(
                      id,supersedes_evidence_link_id,claim_revision_id,representation_target_id,
                      relation,origin_kind,process_run_id,lifecycle,rationale,created_at
                    ) VALUES (?,NULL,?,?,?,?,?,?,?,?)
                    """,
                    row,
                )
            con.commit()
            return DerivedClaimReceipt(
                request.claim_id,
                request.claim_revision_id,
                tuple(item.evidence_link_id for item in request.evidence),
                False,
            )
        except sqlite3.IntegrityError as exc:
            if con.in_transaction:
                con.rollback()
            raise ReasoningWriteError(f"SQLite rejected derived Claim promotion: {exc}") from exc
        except Exception:
            if con.in_transaction:
                con.rollback()
            raise
        finally:
            con.close()

    def record_assessment(self, request: AssessmentRequest, *, created_at: str) -> AssessmentReceipt:
        validate_timestamp(created_at)
        con = self._connect(self.database_path)
        try:
            replay = self._verify_existing_assessment(con, request, created_at)
            if replay is not None:
                return replay
            con.execute("BEGIN IMMEDIATE")
            replay = self._verify_existing_assessment(con, request, created_at)
            if replay is not None:
                con.rollback()
                return replay
            self._require_row(con, "claim_revisions", request.claim_revision_id, "ClaimRevision")
            if request.verification_run_id is not None:
                verification = con.execute(
                    "SELECT claim_revision_id,outcome FROM verification_runs WHERE id=?",
                    (request.verification_run_id,),
                ).fetchone()
                if verification is None or verification[0] != request.claim_revision_id:
                    raise ReasoningInvariantError("Assessment VerificationRun must bind the same ClaimRevision")
                if verification[1] != "completed":
                    raise ReasoningInvariantError("Assessment cannot use a failed VerificationRun")
            if request.supersedes_assessment_id is not None:
                previous = con.execute(
                    "SELECT claim_revision_id,assessor_key,policy_key FROM assessments WHERE id=?",
                    (request.supersedes_assessment_id,),
                ).fetchone()
                if previous is None:
                    raise ReasoningInvariantError("Assessment supersedes unknown predecessor")
                if previous[0] != request.claim_revision_id or previous[1] != request.assessor_key:
                    raise ReasoningInvariantError("Assessment successor must keep ClaimRevision and assessor")
                if (previous[2] is not None or request.policy_key is not None) and previous[2] != request.policy_key:
                    raise ReasoningInvariantError("Assessment successor cannot jump policy lineage")
            con.execute(
                """
                INSERT INTO assessments(
                  id,supersedes_assessment_id,claim_revision_id,judgment,origin_kind,assessor_key,
                  verification_run_id,policy_key,policy_version,rationale,created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    request.assessment_id,
                    request.supersedes_assessment_id,
                    request.claim_revision_id,
                    request.judgment,
                    request.origin_kind,
                    request.assessor_key,
                    request.verification_run_id,
                    request.policy_key,
                    request.policy_version,
                    request.rationale,
                    created_at,
                ),
            )
            con.commit()
            return AssessmentReceipt(
                request.assessment_id, request.claim_revision_id, request.judgment, False
            )
        except sqlite3.IntegrityError as exc:
            if con.in_transaction:
                con.rollback()
            raise ReasoningWriteError(f"SQLite rejected Assessment write: {exc}") from exc
        except Exception:
            if con.in_transaction:
                con.rollback()
            raise
        finally:
            con.close()

    # ------------------------------------------------------------------
    # Load/revalidate helpers
    # ------------------------------------------------------------------

    def _load_input_snapshot(
        self, con: sqlite3.Connection, target_id: str, ordinal: int
    ) -> DerivationInputSnapshot:
        row = self._target_material_row(con, target_id)
        if row is None:
            raise ReasoningInvariantError(f"unknown retained RepresentationTarget: {target_id}")
        (
            representation_id,
            selector_kind,
            selector_version,
            selector_payload_json,
            target_availability,
            representation_kind,
            rep_media_type,
            language,
            charset,
            rep_availability,
            artifact_media_type,
            artifact_availability,
            archive_object_id,
            _source_id,
        ) = row
        if target_availability != "available" or rep_availability == "purged" or artifact_availability == "purged":
            raise ReasoningInvariantError("Derivation input custody is unavailable")
        canonical = self.target_registry.validate(selector_kind, selector_version, selector_payload_json)
        if canonical != selector_payload_json:
            raise ReasoningInvariantError("stored RepresentationTarget selector is not canonical")
        archive = self._archive_bytes(con, archive_object_id)
        target = TargetSnapshot(target_id, representation_id, selector_kind, selector_version, canonical)
        material_bytes = self.source_materializers.materialize(target, archive, charset)
        media_type = rep_media_type or artifact_media_type
        if media_type is None:
            raise ReasoningInvariantError("Derivation input requires known media type")
        return DerivationInputSnapshot(
            ordinal,
            target,
            representation_kind,
            media_type,
            language,
            charset,
            material_bytes,
            rep_availability == "restricted" or artifact_availability == "restricted",
        )

    def _load_scope_snapshot(
        self, con: sqlite3.Connection, target_id: str, ordinal: int
    ) -> VerificationScopeSnapshot:
        row = self._target_material_row(con, target_id)
        if row is None:
            raise ReasoningInvariantError(f"unknown Verification scope target: {target_id}")
        (
            representation_id,
            selector_kind,
            selector_version,
            selector_payload_json,
            target_availability,
            representation_kind,
            rep_media_type,
            language,
            charset,
            rep_availability,
            artifact_media_type,
            artifact_availability,
            archive_object_id,
            source_id,
        ) = row
        if target_availability != "available" or rep_availability == "purged" or artifact_availability == "purged":
            raise ReasoningInvariantError("Verification scope custody is unavailable")
        canonical = self.target_registry.validate(selector_kind, selector_version, selector_payload_json)
        if canonical != selector_payload_json:
            raise ReasoningInvariantError("stored Verification selector is not canonical")
        archive = self._archive_bytes(con, archive_object_id)
        target = TargetSnapshot(target_id, representation_id, selector_kind, selector_version, canonical)
        material_bytes = self.source_materializers.materialize(target, archive, charset)
        media_type = rep_media_type or artifact_media_type
        if media_type is None:
            raise ReasoningInvariantError("Verification scope requires known media type")
        return VerificationScopeSnapshot(
            ordinal,
            target,
            representation_kind,
            media_type,
            language,
            charset,
            source_id,
            material_bytes,
            rep_availability == "restricted" or artifact_availability == "restricted",
        )

    @staticmethod
    def _target_material_row(con: sqlite3.Connection, target_id: str):
        return con.execute(
            """
            SELECT t.representation_id,t.selector_kind,t.selector_version,t.selector_payload_json,
                   t.availability,r.kind,r.media_type,r.language,r.charset,r.availability,
                   a.media_type,a.availability,
                   CASE WHEN r.kind='original' THEN a.archive_object_id ELSE r.archive_object_id END,
                   acq.source_id
            FROM representation_targets t
            JOIN representations r ON r.id=t.representation_id
            JOIN artifacts a ON a.id=r.artifact_id
            JOIN acquisition_artifacts aa ON aa.artifact_id=a.id
            JOIN acquisitions acq ON acq.id=aa.acquisition_id
            WHERE t.id=?
            """,
            (target_id,),
        ).fetchone()

    def _archive_bytes(self, con: sqlite3.Connection, archive_object_id: str | None) -> bytes:
        if archive_object_id is None:
            raise ReasoningInvariantError("retained analytical input has no ArchiveObject")
        row = con.execute(
            "SELECT content_sha256,byte_size,storage_key,availability FROM archive_objects WHERE id=?",
            (archive_object_id,),
        ).fetchone()
        if row is None or row[3] != "available":
            raise ReasoningInvariantError("analytical input ArchiveObject is unavailable")
        self.archive.verify(row[2], row[0], row[1])
        return self.archive.path_for_key(row[2]).read_bytes()

    def _load_target_snapshot(self, con: sqlite3.Connection, target_id: str) -> TargetSnapshot:
        row = con.execute(
            """
            SELECT representation_id,selector_kind,selector_version,selector_payload_json,availability
            FROM representation_targets WHERE id=?
            """,
            (target_id,),
        ).fetchone()
        if row is None or row[4] != "available":
            raise ReasoningInvariantError(f"RepresentationTarget is unavailable: {target_id}")
        canonical = self.target_registry.validate(row[1], row[2], row[3])
        if canonical != row[3]:
            raise ReasoningInvariantError("stored RepresentationTarget selector is not canonical")
        return TargetSnapshot(target_id, row[0], row[1], row[2], canonical)

    def _revalidate_derivation_inputs(
        self,
        con: sqlite3.Connection,
        request: DerivationRequest,
        material: tuple[DerivationInputSnapshot, ...],
    ) -> None:
        for ordinal, target_id in enumerate(request.input_target_ids):
            fresh = self._load_input_snapshot(con, target_id, ordinal)
            expected = self._material_by_ordinal(material, ordinal)
            if fresh.target != expected.target or fresh.material_bytes != expected.material_bytes or fresh.restricted != expected.restricted:
                raise ReasoningInvariantError("Derivation input changed before commit")

    def _revalidate_verification_invocation(
        self, con: sqlite3.Connection, request: VerificationRequest, invocation: VerificationInvocation
    ) -> VerificationInvocation:
        if request.claim_revision_id is not None:
            row = con.execute("SELECT text FROM claim_revisions WHERE id=?", (request.claim_revision_id,)).fetchone()
            if row != (request.proposition_text,):
                raise ReasoningInvariantError("Verification ClaimRevision changed before commit")
        scopes = tuple(
            self._load_scope_snapshot(con, target_id, ordinal)
            for ordinal, target_id in enumerate(request.scope_target_ids)
        )
        authority_scopes = self._load_authority_scopes(con, request, scopes)
        derivations: list[VerificationDerivationSnapshot] = []
        for ordinal, step in enumerate(request.derivation_steps):
            run = con.execute(
                "SELECT implementation_key,implementation_version,configuration_hash,"
                "executor_key,executor_version,executor_source_id,sandbox_profile_key,"
                "sandbox_profile_version,operation_kind,program_kind,program_sha256,outcome,error_code "
                "FROM derivation_runs WHERE id=?",
                (step.derivation_run_id,),
            ).fetchone()
            if run is None:
                raise ReasoningInvariantError("Verification Derivation disappeared before commit")
            self._validate_derivation_inside_scope(con, step.derivation_run_id, scopes)
            consumed_result = None
            if step.use_state == "consumed":
                if run[11] != "success":
                    raise ReasoningInvariantError("Verification consumed Derivation is no longer successful")
                assert step.derivation_result_target_id is not None
                consumed_result = self._load_consumed_derivation(
                    con, ordinal, step.derivation_run_id, step.derivation_result_target_id
                )
            derivations.append(
                VerificationDerivationSnapshot(
                    ordinal,
                    step.derivation_run_id,
                    step.use_state,
                    run[0],
                    run[1],
                    run[2],
                    run[3],
                    run[4],
                    run[5],
                    run[6],
                    run[7],
                    run[8],
                    run[9],
                    run[10],
                    run[11],
                    run[12],
                    consumed_result,
                )
            )
        fresh = VerificationInvocation(request, scopes, authority_scopes, tuple(derivations))
        if self._verification_material_identity(fresh) != self._verification_material_identity(invocation):
            raise ReasoningInvariantError("Verification input material changed before commit")
        return fresh

    def _load_authority_scopes(
        self,
        con: sqlite3.Connection,
        request: VerificationRequest,
        scopes: tuple[VerificationScopeSnapshot, ...],
    ) -> tuple[SourceAuthoritySnapshot, ...]:
        snapshots: list[SourceAuthoritySnapshot] = []
        for scope_id in request.authority_scope_ids:
            row = con.execute(
                "SELECT source_id,scope_kind,valid_from,valid_to,note FROM source_authority_scopes WHERE id=?",
                (scope_id,),
            ).fetchone()
            if row is None:
                raise ReasoningInvariantError(f"unknown SourceAuthorityScope: {scope_id}")
            snapshots.append(SourceAuthoritySnapshot(scope_id, *row))
        scope_sources = {scope.source_id for scope in scopes}
        authority_sources = {item.source_id for item in snapshots}
        if authority_sources != scope_sources:
            raise ReasoningInvariantError(
                "Verification Source Authority must cover exactly the sources represented by its scope"
            )
        return tuple(snapshots)

    def _validate_derivation_inside_scope(
        self,
        con: sqlite3.Connection,
        derivation_run_id: str,
        scopes: tuple[VerificationScopeSnapshot, ...],
    ) -> None:
        inputs = con.execute(
            "SELECT representation_target_id FROM derivation_run_inputs WHERE derivation_run_id=? ORDER BY ordinal",
            (derivation_run_id,),
        ).fetchall()
        if not inputs:
            raise ReasoningInvariantError("Verification references DerivationRun without inputs")
        for (input_target_id,) in inputs:
            target = self._load_target_snapshot(con, input_target_id)
            if not any(
                scope.target.representation_id == target.representation_id
                and contains(scope.target, target, registry=self.target_registry)
                for scope in scopes
            ):
                raise ReasoningInvariantError("DerivationRun expands beyond Verification scope")

    def _load_consumed_derivation(
        self,
        con: sqlite3.Connection,
        ordinal: int,
        derivation_run_id: str,
        target_id: str,
    ) -> ConsumedDerivationSnapshot:
        row = con.execute(
            """
            SELECT t.selector_kind,t.selector_version,t.selector_payload_json,t.lineage_state,
                   t.availability,r.result_kind,r.schema_key,r.schema_version,r.inline_payload_json,
                   r.archive_object_id,r.availability
            FROM derivation_result_targets t
            JOIN derivation_results r ON r.id=t.derivation_result_id
            WHERE t.id=? AND t.derivation_run_id=?
            """,
            (target_id, derivation_run_id),
        ).fetchone()
        if row is None or row[4] != "available" or row[10] != "available":
            raise ReasoningInvariantError("consumed DerivationResultTarget is unavailable")
        selector = self.result_target_registry.validate(row[0], row[1], row[2])
        if selector != row[2]:
            raise ReasoningInvariantError("stored DerivationResultTarget selector is not canonical")
        if row[8] is not None:
            full_result_bytes = row[8].encode("utf-8")
        else:
            full_result_bytes = self._archive_bytes(con, row[9])
        material_bytes = self.result_target_registry.materialize(
            row[0], row[1], selector, full_result_bytes
        )
        lineage = tuple(
            source[0]
            for source in con.execute(
                "SELECT representation_target_id FROM derivation_result_lineage "
                "WHERE derivation_result_target_id=? ORDER BY representation_target_id",
                (target_id,),
            )
        )
        return ConsumedDerivationSnapshot(
            ordinal,
            derivation_run_id,
            target_id,
            row[5],
            row[6],
            row[7],
            material_bytes,
            row[0],
            row[1],
            selector,
            row[3],
            lineage,
        )

    # ------------------------------------------------------------------
    # Replay / receipts / validation
    # ------------------------------------------------------------------

    def _verify_existing_derivation(
        self,
        con: sqlite3.Connection,
        request: DerivationRequest,
        descriptor: DerivationDescriptor | None,
    ) -> DerivationReceipt | None:
        row = con.execute(
            """
            SELECT operation_kind,implementation_key,implementation_version,execution_venue,
                   configuration_hash,model_provider,model_name,executor_key,executor_version,
                   executor_source_id,sandbox_profile_key,sandbox_profile_version,program_kind,
                   program_text,program_sha256,outcome,error_code
            FROM derivation_runs WHERE id=?
            """,
            (request.derivation_run_id,),
        ).fetchone()
        if row is None:
            return None
        expected_program_sha = hashlib.sha256(request.program_text.encode("utf-8")).hexdigest()
        if row[0] != request.operation_kind or row[4] != request.configuration_hash or row[12] != request.program_kind or row[13] != request.program_text or row[14] != expected_program_sha:
            raise ReasoningIdentityCollision(
                f"DerivationRun {request.derivation_run_id} exists with different immutable request"
            )
        if descriptor is not None:
            expected = (
                request.operation_kind,
                descriptor.key,
                descriptor.implementation_version,
                descriptor.execution_venue,
                request.configuration_hash,
                descriptor.model_provider,
                descriptor.model_name,
                descriptor.executor_key,
                descriptor.executor_version,
                descriptor.executor_source_id,
                descriptor.sandbox_profile_key,
                descriptor.sandbox_profile_version,
                request.program_kind,
                request.program_text,
                expected_program_sha,
            )
            if row[:15] != expected:
                raise ReasoningIdentityCollision(
                    f"DerivationRun {request.derivation_run_id} exists with different descriptor"
                )
        inputs = tuple(
            item[0]
            for item in con.execute(
                "SELECT representation_target_id FROM derivation_run_inputs WHERE derivation_run_id=? ORDER BY ordinal",
                (request.derivation_run_id,),
            )
        )
        if inputs != request.input_target_ids:
            raise ReasoningIdentityCollision(
                f"DerivationRun {request.derivation_run_id} exists with different ordered inputs"
            )
        self._verify_egress_identity(
            con,
            "derivation_run_egress",
            "derivation_run_id",
            request.derivation_run_id,
            request.egress,
            descriptor.requires_egress if descriptor is not None else None,
        )
        return self._derivation_receipt(con, request.derivation_run_id, replayed=True)

    def _verify_existing_verification(
        self,
        con: sqlite3.Connection,
        request: VerificationRequest,
        descriptor: VerificationDescriptor | None,
    ) -> VerificationReceipt | None:
        row = con.execute(
            """
            SELECT claim_revision_id,proposition_text,implementation_key,implementation_version,
                   execution_venue,configuration_hash,model_provider,model_name,scope_profile_key,
                   scope_profile_version,scope_payload_json,outcome
            FROM verification_runs WHERE id=?
            """,
            (request.verification_run_id,),
        ).fetchone()
        if row is None:
            return None
        if row[0] != request.claim_revision_id or row[1] != request.proposition_text or row[5] != request.configuration_hash or row[8:11] != (
            request.scope_profile_key,
            request.scope_profile_version,
            request.scope_payload_json,
        ):
            raise ReasoningIdentityCollision(
                f"VerificationRun {request.verification_run_id} exists with different immutable request"
            )
        if descriptor is not None and row[2:8] != (
            descriptor.key,
            descriptor.implementation_version,
            descriptor.execution_venue,
            request.configuration_hash,
            descriptor.model_provider,
            descriptor.model_name,
        ):
            raise ReasoningIdentityCollision(
                f"VerificationRun {request.verification_run_id} exists with different descriptor"
            )
        scopes = tuple(
            item[0]
            for item in con.execute(
                "SELECT representation_target_id FROM verification_scope_targets WHERE verification_run_id=? ORDER BY ordinal",
                (request.verification_run_id,),
            )
        )
        authorities = tuple(
            item[0]
            for item in con.execute(
                "SELECT source_authority_scope_id FROM verification_authority_scopes WHERE verification_run_id=? ORDER BY ordinal",
                (request.verification_run_id,),
            )
        )
        steps = tuple(
            item
            for item in con.execute(
                "SELECT derivation_run_id,use_state,derivation_result_target_id FROM verification_derivation_steps WHERE verification_run_id=? ORDER BY ordinal",
                (request.verification_run_id,),
            )
        )
        expected_steps = tuple(
            (step.derivation_run_id, step.use_state, step.derivation_result_target_id)
            for step in request.derivation_steps
        )
        if scopes != request.scope_target_ids or authorities != request.authority_scope_ids or steps != expected_steps:
            raise ReasoningIdentityCollision(
                f"VerificationRun {request.verification_run_id} exists with different scope/derivation graph"
            )
        self._verify_egress_identity(
            con,
            "verification_run_egress",
            "verification_run_id",
            request.verification_run_id,
            request.egress,
            descriptor.requires_egress if descriptor is not None else None,
        )
        return self._verification_receipt(con, request.verification_run_id, replayed=True)

    def _verify_existing_derived_claim(
        self, con: sqlite3.Connection, request: DerivedClaimRequest, created_at: str
    ) -> DerivedClaimReceipt | None:
        row = con.execute(
            """
            SELECT claim_id,claim_kind,text,origin_kind,process_run_id,derivation_result_target_id,
                   attribution_entity_id,attribution_text,temporal_start,temporal_end,sensitive,
                   quantitative,lifecycle,created_at
            FROM claim_revisions WHERE id=?
            """,
            (request.claim_revision_id,),
        ).fetchone()
        if row is None:
            if con.execute("SELECT 1 FROM claims WHERE id=?", (request.claim_id,)).fetchone() is not None:
                raise ReasoningIdentityCollision("Claim identity exists without requested derived revision")
            return None
        expected = (
            request.claim_id,
            "derived_inference",
            request.text,
            request.origin_kind,
            request.process_run_id,
            request.derivation_result_target_id,
            request.attribution_entity_id,
            request.attribution_text,
            request.temporal_start,
            request.temporal_end,
            int(request.sensitive),
            int(request.quantitative),
            request.lifecycle,
        )
        if row[:13] != expected or row[13] != created_at:
            raise ReasoningIdentityCollision("derived Claim revision identity has different immutable payload")
        claim_created_at = con.execute(
            "SELECT created_at FROM claims WHERE id=?", (request.claim_id,)
        ).fetchone()
        if claim_created_at != (created_at,):
            raise ReasoningIdentityCollision("derived Claim identity has different creation timestamp")
        evidence = tuple(
            item
            for item in con.execute(
                """
                SELECT id,representation_target_id,relation,origin_kind,process_run_id,lifecycle,rationale,created_at
                FROM evidence_links WHERE claim_revision_id=? ORDER BY id
                """,
                (request.claim_revision_id,),
            )
        )
        expected_evidence = tuple(
            sorted(
                (
                    item.evidence_link_id,
                    item.representation_target_id,
                    item.relation,
                    item.origin_kind,
                    item.process_run_id,
                    item.lifecycle,
                    item.rationale,
                    created_at,
                )
                for item in request.evidence
            )
        )
        if evidence != expected_evidence:
            raise ReasoningIdentityCollision("derived Claim evidence differs on retry")
        return DerivedClaimReceipt(
            request.claim_id,
            request.claim_revision_id,
            tuple(item[0] for item in evidence),
            True,
        )

    def _verify_existing_assessment(
        self, con: sqlite3.Connection, request: AssessmentRequest, created_at: str
    ) -> AssessmentReceipt | None:
        row = con.execute(
            """
            SELECT supersedes_assessment_id,claim_revision_id,judgment,origin_kind,assessor_key,
                   verification_run_id,policy_key,policy_version,rationale,created_at
            FROM assessments WHERE id=?
            """,
            (request.assessment_id,),
        ).fetchone()
        if row is None:
            return None
        expected = (
            request.supersedes_assessment_id,
            request.claim_revision_id,
            request.judgment,
            request.origin_kind,
            request.assessor_key,
            request.verification_run_id,
            request.policy_key,
            request.policy_version,
            request.rationale,
            created_at,
        )
        if row != expected:
            raise ReasoningIdentityCollision("Assessment identity exists with different immutable payload")
        return AssessmentReceipt(request.assessment_id, request.claim_revision_id, request.judgment, True)

    @staticmethod
    def _verify_egress_identity(
        con: sqlite3.Connection,
        table: str,
        key_column: str,
        run_id: str,
        authorization,
        requires_egress: bool | None,
    ) -> None:
        row = con.execute(
            f"SELECT policy_profile,data_control_profile,request_template_hash,endpoint_profile FROM {table} WHERE {key_column}=?",
            (run_id,),
        ).fetchone()
        expected = (
            authorization.policy_profile,
            authorization.data_control_profile,
            authorization.request_template_hash,
            authorization.endpoint_profile,
        )
        if requires_egress is True:
            if row != expected:
                raise ReasoningIdentityCollision("reasoning run egress policy differs on replay")
        elif requires_egress is False:
            if row is not None:
                raise ReasoningIdentityCollision("non-egress reasoning run unexpectedly has egress provenance")
        elif row is not None and row != expected:
            # Descriptor-less replay is supported so historical backends can be removed, but a
            # persisted egress run must still match the request's immutable policy identity.
            raise ReasoningIdentityCollision("reasoning run egress policy differs on replay")

    def _derivation_receipt(
        self, con: sqlite3.Connection, run_id: str, *, replayed: bool
    ) -> DerivationReceipt:
        run = con.execute("SELECT outcome FROM derivation_runs WHERE id=?", (run_id,)).fetchone()
        assert run is not None
        result = con.execute(
            "SELECT id,content_sha256,byte_size FROM derivation_results WHERE derivation_run_id=?",
            (run_id,),
        ).fetchone()
        if result is None:
            return DerivationReceipt(run_id, run[0], None, None, None, (), replayed)
        targets = tuple(
            DerivationTargetReceipt(*row)
            for row in con.execute(
                """
                SELECT id,selector_kind,selector_version,selector_payload_json,lineage_state
                FROM derivation_result_targets WHERE derivation_result_id=?
                ORDER BY selector_kind,selector_version,selector_payload_json,id
                """,
                (result[0],),
            )
        )
        return DerivationReceipt(run_id, run[0], result[0], result[1], result[2], targets, replayed)

    @staticmethod
    def _verification_receipt(
        con: sqlite3.Connection, run_id: str, *, replayed: bool
    ) -> VerificationReceipt:
        row = con.execute(
            "SELECT outcome,verdict,sufficiency_state FROM verification_runs WHERE id=?",
            (run_id,),
        ).fetchone()
        assert row is not None
        evidence = tuple(
            item[0]
            for item in con.execute(
                "SELECT representation_target_id FROM verification_evidence_items WHERE verification_run_id=? ORDER BY ordinal",
                (run_id,),
            )
        )
        return VerificationReceipt(run_id, row[0], row[1], row[2], evidence, replayed)

    def _validate_derivation_result(
        self,
        descriptor: DerivationDescriptor,
        material: tuple[DerivationInputSnapshot, ...],
        result: DerivationExecutionResult,
    ) -> None:
        if descriptor.requires_egress:
            if result.egress_bytes is None:
                raise ReasoningInvariantError("egress Derivation must report actual bytes egressed")
        elif result.egress_bytes is not None:
            raise ReasoningInvariantError("non-egress Derivation cannot report egress bytes")
        if result.output is None:
            return
        for target in result.output.targets:
            self.result_target_registry.validate(
                target.selector_kind, target.selector_version, target.selector_payload_json
            )
            for source in target.lineage:
                input_item = self._material_by_ordinal(material, source.input_ordinal)
                # Exact source target is reloaded immediately before write; here only enforce ordinal bounds.
                if input_item.ordinal != source.input_ordinal:
                    raise ReasoningInvariantError("invalid source lineage ordinal")

    @staticmethod
    def _validate_committed_derivation(con: sqlite3.Connection, run_id: str) -> None:
        outcome = con.execute("SELECT outcome FROM derivation_runs WHERE id=?", (run_id,)).fetchone()[0]
        result_count = con.execute(
            "SELECT count(*) FROM derivation_results WHERE derivation_run_id=?", (run_id,)
        ).fetchone()[0]
        if result_count != (1 if outcome == "success" else 0):
            raise ReasoningInvariantError("DerivationRun/result cardinality is invalid")
        if outcome == "success":
            bad = con.execute(
                """
                SELECT t.id FROM derivation_result_targets t
                LEFT JOIN derivation_result_lineage l ON l.derivation_result_target_id=t.id
                JOIN derivation_results r ON r.id=t.derivation_result_id
                WHERE r.derivation_run_id=?
                GROUP BY t.id,t.lineage_state
                HAVING (t.lineage_state IN ('exact','partial') AND count(l.representation_target_id)=0)
                    OR (t.lineage_state IN ('unavailable','none') AND count(l.representation_target_id)<>0)
                """,
                (run_id,),
            ).fetchall()
            if bad:
                raise ReasoningInvariantError("DerivationResultTarget lineage state disagrees with rows")

    @staticmethod
    def _validate_committed_verification(con: sqlite3.Connection, run_id: str) -> None:
        scope_count = con.execute(
            "SELECT count(*) FROM verification_scope_targets WHERE verification_run_id=?", (run_id,)
        ).fetchone()[0]
        authority_count = con.execute(
            "SELECT count(*) FROM verification_authority_scopes WHERE verification_run_id=?", (run_id,)
        ).fetchone()[0]
        if scope_count == 0 or authority_count == 0:
            raise ReasoningInvariantError("VerificationRun must retain scope and Source Authority")

    @staticmethod
    def _material_by_ordinal(
        material: tuple[DerivationInputSnapshot, ...], ordinal: int
    ) -> DerivationInputSnapshot:
        if ordinal < 0 or ordinal >= len(material) or material[ordinal].ordinal != ordinal:
            raise ReasoningInvariantError("lineage references an unknown Derivation input ordinal")
        return material[ordinal]

    def _target_is_restricted(self, con: sqlite3.Connection, target_id: str) -> bool:
        row = con.execute(
            """
            SELECT r.availability,a.availability
            FROM representation_targets t
            JOIN representations r ON r.id=t.representation_id
            JOIN artifacts a ON a.id=r.artifact_id
            WHERE t.id=?
            """,
            (target_id,),
        ).fetchone()
        if row is None:
            raise ReasoningInvariantError("unknown evidence target")
        return "restricted" in row

    def _derivation_has_restricted_input(self, con: sqlite3.Connection, run_id: str) -> bool:
        row = con.execute(
            """
            SELECT 1
            FROM derivation_run_inputs i
            JOIN representations r ON r.id=i.representation_id
            JOIN artifacts a ON a.id=r.artifact_id
            WHERE i.derivation_run_id=? AND (r.availability='restricted' OR a.availability='restricted')
            LIMIT 1
            """,
            (run_id,),
        ).fetchone()
        return row is not None

    @staticmethod
    def _require_row(con: sqlite3.Connection, table: str, record_id: str, label: str) -> None:
        if con.execute(f"SELECT 1 FROM {table} WHERE id=?", (record_id,)).fetchone() is None:
            raise ReasoningInvariantError(f"unknown {label}: {record_id}")

    @staticmethod
    def _canonical_json_value(value) -> str:
        try:
            return json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            )
        except (TypeError, ValueError) as exc:
            raise ReasoningInvariantError("Derivation inline result is not canonical JSON data") from exc

    @staticmethod
    def _verification_material_identity(invocation: VerificationInvocation) -> tuple:
        return (
            tuple(
                (
                    scope.ordinal,
                    scope.target,
                    scope.source_id,
                    hashlib.sha256(scope.material_bytes).hexdigest(),
                    scope.restricted,
                )
                for scope in invocation.scopes
            ),
            tuple(
                (
                    item.id,
                    item.source_id,
                    item.scope_kind,
                    item.valid_from,
                    item.valid_to,
                    item.note,
                )
                for item in invocation.authority_scopes
            ),
            tuple(
                (
                    item.ordinal,
                    item.derivation_run_id,
                    item.use_state,
                    item.implementation_key,
                    item.implementation_version,
                    item.configuration_hash,
                    item.executor_key,
                    item.executor_version,
                    item.executor_source_id,
                    item.sandbox_profile_key,
                    item.sandbox_profile_version,
                    item.operation_kind,
                    item.program_kind,
                    item.program_sha256,
                    item.outcome,
                    item.error_code,
                    None
                    if item.consumed_result is None
                    else (
                        item.consumed_result.result_target_id,
                        hashlib.sha256(item.consumed_result.material_bytes).hexdigest(),
                        item.consumed_result.lineage_state,
                        item.consumed_result.source_target_ids,
                    ),
                )
                for item in invocation.derivations
            ),
        )

    def _cleanup_unreferenced_stored(self, con: sqlite3.Connection, stored: StoredObject) -> None:
        try:
            referenced = con.execute(
                "SELECT 1 FROM archive_objects WHERE content_sha256=? AND availability='available'",
                (stored.content_sha256,),
            ).fetchone()
            if referenced is None:
                self.archive.remove_if_matches(stored)
        except Exception:
            pass
