---
id: ACTAKIT-BOOK-OPENSANCTIONS-001
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

# OpenSanctions — stable local identity and reconciliation pressure

## Question

How can reconciliation preserve stable local identity while absorbing changing source identifiers?

## Evidence horizon

- **AKS-S021 — OpenSanctions identifiers and de-duplication:** Source IDs, canonical entities, referents, automated high-confidence matching + human/LLM ambiguity handling
- **AKS-S038 — OpenSanctions Entity structure:** Entity references and interstitial entities; canonical metadata and referents
- **AKS-S039 — OpenSanctions Statement data model:** Per-source statements, source entity IDs, canonical IDs, first/last seen; data designed to merge/unmerge while keeping lineage
- **AKS-S040 — OpenSanctions monitoring / merge handling:** Confirmed/mismatch/unresolved states; merges cause ID churn and require referent-aware reconciliation

## Source-backed findings

- **AKS-C023:** High-confidence automated matches and human review for ambiguity are compatible, but canonical identity churn is harmful to durable local references.
- **AKS-C061:** A canonical entity can be a projection over source-scoped records and rich relationship objects while source-level assertions remain separately recoverable.
- **AKS-C062:** Collection and entity reconciliation can proceed on different timelines; unresolved or later-merged records remain legitimate intermediate states.

## ActaKit pressure

- **AKS-C023:** Borrow candidate matching; keep ActaKit stable local entity IDs across merge/split.
- **AKS-C061:** Keep Entity as local resolved identity, but do not erase source EntityMentions/provenance when records are reconciled.
- **AKS-C062:** Claim/document ingestion must not block on perfect entity resolution; reconciliation is revisable later.

## Boundaries / do not cargo-cult

- **AKS-S021:** ActaKit should not adopt changing/expiring canonical IDs as local identity
- **AKS-S038:** Domain is sanctions/PEP, richer than ActaKit needs
- **AKS-S039:** Statement-per-property is explicitly advanced and most users use simplified exports
- **AKS-S040:** Screening workflow is not ActaKit workflow

## Disposition

This Book is evidence for the transversal synthesis. It does not independently authorize an architecture or implementation change.
