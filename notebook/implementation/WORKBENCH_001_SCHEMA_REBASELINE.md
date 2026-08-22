# WORKBENCH-001 — Prerelease `0001` Schema Rebaseline

**Input HEAD:** `497b09b3f922676d7c1fd19ab102f3d905a48dd6`  
**Old `0001` SHA256:** `31cac5ccc3440ce555242ba288317df527bb30949b2142026d8ceb2805d3adfc`  
**New candidate SHA256:** `cc8bbdb22a62349494004de642ec21b4ef2f9d30f22d33f1cf5cba08ed28e7a3`  
**State:** `IMPLEMENTED__INDEPENDENT_CERTIFICATION_PENDING`

## Why a rebaseline is required

The closed Civic Processor Bench froze page/block escalation, typed/namespaced
QualityEvidence, explicit egress provenance, and a quality decision independent
from technical execution outcome. The previous schema could not durably answer:

- which exact page/block/table target a failed ProcessRun attempted;
- which processor-attributable quality signals justified escalation;
- whether a technically successful run was accepted or escalated by policy;
- what non-secret source material was egressed and under which data-control
  profile.

Those are generic Workbench requirements, not backend-specific features. Building
around their absence would force a later core/schema redesign. ActaKit is still
pre-release with no compatibility-bearing user database fleet, so policy requires
rebasing `0001` rather than inventing `0002`.

## Physical delta

`process_runs` gains:

```text
execution_venue NOT NULL registered-open key
error_code nullable; required for failed, forbidden for success
```

New STRICT tables:

```text
process_run_inputs
process_run_egress
quality_evidence
quality_decisions
```

`process_run_inputs` records ordered exact RepresentationTarget scope and uses a
composite FK to prove target ownership by the input Representation.

`process_run_egress` stores only non-secret bytes/policy/data-control/template/
endpoint provenance.

`quality_evidence` stores registered `signal_key + signal_version` payloads for an
exact run target. Core code validates bounded payload contracts; SQL JSON is not a
runtime dependency.

`quality_decisions` stores `accept | escalate | quarantine_review` separately from
`ProcessRun.outcome`, with policy/version/reason provenance and a next capability
only for escalation.

Purge target vocabulary is extended to cover the four new Workbench record
families.

## Candidate physical inventory

Portable proof environment:

```text
STRICT tables:        58
FTS5 virtual tables:  3
application triggers: 0
explicit indexes:     118
FK child paths:       125
FK child scans:       0
WITHOUT ROWID:        0
SQL JSON dependency:  absent
```

## Proofs run in the implementation environment

```text
prove_migration_0001_spec.py = PASS
prove_migration_freeze.py    = PASS
prove_storage_operations.py  = PASS
pytest                       = PASS
compileall                   = PASS
```

The implementation environment exposes SQLite 3.46.1, below the registered
ActaKit target 3.53.4. Therefore `prove_runtime_contract.py` correctly fails
closed here. That is not waived: the local certification agent must repeat the
schema/runtime proofs on the registered SQLite 3.53.4 source ID before this
candidate can be marked certified.

## Compatibility and boundaries

- no `0002` exists;
- fresh prerelease databases are recreated from the new `0001`;
- an old schema-v1 file with only 54 STRICT tables now fails the schema inventory
  check rather than being silently accepted;
- DepositWriter and Ingress contracts are unchanged;
- original custody remains immutable;
- the new Workbench writer is bounded to ProcessRun/scope/quality/egress and
  derived Representation custody;
- canonical cutover, Claim writers and historical import remain unauthorized.
