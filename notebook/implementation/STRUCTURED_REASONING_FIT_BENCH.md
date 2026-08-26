# Structured Reasoning Fit Bench

State: **CERTIFIED DETERMINISTIC FOUNDATION - PHASE D AUTHORIZED**

Authority:

```text
research checkpoint: 7e7fd85be5ac607fcb02ccb68b97b5e17f8fd9d6
architecture checkpoint: 516ddd613bf58ef412d59bf4600652c8045c9c6b
candidate base: 516ddd613bf58ef412d59bf4600652c8045c9c6b
public main remains: a1d212c84830b3a0558dd4d1d9354cf10ac7a362
```

This document defines the next bounded technical unit after the fact-verification SOTA
review. The bench-only implementation now lives in
`notebook/implementation/structured_reasoning_fit_bench.py` plus its isolated DuckDB
worker and evidence subtree. It remains outside production `canario/`, introduces no
schema/dependency change, and is not a verifier/model integration or semantic-reference
implementation. Runtime PASS is certified at `0f9a71e5acb0f093469571d59c896eab0c03c4c2`; SQLite remains selected, while DuckDB is a certifiable challenger with no material required advantage demonstrated on the frozen lanes.

## Purpose and Non-Goals

The complete fit-bench program closes G1-G3 from the research gap audit:

```text
G1: deterministic projection and executor fit
G2: simple bounded planner/executor versus Thucy sidecar
G3: derivation provenance fit against existing ProcessRun semantics
```

Checkpoint `0f9a71e5acb0f093469571d59c896eab0c03c4c2` certifies the deterministic foundation for **G1 + G3** and freezes the query/evidence handoff needed by G2. The actual planner/Thucy comparison is now the active Phase D and remains a separate benchmark unit. The foundation also makes evidence sufficiency,
abstention, context and multi-evidence measurable without turning them into new Claim
lifecycle states.

It must not:

- implement or invoke Thucy in this architecture checkpoint;
- vendor Thucy, ClaimDB, FEVEROUS or restricted benchmark data;
- create a query executor or verifier in `canario/`;
- modify SQLite schema, migrations, dependencies or canonical fixtures;
- regenerate LECTOR-002 semantic gold or inspect tested-extractor output;
- treat an engine, query result or model output as source authority.

The existing human product vocabulary remains:

```text
Inbox -> Depósito -> Mesa de trabajo -> Lector -> Fichero
                                      -> Mesa de control -> Consultas -> Salidas
```

Derivation and Verification are operation boundaries around that path, not new mandatory
human stages.

## Operation Boundaries

### Lector

Lector extracts what the source asserts or explicitly contains. Explicit source values,
dates, amounts, attributions, conditions, exceptions and source-stated calculations remain
valid Lector output. A newly computed sum, comparison, aggregation or join is not a source
assertion.

### Derivation

Derivation computes a new result from one or more bounded Representations and an executable
operation. The query/program is provenance, not original source evidence. A successful
proposition-worthy result may later support `Claim(kind=derived_inference)`, but a query
result does not automatically become a Claim.

### Verification

Verification evaluates a proposition against an explicitly bounded evidence scope. A
future verifier result must keep these axes separate:

```text
execution outcome
verdict: supported | contradicted | insufficient_evidence
evidence set and exact reopening
evidence sufficiency
abstention reason
process/model/configuration provenance
```

`timeout`, `crash`, `invalid_query` and `tool_failure` are execution failures, not
`insufficient_evidence`. A result cannot mutate Claim lifecycle. Assessment remains the
optional attributable durable judgment for a later policy decision.

## Phase A - Canonical Relational Projection

### Input authority

The input is a canonical typed `canario.structured_table.v1` Representation, not the
original XLSX as independently parsed by an engine. The Esparza workbook is the first
fixture only; its sheet and region mapping is a fixture manifest, not a generic source
heuristic or product ontology.

### ProjectionManifest

The future experiment must produce a deterministic manifest with at least:

```text
source Representation identity and SHA-256
projection version
sheet/table/region mapping
source row and cell identities
column identities and order
canonical scalar types
formula text versus observed/cached value distinction
null versus blank distinction
projection output encoding and digest
```

The serialization is intentionally not frozen here. The manifest must bind every projected
row/cell back to the source Representation and must be reproducible from the same retained
typed bytes. Formula text is not silently recalculated; cached values are not invented.

For external scale fixtures normalized into the same neutral projection model, projection
identity separates **transformation semantics** from **validation policy**. Encoding,
delimiter, header treatment, dataset/relation identity and column mapping affect the
projection bytes. Expected source digest/header/row-count guards are validated and recorded
in the projection manifest, but do not perturb otherwise identical projection bytes; prose
notes never participate in either deterministic identity. The exact source bytes remain
bound independently by `source_representation_sha256`.

### Projection gate

PASS requires:

- deterministic byte and hash identity across repeated projection;
- 100% fidelity for fixture-selected typed values, formula distinctions and null/blank
  distinctions;
- exact source row/cell lineage for projected values;
- no engine-native XLSX type/range inference used as source authority;
- a changed source Representation producing a changed projection identity.

## Phase B - Executor Comparison

The same ProjectionManifest and projection bytes feed both lanes:

```text
A. hardened SQLite
B. sandboxed DuckDB
```

### SQLite baseline

SQLite is mandatory because Canario already certifies the exact runtime and it provides the
first required aggregate, grouping, ordering, join and window-function surface. The future
implementation must use its authorizer, defensive/read-only controls, extension loading
disabled, interruption/progress controls and disposable derived databases.

### DuckDB challenger

DuckDB is not selected by default. It is adopted only if measured civic workloads or scale
show a material required advantage and the sandbox can be certified. Its direct XLSX reader
is not permitted to define canonical Representation semantics.

### Executor security invariant

Model-generated SQL is untrusted executable input. Neither executor may receive:

```text
canonical Canario SQLite database
arbitrary filesystem authority
network authority
extension loading or installation
write authority
semantic-writer authority
secrets or credential paths
```

The future implementation must use disposable projections and prove or measure:

- read-only enforcement;
- a query-execution timeout/interruption budget distinct from a bounded trusted bootstrap/materialization allowance; corpus runs materialize the neutral DuckDB projection once per isolated session rather than once per query;
- terminal outcome;
- memory, CPU, row and byte bounds where available;
- disabled extensions, network and file escape;
- deterministic result encoding;
- no canonical database mutation;
- no access to credentials or semantic writers.

### Executor gate

PASS requires bounded no-write execution, deterministic result representation, independently bounded **per-query** execution plus worker-process termination evidence, one trusted projection materialization per corpus session, and a clean proof that canonical DB, filesystem, network, extensions
and secrets are outside executor authority.

## Phase C - Deterministic Query Corpus

Before any LLM or external verifier, create a small frozen query/result corpus over the
single projection. Cases must cover where present:

```text
explicit lookup
filter
aggregation
grouping
ordering/top-k
window/rank
multi-step numerical composition
cross-table or cross-sheet join
negative/absence proposition with known bounded scope
insufficient-evidence proposition
```

Each case records:

```text
question or proposition
expected result
required source-row/cell evidence lineage
portable SQL where possible
engine-specific variant only when unavoidable
expected sufficiency/abstention semantics
```

This lane proves projection and executor semantics independently of model quality. A
negative case must distinguish `not_found_in_bounded_scope` from `does_not_exist`; the
latter requires adequate inventory/completeness authority.

## Phase D - Planner and Verifier Fit

Only after Phases A-C pass, compare:

```text
simple bounded single planner/executor
versus
Thucy as a black-box external sidecar
```

Do not build a sophisticated private multi-agent verifier first. Keep Thucy external and
non-vendored. Use the same frozen cases, ProjectionManifest, Source Authority scope,
resource profile and, where feasible, model/provider conditions.

Measure separately:

```text
verdict correctness
evidence correctness and reopenability
retrieval recall
unsupported or hallucinated evidence
evidence sufficiency classification
abstention precision and recall
query/tool success
tool-call count
latency
token/API cost
terminal failure modes
```

A correct verdict with wrong, incomplete or non-reopenable evidence does not pass. A
timeout or tool crash is reported as execution failure, not as an abstention success.

### Thucy stop conditions

Do not vendor or fork during this bench. Stop reuse/adaptation if:

- bounded Source Authority cannot be enforced without invasive redesign;
- evidence queries cannot be captured and reproduced adequately;
- quality or performance does not beat or complement the simple baseline;
- the upstream MIT `LICENSE` versus Apache-2.0 `pyproject.toml` conflict remains
  unresolved for proposed code reuse.

The license conflict blocks vendoring, not black-box benchmarking. External dataset and
software licenses must remain separately recorded.

## G3 - Derivation Provenance Experiment

The bench must attempt to represent one successful and one failed derived query using the
existing `ProcessRun` semantics, without writing production rows. The required conceptual
record is:

```text
ordered input Representation/target identities
optional input Claim revisions where justified
exact query/program/specification
executor implementation and version
configuration/policy identity
resource/sandbox profile
terminal execution outcome
exact result bytes/value
source-row/cell/evidence lineage where available
timestamps
```

Report whether ProcessRun can carry this without confusing a derivation with a
Representation processor, and without losing exact result or lineage. If it cannot, the
bench must state the minimum first-class derivation record design required later. Neither
result authorizes a schema change in this checkpoint.

## Required Dataset Lanes

1. Existing Esparza structured workbook through the canonical typed Representation and
   an explicit frozen ProjectionManifest.
2. At least one larger public structured dataset that stresses scale, kept external unless
   licensing permits execution without repository vendoring.
3. A small external prior-art lane, where licensing permits, selected from ClaimDB,
   frame-guided OECD or SciTab. External schemas remain benchmark metadata, not Canario
   product ontology.

ClaimDB, TSVer and other ShareAlike material, and AVeriTeC non-commercial material, must
not be copied into the repository merely for convenience.

## Gate Summary

### Projection gate

Deterministic identity, typed-value/formula/null fidelity and exact source lineage pass;
no engine independently reinterprets XLSX.

### Executor gate

Disposable, bounded, no-write execution terminates reproducibly without canonical DB,
network, extension, filesystem, semantic-writer or secret authority.

### Engine selection

SQLite remains selected unless DuckDB demonstrates a material required advantage on the
same projection and its sandbox is certifiable.

### Verifier gate

No private verifier architecture is authorized until the simple baseline versus Thucy
comparison exists.

### Evidence gate

Verdict quality, evidence correctness/reopenability and evidence sufficiency are scored
separately.

### Abstention gate

Insufficient-evidence cases are independently represented and scored; execution failures
are not counted as epistemic abstention.

## Required Bench Artifacts

The future implementation may produce these disposable experiment artifacts outside the
canonical schema and production code:

```text
ProjectionManifest
projection bytes + digest
frozen deterministic query/result corpus
executor security/resource report
engine comparison report
planner/Thucy comparison report
derivation provenance fit report
```

No artifact from this list is an authorized canonical table, Claim, Assessment, semantic
gold row or production dependency. The bench closes only when G1-G3 and the evidence,
abstention and security gates have evidence-backed answers.
