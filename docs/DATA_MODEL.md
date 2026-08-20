---
id: ACTAKIT-DATA-001
kind: conceptual-data-model
state: proposed-for-acceptance
created: 2026-08-20
authority: architecture-proposal
summary: Pre-SQL model for a small networked civic-record core with traceable claims, first-class connections, configurable review, queries, and output extensions.
related:
  - ACTAKIT-ARCH-001
  - ACTAKIT-CONTRACTS-001
  - ACTAKIT-IMPLEMENTATION-001
---

# Conceptual Data Model

## Purpose

This is the last conceptual layer before SQLite design. It deliberately does
**not** freeze final table names, indexes, JSON encoding, or module structure.
It freezes the distinctions that SQL must preserve.

```text
what was acquired
!= how it was represented
!= what civic document it is
!= what claims were extracted
!= whether a human reviewed them
!= how a query/output presents them
```

## Core Shape

The pre-SQL model distinguishes what is **core now**, what is **optional when a
fixture proves it**, and what belongs to the **horizon**. This document is not a
promise to create one SQL table per noun.

```text
Source -> AcquisitionObservation -> Artifact -> Representation
                                            |
                                            +-> CivicDocument

Claim -> ClaimRevision -> EvidenceLink -> Representation + typed locator
                         |
                         +-> ClaimEntityLink -> Entity
                         +-> TagAssignment -> Tag
                         +-> ClaimRelationRevision -> another ClaimRevision

ReviewDecision -> exact claim/relation revision(s) or reproducible subject set
```

`DocumentPart`, `CivicCollection`, specialized profiles, explicit correction
events, saved queries, output state, and richer acquisition-run machinery are
optional extensions justified by fixtures/use. `Episode` and `Hilo` are not core.

## Candidate Persistence Families

Final SQL may merge/split these after fixture/query tests.

### Core now

| Concern | Minimum durable meaning |
|---|---|
| source | stable source identity + bounded authority/acquisition configuration |
| acquisition observation | where/when/how a resource was observed or failed; resulting artifact if any |
| artifact | immutable digest, size/media, archive locator, custody/provenance |
| representation | parent, kind, digest/media, attributable generation provenance |
| civic document | stable civic identity/classification separate from representation |
| claim identity + revisions | proposition lineage, origin, lifecycle, attribution/time/flags |
| evidence link | exact claim revision -> representation locator + evidence relation |
| entity + observed names/identifiers | stable local retrieval anchor without name-equality merging |
| claim-entity link | exact claim revision -> entity + role/origin |
| tag + assignment | local topic vocabulary + attributable assignment |
| claim relation identity + revisions | exact claim-revision endpoints + type/origin/basis/lifecycle |
| review decision | exact revision(s)/reproducible set + actor/action/time/rationale as needed |

### Optional with a proving fixture/use case

| Concern | Add when |
|---|---|
| document source observations / anchors | one artifact contains multiple docs or source labels must be preserved independently |
| document parts | meaningful internal structure improves citation/query integrity |
| civic collections + memberships | expediente/package/case spans multiple documents |
| profile data | acta/report/budget semantics need validated specialized fields |
| explicit processing-run record | one execution produces many outputs or replay/audit needs shared run identity |
| entity merge/split event | identity reconciliation must preserve a decision/history |
| explicit correction event | retraction/redaction/public correction/unlinking itself matters |
| batch review record | compact subject-set representation cannot be reconstructed cleanly from decisions alone |
| publication snapshot | deliberate release needs reproducible immutable history |

### Horizon, not first-schema requirements

```text
universal operation receipts
saved-query canonical objects
output package registry / install lifecycle
universal OutputType/OutputInstance/OutputState tables
graph nodes/edges/triples
vector index as authority
multi-tenant accounts/roles
federation/peer synchronization
```

Hashes, idempotency keys, stale-write guards, and cached “current revision”
pointers are implementation tools added where tests show they are needed; they
are not mandatory fields on every canonical record.

## What Is Deliberately Not a Core Table

Do not create universal core tables merely because the current acta workflow
uses these concepts:

```text
episode
Hilo
announcement board
weekly digest
agreement tracker
```

They are Output Type concepts unless a future cross-output requirement proves
otherwise.

Likewise, do not start with universal graph-node/edge/triple tables or universal
tables for every date, amount, office, legal reference, or geographic object. Promote structured fields only when real
queries or integrity constraints need them.

## Document Typing

Typing remains independent from representation:

```text
source_supplied_type
normalized_type
profile_schema
```

Example:

```yaml
source_supplied_type: "Informe especial"
normalized_type: informe
subtype: auditoria
profile_schema: informe:v1
type_basis: machine_then_human | machine | human
```

`unknown` is allowed before classification. `otro` is allowed indefinitely when
that is the most honest broad type.

`expediente` and similar case/package concepts begin as collection kinds, not
forced document types.

## Networked Fichero

The Fichero is graph-shaped, but the baseline SQL should stay explicit and
relational. There are two intentionally different connection mechanisms.

### Shared anchors

```text
claim_revision -> claim_entity_link -> entity
claim_revision -> tag_assignment -> tag
```

These allow broad retrieval without creating an edge between every pair of
claims that mention the same place, project, institution, or topic.

### Direct claim relations

```text
claim_revision A -> claim_relation -> claim_revision B
```

The relation is itself versioned civic metadata and records: exact endpoint
revisions, relation type, machine/rule/human origin, process when applicable,
basis kind, exact basis references/rationale when any, lifecycle status, and
human review decisions when any.

The same review machinery can target a claim relation revision; machine-only is
a valid relation review state.

A claim edit does not silently retarget existing relation endpoints. If a new
revision changes the proposition enough to change a relationship, a new/revised
ClaimRelation is created deliberately.

Machine-only relations are allowed in supervised mode and are filterable just
like machine-only claims. Shared anchors and direct relations therefore provide
useful structure without pretending automation is human confirmation.

Do **not** begin with one generic `nodes`/`edges` or RDF-style triple table. Typed
relational tables provide stronger invariants and simpler code for the known
core. If future traversal workloads justify a specialized graph index/engine, it
can be derived from these canonical records rather than becoming a second source
of truth.

## Claim Data

Claim identity and claim revision are separate. SQL does not need a mandatory
mutable `current_revision` pointer if the current revision can be derived
unambiguously from lineage; such a pointer may be added later as an optimization.

```text
clm_123@1  machine extracted, active
clm_123@2  corrected wording, supersedes @1
```

A revision carries origin/process provenance, lifecycle, attribution/temporal
scope, and flags. Human review is derived from `review_decisions`; it is not
required to insert/search the revision.

Optional human assessment is separate from lifecycle/review and is only stored
when a workflow actually records such a judgment.

## Evidence Locator Storage

Do not create columns `page`, `article`, `item` on every evidence link.
Store a validated locator payload under a typed/versioned contract.

Likely shape:

```text
evidence_links
  claim_revision
  representation_id
  relation
  locator_kind
  locator_version
  locator_payload
  document_id?
  document_part_id?
```

Validation happens in the semantic core before persistence.

## Source Authority Storage

The baseline needs bounded authority scope attached to the source/configuration
or acquisition context, for example:

```text
formal_record
recorded_speech
publisher_statement
reported_observation
structured_value
```

Do not reduce this to a trust score and do not require a standalone versioned
source-policy table until adapters or policy-history requirements justify one.

## Review Modes in Data

### Strict

Protected use queries only exact revisions satisfying required human review.

### Batch

One decision may cover a reproducible deterministic set of exact revisions plus
exceptions. SQL may represent this with a compact set fingerprint/membership
record or individual decisions; do not precommit to a heavyweight batch model.

### Supervised

No synthetic approval is written. Unreviewed machine/rule material remains
searchable until a real human decision exists.

This distinction is important: **absence of review is data, not an error**.

## Queries and Search

SQLite should initially support ordinary deterministic retrieval:

- full-text claim/document search;
- indexes for dates, document type, source, lifecycle/review visibility;
- entity and tag joins;
- direct claim-relation lookup;
- bounded recursive traversal over explicit claim relations;
- evidence resolution.

Queries are ephemeral by default. Saved-query persistence is added only if real
operator workflows require durable identity/versioning. Vector/semantic search
is horizon work and never canonical authority.

## Output Boundary

The core exposes a bounded read/query interface. Output code may own local
validated presentation/curation state but cannot update core civic tables
silently.

The first schema does not need universal tables for output packages/instances/
state. The first proof is:

```text
same Fichero/read model
  -> Hilo output (may define Episode internally)
  -> tiny structurally different non-Episode output/fixture
```

If later outputs need durable configured state, add namespaced output persistence
without making presentation state evidence authority.

## Single-Operator-First Storage

The baseline assumes one writer/operator process at a time, occasionally two
humans in the organization. SQLite and an in-process core writer are sufficient.

Stable civic IDs/revision lineage are preserved now. Universal operation IDs,
distributed locks, multi-tenant accounts, and peer synchronization are not
required. A later daemon/concurrent-client layer can add stale-write/idempotency
controls at its boundary without rewriting civic history.

## Pre-SQL Questions That Must Be Answered

Before migration `0001`, prove with realistic fixtures:

1. PDF acta, spreadsheet budget, HTML notice, and unknown document use the same
   evidence/claim core without invented structure.
2. One concatenated artifact can map to multiple civic documents without byte
   duplication.
3. Hundreds of machine-only claims can be stored/searched under supervised mode.
4. One batch action can cover a deterministic set with exceptions without
   requiring claim-by-claim busywork or a heavyweight batch subsystem.
5. Source authority limitations are representable without a trust score/policy
   engine.
6. Many claims can share one entity/tag without pairwise-edge explosion.
7. Entity aliases/strong identifiers work, and an identity merge/split can
   preserve history without silent mass rewrite.
8. An active claim relation always has exact endpoints, attributable origin, and
   an inspectable basis; candidates can remain unreviewed.
9. Claim correction does not silently retarget an old relation.
10. SQLite can retrieve a bounded multi-step explicit relation chain without a
    graph database.
11. Evidence `challenges` and claim `contradicts` remain unambiguous in queries/UI.
12. Hilo can define Episodes outside core, and a tiny non-Episode output can use
    the same read model.
13. Backup/restore verifies database + archive + relation/evidence consistency.

Only after these pass should final SQL tables, constraints, indexes, cached
current pointers, idempotency keys, or record hashes be reviewed and accepted.
