---
id: ACTAKIT-STATUS-001
kind: status
state: CIVIC_PROCESSOR_BENCH_IN_PROGRESS__NATURAL_CORPUS_AND_D3_D5_PARTIAL
created: 2026-08-19
updated: 2026-08-21
authority: operating
release_phase: prerelease
schema_compatibility_boundary: not-established
summary: Ingress and the Esparza shadow connector are certified; the Civic Processor Bench has natural corpus and D1 evidence but D2-D5 remain partial, so WORKBENCH-001 freeze and processor implementation remain blocked.
related:
  - ACTAKIT-ARCH-001
  - ACTAKIT-ROADMAP-001
  - ACTAKIT-INGRESS-001
  - ACTAKIT-CONNECTOR-ESPARZA-001
  - ACTAKIT-REPRESENTATION-PROCESSOR-RESEARCH-001
---

# Current Status

## Pre-release compatibility policy

ActaKit is **pre-release**. There is currently no public/beta compatibility
commitment and no user SQLite fleet whose historical schema must be preserved.
Until `release_phase` is explicitly advanced to `beta` (or a later
compatibility-bearing release) in this operating-status document:

- `0001` is the mutable/rebaselinable schema baseline;
- a correct schema change updates `MIGRATION_0001_SPEC.sql` and production
  `0001.sql`, then repeats the applicable freeze/runtime/implementation proofs;
- development databases may be recreated from a fresh `0001`;
- do **not** create sequential `0002`/`0003`/... migrations merely to carry
  pre-release development state forward;
- do **not** add legacy-compatibility code for unreleased schema shapes.

The migration-history compatibility obligation begins only at the explicit
compatibility boundary. From that boundary onward, existing user data becomes an
upgrade constraint and schema evolution must use forward migrations instead of
rebasing historical `0001`.

## Current Implementation

The repository currently implements the file/Markdown acta pipeline. Existing
operator data and curated Hilos are preserved; no mass regeneration or migration
is authorized by the architecture proposal.

One existing canton configuration contains deployment-specific absolute paths.
Those paths are legacy deployment configuration, **not** target product
dependencies. The future durable core must operate from its own configurable
storage without requiring any named external workspace or application.

## Current Source Checkpoint

The existing source investigation found the official written Concejo archive at
Acta 161 dated 2026-05-18 while the municipality's official video publication
showed later sessions through Session 180 in August 2026. The videos establish
that later sessions occurred; they do not establish the exact content or
approval status of unavailable written actas.

This source gap remains a useful real-world proof case for the future model:
source occurrence, source authority, artifact acquisition, and formal written
record are not interchangeable.

## Accepted Architecture Baseline

The semantic authority for the durable core is accepted in:

- `ARCHITECTURE.md`;
- `CONTRACTS.md`;
- `DATA_MODEL.md`.

ActaKit remains a self-contained civic-record system using:

```text
Inbox -> Depósito -> Mesa de trabajo -> Lector -> Fichero
                  -> Mesa de control -> Consultas -> Salidas
```

The SQLite candidate then passed deep pre-SQL research, adversarial critical
review, exact-artifact selector proofs, operational backup/restore/purge proofs,
a physical migration-freeze review, and post-freeze certification on the exact
registered SQLite 3.53.4 source ID.

## Active Edge

```text
accepted semantic contracts
-> certified MIGRATION_0001_SPEC.sql
-> bounded production implementation of migration/bootstrap 0001
-> certified implementation proof on exact SQLite 3.53.4
-> certified bounded Depósito custody writer
-> certified INGRESS-001 Source Connector SPI + Inbox
-> certified Esparza connector and bounded real network shadow dogfood
-> processor state-of-the-art Source Books + synthesis complete
-> Civic Processor Bench IN PROGRESS (natural corpus + D1 PASS; D2-D5 partial)
-> Representation processor implementation after benchmark selection
-> semantic writers and explicit canonical-cutover gate later
```

Migration `0001` implementation was authorized by
`notebook/research/pre-sql/schema/MIGRATION_0001_AUTHORIZATION.md` only for the
fresh-database bootstrap/runtime boundary and is now certified by
`notebook/research/pre-sql/schema/MIGRATION_0001_IMPLEMENTATION_CERTIFICATION.md`.
The frozen SQL hash is:

```text
31cac5ccc3440ce555242ba288317df527bb30949b2142026d8ceb2805d3adfc
```

No production code may silently alter that SQL contract. A changed specification
must return to freeze review and target-runtime recertification.

The implementation certification does not authorize canonical cutover or
production semantic writers. The bounded Depósito writer is now certified by
`notebook/research/pre-sql/schema/DEPOSIT_WRITER_CERTIFICATION.md`.

## INGRESS-001 current boundary

`docs/INGRESS.md` is accepted. The implementation lives in `actakit/ingress/` and
proves that HTML-inventory, incremental JSON-API, and manual-push fixtures all
terminate at one `InboxPort` without importing their terrain into the core DTO.

The bridge is intentionally one-way:

```text
SourceConnector -> CaptureEnvelope -> InboxPort -> DepositWriter
```

Connector code does not receive `DepositWriter` or canonical Source/persistence
identity. `DepositInbox` is host-bound to those core concerns. Specialized
connector failures propagate while already accepted custody remains preserved.

This boundary is certified on the exact SQLite 3.53.4 runtime. The Esparza CMS
connector is now the first certified real consumer and has passed bounded shadow
dogfood without changing the SPI. Plugin packaging and durable connector-run/
checkpoint persistence remain unfrozen.

## WP4C processor research gate

The state-of-the-art package at
`notebook/research/workbench/processors/` is complete for the selection horizon.
It does **not** authorize an `actakit/processors` implementation. The research
selects a benchmark slate and an escalation philosophy:

```text
native/direct parse
-> Poppler/pdftotext
-> OCRmyPDF + Tesseract
-> Docling structured processing
-> specialized visual/document AI (local or cloud by policy)
-> frontier multimodal AI (local or cloud by policy)
   - local candidate: Qwen3-VL family
   - cloud candidate: OpenAI multimodal API
   - specialist cloud candidate: Mistral OCR
-> human review
```

Processors are intended to be a curated built-in ActaKit capability. Backend
replaceability is an escape hatch for hardware, licensing, new/hard formats,
execution-venue policy and benchmarking; WP4C is not a plugin-marketplace project.
Cloud frontier capacity is optional but first-class: a weak host may escalate to
OpenAI instead of attempting a heavyweight local VLM, while no-egress deployments
remain fully local.

No universal numeric processor confidence is accepted. The pending design uses
typed, processor-attributable `QualityEvidence` and policy decisions equivalent
to `ACCEPT | ESCALATE | QUARANTINE_REVIEW`. Every transformation remains a
derived Representation with ProcessRun provenance; original custody is immutable.

**Current gate:** the bench has acquired natural Esparza, FECOMUDI and Quepos
fixtures and reproduced D1 findings, but D2-D5 execution is partial because the
host lacks required local runtimes and explicit cloud authorization. Exact
processor/model/version/license pins and escalation thresholds remain unfrozen.
The next run must compare the best local difficult-case path against an explicitly
egress-safe OpenAI cloud path (plus Mistral where useful), measuring quality,
hallucination, cost, latency and egress. API-key values remain external host
secrets and must never enter SQLite, ProcessRun evidence or logs.

## Current Prohibitions

- No canonical-data cutover or historical mass import is authorized yet.
- No legacy Markdown/Hilo rewrite is authorized by migration `0001`.
- No semantic Fichero, Claim, review, purge, or archive/GC writer is authorized
  beyond the bounded Depósito custody writer certified in this checkpoint.
- The Esparza Source Connector is certified only as a bounded shadow-mode SPI
  consumer. Its two dogfood runs do not modify the current scraper/Hilo path and
  are not canonical. Coverage is unknown because the runs were intentionally
  filtered and bounded; historical import and cutover remain unauthorized.
- No daemon/RPC/federation implementation is justified yet.
- No automatic public publication.
- No claim may conceal whether it is machine-only or human-reviewed.
- No AI output may serve as factual source evidence for its own claim.
- No individual political-preference profiling or targeted-persuasion use.

## Planning Documents

`ROADMAP.md`, `IMPLEMENTATION_PLAN.md`, and `RELEASE_1_0.md` remain planning
artifacts. Their future work packages do not expand this authorization. The
current authority for migration `0001` is the accepted semantic contract, the
certified freeze, and the bounded authorization record.
