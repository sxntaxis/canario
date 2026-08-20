---
id: ACTAKIT-BOOK-WARC-001
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

# WARC — observation/capture is not the web resource

## Question

What must ActaKit remember about an observation of a web source?

## Evidence horizon

- **AKS-S010 — WARC 1.1:** Capture date, target URI, record IDs, request/response association, payload digests, revisit semantics

## Source-backed findings

- **AKS-C010:** A capture can record request/response association, timestamp, target URI and payload digest without claiming the resource changed.

## ActaKit pressure

- **AKS-C010:** Acquisition should preserve observation outcome independently from civic-document semantics.

## Boundaries / do not cargo-cult

- **AKS-S010:** Capturing every source as WARC is not required for baseline imports

## Disposition

This Book is evidence for the transversal synthesis. It does not independently authorize an architecture or implementation change.
