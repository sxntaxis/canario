---
id: CANARIO-BOOK-FEVEROUS-001
type: research-source-book
state: research-complete-for-synthesis
authority: evidence
created: 2026-08-25
updated: 2026-08-25
researched_through: 2026-08-25
canario_baseline: a1d212c84830b3a0558dd4d1d9354cf10ac7a362
source_ledger: sources.csv
claim_ledger: claims.csv
---

# FEVEROUS

## Question

What should Canario reuse from mature mixed text/table evidence-set scoring?

## Evidence horizon

This Book uses the primary paper and, where relevant, the current public
implementation/license metadata available through 2026-08-25. It is a bounded
architecture/reuse audit, not a reproduction of all experiments.

## Claim ledger synopsis

- **FEV-C001:** Claims may require structured evidence, unstructured evidence, or mixtures of both. **Canario:** Multi-evidence and cross-modality support is established benchmark practice, not an exceptional case.
- **FEV-C002:** FEVEROUS scoring combines verdict accuracy with evidence retrieval quality rather than rewarding labels alone. **Canario:** Separate evidence sufficiency/retrieval from semantic verdict correctness.
- **FEV-C003:** NotEnoughInfo examples still require partial evidence in the shared task. **Canario:** Abstention should remain evidence-grounded rather than a free fallback label.
- **FEV-C004:** The project releases scorer/annotation code under Apache-2.0. **Canario:** Inspect and potentially adapt evidence-set/scoring mechanics before inventing a new private scorer.

## Bounded transfer

**ADAPT evidence-set and scoring concepts; consider reusing small, separable scorer mechanics after a code-level audit. Use as a mixed-modality external benchmark reference.**

## Do not import

Do not inherit Wikipedia-specific retrieval IDs or assume FEVEROUS evidence semantics map directly onto Canario Representation locators.

## Residual risk / unresolved question

Which FEVEROUS scorer concepts can transfer without dragging dataset-specific assumptions into Canario?

## Closure verdict

Research-complete for this synthesis gate. This Book is evidence, not
implementation authorization.
