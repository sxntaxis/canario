# WORKBENCH-001 — Generic Representation Processor / Workbench Design

**Input authority:** `497b09b3f922676d7c1fd19ab102f3d905a48dd6`  
**State:** implementation design authorized by the closed Civic Processor Bench.

## Purpose

WORKBENCH-001 freezes the generic boundary between retained Representations and
curated processors. It does not select a universal backend and does not extract
civic Claims. Its contract is:

```text
retained Representation + exact RepresentationTarget scope
  -> curated Processor capability
  -> one terminal ProcessRun
  -> typed/namespaced QualityEvidence
  -> ACCEPT | ESCALATE | QUARANTINE_REVIEW
  -> zero or more material derivative Representations
```

The reference policy proven by the bench is D0/D1 direct extraction -> D2 local
OCR -> bounded subscription-backed Codex -> human review. Those rung names are
policy vocabulary, not core API types.

## Resolved decisions

### 1. Schema rebaseline is required

The pre-WORKBENCH `0001` has `process_runs`, `representations`, and
`representation_targets`, but cannot durably express the exact input scope of a
failed run, typed quality signals, a quality decision independent from execution
outcome, or bounded egress provenance. ActaKit is pre-release, so `0001` is
rebaselined rather than adding `0002`.

New/changed durable structures:

- `process_runs.execution_venue` and bounded terminal `error_code`;
- `process_run_inputs`: ordered exact RepresentationTarget inputs for every run;
- `process_run_egress`: non-secret bytes/policy/template/endpoint provenance for
  executions that egress source material;
- `quality_evidence`: ordered typed/namespaced signal payloads attributed to an
  exact ProcessRun + RepresentationTarget;
- `quality_decisions`: terminal policy decision for an exact ProcessRun target,
  with policy key/version, reason code, and optional next capability.

`ProcessRun.outcome` remains `success | partial | failed`; it is never overloaded
with quality acceptance.

### 2. Scope is explicit and target-backed

Processors never receive an arbitrary filesystem path or an unvalidated JSON
selector. A request names one retained Representation and one or more existing,
available `RepresentationTarget` rows. Whole-document processing uses an
explicit `whole:v1` target. Ordered multi-target requests are persisted in
`process_run_inputs.ordinal`.

Failed runs therefore retain exact scope even when they produce no derivative.

### 3. Processor capability and venue are orthogonal

A `ProcessorDescriptor` carries a registered semantic `capability_key`, trusted
implementation identity/version, supported input media/output kinds/scope kinds,
execution venue, and whether source bytes must egress. Provider/model identity is
optional provenance, not a processor type.

Examples expressible without changing the core:

```text
text_extract     + local_deterministic + poppler
ocr              + local_deterministic + ocrmypdf/tesseract
visual_transcribe+ subscription_agent  + codex-cli + model identity
visual_transcribe+ provider_api        + future provider adapter
```

### 4. Processors cannot write canonical state

A Processor receives immutable source bytes plus validated target snapshots and
returns a bounded `ProcessorResult`. It has no database/archive handle. The
core-owned `WorkbenchWriter` is the only Workbench writer of ProcessRun input,
quality evidence/decision provenance, derived archive bytes, and derived
Representations.

### 5. QualityEvidence is registered and namespaced

Durable evidence is keyed by `signal_key + signal_version`; the core registry
validates each payload before persistence. JSON is only a storage encoding of a
registered bounded payload, never an arbitrary metadata bag. Initial contracts
cover the generic/native/OCR/multimodal signals needed by the reference ladder.
Future adapters compose additional contracts explicitly.

There is no universal confidence value.

### 6. Policy is separate from execution

A `QualityPolicy` evaluates one terminal processor result and its validated
signals for an exact scope. It returns one of:

```text
ACCEPT
ESCALATE
QUARANTINE_REVIEW
```

plus policy identity/version, bounded reason code, and optional next capability.
The decision is durably stored separately from `ProcessRun.outcome`.

### 7. Egress and credentials

A processor that declares `requires_egress=True` cannot be invoked unless the
host receives explicit egress authorization and the source Artifact is not
`restricted`. Non-secret egress facts may be persisted; credentials never enter
ProcessorRequest, ProcessRun, QualityEvidence, logs, or SQLite.

The later Codex adapter will delegate ChatGPT authentication entirely to the
official Codex CLI. WORKBENCH-001 contains no Codex credential handling.

### 8. Replay and identity

`ProcessingRequest.process_run_id` is the stable canonical retry token. If that
run already exists, the host verifies immutable descriptor/input provenance and
returns the persisted receipt without invoking the processor again. Reusing the
same ID with different immutable input or descriptor data fails loudly.

A newly allocated ProcessRun ID is a genuinely distinct attempt even when input
bytes/configuration are identical. Physical derivative bytes may deduplicate by
SHA-256 while logical Representation provenance remains distinct.

### 9. Partial/failure semantics

- `success`: may emit zero or more derivatives;
- `partial`: may emit explicitly marked useful derivatives and diagnostics;
- `failed`: cannot emit canonical derivatives;
- every attempted run persists exact input scope;
- expected processor failures are bounded terminal outcomes, not swallowed
  exceptions;
- programmer/integrity errors still raise and do not manufacture provenance.

### 10. Writer atomicity

Derivative bytes are materialized content-addressably before the SQLite write,
then canonical rows are committed under `BEGIN IMMEDIATE`. On rollback, newly
created unreferenced archive objects are removed best-effort. Existing shared
archive objects are never removed. Original Representations are immutable and a
derivative must retain the same Artifact and exact parent Representation.

### 11. Reference orchestration proof

WORKBENCH-001 proves the generic ladder with fixture processors, not fake shipping
backends:

```text
native-like -> ESCALATE
ocr-like -> ESCALATE
subscription-agent-like -> ACCEPT
```

A restricted/no-egress scenario proves the cloud fixture is never invoked and
ends in `QUARANTINE_REVIEW`. Human review is a terminal policy state, not a fake
Processor.

## Non-goals

- plugin marketplace or dynamic entry points;
- production Poppler/OCRmyPDF/Tesseract/Codex adapters;
- scheduler/job lifecycle in `process_runs`;
- universal confidence or benchmark CER/WER thresholds in production;
- civic Claim extraction;
- provider-specific request knobs in generic DTOs.
