---
id: ACTAKIT-BOOK-AUDIO_WHISPER-001
type: research-source-book
state: research-complete-for-selection-gate
authority: evidence
created: 2026-08-21
updated: 2026-08-21
researched_through: 2026-08-21
actakit_baseline: 02b5c3c9efad9207397c077d53aafac9f206cc86
source_ledger: sources.csv
claim_ledger: claims.csv
---

# Whisper-family local ASR: faster-whisper and whisper.cpp

## Question

What should the local audio transcription rung preserve, and which backend is the best default?

## Audit basis

Current faster-whisper data model/quality signals and whisper.cpp portability/runtime support.

## Evidence horizon

- **AUD-S001 — faster-whisper transcription implementation:** Segments expose avg_logprob, compression_ratio, no_speech_prob; words can carry probabilities; VAD and language probability are available. **Boundary:** Internal thresholds/signals are Whisper-family-specific.
- **AUD-S002 — faster-whisper project README:** CTranslate2 implementation with CPU/GPU quantization and performance guidance. **Boundary:** Project benchmark results require same-settings comparison.
- **AUD-S003 — faster-whisper license:** MIT code. **Boundary:** Underlying model weights still have their own provenance/license.
- **AUD-S004 — whisper.cpp README:** v1.9.1; C/C++, CPU, CUDA, Vulkan, ROCm, quantization and VAD; MIT. **Boundary:** Backend behavior/output quality must be benchmarked under equivalent decode settings.

## Claim ledger synopsis

- **AUD-C001:** Whisper transcription exposes multiple heterogeneous quality signals rather than one calibrated confidence. **ActaKit:** Represent ASR QualityEvidence as named signals: avg_logprob/no_speech/compression/language/word probability/VAD coverage.
- **AUD-C002:** faster-whisper is a strong Python-local baseline with efficient CTranslate2 inference and permissive code license. **ActaKit:** Provisional default ASR candidate for benchmark.
- **AUD-C003:** whisper.cpp offers unusually broad hardware portability including Vulkan/ROCm/CPU and quantization. **ActaKit:** Keep as a portable/AMD/edge alternate backend rather than forcing one inference stack.
- **AUD-C004:** Performance comparisons are only meaningful with equivalent model/beam/thread settings. **ActaKit:** Civic Bench must pin model and decoding policy across ASR backends.

## Bounded transfer

Provisional adopt faster-whisper as the local ASR baseline; adapt whisper.cpp as portable alternate. Final choice waits for audio fixture/hardware benchmark.

## Do not import

Do not invent a cross-modal global confidence from Whisper probabilities/logprobs.

## Residual risk / unresolved question

No current Esparza audio source is part of the canonical ingestion path; avoid pulling heavy ASR dependencies until a real source/fixture justifies it.

## Closure verdict

**provisional-adopt-defer-dependency** for the WP4C selection horizon. This Book is evidence, not implementation authorization.
