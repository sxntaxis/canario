---
id: CANARIO-LECTOR-FIT-BENCH-SEMANTICS-FREEZE-001
kind: benchmark-semantics-freeze
state: frozen-within-active-work
authority: active-work-evidence
work: LECTOR-PRODUCTION-FIT-BENCH
created: 2026-08-27
baseline_work_activation: 9742dc87002003885eebe0475b1534d78d564eeb
---

# Lector fit bench — benchmark semantics freeze v1

## Purpose

Freeze **what the benchmark means by a good broad civic extraction** before any A0–A5 candidate output is inspected.

This document does not select a mechanism, model or provider. It defines the semantic target and failure vocabulary shared by every lane.

## Product proposition under test

For one frozen source Representation and scope, a broad Lector candidate should recover the set of **material civic assertions that the source itself explicitly asserts or explicitly contains**, in Claims that remain faithful, self-sufficient enough to stand alone, minimally decomposed without destroying necessary context, and bound to exact reopenable source evidence.

The benchmark does **not** ask whether the assertion is true in the world. Verification, contradiction, derived calculation and external correction remain outside Lector.

## Material civic assertion

A `material civic assertion` is an explicitly source-supported proposition whose preservation can matter for later reconstruction, search, review, verification or public understanding of civic or institutional activity **without depending on current editorial interest**.

Include an assertion when the source explicitly states at least one of these kinds of consequential content:

- a decision, agreement, vote, authorization, refusal, approval, rejection or procedural outcome;
- an actor's stated action, request, commitment, position, finding, recommendation or allegation;
- an obligation, prohibition, permission, condition, exception, eligibility rule or scope rule;
- a public plan, project, procurement, contract term, disposition, deadline, milestone or status;
- an amount, quantity, rate, percentage, date, duration, count, location or other measurement tied to a civic assertion;
- a finding, observation, cause, consequence, risk, deficiency or control statement in an institutional report;
- an explicitly stated fact about public services, resources, infrastructure, territory, population, organizations, offices or institutional operations;
- an occurrence/status statement needed to understand what happened, who did it, under what authority, when, where or with what limitation;
- attributed speech or correspondence whose speaker/sender and attribution are themselves necessary to preserve what the source says.

The definition is intentionally **broad and topic-neutral**. An obscure assertion remains material if it satisfies the definition. Political salience, newsworthiness, likely virality, partisan usefulness or an annotator's personal importance ranking are not inclusion criteria.

### Exclude

Do not create material reference facts for:

- purely ceremonial, greeting, attendance-formula or closing boilerplate that conveys no additional civic proposition;
- document navigation, page furniture, signatures-as-layout, table-of-contents text or repeated headings that carry no semantic assertion beyond structure;
- exact duplicate restatements that add no qualifier, attribution, scope or status change;
- transcription/OCR artifacts not supported by the source;
- a conclusion that requires arithmetic, joining multiple source values, external knowledge or other derivation rather than being explicitly asserted;
- a world-knowledge correction of what the source says;
- an unresolved fragment whose proposition cannot be made faithful without guessing.

When a unit is genuinely unclear whether it contains a material civic assertion, annotate `needs_adjudication`; do not force inclusion or exclusion.

## Claim granularity rule: self-sufficient minimality

The target is **not** the shortest possible sentence and not one relation per Claim.

A good Claim contains the smallest proposition that can be separated **without losing information required to interpret it faithfully**.

Keep with the proposition any qualifier needed to avoid changing its meaning, including:

- source attribution or speaker;
- condition or exception;
- negation;
- normative modality (`must`, `may`, `should`, `prohibited`, etc.);
- temporal scope or deadline;
- quantitative unit/base/period;
- jurisdiction or object scope;
- antecedent/context needed to resolve a reference.

Split conjunctions when each resulting proposition remains faithful and independently interpretable. Do not split when doing so would detach a qualifier shared by the propositions or create false precision.

## Frozen hard capability IDs

### `COV-01` — Material civic coverage

**Question:** Did the candidate recover the frozen set of material civic assertions?

A reference fact is covered only by a full semantic match that preserves every mandatory qualifier. A partial match does not count as covered.

Coverage is fact-level, not sentence-level and not claim-count-based.

### `FOC-01` — Material civic focus

**Question:** Does the candidate avoid emitting semantic noise as if it were a material civic Claim?

Emissions count against focus when they are:

- supported but explicitly non-material under the frozen definition;
- boilerplate/navigation/transcription artifacts;
- redundant Claims that add no semantic distinction after reconciliation.

Unsupported or overstated emissions are classified under `ENT-01` and also fail focus; they are not treated as harmless extra recall.

### `ENT-01` — Source entailment / faithfulness

**Question:** Does the exact bounded source evidence justify the candidate proposition as written?

A Claim fails when it:

- overgeneralizes;
- changes actor or attribution;
- upgrades possibility/proposal into fact/decision;
- drops a condition or exception that changes meaning;
- imports external/world knowledge;
- combines source fragments into a proposition the source itself does not assert;
- states a derived/computed result as source assertion.

Exact quotation is not sufficient for PASS.

### `MIN-01` — Self-sufficient minimality

**Question:** Is the Claim independently understandable without being needlessly compound?

PASS requires both:

- enough context to preserve meaning; and
- no separable second material proposition whose split would preserve all required context.

Over-atomization and under-decomposition are both errors.

### `ATR-01` — Attribution preservation

**Question:** Is the assertion attributed to the correct source actor/voice?

Direct speech, correspondence, reported allegations, staff findings, committee recommendations and institutional decisions must not be collapsed into one institution-level voice unless the source actually does so.

### `SCP-01` — Conditions, exceptions and scope

**Question:** Are conditions, exceptions, eligibility limits, jurisdiction/object scope and cross-reference-dependent limitations preserved when they change the proposition?

A candidate that states the main clause while dropping a meaning-changing limitation fails.

### `MOD-01` — Negation and modality

**Question:** Are negation and epistemic/normative modality preserved?

Examples of materially distinct forms:

```text
did / did not
must / may / should
approved / proposed / considered
confirmed / alleged / estimated
```

A polarity or modality upgrade/downgrade is a hard semantic error.

### `TMP-01` — Temporal preservation

**Question:** Are dates, deadlines, periods, sequence and temporal scope preserved when material?

Do not silently turn a historical/past statement into a current one, or a proposed future deadline into a completed fact.

### `QTY-01` — Quantitative exactness

**Question:** Are material numbers preserved with the correct unit, base, period and referent?

A number without its meaning-changing denominator, currency, unit, period or object is not exact. Arithmetic not explicitly asserted belongs to Derivation.

### `AMB-01` — Ambiguity preservation / abstention

**Question:** Does the candidate avoid guessing when the source does not resolve a material ambiguity?

Allowed outcomes include:

- preserve the ambiguity explicitly;
- keep a bounded unresolved reference diagnostic;
- decline to emit the proposition.

Inventing a referent or choosing one unsupported interpretation fails.

### `CTX-01` — Cross-unit context recovery

**Question:** Can the candidate recover propositions whose faithful interpretation requires bounded context outside the local extraction unit?

Exercise at least:

- heading/section inheritance;
- prior-sentence/prior-paragraph antecedent;
- cross-page continuation;
- explicit internal cross-reference.

This capability does not require unlimited document context. It measures whether the lane's chosen context strategy is sufficient.

### `REC-01` — Semantic duplicate/conflict reconciliation

**Question:** Does the lane reconcile overlapping or repeated semantic candidates without deleting real distinctions?

PASS behavior:

- equivalent repeated assertions collapse to one semantic result;
- materially different qualifiers remain distinct;
- conflicting source assertions remain represented as source assertions rather than silently choosing a winner;
- reconciliation uses semantic equivalence, not claim-text equality.

### `FID-01` — Source-fidelity counterfactual

**Question:** Will the candidate preserve an explicit source assertion even when common world knowledge or model priors suggest it is wrong, outdated or unusual?

The candidate must report what the source says. External correction belongs to later Verification or Assessment.

A silent "helpful correction" is a hard failure.

### `EVD-01` — Evidence support and reopening

**Question:** Does every emitted Claim bind to exact evidence that both reopens deterministically and actually supports the proposition?

This has two layers:

1. deterministic selector/reopening validity;
2. semantic support of the proposition by the reopened evidence.

A reopenable but semantically insufficient quote fails layer 2.

## Cross-cutting Spanish institutional gate

`LANG-ES-01` is a reporting/selection gate rather than a separate linguistic score.

A production selection cannot PASS on English or synthetic cases while failing the required Spanish institutional fixtures. Per-capability results must be reported for the Spanish development corpus and later natural holdouts.

No global average may hide a Spanish failure.

## Candidate-to-reference adjudication labels

Every emitted candidate receives exactly one primary disposition:

```text
FULL_MATCH
PARTIAL_MATCH
SUPPORTED_NON_MATERIAL
DUPLICATE_EQUIVALENT
UNSUPPORTED_OR_OVERSTATED
AMBIGUOUS_UNRESOLVED
REFERENCE_DEFECT
```

Rules:

- `FULL_MATCH` requires all mandatory qualifiers.
- `PARTIAL_MATCH` does not count as reference coverage.
- `DUPLICATE_EQUIVALENT` is not an independent fact and is evaluated under `REC-01`/`FOC-01`.
- `REFERENCE_DEFECT` is used only when candidate inspection reveals that the frozen reference itself is incomplete or malformed. That fixture's formal score is invalid until the reference protocol is repaired and re-frozen; do not silently award the candidate a new truth after seeing its output.

## What a benchmark PASS means

A lane PASS means only:

> On the frozen Canario fixtures, scopes, reference, capabilities and thresholds, this lane met every required semantic gate under the recorded model/provider/config and operational bounds.

It does **not** mean:

- universal support for all civic documents or modalities;
- factual truth in the world;
- production-readiness of a provider;
- GUI/operator readiness;
- Phase-6/WP7 completion;
- authorization to implement the lane as production Lector.

## What remains deliberately unfrozen here

This semantics freeze does **not** yet freeze:

- exact D3/D4/H2 source bytes/Representations;
- numeric pass thresholds;
- model/provider/config;
- A0–A5 prompts;
- segmentation/unit mechanics;
- repetition counts;
- operational budgets.

Those are later gates inside the active Work and must freeze in the required order before tested candidate output.
