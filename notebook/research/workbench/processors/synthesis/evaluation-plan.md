# Civic Processor Bench — required before WORKBENCH-001 freeze

Public benchmarks establish that strong processors exist; they do not answer which stack is best for
ActaKit's civic sources. Build a small, adversarial, legally usable fixture corpus before production
processor implementation is frozen.

## Minimum corpus

1. born-digital Esparza acta PDF;
2. multi-column digital PDF;
3. table-heavy municipal PDF;
4. clean image-only scan;
5. skewed/rotated/noisy scan;
6. low-DPI photocopy;
7. mixed native-text + scanned-page PDF;
8. image-only PDF with stamps/signatures;
9. handwriting-heavy note/form/receipt-like civic material when lawfully available;
10. malformed/truncated PDF;
11. DOCX with headings/lists/tables;
12. XLSX/CSV with multiple tables/sheets;
13. HTML with meaningful hierarchy/links;
14. later: audio/video only when a real source enters scope.

## Ground truth

For each applicable fixture retain:

- normalized text excerpts and must-not-invent spans;
- page/word/block anchors where practical;
- expected reading order;
- key tables with row/cell truth;
- expected warnings/escalation decision;
- expected no-output/unsupported behavior for malformed material.

## Metrics

- normalized edit distance / CER / WER;
- page/content coverage and false insertion rate;
- reading-order error;
- table TEDS/structure/cell fidelity;
- coordinate/locator reopenability;
- hallucinated or fabricated text/fields;
- deterministic replay stability where the backend is deterministic;
- runtime, peak memory, GPU/CPU requirement and artifact-size expansion;
- escalation frequency and per-rung marginal cost;
- provenance completeness;
- cloud cost and bytes/pages sent off-device;
- failure isolation: original custody must survive all failures.

## Comparative runs

At minimum compare:

- Poppler native extraction;
- OCRmyPDF + Tesseract;
- Docling default structured pipeline;
- Docling with selected OCR backend on scans;
- PaddleOCR-VL on hard-document subset;
- Qwen3-VL on handwriting/weird-visual subset;
- optional Mistral OCR on an explicitly egress-safe subset;
- pdfplumber diagnostics on table fixtures;
- MinerU/Marker as comparator runs where installation/license permits.

## Gate

Do not freeze or implement the production processor ladder until the benchmark produces a decision table
for each rung, including exact versions/models/licenses, resource budgets and escalation thresholds.
Research can nominate candidates; Civic Processor Bench chooses the shipped defaults.
