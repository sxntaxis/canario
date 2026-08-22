"""Research-only Codex CLI transcription benchmark harness."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import time
from collections import Counter
from pathlib import Path

from metrics import normalize_text, read_text, text_metrics


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def version() -> str:
    run = subprocess.run(["codex", "--version"], capture_output=True, text=True, check=False)
    return (run.stdout or run.stderr).strip().splitlines()[0]


def validate_output(value: object, page_ids: list[str]) -> None:
    if not isinstance(value, dict) or set(value) != {"pages"}:
        raise ValueError("Codex output is not the expected top-level object")
    pages = value["pages"]
    if not isinstance(pages, list) or len(pages) != len(page_ids):
        raise ValueError("Codex output page count does not match attached images")
    seen: set[str] = set()
    for page in pages:
        if not isinstance(page, dict) or set(page) != {
            "page_id",
            "transcription",
            "uncertain_spans",
            "tables",
        }:
            raise ValueError("Codex output page violates the exact output contract")
        if page["page_id"] not in page_ids or page["page_id"] in seen:
            raise ValueError("Codex output has an unknown or duplicate page ID")
        if not isinstance(page["transcription"], str):
            raise ValueError("Codex transcription is not a string")
        if not isinstance(page["uncertain_spans"], list) or not all(
            isinstance(item, str) for item in page["uncertain_spans"]
        ):
            raise ValueError("Codex uncertain_spans is invalid")
        if not isinstance(page["tables"], list):
            raise ValueError("Codex tables is invalid")
        seen.add(page["page_id"])


def token_diff(truth: str, observed: str) -> dict[str, list[dict[str, object]]]:
    expected = Counter(normalize_text(truth).split())
    actual = Counter(normalize_text(observed).split())
    return {
        "unexpected_tokens": [
            {"token": token, "count": count} for token, count in sorted((actual - expected).items())
        ],
        "missing_tokens": [
            {"token": token, "count": count} for token, count in sorted((expected - actual).items())
        ],
    }


def table_metrics(observed_tables: list[object], expected_rows: list[list[str]]) -> dict[str, object]:
    rows: list[list[str]] = []
    for table in observed_tables:
        if isinstance(table, dict) and isinstance(table.get("rows"), list):
            rows.extend(row for row in table["rows"] if isinstance(row, list) and all(isinstance(cell, str) for cell in row))
    expected_by_key = {normalize_text(row[0]): row for row in expected_rows}
    candidates = [row for row in rows if row and normalize_text(row[0]) in expected_by_key]
    matched_rows = 0
    matched_cells = 0
    false_cells = 0
    for row in candidates:
        expected = expected_by_key[normalize_text(row[0])]
        matches = sum(
            index < len(row) and normalize_text(row[index]) == normalize_text(cell)
            for index, cell in enumerate(expected)
        )
        matched_cells += matches
        matched_rows += matches == len(expected)
        false_cells += sum(
            1 for index, cell in enumerate(row) if index >= len(expected) and normalize_text(cell)
        )
        false_cells += len(expected) - matches
    expected_cell_count = sum(len(row) for row in expected_rows)
    return {
        "observed_table_count": len(observed_tables),
        "observed_row_count": len(rows),
        "candidate_row_count": len(candidates),
        "expected_row_count": len(expected_rows),
        "exact_row_recall": matched_rows / len(expected_rows) if expected_rows else 1.0,
        "cell_fidelity": matched_cells / expected_cell_count if expected_cell_count else 1.0,
        "false_cell_count": false_cells,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--model", required=True)
    args = parser.parse_args()

    bench = args.repo_root / "notebook/research/workbench/processors/bench"
    control = args.work_dir / "control-tse"
    source = bench / "ground_truth/tse-esparza-alcaldias-p2.json"
    metadata = json.loads(source.read_text(encoding="utf-8"))
    truth = read_text(bench / metadata["truth_text"])
    spans = list(metadata["required_spans"])
    expected_rows = [list(row) for row in metadata["table_rows"]]
    scratch = args.work_dir / "codex-run"
    if scratch.exists():
        shutil.rmtree(scratch)
    scratch.mkdir(parents=True)

    image_sources = [
        ("clean_scan_300", control / "tse-p2-clean-scan-300.png"),
        ("lowdpi_110", control / "tse-p2-lowdpi-110.png"),
        ("skew_noise_300", control / "tse-p2-skew-noise-300.png"),
    ]
    mixed_prefix = scratch / "mixed-page"
    subprocess.run(
        [
            "pdftoppm",
            "-f",
            "2",
            "-l",
            "2",
            "-r",
            "300",
            "-png",
            str(control / "tse-p2-mixed-native-scan.pdf"),
            str(mixed_prefix),
        ],
        check=True,
        capture_output=True,
    )
    image_sources.append(("mixed_scan_page2", scratch / "mixed-page-2.png"))
    images: list[tuple[str, Path]] = []
    for page_id, source_path in image_sources:
        target = scratch / f"{page_id}.png"
        shutil.copyfile(source_path, target)
        images.append((page_id, target))

    prompt_path = bench / "codex_transcription_prompt_v1.md"
    schema_path = bench / "codex_transcription_schema.json"
    prompt = prompt_path.read_text(encoding="utf-8")
    schema_copy = scratch / "output-schema.json"
    shutil.copyfile(schema_path, schema_copy)
    output_path = scratch / "result.json"
    command = [
        "codex",
        "exec",
        "--ephemeral",
        "--sandbox",
        "read-only",
        "--skip-git-repo-check",
        "--model",
        args.model,
        "--output-schema",
        str(schema_copy),
        "--output-last-message",
        str(output_path),
        "--cd",
        str(scratch),
    ]
    for _, image in images:
        command.extend(["--image", str(image)])
    command.append("-")
    started = time.perf_counter()
    run = subprocess.run(command, input=prompt, capture_output=True, text=True, check=False)
    elapsed = time.perf_counter() - started
    result: dict[str, object] = {
        "bench_state": "CIVIC_PROCESSOR_BENCH_PARTIAL__CODEX_CONTROLLED_HARD_SUBSET",
        "executor": "official_codex_cli",
        "executor_family": "subscription_agent",
        "codex_cli_version": version(),
        "model": args.model,
        "execution_venue": "cloud",
        "exec_mode": {"ephemeral": True, "sandbox": "read-only", "repository_exposed": False},
        "request_template": {
            "version": "codex_transcription_prompt_v1",
            "sha256": sha256(prompt_path),
        },
        "output_schema": {"path": "codex_transcription_schema.json", "sha256": sha256(schema_path)},
        "billing": {
            "billing_mode": "chatgpt_subscription",
            "per_call_api_cost_usd": "NOT_APPLICABLE",
            "subscription_quota_consumption": "NOT_RECORDED",
        },
        "secret_recorded": False,
        "pages_egressed": len(images),
        "bytes_egressed": sum(path.stat().st_size for _, path in images),
        "wall_seconds": elapsed,
        "returncode": run.returncode,
        "stderr_not_recorded": True,
        "inputs": [
            {"page_id": page_id, "sha256": sha256(path), "bytes": path.stat().st_size}
            for page_id, path in images
        ],
    }
    if run.returncode != 0 or not output_path.exists():
        result["status"] = "FAILED"
        result["failure"] = "codex_exec_nonzero_or_missing_output"
    else:
        try:
            output = json.loads(output_path.read_text(encoding="utf-8"))
            page_ids = [page_id for page_id, _ in images]
            validate_output(output, page_ids)
            result["status"] = "PASS_SCHEMA_VALID"
            result["pages"] = [
                {
                    "page_id": page["page_id"],
                    "transcription": page["transcription"],
                    "uncertain_spans": page["uncertain_spans"],
                    "tables": page["tables"],
                    "metrics": {
                        **text_metrics(truth, page["transcription"], spans),
                        **token_diff(truth, page["transcription"]),
                    },
                    "table_metrics": table_metrics(page["tables"], expected_rows),
                    "uncertain_span_count": len(page["uncertain_spans"]),
                    "table_count": len(page["tables"]),
                }
                for page in output["pages"]
            ]
            result["output_sha256"] = sha256(output_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            result["status"] = "FAILED_SCHEMA_OR_JSON"
            result["failure"] = type(exc).__name__
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
