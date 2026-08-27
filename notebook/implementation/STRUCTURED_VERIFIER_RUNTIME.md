# Structured verifier production orchestration

State: **IMPLEMENTED CANDIDATE — EXACT CODEX/SQLITE + PHASE-D REPLAY + NATURAL MTSS CERTIFICATION PENDING**

Baseline authority:

```text
structured SQLite consumer merge: 51f21f98ed377da302309c8a5c46fd0a32f10bbf
frozen 0001 SHA256:             8d6f793e1c976221311bd73ffe03bdaa2907e9508e7c0f5fad59131a02dc9f96
SQLite target:                  3.53.4
SQLite source ID:               2026-07-24 19:02:57 bf7c7f30031888f4e796e429ab3978879485813aaca6f641c7b33e4e09459bcc
reference Codex CLI:            0.149.0
reference model:                gpt-5.6-terra / medium
```

## Purpose

Phase D proved that explicit intermediate derivations materially improve evidence retrieval and
source-backed verdicts, but did not justify copying Thucy's four-role runtime. This unit turns the
selected minimum decomposition into product behavior over the already-certified persistence/runtime:

```text
proposition + exact RepresentationTarget + Source Authority
-> one bounded planner model call
-> 0..6 proposed SQLite SELECT programs
-> one ordinary StructuredSQLite DerivationRun per proposed program
-> one bounded final-verifier model call over exact executed Derivation events
-> one durable VerificationRun
```

There is no hidden SQL execution and no second execution graph. Every proposed program that reaches
execution is an ordinary immutable `DerivationRun` with exact program/configuration/executor identity.

## One VerificationRun owns the model-backed attempt

The planner and finalizer are two stages of **one Verification attempt**, not separate civic actors
and not separate Derivation provenance. The durable `VerificationRun` therefore owns:

- proposition and bounded source scope;
- Source Authority;
- model/provider/execution profile;
- orchestration configuration identity;
- exact attempted/consumed Derivation references;
- final evidence/sufficiency/verdict or technical failure;
- non-secret egress authorization and prompt-payload byte count.

This avoids falsely attributing one shared planning call to every generated SQL Derivation. The SQL
DerivationRuns remain local deterministic computation and record no model egress.

`verification_run_egress.bytes_egressed` is defined here as the exact UTF-8 prompt payload bytes
handed to the external Codex executor across planner + finalizer calls. It is privacy-relevant
request material, not guessed transport framing/compression/token usage.

## Planner contract

The planner receives only:

- the exact proposition;
- bounded Source Authority records;
- a deterministic schema summary of the structured Representation;
- `max_queries` (`1..6`).

The schema summary exposes table/sheet/column structure but no cell values. The planner may return
zero queries when no useful bounded SQL exists. Every returned item has a local plan ID, purpose and
one proposed SQL string. The ID is not a canonical Canario vocabulary/record ID.

The planner does **not** answer the proposition and receives no web/shell/file/tool authority.
Every SQL string is still untrusted and must pass the existing hardened
`StructuredSQLiteDerivationBackend`; a rejected/failed query survives only as a technical attempted
Derivation.

## Final-verifier contract

The finalizer receives only:

- the proposition;
- the same Source Authority;
- exact executed Derivation events: query ID/purpose/SQL, outcome/error, exact program SHA-256,
  typed result when successful, lineage state and contributing source-target IDs.

It returns:

```text
supported | contradicted | insufficient_evidence
adequate | inadequate evidence sufficiency
explicit cited query IDs
bounded reason
abstention reason for insufficient_evidence
```

Canario then independently validates the model's citations. Unknown or failed query citations are
contract failures. `supported`/`contradicted` is rejected unless at least one cited successful
Derivation has `exact|partial` source lineage. A source-independent constant can be reported to the
model but cannot become civic evidence.

Only cited successful Derivations become `consumed`; every other invoked Derivation remains
`attempted`. Verification evidence items are source `RepresentationTarget`s recovered from consumed
lineage, never the SQL program/result itself.

## Replay and provenance identity

A `StructuredVerificationRequest` preallocates the VerificationRun ID and exactly `max_queries`
DerivationRun IDs. Persistence retry can therefore replay only an identical immutable attempt. If a
planner changes SQL while reusing the same request identity, the existing Derivation collision guard
fails closed.

Verification configuration identity binds at least:

- model adapter configuration;
- exact Codex version/model/reasoning profile;
- prompt and structured-output contracts;
- Codex call timeout/execution policy;
- hardened SQLite policy configuration;
- `max_queries`.

Egress authorization must exactly match the product request-template hash and endpoint profile
before any model invocation.

## Qualified Codex reference adapter

`CodexStructuredVerifierModel` is the reference adapter for certification only. It uses the official
Codex CLI subscription profile with:

```text
Codex CLI 0.149.0
gpt-5.6-terra
reasoning effort medium
keyring authentication
endpoint profile openai_codex_subscription
```

It requires a dedicated private non-default `CODEX_HOME`, forbids `auth.json`, `config.toml`, user
skills and detectable admin skills, strips API-key/arbitrary `CODEX_*` environment variables, uses a
scratch HOME/CWD, `--ephemeral`, `--ignore-user-config`, `--ignore-rules`, read-only sandbox, and
explicitly disables web/shell/plugins/apps/browser/computer-use/multi-agent/bundled-skill surfaces.

No provider API, metered fallback, hidden retry or Thucy runtime is part of this profile.

## Failure semantics

Planner/finalizer technical failure persists a failed VerificationRun when the attempt crossed the
canonical write boundary. Query/tool failure remains a technical Derivation fact. Neither becomes
`insufficient_evidence` automatically.

Conversely, zero useful queries or bounded Source Authority that cannot establish a claim may
legitimately produce completed `insufficient_evidence` with no Derivation evidence.

The receipt separately reports model invocation count and prompt bytes egressed. If a model call
completed but Canario rejects the returned semantic contract afterward, that completed call still
counts in provenance/usage.

## Certification proof

`prove_structured_verifier_runtime.py` has two lanes.

### Phase-D contract replay

It replays four already-certified Phase-D semantics through the production orchestrator:

```text
D1-SUPPORTED-LOOKUP             -> supported
D2-SUPPORTED-AGGREGATE          -> supported
D3-CONTRADICTED-AGGREGATE       -> contradicted
D8-INSUFFICIENT-GLOBAL-TOTAL    -> insufficient_evidence
```

The controlled structured source and Phase-D case builder are reused solely to recover the frozen
claim/Source-Authority semantics. This is not a new quality benchmark, does not rerun Thucy, and does
not compare model lanes.

### Natural MTSS proposition

The exact official MTSS workbook remains:

```text
XLSX SHA256: c98451ffdebc7976757a27ccd9a69a56061c16c37bd808b8d3398b3ffcb8608e
bytes: 26468
openpyxl: 3.1.5
structured Representation SHA256:
0357f16c36f458a525715f64856549d22f39947812184b7c21ae5221d0207b4c
sheet/extent: MTSS / 147 x 15
```

The production planner/verifier must support the bounded proposition that this retained workbook
projection's MTSS sheet contains exactly 147 represented rows, consume at least one real
source-backed SQL Derivation, and persist the completed VerificationRun.

## Certification interpretation

Passing these five propositions proves that the selected minimum Phase-D decomposition is executable
through production persistence and the qualified reference provider. It does **not** establish a
universal verifier-accuracy rate, certify arbitrary model-generated SQL, or authorize automatic Claim
promotion/publication. Broader semantic quality remains a separate measured/adjudicated concern.

## Non-goals

This unit does not authorize:

- schema changes or `0002`;
- generic `OperationRun` or recursive Derivation graphs;
- Thucy role classes/multi-agent runtime;
- web research or external tools during bounded structured verification;
- provider/API fallback or per-token billing;
- automatic Claim/EvidenceLink/Assessment promotion;
- treating failed queries as evidence;
- treating source-independent constants as evidence;
- claiming universal verification quality from four controlled cases plus one natural proposition.

## Candidate gate

Before publication require exact SQLite 3.53.4 and Codex 0.149.0/Terra-medium profiles, the four
Phase-D contract replay verdicts, the natural MTSS proof, exact prompt/egress provenance, focused +
full regressions, frozen-schema identity, compile/diff checks, and clean fresh-clone repetition.

## Exact-runtime certification repair: controlled proof custody source kind

The first local live-proof attempt blocked before any Codex planner/finalizer call because the
proof harness registered its controlled Phase-D fixture with `SourceRegistration.kind="proof"`.
`proof` is not part of the frozen Depósito source-kind vocabulary; the schema/DTO correctly
rejected it. The controlled fixture is now registered as `manual`, matching its actual custody
semantics and its existing `locator_kind="manual"`. The acquisition adapter may still identify
itself as `proof`; adapter identity is execution provenance and is not a Source kind.

A focused regression now executes `_capture_structured()` against a real schema-v1 database and
requires the persisted Source row to have `kind="manual"`. No schema, runtime semantics, model
policy, or natural MTSS authority changed. The blocked attempt performed zero semantic Codex calls.

## Live V2 failure and V3 diagnostic repair

The first semantic V2 campaign was consumed and stopped on the first Phase-D replay case:

```text
D1-SUPPORTED-LOOKUP -> VerificationReceipt verdict None
```

That observation proves the VerificationRun failed technically/contractually; a completed run cannot
have `verdict=None`. V2 could not classify the failure further because `verification_runs.error_code`
was persisted in SQLite but omitted from `VerificationReceipt`, and the proof deleted its disposable
DB before surfacing the durable code. The campaign is therefore recorded as consumed evidence, not
rerun or reinterpreted as an epistemic verdict.

V3 changes diagnostic/read behavior only:

- `VerificationReceipt` exposes the already-persisted `error_code`;
- `DerivationReceipt` exposes the already-persisted Derivation `error_code`;
- planner/provider/final contract failures persist bounded specific error codes instead of collapsing
  all causes into one generic stage code;
- the proof writes a partial JSON report before aborting, including outcome/verdict/error code,
  planned/consumed query IDs, Derivation outcomes and persistence/egress counts;
- the proof can run selected cases so certification may execute D1 alone first.

No prompt, model, SQLite policy, verdict rule, evidence rule, Source Authority semantics, schema or
MTSS identity is changed by this repair. A new semantic run is permitted only under a new explicit
authorization.

## Live V3 localization and V4 wire-schema repair

The single authorized V3 D1 diagnostic campaign localized the failure boundary precisely:

```text
planner: completed
planned query: sheet1_row1_values
SQLite Derivation: success
Derivation error: null
finalizer: provider failure
Verification error_code: codex_final_failed
consumed steps: 0
```

Because `codex_final_failed` is emitted only when the Codex CLI exits non-zero before Canario reads
`result.json`, this is not a final-decision/evidence contract rejection. Static comparison of the
planner/final `--output-schema` payloads against the official OpenAI Structured Outputs subset found
one material wire-only difference: `cited_query_ids` used `uniqueItems: true`. The documented
supported array constraints are `minItems` and `maxItems`; `uniqueItems` is not part of that subset.
`anyOf` is supported, so nullable `abstention_reason_code` is not removed.

V4 therefore makes the minimum transport repair:

- remove `uniqueItems` from the final wire schema;
- keep duplicate cited-query rejection in `StructuredFinalDecision.__post_init__`, so product semantics
  are unchanged;
- when Codex exits non-zero, inspect only a bounded stderr tail in memory and classify
  `invalid_json_schema` / `Invalid schema for response_format` as
  `codex_<role>_invalid_json_schema`;
- do not persist or expose raw stderr.

No planner/final prompt, model, SQLite policy, Source Authority rule, verdict rule, evidence rule,
schema migration or MTSS identity changes in V4.
