---
id: ACTAKIT-BOOK-PYANNOTE-001
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

# pyannote.audio

## Question

When should speaker diarization enter ActaKit, and what operational/privacy details matter?

## Audit basis

Current 4.0.x community pipeline, exclusive diarization, offline use and telemetry.

## Evidence horizon

- **PYA-S001 — pyannote.audio project README:** Python/PyTorch speaker diarization with community and premium pipelines. **Boundary:** Diarization identifies speaker turns/clusters, not semantic identity or transcript truth.
- **PYA-S002 — pyannote.audio 4.0 release notes:** Community-1 exclusive diarization helps reconcile speaker turns with transcription; offline use supported; telemetry optional. **Boundary:** Model hub access/user conditions may apply.
- **PYA-S003 — pyannote.audio changelog:** 4.0.7 released 2026-06-30. **Boundary:** Version does not imply ActaKit needs diarization now.

## Claim ledger synopsis

- **PYA-C001:** Speaker diarization is a separate task from transcription. **ActaKit:** Model it as an optional derived representation/annotation capability, not an ASR requirement.
- **PYA-C002:** Exclusive diarization is designed to simplify alignment with transcription timestamps. **ActaKit:** Useful if later civic video/audio requires speaker-attributed transcripts.
- **PYA-C003:** Community pipeline can run offline after model acquisition. **ActaKit:** Diarization need not imply continuous cloud egress.
- **PYA-C004:** Telemetry exists and is optional. **ActaKit:** If integrated, ActaKit should default telemetry off and document model-fetch/network behavior.

## Bounded transfer

Defer until a real source requires speaker attribution; then adapt pyannote as an optional diarization stage after/beside ASR.

## Do not import

Do not infer real-world person identity from anonymous speaker clusters without separate evidence/review.

## Residual risk / unresolved question

Heavy ML dependency, model hub terms, and speaker-identity privacy all need a concrete use case.

## Closure verdict

**defer-until-source-need** for the WP4C selection horizon. This Book is evidence, not implementation authorization.
