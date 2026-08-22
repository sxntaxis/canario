---
id: ACTAKIT-ARCH-001
kind: target-architecture
state: accepted
accepted: 2026-08-21
created: 2026-08-19
authority: architecture-proposal
summary: Self-contained civic-record architecture for acquiring public documents, extracting traceable claims, reviewing when needed, querying the record, and producing extensible outputs.
related:
  - ACTAKIT-ROADMAP-001
  - ACTAKIT-DATA-001
  - ACTAKIT-STATUS-001
---

# Target Architecture

## Purpose

ActaKit is a self-contained local system for **acquiring, preserving, extracting,
classifying, relating, searching, reviewing, and exporting information contained
in public civic or governmental records**.

Actas are the first mature workflow, not the product boundary. The same core must
handle reports, budgets, official correspondence, resolutions, plans, public
datasets, recordings, and document types not known in advance.

ActaKit is not a party CRM, strategy workspace, general note system, propaganda
engine, or political-profiling system. It may interoperate with other tools only
through generic imports/exports or adapters; no external workspace or service is
part of its architecture.

## Design Law

> **As simple as possible, as complicated as necessary.**

ActaKit applies this in two directions:

1. **Implement only complexity justified by real use.**
2. **Choose boundaries now that prevent expensive destructive migrations later.**

A future risk may justify a stable interface, identifier, or separation today.
It does not automatically justify a daemon, network protocol, federation system,
plugin registry, graph database, or multi-user permission hierarchy today.

## Native Human Vocabulary

ActaKit should be explainable without database vocabulary. These metaphors are
part of the product language used in documentation and operator interfaces. They
are **not mandatory directory or module names**; code uses the clearest technical
names for maintainability.

| Human concept | Question | Technical responsibility |
|---|---|---|
| **Inbox** | ¿Qué está entrando desde afuera? | Terrain-neutral ingress port for interchangeable Source Connectors |
| **Depósito** | ¿Qué conseguimos realmente? | Source capture, immutable-by-default artifacts, custody |
| **Mesa de trabajo** | ¿Cómo podemos leerlo? | Representations: text, OCR, tables, transcripts |
| **Lector** | ¿Qué contiene? | Parsers, rules, AI, or humans extracting structure |
| **Fichero** | ¿Qué afirma el material, dónde y cómo se conecta? | Claims, evidence links, entities, tags, connections |
| **Mesa de control** | ¿Qué necesita atención humana? | Review, correction, privacy, exceptions |
| **Consultas** | ¿Qué necesito encontrar ahora? | Search and filters; durable saved definitions only if real use requires them |
| **Salidas** | ¿Cómo quiero usar o presentar esto? | Hilos, timelines, trackers, reports, exports |

The whole program can therefore be visualized as:

```text
INBOX
  interchangeable source connectors terminate at one ingress contract
    ↓
DEPÓSITO
  public source material as actually acquired
    ↓
MESA DE TRABAJO
  usable representations of that material
    ↓
LECTOR
  software/AI/human extraction and classification
    ↓
FICHERO
  traceable claims + evidence + entities + tags + explicit connections
    ↓
MESA DE CONTROL
  human supervision where policy or importance requires it
    ↓
CONSULTAS
  find the subset relevant to a question
    ↓
SALIDAS
  organize or present that subset for a purpose
```

## Product Scope

A civic record is in scope when it is public material that records or evidences
public decisions, actions, resources, obligations, conditions, claims, or other
information relevant to civic affairs.

Typical material includes:

- actas, agendas, convocatorias, agreements, resolutions, and dictámenes;
- official correspondence, reports, budgets, plans, regulations, and contracts;
- public procurement material and public case files;
- official notices and institutional communications;
- public datasets, spreadsheets, maps, recordings, or transcripts;
- records from municipalities, public institutions, public-service bodies, or
  other organizations acting in a public civic capacity.

ActaKit does **not** attempt to archive the whole internet or convert every
sentence into political intelligence. Extraction aims to be comprehensive
within civic relevance.

## Core Shape

The irreducible evidence/knowledge path is:

```text
Source
  ↓
Acquisition observation
  ↓
Artifact ──> ArchiveObject (physical bytes; shareable by digest)
  ↓
Representation
  ↓
CivicDocument
  ↓
Claim ← EvidenceLink → exact place in Representation
```

Around the claim are lightweight structures useful for retrieval:

```text
Claim
├── raw EntityMentions -> optional resolved Entity anchors
├── tags/topics
├── explicit ClaimRelations
├── dates/periods when useful
└── quantities when useful
```

Review and outputs are deliberately **not** prerequisites for a claim to exist.
They act on top of the traceable record.

## Source ingress: Connector -> Inbox

External sources have incompatible terrain. ActaKit therefore does not define its
acquisition architecture by the current Esparza scraper or by a universal
`scrape()` method. A **Source Connector** owns source-specific discovery/fetching
and terminates at the terrain-neutral **Inbox** ingress port.

```text
HTML/API/browser/feed/filesystem/manual/...
                 ↓
          Source Connector
                 ↓
          CaptureEnvelope
                 ↓
          Inbox / IngressPort
                 ↓
              Depósito
```

The connector may not write canonical custody or semantic tables directly.
ActaKit binds the Inbox to canonical Source identity, connector key/version and
core-owned custody policy. Discovery/checkpoint mechanics remain source-specific;
coverage is reported explicitly so absence in one run is never deletion proof.

The focused accepted contract is `INGRESS.md`. Source Connector acquisition is
separate from downstream Representation processors such as PDF extraction/OCR.

## Evidence Custody: the Depósito

A source, one observation/acquisition attempt, downloaded bytes, extracted text,
and a human-readable document identity are different things.

```text
source
  -> acquisition observation
  -> logical Artifact custody record
  -> content-addressed ArchiveObject bytes
  -> one or more representations
```

The baseline only needs enough acquisition history to answer **where, when, and
how these bytes were observed**. A discovery adapter may later justify separate
run/checkpoint structures, but those are not universal semantic requirements.

The same bytes acquired twice create distinct logical Artifacts while their
Artifacts may reference one shared physical ArchiveObject. This keeps acquisition
provenance, restriction and purge decisions independent without duplicating bytes.
A changed file at the same URL is a new Artifact and a different ArchiveObject.
Failure or absence during a later acquisition never deletes prior evidence.

ArchiveObjects are content-addressed and hash-verified. Artifacts are stable
custody identities, not hashes. The canonical database stores metadata and
relationships; it is not a substitute for original evidence bytes.

## Representations: the Mesa de trabajo

A representation is something the Lector can inspect or cite. The `original`
Representation is the inspectable view of its Artifact's captured bytes; it does
not duplicate the Artifact -> ArchiveObject pointer. Derived material forms keep
their own bytes plus an exact parent and attributable process provenance:


```text
PDF original
text extraction
OCR text
page image
spreadsheet/table view
transcript
normalized text
redacted public derivative
```

Document semantics and locator semantics are independent. An acta can be PDF,
HTML, scan, or transcript; an informe can use the same representation formats.

WORKBENCH-001 makes transformation attempts first-class without creating a generic
operation graph. A processor receives retained bytes plus explicit registered
RepresentationTarget scope, never a caller-controlled path. The core Workbench
persists one terminal ProcessRun, its ordered exact inputs, typed/namespaced
QualityEvidence, a separate policy decision, and any derived Representation bytes.
Processors themselves cannot write SQLite/archive state. Capability and execution
venue are orthogonal, so `visual_transcribe` may later be satisfied by Codex, a
provider API, or an optional local model without changing custody or policy
contracts. Cloud egress is authorized before invocation and credentials stay with
the trusted executor boundary. The Workbench inherits `restricted` onto its derivatives and has no declassification authority; a later explicit reviewed redaction/release operation may publish a `redacted_derivative` without mutating the restricted original.

Evidence locators therefore follow the representation:

```text
PDF         -> page/folio + quote/region
Text/HTML   -> offsets + exact quote + context
Spreadsheet -> sheet/table + cell/range or row/header + values
Image/scan  -> page/image + region
Audio/video -> start/end time + transcript anchor when available
JSON/XML    -> stable path + observed value/hash
```

Article, item, agreement, budget line, or chapter are useful semantic context,
not universal evidence coordinates.

## Civic Documents Without a Closed Ontology

A `CivicDocument` describes what a document **means institutionally**, separate
from how it is encoded.

Typing preserves three facts:

```text
source-supplied type   what the publisher called it
normalized type        ActaKit's broad classification
profile                 optional specialized structure
```

Unknown material is allowed. A new bureaucratic label does not require a schema
migration. Before classification a document may be `unknown`; after review an
unrecognized but legitimate type may remain `otro` with its original label
preserved.

A `DocumentPart` is optional structure inside one document. A collection groups
multiple documents when the civic object is a package or case such as an
expediente. Neither is required for ordinary documents.

## Graceful Degradation

Unknown or malformed material must fail **downward**, not disappear:

```text
Can preserve bytes?        -> preserve them.
Can identify media type?   -> record it.
Can extract usable text?   -> keep the representation.
Can classify the document? -> classify it.
Cannot?                    -> keep it unknown.
Can extract traceable claims? -> keep them.
Cannot use a specialized profile? -> continue generically.
```

ActaKit must never invent structure merely to avoid `unknown`. A malformed
representation may be stored while remaining unusable as exact factual support.

## The Lector Is Not “the AI”

A Lector is anything that inspects a representation and proposes structure:

```text
parser
regular expression/rule
OCR engine
local model
remote model
human entry
```

Use conventional software when it is sufficient and AI when semantic judgment
adds value. No provider or model is architectural authority.

Every automated run records its inputs and implementation/model/configuration so
results can be reproduced, compared, replaced, or reprocessed later.

Documents are always data, never executable instructions to an AI agent. A
reader has no shell, credential, publication, or unrestricted canonical-write
authority merely because it can inspect content.

## Claims: Extract Broadly, Keep State Axes Separate

A claim is **an identifiable proposition found in or derived from civic source
material**, not “a truth approved by a human.”

Extraction should be as comprehensive as practical for politically/civically
relevant content, including decisions, votes, money, responsibilities, dates,
projects, deadlines, requests, commitments, reported problems, institutional
responses, quantitative facts, and other later-searchable developments.

The system should not optimize only for what looks important today. The value of
ActaKit is partly that an obscure fact can become easy to recover months later.

Do not compress different questions into one status or confidence score:

```text
origin       machine / rule / human, with exact process/input when applicable
kind         source assertion / derived inference / community report / question
lifecycle    active / rejected / superseded / retracted / restricted
review       no human decision / human-reviewed, derived from review history
assessment   optional attributable judgment such as supported / contested / refuted
```

`machine-only` describes review visibility, not lifecycle. `corrected` means a
new revision or explicit correction event, not a permanent status. An assessment
is optional and never presented as ActaKit measuring objective truth; evidence
links and claim relations remain the inspectable basis.

A practical claim boundary is:

> the smallest proposition worth verifying, correcting, searching, or relating
> independently.

ActaKit does not atomize prose merely because a model can.

## Source Authority: What Can This Evidence Demonstrate?

“Official” is not a universal proof level. Bounded source authority configuration records the kinds of
assertions a source can reasonably support.

For example:

```text
approved acta      -> what the formal record says was agreed
session recording  -> what was said/heard/observed in the recording
press release      -> what the issuing body announced or claimed
budget table       -> values represented in that budget document
secondary article  -> what that publication reported
```

ActaKit must distinguish “the institution said X” from “X happened” and from
“the institution formally agreed X.” Evidence links and claim wording carry
that limitation instead of laundering all official-looking material into the
same authority class.

AI output can create or contextualize claims. It is never the factual evidence
supporting a source assertion.

## Review: the Mesa de control

ActaKit is **single-operator-first**. A normal canton installation is expected to
have one operator, sometimes two, and potentially many read-only consumers.
The architecture records actions precisely without inventing an organization
chart that small teams do not have. Claims and explicit claim relations use the
same supervision principle: unreviewed machine/rule output is allowed, but never
mislabeled as human-reviewed.

Review policy is configurable. Initial modes:

### `strict`

Claims/relations covered by the policy require explicit human review before
protected downstream use.

### `batch`

One human action can apply to a deterministic set of exact claim/relation
revisions, with individually addressable exceptions. **Batch review is a 1.0
capability; it does not require a heavyweight `ReviewBatch` subsystem or table.**
The implementation may persist a compact subject-set fingerprint plus exceptions
if that is sufficient to reconstruct the decision.

### `supervised`

Machine-extracted claims and relations become internally searchable immediately
with clear unreviewed provenance. Human review happens on demand or when policy
triggers it.

`supervised` is the expected everyday mode for high-volume extraction. A public
or sensitive output may independently require human-reviewed material even when
the internal Fichero allows unreviewed material.

A review decision identifies the exact revision(s) it covered and the actor,
action, time, and rationale when needed. Readiness means process sufficiency,
not metaphysical truth.

## The Fichero Is a Network, Not a Pile of Claims

The Fichero is the durable searchable civic record. Claims do not exist in a
vacuum: durable connections are part of the record, not something an AI must
rediscover every time a user searches.

Its universal core stays small:

- claims and claim revisions;
- exact evidence links;
- raw `EntityMention`s preserving what the source actually said;
- entities needed as shared resolved anchors for retrieval;
- local tags/topics;
- explicit claim-to-claim relations when they carry real meaning.

### Raw mentions before resolved identity

The Lector must not collapse a source string directly into canonical identity. A
raw occurrence such as `"AyA"`, `"Municipalidad Esparza"`, or `"Juan Pérez"`
is preserved first as an `EntityMention` with its exact observed text,
representation/locator context, extraction origin, and optional claim context.

An `EntityMention` may remain unresolved indefinitely. Candidate or confirmed
resolution to an `Entity` is a separate attributable decision. This preserves
what the source actually contained and prevents name equality from becoming
identity truth.

There are two different kinds of connection.

### Shared anchors

Many claims can point to the same entity or tag:

```text
Claim A -> entity: Puerto Caldera
Claim B -> entity: Puerto Caldera
Claim C -> entity: Puerto Caldera
```

This is enough to retrieve the claims together. It does **not** assert that A, B,
and C logically update, contradict, or respond to one another. ActaKit must not
create pairwise edges merely because two claims share a subject.

### Explicit claim relations

When the relationship itself matters, store it as a first-class record:

```text
Claim B -> updates -> Claim A
Claim C -> contradicts -> Claim B
Claim D -> responds_to -> Claim C
```

The relation records who/what proposed it, its exact endpoint revisions, its
basis, lifecycle/review state, and exact evidence/claim references or rationale
needed to understand it. A machine-proposed relation may remain searchable as machine-only; a human
review is not required merely for the connection to exist.

This gives ActaKit a **graph-shaped civic record** without requiring a graph
database. The baseline persists typed entities, joins, and claim relations in
SQLite. A specialized graph engine is justified only if real traversal/query
workloads later exceed what the relational model can handle cleanly.

### Entity reconciliation lineage

Entity identity is stable and local, but reconciliation can improve over time.
Aliases alone are not enough when later evidence shows that two local entities
are the same thing or that one mistaken entity actually represented several.

Merge/split decisions therefore create a small append-only reconciliation
lineage recording the input entity IDs, output/survivor entity IDs, actor/process,
time, and rationale/basis. Old claim/entity links are not silently rewritten.
Queries may follow accepted merge lineage for current retrieval; after a split,
ambiguous old links remain historically explainable and individual mentions/links
can be re-resolved deliberately.

This lineage is an identity-maintenance mechanism, **not** a generic entity graph.

### When a relation becomes a civic object

`ClaimRelation` remains intentionally narrow: it expresses proposition-to-
proposition meaning such as `updates`, `contradicts`, or `responds_to`. Do not
turn it into a generic edge payload.

When a relationship has independent civic attributes or identity — for example a
role with start/end dates, a contract with amount/term, or a membership with a
percentage — it crosses a promotion boundary and belongs in a typed rich record
with its own evidence/provenance. AKF-013 already proves one such 1.0 family, so
`RoleAssignment` is concrete in the first schema: subject entity, organization,
role, validity interval, origin/basis/lifecycle and exact evidence. Other rich
families remain absent until their own fixture/query proves them. `ClaimRelation`
stays narrow rather than becoming an attributed-edge junk drawer.

Tags/taxonomies are local by default and may be shared deliberately. ActaKit
must not impose one national topic taxonomy.

Dates, quantities, locations, or other structured values should become dedicated
relational structures only when real query/integrity requirements justify it.
Do not model a universal ontology or generic everything-is-a-node triple store in
advance.

## Consultas Are First-Class Read Operations

A query selects civic records without changing them:

```text
“agua” + place + date range
all claims mentioning institution X
all budget claims above an amount
all unresolved commitments in a period
```

Queries may follow shared entity/tag anchors or explicit claim-relation chains,
including bounded recursive traversal when useful. Query results are not new
civic truth and do not create semantic edges.

The baseline needs deterministic query functions and filters. A durable
versioned `SavedQuery` becomes canonical only when real operator use demonstrates
that a query definition itself needs identity/history; it is not a mandatory
first-schema object.

Search must let consumers distinguish/filter unreviewed, human-reviewed,
rejected, retracted, restricted, or explicitly assessed material according to
access policy.

## Salidas Are Extensible and Shareable

A **Salida** turns a query/result set into a useful organization or presentation.
The architectural requirement is a narrow read boundary: output code can query
and organize the Fichero but cannot silently rewrite canonical claims/evidence.

Examples:

```text
Hilo
chronology
agreement tracker
budget monitor
project sheet
weekly digest
citation packet
```

An **Exporter** only serializes a result/output as Markdown, JSON, CSV, HTML, or
another transport format. Output logic and serialization are separate concepts.

The first implementation does **not** need a plugin marketplace, package registry,
install lifecycle, or universal `OutputType/OutputInstance/OutputState` tables.
It only needs a boundary clean enough that Hilo can live outside the core and a
small structurally different proof can consume the same read model. A richer
shareable Output API is horizon work once two real outputs justify it.

### Episode belongs to the Hilo output

`Episode` is not universal civic-record structure. It is one useful reader-facing
unit used by the Hilo output to group related claims into a dated development.
Another Output Type may use agreements, cards, rows, milestones, or no grouping
at all.

Hilo-specific state therefore lives in the Hilo output namespace. Deleting or
rebuilding a Hilo never destroys the claims/evidence from which it was built.

## Canonical Storage

The first durable implementation is intentionally local and simple:

```text
CLI / local operator UI / worker
            |
            v
       ActaKit core
        |       |
        v       v
     SQLite   archive
        |
        v
queries / outputs / exports
```

The **ActaKit core is the sole canonical writer**. Clients do not write SQLite
by hand.

A continuously running local service, Unix socket, RPC protocol, PostgreSQL,
or multi-writer architecture is **not required initially**. Those become
implementation choices only when multiple concurrent clients/operators create a
real need. The authority boundary is designed now; the daemon is not.

SQLite remains on local attached storage and uses explicit migrations, foreign
keys, recursive queries where justified, and safe backup procedures.
Idempotency keys, stale-write guards, and record hashes are added where a concrete
replay/concurrency/import failure mode requires them; they are not universal tax
on every mutation. Original/derived bytes live in the archive, not as database
blobs by default.

## Corrections, History, and Purge

No important state is silently overwritten. Correcting a claim creates a new
revision/supersession relationship. Ordinary revision history need not create a
separate heavyweight “correction case”; explicit correction records are
reserved for events such as retraction, public correction, redaction, evidence
unlinking, identity reconciliation, or purge where the action itself matters.

Absence from a new acquisition observation, query, output, or export never means
deletion.

Evidence custody is **immutable by default, not absolutely undeletable**. Normal
editing never mutates or overwrites acquired bytes; redaction creates a separate
derivative. A lawful or safety-driven purge is an exceptional explicit policy
operation that removes the targeted bytes and derived copies/indexes that retain
the purged content.

When policy and law permit, ActaKit keeps a minimal non-sensitive tombstone:
opaque record identity, purge time, attributable authority/action, broad reason
code, and enough lineage to explain that material once existed. The tombstone
must not retain the very content, raw mention, locator, digest, or metadata whose
retention the purge forbids. If even that audit metadata cannot lawfully remain,
the policy may require its removal as well.

`restricted` and `purged` are different: restricted material still exists under
access controls; purged material does not. Claims or evidence links affected by
purge must become visibly unavailable/reviewable according to policy rather than
silently appearing fully evidenced.

## Privacy and Publication

Preserving original public evidence and republishing every datum from it are
different actions. ActaKit can retain source material while minimizing public
outputs.

Precise home addresses, medical information, identifying information about
minors, personal contact details, and inferred individual political preference
are blocked from public outputs by default unless a deliberately accepted policy
says otherwise.

ActaKit does not automate targeted political persuasion or individual political
profiling.

Publication, if enabled, is an Output/Export concern over an explicit immutable
snapshot. It never turns generated Markdown, a search index, or a public site
into canonical authority.

## Horizon: Design For, Do Not Build Yet

These possibilities justify clean boundaries but are not first-version
requirements:

- local daemon/RPC for concurrent clients;
- richer multi-user roles and permissions;
- a stable third-party Output Type package API/registry;
- data exchange between independent installations;
- cryptographically signed inter-canton snapshots;
- public network/API/automation services;
- specialized graph/RDF/vector engines or projections;
- large-scale historical migration;
- alternate database engines.

They must earn implementation through real use.

## Verification

Before the first persistent canonical schema is accepted, demonstrate:

1. original bytes survive acquisition and reprocessing unchanged;
2. a claim resolves to exact evidence in multiple representation types;
3. unknown/misshaped documents degrade gracefully;
4. machine-only claims are searchable without masquerading as reviewed claims;
5. `strict`, `batch`, and `supervised` review policies have unambiguous behavior;
6. claims sharing an entity are jointly retrievable without manufacturing
   pairwise semantic edges;
7. an explicit claim relation retains endpoint revisions, origin, basis, and
   review state and can be traversed later;
8. a query can retrieve claims across documents, entities, tags, relations, and time;
9. an Output Type can organize results without canonical-write authority;
10. a Hilo can define Episodes without making Episode a core record;
11. correction/reprocessing does not erase history or silently retarget relations;
12. backup/restore reproduces the Fichero, its connections, and referenced evidence.

## Acceptance Required

This document is proposed architecture, not implementation authorization.
Acceptance freezes the **semantic boundaries**, not every future module, SQL
column, plugin API, deployment mechanism, or release ceremony.

The pre-SQL model has now been exercised by the Book/fixture gate and a revised
SQLite candidate. The current concrete gate is the artifact/runtime proof list in
`SQLITE_SCHEMA_CANDIDATE.md` and the adversarial findings in
`notebook/research/pre-sql/schema/CRITICAL_REVIEW.md`; migration `0001` remains
unauthorized until those proofs pass.
