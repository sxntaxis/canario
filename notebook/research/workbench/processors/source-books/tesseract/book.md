---
id: ACTAKIT-BOOK-TESSERACT-001
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

# Tesseract OCR

## Question

What should the classical OCR rung provide before any document-AI escalation?

## Audit basis

Current Tesseract 5.x input/output behavior and confidence-bearing outputs.

## Evidence horizon

- **TES-S001 — Tesseract input formats:** Image inputs; PDF is not a native input format. **Boundary:** Does not describe orchestration around PDF rasterization.
- **TES-S002 — Tesseract command-line usage:** Text, PDF, hOCR and TSV output; TSV/hOCR expose geometry and confidence-related fields. **Boundary:** Confidence is engine-specific, not globally calibrated.
- **TES-S003 — Tesseract release notes:** 5.5.x current lineage including 2026 maintenance. **Boundary:** Release notes do not establish civic-document accuracy.

## Claim ledger synopsis

- **TES-C001:** Tesseract OCRs images, not PDFs directly. **ActaKit:** PDF OCR needs a rasterization/orchestration layer such as OCRmyPDF.
- **TES-C002:** Tesseract can emit hOCR/TSV geometry and word-level confidence-like evidence. **ActaKit:** Capture engine-native quality evidence without pretending it is a universal confidence score.
- **TES-C003:** Classical OCR is deterministic/local enough to be a cheaper rung than VLM processing for ordinary scans. **ActaKit:** Use Tesseract as D2 baseline for clean Spanish scans before AI escalation.
- **TES-C004:** Language/model choice and page segmentation materially influence recognition. **ActaKit:** Record language pack, engine version and parameters in ProcessRun.

## Bounded transfer

Adopt Tesseract as the baseline classical OCR engine, normally orchestrated by OCRmyPDF for PDFs.

## Do not import

Do not expose raw Tesseract confidence as ActaKit global confidence and do not feed it PDFs as though rasterization were its job.

## Residual risk / unresolved question

Need Spanish municipal scan benchmark, including low-DPI photocopies and handwriting where Tesseract is expected to fail/escalate.

## Closure verdict

**adopt-candidate** for the WP4C selection horizon. This Book is evidence, not implementation authorization.
