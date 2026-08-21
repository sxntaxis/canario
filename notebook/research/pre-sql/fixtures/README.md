---
id: ACTAKIT-PRE-SQL-FIXTURES-001
type: research-fixture-program
state: pass
authority: evidence
created: 2026-08-20
actakit_baseline: 59bab9de30bbf2aa1eec96dddaee3cded31a9f3a
research_baseline: f790517ea7dd16796a1484289275ff4ddc93cc84
---

# Pre-SQL fixtures and counterexamples

These fixtures are the bridge between external research and schema design.
They test whether the **conceptual model** can represent difficult civic-record
cases without choosing SQL tables yet.

A fixture may be synthetic. Synthetic fixtures can prove that a conceptual shape
is coherent; they cannot prove that a real parser/OCR/profile understands public
records correctly. `proof-requirements.csv` records where an artifact-backed
fixture is still required before implementation certification.

The first-pass fixture verdict exposed four bounded design questions. Those are
resolved and revalidated in `revalidation.md`; `verdict.md` and the original
`open` assertions remain as historical evidence of what the first pass found.
The current semantic fixture gate is PASS, while artifact-backed operational proof
remains required later where `proof-requirements.csv` says so.

## Method

Each case has four kinds of expectations:

- **must** — the future model must represent this without ambiguity;
- **must_not** — behavior that would silently corrupt identity/evidence/meaning;
- **may** — implementation freedom that should not be frozen pre-SQL;
- **open** — a real design decision exposed by the fixture.

Ledgers:

```text
fixtures.csv            fixture catalog and research pressure
assertions.csv          stable requirements extracted from cases
counterexamples.csv     tempting but invalid shortcuts
proof-requirements.csv  where real public artifacts are still needed
verdict.md               cross-fixture review before SQLite
cases/*.yaml             compact semantic examples; not SQL schemas
```

## Boundary

The fixture package does **not** authorize:

- SQLite tables/migrations;
- production code;
- parser implementation;
- graph database/RDF runtime;
- plugin/output package machinery;
- architecture promotion.

Promotion remains:

```text
Source Books -> synthesis -> fixtures/counterexamples
  -> explicit design decision -> architecture/contracts -> SQL
```
