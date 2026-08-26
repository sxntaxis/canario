---
id: CANARIO-RESEARCH-LITERATURE-MAP-001
type: research-index
state: current
authority: navigation
updated: 2026-08-25
---

# Literature map

Canonical citations live in `references.bib`. This file is a decision-oriented map,
not a second bibliography.

| Work | Problem / evidence | Key lesson for Canario | Code / license signal | Current disposition |
|---|---|---|---|---|
| ClaimDB (ACL 2026) | Verification over millions of structured records / multiple tables | At scale, evidence must be queried/composed executablely; abstention is a hard capability | Released benchmark; repo observed CC BY-SA 4.0 | **BENCHMARK + ADAPT** |
| Thucy (2025) | Cross-database/cross-table claim verification with SQL evidence | Strongest direct verifier baseline; source authority and bounded provenance need Canario-specific constraints | OSS; LICENSE=MIT but pyproject says Apache-2.0 | **BENCHMARK; ADAPT only after fit/licensing audit** |
| Frame-guided OECD (LREC 2026) | 78K synthetic claims over 434 huge OECD tables, including Spanish | Sample reasoning phenomena and real values, not arbitrary physical rows; evidence retrieval is a separate bottleneck | Research benchmark | **BENCHMARK + ADAPT construction principles** |
| FEVEROUS (2021) | Mixed text/table evidence retrieval + verdict | Multi-evidence sets and evidence-aware scoring are mature prior art | Apache-2.0 software repo | **ADAPT scorer/evidence-set ideas** |
| FinDVer (EMNLP 2024) | Long hybrid financial documents | Separate extraction, numerical reasoning, knowledge reasoning, and relevant context | MIT software repo | **BENCHMARK + ADAPT capability split** |
| SciTab (EMNLP 2023) | Expert-verified compositional scientific table claims | Table grounding, ambiguity and composition are distinct failure modes | MIT repo | **BENCHMARK** |
| AVeriTeC (NeurIPS 2023) | Real claims + open-web evidence + multi-step QA | Evidence sufficiency, temporal leakage and context dependence must be evaluated explicitly | CC BY-NC 4.0 repo | **ADAPT principles; external benchmark only** |
| TSVer (EMNLP 2025) | Real claims against time-series evidence | Time windows and justification need explicit semantics | CC BY-SA 4.0 repo | **BENCHMARK future temporal capability** |
| CaseFacts (ACL 2026) | Legal claims / temporally valid precedent | Unrestricted retrieval can hurt; authority and time constrain usable evidence | Released repo | **ADOPT authority lesson + BENCHMARK** |
| ClaimVer (Findings 2024) | Human-facing claim verification / attribution | Evidence localization and explanations reduce cognitive burden | Paper provides software/data attachment | **ADAPT human-review principles** |
| SQLite (current docs) | Bounded relational query execution | Already supports aggregates/windows; authorizer + defensive controls make it the smallest executor baseline | Public domain | **BENCHMARK FIRST** |
| DuckDB (current docs) | Embedded analytical SQL | Strong OLAP challenger; XLSX inference is not source-fidelity semantics; generated SQL requires sandboxing | MIT | **BENCHMARK** |
| Apache Arrow | Columnar interchange / in-memory analytics | Useful derivative/interchange layer, not canonical workbook semantics | Apache-2.0 ecosystem | **DEFER** |
| Claim Verification LLM Survey (ACL 2026) | Survey of LLM verification pipelines | Use as literature radar and terminology cross-check, not architectural authority | Paper | **REFERENCE** |
| TabFact | Small-table entailment | Historical baseline; insufficient alone for Canario scale | Public benchmark | **REFERENCE / external baseline** |
| BIRD | Realistic large DB NL2SQL | Useful query-generation lineage; ClaimDB inherits it | Public benchmark | **REFERENCE** |
| Program of Thoughts | Executable numerical reasoning | Keep semantic planning separate from deterministic computation | Public code/paper | **ADAPT principle** |
| Chain-of-Table | Evolving table operations | Useful table-reasoning baseline, but still not large civic-data architecture | Apache-2.0 code | **REFERENCE / BENCHMARK candidate** |

## Reading rule

A new paper/project enters the architecture discussion only after its mechanism,
failure modes, licensing/reuse boundary, and Canario transfer have been recorded.
Leaderboard placement alone is never an adoption argument.
