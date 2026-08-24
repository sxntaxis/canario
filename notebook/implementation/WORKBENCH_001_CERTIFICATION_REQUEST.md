# WORKBENCH-001 — Independent Certification Request

**Expected implementation start:** `497b09b3f922676d7c1fd19ab102f3d905a48dd6`
**Candidate state:** `WORKBENCH_001_IMPLEMENTED__CERTIFICATION_PENDING`
**Current `0001` SHA256:** `adf14a5006565197af3acf57c5cfc213510ba94217beb650403acbaf363b975a`

The implementation author did not self-certify the target SQLite runtime. The
certification agent should treat the supplied implementation bundle as immutable
input, inspect the design/code independently, and report defects rather than
silently widening scope.

## Required target-runtime proof

Run on the registered ActaKit SQLite 3.53.4 source ID:

```text
2026-07-24 19:02:57 bf7c7f30031888f4e796e429ab3978879485813aaca6f641c7b33e4e09459bcc
```

At minimum:

```bash
python notebook/research/pre-sql/schema/prove_runtime_contract.py
python notebook/research/pre-sql/schema/prove_migration_0001_spec.py
python notebook/research/pre-sql/schema/prove_migration_freeze.py
python notebook/research/pre-sql/schema/prove_storage_operations.py
python notebook/research/workbench/processors/bench/validate_bench.py
python notebook/research/workbench/processors/validate_research.py
PYTHONPATH=. pytest -q
python -m compileall -q actakit
git diff --check
```

The ignored natural corpus is not transported in the Git bundle; strict-corpus
validation is not a WORKBENCH-001 certification requirement if those bytes are
absent in the certification checkout.

## Architecture audit

Independently verify:

1. failed page-scoped runs retain exact target scope without fake outputs;
2. `ProcessRun.outcome` is separate from durable quality decision;
3. QualityEvidence is registered/typed/namespaced and no universal confidence was
   introduced;
4. Processor implementations receive no SQLite/archive write authority;
5. egress-required processors are ineligible before invocation for restricted or
   unauthorized material;
6. credentials/account/auth data are not representable in canonical Workbench
   persistence;
7. Workbench processing cannot declassify restricted custody; public redaction/release is not a Processor side effect;
8. retrying the same stable ProcessRun identity does not re-invoke the processor
   after commit and changed immutable scope/config fails loudly;
9. distinct attempts may share physical derivative bytes without provenance
   collapse;
10. rollback leaves no canonical partial graph and cleans only newly-created
    unreferenced archive bytes;
11. Poppler-like, OCR-like and Codex-like fixture descriptors fit one generic
    boundary without vendor-specific core fields;
12. no plugin marketplace/event-sourcing/scheduler architecture was introduced;
13. DepositWriter and Ingress behavior remain unchanged.

## Certification outcome

Only if the target-runtime suite and architecture audit pass should the state be
advanced to:

```text
WORKBENCH_001_GENERIC_PROCESSOR_BOUNDARY_IMPLEMENTED_AND_CERTIFIED
```

A certification failure should report the exact violated invariant. Do not start
concrete D0/D1 adapters in the certification pass.
