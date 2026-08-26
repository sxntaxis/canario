---
id: CANARIO-BOOK-FRAME_GUIDED_OECD-001
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

# Frame-guided high-volume tabular claim generation

## Question

How should Canario choose meaningful structured-data stress cases instead of sampling arbitrary rows?

## Evidence horizon

This Book uses the primary paper and, where relevant, the current public
implementation/license metadata available through 2026-08-25. It is a bounded
architecture/reuse audit, not a reproduction of all experiments.

## Claim ledger synopsis

- **FGT-C001:** The dataset contains 78,503 claims grounded in 434 OECD tables averaging over 500K rows and supports English, Chinese, Spanish, and Hindi. **Canario:** Provides a directly relevant multilingual, large-table external stress benchmark including Spanish.
- **FGT-C002:** Claim generation begins with programmatic selection of significant data points under six semantic frames rather than random row sampling. **Canario:** Replace arbitrary structural-row semantic sampling with explicit reasoning phenomena.
- **FGT-C003:** The baseline uses SQL generation and identifies evidence retrieval as the primary bottleneck. **Canario:** Benchmark evidence retrieval separately from query/reasoning correctness.
- **FGT-C004:** The benchmark uses synthetic natural-language claims while grounding them in real OECD data. **Canario:** Use for controlled structured reasoning stress, not as the sole proof of civic-document extraction quality.

## Bounded transfer

**ADAPT benchmark construction principles and BENCHMARK against the released cases. Semantic structured-data cases should exercise identifiable operations/frames over real values, not merely sample physical rows.**

## Do not import

Do not adopt the six frames as a closed Canario ontology. They are benchmark stress families, not universal civic claim kinds.

## Residual risk / unresolved question

Which operation families should Canario declare as capabilities after measuring actual civic datasets, and which external benchmark cases are license-compatible for automated CI?

## Closure verdict

Research-complete for this synthesis gate. This Book is evidence, not
implementation authorization.
