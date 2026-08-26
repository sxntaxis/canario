---
id: ACTAKIT-CONTRACTS-001
kind: canonical-contracts
state: accepted
accepted: 2026-08-21
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

Canonical meaning belongs to Canario records and their relationships, not to one
serialization format. SQLite rows, JSON, YAML, Markdown, and output files are
representations of contracts.

Use stable opaque IDs for records whose identity must survive renaming,
correction, or reprocessing. Use append-only revisions where civic meaning can
change materially: claims, claim relations, document classification/identity
when necessary, and other subjects proven by fixtures to need revision history.

Do **not** require `record_hash`, `operation_id`, expected-revision guards, or a
second revision protocol for every canonical row. Add hashes/idempotency/stale-
write controls at concrete boundaries that need replay safety or concurrency.

Every attributable action records enough provenance to answer who/what created
or changed it and when. Source filenames, URLs, document numbers, titles, tag
names, and output positions are labels, not canonical keys.

## Sources, Source Connectors, Inbox, and Acquisition

A `Source` identifies a bounded public information source or source family.
The baseline stores bounded acquisition configuration and authority scope only as
needed by real adapters; it does not require a general-purpose policy engine.

Source-specific terrain belongs to a **Source Connector**. Connectors implement
the accepted `ACTAKIT-INGRESS-001` SPI and terminate at the `InboxPort`; they do
not call canonical writers directly. The Inbox is host-bound to canonical Source
identity plus `ConnectorDescriptor(key, version)`, so connector code cannot choose
its own canonical source, adapter attribution, validation state, or persistence
identity.

The terrain-neutral boundary DTO is `CaptureEnvelope`: observation time/outcome,
an optional open-kind locator, optional transport status/error, and zero or more
`CapturePayload` byte bodies with bounded observed metadata. It contains no acta,
municipality, HTML/API/browser, document-ontology, or Fichero concepts.

An `AcquisitionObservation` records one concrete observation/retrieval attempt:
source, resource locator/URI, time, outcome, connector key/version, and resulting
artifact or failure. The bounded Inbox maps accepted envelopes to the certified
Depósito writer; incoming Artifact validation begins as `pending` rather than
letting a connector self-certify captured bytes.

Discovery is not universal: pull crawlers, APIs, browser automation, feeds,
filesystem/manual push and future transports may all use different private
mechanics. A connector reports run coverage only as `unknown`, `incremental`, or
`complete_inventory`; the latter two require matching generic capabilities.
Opaque checkpoints may be passed only to connectors advertising checkpointing.
The core does not interpret checkpoint contents. Durable run/checkpoint storage is
not part of INGRESS-001 and must be justified by a real connector.

Specialized connector assumptions fail loudly. Already accepted custody remains
preserved when a later part of the connector run fails. In all cases:

> failure or absence in one observation/run never deletes prior knowledge.

Source Connectors stop at original custody. PDF/DOCX/OCR/table/transcript work is
a separate Representation-processing boundary in the Mesa de trabajo.

## Artifacts and Representations

An `Artifact` is a stable logical custody record created by one acquisition
observation. It points to an `ArchiveObject` holding the physical content-addressed
bytes. Digest, byte length and storage key therefore belong to ArchiveObject;
Artifact retains acquisition provenance, media/custody context, and **separate**
validation and availability state. Do not compress these axes into one lifecycle:

```text
validation:   pending | verified | quarantined | rejected
availability: available | restricted | purged
```

`restricted` retains bytes under access limits. `purged` is reachable only by the
explicit purge contract defined below; it is not an ordinary edit/delete state.
The same bytes acquired from two captures create two Artifact identities that may
share one ArchiveObject. Physical deduplication must never collapse acquisition,
restriction, review or purge provenance.

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

The `original` Representation reuses the Artifact's captured ArchiveObject rather
than duplicating a physical-byte pointer. A material derivative records its own
physical bytes, exact parent Representation, media type, generator/process,
configuration, language/charset where relevant, and quality/diagnostic metadata.

A derivative never replaces its parent, and a retained derivative never exists
without both an attributable parent and generator/process.

## Processing Provenance and the Lector

Parser, OCR, model, normalization, classifier, or other machine/rule work that
materially creates a derived Representation or semantic row records an exact
terminal `ProcessRun`. A ProcessRun is provenance, not scheduler state. It records
registered capability/process kind, implementation/version, execution venue,
configuration identity, optional provider/model identity, terminal outcome,
bounded error code, and timestamps.

For Representation processing, exact input scope is durable even when execution
fails: ordered `process_run_inputs` point to validated `RepresentationTarget` rows
owned by the input Representation. Whole-document work uses an explicit
`whole:v1` target; physical PDF page processing uses `pdf_page:v1`; quote-bearing
PDF evidence remains `pdf_page_quote:v1`; other block/table work uses its own
registered selector contract.

Every derivative generated by a ProcessRun is attributed to that run's full
ordered input scope. A processor that needs separately citable outputs for narrower
subsets must use separate bounded ProcessRuns (or one combined derivative for the
batched scope); WORKBENCH-001 does not introduce an arbitrary per-output process
graph.

`ProcessRun.outcome` (`success | partial | failed`) answers whether execution
technically completed. It is deliberately separate from the Workbench quality
decision (`accept | escalate | quarantine_review`). The latter records policy
key/version, bounded reason code and optional next capability for each exact input
target. A technically successful OCR run may therefore escalate without rewriting
its execution history.

Processors emit registered, typed/namespaced `QualityEvidence`. Each durable
signal is attributed to a ProcessRun and exact RepresentationTarget and is
validated by `signal_key + signal_version`; arbitrary metadata dictionaries and a
universal confidence value are forbidden. Provider-specific confidence may exist
only under its own registered namespace.

Cloud/agent execution records only non-secret egress provenance such as source/evidence
payload bytes handed to the external executor and policy/data-control/template/endpoint
profile identity. Zero bytes is valid only when an egress-capable terminal attempt fails
before external handoff. This is not a fabricated total network-traffic counter. Credentials,
OAuth tokens, account identity and secret paths never enter Processor requests,
SQLite, QualityEvidence or derivative Representations.

Material processor outputs are new same-Artifact Representations with their own
ArchiveObject, exact parent Representation, and generating ProcessRun. Originals
are never overwritten. Workbench processing inherits restricted custody onto derivatives. Making a redacted derivative public is a separate explicit reviewed correction/release action; a Processor cannot declassify its own output. Physical
content deduplication may reuse an ArchiveObject but never collapses logical
Representation or ProcessRun provenance.

AI output is processing output, never factual source evidence by itself.

## Civic Documents, Parts, and Collections

A `CivicDocument` expresses stable civic/institutional identity independently of
file format. Common mutable metadata such as title/display identity, issuer/body,
date, language and visibility belongs to append-only `CivicDocumentRevision`;
normalized type/subtype/profile remains separate attributable classification
history. A metadata correction never mutates the stable document row.

Source-supplied labels are attributable observations, not values Canario silently
overwrites:

```text
source_supplied_type   what that source called it
normalized_type        broad Canario classification
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
origin_kind: machine | rule | human
origin_process_ref: optional attributable processing provenance
attribution: optional speaker/body/source actor
temporal_scope: optional
flags:
  sensitive: false
  quantitative: false
lifecycle: active | rejected | superseded | retracted | restricted
```

Human review is derived from review decisions and remains separate from
lifecycle. Consumers must at minimum distinguish unreviewed machine/rule output
from human-reviewed material.

An optional attributable assessment (`supported`, `contested`, `refuted`, etc.)
may exist when a workflow needs it, but it is **not a mandatory claim field** and
must not be presented as an objective truth score. Evidence links and explicit
claim relations remain the inspectable record.

A claim is not split further unless the parts need independent evidence,
correction, retrieval, or relationships.

## Extraction, Derivation, Verification, and Assessment

These are semantic operation boundaries, not new mandatory product stages or immediate
tables.

**Lector/source extraction** answers what the source asserts or explicitly contains. It
may use bounded context and multiple exact evidence links, but a newly computed sum,
comparison or join is not a `source_assertion`. A source may explicitly state a computed
conclusion; Lector can extract that statement without recomputing it.

**Derived analysis** answers what can be reproducibly computed from bounded Canario
Representations. The conceptual execution record includes ordered input
Representation/target identities, exact query/program, executor/runtime and configuration
identity, sandbox/resource profile, terminal outcome, exact result and available source
row/cell/evidence lineage. The query/program is provenance and never original source
evidence. A successful result may support a Claim with `kind=derived_inference`, but does
not automatically become a Claim.

The certified G3 fit bench at `0f9a71e5acb0f093469571d59c896eab0c03c4c2` concluded `FIRST_CLASS_DERIVATION_REQUIRED`: existing `ProcessRun` semantics are Representation-processor-shaped and may not be overloaded as the canonical analytical execution record. A distinct first-class derivation execution contract is required. No schema change is authorized until that contract is reconciled with Verification and Claim provenance.

**Verification** evaluates a proposition against an explicitly bounded evidence scope.
A verifier-result-like artifact keeps these axes separate:

```text
execution outcome
verdict: supported | contradicted | insufficient_evidence
evidence set and reopenability
evidence sufficiency
abstention reason
process/model/configuration provenance
```

Timeout, crash, invalid query and tool failure are execution failures, not
`insufficient_evidence`. A verifier result must not mutate Claim lifecycle (`reject`,
`retract`, `supersede` or equivalent). The existing optional attributable `Assessment`
remains the durable judgment that may later be recorded or promoted by policy from a
specific verifier result.

Phase D measured material value from stronger decomposition in evidence retrieval/backing without a
verdict-accuracy gain. The accepted minimum contract is therefore Canario-native: a Verification
execution references the exact ordered `DerivationRun` executions whose results it used, while
keeping verdict, evidence set, explicit sufficiency and execution outcome separate. No Thucy role
class or multi-agent runtime is part of this contract.

Evidence sufficiency is initially typed result information, not a new entity or table. It
records whether the bounded scope was adequate, whether required coverage was missing and
whether a negative/absence proposition had sufficient inventory/completeness authority.
“Not found” is not “does not exist” without that authority.

### Extraction policy

Extraction aims for broad civic relevance: decisions, votes, agreements,
requests, commitments, responsibilities, money, quantities, deadlines, dates,
projects, services, works, contracts, public resources, reported problems,
responses, findings, recommendations, outcomes, and retrieval-relevant entities.

The policy favors later recoverability over guessing today's importance while
excluding purely ceremonial/noise content with no plausible civic retrieval
value. A versioned policy object is only required when changing policy itself
must be audited/replayed; simple configuration is sufficient initially.

## Evidence Links and Typed Locators

An `EvidenceLink` binds a specific claim revision to a specific representation
using one relation:

```text
supports
challenges
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

Interpretation context is not the same thing as the smallest exact locator. A future
`ContextEnvelope` is a bounded benchmark/retrieval artifact that may include neighboring
text, structural table rows, headers or multiple permitted Representations. Its membership
does not imply review, truth, evidence support or recall coverage. It requires deterministic
identity/digest when used by a benchmark.

One Claim revision may have multiple independently reopenable typed EvidenceLinks. This is
valid when attribution, conditions, exceptions, hierarchy, cross-reference or mixed
modality requires several evidence units. For derived analysis, row/cell/query-result
lineage may support the result, while the executable query remains provenance rather than
source evidence.

| Locator | Required anchor |
|---|---|
| `pdf:v1` | page/folio; quote or region as available |
| `text:v1` | start/end offsets in a hashed representation + exact quote/context |
| `spreadsheet:v1` | sheet/table + cell/range or row/header + observed values |
| `image:v1` | image/page + region |
| `media:v1` | start/end time; transcript anchor when available |
| `json:v1` | stable path/JSON Pointer + observed value/hash |
| `xml:v1` | stable path/XPath equivalent + observed value/hash |

The current runtime realizes `spreadsheet:v1` through the bounded `table_range:v1`
selector against the typed `canario.structured_table.v1` Representation. Timed media
uses integer microseconds and a SHA-256-bound `media:v1` selector; media duration must
come from a retained deterministic inspection index. A transcript remains a derivative
and may be cited separately or as a validated anchor, but never replaces the recording.

Semantic labels such as article/item/agreement may strengthen context but are not
universal locator requirements.

A malformed artifact can remain in custody without a usable locator. A direct
source assertion cannot be treated as evidence-backed until an active supporting
link resolves to a verifiable representation location.

## Source Authority Scope

Evidence quality is not a single `official=true` flag. Bounded source configuration or acquisition observations describe what the
source can directly demonstrate.

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

## Entities, Tags, and Claim Connections

### EntityMention preserves the source occurrence

An `EntityMention` is the provenance-preserving occurrence of a possible entity
in source-derived material **before canonical identity resolution**. Minimum
semantics:

```yaml
mention_id: emn_...
representation_ref: rep_...
locator: typed locator or equivalent exact occurrence context
observed_text: "AyA"
claim_revision_ref: optional clm_...@N
origin_kind: machine | rule | human
origin_process_ref: optional attributable process
```

A mention may remain unresolved. Candidate matching and confirmed resolution are
separate from the observed text; resolution never overwrites `observed_text`.
When a resolution decision changes, history remains attributable rather than
mutating the source occurrence.

### Entities are shared resolved anchors

An `Entity` gives a retrieval-relevant thing a stable **local** identity.
Initial classes may include person, organization/institution, place, project,
legal instrument, contract/procurement object, and other locally justified
classes.

Identity resolution is explicit rather than name-equality magic:

- preserve source occurrences through `EntityMention`;
- attach strong external identifiers when available (legal ID, contract number,
  official expediente/agreement identifier, etc.);
- do not merge people merely because names match;
- projects/places/organizations may have aliases and changing display names;
- unresolved or machine-suggested mention resolution is valid;
- merge/split decisions preserve history and provenance instead of silently
  rewriting every old link.

A `ClaimEntityLink` binds an exact claim revision to an entity using a small,
extensible relation/role vocabulary such as `mentions`, `about`, `actor`,
`responsible`, or `place` when useful. It records origin and processing/review
provenance. If derived from a mention resolution it cites the exact accepted
resolution revision; later resolution correction must not leave the old anchor
appearing current. Link correction is append-only/superseding rather than silent
retargeting. A direct claim-level anchor may exist without a literal mention; no
matching raw string alone proves entity identity.

### Entity reconciliation is append-only

A minimal `EntityReconciliation` lineage records identity changes without
becoming a general graph:

```yaml
reconciliation_id: erc_...
supersedes_reconciliation: optional erc_...
kind: merge | split
input_entities: [ent_...]
output_entities: [ent_...]
origin_kind: human | rule | machine
origin_process_ref: required for rule/machine; optional for human
basis_refs: exact mention/document/identifier references when available
rationale: concise explanation when needed
created_at: ...
```

For `merge`, accepted current retrieval may follow the lineage to the survivor or
replacement entity while old links remain historically intact. Candidate promotion
or correction creates a superseding reconciliation row rather than mutating the
old event. For `split`, old links are not bulk-rewritten: affected mentions/links
are re-resolved when enough evidence exists, and unresolved historical ambiguity
remains visible.

A tag assignment follows the same correction principle as an entity anchor: it
has attributable origin, an operative/candidate/rejected state, and append-only
supersession when corrected. Flat local tags remain intentionally simpler than
entities; no taxonomy graph is required in `0001`.

Shared entity membership is a retrieval fact, not a semantic shortcut:

```text
Claim A -> entity: Puerto Caldera
Claim B -> entity: Puerto Caldera
```

means the claims can be found together. It does **not** mean A updates, supports,
or contradicts B.

### ClaimRelation is first-class civic memory

A `ClaimRelation` records a meaningful proposition-to-proposition connection.
It is canonical data with its own stable identity/revision, not a search result
or something an AI must rediscover each time.

It binds **specific claim revisions**:

```yaml
from_claim_revision: clm_...@N
relation_type: updates | contradicts | corrects | responds_to | implements | supersedes | same_matter_as | other
to_claim_revision: clm_...@N
origin_kind: machine | rule | human
origin_process_ref: optional attributable processing provenance
basis_kind: source_evidence | analyst_inference | mechanical_identity | other
basis_refs: exact claim/evidence/document references when available
rationale: concise explanation when basis refs alone do not explain the link
lifecycle: candidate | active | rejected | superseded
```

A canonical **active** relation must have attributable origin plus an inspectable
basis: exact references, a concise rationale, or both. `AI thinks these are
related` is provenance for a candidate, not sufficient canonical meaning.

Review is derived from review decisions just as for claims. In supervised mode a
machine/rule candidate may remain searchable without masquerading as human-
confirmed. Promotion to active follows the relation policy and basis minimum.

Relation types remain a small versioned vocabulary with explicit directionality.
In the initial vocabulary `updates`, `corrects`, `responds_to`, `implements` and
`supersedes` are directed; `contradicts` and `same_matter_as` are symmetric for
retrieval. Store one attributable relation record rather than manufacturing a
reverse duplicate for symmetric types. `other` is treated as directed unless a
future typed contract replaces it. Do not encode a universal civic ontology in
relation names.

`ClaimRelation` is only for relationships whose meaning is adequately expressed
by the typed proposition-to-proposition edge plus provenance/review. If the
relationship itself carries independent civic identity or attributes — role,
start/end dates, amount, percentage, contract term, or similar — it must be
promoted to a typed Association/Event-style record rather than hidden inside a
generic relation payload. AKF-013 already requires one concrete rich family: `RoleAssignment`, with stable
identity/revisions for subject entity, organization entity, role label/key,
validity interval, attributable origin/basis/lifecycle, and exact evidence.
Other association/event families remain deferred until a real fixture requires
them; this contract forbids designing `ClaimRelation` as the future junk drawer.

### RoleAssignment is the first rich civic relation

A `RoleAssignment` represents a person/entity holding a named role in an
organization over an optional interval. The role and dates belong to the
relationship, not to either entity and not to a ClaimRelation. Its revision
records at minimum:

```yaml
subject_entity: ent_...
organization_entity: ent_...
role_label: source-compatible human label
role_key: optional normalized local key
valid_from: optional civic date
valid_to: optional civic date
origin_kind: machine | rule | human
basis_kind: source_evidence | analyst_inference | mechanical_identity | other
evidence_refs: exact RepresentationTarget references when source-backed
rationale: optional concise explanation
lifecycle: candidate | active | rejected
```

Material correction creates a new revision rather than mutating the historical
assignment. Rich relationships with materially different attributes get their
own typed family rather than overloading RoleAssignment.

When a claim revision changes materially, existing relations keep their original
revision endpoints. The core may propose/review a replacement relation; it does
not silently retarget history.

`EvidenceLink.relation` and `ClaimRelation.relation_type` are different
contracts: evidence `challenges` one claim; one proposition may `contradict`
another proposition.

### Tags

Tags/topics are local, versioned vocabulary. A canton may create, import, or
share a taxonomy without making it globally canonical. Tags provide another
cheap shared anchor and do not imply pairwise claim relations.

### Storage shape

The baseline is relational, not a generic triple store. Prefer typed tables such
as claims, entities, claim-entity links, and claim relations over universal
`node/edge` or `subject/predicate/object` tables. This still forms a graph-shaped
record and can be traversed with ordinary/recursive SQLite queries.

Do not normalize every noun, date, or number into its own table before use cases
require it.

## Review Policies and Decisions

Review is a policy layer over records, not the condition for a Claim or
ClaimRelation to exist. Configuration may select mode by installation, source,
document profile, output, sensitivity, subject kind, or other bounded criteria.

Initial modes:

```text
strict
batch
supervised
```

### Strict

Protected use requires an explicit human review decision on the relevant exact
revision(s).

### Batch

One human action may cover a deterministic set of exact subject revisions, with
per-subject exceptions. The contract requires reproducible membership (for
example an ordered set or set fingerprint) and attributable outcome; it does
**not** require a permanent `ReviewBatch` entity/table.

### Supervised

Unreviewed machine/rule claims and relation candidates are immediately available
for permitted internal search. Human review occurs on demand or when another
policy requires it.

A `ReviewDecision` records exact subject revision(s) or reproducible subject set,
actor, action, rationale when needed, time, and applicable policy/configuration
identity when relevant. One operator may perform all actions; Canario records
actions/capabilities rather than requiring staffing roles.

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

### Purge and tombstones

Normal custody is immutable-by-default: no edit operation mutates acquired bytes.
`purge` is a separate exceptional policy action for a lawful/safety-driven need
to remove retained material. It must identify the affected canonical records,
remove the targeted bytes plus derived copies/index entries that preserve the
purged content, and record attributable authority/reason to the extent retention
of that audit information is itself lawful.

A tombstone, when permitted, contains only the minimum non-sensitive facts needed
to explain the deletion (opaque identity, time, action/authority, broad reason,
and safe lineage). It must not preserve prohibited content indirectly through raw
text, exact locators, digests, or sensitive metadata. `restricted` means bytes
still exist; `purged` means they do not.

## Queries

A query is read-only. It selects records by supported fields such as text,
entity, tag, source/document type, date, lifecycle/review visibility, optional
assessment, and explicit claim relations. It may use bounded relation traversal
or shared anchors without inventing semantic edges.

Queries are ephemeral by default. A durable saved-query contract is added only
when operator use proves that query definitions themselves need stable identity,
versioning, or sharing. Query results never become canonical civic claims merely
because they were returned or ranked.

## Outputs

An output consumes a bounded query/read model and organizes it for a purpose.
The baseline contract is deliberately small:

```text
read/query capabilities -> output-specific logic/state -> exporter
```

Output code has read-only core access by default. It may own validated local
presentation/curation state, but it cannot silently rewrite claims, evidence,
review decisions, entities, relations, or artifacts. Canonical mutation must go
through an explicit core operation.

The first implementation does not require a universal package manifest,
registry, install lifecycle, or canonical `OutputType/OutputInstance/OutputState`
records. Use versioned local identifiers/configuration where compatibility
actually exists. A stable shareable Output API/package format is promoted later
when multiple real outputs/installations prove the need.

An `Exporter` serializes output/query results to Markdown, JSON, CSV, HTML, or
another transport format.

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

When an output is deliberately released and reproducible publication history
matters, Canario may create an immutable snapshot containing exact input
revisions, output implementation/configuration identity, hashes, and publication
decision. Publication snapshots are not a prerequisite for internal outputs.

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

The first implementation uses a local Canario core as the sole canonical writer
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
