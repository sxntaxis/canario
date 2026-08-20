---
id: ACTAKIT-BOOK-BAGIT-001
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

# BagIt — integrity packages for backup and export

## Question

What is the smallest robust boundary for moving/verifying a backup or export corpus?

## Evidence horizon

- **AKS-S009 — BagIt RFC 8493:** Payload + checksum manifests; complete vs valid package

## Source-backed findings

- **AKS-C008:** Checksummed self-describing packages provide a simple integrity boundary for transfer/backup.

## ActaKit pressure

- **AKS-C008:** Prefer BagIt-like package manifests for export/backup before inventing federation packages.

## Boundaries / do not cargo-cult

- **AKS-S009:** Better fit for export/backup/evidence packages than canonical internal store

## Disposition

This Book is evidence for the transversal synthesis. It does not independently authorize an architecture or implementation change.
