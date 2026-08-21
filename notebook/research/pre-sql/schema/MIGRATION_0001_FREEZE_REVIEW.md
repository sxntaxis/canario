# Migration 0001 Freeze Review

**State:** `MIGRATION_0001_FREEZE_COMPLETE__AUTHORIZATION_REVIEW_READY`
**Migration/implementation authorized:** **NO**

## Purpose

This review turns the semantic SQLite candidate into a physically deterministic
`0001` specification without yet creating a production migration. It is narrower
than the completed critical review: no new civic ontology, generic graph layer,
association family, output subsystem, or storage engine is introduced here.

The freeze asks only whether a fresh ActaKit database can be created atomically
with one unambiguous schema, connection contract, vocabulary set, current-leaf
semantics, query/index contract, FTS rebuild rule and SQL/core invariant boundary.

## Lineage boundary

The freeze work in this checkout was developed from:

```text
863edaaed76bd5f3a49f3a896bafd167a5efdc7a
```

The authoritative target-runtime certification supplied after that checkpoint is:

```text
6deafab40d40ea3f70e5e8c96433015ac5e54f6b
PASS_TARGET_SQLITE_RUNTIME_CERTIFICATION
SQLite 3.53.4
source id: 2026-07-24 19:02:57 bf7c7f30031888f4e796e429ab3978879485813aaca6f641c7b33e4e09459bcc
```

The delta has been reconciled onto `6deafab...` without discarding the historical
runtime evidence. The complete post-freeze suite passed on the exact certified
SQLite 3.53.4 source ID; this document is now the freeze specification review
authority for a separate authorization decision.

## Frozen physical inventory proposed by this delta

```text
ordinary STRICT tables: 54
FTS5 virtual tables:     3
application triggers:    0
explicit indexes:        114
FK child paths checked:  118
FK child table scans:    0
WITHOUT ROWID tables:    0
schema_migrations table: 0
SQLite JSON dependency:  absent
```

The SQL design artifact is:

```text
notebook/research/pre-sql/schema/MIGRATION_0001_SPEC.sql
```

It is Notebook design authority only. It is not yet a production migration.

Current delta SHA256:

```text
31cac5ccc3440ce555242ba288317df527bb30949b2142026d8ceb2805d3adfc
```

## Freeze findings

### MFR-001 — Connection PRAGMAs do not belong inside migration SQL

`0001` runs under a bootstrap executor that first establishes the writable
connection contract:

```text
foreign_keys=ON
journal_mode=WAL
synchronous=FULL
trusted_schema=OFF
secure_delete=ON
busy_timeout=5000
```

The SQL specification itself contains no connection PRAGMAs and no transaction
wrapper. The bootstrap owns `BEGIN IMMEDIATE` / `COMMIT`.

### MFR-002 — File identity markers are the last writes inside bootstrap

The SQL specification writes:

```text
application_id = 0x414B4954  # AKIT
user_version   = 1
```

only at the end of the migration transaction. A forced failure after those writes
rolls back the schema and both markers to an empty `0/0` database.

A non-empty unknown SQLite database is not accepted as a fresh ActaKit target.

### MFR-003 — SQL JSON was an accidental runtime dependency

The candidate required selector JSON to be validated by the owning
`selector_kind + selector_version` core registry, but the scratch DDL still used
`json_valid(...)`.

`0001` now contains no SQL-JSON dependency. Selector payload validation remains a
core registry invariant and exact selectors remain artifact-proven.

### MFR-004 — SourceLocator is identity, Acquisition is temporal observation

The former `valid_from/valid_to` on `source_locators` conflicted with
`UNIQUE(source_id, locator)`: the same URI could not have multiple validity
spans anyway.

The freeze chooses one model:

```text
SourceLocator = stable known address
Acquisition.observed_at = history of actual observation attempts
```

URI changes do not change Source identity, and re-observing an old URI does not
manufacture a duplicate locator identity.

### MFR-005 — Archive purge must not reserve destroyed bytes forever

`archive_objects(content_sha256)` and `storage_key` are unique only for
`availability='available'` rows. A minimal purged tombstone may keep a digest when
policy allows, but it does not block legitimate future reingestion of the same
bytes.

A purged ArchiveObject may not retain `storage_key`.

### MFR-006 — Cheap physical domains are enforced in SQL

`content_sha256`, when retained, is exactly 64 lowercase hexadecimal characters.
`http_status`, when present, is restricted to `100..599`.

These are physical sanity constraints, not domain-policy guesses.

### MFR-007 — Symmetric ClaimRelations have one stored orientation

For `contradicts` and `same_matter_as`, the stored endpoint IDs use canonical
BINARY order:

```text
from_claim_revision_id < to_claim_revision_id
```

Retrieval remains symmetric. Directed relation types remain directional. This
prevents storing both orientations of one symmetric edge while preserving the
ClaimRelation multigraph and parallel relation types.

### MFR-008 — Purge lifecycle state is internally coherent

A purge in `planned` state has no `executed_at`; terminal
`completed|partial|failed` states require it. Purge targets likewise have either
both `executed_at + outcome` or neither.

Cross-row completion remains a core operation invariant: a `completed` purge may
not retain pending/failed targets.

### MFR-009 — RepresentationTarget availability participates in custody validation

An available target may not remain attached to a purged/unavailable
Representation. This is a cross-row core transaction invariant, mechanically
exercised by the proof harness.

### MFR-010 — ProcessRun is terminal provenance, not job scheduling

`process_runs.finished_at` is required and `outcome` is closed to:

```text
success | partial | failed
```

with `started_at <= finished_at`.

Canonical machine/rule semantic outputs may reference only `success|partial`
runs. Failed runs may remain as audit provenance but cannot silently authorize
canonical outputs. That cross-row rule belongs to the core transaction validator.

`process_kind` remains a registered open key because processors/extensions can
add typed implementations without changing a global civic enum.

### MFR-011 — Consecutive revision numbering is deliberately a core invariant

SQL guarantees, where applicable:

- positive revision numbers;
- uniqueness within stable identity;
- revision 1 as root;
- later revision names a same-identity predecessor;
- predecessor cannot be self;
- at most one successor.

Core write validation additionally requires the new number to be exactly the
predecessor/current number plus one. The proof deliberately inserts a legal-SQL
`1 -> 3` gap and verifies the validator detects it.

`mention_resolution_revisions` uses the same consecutive-number rule with
`MAX(revision_no)+1` for the exact mention rather than a supersedes pointer.

No trigger is added merely to enforce this cross-row rule.

### MFR-012 — Current/operative state is derived, not mutable

For supersession families, the current leaf is a row for which no successor
references it. Operative semantic records additionally apply their lifecycle,
for example `lifecycle='active'`.

Competing candidate roots are permitted only where the model explicitly allows
independent proposals. The core rejects multiple non-superseded active document
classifications for one CivicDocument.

### MFR-013 — Review decisions are immutable and reviewer-relative

A review does not mutate its semantic subject and is not itself a semantic
revision chain. If the same reviewer changes judgment, they append another review
row.

Effective state for one reviewer is the deterministic latest row:

```text
ORDER BY created_at DESC, id DESC
```

Reviews by different reviewers remain independent and are combined by policy,
not collapsed into one global truth field.

Review subject indexes therefore use the prefix:

```text
(subject_id, reviewer, created_at DESC, id DESC)
```

while still covering FK reverse lookup.

### MFR-014 — FTS eligibility is deterministic

`claim_fts` contains exactly current non-superseded ClaimRevisions with:

```text
lifecycle='active'
```

Human review is not required for supervised internal search. `rejected`,
`retracted`, `restricted` and superseded claim revisions are excluded. Sensitivity
is an output/access-policy axis, not a synthetic review gate.

`document_fts` contains current normal-visibility document revisions with a title.

`representation_fts` contains only available textual Representations supported by
the rebuild reader. Restricted/purged representations are excluded.

All three tables remain ordinary self-content FTS5 projections, disposable and
rebuildable from canonical authority, with FTS5 `secure-delete=1`.

### MFR-015 — Rowid is an implementation detail, not civic identity

All 54 ordinary `0001` tables remain ordinary rowid tables. No application
contract may use hidden `rowid` as durable identity.

`WITHOUT ROWID` is not frozen merely because many PKs are text/composite. It is an
optimization whose value depends on row size and the secondary-index mix; it can
be benchmarked later without changing civic identity or semantics.

### MFR-016 — Retry idempotency uses stable preallocated IDs

A canonical write operation allocates opaque IDs and timestamps before opening its
write transaction. A retry reuses the same IDs.

On PK collision:

- exact immutable payload match => the core may recognize the prior committed
  attempt as the same operation;
- payload mismatch => hard identity collision.

`INSERT OR REPLACE` is forbidden for canonical writes. `0001` has no generic
idempotency table because the stable civic IDs already supply the bounded retry
identity needed by current operations.

### MFR-017 — Index freeze follows planner evidence, not “one FK = one index”

The freeze checks every child-FK lookup through `EXPLAIN QUERY PLAN` instead of
requiring a syntactically identical index for every composite FK.

Current result:

```text
118 FK paths checked
0 child table scans
114 explicit indexes
0 exact duplicate explicit indexes
0 simple same-predicate prefix redundancies
```

Two indexes from the earlier candidate that exactly duplicated UNIQUE autoindexes
were removed before freeze.

## Closed vs registered-open vocabulary boundary

The SQL `CHECK ... IN (...)` vocabularies are contract-level closed values,
including source/acquisition/artifact/representation kinds, occurrence/name kinds,
document type, claim/evidence/relation kinds, origin/lifecycle, mention-resolution
state, reconciliation kind, basis roles, review mode/decision, process outcome and
purge state/action.

The following remain registered/extensible text keys and are **not** global civic
enums:

```text
SourceLocator.locator_kind
Acquisition.adapter_key / adapter_version / error_code
ProcessRun.process_kind / implementation / implementation_version
ProcessRun.model_provider / model_name
RepresentationTarget.selector_kind / selector_version
DocumentIdentifier.scheme
EntityIdentifier.scheme
DocumentClassification.subtype / profile_key / profile_version
Tag.namespace / key
ClaimEntityLink.role
RoleAssignment.role_key
Purge.reason_code
```

“Open” means validated by the owning adapter/registry/local taxonomy, not arbitrary
unchecked semantics.

## SQL vs core invariant boundary

| Invariant | Enforcement |
|---|---|
| type affinity, NOT NULL, booleans, closed vocabularies | SQLite STRICT/CHECK |
| known typed references | SQLite FK |
| same-owner supersession / selector ownership | composite SQLite FK |
| at most one successor in linear supersession | partial UNIQUE index |
| canonical symmetric edge orientation | SQLite CHECK |
| SHA-256 / HTTP status / local row lifecycle sanity | SQLite CHECK |
| exact consecutive revision number | core transaction validator |
| retained Artifact/Representation/Target availability closure | core transaction validator |
| exactly one active current document classification | core transaction validator |
| machine/rule output references success/partial ProcessRun | core transaction validator |
| active source assertion has usable active supporting evidence | core transaction validator |
| reconciliation inputs/outputs/basis remain operational | core transaction validator |
| purge dependency closure and completed-target consistency | purge executor + core validator |
| scheme/selector/adapter-specific payload contracts | registered core/adapter validators |
| effective review policy across independent reviewers | policy/query layer |
| FTS projection equality with canonical eligibility set | rebuild/integrity proof |

The absence of application triggers is deliberate. Cross-row invariants that need
business-policy context are checked in the same `BEGIN IMMEDIATE` write transaction
before commit rather than hidden in trigger programs.

## Bootstrap/open contract

Fresh bootstrap:

```text
verify empty unknown file + markers 0/0
  -> establish writable connection contract
  -> BEGIN IMMEDIATE
  -> execute exact MIGRATION_0001_SPEC.sql
  -> set application_id=AKIT and user_version=1 as final statements
  -> COMMIT
  -> reopen and verify markers/integrity/schema inventory
```

Forced failure after marker writes must roll back to an empty schema and `0/0`
markers. WAL mode may persist because it is a connection/file mode established
before the migration transaction.

Read-only authority opens with SQLite URI `mode=ro`, `query_only=ON`,
`trusted_schema=OFF`, FK enforcement enabled and marker verification.

## Reconciled target-runtime proof result

On the certified SQLite 3.53.4 runtime:

```text
MIGRATION_0001_SPEC_PROOF=PASS sqlite=3.53.4
strict_tables=54
fts_tables=3
critical_invariants=16/16 PASS
semantic_fixture_storage=16/16 REPRESENTABLE

MIGRATION_FREEZE_PROOF=PASS sqlite=3.53.4
bootstrap_transaction=PASS
bootstrap_failure_rollback=PASS
wrong_file_rejection=PASS
closed_vocabularies=PASS
core_write_contracts=PASS
rowid_strategy=PASS
index_inventory=PASS explicit=114 exact_duplicates=0 simple_prefix_redundancy=0
foreign_key_child_plans=PASS checked=118 scans=0
query_surface_indexes=PASS
readonly_open_contract=PASS
sql_json_dependency=ABSENT

STORAGE_OPERATION_PROOF=PASS
backup/clean restore/FTS rebuild=PASS
purge archive/FTS/WAL/VACUUM=PASS
```

The exact target-runtime result is recorded in
`TARGET_RUNTIME_CERTIFICATION.md`, including the prior certification and this
post-freeze revalidation.

## Freeze result

The reconciled `MIGRATION_0001_SPEC.sql` hash is:

```text
31cac5ccc3440ce555242ba288317df527bb30949b2142026d8ceb2805d3adfc
```

The migration spec proof, migration freeze proof, selectors, storage/restore/
purge proof, and final runtime contract all pass. The freeze is complete and
ready for authorization review. `migration_authorized: false` remains in force.

## Verdict

```text
MIGRATION_0001_FREEZE_REVIEW:
MIGRATION_0001_FREEZE_COMPLETE__AUTHORIZATION_REVIEW_READY
```

The physical contract carries no unresolved freeze proof gate in this review.
This freezes a design specification only; it does not create or authorize the
production migration.

**This review does not create or authorize migration `0001`.**
