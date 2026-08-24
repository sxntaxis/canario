# Cloud execution and OpenAI-compatible transport

Cloud capacity is an **execution venue**, not a separate semantic processor family. ActaKit's processing
rungs describe what capability is needed; deployment policy chooses where a qualified implementation runs.

## Provider classes in the current research horizon

```text
subscription-backed agent executor
  -> official Codex CLI + ChatGPT subscription (primary reference path)

first-party frontier API
  -> OpenAI API candidate (optional)

specialized cloud Document AI
  -> Mistral OCR candidate

OpenAI-compatible endpoint
  -> transport escape hatch for local/self-hosted/other providers
```

The last category is intentionally not called a standard. vLLM demonstrates that the OpenAI client shape
(`base_url`, `api_key`, model, OpenAI-style endpoints) is useful and widespread, while also documenting
endpoint/parameter differences. A future provider boundary must declare/probe capabilities before use.

## Required capability dimensions

A provider cannot satisfy a rung merely because it accepts an OpenAI-style request. The host must know,
at minimum, which of the following are supported for the selected model/endpoint:

- image input;
- multi-page/document input strategy;
- structured/schema-constrained output;
- audio/transcription input when that ladder activates;
- input-size/page/image limits;
- deterministic/replay controls where meaningful;
- usage/cost reporting where available;
- provider/model identity suitable for ProcessRun provenance.

Provider-specific extras stay behind the provider implementation and must not leak into the generic
Representation Processor contract.

## Credentials

Credential values are **host secrets**. They are never civic evidence and are never persisted in:

- SQLite;
- ProcessRun configuration/evidence payloads;
- benchmark fixtures/results;
- logs or exception text;
- derivative Representations.

A later implementation may resolve a non-secret credential slot from environment variables, an OS secret
service/keyring or deployment secret manager. The research package does not freeze that mechanism yet.
The Codex path is different: the official CLI owns ChatGPT sign-in and refresh; ActaKit must invoke it as a
bounded executor without taking custody of that credential material.

## Egress policy

Cloud execution requires an explicit source/deployment policy decision. Provenance records non-secret:

- provider and exact model identity;
- endpoint profile/provider class;
- request/prompt/schema template version;
- input Representation/page/block scope;
- that bytes/pages left the host and the measured amount where practical;
- reported usage/cost inputs;
- the retention/data-control profile the deployment asserted for that run.

Do not infer `zero retention` from the fact that a provider is accessed through an API. Current OpenAI
documentation distinguishes default API handling from account/endpoint-specific controls such as ZDR.

## Venue policy

ActaKit should be deterministic-first, not dogmatically local-ML-first:

```text
D0-D3 local succeeds
  -> ACCEPT

D4/D5 required
  -> if egress forbidden: best qualified local backend
  -> if local hardware unsuitable and egress allowed: qualified cloud backend
  -> if both viable: benchmarked quality/cost/latency policy chooses
  -> if neither qualified: QUARANTINE_REVIEW
```

For the reference deployment, a modest laptop may use subscription-backed Codex without a separate ActaKit
API key or per-token API account. This does not imply that the subscription is free or unlimited, and it
does not make cloud mandatory for installations that need offline/no-egress operation.
