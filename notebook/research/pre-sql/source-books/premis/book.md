---
id: ACTAKIT-BOOK-PREMIS-DEEP-001
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

# PREMIS

## Question

Which preservation events deserve durable history?

## Deep-audit basis

Mature preservation standard/community guidance explicitly favors use-case-driven event recording.

## Evidence horizon

- **AKS-S007 — PREMIS 3.0:** Objects, Events, Agents and preservation-event thinking
- **AKS-S058 — PREMIS preservation events guidance:** Advises recording preservation events according to concrete use cases rather than treating all activity as preservation metadata

## Claim ledger synopsis

- **AKS-C005:** Preservation event modeling is valuable for consequential actions, but preservation standards do not imply that every transient operation is canonical civic data. **ActaKit:** Persist consequential custody/process events; leave low-value operational noise in logs.
- **AKS-C078:** Preservation metadata practice is use-case selective about which events deserve durable records. **ActaKit:** Persist acquisition, transformation, correction and purge events when consequential; keep routine execution noise in logs.

## Bounded transfer

Persist consequential custody/validation/migration/purge events.

## Do not copy

Do not store all runtime events forever.

## Schema pressure / expensive mistake avoided

Separate durable custody/process history from operational logs.

## Residual risk

ActaKit is not a preservation repository; transfer only what supports civic evidence custody.

## Closure verdict

Deep-audited for the pre-SQL decision horizon. This Book contributes evidence and constraints; it does not independently authorize schema or implementation changes.
