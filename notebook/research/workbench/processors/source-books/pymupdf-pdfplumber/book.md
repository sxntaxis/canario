---
id: ACTAKIT-BOOK-PYMUPDF_PDFPLUMBER-001
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

# PyMuPDF and pdfplumber

## Question

What value do Python-native PDF geometry/tooling libraries add, and what licensing/deployment constraints matter?

## Audit basis

Current project documentation for extraction geometry, OCR integration, tables, diagnostics and licenses.

## Evidence horizon

- **PYP-S001 — PyMuPDF 1.28.2 documentation:** Current extraction API, text/blocks/words/dict/rawdict and document handling. **Boundary:** Project documentation is implementation evidence, not independent accuracy evidence.
- **PYP-S002 — PyMuPDF TextPage documentation:** Character/word geometry and coordinate representation. **Boundary:** Coordinates still inherit PDF layout ambiguity.
- **PYP-S003 — PyMuPDF about/licensing:** PyMuPDF/MuPDF licensing is commercial or copyleft-oriented rather than permissive. **Boundary:** Exact distribution obligations require legal review for any shipping decision.
- **PYP-S004 — pdfplumber stable README:** Detailed chars/lines/rects, tables and visual debugging; works best on machine-generated PDFs. **Boundary:** Project comparison text can favor its own ergonomics.
- **PYP-S005 — pdfplumber current CITATION.cff:** Current project metadata identifies 0.11.10 and MIT license. **Boundary:** Some older README comparison text still calls pdfplumber BSD, so license metadata should be verified at pin time.

## Claim ledger synopsis

- **PYP-C001:** PyMuPDF exposes high-granularity text and geometry suitable for diagnostic/reopenable PDF locators. **ActaKit:** Keep it in benchmark/tooling candidates for geometry-sensitive extraction.
- **PYP-C002:** PyMuPDF is not a frictionless permissive dependency for a distributable kit. **ActaKit:** Do not make it an unquestioned core dependency; require license review or keep as optional tooling.
- **PYP-C003:** pdfplumber offers table extraction and visual debugging and explicitly works best on machine-generated PDFs. **ActaKit:** Useful as a table/diagnostic fallback and benchmark tool, not scan OCR.
- **PYP-C004:** Current pdfplumber licensing metadata is not perfectly consistent across its own prose, though current package metadata says MIT. **ActaKit:** Pin/version review must verify exact package license rather than copying a stale comparison table.
- **PYP-C005:** Neither library removes the need for a quality/escalation policy on malformed reading order or scans. **ActaKit:** Treat both as tools/backends, not the architecture.

## Bounded transfer

Benchmark both for geometry/table diagnostics. Keep PyMuPDF optional pending licensing; keep pdfplumber as a narrow diagnostic/table candidate.

## Do not import

Do not let a convenient Python API redefine the canonical representation model or force an AGPL/commercial dependency into core.

## Residual risk / unresolved question

Need measured performance/accuracy and exact pinned-license review.

## Closure verdict

**adapt-or-reference** for the WP4C selection horizon. This Book is evidence, not implementation authorization.
