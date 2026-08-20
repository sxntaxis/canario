---
id: ACTAKIT-CONTRACTS-001
kind: canonical-contracts
state: proposed-for-acceptance
created: 2026-08-19
authority: architecture-proposal
summary: Minimal durable contracts for evidence custody, civic documents, traceable claims, review policy, queries, and extensible outputs.
related:
  - ACTAKIT-ARCH-001
  - ACTAKIT-DATA-001
  - ACTAKIT-IMPLEMENTATION-001
  - ACTAKIT-RELEASE-001
---

# Canonical Contracts

## Contract Rules

Canonical meaning belongs to ActaKit records and their relationships, not to one
serialization format. SQLite rows, JSON, YAML, Markdown, and output files are
representations of contracts.

Every mutable canonical record has at least:

```yaml
id: opaque stable identifier
schema_version: contract version
revision: monotonic record-local revision
created_at: ISO-8601 UTC timestamp
created_by: actor/process identity
record_hash: hash of canonical serialization
```

Every consequential mutation has an `operation_id`. Replaying the same operation
with the same request is safe; reusing the ID for a different request is an
error. Updates to existing records use an expected revision or equivalent stale-
write guard.

Opaque IDs are preferred for canonical identity. Source filenames, URLs,
document numbers, titles, tag names, and output positions are labels, not keys.

## Sources and Captures

A `Source` identifies a bounded public information source or source family.
A versioned `SourcePolicy` controls:

- acquisition hosts/paths/media where relevant;
- retention and privacy expectations;
- source authority/scope: what kinds of claims this source can reasonably
  support;
- completeness/checkpoint rules when they are knowable.

A `SourceRun` is one bounded inspection attempt. A `SourceCapture` records one
observed resource, retrieval attempt, final URI/locator, supplied metadata,
time, and resulting artifact or failure.

Failure or absence in one run never deletes prior knowledge.

## Artifacts and Representations

An `Artifact` is immutable acquired bytes with digest, byte length, media type,
acquisition provenance, archive location, and custody state:

```text
pending -> verified | quarantined | rejected | disposed
```

The same bytes acquired from two captures may share physical storage while
retaining both provenance chains.

A `Representation` is an inspectable form of an artifact or another
representation:

```text
original
extracted_text
ocr_text
page_image
table
transcript
normalized_text
redacted_derivative
other
```

It records its parent, digest, media type, generator/process, configuration,
language/charset where relevant, and quality/diagnostic metadata.

A derivative never replaces its parent.

## Process Runs and the Lector

Every parser, OCR, rule engine, AI model, normalization pass, classifier, or
human-assisted extraction can be recorded as a `ProcessRun` with exact inputs,
implementation/model/configuration identifiers, time, outputs, and diagnostics.

A ProcessRun may create claims, entity/tag suggestions, document classification,
relations, or new representations. AI output is attributable processing output,
never factual source evidence by itself.

## Civic Documents, Parts, and Collections

A `CivicDocument` expresses civic/institutional identity independently of file
format. It records common metadata such as display identity, issuer/body, date,
language, normalized type, subtype/profile, classification basis, visibility,
and revision.

Source-supplied labels are attributable observations, not values ActaKit silently
overwrites:

```text
source_supplied_type   what that source called it
normalized_type        broad ActaKit classification
profile_schema         optional specialized structure
```

Initial broad document types remain intentionally small:

```text
acta, agenda, convocatoria, acuerdo, resolucion, oficio, informe,
dictamen, presupuesto, plan, reglamento_ordenanza, aviso_publico,
correspondencia, comunicado_prensa, contrato, dataset, grabacion, otro
```

Before classification the value may be `unknown`. `otro` is a legitimate safe
classification, not a failure.

Profiles such as `acta:v1`, `informe:v1`, or `presupuesto:v1` add validated
specialized fields only when real semantics justify them. New bureaucratic
labels do not automatically create new SQL tables or profiles.

A `DocumentPart` optionally models meaningful structure inside one document.
A `CivicCollection` groups multiple documents when the civic object is a package,
case, expediente, procurement process, or similar multi-document object.

One artifact may contain multiple documents and one document may have multiple
representations. Anchors connect those semantic boundaries without rewriting the
source bytes.

## Claims

A Claim is an identifiable proposition found in or derived from source material.
It may exist before human review.

A claim revision records at least:

```yaml
text: exact normalized proposition or explicit question
kind: source_assertion | derived_inference | community_report | verification_question
origin_kind: machine | human
origin_process_id: optional ProcessRun
attribution: optional speaker/body/source actor
temporal_scope: optional
flags:
  sensitive: false
  quantitative: false
status: active | rejected | superseded | retracted | restricted
epistemic_status: unverified | supported | corroborated | contested | refuted | indeterminate
```

Human review level is derived from review decisions and must remain separate from
epistemic status. At minimum consumers can distinguish:

```text
machine-only
human-reviewed
```

A claim is not split further unless the parts need independent evidence,
correction, retrieval, or relationships.

### Extraction policy

A versioned extraction policy defines what counts as civically relevant for a
source/document profile. The default aims for broad capture of relevant:

- decisions, votes, agreements, requests, commitments and responsibilities;
- money, quantities, deadlines, dates and periods;
- projects, services, works, contracts and public resources;
- reported problems, responses, findings, recommendations and outcomes;
- named institutions, places, public actors and other retrieval-relevant
  entities;
- contradictions, uncertainty, or verification questions when material.

The policy should favor later recoverability over guessing today's importance,
while excluding purely ceremonial/noise content when it has no plausible civic
retrieval value.

## Evidence Links and Typed Locators

An `EvidenceLink` binds a specific claim revision to a specific representation
using one relation:

```text
supports
contradicts
contextualizes
quotes
mentions
```

It includes:

```yaml
claim_revision: clm_...@N
representation_id: rep_...
relation: supports
locator_kind: pdf | text | spreadsheet | image | media | json | xml
locator_version: 1
locator_payload: validated payload
document_id: optional civic context
document_part_id: optional civic context
```

Locator payloads are versioned and validated, not arbitrary JSON.

| Locator | Required anchor |
|---|---|
| `pdf:v1` | page/folio; quote or region as available |
| `text:v1` | start/end offsets in a hashed representation + exact quote/context |
| `spreadsheet:v1` | sheet/table + cell/range or row/header + observed values |
| `image:v1` | image/page + region |
| `media:v1` | start/end time; transcript anchor when available |
| `json:v1` | stable path/JSON Pointer + observed value/hash |
| `xml:v1` | stable path/XPath equivalent + observed value/hash |

Semantic labels such as article/item/agreement may strengthen context but are not
universal locator requirements.

A malformed artifact can remain in custody without a usable locator. A direct
source assertion cannot be treated as evidence-backed until an active supporting
link resolves to a verifiable representation location.

## Source Authority Scope

Evidence quality is not a single `official=true` flag. SourcePolicy or bounded
source observations describe what the source can directly demonstrate.

Examples:

```text
formal_record       formal record states/agrees X
recorded_speech     recording contains statement X
publisher_statement issuing body announced/claimed X
reported_observation source reports X
structured_value    source table/dataset contains value X
```

Claim wording and evidence relations must preserve this scope. “The institution
announced X” must not silently become “X happened.”

## Entities, Tags, and Relations

Entities exist to improve retrieval and linkage, not to build a universal civic
ontology. Initial useful classes may include person, organization/institution,
place, project, legal instrument, and other locally justified entities.

Tags/topics are local, versioned vocabulary. A canton may create, import, or
share a taxonomy without making it globally canonical.

Relations are simple typed edges only when they improve retrieval or integrity,
for example:

```text
claim -> mentions -> entity
claim -> concerns -> place
project -> managed_by -> institution
claim -> contradicts -> claim
```

Do not normalize every noun, date, or number into its own table before use cases
require it.

## Review Policies and Decisions

Review is a policy layer over records, not the condition for a Claim to exist.
A `ReviewPolicy` may select mode by installation, source, document profile,
output, sensitivity, or other bounded criteria.

Initial modes:

```text
strict
batch
supervised
```

### Strict

Protected use requires an explicit human review decision on the relevant claim
or deterministic review set.

### Batch

A `ReviewBatch` identifies an immutable deterministic set of subject revisions
and its set hash. One human action can approve/reject that set while exceptions
receive individual decisions.

### Supervised

Machine-only claims are immediately available for permitted internal search.
Human review occurs on demand or when another policy requires it.

A `ReviewDecision` records subject revision/batch hash, actor, action, rationale
when needed, time, and policy revision. The ordinary installation may have one
operator performing all actions; authority is recorded as an action/capability,
not a required staffing role.

Sensitive data, public publication, or other high-consequence contexts may force
human review independently of the default ingestion mode.

## Corrections

Claim/document revisions preserve history. Ordinary edits use revision lineage.
A separate explicit correction event is reserved for actions whose meaning must
itself be retained, such as:

```text
retract
public_correct
redact
unlink_evidence
merge_identity
```

A redacted public representation never overwrites the restricted original.

## Queries

A query is read-only. It selects records by documented fields such as text,
entity, tag, source/document type, date, review level, epistemic status, or other
supported indexes.

A query may be ephemeral or saved as a versioned `SavedQuery` with parameters.
Results do not become canonical civic claims merely because they were returned
or ranked.

## Output Types

An `OutputType` is a versioned extension that consumes a bounded query/read model
and organizes it for a purpose. The core contract separates:

```text
OutputType      logic/schema/capabilities
OutputInstance  configured local use of that type
OutputState     optional derived/curated state owned by that output namespace
Exporter        serialization/transport such as Markdown, JSON, CSV, HTML
```

An OutputType declares at least:

```yaml
output_type_id: stable package/type identity
version: semantic/schema version
input_capabilities: required read/query capabilities
config_schema: validated configuration schema
state_schema: optional validated derived/curation state schema
exporters: supported serializers
permissions: read-only core access by default
```

Output state may contain human curation specific to that presentation, but it
cannot silently rewrite claims, evidence, review decisions, or artifacts. Any
canonical mutation must use an explicit core operation.

Output Types may be shared between installations independently of civic data.

### Hilo

`Hilo` is one Output Type. Its own schema may define:

```text
Hilo
episode
membership
reader summary
chronological rendering
```

`Episode` is therefore not a universal canonical record. It is Hilo-specific
reader organization over claims.

## Publication Snapshots

When an output is deliberately released, ActaKit may create an immutable
snapshot containing exact input claim/document revisions, output type/version,
configuration, policy state, output hashes, and publication decision.

Later correction creates a new snapshot. Omission from a later snapshot is not
implicit deletion.

## Privacy

Public output is default-deny for sensitive classes such as precise home
addresses, medical data, identifying information about minors, personal contact
details, and inferred individual political preference unless an accepted policy
explicitly permits the case.

Preservation of original public evidence does not imply unrestricted
republication.

## Storage Boundary

The first implementation uses a local ActaKit core as the sole canonical writer
to SQLite and the evidence archive. A daemon/RPC service is optional future
infrastructure, not a canonical semantic requirement.

Clients, Output Types, exporters, and external adapters never write SQLite
schema/tables directly.

## Compatibility Principle

Semantic contracts are versioned so implementation details can evolve without
rewriting history. The project designs stable IDs, provenance, evidence links,
revision lineage, Output Type boundaries, and export schemas before they become
expensive to change; it does not implement unused distributed machinery merely
because those boundaries could support it later.
