---
id: ACTAKIT-BOOK-OPENSTATES-DEEP-001
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

# Open States

## Question

How should civic scrapers normalize imperfect source data safely?

## Deep-audit basis

Production civic-data project preserves raw labels/resolutions and documents fail-loud parser philosophy plus real scraper defects.

## Evidence horizon

- **AKS-S023 — Open States data model:** Raw source names coexist with resolved entities; source and normalized classifications can differ; multiple manifestations
- **AKS-S024 — Open States scraper testing guidance:** Unexpected input should fail loudly rather than silently ingest wrong structured data
- **AKS-S041 — Open States Data Types:** Interconnected civic nodes; optional fields; Membership/RelatedEntity preserve raw person/entity names alongside resolved nodes
- **AKS-S042 — Open States Categorization:** Source-specific legislative categories are mapped to a smaller normalized cross-jurisdiction view
- **AKS-S043 — Open States Name Matching notes:** Raw person/organization string is always collected; resolved Person/Organization link is attempted later and may be absent

## Claim ledger synopsis

- **AKS-C024:** Source-supplied labels/classifications and normalized classifications can coexist rather than silently overwriting each other. **ActaKit:** Preserve raw type/name and normalized interpretation separately.
- **AKS-C025:** Specialized scrapers/parsers should fail loudly on unexpected structure because silent bad structured data is harder to detect than a failed run. **ActaKit:** Graceful degradation means preserve/generic-process; specialized profile parse may become partial/failed.
- **AKS-C064:** A civic record can preserve a raw source-provided person or organization name while the normalized entity link remains absent or is resolved later. **ActaKit:** EntityMention is not an optional convenience; it is the safe boundary between extraction and identity resolution.
- **AKS-C065:** Cross-jurisdiction normalization can coexist with source-specific classification instead of replacing it. **ActaKit:** Keep source_supplied_type/classification separate from normalized_type/profile semantics.
- **AKS-C116:** Raw source-provided names can coexist with resolved civic entities rather than blocking ingestion. **ActaKit:** Preserve EntityMention/raw labels and resolve later.
- **AKS-C117:** Specialized scrapers are intentionally expected to fail when source structure changes rather than emitting plausible bad data. **ActaKit:** Generic acquisition may degrade; specialized interpretation must fail loudly on invariant violation.

## Bounded transfer

Keep raw names/types, optional normalized identity, and specialized-parser invariant tests.

## Do not copy

Do not import US legislative ontology/categorization wholesale.

## Schema pressure / expensive mistake avoided

Acquisition can succeed while specialized parse fails/partial; normalized fields never overwrite raw evidence.

## Residual risk

Source websites remain unstable and require adapter-specific tests/monitoring.

## Closure verdict

Deep-audited for the pre-SQL decision horizon. This Book contributes evidence and constraints; it does not independently authorize schema or implementation changes.
