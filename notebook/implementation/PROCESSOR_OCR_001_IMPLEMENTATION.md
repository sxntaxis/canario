# PROCESSOR-OCR-001 — Implementation record

**Start HEAD:** `0fcdc1cde8a2be3bbee45f4e4337991388b10225`  
**Parent state:** `PROCESSOR_DIRECT_001_POPPLER_PDF_IMPLEMENTED_AND_CERTIFIED`  
**Candidate state:** `PROCESSOR_OCR_001_IMPLEMENTED__CERTIFICATION_PENDING`

## Production code

`actakit/processors/ocr.py` adds the bounded `OcrPdfProcessor` reference D2
adapter. It invokes OCRmyPDF/Tesseract as external trusted tooling and writes only
an `ocr_text` Representation through the already-certified `WorkbenchWriter`.

The generic Workbench contracts and SQLite schema are unchanged.

## Reference configuration

The adapter fixes the benchmark-derived operational shape:

```text
OCRmyPDF 17.10.x family; certification pin 17.10.0
Tesseract; certification pin 5.5.3
spa+eng OCR with osd data present
mode=skip
ocr-engine=tesseract
rasterizer=pypdfium
rotate-pages + deskew
output-type=pdf
optimize=0
jobs=1
OMP_THREAD_LIMIT=1
bounded Tesseract timeout
bounded subprocess timeout
bounded total attempt deadline
max-image-mpixels=250
separate intermediate searchable-PDF byte ceiling
```

The exact configuration is SHA-256 addressed in `ProcessRun.configuration_hash`.
`implementation_version` additionally records OCRmyPDF, Tesseract, pypdfium2,
fpdf2, uharfbuzz, pikepdf and Poppler versions. The exact selected Tesseract
traineddata files are hashed and
represented as a non-path model digest in `ProcessRun.model_name`.

For explicit `pdf_page:v1` scope the adapter refuses pages that already expose
native text. For `whole:v1`, mixed native/scan PDFs are supported: native pages are
preserved while only empty-native pages are passed to OCRmyPDF. The per-attempt
OCR page ceiling therefore counts pages that actually need OCR, not already-good
native pages.

## Quality policy

The closed bench did not establish a reliable production-time automatic OCR
acceptance threshold. In particular, Tesseract word confidence was proven capable
of remaining high while actual text error was severe. Therefore this unit emits:

```text
ocr.needs_visual_review:v1 = true
```

for every successful D2 target. The reference future `visual_transcribe` capability
is page-scoped, so only exact `pdf_page:v1` OCR attempts are eligible to continue
toward cloud. Whole/mixed attempts stop locally and expose
`ocr.ocr_page_ordinals:v1` so callers can register exact page targets before any
egress. Restricted/no-egress deployments terminate at human review. No universal
confidence was introduced.

OCRmyPDF does not expose Tesseract confidence for the exact internally preprocessed
page through the CLI. PROCESSOR-OCR-001 deliberately does not perform a second,
different Tesseract diagnostic pass merely to manufacture a confidence number.

## D1 -> D2 handoff

`PROCESSOR-DIRECT-001` already emits exact `native.empty_page_ordinals:v1` for a
mixed whole-document probe. Tests prove those ordinals can be registered as
`pdf_page:v1` targets and passed to D2, allowing page-bounded OCR rather than
unconditional whole-document reprocessing.

## Security/resource boundary

- external executable paths come only from trusted host discovery/configuration;
- no shell expansion;
- no network or credential surface;
- no direct SQLite/archive authority;
- private temp input/searchable-PDF/output text only;
- sanitized subprocess environment with trusted PATH and private HOME/cache/TMPDIR;
- proxy/account/token variables are not inherited;
- bounded input/canonical-output/intermediate-PDF/page/scope/image-megapixel limits;
- jobs/OMP threads bounded to one for the reference adapter;
- per-command and total-attempt deadlines, with process-group termination so an OCRmyPDF timeout does not leave child OCR work running.

## Schema

`0001` is unchanged. Its certified SHA256 remains:

```text
adf14a5006565197af3acf57c5cfc213510ba94217beb650403acbaf363b975a
```

No `0002` exists.

## Dependency surface

The adapter fixes OCRmyPDF's Tesseract engine and pypdfium rasterizer explicitly.
It therefore does not require qpdf CLI or Ghostscript as ActaKit gates for this
standard-PDF, `--optimize 0` path. Certification records the selected OCRmyPDF,
Tesseract, pypdfium2, fpdf2, uharfbuzz, pikepdf and Poppler versions.
