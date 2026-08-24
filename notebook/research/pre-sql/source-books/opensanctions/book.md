---
id: ACTAKIT-BOOK-OPENSANCTIONS-DEEP-001
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

# OpenSanctions / Nomenklatura

## Question

How should entity reconciliation evolve without erasing source identity?

## Deep-audit basis

Production-scale entity reconciliation separates source records, canonical IDs, referents and monitoring effects.

## Evidence horizon

- **AKS-S021 — OpenSanctions identifiers and de-duplication:** Source IDs, canonical entities, referents, automated high-confidence matching + human/LLM ambiguity handling
- **AKS-S038 — OpenSanctions Entity structure:** Entity references and interstitial entities; canonical metadata and referents
- **AKS-S039 — OpenSanctions Statement data model:** Per-source statements, source entity IDs, canonical IDs, first/last seen; data designed to merge/unmerge while keeping lineage
- **AKS-S040 — OpenSanctions monitoring / merge handling:** Confirmed/mismatch/unresolved states; merges cause ID churn and require referent-aware reconciliation

## Claim ledger synopsis

- **AKS-C023:** High-confidence automated matches and human review for ambiguity are compatible, but canonical identity churn is harmful to durable local references. **ActaKit:** Borrow candidate matching; keep ActaKit stable local entity IDs across merge/split.
- **AKS-C061:** A canonical entity can be a projection over source-scoped records and rich relationship objects while source-level assertions remain separately recoverable. **ActaKit:** Keep Entity as local resolved identity, but do not erase source EntityMentions/provenance when records are reconciled.
- **AKS-C062:** Collection and entity reconciliation can proceed on different timelines; unresolved or later-merged records remain legitimate intermediate states. **ActaKit:** Claim/document ingestion must not block on perfect entity resolution; reconciliation is revisable later.
- **AKS-C114:** Canonical identity can change through reconciliation while source identifiers remain distinct and referents preserve continuity. **ActaKit:** ActaKit local entity IDs and reconciliation lineage must be distinct from source IDs and aliases.
- **AKS-C115:** Entity merges/splits and score changes can surface as apparent monitoring changes even when source reality did not change. **ActaKit:** Identity reconciliation events must be distinguishable from new civic evidence in queries/outputs.

## Bounded transfer

Preserve raw mentions/source IDs; canonicalize later; keep merge/split/referent lineage.

## Do not copy

Do not promise external canonical IDs are permanent or auto-merge by name.

## Schema pressure / expensive mistake avoided

EntityMention and Entity lineage must be first class; reconciliation change must not masquerade as new civic evidence.

## Residual risk

Local stable IDs may deliberately be stronger than external IDs, requiring careful import mapping.

## Closure verdict

Deep-audited for the pre-SQL decision horizon. This Book contributes evidence and constraints; it does not independently authorize schema or implementation changes.
