---
id: ACTAKIT-BOOK-MEMENTO-DEEP-001
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

# Memento

## Question

What does a web-archive URI actually prove about historical identity/time?

## Deep-audit basis

RFC plus longitudinal studies show archive replay drift and locator instability.

## Evidence horizon

- **AKS-S011 — Memento RFC 7089:** Original resource vs datetime-specific past representations
- **AKS-S063 — Where Did the Web Archive Go?:** Across 16,627 mementos, archive base-URI changes altered or lost rediscovery of some captures
- **AKS-S064 — Temporal drift in web archive browsing:** Shows browsing archived links can silently drift far from the requested datetime; sticky target policies reduce drift

## Claim ledger synopsis

- **AKS-C084:** Archived-resource locator URLs can change, and rediscovered captures can differ in timestamp/status/original-URI or disappear. **ActaKit:** Capture identity cannot be the replay URL; preserve observed archive identity, datetime and source metadata separately.
- **AKS-C085:** Following archived links can silently shift the effective historical datetime by large amounts. **ActaKit:** A query/output assembling archived evidence must not imply temporal coherence merely because pages are linked.

## Bounded transfer

Preserve original-resource URI, capture datetime, observed replay locator and acquisition identity separately.

## Do not copy

Do not assume linked archived pages represent the same historical instant.

## Schema pressure / expensive mistake avoided

Source/capture identity must not be a URL alone; query/output must expose temporal uncertainty when relevant.

## Residual risk

External archives can disappear or reinterpret captures beyond ActaKit control.

## Closure verdict

Deep-audited for the pre-SQL decision horizon. This Book contributes evidence and constraints; it does not independently authorize schema or implementation changes.
