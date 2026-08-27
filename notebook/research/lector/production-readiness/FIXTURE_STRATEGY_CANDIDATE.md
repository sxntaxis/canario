---
id: CANARIO-LECTOR-FIT-BENCH-FIXTURE-STRATEGY-CANDIDATE-001
type: benchmark-fixture-strategy
state: research-candidate
authority: none
created: 2026-08-27
---

# Lector fit-bench fixture strategy candidate

This is fixture-selection research, not a product ontology and not benchmark freeze authority.

## Selection principle

Choose sources because they expose materially different **failure modes**, not because Canario needs
one fixture for every named document genre.

The benchmark should remain small enough for high-quality human reference work and broad enough that
one source family cannot dominate the result.

## Development/reference-design set

### D1 — Acta Sesión Ordinaria N.° 161, Municipalidad de Esparza

Role:
- long Spanish institutional record;
- many topics;
- attribution and decisions;
- cross-page continuation;
- already deeply understood by the project.

Use:
- develop reference protocol;
- develop/contextual-unit mechanics;
- diagnose long-document coverage.

Restriction:
- **not an independent final holdout**. It has already influenced Canario design substantially.

### D2 — Existing INCOP correspondence fixture

Role:
- correspondence attribution;
- conditions, exceptions, references to other instruments;
- shorter but context-sensitive prose.

Use:
- stress standalone claim formulation and attribution.

### D3 candidate — Reglamento interno de contratación pública de la Municipalidad de Esparza y CCDR

Public authority:
Sistema Costarricense de Información Jurídica (SCIJ), regulation dated 2025-04-10, 54 articles.

Why selected:
- dense definitions, duties, exceptions and procedural conditions;
- internal and external legal cross-references;
- normative modality ("debe", "podrá", conditions for actions);
- substantially different semantics from meeting minutes;
- source is structured legal HTML rather than merely another PDF minutes file.

Candidate URL family:
`https://pgrweb.go.cr/scij/Busqueda/Normativa/Normas/`

This source is not frozen until exact source identity/version and a deterministic inspectable
Representation are recorded.

### D4 candidate — CGR audit report DFOE-LOC-IAD-00011-2024

Title:
**Informe de auditoría sobre la gestión de contratación pública en la Municipalidad de Santa Ana**

Public PDF:
`https://cgrfiles.cgr.go.cr/publico/docs_cgr/2024/SIGYD_D/SIGYD_D_2024012846.pdf`

Observed shape:
- 28 pages;
- executive summary + methodology + findings + conclusions + dispositions;
- quantities and percentages;
- findings with causes/consequences;
- mandatory recommendations/dispositions with dates;
- tables and figures embedded in the report.

Why selected:
- different issuing institution and writing style;
- finding/recommendation distinction;
- quantitative exactness;
- long-range references to paragraphs, laws, and deadlines;
- tests whether extraction preserves "finding" versus "CGR orders X to do Y by date Z".

This source is a candidate development fixture, not yet frozen.

## Structured and media capability lanes

Do not force them into the free-text Claim campaign.

- Existing Esparza workbook remains a structured-table stress source.
- Existing INCOP/Caldera media remains timed-media stress material.

Their Representation/evidence gates remain typed. Numerical composition and cross-table reasoning are
already owned by Derivation/Verification, not Lector.

## Natural holdouts

### H1 — Acta Extraordinaria N.° 160, Municipalidad de Esparza

Reserved first end-to-end holdout.

Reason:
- selected by the interrupted Phase-6 vertical;
- not used to tune the future Lector;
- same real connector terrain as the first deployment, making it an honest product integration check.

Do not inspect its semantic content to tune extraction before the production candidate is frozen.

### H2 — non-minutes Spanish civic holdout

Must be selected and byte/source-frozen **before** the production candidate is finalized.

Requirements:
- different institution or source family from D1;
- exercises at least one hard capability not dominated by minutes;
- no prompt/orchestration/threshold tuning on its semantic contents.

Possible families:
- CGR report not used in development;
- public contract/procurement instrument;
- institutional normative material;
- formal technical report/correspondence package.

Exact source is intentionally not selected yet to avoid accidental tuning.

## Holdout failure rule

If a holdout exposes a material failure:

```text
candidate FAIL
-> convert failure into an explicit benchmark capability/counterexample
-> revise research/design
-> choose a NEW untouched holdout
```

The failed holdout cannot later be called independent certification evidence for the revised system.

## What this fixture set does NOT claim

It does not prove universal support for:
- all legal documents;
- all reports;
- all Spanish;
- every civic source or modality.

It proves only the frozen declared capabilities exercised by the selected fixtures.
