---
id: CANARIO-D1-INDEPENDENT-SEMANTIC-REVIEW-001
kind: benchmark-reference-semantic-review
state: complete-with-reference-disputes
authority: independent-review-evidence
work: LECTOR-PRODUCTION-FIT-BENCH
fixture: CR-ESPARZA-MINUTES-001
---

# D1 independent semantic review v1

## Verdict

```text
REFERENCE_DISPUTE
```

The full frozen D1 source and all 660 proposed facts were audited in both directions. The candidate remains `SUPERVISOR_DRAFT`; this review does not modify or freeze it.

## Independence

```text
provider: OpenAI
model: GPT-5.6 Sol
model/version: GPT-5.6 Sol
independence_strength: WEAK_OR_UNKNOWN
strong_independent_gate_satisfied: false
```

The supervising author was also OpenAI GPT-5.6 Sol. This audit is useful semantic evidence, but it does **not** satisfy the required materially independent gate.

## Leakage declaration

```text
formal_A0_A5_output_seen = false
formal_candidate_scores_seen = false
Acta_160_semantics_inspected = false
H2_selected_or_inspected = false
```

## Coverage

```text
structures:       36 / 36
frozen units:     61 / 61
proposed facts:  660 / 660
evidence targets: 1240 / 1240
```

`U0007` was independently reopened and confirmed as a page marker only, so its `NO_MATERIAL_CIVIC_FACT` classification is not disputed.

## Findings

Total hard disputes: **61**

```text
SOURCE_TO_REFERENCE: 38
REFERENCE_TO_SOURCE: 23

MISSING_MATERIAL_ASSERTION: 38
EVIDENCE_INSUFFICIENT:      21
QUALIFIER_ERROR:            1
CONTEXT_ERROR:              1
```

### Principal dispute families

- **33 explicit vote/finality outcomes are omitted.** The source repeatedly records `APROBADO/A DEFINITIVAMENTE ... POR UNANIMIDAD` (including five quoted prior/committee decisions), while the reference generally preserves only the operative decision. The frozen target explicitly treats votes, approvals and procedural outcomes as material civic assertions.
- **Two act-approval procedural outcomes are omitted.** For Acts 158 and 159, the source explicitly says that no observations were presented before the unanimous vote.
- **Additional source omissions remain** in C13 (repeated reminder agreements), U04 (proposal/acceptance context around the Presidency copy and recent MOPT minister designation), U06 (ministerial efforts already underway for Puntarenas), and M01 (a recess decreed for up to five minutes).
- **Named-speaker attribution evidence is systematically insufficient in 13 structures.** 116 affected facts resolve role-only evidence such as `Señor Alcalde` or `Señor Presidente Municipal` to named people without binding the roster/local identification needed to support that attribution.
- **Formal-decision subfact evidence is incomplete** in C05, C06, M01 and M03: decomposed operative fragments attribute actions to the Concejo while omitting the local `SE ACUERDA` context that establishes formal actor/status.
- **V05 contains unresolved antecedent/evidence defects.** The Mata de Limón bridge/project context is not consistently carried into the exact evidence or self-sufficient semantic notes.

The canonical JSON companion contains every dispute as a machine-readable `D1-IR-*` finding with exact source evidence, affected facts and advisory resolution only.

## Comparison with supervising-author self-review

The independent findings were persisted before the 38-finding supervising review was opened. The later provenance comparison did not disprove any independent dispute from exact source evidence. Several categories overlap earlier repair work, but the surviving candidate still exhibits the defects recorded here.

## Custody

```text
reviewed commit: 6aac2af5802996b8c17c612107f6771e0e612318
reviewed tree:   130b4a8a50e96ead79fbc8217f5f605fd3c8264b
reference JSON SHA256: 56a485ef4dfc5923ad059c47337f14db608ddd82a6a1f7aef4642b6ec0af625f
reference MD SHA256:   a75535a4993cdc6ee44482e63624e634ae236a32765c4b075a79b28020af1fc0
```

No D1 reference fact, evidence selector, qualifier, capability binding, benchmark rule, tested-extractor output, production code or test was modified by this review.
