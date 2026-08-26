# Structured Reasoning Fit Bench — certified local results

State: **PASS**

Certified checkpoint:

```text
commit: 0f9a71e5acb0f093469571d59c896eab0c03c4c2
parent: 516ddd613bf58ef412d59bf4600652c8045c9c6b
bundle SHA256: 003b1823eed6f717c9d7a263044dca74ef54622a223acef8ddf30175c030fe1d
```

The checkpoint changed only Notebook/tests. `canario/`, schema/migrations, product
dependencies and raw/temporary benchmark data remained unchanged.

## Validation

```text
structured focused: 29 passed
LECTOR focused: 39 passed
full pytest: 239 passed, 2 subtests passed
compileall: PASS
git diff --check: PASS
fresh bundle clone: PASS, same test results
```

## Phase 0 — retired structured semantic gate

The old `semantic:structured_values` semantic-scope minting path is fail-closed.
Structural-only table preparation remains available without creating semantic gold/reference
authority. No historical artifact was deleted.

## Phase A — Esparza canonical projection

Exact retained `canario.structured_table.v1` source:

```text
SHA256:
55bf57e4b6a788cd962a8485ab2c9df8987cb2a3d1e42faff56bf88283d16d5d

projection SHA256:
1fc5e653ea125d326db297b83b464c90a55dccdf67f0932b48a1bc38af1768f5

deterministic independent repeat: PASS
```

No SQL engine reparsed the original XLSX.

## SQLite baseline

Exact runtime:

```text
SQLite: 3.53.4
source ID:
2026-07-24 19:02:57 bf7c7f30031888f4e796e429ab3978879485813aaca6f641c7b33e4e09459bcc
```

```text
Esparza corpus: 9/9 executable cases PASS
adversarial/read-only/runaway/result-bound tests: PASS
```

SQLite remains the architectural baseline.

## DuckDB challenger

Exact temporary benchmark runtime:

```text
DuckDB: 1.5.5
bubblewrap: 0.11.0
product dependency added: NO
```

Certified controls:

```text
AST single-SELECT gate: PASS
per-query timeout: 2000 ms
trusted bootstrap allowance: 30000 ms
fixed process allowance: 5000 ms
external access: disabled
autoload/autoinstall: disabled
configuration: locked
network: unshared
home/repo/canonical DB authority: absent
runaway query interruption: PASS
```

Esparza corpus:

```text
9/9 PASS
projection materializations: 1
total worker duration: 769.676 ms
query watchdog firings: 0
SQLite/DuckDB disagreements: 0
```

## INEC external scale lane

Exact retained public source:

```text
publisher: Instituto Nacional de Estadística y Censos (Costa Rica)
bytes: 431392
source SHA256:
a815ea5e36aeb9b586073941e6c52962aacaa60dbd8ff62b49396ac31ef8541d

rows: 2260
cells: 18080
non-empty: 17496
formulas: 0

transform spec SHA256:
a7bc996f84f26a9b7101b6be20c4043fd140e32015500e66c14e92019b7dbdf9

validation spec SHA256:
77c7a7184049daa15a48214fa9ff80f3d16cfd353a07d472e14dd2ed8085c13d

projection SHA256:
6968bcb15a0ae7a12146fd9e0c44df9f39ebbccb74471d6aef65e50414a78f34

deterministic repeat: PASS
```

Engine comparison:

```text
SQLite: 7/7 PASS
DuckDB: 7/7 PASS
DuckDB projection materializations: 1
DuckDB query count: 7
DuckDB hard process bound: 49000 ms
DuckDB bootstrap duration: 15591.353 ms
DuckDB total worker duration: 15919.596 ms
DuckDB query durations: 3.128, 3.092, 2.073, 1.843, 3.404, 1.458, 0.884 ms
normal DuckDB query-watchdog firings: 0
parent hard-timeout firing: NO
SQLite/DuckDB disagreements: 0
raw INEC data committed: NO
```

## SciTab prior-art representability

Exact external source:

```text
commit: 217cfbd71ebf39ba26a0938f0d87a9fce560e0fe
dataset Git blob: 8527241b039422c03d96929d09409e1d64afec8d
selected deterministic cases: 5
representability: PASS
model/verifier invoked: NO
raw data committed: NO
```

## G3 derivation provenance

Mechanical fit against the existing certified ProcessRun contract concluded:

```text
FIRST_CLASS_DERIVATION_REQUIRED = CONFIRMED
```

`ProcessRun` remains Representation-processor provenance. General analytical query/program
execution requires a distinct first-class Derivation execution contract; no schema change is
authorized by this checkpoint.

## Engine selection

```text
SQLite remains selected: YES
DuckDB sandbox certifiable: YES
DuckDB material required advantage demonstrated: NO
DuckDB product dependency authorized: NO
```

The challenger proved technically viable and analytically equivalent on these lanes, but no
measured required capability/performance advantage justifies increasing Canario's product
surface. DuckDB remains an optional benchmark/challenger until a future workload proves a
material need.

## Phase D handoff

The deterministic foundation is green, so Phase D is now authorized:

```text
simple bounded single planner/executor
versus
Thucy external/transport-adapted baseline
```

The parent checkpoint did not invoke Thucy, a model, semantic gold/reference generation, or
the tested LECTOR extractor.
