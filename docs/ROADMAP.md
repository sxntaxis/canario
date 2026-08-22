---
id: ACTAKIT-ROADMAP-001
kind: roadmap
state: proposed-for-acceptance
created: 2026-08-19
authority: roadmap-proposal
summary: Proof-gated roadmap from the current acta pipeline to a self-contained civic-record core, with complexity added only when real use requires it.
related:
  - ACTAKIT-ARCH-001
  - ACTAKIT-DATA-001
  - ACTAKIT-STATUS-001
---

# Roadmap

## Rule

ActaKit builds the smallest durable civic-record system that solves real work.
Future complexity is anticipated through boundaries, not preimplemented.

No persistent canonical database migration begins until the architecture, claim
semantics, evidence locators, review modes, pre-SQL model, revised schema
candidate, and its artifact/runtime proof gates are accepted. Disposable scratch
DDL is allowed only as a design proof and is not migration authority.

### Pre-release schema rule

Until ActaKit explicitly enters a compatibility-bearing Beta (or later) release,
there is no migration-history compatibility promise. Schema evolution is
**rebaselined into `0001`** and certified again. Do not accumulate `0002`,
`0003`, ... solely to preserve unreleased development databases. Incremental
forward migrations become the rule only after that compatibility boundary, when
real operator data must survive upgrades.

## Phase 0 — Accept the Model

Agree on:

- product scope and self-contained boundary;
- Depósito / Mesa de trabajo / Lector / Fichero / Mesa de control / Consultas /
  Salidas vocabulary;
- document typing vs representation/locator typing;
- claim meaning, shared anchors, first-class claim relations, and broad civic
  extraction policy;
- `strict`, `batch`, and `supervised` review semantics;
- source authority scopes;
- Output Type boundary and Episode/Hilo placement;
- privacy and correction principles.

**Gate:** a non-developer operator can explain the system accurately in ordinary
language and the pre-SQL examples expose no unresolved semantic contradiction.

## Phase 1 — Semantic Kernel and Tests

Implement dependency-light types/validation for:

- stable IDs and revision lineage where civic meaning requires it;
- CivicDocuments plus Representation occurrences/targets; DocumentPart/Collection only when a proving fixture/query requires them;
- claims, evidence links and typed locators;
- entities, claim-entity links, tags, and first-class claim relations;
- strict/batch/supervised review semantics and decisions;
- bounded query/read boundary and output separation.

**Gate:** invalid states fail before touching SQLite. Hilo/Episode can be modeled
as an Output Type fixture without becoming core entities.

## Phase 2 — Local Durable Depósito and Fichero

Implement:

- SQLite canonical store with a rebaselinable `0001` during pre-release, then explicit forward migrations after the compatibility boundary;
- content-addressed evidence archive;
- core-owned writes only;
- replay/stale-write protection only on boundaries proven to need it;
- backup and restore verification.

Do **not** require a daemon. CLI/local worker can call the core directly.

**Gate:** interrupted writes, duplicate acquisitions, changed source bytes, and
restore all preserve evidence/history correctly.

## Phase 3 — Source Connectors, Inbox, and Mesa de trabajo

First standardize acquisition at `ACTAKIT-INGRESS-001`:

```text
arbitrary external terrain
-> Source Connector
-> CaptureEnvelope
-> InboxPort
-> Depósito
```

The current Esparza scraper becomes one connector **after** the socket contract is
proved independently. Source connectors may privately use HTML, APIs, browser
automation, feeds, filesystems, or manual/push acquisition. Their common boundary
is the Inbox, not a common discovery algorithm. Explicit coverage/checkpoint
semantics prevent scrape absence from becoming deletion evidence.

Separately, implement Mesa de trabajo Representation processors as a curated
built-in ActaKit ladder. Swappable backends are an escape hatch for hardware,
licensing, unusual formats and local/cloud policy; ActaKit owns the default
processing/escalation policy.

The state-of-the-art research gate is closed. Its accepted reference path is:

```text
native/direct parse (D0/D1)
-> Poppler/pdftotext
-> OCRmyPDF + Tesseract
-> bounded official Codex CLI escalation
-> human review
```

Docling is optional and not the reference default. Heavy local VLMs, provider APIs
and OpenAI-compatible endpoints are specialized future venues, not freeze blockers.
Spreadsheet cells use direct deterministic structured parsing by default. No
universal numeric confidence spans these engines: preserve typed quality evidence
and let core policy accept, escalate or quarantine/review. Original custody is
immutable; every processor attempt/output is attributable.

**Current Phase-3 gate:** Connector SPI, Esparza shadow ingestion, processor
research and the Civic Processor Bench are complete. The generic `WORKBENCH-001`
boundary is implemented with exact target-backed run scope, typed QualityEvidence,
separate durable quality decisions, safe derived custody, replay semantics and
explicit egress policy. Independent certification is now required before the first
concrete D0/D1 adapter. Exact pins/licenses for optional backends become required
only when selected/enabled. Unsupported or low-quality extraction must fail
visibly or escalate without corrupting custody.

## Phase 4 — Lector and Broad Claim Extraction

Implement replaceable processors:

```text
rules/parsers
AI providers/local models
human entry
```

Extract civically relevant claims broadly, plus retrieval-relevant entities,
claim-entity links, tags, and candidate/direct claim relations. Store exact
process provenance and evidence links. Shared anchors must not create semantic
pairwise relations automatically.

**Gate:** a substantial real document can yield many machine-only claims without
requiring human clicks or losing exact citation traceability; entity anchors and
claim relations retain their own machine/rule/human provenance.

## Phase 5 — Mesa de control

Implement:

- supervised mode as the normal high-volume workflow;
- strict mode for selected high-consequence scopes;
- batch review with deterministic subject sets;
- correction/supersession;
- privacy/restriction exceptions;
- one-operator-first UX.

**Gate:** the operator can inspect/correct an important claim quickly, approve a
batch without claim-by-claim busywork, and always see whether material is
machine-only or human-reviewed.

## Phase 6 — First Vertical Proof

Use one newly acquired acta as the first end-to-end proof because the current
pipeline already understands that source class.

```text
source
-> artifact
-> representation
-> document profile
-> broad claim extraction
-> supervised review state
-> evidence resolution
-> query
```

No historical mass rewrite is part of this gate.

**Gate:** a later question about an obscure event can recover a machine-only
claim, open its exact evidence, review/correct it, and retain that history.

## Phase 7 — Consultas and Salidas

Implement deterministic search/filtering, then a minimal Output read boundary.
Persist saved queries only if operator use proves they need durable identity.

The first output proves the boundary by implementing the existing Hilo concept
outside the core:

```text
query -> Hilo output -> Episodes -> Markdown/JSON exporter
```

Add one tiny structurally different non-Episode output/fixture to prove Episode
is not universal; it need not be a second full product.

**Gate:** queries can use shared anchors and explicit relation chains; both outputs
consume the same Fichero without custom core schema and cannot silently mutate
claims/evidence/connections.

## Phase 8 — Operational 1.0

Harden the smallest useful deployment:

- one supported local installation path;
- clear configuration and health check;
- backup/restore commands;
- migration compatibility from the declared Beta/public compatibility boundary onward;
- source/extraction failure diagnostics;
- privacy-safe exports;
- operator documentation using the native metaphors;
- real routine use over a meaningful civic work cycle.

**Gate:** one operator can maintain the installation without understanding the
internal database, and a read-only consumer can find/cite records without
operator privileges.

## Horizon — Only When Earned

Design boundaries should allow, but roadmap does not require yet:

- local daemon/RPC and concurrent clients;
- multiple operator permissions/roles;
- stable third-party Output Type package SDK/registry;
- sharing/installing output types between cantons;
- inter-installation civic-data exchange;
- signed/federated snapshots;
- public web/API/automation access;
- specialized semantic/vector/graph search engines;
- alternate database engines;
- deliberate historical bulk migration.

Each moves into an active phase only with a concrete use case and acceptance
criteria.
