from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from metrics import read_text, text_metrics


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Record and score a non-secret cloud benchmark output. This script does not call a provider API."
    )
    parser.add_argument("--truth-meta", type=Path, required=True)
    parser.add_argument("--output-text", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--endpoint-profile", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--request-template", type=Path, required=True)
    parser.add_argument("--input-pages", required=True, help="comma-separated 1-based page ordinals")
    parser.add_argument("--bytes-egressed", type=int, required=True)
    parser.add_argument("--latency-ms", type=float, required=True)
    parser.add_argument("--retention-profile", required=True)
    parser.add_argument("--usage-json", type=Path)
    parser.add_argument("--cost-usd", type=float)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()

    meta = json.loads(args.truth_meta.read_text(encoding="utf-8"))
    truth_path = args.truth_meta.parent.parent / meta["truth_text"]
    truth = read_text(truth_path)
    observed = read_text(args.output_text)
    pages = [int(item) for item in args.input_pages.split(",") if item.strip()]
    if not pages or any(page < 1 for page in pages):
        raise SystemExit("input pages must be positive 1-based ordinals")
    if args.bytes_egressed < args.input.stat().st_size:
        raise SystemExit("bytes-egressed cannot be smaller than the supplied input artifact")

    usage = None
    if args.usage_json:
        usage = json.loads(args.usage_json.read_text(encoding="utf-8"))

    record = {
        "provider_id": args.provider,
        "endpoint_profile": args.endpoint_profile,
        "model_id": args.model,
        "fixture_id": meta["fixture_id"],
        "input_sha256": sha256_file(args.input),
        "input_pages": pages,
        "input_bytes_egressed": args.bytes_egressed,
        "request_template_id": args.request_template.name,
        "request_template_sha256": sha256_file(args.request_template),
        "latency_ms": args.latency_ms,
        "usage": usage,
        "cost_usd": args.cost_usd,
        "retention_profile": args.retention_profile,
        "response_text_sha256": sha256_file(args.output_text),
        "secret_recorded": False,
        "metrics": text_metrics(truth, observed, meta.get("required_spans", [])),
        "notes": [
            "Credential material is intentionally absent; the provider invocation happens outside this recorder.",
            "Provider/model scores are benchmark evidence only and do not authorize production cloud processing.",
        ],
    }
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
