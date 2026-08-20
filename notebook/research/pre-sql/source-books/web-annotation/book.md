---
id: ACTAKIT-BOOK-WEB-ANNOTATION-001
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

# W3C Web Annotation — evidence targeting without inventing locators

## Question

How should a claim point back to the exact evidence segment without inventing a bespoke locator system?

## Evidence horizon

- **AKS-S004 — W3C Web Annotation Data Model:** SpecificResource, Selector, State; simple-to-complex annotation model; non-graph implementation explicitly viable
- **AKS-S005 — W3C Selectors and States / Annotation model selector sections:** TextQuote exact/prefix/suffix, position/fragment/range/media selectors, state of resource

## Source-backed findings

- **AKS-C001:** Web Annotation is intentionally capable of rich graph-shaped annotation while permitting performant non-graph implementations.
- **AKS-C002:** Evidence targeting should separate the resource from the selector that identifies the exact segment and, when needed, the state/version of that resource.
- **AKS-C003:** Redundant selectors can make a citation more durable than one coordinate system alone.

## ActaKit pressure

- **AKS-C001:** Keep ActaKit graph-shaped but relational; no graph DB baseline.
- **AKS-C002:** Refine EvidenceLink into representation + typed selector bundle + state anchor.
- **AKS-C003:** For text/PDF, allow exact quote plus structural/page/offset context instead of one brittle locator.

## Boundaries / do not cargo-cult

- **AKS-S004:** Do not import JSON-LD/RDF runtime merely to reuse selector semantics
- **AKS-S005:** ActaKit needs spreadsheet/JSON-specific bounded extensions

## Disposition

This Book is evidence for the transversal synthesis. It does not independently authorize an architecture or implementation change.
