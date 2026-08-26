---
id: CANARIO-BOOK-TSVER-001
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

# TSVer

## Question

How should Canario represent and benchmark temporal/numerical evidence when claims depend on time windows?

## Evidence horizon

This Book uses the primary paper and, where relevant, the current public
implementation/license metadata available through 2026-08-25. It is a bounded
architecture/reuse audit, not a reproduction of all experiments.

## Claim ledger synopsis

- **TSV-C001:** Each claim is annotated with relevant time frames across pertinent time series, a verdict, and justification. **Canario:** Treat temporal windows as first-class evidence scope rather than flattening time series into text.
- **TSV-C002:** The dataset uses real-world claims from 41 fact-checking organizations and reports substantial but imperfect annotator agreement. **Canario:** Human/reference uncertainty remains measurable and should not be hidden.
- **TSV-C003:** State-of-the-art reasoning models remain challenged on verdict and justification quality. **Canario:** Temporal numerical reasoning deserves its own capability rather than being assumed by generic structured-values extraction.
- **TSV-C004:** Repository is CC BY-SA 4.0. **Canario:** Prefer external benchmark/reference unless ShareAlike implications are deliberately accepted.

## Bounded transfer

**BENCHMARK future temporal/numerical verification and ADAPT explicit time-window evidence semantics.**

## Do not import

Do not add a time-series subsystem merely because this benchmark exists; add it when a Canario source/derived analysis actually requires it.

## Residual risk / unresolved question

What canonical temporal evidence locator should bridge a typed dataset Representation and a derived Claim without duplicating the source?

## Closure verdict

Research-complete for this synthesis gate. This Book is evidence, not
implementation authorization.
