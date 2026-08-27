# Lector production-readiness Research Interrupt

State: resolved_to_fit_bench
Kind: working research interrupt
Severity: architecture_or_reuse_threat
Opened: 2026-08-27

## Observation

The first attempted end-to-end vertical showed that Canario can acquire, retain and process real civic material; it also has LECTOR-001's bounded semantic extraction boundary and REVIEW-001/002 supervision/correction machinery. However, no production broad-Claim SemanticExtractor has been selected and certified. The previous LECTOR-002 semantic campaign is explicitly superseded and requires re-scope.

A disposable vertical experiment immediately prototyped a Codex paged-text extractor. That prototype is quarantined outside repository authority and must not be treated as a selected design.

## Why this interrupts implementation

Lector quality is product-defining. A weak extraction strategy can silently produce an apparently usable Fichero while losing recall, attribution, conditions/exceptions, cross-page meaning, or evidence fidelity. A green vertical that merely wires one model call through the contracts would therefore optimize for demo completion rather than Canario's core epistemic job.

The surprise threatens:

- benchmark validity: LECTOR-002 replacement gold/thresholds are not frozen;
- mechanism choice: one-pass whole-document Codex has not been compared against alternatives;
- scope framing: `broad claims` needs explicit completeness/atomicity boundaries rather than an editorial prompt;
- architecture/reuse: mature information-extraction / OpenIE / event/proposition extraction / document-IE mechanisms and failure evidence have not yet been re-audited for this exact production question.

## Required Discovery / research before implementation

The next authorized Lector Work should separate at least:

1. **Product requirements** — what a useful Fichero must recover and what may remain machine-only/unknown.
2. **Quality dimensions** — broad recall/completeness, atomicity, attribution, conditions/exceptions/cross-references, numeric/date fidelity, evidence sufficiency/reopenability, relation quality, hallucination/unsupported rate, duplicate rate, abstention/failure behavior.
3. **Representation/modality boundaries** — paged text is one case; typed tables/timed media remain distinct.
4. **Mechanism landscape** — deterministic/rule extraction, classic IE/OpenIE/event extraction, single-pass LLM, chunked/hierarchical/multi-pass coverage, model-assisted retrieval/decomposition, and hybrid strategies.
5. **Prior art / reuse gate** — identify mature implementations, benchmarks, papers, failure literature and licensing/operational implications before BUILD.
6. **Benchmark redesign** — re-scope LECTOR-002 with frozen human-approved references before tested extractor output is inspected; capability-based, heterogeneous and explicitly non-universal.
7. **Decision** — ADOPT / ADAPT / BUILD with rationale, limitations and reopen conditions.
8. **Proof design** — freeze proposition-scoped semantic gates before implementation candidate measurement.

## Known useful observations from the quarantined vertical

These are hypotheses to re-evaluate, not accepted changes:

- initial active Claim creation appears not to populate `claim_fts` despite the documented current-active projection invariant;
- Poppler whole-text offsets may permit deterministic page-ordinal projection for evidence display without changing evidence authority.

## Resume condition

The affected front may resume implementation only after the Discovery/Deep Research/Synthesis/Decision chain produces accepted Lector production design authority and explicitly activated Work.

## Resolution — 2026-08-27

The required Discovery/Deep Research/Synthesis chain completed as the production-readiness research package researched through 2026-08-27. Its decision is intentionally **not** a production-extractor selection:

```text
BROAD_LECTOR_MECHANISM_NOT_SELECTED
RUN_CANARIO_NATIVE_LECTOR_FIT_BENCH
```

The research package, adversarial review, fit-bench design and fixture strategy are preserved under `notebook/research/lector/production-readiness/`. The owner approved and activated `docs/work/20260827-lector-production-fit-bench.md` after governance merge.

This resolves the Research Interrupt only far enough to authorize the benchmark/research Work. Production broad-Lector implementation remains blocked until that Work exits with an explicit lane-selection decision and a later separately authorized implementation Work. The quarantined Phase-6/WP7 extractor remains without authority.
