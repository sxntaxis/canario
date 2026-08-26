# LECTOR-002 Semantic Gold Protocol

State: **scope frozen; human gold pending; semantic evaluation not run**.

This protocol governs benchmark validation only. Gold scope is a bounded benchmark
scope, not a product-ingestion ontology or a production review policy. Human gold is
engineering validation for representative fixtures; `machine-only` remains a valid
production state.

## Separate States

The corpus keeps four independent facts per semantic case:

```text
gold_scope_state: pending | frozen
adjudication_state: not_run | incomplete | complete
semantic_verification[capability]:
  state: not_run | passed | failed
  result_sha256: null for not_run, immutable result digest otherwise
```

Frozen gold and complete adjudication never verify a capability by themselves. A
semantic capability is verified only when a covering case has an exact frozen scope,
frozen gold, complete adjudication, a `passed` state, and a valid result digest. The
threshold policy must also be frozen after gold counts are inspected and before any
tested extractor runs. The executable gate reports evaluation pending separately.

## Truth Binding

Every human truth binds to one or more semantic capabilities through sorted,
semicolon-separated `capability_ids`. A bound capability must be declared semantic
gold and covered by that case. Deterministic capabilities cannot appear in truth
bindings; candidates never declare capability success. Per-capability metrics are
computed from human-adjudicated candidate-to-truth mappings, not automated semantic
matching.

`semantic:multi_topic_longform` is a scope-wide capability. Its recall denominator is
all truths in the frozen selected scope, so reviewers do not need to label every Acta
truth with a topic-like tag. Other semantic capabilities derive membership from truth
bindings.

## Frozen Gold Scope

Each packet contains a canonical `gold_scope.json` bound to exact source and units
digests, the selected-unit digest, selection policy and semantic capabilities. Scoring
requires those identities to match. Coverage includes every prepared unit: selected
units receive `truth_recorded`, `no_material_truth`, or `needs_adjudication`; non-selected units
explicitly remain `unjudged`. `needs_adjudication` is a valid human-review outcome, not a hidden
negative label: it means the reviewer is unsure and the unit must receive a second independent
review before gold can freeze. The benchmark never forces uncertainty into a yes/no answer. Truths outside the selected set are rejected. A sampled structured
table result reports total units, selected units, selection kind and fraction, and
cannot claim full-workbook semantic recall.

The longform minutes case uses `full_source_order` over all 61 generic units. The
structured table uses `lector-002-structural-sample:v1`, a source-digest-seeded sample
that represents sheets, boundary rows, value-type signatures, formulas, merged
structure and row-shape diversity without reading labels or candidate output. The
correspondence uses full source order over its 17 generic text units.

## Freeze Ordering

```text
1. freeze gold scope
2. human completes gold
3. validate and freeze gold
4. inspect gold counts only
5. freeze semantic scoring thresholds/policy
6. run the tested extractor
7. human adjudicates candidates
8. score against frozen thresholds
```

`review-status` reports only mechanical progress: resolved units, blank units and units marked
`needs_adjudication`. It performs no semantic interpretation.

## Helper local de revisión

Para revisar un packet desempaquetado sin abrir una interfaz externa:

```bash
PYTHONPATH=. python notebook/implementation/lector_002_benchmark.py human-review \
  --packet /ruta/al/packet --session-size 5
```

El helper muestra una unidad por vez en orden de fuente y continúa desde la primera unidad
seleccionada que aún está en blanco. `--start-unit UNIT_ID` permite reanudar desde una unidad
concreta; `--read-only` permite inspeccionar sin escribir. Las opciones son `1` material,
`2` no material, `3` dudosa, `4` saltar, `b` volver a la anterior, `c` mostrar contexto,
`r` repetir la unidad, `q` salir guardando lo ya resuelto, `x` cancelar sin guardar y `?` mostrar ayuda. Las opciones `1`
y `3` aceptan una nota breve opcional, pero ninguna nota se convierte en truth.

Solo se escriben `coverage.csv` y `review_notes.csv`, con reemplazo atómico por archivo; la
primera modificación de una sesión conserva una copia en `.review-backups/`. El helper verifica
antes y después de la sesión los bytes de la Representation, `gold_scope.json`, manifests,
unidades, selección y artefactos semánticos. Si hay drift, la sesión se detiene. No lee
candidatos, no llama modelos, no crea truths, no adjudica incertidumbre y no toca los packets
canónicos reales durante pruebas sintéticas.

The `freeze-gold` validator refuses unresolved `needs_adjudication` units, empty semantic-capability gold (unless the
capability is explicitly scope-wide), candidate output, model assistance, changed
source/scope bytes, incomplete coverage, invalid evidence, or missing capability
bindings. It does not generate truths or decide semantic equivalence.

Benchmark assistance, if introduced later, may reduce search effort but cannot silently
become gold or final adjudication. No tested extractor, candidate output, semantic model
call, or truth row is present in the current review packets.
