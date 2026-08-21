---
id: ACTAKIT-BOOK-DATASETTE-DEEP-001
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

# Datasette

## Question

How should read-heavy consumers query SQLite safely?

## Deep-audit basis

Mature read-oriented SQLite product exposes security/permission and plugin-write scars plus bounded query controls.

## Evidence horizon

- **AKS-S029 — Datasette:** SQLite can support faceting, FTS, filters, JSON/CSV and broad read-only audiences
- **AKS-S085 — Datasette authentication and permissions:** Restricting tables does not block access through arbitrary SQL unless execute-sql is also denied
- **AKS-S086 — Datasette plugin internals:** Plugins sharing an internal SQLite DB are warned to avoid long writes, collisions and private-data exposure
- **AKS-S087 — Datasette settings and bounded facets:** Facet and result limits are explicitly bounded to keep interactive querying tractable
- **AKS-S088 — Datasette 2026 write-SQL changes:** Write SQL was added behind explicit permissions and table-level authorization rather than assumed safe from read-only heritage

## Claim ledger synopsis

- **AKS-C109:** Table-level restrictions can be bypassed by arbitrary SQL unless execute-sql permission is also restricted. **ActaKit:** Consumer APIs should expose bounded query capabilities, not unrestricted SQL over canonical/private tables.
- **AKS-C110:** Shared plugin writes create blocking, namespace and privacy risks inside one SQLite database. **ActaKit:** Outputs/plugins should be read-oriented and isolated; mutation must route through core capabilities.
- **AKS-C111:** Interactive facets/search are explicitly protected with row/time/thread limits. **ActaKit:** Queries and graph traversal need bounded depth/result/time budgets.

## Bounded transfer

Use read-oriented projections/contracts with bounded query capabilities; canonical mutation separate.

## Do not copy

Do not expose arbitrary SQL or unrestricted plugin writes over canonical DB.

## Schema pressure / expensive mistake avoided

Consumer query API must enforce row/time/depth permissions; Outputs default read-only.

## Residual risk

ActaKit may not need a network query service at 1.0; transfer the constraints, not the server.

## Closure verdict

Deep-audited for the pre-SQL decision horizon. This Book contributes evidence and constraints; it does not independently authorize schema or implementation changes.
