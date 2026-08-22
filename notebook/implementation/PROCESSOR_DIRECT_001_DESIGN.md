# PROCESSOR-DIRECT-001 — Poppler born-digital PDF adapter design

**Start authority:** `e719f28f6fdf63d03e68fcba760779a4d4ea0ba8`  
**Parent gate:** `WORKBENCH_001_GENERIC_PROCESSOR_BOUNDARY_IMPLEMENTED_AND_CERTIFIED`

## Purpose

Land the first real production processor on the certified Workbench boundary:
Poppler direct text extraction for born-digital PDF.

The unit is deliberately narrower than OCR. Its job is to extract native PDF
text cheaply and deterministically, preserve exact page/whole scope, expose the
runtime signals needed to detect obvious empty/mixed-page failure modes, and
escalate rather than guess when native text is absent.

## Trusted toolchain

The adapter uses the Poppler command-line tools:

```text
pdftotext
pdfinfo
pdfimages
```

The three executables are resolved from trusted host configuration/PATH, never
from source-document content. Their reported Poppler versions must agree. The
exact observed version is persisted as the Processor implementation version.
The adapter does not shell-expand commands and never accepts executable names,
CLI flags, output paths or network endpoints from a Representation.

Poppler is an external system dependency, not a Python runtime dependency or
vendored model. Upstream Poppler code is GPL-2.0-or-later; ActaKit invokes the
installed utilities as separate processes. Upstream project/release authority:
`https://poppler.freedesktop.org/`.

## Exact adapter configuration

The production configuration fixes:

```text
encoding = UTF-8
line endings = unix
layout preservation = on
per-command timeout = bounded
total attempt deadline = bounded
input/output/page/scope ceilings = bounded
```

A canonical SHA-256 over those trusted settings is exposed as
`PopplerPdfTextProcessor.configuration_hash`. A processing request must carry
that exact hash; a mismatch is an operator/programming error and is rejected
before canonical attempt persistence.

Poppler version and configuration identity remain separate provenance facts.

## Processing scopes

Supported selectors:

```text
whole:v1
pdf_page:v1  {"page_ordinal": N, "page_label"?: "..."}
```

`pdf_page:v1` is intentionally distinct from `pdf_page_quote:v1`.
The latter is an evidence locator that may contain exact/prefix/suffix quote
anchors; treating it as the scope of a whole-page processor would overstate the
bytes actually processed.

A run may select ordered non-overlapping `pdf_page:v1` targets. Whole-document
scope cannot be mixed with page targets in the same run.

## Extraction and page boundaries

For `whole:v1`, `pdfinfo` establishes the authoritative page count and
`pdftotext` extracts the document once with explicit form-feed page boundaries.
The adapter rejects a boundary count that does not match `pdfinfo` rather than
silently assigning text to the wrong page.

For selected pages, `pdftotext -f/-l` extracts only those pages in requested
target order.

The output is a `text/plain; charset=utf-8` `extracted_text` Representation.
Empty native extraction is a technically successful run with no material
DerivativeOutput; policy decides escalation.

## QualityEvidence

Per page target, the adapter emits:

```text
core.output_nonempty:v1
native.page_text_present:v1
native.page_text_coverage:v1
native.replacement_character_ratio:v1
native.page_character_count:v1
native.page_raster_image_count:v1
```

For whole-document scope it additionally emits:

```text
native.selected_page_count:v1
native.empty_page_count:v1
native.empty_page_ordinals:v1
native.mixed_page_modes:v1
```

`native.page_text_coverage` means the fraction of selected PDF pages with
non-empty native text. `native.empty_page_ordinals:v1` preserves the exact 1-based
physical pages that need targeted follow-up after a whole-document probe. For a single page this is therefore `0.0` or `1.0`.
It is not a visual completeness probability.

`pdfimages -list` supplies raster-image counts. Raster presence is factual
structural evidence only. A page containing native text plus raster images is
**not** declared visually complete and the adapter does not claim to read text
inside images. `native.mixed_page_modes` is true only when a whole-document run
contains both native-text and empty-native-text pages; it specifically addresses
the benchmarked multi-page mixed-PDF failure mode.

## Failure semantics

Expected document/tool failures produce bounded terminal error codes such as:

```text
poppler_failed
pdfinfo_invalid_output
page_out_of_range
duplicate_page_scope
overlapping_scope
page_boundary_mismatch
input_too_large
output_too_large
processor_timeout
```

Malformed PDFs therefore become failed ProcessRuns without derivative output.
Image-only PDFs do not become parser failures: Poppler may succeed with empty
text, and QualityEvidence causes OCR escalation when OCR is available.

## Security/resource boundary

- source bytes are materialized only inside a disposable private temp directory;
- subprocess arguments are arrays, not shell strings;
- locale and output EOL are made deterministic;
- per-command timeout and a total attempt deadline bound multi-page work;
- extracted text is written to size-checked temp files rather than retained as unbounded in-memory stdout;
- no network is used;
- no credential exists in the adapter contract;
- no SQLite/archive authority is given to Poppler;
- temporary bytes are deleted when the invocation closes.

## Acceptance boundary

This unit proves D1 only. It does not implement OCR, Codex, DOCX/HTML, spreadsheet
parsing, or semantic Claim extraction.

A native page with non-empty text can be accepted under the current conservative
reference policy. Empty native text escalates to OCR when that capability is
available. Whole-document mixed coverage escalates rather than treating Poppler
exit 0 as completeness.

## Subprocess environment minimization

Poppler receives a minimal subprocess environment containing only deterministic locale settings (`LC_ALL=C`, `LANG=C`). It does not inherit caller credentials, account variables, proxy settings, or unrelated host environment state. Executable paths are resolved from trusted operator context before invocation.
