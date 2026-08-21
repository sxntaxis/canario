---
id: ACTAKIT-IMPLEMENTATION-001
kind: implementation-plan
state: proposed-for-acceptance
created: 2026-08-19
authority: roadmap-proposal
summary: Concrete work packages for a minimal local civic-record core, broad traceable extraction, configurable supervision, queries, and extensible outputs.
related:
  - ACTAKIT-ARCH-001
  - ACTAKIT-CONTRACTS-001
  - ACTAKIT-DATA-001
  - ACTAKIT-ROADMAP-001
---

# Implementation Plan

## Implementation Doctrine

- Current scripts are adapters/legacy tools, not future canonical writers.
- Stable semantic boundaries are implemented before persistence.
- One operator is the default deployment assumption.
- The ActaKit core owns canonical writes; no daemon is required until concurrency
  justifies it.
- Machine extraction may create searchable claims without human approval.
- Human review is recorded precisely but can be strict, batch, or supervised.
- Output-specific concepts do not enter core schema merely because the first
  workflow uses them.

## WP0 — Architecture and Policy Acceptance

Freeze only what would be expensive to migrate later:

- product scope;
- core record distinctions;
- stable ID/revision/provenance boundaries where civic meaning requires them;
- typed locators;
- source authority scope and minimum acquisition provenance;
- claim/relation/review semantics;
- privacy/correction rules;
- Output Type write boundary.

Do not freeze daemon protocol, plugin packaging, federation, or final SQL names.

**Gate:** `ARCHITECTURE.md`, `CONTRACTS.md`, and `DATA_MODEL.md` accepted.

## WP1 — Repository and Test Foundation

- Make the full automated test command actually run all unit tests.
- Add contract fixtures for PDF, text/HTML, spreadsheet, scan/media, and unknown
  civic type.
- Add synthetic acta, report/officio, spreadsheet, concatenated-document, and
  malformed fixtures.
- Add deterministic canonical serialization/hash tests.
- Keep production civic data out of the repository.

**Gate:** CI/test command exercises semantic contracts instead of only syntax.

## WP2 — Semantic Core

Implement pure/domain logic for:

- stable IDs/revision lineage;
- bounded source authority/acquisition semantics;
- artifact/representation lineage;
- CivicDocument typing, profiles, parts and collections;
- claims/revisions;
- typed EvidenceLinks;
- entities/aliases, claim-entity links, tags, and first-class claim relations;
- strict/batch/supervised review semantics and decisions;
- query/read boundary and output write restrictions.

No SQLite is needed to prove these transitions.

**Gate:** impossible/ambiguous states fail in unit tests; `unknown` and `otro`
work without special-case crashes.

## WP3 — Local Persistence and Evidence Archive

Implement:

- SQLite schema reviewed against `DATA_MODEL.md`;
- logical Artifact custody records separated from content-addressed ArchiveObject storage with atomic verified writes;
- repositories behind the ActaKit core;
- a rebaselinable `0001` during pre-release; forward migration history begins only after the declared compatibility boundary; replay/stale-write guards only where tests require them;
- consistent backup/export and restore verification;
- fixity/health checks.

CLI/workers call the core directly initially.

**Gate:** kill/restart, duplicate capture with shared physical bytes but distinct Artifact provenance, changed file, archive mismatch, stale
write, and clean restore cases pass.

## WP4 — Source Connector SPI, Inbox, and Representation Processors

### WP4A — Source Connector SPI + Inbox (`INGRESS-001`)

Freeze the terrain-neutral ownership boundary, not source geography or plugin
packaging:

- `SourceConnector` is a swappable inbound adapter;
- `InboxPort.accept(CaptureEnvelope)` is the common socket;
- ActaKit binds Source identity, connector key/version and custody policy;
- connector DTOs contain only acquisition facts/bytes, never CivicDocument or
  Fichero semantics;
- generic capabilities describe pull/push, inventory/incremental and checkpointing;
- run coverage is explicit; checkpoint bytes are opaque to core;
- specialized assumptions fail loudly while already accepted custody survives;
- plugin loading/entry-point packaging remains unfrozen.

Prove the SPI with incompatible HTML-inventory, incremental-API and manual-push
fixtures **before** adapting Esparza.

### WP4B — Real source connectors / shadow ingestion

**Current:** the Esparza CMS connector is implemented as the first SPI consumer
and has local proof. It preserves listing HTML before parsing, handles source
outage/changed bytes/duplicates/malformed bodies/redirects fail-closed, and has a
separate isolated shadow host. Exact SQLite 3.53.4 certification and real-network
shadow dogfood remain the gate before this work package is complete.

Esparza remains a consumer of the SPI, not its reference model. No canonical
cutover, historical import, or semantic writer is authorized.

### WP4C — Mesa de trabajo Representation processors

Only after original custody, adapt extraction behind a separate boundary:

- PDF/DOCX/text/HTML extraction;
- spreadsheet/table representation where required;
- OCR/scan path when needed;
- media/transcript path only when a real source requires it;
- representation/locator capability registration.

Security requirements: bounded size/time/resources, safe paths, redirect/host
policy, no document-controlled shell/network behavior. Large-object/streaming
transport is added when a real source proves the need rather than assuming all
payloads are small.

**Gate:** source geography cannot leak through Inbox; source outage/malformed
material preserve custody honestly; unsupported extraction fails visibly without
corrupting original evidence.

## WP5 — Lector and Claim Extraction

Create a common processor interface for rule-based, model-based, and human
extraction.

Initial outputs:

- claim revisions with origin/process metadata;
- exact evidence links;
- entity mentions;
- local topic/tag assignments;
- claim-entity anchors;
- candidate/direct claim relations with origin/basis;
- document classification/profile suggestions.

Default extraction policy aims for comprehensive civic relevance rather than a
small editorial summary. Shared entity/tag anchors may be created broadly;
claim-to-claim semantic relations are recorded separately and never inferred
merely from shared subject matter.

**Gate:** one long document can produce a large claim set with stable provenance,
no duplicate explosion on replay, and no review requirement merely to store or
search those claims/connections; relation replay is idempotent and attributable.

## WP6 — Review and Operator Workflow

Implement review configuration:

```text
strict
batch
supervised
```

Operator experience must support:

- seeing machine-only vs human-reviewed immediately;
- opening exact source evidence from a claim;
- correcting/rejecting/restricting a claim;
- reviewing a whole deterministic batch with exceptions;
- forcing review for sensitive/public contexts;
- inspecting unresolved extraction/locator/type conflicts.

Do not build enterprise staffing roles. Record actor/action/capability so a
future multi-operator system remains possible.

**Gate:** a single operator can process and supervise a high-volume document
without claim-by-claim approval fatigue.

## WP7 — Acta Vertical Proof

Use a newly available official acta as the first real profile proof:

```text
acquire original
-> extract representation
-> classify acta/session structure
-> extract broad claims
-> attach exact evidence
-> supervised search
-> review/correct selected important claims
```

No Episode/Hilo is required for the core proof.

**Gate:** an obscure claim can later be found, verified against the exact source,
corrected, and traced through revisions/process history.

## WP8 — Queries and Output Types

Implement basic deterministic querying:

- full-text;
- source/document type/date;
- entity/tag;
- direct claim relations and bounded relation traversal;
- review visibility/lifecycle and optional attributable assessment;
- evidence resolution.

Then implement the minimal Output read boundary.

### First real output: Hilo

Move reader organization into an output-specific schema:

```text
Hilo
  -> Episode
  -> claim memberships
  -> chronological rendering
```

Preserve useful current Hilo behavior but make it consume core claims via the
query/read interface rather than own civic truth.

### Second proof output

Implement a tiny structurally different non-Episode fixture/output to prove no
Episode dependency in core; do not build a second full product merely for the gate.

**Gate:** a query can follow a real multi-document relation chain using SQLite,
and both output shapes consume the same bounded read model without direct
canonical database mutation. Package/install lifecycle is not required.

## WP9 — Export, Recovery, and Operational Hardening

- Markdown/JSON/CSV exporters as serialization concerns.
- Immutable output snapshot option for deliberate publication/release.
- Backup and restore commands with verification.
- Post-compatibility migration upgrade policy based on actual schema needs; pre-release schema changes rebaseline `0001` rather than accumulating compatibility migrations.
- Spanish-first operator guide using Depósito/Mesa/Lector/Fichero/Consultas/
  Salidas language.
- One supported installation/update path.

**Gate:** clean-machine restore and routine operator workflow pass without manual
SQL/file surgery.

## WP10 — 1.0 Proof

A release candidate must demonstrate:

- routine use by at least one real canton/operator over a meaningful cycle;
- broad extraction without mandatory per-claim approval;
- traceable citations across more than one document/representation type;
- strict/batch/supervised review behavior;
- queries and at least two output shapes;
- backup/restore;
- no unresolved critical integrity/privacy/security defects;
- documentation understandable without architecture expertise.

A second independent installation is valuable compatibility evidence but not a
reason to prebuild federation.

## Explicitly Later

Unless a concrete use case promotes them:

- daemon/RPC/multi-writer architecture;
- complex account/role system;
- public server/API/automation adapters;
- Output Type registry/marketplace;
- cryptographic inter-canton federation;
- cross-canton canonical data synchronization;
- specialized graph/vector databases or indexes;
- alternate relational engines;
- mass historical migration.
