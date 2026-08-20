---
id: ACTAKIT-BOOK-SHACL-001
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

# SHACL — validation separated from the data model

## Question

How can validation evolve independently from canonical records?

## Evidence horizon

- **AKS-S032 — SHACL:** Validation shapes separated from data model

## Source-backed findings

- **AKS-C034:** Validation constraints can be a separate layer from the data vocabulary.
- **AKS-C058:** Typed/versioned validation contracts are a safer extension mechanism than arbitrary payloads.

## ActaKit pressure

- **AKS-C034:** Profiles/locators/outputs should have versioned validators rather than arbitrary JSON.
- **AKS-C058:** Locator/profile/output config schemas must be versioned and validated.

## Boundaries / do not cargo-cult

- **AKS-S032:** ActaKit can borrow validation-layer principle with ordinary typed schemas

## Disposition

This Book is evidence for the transversal synthesis. It does not independently authorize an architecture or implementation change.
