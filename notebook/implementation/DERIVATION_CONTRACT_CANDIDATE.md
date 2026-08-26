# Derivation Contract Candidate

State: **G3 DESIGN ACCEPTED — JOINT PERSISTENCE SHAPE SUPERSEDED BY RECONCILIATION**

Authority chain:

```text
architecture split: 516ddd613bf58ef412d59bf4600652c8045c9c6b
G3 fit proof:       0f9a71e5acb0f093469571d59c896eab0c03c4c2
verdict:            FIRST_CLASS_DERIVATION_REQUIRED
```

## Why ProcessRun is not the canonical Derivation record

`ProcessRun` is a certified Mesa-de-trabajo processor contract. Its semantics are intentionally
optimized around Representation transformation:

```text
one rooted ProcessingRequest
-> exact Representation targets
-> processor capability/configuration
-> terminal execution
-> quality evidence/decision per input target
-> zero or more derived Representations
```

The structured-reasoning fit proved that a general derivation needs facts that are not merely
optional processor metadata:

```text
multiple ordered Representation/target inputs
optional exact Claim-revision inputs where justified
exact executable query/program/specification
executor identity/version
sandbox/resource policy
terminal result independent of creating a Representation
exact typed result identity
result/evidence lineage
```

Encoding those semantics as processor metadata would make `ProcessRun` mean two different
things and weaken its existing invariants. The architecture therefore requires a distinct
first-class derivation execution record.

## Conceptual record

Use the working name `DerivationRun` in technical design. This does not freeze a user-facing
Spanish product term.

Minimum semantics:

```yaml
derivation_run_id: drv_...
operation_kind: query | program | rule | other_registered
implementation_key: stable registered executor/implementation identity
implementation_version: exact version
configuration_ref: exact non-secret configuration/profile identity
sandbox_profile_ref: bounded execution/egress/resource policy identity
started_at: timestamp
finished_at: timestamp
outcome: success | failed
error_code: optional bounded code
program_kind: sql | expression | script | other_registered
program_text_or_digest: exact executable specification or retained object digest
result_kind: scalar | table | structured | artifact_ref | none
result_digest: exact deterministic result digest when material result exists
result_payload_ref: optional retained bounded result object / representation reference
```

No universal confidence field.

## Inputs

Inputs are ordered and first-class.

```yaml
derivation_inputs:
  - ordinal: 1
    representation_id: rep_...
    target_selector_kind: whole:v1 | table_range:v1 | ...
    target_selector_payload: validated selector
  - ordinal: 2
    representation_id: rep_...
    target_selector_kind: ...
```

A future use case may justify an exact Claim-revision input, but Claim input is not required
for the first structured-data implementation and should not be added to SQL until a real
fixture proves it.

Input order is retained even when the operation is mathematically commutative because it is
execution provenance.

## Program/query provenance

The executable operation is provenance, not source evidence.

Requirements:

- exact bytes/text or exact retained-object digest;
- declared program/query language and version/profile;
- no secret interpolation in the stored form;
- normalized display text may exist, but cannot replace exact executable identity;
- model-generated SQL remains untrusted executable input and carries the planner/model
  provenance that proposed it.

If a query contains transient physical paths, secrets or host-only handles, persist a
canonical redacted/parameterized executable plus exact non-secret parameter identity rather
than leaking host state.

## Result

A successful DerivationRun has an exact result identity independent of whether the result is
promoted to a Claim or materialized as a Representation.

The result contract must preserve typed values. Stringifying all SQL output is not
acceptable.

Examples:

```text
scalar decimal result
small deterministic result table
bounded structured JSON result
large retained analytical derivative referenced by Representation/ArchiveObject
```

A failed run may have no result.

`success` means the bounded program executed and produced a valid result. It does not mean
the proposition is true, important, reviewed, or publication-ready.

## Result-to-evidence lineage

Derivation provenance must distinguish:

```text
input scope
executed program
result
supporting source evidence
```

The first structured implementation should retain exact row/cell lineage where the executor
can prove it. If an executor cannot provide cell-level lineage for an operation, that absence
must be explicit rather than fabricated.

A conservative lineage record may link one result/result-row to one or more typed source
locators. Multiple EvidenceLinks on a later `derived_inference` Claim remain valid and
independent.

## Relation to Claim

A DerivationRun does not automatically create a Claim.

```text
DerivationRun
    |
    | optional attributable promotion
    v
Claim(kind=derived_inference)
```

If a Claim is created, its origin provenance can reference the DerivationRun. The Claim's
supporting EvidenceLinks refer to source Representations/locators; the executable program is
not itself factual source evidence.

## Relation to Verification

Verification may internally cause one or more DerivationRuns, for example model-planned SQL
queries. A future verifier execution therefore needs explicit references to the derivations it
used rather than hiding SQL inside an opaque model trace.

```text
VerificationRun
  -> DerivationRun 1
  -> DerivationRun 2
  -> ...
```

Phase D now selects a minimum verifier contract: a future `VerificationRun` references the exact
ordered DerivationRuns whose results were actually used, and separately retains verdict, evidence,
explicit sufficiency, abstention reason and execution provenance. This still does not by itself
authorize a `VerificationRun` table.

## Relation to ProcessRun

Keep the contracts distinct:

```text
ProcessRun
  transforms/inspects Representation material in the Mesa de trabajo

DerivationRun
  executes a bounded analytical operation over one or more canonical evidence scopes
```

A ProcessRun may produce a Representation later consumed by a DerivationRun. A DerivationRun
may produce a large material result that is subsequently retained as a Representation. The
records may reference each other through explicit provenance; neither subsumes the other.

## Security

Every executable Derivation boundary must treat generated program/query text as untrusted.
The first SQL implementation inherits the certified fit-bench security principles:

- disposable analytical projection, never canonical application DB;
- read-only/allowlisted execution;
- no arbitrary filesystem/network/extensions/secrets;
- bounded query time, result rows and bytes;
- explicit executor/runtime identity;
- exact Source Authority remains outside SQL engine semantics.

## Reconciliation transfer

The remaining joint design gate is now closed by
`notebook/implementation/DERIVATION_VERIFICATION_RECONCILIATION.md`.

The accepted refinement keeps this G3 boundary but adds a distinct `DerivationResult` and
`DerivationResultTarget` rather than forcing analytical output into one-Artifact Representation
custody. Source-contribution lineage is attached to exact result targets. Derived Claim origin,
Verification scope/Derivation consumption, EvidenceLink source evidence and optional Assessment are
there reconciled without a polymorphic execution graph.

The next authorized unit is the bounded prerelease `0001` rebaseline plus applicable
freeze/storage/purge/backup/runtime certification. This file remains the historical G3 reasoning
record; the reconciliation document is authority for the joint persistence shape.
