# Derivation / Verification runtime candidate

State: **IMPLEMENTED CANDIDATE — EXACT RUNTIME CERTIFICATION PENDING**

Authority chain:

```text
G3:                                      FIRST_CLASS_DERIVATION_REQUIRED
Phase D:                                 DECOMPOSITION_VALUE_PROVEN__DESIGN_MINIMUM_CANARIO_DECOMPOSITION
reconciliation merge:                    0130762a82b9b5e93a2ebd5231cfcf0e475ecd6d
reconciliation decision:                 SINGLE_EXECUTION_GRAPH__SOURCE_EVIDENCE_NOT_EXECUTION_LINEAGE
schema rebaseline merge:                 0e0f56a0c038deebbf55f69e96cbe5f1cc463704
frozen 0001 SHA256:                      8d6f793e1c976221311bd73ffe03bdaa2907e9508e7c0f5fad59131a02dc9f96
runtime topic branch:                    implementation/derivation-verification-runtime
```

## Purpose

This unit implements the smallest production runtime/API that can write and reopen the already
frozen Derivation/Verification persistence graph without weakening its semantic boundaries.
It does **not** redesign `0001`, select a model/provider, copy the Phase-D challenger topology, or
make analytical/verification work a mandatory human stage.

The runtime shape is:

```text
trusted Canario host
  -> replaceable DerivationBackend / VerificationBackend
       (no SQLite/archive write authority)
  -> ReasoningWriter
       (canonical reads, revalidation, transaction, persistence)
```

The writer owns the cross-row invariants SQLite deliberately cannot encode. A backend receives only
bounded immutable input material plus typed metadata and returns typed proposals/results. It never
receives a canonical database connection, archive root, or core writer.

## Files

The bounded runtime lives in `canario/reasoning/`:

```text
contracts.py      backend-neutral DTOs and Protocols
registries.py     result selectors, source materializers, verification profiles
containment.py    conservative RepresentationTarget containment
writer.py         canonical persistence and cross-row validation
host.py           backend invocation without persistence authority
__init__.py       public runtime surface
```

Focused regression coverage is in `tests/test_reasoning_runtime.py`.

## 1. No generic OperationRun

`ProcessRun`, `DerivationRun`, and `VerificationRun` remain separate typed execution families.
The runtime may share implementation patterns, but it does not add a generic operation graph or a
polymorphic execution writer.

- `ProcessRun` remains owned by existing Workbench/Lector boundaries.
- `DerivationRun` records one exact analytical attempt.
- `VerificationRun` records one exact proposition evaluation over an explicit scope.

No schema file changes are part of this unit.

## 2. Derivation host and writer

`ReasoningHost.run_derivation()` performs this sequence:

```text
stable-run replay check
-> load exact ordered RepresentationTarget inputs
-> materialize only the bounded target material exposed to the backend
-> validate backend capability / limits / egress policy
-> invoke DerivationBackend
-> validate typed result
-> BEGIN IMMEDIATE
-> revalidate all canonical input state
-> persist run + ordered inputs + optional egress + result + targets + lineage
-> validate committed cardinality/lineage invariants
-> COMMIT
```

A successful run has exactly one `DerivationResult`; a failed run has no result. Re-executing the
same analytical operation uses a new run ID. Reusing an already persisted preallocated run ID is
accepted only when the immutable request/descriptor/ordered-input identity is identical.

Program text remains untrusted executable provenance. The runtime does not execute SQL itself and
therefore does not turn the certified benchmark executor into a hidden product dependency. A
production analytical executor lands as a bounded `DerivationBackend` and must enforce its own
sandbox/query limits.

### Result storage

Inline results use canonical JSON serialization (`sort_keys`, compact separators, UTF-8,
non-finite numbers rejected). JSON `null` is a valid typed scalar and is distinct from the absence
of an inline payload.

Larger/binary results may use `ArchiveObject`. Physical bytes are content-addressed and may be
reused by distinct DerivationResults, but run/result civic identity is never deduplicated by digest.
A failed transaction cleans up a newly materialized physical object only when no canonical
ArchiveObject references it.

### Per-target source contribution lineage

Each `DerivationResultTarget` carries one of:

```text
exact | partial | unavailable | none
```

`exact`/`partial` require real lineage rows. `unavailable`/`none` cannot fabricate lineage. Every
lineage target must be equal to or conservatively contained by the exact Derivation input target at
the declared input ordinal.

## 3. Bounded material is stricter than selector identity

A selector identifying a narrow scope is **not** permission to hand the full underlying
Representation to a backend.

The default `SourceMaterializerRegistry` therefore materializes only `whole:v1`. Narrower selectors
such as PDF pages, media spans, or table slices fail closed until the host registers a materializer
that can isolate that exact scope. A page-image Representation can naturally use `whole:v1` because
its retained bytes already are the bounded page.

This is intentional capability pressure:

> missing exact materialization is an implementation gap, not authority to widen evidence scope.

The same rule applies to derived results. `ResultTargetRegistry` validates result-target identity,
but a custom narrow result selector is not consumable by Verification until an exact result
materializer is also registered. The default `whole:v1` and `scalar:v1` selectors expose the full
result because the selected target is the full result by definition.

This prevents a future `table_row:v1` or `table_cell:v1` Verification from silently receiving the
entire analytical table merely because the first runtime knew how to load the containing result.

## 4. Verification host and writer

`ReasoningHost.run_verification()` exposes to a backend:

- exact proposition;
- ordered bounded source scopes and their materialized bytes;
- explicit SourceAuthorityScope snapshots;
- every named Derivation step with `attempted | consumed` state;
- outcome/error of attempted Derivations;
- exact bounded result-target material for consumed Derivations.

Before invocation, the writer requires:

- claim-bound proposition text equals the exact ClaimRevision text;
- scope payload is registered and canonical;
- Source Authority covers exactly the source identities represented in scope;
- every referenced Derivation input remains contained by Verification scope;
- `consumed` means a successful available DerivationResultTarget belonging to that exact run;
- restricted source scope cannot egress;
- backend scope/byte limits are satisfied.

A failed Derivation may remain visible as `attempted`; it has no consumed result. This preserves an
important failed analytical step without laundering failure into evidence.

### Verification result semantics

The runtime preserves the frozen separation:

```text
failed
  -> execution error
  -> no verdict / sufficiency / epistemic evidence

completed + supported|contradicted
  -> sufficient
  -> no abstention reason

completed + insufficient_evidence
  -> insufficient
  -> bounded abstention reason required
```

Verification evidence must itself be contained by an explicit source scope. It is stored as
Verification execution evidence and is never copied into Claim `EvidenceLink` automatically.

The default `explicit_targets:v1` scope profile deliberately claims target membership only. It does
not claim inventory completeness and therefore cannot by itself turn zero query rows into a durable
absence/non-existence proof. Richer negative-evidence semantics require a separately registered
scope/sufficiency profile.

## 5. Explicit derived-Claim promotion

`ReasoningWriter.promote_derived_claim()` is an explicit semantic write, not a side effect of a
successful Derivation.

It creates only `ClaimRevision(kind=derived_inference)` and requires the exact available
`DerivationResultTarget` origin. Active `supports` EvidenceLinks must contain actual
source-contribution lineage for that exact target. Independent `challenges` evidence may come from
outside the derivation lineage. Query/program/result objects themselves never become civic source
evidence.

If a Derivation input or promoted evidence is restricted, the derived Claim must remain
`restricted`; an active/public promotion is rejected.

Machine/rule EvidenceLinks retain the existing rule that they require attributable `ProcessRun`
provenance. The Reasoning runtime does not invent a second generic semantic-origin mechanism.

## 6. Assessment

`ReasoningWriter.record_assessment()` records the already frozen optional judgment without changing
Claim lifecycle or human review state.

Rules enforced in the runtime include:

- Verification basis, when present, must bind the same exact ClaimRevision;
- failed Verification cannot be Assessment basis;
- machine/rule Assessment requires both a VerificationRun and explicit policy key/version;
- supersession keeps the same ClaimRevision and assessor;
- a policy-backed lineage cannot jump to a different policy key;
- preallocated Assessment ID retry must match the complete immutable payload and creation timestamp.

Human Assessment may exist without a VerificationRun or policy because the human is the attributable
assessor, not an automated promotion rule.

## 7. Replay / identity

Stable preallocated IDs provide retry safety, not global semantic deduplication.

- Derivation/Verification replay compares immutable request, descriptor, egress and ordered graph
  identity before returning an existing receipt.
- Derived Claim retry compares Claim/Revision payload, exact EvidenceLink identities, and the exact
  preallocated creation timestamp.
- Assessment retry compares the complete judgment/basis/policy/supersession payload and timestamp.
- changing a program, scope, promotion payload, policy lineage, or preallocated timestamp under the
  same ID is an identity collision.

A genuinely new rerun uses a new opaque ID even when its program/inputs happen to be byte-identical.

## 8. Egress

Egress-capable backends require explicit authorization before invocation. Restricted material cannot
be sent to an egress backend. Terminal egress attempts record actual non-negative source bytes sent
plus non-secret policy/data-control/template/endpoint identity. A failure before handoff may
truthfully record zero bytes.

The backend never receives credentials from the writer. Provider/model identity is execution
provenance, not Source Authority or verification semantics.

## 9. Candidate regression evidence

Portable candidate result before independent target-runtime certification:

```text
reasoning focused:                22 passed
full suite:                       279 passed, 2 skipped, 2 subtests passed
compileall:                       PASS
git diff --check:                 PASS
migration/schema files changed:   NO
```

The focused suite includes:

- Derivation replay/collision and exact source lineage;
- out-of-scope lineage rejection;
- egress rejection before backend invocation;
- physical ArchiveObject reuse without run/result identity collapse;
- valid inline JSON `null`;
- exact registered source materializer use for a narrow PDF-page test scope;
- default fail-closed behavior when a narrow source selector has no materializer;
- custom narrow result selector cannot be consumed without a result materializer;
- Verification receives Source Authority + bounded consumed-result material;
- failed Derivation retained as an `attempted` Verification step;
- failed Verification vs completed `insufficient_evidence` separation;
- out-of-scope Verification evidence rejection;
- explicit derived Claim promotion and lineage-backed `supports` evidence;
- restricted-basis Claim protection;
- Assessment same-Claim/policy supersession rules;
- exact creation timestamp as retry identity;
- non-canonical verification profile payload rejected before backend invocation.

## 10. Certification gate

This candidate is not authoritative until an independent local pass verifies the exact overlay and
runs the focused/full suite on the registered SQLite 3.53.4 source ID, followed by fresh-clone
validation. That pass must also prove:

- `canario/persistence/migrations/0001.sql` is unchanged at the certified SHA256;
- `MIGRATION_0001_SPEC.sql` is unchanged;
- no `0002+` exists;
- existing Workbench and Lector focused suites remain green;
- no production provider/model or Thucy dependency was introduced.

A successful certification may publish one commit on
`implementation/derivation-verification-runtime`. Schema redesign is not part of that closure.
