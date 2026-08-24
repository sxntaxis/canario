---
id: ACTAKIT-BOOK-FRICTIONLESS_DATA_PACKAGE-DEEP-001
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

# Frictionless Data Package

## Question

How should portable Output/import manifests behave?

## Deep-audit basis

Interchange standard plus explicit security guidance around paths/URLs.

## Evidence horizon

- **AKS-S030 — Data Package / Frictionless:** Small pieces, loosely joined; profiles/resources; extensible package manifests
- **AKS-S079 — Data Package security guidance:** Warns that untrusted resource URLs and paths can enable SSRF, local-file access and denial of service

## Claim ledger synopsis

- **AKS-C032:** Interchange packages benefit from small composable manifests/profiles rather than product-specific monoliths. **ActaKit:** Outputs/exports should have bounded manifests once sharing is real.
- **AKS-C103:** Portable manifests containing untrusted URLs or paths are active security inputs, not passive metadata. **ActaKit:** Output/import package handling must confine local paths and default-deny remote fetches unless explicitly authorized.

## Bounded transfer

Small versioned manifests are useful boundary formats with strict path/network policy.

## Do not copy

Do not make package format the internal database model or auto-fetch arbitrary URLs.

## Schema pressure / expensive mistake avoided

Output manifests need schema/version validation, root confinement and explicit remote-fetch capability.

## Residual risk

Exact interchange format can be chosen when a real cross-node/use case arrives.

## Closure verdict

Deep-audited for the pre-SQL decision horizon. This Book contributes evidence and constraints; it does not independently authorize schema or implementation changes.
