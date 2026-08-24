---
id: ACTAKIT-AKF-013-ARTIFACT-PROOF-001
type: semantic-fixture-artifact-proof
state: pass
authority: evidence
created: 2026-08-21
fixture: AKF-013
---

# AKF-013 real civic proof — office-holder relation

## Public artifact

Primary source: Tribunal Supremo de Elecciones, resolución **2160-E11-2024**, 8
March 2024:

- https://www.tse.go.cr/juris/relevantes/2160-E11-2024.html

Corroborating institutional surface:

- https://www.muniesparza.go.cr/articulo/232/alcaldia-municipal

## Observed civic fact shape

The TSE declaration establishes one relationship with attributes that belong to
the relationship itself, not merely to either endpoint:

```text
subject: Bienvenido Venegas Porras
organization: Municipalidad de Esparza
role: Alcalde
valid_from: 2024-05-01
valid_to: 2028-04-30
basis: official TSE election declaration
```

The resolution's heading and dispositive section define the municipal term from
1 May 2024 through 30 April 2028; its Esparza section declares Bienvenido Venegas
Porras elected Alcalde. The municipal Alcaldía page independently identifies the
2024–2028 administration.

## What this proves

A pairwise Entity anchor cannot own `role + valid_from + valid_to + evidence`
without hiding relationship semantics. A plain ClaimRelation is also the wrong
owner because its endpoints are ClaimRevisions, while this fact relates civic
Entities directly and has its own temporal scope.

Therefore `RoleAssignment` is not speculative horizon modeling. One concrete
real civic record already requires the typed family in the first candidate.

## What this does not prove

- It does not justify a generic Association/Event table.
- It does not prove amount-bearing, ownership, vote-participation, or procurement
  relationship families.
- It does not certify the final HTML/PDF selector/parser implementation. That
  remains part of the exact RepresentationTarget artifact proof gate.
