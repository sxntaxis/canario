# Processing escalation ladder

The ladder is **policy**, not a chain that every document must traverse. A processor attempt produces
QualityEvidence; the host decides `ACCEPT`, `ESCALATE`, or `QUARANTINE_REVIEW`.

A second, orthogonal decision chooses the **execution venue**. Deterministic rungs are normally local;
AI rungs may run locally or through an explicitly authorized cloud provider. ActaKit must not encode
“local” or a vendor name into the semantic meaning of a rung.

## Documents and images

| Rung | Purpose | Candidate family | Escalate when |
|---|---|---|---|
| D0 | native format/direct parse | format-native parser / structured reader | unsupported, malformed, structure loss |
| D1 | born-digital PDF text | Poppler `pdftotext` (+ geometry when needed) | empty/garbled text, bad reading order, mixed scan pages |
| D2 | classical PDF OCR | OCRmyPDF + Tesseract | low coverage/confidence, complex layout/table, handwriting |
| D3 | structured document understanding | Docling candidate | low quality grade, layout/table failure, difficult visuals |
| D4 | specialized visual/document AI | PaddleOCR-VL local candidate; Mistral OCR cloud specialist | still incomplete/incorrect, unusual handwriting/visual semantics |
| D5 | frontier general multimodal AI | Qwen3-VL-family local candidate; OpenAI cloud candidate | unresolved disagreement or automated evidence remains weak |
| D6 | human | quarantine/review | automated evidence remains insufficient |

D5 is the **last automated rung**, not the final authority. Human review remains the terminal fallback.

### Venue selection inside an AI rung

```text
AI rung required
   |
   +-- source policy forbids egress -> best qualified local backend
   |
   +-- host lacks viable local compute -> qualified cloud backend
   |
   +-- both viable -> policy compares benchmarked quality, latency and marginal cost
   |
   `-- no qualified backend -> human/quarantine
```

The default is therefore **deterministic-first**, not necessarily local-ML-first. A low-power machine may
rationally run D0-D3 locally and choose cloud for D4/D5. A workstation with a suitable accelerator may
remain entirely local. Neither deployment changes the representation/provenance contract.

OpenAI is a first-class D5 cloud benchmark candidate. Mistral remains a specialized D4 cloud-document
candidate. An OpenAI-compatible endpoint may satisfy a rung only after capability declaration/probing;
API shape alone is not proof of vision, structured-output, audio or security equivalence.

## Reference deployment decision table

| Scenario | Inspect | Accept | Escalate | Quarantine/review | Venue boundary |
|---|---|---|---|---|---|
| Native text is present and complete | D1 text, page coverage, reading order | required spans and structure pass | missing/garbled page or block -> D2 | contradictory or unopenable source | local deterministic |
| Native extraction is empty/incomplete | D1 empty output and page coverage | never accept empty output as complete | D2 OCR on affected pages | malformed input or custody failure | local, no egress |
| D2 OCR output | CER/WER where truth exists, required-span recall, false insertions, page coverage, OCR signal namespaced | benchmarked threshold and structure checks pass | hard page/block -> Codex controlled request | disagreement, poor coverage, restricted source | Codex only with explicit egress; CLI owns auth |
| Table/reading-order failure | row/cell fidelity and coordinates, not text CER alone | rows reopen and preserve source order | compare bounded Docling or Codex page/block run | unresolved structure or invented cells | D3 local if justified; Codex if egress allowed |
| Restricted or no-egress hard visual | same quality evidence plus source policy | qualified local result | optional future local-heavy backend | human review when no qualified local backend | no cloud; local heavyweight remains optional |

The controlled evidence currently supports D2 for mixed-page recovery and Codex
for selected hard-page escalation. It does not establish production thresholds,
natural-scene quality, or a mandatory D3/local-heavy dependency.

Escalation may be page- or block-scoped when the upstream representation and processor preserve stable
coordinates. Do not rerun a whole 400-page file through a VLM because one page is bad.

## Audio

```text
A0 decode/inspect
-> A1 VAD/segmentation
-> A2 ASR (faster-whisper candidate; whisper.cpp alternate)
-> A3 optional diarization (pyannote only when required)
-> A4 optional audio-language/multimodal escalation for hard segments
     (local or explicitly authorized cloud venue)
-> A5 human review
```

Audio and visual ladders share provenance/quality policy but not numeric confidence scales.

## Invariants

- Original Representation is immutable.
- Every attempt has a ProcessRun with processor/provider/model/version/config identity.
- Every derivative points to its parent Representation and ProcessRun.
- Failed attempts remain diagnosable; successful later escalation does not erase them.
- Local processors are network-off by default after explicit/pinned model installation.
- Cloud escalation requires explicit egress authorization and provider/model/endpoint-profile provenance.
- Secret credential values never enter SQLite, ProcessRun payloads, logs or Representations.
- Cloud provenance records that material left the host and enough non-secret request/model identity to audit the attempt.
- OpenAI-compatible endpoints are capability-gated; compatibility is never inferred from URL shape alone.
- AI outputs are derived machine material; they never become factual source evidence merely because a model produced them.
