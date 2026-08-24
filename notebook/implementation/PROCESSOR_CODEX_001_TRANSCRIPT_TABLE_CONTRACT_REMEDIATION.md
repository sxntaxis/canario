# PROCESSOR-CODEX-001 — transcript/table contract remediation

**Prior candidate HEAD:** `186869f024f8423d80b59bea848c4c3809f2234e`  
**State:** certification remediation after controlled TSE text-gate instability

## Observed certification result

The Fedora certification environment was fully qualified and all deterministic gates passed.
The real controlled TSE page then produced a semantically poor `transcription`:

```text
CER:                  0.7985401459854015
required-span recall: 0.14285714285714285
Esparza:              not attempted
```

A prior real call on the same controlled page had produced table cells with
`cell_fidelity = 1.0`. The image is dominated by a visibly bordered table.

This combination exposed a contract ambiguity rather than a reason to relax the
text gate or retry until a stochastic call happens to pass.

## Root cause

The v1 prompt/schema exposed two output channels:

```text
transcription
+ tables[].rows[][]
```

but did not define their relationship. It asked for exact visible transcription
and also asked the model to put visually supported rows in `tables`, without
saying whether table text must remain in `transcription`.

Therefore both of these model behaviours were compatible with the written v1
contract:

```text
A. page-complete transcription + supplemental table structure
B. prose-only/partial transcription + table text only in tables
```

The production proof correctly compares the complete page truth against the
`transcript` Representation. Behaviour B therefore creates an incomplete canonical
text derivative even if the separate table derivative is accurate.

Combining channels only inside the certification proof would hide this product
bug: downstream consumers of the canonical transcript would still receive missing
text.

## Remediation: v2 page-complete transcript contract

The reference prompt is versioned to:

```text
codex_visual_transcription_v2
```

Its semantics are now explicit:

- `transcription` is the complete readable page text in natural reading order;
- readable text inside tables remains in `transcription`;
- `tables` is a supplemental structured copy, not a replacement for transcript text;
- cross-field duplication between `transcription` and `tables` is intentional;
- unreadable text is still not invented and remains represented by explicit
  `uncertain_spans`.

The transmitted JSON Schema repeats the same field semantics in descriptions, so
prompt and structured-output contract do not disagree.

Frozen v2 identities for this remediation are:

```text
request_template_hash: b10745051bffc0ddded6fd08e30a8947154ccb8e71dce4fd35d0a9c9c27fee84
output_schema_hash:     8c8c369cf18f4269c72ca2293db6cb3556d6db8a2f9f3f103dca16aa4543a72a
configuration_hash:     6650c221ee5ef2a0a499fe4af83e460ffaa715e883ed1049c4948b76f4eddc31
```

## Local cross-channel invariant

Prompting alone is not the safety boundary. After structural schema validation,
the adapter computes deterministic:

```text
multimodal.table_text_coverage:v1
```

This is **not confidence**. It is the fraction of non-empty structured table-cell
occurrences that are also present in the normalized page transcription. Repeated
cell values retain multiplicity; whitespace/case normalization is used only for
the cross-channel comparison.

Required successful contract state:

```text
table_text_coverage == 1.0
```

If Codex emits table text that is absent from `transcription`, the executor handoff
is preserved but the model output is rejected as:

```text
codex_contract_invalid
```

with:

```text
multimodal.schema_valid = true
multimodal.table_text_coverage < 1.0
```

No transcript/table derivative is created and the existing failed-ProcessRun policy
ends in review. This prevents an internally contradictory response from receiving
`ACCEPT` in production.

## What does not change

This remediation does **not** change:

- one-page-only cloud scope;
- model (`gpt-5.6-sol`) or Codex CLI qualification (`0.149.0`);
- egress/auth/custody boundaries;
- CER, span, table-row, cell-fidelity or uncertainty certification thresholds;
- Workbench persistence shape;
- SQLite `0001` or its SHA256;
- DIRECT/OCR behaviour;
- human-review fallback.

It does change the Codex request-template hash, output-schema hash and therefore
`configuration_hash`, because the externally visible processor contract itself is
now different. That identity change is deliberate and required.
