# Derivation / Verification prerelease `0001` rebaseline

State: **IMPLEMENTED CANDIDATE — EXACT SQLITE 3.53.4 CERTIFICATION GATE REQUIRED BEFORE MERGE**

Authority chain:

```text
Phase-D merge:          310d060cc1ced3640892a0dc29a7fbcb2c010920
reconciliation merge:   0130762a82b9b5e93a2ebd5231cfcf0e475ecd6d
design decision:        SINGLE_EXECUTION_GRAPH__SOURCE_EVIDENCE_NOT_EXECUTION_LINEAGE
schema compatibility:   prerelease / rebaseline 0001, no 0002
```

This unit implements only the persistence delta already accepted by
`DERIVATION_VERIFICATION_RECONCILIATION.md`. It does not add a production Derivation or Verification
writer, model runtime, multi-agent topology, automatic Claim/EvidenceLink/Assessment promotion, or
recursive analytical graph.

## Candidate identity

The candidate keeps the notebook specification and production migration byte-identical:

```text
notebook/research/pre-sql/schema/MIGRATION_0001_SPEC.sql
canario/persistence/migrations/0001.sql
SHA256 8d6f793e1c976221311bd73ffe03bdaa2907e9508e7c0f5fad59131a02dc9f96
```

Physical inventory:

```text
ordinary STRICT tables: 71
FTS5 virtual tables:     3
application triggers:    0
explicit indexes:        135
FK child paths checked:  152
FK child table scans:    0
SQLite JSON dependency:  absent
user_version:             1
forward migration 0002:  absent
```

`canario/persistence/database.py` is changed only as required to recognize this exact frozen SQL
hash and the 71-table schema-v1 inventory. Existing open/bootstrap identity, WAL, FK, FULL,
trusted-schema, secure-delete and runtime-registry boundaries remain unchanged.

## New durable families

The rebaseline adds the thirteen accepted typed families:

```text
derivation_runs
derivation_run_egress
derivation_run_inputs
derivation_results
derivation_result_targets
derivation_result_lineage
verification_runs
verification_run_egress
verification_scope_targets
verification_authority_scopes
verification_derivation_steps
verification_evidence_items
assessments
```

`claim_revisions` gains nullable `derivation_result_target_id`, required exactly for
`claim_kind=derived_inference` and forbidden for every other Claim kind.

The purge closed vocabulary adds only the seven new content-bearing roots:

```text
derivation_run
derivation_run_egress
derivation_result
derivation_result_target
verification_run
verification_run_egress
assessment
```

Payload-free scope/ordinal/FK joins are operation closure and are expanded by core purge logic rather
than exposed as generic purge targets.

## SQL-enforced invariants

The relational shape directly prevents, among other errors:

- a result belonging to a failed DerivationRun;
- a result target claiming a different run/result owner;
- lineage rows on `none` or `unavailable` result targets;
- lineage whose declared Representation does not match the exact Derivation input owner;
- a consumed Verification step naming a result target from another DerivationRun;
- an attempted Verification step pretending to consume a result;
- a source/non-derived Claim carrying analytical origin;
- a derived Claim omitting analytical origin;
- a failed VerificationRun carrying an epistemic verdict/sufficiency result;
- completed `insufficient_evidence` without explicit insufficiency + abstention reason;
- machine/rule Assessment without exact same-Claim VerificationRun + policy;
- Assessment supersession across ClaimRevision or assessor identity.

No trigger is introduced. Cross-row semantics that require selector containment, source authority,
or cardinality over multiple rows remain explicit core transaction validation rather than hidden SQL
behavior.

## Core-validation proofs

The migration-spec proof exercises the reconciliation's non-local invariants:

1. successful DerivationRun has exactly one result; failed run has none;
2. result/target ownership cannot cross runs;
3. source-contribution lineage stays inside the exact ordered Derivation input scope;
4. `none`/`unavailable` cannot fabricate lineage;
5. a derived Claim cannot depend on an unavailable/unrelated result target;
6. non-derived Claims cannot use analytical origin;
7. consumed Verification target belongs to the stated successful Derivation;
8. Derivation inputs and Verification evidence cannot silently expand Verification scope;
9. execution failure remains distinct from epistemic abstention;
10. Assessment basis/policy/supersession rules are enforced;
11. Claim review can coexist with a contrary Assessment because review is not truth judgment;
12. derived Claim `supports` evidence must selector-contain source-contribution lineage while
    independent `challenges` remains legal;
13. re-execution receives a new run identity while persistence retry can recognize the same
    preallocated immutable identity;
14. purge expansion covers new content-bearing records and shared ArchiveObject ownership;
15. backup/restore/FK/FTS/WAL/runtime requirements remain part of certification.

The proof intentionally demonstrates both FK/CHECK failures and core-detected invalid states under
savepoints. A query/program/result is execution provenance/output and never becomes source evidence
merely by existing.

## Shared ArchiveObject and purge proof

The storage proof now creates one sensitive ArchiveObject simultaneously referenced by:

```text
captured Artifact
+
DerivationResult
```

Trying to purge those physical bytes while either logical owner remains available is detected as an
invalid authority state. Full purge expands through Assessment -> Verification -> derived Claim ->
Derivation -> source evidence in FK-safe order, removes current FTS material, truncates WAL,
VACUUMs free pages, and verifies the sentinel is absent from the current DB/WAL/archive.

A pre-purge backup deliberately remains out of current-authority purge scope and is reported as
retaining the pre-purge material. Clean-machine restore includes ArchiveObjects retained solely by
DerivationResult as well as ordinary Artifact/Representation owners.

## Portable candidate proof

The authoring environment's Python SQLite is `3.46.1`, which is **not** an authorized Canario
runtime. It is used only to catch portable relational/proof regressions. On that environment:

```text
MIGRATION_0001_SPEC_PROOF: PASS
MIGRATION_FREEZE_PROOF:    PASS
STORAGE_OPERATION_PROOF:   PASS
full pytest suite:         257 passed, 2 skipped, 2 subtests passed
```

This does not replace the registered-runtime gate.

## Certification gate

Before this rebaseline can become current authority, the local certification pass must use the exact
registered upstream SQLite `3.53.4` source ID and repeat at minimum:

```text
prove_runtime_contract.py
prove_migration_0001_spec.py
prove_migration_freeze.py
prove_storage_operations.py
focused persistence/schema tests
full pytest suite
compileall
git diff --check
fresh-clone repeat
```

It must additionally confirm spec/production byte identity, the exact SHA above, the 71/3/135/152
inventory, zero FK child scans, no application triggers, no SQL JSON dependency, no `0002`, and no
unexpected production surface beyond the bounded schema/bootstrap rebaseline.

Only after that independent pass may the topic branch commit/push/bundle be treated as ready for
merge. Production Derivation/Verification writers remain a later bounded implementation unit.
