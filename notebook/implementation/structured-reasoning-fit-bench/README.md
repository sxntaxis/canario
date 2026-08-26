# Structured Reasoning Fit Bench — deterministic foundation

State: **certified deterministic foundation; Phase D authorized**

Certified checkpoint:

```text
0f9a71e5acb0f093469571d59c896eab0c03c4c2
```

This subtree contains bench artifacts only. It does not define production schema or
product dependencies.

## Invariants

1. The Esparza engine input is the retained `canario.structured_table.v1` derivative,
   never an independently parsed XLSX.
2. `structured_reasoning_fit_bench.py` converts those bytes to a neutral canonical JSON
   projection before an SQL engine sees data.
3. The neutral projection preserves every in-extent cell's sheet/row/column/address,
   typed value, formula text, `data_type`, `number_format`, and merged-range metadata.
4. Engine analytical columns are conveniences. Exact canonical numeric text/lineage stays
   alongside `DOUBLE` values used by SQL.
5. Expected deterministic answers are produced from the neutral projection by Python /
   `Decimal`, not copied from SQLite or DuckDB output.
6. SQLite and DuckDB receive disposable derived state only.
7. DuckDB runs in a separate bubblewrap namespace with no network/home/repository/canonical
   database mount; external access and extension autoload/install are disabled, configuration
   is locked before untrusted SQL, and every SQL statement is AST-gated to exactly one parsed
   `SELECT`. A corpus run materializes the trusted neutral projection once in that disposable
   sandbox session; each query still receives its own watchdog/interruption budget.
8. Model-generated SQL is untrusted code. No model is invoked in this checkpoint.
9. External CSV projection identity binds only transformation semantics plus the exact source bytes. Source-validation guards (expected SHA/header/row count) are recorded separately in the projection manifest; prose notes and validation-only pins must not perturb the neutral projection bytes.

## Files

- `../structured_reasoning_fit_bench.py` — projection, SQLite executor, DuckDB sandbox
  launcher, independent oracle/corpus generation, external-lane normalization.
- `../structured_reasoning_duckdb_worker.py` — minimal sandbox worker; no Canario imports.
- `external-datasets.csv` — exact external scale lane metadata.
- `inec-historic-purchases-spec.json` — explicit external CSV normalization contract.
- `prior-art-cases.csv` — prior-art dataset/version/selection contract.
- `PROCESSRUN_DERIVATION_FIT.md` — G3 fit result.
- `RESULTS.md` — local execution record template; it is intentionally pending here.

## Local execution order

The local certifier should resolve the retained Esparza derivative by exact SHA-256:

```text
55bf57e4b6a788cd962a8485ab2c9df8987cb2a3d1e42faff56bf88283d16d5d
```

Then:

```text
project-table
-> build-esparza-corpus
-> run-corpus --engine sqlite
-> provision exact temporary DuckDB venv
-> run-corpus --engine duckdb
-> compare-corpus-runs
-> adversarial executor checks
-> external INEC scale lane (exact retained public bytes bound by SHA-256 + row count in the source spec)
-> SciTab deterministic prior-art selection/representability
```

No semantic gold and no Thucy call belongs in this checkpoint.

## Deterministic corpus runner

`run-corpus` validates every evidence reference against the exact projection, executes only
cases carrying SQL, and compares each result to the pre-existing Python/`Decimal` oracle.
Cases such as global absence that are intentionally `insufficient_evidence` remain
`not_executed_by_design`; they are never counted as successful SQL and never as execution
failures. `compare-corpus-runs` then compares only cases successfully executed by both
engines. Runtime timing is recorded but excluded from result correctness/digests. DuckDB corpus
runs expose bootstrap duration separately from each query duration so setup cost is not
confused with the untrusted-query budget.

The SciTab lane in this deterministic checkpoint proves selected prior-art tables can be
projected without importing SciTab ontology. It does **not** claim that a hand-written or
model-generated SQL program has verified those natural-language claims; that mapping belongs
to the later planner/Thucy Phase D.
