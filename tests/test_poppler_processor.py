from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
import zlib
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
from actakit.persistence import database
from actakit.processors import (
    ProcessingRequest,
    ProcessorDescriptor,
    ProcessorRegistry,
    ProcessorResolutionError,
    ProcessorResult,
    TargetContractError,
    TargetRegistration,
    WorkbenchHost,
    WorkbenchWriter,
)
import actakit.processors.poppler as poppler_module

from actakit.processors.poppler import (
    PopplerConfigurationError,
    PopplerPdfTextProcessor,
)

NO_RUNTIME_CHECK = lambda: None
T = "2026-08-22T17:30:00.000Z"
ROOT = Path(__file__).resolve().parents[1]
TSE_PDF = ROOT / "notebook/research/pre-sql/fixtures/artifact-proofs/alcaldias_pu.pdf"
TSE_TRUTH = (
    ROOT
    / "notebook/research/workbench/processors/bench/ground_truth/tse-esparza-alcaldias-p2.json"
)


def local_connection(path: Path) -> sqlite3.Connection:
    return database._open_writable_v1(path, NO_RUNTIME_CHECK)


class _NeverCalledOcr:
    def __init__(self) -> None:
        self.calls = 0
        self._descriptor = ProcessorDescriptor(
            "fixture.ocr",
            "ocr",
            "1",
            "local_deterministic",
            frozenset({"application/pdf"}),
            frozenset({"ocr_text"}),
            frozenset({"whole", "pdf_page"}),
        )

    @property
    def descriptor(self) -> ProcessorDescriptor:
        return self._descriptor

    def process(self, invocation):
        self.calls += 1
        return ProcessorResult("failed", error_code="unexpected_fixture_invocation")


def _pdf_bytes(pages: list[tuple[str | None, bool]]) -> bytes:
    """Build a tiny valid PDF with optional text and a tiny raster image per page."""

    objects: list[bytes | None] = [None, None]
    font_obj = 3
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    image_data = zlib.compress(
        bytes(
            [
                255,
                255,
                255,
                0,
                0,
                0,
                255,
                255,
                255,
                0,
                0,
                0,
            ]
        )
    )
    image_obj = 4
    objects.append(
        b"<< /Type /XObject /Subtype /Image /Width 2 /Height 2 "
        b"/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /FlateDecode /Length "
        + str(len(image_data)).encode("ascii")
        + b" >>\nstream\n"
        + image_data
        + b"\nendstream"
    )

    page_refs: list[int] = []
    for text, has_image in pages:
        content: list[str] = []
        if has_image:
            content.append("q 200 0 0 200 72 500 cm /Im1 Do Q")
        if text:
            escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            content.append(f"BT /F1 12 Tf 72 450 Td ({escaped}) Tj ET")
        stream = "\n".join(content).encode("ascii")
        content_obj = len(objects) + 1
        objects.append(
            b"<< /Length "
            + str(len(stream)).encode("ascii")
            + b" >>\nstream\n"
            + stream
            + b"\nendstream"
        )
        page_obj = len(objects) + 1
        resources = (
            f"<< /Font << /F1 {font_obj} 0 R >> "
            f"/XObject << /Im1 {image_obj} 0 R >> >>"
        )
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Resources {resources} /Contents {content_obj} 0 R >>"
            ).encode("ascii")
        )
        page_refs.append(page_obj)

    objects[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
    kids = " ".join(f"{ref} 0 R" for ref in page_refs)
    objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_refs)} >>".encode("ascii")

    payload = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        assert obj is not None
        offsets.append(len(payload))
        payload.extend(f"{number} 0 obj\n".encode("ascii"))
        payload.extend(obj)
        payload.extend(b"\nendobj\n")
    xref = len(payload)
    payload.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    payload.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        payload.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    payload.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(payload)


class PopplerProcessorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.processor = PopplerPdfTextProcessor.discover()

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / "actakit.sqlite3"
        self.archive = self.root / "archive"
        database._ensure_schema_v1(self.db, NO_RUNTIME_CHECK)
        self.deposit = DepositWriter(self.db, self.archive, connection_factory=local_connection)
        self.writer = WorkbenchWriter(self.db, self.archive, connection_factory=local_connection)
        self.source = SourceRegistration(new_id("src_"), "web", "Fixture authority", True, T)
        self.deposit.register_source(self.source)
        self.locator = SourceLocatorRegistration(
            new_id("sloc_"), self.source.id, "https://example.test/document.pdf", "http_url", T
        )
        self.deposit.register_source_locator(self.locator)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _capture(self, data: bytes, *, availability: str = "available") -> str:
        rep_id = new_id("rep_")
        artifact = CapturedArtifact(
            new_id("art_"),
            new_id("aob_"),
            rep_id,
            data,
            "primary",
            "document.pdf",
            self.locator.locator,
            "application/pdf",
            "verified",
            availability,
            "es",
            None,
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
        self.writer.register_target(TargetRegistration(target_id, rep_id, kind, "v1", payload, T))
        return target_id

    def _host(self, *extra) -> WorkbenchHost:
        return WorkbenchHost(
            self.writer,
            ProcessorRegistry((self.processor, *extra)),
        )

    def _request(self, rep_id: str, target_ids: tuple[str, ...]) -> ProcessingRequest:
        return ProcessingRequest(
            rep_id,
            target_ids,
            "text_extract",
            self.processor.configuration_hash,
        )

    def _quality_rows(self, run_id: str) -> list[tuple[str, str, str]]:
        con = local_connection(self.db)
        try:
            return con.execute(
                """
                SELECT representation_target_id,signal_key,payload_json
                FROM quality_evidence
                WHERE process_run_id=?
                ORDER BY representation_target_id,signal_key
                """,
                (run_id,),
            ).fetchall()
        finally:
            con.close()


    def test_local_poppler_subprocess_environment_is_minimal(self):
        env = poppler_module._clean_env()
        self.assertEqual(env, {"LC_ALL": "C", "LANG": "C"})

    def test_discovery_records_actual_poppler_and_stable_configuration(self):
        descriptor = self.processor.descriptor
        self.assertEqual(descriptor.key, "poppler.pdf_text")
        self.assertEqual(descriptor.capability_key, "text_extract")
        self.assertEqual(descriptor.execution_venue, "local_deterministic")
        self.assertIn("application/pdf", descriptor.input_media_types)
        self.assertEqual(descriptor.scope_kinds, frozenset({"whole", "pdf_page"}))
        self.assertRegex(descriptor.implementation_version, r"^[0-9]+\.[0-9]+\.[0-9]+$")
        self.assertRegex(self.processor.configuration_hash, r"^[0-9a-f]{64}$")
        self.assertFalse(descriptor.requires_egress)

    def test_real_tse_page_extracts_exact_required_spans_and_accepts(self):
        rep_id = self._capture(TSE_PDF.read_bytes())
        page = self._target(rep_id, "pdf_page", '{"page_ordinal":2}')
        receipt = self._host().run_attempt(self._request(rep_id, (page,)))
        self.assertEqual(receipt.outcome, "success")
        self.assertEqual([decision.decision for decision in receipt.decisions], ["accept"])
        self.assertEqual(len(receipt.outputs), 1)
        text = self.writer.archive.path_for_key(receipt.outputs[0].storage_key).read_text("utf-8")
        truth = json.loads(TSE_TRUTH.read_text("utf-8"))
        normalized = " ".join(text.split())
        for span in truth["required_spans"]:
            self.assertIn(" ".join(span.split()), normalized)
        evidence = {key: value for _, key, value in self._quality_rows(receipt.process_run_id)}
        self.assertEqual(evidence["native.replacement_character_ratio"], "0.0")

        con = local_connection(self.db)
        try:
            run = con.execute(
                """
                SELECT implementation,implementation_version,execution_venue,configuration_hash
                FROM process_runs WHERE id=?
                """,
                (receipt.process_run_id,),
            ).fetchone()
            self.assertEqual(
                run,
                (
                    "poppler.pdf_text",
                    self.processor.descriptor.implementation_version,
                    "local_deterministic",
                    self.processor.configuration_hash,
                ),
            )
        finally:
            con.close()

    def test_image_only_page_emits_no_derivative_and_escalates_to_ocr(self):
        rep_id = self._capture(_pdf_bytes([(None, True)]))
        page = self._target(rep_id, "pdf_page", '{"page_ordinal":1}')
        ocr = _NeverCalledOcr()
        receipt = self._host(ocr).run_attempt(self._request(rep_id, (page,)))
        self.assertEqual(receipt.outcome, "success")
        self.assertEqual(receipt.outputs, ())
        self.assertEqual(receipt.decisions[0].decision, "escalate")
        self.assertEqual(receipt.decisions[0].next_capability_key, "ocr")
        self.assertEqual(ocr.calls, 0)
        evidence = {(key, value) for _, key, value in self._quality_rows(receipt.process_run_id)}
        self.assertIn(("native.page_text_present", "false"), evidence)
        self.assertIn(("native.page_raster_image_count", "1"), evidence)

    def test_whole_mixed_pdf_detects_page_coverage_and_escalates(self):
        rep_id = self._capture(_pdf_bytes([("Native first page", False), (None, True)]))
        whole = self._target(rep_id, "whole", "{}")
        receipt = self._host(_NeverCalledOcr()).run_attempt(self._request(rep_id, (whole,)))
        self.assertEqual(receipt.decisions[0].decision, "escalate")
        self.assertEqual(len(receipt.outputs), 1)
        evidence = {key: value for _, key, value in self._quality_rows(receipt.process_run_id)}
        self.assertEqual(evidence["native.page_text_coverage"], "0.5")
        self.assertEqual(evidence["native.empty_page_count"], "1")
        self.assertEqual(evidence["native.empty_page_ordinals"], "[2]")
        self.assertEqual(evidence["native.mixed_page_modes"], "true")
        self.assertEqual(evidence["native.page_raster_image_count"], "1")

    def test_text_and_raster_page_records_image_presence_without_inventing_visual_truth(self):
        rep_id = self._capture(_pdf_bytes([("Visible native text", True)]))
        page = self._target(rep_id, "pdf_page", '{"page_ordinal":1}')
        receipt = self._host().run_attempt(self._request(rep_id, (page,)))
        self.assertEqual(receipt.decisions[0].decision, "accept")
        evidence = {key: value for _, key, value in self._quality_rows(receipt.process_run_id)}
        self.assertEqual(evidence["native.page_text_present"], "true")
        self.assertEqual(evidence["native.page_raster_image_count"], "1")
        # Raster presence is factual evidence only; D1 does not pretend to know
        # whether text embedded in an image has been visually recovered.

    def test_selected_page_output_preserves_requested_target_order(self):
        rep_id = self._capture(_pdf_bytes([("FIRST", False), ("SECOND", False), ("THIRD", False)]))
        page3 = self._target(rep_id, "pdf_page", '{"page_ordinal":3}')
        page1 = self._target(rep_id, "pdf_page", '{"page_ordinal":1}')
        receipt = self._host().run_attempt(self._request(rep_id, (page3, page1)))
        self.assertEqual([decision.decision for decision in receipt.decisions], ["accept", "accept"])
        output = self.writer.archive.path_for_key(receipt.outputs[0].storage_key).read_text("utf-8")
        self.assertLess(output.index("THIRD"), output.index("FIRST"))

    def test_malformed_pdf_is_terminal_failed_run_without_derivative(self):
        rep_id = self._capture(b"%PDF-1.7\nthis is deliberately truncated")
        whole = self._target(rep_id, "whole", "{}")
        receipt = self._host().run_attempt(self._request(rep_id, (whole,)))
        self.assertEqual(receipt.outcome, "failed")
        self.assertEqual(receipt.outputs, ())
        self.assertEqual(receipt.decisions[0].decision, "quarantine_review")

    def test_out_of_range_page_is_failed_not_silent_empty_success(self):
        rep_id = self._capture(_pdf_bytes([("ONLY PAGE", False)]))
        page = self._target(rep_id, "pdf_page", '{"page_ordinal":2}')
        receipt = self._host().run_attempt(self._request(rep_id, (page,)))
        self.assertEqual(receipt.outcome, "failed")
        self.assertEqual(receipt.outputs, ())

    def test_quote_locator_is_not_accepted_as_processing_page_scope(self):
        rep_id = self._capture(_pdf_bytes([("TEXT", False)]))
        quote = self._target(
            rep_id,
            "pdf_page_quote",
            '{"page_ordinal":1,"exact":"TEXT"}',
        )
        with self.assertRaises(ProcessorResolutionError):
            self._host().run_attempt(self._request(rep_id, (quote,)))


    def test_pdf_page_scope_rejects_quote_fields(self):
        rep_id = self._capture(_pdf_bytes([("TEXT", False)]))
        with self.assertRaises(TargetContractError):
            self._target(
                rep_id,
                "pdf_page",
                '{"page_ordinal":1,"exact":"TEXT"}',
            )

    def test_duplicate_physical_page_scope_fails_explicitly(self):
        rep_id = self._capture(_pdf_bytes([("TEXT", False)]))
        first = self._target(rep_id, "pdf_page", '{"page_ordinal":1}')
        second = self._target(rep_id, "pdf_page", '{"page_ordinal":1,"page_label":"1"}')
        receipt = self._host().run_attempt(self._request(rep_id, (first, second)))
        self.assertEqual(receipt.outcome, "failed")
        self.assertEqual(receipt.outputs, ())

    def test_whole_and_page_scope_cannot_overlap(self):
        rep_id = self._capture(_pdf_bytes([("TEXT", False)]))
        whole = self._target(rep_id, "whole", "{}")
        page = self._target(rep_id, "pdf_page", '{"page_ordinal":1}')
        # The descriptor admits both selector kinds individually; the adapter
        # rejects overlapping semantic scope before any derivative is persisted.
        receipt = self._host().run_attempt(self._request(rep_id, (whole, page)))
        self.assertEqual(receipt.outcome, "failed")
        self.assertEqual(receipt.outputs, ())

    def test_restricted_pdf_can_process_locally_but_derivative_stays_restricted(self):
        rep_id = self._capture(_pdf_bytes([("RESTRICTED TEXT", False)]), availability="restricted")
        page = self._target(rep_id, "pdf_page", '{"page_ordinal":1}')
        receipt = self._host().run_attempt(self._request(rep_id, (page,)))
        self.assertEqual(receipt.decisions[0].decision, "accept")
        con = local_connection(self.db)
        try:
            self.assertEqual(
                con.execute(
                    "SELECT availability FROM representations WHERE process_run_id=?",
                    (receipt.process_run_id,),
                ).fetchone(),
                ("restricted",),
            )
        finally:
            con.close()

    def test_configuration_hash_must_match_trusted_adapter_config(self):
        self.assertNotEqual(
            PopplerPdfTextProcessor.discover().configuration_hash,
            PopplerPdfTextProcessor.discover(
                config=poppler_module.PopplerPdfTextConfig(attempt_timeout_seconds=121)
            ).configuration_hash,
        )
        rep_id = self._capture(_pdf_bytes([("TEXT", False)]))
        page = self._target(rep_id, "pdf_page", '{"page_ordinal":1}')
        request = ProcessingRequest(rep_id, (page,), "text_extract", "0" * 64)
        with self.assertRaises(PopplerConfigurationError):
            self._host().run_attempt(request)


if __name__ == "__main__":
    unittest.main()
