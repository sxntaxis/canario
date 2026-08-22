#!/usr/bin/env python3
"""Validate the processor research package ledgers without network access."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BOOKS = ROOT / "source-books"
SYNTHESIS = ROOT / "synthesis"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def refs(value: str) -> set[str]:
    return {part.strip() for part in value.split(";") if part.strip()}


def main() -> None:
    errors: list[str] = []
    index = rows(BOOKS / "INDEX.csv")
    indexed = {row["book"] for row in index}
    actual = {p.name for p in BOOKS.iterdir() if p.is_dir()}
    if indexed != actual:
        errors.append(f"INDEX mismatch indexed={sorted(indexed)} actual={sorted(actual)}")

    all_claims: set[str] = set()
    for book in sorted(actual):
        folder = BOOKS / book
        for required in ("book.md", "sources.csv", "claims.csv"):
            if not (folder / required).is_file():
                errors.append(f"{book}: missing {required}")
        source_rows = rows(folder / "sources.csv")
        claim_rows = rows(folder / "claims.csv")
        source_ids = {row["source_id"] for row in source_rows}
        claim_ids = {row["claim_id"] for row in claim_rows}
        if len(source_ids) != len(source_rows):
            errors.append(f"{book}: duplicate source_id")
        if len(claim_ids) != len(claim_rows):
            errors.append(f"{book}: duplicate claim_id")
        overlap = all_claims & claim_ids
        if overlap:
            errors.append(f"{book}: globally duplicate claim ids {sorted(overlap)}")
        all_claims |= claim_ids
        for claim in claim_rows:
            missing = refs(claim["evidence_refs"]) - source_ids
            if missing:
                errors.append(
                    f"{book}:{claim['claim_id']}: unresolved source refs {sorted(missing)}"
                )

    for required in (
        "BOOK.md",
        "claims.csv",
        "processor-matrix.csv",
        "escalation-ladder.md",
        "quality-evidence.md",
        "evaluation-plan.md",
        "cloud-execution.md",
        "transfers.csv",
        "gap-audit.md",
        "scenario-matrix.csv",
    ):
        if not (SYNTHESIS / required).is_file():
            errors.append(f"synthesis: missing {required}")

    synthesis_claims = rows(SYNTHESIS / "claims.csv")
    synthesis_ids = {row["claim_id"] for row in synthesis_claims}
    for claim in synthesis_claims:
        missing = refs(claim["evidence_refs"]) - all_claims
        if missing:
            errors.append(
                f"synthesis:{claim['claim_id']}: unresolved claim refs {sorted(missing)}"
            )

    accepted_refs = all_claims | synthesis_ids
    for transfer in rows(SYNTHESIS / "transfers.csv"):
        missing = refs(transfer["evidence_refs"]) - accepted_refs
        if missing:
            errors.append(
                f"transfer:{transfer['transfer_id']}: unresolved refs {sorted(missing)}"
            )

    if errors:
        print("PROCESSOR_RESEARCH_PACKAGE=FAIL")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("PROCESSOR_RESEARCH_PACKAGE=PASS")
    print(f"source_books={len(actual)}")
    print(f"source_claims={len(all_claims)}")
    print(f"synthesis_claims={len(synthesis_ids)}")
    print(f"transfers={len(rows(SYNTHESIS / 'transfers.csv'))}")


if __name__ == "__main__":
    main()
