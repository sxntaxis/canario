---
id: ACTAKIT-SQLITE-CANDIDATE-CRITICAL-REVIEW-001
type: schema-candidate-critical-review
state: ddl-proof-pass-artifact-runtime-proof-required
authority: research
created: 2026-08-21
candidate_baseline: 8b98010b32f88ce64b616ea51cccb48058ad35bb
migration_authorized: false
---

# SQLite candidate critical review

## Verdict

**SCHEMA_CANDIDATE_GATE: DDL_PROOF_PASS__ARTIFACT_RUNTIME_PROOF_REQUIRED**

The first candidate was not safe to freeze. Adversarial review found several
places where a plausible relational sketch contradicted the already-accepted
contracts or SQLite's actual semantics. The candidate has been revised at design
level. No production DDL, migration, schema file, or current pipeline cutover is
authorized by this review.

## Research horizon after reopening

The deep Book gate remains the basis. It was reopened **narrowly** where the
candidate exposed an implementation-level uncertainty that could change schema:

- 29/29 Books deep-audited;
- 99 source records;
- 110 source-book research claims;
- 14 schema pressures;
- 21 expensive mistakes;
- 16 semantic fixtures, now backed by 56 explicit assertions.

New SQLite evidence establishes STRICT-primary-key nullability behavior,
database/FTS deletion scars, and a durability-relevant version floor. Existing
Popolo/W3C ORG/FollowTheMoney Books already supplied enough evidence for the
role/time rich-association decision; no new ontology was imported.

## Findings that forced candidate changes

### CR-001 — ClaimRevision contract regression

The first candidate omitted already-required `origin_kind`, lifecycle,
attribution, temporal scope, and flags from ClaimRevision. Those are canonical
meaning, not UI metadata. They are restored.

### CR-002 — ClaimRelation origin/basis regression

The first candidate blurred who/what proposed a relation with why the relation is
asserted, and did not provide a typed exact source-evidence path. Relation
revision now carries `origin_kind`, `basis_kind`, lifecycle and rationale, while
source-backed basis points to an exact RepresentationTarget.

### CR-003 — rich association was no longer honestly deferrable

AKF-013 already contains a real 1.0 shape: person/entity + organization + role +
validity interval + exact evidence. Popolo and FollowTheMoney both support the
same modeling pressure. `RoleAssignment` is therefore concrete in the first
schema candidate. This does **not** authorize a generic Association/Event table.
Other rich relation families remain fixture-driven.

### CR-004 — nullable composite-primary-key contradiction

The first candidate made optional `role`/`mention_id` components of the
`claim_entity_links` primary key. In SQLite STRICT tables, primary-key components
are implicitly NOT NULL. The link now has its own stable row ID; genuinely
optional fields remain optional.

### CR-005 — logical custody identity was conflated with byte deduplication

A digest identifies physical content, not the full provenance/custody record.
The revised candidate separates:

```text
Acquisition -> Artifact (logical custody identity) -> ArchiveObject (physical bytes)
```

Repeated equal captures create separate Artifacts and may share one ArchiveObject.
This preserves acquisition/restriction/purge history while retaining physical
deduplication.

### CR-006 — exact representation selectors were duplicated and under-reusable

EvidenceLink and EntityMention both need the same durable answer to “where in
this representation?”, while ClaimRelation and RoleAssignment also need exact
source basis. `RepresentationTarget` now owns only this bounded locator concern;
semantic link tables remain typed and FK-backed. This is not a generic graph.

### CR-007 — purge semantics overstated what DELETE means

SQLite ordinary deletion and FTS row removal can leave recoverable material. The
revised policy distinguishes logical record removal, database-file scrubbing,
FTS scrubbing, archive-byte deletion, WAL maintenance, backup scope, and storage
outside ActaKit's authority boundary.

A purge freezes an exact `purge_targets` manifest before execution. This is the
bounded exception to typed FK targets because a purge target may intentionally
cease to exist. The target kind is closed to registered core record families and
cannot become a generic civic subject namespace.

### CR-008 — FTS mode was carrying unnecessary maintenance risk

For the expected canton-scale corpus, ordinary self-content FTS5 tables are the
simpler disposable projection. They duplicate limited search text but avoid the
rowid/content-table consistency coupling of external-content mode and the
rebuild/deletion tradeoffs of contentless mode. FTS remains non-authoritative.

### CR-009 — version floor is part of durability

The initial support floor is SQLite 3.51.3+, where the documented WAL-reset
corruption defect affecting earlier unpatched releases is fixed. A deliberately
patched older runtime could be certified later, but is not the default contract.

### CR-010 — fixture evidence trace itself had stale/misaligned refs

Adversarial review found assertions whose `basis_refs` no longer supported the
statement they were attached to, including AKF-013 pointing at the OCFL purge
claim. The fixture ledger now points rich-relation assertions to the actual
Popolo/FollowTheMoney claims and strengthens acquisition, reconciliation,
relation, backup and purge traces. This is a research-governance fix, not a schema
feature.

### CR-011 — ClaimRelation traversal is multigraph traversal

The scratch proof exposed two simultaneously active edges from the same source
ClaimRevision to the same destination (`updates` and `contradicts`). A naive
`UNION ALL` node walk duplicated the destination. SQLite explicitly distinguishes
`UNION` duplicate suppression from `UNION ALL`, and its graph example uses
`UNION` to avoid cycling. ActaKit now treats ClaimRelation as a directed
multigraph: node reachability is deduplicated/cycle-safe, while edge/path queries
preserve relation-revision identity. Both remain depth/result bounded.

### CR-012 — Acquisition locator/source integrity was under-constrained

The first scratch DDL allowed an Acquisition whose `source_id` named Source A
while `source_locator_id` belonged to Source B. That makes provenance internally
self-contradictory. `source_locators` now exposes `(id, source_id)` as a composite
candidate key and Acquisition uses a composite FK when a locator is present.

### CR-013 — Representation custody lineage could become orphaned or cross-capture

A retained Representation could previously have bytes but no Artifact at all, or
name a parent Representation from one Artifact while claiming another Artifact.
That breaks custody provenance even though every individual FK is valid. Retained
Representations now require `artifact_id`; parent/child lineage uses a composite
FK on `(representation_id, artifact_id)`. Multi-Artifact transformations are not
smuggled through this pointer; they require a future typed contract if proven.

### CR-014 — mention-derived ClaimEntityLink could become stale after re-resolution

The link stored `mention_id` but not the exact MentionResolutionRevision that
justified the Entity. A later corrected/cleared resolution therefore left no
mechanical way to distinguish the historical anchor from the current one.
Mention-derived links now cite the exact resolution revision, composite FKs prove
mention/claim/entity agreement, and link correction is append-only via explicit
supersession. ClaimEntityLink review is also typed rather than polymorphic.

### CR-015 — EntityReconciliation had no operative/review state

The prose allowed only accepted merge lineage to affect current retrieval, but
the table could not distinguish a machine proposal from an operative or rejected
merge/split. Reconciliation now has candidate/active/rejected lifecycle, explicit append-only
supersession and a typed review table. Historical inputs/outputs remain immutable;
a reviewed candidate is promoted by a superseding row rather than an in-place
state flip, and current retrieval uses only non-superseded operative lineage.

### CR-016 — Tag anchors were not correctable without history loss

`claim_tags` used `(claim_revision_id, tag_id)` as its only identity. A wrong
machine tag could therefore only be deleted, silently mutated, or left active.
Because tags are first-class shared retrieval anchors, that violates the same
correction/history rule already applied to entity anchors. The candidate now uses
append-only `ClaimTagLink` identity, supersession, lifecycle and typed review; it
does not add taxonomy hierarchy or ontology machinery.

### CR-017 — machine/rule origin could exist without attributable process

Several rows exposed `origin_kind=machine|rule` while leaving `process_run_id`
nullable. That made the provenance label stronger than the retained evidence.
The candidate now requires a ProcessRun for machine/rule semantic writes, and for
all derived Representations. Human-origin rows and original Representations may
omit it. This is a schema pressure already required by the processing provenance
contract, not a new workflow feature.

### CR-018 — CivicDocument metadata contradicted the correction contract

The accepted contract already said document corrections preserve history, but the
first candidate put `title`, `issuer`, `document_date` and `language` directly on
the stable `civic_documents` row. Improved extraction or a human correction would
therefore require an in-place rewrite. `CivicDocument` is now identity-only and
`CivicDocumentRevision` owns mutable civic metadata plus origin/process provenance
and same-document supersession. Document FTS keys the exact revision, not a
mutable document title.

### CR-019 — relation directionality was implicit and therefore query-lossy

The candidate called ClaimRelation a directed multigraph while the same closed
vocabulary contained semantically symmetric relations. `contradicts` and
`same_matter_as` must be discoverable from either endpoint; `updates`, `corrects`,
`responds_to`, `implements` and `supersedes` must not be silently reversed. The
contract now registers directionality per relation type. Storage preserves one
attributable edge; query expansion handles symmetry without manufacturing reverse
canonical relations.

## Decisions closed before scratch DDL

1. initial closed vocabularies;
2. first selector contracts;
3. no generic process input/output graph in `0001`;
4. no DocumentPart/Collection table until a proving query/fixture requires one;
5. concrete `RoleAssignment` as the first rich relationship;
6. SQLite 3.51.3+ support floor;
7. ordinary self-content FTS5 as disposable projection;
8. frozen exact purge manifest + explicit tombstone/scrub/storage boundary.

## Mechanical proof status

Disposable `SCRATCH_DDL.sql` plus `prove_scratch_ddl.py` now pass on the cloud
runtime for the structural questions they can certify:

- 48 STRICT ordinary tables created successfully;
- FK/CHECK/nullability ownership constraints exercised, including same-Source
  acquisition locators, same-Document/Claim revision lineage, same-Relation revision
  lineage, RepresentationTarget ownership, ClaimEntityLink mention context, append-only Tag anchors, and generated-row process provenance;
- all 16 fixture shapes are representable;
- ClaimRelation multigraph reachability and parallel-edge preservation are both
  exercised;
- ordinary self-content FTS5 + persistent FTS secure-delete command works on the
  available runtime;
- SQLite backup API snapshot restores with `foreign_key_check` clean.

The cloud Python runtime embeds SQLite 3.46.1, below the candidate's 3.51.3
durability floor, so this is **not** packaged-runtime certification. The real RoleAssignment shape is now independently proven by TSE resolution 2160-E11-2024. Remaining gates are artifact-backed selector/parser reopening, shared-byte purge maintenance, full archive+DB clean-machine restore, WAL/FTS/backup purge maintenance, and certification on the actual >=3.51.3 runtime/compile options. None is reclassified as optional.

Until those pass, migration `0001` remains unauthorized.
