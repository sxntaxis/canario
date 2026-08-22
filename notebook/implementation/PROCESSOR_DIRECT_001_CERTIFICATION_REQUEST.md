# PROCESSOR-DIRECT-001 — Independent certification request

**Expected start HEAD:** `e719f28f6fdf63d03e68fcba760779a4d4ea0ba8`  
**Candidate state:** `PROCESSOR_DIRECT_001_IMPLEMENTED__CERTIFICATION_PENDING`  
**Parent state:** `WORKBENCH_001_GENERIC_PROCESSOR_BOUNDARY_IMPLEMENTED_AND_CERTIFIED`  
**Canonical `0001` SHA256:** `adf14a5006565197af3acf57c5cfc213510ba94217beb650403acbaf363b975a`

The certification agent must treat the supplied candidate as immutable input. Do
not patch defects during certification.

## Adapter boundary to verify

The candidate adds one production backend only:

```text
PopplerPdfTextProcessor
capability: text_extract
input: application/pdf
output: extracted_text / text/plain UTF-8
venue: local_deterministic
scope: whole:v1 | pdf_page:v1
egress: false
```

No OCR, Codex, Docling, provider-API, local-VLM, DOCX, spreadsheet or Claim
processor is part of this unit.

## Required toolchain

Certification requires a working Poppler CLI suite:

```text
pdftotext
pdfinfo
pdfimages
```

All three must report the same Poppler version. The production adapter records
that exact version in ProcessRun provenance. Do not replace the executable paths
from document-controlled input.

The implementation was developed against Poppler `25.06.0`; the independent
source machine previously reported Poppler `26.07.0`. Certification should record
its exact observed version rather than changing the generic schema to pin a distro
package build.

## Required commands

Run on the exact registered SQLite 3.53.4 runtime used for WORKBENCH-001
certification:

```bash
python notebook/research/pre-sql/schema/prove_runtime_contract.py
python notebook/research/pre-sql/schema/prove_migration_0001_spec.py
python notebook/research/pre-sql/schema/prove_migration_freeze.py
python notebook/research/pre-sql/schema/prove_storage_operations.py
python notebook/research/workbench/processors/bench/validate_bench.py
python notebook/research/workbench/processors/validate_research.py
python notebook/implementation/prove_processor_direct_001.py
PYTHONPATH=. pytest -q
python -m compileall -q actakit notebook/implementation/prove_processor_direct_001.py
git diff --check
```

The default proof always exercises the tracked official TSE page through the real
production Workbench/Poppler path.

## Natural Esparza proof

If the hash-recorded natural corpus is present from the earlier bench, additionally
run:

```bash
python notebook/implementation/prove_processor_direct_001.py \
  --natural-esparza \
  notebook/research/workbench/processors/bench/work/natural-corpus/esparza-2026-concejo.pdf
```

The file must hash exactly to:

```text
ffb354c67d8b56ebf265884c820a98fee27015cadaac3ea1011069f7969b8bfd
```

The proof checks page 4 against the independently curated natural-layout truth.
If the ignored bytes are absent, reacquisition from the already-recorded public
source URL is allowed only if the exact SHA256 matches. Do not change corpus
metadata to make a changed upstream file pass.

## Required adapter audit

Independently verify:

1. `pdf_page:v1` is a full physical-page processing scope and does not weaken
   `pdf_page_quote:v1` evidence semantics;
2. page ordinal is validated and out-of-range pages fail explicitly;
3. whole and page targets cannot overlap in one run;
4. duplicate physical page scopes cannot silently double-process the same page;
5. Poppler executables/version/configuration are trusted host configuration, not
   document-controlled data;
6. subprocesses use argument arrays with no shell expansion;
7. locale/output EOL are deterministic;
8. source/output temp files are disposable and bounded, and a total attempt deadline prevents per-page timeout multiplication;
9. a malformed PDF produces a failed ProcessRun without derivative output;
10. an image-only page may be technical `success` but emits no derivative and
    escalates to OCR when that capability is available;
11. whole mixed native/image-only coverage records exact empty page ordinals for
    targeted follow-up rather than inferring completeness from process return code;
12. raster-image presence is namespaced evidence, not a claim that image text was
    visually recovered; replacement-character ratio is retained as namespaced evidence
    without inventing a universal acceptance threshold;
13. native accepted output is written only through WorkbenchWriter and preserves
    parent Artifact/Representation custody;
14. replay/idempotence remains provided by the already-certified Workbench;
15. no network/credentials/API surface was added;
16. no schema change or `0002` was introduced;
17. the full pre-existing 66-test Workbench suite still passes;
18. the tracked TSE page retains all independently curated required spans.

## Certification outcome

Only if runtime, proofs, tests and all 18 adapter checks pass should the state
advance to:

```text
PROCESSOR_DIRECT_001_POPPLER_PDF_IMPLEMENTED_AND_CERTIFIED
```

If certification fails, report the exact invariant and evidence. Do not start D2
OCR in the certification pass.

Certification must verify the Poppler subprocess environment is minimized to deterministic locale settings and does not inherit unrelated caller credentials/environment state.
