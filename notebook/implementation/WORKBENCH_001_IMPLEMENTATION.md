# WORKBENCH-001 — Generic Processor Boundary Implementation

**Start HEAD:** `497b09b3f922676d7c1fd19ab102f3d905a48dd6`
**Implementation state:** `WORKBENCH_001_IMPLEMENTED__CERTIFICATION_PENDING`

## What landed

Production code now lives in `actakit/processors/`:

```text
contracts.py   backend-neutral processor/request/result/scope DTOs
quality.py     registered typed QualityEvidence + policy decisions
registry.py    explicit curated processor composition
host.py        bounded Workbench orchestration/escalation
writer.py      canonical ProcessRun/evidence/decision/derivative writer
targets.py     registered RepresentationTarget selector validation
```

No concrete Poppler, OCRmyPDF/Tesseract, Codex, Docling, provider-API or local-VLM
adapter is included in this unit.

## Frozen generic contracts

### Processor

A `ProcessorDescriptor` declares:

- semantic capability key;
- trusted implementation/version;
- execution venue independently from capability;
- supported input media, output Representation kinds and selector scope kinds;
- bounded input/scope limits;
- whether source material must egress;
- optional model provider/name provenance.

A Processor receives only immutable retained bytes and validated target snapshots.
It receives no SQLite connection, archive path, credential or shell/network
command from document-controlled data.

### Scope

`ProcessingRequest` is grounded in one retained Representation plus an ordered
non-empty tuple of existing RepresentationTarget IDs. Whole-document scope is
explicit `whole:v1`. The Workbench validates target ownership and availability
before invocation and revalidates it under the write transaction.

### Result

`ProcessorResult` separates:

```text
outcome          success | partial | failed
material outputs zero or more derivative byte payloads
QualityEvidence  typed/namespaced signals on exact targets
error_code       bounded terminal failure identity
diagnostics      bounded non-canonical diagnostic codes
egress_bytes     actual bytes sent only for egress processors
```

Failed results cannot emit canonical derivatives; successful results cannot carry
an error code. Every derivative from a run inherits that run's full ordered input
scope; an adapter needing narrower output provenance must split the work into
separate bounded runs rather than invent per-output metadata edges.

### Quality

`QualityRegistry` validates `signal_key + signal_version` against explicit bounded
contracts before policy evaluation or persistence. Initial contracts cover the
signals required to prove native/OCR/visual escalation; new adapters compose new
registered contracts rather than writing arbitrary metadata.

`ReferenceEscalationPolicy` uses runtime-observable signals only. It contains no
CER/WER truth metrics and no universal confidence threshold.

### Egress

`EgressAuthorization` is non-secret policy context. A descriptor declaring egress
is ineligible unless egress is explicitly allowed and the retained Artifact is
not restricted. Credentials are not representable in Workbench DTOs/schema.

### Replay

`ProcessingRequest.process_run_id` is the stable canonical retry identity. The
host verifies retained input custody, then checks for an existing immutable-matching run before resolving or invoking a processor.
A matching retry returns persisted outputs/decisions and does not invoke the
processor again; changed input scope/configuration under the same ID is a hard
collision. A newly allocated ProcessRun ID is a distinct attempt.

## Canonical writer

`WorkbenchWriter` is deliberately separate from `DepositWriter`.

It owns only:

- registered RepresentationTarget creation;
- terminal ProcessRun provenance;
- exact ordered ProcessRun input scopes;
- non-secret egress provenance;
- typed QualityEvidence;
- durable quality decisions;
- material derivative ArchiveObjects/Representations.

Derivative bytes are content-addressed through the existing `EvidenceArchive`.
New orphan files are compensated after a failed transaction when unreferenced;
existing shared objects are never removed. A derivative always keeps the same
Artifact and exact parent Representation. Restricted custody propagates to the
derivative rather than being laundered to `available`. WORKBENCH-001 has no
declassification authority; the already-accepted public-redaction path remains a
separate explicit reviewed correction/release operation.

## Rebaseline

WORKBENCH-001 rebaselines prerelease `0001`; see
`WORKBENCH_001_SCHEMA_REBASELINE.md`.

```text
old SHA256: 31cac5ccc3440ce555242ba288317df527bb30949b2142026d8ceb2805d3adfc
new SHA256: adf14a5006565197af3acf57c5cfc213510ba94217beb650403acbaf363b975a
STRICT tables: 54 -> 58
explicit indexes: 114 -> 118
FK child paths in freeze proof: 118 -> 127
```

No `0002` was created.

## Implemented proof cases

`tests/test_workbench.py` proves:

- invalid descriptor/signal/selector rejection;
- success + derivative + exact scope + evidence + quality decision;
- replay skips processor invocation;
- failed page-scoped run survives without fake output;
- native -> OCR -> subscription-agent escalation;
- cloud egress provenance without credentials;
- restricted source prevents cloud invocation and ends in review;
- Workbench processing cannot declassify restricted custody; public redaction/release remains a separate reviewed operation;
- cross-Representation target rejection before invocation;
- same stable ProcessRun ID with changed immutable configuration fails;
- distinct attempts retain distinct logical provenance while derivative bytes
  physically deduplicate;
- forced transaction failure rolls back canonical rows and removes a newly
  materialized unreferenced archive object;
- purged targets cannot be processed.

All 51 pre-existing tests continue to pass unchanged; the full implementation suite is currently 66 tests (15 Workbench-focused tests).

## Certification boundary

This implementation environment has SQLite 3.46.1. Portable migration, freeze,
storage, unit and compilation proofs pass, but the project runtime contract
correctly rejects this SQLite version because canonical certification requires the
registered SQLite 3.53.4 source ID.

Therefore this implementation does **not** self-certify WORKBENCH-001. The local
certification agent must run the exact target-runtime proof and repeat the full
suite before changing state to `IMPLEMENTED_AND_CERTIFIED`.

No concrete backend adapter is authorized before that certification.
