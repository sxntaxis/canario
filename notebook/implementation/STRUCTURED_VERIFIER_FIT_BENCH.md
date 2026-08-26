# Structured Verifier Fit Bench — Phase D

State: **MEASURED — MINIMUM CANARIO DECOMPOSITION SELECTED; FINAL LOCAL CERTIFICATION PENDING**

Authority chain:

```text
fact-verification SOTA research: 7e7fd85be5ac607fcb02ccb68b97b5e17f8fd9d6
architecture reconciliation:     516ddd613bf58ef412d59bf4600652c8045c9c6b
structured reasoning foundation: 0f9a71e5acb0f093469571d59c896eab0c03c4c2
```

This unit closes research gap G2 as far as the available **subscription-backed execution
venue** can honestly support. It compares a deliberately simple Canario verifier loop against
the architectural decomposition published by Thucy, while preserving the exact frozen
projection, Source Authority, model, and SQLite query boundary.

It does **not** authorize production verifier code, Assessment writes, schema changes,
model dependencies, semantic gold regeneration, or canonical cutover.

## Execution-profile and cost policy

Phase D needs one fair paired campaign now, while Canario's transport architecture must remain
provider-independent. The current **reference execution profile** is therefore:

```text
current campaign transport: official Codex CLI + ChatGPT subscription
OPENAI_API_KEY required: NO
per-token API billing in this campaign: NO
automatic OpenAI API/OpenRouter fallback: NO
```

This is sequencing, not a permanent prohibition. Future execution profiles may include:

```text
OpenAI API
OpenRouter / OpenAI-compatible APIs
other explicitly qualified providers
```

Those transports are architecturally allowed but **deferred**. They must be implemented,
benchmarked and authorized as explicit profiles later; the current campaign must never start a
metered provider implicitly when Codex/subscription execution is unavailable. Provider transport
does not define verification semantics or Source Authority.

The current candidate uses the already certified Codex subscription pattern:

```text
official codex CLI
+ dedicated non-default CODEX_HOME
+ keyring authentication
+ no auth.json
+ no ambient config.toml
+ no user-installed skills
+ strict/ephemeral execution
+ structured output schema
```

Default model for the paired campaign:

```text
gpt-5.6-terra
reasoning effort: medium
```

The local provider probe must prove that exact model is available through the qualified
subscription profile. If the subscription does not expose it, that is an environment blocker for
**this profile**; the agent may not silently substitute a metered API or another model. A future
explicit API-profile campaign may test the same semantic contracts separately.

The campaign records **Codex CLI invocation count**, prompt bytes egressed, structured-output
bytes and wall-clock time. It does not call that count a provider/model-request count: Codex's
internal provider request topology is not exposed by the certified CLI contract. Token usage is
likewise treated as unavailable unless Codex exposes it. No synthetic dollar estimate is invented
for subscription use. With eight completed cases, the expected upper bound is 43 Codex CLI
invocations total: 1 provider probe + 2 shared Thucy setup + 16 simple + 24 Thucy-adapted, with
zero semantic retries.

## Closed prerequisites

Checkpoint `0f9a71e5...` proved:

- deterministic typed projection identity and exact source lineage;
- hardened SQLite 3.53.4 execution;
- sandboxed DuckDB 1.5.5 execution;
- Esparza SQLite/DuckDB agreement on 9/9 executable cases;
- INEC SQLite/DuckDB agreement on 7/7 scale cases;
- SciTab representability;
- `FIRST_CLASS_DERIVATION_REQUIRED` for G3.

SQLite remains the architectural analytical baseline. DuckDB demonstrated no material
required advantage and remains outside product dependencies.

## Question

> Given the same claim, Source Authority, deterministic projection, hardened SQLite
> executor, subscription provider, exact model and semantic-attempt policy, does a simple
> Canario planner/verifier perform well enough, or does Thucy's multi-role decomposition add
> material verification value that justifies additional complexity?

This is a fit comparison, not an adoption contest.

## Why native Thucy is not executed

Exact upstream source authority:

```text
repository: https://github.com/thucy-ai/thucy
commit: feaecdb5bd876a09db507ed31e93dc9393940689
agents.py blob: e7ca065a05dad6fa8992c87934c8874834f9b4bd
LICENSE blob: 33c7f9f5e7e30d62c9a33f69c137ecaf9172f03a
pyproject.toml blob: cb8866f911326d07b1af83239f3b3800c4f2be9e
```

Native Thucy requires `openai-agents`, an OpenAI API execution path and Google MCP Toolbox.
That is not the selected path for this campaign because it would require a separately funded and qualified metered runtime.
The native project also still has a license metadata collision: `LICENSE` contains MIT while
`pyproject.toml` says Apache-2.0. Vendoring/forking remains blocked.

Phase D therefore does **not** claim to run native Thucy. It runs:

```text
thucy_bounded_codex_runtime_adapted
```

The adapter:

- verifies the exact external checkout and blobs;
- parses the four upstream role prompts directly from `thucy/agents.py` using Python AST;
- does not import or execute the Thucy package;
- does not copy those prompts into Canario's repository;
- preserves the published Data Expert -> Schema Expert -> SQL Expert -> Lead Verifier
  decomposition;
- executes every role through the same subscription-backed Codex CLI/model used by the
  simple baseline;
- replaces native Toolbox/OpenAI-Agent runtime mechanics with a bounded deterministic
  orchestrator over Canario's hardened SQLite projection.

This is intentionally reported as a **runtime/protocol adaptation**, not native Thucy and not
mere transport adaptation.

If the adapted decomposition fails to improve materially on the simple baseline, Canario has
no reason to pay the complexity cost of reproducing Thucy's native runtime. If it materially
wins, that establishes evidence for decomposition value, not permission to vendor Thucy.

## Systems

### A — `simple_codex`

Per case:

```text
Codex call 1: bounded SQL planner
-> zero..6 proposed SELECT statements
-> hardened SQLite executes them
Codex call 2: final verifier
-> supported | contradicted | insufficient_evidence
-> explicit adequate | inadequate evidence-sufficiency axis
```

The planner sees deterministic schema metadata, not gold SQL. The final model sees only the
actual execution events.

### B — `thucy_bounded_codex_runtime_adapted`

One shared setup per frozen projection:

```text
Data Expert prompt -> one bounded DataReport
Schema Expert prompt -> one bounded SchemaQueryAnswer
```

This setup is projection-scoped rather than case-scoped: it consumes the frozen projection and
campaign Source Authority, and deliberately has no case prompt. Case-prompt validation begins only
for the per-case simple or Thucy-adapted execution paths.

Per case:

```text
SQL Expert prompt: plan SQL
-> hardened SQLite executes zero..6 statements
SQL Expert prompt: synthesize NLQueryAnswer from actual results
Lead Verifier prompt: consume bounded Data/Schema/SQL reports
-> original five Thucy verdict labels
```

All four upstream prompts are exact literals extracted from the exact external source. Small
wrapper text only explains the benchmark runtime/transport contract and supplies deterministic
tool outputs.

Thucy's explicit prompt instruction to treat accessible data as reliable/authoritative is
**not patched**. The lead receives the same exact per-case Source Authority scope as the simple
system. Overclaiming caused by the upstream authority assumption is therefore measurable.

## Model isolation and egress

Codex itself receives **no database path and no shell/database tool**.

Each Codex invocation is configured with:

```text
--strict-config
--ephemeral
--ignore-user-config
--ignore-rules
--sandbox read-only
--output-schema <schema>
--output-last-message <file>
web search disabled
shell/unified exec disabled
plugins/apps/browser/computer-use disabled
multi-agent disabled
bundled skills disabled
```

The model only proposes SQL as schema-constrained text. The Python harness then executes that
text through the certified `execute_sqlite()` boundary. Query rejection or timeout is recorded
as an execution event; it is never converted into epistemic `insufficient_evidence`.

The worker environment deliberately forwards only locale plus keyring/TLS host plumbing. It
never forwards `OPENAI_API_KEY` or arbitrary `CODEX_*` environment variables.

The exact egress measure for this unit is prompt UTF-8 bytes handed to Codex CLI. Credentials
are never part of those prompts or results.

## Provider gate

Before scored cases, local certification must prove:

1. qualified Codex CLI version;
2. dedicated private keyring-backed CODEX_HOME;
3. exact `gpt-5.6-terra` model call succeeds through subscription auth;
4. JSON-Schema-constrained output succeeds;
5. shell/web/skills remain disabled by command construction;
6. no API key is required or forwarded;
7. result identifies `billing_mode=chatgpt_subscription` and
   `per_token_api_billing=false`.

`run-paired` requires the exact passing provider-probe JSON as an input and rejects a different
model/reasoning/profile, so this gate is machine-enforced rather than only procedural. No scored
campaign starts if it fails.

## Frozen corpus

The corpus is deterministically derived from the certified Esparza query corpus and hidden
independent oracle. Eight cases are required:

```text
D1 supported explicit lookup
D2 supported aggregation
D3 contradicted aggregation
D4 supported cross-sheet relation
D5 contradicted top-k proposition
D6 supported absence inside a complete retained workbook scope
D7 insufficient global-absence proposition
D8 insufficient global-total proposition despite valid local arithmetic
```

Expected labels, evidence obligations, exact locators and gold deterministic results never
cross the model boundary.

Contradictions are mechanically perturbed from the independent oracle. Insufficiency cases
change proposition scope/authority rather than source bytes.

## Evidence obligations

Phase D intentionally does not require a verifier to discover the same SQL string as the
frozen deterministic corpus.

Evidence is scored by **semantic result obligation**:

- exact-result match where exact shape is inherent;
- expected scalar contained in an actual successful result;
- expected row/value sets contained in actual successful result rows for cross-sheet/top-k
  claims.

This fixes a critical benchmarking distinction:

```text
retrieved the needed evidence
!=
used the exact gold SQL / exact gold column layout
```

Every evidence-bearing SQL statement still must have actually executed successfully against
the exact projection. Unsupported SQL citations or unsupported query IDs are separate
failures.

### Hidden causal-evidence check

Correct output alone is insufficient. An SQL statement could echo a number from the claim, for
example `SELECT 123 AS total`, and accidentally satisfy the visible result obligation while not
actually depending on source evidence.

For every evidence-required case, the hidden oracle therefore carries one or more deterministic,
type-compatible source-cell mutations. After the original successful SQL has satisfied the
evidence obligation, the scorer re-executes **the same SQL** over an in-memory counterfactual
projection whose essential source evidence was changed. The SQL counts as causally grounded only
when the original hidden obligation no longer remains satisfied.

```text
correct verdict
!= evidence retrieved
!= causal dependence on source evidence
```

The counterfactual projection and mutations are never model-visible and never become canonical
evidence. They are benchmark-only anti-cheating probes.

## Sufficiency and failures

Canario simple output has an explicit sufficiency axis.

Native Thucy's published `VerificationAnswer` does not. The adapted Thucy lane therefore
keeps:

```text
explicit_sufficiency = false
```

rather than inventing a new Thucy field. `NOT ENOUGH INFO` remains a verdict and is scored in
abstention metrics, but it is not rewritten into an explicit sufficiency record.

SQL/tool rejection is counted independently from abstention. A correct `NOT ENOUGH INFO`
answer after a rejected query can still be semantically correct while remaining
`execution_clean=false`.

## Scoring

Per system:

- completion/execution-clean rate;
- verdict accuracy;
- evidence retrieval recall;
- evidence-backed verdict rate;
- unsupported SQL citations/query IDs;
- tool rejection/execution-failure count;
- abstention precision/recall;
- explicit sufficiency availability/correctness;
- subscription Codex-invocation count;
- prompt bytes egressed;
- structured-output bytes;
- wall-clock duration.

No API dollar cost or token-cost estimate is fabricated.

## Semantic retry policy

Exactly one scored semantic attempt exists per system/case.

```text
semantic retry: NO
"retry until green": NO
```

A Codex/worker execution failure remains an execution failure. The harness does not make a
second semantic attempt to improve the answer.

## Decision gate

The benchmark itself does not choose architecture. It writes raw paired runs, scores and
deltas ending in:

```text
MEASUREMENT_ONLY__DESIGN_AGENT_MUST_INTERPRET
```

The measured decision is:

```text
DECOMPOSITION_VALUE_PROVEN__DESIGN_MINIMUM_CANARIO_DECOMPOSITION
```

The bounded eight-case campaign kept verdict accuracy unchanged while the Thucy-adapted lane
improved evidence-retrieval recall by `0.3333333333333333` and evidence-backed verdict rate by
`0.25`. It also reduced abstention precision by `0.33333333333333337` and added 10 Codex CLI
invocations, 78,009 prompt bytes and 104,036.601 ms. The evidence gain is material to Canario's
verification contract, but the burden and mixed abstention result do not justify reproducing
Thucy's four-role runtime. See `structured-verifier-fit-bench/RESULTS.md`.

The selected transfer is the minimum Canario-native decomposition: bounded context, explicit
Derivation planning/execution with exact lineage, and a final Verification judgment that
references those DerivationRuns and retains explicit sufficiency. No Thucy role classes,
multi-agent framework, vendoring, production model dependency or schema change are authorized by
this fit bench.

The measurement candidate was deliberately **not committed** before interpretation. This authored
closure has passed its separate local certification pass; machine execution/testing remain local.

## Production boundary

This unit must not modify:

```text
canario/
MIGRATION_0001_SPEC.sql
canario/persistence/migrations/0001.sql
requirements.txt / product dependency manifests
```

No schema change is authorized.

## Relation to Derivation

G3 is already closed:

```text
FIRST_CLASS_DERIVATION_REQUIRED
```

`DERIVATION_CONTRACT_CANDIDATE.md` records the minimum conceptual record. Phase D now requires
a future Verification execution to reference the exact ordered DerivationRuns whose results were
actually used. Persistence remains blocked only for the one Derivation/Verification/Claim/Evidence
reconciliation design pass; this bench itself does not edit `0001`.
