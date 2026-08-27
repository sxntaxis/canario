# Structured reasoning production runtime

State: **IMPLEMENTED CANDIDATE — EXACT-RUNTIME + NATURAL ARTIFACT CERTIFICATION PENDING**

Baseline authority:

```text
generic reasoning runtime merge: b853519580f75f42385ac11d5a6d7bd4130118d0
merge authority:                 51f21f98ed377da302309c8a5c46fd0a32f10bbf
certified implementation commit: b5932e60416a000bcd4b878862bc4483e3dcbbc2
frozen 0001 SHA256:             8d6f793e1c976221311bd73ffe03bdaa2907e9508e7c0f5fad59131a02dc9f96
SQLite target:                  3.53.4
SQLite source ID:               2026-07-24 19:02:57 bf7c7f30031888f4e796e429ab3978879485813aaca6f641c7b33e4e09459bcc
```

## Purpose

This is the first production consumer of the frozen `canario.reasoning` boundary. It does not add
another reasoning framework and does not alter persistence. It proves that Canario can take an
already-canonical structured Representation, execute one bounded deterministic analytical query,
persist the exact Derivation/result/lineage, and then verify a proposition against explicit Source
Authority through the production runtime.

```text
canario.structured_table.v1 RepresentationTarget
-> exact host-owned materialization
-> StructuredSQLiteDerivationBackend
-> DerivationRun / DerivationResult / DerivationResultTarget / source lineage
-> StructuredScalarVerifierBackend
-> VerificationRun / source evidence / sufficiency / verdict
```

The concrete path intentionally contains no model/provider dependency. Model-assisted planning may
be added later as an orchestration profile, but the executable and verifier authority remain explicit.

## Structured SQLite Derivation backend

`canario.reasoning.structured_sqlite.StructuredSQLiteDerivationBackend` accepts exactly one bounded
structured-table input and one SQL query. It:

- requires the registered SQLite 3.53.4 runtime contract in production;
- materializes a disposable in-memory projection, never the canonical Canario database;
- enables `query_only`, disables extension loading, installs a SELECT/read/function authorizer, and
  enforces a progress/wall-clock budget;
- exposes only deterministic allowlisted SQL functions;
- bounds input bytes, rows and result bytes;
- serializes results as `canario.structured_sqlite_query_result.v1`;
- records the exact SQLite executor/source identity through the normal Derivation descriptor;
- binds its execution limits into `configuration_hash` so a different policy cannot replay under the
  same Derivation identity;
- reports `partial` source lineage when source projection tables were actually read and `none` for a
  source-independent result such as a constant query.

`partial` is intentionally conservative in v1: the backend knows that the bounded input target
contributed, but it does not claim exact row/cell causality merely because SQLite executed a SELECT.

## Deterministic scalar verifier

`StructuredScalarVerifierBackend` is a deliberately narrow first verifier. A
`ScalarVerificationRule` binds:

- exact proposition text;
- exact expected typed scalar;
- exact Derivation program SHA-256;
- exact Derivation configuration hash;
- required Source Authority scope kind.

A consumed result is accepted only when its immutable invocation snapshot identifies the expected
production SQLite backend/executor/source ID, exact program hash, exact configuration hash, and one
source-backed scalar result. The same numeric value produced by a different SQL program is therefore
not interchangeable evidence.

The v1 truth comparison supports exact `integer`, `string`, `boolean`, and `null` cells. It does not
promote SQLite binary-REAL equality to exact civic truth. Decimal/money verification needs a real
fixture and an exact numeric representation/profile rather than silent float semantics.

If the exact rule/program is valid but the Derivation has `none`/unavailable source lineage, the
result is `completed + insufficient_evidence`; it is not `supported`. A technical provenance/rule
mismatch is an execution failure instead.

## Generic read-contract extension proven by this consumer

The first concrete verifier exposed one missing read-side fact: a verifier receiving a consumed
Derivation result must also know which exact analytical executable/configuration produced it.

`VerificationDerivationSnapshot` therefore now includes immutable, already-persisted Derivation
provenance:

```text
implementation key/version
configuration hash
executor key/version/source ID
sandbox profile key/version
operation kind
program kind
program SHA256
outcome/error
```

This is **not a schema change**. It is a stricter host-owned read DTO over the already-frozen
`derivation_runs` record. It prevents two programs that coincidentally return the same bytes from
being treated as equivalent verification basis.

## Natural civic proof

Portable tests prove the production processor-to-reasoning chain with a generated XLSX. Final
certification also requires the exact previously retained official MTSS open-data workbook:

```text
source:
  Ministerio de Trabajo y Seguridad Social
  Liquidación presupuestaria enero 2026
XLSX SHA256:
  c98451ffdebc7976757a27ccd9a69a56061c16c37bd808b8d3398b3ffcb8608e
expected production structured Representation SHA256:
  0357f16c36f458a525715f64856549d22f39947812184b7c21ae5221d0207b4c
required parser/runtime identity:
  openpyxl 3.1.5
expected sheet/extent:
  MTSS / 147 rows / 15 columns
historical structural controls:
  A1=Subp. / C1=Descripción / O1=% Ejec. / A2=0 / C2=REMUNERACIONES
  O2=0.09557853868871936 / formula_count=0
```

`prove_structured_reasoning_runtime.py` must demonstrate on the exact registered SQLite runtime:

1. exact retained/recovered XLSX -> production `StructuredTableProcessor` -> exact MTSS production structured hash and historical 147x15/cell controls;
2. `SELECT COUNT(*) FROM sheet_1_rows` -> persisted source-backed Derivation -> `147`;
3. explicit `dataset_value` Source Authority -> persisted `supported` Verification;
4. hidden counterfactual `SELECT 147` -> lineage `none` -> `insufficient_evidence`.

The proof script itself never downloads data. Certification may recover only the exact documented
Drive object when its bytes reproduce the frozen source SHA-256 and size; any different upstream
revision remains a blocker.

### Representation identity correction

The first certification attempt correctly exposed a proof-authoring mistake: the earlier
`55bf57e4b6a788cd962a8485ab2c9df8987cb2a3d1e42faff56bf88283d16d5d` identity was copied from
the structured-reasoning bench without checking its source binding. That Representation belongs
to `CR-ESPARZA-BUDGET-001`, whose source XLSX SHA-256 is
`7ad3e90e9c64c781d51df178ee5565b37097109112fbe0ec77727de51ed71cc0`. It does **not** belong to
the MTSS workbook (`c98451ff...`).

For MTSS, the older Civic Processor Bench froze source identity, parser `openpyxl 3.1.5`, sheet
`MTSS`, extent `147 x 15`, zero formulas and selected control cells, but did not freeze a
`canario.structured_table.v1` byte hash. The first exact production materialization of those same
source bytes under the current certified processor is therefore frozen here as
`0357f16c36f458a525715f64856549d22f39947812184b7c21ae5221d0207b4c`. The natural proof checks
both that byte identity and the historical structural controls, so this correction does not
weaken provenance or silently reinterpret `55bf...`.

## Non-goals

This unit does not authorize:

- schema changes or `0002`;
- a generic OperationRun or recursive Derivation graph;
- unrestricted SQL over canonical Canario SQLite;
- automatic Claim/EvidenceLink/Assessment promotion;
- planner/model calls as verifier authority;
- exact row/cell lineage claims that this executor cannot prove;
- binary-REAL equality as exact civic truth;
- universal spreadsheet/document semantics from one MTSS workbook.

## Certification closure

The unit passed the exact SQLite 3.53.4/source-ID runtime, focused + full regression suites,
unchanged frozen `0001`, the exact natural MTSS proof above, compile/diff checks, bundle verification
and clean fresh-clone repeat. The certified implementation commit `b5932e604...` is merged through
`51f21f98...`; this concrete structured consumer is production-authorized within the non-goals above.
The next gate is the minimum Phase-D planner/final-verifier orchestration documented separately in
`STRUCTURED_VERIFIER_RUNTIME.md`.
