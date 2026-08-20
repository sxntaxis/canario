---
id: ACTAKIT-BOOK-OCFL-001
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

# OCFL — immutable artifact thinking without repository overkill

## Question

How should ActaKit think about artifact identity, prior versions, and content addressing?

## Evidence horizon

- **AKS-S008 — Oxford Common File Layout 1.1:** Immutable prior versions, digest-addressed content, logical vs physical paths, deduplication

## Source-backed findings

- **AKS-C006:** Content-addressed immutable prior versions and logical/physical path separation are proven preservation patterns.
- **AKS-C007:** Absolute immutability can collide with legitimate purge/redaction obligations.

## ActaKit pressure

- **AKS-C006:** Use immutable artifact identity/digests; do not make path the identity.
- **AKS-C007:** Define custody deletion/purge semantics explicitly instead of promising eternal bytes.

## Boundaries / do not cargo-cult

- **AKS-S008:** Full OCFL repository machinery is likely excessive; deletion/purge policy can collide with immutability

## Disposition

This Book is evidence for the transversal synthesis. It does not independently authorize an architecture or implementation change.
