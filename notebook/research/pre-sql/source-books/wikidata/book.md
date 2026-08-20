---
id: ACTAKIT-BOOK-WIKIDATA-001
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

# Wikidata — sourced plural assertions and qualifiers

## Question

How can conflicting sourced assertions coexist without forcing ActaKit into atomic triples?

## Evidence horizon

- **AKS-S017 — Wikidata Statements:** Statement = property/value plus optional qualifiers, references, ranks; supports conflicting sourced values
- **AKS-S018 — Wikidata Qualifiers / Data Model:** Temporal/jurisdiction/method qualifiers contextualize assertions; restrictive qualifiers change meaning

## Source-backed findings

- **AKS-C016:** Sourced knowledge systems can preserve multiple conflicting assertions and contextual qualifiers without choosing a single truth.
- **AKS-C018:** Some qualifiers are meaning-changing, especially time, jurisdiction and scope.
- **AKS-C054:** A claim should remain meaningful and verifiable even when machine-readable context is absent.

## ActaKit pressure

- **AKS-C016:** ActaKit should store source-bounded claims and contradictions, not a universal truth value.
- **AKS-C018:** Pre-SQL fixtures must test whether claim scope needs explicit structured qualifiers, but avoid a universal qualifier graph.
- **AKS-C054:** Structured qualifiers/enrichments should augment rather than define the proposition.

## Boundaries / do not cargo-cult

- **AKS-S017:** ActaKit claims should not collapse into atomic property/value statements
- **AKS-S018:** Universal qualifier graph would make ActaKit harder to explain

## Disposition

This Book is evidence for the transversal synthesis. It does not independently authorize an architecture or implementation change.
