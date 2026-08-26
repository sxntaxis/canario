# Structured Verifier Fit Bench — Phase D results

State: **LOCALLY CERTIFIED — DECOMPOSITION VALUE PROVEN**

Decision:

```text
DECOMPOSITION_VALUE_PROVEN__DESIGN_MINIMUM_CANARIO_DECOMPOSITION
```

This decision is bounded to the frozen eight-case Phase-D campaign. It is **not** a claim that
native Thucy is production-ready, that the four-role topology should be copied, or that either
bench lane establishes universal verifier quality.

## Measurement identity

```text
parent: 0f9a71e5acb0f093469571d59c896eab0c03c4c2
candidate v3 archive: 8f0e182e075263962093151abe5eae4ff70a4d885aae8d69e72b8afd7f0a2a32
candidate v3 manifest: d3454e3e9810ebe19a46d5eee14b7aa7774781136215acca437533b879b45a27
representation: 55bf57e4b6a788cd962a8485ab2c9df8987cb2a3d1e42faff56bf88283d16d5d
projection: 1fc5e653ea125d326db297b83b464c90a55dccdf67f0932b48a1bc38af1768f5
query corpus: b1e6c9a9e359f5e7b2ccf41f7652071e94c3d52b7c955d2e88221d7b8ba9b251
planner handoff: a856e4db82c6ae327c808264806d231e2a4cc8339e627da4f622d852cc4e210c
phase-d cases: e3457df7f696358edfdac129581c3d16bcd53475b9229585088d589eaf39516a
provider probe: 5a944033daf7961bc236f4f331be3b6cd39b10ced028f9f70d8b71cbb8cf01c8
paired run: 590a4c8e0e1123a71efe2d0c2f0468ff9771d1c6f15efa661991a806dbe60028
raw measurement archive: 9d44a714f94b64556632bfc0fb5a165080ec283eaba00200336ac11224352f2e
raw measurement manifest: d5a3feffc6206978111637f66d42e8388138fcbd914de97f003da36fc1e39f42
```

The authoritative absolute case rows and aggregates remain in the SHA-bound external
`score.json` and `comparison.json` measurement handoff. They are intentionally not committed as
raw runtime output. This closure records the decision-relevant deltas that were returned in the
measurement report and does not reconstruct missing aggregate columns from arithmetic guesses.

## Execution integrity

```text
verifier focused: 20 passed
structured reasoning focused: 27 passed, 2 skipped
LECTOR focused: 39 passed
full suite: 257 passed, 2 skipped, 2 subtests passed
compileall: PASS
git diff --check: PASS
paired campaign status: completed
worker execution failures: 0
semantic retries: 0
simple Codex invocations: 16
Thucy-adapted Codex invocations including shared setup: 26
paired Codex invocations: 42
provider-probe invocations: 1
total current-campaign Codex invocations: 43
API key used: NO
per-token API billing: NO
automatic metered fallback: NO
```

The historical v2 structural failure remains separate: one provider probe, zero setup/semantic
invocations, zero prompt bytes and zero semantic retries. It is not folded into the scored v3
campaign.

## Decision-relevant paired deltas

Thucy-adapted minus simple:

```json
{
  "verdict_accuracy": 0.0,
  "evidence_retrieval_recall": 0.3333333333333333,
  "evidence_backed_verdict_rate": 0.25,
  "abstention_precision": -0.33333333333333337,
  "abstention_recall": 0.0,
  "subscription_codex_invocations": 10,
  "prompt_bytes_egressed": 78009,
  "duration_ms": 104036.601
}
```

## Interpretation

The decomposition produced **no verdict-accuracy gain** in this bounded campaign. It did,
however, produce a large improvement in the two metrics that test whether a verifier can reopen
and causally ground the evidence behind its answer:

```text
+0.333333 evidence-retrieval recall
+0.25 evidence-backed verdict rate
```

Those are material verifier-quality gains for Canario because a correct label without reopenable,
causally dependent evidence is not sufficient product behavior. The gain is not free:

```text
+10 Codex CLI invocations
+78,009 prompt bytes egressed
+104,036.601 ms wall-clock duration
-0.333333 abstention precision
```

Therefore the measured result rejects both extremes:

```text
SIMPLE_VERIFIER_SELECTED                              -> rejected for this gate
COPY / VENDOR THUCY FOUR-ROLE RUNTIME                -> not authorized
```

The data supports a **minimum Canario-native decomposition**, not a Thucy clone.

## Minimum Canario decomposition selected

The durable architecture should preserve four conceptual facts while minimizing model topology:

```text
1. bounded Source Authority + projection context
2. explicit Derivation planning/execution over canonical evidence scopes
3. exact DerivationRun result/evidence lineage
4. one Verification execution that consumes those derivations and emits
   verdict + explicit evidence sufficiency + abstention reason
```

Important constraints:

- no `Data Expert`, `Schema Expert`, `SQL Expert`, or `Lead Verifier` product classes are frozen;
- no multi-agent framework is required;
- projection/schema context should be deterministic or cached where possible rather than paid
  model work merely because the benchmark challenger used model roles;
- model-planned SQL remains untrusted and runs only through the hardened analytical executor;
- Verification must reference the exact DerivationRuns it used instead of hiding queries/results
  inside an opaque model trace;
- explicit sufficiency remains a Canario contract even though upstream Thucy lacks that field;
- execution failure remains separate from epistemic `insufficient_evidence`;
- Verification never mutates Claim lifecycle; optional durable `Assessment` remains a separate,
  attributable policy action;
- native Thucy remains non-vendored/non-executed and the upstream license metadata conflict remains
  recorded;
- future OpenAI API, OpenRouter/OpenAI-compatible and other provider profiles remain allowed but
  deferred. Codex subscription is a reference execution profile, not verification semantics.

## What the benchmark does not prove

This eight-case campaign does not identify which individual Thucy stage caused the evidence gain.
It therefore does **not** justify reproducing all four stages or adding four model calls/agents as
architecture. It also does not certify production accuracy across heterogeneous civic media.

The correct transfer is the smallest one directly supported by the result: **make analytical
derivations explicit and inspectable before the final verification judgment** and retain enough
bounded context for evidence retrieval. Further decomposition requires a new bounded benchmark,
not intuition.

## Schema/persistence gate

Phase D closes the conceptual relationship needed by G3:

```text
VerificationRun
  -> ordered references to zero..N DerivationRuns actually used
  -> bounded proposition + Source Authority identity
  -> execution outcome
  -> verdict
  -> evidence set
  -> explicit sufficiency
  -> abstention reason when applicable
  -> model/process/configuration provenance
```

This results document still does **not** modify or authorize `0001` by itself. The immediate next
design unit is one reconciliation of `DerivationRun`, `VerificationRun`, Claim-origin provenance,
EvidenceLink semantics and optional Assessment promotion. Because Canario is pre-release, the
resulting accepted schema should then rebaseline `0001` once rather than accumulate speculative
migrations.

## Closure token

```text
CANARIO_STRUCTURED_VERIFIER_PHASE_D_DESIGN_INTERPRETATION_PASS__MINIMUM_DECOMPOSITION_SELECTED
```
