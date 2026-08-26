---
id: ACTAKIT-SQLITE-CANDIDATE-001
kind: schema-candidate
state: prerelease-0001-rebaseline-design-accepted__implementation-pending
created: 2026-08-21
updated: 2026-08-26
authority: design-proposal
baseline: 310d060cc1ced3640892a0dc29a7fbcb2c010920
summary: Existing SQLite 1.0 baseline is certified; accepted Derivation/Verification reconciliation now requires one bounded prerelease 0001 rebaseline and full applicable recertification.
---

# SQLite Schema Candidate

## Status and rule

This document is a **candidate**, not migration `0001`. The first candidate at
`8b98010` fit the semantic fixtures at a high level but the adversarial review
found several places where it silently dropped already-accepted contract meaning
or encoded an impossible/unsafe SQLite shape. Those faults were repaired and the resulting
pre-Derivation baseline was independently certified. The accepted 2026-08-26
Derivation/Verification reconciliation now advances this candidate ahead of the current production
`0001`: section 29 freezes the next prerelease rebaseline delta, but production DDL remains at the
last certified hash until that bounded implementation and full applicable recertification pass.

Design rule:

> Store civic authority in explicit relational records. Use JSON only at bounded,
> versioned selector/state seams whose shape is selected by a closed kind/version
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

Only the Canario core writes canonical tables. Outputs, importers, AI readers,
and external tools use core contracts; they do not write SQLite directly.

Logical civic/custody identity and physical byte deduplication are distinct. Two
captures may retain independent Artifact provenance while referencing one shared
archive object. A digest therefore identifies physical content, **not** the
semantic/custody record.

## 2. SQLite operating invariants

### Runtime floor

Initial supported SQLite version: **3.53.4 or newer**.

Reason: Canario intentionally uses WAL and long-lived evidence custody. SQLite's
WAL-reset corruption bug affected ordinary upstream releases through 3.51.2 and
was first fixed in 3.51.3, but the intervening 3.52.0 release was withdrawn. For
a new no-legacy deployment, the support set therefore starts at 3.53.4, the
current stable maintenance release at this review boundary, rather than using a
numeric floor that accidentally admits a withdrawn release. The packaged runtime
must still be certified by exact version/source ID and required compile options.
The numeric floor is necessary but **not sufficient**: Canario uses a positive
registry of runtime releases/source IDs that have passed this proof suite. An
unknown newer SQLite is rejected until certified rather than being trusted merely
because its version number compares greater. The initial certification target is
SQLite 3.53.4 with upstream `SQLITE_SOURCE_ID`
`2026-07-24 19:02:57 bf7c7f30031888f4e796e429ab3978879485813aaca6f641c7b33e4e09459bcc`.

Required runtime capabilities for `0001` are deliberately small:

- FTS5 compiled in (`ENABLE_FTS5`);
- SQLite mutex/thread-safety code present (`THREADSAFE=1|2`, never `0`);
- WAL, foreign keys and trigger support not omitted (`OMIT_WAL`,
  `OMIT_FOREIGN_KEY`, `OMIT_TRIGGER` are disallowed);
- functional startup probes must actually create/use `STRICT`, FTS5, WAL and
  enforced foreign keys rather than trusting compile-option strings alone.

No JSON SQL extension is required by the schema: selector JSON is validated by
Canario core contracts, not by making SQLite a JSON-domain authority.

All canonical ordinary tables are `STRICT`. FTS5 virtual tables are the explicit
exception.

Every writable connection must establish and verify at open time:

```text
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = FULL;
PRAGMA trusted_schema = OFF;
PRAGMA secure_delete = ON;
```

These are **connection-opening invariants**, not a bundle of settings that backup
bytes are assumed to preserve. In particular, `secure_delete` defaults are
compile/runtime dependent; a clean-machine restore must open the restored database
through the same invariant initializer before it is accepted as writable authority,
then verify every required PRAGMA. `application_id`/`user_version` remain file
identity checks; WAL mode is also explicitly re-established/verified rather than
trusted implicitly.

The implementation must also set and verify a bounded busy timeout, keep write
transactions short, and reject unsupported SQLite versions. Canario reserves SQLite
`application_id = 0x414B4954` (`AKIT`, decimal `1095453012`) and migration `0001`
uses `user_version = 1`; every canonical connection verifies both before treating
the file as Canario authority. While Canario remains pre-release and has no public
compatibility boundary, schema changes rebaseline `0001` and may keep
`user_version = 1`; they must repeat the applicable freeze/runtime certification
rather than accumulating `0002`, `0003`, ... for disposable development databases.
After the explicit Beta/public compatibility boundary, forward migrations advance
`user_version` through the migration mechanism rather than changing
`application_id`. A connection that cannot
establish the required invariants is not a writer.

SQLite/WAL must live on local attached storage, never a synced/network filesystem.
There is one canonical writer/checkpoint authority. Readers must not keep
unbounded read transactions open. WAL size/checkpoint health is operationally
observable rather than assumed.

`secure_delete = ON` is a baseline defense, **not** a claim of device-level secure
erasure. Exceptional purge has stronger maintenance rules in section 16.

## 3. ID and revision rules

- Stable civic identities use opaque text IDs, UUIDv7-compatible with readable
  prefixes at the API boundary (`src_`, `acq_`, `aob_`, `art_`, `rep_`, `doc_`,
  `clm_`, `ent_`, `rel_`, `ras_`, ...).
- External numbers, URLs, filenames, acta numbers, names, and hashes are
  identifiers/attributes, never primary identity.
- Material semantic changes use append-only revisions where history matters.
- Revision rows point to the exact prior revision they supersede; revisioned stable
  identities are **linear histories**, not revision DAGs. Numbered families use
  revision 1 as the only root, later revisions must name a predecessor, and a row
  may have at most one successor. Core write validation also requires monotonically
  consecutive revision numbers. Supersession/current-leaf state is derived without
  mutating the old row.
- Candidate/active/rejected transitions on revisioned/link-like semantic records
  are append-only: promotion or correction writes a new revision/link/reconciliation
  that supersedes the prior row. A superseded row has at most one successor;
  competing proposals start as independent candidate roots rather than branching an
  accepted history. Review decisions never rewrite the reviewed row.
- `created_at` is stored as UTC RFC3339 text with subsecond precision; civic
  source dates/periods are separate domain fields. Date-only civic values are
  normalized as ISO `YYYY-MM-DD`; any interval comparison in SQLite is permitted
  only after core validation has established the normalized form.
- Foreign keys are real SQLite FKs wherever the target type is known. Avoid a
  universal polymorphic `subject_type + subject_id` table that forfeits FK
  integrity.
- Genuinely optional fields never participate in a composite primary key. This
  matters under `STRICT`, where every PK component is implicitly `NOT NULL`.
- Operation retries preallocate stable opaque IDs and timestamps before the write
  transaction. Retrying the same operation reuses those IDs: a PK collision is
  treated as success only after the core verifies the existing immutable payload is
  identical; a different payload under the same ID is a hard collision. `0001`
  deliberately has no generic idempotency table and canonical writes never use
  `INSERT OR REPLACE`.

## 4. Closed 1.0 vocabularies

These are the initial semantic enums. Adding a new value is a deliberate contract
change, not arbitrary text written by importers.

```text
source_kind:
  web | api | feed | filesystem | manual | other

source_authority_scope:
  formal_record | recorded_speech | issuer_statement | reported_statement |
  dataset_value | visual_record | other

acquisition_outcome:
  success | partial | not_found | failed

acquisition_artifact_role:
  primary | attachment | response_body | other

process_outcome:
  success | partial | failed

artifact_validation:
  pending | verified | quarantined | rejected

availability:
  available | restricted | purged

representation_kind:
  original | extracted_text | ocr_text | normalized_text | table | page_image |
  transcript | redacted_derivative | other

document_type:
  unknown | acta | agenda | convocatoria | acuerdo | resolucion | oficio |
  informe | dictamen | presupuesto | plan | reglamento_ordenanza |
  aviso_publico | correspondencia | comunicado_prensa | contrato | dataset |
  grabacion | otro

document_visibility:
  normal | restricted

document_occurrence_kind:
  whole | contained | attachment | other

entity_name_kind:
  official | alias | former | display | other

mention_resolution_state:
  resolved | cleared

entity_reconciliation_kind:
  merge | split

claim_kind:
  source_assertion | derived_inference | community_report | verification_question

origin_kind:
  machine | rule | human

claim_lifecycle:
  active | rejected | retracted | restricted
  # superseded is derived from a later revision's supersedes_revision_id

evidence_relation:
  supports | challenges | contextualizes | quotes | mentions

entity_kind:
  person | organization | place | project | legal_instrument | contract |
  program | other

relation_type:
  updates | contradicts | corrects | responds_to | implements | supersedes |
  same_matter_as | other
  directed: updates | corrects | responds_to | implements | supersedes | other
  symmetric: contradicts | same_matter_as

relation_basis_kind:
  source_evidence | analyst_inference | mechanical_identity | other

relation_lifecycle:
  candidate | active | rejected
  # superseded is derived from revision/link/reconciliation lineage

semantic_link_lifecycle:
  candidate | active | rejected
  # for correctable semantic metadata/links such as EvidenceLink, identity metadata,
  # document occurrence/classification, ClaimEntityLink / ClaimTagLink / EntityReconciliation

review_mode:
  strict | batch | supervised

review_decision:
  accepted | rejected | needs_work

evidence_basis_role:
  source_basis | context

derivation_outcome:
  success | failed

derivation_lineage_state:
  exact | partial | unavailable | none

verification_outcome:
  completed | failed

verification_verdict:
  supported | contradicted | insufficient_evidence

verification_sufficiency:
  sufficient | insufficient

verification_derivation_use_state:
  attempted | consumed

verification_evidence_role:
  supports | challenges | context

assessment_judgment:
  supported | contested | refuted | unresolved

purge_target_kind:
  source | source_authority_scope | source_locator | acquisition | acquisition_artifact |
  archive_object | artifact | process_run | process_run_egress |
  derivation_run | derivation_run_egress | derivation_result | derivation_result_target |
  verification_run | verification_run_egress | assessment |
  quality_evidence | quality_decision | representation | representation_target | civic_document |
  civic_document_revision | document_identifier | document_identifier_review |
  document_classification | document_classification_review | document_representation |
  document_representation_review | claim | claim_revision | evidence_link | evidence_link_review |
  entity_mention | entity | entity_name | entity_name_review | entity_identifier |
  entity_identifier_review | mention_resolution_candidate |
  mention_resolution_revision | entity_reconciliation | claim_entity_link |
  claim_entity_link_review | entity_reconciliation_review | tag | claim_tag_link |
  claim_tag_link_review | claim_relation | claim_relation_revision | claim_relation_evidence_link |
  role_assignment | role_assignment_revision | role_assignment_evidence_link | review_action |
  claim_review | claim_relation_review | mention_resolution_candidate_review |
  role_assignment_review

purge_action:
  delete_record | scrub_payload | detach | delete_bytes
```

Local taxonomies and registered adapter contracts remain deliberately open text rather
than global enums. In `0001` this includes tag namespaces/keys, normalized role
keys, identifier schemes, locator kinds, selector kind/version, process kinds,
adapter keys/versions, parser profile keys/versions, error codes, execution-venue
keys, quality signal/policy keys and versions, egress/data-control profile keys, and
implementation/model identifiers. These values are validated by the owning registry/adapter contract;
they are not permission for arbitrary unregistered strings.

## 5. Source and acquisition — Depósito ingress

### `sources`

Stable bounded public information source/family being observed.

```text
id PK
kind                     -- source_kind
name
active
created_at
```

A municipal acta archive and the same municipality's press-release feed may be
separate Sources because their authority scopes differ.

### `source_authority_scopes`

Persist the bounded kinds of statements a source family can reasonably evidence.
This guides extraction without laundering “official-looking” material into
universal truth.

```text
id PK
source_id FK -> sources
scope_kind               -- source_authority_scope
valid_from nullable
valid_to nullable
note nullable
created_at
```

Examples:

```text
approved acta archive -> formal_record
session recordings    -> recorded_speech
municipal news feed    -> issuer_statement
budget dataset         -> dataset_value
```

### `source_locators`

Observed/known addresses for a source. URI change does not change source identity.
`SourceLocator` is the stable known address, not a validity episode: observation
history belongs to `Acquisition.observed_at`. Re-observing an old URI later therefore
does not require manufacturing a second locator row.

```text
id PK
source_id FK -> sources
locator
locator_kind
created_at
UNIQUE(source_id, locator)
UNIQUE(id, source_id)              -- supports same-Source composite FK from Acquisition
```

### `acquisitions`

One observation/attempt at a specific time. Absence/failure is an observation,
not deletion.

```text
id PK
source_id FK
source_locator_id FK nullable
observed_at
outcome                  -- acquisition_outcome
http_status nullable
adapter_key
adapter_version
error_code nullable
created_at
FK(source_locator_id, source_id) -> source_locators(id, source_id)
```

If a locator is present, it must belong to the same Source as the Acquisition; a
plain independent FK would permit an impossible observation such as “acquire
Source A through Source B's locator”. No universal crawl event log is required.
This record exists because acquisition identity is itself semantically necessary.

## 6. Physical archive objects vs logical custody

### `archive_objects`

Physical content-addressed storage object. This is where byte deduplication lives.

```text
id PK
content_sha256 nullable
byte_size nullable
storage_key nullable
availability             -- available | purged
created_at
purged_at nullable
```

While retained:

```text
UNIQUE(content_sha256) WHERE content_sha256 IS NOT NULL
UNIQUE(storage_key) WHERE storage_key IS NOT NULL
```

While `availability=available`, digest, byte size and storage key are all
required; their column nullability exists only so an allowed purge tombstone can
clear recoverable storage metadata. A purge policy may require clearing those
fields. Stable `archive_object` identity survives only when the selected tombstone
policy permits it.

### `artifacts`

Logical custody record for bytes captured from a source observation. Artifact
identity is not its digest.

```text
id PK
archive_object_id FK -> archive_objects nullable
media_type nullable
validation_state       -- artifact_validation
availability           -- available | restricted | purged
created_at
purged_at nullable
```

Two captures of identical bytes may point to one `archive_object` while retaining
separate Artifact IDs and separate provenance/restriction/purge decisions. Core
transaction validation also enforces the cross-row availability invariant: every
retained Artifact points to an `available` ArchiveObject; an ArchiveObject cannot
be marked purged while any retained Artifact or material derivative still depends
on it.

### `acquisition_artifacts`

One acquisition may yield multiple logical artifacts. Each Artifact belongs to
exactly one acquisition observation: repeated identical bytes create a new
Artifact but may reuse the same physical `archive_object`. This keeps capture
provenance, restriction and purge decisions independent.

```text
artifact_id PK FK
acquisition_id FK
role                    -- primary | attachment | response_body | other
observed_filename nullable
observed_url nullable
```

## 7. Representations and process provenance — Mesa de trabajo

### `representations`

Derived or directly usable inspectable forms. Originals are never overwritten by
OCR, normalization, redaction, or edited derivatives.

```text
id PK
artifact_id FK nullable            -- required while retained; nullable only in an allowed purge tombstone
archive_object_id FK nullable      -- derivative bytes only; original bytes are inherited from Artifact
parent_representation_id FK nullable
kind                              -- representation_kind
media_type nullable
language nullable
charset nullable
process_run_id FK nullable
availability                     -- available | restricted | purged
created_at
purged_at nullable
```

Every available/restricted Representation belongs to one retained logical Artifact
custody chain; a retained material derivative also points to an `available`
ArchiveObject. These cross-row availability rules are core transaction invariants
because row CHECK constraints cannot inspect the referenced row's lifecycle. If
`parent_representation_id` is present, a composite FK requires parent
and child to carry the same `artifact_id`; a derivative cannot silently jump to a
different capture. A purge tombstone may clear those links only under the explicit
purge policy.

`original` is a view of the Artifact's captured bytes, not a second custody byte
pointer: while retained it has no `archive_object_id`, no parent and no
`process_run_id`, and there is at most one original Representation per Artifact.
The original's physical bytes resolve through `Artifact.archive_object_id`.
Every retained non-original Representation is a material derivative: it has its
own `archive_object_id`, an exact same-Artifact parent Representation, and the
`process_run_id` that created it. This prevents an impossible state where an
"original" silently points to bytes other than its Artifact, and it prevents a
derivative from existing without an attributable transformation input.

`parent_representation_id + process_run_id` therefore gives the exact
transformation input and generator provenance without a generic process-output
graph. Creating the one required original Representation together with a retained
Artifact is a core transaction invariant; the partial unique index enforces only
"at most one" because SQLite cannot express "at least one child row" with a row
CHECK. A future transformation that genuinely combines multiple Artifacts needs a
separately proven typed input contract rather than abusing one parent pointer.

### `process_runs`

Bounded terminal provenance for one completed processing attempt. This is **not**
a scheduler/job table and not universal event sourcing.

```text
id PK
process_kind                 -- registered semantic capability/process key
implementation               -- trusted adapter/executor identity
implementation_version
execution_venue              -- registered venue key; orthogonal to capability
configuration_hash nullable  -- non-secret canonical configuration identity
model_provider nullable
model_name nullable
started_at
finished_at
outcome                      -- success | partial | failed
error_code nullable           -- required for failed; absent for success
created_at
```

`outcome` records technical execution only. It is never reused for the quality
decision. Failed runs remain durable provenance but cannot authorize derivative
Representations.

### `process_run_inputs`

Ordered exact RepresentationTarget scope for every terminal run:

```text
process_run_id FK
ordinal >= 0
representation_id
representation_target_id
PK(process_run_id, ordinal)
UNIQUE(process_run_id, representation_target_id)
composite FK (representation_target_id, representation_id)
  -> representation_targets(id, representation_id)
```

This preserves exact page/block/table/whole scope even when execution fails and no
derivative exists. Whole-document processing uses an explicit `whole:v1` target;
absence of a target never implicitly means whole document. A selected multi-target
run preserves deterministic target order.

### `process_run_egress`

Optional non-secret egress provenance for runs whose trusted adapter is authorized to
send source material outside the local deployment. The byte count means measured
source/evidence payload bytes handed to the external executor, not guessed total
wire/protocol traffic. Zero preserves truthful policy provenance when local preparation
fails before handoff:

```text
process_run_id PK/FK
bytes_egressed >= 0
policy_profile
data_control_profile
request_template_hash nullable
endpoint_profile nullable
created_at
```

Credentials, account identity, OAuth/API tokens, environment dumps and secret
paths are forbidden. Core policy also verifies that local runs have no egress row
and that cloud/agent runs were explicitly authorized before invocation.

### `quality_evidence`

Processor-attributable runtime evidence for one exact run target:

```text
id PK
process_run_id FK
ordinal >= 0
representation_id
representation_target_id
signal_key
signal_version
payload_json                 -- validated by registered bounded contract
interpretation_key nullable
created_at
UNIQUE(process_run_id, ordinal)
UNIQUE(process_run_id, representation_target_id, signal_key, signal_version)
composite target/representation FK
composite run/target FK -> process_run_inputs(process_run_id, representation_target_id)
```

`signal_key + signal_version` is registered in core/adapter composition. The JSON
column is only a storage encoding for a validated bounded payload; it is not an
arbitrary metadata bag and there is no universal confidence signal.

### `quality_decisions`

One durable policy decision per exact ProcessRun input target:

```text
id PK
process_run_id FK
representation_id
representation_target_id
decision                     -- accept | escalate | quarantine_review
policy_key
policy_version
reason_code
next_capability_key nullable  -- required only for escalate
created_at
UNIQUE(process_run_id, representation_target_id)
composite target/representation FK
composite run/target FK -> process_run_inputs(process_run_id, representation_target_id)
```

A technically successful OCR run may therefore persist `outcome=success` while
its target decision is `escalate`. Policy evolution appends new ProcessRuns/
decisions; it does not rewrite the old execution or its signals.

Every derived Representation (anything other than `original`) still points
directly to the exact ProcessRun that created it and to its same-Artifact parent.
`process_run_inputs` does not create a generic process graph: it exists only to
retain otherwise-lost exact Workbench input scope. Semantic rows continue to use
their typed FKs/EvidenceLinks rather than this table as a generic provenance edge.

## 8. Reusable exact representation targets

The first candidate duplicated selector payloads in EvidenceLink and
EntityMention and could not naturally attach exact source evidence to a
ClaimRelation or rich association. `representation_targets` factors only the
**where in this representation** concern; semantic link tables remain typed.

### `representation_targets`

```text
id PK
representation_id FK
selector_kind nullable
selector_version nullable
selector_payload_json nullable
state_payload_json nullable
availability              -- available | purged
created_at
purged_at nullable
```

A normal target has non-null selector kind/version/payload and must validate
against its registered contract. A minimal purge tombstone may retain the stable
target ID and parent Representation while clearing selector material and setting
`availability=purged`; no EvidenceLink then falsely resolves to content that no
longer exists.

JSON is allowed only under a registered `selector_kind + selector_version`
contract validated by core code.

### Initial selector contracts

`whole:v1`

```json
{}
```

Use only when the entire representation is genuinely the smallest honest target.

`text_quote:v1`

```text
required: exact
optional: prefix, suffix, start_char, end_char
rules:
  - exact is non-empty
  - offsets address the decoded text Representation, not the source PDF/HTML bytes
  - start_char/end_char are 0-based Unicode-code-point offsets
  - start_char is inclusive; end_char is exclusive
  - start/end either both absent or both present
  - 0 <= start_char < end_char <= text length
  - when offsets are present, text[start_char:end_char] == exact exactly
```

`pdf_page:v1`

```text
required: page_ordinal
optional: page_label
rules:
  - page_ordinal is a 1-based physical page sequence
  - page_label is corroborating display metadata, never the physical coordinate
  - this selector denotes the full physical page as a processing scope
```

`pdf_page_quote:v1`

```text
required: page_ordinal
optional: exact, prefix, suffix, page_label
rules:
  - page_ordinal is a 1-based physical page sequence
  - page_label is corroborating display metadata, never the physical coordinate
  - when machine-readable text exists, exact quote is preferred
  - v1 quote matching applies Unicode NFC, collapses each Unicode-whitespace run
    to one ASCII space, and trims outer whitespace
  - v1 performs no case folding, punctuation substitution, dehyphenation, or OCR repair
```

`table_range:v1`

```text
optional: sheet, table_name, a1_range, row_start, row_end, headers, observed_values
rules:
  - at least one structural coordinate is required
  - row_start/row_end are 1-based inclusive row ordinals within the represented table
  - row_start/row_end either both absent or both present, with 1 <= start <= end
  - a1_range uses standard A1 coordinates only when the represented format preserves them
  - sheet/table_name are used only when those names exist in the Representation
  - headers, when supplied, preserve ordered observed header labels
  - observed_values preserves the exact selected cell values used to make the claim when practical
```

The payload may contain redundant coordinates because durable evidence targeting
sometimes needs both quote/context and position. These are bounded selector
bundles, not arbitrary application JSON.

## 9. Civic document identity

### `civic_documents`

Stable logical document identity only, independent of bytes, encoding and mutable
metadata.

```text
id PK
created_at
```

### `civic_document_revisions`

```text
id PK
document_id FK
revision_no
supersedes_document_revision_id FK nullable
title nullable
issuer_entity_id FK nullable
document_date nullable
language nullable
visibility               -- normal | restricted
origin_kind              -- human | rule | machine
process_run_id FK         -- required for machine/rule; optional for human
created_at
UNIQUE(document_id, revision_no)
```

Title/issuer/date/language are civic metadata, not document identity. Ordinary
correction or improved extraction therefore writes a new revision and preserves
the old values. The self-FK is scoped to the same stable CivicDocument.
Classification remains a separate append-only observation because source-supplied
type and normalized interpretation have different semantics.

### `document_identifiers`

Document identifiers participate in identity resolution, so they are attributable
and correctable rather than immortal strings attached to a Document.

```text
id PK
supersedes_document_identifier_id FK nullable
document_id FK
scheme
value
issuer_entity_id FK nullable
representation_target_id FK nullable
origin_kind              -- human | rule | machine
process_run_id FK         -- required for machine/rule; optional for human
lifecycle                 -- candidate | active | rejected
rationale nullable
created_at
```

A correction supersedes a prior identifier **for the same CivicDocument**; the old
value remains auditably historical but is not a current identifier leaf. Multiple
independent active identifiers are legitimate because a document may carry several
schemes. Identifier uniqueness across documents is **not** globally assumed unless
a scheme contract proves it. Scheme-specific uniqueness is validated by the core;
nullable issuer scope is not hidden inside a fragile SQL UNIQUE key.

### `document_classifications`

Append-only classification history. Source wording and normalized interpretation
live in the same attributable observation rather than silently overwriting each
other. Classification is query-significant semantic metadata, so a mistaken parser
result must be rejectable/correctable without deletion.

```text
id PK
supersedes_document_classification_id FK nullable
document_id FK
source_supplied_type nullable
source_type_label nullable
normalized_type          -- document_type
subtype nullable
profile_key nullable
profile_version nullable
confidence nullable
representation_target_id FK nullable
origin_kind              -- human | rule | machine
process_run_id FK         -- required for machine/rule; optional for human
lifecycle                 -- candidate | active | rejected
rationale nullable
created_at
```

Current classification is the non-superseded active leaf. Core transaction
validation permits competing **candidate** roots but rejects more than one
non-superseded `active` classification for the same CivicDocument.

### `document_representations`

One representation may contain multiple documents; one logical document may have
multiple representations; the same document may occur more than once in a
compound representation.

```text
id PK
supersedes_document_representation_id FK nullable
document_id FK
representation_id FK
occurrence_kind          -- whole | contained | attachment | other
representation_target_id FK nullable
origin_kind              -- human | rule | machine
process_run_id FK         -- required for machine/rule; optional for human
lifecycle                 -- candidate | active | rejected
rationale nullable
created_at
```

If `representation_target_id` is present, its representation must match
`representation_id`. The composite FK enforces that ownership. Detection of a
Document occurrence can itself be wrong (especially in compound PDFs), so the
mapping is attributable and corrected by same-Document supersession rather than
deleting the prior occurrence. Multiple independent active occurrences remain
valid when the same logical Document genuinely appears in multiple Representations.

### `document_parts` / `document_collections` decision

They are **not in `0001`**. AKF-004 is satisfied by independent CivicDocument IDs
plus repeated `document_representations` occurrences with exact targets. No
current artifact-backed fixture requires a separately citable part identity or a
durable cross-document case/package identity. Both structures are purely
additive later because CivicDocument identity and occurrence targets are already
separate.

This is a closed 1.0 decision, not permission to stuff collection semantics into
JSON.

## 10. Claims and evidence — Fichero

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
supersedes_revision_id FK nullable
claim_kind               -- claim_kind
text
origin_kind              -- machine | rule | human
process_run_id FK nullable -- required for machine/rule non-derived origin; optional extra phrasing provenance on derived claims
derivation_result_target_id FK nullable -- required exactly for derived_inference
attribution_entity_id FK nullable
attribution_text nullable
temporal_start nullable
temporal_end nullable
sensitive                 -- boolean
quantitative              -- boolean
lifecycle                 -- claim_lifecycle
created_at
UNIQUE(claim_id, revision_no)
```

A claim can exist machine-only. Human review is a separate axis. `corrected` is
not a status: correction creates a new revision whose `supersedes_revision_id`
points to the exact prior revision. The prior revision becomes *effectively
superseded* by lineage rather than being rewritten.

`claim_kind=derived_inference` requires one exact available `DerivationResultTarget` as analytical
origin; non-derived Claim kinds must not populate that field. A distinct ProcessRun may additionally
be recorded when a semantic process materially phrases/normalizes the derived Claim, but it is not
the analytical basis. The result target identifies its DerivationRun transitively and no
polymorphic `origin_type/origin_id` is introduced.

Contradiction/dispute is not a truth flag on the row. No universal
`epistemic_status` column exists.

`temporal_start/end` are optional normalized civic scope, not creation time. More
complex uncertainty/recurrence is not forced into `0001`; the exact source
wording remains in the Claim/Evidence.

### `evidence_links`

Evidence is revision-bound and targets a reusable exact representation location.
The link itself is semantic: a locator can be wrong, or `supports` can later be
judged `contextualizes`/`challenges`. That correction must not erase the historical
link.

```text
id PK
supersedes_evidence_link_id FK nullable
claim_revision_id FK
representation_target_id FK
relation                 -- evidence_relation
origin_kind              -- machine | rule | human
process_run_id FK         -- required for machine/rule; optional for human
lifecycle                 -- candidate | active | rejected
rationale nullable
created_at
```

Supersession is constrained to the same ClaimRevision and is linear. Multiple
independent EvidenceLinks may coexist. A source assertion counts as evidenced only
through at least one **non-superseded active `supports` link** whose
RepresentationTarget remains available. For `derived_inference`, an active `supports` link must
also mechanically overlap the source-contribution lineage of the Claim's exact
DerivationResultTarget under the registered selector-containment contract. Independent
`challenges` evidence remains legal and need not have participated in the original calculation.
Cross-table minima are semantic-core invariants rather than fake CHECK constraints. Review remains
a separate axis.

## 11. Raw mentions and entity identity

### `entity_mentions`

Raw observed occurrence **before** reconciliation.

```text
id PK
representation_target_id FK
claim_revision_id FK nullable
observed_text
origin_kind              -- machine | rule | human
process_run_id FK         -- required for machine/rule; optional for human
created_at
```

The exact mention is never overwritten by canonical naming. Core validation
requires the target to identify the source occurrence being preserved.

### `entities`

```text
id PK
kind                     -- entity_kind
canonical_name nullable
created_at
```

`canonical_name` is a local display convenience, not evidence and not identity.

### `entity_names`

Names/aliases are retrieval and reconciliation inputs, not timeless properties.
They therefore retain attributable source context and correction lineage.

```text
id PK
supersedes_entity_name_id FK nullable
entity_id FK
name
name_kind                -- official | alias | former | display | other
representation_target_id FK nullable
valid_from nullable
valid_to nullable
origin_kind              -- machine | rule | human
process_run_id FK         -- required for machine/rule; optional for human
lifecycle                 -- candidate | active | rejected
rationale nullable
created_at
```

A corrected/rejected alias supersedes a prior row for the **same Entity**; it does
not rewrite raw EntityMentions. Multiple independent active names are legitimate.

### `entity_identifiers`

Identifiers are stronger identity inputs than names and receive the same bounded
provenance/correction treatment.

```text
id PK
supersedes_entity_identifier_id FK nullable
entity_id FK
scheme
value
issuer_entity_id FK nullable
representation_target_id FK nullable
origin_kind              -- machine | rule | human
process_run_id FK         -- required for machine/rule; optional for human
lifecycle                 -- candidate | active | rejected
rationale nullable
created_at
```

Global uniqueness is not assumed for an arbitrary scheme. Schemes that prove a
strong uniqueness scope receive explicit core validation/indexing rather than
pretending every `(scheme,value)` is globally unique. An operative
EntityReconciliation may use identifier basis only while those exact identifier
rows remain non-superseded and active; correcting identity evidence therefore
forces the dependent reconciliation to be revisited/superseded instead of silently
continuing on stale evidence.

### `mention_resolution_candidates`

Machine/rule/human suggestions are proposals, not current identity.

```text
id PK
mention_id FK
entity_id FK
score nullable
origin_kind              -- machine | rule | human
process_run_id FK         -- required for machine/rule; optional for human
created_at
```

### `mention_resolution_revisions`

Accepted current resolution is append-only and reversible.

```text
id PK
mention_id FK
revision_no
resolved_entity_id FK nullable
resolution_state         -- resolved | cleared
origin_kind              -- machine | rule | human
process_run_id FK         -- required for machine/rule; optional for human
actor nullable
rationale nullable
created_at
UNIQUE(mention_id, revision_no)
```

No resolution row means unresolved. `cleared` explicitly removes a prior
resolution without deleting history. Current resolution is the highest revision
number. A strong deterministic rule may resolve a mention without human review;
the origin remains visible.

### `entity_reconciliations`

Narrow append-only merge/split lineage.

```text
id PK
supersedes_entity_reconciliation_id FK nullable
kind                     -- merge | split
origin_kind              -- machine | rule | human
process_run_id FK         -- required for machine/rule; optional for human
actor nullable
rationale
lifecycle                 -- candidate | active | rejected
created_at
```

### `entity_reconciliation_inputs` / `entity_reconciliation_outputs`

```text
reconciliation_id FK
entity_id FK
PRIMARY KEY(reconciliation_id, entity_id)
```

### `entity_reconciliation_basis_mentions`

```text
reconciliation_id FK
mention_id FK
PRIMARY KEY(reconciliation_id, mention_id)
```

### `entity_reconciliation_basis_identifiers`

```text
reconciliation_id FK
entity_identifier_id FK
PRIMARY KEY(reconciliation_id, entity_identifier_id)
```

Core validation enforces the actual operation shape before an operative row is
committed: `merge` has at least two distinct inputs and exactly one output; `split`
has exactly one input and at least two distinct outputs. Input and output may share
an Entity when a surviving local ID is intentionally retained.

Old entity IDs remain explainable; historical claim anchors are not silently
mass-retargeted. Candidate promotion/correction is append-only: a new reconciliation
row may supersede the prior candidate rather than mutating it in place. Current
retrieval considers only non-superseded operative reconciliation rows and the
applicable review policy. Splits do not silently decide which old ambiguous link
belongs to which output entity. Review is recorded separately in section 15.

## 12. Claim anchors and tags

### `claim_entity_links`

The first candidate used nullable `role` and `mention_id` inside the composite PK,
which is incompatible with `STRICT`. Links therefore receive their own identity.

```text
id PK
supersedes_claim_entity_link_id FK nullable
claim_revision_id FK
entity_id FK
mention_id FK nullable
mention_resolution_revision_id FK nullable
role nullable
origin_kind              -- machine | rule | human
process_run_id FK         -- required for machine/rule; optional for human
lifecycle                -- candidate | active | rejected
rationale nullable
created_at
```

A machine resolution candidate does not automatically become an active shared
anchor. A mention-derived ClaimEntityLink points to the **exact accepted
MentionResolutionRevision** that resolved that same mention to that same Entity;
composite FKs enforce both same-Claim context and same resolved Entity. `mention`
and `mention_resolution_revision` are therefore both present or both absent. A
direct claim-level anchor not derived from a literal mention leaves both null.

ClaimEntityLink is append-only semantic metadata, not a mutable cache. If an
anchor itself is corrected, a new row supersedes the prior link for the same
ClaimRevision; the old row remains explainable. Current retrieval uses the
non-superseded operative link and, for mention-derived anchors, can verify that
its resolution revision is still the current accepted resolution. This prevents a
later `AyA -> different Entity` correction from leaving a stale anchor that looks
current. Idempotency remains a core write invariant; optional fields are not
abused as primary-key components.

### `tags`

```text
id PK
namespace
key
label
created_at
UNIQUE(namespace, key)
```

### `claim_tag_links`

```text
id PK
supersedes_claim_tag_link_id FK nullable
claim_revision_id FK
tag_id FK
origin_kind              -- machine | rule | human
process_run_id FK         -- required for machine/rule; optional for human
lifecycle                -- candidate | active | rejected
rationale nullable
created_at
```

A tag is a shared retrieval anchor, so its assignment must be correctable without
deleting history or forcing a new ClaimRevision merely to fix metadata. The same
append-only rule therefore applies as for ClaimEntityLink: a correction/rejection
supersedes the prior link for that exact ClaimRevision, while review is recorded
separately. Current retrieval uses only the non-superseded operative assignment.
Tag taxonomies remain local/extensible; the core does not impose a national civic
ontology or tag hierarchy.

## 13. Direct ClaimRelations with inspectable basis

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
supersedes_relation_revision_id FK nullable
from_claim_revision_id FK
to_claim_revision_id FK
relation_type            -- relation_type
origin_kind              -- machine | rule | human
basis_kind               -- relation_basis_kind
rationale nullable
process_run_id FK         -- required for machine/rule; optional for human
lifecycle                -- relation_lifecycle
created_at
UNIQUE(claim_relation_id, revision_no)
```

Origin and basis are separate. `machine` says **who/what proposed it**;
`source_evidence` or `analyst_inference` says **why the relation is asserted**.
The first candidate incorrectly collapsed those dimensions.

### `claim_relation_evidence_links`

A relation whose basis is source evidence can cite the exact source segment; it
must not rely only on a prose rationale.

```text
id PK
claim_relation_revision_id FK
representation_target_id FK
basis_role                -- source_basis | context
created_at
```

The exact endpoint ClaimRevisions are themselves basis references. Additional
source evidence is represented through this typed table, preserving real FKs
without a polymorphic universal basis table.

Only **direct** semantic edges are persisted. Co-occurrence and transitive closure
are query-time facts, never materialized canonical edges.

An `active` relation must have attributable origin and inspectable basis. The core
requires either exact source-basis evidence, a mechanical-identity rule with
reproducible process, or a concise rationale sufficient for an analyst inference.
`AI thinks these are related` is not enough to become active.

## 14. First concrete rich association: RoleAssignment

AKF-013 is already a 1.0 proving fixture: a person/entity holds a role in an
organization for a bounded period and the role/dates belong to the relationship
itself. Leaving only an abstract “promotion boundary” would postpone a known
schema need and risk turning ClaimRelation into a junk drawer.

The first schema therefore includes **one narrow rich-association family**. It is
not a generic Association table and does not pre-create contracts, ownership,
amount-bearing interests, events, or every Popolo/FtM relation.

### `role_assignments`

Stable identity.

```text
id PK
created_at
```

### `role_assignment_revisions`

```text
id PK
role_assignment_id FK
revision_no
supersedes_role_assignment_revision_id FK nullable
subject_entity_id FK
organization_entity_id FK
role_key nullable           -- local normalized role key
role_label                  -- human-readable/source-compatible role
valid_from nullable
valid_to nullable
origin_kind                 -- machine | rule | human
basis_kind                  -- relation_basis_kind
process_run_id FK         -- required for machine/rule; optional for human
rationale nullable
lifecycle                   -- candidate | active | rejected
created_at
UNIQUE(role_assignment_id, revision_no)
```

Core validation checks `valid_from <= valid_to` when both are present and applies
entity-kind expectations (normally person/organization -> organization) without
pretending SQLite FKs can express every subtype rule.

### `role_assignment_evidence_links`

```text
id PK
role_assignment_revision_id FK
representation_target_id FK
basis_role                  -- source_basis | context
created_at
```

This satisfies AKF-013 directly:

```text
Persona X
  -- RoleAssignment(role=Alcaldía, 2024-05-01..2028-04-30) -->
Municipalidad Ejemplo
  -- exact evidence --> official appointment record target
```

Future relationships with amount, ownership percentage, contract term, vote
participation, etc. get their own typed family only when a fixture/query proves
one. `RoleAssignment` is the demonstration that promotion is real, not a promise
that all rich relations share one schema.

## 15. Review without a truth column

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
decision                 -- review_decision
reviewer
reason nullable
created_at
```

### Identity/evidence/document-metadata reviews

The same typed review shape is available for the correctable semantic metadata
whose mistakes can change identity, evidence, or document interpretation:

- `document_identifier_reviews` -> `document_identifiers`;
- `document_classification_reviews` -> `document_classifications`;
- `document_representation_reviews` -> `document_representations`;
- `evidence_link_reviews` -> `evidence_links`;
- `entity_name_reviews` -> `entity_names`;
- `entity_identifier_reviews` -> `entity_identifiers`.

Review records judgment; it does not mutate the semantic row. Actual correction
uses the corresponding supersession chain.

### `claim_relation_reviews`

Same shape, FK to `claim_relation_revisions`.

### `mention_resolution_candidate_reviews`

Same shape, FK to `mention_resolution_candidates`. Accepting a candidate and
writing the corresponding `mention_resolution_revision` is one canonical
transaction.

### `claim_entity_link_reviews`

Same shape, FK to `claim_entity_links`.

### `claim_tag_link_reviews`

Same shape, FK to `claim_tag_links`. Review changes the attributable judgment of
the assignment; correction/removal of the anchor itself is represented by link
supersession rather than deletion.

### `entity_reconciliation_reviews`

Same shape, FK to `entity_reconciliations`. This keeps candidate/active
reconciliation provenance inspectable without mutating the append-only merge/split
record.

### `role_assignment_reviews`

Same shape, FK to `role_assignment_revisions`.

Separate review tables intentionally preserve FK integrity rather than using a
polymorphic universal review subject.

Review rows are immutable review judgments, not semantic-row revisions or civic Assessments. A reviewer who
changes their judgment appends another review row for the same exact subject. The
effective state for that reviewer is the latest row under the deterministic order
`(created_at DESC, id DESC)`; reviews by different reviewers remain independent and
are combined by the applicable policy rather than collapsed into one global truth
flag. The physical indexes support this per-subject/per-reviewer lookup.

No review row means **unreviewed**, which is valid and searchable in supervised
mode.

## 16. Custody restriction and purge

Normal correction never mutates archived bytes. Redaction creates a new
Representation and normally a new ArchiveObject.

A purge is an exceptional maintenance operation, not ordinary row deletion and
not a universal event ledger. It has two separate questions:

1. **what exact logical/physical records are in scope?**
2. **what can Canario truthfully claim was removed at each storage boundary?**

### `purges`

```text
id PK
reason_code
actor
retention_mode           -- minimal_tombstone | no_tombstone
created_at
executed_at nullable
outcome                  -- planned | completed | partial | failed
note nullable
```

### `purge_targets`

The first candidate's three typed purge-target tables covered Artifact,
Representation and ArchiveObject but missed a harder case: canonical derivative
rows such as EntityMention, RepresentationTarget or ClaimRevision can themselves
retain content that policy requires removing. A fixed list of only three target
tables would therefore make an exact purge claim impossible.

Purge planning is the bounded exception to the normal no-polymorphic-reference
rule because its target may intentionally cease to exist and therefore cannot
remain protected by a durable FK.

```text
purge_id FK
record_kind              -- closed purge_target_kind vocabulary
record_id                -- exact opaque ID existing when the plan is frozen
action                    -- purge_action
planned_at
executed_at nullable
outcome nullable
PRIMARY KEY(purge_id, record_kind, record_id, action)
```

`purge_target_kind` is a closed list of canonical content-bearing record families
that the implementation knows how to purge; it is **not** an open plugin
namespace or generic civic subject type. `acquisition_artifact` is included because
its observed filename/URL can itself retain prohibited source metadata even though
the row also acts as a join. The core validates target existence and allowed action
before freezing a plan. After execution the row intentionally remains an
operational manifest even when its target no longer exists.

Roots such as Artifact/Representation are expanded by dependency traversal into
every exact in-scope canonical/derived record that still retains the prohibited
material. The frozen target manifest is inspectable before execution. A vague
`derived_set`, search query or dynamically re-evaluated predicate is not an
acceptable purge target.

### Minimal retained rows and tombstones

When surviving canonical references must remain explainable, the affected type
may keep only its explicit minimal purge state instead of being deleted. For
example:

- `Artifact`/`Representation` may retain stable identity, `availability=purged`
  and `purged_at` while storage/digest metadata is cleared as policy requires;
- `RepresentationTarget` may retain its ID/parent but clear selector payload and
  become `availability=purged`;
- a type-specific record such as EntityMention may be scrubbed only if its DDL
  has an explicit tombstone contract that removes observed text/locator material.

Otherwise the content-bearing record and all content-bearing dependents that cannot
survive without it are included in the exact purge plan. Pure referential join-row
cleanup with no independent payload is deterministic execution closure rather than
inventing opaque IDs for every composite-key join; the purge executor reports its
per-table cleanup counts separately. There is no silent dangling reference or
unreported content-bearing deletion.

`minimal_tombstone` keeps only what policy permits: opaque record identity,
purge time/action, broad reason code, and enough non-sensitive lineage to explain
that material once existed. It must not retain the content, raw mention, locator,
digest, or metadata the purge is meant to remove.

`no_tombstone` permits removal of even that residue when required. The schema
supports both product semantics without pretending Canario can choose the legal
rule for every deployment.

### Shared-byte rule

If two retained logical Artifacts reference one `archive_object`, a purge cannot
claim the physical bytes were erased while another in-scope retained reference
still lawfully requires them. Because each acquisition gets its own Artifact,
record-scoped restriction/purge does not accidentally erase another capture.

The operation must either:

1. be logical-record scoped and detach/minimize only the targeted Artifact,
   explicitly **not** claiming byte erasure; or
2. expand the content purge to every affected retained reference under the
   governing policy before the shared ArchiveObject can be deleted.

### SQLite/FTS scrubbing rule

A purge that requires local database-level forensic scrubbing must not finish at
`DELETE`:

- core `PRAGMA secure_delete = ON` is already required;
- every FTS5 projection uses FTS5 `secure-delete=1`;
- affected FTS rows are removed/rebuilt from surviving canonical records;
- the WAL is checkpointed/truncated under the single-writer maintenance path;
- a maintenance `VACUUM` or clean `VACUUM INTO`/replacement path is performed
  when policy requires removal of recoverable free-page content;
- archive bytes and non-regenerable derived copies are deleted according to the
  exact frozen target manifest.

This is **database/file-level best effort**, not a promise to defeat SSD wear
levelling, filesystem snapshots, remote backups, or forensic recovery outside
Canario's controlled storage boundary.

### Backup rule

Every purge policy must state whether existing backups/snapshots are in scope and
when they expire or are rewritten. Canario may report current-authority purge
complete while separately reporting an out-of-scope retained backup, but it may
not claim corpus-wide erasure if an in-scope backup still contains the material.

`restricted` remains different from `purged`: restricted bytes still exist;
purged bytes do not exist inside the declared Canario authority boundary.

## 17. Search is a disposable projection

FTS5 is rebuildable and non-authoritative.

The first candidate left external-content vs contentless open. The critical
review closes this in favor of **ordinary self-content FTS5 virtual tables**.
At canton scale, small duplicate-text cost is preferable to external-content
rowid/trigger consistency coupling or contentless rebuild/deletion complexity.

Candidate projections:

```text
claim_fts
  claim_revision_id UNINDEXED
  text

representation_fts
  representation_id UNINDEXED
  text

document_fts
  document_revision_id UNINDEXED
  title
```

Eligibility is deterministic and rebuildable from canonical authority:

- `claim_fts` contains exactly current (non-superseded) ClaimRevisions whose
  `lifecycle='active'`. Human review is not required for internal supervised search;
  `rejected`, `retracted` and `restricted` revisions are excluded. The `sensitive`
  flag is an output/access-policy concern rather than a synthetic review gate.
- `document_fts` contains exactly current CivicDocumentRevisions with
  `visibility='normal'` and a non-null title.
- `representation_fts` contains only `availability='available'` textual
  Representations whose registered media type is supported by the rebuild reader.
  Restricted/purged representations are excluded.

`representation_fts` does not flatten an arbitrary “current extracted text” into
CivicDocument, which would hide representation identity and complicate
purge/reprocessing.

All three projections:

- are disposable and can be dropped/recreated from canonical rows;
- set FTS5 `secure-delete=1`;
- have an application `rebuild` command that repopulates from canonical records;
- run FTS5 integrity checks plus a projection-vs-canonical coverage check;
- are never FK targets and never evidence authority.

Normal relational indexes should cover at least:

```text
acquisitions(source_id, observed_at)
archive_objects(content_sha256) WHERE content_sha256 IS NOT NULL
artifacts(archive_object_id)
representations(artifact_id, kind)
representations(parent_representation_id)
representation_targets(representation_id, selector_kind)
document_identifiers(scheme, value)
civic_document_revisions(document_id, revision_no)
document_classifications(document_id, created_at)
document_representations(document_id, representation_id)
claim_revisions(claim_id, revision_no)
claim_revisions(lifecycle, created_at)
evidence_links(claim_revision_id)
evidence_links(representation_target_id)
entity_mentions(claim_revision_id)
mention_resolution_candidates(mention_id, created_at)
mention_resolution_revisions(mention_id, revision_no)
claim_entity_links(entity_id, claim_revision_id)
claim_tag_links(tag_id, claim_revision_id)
claim_relation_revisions(from_claim_revision_id, relation_type)
claim_relation_revisions(to_claim_revision_id, relation_type)
claim_reviews(claim_revision_id, reviewer, created_at, id)
role_assignment_revisions(subject_entity_id, organization_entity_id)
role_assignment_revisions(organization_entity_id, role_key, valid_from, valid_to)
```

### Rowid strategy

All 58 ordinary `0001` tables remain ordinary SQLite rowid tables. Application
contracts never expose or persist the hidden `rowid`; stable text IDs/composite
keys remain the only civic identity. `WITHOUT ROWID` is intentionally not frozen
without workload measurements: it can save a B-tree for non-integer/composite PKs,
but secondary indexes then carry the full PK and the benefit depends on real row
size/index mix. It may be evaluated later as a storage optimization without
changing semantic identity.

## 18. Query graph boundary

SQLite recursive CTEs may traverse **explicit ClaimRelations only**. Canonical
traversal uses only non-superseded operative ClaimRelationRevision leaves; historical
revisions remain queryable for audit but never appear as duplicate current edges.
Default query depth and result count are bounded. Storage keeps one attributable edge orientation,
but relation-type semantics matter: `contradicts` and `same_matter_as` are
symmetric for retrieval and are expanded from either endpoint; the other initial
types are directed and are not silently reversed. A symmetric relation is not
materialized twice merely to support reverse lookup. Shared tags/entities and
RoleAssignments are typed joins/anchors, not instructions to generate pairwise
Claim edges.

`ClaimRelation` is a **directed multigraph**, not a simple graph: the same two
ClaimRevisions may legitimately carry more than one direct relation type (for
example `updates` and `contradicts`) when each edge has independent basis. Query
APIs therefore separate two semantics:

- **reachability / neighborhood** returns deduplicated ClaimRevision nodes and
  uses cycle-safe bounded traversal (`UNION` or equivalent visited-node policy);
- **edge/path enumeration** preserves `claim_relation_revision_id` and relation
  type, so parallel edges remain inspectable instead of being silently collapsed.

A raw `UNION ALL` node walk is not the default reachability primitive: parallel
edges duplicate destinations and cycles can multiply work even when a depth cap
prevents infinite recursion. Result caps remain mandatory in both modes.

Examples:

```text
claims about Entity X
claims associated with an organization via a RoleAssignment
A -> updates -> B -> corrects -> C   (bounded recursive ClaimRelation traversal)
```

Co-occurrence and transitive closure remain derived query results. This keeps
Canario graph-shaped without creating a graph database or a home-grown triple
store.

## 19. Outputs and extensions

No canonical Output/Hilo/Episode tables are required in migration `0001`.
Outputs consume a bounded read/query model. Hilo may own Episode internally.
Another structurally different output must be able to consume the same Fichero
without Episode.

If future Outputs need durable local state, they receive namespaced persistence
outside core civic tables and no implicit filesystem/network/raw-SQL authority.

## 20. Backup and restore boundary

A complete backup is not `cp canario.db`.

It consists of:

```text
consistent SQLite snapshot
+
all retained archive-object bytes referenced by retained Artifacts/Representations
+
all retained non-regenerable representation bytes
+
integrity manifest relating IDs/storage keys/digests where policy permits
+
backup retention/purge policy metadata
```

FTS indexes and explicitly classified caches are rebuilt, not trusted from the
backup as authority.

Backup must use the SQLite backup API, `VACUUM INTO`, or another documented
consistent-snapshot mechanism, not copy a live WAL main file blindly. Restore
proof verifies:

- SQLite integrity + foreign keys;
- archive-object references and retained hashes;
- Artifact/Representation custody chains;
- EvidenceLink, ClaimRelation, reconciliation and RoleAssignment FKs;
- FTS rebuild from canonical rows;
- purge/tombstone policy state and whether any retained backup is intentionally
  outside a later purge scope.

## 21. Fixture pressure test after critical revision

| Fixture | Revised candidate representation |
|---|---|
| AKF-001 exact PDF evidence | Artifact -> Representation -> RepresentationTarget(`pdf_page_quote:v1`) -> EvidenceLink |
| AKF-002 repeated acquisition | two Acquisitions/Artifacts may share one ArchiveObject without collapsing provenance |
| AKF-003 unknown/broken profile | CivicDocument + classification `unknown`; bytes survive |
| AKF-004 compound artifact | one Representation -> many document occurrences with independent targets |
| AKF-005 spreadsheet locator | `table_range:v1` target with structural coordinates + observed values |
| AKF-006 supervised/batch | no review row is valid; ReviewAction groups exact per-record reviews |
| AKF-007 raw mention | EntityMention -> exact RepresentationTarget before resolution |
| AKF-008 same-name people | candidate resolution separated from append-only accepted resolution history |
| AKF-009 rename/merge/split | names/identifiers + reconciliation input/output lineage + exact basis refs |
| AKF-010 correction/relation | relation endpoints bind exact ClaimRevisions; supersession explicit |
| AKF-011 anchor/traversal | Entity/Tag joins; explicit bounded ClaimRelation recursion only |
| AKF-012 disagreement | EvidenceLink `challenges` remains distinct from ClaimRelation `contradicts` |
| AKF-013 rich association | concrete RoleAssignment revision + role/time + exact evidence |
| AKF-014 output independence | no Episode/Hilo core dependency |
| AKF-015 backup/restore | DB + ArchiveObjects + manifest + typed FK consistency |
| AKF-016 redaction/purge | derivative Representation + frozen exact purge manifest + type-specific tombstone/delete actions + SQLite/FTS/archive scrubbing policy |

All 16 fit structurally after the adversarial fixes. This is **still not
operational proof**.

## 22. Expensive-mistake check

The revised candidate avoids the existing research-ledger mistakes plus the two
new scars exposed by critical review:

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
15. no RDF/OWL/XML runtime stack;
16. no `DELETE`/FTS-row-removal = completed lawful purge claim;
17. no digest-unique Artifact identity that couples independent custody chains.

## 23. Decisions closed by critical review

The eight questions left open by `8b98010` are now closed at design level:

1. **Closed enums:** initial 1.0 vocabularies are enumerated in section 4.
2. **Selector schemas:** `whole:v1`, `text_quote:v1`, `pdf_page_quote:v1`, and
   `table_range:v1` have explicit bounded contracts in section 8.
3. **Process joins:** no generic process input/output graph in `0001`; typed output
   provenance + semantic FKs already identify required inputs.
4. **Document parts/collections:** absent from `0001`; current fixture is satisfied
   by independent documents + repeated representation occurrences/targets.
5. **Rich association:** AKF-013 already proves one; `RoleAssignment` is concrete in
   `0001`, while unrelated rich families remain typed future additions.
6. **SQLite floor:** 3.53.4+ baseline.
7. **FTS mode:** ordinary self-content FTS5 projection, application-rebuilt from
   canonical rows, with FTS secure-delete enabled.
8. **Purge retention:** a frozen exact `purge_targets` manifest plus
   `minimal_tombstone|no_tombstone` handles physical and semantic derivatives;
   operation explicitly scopes archive, SQLite, FTS, WAL and backups and does
   not claim device-level secure erasure.

These decisions do **not** authorize migration. They remove semantic ambiguity so
DDL can now be attacked mechanically.

## 23A. Migration 0001 freeze

The post-certification physical freeze work is documented in
`notebook/research/pre-sql/schema/MIGRATION_0001_FREEZE_REVIEW.md` and materialized
as `MIGRATION_0001_SPEC.sql`. That review closes bootstrap, SQL/core invariant
boundaries, FTS eligibility, rowid strategy, idempotent retry semantics, physical
index coverage and the remaining closed-vocabulary mismatches. The reconciled
specification has been re-run on the authoritative SQLite 3.53.4 runtime and
retains the prior target-runtime certification evidence.

## 24. Remaining proof gates before migration `0001`

What remains is proof, not unresolved domain semantics:

1. ~~executable **scratch DDL** proving critical nullability/FK/CHECK/STRICT constraints~~ — **PASS** in the disposable proof harness (58 STRICT tables; target runtime certification remains separate);
2. ~~selector validation against real PDF/text/table artifacts, including reopening
   the exact evidence location~~ — **PASS** against the preserved TSE `alcaldias_pu.pdf` artifact: physical PDF page quote, decoded-text offsets, and derived-table row/value coordinates all reopen exactly;
3. ~~RoleAssignment proof against a real appointment/office-holder source~~ — **PASS** against TSE resolution 2160-E11-2024, now including exact selector reopening under gate 2;
4. ~~repeated-byte/archive-object proof including shared-reference purge behavior~~ — **PASS** in the scratch operation proof: one logical capture can be purged without deleting shared bytes, while an attempted physical purge with a surviving retained reference is detected and forbidden;
5. ~~ClaimRelation basis/revision/review traversal proof~~ — **PASS** with exact revision-bound source basis, typed review, linear supersession, current-leaf filtering, directed/symmetric behavior and parallel-edge traversal;
6. ~~entity resolution merge/split/correction proof~~ — **PASS** with candidate→active supersession, mention re-resolution/anchor correction, merge/split history, review and active-operation cardinality validation;
7. ~~FTS rebuild/integrity/purge proof~~ — **PASS at candidate-operation level**: ordinary self-content FTS5 rebuilds from canonical rows, integrity checks pass, and FTS `secure-delete` participates in purge maintenance; packaged-runtime repeat remains gate 10;
8. ~~backup -> clean-machine restore -> FTS rebuild proof~~ — **PASS** with manifest/checksum validation, clean-location restore, `foreign_key_check`, database markers and FTS reconstruction;
9. ~~purge maintenance proof, including WAL/FTS and backup-scope reporting~~ — **PASS**: exact manifest, archive-byte removal, FTS secure deletion, WAL checkpoint plus VACUUM and explicit reporting that a pre-purge backup remains outside the current purge boundary;
10. ~~**packaged-runtime certification:** run `prove_runtime_contract.py` and
     the complete candidate proof suite with registered upstream SQLite 3.53.4;
     verify exact source ID, compile capabilities, STRICT/FTS5/WAL/FK probes and
     repeat gates 1/4/5/6/7/8/9 on that runtime~~ — **PASS** under the exact
     upstream SQLite 3.53.4 source ID; see
     `notebook/research/pre-sql/schema/TARGET_RUNTIME_CERTIFICATION.md`.

No production migration, canonical-data cutover, or current file-pipeline rewrite
is authorized by this design freeze. A separate explicit authorization checkpoint
is required.

## 25. Candidate verdict

**SCHEMA_CANDIDATE_GATE: MIGRATION_0001_FREEZE_COMPLETE__AUTHORIZATION_REVIEW_READY**

The first candidate was not safe to freeze. The critical revision restores
contract-required document/claim/relation revision provenance and lifecycle,
separates logical custody from physical byte deduplication, makes exact evidence reusable across
claims/relations/associations, concretely models the already-proven role/time
association, fixes the nullable-PK/STRICT contradiction, makes entity/tag anchors append-only
and correctable, requires attributable process identity for machine/rule writes,
and makes purge/FTS claims match SQLite's actual behavior.

The migration spec proof, migration-freeze bootstrap/inventory proof, real
selector/RoleAssignment artifacts, relation/entity correction traversal,
shared-byte purge safety, backup/clean restore/FTS rebuild,
archive+FTS+WAL purge maintenance, and the exact packaged SQLite 3.53.4
post-freeze certification all pass. At the freeze checkpoint the specification was
ready for a separate authorization review and migration `0001` remained
unauthorized. Section 26 records the subsequent bounded authorization.

## 26. Historical migration 0001 authorization

The original bounded migration implementation authorization is recorded in
`notebook/research/pre-sql/schema/MIGRATION_0001_AUTHORIZATION.md`. It authorized
the pre-WORKBENCH prerelease baseline with SHA256:

```text
31cac5ccc3440ce555242ba288317df527bb30949b2142026d8ceb2805d3adfc
```

That hash remains historical evidence only. WORKBENCH-001 proved that exact
ProcessRun scope, typed QualityEvidence, a quality decision separate from
execution outcome, and non-secret egress provenance are generic durable
requirements. Because Canario remains pre-release, those requirements rebaseline
`0001` rather than creating `0002`.

## 27. WORKBENCH-001 prerelease rebaseline

WORKBENCH-001 rebaselined `0001` to add terminal execution venue/error provenance,
ordered exact ProcessRun inputs, non-secret egress provenance, typed/namespaced
quality evidence, and durable quality decisions. That baseline was independently
certified on the exact registered upstream SQLite 3.53.4 runtime with SHA256:

```text
adf14a5006565197af3acf57c5cfc213510ba94217beb650403acbaf363b975a
```

Its certified inventory is 58 ordinary STRICT tables, 3 FTS5 tables, 118 explicit
indexes, 127 checked FK child paths with zero child-table scans, and no SQL JSON
runtime dependency. DIRECT-001 and OCR-001 were independently certified against
that same baseline.

## 28. PROCESSOR-CODEX-001 prerelease egress correction

The first production egress backend exposed one generic assumption that the local
backends could not exercise: an egress-capable processor may terminate during local
page preparation before the external executor receives source bytes. The previous
`bytes_egressed > 0` CHECK could only represent that failure by dropping terminal
provenance or lying about egress.

Because Canario remains pre-release, the certified integration is byte-identical
between:

```text
notebook/research/pre-sql/schema/MIGRATION_0001_SPEC.sql
canario/persistence/migrations/0001.sql
```

with SHA256:

```text
5226c873487d9bd05fc62b7a1f323d6e804b003cc4e08bd2fe2b531adb6057bb
```

The only SQL semantic delta from the independently certified pre-Codex baseline is:

```text
process_run_egress.bytes_egressed: > 0  ->  >= 0
```

Here the byte count means measured source/evidence payload bytes handed to the
external executor, not guessed total wire/protocol traffic. `0` therefore means the
selected egress processor terminated before external handoff while preserving its
policy/data-control/template/endpoint provenance. Negative values remain forbidden.

Physical inventory is unchanged:

```text
ordinary STRICT tables: 58
FTS5 virtual tables:     3
application triggers:    0
explicit indexes:        118
FK child paths checked:  127
FK child table scans:    0
SQLite JSON dependency:  absent
```

Portable migration-spec, freeze, storage, Workbench, DIRECT and OCR regressions pass
in the implementation checkout. Independent PROCESSOR-CODEX-001 certification must
repeat these proofs on the exact registered SQLite 3.53.4 runtime before this hash
becomes current certified authority. No `0002` exists.

```text
PROCESSOR_CODEX_001_SCHEMA_REBASELINE: IMPLEMENTED__CERTIFICATION_PENDING
canonical_cutover_authorized: false
forward_migration_0002_created: false
```

## 29. Derivation/Verification prerelease rebaseline design

The structured-reasoning G3 proof, bounded Phase-D measurement, local closure certification and
post-merge reconciliation now require one additional prerelease `0001` rebaseline. The accepted
authority is `notebook/implementation/DERIVATION_VERIFICATION_RECONCILIATION.md` with decision:

```text
SINGLE_EXECUTION_GRAPH__SOURCE_EVIDENCE_NOT_EXECUTION_LINEAGE
```

This section advances the **candidate**; it does not claim that current production `0001` already
contains these records.

### Typed families to add

```text
derivation_runs
  immutable analytical attempt
  exact program + planner/orchestration provenance + executor identity + sandbox + outcome

derivation_run_egress
  non-secret egress facts for the analytical attempt

derivation_run_inputs
  ordered exact RepresentationTarget scopes

derivation_results
  one exact typed result for each successful DerivationRun
  bounded registered inline payload OR ArchiveObject-backed material payload

derivation_result_targets
  exact reusable slice of one result + per-target lineage_state

derivation_result_lineage
  exact DerivationResultTarget -> source-contribution RepresentationTarget

verification_runs
  exact proposition + optional ClaimRevision binding + scope profile + execution outcome
  + verdict/sufficiency/abstention when completed
verification_run_egress
  non-secret verifier egress facts
verification_scope_targets
  ordered explicit RepresentationTarget terrain available to the verifier
verification_authority_scopes
  ordered exact SourceAuthorityScope rows
verification_derivation_steps
  ordered attempted/consumed DerivationRuns; consumed successful steps name exact result targets
verification_evidence_items
  exact source RepresentationTargets returned as supports/challenges/context for the run

assessments
  optional attributable durable ClaimRevision judgment
  supported | contested | refuted | unresolved
  human basis may be direct/attributable; machine/rule requires same-Claim VerificationRun + registered policy
  supersession stays within the same ClaimRevision + assessor/policy lineage; no automatic promotion
```

### Existing families to change

`claim_revisions` gains nullable `derivation_result_target_id`, required exactly for
`claim_kind=derived_inference`. Existing ProcessRun origin remains the source-extraction/semantic
process path and may coexist only as distinct wording/promotion provenance on a derived Claim.

`EvidenceLink` remains ClaimRevision -> source RepresentationTarget. It is **not** replaced by
Derivation lineage or Verification evidence. Active `supports` evidence for a derived Claim must be
traceable to source-contribution lineage for the exact origin result target; independent
`challenges` evidence remains ordinary civic evidence.

Archive availability/shared-byte validation expands so an available ArchiveObject referenced by an
available DerivationResult is a real retained dependency. Purge root expansion adds the seven new
content-bearing record families in the closed vocabulary; payload-free FK/ordinal joins are exact
execution closure, not generic purge targets.

### Identity and correction rules

DerivationRun and VerificationRun are immutable attempts. Re-execution creates new IDs even if
inputs/program/model/result match; only persistence retry of one preallocated immutable attempt may
reuse its ID. No mutable current-run pointer or hash-as-identity exists.

Source correction/reprocessing creates new Representation targets and therefore new analytical
runs; historical runs remain bound to old exact inputs. Claim correction continues through
ClaimRevision supersession. Assessment correction is append-only same-Claim supersession per
assessor/policy; multiple independent assessors may disagree.

### Rebaseline gate

The implementation must update `MIGRATION_0001_SPEC.sql` and production `0001.sql` together, extend
closed vocabularies/purge logic/storage operations, and mechanically prove the 15 invariants listed
in the reconciliation document. It must then repeat the full applicable freeze, FK/index,
selector-containment, shared-byte purge, backup/restore/FTS/WAL and exact registered SQLite 3.53.4
runtime certification.

Until that gate passes:

```text
current production 0001: prior certified authority
this section:               accepted next-schema design
production Derivation writer:    NOT AUTHORIZED
production Verification writer:  NOT AUTHORIZED
automatic Assessment promotion:  NOT AUTHORIZED
forward migration 0002:          NOT AUTHORIZED / NOT NEEDED IN PRERELEASE
```
