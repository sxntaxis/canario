---
id: ACTAKIT-BOOK-OMNIDOCBENCH-001
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

# OmniDocBench

## Question

How should ActaKit use external document-parsing benchmarks without selecting processors by leaderboard alone?

## Audit basis

Current OmniDocBench v1.6 benchmark design and leaderboard.

## Evidence horizon

- **ODB-S001 — OmniDocBench repository README:** End-to-end metrics for text edit distance, table TEDS, formula CDM and reading order; current v1.6 leaderboard. **Boundary:** Dataset is research/evaluation material, not a Costa Rican municipal corpus.
- **ODB-S002 — OmniDocBench paper/repository:** Multi-type/language/layout benchmark including challenging document content. **Boundary:** Benchmark composition differs from ActaKit’s civic source distribution.

## Claim ledger synopsis

- **ODB-C001:** Document parsing quality is multidimensional: text, table structure, formula and reading order can move independently. **ActaKit:** ActaKit benchmark must score multiple dimensions, not a single “OCR accuracy”.
- **ODB-C002:** Current v1.6 leaderboard places PaddleOCR-VL-1.6 at 96.34 overall. **ActaKit:** Use as an external sanity signal for D4 candidates, not a selection verdict.
- **ODB-C003:** Public benchmark leadership may not predict performance on municipal scans, stamps, photocopies or handwriting. **ActaKit:** Create an ActaKit Civic Processor Bench with real representative fixtures.
- **ODB-C004:** Reading order and table structure deserve explicit metrics. **ActaKit:** Benchmark locator reopenability, reading order and tables separately from raw text similarity.

## Bounded transfer

Adopt benchmark discipline and metrics; use OmniDocBench as external comparison while making Civic Processor Bench the actual selection gate.

## Do not import

Do not pick a stack from one leaderboard score.

## Residual risk / unresolved question

Need legally usable representative civic fixtures and ground truth.

## Closure verdict

**adopt-evaluation-principles** for the WP4C selection horizon. This Book is evidence, not implementation authorization.
