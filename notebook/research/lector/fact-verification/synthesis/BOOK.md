---
id: CANARIO-RESEARCH-LECTOR-FACTVER-SYNTHESIS-001
type: research-synthesis
state: research-complete-for-design-gate
authority: evidence
created: 2026-08-25
updated: 2026-08-25
researched_through: 2026-08-25
baseline: a1d212c84830b3a0558dd4d1d9354cf10ac7a362
---

# Synthesis: extraction, executable analysis, and verification

## Executive result

The research does **not** justify replacing Canario with an external fact-checker.
The external systems generally start after Canario's distinctive work — acquiring,
preserving, typing and attributing civic evidence — has already happened.

It **does** invalidate a meaningful part of the recent LECTOR-002 direction:
structured semantic quality cannot be established by selecting physical spreadsheet
rows and asking whether each row "contains a structured value." That measures local
lookup and representation shape, not the retrieval/composition/abstention failures
that dominate serious structured verification.

The architecture should therefore stop treating these as one problem:

```text
SOURCE EXTRACTION
  What does this source assert explicitly?

DERIVED ANALYSIS
  What can be computed from one or more Representations?

VERIFICATION / ASSESSMENT
  Does bounded evidence support, contradict, or fail to decide a claim?

ABSTENTION / SUFFICIENCY
  Is the available evidence adequate for a justified verdict?
```

`Lector` remains responsible for the first problem. The other three need a separate
design boundary or explicit derivation/assessment path; they should not be smuggled
into Lector merely because an LLM can perform all of them.

## KEEP from Canario

1. **Artifact custody and exact Representation lineage.** None of the studied
   verifiers replaces source acquisition/custody.
2. **Typed evidence locators.** External benchmarks strengthen the need for
   multi-evidence, not text flattening.
3. **Source assertion vs derived inference.** This existing Claim distinction is
   exactly the boundary needed to prevent calculations from masquerading as what a
   document literally says.
4. **Assessment separate from Claim lifecycle/review.** Entailment/refutation is a
   judgment over evidence, not Claim identity.
5. **Source Authority.** CaseFacts and the Thucy collision make this more important,
   not less.
6. **Machine-only as valid production state.** Benchmark annotation is engineering
   evidence, not a production ingestion requirement.
7. **Provider/model independence and bounded egress.** External agent frameworks are
   implementation candidates, not architectural authority.
8. **Heterogeneous Representation design.** FinDVer/FEVEROUS/TSVer reinforce the
   need to preserve text, tables and temporal evidence distinctly.

## CHANGE in Canario

### 1. Split structured semantic capabilities

Retire `semantic:structured_values` as a sufficient single semantic claim about
structured-data quality. A candidate replacement capability family should distinguish
at least:

```text
structured:explicit_value_extraction
structured:evidence_retrieval
structured:numerical_composition
structured:cross_table_composition
verification:evidence_sufficiency
verification:abstention
```

Exact naming is a later design decision; the separation is the research conclusion.

### 2. Separate structural sampling from semantic cases

Blank/styled rows can be valuable deterministic Representation fixtures. They should
not consume semantic benchmark slots unless absence itself is the declared semantic
phenomenon. Structured semantic cases should be derived from meaningful operations or
questions over actual values.

### 3. Make interpretation context wider than the evidence locator

A compact locator answers "where can I reopen evidence?" It must not silently answer
"how much source context may be used to interpret it?" Adopt explicit context/evidence
separation and support multi-evidence propositions.

### 4. Introduce executable derivation provenance

A derived structured inference should be reproducible from something like:

```text
input Representation identities/hashes
+ bounded query/program
+ executor/runtime identity
+ exact result
+ evidence/row lineage
```

The program/query is derivation provenance, not original source evidence.

### 5. Benchmark retrieval separately from reasoning

Large-table work repeatedly identifies retrieval/grounding as an independent
bottleneck. A verifier that reasons correctly over the wrong rows is still wrong.

### 6. Treat abstention/evidence insufficiency as first-class

`NOT ENOUGH INFO` cannot be a generic escape hatch. It needs evidence-grounded
semantics and dedicated evaluation because model behavior is systematically biased.

### 7. Bound verification by Source Authority and time

A queryable data source is not automatically authoritative for every proposition.
Evidence scope, authority and temporal validity must constrain the verifier.

## DELETE / STOP BUILDING

- The bespoke strategy "sample ~24 workbook rows and use them as the semantic
  `structured_values` gold."
- The assumption that one selected review unit should simultaneously define semantic
  context, benchmark coverage, and all supporting evidence.
- Any Canario-specific SQL/agent verifier built before a Thucy baseline/fit experiment.
- Any metric that rewards a verdict without requiring adequate supporting evidence.
- Any architecture where unrestricted web search can silently outrank known
  authoritative civic sources.

## ADOPT / ADAPT external mechanisms

### Thucy — **BENCHMARK first**

Run a bounded sidecar experiment against a relational projection of Canario evidence.
Do not vendor yet: its source-authority assumption conflicts with Canario and upstream
license metadata is inconsistent.

### FEVEROUS — **ADAPT**

Study the Apache-2.0 scorer/evidence-set implementation for multi-evidence and
evidence-aware scoring. Reuse only separable mechanisms after proving they do not
carry Wikipedia-specific identity semantics.

### FinDVer — **ADAPT benchmark decomposition**

Use its extraction / numerical reasoning / knowledge reasoning separation and
`relevant_context` idea as prior art for hybrid civic documents.

### External datasets — **BENCHMARK, don't absorb blindly**

ClaimDB, frame-guided OECD, SciTab, TSVer, AVeriTeC and CaseFacts should become
external stress lanes subject to licensing and modality fit. They do not become the
Canario product ontology.

## BENCHMARK plan

1. **Structured verifier baseline:** Thucy + ClaimDB/frame-guided high-volume cases.
2. **Table composition:** SciTab plus a small Canario civic-derived set.
3. **Hybrid long documents:** FinDVer-style retrieval/context/evidence tests.
4. **Mixed text/table evidence:** FEVEROUS-style evidence-set scoring.
5. **Temporal numerical evidence:** TSVer when a real Canario source requires it.
6. **Authority-aware retrieval:** CaseFacts-inspired counterexamples where a less
   authoritative but semantically similar source conflicts with the bounded source.
7. **Human evidence UX:** ClaimVer-inspired evidence localization and explanation.


## Query-engine fit result

The technology audit narrows G1 without prematurely selecting a winner:

1. **SQLite is the mandatory simple baseline.** It already exists in Canario,
   supports the required aggregate/window/join class, exposes an authorizer for
   read-only allowlisting, has defensive/trusted-schema controls, leaves extension
   loading off by default, and supports interruption via progress handler.
2. **DuckDB is the leading analytical challenger**, not the canonical
   Representation. Its direct XLSX reader performs header/range/type inference,
   which is useful for data wrangling but unacceptable as source-fidelity authority.
3. **All model-generated SQL is untrusted executable input.** DuckDB explicitly
   documents this as Bash/Python-like risk; SQLite also documents a hardened path
   for untrusted SQL. The executor must be isolated from Canario's canonical DB,
   filesystem/network authority and semantic write paths.
4. **Arrow is an interoperability option, not an evidence model.** Keep the
   projection boundary capable of Arrow/Parquet later, but add no dependency until
   scale or multi-engine interchange justifies it.

Therefore the first structured fit bench should create one deterministic relational
projection from the canonical typed workbook and run the same cases through:

```text
A. hardened SQLite
B. sandboxed DuckDB
C. Thucy using the selected relational backend as an external verifier baseline
```

No engine may read the original XLSX independently and redefine its types/extent.

## OPEN QUESTIONS needing experiment

1. **Executor selection after benchmark:** SQLite is the simple baseline; DuckDB is the analytical challenger; Arrow/Parquet remains optional interchange. Measure civic fixtures before adoption.
2. **Thucy integration shape:** black-box baseline, sidecar adapter, fork, or no reuse.
3. **Derivation record shape:** is existing Claim `kind=derived inference` plus
   ProcessRun enough, or is a first-class derivation record required?
4. **Verifier output:** should support/refute/insufficient live as an `assessment`,
   a typed verifier result, or both?
5. **Query safety:** what SQL/program subset, resource budget and egress rules allow
   reproducible analysis without giving a semantic model arbitrary authority?
6. **Evidence sufficiency:** how should a verifier prove that retrieved evidence is
   enough, especially for negative/absence claims?
7. **Reference bias:** when reference assistance and tested verifier share model
   family/provider, what independent review sample is sufficient?
8. **Cross-modal composition:** how should one proposition cite table + text + media
   evidence without flattening either modality?

## Design gate

Do not resume LECTOR-002 semantic gold production yet.

The next authorized technical work is a bounded **structured reasoning fit bench**:
convert the existing Esparza workbook into a queryable derivative without losing its
original typed Representation lineage, run deterministic query cases, and compare a
simple bounded planner/executor against Thucy as an external baseline.

Before that bench, perform the focused query-engine technology audit named in
`gap-audit.md`.
