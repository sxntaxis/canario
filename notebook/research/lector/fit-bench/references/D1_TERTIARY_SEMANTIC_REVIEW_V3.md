---
id: CANARIO-D1-TERTIARY-SEMANTIC-REVIEW-V3-001
kind: benchmark-reference-tertiary-semantic-review
state: complete-with-reference-disputes
authority: tertiary-review-evidence
work: LECTOR-PRODUCTION-FIT-BENCH
fixture: CR-ESPARZA-MINUTES-001
---

# D1 v3 tertiary semantic review

## Verdict

```text
REFERENCE_DISPUTE
```

D1 v3 remains `SUPERVISOR_DRAFT`. This review does not modify, freeze, or relabel the reference.

## Reviewer / independence

```text
provider: OpenAI
model/version: GPT-5.6 Sol
independence_strength: WEAK_OR_UNKNOWN
strong_independent_gate_satisfied: false
```

## Anti-anchoring / leakage

The blind pass was persisted before any prior secondary-review/adjudication material was opened: **14** provisional hard-dispute groups, SHA256 `e9ea7672925e20ddc5ecccd95e850b7a5576636e49c4a01cf45e76e44a01d437`. The four v2 secondary-review/adjudication files were opened only after that gate.

```text
anchoring_contamination = false
formal_A0_A5_output_seen = false
formal_candidate_scores_seen = false
Acta_160_semantics_inspected = false
H2_selected_or_inspected = false
tested_extraction_behavior_seen = false
```

## Coverage

```text
structures source→reference: 36 / 36
frozen units source→reference: 61 / 61
facts reference→source: 700 / 700
evidence targets considered as sets: 1566 / 1566
v2 repairs regression-checked: 23 / 23
```

`U0007` was independently verified as the isolated page marker `1`.

## Findings

Hard disputes: **14** — 2 `SOURCE_TO_REFERENCE`, 12 `REFERENCE_TO_SOURCE`.

```text
MISSING_MATERIAL_ASSERTION: 2
MODALITY_ERROR: 1
QUANTITATIVE_ERROR: 1
EVIDENCE_INSUFFICIENT: 10
```

- `D1-V3-IR-0001` — `REFERENCE_TO_SOURCE` / `MODALITY_ERROR` — D1-F0091, D1-F0092, D1-F0093 — F0091-F0093 change a present-tense description of what the pool regulation contains into a normative claim that it “debía contemplar” those matters. (`NEW`)
- `D1-V3-IR-0002` — `SOURCE_TO_REFERENCE` / `MISSING_MATERIAL_ASSERTION` — no existing fact ID (omission) — D1 v3 omits Stephannie/Stephanie Quesada’s stated expectation that an Esparza-born President would bring greater attention to the canton’s road needs because of the considerable deterioration of the roads. (`NEW`)
- `D1-V3-IR-0003` — `SOURCE_TO_REFERENCE` / `MISSING_MATERIAL_ASSERTION` — no existing fact ID (omission) — D1 v3 omits the source assertion that expediente 23.898 had previously also been related to the port-reserve zone (“zona de reserva portuaria”). (`NEW`)
- `D1-V3-IR-0004` — `REFERENCE_TO_SOURCE` / `QUANTITATIVE_ERROR` — D1-F0501, D1-F0502 — F0501 and F0502 assert totals of 25 and 10 educational centers, respectively, although the frozen source only enumerates the centers and never states those totals. (`NEW`)
- `D1-V3-IR-0005` — `REFERENCE_TO_SOURCE` / `EVIDENCE_INSUFFICIENT` — D1-F0021 — F0021 carries mandatory temporal qualifier “8 de agosto de 2026”, but its only bound decision evidence says “8 de agosto” and does not bind the 2026 source-date context. (`NEW`)
- `D1-V3-IR-0006` — `REFERENCE_TO_SOURCE` / `EVIDENCE_INSUFFICIENT` — D1-F0122, D1-F0128, D1-F0713, D1-F0135 — Four C06 facts normalize “12 de junio” to mandatory temporal qualifier “12 de junio de 2026” without any bound evidence target supplying the year/date context. (`REPAIR_REGRESSION`; related D1-V2-IR-0003)
- `D1-V3-IR-0007` — `REFERENCE_TO_SOURCE` / `EVIDENCE_INSUFFICIENT` — D1-F0146, D1-F0147 — F0146 and F0147 normalize the 27 May 10:00 event to “27 de mayo de 2026”, but their bound evidence does not include the dated Club de Leones note or other source-date context. (`NEW`)
- `D1-V3-IR-0008` — `REFERENCE_TO_SOURCE` / `EVIDENCE_INSUFFICIENT` — D1-F0156, D1-F0157 — F0156 and F0157 assign 2026 to Ronald Robles’s “próximo 30 de mayo” and “28 de noviembre” statements even though the bound evidence does not supply a source-date anchor for the year. (`NEW`)
- `D1-V3-IR-0009` — `REFERENCE_TO_SOURCE` / `EVIDENCE_INSUFFICIENT` — D1-F0164 — F0164 carries “30 de mayo de 2026” while its operative-clause evidence states only “30 de mayo”. (`NEW`)
- `D1-V3-IR-0010` — `REFERENCE_TO_SOURCE` / `EVIDENCE_INSUFFICIENT` — D1-F0181 — F0181 carries “29 de mayo de 2026”, but its decision evidence says only “la asamblea del 29 de mayo”; the embedded document identifier DE-084-05-2026 is not itself an assertion that the assembly date is in 2026. (`NEW`)
- `D1-V3-IR-0011` — `REFERENCE_TO_SOURCE` / `EVIDENCE_INSUFFICIENT` — D1-F0388, D1-F0398, D1-F0399, D1-F0400, D1-F0401, D1-F0735, D1-F0405, D1-F0411 — Eight U06 facts normalize session-relative shorthand (“este mes”, “12 de junio”, and associated times) to 2026 without binding the session-date context that makes those calendar resolutions possible. (`REPAIR_REGRESSION`; related D1-V2-IR-0016)
- `D1-V3-IR-0012` — `REFERENCE_TO_SOURCE` / `EVIDENCE_INSUFFICIENT` — D1-F0501, D1-F0502, D1-F0503 — F0501-F0502 resolve “15 de mayo del presente año” to 15 May 2026, and F0503 normalizes “15 de junio” to 15 June 2026, without binding the dated AME/GDHL source context or session date. (`NEW`)
- `D1-V3-IR-0013` — `REFERENCE_TO_SOURCE` / `EVIDENCE_INSUFFICIENT` — D1-F0644 — F0644 normalizes “actividades de agosto” and “8 de agosto” to August 2026 / 8 August 2026 without binding the dated CCPJ correspondence or session-date context. (`NEW`)
- `D1-V3-IR-0014` — `REFERENCE_TO_SOURCE` / `EVIDENCE_INSUFFICIENT` — D1-F0649, D1-F0651 — F0649 and F0651 resolve the deictic expressions “el día de hoy” and “hoy en la tarde” to 18 May 2026 without binding the session-date evidence needed for that resolution. (`NEW`)

## v2 repair regression audit

```text
RESOLVED_IN_V3: 21
STILL_PRESENT: 0
PARTIALLY_RESOLVED: 0
REGRESSED_DIFFERENTLY: 2
```

`D1-V2-IR-0003` and `D1-V2-IR-0016` repaired their original antecedent/context defects, but mapped replacement facts `D1-F0713` and `D1-F0735` respectively carry a different v3 evidence defect: mandatory year `2026` is not supported by the complete bound evidence set. The canonical JSON contains the full 23-row regression matrix.

## Custody

```text
reviewed commit: f67be88dd34231f472e8bf485aba72760eeb36a0
reviewed tree:   c19b5a068dcffae6d497ae8eb6e71ad174cf8308
reference JSON:  0d5a4e07e9b2cd9ba3f7dd736f99b08c5202747b87d5f1ca058efee04e67a111
reference MD:    f6904b35c2083fbd347045113c5a2ac54975388af540a6f743012c5c9834afe6
```

No existing D1 reference/review/adjudication artifact was modified by this tertiary review.
