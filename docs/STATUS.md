---
id: ACTAKIT-STATUS-001
kind: status
state: CLAIM_REVISION_CONTROL_CANDIDATE
created: 2026-08-19
updated: 2026-08-26
authority: operating
release_phase: prerelease
schema_compatibility_boundary: not-established
summary: The reasoning stack is certified through e5a0485 and REVIEW-001 claim supervision is certified/merged at 971b9bbf. The active REVIEW-002 candidate adds append-only human ClaimRevision correction/restriction control with explicit actor/action lineage, atomic human acceptance of corrections, safe active-evidence custody, FTS privacy behavior and a narrow prerelease 0001 rebaseline. Exact SQLite 3.53.4 plus natural Esparza correction proof remain pending.
related:
  - ACTAKIT-ARCH-001
  - ACTAKIT-ROADMAP-001
  - ACTAKIT-INGRESS-001
  - ACTAKIT-CONNECTOR-ESPARZA-001
  - ACTAKIT-REPRESENTATION-PROCESSOR-RESEARCH-001
---

# Current Status

## Pre-release compatibility policy

Canario is **pre-release**. There is currently no public/beta compatibility
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

The repository now contains the certified generic durable core (`canario/`) alongside
the preserved file/Markdown municipal-acta/Hilo workflow. The latter remains real operator
history and regression material but is explicitly legacy/source-specific; it is not the
architectural template for new Canario capabilities. Existing operator data and curated
Hilos are preserved; no mass regeneration or migration is authorized by the architecture
proposal.

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

Canario remains a self-contained civic-record system using:

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
-> SOTA research checkpoint 7e7fd85: fact verification and structured reasoning audit complete
-> architecture reconciliation: Lector/extraction, Derivation, Verification, Assessment separated
-> STRUCTURED-REASONING-FIT-BENCH certified at 0f9a71e; SQLite selected, DuckDB challenger retained, G3 FIRST_CLASS_DERIVATION_REQUIRED
-> STRUCTURED-VERIFIER-FIT-BENCH Phase D locally certified and merged at 310d060c; minimum Canario decomposition selected
-> DERIVATION-VERIFICATION reconciliation merged at 0130762a; SINGLE_EXECUTION_GRAPH__SOURCE_EVIDENCE_NOT_EXECUTION_LINEAGE
-> prerelease 0001 Derivation/Verification rebaseline certified and merged at 0e0f56a0
-> bounded canario.reasoning Derivation/Verification runtime certified and merged at b8535195
-> first production structured SQLite Derivation/Verification consumer certified and merged at 51f21f98
-> minimum structured planner/final-verifier orchestration certified and merged at e5a0485
-> REVIEW-001 claim review workflow core certified and merged at 971b9bbf
-> REVIEW-002 human ClaimRevision control implemented as candidate; exact SQLite + natural Esparza correction proof pending
-> LECTOR-002 semantic campaign superseded/re-scope pending; no replacement gold generated
-> explicit canonical-cutover gate later
```

Migration `0001` implementation was authorized by
`notebook/research/pre-sql/schema/MIGRATION_0001_AUTHORIZATION.md` only for the
fresh-database bootstrap/runtime boundary and is now certified by
`notebook/research/pre-sql/schema/MIGRATION_0001_IMPLEMENTATION_CERTIFICATION.md`.
WORKBENCH-001 required a prerelease `0001` rebaseline so exact ProcessRun scope,
typed quality evidence, quality decisions, and egress provenance survive restart.
The last merged/certified PROCESSOR-CODEX-001 SQL authority is:

```text
5226c873487d9bd05fc62b7a1f323d6e804b003cc4e08bd2fe2b531adb6057bb
```

The merged Derivation/Verification `0001` authority is byte-identical between spec and production
migration at:

```text
8d6f793e1c976221311bd73ffe03bdaa2907e9508e7c0f5fad59131a02dc9f96
```

Its certified inventory is 71 STRICT tables, 3 FTS tables, 135 explicit indexes and 152 FK child
paths with zero scans. It passed the exact registered SQLite 3.53.4 runtime, selector,
backup/restore/purge, full-suite and fresh-clone gates before merge at `0e0f56a0`.

REVIEW-002 currently carries a **candidate** prerelease `0001` rebaseline at
`55b05a11f129cfbe1ffd199bcb6774ef8096f46424ebca6f43c169cb3eef7356`: 72 STRICT tables,
3 FTS tables, 137 explicit indexes and 155 FK child paths with zero portable-proof scans. The only
new canonical family is narrow `claim_revision_actions`; `claim_revision_action` is also added to the
closed purge-target vocabulary. This candidate is not schema authority until exact SQLite 3.53.4,
storage/purge, natural correction and fresh-clone certification pass.

The generic `canario.reasoning` runtime is certified and merged at `b8535195`: typed
Derivation/Verification backend contracts, a core-owned host/writer, conservative selector
containment, explicit derived-Claim and Assessment writes, and host-owned bounded materialization.
The runtime refuses to expose a narrow source/result target as containing full bytes unless an exact
materializer is registered.

The first concrete consumer, `StructuredSQLiteDerivationBackend` plus
`StructuredScalarVerifierBackend`, is certified and merged at `51f21f98`. It runs untrusted SELECTs
only against a disposable in-memory projection of one exact `canario.structured_table.v1` target,
binds executor policy and exact program identity into verification, and requires Source Authority.
Its natural MTSS proof freezes the exact official workbook, production Representation identity,
historical 147x15 structural controls, source-backed `COUNT(*) = 147`, and the constant-query
counterfactual that must abstain as `insufficient_evidence`.

The minimum Phase-D orchestration is now certified and merged at `e5a0485`. The qualified V4
campaign passed D1 supported, D2 supported, D3 contradicted, D8 insufficient_evidence and natural
MTSS supported, then repeated from a fresh bundle clone with the same 10 Codex invocations and
39,067 prompt bytes. SQL still executes only as ordinary local DerivationRuns and source evidence
remains separate from execution lineage.

REVIEW-001 is certified and merged at `971b9bbf`. `canario.review` now has deterministic current
machine-Claim queues, exact retained evidence reopening, strict/batch/supervised decisions,
strict-ready derivation, immutable replay/collision behavior and same-transaction stale guards without
synthetic approval or Claim lifecycle mutation.

The active edge is REVIEW-002 human ClaimRevision control. A prepared exact current snapshot may be
mutated only by `correct | restrict | unrestrict | retract`; every successful action creates a new
human ClaimRevision and one narrow `claim_revision_actions` row binding source/result revisions,
actor, rationale, the exact correction ReviewAction when applicable, and canonical request SHA-256.
A `correct` action atomically creates a fresh accepted ClaimReview for the exact result revision; it
does not inherit a predecessor review or require a redundant second operator action. Any new active
revision revalidates that all carried evidence custody remains available; restriction/retraction
removes all revisions of that Claim from derived FTS before optional current-active reindexing. Existing
ClaimRelations remain attached to their historical exact endpoints. The candidate rebaselines prerelease
`0001` from the merged 8d6f... authority to `55b05a11...`; exact SQLite 3.53.4 and natural Esparza
correction/fresh-clone proof are required before it becomes authority. No `0002` exists.

The independently certified WORKBENCH/DIRECT/OCR baseline
`adf14a5006565197af3acf57c5cfc213510ba94217beb650403acbaf363b975a` and prior
`31cac5...` baseline remain historical evidence. The historical WORKBENCH/Codex integration
rebaseline changed `process_run_egress.bytes_egressed` from a positive to a non-negative lower
bound so an externally capable attempt that fails before handoff can truthfully persist zero source
bytes plus policy provenance. That change is already part of the frozen current `0001`; REVIEW-001
introduces no schema delta. The exact registered upstream SQLite 3.53.4 source ID remains the runtime
authority, and no `0002` exists under the prerelease rebaseline policy.

The earlier migration/processor implementation certifications did not themselves
authorize canonical cutover or semantic writers. The bounded Depósito writer is
certified by `notebook/research/pre-sql/schema/DEPOSIT_WRITER_CERTIFICATION.md`;
LECTOR-001 later and separately authorizes only the bounded semantic writer described
below.

## INGRESS-001 current boundary

`docs/INGRESS.md` is accepted. The implementation lives in `canario/ingress/` and
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
It authorized the generic `canario/processors` boundary, which is now independently
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

Processors are intended to be a curated built-in Canario capability. Backend
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
and LECTOR-001 writes no synthetic human review. The current certified SQL authority is the
Derivation/Verification rebaseline at
`8d6f793e1c976221311bd73ffe03bdaa2907e9508e7c0f5fad59131a02dc9f96`; no `0002` exists.

The deterministic structured-reasoning foundation is certified at
`0f9a71e5acb0f093469571d59c896eab0c03c4c2`. SQLite remains the analytical baseline; DuckDB
remains a certifiable non-product challenger; G3 concluded `FIRST_CLASS_DERIVATION_REQUIRED`.
`STRUCTURED-VERIFIER-FIT-BENCH` Phase D completed one eight-case, zero-retry paired campaign on
the qualified subscription-backed Codex/Terra profile with no worker failures. The measured
design decision is `DECOMPOSITION_VALUE_PROVEN__DESIGN_MINIMUM_CANARIO_DECOMPOSITION`: explicit
Derivation execution/lineage must precede final Verification judgment, but Thucy's four-role
runtime is not selected. Phase-D closure and the subsequent Derivation/Verification reconciliation
are merged. The persistence rebaseline passed exact registered SQLite 3.53.4 certification and is
merged at `0e0f56a0`. The bounded runtime/API over those records is certified and merged at `b8535195`, and its first
structured SQLite consumer is certified and merged at `51f21f98`. The active gate is the minimum
planner/final-verifier orchestration over that production path, with exact Codex/SQLite identity,
Phase-D contract replay and the natural MTSS proposition. V2 failed opaquely on D1; V3 exposed the
durable cause boundary and showed planner + SQL Derivation succeeded while the Codex finalizer exited
non-zero as `codex_final_failed`. The final wire schema alone carried `uniqueItems`, which the official
Structured Outputs supported-array subset does not include. V4 removes that redundant wire constraint,
retains duplicate-citation rejection in `StructuredFinalDecision`, and classifies future
`invalid_json_schema` stderr without retaining raw stderr. Prompts, verdict rules and evidence rules are
unchanged.
Metered provider transports remain allowed future profiles. The prior LECTOR-002 semantic campaign
remains superseded.

Research basis: `notebook/research/lector/fact-verification/synthesis/BOOK.md`, checkpoint
`7e7fd85be5ac607fcb02ccb68b97b5e17f8fd9d6`.

The product vocabulary remains Inbox -> Depósito -> Mesa de trabajo -> Lector -> Fichero
-> Mesa de control -> Consultas -> Salidas. Derived analysis and Verification are semantic
operation boundaries around the Fichero/Mesa de trabajo, not new mandatory human stages.

Lector answers what a source asserts or explicitly contains. A new sum, comparison or join
belongs to Derived analysis, not a source assertion. The accepted reconciliation now freezes a
distinct DerivationRun -> DerivationResult -> DerivationResultTarget execution path with explicit
source-contribution lineage, and a separate VerificationRun with bounded scope, Source Authority,
Derivation attempts/consumption, evidence, sufficiency and abstention/execution outcome. Derived
Claims point to exact result targets; EvidenceLink remains source evidence. Assessment remains
optional, attributable and separate from review/lifecycle. Production `0001` now persists these
records at the certified schema merge `0e0f56a0`; `canario.reasoning` is certified and merged at
`b8535195`, and the first structured SQLite execution/verification consumer is merged at `51f21f98`.
Acta 161 carries the descriptive benchmark archetype `institutional_minutes` and currently
covers only a subset of declared text/semantic stress capabilities. Real structured-table and timed-media fixtures are frozen externally. Their typed evidence
substrate is now canonical at `e0ab1cd831740241736086f5db568468aacac779`: deterministic
XLSX/table Representation, deterministic ffprobe media index, production locator reopening,
same-Artifact lineage protection and typed benchmark scoring passed exact registered SQLite
3.53.4 certification plus fresh/post-push clone proof. LECTOR-002 now distinguishes
deterministically verifiable Representation/evidence capabilities from semantic capabilities
that require a frozen semantic reference plus adjudication.
The superseded campaign has frozen, extractor-blind scopes for semantic reference: 61
full-source minutes units, a 24-row deterministic structural table sample, and 17 full-source
official-correspondence units. The 24-row structural semantic scope and BATCH-001 are
superseded/non-authoritative for semantic certification. Truth, candidate and assessment rows
remain empty; replacement semantic evaluation has not run. Reference construction,
adjudication, threshold policy and semantic verification remain separate. The historical
reference workflow is explicitly human+AI assisted: exact
evidence is exported before extractor exposure, assistant proposals require explicit human approval,
and assistance provenance is frozen alongside the reference. The campaign remains blocked on the
completed frozen reference, adjudication, and accepted semantic scoring thresholds.
`certification_scope` remains explicitly `declared_capabilities_only` for the historical
campaign;
`universal_support_claimed` is false. Production review policy remains separate: machine-only
is a valid searchable state, not a mandatory review queue.

## Known modality gaps — do not paper over them

The contracts/schema are broader than the adapters currently implemented. In particular:

- Ingress/custody can preserve arbitrary recording bytes, but Canario does **not** yet ship
  an audio/video transcription processor;
- the canonical evidence model now has production reopening for bounded `media:v1` time
  spans, but no transcription processor is authorized and no real transcript exists;
- the current Codex visual adapter is bounded to one PDF page, not a universal image/video
  semantic processor;
- structured table evidence has a deterministic typed Representation plus typed worksheet/
  scorer using production locator semantics; gold/adjudication remain pending;
- a transcript is a derivative Representation and may not replace the original recording's
  custody or timed evidence semantics.

These are explicit implementation gaps. An agent must not claim broad multimodal support by
flattening unsupported media into text or by extrapolating from the minutes/PDF fixtures.

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
- Derived analysis and Verification are authorized only through the certified bounded
  `canario.reasoning` runtime and structured SQLite consumer. Executors may not access the canonical
  SQLite DB, arbitrary filesystem/network, extensions, semantic writers or secrets. The active
  planner/final-verifier candidate adds only the qualified bounded Codex subscription profile and
  remains unauthorized until its exact certification gate passes.
- No individual political-preference profiling or targeted-persuasion use.

## Planning Documents

`ROADMAP.md`, `IMPLEMENTATION_PLAN.md`, and `RELEASE_1_0.md` remain planning
artifacts. Their future work packages do not expand this authorization. The
current authority for migration `0001` is the accepted semantic contract, the
certified freeze, and the bounded authorization record.

- Historical LECTOR-002 reference packets treat uncertainty as explicit `needs_adjudication`;
  unresolved units block reference freeze/scoring. The superseded table scope and BATCH-001
  are not semantic certification authority. Any future campaign must use the reconciled
  capability decomposition and must not be described as independent human gold when using
  human-approved AI assistance.
