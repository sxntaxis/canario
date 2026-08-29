---
id: CANARIO-D1-INDEPENDENT-REVIEW-ADJUDICATION-001
kind: benchmark-reference-review-adjudication
state: complete
work: LECTOR-PRODUCTION-FIT-BENCH
fixture: CR-ESPARZA-MINUTES-001
---

# D1 independent-review adjudication v1

## Result

The separate-session D1 v1 review returned `REFERENCE_DISPUTE` with 61 hard findings. The supervising author
reopened each dispute against the exact frozen D1 Representation and the frozen benchmark semantics/protocol.

```text
findings reviewed       61
accepted                61
rejected                 0
unresolved               0
v1 disposition           REQUIRES_REVISION
resulting reference      D1_REFERENCE_SUPERVISOR_DRAFT_V2
```

The review's `WEAK_OR_UNKNOWN` independence classification remains unchanged and truthful. Adjudication does
not upgrade it to material independence.

## Adjudication principles

- Vote/finality text was accepted as material because `BENCHMARK_SEMANTICS_FREEZE_V1` explicitly includes
  decisions, votes, approvals and procedural outcomes.
- Named attribution was repaired where the semantic note resolved a role to a person without binding the exact
  source identification needed for that resolution.
- Decomposed formal-decision fragments now bind `SE ACUERDA` evidence when that context is necessary to support
  Concejo actor/status.
- Required antecedents were added rather than left to parametric inference.
- The reviewer finding concerning Mariela Cruz Pérez had a valid evidence-sufficiency defect even though its
  generic roster example was not the correct identity source; v2 binds the exact local text identifying her as
  signer/analyst of GOT-ZLMT-130-2026.
- No dispute was resolved from external knowledge, A0–A5 output, candidate scores, Acta 160 or H2.

The canonical machine-readable file `D1_INDEPENDENT_REVIEW_ADJUDICATION_V1.json` records all 61 decisions and
the corresponding v2 fact IDs.

## Consequence

D1 v1 is retired as live semantic authority and remains available in Git history. D1 v2 is still a
`SUPERVISOR_DRAFT`. It requires new mechanical certification and then a new semantic audit before any reference
freeze can be considered.
