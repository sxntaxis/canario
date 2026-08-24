# PROCESSOR-OCR-001 — Independent certification request

**Expected start HEAD:** `0fcdc1cde8a2be3bbee45f4e4337991388b10225`  
**Candidate state:** `PROCESSOR_OCR_001_IMPLEMENTED__CERTIFICATION_PENDING`  
**Parent state:** `PROCESSOR_DIRECT_001_POPPLER_PDF_IMPLEMENTED_AND_CERTIFIED`  
**Canonical `0001` SHA256:** `adf14a5006565197af3acf57c5cfc213510ba94217beb650403acbaf363b975a`

The certification agent must treat the supplied candidate as immutable input.
Do not patch defects during certification.

## Adapter boundary

```text
OcrPdfProcessor
capability: ocr
input: application/pdf
output: ocr_text / text/plain UTF-8
venue: local_deterministic
scope: whole:v1 | pdf_page:v1
egress: false
model provider: tesseract
```

No Codex, Docling, provider-API or local-VLM production adapter is part of this
unit.

## Required reference toolchain

Certification must use the toolchain already benchmarked for the reference D2
path where available:

```text
OCRmyPDF 17.10.0
Tesseract 5.5.3
Tesseract data: spa + eng + osd
OCRmyPDF rasterizer: pypdfium2 (explicit `--rasterizer pypdfium`)
Poppler 26.07.0
```

OCRmyPDF may live in a disposable benchmark/certification virtual environment;
it is not a production Python dependency of ActaKit. Its Python environment must
provide pypdfium2, fpdf2, uharfbuzz and pikepdf. Record the observed versions of
all four packages during certification because they materially rasterize, render or
graft the OCR layer. Verify that the ProcessRun model identity
contains the aggregate SHA-256 identity of the exact `spa`, `eng`, and `osd`
traineddata files without persisting their host paths. Do not change system Python or vendor
OCRmyPDF into the repository. qpdf CLI and Ghostscript are not certification
gates for this fixed standard-PDF/pypdfium path.

Certification must also use the exact registered upstream SQLite 3.53.4 runtime
used for WORKBENCH-001 and PROCESSOR-DIRECT-001 certification.

## Controlled proof input

Generate the already-defined controlled variants from the tracked TSE source in a
disposable directory using:

```bash
python notebook/research/workbench/processors/bench/generate_controlled_variants.py \
  --source notebook/research/pre-sql/fixtures/artifact-proofs/alcaldias_pu.pdf \
  --source-sha256 192da0e99878aa310a906f381f3bb25c9678934743b1b7563df747e05a8eb4f3 \
  --page 2 \
  --work-dir "$WORK/control"
```

Then run:

```bash
python notebook/implementation/prove_processor_ocr_001.py \
  --controlled-variants "$WORK/control/controlled-variants.json"
```

The production proof checks clean-scan and low-DPI required-span floors grounded
in the closed D2 benchmark, ensures skew/noise is never auto-accepted, proves
mixed native+scan preservation/recovery, and proves malformed-input failure
isolation.

## Natural Esparza proof

Full certification requires the exact hash-recorded public Esparza source. Reuse
an existing exact copy or reacquire it from the recorded official source, verify
the hash, then run:

```bash
python notebook/implementation/prove_processor_ocr_001.py \
  --controlled-variants "$WORK/control/controlled-variants.json" \
  --natural-esparza /exact/path/to/esparza-2026-concejo.pdf
```

Required source SHA256:

```text
ffb354c67d8b56ebf265884c820a98fee27015cadaac3ea1011069f7969b8bfd
```

The proof renders official page 4 into the same 300-DPI controlled-degradation
class already scored in the Civic Processor Bench and requires at least 4/5
independently curated required spans while still forcing visual-review escalation.
If the exact bytes cannot be obtained after a bounded attempt, report certification
blocked rather than weakening the hash or truth requirement.

## Required adapter audit

Independently verify at least:

1. D2 uses the frozen Workbench boundary without schema redesign;
2. explicit page scopes reject native-text pages instead of relabeling them as OCR;
3. whole mixed PDFs use skip-text semantics and preserve native pages;
4. explicit page order is preserved in canonical text output;
5. `ocr.page_text_coverage` is coverage only, never correctness probability;
6. `ocr.needs_visual_review:v1` is always true under this conservative first policy;
6a. `ocr.ocr_page_ordinals:v1` identifies exactly which physical pages were OCRed; whole/mixed scope cannot make a whole document eligible for the page-scoped visual/cloud capability;
7. no Tesseract confidence is fabricated via a second mismatched raster pass;
8. output is canonicalized only as `ocr_text` through WorkbenchWriter;
9. OCRmyPDF searchable PDF remains temporary;
10. malformed input yields failed ProcessRun/no derivative;
11. restricted input remains restricted and cloud is not made eligible by the adapter;
12. no network/egress/credential surface exists;
13. subprocesses do not inherit caller secrets/proxy/account environment;
14. executable paths/flags are trusted host configuration, not document data;
15. input/canonical-output/intermediate-PDF/page/scope/process/thread limits are bounded, and OCRmyPDF image decompression is explicitly capped with `--max-image-mpixels 250`;
16. per-command and total-attempt deadlines are enforced and timeout cleanup terminates the OCRmyPDF child process group;
17. D1 empty-page ordinals can drive exact `pdf_page:v1` D2 follow-up;
18. no schema change/`0002` exists;
19. all pre-existing direct/Workbench tests continue passing;
20. controlled and natural production proofs meet their benchmark-grounded floors;
21. OCRmyPDF is explicitly pinned to the Tesseract OCR engine and pypdfium rasterizer; optional Ghostscript/qpdf CLI presence cannot silently select another path;
22. the OCR page ceiling counts only pages actually missing native text, so large mixed documents are not rejected merely for containing many preserved native pages;
23. selected dependency licenses and observed runtime versions are recorded without host fingerprinting;
24. intermediate searchable-PDF bytes use their own bounded ceiling rather than the canonical text-output ceiling, and exceeding it fails explicitly without persistence;
25. pypdfium2, fpdf2, uharfbuzz and pikepdf versions plus exact Tesseract traineddata model-set identity are durable ProcessRun provenance, while host filesystem paths remain absent.

Only after every required runtime/proof/audit check passes should the state advance
to:

```text
PROCESSOR_OCR_001_OCRMYPDF_TESSERACT_IMPLEMENTED_AND_CERTIFIED
```
