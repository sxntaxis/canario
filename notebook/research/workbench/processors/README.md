---
id: ACTAKIT-REPRESENTATION-PROCESSOR-RESEARCH-001
type: research-package
state: research-complete-for-benchmark-gate
authority: evidence
created: 2026-08-21
updated: 2026-08-21
researched_through: 2026-08-21
actakit_baseline: 02b5c3c9efad9207397c077d53aafac9f206cc86
---

# Representation processor research

This package is the mandatory research gate before `WORKBENCH-001` / WP4C implementation.
It studies existing extraction, OCR, document-AI, multimodal and audio processors so ActaKit does
not reimplement solved machinery or confuse processor novelty with product value.

## Design stance under test

ActaKit should ship a **curated built-in processing ladder** as part of the kit. Backend
replaceability is retained as an escape hatch for hardware, licensing, hard/new formats,
local-vs-cloud policy and benchmarking; WP4C is not a plugin-marketplace project.

The working ladder emerging from the evidence is:

```text
native/direct extraction
-> deterministic digital-PDF extraction
-> classical OCR orchestration
-> structured document processor
-> local specialized visual AI
-> local general multimodal AI / opt-in cloud Document AI
-> quarantine / human review
```

Audio follows a parallel path: decode/VAD -> ASR -> optional diarization -> human review.

## Package contents

- `source-books/`: 14 bounded tool/family Books, each with `book.md`, `sources.csv`, `claims.csv`.
- `synthesis/BOOK.md`: cross-source decision synthesis.
- `synthesis/processor-matrix.csv`: adopt/adapt/defer/reject matrix.
- `synthesis/escalation-ladder.md`: proposed rungs and escalation rules.
- `synthesis/quality-evidence.md`: typed quality evidence; explicitly no universal confidence.
- `synthesis/evaluation-plan.md`: Civic Processor Bench required before processor freeze.
- `synthesis/transfers.csv`: bounded transfers with stop conditions.
- `synthesis/gap-audit.md`: remaining decision-threatening gaps.

Research evidence does **not** authorize processor implementation. The next gate is fixture/benchmark
construction and comparative execution on candidate backends.
