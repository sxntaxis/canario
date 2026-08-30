---
id: CANARIO-D1-QUINARY-SEMANTIC-REVIEW-V5-001
kind: benchmark-reference-quinary-semantic-review
state: complete-with-reference-disputes
authority: quinary-review-evidence
work: LECTOR-PRODUCTION-FIT-BENCH
fixture: CR-ESPARZA-MINUTES-001
---

# D1 v5 quinary semantic review

## Verdict

```text
REFERENCE_DISPUTE
```

D1 v5 remains `SUPERVISOR_DRAFT`. This review does not freeze or relabel it.

## Reviewer / independence

```text
provider: OpenAI
model/version: GPT-5.6 Sol
independence_strength: WEAK_OR_UNKNOWN
strong_independent_gate_satisfied: false
human_independence_gate_satisfied: false
```

## Anti-anchoring / leakage

The blind pass was completed and persisted before any prior semantic-review artifact was opened: **30** provisional hard disputes, SHA256 `cc3d06a1dc5a8a52eea09bf0c0beb4f72723e82205e85b127e41ae9d23ffba11`. `anchoring_contamination = false`. No formal A0–A5 output/scores, Acta 160 semantics, H2 semantics, or tested extraction behavior were inspected.

## Coverage

```text
structures source→reference:          36 / 36
frozen units source→reference:        61 / 61
unit-state classifications:           61 / 61
facts reference→source:              744 / 744
evidence targets considered as sets: 1727 / 1727
```

All required global scans were completed: list/table, formal-decision/finality, temporal, quantitative, identity-resolution, deictic/antecedent, semantic-duplicate, and capability-binding. Mechanical reopening also passed for all 1,727 targets, but was not treated as semantic sufficiency.

The independent unit-state pass matches v5: **57 `MATERIAL_FACTS`**, **4 `NO_MATERIAL_CIVIC_FACT`** (`U0003`, `U0004`, `U0005`, `U0007`), with **0** unit-state disputes.

## Findings

Hard dispute groups: **30**.

```text
SOURCE_TO_REFERENCE: 13
REFERENCE_TO_SOURCE: 17
UNIT_STATE: 0

MISSING_MATERIAL_ASSERTION: 13
EVIDENCE_INSUFFICIENT: 15
CAPABILITY_BINDING_ERROR: 2
```

The source→reference disputes are omitted material positions, recommendations, uncertainty/reasons, and institutional assertions. The reference→source disputes are dominated by canonical actor/identity resolutions whose complete bound evidence sets do not contain the source-internal resolver, plus isolated attribution/context and capability-binding failures. The canonical JSON contains all 30 source-grounded finding records and recommended advisory resolutions; D1 v5 itself was not modified.

## v4 bounded spot-check regression

```text
RESOLVED_IN_V5: 13
STILL_PRESENT: 0
PARTIALLY_RESOLVED: 0
REGRESSED_DIFFERENTLY: 0
```

All 13 accepted v4 spot-check disputes survive regression inspection as repaired in v5. None of the 30 blind v5 disputes is counted as a continuation of those 13 repairs.

## Quaternary comparison

The prior D1 v4 quaternary review reported `QUATERNARY_AUDIT_PASS_NO_DISPUTES`. This quinary blind pass **finds defects despite the earlier clean v4 audit**. That comparison is diagnostic evidence about review reliability and does not soften the present findings.

## Custody

```text
reviewed commit: e1ebb27f646ca54546bf2b5aff75f09b28b29ffb
reviewed parent: 03fed18a609eaed516dfacf361a520a9ad6371bd
reviewed tree:   aa4a8d78f3c8a66b03cd272071d76dd2e9ccb7a2
reference JSON:  3c74b8142933531e6e6aa4a9c1ab016e7cace0e6ca39d32500f08cb3d63f81ec
reference MD:    7b2e26d3bb2de71018954030819dc84a901aa4fea770484ed9aca8823540e0b4
```

A `REFERENCE_DISPUTE` result here does not establish material provider/model-family independence and does not freeze D1.
