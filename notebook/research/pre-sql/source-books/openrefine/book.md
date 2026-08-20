---
id: ACTAKIT-BOOK-OPENREFINE-001
type: research-source-book
state: complete
authority: evidence
created: 2026-08-20
updated: 2026-08-20
researched_through: 2026-08-20
actakit_baseline: 59bab9de30bbf2aa1eec96dddaee3cded31a9f3a
source_ledger: sources.csv
claim_ledger: claims.csv
---

# OpenRefine — unresolved identity and batch reconciliation

## Question

How should one operator resolve ambiguous entities efficiently and honestly?

## Evidence horizon

- **AKS-S022 — OpenRefine Reconciliation:** Raw label -> ranked candidates -> matched/new/unresolved; batch review and additional fields for disambiguation
- **AKS-S044 — OpenRefine Reconciliation API:** Ranked entity candidates from label plus optional type/properties; identifier spaces remain service-defined

## Source-backed findings

- **AKS-C022:** Ambiguous reconciliation works well as ranked candidates plus explicit matched/new/unresolved judgments and batch approval.
- **AKS-C063:** Reconciliation preserves the original value alongside candidate/match state and supports explicit matched/new/unresolved judgments plus mass actions over filtered subsets.

## ActaKit pressure

- **AKS-C022:** Entity resolution UI/workflow should be semi-automatic, not name-equality magic.
- **AKS-C063:** EntityMention resolution should preserve raw text, candidate/decision state, and per-record outcome even when an operator acts in bulk.

## Boundaries / do not cargo-cult

- **AKS-S022:** External reconciliation services are optional, not core authority
- **AKS-S044:** ActaKit need not expose a reconciliation web service

## Disposition

This Book is evidence for the transversal synthesis. It does not independently authorize an architecture or implementation change.
