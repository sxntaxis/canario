#!/usr/bin/env python3
"""Target-runtime proof for PROCESSOR-DIRECT-001 using the production Workbench path."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from actakit.deposit import (
    AcquisitionObservation,
    AcquisitionWrite,
    CapturedArtifact,
    DepositWriter,
    SourceLocatorRegistration,
    SourceRegistration,
    new_id,
    utc_now,
)
from actakit.persistence import ensure_schema_v1
from actakit.processors import (
    ProcessingRequest,
    ProcessorRegistry,
    TargetRegistration,
    WorkbenchHost,
    WorkbenchWriter,
)
from actakit.processors.poppler import PopplerPdfTextProcessor

ROOT = Path(__file__).resolve().parents[2]
TSE_PDF = ROOT / "notebook/research/pre-sql/fixtures/artifact-proofs/alcaldias_pu.pdf"
TSE_TRUTH = (
    ROOT
    / "notebook/research/workbench/processors/bench/ground_truth/tse-esparza-alcaldias-p2.json"
)
ESPARZA_TRUTH = (
    ROOT
    / "notebook/research/workbench/processors/bench/ground_truth/natural-layout/esparza-p4.json"
)


def _normalize(text: str) -> str:
    return " ".join(text.split())


def _prove_pdf(
    *,
    pdf_bytes: bytes,
    page_ordinal: int,
    source_url: str,
    truth: dict,
    processor: PopplerPdfTextProcessor,
) -> None:
    with tempfile.TemporaryDirectory(prefix="actakit-direct-proof-") as tempdir:
        root = Path(tempdir)
        db = root / "actakit.sqlite3"
        archive = root / "archive"
        ensure_schema_v1(db)
        deposit = DepositWriter(db, archive)
        writer = WorkbenchWriter(db, archive)
        now = utc_now()
        source = SourceRegistration(new_id("src_"), "web", truth["fixture_id"], True, now)
        deposit.register_source(source)
        locator = SourceLocatorRegistration(
            new_id("sloc_"), source.id, source_url, "http_url", now
        )
        deposit.register_source_locator(locator)
        rep_id = new_id("rep_")
        artifact = CapturedArtifact(
            new_id("art_"),
            new_id("aob_"),
            rep_id,
            pdf_bytes,
            "primary",
            "proof.pdf",
            source_url,
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
            "processor_direct_001_proof",
            "v1",
            None,
            now,
        )
        deposit.record_acquisition(AcquisitionWrite(observation, (artifact,)))

        target_id = new_id("rtgt_")
        writer.register_target(
            TargetRegistration(
                target_id,
                rep_id,
                "pdf_page",
                "v1",
                json.dumps({"page_ordinal": page_ordinal}, separators=(",", ":")),
                now,
            )
        )
        request = ProcessingRequest(
            rep_id,
            (target_id,),
            "text_extract",
            processor.configuration_hash,
        )
        receipt = WorkbenchHost(
            writer, ProcessorRegistry((processor,))
        ).run_attempt(request)
        if receipt.outcome != "success" or len(receipt.outputs) != 1:
            raise SystemExit(
                f"PROCESSOR_DIRECT_001_PROOF=FAIL fixture={truth['fixture_id']} outcome={receipt.outcome}"
            )
        if [decision.decision for decision in receipt.decisions] != ["accept"]:
            raise SystemExit(
                f"PROCESSOR_DIRECT_001_PROOF=FAIL fixture={truth['fixture_id']} decision"
            )
        text = writer.archive.path_for_key(receipt.outputs[0].storage_key).read_text("utf-8")
        normalized = _normalize(text)
        missing = [
            span for span in truth["required_spans"] if _normalize(span) not in normalized
        ]
        if missing:
            raise SystemExit(
                f"PROCESSOR_DIRECT_001_PROOF=FAIL fixture={truth['fixture_id']} missing={missing!r}"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--natural-esparza",
        type=Path,
        help="optional exact hash-recorded Esparza PDF for page-4 natural proof",
    )
    args = parser.parse_args()

    processor = PopplerPdfTextProcessor.discover()
    tse_truth = json.loads(TSE_TRUTH.read_text("utf-8"))
    tse_bytes = TSE_PDF.read_bytes()
    if hashlib.sha256(tse_bytes).hexdigest() != tse_truth["source_pdf_sha256"]:
        raise SystemExit("PROCESSOR_DIRECT_001_PROOF=FAIL TSE source hash mismatch")
    _prove_pdf(
        pdf_bytes=tse_bytes,
        page_ordinal=tse_truth["page_ordinal"],
        source_url="https://www.tse.go.cr/pdf/gobernantes/alcaldias_pu.pdf",
        truth=tse_truth,
        processor=processor,
    )

    natural_status = "NOT_REQUESTED"
    if args.natural_esparza is not None:
        esparza_truth = json.loads(ESPARZA_TRUTH.read_text("utf-8"))
        esparza_bytes = args.natural_esparza.read_bytes()
        observed = hashlib.sha256(esparza_bytes).hexdigest()
        if observed != esparza_truth["source_sha256"]:
            raise SystemExit(
                "PROCESSOR_DIRECT_001_PROOF=FAIL Esparza source hash mismatch "
                f"observed={observed}"
            )
        _prove_pdf(
            pdf_bytes=esparza_bytes,
            page_ordinal=esparza_truth["source_page"],
            source_url=(
                "https://muniesparza.go.cr/files/folder/"
                "e0256fdf-3714-40f5-ae10-aff18f0ca95e.pdf"
            ),
            truth=esparza_truth,
            processor=processor,
        )
        natural_status = "PASS"

    print("PROCESSOR_DIRECT_001_PROOF=PASS")
    print(f"poppler_version={processor.descriptor.implementation_version}")
    print(f"configuration_hash={processor.configuration_hash}")
    print("tse_controlled=PASS")
    print(f"esparza_natural={natural_status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
