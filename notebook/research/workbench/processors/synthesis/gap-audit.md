# Gap audit

## Closed enough for the next gate

- Existing tooling covers native PDF text, classical OCR orchestration, structured layout/table parsing,
  specialized visual AI, general multimodal AI and local ASR; ActaKit does not need to invent these engines.
- A cost/quality escalation pattern is already used by mature systems (Unstructured, Marker, Docling).
- The architecture must keep processor/model quality evidence typed and namespaced rather than force a
  universal confidence score.
- Code, model-weight and cloud-service licenses are distinct and must be pinned separately.
- Local-vs-cloud is an execution-venue choice orthogonal to the processing rung; OpenAI is a first-class
  frontier cloud candidate and OpenAI-compatible transport is only an escape hatch with capability gates.

## Decision-threatening gaps that remain

1. **Civic corpus performance:** the controlled TSE civic baseline now proves bench mechanics and exposes coverage/confidence failure modes, but natural Esparza/municipal corpus coverage is still too small to select shipped defaults.
2. **Docling vs simpler stack:** need measured evidence that Docling's structure value justifies its
   runtime/model footprint for the default built-in path.
3. **Spanish handwriting:** public capability claims are insufficient; need legal real/representative fixtures.
4. **Exact model licenses:** freeze must pin every enabled Docling/Paddle/Qwen model artifact and terms.
5. **Resource budgets:** target CPU/RAM/GPU envelope is not yet measured on representative hardware.
6. **Cloud provider policy:** Civic Bench must compare the best local hard-case path with OpenAI and,
   where useful, Mistral; deployment must verify retention/region/provider terms and egress authorization.
   Exact OpenAI model choice is intentionally not frozen by this research snapshot.
7. **Audio:** no current canonical source requires ASR; keep research ready but defer runtime dependency.
8. **Large-object transport:** current ingress uses bytes; WORKBENCH may need stream/file handles after
   benchmark reveals realistic page/media sizes.
9. **Quality policy thresholds:** must be learned from Civic Processor Bench, not guessed from vendor scores.
10. **Provider capability contract:** WORKBENCH design still must decide static declaration vs runtime probe
    for OpenAI-compatible endpoints and how provider-specific options stay outside the processor contract.
11. **Secret facility:** processor implementation needs a host secret-resolution boundary before any cloud
    provider ships; this research explicitly forbids storing credential values in SQLite/provenance.

## Non-gaps / deliberate non-goals

- A processor marketplace is not required for WP4C.
- One universal confidence value is rejected, not pending.
- Reimplementing OCR/layout/VLM engines inside ActaKit is rejected.
- AI output does not become source evidence; this is already an accepted provenance invariant.

## Bench execution update

The natural corpus increment is present in the ignored bench work area and is
hash-recorded in `bench/corpus.yaml`. D1 Poppler inventory ran on Esparza,
FECOMUDI and Quepos PDFs without independent quality scoring. Tesseract,
OCRmyPDF, Docling, PaddleOCR-VL and Qwen3-VL were not runnable on this host;
OpenAI/Mistral were not authorized. Exact blockers are recorded in
`bench/results/natural-corpus-d1-and-availability.json`.

## Next research action

Curate independent truth for a small natural hard subset and run D2-D5 in a
capable local environment or under explicit cloud authorization. Only after
those results exist should WORKBENCH-001 freeze the Processor interface,
built-in ladder, exact backend pins and quality/escalation policy. The controlled
and natural D1 evidence is not enough to freeze WORKBENCH-001.
