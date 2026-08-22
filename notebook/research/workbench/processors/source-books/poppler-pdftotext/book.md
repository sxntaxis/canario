---
id: ACTAKIT-BOOK-POPPLER_PDFTOTEXT-001
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

# Poppler / pdftotext

## Question

What should ActaKit use as the cheapest deterministic text-extraction rung for born-digital PDFs?

## Audit basis

Current pdftotext behavior and output modes, with attention to geometry, reading order and failure boundaries.

## Evidence horizon

- **PDT-S001 — Poppler pdftotext manpage (Debian trixie):** Current CLI behavior: reading-order default, -layout, -bbox/-bbox-layout/-tsv, hyphen policy. **Boundary:** Manpage documents behavior; it is not a benchmark on civic PDFs.
- **PDT-S002 — Poppler pdftotext manpage (Debian experimental/current package):** Confirms current layout/raw/hyphen semantics across newer packaging. **Boundary:** Packaging page is a distribution view, not upstream release policy.

## Claim ledger synopsis

- **PDT-C001:** pdftotext defaults toward reading-order text while -layout instead tries to preserve physical layout. **ActaKit:** Use plain extraction first; request layout mode only for a specific downstream need.
- **PDT-C002:** pdftotext can emit word/block/line bounding boxes via -bbox, -bbox-layout and -tsv. **ActaKit:** A deterministic PDF rung can preserve coordinate evidence without invoking OCR or AI.
- **PDT-C003:** Raw content-stream order is explicitly discouraged; layout/reading-order choices are heuristic rather than universal truth. **ActaKit:** ActaKit must record extraction mode/version and assess quality instead of treating one order as authoritative.
- **PDT-C004:** Hyphen removal is configurable and therefore can change the textual representation. **ActaKit:** Normalization choices are processor parameters and must be captured in ProcessRun provenance.
- **PDT-C005:** A digital-text extractor solves only PDFs with usable text layers; it does not solve image-only or badly encoded pages. **ActaKit:** Make pdftotext D1, not the universal PDF processor; quality failure escalates.

## Bounded transfer

Adopt pdftotext/Poppler as the default cheapest deterministic PDF text rung, with optional coordinate output and explicit mode provenance.

## Do not import

Do not treat its reading order as ground truth, and do not OCR every PDF before trying the native text layer.

## Residual risk / unresolved question

Need Civic Processor Bench evidence for Spanish municipal PDFs, mixed native/scanned pages, columns and malformed encodings.

## Closure verdict

**adopt-candidate** for the WP4C selection horizon. This Book is evidence, not implementation authorization.
