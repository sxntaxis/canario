# Civic Processor Bench status

State: **CIVIC_PROCESSOR_BENCH_IN_PROGRESS__NATURAL_CORPUS_AND_D3_D5_PARTIAL**

The bench infrastructure is operational. This is **not** a processor-stack selection and does not
unblock `WORKBENCH-001` yet.

## First controlled civic baseline

Fixture: official TSE Puntarenas alcaldías PDF, physical page 2 (Esparza). The source hash is the same
one already used by the selector proof:

```text
192da0e99878aa310a906f381f3bb25c9678934743b1b7563df747e05a8eb4f3
```

The local run used:

```text
Poppler/pdftotext 25.06.0
Tesseract 5.5.0, spa, PSM 3
Pillow 12.3.0
pdfplumber 0.11.9
Python 3.13.5
```

Exact environment details and every raw metric are in
`results/local-controlled-baseline.json`.

| Case | Backend | CER | WER | Required-span recall | Engine signal | Observation |
|---|---|---:|---:|---:|---|---|
| native PDF | Poppler | 0.000 | 0.000 | 1.000 | n/a | exact normalized text; D1 can be extremely cheap when native text is real |
| clean image-only PDF | Poppler | 1.000 | 1.000 | 0.000 | n/a | empty output with exit 0; clean escalation signal |
| low-DPI image-only PDF | Poppler | 1.000 | 1.000 | 0.000 | n/a | empty output with exit 0 |
| skew/noise image-only PDF | Poppler | 1.000 | 1.000 | 0.000 | n/a | empty output with exit 0 |
| mixed native + scan | Poppler | 0.500 | 0.500 | 1.000 | n/a | exit 0 and plausible text, but half the known document truth is missing |
| clean 300-DPI scan | Tesseract | 0.029 | 0.068 | 0.429 | mean word conf 94.37 | good-looking OCR still dropped PUSC cells and damaged the email/punctuation |
| low-DPI 110 scan | Tesseract | 0.007 | 0.049 | 0.857 | mean word conf 91.53 | unexpectedly better than the 300-DPI default configuration; config/segmentation matters |
| skew/noise scan | Tesseract | 0.531 | 0.709 | 0.286 | mean word conf 93.17 | severe reading-order corruption despite high engine confidence |
| native table | pdfplumber | n/a | n/a | n/a | exact row recall 1.000 | all three manually curated table rows recovered exactly |
| truncated PDF | Poppler | n/a | n/a | n/a | non-zero exit | explicit parser failure; original custody must remain untouched |

### What this already proves

1. **No universal confidence.** Tesseract's mean word confidence remained about 93 on the skew/noise
   variant while document-level CER exceeded 0.53. Its confidence is useful namespaced evidence but not
   an acceptance probability.
2. **Success return codes are insufficient.** Poppler exits successfully on image-only PDFs and on the
   mixed PDF. Empty-output detection catches pure scans; page/content coverage is needed for mixed files.
3. **Escalation should be scoped.** The mixed fixture supports the research direction of page/block-level
   escalation when coordinates are stable rather than sending an entire long document to OCR/VLM.
4. **Processor configuration is benchmark material.** The 110-DPI Tesseract run outperforming the
   nominal 300-DPI run means the bench must pin/render/configure attempts, not just compare product names.
5. **Tables need their own evidence.** Text CER alone would not prove that row/cell structure survived;
   exact table-row recovery is recorded separately.

None of those observations freeze production thresholds yet.

## Scenario coverage

Controlled coverage now exercises:

- born-digital PDF;
- table-heavy PDF;
- clean image-only scan;
- low-DPI scan;
- skew/noise scan;
- mixed native + scan;
- malformed/truncated PDF.

The natural increment added five ignored source artifacts: a certified Esparza
39-page born-digital PDF, its HTML listing, an official Esparza DOCX, FECOMUDI
Sesion Ordinaria 14-2025 (56 pages), and Quepos Acta 086-2021 (35 pages). All
natural material is `UNSCORED_NATURAL`. The listing exposes 40 public DOCX links.
Cartago could not be promoted: local TLS verification failed and an explicit
retry returned HTTP 404.

Natural D1 inventory found non-empty Poppler text on every page of the three
natural PDFs. This is coverage/behavior evidence only, not quality scoring.

Still required before the gate can close:

- multi-column civic PDF;
- natural difficult scan/photocopy and stamps/signatures;
- lawful handwriting-heavy civic material;
- XLSX/CSV multi-table material;
- D2 OCRmyPDF/Tesseract runs (blocked by missing system dependencies on this host);
- D3 Docling runs (blocked by missing benchmark dependency);
- D4 specialized document-AI runs (blocked by missing runtime/GPU);
- D5 local frontier multimodal run (blocked by missing runtime/GPU);
- D5 OpenAI cloud run over the **same explicitly egress-safe hard subset** (blocked by absent explicit authorization);
- optional Mistral specialist comparison;
- exact licenses/model-weight terms/pins and resource/cost evidence.

## Cloud benchmark boundary

Cloud remains benchmark-first-class but explicit. A cloud attempt must record provider/model/endpoint
profile, request-template identity, pages/bytes egressed, latency, usage/cost inputs and a declared
retention/data-control profile. API-key/token values never enter benchmark artifacts.

The bench intentionally does not hard-code an OpenAI model default. The local operator supplies the exact
model being evaluated; that model identity becomes evidence. OpenAI-compatible endpoints are recorded as
capability profiles rather than assumed equivalent from URL shape.

## Gate

`WORKBENCH-001` remains blocked. The next bench increment must curate independent
truth for a small natural hard subset and run D2-D5 in an environment with the
required dependencies/hardware or explicit cloud authorization. Exact evidence
is recorded in `results/natural-corpus-d1-and-availability.json`.
