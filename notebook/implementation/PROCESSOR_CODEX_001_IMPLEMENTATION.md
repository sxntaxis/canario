# PROCESSOR-CODEX-001 — implementation record

**Start HEAD:** `49d337ddbfae0be32a351e5adb37063bbaabe528`  
**Parent state:** `PROCESSOR_OCR_001_OCRMYPDF_TESSERACT_IMPLEMENTED_AND_CERTIFIED`  
**Candidate state:** `PROCESSOR_CODEX_001_IMPLEMENTED__CERTIFICATION_PENDING`

## Production code

`actakit/processors/codex.py` adds `CodexVisualTranscriptionProcessor`, the first
production egress backend. It uses official Codex CLI only as a one-page,
schema-constrained visual executor through the already-certified Workbench.

The adapter is fixed to:

```text
Codex CLI certification pin: 0.149.0
model: gpt-5.6-sol
venue: subscription_agent
scope: exactly one pdf_page:v1
endpoint profile: openai_codex_subscription
auth store: keyring
```

There is no OpenAI API-key path in this unit.

## Isolation

A dedicated non-default CODEX_HOME is mandatory and must be private (`0700` on
POSIX). `auth.json`, ambient `config.toml`, user skills and POSIX
`/etc/codex/skills` make the profile ineligible. The child receives an empty scratch HOME and a minimal environment.
The command uses `--ephemeral --ignore-user-config --ignore-rules --strict-config`,
disables bundled skills for the process, and disables unrelated tools/features.
The exec policy is versioned in the adapter configuration hash; the corrected
0.149.0-qualified policy uses `features.view_image=false` and top-level
`web_search="disabled"`, disables lifecycle hooks, and hashes the exact static Codex override list as part of configuration identity.

The source PDF is used only for local Poppler rendering and is deleted before
Codex starts. Scratch contains only the single rendered page attachment, static
schema, output target and empty HOME.

## Page-complete transcript contract v2

Certification exposed an ambiguity in the original two-channel output: Codex could
place table text only in `tables` while returning an incomplete `transcription`.
The request template is therefore versioned to `codex_visual_transcription_v2`.
`transcription` is now explicitly page-complete, including readable table text, and
`tables` is supplemental structure. The JSON Schema carries the same descriptions.

After schema validation the adapter deterministically verifies that every non-empty
structured table-cell occurrence is represented in the transcription, preserving
repeated-cell multiplicity. It emits `multimodal.table_text_coverage:v1`; coverage
below `1.0` is `codex_contract_invalid`, keeps positive post-handoff egress truth,
creates no derivative, and cannot be accepted.

This changes prompt/schema/configuration identity but does not change SQLite, scope,
auth, egress, model, CLI qualification, or fidelity thresholds.

## Persistence and egress

The processor returns material bytes and QualityEvidence only. `WorkbenchWriter`
owns canonical ProcessRun/egress/evidence/decision/Representation writes.

The integration exposed and fixed the generic pre-egress failure case. Candidate
`0001` SHA256 is now:

```text
5226c873487d9bd05fc62b7a1f323d6e804b003cc4e08bd2fe2b531adb6057bb
```

Only `process_run_egress.bytes_egressed > 0` changed to `>= 0`; schema inventory
is unchanged and no `0002` exists.

## Portable implementation proof

Without invoking Codex, the implementation checkout proves:

- dedicated-profile rejection paths;
- exact page-only descriptor;
- strict command/config isolation;
- child environment secret minimization;
- endpoint/prompt/config authorization matching;
- unauthorized/restricted rejection before executor invocation;
- transcript + table persistence and model/egress provenance;
- uncertainty -> review;
- empty valid output not accepted;
- invalid schema -> failed ProcessRun;
- pre-handoff failure -> zero source bytes egressed;
- post-handoff failure -> rendered attachment byte count retained;
- replay without a second executor call;
- no profile/auth paths in canonical metadata.

Actual Codex fidelity remains an independent certification gate.
