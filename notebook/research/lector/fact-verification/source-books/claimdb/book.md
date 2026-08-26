---
id: CANARIO-BOOK-CLAIMDB-001
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

# ClaimDB

## Question

What does large-scale structured-data fact verification imply for Canario's benchmark and reasoning architecture?

## Evidence horizon

This Book uses the primary paper and, where relevant, the current public
implementation/license metadata available through 2026-08-25. It is a bounded
architecture/reuse audit, not a reproduction of all experiments.

## Claim ledger synopsis

- **CDB-C001:** ClaimDB pairs claims with databases averaging 11.3 tables and about 4.6 million records, making naive in-context reading infeasible. **Canario:** Change structured verification from row-reading toward executable reasoning.
- **CDB-C002:** The benchmark intentionally selects compositional questions involving aggregation, ordering/superlatives, window functions, or joins across at least three tables. **Canario:** Do not treat single-cell or random-row lookup as sufficient evidence of structured reasoning quality.
- **CDB-C003:** Evaluation agents use executable SQL over the database; the paper frames programmatic reasoning as necessary at large scale. **Canario:** Require an executable/queryable derivation path for structured analysis rather than making an LLM consume full tables.
- **CDB-C004:** Both proprietary and open models show systematic failure around NOT ENOUGH INFO / abstention. **Canario:** Make evidence insufficiency/abstention a first-class verification capability and benchmark target.
- **CDB-C005:** Longer agent-database interaction traces correlate with worse performance; strongest systems tend to use a bounded number of tool calls. **Canario:** Benchmark tool-call budget/trace efficiency and avoid unconstrained agent loops.
- **CDB-C006:** ClaimDB's released repository is CC BY-SA 4.0. **Canario:** Use as an external benchmark/reference unless a deliberate ShareAlike-compatible redistribution decision is made.

## Bounded transfer

**BENCHMARK + ADAPT. Adopt the benchmark lesson that large structured evidence needs executable composition and explicit abstention. Do not import ClaimDB's three-way verifier labels into Lector source extraction, and do not copy its dataset/code into Canario without a license decision.**

## Do not import

Do not reinterpret Canario as a database fact-checker only. ClaimDB assumes a claim and a database already exist; it does not solve custody, Representation provenance, source assertions, multimodality, or civic source authority.

## Residual risk / unresolved question

Which queryable Representation and execution boundary should Canario use, and how should derived analytical claims record executable provenance?

## Closure verdict

Research-complete for this synthesis gate. This Book is evidence, not
implementation authorization.
