# PROCESSOR-OCR-001 — OCRmyPDF + Tesseract PDF OCR adapter design

**Start authority:** `0fcdc1cde8a2be3bbee45f4e4337991388b10225`  
**Parent gate:** `PROCESSOR_DIRECT_001_POPPLER_PDF_IMPLEMENTED_AND_CERTIFIED`

## Purpose

Land the D2 reference adapter on the independently certified Workbench boundary:
OCRmyPDF orchestration with Tesseract for PDF pages where D1 native extraction is
absent/incomplete.

The adapter is deliberately conservative. The closed Civic Processor Bench proved
that Tesseract confidence is not a universal correctness score and did not justify
a production-wide automatic OCR acceptance threshold. PROCESSOR-OCR-001 therefore
persists OCR text and bounded runtime evidence but sets `ocr.needs_visual_review:v1`
to `true`. Exact `pdf_page:v1` attempts may escalate to the page-scoped
`visual_transcribe` reference capability when egress is authorized. Whole/multi-page
OCR attempts remain local/review-bound and expose `ocr.ocr_page_ordinals:v1` so a
caller can register exact page targets before any cloud step.

## Trusted toolchain

The reference adapter uses external host tools:

```text
ocrmypdf
Tesseract
Poppler pdfinfo/pdftotext
```

The tool paths are resolved from trusted operator configuration/PATH, never from
Representation bytes or target selectors. Exact observed OCRmyPDF, Tesseract,
pypdfium2, fpdf2, uharfbuzz, pikepdf and Poppler versions are retained in the
processor implementation identity. The required Tesseract `*.traineddata` files
are SHA-256 hashed at trusted tool discovery and an aggregate model-set digest is
retained in `model_name`; filesystem paths are never persisted. The reference configuration requires Spanish and English Tesseract data
(`spa`, `eng`) and, because page rotation is enabled, OSD data (`osd`).
OCRmyPDF 17's pypdfium2 rasterizer is selected explicitly; Ghostscript and the
qpdf CLI are not required by this ActaKit path.

OCRmyPDF is invoked as a separate process; ActaKit does not import its Python API
or add it to the core Python runtime dependencies.

## Scope

Supported selectors:

```text
whole:v1
pdf_page:v1  {"page_ordinal": N, "page_label"?: "..."}
```

Explicit page scopes are the preferred path after D1 emits exact
`native.empty_page_ordinals:v1`. A page-scoped D2 attempt refuses a page that
already contains native text; this prevents relabeling an unneeded native extract
as OCR output.

`whole:v1` remains supported for wholly scanned PDFs and for the benchmarked
mixed native/scan case. OCRmyPDF runs in skip-text mode so native pages are
preserved while empty-native pages are OCRed. A whole run whose every page already
has native text fails explicitly as `ocr_not_required`.

## Fixed reference configuration

```text
mode = skip
ocr_engine = tesseract
rasterizer = pypdfium
languages = spa+eng
rotate_pages = true
deskew = true
output_type = pdf
optimize = 0
jobs = 1
OMP_THREAD_LIMIT = 1
Tesseract OCR timeout = bounded
per-command timeout = bounded
total attempt deadline = bounded
input/output/intermediate-PDF/page/scope ceilings = bounded
max image size = 250 megapixels (explicit OCRmyPDF bound)
```

`--output-type pdf` and `--optimize 0` avoid unrelated PDF/A conversion and whole-
file image optimization. `--max-image-mpixels 250` pins OCRmyPDF's current safety ceiling instead of inheriting a future default. The intermediate searchable PDF has a separate bounded size ceiling from the canonical text output, so a legitimate scanned PDF is not rejected merely because its temporary PDF is larger than its extracted UTF-8 text. `--rasterizer pypdfium` removes optional Ghostscript
selection from the reference path. For a mixed whole-document request, ActaKit
preflights native text and sends only pages that actually need OCR to `--pages`;
native pages remain untouched in the temporary searchable PDF. OCRmyPDF may sort
its page set internally; ActaKit re-extracts requested text in the caller's target
order before creating the derivative.

The entire trusted configuration is canonicalized and SHA-256 hashed. Requests
must carry the exact hash. Tool implementation versions and Tesseract model-data
identity remain separate provenance facts, so changing installed model bytes does
not masquerade as a configuration change.

## Output

The canonical material output is:

```text
Representation kind: ocr_text
media type: text/plain
charset: utf-8
```

OCRmyPDF's searchable-PDF product is an intermediate in private temporary storage,
not a canonical derivative in this unit. Poppler extracts text from that product
for the exact requested scope. Original custody is never overwritten.

## QualityEvidence

Each target receives:

```text
core.output_nonempty:v1
ocr.page_text_coverage:v1
ocr.page_character_count:v1
ocr.selected_page_count:v1
ocr.empty_page_count:v1
ocr.empty_page_ordinals:v1
ocr.native_page_count:v1
ocr.ocr_page_count:v1
ocr.needs_visual_review:v1
```

`ocr.page_text_coverage` is only the fraction of selected pages with non-empty
post-OCR text. It is not accuracy/confidence.

`ocr.native_page_count` / `ocr.ocr_page_count` state what the adapter observed
before OCR and therefore make mixed-document behavior auditable.

`ocr.needs_visual_review:v1` is deliberately `true` for this first reference
policy. The benchmark did not establish a reliable runtime-only automatic
acceptance threshold across difficult natural pages.

The adapter does **not** emit `ocr.word_confidence_summary:v1`. OCRmyPDF's CLI does
not expose confidence for the exact internally preprocessed page, and running a
second Tesseract pass over a different raster would create misleading evidence.
A future backend may emit that registered signal only when it can attribute it to
the exact OCR attempt.

## Security/resource boundary

- no network or egress capability;
- no credential fields;
- no document-controlled commands, flags, paths or endpoints;
- subprocess environment contains only deterministic locale, a trusted tool PATH,
  a private temporary HOME/cache/TMPDIR and explicit thread bound;
- proxy/account/token environment variables are not inherited;
- OCRmyPDF concurrency is fixed to one job for bounded reference behavior;
- each subprocess and the whole attempt have deadlines; OCRmyPDF runs in its own process group so timeout cleanup terminates child Tesseract work too;
- only pages missing native text are sent to OCRmyPDF and those OCR pages are capped per attempt;
- intermediate searchable PDFs remain in private temporary storage;
- WorkbenchWriter alone owns canonical archive/SQLite writes.

## Failure semantics

Expected failures map to bounded terminal codes, including:

```text
ocrmypdf_failed
processor_timeout
page_out_of_range
duplicate_page_scope
overlapping_scope
native_text_present_for_ocr_scope
ocr_not_required
ocr_page_limit_exceeded
intermediate_pdf_too_large
output_too_large
page_boundary_mismatch
```

A failed OCR attempt creates no derivative. A technically successful but empty OCR
run remains auditable and cannot be accepted by the reference quality policy.

## No schema redesign

PROCESSOR-OCR-001 uses the certified WORKBENCH-001 contracts and schema unchanged.
If this adapter required a new ProcessRun/QualityEvidence persistence shape, that
would be a certification failure of the supposedly frozen generic boundary.

## Selected dependency licenses

The reference path invokes external/open-source components without vendoring them
into ActaKit. At this unit's freeze point the selected dependency licenses are:

```text
OCRmyPDF 17.10.0: MPL-2.0
Tesseract 5.5.3: Apache-2.0
pypdfium2/PDFium: Apache-2.0 / BSD-3-Clause plus shipped PDFium dependency licenses
fpdf2: LGPL-3.0
uharfbuzz: Apache-2.0 (bundled HarfBuzz carries its own MIT-style licensing)
pikepdf: MPL-2.0 (binary distributions may include qpdf under Apache-2.0)
Poppler CLI: GPL-2.0-or-later family
```

Packaging/distribution must preserve the licenses shipped by those projects. The
license identity is dependency provenance; it does not change ActaKit's generic
Processor contracts.
