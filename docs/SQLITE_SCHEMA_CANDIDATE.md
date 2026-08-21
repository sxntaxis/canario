---
id: ACTAKIT-SQLITE-CANDIDATE-001
kind: schema-candidate
state: draft-for-review
created: 2026-08-21
authority: design-proposal
baseline: 1fc39e24800550ac14c0764bebc6b05a3d2b9dbf
summary: Reviewable SQLite candidate derived from the deep pre-SQL research, semantic fixtures, schema pressures, and expensive-mistake ledger. Not a migration or implementation authorization.
---

# SQLite Schema Candidate

## Status and rule

This document is a **candidate**, not migration `0001`. It converts the accepted
semantic model and deep research into a relational shape that can be attacked by
fixtures before code exists.

Design rule:

> Store civic authority in explicit relational records. Use JSON only at bounded,
> versioned extension seams where the shape is selected by a closed kind/version
> contract. Search indexes, caches, Outputs, and inferred graph closure are not
> authority.

The baseline remains single-writer-first, local-attached SQLite plus a
content-addressed evidence archive.

## 1. Authority boundary

Canonical authority is the pair:

```text
SQLite canonical records
+
evidence/representation byte archive
```

The database does not embed large source bytes. The archive does not encode civic
meaning by filenames. Stable opaque IDs connect both.

Only the ActaKit core writes canonical tables. Outputs, importers, AI readers,
and external tools use core contracts; they do not write SQLite directly.

## 2. SQLite operating invariants

Every writable connection must establish and verify at open time:

```text
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = FULL;
PRAGMA trusted_schema = OFF;
```

The implementation must also set a bounded busy timeout, keep write transactions
short, reject unsupported SQLite versions, and record/check `application_id` and
schema version. A connection that cannot establish required invariants is not a
writer.

SQLite/WAL must live on local attached storage, never a synced/network filesystem.
There is one canonical writer path. Concurrency does not justify a daemon until
real clients require it.

## 3. ID and revision rules

- Stable civic identities use opaque text IDs, UUIDv7-compatible with readable
  prefixes at the API boundary (`src_`, `acq_`, `art_`, `rep_`, `doc_`, `clm_`,
  `ent_`, `rel_`, ...).
- External numbers, URLs, filenames, acta numbers, names, and hashes are
  identifiers/attributes, never primary identity.
- Material semantic changes use append-only revisions where history matters.
- `created_at` is stored as UTC RFC3339 text with subsecond precision; civic
  source dates/periods are separate domain fields.
- Foreign keys are real SQLite FKs wherever the target type is known. Avoid a
  universal polymorphic `subject_type + subject_id` table that forfeits FK
  integrity.

## 4. Source and acquisition — Depósito ingress

### `sources`

Stable logical place/provider being observed.

```text
id PK
kind
name
active
created_at
```

### `source_locators`

Observed/known addresses for a source. URI change does not change source identity.

```text
id PK
source_id FK -> sources
locator
locator_kind
valid_from nullable
valid_to nullable
created_at
UNIQUE(source_id, locator)
```

### `acquisitions`

One observation/attempt at a specific time. Absence/failure is an observation,
not deletion.

```text
id PK
source_id FK
source_locator_id FK nullable
observed_at
outcome                 -- success | partial | not_found | failed
http_status nullable
adapter_key
adapter_version
error_code nullable
created_at
```

No universal crawl event log is required. This record exists because acquisition
identity is itself semantically necessary.

## 5. Artifacts and representations — Depósito / Mesa de trabajo

### `artifacts`

Logical custody record for acquired bytes.

```text
id PK
content_sha256 nullable
byte_size nullable
media_type nullable
storage_key nullable
availability            -- available | restricted | purged
validation_state         -- unchecked | verified | invalid
created_at
purged_at nullable
```

Important: artifact identity is **not** its digest. During lawful purge, policy may
require clearing digest/size/storage metadata. Use a partial unique index on
`content_sha256` only while a digest is retained.

### `acquisition_artifacts`

Many acquisition observations may yield the same bytes; one acquisition can also
produce multiple captured artifacts.

```text
acquisition_id FK
artifact_id FK
role                     -- primary | attachment | response_body | other
observed_filename nullable
observed_url nullable
PRIMARY KEY(acquisition_id, artifact_id, role)
```

### `representations`

Derived or directly usable representations. Originals are never overwritten by
OCR, normalization, redaction, or edited derivatives.

```text
id PK
artifact_id FK nullable            -- ultimate source artifact when known
parent_representation_id FK nullable
kind                              -- pdf | text | html | table | image | audio | video | json | xml | other
media_type nullable
content_sha256 nullable
byte_size nullable
storage_key nullable
availability                     -- available | restricted | purged
created_at
```

### `process_runs`

Bounded provenance for transformations/readers that actually create canonical
representations or extracted records. This is **not** universal event sourcing.

```text
id PK
process_kind                      -- extract_text | ocr | classify | extract_claims | reconcile | other registered kind
implementation
implementation_version
configuration_hash nullable
model_provider nullable
model_name nullable
started_at
finished_at nullable
outcome
```

### `process_inputs` / `process_outputs`

Typed joins from a process run to representations/artifacts or produced
representations. Exact table shape may be narrowed after implementation spike;
these joins must not become a generic graph of every operation in ActaKit.

## 6. Civic document identity

### `civic_documents`

Stable logical document identity, independent of bytes and encoding.

```text
id PK
title nullable
issuer_entity_id FK nullable
source_supplied_type nullable
source_type_label nullable
created_at
```

### `document_identifiers`

```text
id PK
document_id FK
scheme                   -- acta_number | oficio_number | procurement_id | uri | local_source_id | other registered scheme
value
issuer_entity_id FK nullable
created_at
UNIQUE(document_id, scheme, value)
```

Identifier uniqueness across documents is **not** globally assumed unless the
scheme contract proves it.

### `document_classifications`

Append-only classification history; source wording is preserved separately.

```text
id PK
document_id FK
normalized_type          -- broad civic type incl. unknown/otro
subtype nullable
profile_key nullable
profile_version nullable
confidence nullable
basis_kind               -- human | rule | machine
process_run_id FK nullable
created_at
```

Current classification is selected deterministically by policy/query, not by
silently overwriting history.

### `document_representations`

One artifact/representation may contain multiple documents; one logical document
may have multiple representations.

```text
document_id FK
representation_id FK
occurrence_kind          -- whole | contained | attachment | other
locator_kind nullable
locator_version nullable
locator_payload_json nullable
PRIMARY KEY(document_id, representation_id)
```

`locator_payload_json` is a bounded exception: it is accepted only for registered
`locator_kind + locator_version` contracts and must be validated by the core.
It is not arbitrary application JSON.

### Optional proof-only structures

`document_parts` and `document_collections` are added only when an artifact-backed
fixture proves they are needed. The candidate preserves IDs/FKs so adding them
later does not require identity collapse.

## 7. Claims and revisions — Fichero

### `claims`

Stable identity only.

```text
id PK
created_at
```

### `claim_revisions`

```text
id PK
claim_id FK
revision_no
claim_kind               -- source_assertion | derived_inference | community_report | verification_question
text
process_run_id FK nullable
created_at
UNIQUE(claim_id, revision_no)
```

A claim can exist machine-only. Human review is a separate axis. `corrected` is
not a status: correction creates a new revision. Contradiction/dispute is not a
truth flag on the row.

No universal `epistemic_status` column exists.

## 8. Exact evidence targeting

### `evidence_links`

Evidence is revision-bound.

```text
id PK
claim_revision_id FK
representation_id FK
relation                  -- supports | challenges | contextualizes | quotes | mentions
selector_kind
selector_version
selector_payload_json
state_payload_json nullable
created_at
```

The selector/state model is inspired by W3C Web Annotation: target a specific
representation using a typed selector, and optionally capture state needed to
re-anchor/version-check it.

JSON is permitted here only because selector families differ structurally. Both
payloads are validated against closed, versioned core schemas; unknown selector
kinds cannot become factual support until supported explicitly.

Initial selector kinds should be limited to fixtures actually proven for 1.0,
for example:

```text
text_quote:v1
pdf_page_quote:v1
table_range:v1
```

Other kinds remain an extension seam, not pre-created tables.

## 9. Raw mentions and entity identity

### `entity_mentions`

Raw observed occurrence **before** reconciliation.

```text
id PK
representation_id FK
claim_revision_id FK nullable
observed_text
selector_kind
selector_version
selector_payload_json
process_run_id FK nullable
created_at
```

The exact mention is never overwritten by canonical naming.

### `entities`

```text
id PK
kind                     -- organization | person | place | project | contract | program | other
canonical_name nullable
created_at
```

`canonical_name` is a local display convenience, not evidence and not identity.

### `entity_names`

```text
id PK
entity_id FK
name
name_kind                -- official | alias | former | display | other
source_document_id FK nullable
created_at
```

### `entity_identifiers`

```text
id PK
entity_id FK
scheme
value
issuer_entity_id FK nullable
created_at
UNIQUE(entity_id, scheme, value)
```

### `mention_resolutions`

Resolution is explicit and reversible; unresolved is valid.

```text
id PK
mention_id FK
entity_id FK
resolution_kind          -- candidate | accepted | rejected
score nullable
basis_kind               -- human | rule | machine
process_run_id FK nullable
created_at
```

Current resolution is derived from decisions/policy. Name equality never creates
identity automatically.

### `entity_reconciliations`

Narrow append-only merge/split lineage.

```text
id PK
kind                     -- merge | split
basis
actor nullable
created_at
```

### `entity_reconciliation_inputs` / `entity_reconciliation_outputs`

```text
reconciliation_id FK
entity_id FK
PRIMARY KEY(reconciliation_id, entity_id)
```

Old entity IDs remain explainable; historical claim anchors are not silently
mass-retargeted.

## 10. Claim anchors, tags, and direct relations

### `claim_entity_links`

```text
claim_revision_id FK
entity_id FK
mention_id FK nullable
role nullable
basis_kind               -- observed | human | rule | machine
created_at
PRIMARY KEY(claim_revision_id, entity_id, role, mention_id)
```

Shared entity anchors support retrieval. They **do not** imply pairwise semantic
relations between claims.

### `tags`

```text
id PK
namespace
key
label
created_at
UNIQUE(namespace, key)
```

### `claim_tags`

```text
claim_revision_id FK
tag_id FK
basis_kind
created_at
PRIMARY KEY(claim_revision_id, tag_id)
```

Tag taxonomies are local/extensible; the core does not impose a national civic
ontology.

### `claim_relations`

Stable relation identity.

```text
id PK
created_at
```

### `claim_relation_revisions`

```text
id PK
claim_relation_id FK
revision_no
from_claim_revision_id FK
to_claim_revision_id FK
relation_type            -- updates | contradicts | responds_to | corrects | other registered direct semantic relation
basis_kind               -- source | analyst_inference | machine_inference
rationale nullable
process_run_id FK nullable
created_at
UNIQUE(claim_relation_id, revision_no)
```

Only **direct** semantic edges are persisted. Co-occurrence and transitive closure
are query-time facts, never materialized canonical edges.

If a relationship has independent role/time/amount/identity, it must not be
stuffed into relation JSON. It is promoted to a typed Association/Event model
when an artifact-backed 1.0 fixture proves the need. No universal association
ontology is created preemptively.

## 11. Review without a truth column

Batch review is a UX/action grouping, not a new authority layer.

### `review_actions`

```text
id PK
actor
mode                     -- strict | batch | supervised
created_at
note nullable
```

### `claim_reviews`

```text
id PK
review_action_id FK nullable
claim_revision_id FK
decision                 -- accepted | rejected | needs_work
reviewer
reason nullable
created_at
```

### `claim_relation_reviews`

Same shape, FK to `claim_relation_revisions`.

### `mention_resolution_reviews`

Same shape, FK to `mention_resolutions` when human adjudication is recorded.

Separate review tables intentionally preserve FK integrity rather than using a
polymorphic universal review subject.

No review row means **unreviewed**, which is valid and searchable in supervised
mode.

## 12. Custody restriction and purge

Normal correction never mutates archived bytes. Redaction creates a new
representation.

An exceptional purge operation is explicit and scoped. The candidate does not
require a universal operation ledger; it does require a small `purges` record
because physical destruction changes what evidence remains inspectable.

### `purges`

```text
id PK
scope_kind               -- artifact | representation | derived_set
reason
actor
created_at
```

Target join tables record affected IDs. Purge implementation clears/deletes
scoped bytes and derived search/cache copies. Artifact/representation rows move
to `availability = purged`; policy may require nulling hashes, sizes, locators,
or other metadata. Tombstone content is therefore intentionally minimal and
policy-dependent.

## 13. Search is a projection

FTS5 is rebuildable and non-authoritative.

Candidate projections:

```text
claim_fts
  claim_revision_id UNINDEXED
  text

document_fts
  document_id UNINDEXED
  title
  extracted_text (only when policy permits)
```

The exact FTS mode (external-content vs contentless) is an implementation choice,
but rebuild and integrity-check commands are mandatory. No canonical FK points
**to** FTS tables.

Normal relational indexes should cover:

```text
acquisitions(source_id, observed_at)
artifacts(content_sha256) WHERE content_sha256 IS NOT NULL
representations(artifact_id, kind)
document_identifiers(scheme, value)
document_classifications(document_id, created_at)
claim_revisions(claim_id, revision_no)
evidence_links(claim_revision_id)
evidence_links(representation_id)
entity_mentions(claim_revision_id)
mention_resolutions(mention_id, created_at)
claim_entity_links(entity_id, claim_revision_id)
claim_tags(tag_id, claim_revision_id)
claim_relation_revisions(from_claim_revision_id, relation_type)
claim_relation_revisions(to_claim_revision_id, relation_type)
claim_reviews(claim_revision_id, created_at)
```

## 14. Query graph boundary

SQLite recursive CTEs may traverse **explicit ClaimRelations only**. Default
query depth must be bounded. Shared tags/entities are filter/anchor joins, not
edges to expand into all pairwise claims.

This keeps ActaKit graph-shaped without creating a graph database or a home-grown
triple store.

## 15. Outputs and extensions

No canonical Output/Hilo/Episode tables are required in migration `0001`.
Outputs consume a bounded read/query model. Hilo may own Episode internally.
Another structurally different output must be able to consume the same Fichero
without Episode.

If future Outputs need durable local state, they receive namespaced persistence
outside core civic tables and no implicit filesystem/network/raw-SQL authority.

## 16. Backup and restore boundary

A complete backup is not `cp actakit.db`.

It consists of:

```text
consistent SQLite snapshot
+
all retained original artifact bytes
+
all retained non-regenerable representation bytes
+
integrity manifest relating IDs/storage keys/digests where policy permits
```

FTS indexes and explicitly classified caches may be rebuilt. Backup must use the
SQLite backup API or another documented consistent-snapshot mechanism, not copy a
live WAL database file blindly. Restore proof must verify foreign keys, archive
references, retained hashes, and FTS rebuild.

## 17. Fixture pressure test

| Fixture | Candidate representation |
|---|---|
| AKF-001 exact PDF evidence | Artifact -> Representation -> EvidenceLink selector |
| AKF-002 repeated acquisition | Source -> multiple Acquisitions -> same/new Artifact |
| AKF-003 unknown/broken profile | CivicDocument + classification `unknown`; bytes survive |
| AKF-004 compound artifact | one Representation -> multiple CivicDocuments via join |
| AKF-005 spreadsheet locator | typed `table_range:v1` selector |
| AKF-006 supervised/batch | no review row is valid; `review_actions` groups per-record reviews |
| AKF-007 raw mention | `entity_mentions` before resolution |
| AKF-008 same-name people | multiple unresolved/resolved mentions; no name merge |
| AKF-009 rename/merge/split | names/identifiers + append-only reconciliation lineage |
| AKF-010 correction/relation | relation endpoints bind exact ClaimRevisions |
| AKF-011 anchor/traversal | joins through Entity/Tag; explicit relation recursion only |
| AKF-012 disagreement | EvidenceLink `challenges` distinct from ClaimRelation `contradicts` |
| AKF-013 rich association | promotion boundary reserved; no JSON edge junk drawer |
| AKF-014 output independence | no Episode/Hilo core dependency |
| AKF-015 backup/restore | DB + archive + integrity boundary |
| AKF-016 redaction/purge | derivative Representation + explicit purge lifecycle |

All 16 fit structurally. This is **not** operational proof.

## 18. Expensive-mistake check

The candidate explicitly avoids all current research-ledger mistakes:

1. no URL/filename/acta-number PK;
2. no name-based entity merge;
3. no universal nodes/edges/triples;
4. no materialized co-occurrence/transitive closure;
5. no external direct SQLite writes;
6. no network/synced WAL;
7. no live-file-copy backup;
8. no canonical FTS;
9. no overwrite of originals;
10. no scrape absence = deletion;
11. specialized parsers may fail loudly rather than guess;
12. Outputs get no arbitrary URL/path capability by default;
13. no universal truth/epistemic-status column;
14. no universal event sourcing/operation receipts;
15. no RDF/OWL/XML runtime stack.

## 19. Deliberate open decisions before migration `0001`

These are review questions, not permission to defer core semantics indefinitely:

1. Exact initial closed enums for source/document/claim/relation kinds.
2. Exact selector schemas for the first artifact-backed locator proofs.
3. Whether `process_inputs/process_outputs` remain two typed joins or collapse to
   narrower representation-specific FKs after an implementation spike.
4. Whether document parts/collections are needed in `0001` after real compound
   civic artifact fixtures.
5. Whether a real 1.0 attributed relationship requires concrete Association/Event
   tables in `0001`; if yes, design them before freezing the migration.
6. Exact SQLite minimum version after local/runtime compatibility testing.
7. FTS external-content vs contentless implementation after rebuild/integrity
   tests.
8. Exact purge metadata-retention policy for the intended jurisdiction/use.

None of these reopen the core identity/evidence/relation architecture.

## 20. Candidate verdict

**SCHEMA_CANDIDATE_GATE: READY_FOR_CRITICAL_REVIEW**

The candidate is relational, FK-oriented, single-writer-first, graph-shaped where
needed, and keeps flexible JSON at only two bounded seams: evidence/document
locators and optional state anchors. It does not authorize migration or code.

Next step: attack this candidate with concrete DDL review and artifact-backed
fixtures, then either revise it or authorize a migration design.
