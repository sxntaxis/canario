---
id: ACTAKIT-BOOK-SQLITE-DEEP-001
type: research-source-book
state: deep-audited
authority: evidence
created: 2026-08-20
updated: 2026-08-21
researched_through: 2026-08-21
actakit_baseline: 59bab9de30bbf2aa1eec96dddaee3cded31a9f3a
source_ledger: sources.csv
claim_ledger: claims.csv
---

# SQLite

## Question

Can one local relational store safely host canonical graph-shaped civic data and search indexes?

## Deep-audit basis

Current database docs plus 2026 release scars cover WAL, FK bootstrap, backup, FTS and type discipline.

## Evidence horizon

- **AKS-S035 — SQLite recursive CTEs:** Recursive CTEs traverse trees/graphs in ordinary relational storage
- **AKS-S036 — SQLite FTS5:** Full-text search can live in same database and be rebuilt as projection/index
- **AKS-S037 — SQLite STRICT tables:** Stronger type discipline is available while retaining SQLite simplicity
- **AKS-S092 — SQLite WAL documentation:** WAL permits readers with a writer but requires same-machine shared memory; long readers can cause checkpoint starvation
- **AKS-S093 — SQLite foreign key documentation:** Foreign-key enforcement is enabled per connection and historically defaults off unless explicitly requested
- **AKS-S094 — SQLite Online Backup API:** Backup API produces a consistent snapshot of a live database
- **AKS-S095 — SQLite release/change history:** 2026 releases include WAL-related corruption/deadlock fixes, showing version choice is an operational invariant
- **AKS-S098 — SQLite secure_delete pragma:** ordinary deletion can leave recoverable bytes; forensic scrubbing requires explicit handling and has virtual-table limits
- **AKS-S099 — SQLite FTS5 secure-delete and projection modes:** old indexed terms can survive normal deletes; FTS projection modes carry different consistency/rebuild tradeoffs

## Claim ledger synopsis

- **AKS-C049:** Full-text search is a rebuildable retrieval index, not evidence authority. **ActaKit:** Treat FTS as projection/index that can be rebuilt from canonical text/claims.
- **AKS-C050:** SQLite can enforce a stricter relational baseline than loose dynamic typing suggests. **ActaKit:** Use explicit columns/FKs/constraints; reserve JSON for versioned extensible payloads such as locators.
- **AKS-C124:** WAL is same-machine only, permits one writer and can grow under long readers/checkpoint starvation. **ActaKit:** Use local attached storage, one canonical writer path, short transactions/read snapshots and explicit checkpoint monitoring.
- **AKS-C125:** Foreign-key enforcement must be explicitly enabled on each SQLite connection. **ActaKit:** Connection bootstrap must set/verify required PRAGMAs before any canonical read/write service starts.
- **AKS-C126:** A live SQLite database requires the backup API or equivalent consistent snapshot mechanism rather than naive file copying. **ActaKit:** Backup/restore design is part of storage correctness, not an afterthought.
- **AKS-C127:** Recent SQLite releases have fixed WAL/concurrency corruption and deadlock defects. **ActaKit:** Declare/test a minimum SQLite version and include upstream defect history in upgrade policy.
- **AKS-C128:** External/contentless FTS indexes can diverge from authoritative content unless maintained and checked. **ActaKit:** FTS stays rebuildable and integrity-checkable; never make it canonical evidence/claim storage.
- **AKS-C131:** STRICT primary-key components are implicitly non-null. **ActaKit:** optional role/mention fields cannot double as composite primary-key columns; give such links stable row identity.
- **AKS-C132:** SQLite logical deletion is not physical scrubbing. **ActaKit:** purge must explicitly scrub database remnants rather than equating `DELETE` with erasure.
- **AKS-C133:** FTS5 needs its own secure-delete handling in addition to SQLite core scrubbing. **ActaKit:** purge propagates through FTS with explicit secure-delete/rebuild policy.
- **AKS-C134:** the WAL-reset corruption bug is fixed in 3.51.3+. **ActaKit:** initial runtime floor is 3.51.3 unless a patched earlier build is specifically certified.
- **AKS-C135:** external/contentless FTS modes add consistency/rowid/rebuild tradeoffs that ActaKit does not need at canton scale. **ActaKit:** ordinary self-content FTS is the simpler disposable projection baseline.
- **AKS-C136:** recursive CTE `UNION` suppresses repeated rows while `UNION ALL` preserves them; SQLite uses `UNION` in its graph example to avoid cycle repetition. **ActaKit:** distinguish deduplicated node reachability from relation-edge/path enumeration in the ClaimRelation multigraph.

## Bounded transfer

Use one local SQLite authority with explicit connection invariants, bounded transactions, consistent backup and rebuildable FTS.

## Do not copy

Do not use network/synced filesystem, direct external writes, naive live file copy or FTS as authority.

## Schema pressure / expensive mistake avoided

Schema design must include PRAGMA bootstrap, one-writer discipline, a safe version floor, backup/restore, FTS rebuild policy, and an explicit purge-scrubbing path for ordinary/FTS storage.

## Residual risk

Performance/concurrency must still be proven with ActaKit fixtures and expected corpus sizes. Device-level secure erasure and historical-backup deletion remain policy/storage concerns beyond SQLite row semantics.

## Closure verdict

Deep-audited for the pre-SQL decision horizon. This Book contributes evidence and constraints; it does not independently authorize schema or implementation changes.
