---
id: ACTAKIT-BOOK-WARC-DEEP-001
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

# WARC

## Question

How should repeated acquisition of web resources be identified?

## Deep-audit basis

Standard + implementation guidelines + production erratum expose capture/record/payload distinctions.

## Evidence horizon

- **AKS-S010 — WARC 1.1:** Capture date, target URI, record IDs, request/response association, payload digests, revisit semantics
- **AKS-S061 — WARC implementation guidelines:** Separates capture-event records and links request/response/revisit records arising from one retrieval
- **AKS-S062 — Common Crawl WARC revisit Content-Type erratum:** A WARC example propagated an incorrect revisit Content-Type into crawls spanning 2013–2026

## Claim ledger synopsis

- **AKS-C010:** A capture can record request/response association, timestamp, target URI and payload digest without claiming the resource changed. **ActaKit:** Acquisition should preserve observation outcome independently from civic-document semantics.
- **AKS-C082:** One retrieval can produce multiple linked records while still representing a single capture event. **ActaKit:** Separate Acquisition observation from Artifact bytes and allow multiple observations of identical bytes.
- **AKS-C083:** A specification example mistake propagated into production archive records for years. **ActaKit:** Store parser/format version and raw metadata so normalized interpretations can be repaired without losing the capture.

## Bounded transfer

Separate source URI, acquisition observation, record identity and payload Artifact; identical bytes can be observed repeatedly.

## Do not copy

Do not require WARC for ordinary source adapters.

## Schema pressure / expensive mistake avoided

Acquisition rows need stable observation identity and raw source metadata/version provenance.

## Residual risk

HTTP/web archives are only one acquisition family; model must remain generic.

## Closure verdict

Deep-audited for the pre-SQL decision horizon. This Book contributes evidence and constraints; it does not independently authorize schema or implementation changes.
