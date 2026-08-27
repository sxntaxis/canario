---
id: ACTAKIT-DATA-001
kind: conceptual-data-model
state: accepted
accepted: 2026-08-21
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
Source -> AcquisitionObservation -> Artifact -> ArchiveObject
                                      \-> Representation
                                            |
                                            +-> CivicDocument

Claim -> ClaimRevision -> EvidenceLink -> Representation + typed locator
                         |
                         +-> EntityMention -> optional Entity resolution
                         +-> ClaimEntityLink -> Entity
                         +-> TagAssignment -> Tag
                         +-> ClaimRelationRevision -> another ClaimRevision

Entity -> append-only EntityReconciliation (merge/split lineage)

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
| archive object | physical content-addressed bytes, digest/size/storage key, availability |
| artifact | logical acquisition/custody identity pointing to physical bytes; validation/availability independent of digest |
| representation | original view of Artifact bytes or material derivative with own bytes + exact parent + attributable generation provenance |
| process run + exact inputs | terminal processor provenance plus ordered exact RepresentationTarget scope, including failed attempts |
| quality evidence | typed/namespaced processor-attributable runtime signals for one exact run target; no universal confidence |
| quality decision | ACCEPT/ESCALATE/QUARANTINE_REVIEW policy result separate from execution outcome, with policy/version/reason provenance |
| process egress | non-secret egress bytes/profile/template provenance for cloud/agent runs; credentials remain external |
| civic document identity + revisions | stable civic identity separate from representation; title/issuer/date/language corrections are revisioned |
| claim identity + revisions | proposition lineage, origin, lifecycle, attribution/time/flags |
| claim revision action | attributable human `correct/restrict/unrestrict/retract` source->result revision mutation + immutable request identity |
| evidence link | exact claim revision -> representation locator + evidence relation |
| entity mention | exact observed source text + representation/locator context + origin + optional resolution |
| entity + identifiers/aliases | stable local resolved retrieval anchor without name-equality merging |
| entity reconciliation | append-only merge/split lineage preserving old links and ambiguity |
| claim-entity link | append-only/superseding exact claim revision -> entity anchor, optional exact mention-resolution basis, role/origin/lifecycle/review |
| tag + assignment | local topic vocabulary + attributable assignment |
| claim relation identity + revisions | exact claim-revision endpoints + type/origin/basis/lifecycle |
| role assignment identity + revisions | subject + organization + role/time + origin/basis/lifecycle + exact evidence |
| review decision | exact revision(s)/reproducible set + actor/action/time/rationale as needed |

### Optional with a proving fixture/use case

| Concern | Add when |
|---|---|
| document source observations / anchors | one artifact contains multiple docs or source labels must be preserved independently |
| document parts | meaningful internal structure improves citation/query integrity |
| civic collections + memberships | expediente/package/case spans multiple documents |
| profile data | acta/report/budget semantics need validated specialized fields |
| typed association/event | a relationship carries independent role/time/amount/term identity that does not fit ClaimRelation |
| additional correction/purge event families | public redaction/release, evidence unlink/repair, identity actions or purge require semantics beyond the core ClaimRevisionAction |
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
relational. Raw mention, resolved identity, shared-anchor membership, and direct
claim relation are distinct facts.

### Raw mentions and resolved identity

```text
representation occurrence -> EntityMention -> optional Entity resolution
claim revision -----------------------------> ClaimEntityLink -> Entity
```

`EntityMention` is core because the exact source occurrence must survive even
when resolution is unknown, machine-suggested, later corrected, merged, or split.
The SQL shape may use separate resolution-decision rows rather than a mutable
`resolved_entity` column if that better preserves history. What is non-negotiable
is that reconciliation never overwrites the raw mention.

Entity merge/split uses a narrow append-only reconciliation lineage with
input/output entity IDs plus attribution/basis. Candidate promotion/correction
creates a superseding reconciliation row rather than mutating history. It is not
a universal identity graph. Accepted non-superseded merge lineage may inform
current retrieval; splits do not cause silent mass retargeting of old links.

### Shared anchors

```text
claim_revision -> claim_entity_link -> entity
claim_revision -> ClaimTagLink -> tag
```

These allow broad retrieval without creating an edge between every pair of
claims that mention the same place, project, institution, or topic. Entity and
tag links are append-only/correctable metadata: fixing an anchor does not erase
its prior machine/rule/human provenance or require rewriting the ClaimRevision.

Relation directionality is type semantics: contradiction/same-matter are
symmetric for retrieval; update/correction/response/implementation/supersession
are directed. Symmetric reverse lookup never creates a duplicate canonical edge.

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

### Rich relationship promotion boundary

The first schema must keep `ClaimRelation` narrow. A relationship that has its
own role/time/amount/term or otherwise needs independent identity is **not**
serialized into arbitrary edge JSON. AKF-013 already proves `RoleAssignment`, so
that one rich family belongs in migration `0001`: subject entity, organization,
role label/key, validity interval, origin/basis/lifecycle and exact evidence.
Other association/event families remain absent until a fixture/query proves them;
the migration-safe boundary is the prohibition on using ClaimRelation as a
generic attributed edge.

## Claim Data

Claim identity and claim revision are separate. SQL does not need a mandatory
mutable `current_revision` pointer if the current revision can be derived
unambiguously from lineage; such a pointer may be added later as an optimization.

```text
clm_123@1  machine extracted, active
clm_123@2  corrected wording, supersedes @1
```

A revision carries origin/process provenance, lifecycle, attribution/temporal scope, and flags.
Currentness is derived from supersession rather than a mutable current pointer. A later revision does
not rewrite the historical row it supersedes.

Human review is derived from `review_decisions`; it is not required to insert/search the revision and
is never inherited by a successor revision. REVIEW-002 adds one narrow `ClaimRevisionAction` row for
human `correct | restrict | unrestrict | retract` mutations so the source/result revision pair, actor,
rationale and immutable request identity remain attributable without overloading ReviewAction.

A correction can retain/remove only evidence/anchors/tags from the prepared source-revision snapshot;
creating new source evidence or retargeting existing ClaimRelations is a separate operation. Human
correction cannot fabricate `derived_inference` origin: a changed derived inference needs a real new
DerivationResultTarget. Any new `active` revision must remain compatible with the availability of its
carried source evidence.

Optional human assessment is separate from lifecycle/review and is only stored when a workflow
actually records such a judgment.

## Analysis and Verification Boundaries

The accepted model now has explicit non-overlapping analytical records:

```text
Lector / ProcessRun
  source assertion / explicit source content

RepresentationTarget(s)
  -> DerivationRun
  -> DerivationResult
  -> DerivationResultTarget
  -> source-contribution lineage -> RepresentationTarget(s)

bounded scope + SourceAuthorityScope(s)
  -> VerificationRun
  -> attempted/consumed Derivation steps
  -> exact verification evidence
  -> verdict + sufficiency + abstention/execution outcome

DerivationResultTarget
  -> optional ClaimRevision(kind=derived_inference)
  -> EvidenceLink(s) -> source RepresentationTarget(s)

ClaimRevision
  -> optional Assessment
```

`ProcessRun` remains Representation-processing / existing semantic-extraction provenance.
`DerivationRun` is a distinct immutable analytical attempt with ordered exact inputs, exact
program, executor/runtime/configuration, sandbox profile, outcome and one typed successful result.
Re-execution receives a new run ID; program/input/result hashes are not civic identity.

`DerivationResult` has its own logical result identity because an analytical result may combine
multiple Artifacts and therefore cannot safely be forced into the one-Artifact Representation
custody model. Bounded inline typed results or archive-backed material results are allowed. Exact
result slices use `DerivationResultTarget`; lineage state is per target (`exact | partial |
unavailable | none`) and source-contribution rows reuse exact `RepresentationTarget` identities.

A `VerificationRun` may bind to an exact ClaimRevision or remain ad hoc. It records its explicit
scope targets, exact SourceAuthorityScope rows, every Derivation attempted, which exact successful
result targets were consumed, and its direct/reachable source evidence. A failed run has no verdict;
`insufficient_evidence` exists only on a completed run with explicit insufficiency and an abstention
reason.

A `derived_inference` ClaimRevision must reference one exact available DerivationResultTarget.
EvidenceLink remains ClaimRevision -> source RepresentationTarget and is not derivation lineage or a
verifier trace. Supporting evidence for a derived Claim must be traceable to the selected result
target's source-contribution lineage; independent challenging evidence remains legal.

Assessment is now frozen as an optional first-class durable judgment family rather than a Claim
field or review synonym. It targets one exact ClaimRevision, permits independent disagreeing
assessors/policies, and may reference a same-Claim VerificationRun as basis. It never mutates Claim
lifecycle and no automatic verifier-to-Assessment promotion is authorized.

`ContextEnvelope` remains bounded interpretation material, not exact evidence or a canonical truth
entity. Evidence sufficiency remains typed Verification result data; negative/absence findings
require explicit inventory/completeness authority.

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

Protected use queries only exact **current** revisions satisfying required human review. A review of
a superseded revision never authorizes its successor.

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
- bounded recursive traversal over explicit claim relations, with deduplicated node reachability separate from edge/path enumeration in the ClaimRelation multigraph;
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

## Custody Status, Purge, and Tombstones

Artifact/representation bytes are immutable under normal operation. The model
must nevertheless represent the exceptional case where policy requires physical
purge. This is not ordinary deletion and must not be inferred from absence.

The schema design must be able to distinguish at least conceptually:

```text
available   bytes retained and usable
restricted  bytes retained but access-limited
purged      bytes intentionally removed by explicit policy action
```

A purge propagates to derived bytes/search indexes/caches that retain the scoped
content. A minimal tombstone may remain only when lawful and non-sensitive; its
contract must not require retaining a digest, locator, raw text, or metadata that
the purge itself is meant to remove. Claims/evidence depending on purged material
remain historically explainable only to the extent policy permits and must not be
presented as if their evidence were still inspectable.

## Single-Operator-First Storage

The baseline assumes one writer/operator process at a time, occasionally two
humans in the organization. SQLite and an in-process core writer are sufficient.

Stable civic IDs/revision lineage are preserved now. Universal operation IDs,
distributed locks, multi-tenant accounts, and peer synchronization are not
required. A later daemon/concurrent-client layer can add stale-write/idempotency
controls at its boundary without rewriting civic history.

## Pre-SQL Questions That Must Be Answered

Before migration `0001`, semantic fixtures must show that the model can represent:

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
7. Raw `EntityMention` survives unresolved/candidate/resolved identity states,
   and aliases/strong identifiers plus merge/split lineage preserve history
   without silent mass rewrite.
8. An active claim relation always has exact endpoints, attributable origin, and
   an inspectable basis; candidates can remain unreviewed.
9. Claim correction does not silently retarget an old relation.
10. SQLite can retrieve a bounded multi-step explicit relation chain without a
    graph database.
11. Evidence `challenges` and claim `contradicts` remain unambiguous in queries/UI.
12. Hilo can define Episodes outside core, and a tiny non-Episode output can use
    the same read model.
13. The backup/restore boundary includes database + archive + relation/evidence consistency; operational restore proof follows implementation.
14. Rich role/time/amount relationships cannot be forced into ClaimRelation; the
    promotion boundary to typed Association/Event remains migration-safe even if
    concrete tables are deferred.
15. Restricted material and explicit purge are distinguishable; lawful purge can
    remove bytes/derivatives without requiring prohibited tombstone content.

Only after these semantic gates pass should final SQL tables, constraints,
indexes, cached current pointers, idempotency keys, or record hashes be reviewed
and accepted. Artifact-backed parser/locator proofs and operational backup/restore
proofs remain required after the corresponding implementation exists.
## Pending analytical execution records

Phase D now closes the conceptual relationship between analytical derivation and verification:
a future `VerificationRun` must reference the exact ordered `DerivationRun` executions whose
results it used. `DerivationRun` retains executable provenance, bounded input scopes, typed result
identity and available result-to-source lineage; `VerificationRun` retains execution outcome,
verdict, evidence set, explicit sufficiency, abstention reason and model/process provenance.
Neither record is added to the current schema by this document. The next schema design must
reconcile both records with Claim origin provenance, existing `EvidenceLink` semantics and optional
`Assessment` without duplicate execution graphs.
