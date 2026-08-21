---
id: ACTAKIT-PRE-SQL-RESEARCH-001
type: research-program
state: deep-audited
authority: evidence
created: 2026-08-20
researched_through: 2026-08-20
actakit_baseline: 59bab9de30bbf2aa1eec96dddaee3cded31a9f3a
---

# Pre-SQL external research

This research asks what ActaKit should learn **before** freezing a durable SQLite schema.

Structure:

- `source-books/` — one Book per coherent external object, each with its own source and claim ledgers;
- `synthesis/` — only cross-source claims, scenarios, collisions, bounded transfers, gap audit, and current synthesis;
- `fixtures/` — semantic fixtures/counterexamples that pressure-test the model before SQL.

Current horizon:

- **29 source Books**;
- **97 source records**;
- **104 source-book research claims**, plus the pre-existing cross-source synthesis ledgers;
- **36 scenarios**;
- **27 collisions**;
- **30 bounded transfers**.

The package is research evidence. The four bounded fixture decisions (raw entity mentions, merge/split lineage, rich-relation promotion, and purge/tombstone policy) were resolved in the pre-SQL architecture closure before this deep audit. The completed Book-by-Book audit authorizes candidate schema design only; it does not authorize migrations or production implementation.

## Deep-audit closure

The 29 Source Books are individually deep-audited. See `synthesis/deep-audit-closure.md`, `synthesis/schema-pressures.csv`, and `synthesis/expensive-mistakes.csv`. Research closure authorizes candidate schema design only, not implementation.
