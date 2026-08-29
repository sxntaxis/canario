---
id: CANARIO-LECTOR-FIT-BENCH-D1-REFERENCE-SUPERVISOR-DRAFT-002
kind: benchmark-reference-candidate
state: supervisor-draft
authority: active-work-evidence
work: LECTOR-PRODUCTION-FIT-BENCH
fixture: CR-ESPARZA-MINUTES-001
protocol: CANARIO-LECTOR-FIT-BENCH-REFERENCE-PROTOCOL-FREEZE-002
method: CANARIO-LECTOR-FIT-BENCH-REFERENCE-AUTHORING-METHOD-001
supersedes: CANARIO-LECTOR-FIT-BENCH-D1-REFERENCE-SUPERVISOR-DRAFT-001
---

# D1 semantic reference — supervisor draft v2

This is the supervising/cloud author's revised semantic reference candidate for the exact frozen D1 development fixture:

> Acta Sesión Ordinaria N.º 161 — 18 May 2026, Concejo Municipal de Esparza.

It is **not frozen gold** and is not eligible for A0–A5 scoring.

## Why v2 exists

D1 v1 was mechanically certified unchanged at `6aac2af5802996b8c17c612107f6771e0e612318`.
A separate clean-context review at `eaf74f8f65c5f98b79afaa185bc75baa24ac094c` then completed full
source→reference and reference→source review of all 36 structures, 61 units, 660 v1 facts and 1,240 evidence
targets. It returned `REFERENCE_DISPUTE` with 61 hard findings.

The reviewer was also OpenAI GPT-5.6 Sol, so its recorded independence strength is correctly
`WEAK_OR_UNKNOWN`; it does not satisfy the strong materially-independent gate. Its disputes are nevertheless
valid review evidence and were adjudicated one-by-one from the exact frozen source.

The supervising author accepted all 61 disputes on source/protocol grounds:

```text
accepted                              61
rejected                               0
unresolved                             0
source->reference findings            38
reference->source findings            23
```

The canonical adjudication record is `D1_INDEPENDENT_REVIEW_ADJUDICATION_V1.json`.

## What changed

The 61 findings collapse into four substantive repair families:

1. **Missing procedural assertions.** Forty material assertions were added, including 33 explicit
   unanimous/finality outcomes, two no-observation outcomes for Acts 158/159, repeated reminder-agreement
   history in C13, U04 proposal/acceptance context, the source-attributed U06 ministerial-effort statement and
   the M01 five-minute recess.
2. **Named-speaker evidence.** Facts that resolved role-only `Presidente Municipal` or `Alcalde` statements to
   Juan Carlos Zeledón or Bienvenido Venegas now bind exact source identity evidence. The two Mariela Cruz
   facts bind the exact local GOT-ZLMT-130-2026 authorship text rather than the reviewer's generic roster
   example.
3. **Formal-decision evidence.** Decomposed operative subfacts in C05, C06, M01 and M03 now also bind the local
   `SE ACUERDA` context needed to establish Concejo actor/status.
4. **Antecedent/qualifier repairs.** C05 now binds the pool-regulation antecedent; U04 preserves the stated
   importance-of-route rationale and separately preserves proposal/acceptance; V05 resolves the project,
   bridge, site and paradero references to the Mata de Limón bridge context.

Ten v1 facts whose semantic notes required actual rewrite were retired from the live v2 fact set and replaced
with new provenance-preserving IDs. Evidence-only repairs retain their existing fact IDs.

## Final v2 draft size

```text
facts                              700
evidence targets                  1473
semantic carriers                   36
frozen units                        61
cross-unit facts                   349
CTX-01 facts                       315
multi-evidence facts               588
new/replacement v2 facts            50
retired v1 facts                    10
independent-review disputes          61
unresolved disputes                   0
```

The fact-count increase is a consequence of restoring material assertions omitted by v1. It is not a target.

## Identity boundary

The draft remains bound to the exact frozen D1 identities:

- primary PDF SHA256 `ffb354c67d8b56ebf265884c820a98fee27015cadaac3ea1011069f7969b8bfd`;
- Representation SHA256 `02d1578cfc44097c6e5e802880919ff6f7a18bd2105330035959c4cccd467ea1`;
- benchmark scope SHA256 `25d3bb9dd604109e1d01b7465f11c88a35a2adb26a388a0dd4ef48842cb9c3a5`;
- unit inventory SHA256 `0a2f76f1e737acb82a3430b7d6a7b1394525d9502dc4163298d45e3d6f4cf3de`;
- unit count `61`;
- exact recovery transport SHA256 `ace4020b156888474ef7097b98e405756abbb1e1d06366165ab796d1593a5fbf`.

`U0007` remains the only unit classified `NO_MATERIAL_CIVIC_FACT`; it contains only the isolated page marker
`1`.

## Author-time v2 validation

The revised materialization was reopened against the exact 151,940-character Representation after the dispute
repairs. Author-time checks report:

```text
facts / evidence targets           700 / 1473
structures / frozen units           36 / 61
duplicate fact IDs                         0
duplicate canonical notes                  0
duplicate reverse-audit notes              0
empty evidence                              0
scope / structure escapes                   0
mid-word selector boundaries                0
selected-text hash mismatches               0
unit-map mismatches                         0
unknown capability IDs                      0
FID-01 bindings                             0
unaccounted units / structures              0 / 0
unresolved review disputes                  0
```

This is still author-time evidence. Local mechanical certification must independently reopen the exact v2
candidate and run the repository checks without changing semantics.

## Review boundary

The prior separate-session review **cannot certify v2**, because v2 did not exist when that review ran. After
mechanical certification, v2 therefore requires a fresh full semantic review. If that review is again an OpenAI
GPT-5.6 Sol session, its independence must remain truthfully `WEAK_OR_UNKNOWN`; it may find defects but cannot
satisfy the strong materially-independent gate by itself.

```text
v1 mechanical certification          complete
v1 separate-session semantic review  REFERENCE_DISPUTE
v1 disputes adjudicated               61 / 61
v2 local mechanical certification     pending
v2 fresh semantic review              pending
reference frozen                      false
```

## Leakage / maturity

```text
formal_A0_A5_output_seen             = false
formal_candidate_scores_seen         = false
Acta_160_semantics_inspected         = false
H2_selected_or_inspected             = false
thresholds_frozen                    = false
production_implementation_authorized = false
```

No A0–A5 lane, threshold freeze, Acta-160 inspection, H2 selection or production-Lector implementation is
authorized by this revision.
