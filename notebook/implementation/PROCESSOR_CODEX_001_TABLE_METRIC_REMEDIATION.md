# PROCESSOR-CODEX-001 — table proof metric remediation

**Prior remediated candidate HEAD:** `5d7e5849c00d40a8889ab968b599ee676a41b8dd`  
**State:** certification remediation after controlled TSE table gate

## Observed certification result

The Fedora production proof reached the real subscription-backed Codex processor and returned a successful transcription whose expected table cells were all faithful, but the TSE table gate failed:

```text
exact_row_recall: 0.0
cell_fidelity: 1.0
Esparza: not attempted
```

All deterministic, runtime, schema, auth and migration gates passed before that call.

## Root cause

The production proof's `_table_metrics` had drifted from the metric already frozen in the Civic Processor Bench research harness.

The research metric defines a recovered expected row as one where every curated expected cell appears in its expected position. It separately counts:

- missing or mismatched expected cells; and
- extra **non-empty** cells

as `false_cell_count`.

This deliberately permits trailing empty padding because an empty structural slot adds no document content and does not shift any expected field. An inserted empty cell before an expected field still fails cell matching because the later expected values move out of position.

The production proof accidentally added an additional requirement:

```text
len(observed_row) == len(expected_row)
```

and omitted `false_cell_count`. That made harmless empty trailing padding fail the entire row while providing weaker visibility into actually invented non-empty cells.

## Remediation

The production proof is realigned exactly with the research metric semantics:

```text
exact_row_recall == 1.0
cell_fidelity == 1.0
false_cell_count == 0
```

Consequences:

- all expected cells must still match in position;
- missing/mismatched cells still fail;
- extra non-empty cells still fail;
- only empty trailing padding is tolerated.

A focused regression test proves both the tolerated empty-padding case and rejection accounting for an extra non-empty cell.

## What does not change

This remediation does **not** change:

- `actakit/processors/codex.py`;
- the Codex prompt;
- output JSON Schema;
- processor configuration hash;
- model or CLI qualification;
- quality policy;
- CER or required-span thresholds;
- egress/auth rules;
- SQLite schema or migration hash;
- Workbench behavior.

It repairs certification-metric drift rather than weakening processor quality requirements.
