---
id: ACTAKIT-BOOK-OCFL-DEEP-001
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

# OCFL

## Question

How should immutable-by-default artifact custody coexist with exceptional deletion?

## Deep-audit basis

Preservation specification plus implementation notes address version inventories and purge tension.

## Evidence horizon

- **AKS-S008 — Oxford Common File Layout 1.1:** Immutable prior versions, digest-addressed content, logical vs physical paths, deduplication
- **AKS-S059 — OCFL implementation notes:** Documents implementation tradeoffs including exceptional purge/reconstruction and digest/version handling

## Claim ledger synopsis

- **AKS-C006:** Content-addressed immutable prior versions and logical/physical path separation are proven preservation patterns. **ActaKit:** Use content-addressed ArchiveObject byte identity behind stable logical Artifact custody identity; do not make path or digest the whole provenance record.
- **AKS-C007:** Absolute immutability can collide with legitimate purge/redaction obligations. **ActaKit:** Define custody deletion/purge semantics explicitly instead of promising eternal bytes.
- **AKS-C079:** Immutable-version preservation systems still need an exceptional purge path and may require object reconstruction to remove content. **ActaKit:** Model purge as explicit exceptional lifecycle action distinct from ordinary revision/redaction.

## Bounded transfer

Use digest-addressed immutable artifacts/versions and an explicit exceptional purge path.

## Do not copy

Do not adopt full OCFL object layout/inventory unless export/scale later proves value.

## Schema pressure / expensive mistake avoided

Artifact identity must not be filesystem path; purge needs lineage/tombstone policy.

## Residual risk

Legal retention requirements vary by deployment and cannot be solved by storage structure alone.

## Closure verdict

Deep-audited for the pre-SQL decision horizon. This Book contributes evidence and constraints; it does not independently authorize schema or implementation changes.
