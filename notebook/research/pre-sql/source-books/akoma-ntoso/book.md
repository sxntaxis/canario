---
id: ACTAKIT-BOOK-AKOMA_NTOSO-DEEP-001
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

# Akoma Ntoso

## Question

How should civic-document identity, versions and parts remain stable?

## Deep-audit basis

OASIS standard/naming convention plus 2025 evolution after adoption.

## Evidence horizon

- **AKS-S012 — Akoma Ntoso 1.0:** Work/expression/manifestation-style legal-document identity, components, persistent references, metadata
- **AKS-S065 — Akoma Ntoso Naming Convention 1.0:** Defines persistent versus expression-level identifiers and the proportionality-of-impact principle for rare cases
- **AKS-S066 — Akoma Ntoso 3.1 public-review announcement:** Reports incremental refinement after broad adoption to cover practical implementation and interoperability needs

## Claim ledger synopsis

- **AKS-C012:** Components/subdocuments can be modeled when structure matters without forcing every document into maximal decomposition. **ActaKit:** DocumentPart stays optional.
- **AKS-C086:** Stable identity of a document part can differ from its current display number/name across versions. **ActaKit:** Never use article number, filename or title as the stable primary identity of a mutable civic/document part.
- **AKS-C087:** Akoma Ntoso explicitly applies proportionality of impact: rare cases should not complicate frequent cases. **ActaKit:** Keep DocumentPart/Collection/profile machinery optional and pay complexity only when a fixture requires it.
- **AKS-C088:** A mature legal-document vocabulary continued evolving after adoption in response to implementation and interoperability needs. **ActaKit:** Version document profiles/locators so ActaKit can evolve without treating the first profile set as final ontology.

## Bounded transfer

Stable document identity separate from expression/manifestation/display numbering; optional parts/collections; proportional complexity.

## Do not copy

Do not import XML/FRBR/IRI vocabulary wholesale.

## Schema pressure / expensive mistake avoided

Document/Artifact/Representation/Part identities must be separate and version-aware.

## Residual risk

ActaKit covers broader civic records than legislative text, so profiles must remain optional.

## Closure verdict

Deep-audited for the pre-SQL decision horizon. This Book contributes evidence and constraints; it does not independently authorize schema or implementation changes.
