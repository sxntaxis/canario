# Structured Reasoning Fit Bench — local results

State: **PENDING_LOCAL_CERTIFICATION**

The candidate intentionally contains no fabricated runtime results. The local agent owns
execution, tests, real artifact resolution, timing/resource observations, commit, and
certification.

## Candidate expectations

### Phase 0

- old `prepare-table` fails closed;
- `prepare-table-structural` creates no `gold_scope.json`;
- no active path can mint `semantic:structured_values` authority.

### Phase A

Real source Representation expected SHA-256:

```text
55bf57e4b6a788cd962a8485ab2c9df8987cb2a3d1e42faff56bf88283d16d5d
```

Record after local execution:

```text
path:
source SHA:
projection SHA:
projection bytes:
sheets:
rows:
cells:
non-empty cells:
formulas:
repeat deterministic:
```

### Phase B — SQLite

Record exact:

```text
sqlite_version:
sqlite_source_id:
registered runtime match:
security adversarial lane:
result bounds:
runaway termination:
```

### Phase B — DuckDB

Use a dedicated temporary venv outside the repository. The candidate does not add a
product dependency. Record:

```text
duckdb version:
venv path:
bubblewrap version:
AST SELECT guard:
enable_external_access:
autoinstall_known_extensions:
autoload_known_extensions:
lock_configuration:
AST SELECT-only gate:
network namespace:
filesystem escape tests:
extension tests:
write/DDL tests:
query timeout:
bootstrap grace:
process fixed overhead allowance:
corpus query count:
process hard timeout:
projection materializations per corpus: 1 required
bootstrap duration:
per-query durations:
```

### Phase C — Esparza corpus

`build-esparza-corpus` must emit exactly ten cases covering lookup, filter, aggregate,
group, top-k, window, numerical composition, cross-sheet representability, bounded
absence, and insufficient evidence. Expected values come from the independent Python
projection oracle.

Run both corpora through `run-corpus`, then `compare-corpus-runs`. Record SQLite/DuckDB
agreement and every dialect divergence. A numeric comparison may use the bounded comparator
while preserving exact source decimal lineage separately. Semantic-only insufficiency cases
are expected to remain `not_executed_by_design`.

### External scale lane

Source: INEC, `Histórico de compras 2016 - 2021`.

Raw data remains external. Verify exact downloaded bytes, encoding hypothesis, row count,
then run both engines over the same neutral projection. License metadata from the publisher
currently says `Licencia no especificada`; this lane is execution-only and authorizes no
vendoring/redistribution.

### Prior-art lane

SciTab exact repository commit:

```text
217cfbd71ebf39ba26a0938f0d87a9fce560e0fe
```

Dataset Git blob:

```text
8527241b039422c03d96929d09409e1d64afec8d
```

Record downloaded SHA-256 and the five mechanically selected case IDs. Do not commit the
raw dataset.

## Engine selection

Do not fill this before measurements:

```text
SQLite remains selected: YES/NO
DuckDB material required advantage: YES/NO
DuckDB sandbox certifiable: YES/NO
recommendation:
```

The architecture default remains SQLite unless both DuckDB conditions are YES.

## Phase D

Thucy invoked: **NO in this checkpoint**.
Private semantic verifier built: **NO**.

Phase D is authorized only after the deterministic foundation is locally green.
