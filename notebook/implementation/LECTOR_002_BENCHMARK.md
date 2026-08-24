# LECTOR-002 — Acta 161 semantic benchmark scaffold

State: **BENCHMARK PREPARATION COMPLETE — GOLD TRUTH NOT YET FROZEN**

Parent authority:

```text
main = 98c2d60387fd7ec176033563566f62c59123587d
LECTOR-001 = certified + integrated semantic extraction boundary
```

## Purpose

LECTOR-002 is the first real broad civic-extraction proof. It must answer two
separate questions without conflating them:

1. **structural integrity** — can every persisted candidate reopen exact source
   evidence, preserve provenance/scope, replay safely, and avoid forbidden
   authority?
2. **semantic quality** — did the extractor capture the materially relevant civic
   propositions without distortion, unsupported claims, duplicate explosion, or
   destructive over-merging?

The first class is mostly machine-proof. The second needs an independent reference
set and final human semantic judgment.

## Production doctrine versus certification doctrine

Production does **not** require claim-by-claim human approval. `machine-only` is a
valid durable state: searchable, attributable, evidence-backed, and explicitly not
human-reviewed. Human review is demand-driven or policy-driven, not ingestion debt.

LECTOR-002 is different. A one-time gold benchmark is engineering validation of the
extractor itself. Avoiding independent semantic review here would only prove that
citations reopen, not that broad civic material was actually found.

## Frozen source fixture

The external source pack supplied for this unit contains:

```text
Municipalidad de Esparza
Acta Sesión Ordinaria N° 161 — 18 de mayo de 2026
PDF SHA256:
ffb354c67d8b56ebf265884c820a98fee27015cadaac3ea1011069f7969b8bfd

Poppler extracted text SHA256:
02d1578cfc44097c6e5e802880919ff6f7a18bd2105330035959c4cccd467ea1
```

The source pack remains outside the repository. No source PDF/text or operator data
is committed by this benchmark scaffold.

## Deterministic preparation

`notebook/implementation/lector_002_benchmark.py prepare`:

- reads the exact UTF-8 Representation;
- partitions **all** characters into lossless review units;
- preserves page, character offsets, current article/item context, and exact unit
  text;
- recognizes only mechanical boundaries (article, numbered item, `SE ACUERDA`,
  speaker turn, session close, bounded continuation);
- assigns deterministic triage cues for decision/action/money/deadline/legal/etc.;
- never drops low-score units;
- never writes a proposition or review decision;
- records `truth_generated=false` and `semantic_model_calls=0`.

`triage_score` is an attention-ordering aid only. It is deliberately **not** named
confidence and has no truth/review authority.

Generated external worksheet:

```text
manifest.json   frozen preparation identity
units.csv       compact ordered review index
units.jsonl     exact lossless unit text + offsets
coverage.csv    human coverage decisions (initially blank)
truth.csv       human gold propositions (initially header-only)
candidates.csv  future extractor export template
assessment.csv  future human candidate adjudication template
README.md       workflow contract
```


## Acta 161 preparation proof

The frozen external Representation was prepared twice independently with byte-for-byte
identical worksheet outputs:

```text
source text SHA256:
02d1578cfc44097c6e5e802880919ff6f7a18bd2105330035959c4cccd467ea1

source bytes:       154866
source characters:  151940
PDF pages:           39
review units:        146
max unit span:       4955 characters

unit kinds:
  session            1
  article            5
  item              32
  agreement         30
  speaker           75
  continuation       3

triage score >= 5:  57
triage score >= 3:  82
triage score == 0:  33  (retained; never dropped)

semantic model calls: 0
truth generated:      NO
```

The detected article headings are exactly `I`, `II`, `III`, `IV`, `VI`; the harness
preserves that source fact and does not invent or normalize an `ARTÍCULO V`.

Real-fixture output hashes from both preparation runs:

```text
README.md      b81a82191f1f070111389eb8d17579712eaf991b16113aa25d63c59ce0bbb28d
assessment.csv 9020289ba741a724bc97970efcdf001f3f89f4f9a31761174a8e5006f3f5aebd
candidates.csv c1ca3863701da57d6362c0670d71d04bd7ac5630cb814214d87e54bf7b4cd020
coverage.csv   657042a7686567b30053977ee83ac4c497ba597cbd52cefb7feb2e8efbcea90a
manifest.json  1a57483d58bbba805c72b7e47018ad54af7580808c7baf3e3ab7a1615d86e702
truth.csv      48cde93a262cb0157e1204546303196bed27fea8ae70118d20d0c0f226ac9094
units.csv      a2ab75f396209d83f6250a306efd4257ccee10bfbbba6b4f07f21e702df45281
units.jsonl    d80d67e61224b108c00d253ea48fd48bb9c9d4a72213e6ec38f07bba285dcdf2
```

The scorer was also run intentionally against the untouched blank gold worksheet and
failed closed on the first unreviewed unit rather than producing zero/empty metrics.

Regression evidence for this checkpoint:

```text
focused LECTOR + benchmark: 46 passed
full repository:             171 passed + 2 subtests
compileall:                  PASS
git diff --check:            PASS
0001 production/spec SHA:    5226c873487d9bd05fc62b7a1f323d6e804b003cc4e08bd2fe2b531adb6057bb
schema changes:              NONE
```

The available container Python links SQLite 3.46.1 rather than the exact registered
3.53.4 runtime. This unit performs no canonical SQLite write and changes no schema;
LECTOR-001's exact-runtime certification remains parent evidence rather than being
reclaimed here.

## Gold completeness contract

Every review unit must eventually have exactly one coverage state:

```text
truth_recorded
no_material_truth
```

A `truth_recorded` unit must own at least one truth row. A
`no_material_truth` unit must own none. This makes omissions visible instead of
letting the benchmark silently inspect only heuristic hits.

Each truth has:

```text
truth_id
unit_id
importance = must | material
proposition
evidence_quote
evidence_start
evidence_end
```

The exact quote/offsets must reopen against the frozen Representation.

Machine/LLM assistance may later suggest likely truths or candidate matches to
reduce reviewer search, but it cannot set the final coverage state, gold truth, or
semantic verdict by itself.

## Candidate adjudication and deterministic scoring

Only after the gold set is frozen should a real extractor be run. Every candidate
then receives one human semantic verdict:

```text
correct
distorted
unsupported
redundant
overmerged
```

A correct candidate maps to exactly one truth. `overmerged` maps to two or more. Unsupported
candidates map to none.

The scorer does **not** decide semantic equivalence. It validates that truth and
candidate evidence reopen exactly, requires complete unit coverage and complete
candidate adjudication, then computes:

- must recall;
- material recall;
- relevance precision;
- unsupported rate;
- redundant rate;
- overmerge rate;
- distorted rate;
- uncovered truth IDs.

This preserves the rule:

```text
human: semantic judgment
software: validation + accounting
```

## Current stop condition

Do not run Codex/another real claim extractor against Acta 161 until the gold truth
set is frozen independently. Doing so first would contaminate the reference set by
showing the reviewer what the tested extractor chose to notice.

The deterministic worksheet has now been generated and its segmentation/ergonomics
checked without semantic/model calls. The next gate is to complete unit coverage and
freeze the independent gold truth from that worksheet before any tested extractor sees
Acta 161.
