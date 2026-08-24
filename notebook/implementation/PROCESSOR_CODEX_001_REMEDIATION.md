# PROCESSOR-CODEX-001 — strict-config remediation

**Original candidate HEAD:** `12c52c6fb0901c167f65ea76e9412318306269d5`  
**State:** certification remediation before cloud-fidelity certification

## Observed failure

The deterministic candidate, schema and runtime gates passed, but the first real
controlled TSE Codex attempt terminated as:

```text
ProcessRun outcome: failed
error_code: codex_exec_failed
QualityDecision: quarantine_review / processor_failed
source attachment bytes handed to executor: 942063
outputs: none
```

A bounded diagnostic of the exact candidate-generated CLI invocation returned:

```text
Error loading config.toml: unknown configuration field `tools.view_image`
```

No model output had been produced. This was therefore an adapter invocation bug,
not a transcription-quality, Workbench-policy, authentication or SQLite failure.

## Root cause

The Codex CLI is pinned to `0.149.0` and runs with `--strict-config`. In that
version, `view_image` is a stable key in the `[features]` namespace. The nested
`[tools]` namespace does not define `view_image`.

The original candidate incorrectly emitted:

```text
-c tools.view_image=false
```

Strict config correctly failed closed.

## Remediation

The corrected execution policy:

- replaces the invalid field with `features.view_image=false`;
- retains top-level `web_search="disabled"` and removes the redundant
  `tools.web_search=false` override;
- disables lifecycle hooks with the qualified `features.hooks=false` key;
- centralizes the static Codex `-c` overrides in one versioned tuple;
- hashes that exact static override tuple into `configuration_hash`.

The final item is provenance-critical: a material Codex execution-policy change
must no longer reuse the same durable configuration identity.

## Certification consequence

The old HEAD remains an immutable failed certification candidate. Certification
must use the remediated HEAD/bundle and repeat deterministic gates before making
new cloud calls. No TSE/Esparza fidelity gate is weakened.
