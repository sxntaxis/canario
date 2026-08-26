---
id: CANARIO-BOOK-FINDVER-001
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

# FinDVer

## Question

How should Canario benchmark long hybrid civic documents that mix narrative text, tables, numerical reasoning, and domain knowledge?

## Evidence horizon

This Book uses the primary paper and, where relevant, the current public
implementation/license metadata available through 2026-08-25. It is a bounded
architecture/reuse audit, not a reproduction of all experiments.

## Claim ledger synopsis

- **FDV-C001:** FinDVer evaluates claim verification over long hybrid-content financial documents and expert-domain reasoning. **Canario:** Strong external analogue for civic reports/budgets containing both text and tables.
- **FDV-C002:** Current data separates information extraction, numerical reasoning, and knowledge-intensive reasoning and provides relevant-context annotations. **Canario:** Split Canario structured/hybrid capabilities instead of treating semantic:structured_values as one catch-all.
- **FDV-C003:** Long-context and RAG systems still lag human experts substantially. **Canario:** Do not equate larger context windows with solved evidence retrieval or reasoning.
- **FDV-C004:** Examples contain explicit relevant_context plus explanations and verdicts. **Canario:** Context envelope should be represented separately from the smallest exact evidence locator.
- **FDV-C005:** Repository code is MIT licensed. **Canario:** Code can be inspected/adapted with normal MIT obligations; dataset/report licensing still needs independent review.

## Bounded transfer

**BENCHMARK hybrid-document reasoning against FinDVer and ADAPT its separation of extraction, math, and knowledge-intensive cases plus explicit relevant context.**

## Do not import

Do not import financial-domain assumptions or let external knowledge silently become source evidence.

## Residual risk / unresolved question

How should Canario distinguish source-grounded numerical derivation from knowledge-assisted assessment while keeping both provenance chains inspectable?

## Closure verdict

Research-complete for this synthesis gate. This Book is evidence, not
implementation authorization.
