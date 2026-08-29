---
id: CANARIO-D1-SECONDARY-SEMANTIC-REVIEW-V2-001
kind: benchmark-reference-secondary-semantic-review
state: complete-with-reference-disputes
authority: secondary-review-evidence
work: LECTOR-PRODUCTION-FIT-BENCH
fixture: CR-ESPARZA-MINUTES-001
---

# D1 secondary semantic review v2

## Verdict

```text
REFERENCE_DISPUTE
```

The exact mechanically certified D1 v2 candidate remains `SUPERVISOR_DRAFT`. This review does not modify, freeze, or relabel the reference.

## Reviewer / independence

```text
provider: OpenAI
model/version: GPT-5.6 Sol
independence_strength: WEAK_OR_UNKNOWN
strong_independent_gate_satisfied: false
```

This is a fresh-context secondary review, but not materially independent because the supervising author and prior semantic reviewer were also OpenAI GPT-5.6 Sol.

## Anti-anchoring and leakage

The blind pass was persisted before any prior review/adjudication/self-review was opened: **23 provisional hard-dispute groups**, SHA256 `2d3f69cc326e07b3449dc227a6fa080e4c6383c4d011bb70bb01b213fef2e532`. Prior material was then used only for regression classification.

```text
formal_A0_A5_output_seen = false
formal_candidate_scores_seen = false
Acta_160_semantics_inspected = false
H2_selected_or_inspected = false
```

## Coverage

```text
structures source→reference: 36 / 36
frozen units source→reference: 61 / 61
facts reference→source: 700 / 700
evidence targets considered: 1473 / 1473
```

`U0007` was independently confirmed as only the isolated page marker `1`. No source→reference omission survived the blind source-order pass.

## Findings

Hard disputes: **23** (all `REFERENCE_TO_SOURCE`).

```text
EVIDENCE_INSUFFICIENT: 19
CONTEXT_ERROR: 3
SOURCE_FIDELITY_ERROR: 1
```

Main surviving families are: source-typo normalization in C05; unresolved or unbound antecedents in C06/C08/C11/C12/C13/U04/U06/U08/M02/V02; formal-decision evidence gaps; and finality selectors that omit material clauses they canonically claim to cover.

### Finding inventory

- `D1-V2-IR-0001` — `SOURCE_FIDELITY_ERROR` — `NEW` — D1-F0079, D1-F0080, D1-F0081, D1-F0082, D1-F0083: The v2 canonical facts normalize the frozen speaker label “Rolnald Robles” to “Ronald Robles” without binding evidence that authorizes that correction.
- `D1-V2-IR-0002` — `EVIDENCE_INSUFFICIENT` — `NEW` — D1-F0123, D1-F0124, D1-F0125: The bound evidence does not identify the referenced prior agreement as the hija-predilecta declaratory agreement, and the F0125 evidence names only “la señora presidenta” rather than Laura Fernández Delgado.
- `D1-V2-IR-0003` — `EVIDENCE_INSUFFICIENT` — `REPAIR_REGRESSION` — D1-F0129, D1-F0130, D1-F0131, D1-F0132: The bound evidence resolves the speaker as Bienvenido Venegas but does not resolve “la señora presidenta electa”, “ella” or “ellos” to Laura Fernández or her team.
- `D1-V2-IR-0004` — `EVIDENCE_INSUFFICIENT` — `REPAIR_REGRESSION` — D1-F0133, D1-F0134: The bound evidence does not bind the response/recipient antecedent to Douglas Salazar.
- `D1-V2-IR-0005` — `EVIDENCE_INSUFFICIENT` — `NEW` — D1-F0139: The sole bound selector is only the attachment fragment and does not bind either the formal SE ACUERDA status/Concejo actor or the communication to Douglas Salazar.
- `D1-V2-IR-0006` — `EVIDENCE_INSUFFICIENT` — `REPAIR_REGRESSION` — D1-F0155, D1-F0158: The bound evidence does not resolve the invitation/activity to the Expo Feria del Aguacate.
- `D1-V2-IR-0007` — `EVIDENCE_INSUFFICIENT` — `NEW` — D1-F0179: The bound evidence does not resolve “la asamblea” to Asamblea Nacional Ordinaria 01-2026.
- `D1-V2-IR-0008` — `CONTEXT_ERROR` — `REPAIR_REGRESSION` — D1-F0184, D1-F0191, D1-F0192, D1-F0195: The canonical/evidence pair leaves required event or enlace antecedents unresolved instead of making the propositions self-sufficient.
- `D1-V2-IR-0009` — `EVIDENCE_INSUFFICIENT` — `REPAIR_REGRESSION` — D1-F0196, D1-F0676: The formal designation evidence says only “coordinar el evento” and never binds that event to the Festival Nacional de Folclore.
- `D1-V2-IR-0010` — `EVIDENCE_INSUFFICIENT` — `REPAIR_REGRESSION` — D1-F0219, D1-F0229, D1-F0230, D1-F0232, D1-F0243, D1-F0246, D1-F0248, D1-F0250, D1-F0252, D1-F0255, D1-F0258, D1-F0259, D1-F0260, D1-F0261, D1-F0262, D1-F0263, D1-F0264, D1-F0265, D1-F0266, D1-F0269, D1-F0270: Multiple C13 facts resolve generic “esto”, “la comisión”, “esta nueva etapa”, “esos expedientes”, “la carta”, or a suspended meeting/session to the ZMT dispute/document without binding the antecedent in the evidence set.
- `D1-V2-IR-0011` — `EVIDENCE_INSUFFICIENT` — `REPAIR_REGRESSION` — D1-F0696: The restored reminder-history fact binds only “acuerdos recordatorios relacionados con ese tema” and does not bind “ese tema” to SINAC/Patrimonio Natural del Estado certifications.
- `D1-V2-IR-0012` — `EVIDENCE_INSUFFICIENT` — `REPAIR_REGRESSION` — D1-F0677: The finality evidence covers item 1 (receipt of the Mata de Limón note) but omits item 2 requesting the ZMT pending-expedients report.
- `D1-V2-IR-0013` — `EVIDENCE_INSUFFICIENT` — `REPAIR_REGRESSION` — D1-F0697, D1-F0698: The bound proposal/acceptance evidence refers only to “la ruta” and the preceding solicitud, without binding that route/gestion to route 756.
- `D1-V2-IR-0014` — `EVIDENCE_INSUFFICIENT` — `REPAIR_REGRESSION` — D1-F0682: The finality evidence supports transfer of the route-756 request to CONAVI and MOPT but omits the additional remittance to the Presidency of the Republic.
- `D1-V2-IR-0015` — `EVIDENCE_INSUFFICIENT` — `REPAIR_REGRESSION` — D1-F0683: The finality evidence supports the route-622 intervention clause but omits the added speed-bump clause from Nances toward the UCR.
- `D1-V2-IR-0016` — `EVIDENCE_INSUFFICIENT` — `REPAIR_REGRESSION` — D1-F0374, D1-F0378, D1-F0382, D1-F0383, D1-F0391, D1-F0395, D1-F0402, D1-F0406, D1-F0407, D1-F0413, D1-F0685: Several U06 facts resolve generic project/topic references to expediente 23.898/Puntarenas or add recognition-event context that is not carried by their bound evidence.
- `D1-V2-IR-0017` — `CONTEXT_ERROR` — `NEW` — D1-F0494, D1-F0495, D1-F0496: The U08 disposition/finality set uses the unresolved source phrase “el tema” while the canonical record attributes the action to the Juegos Deportivos Nacionales topic.
- `D1-V2-IR-0018` — `EVIDENCE_INSUFFICIENT` — `REPAIR_REGRESSION` — D1-F0687: The M01 finality evidence covers only the renewed referral/criterion-jurídico clause and omits the school-supervisor follow-up clauses.
- `D1-V2-IR-0019` — `EVIDENCE_INSUFFICIENT` — `REPAIR_REGRESSION` — D1-F0573, D1-F0575: The M02 bound evidence leaves “esa posibilidad” / “concretarlo” unresolved and does not bind the specific interino use of vacancies that the canonical facts state.
- `D1-V2-IR-0020` — `EVIDENCE_INSUFFICIENT` — `REPAIR_REGRESSION` — D1-F0689: The M03 finality evidence stops at the agreement header and item “1.”, omitting the operative permit, canon, notification/appeal and Natalia Araya Freeman clauses.
- `D1-V2-IR-0021` — `CONTEXT_ERROR` — `REPAIR_REGRESSION` — D1-F0638, D1-F0639: The V02 follow-up facts leave the pending topic/meeting antecedent unresolved in their bound evidence.
- `D1-V2-IR-0022` — `EVIDENCE_INSUFFICIENT` — `REPAIR_REGRESSION` — D1-F0661, D1-F0662: The C01/C02 finality evidence does not carry the full substitution agreements whose finality the canonical facts assert.
- `D1-V2-IR-0023` — `EVIDENCE_INSUFFICIENT` — `REPAIR_REGRESSION` — D1-F0668: The C04 finality evidence does not bind the generic CCPJ request transferred to the Administration to the Campaña de emprendedurismo joven.

## Prior-v1 regression audit

All **61/61** accepted v1 adjudications were rechecked against D1 v2 after the blind provisional pass.

```text
RESOLVED_IN_V2: 42
STILL_PRESENT: 0
PARTIALLY_RESOLVED: 0
REGRESSED_DIFFERENTLY: 19
```

The 19 regressions are not the original v1 defects unchanged: v2 repaired the original omission/attribution problem, but the mapped repair facts have a different evidence/context defect. The canonical JSON contains the complete 61-row matrix.

## Custody

```text
reviewed commit: bf59bddcfe2a4027c86507491f782aa9fe027b7c
reviewed tree:   af96133b9e6fe8ce4888a5273c2242152419f4a5
reference JSON:  a9689592ed1ce05c2549269bfdc1bfa328e27e9f3644c0de5e825ef644f28d24
reference MD:    2bd127567328f8df46baa471312596ceb503a909d2f34d73a5a1e3f93d539b74
```

No existing D1 reference/review/adjudication artifact was modified by this semantic review.
