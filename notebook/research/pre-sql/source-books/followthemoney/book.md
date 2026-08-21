---
id: ACTAKIT-BOOK-FOLLOWTHEMONEY-DEEP-001
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

# FollowTheMoney

## Question

How should investigative entities and rich relationships be represented?

## Deep-audit basis

Operational investigative schema explicitly documents graph-model traps and statement provenance tradeoffs.

## Evidence horizon

- **AKS-S019 — FollowTheMoney:** Relationship with attributes becomes interstitial entity; explicit warning against naive node/edge mapping
- **AKS-S020 — FollowTheMoney Statements:** Per-property value provenance and original value; statement-level representation
- **AKS-S077 — FollowTheMoney schema extension principles:** Schema extensions are justified by practical precision needs and explicitly reject modelling every theoretical distinction
- **AKS-S078 — FollowTheMoney schema API reference:** Schema definitions are explicit typed structures with inheritance and validation metadata

## Claim ledger synopsis

- **AKS-C019:** Naively equating every real relation with an edge is known to fail when relations themselves carry data. **ActaKit:** No universal nodes/edges schema; explicit tables plus optional association objects.
- **AKS-C020:** Per-value provenance is possible but materially increases record count and model complexity. **ActaKit:** Do not adopt statement-per-field provenance unless fixtures show claim-level provenance is insufficient.
- **AKS-C100:** Treating every relation as a generic edge is explicitly identified as a modeling error when interstitial entities carry attributes. **ActaKit:** Use ClaimRelation for simple semantics and Association/Event for relations with role/time/amount/other own attributes.
- **AKS-C101:** Per-value provenance is powerful but turns normalized values into many statement records. **ActaKit:** Use claim/evidence provenance as default; introduce finer-grained value provenance only for demonstrated high-value fields.
- **AKS-C102:** FollowTheMoney explicitly frames schema extensions around practical precision rather than modelling domain theory completely. **ActaKit:** Version extensible civic profiles; do not build a national civic ontology in core.

## Bounded transfer

Simple relations stay edges; attribute-rich relations become interstitial association entities.

## Do not copy

Do not adopt generic node/edge storage or statement-per-field provenance by default.

## Schema pressure / expensive mistake avoided

Provide relational tables for core entities/links and a typed rich-association extension point.

## Residual risk

Exact rich-association families should be fixture-driven, not pre-enumerated.

## Closure verdict

Deep-audited for the pre-SQL decision horizon. This Book contributes evidence and constraints; it does not independently authorize schema or implementation changes.
