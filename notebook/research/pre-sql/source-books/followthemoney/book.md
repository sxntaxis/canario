---
id: ACTAKIT-BOOK-FOLLOWTHEMONEY-001
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

# FollowTheMoney — investigative entities, statements, and rich associations

## Question

How do mature investigative systems model entities, provenance, and relationships with attributes?

## Evidence horizon

- **AKS-S019 — FollowTheMoney:** Relationship with attributes becomes interstitial entity; explicit warning against naive node/edge mapping
- **AKS-S020 — FollowTheMoney Statements:** Per-property value provenance and original value; statement-level representation

## Source-backed findings

- **AKS-C019:** Naively equating every real relation with an edge is known to fail when relations themselves carry data.
- **AKS-C020:** Per-value provenance is possible but materially increases record count and model complexity.

## ActaKit pressure

- **AKS-C019:** No universal nodes/edges schema; explicit tables plus optional association objects.
- **AKS-C020:** Do not adopt statement-per-field provenance unless fixtures show claim-level provenance is insufficient.

## Boundaries / do not cargo-cult

- **AKS-S019:** FtM is richer than ActaKit needs; borrow promotion heuristic, not schema wholesale
- **AKS-S020:** Universal per-field statement ledger would explode ActaKit complexity

## Disposition

This Book is evidence for the transversal synthesis. It does not independently authorize an architecture or implementation change.
