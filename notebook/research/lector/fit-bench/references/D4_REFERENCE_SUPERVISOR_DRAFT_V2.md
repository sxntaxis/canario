---
id: CANARIO-LECTOR-FIT-BENCH-D4-REFERENCE-SUPERVISOR-DRAFT-002
kind: benchmark-reference-candidate
state: supervisor-draft
authority: active-work-evidence
work: LECTOR-PRODUCTION-FIT-BENCH
fixture: CR-CGR-SANTA-ANA-PROCUREMENT-AUDIT-001
protocol: CANARIO-LECTOR-FIT-BENCH-REFERENCE-PROTOCOL-FREEZE-002
method: CANARIO-LECTOR-FIT-BENCH-REFERENCE-AUTHORING-METHOD-001
supersedes: CANARIO-LECTOR-FIT-BENCH-D4-REFERENCE-SUPERVISOR-DRAFT-001
---

# D4 semantic reference — supervisor draft v2

This is the supervising/cloud author's revised semantic reference candidate for the exact frozen D4
development fixture:

> Informe de auditoría sobre la gestión de contratación pública en la Municipalidad de Santa Ana,
> informe n.° DFOE-LOC-IAD-00011-2024, Contraloría General de la República, 28 June 2024.

It is **not frozen gold** and is not eligible for A0–A5 scoring.

## Why v2 exists

D4 v1 was mechanically certified unchanged at `c4fddeca4996254b6c8609ee586a1ad695c9f5f3`.
That certification correctly proved hashes/selectors/tests, but primary-PDF inspection also exposed a
semantic defect in v1: the text Representation linearized visible `10` plus superscript footnote marker
`4` as `104`. The exact primary PDF shows **10** exception procedures and footnote 4 breaks them down
as 5 + 4 + 1.

The supervising/cloud author then re-read the complete frozen D4 scope in source order and performed
multiple source→reference, omission-only, reference→source, structure-mapping, capability-binding and
primary-source challenge passes. The machine-readable record is
`D4_SUPERVISING_AUTHOR_ADVERSARIAL_REVIEW_V1.json`.

The final v2 draft contains:

```text
facts                              289
evidence targets                   368
structure carriers                 150
frozen units                       260
cross-unit facts                   165
multi-evidence facts               71
supervising-author findings         98
unresolved semantic structures       0
primary-source adjudications          2
```

The fact increase from 185 to 289 is a consequence of source-exhaustive decomposition and repair, not
a target count.

## Identity boundary

The draft remains bound to the exact F2 D4 identities:

- primary PDF SHA256 `587e4ba2ca65c4a3f453471434ca69b41ba71fe59ae64897590b1fc6c44c97fe`;
- Representation / benchmark-scope SHA256 `324dfd50e4cee6619bf0f8cbce223004bc34bd9d980cad90823f3a195111893d`;
- unit inventory SHA256 `b4c45ebccf7bfc4ec02d902aaa96b7f968bcc07719b40ceef28c79985bf1c5b4`;
- unit count `260`;
- source pack SHA256 `eb729446edb1c698cc0ea3ecc6e92a1cf3cf217a24bea6320c744e919699f7ae`.

The full frozen 28-page Representation remains the benchmark scope.

## Primary-source adjudications

### `D4-PSA-0001` — footnote 4 / exception procedures

The exact frozen primary PDF established that paragraph 2.13 visibly says `10` followed by superscript
footnote marker `4`. Footnote 4 refers to those 10 procedures and states:

```text
5 proveedor único
4 reparaciones indeterminadas
1 bienes o servicios artísticos, culturales e intelectuales
```

The v1 quantity `104` is therefore retired as an extraction-layer artifact. Because the primary source
resolves the referent, the corresponding facts no longer bind `AMB-01`; they retain cross-unit context
because the paragraph and footnote must be read together.

### `D4-PSA-0002` — `activo motivado` / `acto motivado`

The report contains an internal wording conflict for the same 9-case finding:

- the executive summary states `acto motivado`;
- Cuadro n.° 2 visibly prints `activo motivado` in the official CGR PDF.

The semantic fact uses the unambiguous executive-summary assertion while preserving the table conflict
in adjudication evidence with `AMB-01` / `REC-01`. It is not silently corrected as an OCR defect.
Exact byte-identical confirmation of that table wording in the frozen PDF remains a local mechanical
certification check; the local agent may report literal evidence but may not alter semantics.

## Final quality invariants

```text
FID-01 bindings                       0
all-15 capability templates           0
generic qualifier placeholders        0
generic reverse-audit notes           0
blank reverse-audit notes             0
note == single evidence               0
empty/zero evidence                    0
scope escapes                          0
facts without units                    0
unknown capability IDs                 0
unaccounted units                      0
unaccounted structures                 0
material carriers without facts        0
```

The supervising author also rechecked evidence-selector boundaries after the semantic rebuild; no final
selector begins or ends inside a word. This is an author-time check, not a substitute for local
mechanical reopening against the exact frozen source pack.

## Review boundary

This v2 was written and challenged by the same supervising/cloud author. The review is explicitly
**self-adversarial, not materially independent**.

```text
supervising_author_adversarial_review = complete
local_mechanical_certification_v2     = pending
independent_semantic_review            = still required
reference_frozen                       = false
```

A small local model must not substitute for semantic authorship or for the materially independent
big-model review gate. Local execution remains limited to source/hash/selector verification, literal
primary-source checks, repository tests, bundles and unchanged push.

## Leakage / maturity

```text
formal_A0_A5_output_seen             = false
formal_candidate_scores_seen         = false
Acta_160_semantics_inspected         = false
H2_selected_or_inspected             = false
thresholds_frozen                    = false
production_implementation_authorized = false
```

A successful local mechanical certification advances evidence only. It does not freeze D4 or authorize
lane execution.
