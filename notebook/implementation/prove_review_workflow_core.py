#!/usr/bin/env python3
"""Natural end-to-end proof for REVIEW-001 claim review workflow core."""

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
from canario.persistence import ensure_schema_v1, open_readonly_v1
from canario.processors import (
    ProcessingRequest,
    ProcessorRegistry,
    TargetRegistration,
    WorkbenchHost,
    WorkbenchWriter,
)
from canario.processors.poppler import PopplerPdfTextProcessor
from canario.review import ClaimBatchReviewRequest, ReviewReader, ReviewWriter

ESPARZA_SHA256 = "ffb354c67d8b56ebf265884c820a98fee27015cadaac3ea1011069f7969b8bfd"
ESPARZA_BYTES = 760485
ESPARZA_PAGE = 4
ESPARZA_URL = (
    "https://muniesparza.go.cr/files/folder/"
    "e0256fdf-3714-40f5-ae10-aff18f0ca95e.pdf"
)
REQUIRED_EXACT = "Comité Cantonal de la Persona Joven de Esparza"


class _ControlledReviewClaimExtractor:
    """Controlled machine claim: REVIEW-001 proves review, not extraction quality."""

    def __init__(self, claim: ClaimDraft) -> None:
        self.claim = claim
        self._descriptor = SemanticExtractorDescriptor(
            key="review.proof_controlled_claim",
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
            "REVIEW_WORKFLOW_CORE_PROOF=FAIL natural source identity mismatch "
            f"bytes={len(source_bytes)} sha256={observed_sha}"
        )

    poppler = PopplerPdfTextProcessor.discover()

    with tempfile.TemporaryDirectory(prefix="canario-review-proof-") as tempdir:
        root = Path(tempdir)
        db = root / "canario.sqlite3"
        archive = root / "archive"
        ensure_schema_v1(db)
        deposit = DepositWriter(db, archive)
        workbench_writer = WorkbenchWriter(db, archive)
        lector_writer = LectorWriter(db, archive)
        review_writer = ReviewWriter(db)
        review_reader = ReviewReader(db, archive)

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
            "review_workflow_core_proof",
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
            raise SystemExit("REVIEW_WORKFLOW_CORE_PROOF=FAIL Poppler extraction failed")
        if [item.decision for item in processor_receipt.decisions] != ["accept"]:
            raise SystemExit("REVIEW_WORKFLOW_CORE_PROOF=FAIL Poppler output not accepted")

        extracted = processor_receipt.outputs[0]
        extracted_rep = extracted.representation_id
        extracted_text = workbench_writer.archive.path_for_key(extracted.storage_key).read_text(
            "utf-8"
        )
        if extracted_text.count(REQUIRED_EXACT) != 1:
            raise SystemExit(
                "REVIEW_WORKFLOW_CORE_PROOF=FAIL required natural evidence is not unique"
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
        claim = ClaimDraft(
            "natural_review_claim",
            "source_assertion",
            "La página menciona al Comité Cantonal de la Persona Joven de Esparza.",
            (EvidenceDraft(evidence_ref, "supports", "active"),),
        )
        lector_receipt = LectorHost(
            lector_writer,
            SemanticExtractorRegistry((_ControlledReviewClaimExtractor(claim),)),
        ).run_attempt(
            SemanticExtractionRequest(extracted_rep, (whole_target,), "claim_extract")
        )
        if lector_receipt.outcome != "success" or len(lector_receipt.claims) != 1:
            raise SystemExit("REVIEW_WORKFLOW_CORE_PROOF=FAIL controlled Claim creation failed")
        revision_id = lector_receipt.claims[0].revision_id

        before = review_reader.claim_state(revision_id)
        if not before.machine_only or before.human_reviewed or before.strict_ready:
            raise SystemExit("REVIEW_WORKFLOW_CORE_PROOF=FAIL initial review state is dishonest")
        detail = review_reader.open_claim(revision_id)
        if len(detail.evidence) != 1 or detail.evidence[0].preview.get("exact") != REQUIRED_EXACT:
            raise SystemExit("REVIEW_WORKFLOW_CORE_PROOF=FAIL exact evidence did not reopen")
        batch = review_reader.prepare_claim_batch(extracted_rep)
        if batch.claim_revision_ids != (revision_id,):
            raise SystemExit("REVIEW_WORKFLOW_CORE_PROOF=FAIL deterministic batch membership mismatch")

        review_receipt = review_writer.record_claim_batch(
            ClaimBatchReviewRequest(
                batch,
                "review-proof-operator",
                "accepted",
                note="REVIEW-001 natural proof",
            ),
            created_at=utc_now(),
        )
        after = review_reader.claim_state(revision_id)
        if not after.human_reviewed or after.latest_decision != "accepted" or not after.strict_ready:
            raise SystemExit("REVIEW_WORKFLOW_CORE_PROOF=FAIL accepted Claim is not strict-ready")

        con = open_readonly_v1(db)
        try:
            counts = {
                "review_actions": _count(con, "review_actions"),
                "claim_reviews": _count(con, "claim_reviews"),
            }
        finally:
            con.close()
        if counts != {"review_actions": 1, "claim_reviews": 1}:
            raise SystemExit("REVIEW_WORKFLOW_CORE_PROOF=FAIL review rows mismatch")

        report = {
            "format": "canario.review_workflow_core_proof.v1",
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
            "claim_revision_id": revision_id,
            "before": {
                "machine_only": before.machine_only,
                "human_reviewed": before.human_reviewed,
                "strict_ready": before.strict_ready,
            },
            "evidence": {
                "selector_kind": detail.evidence[0].selector_kind,
                "exact": detail.evidence[0].preview["exact"],
            },
            "batch": {
                "subject_count": len(batch.claim_revision_ids),
                "subject_set_sha256": batch.subject_set_sha256,
            },
            "review": {
                "review_action_id": review_receipt.review_action_id,
                "decision": after.latest_decision,
                "strict_ready": after.strict_ready,
            },
            "persistence": counts,
        }
        if args.result is not None:
            args.result.parent.mkdir(parents=True, exist_ok=True)
            args.result.write_text(
                json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
            )
        print("REVIEW_WORKFLOW_CORE_PROOF=PASS")
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
