---
id: ACTAKIT-BOOK-W3C_ORG-DEEP-001
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

# W3C ORG

## Question

What is the minimum reusable organization/membership vocabulary?

## Deep-audit basis

Normative generic model plus evolution diff around Post/change/provenance.

## Evidence horizon

- **AKS-S016 — W3C Organization Ontology:** Simple memberOf shortcut vs first-class Membership/Post when role/time matters
- **AKS-S072 — W3C ORG change diff:** Shows evolution around Post, organizational change and PROV alignment after implementation feedback

## Claim ledger synopsis

- **AKS-C094:** Organization, Role, Membership and Post are reusable primitives but the vocabulary is not a complete accountability model. **ActaKit:** Use small local Entity kinds/associations and extend only when needed; do not import a full RDF organizational ontology.
- **AKS-C095:** The standard itself evolved around Post and change/provenance modeling, showing generic membership abstractions need domain refinement. **ActaKit:** Keep role/post/association semantics versioned/extensible rather than freezing one civic relationship schema.

## Bounded transfer

Use Organization/Role/Post/Membership as design references, not compulsory storage classes.

## Do not copy

Do not import RDF ontology or assume it captures civic accountability.

## Schema pressure / expensive mistake avoided

Entity kinds and association records need extension/version boundaries.

## Residual risk

Organization semantics vary across public bodies; source identifiers remain important.

## Closure verdict

Deep-audited for the pre-SQL decision horizon. This Book contributes evidence and constraints; it does not independently authorize schema or implementation changes.
