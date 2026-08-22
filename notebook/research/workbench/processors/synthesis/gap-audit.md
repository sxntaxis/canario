# Gap audit

## Closed enough for the next gate

- Existing tooling covers native PDF text, classical OCR orchestration, structured layout/table parsing,
  specialized visual AI, general multimodal AI and local ASR; ActaKit does not need to invent these engines.
- A cost/quality escalation pattern is already used by mature systems (Unstructured, Marker, Docling).
- The architecture must keep processor/model quality evidence typed and namespaced rather than force a
  universal confidence score.
- Code, model-weight and cloud-service licenses are distinct and must be pinned separately.

## Decision-threatening gaps that remain

1. **Civic corpus performance:** no studied benchmark substitutes for Costa Rican municipal documents.
2. **Docling vs simpler stack:** need measured evidence that Docling's structure value justifies its
   runtime/model footprint for the default built-in path.
3. **Spanish handwriting:** public capability claims are insufficient; need legal real/representative fixtures.
4. **Exact model licenses:** freeze must pin every enabled Docling/Paddle/Qwen model artifact and terms.
5. **Resource budgets:** target CPU/RAM/GPU envelope is not yet measured on representative hardware.
6. **Cloud policy:** retention/region/provider terms must be checked at deployment if Mistral is enabled.
7. **Audio:** no current canonical source requires ASR; keep research ready but defer runtime dependency.
8. **Large-object transport:** current ingress uses bytes; WORKBENCH may need stream/file handles after
   benchmark reveals realistic page/media sizes.
9. **Quality policy thresholds:** must be learned from Civic Processor Bench, not guessed from vendor scores.

## Non-gaps / deliberate non-goals

- A processor marketplace is not required for WP4C.
- One universal confidence value is rejected, not pending.
- Reimplementing OCR/layout/VLM engines inside ActaKit is rejected.
- AI output does not become source evidence; this is already an accepted provenance invariant.

## Next research action

Construct and run Civic Processor Bench. Only after results exist should WORKBENCH-001 freeze the
Processor interface, built-in ladder, exact backend pins and quality/escalation policy.
