# Processing escalation ladder

The ladder is **policy**, not a chain that every document must traverse. A processor attempt produces
QualityEvidence; the host decides `ACCEPT`, `ESCALATE`, or `QUARANTINE_REVIEW`.

## Documents and images

| Rung | Purpose | Default candidate | Escalate when |
|---|---|---|---|
| D0 | native format/direct parse | format-native parser / structured reader | unsupported, malformed, structure loss |
| D1 | born-digital PDF text | Poppler `pdftotext` (+ geometry when needed) | empty/garbled text, bad reading order, mixed scan pages |
| D2 | classical PDF OCR | OCRmyPDF + Tesseract | low coverage/confidence, complex layout/table, handwriting |
| D3 | structured document understanding | Docling candidate | low quality grade, layout/table failure, difficult visuals |
| D4 | specialized visual AI | PaddleOCR-VL candidate | still incomplete/incorrect, unusual handwriting/visual semantics |
| D5 | general multimodal / opt-in cloud AI | Qwen3-VL local; Mistral OCR cloud | unresolved disagreement or policy forbids provider/model |
| D6 | human | quarantine/review | automated evidence remains insufficient |

D5 is the **last automated rung**, not the final authority. Human review remains the terminal fallback.

Escalation may be page- or block-scoped when the upstream representation and processor preserve stable
coordinates. Do not rerun a whole 400-page file through a VLM because one page is bad.

## Audio

```text
A0 decode/inspect
-> A1 VAD/segmentation
-> A2 ASR (faster-whisper candidate; whisper.cpp alternate)
-> A3 optional diarization (pyannote only when required)
-> A4 optional audio-language/multimodal escalation for hard segments
-> A5 human review
```

Audio and visual ladders share provenance/quality policy but not numeric confidence scales.

## Invariants

- Original Representation is immutable.
- Every attempt has a ProcessRun with processor/model/version/config identity.
- Every derivative points to its parent Representation and ProcessRun.
- Failed attempts remain diagnosable; successful later escalation does not erase them.
- Local processors are network-off by default after explicit/pinned model installation.
- Cloud escalation requires explicit egress authorization and provider/model provenance.
- AI outputs are derived machine material; they never become factual source evidence merely because a model produced them.
