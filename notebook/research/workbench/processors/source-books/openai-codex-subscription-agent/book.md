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

## Decision

Codex is a first-class optional cloud/agent candidate for D4/D5 escalation in
the reference deployment profile. A research harness may test it, but production
Codex invocation, credential ownership, processor SPI and semantic output remain
unfrozen. Natural public artifacts require explicit egress policy and remain
unscored without independent truth.
