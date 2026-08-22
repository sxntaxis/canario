# Civic Processor Bench checkpoint

State: `CIVIC_PROCESSOR_BENCH_IN_PROGRESS__NATURAL_CORPUS_AND_D3_D5_PARTIAL`

This checkpoint establishes the executable/scored benchmark mechanics before heavyweight processor
installation or cloud runs.

## Proven here

- official public civic source fixture with fixed SHA-256;
- manual text/table truth independent of OCR output;
- deterministic clean/low-DPI/skew-noise/image-only/mixed/malformed derivatives;
- comparable CER/WER/token/span metrics;
- namespaced Tesseract word-confidence evidence;
- table-specific exact-row evidence;
- best-effort wall time/peak RSS recording;
- non-secret cloud-run evidence schema/recorder;
- no production processor package or schema change.

## Not proven here

- natural-corpus representativeness;
- final escalation thresholds;
- Docling/Paddle/Qwen/OpenAI/Mistral winner/default choices;
- production Processor SPI;
- production credential facility.

## Natural corpus increment

The local certified Esparza shadow material is now represented by ignored work
files: one 39-page born-digital PDF, its HTML listing, and an official DOCX
linked by that listing. Two additional official long actas were downloaded and
hashed: FECOMUDI (56 pages) and Quepos (35 pages). All natural material is
`UNSCORED_NATURAL`; no CER/WER was derived from a processor output.

Cartago returned HTTP 404 after a local CA verification failure and remains
`NOT_READY_FETCH_FAILED`. No cloud bytes were sent.

## Environment-limited candidates

The controlled D1 semantic outcomes reproduced with Poppler 26.07.0. The host
does not have Tesseract, OCRmyPDF, qpdf, Docling, PaddleOCR, PyTorch or a GPU;
these candidates are recorded as exact `NOT_RUN_*` evidence. OpenAI and Mistral
cloud authorization variables were absent, so no provider was contacted.
