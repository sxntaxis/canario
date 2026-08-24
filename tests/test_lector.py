from __future__ import annotations

import json
import sqlite3
import tempfile
import threading
import unittest
from dataclasses import replace
from pathlib import Path

from actakit.deposit import (
    AcquisitionObservation,
    AcquisitionWrite,
    CapturedArtifact,
    DepositWriter,
    SourceLocatorRegistration,
    SourceRegistration,
    new_id,
)
from actakit.lector import (
    ClaimDraft,
    ClaimRelationDraft,
    ClaimRevisionRef,
    EntityAnchorDraft,
    EntityMentionDraft,
    EvidenceDraft,
    LectorContractError,
    LectorHost,
    LectorIdentityCollision,
    LectorInvariantError,
    LectorWriter,
    RelationBasisDraft,
    ResolutionCandidateDraft,
    SemanticExtractionRequest,
    SemanticExtractorDescriptor,
    SemanticExtractorRegistry,
    SemanticLocatorError,
    SemanticResult,
    TagAssignmentDraft,
    TargetRef,
)
from actakit.lector.registry import SemanticExtractorResolutionError
from actakit.persistence import database
from actakit.processors import EgressAuthorization, TargetRegistration, WorkbenchWriter

NO_RUNTIME_CHECK = lambda: None
T = "2026-08-24T16:00:00.000Z"


def local_connection(path: Path) -> sqlite3.Connection:
    return database._open_writable_v1(path, NO_RUNTIME_CHECK)


class FixtureExtractor:
    def __init__(self, descriptor: SemanticExtractorDescriptor, fn) -> None:
        self._descriptor = descriptor
        self._fn = fn
        self.calls = 0

    @property
    def descriptor(self) -> SemanticExtractorDescriptor:
        return self._descriptor

    def extract(self, invocation):
        self.calls += 1
        return self._fn(invocation)


def descriptor(
    *,
    key: str = "lector.fixture",
    origin_kind: str = "machine",
    venue: str = "local_deterministic",
    media_types: frozenset[str] = frozenset({"text/plain"}),
    representation_kinds: frozenset[str] = frozenset({"original"}),
    scope_kinds: frozenset[str] = frozenset({"whole", "text_quote", "table_range"}),
    requires_egress: bool = False,
    model: bool = False,
    **bounds,
) -> SemanticExtractorDescriptor:
    values = dict(
        key=key,
        capability_key="claim_extract",
        implementation_version="1",
        origin_kind=origin_kind,
        execution_venue=venue,
        input_media_types=media_types,
        input_representation_kinds=representation_kinds,
        scope_kinds=scope_kinds,
        requires_egress=requires_egress,
        model_provider="openai" if model else None,
        model_name="gpt-test" if model else None,
    )
    values.update(bounds)
    return SemanticExtractorDescriptor(**values)


class LectorWriterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / "actakit.sqlite3"
        self.archive = self.root / "archive"
        database._ensure_schema_v1(self.db, NO_RUNTIME_CHECK)
        self.deposit = DepositWriter(self.db, self.archive, connection_factory=local_connection)
        self.workbench = WorkbenchWriter(
            self.db, self.archive, connection_factory=local_connection
        )
        self.writer = LectorWriter(
            self.db, self.archive, connection_factory=local_connection
        )
        self.source = SourceRegistration(new_id("src_"), "web", "Municipalidad", True, T)
        self.deposit.register_source(self.source)
        self.locator = SourceLocatorRegistration(
            new_id("sloc_"), self.source.id, "https://example.test/document", "http_url", T
        )
        self.deposit.register_source_locator(self.locator)
        self.text = (
            "SE ACUERDA aprobar ₡25 millones para el camino de San Jerónimo. "
            "AyA coordinará las obras."
        )
        self.rep_id = self._capture(self.text.encode("utf-8"), "text/plain", "available")
        self.whole = self._target(self.rep_id, "whole", "{}")
        self.entity_id = new_id("ent_")
        self.tag_id = new_id("tag_")
        con = self._con()
        try:
            con.execute(
                "INSERT INTO entities(id,kind,canonical_name,created_at) VALUES (?,?,?,?)",
                (self.entity_id, "organization", "AyA", T),
            )
            con.execute(
                "INSERT INTO tags(id,namespace,key,label,created_at) VALUES (?,?,?,?,?)",
                (self.tag_id, "civic", "obra_publica", "Obra pública", T),
            )
            con.commit()
        finally:
            con.close()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _con(self) -> sqlite3.Connection:
        return local_connection(self.db)

    def _capture(self, data: bytes, media_type: str, availability: str) -> str:
        rep_id = new_id("rep_")
        artifact = CapturedArtifact(
            new_id("art_"),
            new_id("aob_"),
            rep_id,
            data,
            "primary",
            "document.bin",
            self.locator.locator,
            media_type,
            "verified",
            availability,
            "es",
            "utf-8",
            T,
        )
        observation = AcquisitionObservation(
            new_id("acq_"),
            self.source.id,
            self.locator.id,
            T,
            "success",
            200,
            "fixture",
            "1",
            None,
            T,
        )
        self.deposit.record_acquisition(AcquisitionWrite(observation, (artifact,)))
        return rep_id

    def _target(self, rep_id: str, kind: str, payload: str) -> str:
        target_id = new_id("rtgt_")
        self.workbench.register_target(
            TargetRegistration(target_id, rep_id, kind, "v1", payload, T)
        )
        return target_id

    def _quote(self, exact: str) -> TargetRef:
        start = self.text.index(exact)
        return TargetRef.proposed(
            "text_quote",
            "v1",
            json.dumps(
                {"exact": exact, "start_char": start, "end_char": start + len(exact)}
            ),
        )

    def _rich_result(self) -> SemanticResult:
        agreement = "SE ACUERDA aprobar ₡25 millones para el camino de San Jerónimo."
        coordination = "AyA coordinará las obras."
        agreement_ref = self._quote(agreement)
        coordination_ref = self._quote(coordination)
        aya_ref = self._quote("AyA")
        c1 = ClaimDraft(
            "c1",
            "source_assertion",
            "El Concejo acordó aprobar ₡25 millones para el camino de San Jerónimo.",
            (EvidenceDraft(agreement_ref, "supports", "active"),),
            tags=(TagAssignmentDraft(self.tag_id, "active"),),
            quantitative=True,
        )
        c2 = ClaimDraft(
            "c2",
            "source_assertion",
            "AyA coordinará las obras.",
            (EvidenceDraft(coordination_ref, "quotes", "active"),),
            mentions=(
                EntityMentionDraft(
                    "AyA",
                    aya_ref,
                    (ResolutionCandidateDraft(self.entity_id, 0.9),),
                ),
            ),
            entity_anchors=(EntityAnchorDraft(self.entity_id, "actor", "candidate"),),
            attribution_text="AyA",
        )
        relation = ClaimRelationDraft(
            ClaimRevisionRef.local("c2"),
            ClaimRevisionRef.local("c1"),
            "implements",
            "source_evidence",
            (RelationBasisDraft(coordination_ref, "source_basis"),),
            "La obligación de coordinación forma parte del mismo acuerdo.",
            "candidate",
        )
        return SemanticResult("success", (c1, c2), (relation,))

    def test_rich_semantic_transaction_persists_and_replays_without_reinvocation(self) -> None:
        proc = FixtureExtractor(descriptor(), lambda inv: self._rich_result())
        host = LectorHost(self.writer, SemanticExtractorRegistry((proc,)))
        request = SemanticExtractionRequest(self.rep_id, (self.whole,), "claim_extract")

        receipt = host.run_attempt(request)
        self.assertFalse(receipt.replayed)
        self.assertEqual(receipt.outcome, "success")
        self.assertEqual(len(receipt.claims), 2)
        self.assertEqual(len(receipt.relations), 1)
        self.assertEqual(proc.calls, 1)
        for persisted in receipt.claims:
            con = self._con()
            try:
                self.assertEqual(
                    con.execute(
                        "SELECT claim_id FROM claim_revisions WHERE id=?",
                        (persisted.revision_id,),
                    ).fetchone(),
                    (persisted.claim_id,),
                )
            finally:
                con.close()

        replay = host.run_attempt(request)
        self.assertTrue(replay.replayed)
        self.assertEqual(replay.claims, receipt.claims)
        self.assertEqual(replay.relations, receipt.relations)
        self.assertEqual(proc.calls, 1)

        replay_without_adapter = LectorHost(
            self.writer, SemanticExtractorRegistry(())
        ).run_attempt(request)
        self.assertTrue(replay_without_adapter.replayed)
        self.assertEqual(replay_without_adapter.claims, receipt.claims)

        con = self._con()
        try:
            self.assertEqual(
                con.execute(
                    "SELECT process_kind,outcome FROM process_runs WHERE id=?",
                    (request.process_run_id,),
                ).fetchone(),
                ("lector.claim_extract", "success"),
            )
            self.assertEqual(
                con.execute(
                    "SELECT count(*) FROM mention_resolution_revisions"
                ).fetchone()[0],
                0,
            )
            self.assertEqual(
                con.execute(
                    "SELECT lifecycle FROM claim_entity_links WHERE process_run_id=?",
                    (request.process_run_id,),
                ).fetchone(),
                ("candidate",),
            )
        finally:
            con.close()

    def test_failed_run_persists_provenance_without_semantic_rows_and_replays(self) -> None:
        proc = FixtureExtractor(
            descriptor(), lambda inv: SemanticResult("failed", error_code="extract_failed")
        )
        host = LectorHost(self.writer, SemanticExtractorRegistry((proc,)))
        request = SemanticExtractionRequest(self.rep_id, (self.whole,), "claim_extract")
        first = host.run_attempt(request)
        second = host.run_attempt(request)
        self.assertEqual(first.outcome, "failed")
        self.assertTrue(second.replayed)
        self.assertEqual(proc.calls, 1)
        con = self._con()
        try:
            self.assertEqual(
                con.execute(
                    "SELECT count(*) FROM claim_revisions WHERE process_run_id=?",
                    (request.process_run_id,),
                ).fetchone()[0],
                0,
            )
            self.assertEqual(
                con.execute(
                    "SELECT representation_target_id FROM process_run_inputs WHERE process_run_id=?",
                    (request.process_run_id,),
                ).fetchone(),
                (self.whole,),
            )
        finally:
            con.close()

    def test_partial_run_can_preserve_exact_evidence_backed_claims(self) -> None:
        claim = ClaimDraft(
            "c1",
            "source_assertion",
            "AyA coordinará las obras.",
            (EvidenceDraft(self._quote("AyA coordinará las obras.")),),
        )
        proc = FixtureExtractor(
            descriptor(),
            lambda inv: SemanticResult(
                "partial", (claim,), error_code="some_content_unreadable"
            ),
        )
        request = SemanticExtractionRequest(self.rep_id, (self.whole,), "claim_extract")
        receipt = LectorHost(self.writer, SemanticExtractorRegistry((proc,))).run_attempt(request)
        self.assertEqual(receipt.outcome, "partial")
        self.assertEqual(len(receipt.claims), 1)
        con = self._con()
        try:
            self.assertEqual(
                con.execute(
                    "SELECT outcome,error_code FROM process_runs WHERE id=?",
                    (request.process_run_id,),
                ).fetchone(),
                ("partial", "some_content_unreadable"),
            )
        finally:
            con.close()


    def test_same_process_run_with_changed_scope_collides(self) -> None:
        exact = self._target(
            self.rep_id,
            "text_quote",
            json.dumps({"exact": "AyA", "start_char": self.text.index("AyA"), "end_char": self.text.index("AyA") + 3}),
        )
        proc = FixtureExtractor(descriptor(), lambda inv: self._rich_result())
        host = LectorHost(self.writer, SemanticExtractorRegistry((proc,)))
        request = SemanticExtractionRequest(self.rep_id, (self.whole,), "claim_extract")
        host.run_attempt(request)
        changed = SemanticExtractionRequest(
            self.rep_id,
            (exact,),
            "claim_extract",
            process_run_id=request.process_run_id,
        )
        with self.assertRaises(LectorIdentityCollision):
            host.run_attempt(changed)
        self.assertEqual(proc.calls, 1)

    def test_false_locator_rolls_back_entire_attempt(self) -> None:
        bad = TargetRef.proposed(
            "text_quote", "v1", json.dumps({"exact": "NO EXISTE"})
        )
        claim = ClaimDraft(
            "c1", "source_assertion", "Algo ocurrió.", (EvidenceDraft(bad),)
        )
        proc = FixtureExtractor(descriptor(), lambda inv: SemanticResult("success", (claim,)))
        request = SemanticExtractionRequest(self.rep_id, (self.whole,), "claim_extract")
        with self.assertRaises(SemanticLocatorError):
            LectorHost(self.writer, SemanticExtractorRegistry((proc,))).run_attempt(request)
        con = self._con()
        try:
            self.assertEqual(
                con.execute(
                    "SELECT count(*) FROM process_runs WHERE id=?", (request.process_run_id,)
                ).fetchone()[0],
                0,
            )
            self.assertEqual(con.execute("SELECT count(*) FROM claims").fetchone()[0], 0)
        finally:
            con.close()

    def test_narrow_scope_cannot_expand_to_unrelated_locator(self) -> None:
        aya = self._target(
            self.rep_id,
            "text_quote",
            json.dumps({"exact": "AyA", "start_char": self.text.index("AyA"), "end_char": self.text.index("AyA") + 3}),
        )
        unrelated = self._quote("SE ACUERDA")
        claim = ClaimDraft(
            "c1", "source_assertion", "Se acuerda.", (EvidenceDraft(unrelated),)
        )
        proc = FixtureExtractor(descriptor(), lambda inv: SemanticResult("success", (claim,)))
        request = SemanticExtractionRequest(self.rep_id, (aya,), "claim_extract")
        with self.assertRaisesRegex(LectorInvariantError, "expands ProcessRun"):
            LectorHost(self.writer, SemanticExtractorRegistry((proc,))).run_attempt(request)

    def test_proposed_exact_input_scope_reuses_existing_target(self) -> None:
        start = self.text.index("AyA")
        payload = json.dumps({"exact": "AyA", "start_char": start, "end_char": start + 3})
        aya = self._target(self.rep_id, "text_quote", payload)
        claim = ClaimDraft(
            "c1",
            "source_assertion",
            "AyA aparece en el documento.",
            (EvidenceDraft(TargetRef.proposed("text_quote", "v1", payload)),),
        )
        proc = FixtureExtractor(descriptor(), lambda inv: SemanticResult("success", (claim,)))
        request = SemanticExtractionRequest(self.rep_id, (aya,), "claim_extract")
        LectorHost(self.writer, SemanticExtractorRegistry((proc,))).run_attempt(request)
        con = self._con()
        try:
            target_count = con.execute(
                "SELECT count(*) FROM representation_targets WHERE representation_id=?",
                (self.rep_id,),
            ).fetchone()[0]
            evidence_target = con.execute(
                "SELECT representation_target_id FROM evidence_links WHERE process_run_id=?",
                (request.process_run_id,),
            ).fetchone()[0]
            self.assertEqual(target_count, 2)  # whole + exact AyA only
            self.assertEqual(evidence_target, aya)
        finally:
            con.close()

    def test_canonicalized_duplicate_evidence_is_rejected_by_writer(self) -> None:
        a = TargetRef.proposed("text_quote", "v1", '{"exact":"AyA"}')
        b = TargetRef.proposed("text_quote", "v1", '{ "exact" : "AyA" }')
        claim = ClaimDraft(
            "c1",
            "source_assertion",
            "AyA aparece.",
            (EvidenceDraft(a, "supports"), EvidenceDraft(b, "supports")),
        )
        proc = FixtureExtractor(descriptor(), lambda inv: SemanticResult("success", (claim,)))
        request = SemanticExtractionRequest(self.rep_id, (self.whole,), "claim_extract")
        with self.assertRaisesRegex(LectorInvariantError, "duplicate canonical target/relation"):
            LectorHost(self.writer, SemanticExtractorRegistry((proc,))).run_attempt(request)
        con = self._con()
        try:
            self.assertEqual(
                con.execute("SELECT count(*) FROM process_runs WHERE id=?", (request.process_run_id,)).fetchone()[0],
                0,
            )
        finally:
            con.close()

    def test_canonicalized_duplicate_mentions_are_rejected_by_writer(self) -> None:
        a = TargetRef.proposed("text_quote", "v1", '{"exact":"AyA"}')
        b = TargetRef.proposed("text_quote", "v1", '{ "exact" : "AyA" }')
        claim = ClaimDraft(
            "c1",
            "source_assertion",
            "AyA aparece.",
            (EvidenceDraft(a, "supports"),),
            mentions=(EntityMentionDraft("AyA", a), EntityMentionDraft("AyA", b)),
        )
        proc = FixtureExtractor(descriptor(), lambda inv: SemanticResult("success", (claim,)))
        request = SemanticExtractionRequest(self.rep_id, (self.whole,), "claim_extract")
        with self.assertRaisesRegex(LectorInvariantError, "duplicate canonical occurrence"):
            LectorHost(self.writer, SemanticExtractorRegistry((proc,))).run_attempt(request)


    def test_canonicalized_duplicate_relation_basis_is_rejected_by_writer(self) -> None:
        c1 = ClaimDraft("c1", "source_assertion", "A.", (EvidenceDraft(self._quote("SE ACUERDA")),))
        c2 = ClaimDraft("c2", "source_assertion", "B.", (EvidenceDraft(self._quote("AyA")),))
        a = TargetRef.proposed("text_quote", "v1", '{"exact":"AyA"}')
        b = TargetRef.proposed("text_quote", "v1", '{ "exact" : "AyA" }')
        relation = ClaimRelationDraft(
            ClaimRevisionRef.local("c1"),
            ClaimRevisionRef.local("c2"),
            "implements",
            "source_evidence",
            (RelationBasisDraft(a, "source_basis"), RelationBasisDraft(b, "source_basis")),
            lifecycle="candidate",
        )
        proc = FixtureExtractor(
            descriptor(), lambda inv: SemanticResult("success", (c1, c2), (relation,))
        )
        request = SemanticExtractionRequest(self.rep_id, (self.whole,), "claim_extract")
        with self.assertRaisesRegex(LectorInvariantError, "duplicate canonical target/role"):
            LectorHost(self.writer, SemanticExtractorRegistry((proc,))).run_attempt(request)

    def test_missing_entity_or_tag_fails_closed_and_rolls_back(self) -> None:
        claim = ClaimDraft(
            "c1",
            "source_assertion",
            "AyA coordina.",
            (EvidenceDraft(self._quote("AyA coordinará las obras.")),),
            tags=(TagAssignmentDraft(new_id("tag_")),),
        )
        proc = FixtureExtractor(descriptor(), lambda inv: SemanticResult("success", (claim,)))
        request = SemanticExtractionRequest(self.rep_id, (self.whole,), "claim_extract")
        with self.assertRaisesRegex(LectorInvariantError, "unknown Tag"):
            LectorHost(self.writer, SemanticExtractorRegistry((proc,))).run_attempt(request)
        con = self._con()
        try:
            self.assertEqual(
                con.execute("SELECT count(*) FROM process_runs WHERE id=?", (request.process_run_id,)).fetchone()[0],
                0,
            )
        finally:
            con.close()

    def test_machine_cannot_launder_attribution_or_active_entity_anchor(self) -> None:
        base = ClaimDraft(
            "c1",
            "source_assertion",
            "AyA coordina.",
            (EvidenceDraft(self._quote("AyA coordinará las obras.")),),
            attribution_entity_id=self.entity_id,
        )
        proc = FixtureExtractor(descriptor(), lambda inv: SemanticResult("success", (base,)))
        with self.assertRaisesRegex(LectorInvariantError, "attribution Entity"):
            LectorHost(self.writer, SemanticExtractorRegistry((proc,))).run_attempt(
                SemanticExtractionRequest(self.rep_id, (self.whole,), "claim_extract")
            )

        active_anchor = replace(
            base,
            attribution_entity_id=None,
            entity_anchors=(EntityAnchorDraft(self.entity_id, lifecycle="active"),),
        )
        proc2 = FixtureExtractor(descriptor(), lambda inv: SemanticResult("success", (active_anchor,)))
        with self.assertRaisesRegex(LectorInvariantError, "anchors must remain candidate"):
            LectorHost(self.writer, SemanticExtractorRegistry((proc2,))).run_attempt(
                SemanticExtractionRequest(self.rep_id, (self.whole,), "claim_extract")
            )

    def test_relation_promotion_rules(self) -> None:
        c1 = ClaimDraft("c1", "source_assertion", "A.", (EvidenceDraft(self._quote("SE ACUERDA")),))
        c2 = ClaimDraft("c2", "source_assertion", "B.", (EvidenceDraft(self._quote("AyA")),))
        machine_active = ClaimRelationDraft(
            ClaimRevisionRef.local("c1"), ClaimRevisionRef.local("c2"),
            "same_matter_as", "analyst_inference", rationale="model", lifecycle="active"
        )
        proc = FixtureExtractor(descriptor(), lambda inv: SemanticResult("success", (c1, c2), (machine_active,)))
        with self.assertRaisesRegex(LectorInvariantError, "machine ClaimRelations"):
            LectorHost(self.writer, SemanticExtractorRegistry((proc,))).run_attempt(
                SemanticExtractionRequest(self.rep_id, (self.whole,), "claim_extract")
            )

        weak_rule = FixtureExtractor(
            descriptor(origin_kind="rule", key="lector.rule"),
            lambda inv: SemanticResult("success", (c1, c2), (machine_active,)),
        )
        with self.assertRaisesRegex(LectorInvariantError, "active rule"):
            LectorHost(self.writer, SemanticExtractorRegistry((weak_rule,))).run_attempt(
                SemanticExtractionRequest(self.rep_id, (self.whole,), "claim_extract")
            )

        strong = replace(
            machine_active,
            basis_kind="mechanical_identity",
            rationale="same stable identifier",
        )
        strong_rule = FixtureExtractor(
            descriptor(origin_kind="rule", key="lector.rule.strong"),
            lambda inv: SemanticResult("success", (c1, c2), (strong,)),
        )
        receipt = LectorHost(self.writer, SemanticExtractorRegistry((strong_rule,))).run_attempt(
            SemanticExtractionRequest(self.rep_id, (self.whole,), "claim_extract")
        )
        self.assertEqual(len(receipt.relations), 1)

    def test_symmetric_relation_is_canonicalized_once(self) -> None:
        c1 = ClaimDraft("c1", "source_assertion", "A.", (EvidenceDraft(self._quote("SE ACUERDA")),))
        c2 = ClaimDraft("c2", "source_assertion", "B.", (EvidenceDraft(self._quote("AyA")),))
        relation = ClaimRelationDraft(
            ClaimRevisionRef.local("c2"), ClaimRevisionRef.local("c1"),
            "contradicts", "analyst_inference", rationale="candidate"
        )
        proc = FixtureExtractor(descriptor(), lambda inv: SemanticResult("success", (c1, c2), (relation,)))
        receipt = LectorHost(self.writer, SemanticExtractorRegistry((proc,))).run_attempt(
            SemanticExtractionRequest(self.rep_id, (self.whole,), "claim_extract")
        )
        con = self._con()
        try:
            row = con.execute(
                "SELECT from_claim_revision_id,to_claim_revision_id FROM claim_relation_revisions WHERE id=?",
                (receipt.relations[0].revision_id,),
            ).fetchone()
            self.assertLess(row[0], row[1])
            self.assertEqual(con.execute("SELECT count(*) FROM claim_relations").fetchone()[0], 1)
        finally:
            con.close()

    def test_restricted_input_propagates_claim_restriction_and_blocks_cloud(self) -> None:
        restricted_rep = self._capture(b"AyA", "text/plain", "restricted")
        whole = self._target(restricted_rep, "whole", "{}")
        claim = ClaimDraft(
            "c1", "source_assertion", "AyA.",
            (EvidenceDraft(TargetRef.proposed("text_quote", "v1", json.dumps({"exact": "AyA"}))),),
        )
        local = FixtureExtractor(descriptor(), lambda inv: SemanticResult("success", (claim,)))
        request = SemanticExtractionRequest(restricted_rep, (whole,), "claim_extract")
        receipt = LectorHost(self.writer, SemanticExtractorRegistry((local,))).run_attempt(request)
        con = self._con()
        try:
            self.assertEqual(
                con.execute("SELECT lifecycle FROM claim_revisions WHERE id=?", (receipt.claims[0].revision_id,)).fetchone(),
                ("restricted",),
            )
        finally:
            con.close()

        cloud = FixtureExtractor(
            descriptor(
                key="lector.cloud", venue="subscription_agent", requires_egress=True, model=True
            ),
            lambda inv: self.fail("restricted input must not invoke cloud extractor"),
        )
        with self.assertRaises(SemanticExtractorResolutionError):
            LectorHost(self.writer, SemanticExtractorRegistry((cloud,))).run_attempt(
                SemanticExtractionRequest(
                    restricted_rep,
                    (whole,),
                    "claim_extract",
                    egress=EgressAuthorization(True, "public_civic", "chatgpt_operator"),
                )
            )
        self.assertEqual(cloud.calls, 0)

    def test_egress_is_durable_and_replay_policy_is_immutable(self) -> None:
        cloud = FixtureExtractor(
            descriptor(
                key="lector.cloud", venue="subscription_agent", requires_egress=True, model=True
            ),
            lambda inv: SemanticResult("failed", error_code="model_failed", egress_bytes=123),
        )
        auth = EgressAuthorization(
            True, "public_civic", "chatgpt_operator", "a" * 64, "codex_cli"
        )
        request = SemanticExtractionRequest(
            self.rep_id, (self.whole,), "claim_extract", egress=auth
        )
        host = LectorHost(self.writer, SemanticExtractorRegistry((cloud,)))
        host.run_attempt(request)
        con = self._con()
        try:
            self.assertEqual(
                con.execute(
                    "SELECT bytes_egressed,policy_profile,data_control_profile FROM process_run_egress WHERE process_run_id=?",
                    (request.process_run_id,),
                ).fetchone(),
                (123, "public_civic", "chatgpt_operator"),
            )
        finally:
            con.close()
        changed = SemanticExtractionRequest(
            self.rep_id,
            (self.whole,),
            "claim_extract",
            egress=replace(auth, data_control_profile="other_profile"),
            process_run_id=request.process_run_id,
        )
        with self.assertRaisesRegex(LectorIdentityCollision, "egress policy"):
            host.run_attempt(changed)

    def test_egress_zero_before_handoff_is_valid_and_local_cannot_report_egress(self) -> None:
        cloud = FixtureExtractor(
            descriptor(
                key="lector.cloud.zero",
                venue="subscription_agent",
                requires_egress=True,
                model=True,
            ),
            lambda inv: SemanticResult(
                "failed", error_code="pre_handoff_failure", egress_bytes=0
            ),
        )
        auth = EgressAuthorization(True, "public_civic", "chatgpt_operator")
        request = SemanticExtractionRequest(
            self.rep_id, (self.whole,), "claim_extract", egress=auth
        )
        LectorHost(self.writer, SemanticExtractorRegistry((cloud,))).run_attempt(request)
        con = self._con()
        try:
            self.assertEqual(
                con.execute(
                    "SELECT bytes_egressed FROM process_run_egress WHERE process_run_id=?",
                    (request.process_run_id,),
                ).fetchone(),
                (0,),
            )
        finally:
            con.close()

        local = FixtureExtractor(
            descriptor(key="lector.local.egress_lie"),
            lambda inv: SemanticResult(
                "failed", error_code="local_failed", egress_bytes=1
            ),
        )
        local_request = SemanticExtractionRequest(
            self.rep_id, (self.whole,), "claim_extract"
        )
        with self.assertRaisesRegex(LectorInvariantError, "non-egress extractor"):
            LectorHost(self.writer, SemanticExtractorRegistry((local,))).run_attempt(
                local_request
            )


    def test_same_text_new_process_run_remains_distinct_civic_identity(self) -> None:
        claim = ClaimDraft(
            "c1", "source_assertion", "AyA coordina.",
            (EvidenceDraft(self._quote("AyA coordinará las obras.")),),
        )
        proc = FixtureExtractor(descriptor(), lambda inv: SemanticResult("success", (claim,)))
        host = LectorHost(self.writer, SemanticExtractorRegistry((proc,)))
        a = host.run_attempt(SemanticExtractionRequest(self.rep_id, (self.whole,), "claim_extract"))
        b = host.run_attempt(SemanticExtractionRequest(self.rep_id, (self.whole,), "claim_extract"))
        self.assertNotEqual(a.claims[0].claim_id, b.claims[0].claim_id)
        self.assertEqual(proc.calls, 2)

    def test_result_bounds_are_rechecked_by_writer(self) -> None:
        c1 = ClaimDraft("c1", "source_assertion", "A.", (EvidenceDraft(self._quote("SE ACUERDA")),))
        c2 = ClaimDraft("c2", "source_assertion", "B.", (EvidenceDraft(self._quote("AyA")),))
        proc = FixtureExtractor(
            descriptor(max_claims=1), lambda inv: SemanticResult("success", (c1, c2))
        )
        request = SemanticExtractionRequest(self.rep_id, (self.whole,), "claim_extract")
        with self.assertRaisesRegex(LectorInvariantError, "claim limit"):
            LectorHost(self.writer, SemanticExtractorRegistry((proc,))).run_attempt(request)
        con = self._con()
        try:
            self.assertEqual(con.execute("SELECT count(*) FROM process_runs WHERE id=?", (request.process_run_id,)).fetchone()[0], 0)
        finally:
            con.close()

    def test_evidence_link_bound_is_rechecked_by_writer(self) -> None:
        refs = tuple(EvidenceDraft(self._quote("AyA"), "supports", "active") for _ in range(2))
        # Use distinct relations to avoid the intra-result duplicate guard while
        # proving the aggregate writer bound independently.
        refs = (
            EvidenceDraft(self._quote("AyA"), "supports", "active"),
            EvidenceDraft(self._quote("AyA"), "quotes", "active"),
        )
        claim = ClaimDraft("c1", "source_assertion", "AyA.", refs)
        proc = FixtureExtractor(
            descriptor(max_evidence_links=1),
            lambda inv: SemanticResult("success", (claim,)),
        )
        request = SemanticExtractionRequest(self.rep_id, (self.whole,), "claim_extract")
        with self.assertRaisesRegex(LectorInvariantError, "evidence link limit"):
            LectorHost(self.writer, SemanticExtractorRegistry((proc,))).run_attempt(request)

    def test_human_attribution_requires_existing_entity(self) -> None:
        claim = ClaimDraft(
            "c1",
            "source_assertion",
            "La persona indicó algo.",
            (EvidenceDraft(self._quote("AyA")),),
            attribution_entity_id=new_id("ent_"),
        )
        human = FixtureExtractor(
            descriptor(origin_kind="human", key="lector.human"),
            lambda inv: SemanticResult("success", (claim,)),
        )
        request = SemanticExtractionRequest(self.rep_id, (self.whole,), "claim_extract")
        with self.assertRaisesRegex(LectorInvariantError, "unknown Entity"):
            LectorHost(self.writer, SemanticExtractorRegistry((human,))).run_attempt(request)
        con = self._con()
        try:
            self.assertEqual(
                con.execute("SELECT count(*) FROM process_runs WHERE id=?", (request.process_run_id,)).fetchone()[0],
                0,
            )
        finally:
            con.close()

    def test_large_machine_only_batch_persists_and_replays_without_duplicate_explosion(self) -> None:
        target = self._quote("AyA")
        claims = tuple(
            ClaimDraft(
                f"c{i}",
                "source_assertion",
                f"Claim número {i}: AyA aparece en el material.",
                (EvidenceDraft(target),),
            )
            for i in range(300)
        )
        proc = FixtureExtractor(
            descriptor(max_claims=500, max_evidence_links=500),
            lambda inv: SemanticResult("success", claims),
        )
        host = LectorHost(self.writer, SemanticExtractorRegistry((proc,)))
        request = SemanticExtractionRequest(self.rep_id, (self.whole,), "claim_extract")
        first = host.run_attempt(request)
        second = host.run_attempt(request)
        self.assertEqual(len(first.claims), 300)
        self.assertTrue(second.replayed)
        self.assertEqual(first.claims, second.claims)
        self.assertEqual(proc.calls, 1)
        con = self._con()
        try:
            self.assertEqual(
                con.execute("SELECT count(*) FROM claim_revisions WHERE process_run_id=?", (request.process_run_id,)).fetchone()[0],
                300,
            )
            self.assertEqual(
                con.execute("SELECT count(*) FROM claim_reviews").fetchone()[0],
                0,
            )
        finally:
            con.close()

    def test_host_rejects_non_semantic_result(self) -> None:
        proc = FixtureExtractor(descriptor(), lambda inv: {"claims": []})
        with self.assertRaises(LectorContractError):
            LectorHost(self.writer, SemanticExtractorRegistry((proc,))).run_attempt(
                SemanticExtractionRequest(self.rep_id, (self.whole,), "claim_extract")
            )

    def test_process_run_preserves_exact_ordered_inputs(self) -> None:
        a_start = self.text.index("SE ACUERDA")
        b_start = self.text.index("AyA")
        a = self._target(
            self.rep_id, "text_quote",
            json.dumps({"exact":"SE ACUERDA","start_char":a_start,"end_char":a_start+10})
        )
        b = self._target(
            self.rep_id, "text_quote",
            json.dumps({"exact":"AyA","start_char":b_start,"end_char":b_start+3})
        )
        claim = ClaimDraft("c1", "source_assertion", "AyA.", (EvidenceDraft(TargetRef.existing(b)),))
        proc = FixtureExtractor(descriptor(), lambda inv: SemanticResult("success", (claim,)))
        request = SemanticExtractionRequest(self.rep_id, (b, a), "claim_extract")
        LectorHost(self.writer, SemanticExtractorRegistry((proc,))).run_attempt(request)
        con = self._con()
        try:
            rows = con.execute(
                "SELECT ordinal,representation_target_id FROM process_run_inputs WHERE process_run_id=? ORDER BY ordinal",
                (request.process_run_id,),
            ).fetchall()
            self.assertEqual(rows, [(0, b), (1, a)])
        finally:
            con.close()

    def test_table_range_reopens_exact_structured_representation(self) -> None:
        table_rep = self._capture(
            json.dumps({"rows": [["Partida", "Monto"], ["Caminos", 25]]}).encode(),
            "application/json",
            "available",
        )
        whole = self._target(table_rep, "whole", "{}")
        target = TargetRef.proposed(
            "table_range",
            "v1",
            json.dumps({"row_start":2,"row_end":2,"observed_values":[["Caminos",25]]}),
        )
        claim = ClaimDraft(
            "c1", "source_assertion", "La partida Caminos registra 25.", (EvidenceDraft(target),),
            quantitative=True,
        )
        proc = FixtureExtractor(
            descriptor(media_types=frozenset({"application/json"})),
            lambda inv: SemanticResult("success", (claim,)),
        )
        receipt = LectorHost(self.writer, SemanticExtractorRegistry((proc,))).run_attempt(
            SemanticExtractionRequest(table_rep, (whole,), "claim_extract")
        )
        self.assertEqual(len(receipt.evidence_link_ids), 1)

    def test_concurrent_same_run_has_one_canonical_batch(self) -> None:
        barrier = threading.Barrier(2)
        claim = ClaimDraft(
            "c1", "source_assertion", "AyA coordina.",
            (EvidenceDraft(self._quote("AyA coordinará las obras.")),),
        )
        proc = FixtureExtractor(
            descriptor(),
            lambda inv: (barrier.wait(timeout=5), SemanticResult("success", (claim,)))[1],
        )
        host = LectorHost(self.writer, SemanticExtractorRegistry((proc,)))
        request = SemanticExtractionRequest(self.rep_id, (self.whole,), "claim_extract")
        receipts = []
        errors = []

        def run():
            try:
                receipts.append(host.run_attempt(request))
            except Exception as exc:  # pragma: no cover - surfaced below
                errors.append(exc)

        threads = [threading.Thread(target=run), threading.Thread(target=run)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)
        self.assertEqual(errors, [])
        self.assertEqual(len(receipts), 2)
        self.assertEqual({r.claims for r in receipts}, {receipts[0].claims})
        self.assertEqual(proc.calls, 2)
        con = self._con()
        try:
            self.assertEqual(con.execute("SELECT count(*) FROM process_runs WHERE id=?", (request.process_run_id,)).fetchone()[0], 1)
            self.assertEqual(con.execute("SELECT count(*) FROM claim_revisions WHERE process_run_id=?", (request.process_run_id,)).fetchone()[0], 1)
        finally:
            con.close()


if __name__ == "__main__":
    unittest.main()
