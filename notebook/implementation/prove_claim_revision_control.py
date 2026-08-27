#!/usr/bin/env python3
"""Natural end-to-end proof for REVIEW-002 human ClaimRevision control."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from canario.deposit import (
    AcquisitionObservation,
    AcquisitionWrite,
    CapturedArtifact,
    DepositWriter,
    SourceLocatorRegistration,
    SourceRegistration,
    new_id,
    utc_now,
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
from canario.persistence import ensure_schema_v1, open_readonly_v1, open_writable_v1
from canario.processors import (
    ProcessingRequest,
    ProcessorRegistry,
    TargetRegistration,
    WorkbenchHost,
    WorkbenchWriter,
)
from canario.processors.poppler import PopplerPdfTextProcessor
from canario.review import (
    ClaimControlWriter,
    ClaimRevisionControlRequest,
    ClaimReviewActionRequest,
    ClaimReviewDraft,
    HumanClaimCorrection,
    ReviewReader,
    ReviewWriter,
)

ESPARZA_SHA256 = "ffb354c67d8b56ebf265884c820a98fee27015cadaac3ea1011069f7969b8bfd"
ESPARZA_BYTES = 760485
ESPARZA_PAGE = 4
ESPARZA_URL = (
    "https://muniesparza.go.cr/files/folder/"
    "e0256fdf-3714-40f5-ae10-aff18f0ca95e.pdf"
)
REQUIRED_EXACT = "Comité Cantonal de la Persona Joven de Esparza"
WRONG_CLAIM = "La página menciona al Comité Cantonal de la Persona Joven de Esparta."
CORRECTED_CLAIM = "La página menciona al Comité Cantonal de la Persona Joven de Esparza."


class _ControlledIncorrectClaimExtractor:
    """Deliberately wrong Claim: proof exercises correction, not extraction quality."""

    def __init__(self, claim: ClaimDraft) -> None:
        self.claim = claim
        self._descriptor = SemanticExtractorDescriptor(
            key="review.claim_control_proof_fixture",
            capability_key="claim_extract",
            implementation_version="1",
            origin_kind="machine",
            execution_venue="local_deterministic",
            input_media_types=frozenset({"text/plain"}),
            input_representation_kinds=frozenset({"extracted_text"}),
            scope_kinds=frozenset({"whole", "text_quote"}),
        )

    @property
    def descriptor(self) -> SemanticExtractorDescriptor:
        return self._descriptor

    def extract(self, _invocation) -> SemanticResult:
        return SemanticResult("success", (self.claim,))


def _count(con, table: str) -> int:
    return con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--natural-esparza", type=Path, required=True)
    parser.add_argument("--result", type=Path)
    args = parser.parse_args()

    source_bytes = args.natural_esparza.read_bytes()
    observed_sha = hashlib.sha256(source_bytes).hexdigest()
    if len(source_bytes) != ESPARZA_BYTES or observed_sha != ESPARZA_SHA256:
        raise SystemExit(
            "CLAIM_REVISION_CONTROL_PROOF=FAIL natural source identity mismatch "
            f"bytes={len(source_bytes)} sha256={observed_sha}"
        )

    poppler = PopplerPdfTextProcessor.discover()

    with tempfile.TemporaryDirectory(prefix="canario-claim-control-proof-") as tempdir:
        root = Path(tempdir)
        db = root / "canario.sqlite3"
        archive = root / "archive"
        ensure_schema_v1(db)
        deposit = DepositWriter(db, archive)
        workbench_writer = WorkbenchWriter(db, archive)
        lector_writer = LectorWriter(db, archive)
        review_writer = ReviewWriter(db)
        review_reader = ReviewReader(db, archive)
        control_writer = ClaimControlWriter(db)

        now = utc_now()
        source = SourceRegistration(new_id("src_"), "web", "Esparza Acta 161", True, now)
        deposit.register_source(source)
        locator = SourceLocatorRegistration(
            new_id("sloc_"), source.id, ESPARZA_URL, "http_url", now
        )
        deposit.register_source_locator(locator)
        original_rep = new_id("rep_")
        artifact = CapturedArtifact(
            new_id("art_"),
            new_id("aob_"),
            original_rep,
            source_bytes,
            "primary",
            args.natural_esparza.name,
            ESPARZA_URL,
            "application/pdf",
            "verified",
            "available",
            "es",
            None,
            now,
        )
        observation = AcquisitionObservation(
            new_id("acq_"),
            source.id,
            locator.id,
            now,
            "success",
            200,
            "claim_revision_control_proof",
            "v1",
            None,
            now,
        )
        deposit.record_acquisition(AcquisitionWrite(observation, (artifact,)))

        page_target = new_id("rtgt_")
        workbench_writer.register_target(
            TargetRegistration(
                page_target,
                original_rep,
                "pdf_page",
                "v1",
                json.dumps({"page_ordinal": ESPARZA_PAGE}, separators=(",", ":")),
                now,
            )
        )
        processor_receipt = WorkbenchHost(
            workbench_writer, ProcessorRegistry((poppler,))
        ).run_attempt(
            ProcessingRequest(
                original_rep,
                (page_target,),
                "text_extract",
                poppler.configuration_hash,
            )
        )
        if processor_receipt.outcome != "success" or len(processor_receipt.outputs) != 1:
            raise SystemExit("CLAIM_REVISION_CONTROL_PROOF=FAIL Poppler extraction failed")
        if [item.decision for item in processor_receipt.decisions] != ["accept"]:
            raise SystemExit("CLAIM_REVISION_CONTROL_PROOF=FAIL Poppler output not accepted")

        extracted = processor_receipt.outputs[0]
        extracted_rep = extracted.representation_id
        extracted_text = workbench_writer.archive.path_for_key(extracted.storage_key).read_text(
            "utf-8"
        )
        if extracted_text.count(REQUIRED_EXACT) != 1:
            raise SystemExit(
                "CLAIM_REVISION_CONTROL_PROOF=FAIL required natural evidence is not unique"
            )
        start = extracted_text.index(REQUIRED_EXACT)
        end = start + len(REQUIRED_EXACT)

        whole_target = new_id("rtgt_")
        workbench_writer.register_target(
            TargetRegistration(whole_target, extracted_rep, "whole", "v1", "{}", now)
        )
        evidence_ref = TargetRef.proposed(
            "text_quote",
            "v1",
            json.dumps(
                {"exact": REQUIRED_EXACT, "start_char": start, "end_char": end},
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        controlled = ClaimDraft(
            "incorrect_machine_claim",
            "source_assertion",
            WRONG_CLAIM,
            (EvidenceDraft(evidence_ref, "quotes", "active"),),
        )
        lector_receipt = LectorHost(
            lector_writer,
            SemanticExtractorRegistry((_ControlledIncorrectClaimExtractor(controlled),)),
        ).run_attempt(
            SemanticExtractionRequest(extracted_rep, (whole_target,), "claim_extract")
        )
        if lector_receipt.outcome != "success" or len(lector_receipt.claims) != 1:
            raise SystemExit(
                "CLAIM_REVISION_CONTROL_PROOF=FAIL controlled machine Claim creation failed"
            )
        old_revision_id = lector_receipt.claims[0].revision_id

        # Seed the disposable FTS projection as if a normal rebuild had indexed the
        # current active Claim. REVIEW-002 must remove this stale text transactionally.
        con = open_writable_v1(db)
        try:
            con.execute(
                "INSERT INTO claim_fts(claim_revision_id,text) VALUES (?,?)",
                (old_revision_id, WRONG_CLAIM),
            )
            con.commit()
        finally:
            con.close()

        review_writer.record_claim_reviews(
            ClaimReviewActionRequest(
                "review-proof-operator",
                "supervised",
                (ClaimReviewDraft(old_revision_id, "needs_work", "controlled typo"),),
                note="REVIEW-002 old revision needs correction",
            ),
            created_at=utc_now(),
        )
        old_before = review_reader.claim_state(old_revision_id)
        if (
            not old_before.current
            or not old_before.human_reviewed
            or old_before.latest_decision != "needs_work"
            or old_before.strict_ready
        ):
            raise SystemExit(
                "CLAIM_REVISION_CONTROL_PROOF=FAIL old revision review state mismatch"
            )
        detail = review_reader.open_claim(old_revision_id)
        if len(detail.evidence) != 1 or detail.evidence[0].preview.get("exact") != REQUIRED_EXACT:
            raise SystemExit("CLAIM_REVISION_CONTROL_PROOF=FAIL exact evidence did not reopen")

        snapshot = review_reader.prepare_claim_control(old_revision_id)
        correction = HumanClaimCorrection(
            snapshot.claim_kind,
            CORRECTED_CLAIM,
            snapshot.evidence_link_ids,
            entity_link_ids=snapshot.entity_link_ids,
            tag_link_ids=snapshot.tag_link_ids,
            attribution_entity_id=snapshot.attribution_entity_id,
            attribution_text=snapshot.attribution_text,
            temporal_start=snapshot.temporal_start,
            temporal_end=snapshot.temporal_end,
            sensitive=snapshot.sensitive,
            quantitative=snapshot.quantitative,
        )
        request = ClaimRevisionControlRequest(
            old_revision_id,
            snapshot.snapshot_sha256,
            "review-proof-operator",
            "correct",
            correction=correction,
            rationale="Correct controlled Esparza typo from retained evidence",
        )
        control_receipt = control_writer.record(request, created_at=utc_now())
        new_revision_id = control_receipt.result_revision_id

        old_after = review_reader.claim_state(old_revision_id)
        final_state = review_reader.claim_state(new_revision_id)
        if old_after.current or old_after.strict_ready:
            raise SystemExit(
                "CLAIM_REVISION_CONTROL_PROOF=FAIL superseded revision remained current/strict-ready"
            )
        if (
            not final_state.current
            or final_state.origin_kind != "human"
            or not final_state.human_reviewed
            or final_state.unreviewed_human
            or final_state.latest_decision != "accepted"
            or final_state.latest_reviewer != "review-proof-operator"
            or not final_state.strict_ready
            or final_state.text != CORRECTED_CLAIM
        ):
            raise SystemExit(
                "CLAIM_REVISION_CONTROL_PROOF=FAIL correction did not atomically produce an accepted human revision"
            )
        if control_receipt.review_action_id != request.review_action_id or control_receipt.claim_review_id is None:
            raise SystemExit(
                "CLAIM_REVISION_CONTROL_PROOF=FAIL correction acceptance receipt missing"
            )

        history = review_reader.claim_history(final_state.claim_id)
        if len(history) != 2:
            raise SystemExit("CLAIM_REVISION_CONTROL_PROOF=FAIL correction history length mismatch")
        if history[0].current or not history[1].current:
            raise SystemExit("CLAIM_REVISION_CONTROL_PROOF=FAIL correction lineage current marker mismatch")
        if history[1].action != "correct" or history[1].actor != "review-proof-operator":
            raise SystemExit("CLAIM_REVISION_CONTROL_PROOF=FAIL correction actor/action missing")

        con = open_readonly_v1(db)
        try:
            counts = {
                "claim_revisions": _count(con, "claim_revisions"),
                "claim_revision_actions": _count(con, "claim_revision_actions"),
                "review_actions": _count(con, "review_actions"),
                "claim_reviews": _count(con, "claim_reviews"),
            }
            fts_rows = con.execute(
                "SELECT claim_revision_id,text FROM claim_fts ORDER BY claim_revision_id"
            ).fetchall()
            action_row = con.execute(
                """
                SELECT action,actor,rationale,review_action_id,request_sha256
                FROM claim_revision_actions WHERE id=?
                """,
                (control_receipt.claim_revision_action_id,),
            ).fetchone()
        finally:
            con.close()
        if counts != {
            "claim_revisions": 2,
            "claim_revision_actions": 1,
            "review_actions": 2,
            "claim_reviews": 2,
        }:
            raise SystemExit("CLAIM_REVISION_CONTROL_PROOF=FAIL persistence counts mismatch")
        if fts_rows != [(new_revision_id, CORRECTED_CLAIM)]:
            raise SystemExit("CLAIM_REVISION_CONTROL_PROOF=FAIL FTS supersession/rebuild mismatch")
        if (
            action_row is None
            or action_row[3] != request.review_action_id
            or action_row[4] != request.request_sha256()
        ):
            raise SystemExit("CLAIM_REVISION_CONTROL_PROOF=FAIL action/review request identity mismatch")
        con = open_readonly_v1(db)
        try:
            correction_review = con.execute(
                """
                SELECT decision,reviewer,reason
                FROM claim_reviews
                WHERE id=? AND review_action_id=? AND claim_revision_id=?
                """,
                (control_receipt.claim_review_id, request.review_action_id, new_revision_id),
            ).fetchone()
        finally:
            con.close()
        if correction_review != (
            "accepted",
            "review-proof-operator",
            "Correct controlled Esparza typo from retained evidence",
        ):
            raise SystemExit("CLAIM_REVISION_CONTROL_PROOF=FAIL atomic correction acceptance mismatch")

        report = {
            "format": "canario.claim_revision_control_proof.v2",
            "status": "PASS",
            "source": {
                "sha256": observed_sha,
                "bytes": len(source_bytes),
                "page": ESPARZA_PAGE,
            },
            "poppler_version": poppler.descriptor.implementation_version,
            "poppler_configuration_hash": poppler.configuration_hash,
            "extracted_representation_id": extracted_rep,
            "extracted_representation_sha256": extracted.content_sha256,
            "old_revision": {
                "id": old_revision_id,
                "text": WRONG_CLAIM,
                "review_decision": old_after.latest_decision,
                "current_after_correction": old_after.current,
                "strict_ready_after_correction": old_after.strict_ready,
            },
            "evidence": {
                "selector_kind": detail.evidence[0].selector_kind,
                "exact": detail.evidence[0].preview["exact"],
            },
            "correction": {
                "action_id": control_receipt.claim_revision_action_id,
                "request_sha256": control_receipt.request_sha256,
                "actor": action_row[1],
                "action": action_row[0],
                "rationale": action_row[2],
                "result_revision_id": new_revision_id,
                "result_text": CORRECTED_CLAIM,
                "review_inherited": False,
                "review_action_id": control_receipt.review_action_id,
                "claim_review_id": control_receipt.claim_review_id,
                "accepted_atomically": final_state.latest_decision == "accepted",
            },
            "final": {
                "human_reviewed": final_state.human_reviewed,
                "strict_ready": final_state.strict_ready,
                "latest_decision": final_state.latest_decision,
            },
            "history": [
                {
                    "revision_no": item.revision_no,
                    "revision_id": item.claim_revision_id,
                    "current": item.current,
                    "action": item.action,
                    "actor": item.actor,
                }
                for item in history
            ],
            "fts_rows": fts_rows,
            "persistence": counts,
        }
        if args.result is not None:
            args.result.parent.mkdir(parents=True, exist_ok=True)
            args.result.write_text(
                json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
            )
        print("CLAIM_REVISION_CONTROL_PROOF=PASS")
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
