---
id: ACTAKIT-BOOK-DOCLING-001
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

# Docling

## Question

Can Docling provide the main built-in structured-document processing framework without making ActaKit duplicate document-AI internals?

## Audit basis

Current 2.118.1 release, supported formats, OCR/model catalog, confidence model and media processing.

## Evidence horizon

- **DOC-S001 — Docling supported formats:** Unified DoclingDocument across PDF, Office, HTML, images, audio/video and more; lossless JSON output. **Boundary:** Breadth does not imply every backend should be enabled in ActaKit.
- **DOC-S002 — Docling installation/OCR engines:** Selectable OCR backends including Tesseract, RapidOCR, EasyOCR and others. **Boundary:** Backend/model licenses and hardware differ.
- **DOC-S003 — Docling confidence scores:** Layout/OCR/parse/table component grades; numerical scores explicitly internal/unstable, categorical grades intended for users. **Boundary:** Docling confidence cannot become a universal cross-processor metric.
- **DOC-S004 — Docling model catalog:** Layout, OCR, TableFormer and VLM stages/backends. **Boundary:** Individual model licenses differ from MIT code.
- **DOC-S005 — Docling audio/video processing:** Whisper-based ASR plus video framing/optional diarization, with documented limitations. **Boundary:** Audio export lacks word-level timestamps; direct ASR may be preferable where locator precision matters.
- **DOC-S006 — Docling 2.118.1 PyPI release:** 2.118.1 published 2026-08-07 with trusted publishing provenance. **Boundary:** Version recency is not itself a quality guarantee.
- **DOC-S007 — Docling README license:** Codebase MIT; individual models carry their own licenses. **Boundary:** Every enabled model still requires separate license pin/audit.

## Claim ledger synopsis

- **DOC-C001:** Docling offers a single structured intermediate representation across many document types. **ActaKit:** Strong candidate for the built-in structured-document framework behind ActaKit Representations.
- **DOC-C002:** Docling already separates OCR/layout/table/VLM backends. **ActaKit:** ActaKit can own policy/provenance while reusing Docling internals rather than creating another document engine framework.
- **DOC-C003:** Docling explicitly warns that its numeric confidence scores are internal and may change, while grades are the intended interpretation. **ActaKit:** Ingest named QualityEvidence; never normalize Docling 0..1 to a universal ActaKit confidence.
- **DOC-C004:** Docling code is MIT but enabled models have separate licenses. **ActaKit:** Processor capability registry must record model identity/license, not just Python package license.
- **DOC-C005:** Docling can process audio/video but current limitations include no word-level timestamps in its export. **ActaKit:** Do not force all media through Docling if a direct ASR backend preserves better locator/quality evidence.
- **DOC-C006:** Docling is rapidly evolving in 2026. **ActaKit:** Pin exact versions/models and benchmark before freeze; avoid coupling core schema to Docling private objects.

## Bounded transfer

Primary candidate: benchmark Docling as ActaKit’s built-in structured-document orchestrator; map its lossless/structured output into ActaKit derived Representations while keeping core contracts independent.

## Do not import

Do not persist Docling private Python objects as authority; do not enable every model/backend just because Docling supports it.

## Residual risk / unresolved question

Civic Bench must compare native Poppler/OCRmyPDF paths against Docling to prevent an expensive framework from replacing cheaper successful rungs.

## Closure verdict

**adopt-after-benchmark** for the WP4C selection horizon. This Book is evidence, not implementation authorization.
