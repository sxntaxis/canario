#!/usr/bin/env python3
"""Target-runtime production proof for PROCESSOR-CODEX-001."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
BENCH = ROOT / "notebook/research/workbench/processors/bench"
if str(BENCH) not in sys.path:
    sys.path.insert(0, str(BENCH))

from metrics import normalize_text, text_metrics  # type: ignore[import-not-found]
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
    CodexVisualTranscriptionProcessor,
    EgressAuthorization,
    ProcessingRequest,
    ProcessorRegistry,
    TargetRegistration,
    WorkbenchHost,
    WorkbenchWriter,
)

TSE_TRUTH = BENCH / "ground_truth/tse-esparza-alcaldias-p2.json"
ESPARZA_TRUTH = BENCH / "ground_truth/natural-layout/esparza-p4.json"
ESPARZA_SHA256 = "ffb354c67d8b56ebf265884c820a98fee27015cadaac3ea1011069f7969b8bfd"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _truth(meta_path: Path) -> tuple[str, list[str], list[list[str]]]:
    meta = json.loads(meta_path.read_text("utf-8"))
    truth = (BENCH / meta["truth_text"]).read_text("utf-8")
    spans = list(meta["required_spans"])
    rows = [list(row) for row in meta.get("table_rows", [])]
    return truth, spans, rows


def _table_metrics(observed_tables: list[object], expected_rows: list[list[str]]) -> dict[str, object]:
    rows: list[list[str]] = []
    for table in observed_tables:
        if isinstance(table, dict) and isinstance(table.get("rows"), list):
            for row in table["rows"]:
                if isinstance(row, list) and all(isinstance(cell, str) for cell in row):
                    rows.append(row)
    expected_by_key = {normalize_text(row[0]): row for row in expected_rows}
    candidates = [row for row in rows if row and normalize_text(row[0]) in expected_by_key]
    exact = 0
    matched_cells = 0
    expected_cells = sum(len(row) for row in expected_rows)
    for row in candidates:
        expected = expected_by_key[normalize_text(row[0])]
        matches = sum(
            index < len(row) and normalize_text(row[index]) == normalize_text(cell)
            for index, cell in enumerate(expected)
        )
        matched_cells += matches
        exact += matches == len(expected) and len(row) == len(expected)
    return {
        "observed_table_count": len(observed_tables),
        "observed_row_count": len(rows),
        "exact_row_recall": exact / len(expected_rows) if expected_rows else 1.0,
        "cell_fidelity": matched_cells / expected_cells if expected_cells else 1.0,
    }


def _run_page(
    *,
    pdf: Path,
    page_ordinal: int,
    processor: CodexVisualTranscriptionProcessor,
    source_url: str,
) -> tuple[object, str, list[object], dict[str, object], int]:
    with tempfile.TemporaryDirectory(prefix="actakit-codex-proof-") as tempdir:
        root = Path(tempdir)
        db = root / "actakit.sqlite3"
        archive = root / "archive"
        ensure_schema_v1(db)
        deposit = DepositWriter(db, archive)
        writer = WorkbenchWriter(db, archive)
        now = utc_now()
        source = SourceRegistration(new_id("src_"), "web", "Codex proof fixture", True, now)
        deposit.register_source(source)
        locator = SourceLocatorRegistration(new_id("sloc_"), source.id, source_url, "http_url", now)
        deposit.register_source_locator(locator)
        rep_id = new_id("rep_")
        artifact = CapturedArtifact(
            new_id("art_"),
            new_id("aob_"),
            rep_id,
            pdf.read_bytes(),
            "primary",
            pdf.name,
            source_url,
            "application/pdf",
            "verified",
            "available",
            "es",
            None,
            now,
        )
        observation = AcquisitionObservation(
            new_id("acq_"), source.id, locator.id, now, "success", 200,
            "processor_codex_001_proof", "v1", None, now,
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
            "visual_transcribe",
            processor.configuration_hash,
            EgressAuthorization(
                True,
                "public_civic",
                "chatgpt_personal_operator_enabled",
                processor.request_template_hash,
                processor.config.endpoint_profile,
            ),
        )
        receipt = WorkbenchHost(writer, ProcessorRegistry((processor,))).run_attempt(request)
        transcription = ""
        tables: list[object] = []
        con = sqlite3.connect(db)
        try:
            rows = con.execute(
                "SELECT kind,archive_object_id FROM representations WHERE process_run_id=? ORDER BY kind",
                (receipt.process_run_id,),
            ).fetchall()
            for kind, archive_object_id in rows:
                storage_key = con.execute(
                    "SELECT storage_key FROM archive_objects WHERE id=?", (archive_object_id,)
                ).fetchone()[0]
                data = writer.archive.path_for_key(storage_key).read_bytes()
                if kind == "transcript":
                    transcription = data.decode("utf-8")
                elif kind == "table":
                    value = json.loads(data.decode("utf-8"))
                    tables = list(value["tables"])
            evidence = {
                key: json.loads(payload)
                for key, payload in con.execute(
                    "SELECT signal_key,payload_json FROM quality_evidence WHERE process_run_id=?",
                    (receipt.process_run_id,),
                )
            }
            egress = con.execute(
                "SELECT bytes_egressed,policy_profile,data_control_profile,request_template_hash,endpoint_profile "
                "FROM process_run_egress WHERE process_run_id=?",
                (receipt.process_run_id,),
            ).fetchone()
            if egress is None:
                raise SystemExit("PROCESSOR_CODEX_001_PROOF=FAIL missing egress provenance")
            if egress[0] <= 0:
                raise SystemExit("PROCESSOR_CODEX_001_PROOF=FAIL actual cloud run recorded no source egress")
            if egress[1:] != (
                "public_civic",
                "chatgpt_personal_operator_enabled",
                processor.request_template_hash,
                processor.config.endpoint_profile,
            ):
                raise SystemExit("PROCESSOR_CODEX_001_PROOF=FAIL egress policy provenance")
            process_row = con.execute(
                "SELECT execution_venue,model_provider,model_name,configuration_hash FROM process_runs WHERE id=?",
                (receipt.process_run_id,),
            ).fetchone()
            if process_row != (
                "subscription_agent", "openai", processor.config.model, processor.configuration_hash
            ):
                raise SystemExit("PROCESSOR_CODEX_001_PROOF=FAIL ProcessRun model/config provenance")
            return receipt, transcription, tables, evidence, int(egress[0])
        finally:
            con.close()


def _prove_tse(processor: CodexVisualTranscriptionProcessor, manifest: Path) -> dict[str, object]:
    control = json.loads(manifest.read_text("utf-8"))
    variant = control["variants"]["skew_noise_300_pdf"]
    pdf = Path(variant["path"])
    if _sha256(pdf) != variant["sha256"]:
        raise SystemExit("PROCESSOR_CODEX_001_PROOF=FAIL controlled variant hash mismatch")
    truth, spans, expected_rows = _truth(TSE_TRUTH)
    receipt, text, tables, evidence, egress = _run_page(
        pdf=pdf, page_ordinal=1, processor=processor, source_url="fixture://tse-skew-noise-300"
    )
    metrics = text_metrics(truth, text, spans)
    table = _table_metrics(tables, expected_rows)
    if receipt.outcome != "success" or receipt.decisions[0].decision != "accept":
        raise SystemExit("PROCESSOR_CODEX_001_PROOF=FAIL TSE outcome/decision")
    if metrics["required_span_recall"] != 1.0 or float(metrics["cer"]) > 0.03:
        raise SystemExit(f"PROCESSOR_CODEX_001_PROOF=FAIL TSE text metrics {metrics}")
    if table["exact_row_recall"] != 1.0 or table["cell_fidelity"] != 1.0:
        raise SystemExit(f"PROCESSOR_CODEX_001_PROOF=FAIL TSE table metrics {table}")
    if evidence.get("multimodal.schema_valid") is not True:
        raise SystemExit("PROCESSOR_CODEX_001_PROOF=FAIL TSE schema evidence")
    if evidence.get("multimodal.uncertain_span_count") != 0:
        raise SystemExit("PROCESSOR_CODEX_001_PROOF=FAIL TSE uncertainty")
    return {"metrics": metrics, "table_metrics": table, "egress_source_bytes": egress}


def _prove_esparza(processor: CodexVisualTranscriptionProcessor, pdf: Path) -> dict[str, object]:
    if _sha256(pdf) != ESPARZA_SHA256:
        raise SystemExit("PROCESSOR_CODEX_001_PROOF=FAIL Esparza source hash mismatch")
    truth, spans, _ = _truth(ESPARZA_TRUTH)
    receipt, text, _, evidence, egress = _run_page(
        pdf=pdf,
        page_ordinal=4,
        processor=processor,
        source_url="https://muniesparza.go.cr/files/folder/e0256fdf-3714-40f5-ae10-aff18f0ca95e.pdf",
    )
    metrics = text_metrics(truth, text, spans)
    if receipt.outcome != "success" or receipt.decisions[0].decision != "accept":
        raise SystemExit("PROCESSOR_CODEX_001_PROOF=FAIL Esparza outcome/decision")
    if metrics["required_span_recall"] != 1.0 or float(metrics["cer"]) > 0.03:
        raise SystemExit(f"PROCESSOR_CODEX_001_PROOF=FAIL Esparza metrics {metrics}")
    if evidence.get("multimodal.schema_valid") is not True:
        raise SystemExit("PROCESSOR_CODEX_001_PROOF=FAIL Esparza schema evidence")
    if evidence.get("multimodal.uncertain_span_count") != 0:
        raise SystemExit("PROCESSOR_CODEX_001_PROOF=FAIL Esparza uncertainty")
    return {"metrics": metrics, "egress_source_bytes": egress}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--codex-home", type=Path, required=True)
    parser.add_argument("--controlled-variants", type=Path, required=True)
    parser.add_argument("--natural-esparza", type=Path, required=True)
    args = parser.parse_args()

    processor = CodexVisualTranscriptionProcessor.discover(codex_home=args.codex_home)
    tse = _prove_tse(processor, args.controlled_variants)
    esparza = _prove_esparza(processor, args.natural_esparza)
    print(
        json.dumps(
            {
                "PROCESSOR_CODEX_001_PROOF": "PASS",
                "processor_key": processor.descriptor.key,
                "implementation_version": processor.descriptor.implementation_version,
                "model": processor.config.model,
                "configuration_hash": processor.configuration_hash,
                "request_template_hash": processor.request_template_hash,
                "output_schema_hash": processor.output_schema_hash,
                "controlled_tse": tse,
                "natural_esparza": esparza,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
