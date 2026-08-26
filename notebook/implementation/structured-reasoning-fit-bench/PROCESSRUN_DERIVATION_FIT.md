# G3 — ProcessRun vs Derivation provenance fit

Verdict: **FIRST_CLASS_DERIVATION_REQUIRED**

This is a design-fit conclusion only. It does **not** authorize a schema change.

## Why this is not just naming

The existing Workbench `ProcessRun` is intentionally a Representation-processor record.
The durable SQL row has useful generic facts (`process_kind`, implementation/version,
venue, configuration/model identity, timestamps, outcome/error), and
`process_run_inputs` can technically store more than one input row. But the certified
processor API/writer narrows those generic-looking tables into a materially different
contract:

- `ProcessingRequest` is rooted in exactly one `representation_id`;
- every `target_id` must belong to that same materialized Representation;
- replay expects every input row to repeat that one Representation identity;
- every input target must receive a Workbench `QualityDecision`;
- successful outputs are Representation derivatives attributed to the ProcessRun;
- a failed ProcessRun cannot emit such outputs;
- there is no first-class exact query/program body/digest;
- there is no first-class exact query result value/bytes independent of a Representation;
- there is no source-row/cell lineage relation from an analytical result to N input
  evidence refs;
- multi-Representation/cross-source derivation cannot be expressed through the current
  `ProcessingRequest`/writer without violating its invariants.

Changing those invariants to make analytical queries fit would weaken a certified
Workbench boundary merely to reuse its table name.

## Fit matrix

| Required derivation fact | Existing ProcessRun fit | Result |
|---|---|---|
| implementation/version/venue | direct fields | exact |
| model provider/name | direct fields | exact when model-backed |
| configuration identity | `configuration_hash` | exact but opaque |
| started/finished/outcome/error | direct fields | exact |
| ordered targets from one Representation | `process_run_inputs` + current writer | exact |
| ordered targets from multiple Representations | SQL table could store them, certified request/writer cannot | **impossible without boundary change** |
| exact query/program | no dedicated field/artifact identity | **missing** |
| executor/sandbox/resource profile | could be hidden inside configuration hash | **lossy / semantic overload** |
| exact result that is not itself a new Representation | no first-class result contract | **missing** |
| row/cell/evidence lineage for result | no result-to-evidence relation | **missing** |
| failed analytical query | ProcessRun outcome/error can say failed | partial fit |
| no mandatory processor quality-decision semantics | current writer requires one per target | **collision** |

## Three modeling probes

### 1. Successful single-Representation query

A ProcessRun could record implementation, one input target, timestamps and success. To
retain the SQL and result, however, the design would have to either:

1. pretend the result is a derived Representation, or
2. hide SQL/result/sandbox semantics in generic configuration/quality payloads.

Both lose the explicit distinction accepted by architecture:

```text
query/program = derivation provenance
query/program != source evidence
query result != automatically a Representation or Claim
```

Result: **lossy / semantic overload**.

### 2. Failed query

`ProcessRun(outcome=failed,error_code=...)` models the terminal failure axis well. It still
has nowhere explicit for the attempted query/program identity and resource/sandbox profile.

Result: **partial fit**.

### 3. Multi-Representation derivation

The SQL schema's `process_run_inputs` is superficially capable of different
`representation_id` values. The certified processor writer is not: its request has one
root Representation and `_verify_existing_run()` expects all input rows to match that one
identity. Reusing the table directly would bypass the canonical writer or broaden
Workbench semantics.

Result: **not representable through the accepted boundary**.

## Minimum future information contract

A future first-class derivation record should be no larger than necessary:

```text
DerivationRun
- stable id
- operation kind
- implementation + version
- executor/runtime identity
- configuration/policy digest
- sandbox/resource-profile digest
- exact query/program bytes or immutable object/digest
- started_at / finished_at
- terminal outcome + bounded error code
- optional model/provider attribution

DerivationInput[ordered]
- RepresentationTarget identity
- Representation identity

DerivationResult
- exact typed value or immutable result bytes + digest
- deterministic encoding/version

DerivationEvidence[0..N]
- exact existing typed evidence/target refs supporting result lineage
```

A later policy may promote a proposition-worthy result into
`Claim(kind=derived_inference)`. That is separate from recording the execution.

## Stop condition

Revisit this conclusion only if a later experiment demonstrates an extension to
`ProcessRun` that preserves all of the above **without** weakening its one-Representation
processor contract, mandatory per-target quality decisions, or Representation-output
semantics. No such fit exists in the current certified API/writer.
