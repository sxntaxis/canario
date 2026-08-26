---
id: CANARIO-BOOK-AVERITEC-001
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

# AVeriTeC

## Question

What should Canario learn from real-world multi-step evidence annotation and evidence-sufficiency evaluation?

## Evidence horizon

This Book uses the primary paper and, where relevant, the current public
implementation/license metadata available through 2026-08-25. It is a bounded
architecture/reuse audit, not a reproduction of all experiments.

## Claim ledger synopsis

- **AVT-C001:** AVeriTeC annotates claims with evidence-backed question-answer pairs and textual justifications rather than a verdict alone. **Canario:** Represent decomposed evidence/reasoning paths independently from the final assessment.
- **AVT-C002:** Its annotation process explicitly addresses context dependence, evidence insufficiency, and temporal leakage. **Canario:** Make context sufficiency and temporal cutoff explicit benchmark properties.
- **AVT-C003:** Evidence can conflict and must be combined into a justification. **Canario:** Canario assessment must support conflicting evidence rather than forcing one source into a universal truth label.
- **AVT-C004:** Repository README declares CC BY-NC 4.0 for this work. **Canario:** Use as an external benchmark/reference; avoid incorporating dataset/code into distributable Canario without a deliberate non-commercial-license decision.

## Bounded transfer

**ADAPT annotation/evaluation principles: evidence sufficiency, temporally bounded retrieval, decomposed evidence, and justification. BENCHMARK externally where licensing permits.**

## Do not import

Do not make open-web retrieval the default evidence authority for civic verification; Canario's bounded source authority must remain explicit.

## Residual risk / unresolved question

How should Canario record evidence-sufficiency judgments and temporal cutoffs without turning every source assertion into a global fact-check?

## Closure verdict

Research-complete for this synthesis gate. This Book is evidence, not
implementation authorization.
