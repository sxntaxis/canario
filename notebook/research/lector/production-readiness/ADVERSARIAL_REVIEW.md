---
id: CANARIO-LECTOR-PRODUCTION-READINESS-ADVERSARIAL-REVIEW-001
type: adversarial-research-review
state: complete
authority: evidence
researched_through: 2026-08-27
---

# Adversarial review of the Lector readiness synthesis

## Purpose

Try to falsify the emerging `A4` contextual multi-pass hypothesis before it becomes a design decision.

## Where the evidence is weaker than it first appears

### 1. Most claim-extraction literature is not civic-source extraction

Claimify, Molecular Facts, decomposition work, and several factuality benchmarks operate on
LLM-generated answers or fact-checking pipelines. They establish real mechanisms and failure modes,
but do **not** establish that the same orchestration wins on Spanish public records.

**Consequence:** transfer mechanisms, not headline scores.

### 2. Long-document decomposition evidence does not prove dynamic agents are needed

DocETL shows large gains from decomposition/optimization on its tasks. It does not prove that Canario
needs agentic pipeline rewriting. Fixed, inspectable contextual passes may be enough.

**Consequence:** A5 remains a challenger only. Complexity must earn itself against A0–A4.

### 3. Exact evidence grounding is necessary but not semantic proof

A generated Claim can cite an exact quote and still overgeneralize it, drop an exception, change
attribution, or import world knowledge.

**Consequence:** evidence reopening is a deterministic gate; source entailment and qualifier
preservation remain semantic gates.

### 4. “Atomic” is not a universally desirable target

Over-decomposition can produce context-poor facts that are technically small but hard to interpret,
retrieve, correct, or verify independently.

**Consequence:** use self-sufficient minimality, not minimum token count or one-relation-per-Claim.

### 5. Coverage has a domain-definition problem

Canario wants broad later recoverability, but not every ceremonial sentence or boilerplate fragment.
`civic_coverage` is meaningless until the reference protocol defines a **material civic assertion**
without smuggling in today's editorial importance.

**Consequence:** reference annotation needs explicit inclusion/exclusion examples and adjudication.

### 6. Spanish/domain transfer is a genuine uncertainty

External English results cannot certify Costa Rican administrative/legal prose. Spanish evidence found
so far is mostly narrow IE or adjacent tasks.

**Consequence:** Spanish institutional fixtures are hard gates, not decorative diversity.

### 7. Repeated passes may merely repeat the same blind spots

LangExtract-style repeated identical passes can increase stochastic recall, but may waste calls if the
model systematically ignores the same material.

**Consequence:** compare identical repetition (A2) against explicit coverage-directed repair (A4).

### 8. A broad output schema can itself cause quality loss

The first production fit bench should not ask the model to solve Claim extraction, entity resolution,
relations, document classification, assessment, and derived reasoning in one response.

**Consequence:** benchmark Claims + evidence first; add semantic enrichments only in separate measured
lanes after Claim quality is established.

## Anti-overfitting fixture split

### Development/reference-design fixtures

These may shape prompts, orchestration, and reference machinery:

- Acta 161;
- existing INCOP correspondence;
- one Spanish normative/contractual source;
- one report/audit/technical source;
- separate typed table/media capability fixtures.

### Blinded natural holdouts

A holdout must not be inspected to tune prompts, thresholds, segmentation, or orchestration.

- **Acta 160** is reserved as the first end-to-end natural holdout because it was selected by the
  interrupted vertical but has not been used to tune the Lector.
- At least one additional non-minutes Spanish civic holdout should be selected/frozen before the
  production candidate is finalized.

If a holdout reveals a new material failure, the correct response is:

```text
candidate FAIL
-> add failure mode to research/benchmark
-> revise design
-> select a NEW holdout
```

Do not tune on a failed holdout and then report the same source as independent certification.

## What the research can justify now

It can justify:

```text
BROAD_LECTOR_MECHANISM_NOT_SELECTED
FIT_BENCH_REQUIRED
```

It cannot justify:

```text
A4_SELECTED
CODEX_SELECTED
WHOLE_DOCUMENT_REJECTED_FOR_ALL_CASES
CHUNKING_REQUIRED_FOR_ALL_MODALITIES
PRODUCTION_READY
```

## Exit criterion

The research package is adequate for a benchmark-design Work when:

- all major transfer claims expose their source-domain limitations;
- A0–A5 are treated as hypotheses, not feature requirements;
- development and blinded holdout evidence are separate;
- source fidelity, Spanish language, coverage, qualifier retention, ambiguity, and cross-unit context
  each have explicit counterexamples;
- the selection rule still permits the simplest lane to win.
