---
id: CANARIO-D1-QUATERNARY-SEMANTIC-REVIEW-V4-001
kind: benchmark-reference-quaternary-semantic-review
state: complete-clean-pass
authority: quaternary-review-evidence
work: LECTOR-PRODUCTION-FIT-BENCH
fixture: CR-ESPARZA-MINUTES-001
---

# D1 v4 quaternary semantic review

## Verdict

```text
QUATERNARY_AUDIT_PASS_NO_DISPUTES
```

D1 v4 remains `SUPERVISOR_DRAFT`. This review does not freeze or relabel it.

## Reviewer / independence

```text
provider: OpenAI
model/version: GPT-5.6 Sol
independence_strength: WEAK_OR_UNKNOWN
strong_independent_gate_satisfied: false
```

## Anti-anchoring / leakage

The complete blind pass was persisted before opening the four v3 review/adjudication artifacts: **0** provisional findings, SHA256 `eb8d5b9b236fab3ec6bbcd08f8afc8e1b53fe7486741cde7a032dfb798a3b10c`. `anchoring_contamination = false`. No prohibited A0–A5 output/scores, Acta 160 semantics, H2 semantics, or tested extraction behavior were inspected.

## Coverage

```text
structures source→reference: 36 / 36
frozen units source→reference: 61 / 61
facts reference→source: 735 / 735
evidence targets considered as sets: 1694 / 1694
list/table scan: complete
temporal global pass: complete (156 TMP-01 facts)
quantitative global pass: complete (50 QTY-01 facts)
```

`U0007` was independently verified as the isolated page marker `1`. No new hard semantic disputes survived the blind pass.

## School-row verification

M01 contains **35** row-level school/center facts: 25 source rows in the received-project list and 10 source rows in the not-submitted list. Every row is represented exactly once with the correct list status; no source row is omitted or moved; no duplicate semantic row exists; the derived `25`/`10` totals are not asserted as source quantities; and retained 2026 normalization is supported by bound dated source context.

## v3 regression audit

```text
RESOLVED_IN_V4: 14
STILL_PRESENT: 0
PARTIALLY_RESOLVED: 0
REGRESSED_DIFFERENTLY: 0
```

All fourteen v3 hard disputes survive reinspection as repaired in v4. The canonical JSON contains the complete 14-row regression matrix.

## Custody

```text
reviewed commit: 44291aa54f96492d02cc4e9c9f8e4d0bb9ddd770
reviewed tree:   c3cb37b96ac356b952e9454525788dc47e0a0e09
reference JSON:  c56e499e80a954747bad54a79472fecddc9b451edf80fa18613fd090f4fe1ec2
reference MD:    bacae28a8d56665ca5ac188df8608000b7c59531dc58441bf40b8687e43b6929
```

A clean result here does not establish material provider/model-family independence.
