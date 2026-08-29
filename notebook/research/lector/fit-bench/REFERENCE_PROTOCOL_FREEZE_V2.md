---
id: CANARIO-LECTOR-FIT-BENCH-REFERENCE-PROTOCOL-FREEZE-002
kind: benchmark-reference-protocol-freeze
state: frozen-within-active-work
authority: active-work-evidence
work: LECTOR-PRODUCTION-FIT-BENCH
created: 2026-08-28
baseline_work_activation: 9742dc87002003885eebe0475b1534d78d564eeb
depends_on: CANARIO-LECTOR-FIT-BENCH-SEMANTICS-FREEZE-001
supersedes: CANARIO-LECTOR-FIT-BENCH-REFERENCE-PROTOCOL-FREEZE-001
---

# Lector fit bench — semantic reference protocol freeze v2

## Purpose

Freeze a leakage-resistant way to construct semantic benchmark references **without making the
project owner perform fact-by-fact clerical annotation** and without pretending that model-authored
reference material is human gold.

The benchmark target from `BENCHMARK_SEMANTICS_FREEZE_V1.md` is unchanged. The reference still
represents what the frozen source asserts; it is not a preferred wording, a candidate prompt, or a
truth assessment.

V2 changes **who authors and certifies the reference**, not what counts as a good Lector Claim.

## Why v1 is superseded

V1 required a human reviewer to explicitly approve, correct, or leave unresolved every material
reference fact. That requirement was defensible for a small fixture, but F3 demonstrated that it is
not a scalable engineering contract for broad civic sources: one real regulation or long municipal
record can contain hundreds of material assertions.

The project owner explicitly declined a fact-by-fact annotation workload. Canario also treats
`machine-only` as a normal durable production state, so benchmark governance must distinguish
**semantic review quality** from **manual clerical volume**.

No formal A0-A5 candidate output or score was seen before this protocol change. Acta 160 and H2
remain untouched. Therefore this amendment does not tune the reference protocol to a tested lane.

## Authoring and certification roles

The default F3 role split is:

```text
supervising/cloud author
-> architecture + semantic reference authorship + repository writing

local execution agent
-> exact source-pack access + hashes + selector reopening + validators + tests + bundles + exact push

independent semantic reviewer
-> source-grounded challenge of reference completeness/faithfulness before freeze
```

The local execution agent is **not** a substitute architect or reference author. It may not silently
rewrite, repair, decompose, merge, add, or delete semantic facts while performing mechanical
certification. A semantic failure returns to the supervising author as evidence.

A materially independent semantic reviewer may be another model/provider family or a human. It is
not assumed to be the local execution agent merely because that agent has machine access.

## Required freeze order

```text
1. freeze source bytes / canonical source identity
2. freeze Representation bytes + processor/provenance identity
3. freeze deterministic benchmark scope
4. freeze source-unit inventory/order
5. supervising author constructs a source-exhaustive semantic reference blind to tested output
6. supervising author performs omission-only forward audit
7. supervising author performs reverse fact-to-source semantic audit
8. local certifier mechanically reopens every required evidence target and validates identities
9. independent semantic reviewer audits reference correctness/completeness blind to tested output
10. resolve reviewer disputes from source evidence only; unresolved hard-gate regions remain explicit
11. freeze canonical reference digest + review/certification provenance
12. inspect only reference counts/capability distribution
13. freeze thresholds/policy
14. freeze lane-common execution identity/bounds
15. only then expose the source to formal A0-A5 candidate runs
```

Steps may not be reordered to make a lane pass.

## Reference states

Reference artifacts use explicit maturity states:

```text
SUPERVISOR_DRAFT
SUPERVISOR_ACCEPTED
INDEPENDENT_REVIEW_REQUIRED
INDEPENDENTLY_AUDITED
REFERENCE_DISPUTE
FROZEN
```

`SUPERVISOR_ACCEPTED` is not called `gold`, `human gold`, or `FROZEN`.

A development fixture may exist in `SUPERVISOR_ACCEPTED` state while further fixtures are authored,
but formal A0-A5 scoring for that fixture remains blocked until the required independent semantic
audit and final freeze are complete.

## Source and Representation identity

Every fixture reference remains bound to:

```text
fixture_id
role = development | holdout
source_authority
source_locator
source_retrieved_at
source_bytes_sha256
artifact/custody identity if ingested
representation_kind
representation_bytes_sha256
processor/run identity
selector semantics
benchmark_scope
scope_sha256
source_unit_inventory_sha256
language
institution/source family
```

No semantic review can repair an identity mismatch. If source, Representation, scope, or unit
identity changes, stop and re-establish the fixture boundary before annotating.

## Unit accounting

Every frozen source unit is accounted exactly once as:

```text
MATERIAL_FACTS
CONTEXT_ONLY
NO_MATERIAL_CIVIC_FACT
NEEDS_ADJUDICATION
OUT_OF_SCOPE
```

`OUT_OF_SCOPE` is allowed only when the deterministic benchmark scope excluded that region before
semantic annotation.

`CONTEXT_ONLY` means the unit supplies a required heading, antecedent, attribution, recipient,
definition, or other context consumed by one or more facts but contains no independent material
assertion of its own.

A unit cannot disappear because it is difficult to annotate.

## Structure-exhaustion ledger

Unit-level coverage is necessary but not sufficient. One long unit can contain many independent
material assertions.

Each fixture therefore records a source-visible, annotation-only exhaustion ledger appropriate to
its structure, for example:

```text
minutes      -> agenda item / correspondence / speaker turn / formal decision block
correspondence -> paragraph / numbered item / signature or routing block
regulation   -> article / lettered or numbered normative clause
report       -> numbered paragraph / material table row / conclusion / disposition sub-item
```

This ledger is benchmark annotation infrastructure only. It does not create a finite document
taxonomy or become production Lector segmentation authority.

Every material carrier must explicitly reach:

```text
material_assertions_exhausted = PASS
```

after an omission-focused pass. "At least one fact maps to this unit" is never completeness proof.

## Reference fact object

Each material fact is a semantic equivalence object with at least:

```text
fact_id
fixture_id
source_order_position
unit_ids
structure_ids when applicable
canonical_semantic_note
mandatory_qualifiers
allowed_variants_or_equivalence_notes
evidence_targets
capability_bindings
material_civic = true
reference_state
semantic_audit
adjudication_notes
```

### Semantic note

`canonical_semantic_note` is a concise source-faithful proposition in the source language. It is an
annotator/scorer aid, not mandatory candidate wording.

It must not be:

```text
raw evidence copied as the semantic note
a heading or list fragment without its predicate
a whole source block used instead of decomposition
a generic summary that merges separable material assertions
```

### Self-sufficient minimality

Split separable material propositions when each can stand faithfully alone. Keep with a proposition
every qualifier whose removal changes meaning, including attribution, condition, exception,
negation, modality, temporal scope, quantitative base/unit/period, jurisdiction/object scope, or a
required antecedent.

### Mandatory qualifiers

Use concrete fact-specific values only:

```text
attribution
condition
exception
scope
negation
modality
temporal
quantity
unit
currency
denominator
period
location
referent
cross_reference
```

Empty means `[]`. Placeholder values such as `actor indicated in source`, `time indicated`,
`obligation`, `hecho reportado`, or string-valued `False` are forbidden.

Identifiers are referents, not quantities. `QTY-01` is reserved for actual amounts, rates,
percentages, counts, measurements, thresholds, and their required units/bases/periods.

### Capability bindings

Bind only capabilities actually exercised by the fact. Fixture-wide capability templates are
forbidden.

`FID-01` remains reserved for the separate controlled source-fidelity counterfactual fixture. A
natural fact does not receive `FID-01` merely because it contains negation or an unusual assertion.

`CTX-01` requires context outside the fact's local frozen unit/semantic segment. Same-unit syntax or
antecedents do not by themselves exercise cross-unit context recovery.

## Evidence targets

Every fact binds to the smallest **semantically sufficient** exact evidence target set, not merely
the shortest lexical match.

One fact may require multiple targets when, for example:

```text
heading + operative clause
recipient/signatory + attributed statement
antecedent + following sentence
table row label + count/denominator
cross-page continuation
```

Each target must:

- bind to the exact frozen Representation/typed source evidence;
- reopen deterministically;
- remain inside frozen scope;
- support the proposition and every mandatory qualifier it is used to justify.

A reopenable substring that does not entail the whole proposition fails semantic evidence support.

## Supervising-author passes

### Pass A — source-order exhaustive construction

Read the entire frozen scope in source order. Account every unit and structure carrier. Enumerate all
material civic assertions under the frozen semantics. There is no target fact count and no per-unit
fact cap.

### Pass B — omission-only audit

Re-read the source with one question:

> What material civic assertion present in this source is absent from the current reference?

Pay special attention to secondary conjuncts, conditions, exceptions, future steps, deadlines,
quantities, attribution changes, legal duties, table rows, cross-unit antecedents, and repeated
assertions whose qualifiers change.

### Pass C — reverse semantic audit

For every final fact explicitly verify:

```text
source entailment
self-sufficient minimality
mandatory qualifier support
evidence semantic sufficiency
unit/structure mapping
capability binding semantics
duplicate/equivalence handling
```

Audit notes must be fact-specific enough to reveal what was checked. Generic `PASS` boilerplate is
not semantic evidence.

## Local mechanical certification

The local execution agent may verify and, where the candidate already defines the intended exact
text, mechanically materialize:

```text
source/Representation/scope/unit hashes
exact selector offsets
quote uniqueness/disambiguation
scope containment
evidence reopening
JSON/schema invariants
ID uniqueness/referential integrity
coverage-ledger arithmetic
repository tests/validators
bundle completeness
exact commit/tree before push
```

It may not change semantic notes, qualifiers, capability bindings, structure classifications, or fact
membership to make a validator pass. Such a failure returns to the supervising author.

## Independent semantic audit

Before `FROZEN`, a materially independent reviewer receives only:

```text
frozen source/scope and structure ledger
proposed reference facts
qualifiers/evidence
semantic audit provenance
```

It receives no A0-A5 outputs, scores, winner hints, or candidate consensus.

The reviewer checks both directions:

1. **source -> reference**: missing material assertions / wrong non-material classifications;
2. **reference -> source**: entailment, qualifiers, minimality, attribution, evidence sufficiency.

Each disagreement becomes `REFERENCE_DISPUTE`; it is not resolved by majority vote. Resolution must
cite source evidence and remain blind to candidate output.

### Independence strength

Record reviewer model/provider/version or human role when observable.

If author and reviewer independence is unknown or materially overlaps, mark it explicitly. Such a
reference may still serve internal development analysis, but a final strong fit-bench selection
cannot rely solely on that overlap. Obtain a materially independent review path before final
selection evidence is called strong.

## Human involvement

Human fact-by-fact approval is **not a default F3 requirement**.

Human review is reserved for:

- a `REFERENCE_DISPUTE` that the source-grounded independent review process cannot resolve;
- genuinely ambiguous source regions whose inclusion/exclusion affects a hard capability gate;
- a bounded independent spot-check when required to strengthen final certification evidence.

If human review occurs, record exactly what was reviewed. Never label model-authored material as
human-approved merely because the owner authorized the workflow.

## Reference freeze artifact

A frozen fixture reference records at least:

```text
reference_format_version
fixture identity block
unit-state inventory
structure-exhaustion ledger
reference facts
unresolved/dispute inventory
supervising-author provenance
local mechanical certification provenance
independent semantic-review provenance
reference_sha256
evidence_reopening_proof_sha256
fact_count
unit_state_counts
capability_counts
leakage ledger
```

The canonical digest is computed over serialized semantic content and bindings, not presentation
formatting.

## Threshold boundary

Thresholds remain forbidden during reference writing/review.

Only after the reference is `FROZEN` may the benchmark inspect:

```text
total fact count
per-fixture fact count
capability binding counts
unit-state counts
source length/structure metrics
```

Then thresholds and zero-tolerance counterexample rules freeze **before** tested candidate output.

## Candidate reveals a reference defect

The V1 rule remains unchanged:

```text
mark REFERENCE_DEFECT
invalidate that fixture's formal score for the round
do not silently add the fact and keep the score
repair/re-review the development reference
re-freeze thresholds if counts changed
restart formal lane comparison for that fixture
```

A blinded holdout that exposes such a defect cannot be retroactively converted into clean
independent certification evidence without a new untouched holdout.

## Leakage ledger

Maintain fixture-level flags:

```text
tested_candidate_output_seen
candidate_score_seen
prompt_orchestration_tuned_on_fixture
threshold_tuned_on_fixture
holdout_semantics_inspected
reference_author_candidate_model_overlap
independent_reviewer_overlap
```

Any `true` or `unknown` independence value carries an explicit consequence.

## Reference protocol PASS

A fixture may become `FROZEN` only when:

- source, Representation, scope, and unit inventory are frozen;
- every scoped unit and structure carrier is accounted;
- the supervising author completed source-order, omission-only, and reverse audits;
- every material carrier passed assertion exhaustion;
- every material fact has source-faithful semantics, reviewed mandatory qualifiers, and exact
  semantically sufficient evidence;
- every required evidence target mechanically reopens;
- unresolved hard-gate regions are zero or explicitly removed from scored scope before candidate
  exposure;
- independent semantic audit completed with disputes resolved from source evidence;
- authorship/reviewer/mechanical-certification provenance is recorded truthfully;
- candidate output and scores remain unseen;
- canonical reference digest is immutable;
- thresholds are subsequently frozen from reference-only counts.

## What this protocol does not authorize

- treating local execution-agent output as architecture/reference authority;
- fabricating human approval;
- running A0-A5 before reference + threshold freeze;
- inspecting Acta 160 or H2 for tuning;
- selecting a provider/model or production orchestration before measured evidence;
- implementing the eventual winning lane in production;
- changing product schema.
