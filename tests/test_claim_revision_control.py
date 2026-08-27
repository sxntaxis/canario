from __future__ import annotations

import json
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path

from canario.deposit import (
    AcquisitionObservation,
    AcquisitionWrite,
    CapturedArtifact,
    DepositWriter,
    SourceLocatorRegistration,
    SourceRegistration,
    new_id,
)
from canario.lector import (
    ClaimDraft,
    EntityAnchorDraft,
    EvidenceDraft,
    LectorHost,
    LectorWriter,
    SemanticExtractionRequest,
    SemanticExtractorDescriptor,
    SemanticExtractorRegistry,
    SemanticResult,
    TagAssignmentDraft,
    TargetRef,
)
from canario.persistence import database
from canario.processors import TargetRegistration, WorkbenchWriter
from canario.review import (
    ClaimControlIdentityCollision,
    ClaimControlInvariantError,
    ClaimControlWriter,
    ClaimRevisionControlRequest,
    ClaimReviewActionRequest,
    ClaimReviewDraft,
    HumanClaimCorrection,
    ReviewReader,
    ReviewWriter,
)

NO_RUNTIME_CHECK = lambda: None
T = "2026-08-27T05:00:00.000Z"
T2 = "2026-08-27T05:01:00.000Z"
T3 = "2026-08-27T05:02:00.000Z"
T4 = "2026-08-27T05:03:00.000Z"
T5 = "2026-08-27T05:04:00.000Z"


def local_connection(path: Path) -> sqlite3.Connection:
    return database._open_writable_v1(path, NO_RUNTIME_CHECK)


def local_read_connection(path: Path) -> sqlite3.Connection:
    return database._open_readonly_v1(path, NO_RUNTIME_CHECK)


class FixtureExtractor:
    def __init__(self, claim: ClaimDraft) -> None:
        self._descriptor = SemanticExtractorDescriptor(
            key="lector.claim_control_fixture",
            capability_key="claim_extract",
            implementation_version="1",
            origin_kind="machine",
            execution_venue="local_deterministic",
            input_media_types=frozenset({"text/plain"}),
            input_representation_kinds=frozenset({"original"}),
            scope_kinds=frozenset({"whole", "text_quote"}),
        )
        self.claim = claim

    @property
    def descriptor(self):
        return self._descriptor

    def extract(self, _invocation):
        return SemanticResult("success", (self.claim,))


class ClaimRevisionControlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / "canario.sqlite3"
        self.archive = self.root / "archive"
        database._ensure_schema_v1(self.db, NO_RUNTIME_CHECK)
        self.deposit = DepositWriter(self.db, self.archive, connection_factory=local_connection)
        self.workbench = WorkbenchWriter(
            self.db, self.archive, connection_factory=local_connection
        )
        self.lector = LectorWriter(
            self.db, self.archive, connection_factory=local_connection
        )
        self.review_writer = ReviewWriter(self.db, connection_factory=local_connection)
        self.reader = ReviewReader(
            self.db, self.archive, connection_factory=local_read_connection
        )
        self.control = ClaimControlWriter(self.db, connection_factory=local_connection)

        source = SourceRegistration(new_id("src_"), "web", "Municipalidad", True, T)
        self.deposit.register_source(source)
        locator = SourceLocatorRegistration(
            new_id("sloc_"), source.id, "https://example.test/acta", "http_url", T
        )
        self.deposit.register_source_locator(locator)
        self.locator = locator
        self.text = "El Concejo aprobó ₡50 millones para el camino. AyA coordinará las obras."
        self.rep_id = self._capture(self.text.encode("utf-8"))
        self.whole = self._target(self.rep_id, "whole", "{}")
        self.entity_id = new_id("ent_")
        self.tag_id = new_id("tag_")
        con = local_connection(self.db)
        try:
            con.execute("INSERT INTO entities(id,kind,canonical_name,created_at) VALUES (?,?,?,?)", (self.entity_id, "organization", "AyA", T))
            con.execute(
                "INSERT INTO tags(id,namespace,key,label,created_at) VALUES (?,?,?,?,?)",
                (self.tag_id, "topic", "roads", "Roads", T),
            )
            con.commit()
        finally:
            con.close()
        self.revision_id = self._extract_claim()
        con = local_connection(self.db)
        try:
            text = con.execute(
                "SELECT text FROM claim_revisions WHERE id=?", (self.revision_id,)
            ).fetchone()[0]
            con.execute(
                "INSERT INTO claim_fts(claim_revision_id,text) VALUES (?,?)",
                (self.revision_id, text),
            )
            con.commit()
        finally:
            con.close()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _capture(self, data: bytes) -> str:
        rep_id = new_id("rep_")
        artifact = CapturedArtifact(
            new_id("art_"),
            new_id("aob_"),
            rep_id,
            data,
            "primary",
            "document.txt",
            self.locator.locator,
            "text/plain",
            "verified",
            "available",
            "es",
            "utf-8",
            T,
        )
        observation = AcquisitionObservation(
            new_id("acq_"),
            self.locator.source_id,
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

    def _extract_claim(self) -> str:
        exact = "El Concejo aprobó ₡50 millones para el camino."
        start = self.text.index(exact)
        quote = TargetRef.proposed(
            "text_quote",
            "v1",
            json.dumps(
                {"exact": exact, "start_char": start, "end_char": start + len(exact)}
            ),
        )
        context_exact = "AyA coordinará las obras."
        context_start = self.text.index(context_exact)
        context = TargetRef.proposed(
            "text_quote",
            "v1",
            json.dumps(
                {
                    "exact": context_exact,
                    "start_char": context_start,
                    "end_char": context_start + len(context_exact),
                }
            ),
        )
        claim = ClaimDraft(
            "amount",
            "source_assertion",
            exact,
            (
                EvidenceDraft(quote, "quotes", "active"),
                EvidenceDraft(context, "contextualizes", "active"),
            ),
            tags=(TagAssignmentDraft(self.tag_id, "active"),),
            entity_anchors=(EntityAnchorDraft(self.entity_id, "institution", "candidate"),),
            quantitative=True,
        )
        host = LectorHost(
            self.lector,
            SemanticExtractorRegistry((FixtureExtractor(claim),)),
        )
        receipt = host.run_attempt(
            SemanticExtractionRequest(self.rep_id, (self.whole,), "claim_extract")
        )
        return receipt.claims[0].revision_id

    def _correction(self, snapshot, *, text="El Concejo aprobó ₡5 millones para el camino."):
        con = local_read_connection(self.db)
        try:
            quote_ids = tuple(
                row[0]
                for row in con.execute(
                    """
                    SELECT id FROM evidence_links
                    WHERE claim_revision_id=? AND relation IN ('supports','quotes')
                    ORDER BY id
                    """,
                    (snapshot.claim_revision_id,),
                ).fetchall()
            )
        finally:
            con.close()
        return HumanClaimCorrection(
            claim_kind=snapshot.claim_kind,
            text=text,
            evidence_link_ids=quote_ids,
            entity_link_ids=snapshot.entity_link_ids,
            tag_link_ids=snapshot.tag_link_ids,
            attribution_entity_id=snapshot.attribution_entity_id,
            attribution_text=snapshot.attribution_text,
            temporal_start=snapshot.temporal_start,
            temporal_end=snapshot.temporal_end,
            sensitive=snapshot.sensitive,
            quantitative=snapshot.quantitative,
        )

    def _request(self, action: str, snapshot=None, **kwargs):
        snapshot = snapshot or self.reader.prepare_claim_control(self.revision_id)
        correction = kwargs.pop("correction", None)
        if action == "correct" and correction is None:
            correction = self._correction(snapshot)
        return ClaimRevisionControlRequest(
            snapshot.claim_revision_id,
            snapshot.snapshot_sha256,
            kwargs.pop("actor", "operator@example.test"),
            action,
            correction=correction,
            rationale=kwargs.pop("rationale", "human control action"),
            **kwargs,
        )

    def test_correction_creates_human_revision_and_accepts_it_atomically(self) -> None:
        self.review_writer.record_claim_reviews(
            ClaimReviewActionRequest(
                "operator@example.test",
                "strict",
                (ClaimReviewDraft(self.revision_id, "accepted"),),
            ),
            created_at=T2,
        )
        self.assertTrue(self.reader.claim_state(self.revision_id).strict_ready)
        snapshot = self.reader.prepare_claim_control(self.revision_id)
        request = self._request("correct", snapshot, rationale="50 -> 5")
        receipt = self.control.record(request, created_at=T3)

        old = self.reader.claim_state(self.revision_id)
        new = self.reader.claim_state(receipt.result_revision_id)
        self.assertFalse(old.current)
        self.assertFalse(old.strict_ready)
        self.assertTrue(new.current)
        self.assertEqual(new.origin_kind, "human")
        self.assertTrue(new.human_reviewed)
        self.assertFalse(new.unreviewed_human)
        self.assertEqual(new.latest_decision, "accepted")
        self.assertEqual(new.latest_reviewer, "operator@example.test")
        self.assertTrue(new.strict_ready)
        self.assertEqual(new.text, "El Concejo aprobó ₡5 millones para el camino.")
        self.assertEqual(receipt.review_action_id, request.review_action_id)
        self.assertIsNotNone(receipt.claim_review_id)

        con = local_read_connection(self.db)
        try:
            row = con.execute(
                """
                SELECT action,actor,rationale,review_action_id,request_sha256
                FROM claim_revision_actions WHERE id=?
                """,
                (receipt.claim_revision_action_id,),
            ).fetchone()
            self.assertEqual(row[:4], (
                "correct", "operator@example.test", "50 -> 5", request.review_action_id
            ))
            self.assertEqual(row[4], request.request_sha256())
            self.assertEqual(
                con.execute(
                    """
                    SELECT decision,reviewer,reason
                    FROM claim_reviews WHERE id=? AND review_action_id=? AND claim_revision_id=?
                    """,
                    (receipt.claim_review_id, request.review_action_id, receipt.result_revision_id),
                ).fetchone(),
                ("accepted", "operator@example.test", "50 -> 5"),
            )
            self.assertEqual(
                con.execute(
                    "SELECT supersedes_revision_id,revision_no FROM claim_revisions WHERE id=?",
                    (receipt.result_revision_id,),
                ).fetchone(),
                (self.revision_id, 2),
            )
            self.assertTrue(
                all(
                    row == ("human", None)
                    for row in con.execute(
                        "SELECT origin_kind,process_run_id FROM evidence_links WHERE claim_revision_id=?",
                        (receipt.result_revision_id,),
                    ).fetchall()
                )
            )
            self.assertTrue(
                all(
                    row == ("human", None)
                    for row in con.execute(
                        "SELECT origin_kind,process_run_id FROM claim_entity_links WHERE claim_revision_id=?",
                        (receipt.result_revision_id,),
                    ).fetchall()
                )
            )
        finally:
            con.close()

    def test_correction_review_action_collision_rolls_back_everything(self) -> None:
        snapshot = self.reader.prepare_claim_control(self.revision_id)
        request = self._request("correct", snapshot)
        assert request.review_action_id is not None
        con = local_connection(self.db)
        try:
            con.execute(
                "INSERT INTO review_actions(id,actor,mode,created_at,note) VALUES (?,?,?,?,?)",
                (request.review_action_id, "other", "supervised", T2, "occupied"),
            )
            con.commit()
        finally:
            con.close()

        with self.assertRaisesRegex(ClaimControlIdentityCollision, "ReviewAction ID collision"):
            self.control.record(request, created_at=T3)

        con = local_read_connection(self.db)
        try:
            self.assertIsNone(
                con.execute(
                    "SELECT 1 FROM claim_revisions WHERE id=?",
                    (request.result_revision_id,),
                ).fetchone()
            )
            self.assertIsNone(
                con.execute(
                    "SELECT 1 FROM claim_revision_actions WHERE id=?",
                    (request.claim_revision_action_id,),
                ).fetchone()
            )
            self.assertEqual(
                con.execute(
                    "SELECT count(*) FROM claim_reviews WHERE review_action_id=?",
                    (request.review_action_id,),
                ).fetchone()[0],
                0,
            )
        finally:
            con.close()

    def test_correction_preserves_only_explicit_selected_revision_metadata(self) -> None:
        snapshot = self.reader.prepare_claim_control(self.revision_id)
        correction = self._correction(snapshot)
        self.assertLess(len(correction.evidence_link_ids), len(snapshot.evidence_link_ids))
        receipt = self.control.record(
            self._request("correct", snapshot, correction=correction), created_at=T2
        )
        self.assertEqual(len(receipt.evidence_link_ids), len(correction.evidence_link_ids))
        self.assertEqual(len(receipt.entity_link_ids), len(snapshot.entity_link_ids))
        self.assertEqual(len(receipt.tag_link_ids), len(snapshot.tag_link_ids))

    def test_correction_requires_source_backed_evidence_for_source_assertion(self) -> None:
        snapshot = self.reader.prepare_claim_control(self.revision_id)
        con = local_read_connection(self.db)
        try:
            context_id = con.execute(
                "SELECT id FROM evidence_links WHERE claim_revision_id=? AND relation='contextualizes'",
                (self.revision_id,),
            ).fetchone()[0]
        finally:
            con.close()
        correction = HumanClaimCorrection(
            "source_assertion",
            "El Concejo aprobó ₡5 millones para el camino.",
            (context_id,),
            entity_link_ids=snapshot.entity_link_ids,
            tag_link_ids=snapshot.tag_link_ids,
            quantitative=True,
        )
        with self.assertRaisesRegex(ClaimControlInvariantError, "supports/quotes"):
            self.control.record(
                self._request("correct", snapshot, correction=correction), created_at=T2
            )

    def test_correction_can_change_non_derived_claim_kind(self) -> None:
        snapshot = self.reader.prepare_claim_control(self.revision_id)
        base = self._correction(snapshot)
        correction = HumanClaimCorrection(
            "community_report",
            base.text,
            base.evidence_link_ids,
            entity_link_ids=base.entity_link_ids,
            tag_link_ids=base.tag_link_ids,
            attribution_entity_id=base.attribution_entity_id,
            attribution_text=base.attribution_text,
            temporal_start=base.temporal_start,
            temporal_end=base.temporal_end,
            sensitive=base.sensitive,
            quantitative=base.quantitative,
        )
        receipt = self.control.record(
            self._request("correct", snapshot, correction=correction), created_at=T2
        )
        self.assertEqual(
            self.reader.prepare_claim_control(receipt.result_revision_id).claim_kind,
            "community_report",
        )

    def test_human_correction_cannot_fabricate_derived_inference_kind(self) -> None:
        snapshot = self.reader.prepare_claim_control(self.revision_id)
        with self.assertRaisesRegex(ValueError, "human-correctable claim kind"):
            HumanClaimCorrection(
                "derived_inference",
                "Derivación humana sin resultado.",
                snapshot.evidence_link_ids,
            )

    def test_noop_correction_is_rejected(self) -> None:
        snapshot = self.reader.prepare_claim_control(self.revision_id)
        correction = self._correction(snapshot, text=snapshot.text)
        with self.assertRaisesRegex(ClaimControlInvariantError, "materially change"):
            self.control.record(
                self._request("correct", snapshot, correction=correction), created_at=T2
            )

    def test_stale_snapshot_fails_after_evidence_change(self) -> None:
        snapshot = self.reader.prepare_claim_control(self.revision_id)
        old_evidence = snapshot.evidence_link_ids[0]
        con = local_connection(self.db)
        try:
            target_id, relation, rationale = con.execute(
                "SELECT representation_target_id,relation,rationale FROM evidence_links WHERE id=?",
                (old_evidence,),
            ).fetchone()
            con.execute(
                """
                INSERT INTO evidence_links(
                  id,supersedes_evidence_link_id,claim_revision_id,representation_target_id,
                  relation,origin_kind,process_run_id,lifecycle,rationale,created_at
                ) VALUES (?,?,?,?,?,'human',NULL,'active',?,?)
                """,
                (new_id("evl_"), old_evidence, self.revision_id, target_id, relation, rationale, T2),
            )
            con.commit()
        finally:
            con.close()
        with self.assertRaisesRegex(ClaimControlInvariantError, "snapshot is stale"):
            self.control.record(self._request("restrict", snapshot), created_at=T3)

    def test_restrict_unrestrict_and_retract_are_append_only_and_fts_safe(self) -> None:
        first = self.reader.prepare_claim_control(self.revision_id)
        restricted = self.control.record(self._request("restrict", first), created_at=T2)
        restricted_state = self.reader.claim_state(restricted.result_revision_id)
        self.assertEqual(restricted_state.lifecycle, "restricted")
        self.assertTrue(restricted_state.current)
        con = local_read_connection(self.db)
        try:
            self.assertEqual(con.execute("SELECT count(*) FROM claim_fts").fetchone()[0], 0)
        finally:
            con.close()

        second = self.reader.prepare_claim_control(restricted.result_revision_id)
        restored = self.control.record(self._request("unrestrict", second), created_at=T3)
        restored_state = self.reader.claim_state(restored.result_revision_id)
        self.assertEqual(restored_state.lifecycle, "active")
        con = local_read_connection(self.db)
        try:
            self.assertEqual(
                con.execute(
                    "SELECT claim_revision_id,text FROM claim_fts"
                ).fetchall(),
                [(restored.result_revision_id, first.text)],
            )
        finally:
            con.close()

        third = self.reader.prepare_claim_control(restored.result_revision_id)
        retracted = self.control.record(self._request("retract", third), created_at=T4)
        self.assertEqual(
            self.reader.claim_state(retracted.result_revision_id).lifecycle, "retracted"
        )
        con = local_read_connection(self.db)
        try:
            self.assertEqual(con.execute("SELECT count(*) FROM claim_fts").fetchone()[0], 0)
        finally:
            con.close()

    def test_restrict_removes_stale_fts_from_all_historical_revisions(self) -> None:
        first = self.reader.prepare_claim_control(self.revision_id)
        corrected = self.control.record(self._request("correct", first), created_at=T2)
        current = self.reader.prepare_claim_control(corrected.result_revision_id)

        # Simulate a stale/rebuilt retrieval row for the historical revision.
        # Restriction must remove the Claim's entire derived FTS footprint, not
        # merely the immediate source revision.
        con = local_connection(self.db)
        try:
            con.execute(
                "INSERT INTO claim_fts(claim_revision_id,text) VALUES (?,?)",
                (self.revision_id, first.text),
            )
            self.assertEqual(con.execute("SELECT count(*) FROM claim_fts").fetchone()[0], 2)
            con.commit()
        finally:
            con.close()

        restricted = self.control.record(self._request("restrict", current), created_at=T3)
        self.assertEqual(self.reader.claim_state(restricted.result_revision_id).lifecycle, "restricted")
        con = local_read_connection(self.db)
        try:
            self.assertEqual(con.execute("SELECT count(*) FROM claim_fts").fetchone()[0], 0)
        finally:
            con.close()

    def test_unrestrict_fails_while_underlying_evidence_custody_is_restricted(self) -> None:
        first = self.reader.prepare_claim_control(self.revision_id)
        restricted = self.control.record(self._request("restrict", first), created_at=T2)

        con = local_connection(self.db)
        try:
            con.execute(
                "UPDATE representations SET availability='restricted' WHERE id=?",
                (self.rep_id,),
            )
            artifact_id = con.execute(
                "SELECT artifact_id FROM representations WHERE id=?", (self.rep_id,)
            ).fetchone()[0]
            con.execute(
                "UPDATE artifacts SET availability='restricted' WHERE id=?",
                (artifact_id,),
            )
            con.commit()
        finally:
            con.close()

        current = self.reader.prepare_claim_control(restricted.result_revision_id)
        with self.assertRaisesRegex(
            ClaimControlInvariantError, "restricted or purged evidence custody"
        ):
            self.control.record(self._request("unrestrict", current), created_at=T3)

    def test_active_correction_revalidates_evidence_custody_inside_write(self) -> None:
        snapshot = self.reader.prepare_claim_control(self.revision_id)
        request = self._request("correct", snapshot)

        con = local_connection(self.db)
        try:
            con.execute(
                "UPDATE representations SET availability='restricted' WHERE id=?",
                (self.rep_id,),
            )
            con.commit()
        finally:
            con.close()

        with self.assertRaisesRegex(
            ClaimControlInvariantError, "restricted or purged evidence custody"
        ):
            self.control.record(request, created_at=T2)

    def test_lifecycle_actions_preserve_current_evidence_entity_and_tag_sets(self) -> None:
        snapshot = self.reader.prepare_claim_control(self.revision_id)
        receipt = self.control.record(self._request("restrict", snapshot), created_at=T2)
        self.assertEqual(len(receipt.evidence_link_ids), len(snapshot.evidence_link_ids))
        self.assertEqual(len(receipt.entity_link_ids), len(snapshot.entity_link_ids))
        self.assertEqual(len(receipt.tag_link_ids), len(snapshot.tag_link_ids))

    def test_exact_replay_is_idempotent_and_payload_collision_fails(self) -> None:
        snapshot = self.reader.prepare_claim_control(self.revision_id)
        request = self._request("restrict", snapshot)
        first = self.control.record(request, created_at=T2)
        second = self.control.record(request, created_at=T3)
        self.assertFalse(first.replayed)
        self.assertTrue(second.replayed)
        collision = ClaimRevisionControlRequest(
            request.source_revision_id,
            request.expected_snapshot_sha256,
            "different@example.test",
            request.action,
            rationale=request.rationale,
            claim_revision_action_id=request.claim_revision_action_id,
            result_revision_id=request.result_revision_id,
        )
        with self.assertRaises(ClaimControlIdentityCollision):
            self.control.record(collision, created_at=T4)

    def test_exact_replay_does_not_reauthorize_against_later_custody_state(self) -> None:
        snapshot = self.reader.prepare_claim_control(self.revision_id)
        request = self._request("correct", snapshot)
        first = self.control.record(request, created_at=T2)
        self.assertFalse(first.replayed)

        # A later custody restriction changes what a *new* active mutation may do,
        # but must not invalidate exact replay of the already-committed historical
        # correction.
        con = local_connection(self.db)
        try:
            con.execute(
                "UPDATE representations SET availability='restricted' WHERE id=?",
                (self.rep_id,),
            )
            con.commit()
        finally:
            con.close()

        replay = self.control.record(request, created_at=T3)
        self.assertTrue(replay.replayed)
        self.assertEqual(replay.result_revision_id, first.result_revision_id)
        self.assertEqual(replay.review_action_id, first.review_action_id)
        self.assertEqual(replay.claim_review_id, first.claim_review_id)

    def test_second_independent_action_against_superseded_source_fails(self) -> None:
        snapshot = self.reader.prepare_claim_control(self.revision_id)
        self.control.record(self._request("restrict", snapshot), created_at=T2)
        with self.assertRaisesRegex(ClaimControlInvariantError, "exact current revision"):
            self.control.record(self._request("restrict", snapshot), created_at=T3)

    def test_concurrent_identical_action_commits_once(self) -> None:
        snapshot = self.reader.prepare_claim_control(self.revision_id)
        request = self._request("restrict", snapshot)
        receipts = []
        errors = []

        def run():
            try:
                receipts.append(self.control.record(request, created_at=T2))
            except Exception as exc:  # pragma: no cover - diagnostic collection
                errors.append(exc)

        threads = [threading.Thread(target=run), threading.Thread(target=run)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(errors, [])
        self.assertEqual(len(receipts), 2)
        self.assertEqual({item.replayed for item in receipts}, {False, True})
        con = local_read_connection(self.db)
        try:
            self.assertEqual(
                con.execute("SELECT count(*) FROM claim_revision_actions").fetchone()[0], 1
            )
            self.assertEqual(
                con.execute("SELECT count(*) FROM claim_revisions WHERE claim_id=(SELECT claim_id FROM claim_revisions WHERE id=?)", (self.revision_id,)).fetchone()[0],
                2,
            )
        finally:
            con.close()

    def test_history_exposes_actor_action_and_current_revision(self) -> None:
        first = self.reader.prepare_claim_control(self.revision_id)
        corrected = self.control.record(
            self._request("correct", first, actor="alice", rationale="amount typo"),
            created_at=T2,
        )
        second = self.reader.prepare_claim_control(corrected.result_revision_id)
        restricted = self.control.record(
            self._request("restrict", second, actor="bob", rationale="privacy"),
            created_at=T3,
        )
        claim_id = self.reader.claim_state(restricted.result_revision_id).claim_id
        history = self.reader.claim_history(claim_id)
        self.assertEqual([item.revision_no for item in history], [1, 2, 3])
        self.assertEqual([item.action for item in history], [None, "correct", "restrict"])
        self.assertEqual([item.actor for item in history], [None, "alice", "bob"])
        self.assertEqual([item.current for item in history], [False, False, True])

    def test_correction_cannot_select_links_outside_exact_snapshot(self) -> None:
        snapshot = self.reader.prepare_claim_control(self.revision_id)
        correction = HumanClaimCorrection(
            snapshot.claim_kind,
            "El Concejo aprobó ₡5 millones para el camino.",
            (new_id("evl_"),),
            quantitative=True,
        )
        with self.assertRaisesRegex(ClaimControlInvariantError, "outside the exact prepared"):
            self.control.record(
                self._request("correct", snapshot, correction=correction), created_at=T2
            )


if __name__ == "__main__":
    unittest.main()
