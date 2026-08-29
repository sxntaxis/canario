---
id: CANARIO-LECTOR-FIT-BENCH-D1-SUPERVISING-AUTHOR-ADVERSARIAL-REVIEW-001
kind: benchmark-reference-semantic-review
state: complete-non-independent
authority: active-work-evidence
work: LECTOR-PRODUCTION-FIT-BENCH
fixture: CR-ESPARZA-MINUTES-001
---

# D1 supervising-author adversarial review v1

This record challenges the reproducibly preserved D1 context-limit WIP against the complete exact frozen D1
scope in both directions:

```text
source -> reference completeness
reference -> source faithfulness / self-sufficient minimality
```

It also includes explicit evidence-context, attribution-antecedent, frozen-unit, capability-binding and duplicate
semantic passes.

## Recovery premise

The emergency checkpoint was not a reference candidate. It preserved:

```text
328 runnable A(...) specs
 78 separate fragment A(...) records
no valid prior final fact count
no final D1 reference artifact
```

The two record counts are intentionally **not summed into a semantic baseline**. The fragment could overlap or
revise the runnable builder, and the later narrative ~380 state was not fully materialized. Review therefore
starts from exact source authority, not from a fictional previous fact count.

## Result

```text
final D1 v1 facts             660
final evidence targets       1240
findings                       38
unresolved semantic items       0
primary adjudications           0
verdict  CONTEXT_LIMIT_WIP_REQUIRES_RECONSTRUCTION_FINAL_D1_V1_AUTHORED
```

Findings by review pass:

```text
PASS_1_RECOVERY   19
PASS_2_OMISSION    5
PASS_3_REVERSE    14
PASS_4_INVARIANTS  PASS
```

Findings by action:

```text
ADD_MISSING_TAIL              11
EVIDENCE_CONTEXT_REPAIR       11
SOURCE_EXHAUSTIVE_REWRITE      7
ADD_OMISSION                    4
REWRITE                         3
SPLIT_AND_REWRITE               1
SPLIT                           1
```

The 19 recovery findings are not claimed to be the same 19 findings mentioned narratively before the context
cut. They are a new, reproducible classification of what the checkpoint plus exact frozen source actually
required after recovery.

## Main defects removed

- WIP carrier-local selector/evidence drift in C04/C05/C06/C07/C10/C12/U03/M01;
- missing reproducible semantic authorship for M02–M07 and V01–V05;
- under-decomposition of distinct requests, positions and dispositions;
- omitted purpose/status/origin assertions found during the dedicated omission-only pass;
- local sentences whose actor, route, legislative expediente, date or source pronouncement identity depended on
  a prior antecedent not included in evidence;
- generic commission-waiver notes that failed to identify the proposal being waived from commission;
- two M03 facts that had converged to the same combined notification+transfer wording despite representing
  distinct actions;
- one unnecessary calendar inference that upgraded `miércoles 20` to a month not stated in the local source
  assertion.

Every finding in the JSON companion records the source excerpt, exact final replacement fact IDs and final
replacement notes. Replacement-note synchronization is mechanically checkable.

## Independence boundary

This review is **not** the materially independent semantic audit required by `REFERENCE_PROTOCOL_FREEZE_V2.md`.
The same supervising/cloud author performed recovery, semantic authorship and this challenge.

Its purpose is to remove defects discoverable by the semantic author before paying the independent-review cost.
A later independent **big-model** review remains required before D1 can freeze.

The local execution agent has no semantic-authoring role.
