---
id: ACTAKIT-BOOK-PAPERLESS_NGX-DEEP-001
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

# Paperless-ngx

## Question

How should logical documents, file versions and backup boundaries be separated?

## Deep-audit basis

Operational document manager distinguishes source/working/derived versions, bulk workflows and backup/export.

## Evidence horizon

- **AKS-S025 — Paperless-ngx usage/configuration:** Original preserved separately from OCR/archive; optional document types; tags/custom fields; bulk edit; history
- **AKS-S045 — Paperless-ngx REST API:** Root document metadata separated from file versions; version-specific files/checksums/text; asynchronous bulk editing/reprocessing
- **AKS-S046 — Paperless-ngx FAQ:** Original documents are not modified; checksums/sanity checking and exporter support portability
- **AKS-S047 — Paperless-ngx Advanced Usage:** Original/archive paths are distinct; document/version filenames and checksums are modeled separately

## Claim ledger synopsis

- **AKS-C066:** A root document can retain stable metadata while file versions carry their own bytes, checksums and extracted text. **ActaKit:** Fixture CivicDocument identity separately from Artifact/Representation versions; do not duplicate document identity for every processing version.
- **AKS-C067:** Bulk edit/reprocess and file integrity checking coexist without making the bulk action itself the durable domain object. **ActaKit:** Batch/supervised operations may write many individually attributable results without a permanent ReviewBatch entity.
- **AKS-C118:** Logical document metadata can remain stable while file versions/checksums/text change through processing. **ActaKit:** Keep CivicDocument identity separate from Artifact and Representation versions.
- **AKS-C119:** Unsafe source-path mutation and nondeterministic preprocessing can damage custody or create duplicate processing outcomes. **ActaKit:** Transform only working/derived copies; capture transformation tool/version/config and artifact identity.
- **AKS-C120:** Backup/export guidance distinguishes authority-bearing content from regenerable derived material. **ActaKit:** Define backup boundary as DB + originals + non-regenerable state; rebuild FTS/thumbnails/derived caches when safe.

## Bounded transfer

Stable logical document identity; immutable source Artifact; regenerable derived representations; whole-authority backup.

## Do not copy

Do not copy consumer document-management workflow or tags as ActaKit ontology.

## Schema pressure / expensive mistake avoided

Document vs Artifact vs Representation tables; backup marks derived indexes/caches as rebuildable.

## Residual risk

ActaKit custody requirements are stricter than ordinary personal document management.

## Closure verdict

Deep-audited for the pre-SQL decision horizon. This Book contributes evidence and constraints; it does not independently authorize schema or implementation changes.
