---
id: ACTAKIT-BOOK-RECORDS_IN_CONTEXTS-DEEP-001
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

# Records in Contexts / RiC-O

## Question

How far should a relational civic record model go toward rich context graphs?

## Deep-audit basis

Archival standard plus maintainer scars around n-ary relation complexity and inference bugs.

## Evidence horizon

- **AKS-S014 — Records in Contexts Conceptual Model / Ontology:** Records gain meaning through contextual relations; merge/split/context are explicit
- **AKS-S069 — RiC-O 1.1 repository and release history:** RiC-O 1.0.2 fixed an inconsistency caused by global reflexivity; 1.1 continued relation-model evolution
- **AKS-S070 — RiC-O issue #67: rolifying n-ary relation classes:** Maintainers describe 48 relation classes and many generated properties as difficult to maintain and discuss more abstract replacements

## Claim ledger synopsis

- **AKS-C013:** Archival context can be highly relational, but using an ontology runtime is not required to preserve contextual relations. **ActaKit:** Borrow relation semantics selectively; reject RiC-O/OWL baseline.
- **AKS-C091:** Rich archival relation modeling produced substantial property/class maintenance complexity and abstraction pressure. **ActaKit:** Keep simple typed relations simple; promote only relations with real attributes to association/event objects.
- **AKS-C092:** A stable ontology still required bug-fix releases for relation semantics after 1.0. **ActaKit:** Avoid ontology-wide inference rules as canonical ActaKit semantics; explicit relational invariants are easier to audit.

## Bounded transfer

Keep typed contextual relations and promote rich relations only when attributes justify it.

## Do not copy

Do not implement ontology-wide RDF/OWL reasoning or hundreds of generated relation properties.

## Schema pressure / expensive mistake avoided

Simple ClaimRelation plus bounded Association/Event promotion path.

## Residual risk

Some future archival exports may need richer mappings, but that is boundary interoperability.

## Closure verdict

Deep-audited for the pre-SQL decision horizon. This Book contributes evidence and constraints; it does not independently authorize schema or implementation changes.
