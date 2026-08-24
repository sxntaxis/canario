---
id: ACTAKIT-BOOK-QWEN3_VL-001
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

# Qwen3-VL

## Question

Can a general local multimodal model serve as the ultimate automated escape hatch for visual/handwritten documents?

## Audit basis

Official Qwen3-VL repository/model card and current OCR capability claims.

## Evidence horizon

- **QVL-S001 — Qwen3-VL official repository:** General multimodal model family; expanded OCR supports 32 languages and difficult visual conditions. **Boundary:** Vendor capability statements require civic benchmark verification.
- **QVL-S002 — Qwen3-VL-32B-Instruct model card:** Apache-2.0 model card and standard local Transformers usage. **Boundary:** 32B is a heavyweight example, not necessarily the ActaKit default size.

## Claim ledger synopsis

- **QVL-C001:** Qwen3-VL explicitly targets OCR under blur, low light, tilt, rare characters and long-document structure. **ActaKit:** A general multimodal rung may recover content that specialized OCR misses, including unusual handwriting/visual context.
- **QVL-C002:** At least the 32B Instruct release is Apache-2.0 and locally runnable through standard model tooling. **ActaKit:** Local multimodal escalation is viable without mandatory cloud egress.
- **QVL-C003:** Qwen3-VL is generative and general-purpose rather than an OCR-specific deterministic extractor. **ActaKit:** Constrain prompts/output schemas, keep image/page provenance, and treat output as machine-derived rather than source truth.
- **QVL-C004:** General VLM OCR capability is a last automated rung, not evidence that every document should use a VLM. **ActaKit:** Escalate only when cheaper/specialized rungs fail quality policy.

## Bounded transfer

Adapt a pinned local Qwen3-VL-family model as a general visual escape hatch after specialized document processing, subject to Civic Bench.

## Do not import

Do not make unconstrained VLM prose a canonical Representation or use it as factual evidence for itself.

## Residual risk / unresolved question

Need handwriting-specific municipal fixtures, hallucination measurement, hardware sizing and model-size selection.

## Closure verdict

**adapt-after-benchmark** for the WP4C selection horizon. This Book is evidence, not implementation authorization.
