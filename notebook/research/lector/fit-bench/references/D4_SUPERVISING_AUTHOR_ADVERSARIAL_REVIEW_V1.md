---
id: CANARIO-LECTOR-FIT-BENCH-D4-SUPERVISING-AUTHOR-ADVERSARIAL-REVIEW-001
kind: benchmark-reference-semantic-review
state: complete-non-independent
authority: active-work-evidence
work: LECTOR-PRODUCTION-FIT-BENCH
fixture: CR-CGR-SANTA-ANA-PROCUREMENT-AUDIT-001
---

# D4 supervising-author adversarial review v1

This record challenges the mechanically certified D4 v1 reference against the complete exact frozen
D4 scope in both directions:

```text
source -> reference completeness
reference -> source faithfulness / self-sufficient minimality
```

It also includes explicit structure-ledger, capability-binding, evidence-context and primary-source
adjudication passes.

## Result

```text
v1 facts                    185
final v2 facts              289
net increase                104
findings                    98
unresolved semantic items   0
primary adjudications       2
verdict                     V1_REQUIRES_REVISION_FINAL_V2_AUTHORED
```

Findings by action:

```text
SPLIT                              51
REWRITE                            17
SPLIT_AND_REWRITE                  6
ADD_OMISSION                       12
EVIDENCE_CONTEXT_REPAIR            5
other explicit repairs              7
```

Review passes:

```text
PASS_1_2                                  68
PASS_3_FINAL_SOURCE_ORDER_AND_REVERSE     26
PASS_4_FINAL_OMISSION_AND_PRIMARY_VISUAL  4
```

Representative defects removed from v1/provisional-v2 included:

- the `104` extraction artifact caused by visible `10` + superscript footnote `4`;
- under-decomposed duties, findings, controls, procedural stages and disposition proof milestones;
- missing actor, condition, scope, temporal, denominator and cross-reference qualifiers;
- evidence spans that lacked the context needed to interpret table rows or dispositions;
- source statements whose modality had been weakened (`debe`/`es causal de sanción`);
- omitted audit-scope, planning, public-purpose and control/risk assertions;
- source wording that had been normalized instead of preserving genuine ambiguity;
- stale `AMB-01` on the FN4 facts after the exact primary PDF resolved the referent;
- an internal report conflict where the executive summary says `acto motivado` while Cuadro n.° 2
  prints `activo motivado` for the same 9-case finding.

The machine-readable companion records every finding, source excerpt, disposition, replacement IDs and
replacement notes. Final replacement-note synchronization is mechanically checkable.

## Primary-source boundary

The FN4 adjudication is grounded in exact frozen-PDF evidence returned by local mechanical inspection;
semantic repair was performed only by the supervising/cloud author.

For the `activo motivado` table wording, the supervising author visually inspected the official CGR
PDF and preserved the conflict rather than harmonizing it. Exact byte-identical confirmation in the
frozen source-pack PDF remains part of the next local mechanical certification.

## Independence boundary

This review is **not** the materially independent semantic audit required by
`REFERENCE_PROTOCOL_FREEZE_V2.md`: the same supervising/cloud author performed the reference writing
and this challenge.

Its purpose is to remove defects discoverable by the author before paying the independence cost. A
later independent **big-model** review remains required before D4 can freeze.

The local execution agent has no semantic-authoring role.
