# Canario Lector production fit bench

Kind: work
Status: active
Created: 2026-08-27
Activated: 2026-08-27
Authority: owner-approved after governance merge 45997d5088f88ef75e00f08a310e84292a4a077b

## ELI5

Canario already has the safe pipe that accepts semantic proposals and stores evidence-backed Claims.

What it does **not** yet know is the best way to read a long civic source comprehensively.

This Work does not build the final Lector. It runs a controlled contest:

```text
same sources
same frozen reference
same model/provider where possible
same evidence rules

A0 simple whole-document read
A1 local chunks
A2 repeated local passes
A3 contextual staged extraction
A4 contextual extraction + explicit coverage repair + reconciliation
A5 dynamic/agentic decomposition challenger
```

The **simplest approach that passes every frozen semantic gate wins**.

Only a later separately authorized Work may implement that winner as the production broad Lector.

## Goal

Select or reject a production orchestration strategy for broad civic source extraction using a
Canario-native, leakage-resistant fit bench.

## Pressure

LECTOR-001 certifies the bounded extraction/persistence boundary but explicitly does not certify
semantic quality. The superseded LECTOR-002 campaign was stopped before replacement gold because its
structured semantic capability model conflated extraction, retrieval, composition and verification.
That reasoning split has since been resolved and certified.

The interrupted first vertical then exposed the remaining open gate: no production broad-Claim
extractor has been selected or certified.

Research through 2026-08-27 shows that:

- schema-valid output and exact quotes do not establish completeness or faithfulness;
- whole-document long-context calls can omit material facts;
- naive independent chunking can destroy dependencies/context;
- maximal atomization can remove necessary meaning;
- repeated passes can improve recall but may repeat systematic blind spots;
- structured-output breadth can itself degrade semantic quality;
- LLMs can silently "correct" source material from parametric knowledge;
- English performance does not establish Spanish institutional performance.

## Authority / prerequisites

Activation prerequisite satisfied: governance reconciliation is accepted/merged through PR #9 at `45997d5088f88ef75e00f08a310e84292a4a077b`.

Research basis:
- current accepted Canario contracts and LECTOR-001;
- historical/superseded LECTOR-002 corpus and reference protocol;
- `CANARIO-LECTOR-PRODUCTION-READINESS-SYNTHESIS-001`;
- its Source Books, fit matrix, gap audit and adversarial review.

## Scope

### 1. Freeze replacement benchmark semantics

Define exact candidate capability IDs for at least:

- civic coverage / recall;
- civic focus / precision;
- source entailment / faithfulness;
- self-sufficient minimality;
- attribution preservation;
- conditions / exceptions / scope;
- negation / modality;
- temporal preservation;
- quantitative exactness;
- ambiguity behavior;
- cross-unit context;
- duplicate/conflict reconciliation;
- source-fidelity counterfactuals.

These names remain provisional until this Work freezes them.

### 2. Freeze reference protocol

Use the current leakage controls frozen in `notebook/research/lector/fit-bench/REFERENCE_PROTOCOL_FREEZE_V2.md`:

```text
freeze source + Representation + scope + units
-> supervising-author source-exhaustive reference
-> omission-only + reverse semantic audit
-> local mechanical evidence/hash certification
-> materially independent semantic audit
-> reference freeze
-> inspect fact counts
-> threshold freeze
-> only then tested extraction
```

The project owner is not required to perform fact-by-fact clerical annotation. Human review is reserved for unresolved reference disputes/ambiguity or bounded independent spot-checks. Reference entries remain semantic fact-equivalence objects, not one mandatory sentence.

### 3. Freeze development versus holdout split

Development/reference-design:
- Acta 161;
- existing INCOP correspondence;
- selected Spanish normative/contractual source;
- selected report/audit/technical source.

Typed structured/media capabilities remain separate lanes.

Natural holdouts:
- Acta 160 is reserved for the post-selection end-to-end vertical;
- at least one non-minutes Spanish civic holdout must be selected/frozen before production candidate
  finalization.

Holdout semantic contents may not be used for tuning.

### 4. Run mechanism comparison

Required baseline/challenger set unless research proves a lane strictly redundant before candidate
output is seen:

- A0 whole-document one-shot;
- A1 deterministic structure-aware units, one pass;
- A2 repeated independent unit passes;
- A3 contextual selection/disambiguation/decomposition;
- A4 contextual extraction + explicit coverage audit + targeted repair + semantic reconciliation;
- A5 dynamic agentic decomposition/optimization challenger.

### 5. Measure quality and cost separately

Primary hard semantic dimensions:
- reference-fact coverage;
- material-civic focus;
- unsupported/overstated Claim rate;
- qualifier/context errors;
- ambiguity guesses;
- evidence-support errors;
- duplicate/conflict reconciliation;
- Spanish fixture results.

Operational evidence:
- model calls;
- input/output/egress bytes or tokens where observable;
- latency;
- execution failures/timeouts;
- run-to-run variance;
- monetary cost only when reliably observable.

No global average may hide a failed required capability.

## Narrow first benchmark output

The first model-facing extraction lane should request only:

```text
candidate-local-key
proposition
exact evidence target proposal(s)
optional source attribution text
optional temporal scope
lane-specific ambiguity diagnostic when needed
```

Do not require the same call to resolve canonical Entities, create taxonomy, classify documents,
produce rich ClaimRelations, assess truth, or perform derived computation.

Those may be measured as later enrichment lanes only after Claim quality is understood.

## Product constraints

- Lector answers only what the source asserts/explicitly contains.
- Parametric/world knowledge may not silently correct source assertions.
- Tables/media retain typed Representation/evidence semantics.
- Numerical/cross-table composition stays in Derivation.
- Verification verdicts stay in Verification.
- Machine-only remains a normal durable state.
- No human review is fabricated by the benchmark.
- No finite document taxonomy is introduced.

## Non-goals

- no production extractor implementation;
- no provider/model architectural lock-in;
- no schema rebaseline unless benchmark mechanics unexpectedly prove a canonical invariant is missing,
  in which case stop for separate design review;
- no Phase-6/WP7 vertical certification;
- no GUI/MCP/query/output implementation;
- no dynamic agent framework adoption simply because A5 exists;
- no mass historical ingestion.

## Anti-overfitting rule

If a natural holdout exposes a material new failure:

```text
candidate fails
-> record the failure mode
-> revise benchmark/design
-> select a NEW untouched holdout
```

The failed holdout cannot be reused as independent certification evidence for the revised candidate.

## Selection rule

Select the **simplest lane that clears every hard frozen semantic gate**.

Examples:

```text
A0 passes all gates -> select A0
A0 fails, A1 passes -> select A1
A4 passes -> A5 remains out of production even if slightly better on a soft aggregate
```

More complexity is justified only by a measured failure that the simpler lane cannot satisfy.

## Proof obligations

Before tested lanes run:
- source/Representation/scope identities frozen;
- reference complete, supervisor-authored, mechanically certified, independently semantically audited, and frozen;
- exact reference evidence reopens;
- candidate output unseen during reference construction;
- thresholds/policy frozen;
- provider/model/config identities fixed per comparison;
- development/holdout separation recorded.

After runs:
- complete per-fixture/per-capability results;
- candidate-to-reference adjudication complete;
- semantic result digests immutable;
- operational measurements reported separately;
- repeated-run variance reported where stochastic execution is material;
- selection decision names what evidence caused every rejected simpler lane to fail.

## Exit states

Success:

```text
LECTOR_PRODUCTION_FIT_BENCH_PASS
SELECT_<LANE>
```

or, if no candidate is sufficient:

```text
LECTOR_PRODUCTION_FIT_BENCH_NO_SUITABLE_LANE
```

Either result is valid research.

## Closure / next authorization

A PASS may propose a production broad-Lector implementation Work.

It does **not** authorize that implementation automatically.

The first end-to-end Acta-160 vertical remains a later post-selection proof.

## Progress — F3 semantic reference construction

F1 benchmark semantics remain frozen. The original fact-by-fact human-approval reference protocol was superseded before any formal A0-A5 output was seen. Current protocol authority is `REFERENCE_PROTOCOL_FREEZE_V2.md`, which uses supervisor authorship, local mechanical certification, and a materially independent semantic audit before reference freeze.

F2 D1-D4 fixture/source/Representation/scope freeze is complete and merged through PR #12 at `da3854bd25f3129244ae49d8cd79a16a2c777ad6`. Exact development fixture identities remain in `FIXTURE_SOURCE_FREEZE_V1.md` and its canonical JSON companion.

F3 is active. Semantic/reference writing is owned by the supervising/cloud author. The local execution agent is limited to source-pack access, mechanical evidence/hash validation, repository tests, bundle verification, and exact push unless explicitly authorized otherwise. `REFERENCE_AUTHORING_METHOD_V1.md` records the anti-slop method.

Formal A0-A5 output/scores remain unseen, Acta 160 and H2 remain untouched, references and thresholds remain unfrozen, and production implementation remains unauthorized.
