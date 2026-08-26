---
id: CANARIO-BOOK-CLAIMVER-001
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

# ClaimVer

## Question

What should Canario learn about human-facing verification and cognitive load?

## Evidence horizon

This Book uses the primary paper and, where relevant, the current public
implementation/license metadata available through 2026-08-25. It is a bounded
architecture/reuse audit, not a reproduction of all experiments.

## Claim ledger synopsis

- **CLV-C001:** ClaimVer argues that blanket labels are insufficient and emphasizes claim-level localization of evidence and rationale. **Canario:** Present evidence and explanation at the smallest useful claim granularity rather than only a document-level verdict.
- **CLV-C002:** The framework is explicitly designed to reduce cognitive load through rich annotations and succinct explanations. **Canario:** Treat reviewer cognitive burden as a quality property of review tooling, not user error.
- **CLV-C003:** ClaimVer grounds predictions in a trusted knowledge graph and exposes evidence attribution. **Canario:** Evidence attribution and trusted-source boundaries should remain visible to the reviewer.
- **CLV-C004:** The paper introduces a distinct attribution score. **Canario:** Consider evidence-attribution quality as separate from semantic correctness, but do not import a universal scalar without validating meaning across modalities.

## Bounded transfer

**ADAPT human-facing evidence localization and explanation principles. Use as a warning against cognitively opaque benchmark/review interfaces.**

## Do not import

Do not adopt knowledge-graph dependence as a Canario core requirement, and do not resurrect a single universal confidence/attribution scalar across modalities.

## Residual risk / unresolved question

Which reviewer UI/evidence projection minimizes cognitive load while preserving exact source context and uncertainty?

## Closure verdict

Research-complete for this synthesis gate. This Book is evidence, not
implementation authorization.
