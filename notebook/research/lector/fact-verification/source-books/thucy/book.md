---
id: CANARIO-BOOK-THUCY-001
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

# Thucy

## Question

Should Canario build, adapt, embed, or merely benchmark Thucy's relational claim verifier?

## Evidence horizon

This Book uses the primary paper and, where relevant, the current public
implementation/license metadata available through 2026-08-25. It is a bounded
architecture/reuse audit, not a reproduction of all experiments.

## Claim ledger synopsis

- **THU-C001:** Thucy discovers unknown relational data sources, inspects schemas, executes SQL, and returns verification verdicts with supporting SQL. **Canario:** Treat Thucy as the strongest reuse/baseline candidate for structured claim verification.
- **THU-C002:** Thucy's verifier delegates to distinct data-discovery, schema, and SQL experts before a lead verifier synthesizes a verdict. **Canario:** Benchmark whether specialization improves Canario cases before recreating a multi-agent topology.
- **THU-C003:** Thucy's verifier prompt instructs the model to treat all accessible data sources as reliable and authoritative. **Canario:** Do not adopt this authority assumption; it conflicts directly with Canario Source Authority and evidence-scope semantics.
- **THU-C004:** The implementation currently depends on OpenAI Agents/API and Google MCP Toolbox configuration. **Canario:** Prefer external baseline/sidecar experiment before embedding a provider-specific multi-agent stack into Canario.
- **THU-C005:** License metadata is internally inconsistent: LICENSE says MIT while pyproject declares Apache-2.0. **Canario:** No vendoring or copied implementation until upstream licensing is clarified.
- **THU-C006:** The paper reports 94.3% TabFact accuracy, 5.6 points above the cited previous state of the art. **Canario:** Use Thucy as a concrete benchmark target, but not as evidence of civic-source correctness or large-database robustness by itself.

## Bounded transfer

**BENCHMARK first; ADAPT only after a fit experiment. Reuse its source-discovery/schema/query separation and SQL transparency as hypotheses. Preserve Canario's source authority, bounded execution, custody, and model/provider independence.**

## Do not import

Do not vendor now. Do not import the 'all accessible data is authoritative' assumption. Do not make multi-agent architecture mandatory without evidence that a simpler query planner/executor cannot match it.

## Residual risk / unresolved question

Can a bounded Thucy sidecar run against a Canario-derived relational projection while preserving source-authority constraints and exact Representation lineage?

## Closure verdict

Research-complete for this synthesis gate. This Book is evidence, not
implementation authorization.
