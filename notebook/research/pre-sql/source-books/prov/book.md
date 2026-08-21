---
id: ACTAKIT-BOOK-PROV-DEEP-001
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

# W3C PROV

## Question

Which provenance distinctions are worth preserving?

## Deep-audit basis

Normative model plus implementation report shows real interoperability while keeping provenance separate from truth.

## Evidence horizon

- **AKS-S006 — PROV-O:** Entity/Activity/Agent; derivation, generation, attribution, association, revision, primary source
- **AKS-S057 — PROV implementation report:** Documents independent PROV implementations and interoperability experience

## Claim ledger synopsis

- **AKS-C004:** Provenance commonly distinguishes entities, activities and agents and links derivation/generation/attribution explicitly. **ActaKit:** Map ActaKit provenance vocabulary to PROV semantics without implementing PROV-O storage.
- **AKS-C076:** PROV semantics were exercised by multiple independent implementations and interchange tests. **ActaKit:** Borrow stable provenance distinctions, but validate an ActaKit relational mapping rather than importing PROV-O.
- **AKS-C077:** Provenance describes derivation/generation/attribution; it does not certify the truth of the generated entity. **ActaKit:** Keep provenance separate from review/assessment/truth semantics.

## Bounded transfer

Borrow Entity/Activity/Agent and derivation/attribution semantics selectively.

## Do not copy

Do not implement PROV-O/RDF globally or make every operation canonical.

## Schema pressure / expensive mistake avoided

Schema needs provenance for consequential derivation/acquisition/review actors without universal event sourcing.

## Residual risk

Exact granularity of process-run persistence remains an implementation tuning problem.

## Closure verdict

Deep-audited for the pre-SQL decision horizon. This Book contributes evidence and constraints; it does not independently authorize schema or implementation changes.
