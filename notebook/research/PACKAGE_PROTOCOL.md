---
id: ACTAKIT-RESEARCH-PACKAGE-PROTOCOL-001
type: research
state: accepted
authority: working
created: 2026-08-20
updated: 2026-08-20
---

# Research package protocol

> **Use the smallest evidence structure that preserves trust, but do not collapse breadth/depth into a link list.**

## 1. Source Book

A Source Book owns one coherent research object: one standard, product/project, institution, protocol family, or historical lineage. Multiple URLs from the same object belong in the same Book when they answer the same bounded research question.

Minimum package:

```text
book.md
sources.csv
claims.csv
```

Optional ledgers when directly observed or materially useful:

```text
observations.csv
scenarios.csv
collisions.csv
```

The Book must define:

- subject and boundary;
- research horizon/date;
- what the source actually establishes;
- evidence limits or bias;
- what ActaKit may transfer;
- what ActaKit must not import;
- unresolved questions.

## 2. Claims before prose

Long prose is optional. Stable evidence is not.

Every material conclusion should exist in `claims.csv` with:

```text
claim_id
evidence_refs
statement
evidence_kind
actakit_implication
```

A Book may summarize the ledger, but prose must not become the only place where important evidence survives.

## 3. Source quality and breadth

Prefer primary standards/project documentation for mechanism claims. Add operational scars, audits, issue histories, or independent evidence when the question is about failure modes or long-term operation.

There is no source-count quota. A study closes when:

1. each material claim resolves to evidence;
2. the research question has coverage across both intended mechanism and known failure modes where available;
3. contradictory or limiting evidence has been sought;
4. remaining gaps no longer threaten the pending decision.

A homepage or one search result does not by itself count as studying a system.

## 4. Synthesis comes after source Books

Cross-source work belongs in a synthesis package containing, as needed:

```text
claims.csv
scenario-matrix.csv
collisions.csv
transfers.csv
gap-audit.md
BOOK.md
```

The synthesis distinguishes:

- **adopt** — mechanism fits ActaKit directly;
- **adapt** — mechanism transfers with a stated simplification;
- **defer** — useful only after a concrete requirement appears;
- **reject** — conflicts with ActaKit's scope or simplicity.

Every transfer states a stop condition. External research is not feature harvesting.

## 5. Research does not become authority automatically

A research package is evidence, not implementation authorization.

Promotion path:

```text
Source Books -> synthesis -> fixtures/counterexamples -> explicit design decision -> docs/contracts -> implementation
```

Do not change architecture merely because a standard is prestigious or a mature system uses a mechanism.

## 6. Current-version rule

Keep stable source/claim identity and factual evidence horizons. Rewrite synthesis when later evidence changes the current conclusion. Git preserves old package versions; the live Notebook should express the best current research rather than competing historical conclusions.
