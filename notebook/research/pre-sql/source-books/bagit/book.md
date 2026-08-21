---
id: ACTAKIT-BOOK-BAGIT-DEEP-001
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

# BagIt

## Question

What can portable checksum manifests teach export/backup?

## Deep-audit basis

RFC plus implementation bug demonstrates both simplicity and interoperability scars.

## Evidence horizon

- **AKS-S009 — BagIt RFC 8493:** Payload + checksum manifests; complete vs valid package
- **AKS-S060 — BagIt path-encoding interoperability bug:** Implementations diverged from RFC path percent-encoding rules, producing interoperability failures around percent signs

## Claim ledger synopsis

- **AKS-C008:** Checksummed self-describing packages provide a simple integrity boundary for transfer/backup. **ActaKit:** Prefer BagIt-like package manifests for export/backup before inventing federation packages.
- **AKS-C080:** Even a small transfer standard accumulated cross-implementation path-encoding divergence around percent signs. **ActaKit:** Treat package validation/version compatibility as real tests; never assume manifest conformance from library name alone.
- **AKS-C081:** Bag integrity checks detect accidental corruption but do not by themselves provide authenticity against an active attacker. **ActaKit:** Use hashes for integrity; do not imply cryptographic signer authenticity unless separately implemented.

## Bounded transfer

Use simple manifest/checksum packages for bounded export/backup validation.

## Do not copy

Do not treat hashes as authenticity or fetch.txt URLs as safe implicit network authority.

## Schema pressure / expensive mistake avoided

Export package paths must be confined and version-validated.

## Residual risk

BagIt may be useful as an output format, not internal authority.

## Closure verdict

Deep-audited for the pre-SQL decision horizon. This Book contributes evidence and constraints; it does not independently authorize schema or implementation changes.
