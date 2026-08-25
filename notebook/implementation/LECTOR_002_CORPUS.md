# LECTOR-002 — heterogeneous civic reference corpus

State: **CAPABILITY-COVERAGE FRAMEWORK ACTIVE — GOLD/EVALUATION NOT READY**

Parent authority:

```text
LECTOR-001 = certified + integrated bounded semantic extraction boundary
```

## Why this changed

The first LECTOR-002 scaffold used Acta 161 and embedded acta-shaped segmentation
(`ARTÍCULO`, numbered items, `SE ACUERDA`, municipal speaker turns). It was lossless, but
that still let the first mature source family shape a supposedly generic benchmark.

That design is retired. A second design then described six required "document classes".
That was safer than minutes-only testing, but still carried the wrong implication: Canario
must not maintain an ontology of every civic record type before it can ingest evidence.
There may be hundreds of genres, hybrids, containers and future formats that no finite
classification can enumerate.

LECTOR-002 therefore treats source genres only as **descriptive benchmark archetypes**.
The executable gate is now a matrix of **declared capabilities / failure modes**.

## Product ontology versus benchmark metadata

The product path remains:

```text
anything -> Artifact -> typed Representation(s) -> Lector -> Fichero
```

A PDF containing a letter, tables, annexes and images does not need one globally correct
`document_class`. A ZIP containing text, audio, images and a workbook may produce several
Artifacts/Representations. What matters to the generic core is custody, Representation
semantics, evidence locators, provenance and bounded semantic authority.

The benchmark may annotate a case with:

```text
benchmark_archetypes = ["institutional_minutes"]
```

or later:

```text
benchmark_archetypes = ["audit_report", "mixed_annexes"]
```

Those labels exist only to explain why a fixture was selected. They are **not registered
Canario document types**, are not exhaustive, and cannot route production ingestion.

## Capability coverage is the executable gate

`lector_002_corpus.json` declares a finite, revisable set of stress capabilities that the
current reference campaign intends to exercise. They span dimensions such as:

- Representation fidelity: paged text, structured tables, timed media;
- evidence reopening: exact text quote, table/path evidence, media time span;
- semantic stress: many topics, attribution, conditions/exceptions/cross-references,
  structured values.

One case may cover several capabilities. Several very different cases may cover the same
capability. A newly discovered failure mode should normally add a new capability target and
a fixture that exposes it — **not a new universal document class**.

This capability list is itself not a closed ontology. It is the explicit scope of the
current benchmark campaign and may grow whenever reality exposes a materially different
failure mode.

## What readiness can and cannot mean

A finite corpus can never prove:

```text
Canario supports every document/media type that can exist.
```

Accordingly the corpus manifest requires:

```text
certification_scope = declared_capabilities_only
universal_support_claimed = false
```

and the evaluator reports:

```text
declared_capability_gate_ready
```

rather than `broad_certification_ready`.

A green gate means only that every **currently declared capability target** has suitable
reference evidence whose gold/adjudication state satisfies the gate. Per-case semantic
scores and their thresholds remain separate evidence; results must still be reported by
capability and fixture so aggregate strength cannot hide a weak modality.

## Generic evaluator machinery versus optional specialization

1. **Generic corpus/evaluator machinery** knows typed Representation/evidence contracts and
   generic structure.
2. **Case-specific helpers** may understand a language, source, genre or layout, but are
   optional aids. They cannot define product ontology, completeness or universal support.

`lector_002_benchmark.py` currently implements only the `text_quote:v1` evaluator mode.
Its v2 preparation partitions UTF-8 text losslessly using page separators, blank-line
blocks and bounded continuation. It deliberately has no acta vocabulary or civic keyword
triage and keeps coverage in source order.

Structured table and timed-media evidence need their own typed evaluator modes rather than
being flattened into text.

## Current declared capability targets

The current `v2` campaign declares these targets:

| Dimension | Capability | What it stresses |
|---|---|---|
| Representation | `representation:paged_text` | page-aware text without genre assumptions |
| Representation | `representation:structured_table` | row/cell/path structure survives processing |
| Representation | `representation:timed_media` | original audio/video remains timed evidence |
| Evidence | `evidence:text_quote:v1` | exact textual evidence reopens |
| Evidence | `evidence:table_path` | exact table/path evidence reopens |
| Evidence | `evidence:media_time_span` | exact media time span reopens |
| Semantic | `semantic:multi_topic_longform` | many materially distinct propositions coexist |
| Semantic | `semantic:attribution` | who said/requested/decided/reported is preserved |
| Semantic | `semantic:conditions_exceptions_crossrefs` | conditions/scope/exceptions are not erased |
| Semantic | `semantic:structured_values` | labels, types and values survive tabular extraction |

The old six genres — minutes, report/audit, correspondence, normative/contractual,
structured data and timed media — remain useful **fixture-selection archetypes** because
together they are likely to exercise different parts of this matrix. They are not a
required product taxonomy, and a better fixture can replace or combine them if it covers
the intended failure modes more effectively.

## Current real case

`CR-ESPARZA-MINUTES-001`:

```text
benchmark_archetypes: institutional_minutes
covers:
  - representation:paged_text
  - evidence:text_quote:v1
  - semantic:multi_topic_longform
  - semantic:attribution

Acta Sesión Ordinaria N° 161 — 18 May 2026
PDF SHA256:
ffb354c67d8b56ebf265884c820a98fee27015cadaac3ea1011069f7969b8bfd

Poppler text SHA256:
02d1578cfc44097c6e5e802880919ff6f7a18bd2105330035959c4cccd467ea1
```

It remains external to the repository. Its gold is **not frozen**. Any worksheet produced
by the retired acta-shaped v1 preparation is obsolete.

The v2 generic-text worksheet may be regenerated from the same frozen Representation. A
reconstruction proof currently yields:

```text
page_count:                39
review_units:              61
unit kinds:                source=1, page=38, block=7, continuation=15
max unit span:             3992 characters
attention_heuristics_used: false
semantic_model_calls:      0
truth_generated:           false
```

Those counts prove deterministic preparation for this fixture only. They are not target
shapes for reports, correspondence, transcripts or future evidence.

## Production doctrine still stands

`machine-only` is a normal durable/searchable production state, not review debt. Corpus
gold/adjudication is engineering validation paid on a small representative set, not a rule
that every ingested Claim enters a human queue.

## Current stop condition

LECTOR-002 cannot close merely because several named document genres are present. The
current declared-capability gate remains blocked until:

1. real fixtures collectively cover every declared target capability;
2. each capability uses evidence semantics appropriate to its Representation;
3. independent gold is frozen before tested extractor output is inspected;
4. candidates are adjudicated against that gold;
5. deterministic scoring passes the accepted per-case/per-capability thresholds;
6. results are reported separately enough that one strong modality cannot hide another;
7. any materially new failure mode discovered during the campaign is added explicitly
   rather than being hidden behind a green aggregate number.

Even after closure, the claim is bounded: **the tested extractor passed the declared
LECTOR-002 capability campaign**. It is never a proof that Canario can correctly interpret
every possible future civic artifact.
