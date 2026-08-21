---
id: ACTAKIT-BOOK-WEB_ANNOTATION-DEEP-001
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

# W3C Web Annotation

## Question

How should a durable evidence link identify an exact segment of a representation?

## Deep-audit basis

Normative W3C model plus interoperable protocol; selectors are intentionally media-specific and can be redundant.

## Evidence horizon

- **AKS-S004 — W3C Web Annotation Data Model:** SpecificResource, Selector, State; simple-to-complex annotation model; non-graph implementation explicitly viable
- **AKS-S005 — W3C Selectors and States / Annotation model selector sections:** TextQuote exact/prefix/suffix, position/fragment/range/media selectors, state of resource
- **AKS-S056 — Web Annotation Protocol:** Shows the annotation data model was intended for interoperable implementations, not a mandatory graph database runtime

## Claim ledger synopsis

- **AKS-C001:** Web Annotation is intentionally capable of rich graph-shaped annotation while permitting performant non-graph implementations. **ActaKit:** Keep ActaKit graph-shaped but relational; no graph DB baseline.
- **AKS-C002:** Evidence targeting should separate the resource from the selector that identifies the exact segment and, when needed, the state/version of that resource. **ActaKit:** Refine EvidenceLink into representation + typed selector bundle + state anchor.
- **AKS-C003:** Redundant selectors can make a citation more durable than one coordinate system alone. **ActaKit:** For text/PDF, allow exact quote plus structural/page/offset context instead of one brittle locator.
- **AKS-C074:** TextQuoteSelector and TextPositionSelector solve different durability problems and can be combined/refined. **ActaKit:** EvidenceLocator should allow typed redundant selectors rather than one universal coordinate field.
- **AKS-C075:** The annotation model is interoperable without requiring a graph-database storage topology. **ActaKit:** Represent connected evidence relationally; interoperability belongs at boundaries, not in storage technology.

## Bounded transfer

Representation target + typed selector(s) + optional state/version anchor.

## Do not copy

Do not import RDF/JSON-LD or graph storage as runtime requirements.

## Schema pressure / expensive mistake avoided

Evidence locator type/version should be explicit; text locators should support exact/context plus structural/offset coordinates.

## Residual risk

Locator durability still depends on quality/stability of the underlying representation.

## Closure verdict

Deep-audited for the pre-SQL decision horizon. This Book contributes evidence and constraints; it does not independently authorize schema or implementation changes.
