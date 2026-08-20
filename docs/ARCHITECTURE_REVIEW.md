# ActaKit Architecture Review

Review target: the architecture sequence ending at `cc320894`, especially
`docs/ARCHITECTURE.md`, `docs/CONTRACTS.md`, `docs/DATA_MODEL.md`,
`docs/IMPLEMENTATION_PLAN.md`, `docs/ROADMAP.md`, and `docs/RELEASE_1_0.md`.

## Verdict

The proposal has the right durable boundaries and is substantially simpler than
the original acta workflow. It is **not yet ready to become a SQLite model**.
The main risk is not a missing graph feature. It is allowing every useful
boundary, audit concern, future extension, and operational policy to become a
first-class 1.0 table at once.

Accept the direction, but make one reduction pass first. The next model should
be a small evidence-and-claims core with optional document structure, explicit
review history, and two non-equivalent kinds of connection. Acquisition runs,
output packaging, saved queries, operation receipts, rich policy engines, and
most extension machinery should not determine the first schema unless a proof
fixture requires them.

The proposal passes the conceptual test when explained as Depósito, Mesa de
trabajo, Lector, Fichero, Mesa de control, Consultas, and Salidas. It currently
fails the implementation test in places: a reader can still mistake the
catalog of table families in `DATA_MODEL.md` for a required product inventory.

## Keep

- **Self-contained civic scope** in `docs/ARCHITECTURE.md` sections `Purpose`
  and `Product Scope`. It correctly removes Plaza, Esparza, party systems, and
  external workspaces from the product boundary.
- **Evidence custody separated from representations** in
  `docs/ARCHITECTURE.md` sections `Evidence Custody` and `Representations`.
  Original bytes, derived text, OCR, tables, and transcripts must not replace
  one another.
- **Semantic document type separated from physical representation and locator**
  in `ARCHITECTURE.md` sections `Civic Documents` and `Graceful Degradation`,
  and `CONTRACTS.md` sections `Civic Documents` and `Evidence Links`. This is
  the correct migration boundary for PDFs, scans, spreadsheets, media, and
  unknown material.
- **Unknown and malformed material remains preserved**. This is a product
  invariant, not merely an error-handling detail.
- **Claim identity, claim revision, and exact evidence links** in
  `CONTRACTS.md` and `DATA_MODEL.md`. Relations pointing to exact revisions is
  the right answer to correction history.
- **Shared anchors versus direct claim relations** in
  `ARCHITECTURE.md` section `The Fichero Is a Network`. This avoids both AI
  rediscovery and pairwise-edge explosion.
- **ClaimRelation as attributable data**. Its endpoint revisions, origin,
  basis, rationale, lifecycle, and review visibility are worth preserving.
- **Single-operator-first deployment** in `ARCHITECTURE.md`, `DATA_MODEL.md`,
  and `RELEASE_1_0.md`. Stable IDs and history do not justify accounts, roles,
  a daemon, RPC, or multi-writer infrastructure.
- **Outputs are read-oriented projections**. Keeping Hilo and Episode out of
  the universal core is a material improvement over the legacy workflow.
- **No generic nodes/edges/triples table** and no dependency on vector search,
  an LLM memory, or a graph database. This boundary should remain explicit in
  the pre-SQL patch.

## Simplify

### 1. Separate the semantic core from operational support

`DATA_MODEL.md` section `Likely Table Families` lists roughly thirty families.
It is a useful inventory of possible concerns, but it reads too much like a
schema prescription. Mark each family as `core now`, `optional with fixture`,
or `horizon` and make the first group small:

```text
artifact -> representation -> civic document
claim revision -> evidence link -> representation locator
claim revision -> entity/tag anchor
claim relation revision -> claim revision
review decision -> exact subject revision
```

`SourcePolicy`, `SourceRun`, `SourceCapture`, `ProcessRun`, `OperationReceipt`,
`SavedQuery`, `OutputType`, `OutputInstance`, `OutputState`, and
`OutputSnapshot` are valid concepts, but not all need to be universal canonical
tables before a real workflow uses them. `CONTRACTS.md` currently gives them
equal visual weight to claims and evidence.

### 2. Avoid two revision systems for every object

`CONTRACTS.md` section `Contract Rules` requires `schema_version`, `revision`,
`record_hash`, and `operation_id` for every mutable canonical record. This is
too broad for 1.0. It adds serialization, hash, stale-write, and replay
semantics before their failure cases are demonstrated.

Require immutable IDs and append-only revisions for claims, documents when
their identity/classification changes, and claim relations. Require review
history for reviewed subjects. Use ordinary timestamps and process provenance
elsewhere. Add canonical record hashes and idempotency receipts where a
concrete import/replay operation needs them, not as a universal tax.

For claims, do not store both a mandatory `current revision` pointer and a
second set of rules for determining current state until query tests prove the
pointer is needed. A claim identity plus revision lineage is sufficient; a
cached current pointer can be an optimization later.

### 3. Collapse claim state into non-overlapping axes

`ARCHITECTURE.md` section `Claims` and `CONTRACTS.md` section `Claims` currently
combine:

```text
origin, kind, review level, lifecycle status, epistemic status,
correction/retraction, sensitivity, and privacy restriction
```

These are not one state machine. For 1.0 define only:

- **review**: no human decision | human-reviewed, derived from review records;
- **lifecycle**: active | rejected | superseded | retracted | restricted;
- **assessment**, only if a real workflow needs it: unassessed | supported |
  contested | refuted.

`machine-only` is origin/review visibility, not a claim lifecycle. `corrected`
is a new revision or explicit correction event, not a status. `disputed` is an
assessment or review action, not a synonym for rejected. Do not make
`epistemic_status` look like a fact validator; it records an attributable
assessment about the claim.

The same axes should apply to a ClaimRelation without inventing a second set of
meanings. A relation proposal may be searchable in `supervised` mode, but an
active machine proposal must remain visibly unreviewed.

### 4. Tighten evidence-link vocabulary

`CONTRACTS.md` gives `EvidenceLink.relation` the value `contradicts`, while
`ClaimRelation.relation_type` also has `contradicts`. These are different
directions, but the identical word invites incorrect queries and UI wording.

Keep the contracts separate and rename or define the evidence-side value as
`supports | challenges | contextualizes | quotes | mentions`. Reserve
`contradicts` for proposition-to-proposition ClaimRelation. A source passage can
challenge a claim without being a proposition that contradicts another claim.

### 5. Make relation bases non-optional for canonical meaning

`CONTRACTS.md` allows `basis_refs` and `rationale` to be optional. That is safe
for a candidate suggestion, not for an active canonical relation. Require at
least attributable origin plus either exact basis references or a concise
human/rule rationale. Store a machine suggestion as a candidate state if it has
not met that minimum. Otherwise a relation becomes an unexplained edge that
the system cannot audit.

### 6. Treat source acquisition as a boundary, not a schema center

`ARCHITECTURE.md` models `source -> source run/capture -> artifact`, and
`DATA_MODEL.md` splits this into `sources`, `source_policies`, `source_runs`,
and `source_captures`. The distinction is useful for repeat acquisition and
changed URLs, but a one-operator 1.0 can begin with a source identity and an
acquisition observation attached to the artifact. Split runs and captures when
the first discovery adapter needs checkpoints, retry history, or completeness
reporting.

Do not lose the invariant that two captures of changed bytes are distinct
observations and that absence never deletes prior evidence. Simplify the table
shape, not the custody rule.

### 7. Keep profiles and tags extensible without building registries

`CONTRACTS.md` and `DATA_MODEL.md` correctly make profiles, tags, relation types,
and locators extensible. `IMPLEMENTATION_PLAN.md` and `ROADMAP.md` risk turning
that into a package/manifest system too early.

For 1.0, use versioned identifiers and validated local definitions. A profile is
optional data plus validation code; a tag taxonomy is local configuration; a
locator is a small typed validator. Defer installation, sharing, registry, and
third-party package lifecycle until two independent outputs or profiles make
the boundary real.

## Remove/defer

- **Universal `OperationReceipt`** from `DATA_MODEL.md`. Keep an operation ID in
  the one acquisition/import path that needs replay safety; do not make every
  mutation use a distributed-systems pattern.
- **`SourcePolicy` as a full policy engine** from the first schema. Retain a
  source authority label/observation and bounded acquisition configuration;
  defer policy revision machinery until multiple source adapters require it.
- **`SavedQuery` as a 1.0 canonical object** from `DATA_MODEL.md`. Start with
  deterministic query functions/fixtures. Save a query only when operator use
  demonstrates that its definition and version need durable identity.
- **`OutputType`, `OutputInstance`, `OutputState`, and `OutputSnapshot` as a
  package ecosystem** from `CONTRACTS.md` and `DATA_MODEL.md`. Keep a narrow
  read interface and one built-in Hilo proof. Defer portable package manifests,
  output registries, and publication snapshots unless release work requires
  them.
- **`ReviewBatch` as a large independent subsystem** from `CONTRACTS.md`. The
  semantic requirement is a deterministic set plus one attributable decision.
  Implement it only after individual review works; do not let batch machinery
  define all review storage.
- **Full epistemic status and source-authority compatibility rules** from the
  first migration. Preserve source wording and attribution now; add automated
  compatibility validation after concrete claim kinds and source examples show
  that it prevents a real error.
- **Media, XML, JSON, and every locator validator** from the first vertical
  proof. Preserve the extensible locator boundary, but implement only the
  representations used by the fixtures. The contract must permit later kinds
  without making all of them 1.0 requirements.
- **The second output as a release gate** in `IMPLEMENTATION_PLAN.md`,
  `ROADMAP.md`, and `RELEASE_1_0.md` unless it is needed to prove the Hilo
  boundary. A small fixture is valuable; a production agreement tracker is not
  required to establish the core.
- **Release ceremony and supply-chain checklist** in `RELEASE_1_0.md` as
  architecture gates. Keep backup/restore, privacy, parser safety, and version
  identity. Defer packaging ecosystems, signing hierarchy, and broad release
  process until the supported installation path exists.

## Missing

### 1. An explicit distinction between candidate and canonical relation

The documents say machine-only relations are allowed, but `active` can still
sound canonical. Add a small relation lifecycle rule:

```text
candidate -> accepted | rejected
accepted -> superseded | retracted
```

The review axis remains independent. In `supervised`, candidates can be
searchable when policy permits, but queries must be able to exclude them.

### 2. Identity observations and safe merge/split rules

`CONTRACTS.md` mentions aliases/source observations and `DATA_MODEL.md` lists
`entity_aliases`, but neither defines when two labels may resolve to one entity.
Add an explicit `EntityIdentifier/observation` concept, which may be a small
typed record rather than a national ontology. It needs:

- entity-local class, label, identifier scheme/value when available;
- source/evidence and observation time;
- optional validity interval;
- origin and review state;
- merge/split history without deleting the old IDs.

Never auto-merge people from name similarity. Organizations with renamed legal
identities need evidence of continuity; otherwise keep separate entities linked
by an explicit, reviewable relation or note. Projects may retain one entity
with time-bounded aliases only when continuity is supported. Contracts,
expedientes, agreements, and official case numbers should use identifiers tied
to the document/collection or entity, not free-text title matching.

### 3. A rule for document identity versus artifact identity

`DATA_MODEL.md` says one artifact may contain multiple documents, but the
identity operation is not defined. Add a boundary rule: an artifact is bytes;
a CivicDocument is a semantic record anchored to one or more locators in one or
more representations. A concatenated PDF can therefore yield two documents
without copying bytes. A document appearing in two captures remains one
document only when identity evidence supports that conclusion; same title is
not enough.

### 4. A bounded relation-query contract

`ARCHITECTURE.md` permits bounded recursive traversal, but does not define
bounded. Before SQLite, specify maximum depth, direction, relation lifecycle,
review filter, and result cap. Never materialize transitive closure and never
follow shared entity membership as if it were a semantic edge.

### 5. Archive/database backup scope

`RELEASE_1_0.md` and `DATA_MODEL.md` require consistent restore, but the
canonical boundary should state which archive objects are referenced by which
representations and how missing/unreferenced objects are reported. This is a
real operational failure mode, not a future enterprise concern.

## Core model

The irreducible model is seven ideas, not the full table-family list:

1. **Artifact**: bytes ActaKit obtained, preserved by digest and provenance.
2. **Representation**: a readable/inspectable derivative or view of an artifact,
   with lineage and quality information.
3. **CivicDocument**: what the material means institutionally, with source label,
   broad normalized type, and optional profile. It may be unknown.
4. **Claim revision**: a proposition worth finding, checking, correcting, or
   relating. Its exact wording and origin are historical records.
5. **Evidence link**: a claim revision connected to an exact representation
   locator. No claim is source-backed merely because an AI produced it.
6. **Shared anchors**: reviewed or machine-attributed links from claim revisions
   to local entities and tags. They support retrieval and do not imply meaning
   between claims.
7. **Claim relation**: an explicit, attributable proposition-to-proposition
   connection between exact claim revisions, with basis, lifecycle, and review
   visibility.

Review decisions and output projections act on this core. They are not evidence
and do not change claims silently. Document parts and collections are optional
structure attached only when a document package or internal section needs it.

The minimum explanation is:

```text
keep what arrived;
keep how it can be read;
record what it says and where it says it;
connect shared subjects without inventing meaning;
record meaningful connections explicitly;
let a person review or correct the record;
build views from the record without replacing it.
```

## Open decisions before SQLite

These are semantic decisions, not a request to design every table now:

1. **Claim lifecycle**: confirm the three axes above and remove `corrected` and
   `disputed` from any single status enum.
2. **Relation lifecycle**: decide whether candidate and accepted are explicit
   states, and require a basis for accepted relations.
3. **Evidence vocabulary**: resolve the duplicate `contradicts` meaning between
   `EvidenceLink` and `ClaimRelation`.
4. **Revision rule**: decide which records are append-only revisions in 1.0 and
   which use ordinary mutable metadata. Do not require record hashes universally
   until canonical serialization is proven.
5. **Source acquisition minimum**: test whether one acquisition observation is
   enough for the first adapters before splitting run/capture/checkpoint data.
6. **Document identity**: define the evidence threshold for reusing a document
   identity across captures and for mapping parts of one artifact to multiple
   documents.
7. **Entity identity**: define alias, identifier, validity, merge, and split
   behavior. Name similarity alone must never merge people.
8. **Relation query bounds**: set depth, direction, filters, and result limits;
   explicitly reject pairwise expansion through shared anchors.
9. **Review minimum**: make `supervised` the normal path, retain strict for
   protected uses, and implement batch only if a deterministic review fixture
   demonstrates the need.
10. **Archive contract**: define backup, restore, fixity, and missing-object
    behavior before trusting the first SQLite database.
11. **First proof scope**: choose the smallest fixtures that cover PDF/text,
    spreadsheet or table evidence, unknown type, a corrected claim, a shared
    entity, and one explicit relation. Do not make every future representation
    a migration prerequisite.

## Recommended next patch

Make a documentation-only reduction patch before any SQLite migration:

1. Add a `Core now / Optional proof / Later` classification to
   `docs/DATA_MODEL.md` and remove the appearance that every listed family is a
   required table.
2. Amend `docs/CONTRACTS.md` to define non-overlapping claim/relation state axes,
   candidate relations, evidence-side vocabulary, and the minimum relation
   basis.
3. Add identity observation, official identifier, merge, split, and
   document/artifact identity rules without introducing a national ontology.
4. Reduce `docs/IMPLEMENTATION_PLAN.md` and `docs/ROADMAP.md` to a first proof
   that exercises the core, then explicitly defer operation receipts, saved
   queries, output package sharing, broad locator implementations, and rich
   policy engines.
5. Keep `docs/ARCHITECTURE.md` as the human explanation, but move table-like
   detail out of its core narrative.
6. Only then create a pre-SQL fixture specification and review it against the
   reduced concepts. This review authorizes no schema or production code.

## ELI5 summary

ActaKit is a careful filing cabinet for public civic information.

First, it keeps the original things it found, such as a PDF, spreadsheet, or
recording. Then it keeps ways to read those things, such as extracted text or
OCR. A reader, which can be software or a person, writes down useful claims and
the exact place where each claim came from.

Claims are not automatically treated as truth. The cabinet remembers whether a
claim was only machine-found, reviewed by a person, rejected, or replaced by a
new wording. It can also connect claims when there is a real reason, such as one
announcement updating an earlier one. Merely mentioning the same place does not
pretend that two claims agree or disagree.

Names are handled carefully: different names may refer to the same organization
or project, but similar names alone do not merge people. Unknown documents are
kept rather than forced into the wrong category.

Searches and products such as a Hilo are views over the filing cabinet. They can
organize and export what is there, but they cannot silently rewrite the evidence.
The first version should be a small local system for one or two operators, not a
graph database, corporate permissions system, or network service.
