"""Run the lightweight OCRmyPDF/Tesseract benchmark on controlled variants."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from metrics import read_text, text_metrics


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def first_line(command: list[str]) -> str:
    run = subprocess.run(command, capture_output=True, text=True, check=False)
    text = (run.stdout or run.stderr).strip()
    return text.splitlines()[0] if text else "unknown"


def timed(command: list[str]) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as temporary:
        timing = Path(temporary) / "time.txt"
        wrapped = command
        if Path("/usr/bin/time").exists():
            wrapped = ["/usr/bin/time", "-f", "%e\t%M", "-o", str(timing), *command]
        started = time.perf_counter()
        run = subprocess.run(wrapped, capture_output=True, text=True, check=False)
        elapsed = time.perf_counter() - started
        rss = None
        if timing.exists():
            fields = timing.read_text(encoding="utf-8").strip().split("\t")
            if len(fields) == 2:
                elapsed = float(fields[0])
                rss = int(fields[1])
        return {
            "returncode": run.returncode,
            "stderr": run.stderr,
            "wall_seconds": elapsed,
            "max_rss_kib": rss,
        }


def page_text(pdf: Path, page: int) -> str:
    run = subprocess.run(
        ["pdftotext", "-f", str(page), "-l", str(page), "-layout", str(pdf), "-"],
        capture_output=True,
        text=True,
        check=False,
    )
    return run.stdout


def run_case(
    *,
    label: str,
    source: Path,
    output: Path,
    truth: str,
    spans: list[str],
    input_page: int = 1,
    mixed: bool = False,
) -> dict[str, object]:
    output.parent.mkdir(parents=True, exist_ok=True)
    options = ["--deskew", "--rotate-pages"]
    if not mixed:
        options.append("--force-ocr")
    else:
        options.append("--skip-text")
    command = [sys.executable, "-m", "ocrmypdf", *options, "--output-type", "pdf", str(source), str(output)]
    run = timed(command)
    result: dict[str, object] = {
        "backend": "ocrmypdf+tesseract",
        "label": label,
        "input_sha256": sha256(source),
        "input_bytes": source.stat().st_size,
        "config": {
            "language": "spa+eng",
            "deskew": True,
            "rotate_pages": True,
            "force_ocr": not mixed,
            "mixed_skip_existing_text": mixed,
        },
        **run,
    }
    if output.exists():
        observed_page_1 = page_text(output, input_page)
        observed_page_2 = page_text(output, 2) if mixed else ""
        text = observed_page_1 + ("\n" + observed_page_2 if mixed else "")
        expected = truth if not mixed else truth + "\n" + truth
        result.update(
            {
                "output_sha256": sha256(output),
                "output_bytes": output.stat().st_size,
                "output_size_expansion": output.stat().st_size / source.stat().st_size,
                "metrics": text_metrics(expected, text, spans),
                "page_1_text_chars": len(observed_page_1.strip()),
                "page_2_text_chars": len(observed_page_2.strip()),
            }
        )
    else:
        result["output_sha256"] = None
        result["output_bytes"] = None
        result["expected_failure_observed"] = run["returncode"] != 0
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()

    bench = args.repo_root / "notebook/research/workbench/processors/bench"
    meta = json.loads((bench / "ground_truth/tse-esparza-alcaldias-p2.json").read_text())
    truth = read_text(bench / meta["truth_text"])
    spans = list(meta["required_spans"])
    variants = json.loads((args.work_dir / "controlled-variants.json").read_text())["variants"]
    output_dir = args.work_dir / "d2-outputs"
    runs = [
        run_case(
            label="clean_scan_300",
            source=Path(variants["clean_scan_300_pdf"]["path"]),
            output=output_dir / "clean_scan_300_ocr.pdf",
            truth=truth,
            spans=spans,
        ),
        run_case(
            label="lowdpi_110",
            source=Path(variants["lowdpi_110_pdf"]["path"]),
            output=output_dir / "lowdpi_110_ocr.pdf",
            truth=truth,
            spans=spans,
        ),
        run_case(
            label="skew_noise_300",
            source=Path(variants["skew_noise_300_pdf"]["path"]),
            output=output_dir / "skew_noise_300_ocr.pdf",
            truth=truth,
            spans=spans,
        ),
        run_case(
            label="mixed_native_scan",
            source=Path(variants["mixed_native_scan_pdf"]["path"]),
            output=output_dir / "mixed_native_scan_ocr.pdf",
            truth=truth,
            spans=spans,
            mixed=True,
        ),
    ]
    malformed = Path(variants["malformed_truncated_pdf"]["path"])
    malformed_output = output_dir / "malformed_ocr.pdf"
    malformed_run = timed(
        [sys.executable, "-m", "ocrmypdf", "--deskew", "--rotate-pages", str(malformed), str(malformed_output)]
    )
    runs.append(
        {
            "backend": "ocrmypdf+tesseract",
            "label": "malformed_truncated",
            "input_sha256": sha256(malformed),
            **malformed_run,
            "expected_failure_observed": malformed_run["returncode"] != 0,
        }
    )
    result = {
        "bench_state": "CIVIC_PROCESSOR_BENCH_PARTIAL__D2_LIGHTWEIGHT_LOCAL",
        "environment": {
            "python": sys.version.split()[0],
            "ocrmypdf": first_line([sys.executable, "-m", "ocrmypdf", "--version"]),
            "tesseract": first_line(["tesseract", "--version"]),
            "qpdf": first_line(["qpdf", "--version"]),
            "ghostscript": first_line(["gs", "--version"]),
            "tesseract_languages": "spa+eng+osd",
        },
        "runs": runs,
        "notes": [
            "OCRmyPDF is benchmark-only and installed outside ActaKit runtime packaging.",
            "Natural fixtures remain unscored; this run uses independently curated controlled truth.",
            "Tesseract confidence remains namespaced evidence, not universal confidence.",
        ],
    }
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
