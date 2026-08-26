---
id: CANARIO-BOOK-SCITAB-001
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

# SciTab

## Question

What does expert-verified compositional table reasoning reveal about a serious structured benchmark?

## Evidence horizon

This Book uses the primary paper and, where relevant, the current public
implementation/license metadata available through 2026-08-25. It is a bounded
architecture/reuse audit, not a reproduction of all experiments.

## Claim ledger synopsis

- **SCI-C001:** SciTab claims come from authentic scientific publications and require compositional reasoning over tables. **Canario:** Use authentic, expert-reviewed compositional cases as a counterweight to synthetic structured benchmarks.
- **SCI-C002:** The paper identifies table grounding, claim ambiguity, and compositional reasoning as distinct challenges. **Canario:** Benchmark these failure modes separately; do not collapse them into generic table understanding.
- **SCI-C003:** Most evaluated systems were near random guessing and Chain-of-Thought gave limited gains. **Canario:** Prompting alone is not a sufficient architecture for reliable compositional table reasoning.
- **SCI-C004:** Repository software is MIT licensed. **Canario:** Safe to inspect/adapt code subject to MIT; dataset licensing and scientific-domain fit remain separate.

## Bounded transfer

**BENCHMARK compositional table reasoning; ADAPT challenge taxonomy. Keep Canario's benchmark capability-oriented rather than document-type-oriented.**

## Do not import

Do not copy scientific-table conventions into generic civic table Representation semantics.

## Residual risk / unresolved question

Can Canario's future executable-reasoning path reproduce SciTab results without source-specific prompting?

## Closure verdict

Research-complete for this synthesis gate. This Book is evidence, not
implementation authorization.
