from __future__ import annotations

import hashlib
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from canario.deposit.ids import new_id
from canario.lector import SemanticLocatorError, reopen_selector
from canario.processors import (
    MediaInspectionProcessor,
    ProcessingRequest,
    ProcessorInvocation,
    StructuredTableProcessor,
    TargetSnapshot,
)
from canario.processors.targets import TargetRegistry


def invocation(data: bytes, media_type: str, selector_kind: str = "whole") -> ProcessorInvocation:
    representation_id = new_id("rep_")
    target_id = new_id("rtgt_")
    request = ProcessingRequest(representation_id, (target_id,), "fixture")
    return ProcessorInvocation(
        request,
        "original",
        media_type,
        None,
        None,
        data,
        (TargetSnapshot(target_id, representation_id, selector_kind, "v1", "{}"),),
    )


class TypedEvidenceTests(unittest.TestCase):
    def test_workbook_derivative_preserves_sheets_types_and_formula_text(self) -> None:
        workbook = Workbook()
        first = workbook.active
        first.title = "Alpha"
        first.append(["Name", "Amount", None])
        first.append(["x", 4, "=B2*2"])
        second = workbook.create_sheet("Beta")
        second["A1"] = True
        stream = io.BytesIO()
        workbook.save(stream)

        result = StructuredTableProcessor().process(
            invocation(
                stream.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        )
        self.assertEqual(result.outcome, "success")
        payload = json.loads(result.outputs[0].data)
        self.assertEqual([sheet["name"] for sheet in payload["sheets"]], ["Alpha", "Beta"])
        self.assertEqual(payload["sheets"][0]["rows"][1][1]["value"], {"type": "integer", "value": 4})
        self.assertEqual(payload["sheets"][0]["rows"][1][2]["value"]["type"], "formula")
        selector = json.dumps({
            "sheet": "Alpha",
            "a1_range": "A2:C2",
            "row_start": 2,
            "row_end": 2,
            "observed_values": [
                [
                    {"type": "string", "value": "x"},
                    {"type": "integer", "value": 4},
                    {"type": "formula", "value": "=B2*2"},
                ]
            ],
        })
        reopen_selector("table_range", "v1", selector, source_bytes=result.outputs[0].data, charset="utf-8")
        with self.assertRaises(SemanticLocatorError):
            reopen_selector("table_range", "v1", selector.replace("Alpha", "Beta"), source_bytes=result.outputs[0].data, charset="utf-8")

    def test_media_selector_is_digest_bound_and_duration_bounded(self) -> None:
        source = b"controlled media bytes"
        digest = hashlib.sha256(source).hexdigest()
        selector = json.dumps({
            "media_sha256": digest,
            "duration_us": 2_000_000,
            "start_us": 500_000,
            "end_us": 1_500_000,
        })
        TargetRegistry().validate("media", "v1", selector)
        reopen_selector("media", "v1", selector, source_bytes=source, charset=None)
        with self.assertRaises(SemanticLocatorError):
            reopen_selector("media", "v1", selector.replace("1500000", "2500000"), source_bytes=source, charset=None)
        with self.assertRaises(SemanticLocatorError):
            reopen_selector("media", "v1", selector, source_bytes=b"other", charset=None)

    @unittest.skipUnless(shutil.which("ffprobe") and shutil.which("ffmpeg"), "ffmpeg toolchain unavailable")
    def test_media_processor_records_integer_duration_and_source_digest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.mp4"
            subprocess.run(
                ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=16x16:d=1", "-f", "lavfi", "-i", "anullsrc=r=8000:cl=mono", "-t", "1", str(path)],
                check=True,
            )
            source = path.read_bytes()
        result = MediaInspectionProcessor().process(invocation(source, "video/mp4"))
        self.assertEqual(result.outcome, "success")
        payload = json.loads(result.outputs[0].data)
        self.assertEqual(payload["source_sha256"], hashlib.sha256(source).hexdigest())
        self.assertGreater(payload["duration_us"], 0)


if __name__ == "__main__":
    unittest.main()
