#!/usr/bin/env python3
"""Target-runtime production proof for PROCESSOR-OCR-001."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
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
from canario.persistence import ensure_schema_v1
from canario.processors import (
    EgressAuthorization,
    ProcessingRequest,
    ProcessorDescriptor,
    ProcessorRegistry,
    ProcessorResult,
    TargetRegistration,
    WorkbenchHost,
    WorkbenchWriter,
)
from canario.processors.ocr import OcrPdfProcessor

TSE_TRUTH = ROOT / "notebook/research/workbench/processors/bench/ground_truth/tse-esparza-alcaldias-p2.json"
ESPARZA_TRUTH = ROOT / "notebook/research/workbench/processors/bench/ground_truth/natural-layout/esparza-p4.json"


class _VisualAvailability:
    """Makes the next reference capability eligible without invoking cloud."""

    def __init__(self) -> None:
        self.calls = 0
        self._descriptor = ProcessorDescriptor(
            "proof.visual",
            "visual_transcribe",
            "1",
            "subscription_agent",
            frozenset({"application/pdf"}),
            frozenset({"extracted_text"}),
            frozenset({"pdf_page"}),
            requires_egress=True,
        )

    @property
    def descriptor(self) -> ProcessorDescriptor:
        return self._descriptor

    def process(self, invocation):
        self.calls += 1
        return ProcessorResult("failed", error_code="proof_visual_must_not_run")


def _normalize(text: str) -> str:
    return " ".join(text.split())


def _span_hits(text: str, spans: list[str]) -> int:
    normalized = _normalize(text)
    return sum(_normalize(span) in normalized for span in spans)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _capture_and_run(
    *,
    pdf_bytes: bytes,
    processor: OcrPdfProcessor,
    selector_kind: str,
    selector_payload: dict[str, object],
    source_url: str,
) -> tuple[object, str, dict[str, object]]:
    with tempfile.TemporaryDirectory(prefix="canario-ocr-proof-") as tmp:
        root = Path(tmp)
        db = root / "canario.sqlite3"
        archive = root / "archive"
        ensure_schema_v1(db)
        deposit = DepositWriter(db, archive)
        writer = WorkbenchWriter(db, archive)
        now = utc_now()
        source = SourceRegistration(new_id("src_"), "web", "OCR proof fixture", True, now)
        deposit.register_source(source)
        locator = SourceLocatorRegistration(new_id("sloc_"), source.id, source_url, "http_url", now)
        deposit.register_source_locator(locator)
        rep_id = new_id("rep_")
        artifact = CapturedArtifact(
            new_id("art_"),
            new_id("aob_"),
            rep_id,
            pdf_bytes,
            "primary",
            "ocr-proof.pdf",
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
            "processor_ocr_001_proof",
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
                selector_kind,
                "v1",
                json.dumps(selector_payload, sort_keys=True, separators=(",", ":")),
                now,
            )
        )
        visual = _VisualAvailability()
        request = ProcessingRequest(
            rep_id,
            (target_id,),
            "ocr",
            processor.configuration_hash,
            EgressAuthorization(True, "public_civic", "operator_approved"),
        )
        receipt = WorkbenchHost(writer, ProcessorRegistry((processor, visual))).run_attempt(request)
        text = ""
        if receipt.outputs:
            text = writer.archive.path_for_key(receipt.outputs[0].storage_key).read_text("utf-8")
        evidence = {}
        import sqlite3
        con = sqlite3.connect(db)
        try:
            for key, payload in con.execute(
                "SELECT signal_key,payload_json FROM quality_evidence WHERE process_run_id=?",
                (receipt.process_run_id,),
            ):
                evidence[key] = json.loads(payload)
        finally:
            con.close()
        if visual.calls != 0:
            raise SystemExit("PROCESSOR_OCR_001_PROOF=FAIL visual fixture was invoked")
        return receipt, text, evidence


def _require_escalation(receipt: object, label: str) -> None:
    decisions = getattr(receipt, "decisions")
    if [item.decision for item in decisions] != ["escalate"]:
        raise SystemExit(f"PROCESSOR_OCR_001_PROOF=FAIL {label} decision")
    if decisions[0].next_capability_key != "visual_transcribe":
        raise SystemExit(f"PROCESSOR_OCR_001_PROOF=FAIL {label} next capability")


def _prove_controlled(processor: OcrPdfProcessor, manifest_path: Path) -> None:
    manifest = json.loads(manifest_path.read_text("utf-8"))
    truth_meta = json.loads(TSE_TRUTH.read_text("utf-8"))
    spans = list(truth_meta["required_spans"])
    variants = manifest["variants"]

    thresholds = {
        "clean_scan_300_pdf": 3,
        "lowdpi_110_pdf": 3,
    }
    for key, minimum_hits in thresholds.items():
        path = Path(variants[key]["path"])
        if _sha256(path) != variants[key]["sha256"]:
            raise SystemExit(f"PROCESSOR_OCR_001_PROOF=FAIL controlled hash mismatch {key}")
        receipt, text, evidence = _capture_and_run(
            pdf_bytes=path.read_bytes(),
            processor=processor,
            selector_kind="pdf_page",
            selector_payload={"page_ordinal": 1},
            source_url=f"fixture://{key}",
        )
        if receipt.outcome != "success" or not receipt.outputs:
            raise SystemExit(f"PROCESSOR_OCR_001_PROOF=FAIL {key} output")
        _require_escalation(receipt, key)
        hits = _span_hits(text, spans)
        if hits < minimum_hits:
            raise SystemExit(
                f"PROCESSOR_OCR_001_PROOF=FAIL {key} required_span_hits={hits} expected>={minimum_hits}"
            )
        if evidence.get("ocr.needs_visual_review") is not True:
            raise SystemExit(f"PROCESSOR_OCR_001_PROOF=FAIL {key} visual-review evidence")

    skew = Path(variants["skew_noise_300_pdf"]["path"])
    receipt, _, evidence = _capture_and_run(
        pdf_bytes=skew.read_bytes(),
        processor=processor,
        selector_kind="pdf_page",
        selector_payload={"page_ordinal": 1},
        source_url="fixture://skew-noise",
    )
    if receipt.outcome != "success":
        raise SystemExit("PROCESSOR_OCR_001_PROOF=FAIL skew execution")
    _require_escalation(receipt, "skew_noise")
    if evidence.get("ocr.needs_visual_review") is not True:
        raise SystemExit("PROCESSOR_OCR_001_PROOF=FAIL skew must remain review-bound")

    mixed = Path(variants["mixed_native_scan_pdf"]["path"])
    receipt, text, evidence = _capture_and_run(
        pdf_bytes=mixed.read_bytes(),
        processor=processor,
        selector_kind="whole",
        selector_payload={},
        source_url="fixture://mixed-native-scan",
    )
    if receipt.outcome != "success" or not receipt.outputs:
        raise SystemExit("PROCESSOR_OCR_001_PROOF=FAIL mixed output")
    if [item.decision for item in receipt.decisions] != ["quarantine_review"]:
        raise SystemExit("PROCESSOR_OCR_001_PROOF=FAIL mixed whole scope must stop before visual egress")
    pages = text.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    if len(pages) != 2:
        raise SystemExit(f"PROCESSOR_OCR_001_PROOF=FAIL mixed page boundaries={len(pages)}")
    if _span_hits(pages[0], spans) != len(spans):
        raise SystemExit("PROCESSOR_OCR_001_PROOF=FAIL mixed native page not preserved")
    if _span_hits(pages[1], spans) < 3:
        raise SystemExit("PROCESSOR_OCR_001_PROOF=FAIL mixed scan page below benchmark floor")
    if evidence.get("ocr.native_page_count") != 1 or evidence.get("ocr.ocr_page_count") != 1:
        raise SystemExit("PROCESSOR_OCR_001_PROOF=FAIL mixed provenance counts")
    if evidence.get("ocr.ocr_page_ordinals") != [2]:
        raise SystemExit("PROCESSOR_OCR_001_PROOF=FAIL mixed OCR page ordinals")

    malformed = Path(variants["malformed_truncated_pdf"]["path"])
    receipt, _, _ = _capture_and_run(
        pdf_bytes=malformed.read_bytes(),
        processor=processor,
        selector_kind="whole",
        selector_payload={},
        source_url="fixture://malformed",
    )
    if receipt.outcome != "failed" or receipt.outputs:
        raise SystemExit("PROCESSOR_OCR_001_PROOF=FAIL malformed failure isolation")


def _render_natural_scan(source: Path, page: int, work: Path) -> Path:
    prefix = work / "natural-page"
    subprocess.run(
        [
            "pdftoppm",
            "-f", str(page),
            "-l", str(page),
            "-r", "300",
            "-singlefile",
            "-png",
            str(source),
            str(prefix),
        ],
        check=True,
    )
    png = prefix.with_suffix(".png")
    try:
        from PIL import Image
    except ImportError as exc:
        raise SystemExit("PROCESSOR_OCR_001_PROOF=FAIL Pillow required for natural proof") from exc
    pdf = work / "natural-page.pdf"
    with Image.open(png) as opened:
        opened.convert("RGB").save(pdf, "PDF", resolution=300.0)
    return pdf


def _prove_natural(processor: OcrPdfProcessor, source: Path) -> None:
    truth = json.loads(ESPARZA_TRUTH.read_text("utf-8"))
    observed = _sha256(source)
    if observed != truth["source_sha256"]:
        raise SystemExit(
            f"PROCESSOR_OCR_001_PROOF=FAIL natural source hash mismatch observed={observed}"
        )
    with tempfile.TemporaryDirectory(prefix="canario-ocr-natural-") as tmp:
        scan_pdf = _render_natural_scan(source, int(truth["source_page"]), Path(tmp))
        receipt, text, evidence = _capture_and_run(
            pdf_bytes=scan_pdf.read_bytes(),
            processor=processor,
            selector_kind="pdf_page",
            selector_payload={"page_ordinal": 1},
            source_url="fixture://esparza-page-4-controlled-scan",
        )
    if receipt.outcome != "success" or not receipt.outputs:
        raise SystemExit("PROCESSOR_OCR_001_PROOF=FAIL natural output")
    _require_escalation(receipt, "natural_esparza")
    hits = _span_hits(text, list(truth["required_spans"]))
    if hits < 4:
        raise SystemExit(
            f"PROCESSOR_OCR_001_PROOF=FAIL natural required_span_hits={hits} expected>=4"
        )
    if evidence.get("ocr.needs_visual_review") is not True:
        raise SystemExit("PROCESSOR_OCR_001_PROOF=FAIL natural must remain visual-review bound")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--controlled-variants", type=Path, required=True)
    parser.add_argument("--natural-esparza", type=Path)
    args = parser.parse_args()

    processor = OcrPdfProcessor.discover()
    _prove_controlled(processor, args.controlled_variants)
    natural_status = "NOT_REQUESTED"
    if args.natural_esparza is not None:
        _prove_natural(processor, args.natural_esparza)
        natural_status = "PASS"

    print("PROCESSOR_OCR_001_PROOF=PASS")
    print(f"implementation_version={processor.descriptor.implementation_version}")
    print(f"configuration_hash={processor.configuration_hash}")
    print(f"model_name={processor.descriptor.model_name}")
    print("controlled_d2=PASS")
    print(f"esparza_natural_layout={natural_status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
