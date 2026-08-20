---
id: ACTAKIT-BOOK-METHOD-001
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

# Method — Stereo research discipline and Plaza correctness scars

## Question

How should ActaKit research itself before freezing expensive architectural decisions?

## Evidence horizon

- **AKS-S001 — Stereo Research Package Protocol:** Ledger-v1, bounded transfers, current-version rule
- **AKS-S002 — Plaza Principles:** Evidence before inference; provenance; identity; standards discipline
- **AKS-S003 — Plaza Correctness Audit Report:** Inventory != correctness; derived identity/segmentation can be wrong while raw evidence is sound

## Source-backed findings

- **AKS-C036:** A complete inventory of files does not prove correctness of derived structured records.
- **AKS-C037:** Identity errors propagate into downstream records and can make structurally valid data semantically wrong.
- **AKS-C039:** Research transfers need explicit stop conditions so external mechanisms do not become accidental architecture authority.
- **AKS-C060:** A research horizon is complete when remaining gaps no longer threaten the pending decision, not when source count reaches a quota.

## ActaKit pressure

- **AKS-C036:** ActaKit fixtures/tests must audit derived claims/identity/relations against artifacts, not only pipeline completion.
- **AKS-C037:** Identity reconciliation requires explicit audit and provenance.
- **AKS-C039:** Every adopted standard pattern in this Book has a non-transfer boundary.
- **AKS-C060:** Stop this Book at pre-SQL semantics; move unanswered implementation detail into fixtures/SQL study.

## Boundaries / do not cargo-cult

- **AKS-S001:** Method, not ActaKit product authority
- **AKS-S002:** Plaza is a methodological comparator, never an ActaKit dependency
- **AKS-S003:** Legacy Plaza findings do not directly measure ActaKit

## Disposition

This Book is evidence for the transversal synthesis. It does not independently authorize an architecture or implementation change.
