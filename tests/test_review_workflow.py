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
    EvidenceDraft,
    LectorHost,
    LectorWriter,
    SemanticExtractionRequest,
    SemanticExtractorDescriptor,
    SemanticExtractorRegistry,
    SemanticResult,
    TargetRef,
)
from canario.persistence import database
from canario.processors import TargetRegistration, WorkbenchWriter
from canario.review import (
    BatchDecisionOverride,
    ClaimBatch,
    ClaimBatchReviewRequest,
    ClaimReviewActionRequest,
    ClaimReviewDraft,
    ReviewIdentityCollision,
    ReviewInvariantError,
    ReviewReader,
    ReviewWriter,
)

NO_RUNTIME_CHECK = lambda: None
T = "2026-08-27T04:00:00.000Z"
T2 = "2026-08-27T04:01:00.000Z"
T3 = "2026-08-27T04:02:00.000Z"


def local_connection(path: Path) -> sqlite3.Connection:
    return database._open_writable_v1(path, NO_RUNTIME_CHECK)


def local_read_connection(path: Path) -> sqlite3.Connection:
    return database._open_readonly_v1(path, NO_RUNTIME_CHECK)


class FixtureExtractor:
    def __init__(self, claims: tuple[ClaimDraft, ...]) -> None:
        self._descriptor = SemanticExtractorDescriptor(
            key="lector.review_fixture",
            capability_key="claim_extract",
            implementation_version="1",
            origin_kind="machine",
            execution_venue="local_deterministic",
            input_media_types=frozenset({"text/plain"}),
            input_representation_kinds=frozenset({"original"}),
            scope_kinds=frozenset({"whole", "text_quote"}),
        )
        self.claims = claims

    @property
    def descriptor(self):
        return self._descriptor

    def extract(self, _invocation):
        return SemanticResult("success", self.claims)


class ReviewWorkflowTests(unittest.TestCase):
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
        self.lector_writer = LectorWriter(
            self.db, self.archive, connection_factory=local_connection
        )
        self.review_writer = ReviewWriter(self.db, connection_factory=local_connection)
        self.review_reader = ReviewReader(
            self.db,
            self.archive,
            connection_factory=local_read_connection,
        )

        self.source = SourceRegistration(new_id("src_"), "web", "Municipalidad", True, T)
        self.deposit.register_source(self.source)
        self.locator = SourceLocatorRegistration(
            new_id("sloc_"), self.source.id, "https://example.test/acta", "http_url", T
        )
        self.deposit.register_source_locator(self.locator)
        self.text = (
            "El Concejo aprobó ₡25 millones para el camino. "
            "AyA coordinará las obras. "
            "La contratación iniciará en septiembre."
        )
        self.rep_id = self._capture(self.text.encode("utf-8"))
        self.whole = self._target(self.rep_id, "whole", "{}")
        self.claims = self._extract_claims()

        self.other_rep = self._capture(b"Otro documento sin relacion.")
        self.other_whole = self._target(self.other_rep, "whole", "{}")
        self.other_claim = self._extract_other_claim()

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

    def _quote_ref(self, exact: str) -> TargetRef:
        start = self.text.index(exact)
        return TargetRef.proposed(
            "text_quote",
            "v1",
            json.dumps(
                {"exact": exact, "start_char": start, "end_char": start + len(exact)}
            ),
        )

    def _extract_claims(self) -> tuple[str, ...]:
        snippets = (
            "El Concejo aprobó ₡25 millones para el camino.",
            "AyA coordinará las obras.",
            "La contratación iniciará en septiembre.",
        )
        drafts = tuple(
            ClaimDraft(
                f"c{index}",
                "source_assertion",
                snippet,
                (EvidenceDraft(self._quote_ref(snippet), "quotes", "active"),),
                quantitative="₡" in snippet,
            )
            for index, snippet in enumerate(snippets, start=1)
        )
        host = LectorHost(
            self.lector_writer,
            SemanticExtractorRegistry((FixtureExtractor(drafts),)),
        )
        receipt = host.run_attempt(
            SemanticExtractionRequest(self.rep_id, (self.whole,), "claim_extract")
        )
        return tuple(item.revision_id for item in receipt.claims)

    def _extract_other_claim(self) -> str:
        exact = "Otro documento sin relacion."
        draft = ClaimDraft(
            "other",
            "source_assertion",
            exact,
            (
                EvidenceDraft(
                    TargetRef.proposed(
                        "text_quote",
                        "v1",
                        json.dumps(
                            {"exact": exact, "start_char": 0, "end_char": len(exact)}
                        ),
                    ),
                    "quotes",
                    "active",
                ),
            ),
        )
        host = LectorHost(
            self.lector_writer,
            SemanticExtractorRegistry((FixtureExtractor((draft,)),)),
        )
        receipt = host.run_attempt(
            SemanticExtractionRequest(self.other_rep, (self.other_whole,), "claim_extract")
        )
        return receipt.claims[0].revision_id

    def _con(self) -> sqlite3.Connection:
        return local_connection(self.db)

    def test_batch_fingerprint_binds_representation_and_selection_policy(self) -> None:
        first = ClaimBatch(self.rep_id, self.claims[:2])
        other = ClaimBatch(self.other_rep, self.claims[:2])
        self.assertNotEqual(first.subject_set_sha256, other.subject_set_sha256)
        self.assertEqual(
            first.subject_set_sha256,
            ClaimBatch.compute_sha256(
                self.rep_id,
                self.claims[:2],
                first.selection_policy_key,
                first.selection_policy_version,
            ),
        )

    def test_contracts_reject_duplicate_subjects_and_out_of_batch_exception(self) -> None:
        with self.assertRaisesRegex(ValueError, "repeat"):
            ClaimReviewActionRequest(
                "isaac",
                "batch",
                (
                    ClaimReviewDraft(self.claims[0], "accepted"),
                    ClaimReviewDraft(self.claims[0], "rejected"),
                ),
            )
        batch = ClaimBatch(self.rep_id, self.claims[:2])
        with self.assertRaisesRegex(ValueError, "outside"):
            ClaimBatchReviewRequest(
                batch,
                "isaac",
                "accepted",
                (BatchDecisionOverride(self.other_claim, "rejected"),),
            )

    def test_prepare_batch_is_deterministic_representation_scoped_and_read_only(self) -> None:
        before = self._count_reviews()
        first = self.review_reader.prepare_claim_batch(self.rep_id)
        second = self.review_reader.prepare_claim_batch(self.rep_id)
        self.assertEqual(first.claim_revision_ids, self.claims)
        self.assertEqual(first, second)
        self.assertNotIn(self.other_claim, first.claim_revision_ids)
        self.assertEqual(self._count_reviews(), before)

    def test_batch_action_persists_one_action_with_default_and_exception(self) -> None:
        batch = self.review_reader.prepare_claim_batch(self.rep_id)
        request = ClaimBatchReviewRequest(
            batch,
            "isaac",
            "accepted",
            (BatchDecisionOverride(self.claims[1], "needs_work", "Verificar atribución"),),
            note="Primera pasada",
        )
        receipt = self.review_writer.record_claim_batch(request, created_at=T2)
        self.assertFalse(receipt.replayed)
        self.assertEqual(receipt.mode, "batch")
        self.assertEqual(set(receipt.claim_revision_ids), set(self.claims))
        con = self._con()
        try:
            self.assertEqual(
                con.execute(
                    "SELECT count(*) FROM review_actions WHERE id=?",
                    (request.review_action_id,),
                ).fetchone()[0],
                1,
            )
            rows = con.execute(
                """
                SELECT claim_revision_id,decision,reason,reviewer
                FROM claim_reviews WHERE review_action_id=? ORDER BY claim_revision_id
                """,
                (request.review_action_id,),
            ).fetchall()
        finally:
            con.close()
        by_revision = {row[0]: row[1:] for row in rows}
        self.assertEqual(by_revision[self.claims[0]][0], "accepted")
        self.assertEqual(by_revision[self.claims[1]], ("needs_work", "Verificar atribución", "isaac"))
        self.assertEqual(by_revision[self.claims[2]][0], "accepted")

    def test_exact_action_replays_and_payload_collision_fails(self) -> None:
        request = ClaimReviewActionRequest(
            "isaac",
            "supervised",
            (ClaimReviewDraft(self.claims[0], "accepted"),),
        )
        first = self.review_writer.record_claim_reviews(request, created_at=T2)
        second = self.review_writer.record_claim_reviews(request, created_at=T3)
        self.assertFalse(first.replayed)
        self.assertTrue(second.replayed)
        self.assertEqual(first.claim_review_ids, second.claim_review_ids)
        with self.assertRaises(ReviewIdentityCollision):
            self.review_writer.record_claim_reviews(
                ClaimReviewActionRequest(
                    "isaac",
                    "supervised",
                    (ClaimReviewDraft(self.claims[0], "rejected"),),
                    review_action_id=request.review_action_id,
                ),
                created_at=T3,
            )

    def test_review_state_is_machine_only_until_human_decision_and_strict_ready_only_when_accepted(self) -> None:
        initial = self.review_reader.claim_state(self.claims[0])
        self.assertTrue(initial.machine_only)
        self.assertFalse(initial.human_reviewed)
        self.assertFalse(initial.strict_ready)
        self.review_writer.record_claim_reviews(
            ClaimReviewActionRequest(
                "isaac",
                "strict",
                (ClaimReviewDraft(self.claims[0], "accepted"),),
            ),
            created_at=T2,
        )
        accepted = self.review_reader.claim_state(self.claims[0])
        self.assertFalse(accepted.machine_only)
        self.assertTrue(accepted.human_reviewed)
        self.assertTrue(accepted.strict_ready)

    def test_latest_decision_is_derived_without_mutating_claim_lifecycle(self) -> None:
        self.review_writer.record_claim_reviews(
            ClaimReviewActionRequest(
                "isaac",
                "supervised",
                (ClaimReviewDraft(self.claims[0], "accepted"),),
            ),
            created_at=T2,
        )
        self.review_writer.record_claim_reviews(
            ClaimReviewActionRequest(
                "isaac",
                "supervised",
                (ClaimReviewDraft(self.claims[0], "needs_work", "Nueva duda"),),
            ),
            created_at=T3,
        )
        state = self.review_reader.claim_state(self.claims[0])
        self.assertEqual(state.latest_decision, "needs_work")
        self.assertEqual(state.latest_reason, "Nueva duda")
        self.assertEqual(state.lifecycle, "active")
        self.assertFalse(state.strict_ready)

    def test_completed_claims_leave_batch_while_needs_work_remains(self) -> None:
        self.review_writer.record_claim_reviews(
            ClaimReviewActionRequest(
                "isaac",
                "batch",
                (
                    ClaimReviewDraft(self.claims[0], "accepted"),
                    ClaimReviewDraft(self.claims[1], "rejected"),
                    ClaimReviewDraft(self.claims[2], "needs_work"),
                ),
            ),
            created_at=T2,
        )
        batch = self.review_reader.prepare_claim_batch(self.rep_id)
        self.assertEqual(batch.claim_revision_ids, (self.claims[2],))
        without_needs_work = self.review_reader.prepare_claim_batch(
            self.rep_id, include_needs_work=False
        )
        self.assertEqual(without_needs_work.claim_revision_ids, ())

    def test_batch_stale_guard_rejects_superseded_claim_revision(self) -> None:
        batch = self.review_reader.prepare_claim_batch(self.rep_id)
        stale = self.claims[0]
        con = self._con()
        try:
            row = con.execute(
                """
                SELECT claim_id,revision_no,claim_kind,text,derivation_result_target_id,
                       attribution_entity_id,attribution_text,temporal_start,temporal_end,
                       sensitive,quantitative,lifecycle
                FROM claim_revisions WHERE id=?
                """,
                (stale,),
            ).fetchone()
            successor = new_id("clrev_")
            con.execute(
                """
                INSERT INTO claim_revisions(
                  id,claim_id,revision_no,supersedes_revision_id,claim_kind,text,
                  origin_kind,process_run_id,derivation_result_target_id,attribution_entity_id,
                  attribution_text,temporal_start,temporal_end,sensitive,quantitative,lifecycle,created_at
                ) VALUES (?,?,?,?,?,?, 'human',NULL,?,?,?,?,?,?,?,?,?)
                """,
                (
                    successor,
                    row[0],
                    row[1] + 1,
                    stale,
                    row[2],
                    row[3],
                    row[4],
                    row[5],
                    row[6],
                    row[7],
                    row[8],
                    row[9],
                    row[10],
                    row[11],
                    T2,
                ),
            )
            con.commit()
        finally:
            con.close()
        with self.assertRaisesRegex(ReviewInvariantError, "current"):
            self.review_writer.record_claim_batch(
                ClaimBatchReviewRequest(batch, "isaac", "accepted"),
                created_at=T3,
            )
        self.assertEqual(self._count_reviews(), 0)


    def test_batch_stale_guard_rejects_subject_whose_current_evidence_moves_off_representation(self) -> None:
        batch = self.review_reader.prepare_claim_batch(self.rep_id)
        revision_id = self.claims[0]
        con = self._con()
        try:
            old = con.execute(
                """
                SELECT e.id,e.relation,e.rationale
                FROM evidence_links e
                WHERE e.claim_revision_id=? AND e.lifecycle='active'
                ORDER BY e.id LIMIT 1
                """,
                (revision_id,),
            ).fetchone()
            replacement = new_id("evl_")
            con.execute(
                """
                INSERT INTO evidence_links(
                  id,supersedes_evidence_link_id,claim_revision_id,representation_target_id,
                  relation,origin_kind,process_run_id,lifecycle,rationale,created_at
                ) VALUES (?,?,?,?,?,'human',NULL,'active',?,?)
                """,
                (replacement, old[0], revision_id, self.other_whole, old[1], old[2], T2),
            )
            con.commit()
        finally:
            con.close()
        with self.assertRaisesRegex(ReviewInvariantError, "prepared Representation"):
            self.review_writer.record_claim_batch(
                ClaimBatchReviewRequest(batch, "isaac", "accepted"),
                created_at=T3,
            )
        self.assertEqual(self._count_reviews(), 0)

    def test_open_claim_reopens_exact_text_evidence(self) -> None:
        exact = self.text.split(" AyA")[0]
        revision_id = self._revision_for_text(exact)
        detail = self.review_reader.open_claim(revision_id)
        self.assertEqual(detail.claim.text, exact)
        self.assertEqual(len(detail.evidence), 1)
        preview = detail.evidence[0]
        self.assertEqual(preview.selector_kind, "text_quote")
        self.assertEqual(preview.preview["exact"], detail.claim.text)
        self.assertEqual(preview.relation, "quotes")

    def test_tampered_archive_blocks_review_evidence_open(self) -> None:
        con = self._con()
        try:
            row = con.execute(
                """
                SELECT ao.storage_key
                FROM evidence_links e
                JOIN representation_targets t ON t.id=e.representation_target_id
                JOIN representations r ON r.id=t.representation_id
                JOIN artifacts a ON a.id=r.artifact_id
                JOIN archive_objects ao ON ao.id=CASE WHEN r.kind='original' THEN a.archive_object_id ELSE r.archive_object_id END
                WHERE e.claim_revision_id=?
                """,
                (self.claims[0],),
            ).fetchone()
        finally:
            con.close()
        path = self.archive / row[0]
        path.write_bytes(b"tampered")
        with self.assertRaises(Exception):
            self.review_reader.open_claim(self.claims[0])

    def test_concurrent_same_action_commits_once_and_other_replays(self) -> None:
        request = ClaimReviewActionRequest(
            "isaac",
            "supervised",
            (ClaimReviewDraft(self.claims[0], "accepted"),),
        )
        barrier = threading.Barrier(2)
        receipts = []
        errors = []

        def worker():
            try:
                barrier.wait()
                receipts.append(self.review_writer.record_claim_reviews(request, created_at=T2))
            except Exception as exc:  # pragma: no cover - failure details are asserted below
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(errors, [])
        self.assertEqual(len(receipts), 2)
        self.assertEqual(sorted(item.replayed for item in receipts), [False, True])
        self.assertEqual(self._count_reviews(), 1)

    def _revision_for_text(self, text: str) -> str:
        con = self._con()
        try:
            row = con.execute(
                "SELECT id FROM claim_revisions WHERE text=?", (text,)
            ).fetchone()
            assert row is not None
            return row[0]
        finally:
            con.close()

    def _count_reviews(self) -> int:
        con = self._con()
        try:
            return con.execute("SELECT count(*) FROM claim_reviews").fetchone()[0]
        finally:
            con.close()


if __name__ == "__main__":
    unittest.main()
