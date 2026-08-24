from __future__ import annotations

import hashlib
import json
import re
import argparse
from pathlib import Path
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parents[5]
BENCH = Path(__file__).resolve().parent
CORPUS = BENCH / "corpus.yaml"
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"OPENAI_API_KEY\s*=\s*[^\s$][^\s]*"),
]
PRIVACY_PATTERNS = [
    re.compile("platform" + r"\.platform|os\.cpu" + "_count|cpu" + "_count"),
    re.compile("nvidia" + "-smi|/proc/cpu" + "info|\\bls" + "pci\\b|\\bls" + "hw\\b|\\bvulkan" + "info\\b"),
    re.compile(r"\b" + "host" + "name" + r"\b|Linux-[0-9]+\.[0-9]+|" + "Ry" + "zen" + r"\s+[0-9]"),
    re.compile(r"\b[0-9]+\s+GiB\b|" + "swap" + r"\s+(?:usage|total)", re.IGNORECASE),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--require-corpus",
        action="store_true",
        help="Require every ready_unscored fixture's ignored local bytes and verify their hashes.",
    )
    args = parser.parse_args()
    corpus = yaml.safe_load(CORPUS.read_text(encoding="utf-8"))
    fixtures = corpus.get("fixtures", [])
    ids = [item["id"] for item in fixtures]
    assert len(ids) == len(set(ids)), "duplicate corpus fixture IDs"

    ready = [item for item in fixtures if item.get("status") == "ready"]
    ready_unscored = [item for item in fixtures if item.get("status") == "ready_unscored"]
    assert ready, "bench requires at least one ready civic fixture"
    for item in ready:
        source = ROOT / item["source_path"]
        assert source.exists(), source
        assert sha256(source) == item["source_sha256"], f"hash mismatch: {source}"
        truth = BENCH / item["ground_truth"]
        meta = json.loads(truth.read_text(encoding="utf-8"))
        assert meta["source_pdf_sha256"] == item["source_sha256"]
        truth_text = BENCH / meta["truth_text"]
        assert truth_text.exists() and truth_text.read_text(encoding="utf-8").strip()
        assert meta.get("required_spans")

    missing_corpus: list[str] = []
    for item in ready_unscored:
        digest = item.get("source_sha256", "")
        assert re.fullmatch(r"[0-9a-f]{64}", digest), item["id"]
        parsed = urlparse(item.get("source_url", ""))
        assert parsed.scheme == "https" and parsed.netloc, item["id"]
        assert item.get("media_type"), item["id"]
        if item.get("page_count") is not None:
            assert isinstance(item["page_count"], int) and item["page_count"] > 0
        assert item.get("ground_truth") == "UNSCORED_NATURAL"
        assert item.get("public_classification") in {"public", "restricted"}
        assert item.get("egress_policy")
        source_path = item.get("source_path")
        if args.require_corpus:
            assert source_path, item["id"]
            source = ROOT / source_path
            if not source.exists():
                missing_corpus.append(item["id"])
            else:
                assert sha256(source) == digest, f"hash mismatch: {source}"

    if missing_corpus:
        print(
            "CIVIC_PROCESSOR_BENCH_STRICT_CORPUS=NOT_AVAILABLE "
            f"missing={','.join(missing_corpus)}"
        )
        return 2

    scanned = 0
    for path in BENCH.rglob("*"):
        if not path.is_file() or "work" in path.parts:
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".pdf", ".bin"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        scanned += 1
        for pattern in SECRET_PATTERNS:
            assert pattern.search(text) is None, f"secret-like material in {path}"
        for pattern in PRIVACY_PATTERNS:
            assert pattern.search(text) is None, f"host-fingerprint material in {path}"

    result = BENCH / "results/natural-corpus-d1-and-availability.json"
    if result.exists():
        evidence = json.loads(result.read_text(encoding="utf-8"))
        assert evidence.get("cloud", {}).get("secret_recorded") is False
        assert evidence.get("cloud", {}).get("bytes_egressed") == 0

    print(
        "CIVIC_PROCESSOR_BENCH_PACKAGE=PASS "
        f"fixtures={len(fixtures)} ready={len(ready)} ready_unscored={len(ready_unscored)} "
        f"strict_corpus={args.require_corpus} text_files_scanned={scanned}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
