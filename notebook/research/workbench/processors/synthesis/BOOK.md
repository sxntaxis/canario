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
D4 PaddleOCR-VL specialized local document AI
D5 Qwen3-VL general local visual escape hatch
   OR explicit opt-in Mistral OCR 4.1 cloud escalation
D6 human review
```

This is a research nomination, **not yet an implementation freeze**. The mandatory next gate is the
Civic Processor Bench in `evaluation-plan.md`.

## Why this is the right abstraction

Processors are a built-in ActaKit strength, not an ecosystem outsourced to plugins. Replaceable
backends remain useful for hardware/OS constraints, licensing changes, new formats, local/cloud policy,
and future superior engines. ActaKit owns the default ladder and ships a coherent kit.

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
- Mistral OCR is a hosted commercial service in the studied configuration; egress is explicit, never silent.

## Audio conclusion

Audio is researched but **not activated** merely because the tools exist. If a real source requires it,
faster-whisper is the provisional Python-local ASR baseline, whisper.cpp the portable alternate, and
pyannote diarization remains separate/optional. Direct ASR is preferable where word/timestamp quality
evidence is needed; Docling's media support is useful but currently lacks word-level timestamps in its
export.

## Transfer status

See `processor-matrix.csv` and `transfers.csv`. No production `actakit/processors` package is authorized
by this research package.
