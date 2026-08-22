from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pdfplumber
from PIL import __version__ as pillow_version

from metrics import normalize_text, read_text, text_metrics


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def first_line(command: list[str]) -> str:
    proc = subprocess.run(command, check=False, text=True, capture_output=True)
    text = (proc.stdout or proc.stderr).strip()
    return text.splitlines()[0] if text else "unknown"


def timed_command(command: list[str], *, stdout_path: Path | None = None) -> dict[str, object]:
    time_bin = Path("/usr/bin/time")
    max_rss_kib: int | None = None
    elapsed = 0.0
    with tempfile.TemporaryDirectory() as td:
        timing = Path(td) / "time.txt"
        wrapped = command
        if time_bin.exists():
            wrapped = [str(time_bin), "-f", "%e\t%M", "-o", str(timing), *command]
        start = time.perf_counter()
        if stdout_path is None:
            proc = subprocess.run(wrapped, check=False, text=True, capture_output=True)
            stdout = proc.stdout
        else:
            with stdout_path.open("w", encoding="utf-8") as out:
                proc = subprocess.run(wrapped, check=False, text=True, stdout=out, stderr=subprocess.PIPE)
            stdout = ""
        elapsed = time.perf_counter() - start
        if timing.exists():
            raw = timing.read_text(encoding="utf-8").strip().split("\t")
            if len(raw) == 2:
                try:
                    elapsed = float(raw[0])
                    max_rss_kib = int(raw[1])
                except ValueError:
                    pass
    return {
        "returncode": proc.returncode,
        "stdout": stdout,
        "stderr": proc.stderr,
        "wall_seconds": elapsed,
        "max_rss_kib": max_rss_kib,
        "command": command,
    }


def tesseract_confidence(image: Path, language: str, psm: int) -> dict[str, object]:
    proc = subprocess.run(
        ["tesseract", str(image), "stdout", "-l", language, "--psm", str(psm), "tsv"],
        check=True,
        text=True,
        capture_output=True,
    )
    reader = csv.DictReader(proc.stdout.splitlines(), delimiter="\t")
    values: list[float] = []
    for row in reader:
        try:
            confidence = float(row.get("conf", "-1"))
        except ValueError:
            continue
        if confidence >= 0 and (row.get("text") or "").strip():
            values.append(confidence)
    if not values:
        return {
            "signal": "tesseract.word_confidence",
            "count": 0,
            "mean": None,
            "median": None,
            "p10": None,
        }
    values.sort()
    p10_index = max(0, int(round((len(values) - 1) * 0.10)))
    return {
        "signal": "tesseract.word_confidence",
        "count": len(values),
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "p10": values[p10_index],
    }


def run_poppler(pdf: Path, page: int, truth: str, spans: list[str], out_dir: Path, label: str) -> dict[str, object]:
    output = out_dir / f"{label}.txt"
    run = timed_command(
        ["pdftotext", "-f", str(page), "-l", str(page), "-layout", str(pdf), str(output)]
    )
    observed = output.read_text(encoding="utf-8", errors="replace") if output.exists() else ""
    result = {
        "backend": "poppler.pdftotext",
        "label": label,
        "input": str(pdf),
        "input_sha256": sha256(pdf),
        "execution_venue": "deterministic_local",
        "returncode": run["returncode"],
        "wall_seconds": run["wall_seconds"],
        "max_rss_kib": run["max_rss_kib"],
        "stderr": run["stderr"],
        "metrics": text_metrics(truth, observed, spans),
        "observed_text_path": str(output),
        "observed_text_sha256": sha256(output) if output.exists() else None,
    }
    return result


def run_tesseract(image: Path, truth: str, spans: list[str], out_dir: Path, label: str) -> dict[str, object]:
    output = out_dir / f"{label}.txt"
    run = timed_command(
        ["tesseract", str(image), "stdout", "-l", "spa", "--psm", "3"],
        stdout_path=output,
    )
    observed = output.read_text(encoding="utf-8", errors="replace") if output.exists() else ""
    return {
        "backend": "tesseract",
        "label": label,
        "input": str(image),
        "input_sha256": sha256(image),
        "execution_venue": "deterministic_local",
        "config": {"language": "spa", "psm": 3},
        "returncode": run["returncode"],
        "wall_seconds": run["wall_seconds"],
        "max_rss_kib": run["max_rss_kib"],
        "stderr": run["stderr"],
        "quality_evidence": [tesseract_confidence(image, "spa", 3)],
        "metrics": text_metrics(truth, observed, spans),
        "observed_text_path": str(output),
        "observed_text_sha256": sha256(output) if output.exists() else None,
    }


def normalize_cell(value: object) -> str:
    return normalize_text("" if value is None else str(value))



def run_expected_failure(command: list[str], input_path: Path, label: str) -> dict[str, object]:
    run = timed_command(command)
    return {
        "backend": "poppler.pdftotext",
        "label": label,
        "input": str(input_path),
        "input_sha256": sha256(input_path),
        "execution_venue": "deterministic_local",
        "returncode": run["returncode"],
        "wall_seconds": run["wall_seconds"],
        "max_rss_kib": run["max_rss_kib"],
        "stderr": run["stderr"],
        "expected_failure_observed": run["returncode"] != 0,
    }


def run_pdfplumber_table(pdf: Path, page: int, expected_rows: list[list[str]]) -> dict[str, object]:
    start = time.perf_counter()
    with pdfplumber.open(pdf) as doc:
        tables = doc.pages[page - 1].extract_tables()
    elapsed = time.perf_counter() - start
    normalized_tables = [
        [[normalize_cell(cell) for cell in row] for row in table]
        for table in tables
    ]
    expected = [[normalize_cell(cell) for cell in row] for row in expected_rows]
    matches: list[list[str]] = []
    for table in normalized_tables:
        for row in table:
            row4 = row[:4]
            if row4 in expected and row4 not in matches:
                matches.append(row4)
    return {
        "backend": "pdfplumber.table",
        "label": "tse-p2-native-table",
        "input": str(pdf),
        "input_sha256": sha256(pdf),
        "execution_venue": "deterministic_local",
        "wall_seconds": elapsed,
        "tables_detected": len(tables),
        "expected_rows": len(expected),
        "exact_rows_matched": len(matches),
        "exact_row_recall": len(matches) / len(expected) if expected else 1.0,
        "matched_rows": matches,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()

    bench = args.repo_root / "notebook/research/workbench/processors/bench"
    truth_meta = json.loads((bench / "ground_truth/tse-esparza-alcaldias-p2.json").read_text(encoding="utf-8"))
    truth = read_text(bench / truth_meta["truth_text"])
    spans = list(truth_meta["required_spans"])
    source = args.repo_root / "notebook/research/pre-sql/fixtures/artifact-proofs/alcaldias_pu.pdf"
    if sha256(source) != truth_meta["source_pdf_sha256"]:
        raise SystemExit("TSE source PDF hash mismatch")

    variants_manifest = args.work_dir / "controlled-variants.json"
    if not variants_manifest.exists():
        subprocess.run(
            [
                sys.executable,
                str(bench / "generate_controlled_variants.py"),
                "--source", str(source),
                "--source-sha256", truth_meta["source_pdf_sha256"],
                "--page", str(truth_meta["page_ordinal"]),
                "--work-dir", str(args.work_dir),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )
    variants = json.loads(variants_manifest.read_text(encoding="utf-8"))["variants"]
    out_dir = args.work_dir / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    runs: list[dict[str, object]] = []
    runs.append(run_poppler(source, truth_meta["page_ordinal"], truth, spans, out_dir, "tse-p2-native-poppler"))
    for key in ("clean_scan_300_pdf", "lowdpi_110_pdf", "skew_noise_300_pdf"):
        runs.append(
            run_poppler(Path(variants[key]["path"]), 1, truth, spans, out_dir, f"tse-p2-{key}-poppler")
        )

    # Same civic page twice: first native, second image-only. Poppler should expose
    # the partial-document coverage problem instead of looking like complete success.
    runs.append(
        run_poppler(
            Path(variants["mixed_native_scan_pdf"]["path"]),
            1,
            truth + "\n" + truth,
            spans,
            out_dir,
            "tse-p2-mixed-native-scan-poppler",
        )
    )

    malformed = Path(variants["malformed_truncated_pdf"]["path"])
    runs.append(
        run_expected_failure(
            ["pdftotext", str(malformed), "-"],
            malformed,
            "tse-p2-malformed-poppler",
        )
    )
    for key in ("clean_scan_300_png", "lowdpi_110_png", "skew_noise_300_png"):
        runs.append(
            run_tesseract(Path(variants[key]["path"]), truth, spans, out_dir, f"tse-p2-{key}-tesseract")
        )
    runs.append(run_pdfplumber_table(source, truth_meta["page_ordinal"], truth_meta["table_rows"]))

    result = {
        "bench_state": "CIVIC_PROCESSOR_BENCH_PARTIAL__CONTROLLED_LOCAL_BASELINE",
        "fixture": truth_meta["fixture_id"],
        "source_sha256": truth_meta["source_pdf_sha256"],
        "environment": {
            "python": sys.version.split()[0],
            "pdftotext": first_line(["pdftotext", "-v"]),
            "tesseract": first_line(["tesseract", "--version"]),
            "pillow": pillow_version,
            "pdfplumber": pdfplumber.__version__,
        },
        "notes": [
            "This run validates bench mechanics and local D1/D2 signals; it does not select shipped processor defaults.",
            "The controlled scan variants are deterministic derivatives of an official public civic PDF and share manually curated ground truth.",
            "Tesseract confidence is recorded only as a namespaced engine-specific signal, never as universal confidence.",
        ],
        "runs": runs,
    }
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
