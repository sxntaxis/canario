---
id: ACTAKIT-BOOK-OPENAI_CLOUD_AI-001
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

# OpenAI cloud multimodal API

## Question

Should ActaKit treat frontier cloud multimodal capacity as a first-class processing venue, and what
boundary is required for credentials, egress, model identity and retention?

## Audit basis

Current OpenAI API platform, pricing and data-control documentation as of the research date.

## Evidence horizon

- **OAI-S001 — API Platform overview:** Responses API is the current direct path for text, structured
  output, tools and multimodal workflows; the quickstart uses `Authorization: Bearer $OPENAI_API_KEY`.
  **Boundary:** API/model details are time-sensitive.
- **OAI-S002 — API pricing:** Cloud marginal cost is measurable but model/modality specific.
  **Boundary:** Never freeze today's price table into architecture.
- **OAI-S003/OAI-S004 — data controls/privacy:** API content is not used for training by default, but
  retention/application-state behavior is endpoint/account specific and stronger controls such as ZDR
  require explicit configuration/eligibility. **Boundary:** Cloud processing remains data egress even
  when provider policy is strong.
- **OAI-S005 — multimodal/audio capability surface:** The same provider family exposes vision,
  structured outputs and audio/transcription capabilities. **Boundary:** Exact model quality must be
  benchmark-tested by modality.

## Claim ledger synopsis

- **OAI-C001:** OpenAI is a general cloud multimodal provider candidate, not merely an OCR service.
  **ActaKit:** D5 should be `cloud multimodal AI`, with OpenAI first-class beside specialized cloud
  Document AI.
- **OAI-C002:** API keys are bearer credentials. **ActaKit:** keep secret material outside SQLite,
  logs, ProcessRun payloads and derived Representations; provenance may retain only a non-secret
  credential reference/slot name.
- **OAI-C003:** Structured outputs and multimodal requests support constrained extraction.
  **ActaKit:** benchmark schema-constrained transcription/field extraction, not free-form prose.
- **OAI-C004:** Default training policy is not the same as zero retention. **ActaKit:** egress policy
  must record provider/endpoint/retention posture and permit operator restrictions.
- **OAI-C005:** Model capabilities/cost change. **ActaKit:** choose by capabilities and exact pinned
  model snapshot at benchmark/deployment time.

## Bounded transfer

Add OpenAI as a first-class **cloud execution venue/provider candidate** for the final automated rung,
behind explicit egress authorization, external secret handling, capability declaration and exact
provider/model provenance.

## Do not import

Do not hard-code today's flagship model as the architecture. Do not store API keys in ActaKit's DB or
Notebook. Do not silently upload source material. Do not assume that API business-data policy means
zero retention for every endpoint/account.

## Residual risk / unresolved question

The Civic Processor Bench must identify which current OpenAI model is worth using for handwriting,
difficult scans and structured visual extraction, how often it beats the best local path, and its
cost/latency/false-insertion profile. Deployment must separately verify account retention/regional
policy.

## Closure verdict

**first-class-cloud-benchmark-candidate** for WP4C. This Book expands the benchmark/architecture
selection horizon; it does not authorize provider implementation or credentials storage.
