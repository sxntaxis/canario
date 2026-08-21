---
id: ACTAKIT-BOOK-ELI-DEEP-001
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

# European Legislation Identifier (ELI)

## Question

How do source adapters distinguish coverage from freshness?

## Deep-audit basis

EU implementation experience added Pillar IV specifically because earlier metadata discovery could not prove either.

## Evidence horizon

- **AKS-S013 — European Legislation Identifier (ELI):** Legal resource identity/version/format distinctions and reusable metadata
- **AKS-S067 — ELI Pillar IV protocol specification:** Adds explicit mechanisms for corpus coverage and freshness because metadata pages alone cannot prove either
- **AKS-S068 — ELI Pillar IV helper documentation:** Implements exhaustive sitemap plus recent-update Atom feed generation and periodic full reprocessing

## Claim ledger synopsis

- **AKS-C089:** Finding metadata pages does not prove corpus coverage or freshness; ELI added explicit inventory and update-feed mechanisms to address both. **ActaKit:** Source adapters need separate coverage/freshness/checkpoint semantics; absence in one run is not deletion proof.
- **AKS-C090:** Periodic full inventory processing and incremental update feeds serve different ingestion guarantees. **ActaKit:** Allow adapters to report exhaustive inventory versus incremental discovery instead of pretending all source runs have the same completeness.

## Bounded transfer

Represent source discovery capability/completeness and incremental checkpoints separately.

## Do not copy

Do not adopt ELI RDF/URI identity as core.

## Schema pressure / expensive mistake avoided

Source runs/acquisitions need explicit inventory-vs-incremental semantics and no-delete-by-absence rule.

## Residual risk

Many municipal sources will not offer formal sitemaps/feeds; adapters need degraded confidence states.

## Closure verdict

Deep-audited for the pre-SQL decision horizon. This Book contributes evidence and constraints; it does not independently authorize schema or implementation changes.
