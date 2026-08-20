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
- ID/revision/provenance rules;
- typed locators;
- source authority scope;
- claim/review semantics;
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

- IDs/revisions/operations;
- SourcePolicy authority scopes;
- artifact/representation lineage;
- CivicDocument typing, profiles, parts and collections;
- claims/revisions;
- typed EvidenceLinks;
- entities/tags/simple relations;
- review policy/batch/decision;
- saved query definitions;
- Output Type manifests and permissions.

No SQLite is needed to prove these transitions.

**Gate:** impossible/ambiguous states fail in unit tests; `unknown` and `otro`
work without special-case crashes.

## WP3 — Local Persistence and Evidence Archive

Implement:

- SQLite schema reviewed against `DATA_MODEL.md`;
- content-addressed archive with atomic verified writes;
- repositories behind the ActaKit core;
- migrations and stale-write/operation replay guards;
- consistent backup/export and restore verification;
- fixity/health checks.

CLI/workers call the core directly initially.

**Gate:** kill/restart, duplicate capture, changed file, archive mismatch, stale
write, and clean restore cases pass.

## WP4 — Source and Representation Adapters

Refactor current acquisition/extraction scripts behind bounded interfaces:

- source discovery/acquisition;
- PDF/DOCX/text/HTML extraction;
- spreadsheet/table representation where required;
- OCR/scan path when needed;
- media/transcript path only when a real source requires it;
- representation/locator capability registration.

Security requirements: bounded size/time/resources, safe paths, redirect/host
policy, no document-controlled shell/network behavior.

**Gate:** source outage, malformed file, changed bytes at same URL, duplicate
filename, unknown type, and extraction failure preserve honest state.

## WP5 — Lector and Claim Extraction

Create a common processor interface for rule-based, model-based, and human
extraction.

Initial outputs:

- claim revisions with origin/process metadata;
- exact evidence links;
- entity mentions;
- local topic/tag assignments;
- simple useful relations;
- document classification/profile suggestions.

Default extraction policy aims for comprehensive civic relevance rather than a
small editorial summary.

**Gate:** one long document can produce a large claim set with stable provenance,
no duplicate explosion on replay, and no review requirement merely to store or
search those claims.

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
- review level/epistemic status;
- evidence resolution.

Then implement the minimal Output Type boundary.

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

Implement a small structurally different fixture/output such as a timeline or
agreement tracker to prove no Episode dependency in core.

**Gate:** Output Types can be installed/configured/rebuilt independently; their
code/state has no direct canonical database mutation path.

## WP9 — Export, Recovery, and Operational Hardening

- Markdown/JSON/CSV exporters as serialization concerns.
- Immutable output snapshot option for deliberate publication/release.
- Backup and restore commands with verification.
- Migration upgrade/downgrade policy based on actual schema needs.
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
- graph/vector databases;
- alternate relational engines;
- mass historical migration.
