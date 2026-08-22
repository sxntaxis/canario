---
id: ACTAKIT-REPRESENTATION-PROCESSOR-SYNTHESIS-001
type: research-synthesis
state: complete-benchmark-required
authority: evidence
created: 2026-08-21
updated: 2026-08-21
researched_through: 2026-08-21
actakit_baseline: 02b5c3c9efad9207397c077d53aafac9f206cc86
claim_ledger: claims.csv
transfer_ledger: transfers.csv
---

# Representation processors — state-of-the-art synthesis

## Decision question

Which existing tools should ActaKit compose into a built-in Mesa de trabajo processing ladder, and
when should it escalate from deterministic extraction to OCR, document AI, multimodal AI or human review?

## Executive conclusion

ActaKit should **not invent document processors**. It should own the orchestration contract, provenance,
quality policy and escalation decisions while composing mature engines.

The current strongest candidate stack is:

```text
D0 format-native parsing
D1 Poppler/pdftotext
D2 OCRmyPDF + Tesseract
D3 Docling structured processing
D4 specialized visual/document AI
   - local candidate: PaddleOCR-VL
   - cloud specialist candidate: Mistral OCR
D5 frontier general multimodal AI
   - local candidate: Qwen3-VL-family model
   - cloud candidate: OpenAI multimodal API
   - OpenAI-compatible endpoint: escape-hatch transport, capability-gated
D6 human review
```

This is a research nomination, **not yet an implementation freeze**. The mandatory next gate is the
Civic Processor Bench in `evaluation-plan.md`.

## Why this is the right abstraction

Processors are a built-in ActaKit strength, not an ecosystem outsourced to plugins. Replaceable
backends remain useful for hardware/OS constraints, licensing changes, new formats, execution-venue
policy, and future superior engines. Local and cloud are **venues**, not processor semantics: once a
quality gate requires an AI rung, deployment policy may choose local or cloud based on available
hardware, allowed egress, measured quality, latency and marginal cost. ActaKit owns the default ladder and ships a coherent kit.

A Source Connector answers *how material entered custody*. A Representation Processor answers *how a
custodied representation was transformed/decoded*. Those are separate axes and must stay separate.

## Quality model

There is no cross-engine numeric confidence that means the same thing. Tesseract has word confidence,
Docling has component grades and warns its numeric scores are internal, Mistral offers provider-specific
page/block/word confidence, and Whisper exposes log-probability/no-speech/compression/VAD signals.
Therefore ActaKit should store **typed QualityEvidence** and derive `ACCEPT | ESCALATE |
QUARANTINE_REVIEW` through policy. See `quality-evidence.md`.

## Provenance model

Every attempt is a ProcessRun. Original custody never changes. Every successful derivative identifies
its parent Representation, processor/model/version/config and output. Failed attempts remain diagnosable.
AI results are machine-derived representations, never evidence that authenticates their own factual content.

## Licensing/deployment conclusion

- Poppler/Tesseract/PaddleOCR/faster-whisper/whisper.cpp are attractive local candidates under permissive
  code ecosystems, subject to exact package/model review.
- Docling code is MIT but model licenses are independent and must be pinned.
- PyMuPDF's AGPL/commercial boundary makes it an optional/reference tool unless deliberately licensed.
- Surya/Marker code is permissive but current model weights add commercial thresholds.
- MinerU now uses a custom Apache-derived license with thresholds/attribution, adding policy cost.
- Mistral OCR is a hosted specialist service in the studied configuration; egress is explicit, never silent.
- OpenAI is a first-class general cloud multimodal candidate; current API credentials are bearer secrets
  and must remain outside ActaKit evidence/storage. Current provider retention controls are endpoint/account
  specific, so cloud provenance must not imply zero retention unless deployment policy actually verifies it.
- “OpenAI-compatible” is a useful ecosystem transport convention, demonstrated by vLLM, but does not
  guarantee endpoint/parameter/modality parity. Capability declaration/probing is mandatory.


## Execution venue / provider conclusion

Processor semantics and execution venue must be separate axes. `visual_transcribe`, `structured_document`
or a future equivalent capability should not mean “run Qwen” or “call OpenAI”. A built-in ActaKit policy
selects a candidate that satisfies required capabilities and source policy.

```text
required processor capability
        |
        +-- deterministic/local engine
        +-- local ML/VLM
        +-- first-party cloud provider (OpenAI candidate)
        +-- specialized cloud provider (Mistral candidate)
        `-- OpenAI-compatible endpoint escape hatch
```

Cloud is **optional but first-class**. Weak hosts may sensibly escalate from Tesseract/Docling directly to
a frontier cloud model rather than attempt a heavyweight local VLM. Conversely, restricted/no-egress
sources may forbid cloud entirely. The Civic Processor Bench must therefore compare the best allowed local
path against the best allowed cloud path instead of treating cloud as a Mistral-only emergency feature.

API keys and equivalent credentials are host secrets, not civic evidence. Future implementation should
resolve them from environment/OS secret/deployment facilities and never persist secret values in SQLite,
ProcessRun configuration, logs or derivative representations. Provenance records non-secret provider,
model, endpoint profile/request-template identity and the fact/extent of off-device egress.

## Audio conclusion

Audio is researched but **not activated** merely because the tools exist. If a real source requires it,
faster-whisper is the provisional Python-local ASR baseline, whisper.cpp the portable alternate, and
pyannote diarization remains separate/optional. Direct ASR is preferable where word/timestamp quality
evidence is needed; Docling's media support is useful but currently lacks word-level timestamps in its
export.

## Transfer status

See `processor-matrix.csv` and `transfers.csv`. No production `actakit/processors` package is authorized
by this research package.
