# Gap audit

## Closed enough for the next gate

- Existing tooling covers native PDF text, classical OCR orchestration, structured layout/table parsing,
  specialized visual AI, general multimodal AI and local ASR; ActaKit does not need to invent these engines.
- A cost/quality escalation pattern is already used by mature systems (Unstructured, Marker, Docling).
- The architecture must keep processor/model quality evidence typed and namespaced rather than force a
  universal confidence score.
- Code, model-weight and cloud-service licenses are distinct and must be pinned separately.
- Local-vs-cloud is an execution-venue choice orthogonal to the processing rung; official Codex CLI is a
  first-class subscription-backed agent executor, while OpenAI-compatible transport is only an escape hatch
  with capability gates.

## Residual gaps after closure

1. **Corpus breadth:** the natural truth set is intentionally small and cannot select universal shipped quality thresholds.
2. **Multi-column and handwriting:** no representative handwriting truth was authorized; difficult reading order and handwriting remain specialized escalation/human-review cases.
3. **Backend pins:** no Docling/Paddle/Qwen model is enabled by this freeze, so their future model licenses remain future work.
4. **Deployment resource budgets:** D2 process-tree RSS is measured, but representative hardware envelopes for every optional backend remain deployment work.
5. **Provider capability contract:** OpenAI-compatible endpoints remain an escape hatch requiring capability declaration/probing and deployment policy.
6. **Secret facility:** any production cloud provider still needs a host secret-resolution boundary; credential values remain forbidden in evidence and logs.
7. **Audio and large-object transport:** deferred until a real source requires them.

## Non-gaps / deliberate non-goals

- A processor marketplace is not required for WP4C.
- One universal confidence value is rejected, not pending.
- Reimplementing OCR/layout/VLM engines inside ActaKit is rejected.
- AI output does not become source evidence; this is already an accepted provenance invariant.

## Bench execution update

The natural corpus increment is hash-recorded in `bench/corpus.yaml`. D1 Poppler
inventory ran on Esparza, FECOMUDI and Quepos PDFs without independent quality
scoring. Controlled D2 and official Codex runs are recorded in the bench results.
Docling was evaluated only for disposable footprint and is recorded as optional,
not default, in `bench/results/docling-footprint-decision.json`. PaddleOCR-VL and
Qwen3-VL remain optional unrun venues; no provider API was used. Natural availability is recorded in
`bench/results/natural-corpus-d1-and-availability.json`.

## Freeze implication

The independent natural truth, bounded public Codex diagnostics, corrected page-
level D2 evidence, spreadsheet structure evidence, Codex privacy policy, and
resource evidence now support freezing the generic Processor interface and
quality/escalation shape. They do not authorize production backend code or claim
that every format is solved. Future specialized work must add fixtures and pins
without changing the custody/provenance boundary.
