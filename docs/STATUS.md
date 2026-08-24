---
id: ACTAKIT-STATUS-001
kind: status
state: LECTOR_001_SEMANTIC_EXTRACTION_BOUNDARY_IMPLEMENTED_AND_CERTIFIED
created: 2026-08-19
updated: 2026-08-24
authority: operating
release_phase: prerelease
schema_compatibility_boundary: not-established
summary: WORKBENCH-001, the D1/D2/Codex processor ladder, and LECTOR-001 are independently certified and integrated. The first bounded canonical semantic extraction writer now persists machine-only evidence-backed Claims without granting review/entity-reconciliation authority.
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
-> Civic Processor Bench complete
-> WORKBENCH-001 generic processor substrate independently certified
-> PROCESSOR-DIRECT-001 Poppler native-PDF adapter independently certified
-> PROCESSOR-OCR-001 OCRmyPDF + Tesseract adapter independently certified
-> PROCESSOR-CODEX-001 one-page Codex CLI visual adapter independently certified
-> LECTOR-001 bounded semantic extraction boundary independently certified + integrated
-> LECTOR-002 Acta 161 benchmark scaffold prepared; independent gold truth pending
-> explicit canonical-cutover gate later
```

Migration `0001` implementation was authorized by
`notebook/research/pre-sql/schema/MIGRATION_0001_AUTHORIZATION.md` only for the
fresh-database bootstrap/runtime boundary and is now certified by
`notebook/research/pre-sql/schema/MIGRATION_0001_IMPLEMENTATION_CERTIFICATION.md`.
WORKBENCH-001 required a prerelease `0001` rebaseline so exact ProcessRun scope,
typed quality evidence, quality decisions, and egress provenance survive restart.
The certified PROCESSOR-CODEX-001 SQL hash is:

```text
5226c873487d9bd05fc62b7a1f323d6e804b003cc4e08bd2fe2b531adb6057bb
```

The independently certified WORKBENCH/DIRECT/OCR baseline
`adf14a5006565197af3acf57c5cfc213510ba94217beb650403acbaf363b975a` and prior
`31cac5...` baseline remain historical evidence. The new candidate changes only the
`process_run_egress.bytes_egressed` lower bound from positive to non-negative so a
cloud-capable attempt that fails before external handoff can truthfully persist zero
source bytes plus policy provenance. The WORKBENCH rebaseline was independently certified
on the exact registered upstream SQLite 3.53.4 source
ID; the first attempt correctly rejected a patched build with a mismatched source
ID. No `0002` exists: prerelease policy requires rebaselining `0001` instead.

The earlier migration/processor implementation certifications did not themselves
authorize canonical cutover or semantic writers. The bounded Depósito writer is
certified by `notebook/research/pre-sql/schema/DEPOSIT_WRITER_CERTIFICATION.md`;
LECTOR-001 later and separately authorizes only the bounded semantic writer described
below.

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
It authorized the generic `actakit/processors` boundary, which is now independently
certified, and concrete backends now land as separate bounded adapter units. The closed research
selected this escalation philosophy:

```text
native/direct parse
-> Poppler/pdftotext
-> OCRmyPDF + Tesseract
-> Docling structured processing (optional, not default)
-> specialized visual/document AI (local or cloud by policy)
-> frontier multimodal AI (local or cloud by policy)
   - local candidate: Qwen3-VL family
   - subscription-backed cloud candidate: official Codex CLI + ChatGPT subscription
   - optional API candidate: OpenAI multimodal API, after separate policy/capability checks
   - specialist cloud candidate: Mistral OCR
-> human review
```

Processors are intended to be a curated built-in ActaKit capability. Backend
replaceability is an escape hatch for hardware, licensing, new/hard formats,
execution-venue policy and benchmarking; WP4C is not a plugin-marketplace project.
Cloud frontier capacity is optional but first-class: a weak host may escalate to
bounded Codex escalation instead of attempting a heavyweight local VLM, while
no-egress deployments remain fully local.

No universal numeric processor confidence is accepted. WORKBENCH-001 now stores
typed, processor-attributable `QualityEvidence` plus a separate durable policy
decision (`ACCEPT | ESCALATE | QUARANTINE_REVIEW`) for each exact input target.
Every material transformation remains a derived Representation with ProcessRun
provenance; original custody is immutable.

**Current gate:** WORKBENCH-001, `PROCESSOR-DIRECT-001`,
`PROCESSOR-OCR-001`, and `PROCESSOR-CODEX-001` are independently certified. CODEX-001
accepts exactly one explicit `pdf_page:v1`, renders that page
locally, removes the source PDF before external handoff, and invokes the official Codex
CLI through a dedicated keyring-backed profile and private scratch HOME. Whole/multi-
page cloud scope, restricted material, missing egress authorization, or mismatched
endpoint/prompt/config identity are rejected before Codex invocation. Schema-valid
zero-uncertainty material may be accepted; uncertainty, empty material or failed/schema-
invalid output ends in human review. No API-key/provider-API path is part of this unit. The closure bench retains exact natural Esparza, FECOMUDI, Quepos
and spreadsheet artifacts, corrected page-level D2 evidence with process-tree RSS,
independent truth for two natural hard pages, and controlled plus diagnostic
official Codex CLI runs. Docling is optional rather than default because its
disposable footprint was material and no quality advantage was measured. Exact
pins/licenses for future optional backends, broader natural thresholds, handwriting
and multi-column coverage remain follow-up work. Personal Plus/Pro Codex use is
limited to approved public material; Business/Enterprise/Edu controls must be
verified per deployment. Credential values remain external host secrets and must
never enter SQLite, ProcessRun evidence or logs.

## LECTOR-001 current boundary

The integration merge `98c2d60387fd7ec176033563566f62c59123587d` adopts the
independently certified LECTOR-001 boundary. `SemanticExtractor` backends remain
untrusted/replaceable; `LectorWriter` owns bounded canonical persistence and exact
selector reopening. Stable ProcessRun replay is idempotent without claim-text
deduplication, a 300-Claim machine-only volume proof is part of the focused suite,
and LECTOR-001 writes no synthetic human review. The certified SQL baseline remains
unchanged at `5226c873487d9bd05fc62b7a1f323d6e804b003cc4e08bd2fe2b531adb6057bb`;
no `0002` exists.

The active semantic edge is LECTOR-002: the deterministic Acta 161 worksheet/scorer is
prepared; freeze the independent gold truth before measuring a real broad extractor. Production
review policy remains separate: machine-only is a valid searchable state, not a
mandatory review queue.

## Current Prohibitions

- No canonical-data cutover or historical mass import is authorized yet.
- No legacy Markdown/Hilo rewrite is authorized by migration `0001`.
- LECTOR-001 is the only authorized semantic Claim writer. Its authority is bounded to
  new evidence-backed Claim revision 1 plus the exact LECTOR-001 links/provenance described
  in `notebook/implementation/LECTOR_001_DESIGN.md`; it cannot write human review, resolve
  canonical Entity identity, revise/retract historical Claims, publish outputs, or perform
  canonical cutover. Civic-review, purge, archive/GC, and broader semantic writers remain
  unauthorized.
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
