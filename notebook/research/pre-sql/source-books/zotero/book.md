---
id: ACTAKIT-BOOK-ZOTERO-DEEP-001
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

# Zotero

## Question

What do long-lived local SQLite document tools teach about write boundaries and annotations?

## Deep-audit basis

Operational guidance warns against direct DB writes; annotations remain separate from PDFs.

## Evidence horizon

- **AKS-S027 — Zotero PDF reader / annotations:** Annotations stored separately from PDF; links reopen source context; source file remains intact
- **AKS-S048 — Zotero annotations in database:** Annotations are stored separately from PDFs to avoid file conflicts; export can embed them later
- **AKS-S091 — Zotero direct SQLite database access guidance:** Direct writes are discouraged because they bypass application validation/referential invariants and schema can change

## Claim ledger synopsis

- **AKS-C068:** Separating annotations from source PDFs avoids rewriting evidence while still allowing exact navigation back to source context. **ActaKit:** Claims/review annotations should remain database records linked to immutable evidence representations, with export embedding only as a derivative output.
- **AKS-C122:** Direct SQLite writes can bypass application validation/referential integrity and are discouraged. **ActaKit:** Only ActaKit core writes canonical storage; consumers/adapters use contracts, not direct SQL mutation.
- **AKS-C123:** Annotations are stored separately from source PDFs, avoiding rewriting source evidence. **ActaKit:** Claims/reviews/evidence links are DB records pointing to immutable representations, not embedded source mutations.

## Bounded transfer

Core-only canonical writes; annotations/claims point to source; correct whole-authority backup.

## Do not copy

Do not expose DB schema as supported write API or embed canonical annotations into source files.

## Schema pressure / expensive mistake avoided

Storage contracts must mediate mutations and backup; locators bind to representation revision.

## Residual risk

Zotero-specific sync semantics are not ActaKit requirements.

## Closure verdict

Deep-audited for the pre-SQL decision horizon. This Book contributes evidence and constraints; it does not independently authorize schema or implementation changes.
