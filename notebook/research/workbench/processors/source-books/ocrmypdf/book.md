---
id: ACTAKIT-BOOK-OCRMYPDF-001
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

# OCRmyPDF 17

## Question

Should ActaKit reuse an existing PDF OCR orchestration/preprocessing pipeline instead of building one?

## Audit basis

Current 17.10.0 cookbook, plugins and release changes.

## Evidence horizon

- **OMP-S001 — OCRmyPDF 17.10.0 cookbook:** Rotation, deskew, cleaning, background removal, oversampling and explicit warnings about destructive/rasterizing options. **Boundary:** Recipes do not substitute for fixture-based policy tuning.
- **OMP-S002 — OCRmyPDF 17.10.0 plugins:** OCR engine/rasterizer/image hooks and direct structured OCR tree API. **Boundary:** Plugin SPI is OCRmyPDF-specific, not an ActaKit processor contract.
- **OMP-S003 — OCRmyPDF v17 release notes:** Pluggable OCR engines, pypdfium rasterizer, --ocr-engine none, hardened watcher; Tesseract no longer assumed as permanent primary engine. **Boundary:** Release notes describe capability, not quality on ActaKit sources.
- **OMP-S004 — OCRmyPDF installation:** Rasterizer/text-layer dependencies and optional Tesseract/PDF-A stack. **Boundary:** System dependency choices vary by deployment.

## Claim ledger synopsis

- **OMP-C001:** OCRmyPDF already handles conservative PDF OCR orchestration tasks such as rotation, deskew and oversampling. **ActaKit:** Reuse it rather than reimplementing PDF-to-image/OCR grafting.
- **OMP-C002:** Some preprocessing/force modes rasterize pages or can remove desirable visual content. **ActaKit:** Original Representation is immutable; preprocessing/OCR always produces derivatives with explicit parameters.
- **OMP-C003:** OCRmyPDF 17 deliberately supports replaceable OCR engines and non-OCR preprocessing. **ActaKit:** It can serve as D2 orchestration while ActaKit retains its own higher-level escalation policy.
- **OMP-C004:** A reliable PDF OCR stack includes rasterizer/text-layer/system dependencies beyond the OCR engine itself. **ActaKit:** Treat deployment capability detection as part of processor availability.

## Bounded transfer

Adopt OCRmyPDF as the classical PDF OCR/preprocessing orchestrator; start with conservative settings and Tesseract, benchmark stronger engine hooks later.

## Do not import

Do not use force/rasterizing modes casually or overwrite custody originals.

## Residual risk / unresolved question

Need resource limits and test whether OCRmyPDF output itself or extracted text/geometry should be retained as primary derived Representations.

## Closure verdict

**adopt-candidate** for the WP4C selection horizon. This Book is evidence, not implementation authorization.
