---
id: ACTAKIT-BOOK-IIIF-DEEP-001
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

# IIIF

## Question

How should image/page/spatial/temporal evidence targeting be represented?

## Deep-audit basis

Presentation and Image APIs reuse Web Annotation selectors and document coordinate/compliance implementation differences.

## Evidence horizon

- **AKS-S033 — IIIF Presentation API 3.0:** Canvas/Range structures and Web Annotation selectors for page, spatial and temporal targeting
- **AKS-S080 — IIIF Image API 3.0:** Defines explicit pixel/percentage regions and coordinate origin for image targeting
- **AKS-S081 — IIIF Image API implementation notes:** Documents implementation-dependent rounding and edge-tile calculations
- **AKS-S082 — IIIF Image API compliance levels:** Servers can legitimately support different selector/region capabilities by compliance level

## Claim ledger synopsis

- **AKS-C104:** A stable canvas can provide a spatial/temporal reference frame while annotations target specific regions or time spans. **ActaKit:** Evidence locators should target a specific Representation plus a typed spatial/temporal selector.
- **AKS-C105:** Coordinate/size rounding and edge tiles have implementation-dependent behavior. **ActaKit:** Persist selector scheme/version and sufficient context; do not assume derived pixel coordinates survive every rendering pipeline.
- **AKS-C106:** Different compliant services may support different targeting capabilities. **ActaKit:** Representation adapters must advertise capabilities; unsupported selectors degrade explicitly rather than being guessed.

## Bounded transfer

Representation-scoped typed spatial/temporal locators with explicit coordinate/version semantics.

## Do not copy

Do not require IIIF server/JSON-LD or assume all capabilities.

## Schema pressure / expensive mistake avoided

Locator payloads need media-specific schema/version and adapter capability flags.

## Residual risk

PDF/image coordinate transformations may still require local normalization tests.

## Closure verdict

Deep-audited for the pre-SQL decision horizon. This Book contributes evidence and constraints; it does not independently authorize schema or implementation changes.
