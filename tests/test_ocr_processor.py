from __future__ import annotations

import json
import signal
import sqlite3
import subprocess
import tempfile
import time
import unittest
import zlib
from pathlib import Path
from unittest.mock import MagicMock, patch

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
    EgressAuthorization,
    PlannedStep,
    ProcessingPlan,
    ProcessingRequest,
    ProcessorDescriptor,
    ProcessorRegistry,
    ProcessorResult,
    TargetRegistration,
    WorkbenchHost,
    WorkbenchWriter,
)
from actakit.processors.ocr import OcrPdfConfig, OcrPdfProcessor, OcrUnavailableError, _OcrToolchain
from actakit.processors.poppler import PopplerPdfTextProcessor

NO_RUNTIME_CHECK = lambda: None
T = "2026-08-22T18:30:00.000Z"
_TESSDATA_HASHES = (("spa", "a" * 64), ("eng", "b" * 64), ("osd", "c" * 64))


def local_connection(path: Path) -> sqlite3.Connection:
    return database._open_writable_v1(path, NO_RUNTIME_CHECK)


def _pdf_bytes(pages: list[tuple[str | None, bool]]) -> bytes:
    objects: list[bytes | None] = [None, None]
    font_obj = 3
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    image_data = zlib.compress(bytes([255, 255, 255, 0, 0, 0] * 2))
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
            b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream"
        )
        page_obj = len(objects) + 1
        resources = f"<< /Font << /F1 {font_obj} 0 R >> /XObject << /Im1 {image_obj} 0 R >> >>"
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


class _VisualFixture:
    def __init__(self) -> None:
        self.calls = 0
        self._descriptor = ProcessorDescriptor(
            "fixture.visual",
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
        return ProcessorResult("failed", error_code="fixture_should_not_run")


class _SimulatedOcr(OcrPdfProcessor):
    def __init__(self, output_pdf: bytes, *, config: OcrPdfConfig | None = None) -> None:
        true = "/usr/bin/true"
        super().__init__(
            _OcrToolchain(
                true,
                true,
                "/usr/bin/pdfinfo",
                "/usr/bin/pdftotext",
                "17.10.0",
                "5.5.3",
                "26.07.0",
                "5.12.1",
                "2.8.3",
                "0.51.0",
                "9.11.0",
                frozenset({"spa", "eng", "osd"}),
                _TESSDATA_HASHES,
            ),
            config=config,
        )
        self.output_pdf = output_pdf
        self.ocr_calls = 0
        self.selected_pages: tuple[int, ...] | None = None

    def _run_ocrmypdf(self, input_pdf, output_pdf, selected_pages, tempdir, deadline):
        self.ocr_calls += 1
        self.selected_pages = selected_pages
        output_pdf.write_bytes(self.output_pdf)


class OcrProcessorTests(unittest.TestCase):
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
            new_id("sloc_"), self.source.id, "https://example.test/scan.pdf", "http_url", T
        )
        self.deposit.register_source_locator(self.locator)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _capture(self, payload: bytes, *, availability: str = "available") -> str:
        rep_id = new_id("rep_")
        artifact = CapturedArtifact(
            new_id("art_"),
            new_id("aob_"),
            rep_id,
            payload,
            "primary",
            "scan.pdf",
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
            "fixture.ocr",
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

    def _host(self, processor, *extra) -> WorkbenchHost:
        return WorkbenchHost(self.writer, ProcessorRegistry((processor, *extra)))

    def _request(
        self,
        processor: OcrPdfProcessor,
        rep_id: str,
        targets: tuple[str, ...],
        *,
        cloud_allowed: bool = False,
    ):
        egress = (
            EgressAuthorization(True, "public_civic", "operator_approved")
            if cloud_allowed
            else EgressAuthorization.forbidden()
        )
        return ProcessingRequest(rep_id, targets, "ocr", processor.configuration_hash, egress)

    def _evidence(self, run_id: str) -> dict[str, str]:
        con = local_connection(self.db)
        try:
            return {
                key: value
                for key, value in con.execute(
                    "SELECT signal_key,payload_json FROM quality_evidence WHERE process_run_id=?",
                    (run_id,),
                )
            }
        finally:
            con.close()


    def test_missing_required_tesseract_language_is_rejected(self):
        true = "/usr/bin/true"
        toolchain = _OcrToolchain(
            true, true, "/usr/bin/pdfinfo", "/usr/bin/pdftotext",
            "17.10.0", "5.5.3", "26.07.0", "5.12.1",
            "2.8.3", "0.51.0", "9.11.0",
            frozenset({"eng", "osd"}),
            (("eng", "b" * 64), ("osd", "c" * 64)),
        )
        with self.assertRaises(OcrUnavailableError):
            OcrPdfProcessor(toolchain)

    def test_ocr_command_is_fixed_and_page_set_is_sorted(self):
        true = "/usr/bin/true"
        processor = OcrPdfProcessor(
            _OcrToolchain(
                true, true, "/usr/bin/pdfinfo", "/usr/bin/pdftotext",
                "17.10.0", "5.5.3", "26.07.0", "5.12.1",
                "2.8.3", "0.51.0", "9.11.0",
                frozenset({"spa", "eng", "osd"}),
                _TESSDATA_HASHES,
            )
        )
        captured = {}
        def fake_run(command, tempdir, deadline):
            captured["command"] = command
            return None
        processor._run = fake_run  # type: ignore[method-assign]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            processor._run_ocrmypdf(
                root / "input.pdf", root / "output.pdf", (3, 1), root, 9999999999.0
            )
        command = captured["command"]
        self.assertIn("--mode", command)
        self.assertIn("skip", command)
        self.assertIn("--ocr-engine", command)
        self.assertEqual(command[command.index("--ocr-engine") + 1], "tesseract")
        self.assertIn("--rasterizer", command)
        self.assertEqual(command[command.index("--rasterizer") + 1], "pypdfium")
        self.assertIn("--output-type", command)
        self.assertIn("pdf", command)
        self.assertIn("--optimize", command)
        self.assertIn("0", command)
        self.assertIn("--max-image-mpixels", command)
        self.assertEqual(command[command.index("--max-image-mpixels") + 1], "250")
        self.assertIn("--jobs", command)
        self.assertIn("--rotate-pages", command)
        self.assertIn("--deskew", command)
        self.assertEqual(command[command.index("--pages") + 1], "1,3")
        self.assertEqual(command[command.index("--language") + 1], "spa+eng")

    def test_descriptor_is_local_ocr_and_configuration_is_stable(self):
        processor = _SimulatedOcr(_pdf_bytes([("OCR", False)]))
        self.assertEqual(processor.descriptor.key, "ocrmypdf.tesseract_pdf")
        self.assertEqual(processor.descriptor.capability_key, "ocr")
        self.assertEqual(processor.descriptor.execution_venue, "local_deterministic")
        self.assertEqual(processor.descriptor.model_provider, "tesseract")
        self.assertRegex(processor.descriptor.model_name or "", r"^spa\+eng\+osd@sha256:[0-9a-f]{64}$")
        self.assertIn("pypdfium2-5.12.1", processor.descriptor.implementation_version)
        self.assertIn("fpdf2-2.8.3", processor.descriptor.implementation_version)
        self.assertIn("uharfbuzz-0.51.0", processor.descriptor.implementation_version)
        self.assertIn("pikepdf-9.11.0", processor.descriptor.implementation_version)
        self.assertFalse(processor.descriptor.requires_egress)
        self.assertEqual(processor.descriptor.scope_kinds, frozenset({"whole", "pdf_page"}))
        self.assertRegex(processor.configuration_hash, r"^[0-9a-f]{64}$")
        changed = _SimulatedOcr(
            _pdf_bytes([("OCR", False)]),
            config=OcrPdfConfig(attempt_timeout_seconds=301),
        )
        self.assertNotEqual(processor.configuration_hash, changed.configuration_hash)
        changed_intermediate_limit = _SimulatedOcr(
            _pdf_bytes([("OCR", False)]),
            config=OcrPdfConfig(max_intermediate_pdf_bytes=385 * 1024 * 1024),
        )
        self.assertNotEqual(
            processor.configuration_hash, changed_intermediate_limit.configuration_hash
        )
        changed_image_limit = _SimulatedOcr(
            _pdf_bytes([("OCR", False)]),
            config=OcrPdfConfig(max_image_mpixels=249),
        )
        self.assertNotEqual(processor.configuration_hash, changed_image_limit.configuration_hash)
        changed_model = OcrPdfProcessor(
            _OcrToolchain(
                "/usr/bin/true",
                "/usr/bin/true",
                "/usr/bin/pdfinfo",
                "/usr/bin/pdftotext",
                "17.10.0",
                "5.5.3",
                "26.07.0",
                "5.12.1",
                "2.8.3",
                "0.51.0",
                "9.11.0",
                frozenset({"spa", "eng", "osd"}),
                (("spa", "d" * 64), ("eng", "b" * 64), ("osd", "c" * 64)),
            )
        )
        self.assertEqual(processor.configuration_hash, changed_model.configuration_hash)
        self.assertNotEqual(processor.descriptor.model_name, changed_model.descriptor.model_name)

    def test_rotate_disabled_does_not_require_osd_model(self):
        true = "/usr/bin/true"
        processor = OcrPdfProcessor(
            _OcrToolchain(
                true, true, "/usr/bin/pdfinfo", "/usr/bin/pdftotext",
                "17.10.0", "5.5.3", "26.07.0", "5.12.1",
                "2.8.3", "0.51.0", "9.11.0",
                frozenset({"spa", "eng"}),
                (("spa", "a" * 64), ("eng", "b" * 64)),
            ),
            config=OcrPdfConfig(rotate_pages=False),
        )
        self.assertRegex(processor.descriptor.model_name or "", r"^spa\+eng@sha256:[0-9a-f]{64}$")

    def test_whole_document_limit_counts_only_pages_that_need_ocr(self):
        source_pages = [(f"NATIVE {index}", False) for index in range(1, 40)] + [(None, True)]
        output_pages = [(f"NATIVE {index}", False) for index in range(1, 40)] + [("OCR LAST", True)]
        source = _pdf_bytes(source_pages)
        processor = _SimulatedOcr(
            _pdf_bytes(output_pages),
            config=OcrPdfConfig(max_ocr_pages_per_attempt=1),
        )
        rep = self._capture(source)
        whole = self._target(rep, "whole", "{}")
        receipt = self._host(processor, _VisualFixture()).run_attempt(
            self._request(processor, rep, (whole,), cloud_allowed=True)
        )
        self.assertEqual(receipt.outcome, "success")
        self.assertEqual(processor.selected_pages, (40,))
        evidence = self._evidence(receipt.process_run_id)
        self.assertEqual(evidence["ocr.native_page_count"], "39")
        self.assertEqual(evidence["ocr.ocr_page_count"], "1")

    def test_page_scoped_image_only_ocr_persists_text_but_escalates_to_visual(self):
        source = _pdf_bytes([(None, True)])
        processor = _SimulatedOcr(_pdf_bytes([("RECOVERED OCR TEXT", True)]))
        visual = _VisualFixture()
        rep = self._capture(source)
        page = self._target(rep, "pdf_page", '{"page_ordinal":1}')
        receipt = self._host(processor, visual).run_attempt(self._request(processor, rep, (page,), cloud_allowed=True))
        self.assertEqual(processor.ocr_calls, 1)
        self.assertEqual(receipt.outcome, "success")
        self.assertEqual(receipt.decisions[0].decision, "escalate")
        self.assertEqual(receipt.decisions[0].next_capability_key, "visual_transcribe")
        self.assertEqual(visual.calls, 0)
        self.assertEqual(len(receipt.outputs), 1)
        text = self.writer.archive.path_for_key(receipt.outputs[0].storage_key).read_text("utf-8")
        self.assertIn("RECOVERED OCR TEXT", text)
        evidence = self._evidence(receipt.process_run_id)
        self.assertEqual(evidence["ocr.page_text_coverage"], "1.0")
        self.assertEqual(evidence["ocr.ocr_page_count"], "1")
        self.assertEqual(evidence["ocr.native_page_count"], "0")
        self.assertEqual(evidence["ocr.needs_visual_review"], "true")

    def test_whole_mixed_pdf_preserves_native_and_recovers_empty_page(self):
        source = _pdf_bytes([("NATIVE FIRST", False), (None, True)])
        processor = _SimulatedOcr(
            _pdf_bytes([("NATIVE FIRST", False), ("OCR SECOND", True)])
        )
        visual = _VisualFixture()
        rep = self._capture(source)
        whole = self._target(rep, "whole", "{}")
        receipt = self._host(processor, visual).run_attempt(self._request(processor, rep, (whole,), cloud_allowed=True))
        self.assertEqual(processor.selected_pages, (2,))
        output = self.writer.archive.path_for_key(receipt.outputs[0].storage_key).read_text("utf-8")
        self.assertLess(output.index("NATIVE FIRST"), output.index("OCR SECOND"))
        evidence = self._evidence(receipt.process_run_id)
        self.assertEqual(evidence["ocr.page_text_coverage"], "1.0")
        self.assertEqual(evidence["ocr.native_page_count"], "1")
        self.assertEqual(evidence["ocr.ocr_page_count"], "1")
        self.assertEqual(evidence["ocr.ocr_page_ordinals"], "[2]")
        self.assertEqual(evidence["ocr.empty_page_ordinals"], "[]")
        self.assertEqual(receipt.decisions[0].decision, "quarantine_review")

    def test_page_scoped_ocr_rejects_native_text_instead_of_relabeling_it(self):
        source = _pdf_bytes([("ALREADY NATIVE", False)])
        processor = _SimulatedOcr(_pdf_bytes([("ALREADY NATIVE", False)]))
        rep = self._capture(source)
        page = self._target(rep, "pdf_page", '{"page_ordinal":1}')
        receipt = self._host(processor).run_attempt(self._request(processor, rep, (page,)))
        self.assertEqual(receipt.outcome, "failed")
        self.assertEqual(receipt.outputs, ())
        self.assertEqual(processor.ocr_calls, 0)

    def test_whole_native_document_fails_as_ocr_not_required(self):
        source = _pdf_bytes([("NATIVE", False), ("MORE NATIVE", False)])
        processor = _SimulatedOcr(source)
        rep = self._capture(source)
        whole = self._target(rep, "whole", "{}")
        receipt = self._host(processor).run_attempt(self._request(processor, rep, (whole,)))
        self.assertEqual(receipt.outcome, "failed")
        self.assertEqual(processor.ocr_calls, 0)
        con = local_connection(self.db)
        try:
            self.assertEqual(
                con.execute("SELECT error_code FROM process_runs WHERE id=?", (receipt.process_run_id,)).fetchone()[0],
                "ocr_not_required",
            )
        finally:
            con.close()

    def test_selected_page_output_preserves_requested_order(self):
        source = _pdf_bytes([(None, True), (None, True), (None, True)])
        processor = _SimulatedOcr(
            _pdf_bytes([("OCR ONE", True), ("OCR TWO", True), ("OCR THREE", True)])
        )
        rep = self._capture(source)
        p3 = self._target(rep, "pdf_page", '{"page_ordinal":3}')
        p1 = self._target(rep, "pdf_page", '{"page_ordinal":1}')
        receipt = self._host(processor, _VisualFixture()).run_attempt(
            self._request(processor, rep, (p3, p1))
        )
        self.assertEqual(processor.selected_pages, (3, 1))
        text = self.writer.archive.path_for_key(receipt.outputs[0].storage_key).read_text("utf-8")
        self.assertLess(text.index("OCR THREE"), text.index("OCR ONE"))

    def test_restricted_input_stays_local_and_derivative_remains_restricted(self):
        source = _pdf_bytes([(None, True)])
        processor = _SimulatedOcr(_pdf_bytes([("RESTRICTED OCR", True)]))
        visual = _VisualFixture()
        rep = self._capture(source, availability="restricted")
        page = self._target(rep, "pdf_page", '{"page_ordinal":1}')
        receipt = self._host(processor, visual).run_attempt(self._request(processor, rep, (page,)))
        self.assertEqual(receipt.decisions[0].decision, "quarantine_review")
        self.assertEqual(visual.calls, 0)
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

    def test_empty_post_ocr_output_cannot_be_accepted(self):
        source = _pdf_bytes([(None, True)])
        processor = _SimulatedOcr(_pdf_bytes([(None, True)]))
        rep = self._capture(source)
        page = self._target(rep, "pdf_page", '{"page_ordinal":1}')
        receipt = self._host(processor, _VisualFixture()).run_attempt(
            self._request(processor, rep, (page,), cloud_allowed=True)
        )
        self.assertEqual(receipt.outputs, ())
        self.assertEqual(receipt.decisions[0].decision, "escalate")
        self.assertEqual(self._evidence(receipt.process_run_id)["ocr.page_text_coverage"], "0.0")

    def test_intermediate_pdf_has_separate_bounded_size_limit(self):
        source = _pdf_bytes([(None, True)])
        output = _pdf_bytes([("OCR", True)])
        processor = _SimulatedOcr(
            output,
            config=OcrPdfConfig(max_intermediate_pdf_bytes=max(1, len(output) - 1)),
        )
        rep = self._capture(source)
        page = self._target(rep, "pdf_page", '{"page_ordinal":1}')
        receipt = self._host(processor).run_attempt(self._request(processor, rep, (page,)))
        self.assertEqual(receipt.outcome, "failed")
        con = local_connection(self.db)
        try:
            self.assertEqual(
                con.execute(
                    "SELECT error_code FROM process_runs WHERE id=?",
                    (receipt.process_run_id,),
                ).fetchone(),
                ("intermediate_pdf_too_large",),
            )
        finally:
            con.close()

    def test_page_limit_fails_before_ocr_invocation(self):
        source = _pdf_bytes([(None, True), (None, True)])
        processor = _SimulatedOcr(
            _pdf_bytes([("A", True), ("B", True)]),
            config=OcrPdfConfig(max_ocr_pages_per_attempt=1),
        )
        rep = self._capture(source)
        whole = self._target(rep, "whole", "{}")
        receipt = self._host(processor).run_attempt(self._request(processor, rep, (whole,)))
        self.assertEqual(receipt.outcome, "failed")
        self.assertEqual(processor.ocr_calls, 0)

    def test_clean_environment_excludes_secret_and_proxy_variables(self):
        processor = _SimulatedOcr(_pdf_bytes([("OCR", False)]))
        with tempfile.TemporaryDirectory() as tmp:
            env = processor._clean_env(Path(tmp))
        self.assertEqual(env["LC_ALL"], "C")
        self.assertEqual(env["LANG"], "C")
        self.assertEqual(env["OMP_THREAD_LIMIT"], "1")
        self.assertNotIn("OPENAI_API_KEY", env)
        self.assertNotIn("HTTPS_PROXY", env)
        self.assertNotIn("USER", env)
        self.assertNotIn("HOSTNAME", env)


    def test_timeout_kills_ocr_process_group_before_returning_failure(self):
        processor = _SimulatedOcr(
            _pdf_bytes([("OCR", True)]),
            config=OcrPdfConfig(command_timeout_seconds=1, attempt_timeout_seconds=2),
        )
        fake_process = MagicMock()
        fake_process.pid = 424242
        fake_process.communicate.side_effect = [
            subprocess.TimeoutExpired(["/trusted/ocr"], 1),
            (b"", b""),
        ]
        with tempfile.TemporaryDirectory() as tmp, patch(
            "actakit.processors.ocr.subprocess.Popen", return_value=fake_process
        ) as popen, patch("actakit.processors.ocr.os.killpg") as killpg:
            with self.assertRaises(subprocess.TimeoutExpired):
                processor._run(
                    ["/trusted/ocr"],
                    Path(tmp),
                    time.monotonic() + 1.5,
                )
        self.assertTrue(popen.call_args.kwargs["start_new_session"])
        killpg.assert_called_once_with(424242, signal.SIGKILL)
        self.assertEqual(fake_process.communicate.call_count, 2)

    def test_whole_scope_plan_runs_direct_then_ocr_and_stops_before_visual(self):
        source = _pdf_bytes([("NATIVE", False), (None, True)])
        rep = self._capture(source)
        whole = self._target(rep, "whole", "{}")
        direct = PopplerPdfTextProcessor.discover()
        ocr = _SimulatedOcr(_pdf_bytes([("NATIVE", False), ("OCR SECOND", True)]))
        plan = ProcessingPlan(
            rep,
            (whole,),
            (
                PlannedStep.allocate("text_extract", direct.configuration_hash),
                PlannedStep.allocate("ocr", ocr.configuration_hash),
            ),
        )
        receipt = self._host(direct, ocr).run_plan(plan)
        self.assertEqual(len(receipt.attempts), 2)
        self.assertEqual(receipt.attempts[0].decisions[0].decision, "escalate")
        self.assertEqual(receipt.attempts[1].decisions[0].decision, "quarantine_review")
        self.assertEqual(receipt.attempts[1].decisions[0].reason_code, "visual_escalation_unavailable")
        self.assertEqual(ocr.selected_pages, (2,))
        self.assertEqual(len(receipt.attempts[1].outputs), 1)


    def test_d1_empty_page_signal_can_drive_exact_d2_target(self):
        source = _pdf_bytes([("NATIVE", False), (None, True)])
        rep = self._capture(source)
        whole = self._target(rep, "whole", "{}")
        direct = PopplerPdfTextProcessor.discover()
        direct_receipt = self._host(direct).run_attempt(
            ProcessingRequest(rep, (whole,), "text_extract", direct.configuration_hash)
        )
        direct_evidence = self._evidence(direct_receipt.process_run_id)
        self.assertEqual(direct_evidence["native.empty_page_ordinals"], "[2]")

        page2 = self._target(rep, "pdf_page", '{"page_ordinal":2}')
        ocr = _SimulatedOcr(_pdf_bytes([("NATIVE", False), ("OCR PAGE TWO", True)]))
        ocr_receipt = self._host(ocr, _VisualFixture()).run_attempt(
            self._request(ocr, rep, (page2,), cloud_allowed=True)
        )
        self.assertEqual(ocr.selected_pages, (2,))
        self.assertEqual(ocr_receipt.decisions[0].decision, "escalate")
        self.assertEqual(self._evidence(ocr_receipt.process_run_id)["ocr.ocr_page_ordinals"], "[2]")


if __name__ == "__main__":
    unittest.main()
