"""Canonical Workbench persistence for terminal attempts and derivative custody."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from actakit.deposit.archive import ArchiveIntegrityError, EvidenceArchive, StoredObject
from actakit.deposit.ids import new_id, validate_timestamp
from actakit.persistence import open_writable_v1

from .contracts import (
    EgressAuthorization,
    ProcessingRequest,
    ProcessorDescriptor,
    ProcessorInvocation,
    ProcessorResult,
    TargetSnapshot,
)
from .quality import QualityDecision, QualityRegistry
from .targets import TargetRegistration, TargetRegistry

ConnectionFactory = Callable[[Path], sqlite3.Connection]


class WorkbenchWriteError(RuntimeError):
    """A bounded Workbench write could not be committed honestly."""


class WorkbenchInvariantError(WorkbenchWriteError):
    """Canonical custody/scope/provenance requirements are not satisfied."""


class WorkbenchIdentityCollision(WorkbenchWriteError):
    """A stable Workbench identity is occupied by different immutable data."""


@dataclass(frozen=True, slots=True)
class DerivedRepresentationReceipt:
    representation_id: str
    archive_object_id: str
    content_sha256: str
    byte_size: int
    storage_key: str


@dataclass(frozen=True, slots=True)
class PersistedDecision:
    id: str
    target_id: str
    decision: str
    policy_key: str
    policy_version: str
    reason_code: str
    next_capability_key: str | None


@dataclass(frozen=True, slots=True)
class AttemptReceipt:
    process_run_id: str
    outcome: str
    decisions: tuple[PersistedDecision, ...]
    outputs: tuple[DerivedRepresentationReceipt, ...]
    replayed: bool


@dataclass(frozen=True, slots=True)
class InputMaterial:
    representation_id: str
    artifact_id: str
    representation_kind: str
    media_type: str
    language: str | None
    charset: str | None
    artifact_restricted: bool
    source_bytes: bytes
    scopes: tuple[TargetSnapshot, ...]


class WorkbenchWriter:
    """Sole core writer for processor provenance, evidence and derivatives."""

    def __init__(
        self,
        database_path: str | Path,
        archive_root: str | Path,
        *,
        quality_registry: QualityRegistry | None = None,
        target_registry: TargetRegistry | None = None,
        connection_factory: ConnectionFactory = open_writable_v1,
    ) -> None:
        self.database_path = Path(database_path)
        self.archive = EvidenceArchive(archive_root)
        self.quality_registry = quality_registry or QualityRegistry()
        self.target_registry = target_registry or TargetRegistry()
        self._connect = connection_factory

    def register_target(self, target: TargetRegistration) -> str:
        canonical_payload = self.target_registry.validate(
            target.selector_kind, target.selector_version, target.selector_payload_json
        )
        con = self._connect(self.database_path)
        try:
            con.execute("BEGIN IMMEDIATE")
            rep = con.execute(
                "SELECT availability FROM representations WHERE id=?",
                (target.representation_id,),
            ).fetchone()
            if rep is None:
                raise WorkbenchInvariantError(
                    f"unknown Representation: {target.representation_id}"
                )
            if rep[0] == "purged":
                raise WorkbenchInvariantError("cannot target a purged Representation")

            row = con.execute(
                """
                SELECT representation_id,selector_kind,selector_version,selector_payload_json,
                       availability,created_at,purged_at
                FROM representation_targets WHERE id=?
                """,
                (target.id,),
            ).fetchone()
            expected = (
                target.representation_id,
                target.selector_kind,
                target.selector_version,
                canonical_payload,
                "available",
                target.created_at,
                None,
            )
            if row is None:
                con.execute(
                    """
                    INSERT INTO representation_targets(
                      id,representation_id,selector_kind,selector_version,selector_payload_json,
                      state_payload_json,availability,created_at,purged_at
                    ) VALUES (?,?,?,?,?,NULL,'available',?,NULL)
                    """,
                    (
                        target.id,
                        target.representation_id,
                        target.selector_kind,
                        target.selector_version,
                        canonical_payload,
                        target.created_at,
                    ),
                )
            elif row != expected:
                raise WorkbenchIdentityCollision(
                    f"RepresentationTarget {target.id} exists with different immutable payload"
                )
            con.commit()
            return target.id
        except Exception:
            if con.in_transaction:
                con.rollback()
            raise
        finally:
            con.close()

    def load_input(self, request: ProcessingRequest) -> InputMaterial:
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
                raise WorkbenchInvariantError(
                    f"unknown retained Representation: {request.representation_id}"
                )
            (
                artifact_id,
                kind,
                rep_media_type,
                language,
                charset,
                rep_availability,
                artifact_media_type,
                artifact_availability,
                archive_object_id,
            ) = row
            if rep_availability == "purged" or artifact_availability == "purged":
                raise WorkbenchInvariantError("purged custody cannot be processed")
            if archive_object_id is None:
                raise WorkbenchInvariantError("retained Representation has no byte authority")
            media_type = rep_media_type or artifact_media_type
            if media_type is None:
                raise WorkbenchInvariantError("processor input requires a known media type")

            archive_row = con.execute(
                """
                SELECT content_sha256,byte_size,storage_key,availability
                FROM archive_objects WHERE id=?
                """,
                (archive_object_id,),
            ).fetchone()
            if archive_row is None or archive_row[3] != "available":
                raise WorkbenchInvariantError("processor input ArchiveObject is unavailable")
            digest, size, storage_key, _ = archive_row
            self.archive.verify(storage_key, digest, size)
            source_bytes = self.archive.path_for_key(storage_key).read_bytes()

            scopes: list[TargetSnapshot] = []
            for target_id in request.target_ids:
                target = con.execute(
                    """
                    SELECT representation_id,selector_kind,selector_version,selector_payload_json,availability
                    FROM representation_targets WHERE id=?
                    """,
                    (target_id,),
                ).fetchone()
                if target is None:
                    raise WorkbenchInvariantError(f"unknown RepresentationTarget: {target_id}")
                target_rep, selector_kind, selector_version, payload_json, availability = target
                if target_rep != request.representation_id:
                    raise WorkbenchInvariantError(
                        "processing target does not belong to requested Representation"
                    )
                if availability != "available":
                    raise WorkbenchInvariantError("purged RepresentationTarget cannot be processed")
                self.target_registry.validate(selector_kind, selector_version, payload_json)
                scopes.append(
                    TargetSnapshot(
                        target_id,
                        target_rep,
                        selector_kind,
                        selector_version,
                        payload_json,
                    )
                )
            return InputMaterial(
                request.representation_id,
                artifact_id,
                kind,
                media_type,
                language,
                charset,
                artifact_availability == "restricted" or rep_availability == "restricted",
                source_bytes,
                tuple(scopes),
            )
        finally:
            con.close()

    def invocation(self, request: ProcessingRequest, material: InputMaterial) -> ProcessorInvocation:
        return ProcessorInvocation(
            request,
            material.representation_kind,
            material.media_type,
            material.language,
            material.charset,
            material.source_bytes,
            material.scopes,
        )

    def replay_if_present(
        self,
        request: ProcessingRequest,
    ) -> AttemptReceipt | None:
        con = self._connect(self.database_path)
        try:
            return self._verify_existing_run(con, request, None)
        finally:
            con.close()

    def record_attempt(
        self,
        *,
        request: ProcessingRequest,
        descriptor: ProcessorDescriptor,
        material: InputMaterial,
        result: ProcessorResult,
        decisions: tuple[QualityDecision, ...],
        started_at: str,
        finished_at: str,
    ) -> AttemptReceipt:
        validate_timestamp(started_at)
        validate_timestamp(finished_at)
        if started_at > finished_at:
            raise WorkbenchInvariantError("ProcessRun started_at cannot exceed finished_at")
        self._validate_attempt(request, descriptor, material, result, decisions)

        canonical_evidence = tuple(
            (signal, self.quality_registry.validate(signal)) for signal in result.evidence
        )
        decisions = tuple(decision.with_identity() for decision in decisions)
        created_at = finished_at

        con = self._connect(self.database_path)
        materialized: dict[str, StoredObject] = {}
        committed = False
        try:
            replay = self._verify_existing_run(con, request, descriptor)
            if replay is not None:
                return replay

            digest_by_output = [self.archive.digest(output.data) for output in result.outputs]
            archive_ids: dict[str, str] = {}
            candidate_ids: dict[str, str] = {}
            for digest, output in zip(digest_by_output, result.outputs, strict=True):
                if digest in archive_ids:
                    continue
                row = con.execute(
                    """
                    SELECT id,byte_size,storage_key FROM archive_objects
                    WHERE content_sha256=? AND availability='available'
                    """,
                    (digest,),
                ).fetchone()
                if row is not None:
                    object_id, stored_size, storage_key = row
                    if stored_size != len(output.data):
                        raise ArchiveIntegrityError(
                            f"ArchiveObject {object_id} size disagrees with SHA-256 identity"
                        )
                    self.archive.verify(storage_key, digest, stored_size)
                    archive_ids[digest] = object_id
                    continue
                candidate_id = new_id("aob_")
                stored = self.archive.materialize(output.data)
                materialized[digest] = stored
                candidate_ids[digest] = candidate_id
                archive_ids[digest] = candidate_id

            output_rep_ids = tuple(new_id("rep_") for _ in result.outputs)
            evidence_ids = tuple(new_id("qev_") for _ in canonical_evidence)

            con.execute("BEGIN IMMEDIATE")
            concurrent = self._verify_existing_run(con, request, descriptor)
            if concurrent is not None:
                con.rollback()
                return concurrent
            self._revalidate_material(con, request, material)

            for digest, output in zip(digest_by_output, result.outputs, strict=True):
                row = con.execute(
                    """
                    SELECT id,byte_size,storage_key FROM archive_objects
                    WHERE content_sha256=? AND availability='available'
                    """,
                    (digest,),
                ).fetchone()
                if row is not None:
                    object_id, stored_size, storage_key = row
                    if stored_size != len(output.data):
                        raise ArchiveIntegrityError(
                            f"ArchiveObject {object_id} size disagrees with SHA-256 identity"
                        )
                    self.archive.verify(storage_key, digest, stored_size)
                    archive_ids[digest] = object_id
                    continue
                stored = materialized[digest]
                object_id = candidate_ids[digest]
                con.execute(
                    """
                    INSERT INTO archive_objects(
                      id,content_sha256,byte_size,storage_key,availability,created_at,purged_at
                    ) VALUES (?,?,?,?, 'available', ?, NULL)
                    """,
                    (object_id, digest, stored.byte_size, stored.storage_key, created_at),
                )
                archive_ids[digest] = object_id

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
                    descriptor.capability_key,
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

            for ordinal, ((signal, payload_json), evidence_id) in enumerate(
                zip(canonical_evidence, evidence_ids, strict=True)
            ):
                con.execute(
                    """
                    INSERT INTO quality_evidence(
                      id,process_run_id,ordinal,representation_id,representation_target_id,
                      signal_key,signal_version,payload_json,interpretation_key,created_at
                    ) VALUES (?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        evidence_id,
                        request.process_run_id,
                        ordinal,
                        material.representation_id,
                        signal.target_id,
                        signal.signal_key,
                        signal.signal_version,
                        payload_json,
                        signal.interpretation_key,
                        created_at,
                    ),
                )

            output_receipts: list[DerivedRepresentationReceipt] = []
            for output, digest, rep_id in zip(
                result.outputs, digest_by_output, output_rep_ids, strict=True
            ):
                archive_object_id = archive_ids[digest]
                con.execute(
                    """
                    INSERT INTO representations(
                      id,artifact_id,archive_object_id,parent_representation_id,kind,
                      media_type,language,charset,process_run_id,availability,created_at,purged_at
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,NULL)
                    """,
                    (
                        rep_id,
                        material.artifact_id,
                        archive_object_id,
                        material.representation_id,
                        output.kind,
                        output.media_type,
                        output.language,
                        output.charset,
                        request.process_run_id,
                        "restricted" if material.artifact_restricted else "available",
                        created_at,
                    ),
                )
                archive_row = self._archive_row(con, archive_object_id)
                output_receipts.append(
                    DerivedRepresentationReceipt(
                        rep_id,
                        archive_object_id,
                        archive_row[0],
                        archive_row[1],
                        archive_row[2],
                    )
                )

            persisted_decisions: list[PersistedDecision] = []
            for decision in decisions:
                con.execute(
                    """
                    INSERT INTO quality_decisions(
                      id,process_run_id,representation_id,representation_target_id,decision,
                      policy_key,policy_version,reason_code,next_capability_key,created_at
                    ) VALUES (?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        decision.id,
                        request.process_run_id,
                        material.representation_id,
                        decision.target_id,
                        decision.decision,
                        decision.policy_key,
                        decision.policy_version,
                        decision.reason_code,
                        decision.next_capability_key,
                        created_at,
                    ),
                )
                persisted_decisions.append(
                    PersistedDecision(
                        decision.id,
                        decision.target_id,
                        decision.decision,
                        decision.policy_key,
                        decision.policy_version,
                        decision.reason_code,
                        decision.next_capability_key,
                    )
                )

            self._validate_committed_attempt(con, request.process_run_id)
            con.commit()
            committed = True
            return AttemptReceipt(
                request.process_run_id,
                result.outcome,
                tuple(persisted_decisions),
                tuple(output_receipts),
                False,
            )
        except sqlite3.IntegrityError as exc:
            if con.in_transaction:
                con.rollback()
            raise WorkbenchWriteError(f"SQLite rejected Workbench write: {exc}") from exc
        except Exception:
            if con.in_transaction:
                con.rollback()
            raise
        finally:
            if not committed:
                self._cleanup_unreferenced_materialized(con, materialized)
            con.close()

    def _validate_attempt(
        self,
        request: ProcessingRequest,
        descriptor: ProcessorDescriptor,
        material: InputMaterial,
        result: ProcessorResult,
        decisions: tuple[QualityDecision, ...],
    ) -> None:
        if request.capability_key != descriptor.capability_key:
            raise WorkbenchInvariantError("request capability does not match processor descriptor")
        if material.media_type not in descriptor.input_media_types:
            raise WorkbenchInvariantError("processor does not support input media type")
        scope_kinds = {scope.selector_kind for scope in material.scopes}
        if not scope_kinds.issubset(descriptor.scope_kinds):
            raise WorkbenchInvariantError("processor does not support requested scope kind")
        if descriptor.max_input_bytes is not None and len(material.source_bytes) > descriptor.max_input_bytes:
            raise WorkbenchInvariantError("processor input exceeds declared byte limit")
        if descriptor.max_scopes is not None and len(material.scopes) > descriptor.max_scopes:
            raise WorkbenchInvariantError("processor input exceeds declared scope limit")
        if any(output.kind not in descriptor.output_kinds for output in result.outputs):
            raise WorkbenchInvariantError("processor emitted an undeclared Representation kind")
        target_ids = {scope.id for scope in material.scopes}
        if any(signal.target_id not in target_ids for signal in result.evidence):
            raise WorkbenchInvariantError("QualityEvidence targets scope outside ProcessRun input")
        signal_identities = [
            (signal.target_id, signal.signal_key, signal.signal_version)
            for signal in result.evidence
        ]
        if len(set(signal_identities)) != len(signal_identities):
            raise WorkbenchInvariantError(
                "a ProcessRun target cannot emit duplicate QualityEvidence signal identities"
            )
        if descriptor.requires_egress:
            if material.artifact_restricted:
                raise WorkbenchInvariantError("restricted Artifact cannot egress")
            if not request.egress.allowed:
                raise WorkbenchInvariantError("processor requires explicit egress authorization")
            if result.egress_bytes is None:
                raise WorkbenchInvariantError("egress processor must report actual bytes egressed")
        elif result.egress_bytes is not None:
            raise WorkbenchInvariantError("non-egress processor cannot report egress bytes")
        if len(decisions) != len(material.scopes):
            raise WorkbenchInvariantError("every ProcessRun input target requires one quality decision")
        decision_targets = [decision.target_id for decision in decisions]
        if set(decision_targets) != target_ids or len(set(decision_targets)) != len(decision_targets):
            raise WorkbenchInvariantError("quality decisions must cover each input target exactly once")

    def _revalidate_material(
        self, con: sqlite3.Connection, request: ProcessingRequest, material: InputMaterial
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
            raise WorkbenchInvariantError("input Representation custody changed before commit")
        if row[1] == "purged" or row[2] == "purged":
            raise WorkbenchInvariantError("input custody was purged before commit")
        for scope in material.scopes:
            target = con.execute(
                "SELECT representation_id,availability FROM representation_targets WHERE id=?",
                (scope.id,),
            ).fetchone()
            if target != (material.representation_id, "available"):
                raise WorkbenchInvariantError("ProcessRun target changed before commit")

    def _verify_existing_run(
        self,
        con: sqlite3.Connection,
        request: ProcessingRequest,
        descriptor: ProcessorDescriptor | None,
    ) -> AttemptReceipt | None:
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
        if row[0] != request.capability_key or row[4] != request.configuration_hash:
            raise WorkbenchIdentityCollision(
                f"ProcessRun {request.process_run_id} exists with different immutable capability/configuration"
            )
        if descriptor is not None:
            expected_prefix = (
                descriptor.capability_key,
                descriptor.key,
                descriptor.implementation_version,
                descriptor.execution_venue,
                request.configuration_hash,
                descriptor.model_provider,
                descriptor.model_name,
            )
            if row[:7] != expected_prefix:
                raise WorkbenchIdentityCollision(
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
            raise WorkbenchIdentityCollision(
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
                raise WorkbenchIdentityCollision(
                    f"ProcessRun {request.process_run_id} replay changed egress policy identity"
                )
            if descriptor is not None and not descriptor.requires_egress:
                raise WorkbenchIdentityCollision(
                    "non-egress processor unexpectedly collided with egress ProcessRun"
                )
        elif descriptor is not None and descriptor.requires_egress:
            raise WorkbenchIdentityCollision("egress ProcessRun is missing egress provenance")

        self._validate_committed_attempt(con, request.process_run_id)
        decisions = tuple(
            PersistedDecision(*decision)
            for decision in con.execute(
                """
                SELECT q.id,q.representation_target_id,q.decision,q.policy_key,q.policy_version,
                       q.reason_code,q.next_capability_key
                FROM quality_decisions q
                JOIN process_run_inputs i
                  ON i.process_run_id=q.process_run_id
                 AND i.representation_target_id=q.representation_target_id
                WHERE q.process_run_id=?
                ORDER BY i.ordinal
                """,
                (request.process_run_id,),
            ).fetchall()
        )
        outputs: list[DerivedRepresentationReceipt] = []
        for output in con.execute(
            """
            SELECT r.id,r.archive_object_id,o.content_sha256,o.byte_size,o.storage_key
            FROM representations r
            JOIN archive_objects o ON o.id=r.archive_object_id
            WHERE r.process_run_id=? AND r.kind<>'original'
            ORDER BY r.id
            """,
            (request.process_run_id,),
        ).fetchall():
            self.archive.verify(output[4], output[2], output[3])
            outputs.append(DerivedRepresentationReceipt(*output))
        return AttemptReceipt(request.process_run_id, row[7], decisions, tuple(outputs), True)

    @staticmethod
    def _archive_row(con: sqlite3.Connection, object_id: str) -> tuple[str, int, str]:
        row = con.execute(
            """
            SELECT content_sha256,byte_size,storage_key FROM archive_objects
            WHERE id=? AND availability='available'
            """,
            (object_id,),
        ).fetchone()
        if row is None:
            raise WorkbenchInvariantError(f"derived output lacks available ArchiveObject {object_id}")
        return row

    @staticmethod
    def _validate_committed_attempt(con: sqlite3.Connection, process_run_id: str) -> None:
        run = con.execute(
            "SELECT outcome FROM process_runs WHERE id=?", (process_run_id,)
        ).fetchone()
        assert run is not None
        outputs = con.execute(
            "SELECT count(*) FROM representations WHERE process_run_id=?",
            (process_run_id,),
        ).fetchone()[0]
        if run[0] == "failed" and outputs:
            raise WorkbenchInvariantError("failed ProcessRun cannot authorize derivative output")
        inputs = con.execute(
            "SELECT count(*) FROM process_run_inputs WHERE process_run_id=?",
            (process_run_id,),
        ).fetchone()[0]
        decisions = con.execute(
            "SELECT count(*) FROM quality_decisions WHERE process_run_id=?",
            (process_run_id,),
        ).fetchone()[0]
        if inputs == 0 or decisions != inputs:
            raise WorkbenchInvariantError("ProcessRun must retain exact inputs and one decision per target")

    def _cleanup_unreferenced_materialized(
        self, con: sqlite3.Connection, materialized: dict[str, StoredObject]
    ) -> None:
        for digest, stored in materialized.items():
            if not stored.created:
                continue
            try:
                referenced = con.execute(
                    """
                    SELECT storage_key FROM archive_objects
                    WHERE content_sha256=? AND availability='available'
                    """,
                    (digest,),
                ).fetchone()
                if referenced is None or referenced[0] != stored.storage_key:
                    self.archive.remove_if_matches(stored)
            except Exception:
                pass
