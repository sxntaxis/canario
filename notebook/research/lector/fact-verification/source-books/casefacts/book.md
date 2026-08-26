---
id: CANARIO-BOOK-CASEFACTS-001
type: research-source-book
state: research-complete-for-synthesis
authority: evidence
created: 2026-08-25
updated: 2026-08-25
researched_through: 2026-08-25
canario_baseline: a1d212c84830b3a0558dd4d1d9354cf10ac7a362
source_ledger: sources.csv
claim_ledger: claims.csv
---

# CaseFacts

## Question

What does legal claim verification teach Canario about source authority, temporal validity, and retrieval quality?

## Evidence horizon

This Book uses the primary paper and, where relevant, the current public
implementation/license metadata available through 2026-08-25. It is a bounded
architecture/reuse audit, not a reproduction of all experiments.

## Claim ledger synopsis

- **CSF-C001:** CaseFacts models legal claims as Supported, Refuted, or Overruled and makes temporal precedent validity part of the task. **Canario:** Source authority can change over time; verification must bind to evidence state/time rather than timeless truth.
- **CSF-C002:** Unrestricted web search degraded performance because models retrieved noisy or non-authoritative precedents. **Canario:** Strongly supports Canario's Source Authority model and bounded retrieval over indiscriminate web search.
- **CSF-C003:** The task requires mapping colloquial claims to formal authoritative jurisprudence. **Canario:** Semantic proximity is not enough; retrieval must prioritize authoritative evidence appropriate to the claim.
- **CSF-C004:** The paper finds a gap between verdict prediction and evidence-grounded verification. **Canario:** Do not reward a correct-looking verdict without adequate authoritative evidence.

## Bounded transfer

**ADOPT the principle that authority and temporal validity constrain retrieval and verification. BENCHMARK authority-aware retrieval with civic counterexamples before any generic web-search verifier.**

## Do not import

Do not import U.S.-legal ontology or precedent mechanics into the generic civic core.

## Residual risk / unresolved question

How should Source Authority participate in verifier tool selection and evidence-sufficiency scoring without becoming a brittle universal hierarchy?

## Closure verdict

Research-complete for this synthesis gate. This Book is evidence, not
implementation authorization.
