# Gap audit

## Blocking before LECTOR-002 resumes

### G1 — Query executor fit bench

Research narrowed the candidates:

- **SQLite:** mandatory simple baseline; already pinned and supports a hardened
  SELECT-only surface via authorizer/defensive controls.
- **DuckDB:** leading analytical challenger; must run sandboxed because generated
  SQL has process-level security implications and extensions/network/file access are
  capabilities to disable.
- **Arrow/Parquet:** optional interchange/derivative layer, not a source
  Representation replacement.

Benchmark SQLite vs DuckDB on the existing civic workbook and at least one larger
public dataset using the **same deterministic relational projection**. Measure:

- fidelity to canonical typed values/formulas/null lineage;
- deterministic conversion and hashability;
- query expressiveness;
- resource bounds;
- embedding/deployment cost;
- SQL dialect portability;
- cell/row lineage to the source Representation.

Do not let either engine independently reinterpret the original XLSX.

### G2 — Simple executor vs Thucy

Build no private verifier first. Compare:

```text
bounded single planner/executor
vs
Thucy sidecar
```

on the same frozen cases. Record quality, unsupported claims, abstention,
tool calls, latency, cost, and evidence provenance.

### G3 — Derivation provenance

Prove whether existing `ProcessRun` + Claim `kind=derived inference` can represent:

```text
input Representation(s)
query/program
executor/runtime
exact result
supporting evidence refs
```

without overloading processor semantics. If not, design a first-class derivation
record before persistence implementation.

### G4 — Verifier semantics

Decide the relation among:

```text
Claim
Assessment
VerifierResult
EvidenceSufficiency
```

Do not turn verifier verdicts into Claim lifecycle states.

### G5 — Multi-evidence / context

Prototype at benchmark-artifact level first:

```text
ReviewAnchor
ContextEnvelope
Truth/Claim
EvidenceRefs[1..N]
```

Test one table hierarchy case, one acta condition/decision case, and one
correspondence cross-reference case.

### G6 — Licensing

Before code/data reuse:

- resolve Thucy MIT-vs-Apache metadata conflict upstream;
- keep ClaimDB/TSVer ShareAlike material external unless deliberately accepted;
- keep AVeriTeC non-commercial material external;
- distinguish software license from benchmark/data/source-document license.

## Non-blocking radar

- AVerImaTeC for future image-text claim verification.
- M2-TabFact for multi-document multimodal tabular verification.
- SciTrue for source-level scientific attribution.
- newer claim-verification systems discovered through the ACL 2026 survey.

## Exit condition

This research pause closes only when G1–G5 have an evidence-backed design answer or
a bounded experiment plan precise enough to prevent another row-sampling-style
architecture mistake.
