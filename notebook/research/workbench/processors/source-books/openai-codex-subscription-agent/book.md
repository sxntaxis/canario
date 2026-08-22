# OpenAI Codex CLI as a subscription-backed agent executor

## Scope

This Book evaluates the official OpenAI Codex CLI as an execution venue for a
future bounded ActaKit research adapter. It is not an OpenAI API client, an
OpenAI-compatible transport, or a production processor implementation.

## Evidence

- **COD-C001:** The official Codex CLI runs locally in a terminal and supports
  non-interactive `codex exec` for scripts and CI. **ActaKit:** a bench harness
  may invoke the documented CLI as a subprocess while owning only bounded input,
  output schema, scoring and non-secret provenance.
- **COD-C002:** Official documentation exposes `--ephemeral`, read-only sandbox
  defaults, `--output-schema`, image attachments and an explicit model option.
  **ActaKit:** use ephemeral isolated runs, read-only policy and a versioned
  transcription schema; never grant repository access to document processing.
- **COD-C003:** Official Codex documentation supports signing in with a ChatGPT
  plan, while API-key authentication is a separate path. **ActaKit:** the
  reference deployment can use subscription-backed agent execution without
  taking custody of ChatGPT or API credentials.
- **COD-C004:** ChatGPT-plan usage limits vary by plan and shared agent allowance;
  the official help page does not establish a per-call dollar price for this
  path. **ActaKit:** record `billing_mode=chatgpt_subscription`,
  `per_call_api_cost_usd=NOT_APPLICABLE`, and do not record quota/account data.
- **COD-C005:** OpenAI's current Help Center says Codex content processed through
  individual services, including Codex, may be used to improve models unless the
  user turns training off in ChatGPT Data Controls; Codex also has separate full-
  environment training controls. **ActaKit:** personal Plus/Pro use is not an
  enterprise no-training or zero-retention guarantee.
- **COD-C006:** The same official documentation says Business, Enterprise and Edu
  inputs/outputs are not used for training by default, while the business privacy
  page describes organization controls and retention options. **ActaKit:** a
  managed workspace may qualify for a stricter deployment policy, but the policy
  must name the workspace tier and controls rather than generalize from personal
  subscriptions.

## Decision

Codex is a first-class optional cloud/agent candidate for D4/D5 escalation in
the reference deployment profile. A research harness may test it, but production
Codex invocation, credential ownership, processor SPI and semantic output remain
unfrozen. Natural public artifacts require explicit egress policy and remain
unscored without independent truth.

## Egress policy

The reference small-organization profile may send explicitly public civic pages
through an operator-approved personal Codex subscription. Restricted/private
material is **not automatically eligible** under Plus/Pro: it requires a local
no-egress path, human review, or a deployment-specific approval after Data
Controls and applicable terms are verified. Business/Enterprise/Edu workspaces
have stronger default training controls and may support retention/governance
requirements, but those controls belong to the workspace deployment rather than
the generic Codex executor contract. The bench records only source policy,
executor identity, input hashes/bytes, and result status.
