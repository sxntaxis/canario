---
id: ACTAKIT-BOOK-MINERU-001
type: research-source-book
state: research-complete-for-selection-gate
authority: evidence
created: 2026-08-21
updated: 2026-08-21
researched_through: 2026-08-21
actakit_baseline: 02b5c3c9efad9207397c077d53aafac9f206cc86
source_ledger: sources.csv
claim_ledger: claims.csv
---

# MinerU

## Question

Does MinerU add enough unique structured-document value to justify another built-in framework?

## Audit basis

Current 3.4.4 release, feature surface and 2026 custom license.

## Evidence horizon

- **MIN-S001 — MinerU 3.4.4 PyPI:** 3.4.4 released 2026-07-10; document parsing package. **Boundary:** A 4.0 pre-release exists but is not the stable baseline.
- **MIN-S002 — MinerU current license:** Apache-2.0-based custom license with commercial thresholds and online-service attribution. **Boundary:** License terms require policy/legal review if adopted.
- **MIN-S003 — MinerU current pyproject:** PDF/images/DOCX/PPTX/XLSX, OCR/VLM ecosystem; custom LicenseRef. **Boundary:** Dependency surface is large and can overlap other chosen frameworks.
- **MIN-S004 — OmniDocBench v1.6 leaderboard:** MinerU2.5-Pro remains a top specialized parser. **Boundary:** Benchmark score does not measure integration complexity/license fit.

## Claim ledger synopsis

- **MIN-C001:** MinerU is a broad modern document parser with OCR/VLM and structured-output capabilities overlapping Docling/PaddleOCR. **ActaKit:** Use it as a serious benchmark comparator, not automatically another core framework.
- **MIN-C002:** Current MinerU license adds thresholds/attribution beyond plain Apache 2.0. **ActaKit:** Custom license raises maintenance/deployment cost relative to permissive alternatives.
- **MIN-C003:** MinerU demonstrates strong specialized document parsing performance. **ActaKit:** Include in external benchmark context even if not selected.
- **MIN-C004:** Adopting multiple overlapping structured-document frameworks would increase dependency/model policy complexity. **ActaKit:** Prefer one primary framework plus narrowly justified specialist backends.

## Bounded transfer

Defer implementation adoption; keep MinerU as benchmark/reference and revisit only if Civic Bench exposes a gap the chosen stack cannot close.

## Do not import

Do not stack Docling + MinerU + Marker simply for feature breadth.

## Residual risk / unresolved question

Fast-moving 4.0 pre-release may materially change architecture/license; re-audit if reconsidered.

## Closure verdict

**defer-reference** for the WP4C selection horizon. This Book is evidence, not implementation authorization.
