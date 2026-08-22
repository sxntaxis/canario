# PROCESSOR-DIRECT-001 — Implementation record

**Start HEAD:** `e719f28f6fdf63d03e68fcba760779a4d4ea0ba8`  
**Candidate state:** `PROCESSOR_DIRECT_001_IMPLEMENTED__CERTIFICATION_PENDING`

## Production code

`actakit/processors/poppler.py` adds `PopplerPdfTextProcessor` and its bounded
trusted configuration. The existing Workbench contracts/schema remain unchanged.

`actakit/processors/targets.py` adds the proven processing selector:

```text
pdf_page:v1
```

without changing SQLite schema. `pdf_page_quote:v1` remains an evidence locator.

`actakit/processors/quality.py` registers the additional bounded native-text
signals required by the real adapter. No universal confidence field was added.

## Controlled production proof

`tests/test_poppler_processor.py` executes the actual installed Poppler utilities,
not a fake subprocess.

The tracked official TSE Puntarenas alcaldías PDF, physical page 2 (Esparza), is
processed through:

```text
DepositWriter
-> retained original Representation
-> pdf_page:v1 target
-> WorkbenchHost
-> PopplerPdfTextProcessor
-> WorkbenchWriter
-> derived extracted_text Representation
```

The resulting text contains every independently curated required span in the
existing Civic Processor Bench truth fixture and receives `ACCEPT`.

Synthetic PDFs built in-test from deterministic standard-PDF primitives prove:

- image-only page -> technical success, no derivative, `ESCALATE` to OCR;
- mixed native + image-only two-page whole scope -> coverage `0.5`, exact empty
  page ordinal `[2]`, mixed-page evidence and escalation;
- native text + raster image -> raster presence recorded without pretending to
  have visually transcribed the image;
- selected page order is preserved;
- malformed PDF -> failed ProcessRun, no derivative;
- out-of-range page -> explicit failed ProcessRun;
- `pdf_page_quote` is rejected as a processing scope;
- changed configuration hash is rejected before canonical processing.

## Natural Esparza certification target

The repository intentionally does not commit the ignored natural corpus bytes.
The independent certification pass should, when the exact hash-recorded Esparza
PDF is locally available/reacquired, run the production adapter against the
existing independently curated Esparza p4 truth:

```text
source SHA256:
ffb354c67d8b56ebf265884c820a98fee27015cadaac3ea1011069f7969b8bfd

truth:
notebook/research/workbench/processors/bench/ground_truth/natural-layout/esparza-p4.json
```

That natural proof is a certification check, not a reason to add the raw PDF to
Git.

## Schema boundary

`0001` is unchanged by PROCESSOR-DIRECT-001. Its certified SHA256 remains:

```text
adf14a5006565197af3acf57c5cfc213510ba94217beb650403acbaf363b975a
```

If this adapter required another Workbench/schema redesign, that would be a
certification failure of the previously frozen generic boundary. It did not.

The concrete adapter also uses a minimal subprocess environment (`LC_ALL=C`, `LANG=C`) rather than inheriting the parent process environment, so deterministic local extraction is not accidentally exposed to cloud/API credentials or unrelated host state.

The adapter bounds both each Poppler subprocess invocation and the total processing attempt, so many explicit page scopes cannot multiply the per-command timeout without limit. Native text output also records the existing namespaced `native.replacement_character_ratio:v1` signal; no acceptance threshold is invented from it in this unit.
