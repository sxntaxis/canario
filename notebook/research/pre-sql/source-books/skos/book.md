---
id: ACTAKIT-BOOK-SKOS-001
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

# SKOS — taxonomy semantics without a mandatory ontology

## Question

What taxonomy features are worth preserving if local tags later need aliases or hierarchy?

## Evidence horizon

- **AKS-S031 — SKOS Reference:** ConceptScheme, Concept, preferred/alternative labels, broader/narrower/mapping relations

## Source-backed findings

- **AKS-C033:** Taxonomies can support preferred/alternate labels and hierarchy without forcing one global vocabulary.
- **AKS-C057:** Aliases and hierarchy are useful when taxonomies mature, but flat tags remain a valid starting point.

## ActaKit pressure

- **AKS-C033:** Local tags can later adopt SKOS-like semantics; no national topic ontology baseline.
- **AKS-C057:** Do not build SKOS-like concept tables until local taxonomy needs them.

## Boundaries / do not cargo-cult

- **AKS-S031:** Local tags need not become RDF or a national ontology

## Disposition

This Book is evidence for the transversal synthesis. It does not independently authorize an architecture or implementation change.
