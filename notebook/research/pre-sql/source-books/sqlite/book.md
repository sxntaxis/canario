---
id: ACTAKIT-BOOK-SQLITE-001
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

# SQLite — relational graph traversal, FTS, and type discipline

## Question

Can the expected graph-shaped and full-text queries stay inside one relational baseline?

## Evidence horizon

- **AKS-S035 — SQLite recursive CTEs:** Recursive CTEs traverse trees/graphs in ordinary relational storage
- **AKS-S036 — SQLite FTS5:** Full-text search can live in same database and be rebuilt as projection/index
- **AKS-S037 — SQLite STRICT tables:** Stronger type discipline is available while retaining SQLite simplicity

## Source-backed findings

- **AKS-C049:** Full-text search is a rebuildable retrieval index, not evidence authority.
- **AKS-C050:** SQLite can enforce a stricter relational baseline than loose dynamic typing suggests.

## ActaKit pressure

- **AKS-C049:** Treat FTS as projection/index that can be rebuilt from canonical text/claims.
- **AKS-C050:** Use explicit columns/FKs/constraints; reserve JSON for versioned extensible payloads such as locators.

## Boundaries / do not cargo-cult

- **AKS-S035:** Traversal viability does not imply every relationship should be stored
- **AKS-S036:** FTS is search infrastructure, not canonical claim truth
- **AKS-S037:** STRICT does not replace application invariants or migrations

## Disposition

This Book is evidence for the transversal synthesis. It does not independently authorize an architecture or implementation change.
