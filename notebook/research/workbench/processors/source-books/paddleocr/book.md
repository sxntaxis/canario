---
id: ACTAKIT-BOOK-PADDLEOCR-001
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

# PaddleOCR / PP-StructureV3 / PaddleOCR-VL

## Question

What should ActaKit use for a local specialized document-AI escalation rung?

## Audit basis

Current PaddleOCR 3.7.0, PP-Structure/PaddleOCR-VL capabilities and independent OmniDocBench confirmation.

## Evidence horizon

- **PAD-S001 — PaddleOCR 3.7.0 PyPI:** 3.7.0 current 2026-06-11; Apache 2.0; PP-OCR/PP-Structure/PaddleOCR-VL stack. **Boundary:** Project performance claims need independent benchmark context.
- **PAD-S002 — PaddleOCR-VL 1.6 docs:** 0.9B specialized VLM with document parsing, tables/formulas/seals and strong benchmark result. **Boundary:** Vendor docs may emphasize best-case benchmarks.
- **PAD-S003 — PaddleOCR-VL pipeline docs:** PaddleOCR-VL as a top-level document pipeline. **Boundary:** Requires Paddle ecosystem/model deployment.
- **PAD-S004 — OmniDocBench v1.6 leaderboard:** Independent benchmark repository reports PaddleOCR-VL-1.6 overall 96.34. **Boundary:** Benchmark dataset is not a municipal-civic corpus.

## Claim ledger synopsis

- **PAD-C001:** PaddleOCR code is Apache 2.0 and supports a broad local OCR/document-processing stack. **ActaKit:** Licensing is comparatively attractive for an optional built-in local escalation.
- **PAD-C002:** PaddleOCR-VL-1.6 is a compact specialized VLM with independently reproduced top-tier OmniDocBench performance. **ActaKit:** Strong D4 local specialized document-AI candidate.
- **PAD-C003:** The stack handles layout/text/tables/formulas/seals rather than only plain OCR. **ActaKit:** Escalate hard pages/documents here when classical OCR or structured parsing is insufficient.
- **PAD-C004:** External benchmark leadership does not prove Costa Rican civic-document performance. **ActaKit:** Require Civic Processor Bench before adoption/freeze.

## Bounded transfer

Adapt PaddleOCR-VL as the leading local specialized visual-document escalation candidate, not the default path for all documents.

## Do not import

Do not run a VLM on born-digital PDFs that native extraction already handles correctly.

## Residual risk / unresolved question

Hardware/runtime footprint and Spanish civic-handwriting performance must be measured locally.

## Closure verdict

**adapt-after-benchmark** for the WP4C selection horizon. This Book is evidence, not implementation authorization.
