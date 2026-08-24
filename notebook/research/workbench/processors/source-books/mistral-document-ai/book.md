---
id: ACTAKIT-BOOK-MISTRAL_DOCUMENT_AI-001
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

# Mistral OCR 4.1 / Document AI

## Question

What should a cloud document-AI escalation rung look like, and what evidence must surround data egress?

## Audit basis

Current OCR 4.1 model/API documentation and pricing.

## Evidence horizon

- **MIS-S001 — Mistral OCR 4.1 model page:** OCR 4.1 released 2026-07-16 with paragraph bboxes, structural labels and block confidence. **Boundary:** Hosted service behavior can change independently of ActaKit.
- **MIS-S002 — Mistral OCR API:** Page/block/word confidence granularities and structured JSON schema annotation options. **Boundary:** Confidence is provider/model-specific.
- **MIS-S003 — Mistral Document AI OCR processor:** Tables, headers/footers, block labels, bboxes and confidence; PDF/image/office inputs. **Boundary:** Cloud service implies data egress unless a separately licensed/self-hosted deployment is used.
- **MIS-S004 — Mistral pricing:** Current OCR pricing is per page, with separate annotated pricing. **Boundary:** Pricing is time-sensitive and must not be hard-coded into architecture.

## Claim ledger synopsis

- **MIS-C001:** Mistral OCR 4.1 provides structured blocks, bounding boxes and confidence beyond plain text transcription. **ActaKit:** Good cloud D4 escalation candidate for hard documents.
- **MIS-C002:** Provider confidence can be requested at page/block/word granularity. **ActaKit:** Capture it as namespaced QualityEvidence, not global confidence.
- **MIS-C003:** Cloud OCR has explicit per-page marginal cost. **ActaKit:** Escalation policy should avoid cloud processing when cheaper local rungs already pass quality gates.
- **MIS-C004:** Using the hosted processor sends source material to an external provider. **ActaKit:** Cloud processing must be explicit opt-in with source/privacy policy, egress provenance and retention controls.

## Bounded transfer

Adapt as an optional specialized cloud Document-AI provider behind an explicit egress policy and pinned model identity.

## Do not import

Do not silently upload civic source material or make cloud availability required for ordinary ingestion.

## Residual risk / unresolved question

Provider terms, retention, regional processing and price are time-sensitive and require deployment-time policy.

## Closure verdict

**optional-cloud-adapter** for the WP4C selection horizon. This Book is evidence, not implementation authorization.
