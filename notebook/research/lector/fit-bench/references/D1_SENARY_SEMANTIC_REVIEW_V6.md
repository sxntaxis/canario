# D1 senary semantic review v6

- Fixture: `CR-ESPARZA-MINUTES-001`
- Reviewed candidate: `87cc3a1eeef8b95f49abb2a671f84f7653040883`
- Reviewer: `OpenAI / GPT-5.6 Sol`
- Independence: `WEAK_OR_UNKNOWN`; strong independent gate `false`; human independence gate `false`
- Anchoring contamination: `false`
- Verdict: **`REFERENCE_DISPUTE`**

## Coverage

- Structures: `36 / 36`
- Frozen units: `61 / 61`
- Unit states: `61 / 61`
- Facts: `759 / 759`
- Evidence targets: `1939 / 1939`
- Identity/provenance classifications: `759 / 759`
- Deictic/antecedent matrix rows: `447`
- Qualifier/capability facts checked: `759`

## Blind provisional persistence

- Finding groups: `22`
- SHA-256: `4c1dc41a035513384164f2f79aff1b156082fa943e7b28974bc93591dd053580`
- Persisted before any v5 quinary review/adjudication content was opened.

## Global scan summaries

- Lexical/semantic forcing clauses reviewed: `239`; material covered `215`; material missing `14`.
- Forward completeness: `22` omitted independent assertions across `15` units.
- Identity/provenance: resolver required `699`, resolver bound `691`, unsupported `8`.
- Qualifier/capability mismatches: `2`.
- Unit-state disputes: `0`; temporal errors: `0`; quantitative errors: `0`; duplicate/decomposition hard findings: `0`.

## Findings

Total hard groups: **22** — SOURCE_TO_REFERENCE `18`, REFERENCE_TO_SOURCE `4`, UNIT_STATE `0`.

| ID | Direction | Issue | Summary |
|---|---|---|---|
| `D1-V6-IR-0001` | `SOURCE_TO_REFERENCE` | `MISSING_MATERIAL_ASSERTION` | Fernando Villalobos’s recurrence/causal explanation is not represented as a complete proposition. |
| `D1-V6-IR-0002` | `SOURCE_TO_REFERENCE` | `MISSING_MATERIAL_ASSERTION` | The presidential response omits independent positions of respect, non-devaluation, and institutional commitment. |
| `D1-V6-IR-0003` | `SOURCE_TO_REFERENCE` | `MISSING_MATERIAL_ASSERTION` | Douglas Arce’s specific negative evaluation of reviewing denial-recommended ZMT matters in the Concejo is omitted. |
| `D1-V6-IR-0004` | `SOURCE_TO_REFERENCE` | `MISSING_MATERIAL_ASSERTION` | Flor Cubero’s causal assessment that lengthy files and study time had also hindered commission functioning is omitted. |
| `D1-V6-IR-0005` | `SOURCE_TO_REFERENCE` | `MISSING_MATERIAL_ASSERTION` | Two independent public-safety/status assessments by Heriberto Alvarado are omitted. |
| `D1-V6-IR-0006` | `SOURCE_TO_REFERENCE` | `MISSING_MATERIAL_ASSERTION` | Bienvenido Venegas’s recommendation that the community directly present incidents, with its stated timing rationale, is omitted. |
| `D1-V6-IR-0007` | `SOURCE_TO_REFERENCE` | `MISSING_MATERIAL_ASSERTION` | Flor Cubero’s reason for proposing a district security network is omitted. |
| `D1-V6-IR-0008` | `SOURCE_TO_REFERENCE` | `MISSING_MATERIAL_ASSERTION` | Ronald Robles’s explicit position that it was important to retake the topic, and his attached reason, is omitted. |
| `D1-V6-IR-0009` | `SOURCE_TO_REFERENCE` | `MISSING_MATERIAL_ASSERTION` | Douglas Arce’s plenary-time/agenda rationale for visiting deputies in San José is omitted. |
| `D1-V6-IR-0010` | `SOURCE_TO_REFERENCE` | `MISSING_MATERIAL_ASSERTION` | Bienvenido Venegas’s explicit endorsement of the proposals, including agreement with Douglas under time pressure, is omitted. |
| `D1-V6-IR-0011` | `SOURCE_TO_REFERENCE` | `MISSING_MATERIAL_ASSERTION` | The mayor’s channel/timing rationale for coordinating faction-chief audiences is omitted. |
| `D1-V6-IR-0012` | `SOURCE_TO_REFERENCE` | `MISSING_MATERIAL_ASSERTION` | The source-visible uncertainty attached to the proposed June 12 extraordinary session is omitted. |
| `D1-V6-IR-0013` | `SOURCE_TO_REFERENCE` | `MISSING_MATERIAL_ASSERTION` | Luis Diego Estrada’s explicit expectation that campaign statements could be fulfilled is omitted. |
| `D1-V6-IR-0014` | `SOURCE_TO_REFERENCE` | `MISSING_MATERIAL_ASSERTION` | A reported third-party position that unspecified persons were pleased Esparza’s name was being positioned is omitted. |
| `D1-V6-IR-0015` | `SOURCE_TO_REFERENCE` | `MISSING_MATERIAL_ASSERTION` | Luis Diego Estrada’s explicit institutional-responsibility assessment is omitted. |
| `D1-V6-IR-0016` | `SOURCE_TO_REFERENCE` | `MISSING_MATERIAL_ASSERTION` | Flor Cubero’s explicit stance that she would have to accommodate herself to ICODER’s position despite disagreement is omitted. |
| `D1-V6-IR-0017` | `SOURCE_TO_REFERENCE` | `MISSING_MATERIAL_ASSERTION` | Fernando Villalobos’s procedural proposal to adopt an agreement that same day is omitted. |
| `D1-V6-IR-0018` | `SOURCE_TO_REFERENCE` | `MISSING_MATERIAL_ASSERTION` | Douglas Arce’s explicit evaluation of the U-8 championship achievement is omitted. |
| `D1-V6-IR-0019` | `REFERENCE_TO_SOURCE` | `ATTRIBUTION_ERROR` | The four facts carry canonical attribution to the Contraloría General de la República without binding the quoted correspondence’s sender/provenance in their own complete evidence sets. |
| `D1-V6-IR-0020` | `REFERENCE_TO_SOURCE` | `QUALIFIER_ERROR` | D1-F0310 states an unconditional monitoring role, but the source presents it inside a conditional proposed camera-coordination scenario and uses conditional “sería”. |
| `D1-V6-IR-0021` | `REFERENCE_TO_SOURCE` | `MODALITY_ERROR` | D1-F0784 strengthens “me parece que ...” into an unqualified assertion. |
| `D1-V6-IR-0022` | `REFERENCE_TO_SOURCE` | `ATTRIBUTION_ERROR` | The four M07 decision facts normalize the actor to “Concejo Municipal de Esparza” without an Esparza council resolver in their own evidence sets. |

## v5 quinary regression

- `RESOLVED_IN_V6`: **30**
- `STILL_PRESENT`: **0**
- `PARTIALLY_RESOLVED`: **0**
- `REGRESSED_DIFFERENTLY`: **0**
- The 15 repair facts `D1-F0793`–`D1-F0807` were rechecked individually; all 15 pass semantic sufficiency and introduce no duplicate/unsupported-strengthening defect.
- The senary findings are independently new. `D1-V6-IR-0019` is analogous to the prior CGR provenance repair family and `D1-V6-IR-0022` to the prior Concejo identity family, but the v5 affected facts themselves are resolved.

## Status

D1 v6 remains `SUPERVISOR_DRAFT`. This review does not freeze or relabel the reference, and the reviewer does not satisfy a strong or human independence gate.
