---
id: CANARIO-LECTOR-FIT-BENCH-REFERENCE-PROTOCOL-FREEZE-001
kind: benchmark-reference-protocol-freeze
state: frozen-within-active-work
authority: active-work-evidence
work: LECTOR-PRODUCTION-FIT-BENCH
created: 2026-08-27
baseline_work_activation: 9742dc87002003885eebe0475b1534d78d564eeb
depends_on: CANARIO-LECTOR-FIT-BENCH-SEMANTICS-FREEZE-001
---

# Lector fit bench — semantic reference protocol freeze v1

## Purpose

Freeze the leakage-resistant method for constructing and approving the semantic reference **before** any formal A0–A5 candidate output is inspected.

The reference represents what the source asserts; it is not a preferred wording and not an extraction prompt.

## Required freeze order

```text
1. freeze source bytes / canonical source identity
2. freeze Representation bytes + processor/provenance identity
3. freeze deterministic benchmark scope
4. freeze source-unit inventory/order
5. construct semantic reference blind to tested candidate output
6. reopen every reference evidence target mechanically
7. human approval / unresolved adjudication marking
8. freeze reference digest
9. inspect only reference counts + capability distribution
10. freeze thresholds/policy
11. freeze lane-common execution identity/bounds
12. only then expose the source to formal A0–A5 candidate runs
```

Steps may not be reordered to make a lane pass.

## Source and Representation freeze record

Every semantic fixture must record:

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

For longform text, the benchmark reference normally covers the complete frozen scope in source order. A selected structural sample is acceptable only for a capability explicitly scoped as a structural sample and must never be reported as document-complete coverage.

## Unit states

Every source unit in benchmark scope has exactly one reference state:

```text
MATERIAL_FACTS
NO_MATERIAL_CIVIC_FACT
NEEDS_ADJUDICATION
OUT_OF_SCOPE
```

`OUT_OF_SCOPE` is allowed only when the benchmark scope was deterministically frozen before reference annotation.

A unit cannot disappear merely because it is difficult to annotate.

## Reference fact object

Each material fact is stored as a semantic equivalence object with at least:

```text
fact_id
fixture_id
unit_ids
canonical_semantic_note
mandatory_qualifiers
allowed_variants_or_equivalence_notes
evidence_targets
capability_bindings
material_civic = true
reference_state
adjudication_notes
```

### `canonical_semantic_note`

This is an annotator aid describing required semantic content. It is **not** a sentence the candidate must reproduce.

### `mandatory_qualifiers`

Record every meaning-changing qualifier that a full match must preserve. Use typed keys where applicable:

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

Do not add a qualifier merely because it is nearby. Add it when omission can change the proposition.

### `allowed_variants_or_equivalence_notes`

Record known paraphrase/equivalence boundaries. This field may allow lexical or syntactic variation; it may **not** waive a mandatory qualifier.

### `evidence_targets`

One fact may require more than one exact evidence target when no single target is sufficient.

Each target must use production-compatible selector semantics and reopen from frozen Representation or typed source evidence. Reference annotations may not point to prose descriptions like "page 4-ish".

### `capability_bindings`

Bind facts/counterexamples only to capabilities they actually exercise. Capability counts are for coverage diagnostics, not a document taxonomy.

## Human approval and AI assistance

Reference construction may be AI-assisted only when provenance is explicit.

Permitted states:

```text
human_authored
human_ai_assisted
```

For `human_ai_assisted`:

- assistant proposals are drafts only;
- a human reviewer must explicitly approve, correct or leave unresolved each material fact;
- tested extractor output remains unseen until reference freeze;
- the assistant/model/provider/version and assistance scope are recorded;
- exact evidence reopening is still mechanical.

No model-generated reference is "human gold" without explicit human approval.

## Independence rule

If a reference assistant and a tested extractor use the same model family/provider, or independence is unknown:

- record the overlap explicitly;
- semantic PASS cannot be treated as strong final evidence solely from that reference;
- before strong certification, obtain an independent second-review sample from a materially independent reviewer/model family or human-only review path.

The second review checks reference correctness; it does not inspect candidate scores to tune the gold.

## Reference review packet

A human review packet may contain:

- frozen source units and local structural context;
- proposed reference facts;
- mandatory qualifiers;
- exact evidence previews;
- capability labels;
- unresolved questions.

It must not contain:

- A0–A5 outputs;
- candidate score summaries;
- "truth" fields derived from candidate consensus;
- hints that one orchestration is expected to win.

Non-selected or unresolved units remain explicitly marked. Absence of annotation must never be interpreted as `NO_MATERIAL_CIVIC_FACT`.

## Evidence reopening gate

Before reference freeze, every `evidence_target` must satisfy deterministic reopening.

For text spans:

- exact Representation identity;
- exact selector/range;
- selected bytes/text reopen;
- target remains inside frozen scope.

For typed table/media evidence, use the accepted typed selectors; do not flatten them into text to reuse this protocol.

A reference with one unreopenable required target cannot freeze.

## Semantic reference completeness audit

Before freeze, run two independent passes over the scoped source units:

1. **forward coverage pass** — inspect source order and account for every unit state;
2. **fact-to-source reverse pass** — reopen every fact and verify proposition, qualifiers and evidence.

For development longform fixtures, the reviewer must also inspect transitions between units/pages so cross-unit facts are not lost at segmentation boundaries.

Reference completeness is a human-approved benchmark assertion, not something inferred from claim count.

## Reference freeze artifact

The frozen artifact must include:

```text
reference_format_version
fixture identity block
unit-state inventory
reference facts
unresolved adjudications
reference assistance provenance
reviewer approval record
reference_sha256
evidence_reopening_proof_sha256
fact_count
unit_state_counts
capability_counts
```

The digest is computed over canonical serialized semantic content, not presentation formatting.

## Threshold freeze boundary

Numeric thresholds are **not** chosen during reference writing.

After the reference is frozen, the benchmark may inspect only:

- total reference fact count;
- per-fixture fact count;
- capability binding counts;
- unit-state counts;
- source length/structure metrics.

Then numeric thresholds and zero-tolerance counterexample rules are frozen **before formal candidate output**.

Do not inspect any A0–A5 score while selecting thresholds.

## Candidate adjudication against frozen reference

Candidate comparison is qualifier-sensitive.

For each candidate:

1. reopen candidate evidence;
2. determine whether proposition is supported;
3. compare against reference semantic content;
4. apply one primary disposition from the semantics freeze;
5. bind any error to relevant capability IDs;
6. record adjudicator notes without changing the reference.

A candidate is `FULL_MATCH` only when required semantic content and every mandatory qualifier are preserved.

## Candidate reveals missing reference fact

If formal candidate inspection surfaces a proposition that appears source-supported and material but is absent from the frozen reference:

```text
mark REFERENCE_DEFECT
invalidate that fixture's formal score for the round
do not silently add the fact and keep the score
repair/re-review the development reference
re-freeze thresholds if counts changed
restart formal lane comparison for that fixture
```

Because development fixtures may shape benchmark design, they may be repaired. A blinded natural holdout that exposes such a defect cannot be retroactively converted into clean independent certification evidence without a new untouched holdout.

## Unresolved adjudication

`NEEDS_ADJUDICATION` is a real state, not a temporary excuse to guess.

Before a fixture contributes to a capability threshold:

- all facts needed by that capability must be resolved; or
- the unresolved region must have been frozen out of that capability's scored scope before candidate exposure.

Do not resolve ambiguity using candidate majority vote.

## Leakage ledger

Maintain a fixture-level ledger recording whether any of these occurred before each freeze:

```text
tested_candidate_output_seen
candidate_score_seen
prompt_orchestration_tuned_on_fixture
threshold_tuned_on_fixture
holdout_semantics_inspected
reference_assistant_overlap
```

Any `true` value must have an explicit consequence recorded.

For a final holdout, `prompt_orchestration_tuned_on_fixture`, `threshold_tuned_on_fixture` and `holdout_semantics_inspected` invalidate independent holdout status.

## Reference protocol PASS

A fixture reference is eligible for formal lane measurement only when:

- source, Representation, scope and unit inventory are frozen;
- every scoped unit has an explicit state;
- every material fact has human approval or remains explicitly unresolved outside scored scope;
- every required evidence target reopens mechanically;
- mandatory qualifiers have been reviewed;
- reference digest is immutable;
- assistance/independence provenance is recorded;
- candidate output and scores have remained unseen;
- thresholds are subsequently frozen from reference-only counts.

## What this protocol does not authorize

- generating reference facts before exact fixture/source freeze;
- inspecting Acta 160 semantic content;
- selecting H2 by looking for a known lane weakness after candidate runs;
- running formal A0–A5 extraction before thresholds are frozen;
- implementing the winning lane in production;
- changing product schema.
