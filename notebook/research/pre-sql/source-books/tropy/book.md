---
id: ACTAKIT-BOOK-TROPY-DEEP-001
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

# Tropy

## Question

How can structured profiles, local tags and regions coexist in a research workflow?

## Deep-audit basis

Research-document product supports templates, local tags and selections without mutating originals.

## Evidence horizon

- **AKS-S026 — Tropy documentation:** Local items, multi-page grouping, metadata templates, tags, bulk metadata; standard vocabularies where useful
- **AKS-S051 — Tropy project view and metadata editing:** Broad project view supports list/grid, bulk metadata and tags; item view supports focused notes/transcription
- **AKS-S052 — Tropy metadata editing:** Customizable templates can add vocabulary-backed fields and metadata can be edited across multiple items
- **AKS-S090 — Tropy metadata templates:** Structured templates coexist with flexible project-local metadata and tags

## Claim ledger synopsis

- **AKS-C071:** Structured templates and local tags can coexist, and both can be edited in bulk across heterogeneous research items. **ActaKit:** Keep document profiles optional and local tags flexible; do not force every civic document into one closed schema before it becomes useful.
- **AKS-C121:** Structured templates and flexible local tags coexist in a research-document workflow. **ActaKit:** Document profiles are optional typed enrichments; tags remain local/flexible by default.

## Bounded transfer

Optional profiles + flexible tags + region/selectors over source representation.

## Do not copy

Do not treat every selection as a new document or require one global metadata template.

## Schema pressure / expensive mistake avoided

DocumentPart/region remains optional and locator-bound.

## Residual risk

Collaboration/multiuser is outside baseline; local-project assumptions should not leak into core identity.

## Closure verdict

Deep-audited for the pre-SQL decision horizon. This Book contributes evidence and constraints; it does not independently authorize schema or implementation changes.
