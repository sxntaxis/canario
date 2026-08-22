---
id: ACTAKIT-BOOK-OPENAI_COMPATIBLE_API-001
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

# OpenAI-compatible inference API convention

## Question

Can ActaKit use the widespread OpenAI-shaped `base_url + api_key + model` interface as an escape hatch
across cloud and self-hosted AI without pretending it is a universal standard?

## Audit basis

Current vLLM serving documentation, because it is a major local inference system that explicitly
implements OpenAI-compatible endpoints and multimodal inputs.

## Evidence horizon

- **OAC-S001:** vLLM implements several OpenAI-style endpoints but documents unsupported/different
  parameters. **Boundary:** Compatibility is scoped, not universal equivalence.
- **OAC-S002:** The official OpenAI client can target vLLM by changing `base_url` and `api_key`.
  **Boundary:** Shared client shape says nothing about model quality.
- **OAC-S003:** Multimodal inputs are supported for compatible served models.
  **Boundary:** Modalities depend on model/server/endpoint.
- **OAC-S004:** vLLM explicitly warns that its API-key flag does not secure every endpoint.
  **Boundary:** OpenAI-style authentication syntax is not a complete security model.

## Claim ledger synopsis

- **OAC-C001:** OpenAI compatibility is a useful de-facto transport convention.
- **OAC-C002:** It is not a standard that guarantees feature parity. ActaKit needs explicit capability
  declaration/probing.
- **OAC-C003:** Credential/header similarity does not remove normal endpoint trust, TLS and network
  policy requirements.
- **OAC-C004:** A common transport can span local/self-hosted/cloud execution while model/provider
  identity stays separate.

## Bounded transfer

Allow a future `OpenAICompatibleProvider` escape hatch configured by non-secret endpoint identity plus
an external credential reference. Require capability checks for image/document/audio/structured-output
features before the provider may satisfy a processor rung.

## Do not import

Do not call this a universal API standard. Do not assume `/v1` means OpenAI. Do not assume Responses,
vision, structured output or audio feature parity. Do not trust arbitrary configured endpoints with
civic documents merely because they accept an OpenAI client.

## Residual risk / unresolved question

WORKBENCH design must decide whether capability declaration is static, probed, or both, and how to
isolate provider-specific request options without leaking them into the Processor contract.

## Closure verdict

**adopt-transport-pattern-with-capability-gates**. Useful escape hatch; not a reason to make processor
architecture provider-shaped.
