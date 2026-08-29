---
id: CANARIO-LECTOR-FIT-BENCH-REFERENCE-AUTHORING-METHOD-001
kind: benchmark-reference-authoring-method
state: accepted-within-active-work
authority: active-work-evidence
work: LECTOR-PRODUCTION-FIT-BENCH
created: 2026-08-28
depends_on:
  - CANARIO-LECTOR-FIT-BENCH-SEMANTICS-FREEZE-001
  - CANARIO-LECTOR-FIT-BENCH-REFERENCE-PROTOCOL-FREEZE-002
---

# F3 semantic reference authoring method v1

## Purpose

Turn the F1 semantics into a repeatable source-grounded annotation method without delegating semantic
design to the local machine agent.

This is **not** a production Lector algorithm. It is benchmark-construction procedure.

## Role split

```text
supervising/cloud author
  reads the exact frozen source
  decides semantic materiality
  writes/decomposes facts
  assigns concrete qualifiers and capability bindings
  owns source-order completeness and reverse semantic audit

local execution agent
  verifies exact bytes/hashes
  materializes/verifies exact selectors defined by the candidate
  runs mechanical validators/tests
  returns failures unchanged
  bundles and pushes the exact accepted commit
```

The local agent does not rewrite semantics when a test fails unless the owner/supervising author
explicitly opens a new semantic-authoring task.

## Why this method was needed

Early F3 experiments demonstrated several invalid shortcuts:

- copying evidence blocks into `canonical_semantic_note`;
- treating one source unit as one fact;
- applying fixture-wide capability templates;
- using generic qualifier placeholders;
- reporting exact reopening while evidence did not entail the whole proposition;
- marking a unit `MATERIAL_FACTS` once one fact existed even though additional assertions remained;
- generating apparently exhaustive ledgers mechanically without semantic exhaustion.

Those artifacts were never frozen and no formal candidate output had been exposed.

A small D2 correspondence pilot then demonstrated the viable shape: semantic propositions authored
from the complete source, concrete qualifiers, honest cross-unit context, exact evidence, an
omission-only pass, and a reverse fact audit. The D2 pilot remains method evidence rather than a
frozen reference because its semantic text was authored before the project re-established the
cloud-author/local-certifier role split.

## Authoring algorithm

For each frozen fixture:

### A. Reopen identity

Verify source, Representation, benchmark scope, and frozen unit inventory identities before semantic
work. Never annotate a merely similar or re-downloaded variant whose frozen identity differs.

### B. Build annotation structure from source-visible boundaries

Use only deterministic structural boundaries helpful for exhaustive review. Examples:

```text
regulation: article -> lettered/numbered normative clause
report: numbered paragraph -> table row -> disposition sub-item
minutes: agenda/correspondence/speaker/decision blocks
```

This structure belongs to the benchmark notebook, not generic Canario core.

### C. Source-order semantic pass

Read every scoped region. For each material carrier, enumerate **all** material civic assertions.
Do not target a fact count and do not stop after finding one fact in a unit.

### D. Write facts as propositions

Each fact should be the smallest proposition separable without losing meaning. Preserve the exact
source voice and modality:

```text
approved != proposed
must != may
stated != verified true
past != current
some != all
```

Do not import world knowledge or silently correct the source.

### E. Attach concrete mandatory qualifiers

Only meaning-changing values belong in qualifier fields. Empty categories remain empty.

### F. Bind fact-specific capabilities

Capabilities diagnose what a fact exercises; they are not fixture labels.

### G. Bind semantically sufficient evidence

Select exact evidence sufficient for the proposition and qualifiers. Broader or multi-span evidence
is correct when necessary. A tiny lexical match is not preferred over semantic support.

### H. Omission-only pass

Re-read source order specifically looking for missing propositions, not stylistic rewrites.

### I. Reverse semantic pass

For every fact verify entailment, minimality, qualifier support, evidence sufficiency, context/unit
mapping, capability semantics, and duplicate/equivalence handling. Record a fact-specific reason.

### J. Mechanical certification

Only after semantic authorship is complete does the local agent verify selectors/hashes/invariants.
Mechanical failure returns to the supervising author; it is not license to rewrite the reference.

### K. Independent semantic review

A materially independent reviewer challenges both completeness and faithfulness before freeze under
`REFERENCE_PROTOCOL_FREEZE_V2.md`.

## Required anti-slop invariants

At minimum:

```text
note_equals_evidence = 0 unless the proposition genuinely cannot be paraphrased without semantic loss
raw_heading_or_fragment_facts = 0
generic_placeholder_qualifiers = 0
string_false_qualifiers = 0
identifier_as_QTY_errors = 0
natural_fixture_FID_01_bindings = 0
fixture_wide_capability_templates = 0
unaccounted_units_or_structure_carriers = 0
material_carriers_without_exhaustion_pass = 0
facts_without_fact_specific_reverse_audit = 0
facts_without_semantically_sufficient_reopenable_evidence = 0
```

Any exception must be explicit and source-grounded, not a validator workaround.

## Current fixture sequence

Author and certify one fixture at a time:

```text
D2 correspondence  -> compact method anchor
D3 regulation      -> normative/article exhaustion stress
D4 audit/report    -> findings/tables/dispositions/quantities stress
D1 long minutes    -> long-context/attribution/repetition stress
```

No later fixture may inherit semantic content from an earlier fixture; only the authoring method is
reused.
