---
id: CANARIO-LECTOR-PRODUCTION-FIT-BENCH-DESIGN-CANDIDATE-001
type: benchmark-design-candidate
state: research-candidate
authority: none
created: 2026-08-27
baseline: ce07da9466a638738c845f7fba152a47e9987a59
---

# LECTOR production fit bench — design candidate

This file is research output, not an active Work and not implementation authority.

## Proposition

Canario needs empirical evidence about **orchestration**, not another model leaderboard.

Hold model/provider/source/reference constant and compare extraction plans.

## Lanes

| Lane | Plan | Why it exists |
|---|---|---|
| A0 | whole-document one-shot | simplest baseline; tests whether complexity is needed at all |
| A1 | deterministic structure-aware units, one pass | isolates locality benefit |
| A2 | same units, repeated independent passes | tests stochastic recall improvement |
| A3 | unit + bounded context -> selection -> ambiguity -> decomposition | Claimify-style staged challenger |
| A4 | A3-like extraction + source-unit coverage audit + targeted repair + document reconciliation | leading fixed Canario hypothesis |
| A5 | dynamic decomposition/plan optimization | expensive challenger only if simpler lanes leave material gaps |

The lane count may be reduced **before** extractor exposure only if research establishes strict
dominance or infeasibility; record the reason.

## Common constraints

- same exact Representation bytes/scopes;
- same model/provider/version/reasoning level where transport permits;
- source-only instructions; no web/tools/world-knowledge correction;
- same maximum source authority;
- same canonical narrow draft contract;
- zero human review written to production rows during benchmark;
- candidates cannot inspect reference labels;
- reference cannot inspect candidate output;
- fixed egress/resource bounds per lane;
- all exact evidence must reopen through production selector semantics.

## Narrow model-facing draft

First bench claim lane should request only what is needed to evaluate Claim quality:

```text
local candidate key
proposition text
exact evidence target proposal(s)
optional source attribution text
optional temporal scope
semantic diagnostics needed by the lane (e.g. unresolved ambiguity)
```

Do not require the same generation to create canonical Entities, resolve identities, classify the
document, emit rich relations, assess truth, or perform derived computation.

Run relation/mention enrichment as separate challengers only after claim quality is measured.

## Reference fact object candidate

A reference fact is not a required sentence. It records:

```text
fact_id
required semantic content
mandatory qualifiers
allowed semantic variants / adjudication notes
exact evidence target set(s)
capability bindings
material_civic = true
```

Each selected source unit can also be marked:

```text
no_material_civic_fact
needs_adjudication
```

A candidate Claim matches a fact only after human-approved semantic adjudication or a later
independently validated matcher. Exact string equality is insufficient.

## Threshold freeze order

```text
source/scope freeze
-> reference construction + evidence reopening
-> reference freeze
-> inspect fact counts/distribution
-> freeze per-capability thresholds
-> run tested lanes
```

Never tune thresholds after seeing candidate scores.

## Mandatory counterexamples

Include controlled or natural cases for:

- source typo/conflict with common world knowledge;
- negation;
- exception/condition;
- attributed speech versus institution-level assertion;
- ambiguous pronoun/reference;
- statement whose context is in preceding section/header;
- cross-page continuation;
- multiple quantities with different units/periods;
- repeated near-duplicate proposition;
- same proposition expressed in two distant sections;
- ceremonial/non-material prose adjacent to material decision;
- source cross-reference whose target changes interpretation.

## Reporting

For every lane report:

- per-fixture and per-capability recall/coverage;
- focus/precision;
- unsupported/overstated Claims;
- qualifier errors;
- ambiguity guesses;
- duplicate/conflict outcomes;
- evidence reopening/support errors;
- call/egress/latency/failure metrics;
- repeated-run variance.

No green global average if any required capability is below its frozen threshold.

## Selection rule

Choose the **simplest lane that clears all hard semantic gates**.

If A0 passes, select A0.
If A1 passes and A0 fails, select A1.
Escalate complexity only for demonstrated quality gain required by frozen gates.

A5 is not a prestige winner: if A4 passes, dynamic agentic optimization remains out of production.

## Development versus holdout evidence

Development fixtures may shape prompts/orchestration/reference machinery. Final natural holdouts may
not.

- Acta 161: development/reference-design fixture.
- Acta 160: reserved first natural holdout.
- Add at least one non-minutes Spanish civic holdout before production selection.

A failed holdout retires that holdout from future independent certification. Add the exposed failure
mode to the benchmark, revise the candidate, and select a new untouched holdout.

This prevents a benchmark from becoming a training loop disguised as certification.
