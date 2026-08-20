---
id: ACTAKIT-BOOK-PAPERLESS-NGX-001
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

# Paperless-ngx — original/derived custody and operator bulk workflows

## Question

What does a mature self-hosted document workflow teach about originals, derivatives, typing, and bulk operations?

## Evidence horizon

- **AKS-S025 — Paperless-ngx usage/configuration:** Original preserved separately from OCR/archive; optional document types; tags/custom fields; bulk edit; history
- **AKS-S045 — Paperless-ngx REST API:** Root document metadata separated from file versions; version-specific files/checksums/text; asynchronous bulk editing/reprocessing
- **AKS-S046 — Paperless-ngx FAQ:** Original documents are not modified; checksums/sanity checking and exporter support portability
- **AKS-S047 — Paperless-ngx Advanced Usage:** Original/archive paths are distinct; document/version filenames and checksums are modeled separately

## Source-backed findings

- **AKS-C066:** A root document can retain stable metadata while file versions carry their own bytes, checksums and extracted text.
- **AKS-C067:** Bulk edit/reprocess and file integrity checking coexist without making the bulk action itself the durable domain object.

## ActaKit pressure

- **AKS-C066:** Fixture CivicDocument identity separately from Artifact/Representation versions; do not duplicate document identity for every processing version.
- **AKS-C067:** Batch/supervised operations may write many individually attributable results without a permanent ReviewBatch entity.

## Boundaries / do not cargo-cult

- **AKS-S025:** Personal DMS, not civic claim/evidence system
- **AKS-S045:** Personal DMS API topology is not ActaKit architecture
- **AKS-S046:** Some PDF actions can intentionally modify originals, so ActaKit must be stricter about custody artifacts
- **AKS-S047:** Operational filesystem details are not domain identity

## Disposition

This Book is evidence for the transversal synthesis. It does not independently authorize an architecture or implementation change.
