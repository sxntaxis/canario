# D1 v8 S01 Reopening Patch Report

## Outcome

- D1 v8 commit: `98ca3fbc84f6d35a0ba52068b98da4ea10ec1aad`
- Replacement S01 audit: `SHARD_PASS_NO_DISPUTES`
- S01 reopening blocker: `RESOLVED`
- Fresh reconciliation verdict: `REFERENCE_DISPUTE`
- D1 v8 was not modified.

## Provenance

- The original S01 Terra worker/session was resumed (`source_ledger_worker_continuity=true`).
- The original pre-reference S01 ledger and seal were reused byte-for-byte.
- S02-S06 were reused byte-for-byte from `unchanged-shards/`; they were not rerun.
- Reconciliation used a fresh Terra worker context.
- Independence remains `WEAK_OR_UNKNOWN` because all reviewers are Terra/OpenAI-family workers.

## Mechanical Results

- S01: `156/156` reverse facts PASS and `384/384` evidence targets exact-reopened.
- Global: `61/61` units, `783/783` reverse facts, and `2019/2019` evidence targets.
- Reconciled hard findings: `10`.
- Direction: source-to-reference `5`, reference-to-source `3`, both `2`.
- Type: `MISSING_MATERIAL_ASSERTION` `5`, `MODALITY_ERROR` `3`, `QUALIFIER_ERROR` `2`.

## Canonical Artifacts

- `D1_SHARDED_SEMANTIC_REVIEW_V8_RECONCILED_R2.json`: `b07f35882d73a989d62a3876be56cabf5bb509d88ec9e74073f194da60fd1c91` (8953 bytes)
- `D1_SHARDED_SEMANTIC_REVIEW_V8_RECONCILED_R2.md`: `067618f458964c150aa7c93095189ece156330342e03e5a5d116f26dde470a41` (4216 bytes)
- `outputs/S01/D1_V8_S01_SHARD_AUDIT.json`: `a0e172feb2bffbb8f408299ea695772e916d943a65253c843821031c7e6da982` (78722 bytes)
- `outputs/S01/D1_V8_S01_SHARD_AUDIT.md`: `8679402502519a2759984cda81ebffa355c4eb578151ecd170223f74f395409b` (874 bytes)
