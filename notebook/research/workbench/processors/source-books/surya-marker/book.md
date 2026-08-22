---
id: ACTAKIT-BOOK-SURYA_MARKER-001
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

# Surya OCR and Marker

## Question

What do Surya/Marker teach about selective VLM escalation, and are they suitable dependencies?

## Audit basis

Current 2026 releases, modes and code/model licensing.

## Evidence horizon

- **SYM-S001 — Surya OCR current PyPI:** 0.22.1 current; code Apache 2.0, model weights modified Open Rail-M with commercial thresholds. **Boundary:** Code license alone does not describe model-weight obligations.
- **SYM-S002 — Marker 2.0 current PyPI:** Balanced and fast modes; fast uses native text plus surgical VLM repair; code Apache 2.0, weights carry modified Open Rail-M terms. **Boundary:** Project benchmarks are vendor-maintained.
- **SYM-S003 — Marker 2.0 release:** Device-aware fast vs balanced routing and minimal/full-page VLM escalation. **Boundary:** Specific thresholds/modes are Marker policy, not necessarily ActaKit policy.

## Claim ledger synopsis

- **SYM-C001:** Marker 2 operationalizes a fast native-text path with surgical VLM repair and full-page escalation only when needed. **ActaKit:** Strong precedent for ActaKit’s proposed escalation philosophy.
- **SYM-C002:** Surya/Marker code is permissive but current model weights have additional commercial terms. **ActaKit:** Do not make these models unconditional shipped defaults without a model-license decision.
- **SYM-C003:** Surya provides modern OCR/layout/table capabilities and can be used by other frameworks such as Docling. **ActaKit:** Benchmark Surya as a backend without necessarily adopting Marker wholesale.
- **SYM-C004:** Selective repair can preserve efficiency better than whole-document VLM processing. **ActaKit:** Escalation unit should support page/block granularity when provenance and backend permit.

## Bounded transfer

Adopt the selective-escalation pattern. Benchmark Surya as a backend; keep Marker primarily as reference/comparator unless model licensing is explicitly accepted.

## Do not import

Do not copy Marker’s policy thresholds or treat code license as sufficient model-license clearance.

## Residual risk / unresolved question

Model license and deployment service terms can change; exact weight pin needs audit.

## Closure verdict

**pattern-adopt_backend-benchmark** for the WP4C selection horizon. This Book is evidence, not implementation authorization.
