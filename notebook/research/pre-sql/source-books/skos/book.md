---
id: ACTAKIT-BOOK-SKOS-DEEP-001
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

# SKOS

## Question

How should tags/taxonomies evolve without materializing graph closure?

## Deep-audit basis

W3C vocabulary distinguishes direct broader/narrower links from transitive closure and supports labels/aliases.

## Evidence horizon

- **AKS-S031 — SKOS Reference:** ConceptScheme, Concept, preferred/alternative labels, broader/narrower/mapping relations
- **AKS-S096 — SKOS Primer:** Explains preferred/alternate labels, direct hierarchy semantics, transitive closure and extension choices with practical examples

## Claim ledger synopsis

- **AKS-C033:** Taxonomies can support preferred/alternate labels and hierarchy without forcing one global vocabulary. **ActaKit:** Local tags can later adopt SKOS-like semantics; no national topic ontology baseline.
- **AKS-C057:** Aliases and hierarchy are useful when taxonomies mature, but flat tags remain a valid starting point. **ActaKit:** Do not build SKOS-like concept tables until local taxonomy needs them.
- **AKS-C129:** SKOS explicitly separates asserted direct hierarchy from optional transitive closure and warns that more advanced collections add application complexity. **ActaKit:** If ActaKit grows hierarchical tags, persist direct links and compute closure; add collections only for demonstrated taxonomy needs.

## Bounded transfer

Keep flat/local tags initially; if hierarchy appears, persist direct edges and derive closure at query time.

## Do not copy

Do not impose a national SKOS/RDF taxonomy.

## Schema pressure / expensive mistake avoided

No transitive edge materialization; aliases/hierarchy can be optional extension tables.

## Residual risk

Taxonomy governance is local and may remain simple indefinitely.

## Closure verdict

Deep-audited for the pre-SQL decision horizon. This Book contributes evidence and constraints; it does not independently authorize schema or implementation changes.
