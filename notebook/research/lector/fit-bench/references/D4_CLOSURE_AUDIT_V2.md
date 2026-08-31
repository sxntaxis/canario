# D4 Closure Audit

**Final verdict:** `CLOSURE_PASS_NO_DISPUTES`  
**Hard findings:** 0  
**Systemic class found:** No  
**Recommended next action:** Governance/freeze decision; no further broad audit.

## Custody

The custody identities below are reproduced from `CUSTODY/CUSTODY.json` without alteration.

| Field | Value |
|---|---|
| `fixture` | `D4` |
| `fixture_id` | `CR-CGR-SANTA-ANA-PROCUREMENT-AUDIT-001` |
| `reference_commit` | `a3fd4cd73bab241d0797cb84b2b3f52729bc498b` |
| `reference_file` | `D4_REFERENCE_SUPERVISOR_DRAFT_V2.json` |
| `reference_sha256` | `042c08443f1083adc0d11e1123471529d1a42619d7f5993754eb6459e7cc5e76` |
| `reference_bytes` | `1196145` |
| `reference_state` | `SUPERVISOR_DRAFT` |
| `fact_count` | `289` |
| `evidence_target_count` | `368` |
| `source_pack_sha256` | `eb729446edb1c698cc0ea3ecc6e92a1cf3cf217a24bea6320c744e919699f7ae` |
| `source_pack_bytes` | `1790561` |
| `primary_source_sha256` | `587e4ba2ca65c4a3f453471434ca69b41ba71fe59ae64897590b1fc6c44c97fe` |
| `representation_sha256` | `324dfd50e4cee6619bf0f8cbce223004bc34bd9d980cad90823f3a195111893d` |
| `scope_sha256` | `324dfd50e4cee6619bf0f8cbce223004bc34bd9d980cad90823f3a195111893d` |
| `unit_inventory_sha256` | `b4c45ebccf7bfc4ec02d902aaa96b7f968bcc07719b40ceef28c79985bf1c5b4` |
| `unit_count` | `260` |
| `independence_policy` | `fresh_webchat_execution_independence=True; if_openai_gpt_5_6_family=WEAK_OR_UNKNOWN; strong_gate=False; human_gate=False` |

Direct identity checks for the reference, source pack, primary PDF, source Representation, and unit inventory matched the declared custody values. `scope_sha256` is the benchmark selected-text/source-Representation identity recorded inside `SOURCE/scope.json`; it is not the byte hash of the `scope.json` file itself.

## Reviewer and independence

- Reviewer: OpenAI, `GPT-5.6 Sol`
- Execution context: single fresh temporary ChatGPT webchat
- Independence: `WEAK_OR_UNKNOWN`
- Basis: the supplied policy explicitly requires `WEAK_OR_UNKNOWN` for OpenAI/GPT-5.6-family reviewers; fresh-chat execution is not materially independent model assurance.

The reference was not edited. No repository files were mutated, no commits were created, and Lector was neither implemented nor run. A0-A5 candidate outputs/scores, Acta 160, H2, production Lector output, and thresholds were not inspected.

## Phase 0 — primary-source literal checks

**Result: PASS (2/2).**

1. **`D4-PRIMARY-FOOTNOTE4` — PASS.** Frozen PDF page 16 visibly shows civic quantity **10** followed by superscript footnote marker **4**, not civic quantity 104. Footnote 4 gives the breakdown **5 / 4 / 1**: five proveedor único, four reparaciones indeterminadas, and one bienes o servicios artísticos, culturales e intelectuales. The `104` in the text Representation is therefore an extraction artifact.
2. **`D4-PRIMARY-ACTIVO-MOTIVADO` — PASS.** Frozen PDF page 15, Cuadro n.° 2, literally prints **“activo motivado”**. A separate report occurrence at Representation chars 6959–7206 prints **“acto motivado”**. The audit preserves this internal wording conflict; the table is not silently normalized.

No hard source-fidelity finding was confirmed.

## Phase 1 — full source→reference sweep

**Result: PASS.** All **260/260** scoped source units (`U0001` through `U0260`) were reviewed in source order against `REFERENCE/REFERENCE_COVERAGE_INDEX.json`. The sweep checked preservation of actor, modality, condition, reason, scope, negation, quantity/time, procedural/finality status, and attribution.

Checkpoint:

- scoped units reviewed: **all 260/260**
- source-order completion: **complete**
- candidate omissions after complete coverage-index search: **0**
- confirmed hard omissions: **0**
- semantic unit checkpoint: **170** material-fact units, **88** no-material-civic-fact units, **2** context-only units, **0** unresolved units
- coverage index: **289 facts**; reference: **368 evidence targets**

Ceremonial/page furniture, exact repeats, extraction artifacts, derived arithmetic, and completions requiring guessing were excluded as directed. Executive/conclusion/disposition restatements were searched across the complete coverage index before any omission decision. The page-16 `104` extraction artifact was resolved from the frozen image as `10` + superscript footnote `4`; the page-15 `activo motivado` / separate `acto motivado` source conflict was retained. The graphic occurrence `16 expedientes` is likewise preserved literally rather than normalized to a separate 15-procedure count elsewhere in the report.

**Phase 1 hard findings: none.**

## Phase 2 — bounded reverse audit

**Result: PASS — `80/80`.** Every sampled fact was checked for source entailment, attribution/provenance, modality, conditions/reasons/negation, referent resolution, temporal/quantitative qualifiers, evidence sufficiency, minimality, and absence of a stronger claim than the source.

All **115** embedded evidence entries also matched their declared Representation character ranges and `selected_text_sha256` values exactly.

Sampled facts, all PASS:

`D4-F0003` `D4-F0005` `D4-F0007` `D4-F0011` `D4-F0014` `D4-F0024` `D4-F0025` `D4-F0026` `D4-F0028` `D4-F0030` `D4-F0032` `D4-F0034` `D4-F0039` `D4-F0042` `D4-F0050` `D4-F0059` `D4-F0060` `D4-F0061` `D4-F0062` `D4-F0063` `D4-F0064` `D4-F0065` `D4-F0066` `D4-F0067` `D4-F0071` `D4-F0083` `D4-F0087` `D4-F0106` `D4-F0110` `D4-F0112` `D4-F0117` `D4-F0120` `D4-F0121` `D4-F0123` `D4-F0126` `D4-F0152` `D4-F0163` `D4-F0178` `D4-F0185` `D4-F0202` `D4-F0203` `D4-F0208` `D4-F0213` `D4-F0216` `D4-F0218` `D4-F0220` `D4-F0235` `D4-F0239` `D4-F0240` `D4-F0241` `D4-F0242` `D4-F0243` `D4-F0244` `D4-F0245` `D4-F0248` `D4-F0249` `D4-F0253` `D4-F0254` `D4-F0255` `D4-F0265` `D4-F0269` `D4-F0274` `D4-F0292` `D4-F0293` `D4-F0294` `D4-F0296` `D4-F0297` `D4-F0302` `D4-F0308` `D4-F0324` `D4-F0333` `D4-F0336` `D4-F0337` `D4-F0340` `D4-F0342` `D4-F0346` `D4-F0355` `D4-F0356` `D4-F0366` `D4-F0368`

Special source-fidelity resolutions within the sample:

- `D4-F0067`: PASS. The table literal `activo motivado` and separate executive-summary `acto motivado` occurrence remain explicit; the latter independently supports the semantic fact without silently altering the table.
- `D4-F0218`: PASS. Frozen page 16 resolves extracted `104` as visible 10 plus superscript footnote marker 4.
- `D4-F0220`: PASS. Frozen page 16/footnote 4 supports the 10-case total and the 5/4/1 breakdown.

**Phase 2 hard findings: none.** No expansion to a full reverse audit was warranted.

## Systemic-class analysis

**Systemic class found: No.** There are zero confirmed hard semantic/source-fidelity findings and therefore zero confirmed affected facts. The supplied systemic threshold (normally at least three confirmed affected facts across at least two structures/source regions, or a demonstrated repeated shared transformation with plausible wider reach) is not met.

## Hard findings

None. `hard_finding_count = 0`.

## Final disposition

- Verdict: `CLOSURE_PASS_NO_DISPUTES`
- Phase 0: `PASS`
- Phase 1: complete, `260/260`, no candidate or confirmed hard omissions
- Phase 2: `80/80`, all PASS
- Independence: `WEAK_OR_UNKNOWN`
- Next action: **Governance/freeze decision; no further broad audit.**
