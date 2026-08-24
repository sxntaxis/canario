# LECTOR-002 — heterogeneous civic reference corpus

State: **CORPUS FRAMEWORK ACTIVE — BROAD GOLD/CERTIFICATION NOT READY**

Parent authority:

```text
LECTOR-001 = certified + integrated bounded semantic extraction boundary
```

## Why this changed

The first LECTOR-002 scaffold used Acta 161 and embedded acta-shaped segmentation
(`ARTÍCULO`, numbered items, `SE ACUERDA`, municipal speaker turns). It was lossless, but
that still let the first mature source family shape a supposedly generic benchmark.

That design is retired. Acta 161 is now one corpus case, not “the Lector benchmark”.

## Two different things

1. **Generic corpus/evaluator machinery** must know only typed Representation/evidence
   contracts and generic structure.
2. **Case-specific helpers** may understand a language, source or document type, but they
   are optional aids and cannot define completeness or broad certification.

`lector_002_benchmark.py` currently implements only the `text_quote:v1` evaluator mode.
Its v2 preparation partitions UTF-8 text losslessly using page separators, blank-line
blocks and bounded continuation. It deliberately has no acta vocabulary or civic keyword
triage and keeps coverage in source order.

This is intentionally not enough for broad certification. Table and timed-media evidence
need their own typed evaluator modes rather than being flattened into text.

## Required broad-corpus classes

Before a semantic backend may be called broadly certified, the corpus must contain at
least one independently gold-frozen/adjudicated real case from each class:

| Class | Example source shape | Required evidence mode |
|---|---|---|
| `institutional_minutes` | acta/minutes/session record | text/page locators as source permits |
| `report_or_audit` | report, audit, technical finding | text + tables where present |
| `official_correspondence` | oficio/letter/request/response | text/document structure |
| `normative_or_contractual` | resolution, regulation, contract | text/document structure |
| `structured_data` | budget/procurement table/dataset | table/path typed evidence |
| `timed_media` | public audio/video recording | media time span + transcript anchor when available |

Additional classes can be added when real sources expose a materially different failure
mode. The matrix is a minimum diversity gate, not a claim that these six exhaust civic
records.

## Current real case

`CR-ESPARZA-MINUTES-001`:

```text
Acta Sesión Ordinaria N° 161 — 18 May 2026
PDF SHA256:
ffb354c67d8b56ebf265884c820a98fee27015cadaac3ea1011069f7969b8bfd

Poppler text SHA256:
02d1578cfc44097c6e5e802880919ff6f7a18bd2105330035959c4cccd467ea1
```

It remains external to the repository. Its gold is **not frozen**. Any previous worksheet
produced by the retired acta-shaped v1 preparation is obsolete and must not be used as the
canonical LECTOR-002 gold worksheet.

The v2 generic-text worksheet may be regenerated from the same frozen Representation.
A reconstruction proof on the frozen text currently yields:

```text
page_count:               39
review_units:             61
unit kinds:               source=1, page=38, block=7, continuation=15
max unit span:            3992 characters
attention_heuristics_used: false
semantic_model_calls:      0
truth_generated:           false
```

Those counts are an implementation proof for this case, not a target shape for reports,
correspondence or transcripts. No tested semantic extractor should inspect this case until
that case's independent gold is frozen.

## Production doctrine still stands

`machine-only` is a normal durable/searchable production state, not review debt. Corpus
gold/adjudication is engineering validation paid on a small representative set, not a rule
that every ingested Claim enters a human queue.

## Broad stop condition

Acta 161 alone can never close LECTOR-002. Broad certification is blocked until:

1. heterogeneous real source cases exist;
2. each case has the correct typed evidence evaluator;
3. independent gold is frozen before tested extractor output is inspected;
4. candidates are adjudicated against that gold;
5. deterministic scoring passes per-case and aggregate gates;
6. modality/source-class results are reported separately so a strong minutes score cannot
   hide a weak report/table/audio score.
