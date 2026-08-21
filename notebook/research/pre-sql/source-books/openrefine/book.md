---
id: ACTAKIT-BOOK-OPENREFINE-DEEP-001
type: research-source-book
state: deep-audited
authority: evidence
created: 2026-08-20
updated: 2026-08-20
researched_through: 2026-08-20
actakit_baseline: 59bab9de30bbf2aa1eec96dddaee3cded31a9f3a
source_ledger: sources.csv
claim_ledger: claims.csv
---

# OpenRefine

## Question

How should ambiguous reconciliation and batch human review work?

## Deep-audit basis

Long-lived operator workflow preserves raw cells and stores reconciliation/candidates separately.

## Evidence horizon

- **AKS-S022 — OpenRefine Reconciliation:** Raw label -> ranked candidates -> matched/new/unresolved; batch review and additional fields for disambiguation
- **AKS-S044 — OpenRefine Reconciliation API:** Ranked entity candidates from label plus optional type/properties; identifier spaces remain service-defined

## Claim ledger synopsis

- **AKS-C022:** Ambiguous reconciliation works well as ranked candidates plus explicit matched/new/unresolved judgments and batch approval. **ActaKit:** Entity resolution UI/workflow should be semi-automatic, not name-equality magic.
- **AKS-C063:** Reconciliation preserves the original value alongside candidate/match state and supports explicit matched/new/unresolved judgments plus mass actions over filtered subsets. **ActaKit:** EntityMention resolution should preserve raw text, candidate/decision state, and per-record outcome even when an operator acts in bulk.
- **AKS-C113:** Reconciliation preserves raw values while storing candidates and judgments separately, and supports bulk decisions over filtered records. **ActaKit:** EntityMention must persist independently of Entity resolution; batch UX need not create a heavyweight batch domain object.

## Bounded transfer

Raw mention + candidate set + decision; bulk UX writes per-record outcomes.

## Do not copy

Do not use full universal undo/event history as canonical ActaKit history.

## Schema pressure / expensive mistake avoided

Entity resolution state is separate from EntityMention; batch need not be a domain object.

## Residual risk

Candidate-scoring UX/model can remain implementation-level until operator interface work.

## Closure verdict

Deep-audited for the pre-SQL decision horizon. This Book contributes evidence and constraints; it does not independently authorize schema or implementation changes.
