---
id: ACTAKIT-BOOK-POPOLO-DEEP-001
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

# Popolo

## Question

Which civic relationship shapes are genuinely reusable?

## Deep-audit basis

Small civic schema demonstrates Person/Org/Post/Membership/Motion/Vote patterns.

## Evidence horizon

- **AKS-S015 — Popolo specification:** Small/flexible civic models; Person, Organization, Membership, Post, Motion, VoteEvent, Event; uncertain data tolerated
- **AKS-S071 — Popolo project principles/specification:** Models Person, Organization, Membership, Post, Motion, Vote and related civic records with intentionally small reusable structures

## Claim ledger synopsis

- **AKS-C014:** Civic models benefit from being small, extensible and tolerant of imprecise information. **ActaKit:** Profiles and local extensions should be bounded; unknown remains valid.
- **AKS-C093:** Membership/Post demonstrate that civic relationships with role and time often deserve their own record rather than a bare edge. **ActaKit:** Provide a promotion path for rich associations, but only instantiate it for real domain needs.

## Bounded transfer

Borrow relation-promotion intuition for time/role-bearing memberships/posts.

## Do not copy

Do not make Popolo the national/domain ontology for ActaKit.

## Schema pressure / expensive mistake avoided

Association/Event escape hatch should support role/time/party fields when required.

## Residual risk

Country-specific civic records will need local profiles and raw labels.

## Closure verdict

Deep-audited for the pre-SQL decision horizon. This Book contributes evidence and constraints; it does not independently authorize schema or implementation changes.
