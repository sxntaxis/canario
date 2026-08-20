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

```text
Source -> SourceRun -> SourceCapture -> Artifact -> Representation
                                         |
                                         +-> CivicDocument

CivicDocument -> optional DocumentPart
CivicCollection -> Membership -> CivicDocument

Claim -> ClaimRevision -> EvidenceLink -> Representation + typed locator
  |          |                |
  |          |                +-> optional Document/Part context
  |          +-> ClaimEntityLink -> Entity
  |          +-> tag assignments
  |          +-> ClaimRelation -> another ClaimRevision
  +-> review decisions/batches

SavedQuery -> selected read model -> OutputInstance -> Export/Snapshot
```

`Episode` and `Hilo` are not core tables. They belong to the Hilo Output Type.

## Likely Table Families

The final SQL may merge or split these after concrete query tests.

| Family | Important fields | Why |
|---|---|---|
| `sources` | source ID, display identity, authority class | Stable source family identity |
| `source_policies` | source, revision, acquisition rules, authority scopes, retention/privacy | What may be acquired and what it can demonstrate |
| `source_runs` | run ID, policy revision, scope/checkpoint, outcome, times | One bounded inspection |
| `source_captures` | run, resource locator/URI, supplied metadata, time, artifact/failure | Exact acquisition provenance |
| `artifacts` | digest, bytes, media type, archive locator, custody state | Immutable evidence bytes |
| `representations` | parent, kind, digest, media, process, quality | Text/OCR/table/transcript/etc. |
| `process_runs` | inputs/hashes, executor/model/config, outputs, diagnostics | Replaceable/attributable Lector work |
| `civic_documents` | identity, issuer, normalized type, subtype/profile, date/language, revision | Civic meaning independent of format |
| `document_source_observations` | capture + supplied title/type/id/date | Preserve what each source called it |
| `document_profile_data` | document + profile schema + validated payload | Specialized semantics without table explosion |
| `document_anchors` | document + representation + typed locator | One artifact may contain multiple documents |
| `document_parts` | document, parent part, kind/title/order | Optional meaningful internal structure |
| `document_part_anchors` | part + representation + typed locator | Exact part location |
| `civic_collections` | collection ID, kind, identity/context, revision | Multi-document expediente/package/case |
| `collection_memberships` | collection + document + relation/order | Membership without pretending collection is one file |
| `claims` | stable claim ID + current revision/status pointer | Identity across correction |
| `claim_revisions` | text, kind, origin, attribution, temporal scope, flags, epistemic state, hash | Durable proposition history |
| `evidence_links` | claim revision, relation, representation, locator, optional document/part | Exact provenance |
| `entities` | entity ID, class, canonical/display identity, lifecycle | Retrieval-relevant shared anchors |
| `entity_aliases` / source observations | entity + label/context/source/process | Preserve names and identity resolution provenance |
| `claim_entity_links` | exact claim revision + entity + role/relation + origin/review | Durable claim/entity anchoring |
| `tags` | local tag identity, taxonomy/version, lifecycle | Local/shared topic vocabulary |
| `tag_assignments` | subject + tag + origin/process + review metadata if needed | Search classification |
| `claim_relations` | stable relation ID/revision, exact from/to claim revisions, typed relation, origin, basis kind, status | First-class proposition-to-proposition memory |
| `claim_relation_bases` | relation revision + exact claim/evidence refs + optional rationale | Inspectable reason/evidence for a connection |
| `review_policies` | scope, mode, triggers, revision | strict/batch/supervised behavior |
| `review_batches` | deterministic subject set/hash, policy revision, actor/outcome | One action over many claims |
| `review_decisions` | exact subject/batch, action, actor, rationale/time | Human supervision trail |
| `explicit_corrections` | target/prior/new state, kind, reason, actor | Only corrections that matter as events |
| `saved_queries` | definition/version/parameters/access | Reusable read filters |
| `output_types` | installed type/version/manifest/schema/capabilities | Extensible output definition |
| `output_instances` | type/version + local configuration | Configured use of an Output Type |
| `output_state` | instance + validated namespaced derived/curated state | Output-specific state without core pollution |
| `output_snapshots` | exact inputs/type/version/config/output hashes/publication state | Rebuildable/citable release state |
| `operation_receipts` | operation ID, request hash, result, actor | Replay safety/audit |

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

A claim's identity and review are separate.

```text
claims
  clm_123 -> current revision 3

claim_revisions
  clm_123@1  machine extracted
  clm_123@2  corrected wording
  clm_123@3  current
```

A revision carries origin/process and epistemic state. Human review is derived
from `review_decisions`; it is not required to insert the revision.

This allows high-volume supervised extraction without losing provenance:

```text
machine-only active claim
human-reviewed active claim
rejected claim retained for audit
superseded claim retained for history
```

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

A source policy may define one or more bounded authority scopes such as:

```text
formal_record
recorded_speech
publisher_statement
reported_observation
structured_value
```

Do not reduce this to a single trust score. EvidenceLink validation can check
whether claim wording/kind is compatible with the declared scope when policy
requires it.

## Review Modes in Data

### Strict

Claim may exist, but protected downstream uses query only claims satisfying the
required human review decision.

### Batch

`review_batches` stores an ordered/deterministic set of exact revisions and a
set hash. Batch outcome applies to that set; per-claim exceptions override it.

### Supervised

No synthetic approval is written. Machine-only claims remain machine-only until
a real human decision exists.

This distinction is important: **absence of review is data, not an error**.

## Queries and Search

SQLite should initially support ordinary deterministic retrieval before adding
specialized search infrastructure. Likely needs:

- full-text claim/document search;
- indexes for dates, document type, source, status/review level;
- entity and tag joins;
- direct claim-relation lookup;
- bounded recursive traversal over claim relations when useful;
- evidence resolution;
- saved query definitions.

Vector/semantic search is horizon work. The model must not depend on it.

## Output Type Boundary

Output code receives a bounded read/query interface, not database credentials.
An output can own validated namespaced state but cannot update core civic tables.

Example:

```text
OutputType: hilo:v1
OutputInstance: "Water governance"
OutputState:
  episodes
  episode membership/order
  curated reader summaries
```

Those rows/payloads are **presentation state**, not evidence authority.
Deleting the output state loses presentation curation but not the claims and
citations it references.

Output package sharing later requires stable manifest/schema/version identity,
not a shared database schema between cantons.

## Single-Operator-First Storage

The baseline assumes one operator process at a time, occasionally two humans in
the organization. SQLite and an in-process/core writer are therefore sufficient.

The schema still uses stable revisions and operation IDs so a later daemon or
concurrent client layer does not require rewriting civic history.

No multi-tenant account model, distributed lock service, or peer synchronization
belongs in the first schema.

## Pre-SQL Questions That Must Be Answered

Before writing migration `0001`, prove with realistic fixtures:

1. Can a PDF acta, spreadsheet budget, HTML notice, and unknown document all be
   preserved and cited using the same core relationships?
2. Can one concatenated PDF map to two documents without byte duplication?
3. Can supervised extraction store hundreds of machine-only claims efficiently?
4. Can a batch review cover a deterministic set without manufacturing hundreds
   of redundant approval rows unless needed?
5. Can source authority limitations be represented without a trust-score system?
6. Can hundreds of claims share one entity/tag anchor without pairwise-edge
   explosion?
7. Can an explicit claim relation preserve exact revision endpoints, origin,
   inspectable basis, lifecycle and review state?
8. Can a claim correction occur without silently retargeting an old relation?
9. Can SQLite retrieve a bounded multi-step relation chain without a graph database?
10. Can entity/tag retrieval work without a universal ontology?
11. Can a saved query feed two different outputs?
12. Can a Hilo output define Episodes without any `episodes` core table?
13. Can output state be deleted/rebuilt without touching evidence/claims?
14. Can backup/restore verify database + archive + connection consistency?

Only after these pass should final SQL table names, constraints, and indexes be
reviewed and accepted.
