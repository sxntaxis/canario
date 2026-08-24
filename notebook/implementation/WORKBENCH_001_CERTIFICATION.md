# WORKBENCH-001 — Independent certification

**Candidate HEAD:** `e719f28f6fdf63d03e68fcba760779a4d4ea0ba8`  
**Candidate bundle SHA256:** `7c072407aa70e848c122fb16f98be9bce1fdb30a69ca6ba8506a2715e6e040a9`  
**Certified state:** `WORKBENCH_001_GENERIC_PROCESSOR_BOUNDARY_IMPLEMENTED_AND_CERTIFIED`

The independent local certification agent verified the immutable candidate without
modifying it.

## Registered runtime

```text
SQLite version: 3.53.4
SQLITE_SOURCE_ID:
2026-07-24 19:02:57 bf7c7f30031888f4e796e429ab3978879485813aaca6f641c7b33e4e09459bcc
official amalgamation SHA3-256:
628a44cfe82c66aed1ccbbe85a562d2e33ebe64b3288981ed76285612227934e
runtime contract: PASS
```

The first certification attempt correctly rejected a distribution-patched
3.53.4 build whose source ID ended in `alt1`. The successful certification used
the exact registered upstream amalgamation in a disposable runtime rather than
weakening the runtime gate or replacing system SQLite.

## Schema and storage proof

```text
0001 SHA256: adf14a5006565197af3acf57c5cfc213510ba94217beb650403acbaf363b975a
STRICT tables: 58
FTS5 tables: 3
explicit indexes: 118
FK child paths: 127
FK child scans: 0
migration spec proof: PASS
migration freeze proof: PASS
storage proof: PASS
```

No `0002` exists; prerelease `0001` remains the canonical rebaselined baseline.

## Independent architecture audit

All 18 required invariants passed, including:

- exact scope retention across success/partial/failure;
- separate technical outcome and durable quality decision;
- typed/namespaced QualityEvidence without universal confidence;
- evidence/decision scope constrained to targets actually attempted by the run;
- no Processor SQLite/archive write authority;
- immutable original custody;
- pre-invocation egress denial for restricted material;
- no Workbench declassification authority;
- no representable credentials/account identity in canonical Workbench state;
- stable replay without reinvocation and hard immutable-collision rejection;
- physical derivative deduplication without provenance collapse;
- rollback/orphan cleanup without deleting shared archive objects;
- no ACCEPT from a claimed non-empty signal without material derivative output;
- one adapter-neutral boundary for D1-like, D2-like and Codex-like processors;
- no plugin marketplace, scheduler/event-sourcing layer or arbitrary metadata bag;
- unchanged DepositWriter and Ingress semantics.

## Suite

```text
pytest: PASS — 66 passed
compileall: PASS
Civic Processor Bench validator: PASS
Processor Research validator: PASS
git diff --check: PASS
candidate modified: NO
worktree clean: YES
```

## Authorization after certification

The generic Workbench is now authoritative for concrete processor units. The
next bounded unit may implement the deterministic D0/D1 PDF adapter without
changing the generic persistence/schema contracts merely to accommodate a
backend.
