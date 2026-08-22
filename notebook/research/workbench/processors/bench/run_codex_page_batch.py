"""Run an isolated Codex page batch for scored or diagnostic public pages."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
from pathlib import Path

from metrics import read_text, text_metrics
from run_codex_transcription import sha256, token_diff, validate_output


def run_batch(bench: Path, work: Path, images: list[tuple[str, Path]]) -> dict[str, object]:
    scratch = work / "codex-page-batch"
    if scratch.exists():
        shutil.rmtree(scratch)
    scratch.mkdir(parents=True)
    copied: list[tuple[str, Path]] = []
    for page_id, source in images:
        target = scratch / f"{page_id}.png"
        shutil.copyfile(source, target)
        copied.append((page_id, target))
    prompt_path = bench / "codex_transcription_prompt_v1.md"
    schema_path = bench / "codex_transcription_schema.json"
    schema = scratch / "schema.json"
    shutil.copyfile(schema_path, schema)
    final_output = scratch / "final.json"
    command = [
        "codex",
        "exec",
        "--ephemeral",
        "--sandbox",
        "read-only",
        "--skip-git-repo-check",
        "--model",
        "gpt-5.6-sol",
        "--output-schema",
        str(schema),
        "--output-last-message",
        str(final_output),
        "--cd",
        str(scratch),
    ]
    for _, image in copied:
        command.extend(["--image", str(image)])
    command.append("-")
    started = time.perf_counter()
    run = subprocess.run(
        command,
        input=prompt_path.read_text(encoding="utf-8"),
        capture_output=True,
        text=True,
        check=False,
    )
    result: dict[str, object] = {
        "executor": "official_codex_cli",
        "executor_family": "subscription_agent",
        "codex_cli_version": "codex-cli 0.149.0",
        "model": "gpt-5.6-sol",
        "exec_mode": {"ephemeral": True, "sandbox": "read-only", "repository_exposed": False},
        "request_template_sha256": sha256(prompt_path),
        "output_schema_sha256": sha256(schema_path),
        "billing": {
            "billing_mode": "chatgpt_subscription",
            "per_call_api_cost_usd": "NOT_APPLICABLE",
            "subscription_quota_consumption": "NOT_RECORDED",
        },
        "pages_egressed": len(copied),
        "bytes_egressed": sum(path.stat().st_size for _, path in copied),
        "wall_seconds": time.perf_counter() - started,
        "returncode": run.returncode,
        "secret_recorded": False,
        "inputs": [
            {"page_id": page_id, "sha256": sha256(path), "bytes": path.stat().st_size}
            for page_id, path in copied
        ],
    }
    if run.returncode != 0 or not final_output.exists():
        result["status"] = "FAILED"
        result["failure"] = "codex_exec_nonzero_or_missing_output"
        return result
    value = json.loads(final_output.read_text(encoding="utf-8"))
    validate_output(value, [page_id for page_id, _ in copied])
    result["status"] = "PASS_SCHEMA_VALID"
    result["output_sha256"] = sha256(final_output)
    result["pages"] = value["pages"]
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--mode", choices=["scored", "actual"], required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    bench = args.repo_root / "notebook/research/workbench/processors/bench"
    if args.mode == "scored":
        image_specs = [
            ("natural-layout-esparza-p4", args.work_dir / "natural-layout/natural-layout-esparza-p4.png"),
            ("natural-layout-quepos-p14", args.work_dir / "natural-layout/natural-layout-quepos-p14.png"),
        ]
    else:
        image_specs = [
            ("actual-natural-fecomudi-p30", args.work_dir / "natural-layout/fecomudi-p30-30.png"),
            ("actual-natural-quepos-p14", args.work_dir / "natural-layout/quepos-p14-14.png"),
        ]
    result = run_batch(bench, args.work_dir, image_specs)
    if args.mode == "scored" and result.get("status") == "PASS_SCHEMA_VALID":
        truth_by_id = {
            "natural-layout-esparza-p4": bench / "ground_truth/natural-layout/esparza-p4.json",
            "natural-layout-quepos-p14": bench / "ground_truth/natural-layout/quepos-p14.json",
        }
        scored_pages = []
        for page in result["pages"]:
            meta = json.loads(truth_by_id[page["page_id"]].read_text(encoding="utf-8"))
            truth = read_text(bench / meta["truth_text"])
            scored_pages.append(
                {
                    "page_id": page["page_id"],
                    "transcription": page["transcription"],
                    "uncertain_spans": page["uncertain_spans"],
                    "tables": page["tables"],
                    "metrics": {**text_metrics(truth, page["transcription"], meta["required_spans"]), **token_diff(truth, page["transcription"])},
                    "table_metrics": "NO_INDEPENDENT_TABLE_TRUTH",
                }
            )
        result["pages"] = scored_pages
        result["ground_truth_policy"] = "Independent native text visually checked against each public source page; not candidate-generated."
    elif result.get("status") == "PASS_SCHEMA_VALID":
        result["pages"] = [
            {
                "page_id": page["page_id"],
                "transcription_chars": len(page["transcription"]),
                "uncertain_span_count": len(page["uncertain_spans"]),
                "table_count": len(page["tables"]),
            }
            for page in result["pages"]
        ]
        result["ground_truth"] = "UNSCORED_NATURAL"
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
