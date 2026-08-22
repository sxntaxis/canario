"""Score D1 and D2 on independently grounded natural civic page derivatives."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

from metrics import read_text, text_metrics
from run_d2_ocrmypdf import page_text, sha256, timed


CASES = {
    "natural-layout-esparza-p4": {
        "source": "work/natural-corpus/esparza-2026-concejo.pdf",
        "source_sha256": "ffb354c67d8b56ebf265884c820a98fee27015cadaac3ea1011069f7969b8bfd",
        "page": 4,
        "truth": "ground_truth/natural-layout/esparza-p4.json",
    },
    "natural-layout-quepos-p14": {
        "source": "work/natural-corpus/quepos-acta-086-2021.pdf",
        "source_sha256": "944f362c66e6a14abc3b31044968b467ed272b1ab04a52eb91ae7cafdfc23ac0",
        "page": 14,
        "truth": "ground_truth/natural-layout/quepos-p14.json",
    },
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    bench = args.repo_root / "notebook/research/workbench/processors/bench"
    results: list[dict[str, object]] = []
    for fixture_id, case in CASES.items():
        source = args.work_dir / "natural-corpus" / Path(case["source"]).name
        if sha256(source) != case["source_sha256"]:
            raise SystemExit(f"source hash mismatch: {source}")
        truth_meta_path = bench / case["truth"]
        truth_meta = json.loads(truth_meta_path.read_text(encoding="utf-8"))
        truth_path = bench / truth_meta["truth_text"]
        truth = read_text(truth_path)
        prefix = args.work_dir / "natural-layout" / fixture_id
        prefix.parent.mkdir(parents=True, exist_ok=True)
        image = prefix.with_suffix(".png")
        if not image.exists():
            subprocess.run(
                [
                    "pdftoppm",
                    "-f",
                    str(case["page"]),
                    "-l",
                    str(case["page"]),
                    "-r",
                    "300",
                    "-singlefile",
                    "-png",
                    str(source),
                    str(prefix),
                ],
                check=True,
            )
        image_pdf = image.with_suffix(".pdf")
        if not image_pdf.exists():
            with Image.open(image) as opened:
                opened.convert("RGB").save(image_pdf, "PDF", resolution=300.0)
        output = args.work_dir / "natural-layout" / f"{fixture_id}-ocr.pdf"
        run = timed(
            [
                sys.executable,
                "-m",
                "ocrmypdf",
                "--deskew",
                "--rotate-pages",
                "--force-ocr",
                "--output-type",
                "pdf",
                str(image_pdf),
                str(output),
            ]
        )
        native = page_text(source, int(case["page"]))
        record: dict[str, object] = {
            "fixture_id": fixture_id,
            "scoring_class": truth_meta["scoring_class"],
            "source_sha256": case["source_sha256"],
            "source_page": case["page"],
            "truth_sha256": sha256(truth_path),
            "truth_method": truth_meta["truth_method"],
            "rendered_input_sha256": sha256(image),
            "rendered_input_bytes": image.stat().st_size,
            "native_d1_metrics": text_metrics(truth, native, truth_meta["required_spans"]),
            "d2": {**run, "output_sha256": sha256(output) if output.exists() else None},
        }
        if output.exists():
            observed = page_text(output, 1)
            record["d2"]["metrics"] = text_metrics(truth, observed, truth_meta["required_spans"])
            record["d2"]["output_bytes"] = output.stat().st_size
        results.append(record)
    result = {
        "bench_state": "CIVIC_PROCESSOR_BENCH_PARTIAL__NATURAL_LAYOUT_CONTROLLED_D1_D2",
        "environment": {
            "ocrmypdf": "17.10.0",
            "tesseract": "tesseract 5.5.3",
            "rendering_dpi": 300,
            "language": "spa+eng",
        },
        "ground_truth_policy": "Native text was independently inspected against each rendered page; candidate OCR/Codex output was not used as truth.",
        "runs": results,
    }
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
