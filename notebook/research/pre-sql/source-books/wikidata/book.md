---
id: ACTAKIT-BOOK-WIKIDATA-DEEP-001
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

# Wikidata

## Question

How should sourced claims, conflicts and identity corrections coexist?

## Deep-audit basis

Large operational knowledge base with explicit statement/reference/qualifier/rank and merge/redirect procedures.

## Evidence horizon

- **AKS-S017 — Wikidata Statements:** Statement = property/value plus optional qualifiers, references, ranks; supports conflicting sourced values
- **AKS-S018 — Wikidata Qualifiers / Data Model:** Temporal/jurisdiction/method qualifiers contextualize assertions; restrictive qualifiers change meaning
- **AKS-S073 — Wikidata merge guidance:** Requires certainty before merge, redirects obsolete IDs and forbids reuse of merged identifiers
- **AKS-S074 — Wikidata redirect guidance:** Redirects preserve references and allow merge reversibility; merged IDs are not repurposed
- **AKS-S075 — Wikidata qualifiers guidance:** Qualifiers encode time, method, scope and other context when a simple property/value is insufficient
- **AKS-S076 — Wikidata ranking guidance:** Separates reference/source from preferred/current consensus rank and permits multiple sourced values

## Claim ledger synopsis

- **AKS-C016:** Sourced knowledge systems can preserve multiple conflicting assertions and contextual qualifiers without choosing a single truth. **ActaKit:** ActaKit should store source-bounded claims and contradictions, not a universal truth value.
- **AKS-C018:** Some qualifiers are meaning-changing, especially time, jurisdiction and scope. **ActaKit:** Pre-SQL fixtures must test whether claim scope needs explicit structured qualifiers, but avoid a universal qualifier graph.
- **AKS-C054:** A claim should remain meaningful and verifiable even when machine-readable context is absent. **ActaKit:** Structured qualifiers/enrichments should augment rather than define the proposition.
- **AKS-C096:** A sourced knowledge system may legitimately preserve multiple contradictory values and explicitly states that references identify sources rather than world truth. **ActaKit:** Do not collapse contradictory civic claims into one current truth row; preserve source-bounded assertions and relations.
- **AKS-C097:** Merge requires strong identity confidence and obsolete identifiers are redirected rather than reused. **ActaKit:** Entity merges must preserve lineage/tombstone mapping and never recycle old local IDs.
- **AKS-C098:** Time, method and scope can materially qualify an assertion without requiring the assertion itself to disappear. **ActaKit:** Allow a bounded structured scope/qualifier mechanism when fixtures prove it changes claim meaning; do not universalize Wikidata snaks.
- **AKS-C099:** Source references and preferred/current consensus are separate concepts. **ActaKit:** Review/assessment must not be encoded as provenance or source strength.

## Bounded transfer

Preserve multiple sourced contradictory claims; separate source/reference from assessment; retain merge lineage and never reuse IDs.

## Do not copy

Do not atomize ActaKit into Wikidata property/snaks or implement consensus ranks.

## Schema pressure / expensive mistake avoided

Claim revisions/relations and Entity reconciliation need independent lineage; unknown differs from absence.

## Residual risk

Wikidata community governance is not transferable to a 1–2 operator canton node.

## Closure verdict

Deep-audited for the pre-SQL decision horizon. This Book contributes evidence and constraints; it does not independently authorize schema or implementation changes.
