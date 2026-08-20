---
id: ACTAKIT-BOOK-OPENSTATES-001
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

# Open States — raw-versus-normalized civic ingestion and fail-loud parsers

## Question

What ingestion scars matter for civic documents and fragile source parsers?

## Evidence horizon

- **AKS-S023 — Open States data model:** Raw source names coexist with resolved entities; source and normalized classifications can differ; multiple manifestations
- **AKS-S024 — Open States scraper testing guidance:** Unexpected input should fail loudly rather than silently ingest wrong structured data
- **AKS-S041 — Open States Data Types:** Interconnected civic nodes; optional fields; Membership/RelatedEntity preserve raw person/entity names alongside resolved nodes
- **AKS-S042 — Open States Categorization:** Source-specific legislative categories are mapped to a smaller normalized cross-jurisdiction view
- **AKS-S043 — Open States Name Matching notes:** Raw person/organization string is always collected; resolved Person/Organization link is attempted later and may be absent

## Source-backed findings

- **AKS-C024:** Source-supplied labels/classifications and normalized classifications can coexist rather than silently overwriting each other.
- **AKS-C025:** Specialized scrapers/parsers should fail loudly on unexpected structure because silent bad structured data is harder to detect than a failed run.
- **AKS-C064:** A civic record can preserve a raw source-provided person or organization name while the normalized entity link remains absent or is resolved later.
- **AKS-C065:** Cross-jurisdiction normalization can coexist with source-specific classification instead of replacing it.

## ActaKit pressure

- **AKS-C024:** Preserve raw type/name and normalized interpretation separately.
- **AKS-C025:** Graceful degradation means preserve/generic-process; specialized profile parse may become partial/failed.
- **AKS-C064:** EntityMention is not an optional convenience; it is the safe boundary between extraction and identity resolution.
- **AKS-C065:** Keep source_supplied_type/classification separate from normalized_type/profile semantics.

## Boundaries / do not cargo-cult

- **AKS-S023:** US civic semantics are not universal Costa Rican semantics
- **AKS-S024:** Fail-loud applies to specialized parsing, not to artifact preservation itself
- **AKS-S041:** US legislative model is not a universal civic ontology
- **AKS-S042:** US category vocabulary is not reusable verbatim
- **AKS-S043:** Matching implementation is project-specific

## Disposition

This Book is evidence for the transversal synthesis. It does not independently authorize an architecture or implementation change.
