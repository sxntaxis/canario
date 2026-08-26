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

A green gate means only that every **currently declared capability target** has satisfied
its declared verification mode. Representation/evidence capabilities use deterministic proof
against frozen bytes and production-compatible reopening; semantic-stress capabilities use
a frozen, human-approved reference plus adjudication. The current campaign permits declared
AI assistance while keeping the tested extractor hidden until the reference is frozen. Per-case semantic scores and their thresholds remain
separate evidence; results must still be reported by capability and fixture so aggregate
strength cannot hide a weak modality.

This distinction is deliberate. Human approval is necessary to decide whether a proposition
belongs in the semantic reference and later whether a candidate recovered it correctly; declared
AI assistance may support that review but does not become source evidence itself; it is not necessary to decide whether a byte-identical
cell/range or media time span reopens. Requiring gold for structural invariants would add
annotation labor without increasing assurance.

## Generic evaluator machinery versus optional specialization

1. **Generic corpus/evaluator machinery** knows typed Representation/evidence contracts and
   generic structure.
2. **Case-specific helpers** may understand a language, source, genre or layout, but are
   optional aids. They cannot define product ontology, completeness or universal support.

`lector_002_benchmark.py` implements `text_quote:v1` plus typed worksheet and scoring modes
for `table_range:v1` and `media:v1`. Typed scoring runs selectors through the production
`TargetRegistry` and runtime locator reopener before computing the same explicit candidate-to-reference adjudication
metrics used by text mode. Media preparation/scoring additionally requires a canonical media
index bound by exact source digest and trusted duration. The modes never generate truth,
candidates, or semantic calls. Media review windows are uniform mechanical partitions only;
they do not define semantic completeness.

Structured table and timed-media evidence therefore remain typed rather than being flattened
into text.

## Current declared capability targets

The current `v5` campaign declares these targets:

| Dimension | Capability | Verification | What it stresses |
|---|---|---|---|
| Representation | `representation:paged_text` | deterministic | page-aware text without genre assumptions |
| Representation | `representation:structured_table` | deterministic | row/cell/path structure survives processing |
| Representation | `representation:timed_media` | deterministic | original audio/video remains timed evidence |
| Evidence | `evidence:text_quote:v1` | deterministic | exact textual evidence reopens |
| Evidence | `evidence:table_path` | deterministic | exact table/path evidence reopens |
| Evidence | `evidence:media_time_span` | deterministic | exact media time span reopens |
| Semantic | `semantic:multi_topic_longform` | semantic gold | many materially distinct propositions coexist |
| Semantic | `semantic:attribution` | semantic gold | who said/requested/decided/reported is preserved |
| Semantic | `semantic:conditions_exceptions_crossrefs` | semantic gold | conditions/scope/exceptions are not erased |
| Semantic | `semantic:structured_values` | semantic gold | labels, types and values survive tabular extraction |

The old six genres — minutes, report/audit, correspondence, normative/contractual,
structured data and timed media — remain useful **fixture-selection archetypes** because
together they are likely to exercise different parts of this matrix. They are not a
required product taxonomy, and a better fixture can replace or combine them if it covers
the intended failure modes more effectively.

## Semantic gold protocol and current cases

Semantic cases carry independent `gold_scope_state`, `gold_state`, `adjudication_state`
and per-capability `semantic_verification`. A frozen scope is bound to exact source and
units bytes; it is benchmark scope, not a product ingestion ontology. Gold frozen and
adjudication complete do not verify a semantic capability. Verification additionally
requires a passed per-capability evaluation with a valid immutable result digest, after
threshold policy is frozen. See `LECTOR_002_GOLD_PROTOCOL.md`.

Truth rows bind to sorted semicolon-separated semantic `capability_ids`. Deterministic
capabilities cannot appear in truth bindings. `semantic:multi_topic_longform` is
scope-wide: all truths in the selected full-source scope contribute without requiring
reviewers to invent topic labels. Other semantic metrics derive membership from truth
bindings and human adjudication; semantic matching remains automated=false.

The current extractor-blind frozen review scopes are:

| Case | Scope | Units | Semantic target |
|---|---|---:|---|
| `CR-ESPARZA-MINUTES-001` | full source order | 61 | longform scope-wide, attribution |
| `CR-ESPARZA-BUDGET-001` | deterministic structural sample | 24 of 211 | structured values |
| `CR-INCOP-CORRESPONDENCE-001` | full source order | 17 | conditions/exceptions/cross-references, attribution |

The table sampler is source-digest-seeded and structural-only: it represents sheets,
boundary rows, represented value types, formula/merged structure when present, row-shape
diversity, and deterministic hash-ranked fill. It does not inspect labels or candidate
extractor output. A sampled result cannot claim full-workbook semantic recall.

The three packets are frozen for scope only. Their coverage, truth and assessment
worksheets are intentionally empty/unjudged as appropriate. No semantic model or tested
extractor has seen benchmark content for annotation. The timed-media case remains
deterministic-only with `transcript_status=NOT_GENERATED` and has no semantic packet.

## Current real case

The frozen typed fixtures are represented but not gold-ready:

| Case | Representation | Evaluator | Gold | Transcript |
|---|---|---|---|---|
| `CR-ESPARZA-BUDGET-001` | structured XLSX/table | `table_range:v1` | pending, 0 rows | n/a |
| `CR-INCOP-PUERTO-CALDERA-MEDIA-001` | retained MP4/timed media | `media:v1` | pending, 0 rows | `NOT_GENERATED` |

Their fixture manifests assert `semantic_model_calls=0`, `truth_generated=false`, and
`tested_extractor_seen=false`. Collection does not imply representation, evaluator, gold,
or adjudication readiness; those states are explicit in `lector_002_corpus.json`.

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
reference/adjudication is engineering validation paid on a small representative set, not a rule
that every ingested Claim enters a human queue.

## Current stop condition

LECTOR-002 cannot close merely because several named document genres are present. The
current declared-capability gate remains blocked until:

1. real fixtures collectively cover every declared target capability;
2. each capability uses evidence semantics appropriate to its Representation;
3. deterministic-mode capabilities pass their frozen-byte/locator proofs;
4. a human-approved semantic reference is frozen before tested extractor output is inspected;
   declared AI assistance is provenance, not source evidence;
5. semantic candidates are adjudicated against that frozen reference;
6. deterministic scoring passes the accepted per-case/per-capability thresholds;
7. results are reported separately enough that one strong modality cannot hide another;
8. any materially new failure mode discovered during the campaign is added explicitly
   rather than being hidden behind a green aggregate number.

Even after closure, the claim is bounded: **the tested extractor passed the declared
LECTOR-002 capability campaign**. It is never a proof that Canario can correctly interpret
every possible future civic artifact.
