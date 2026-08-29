---
id: CANARIO-LECTOR-FIT-BENCH-D1-REFERENCE-SUPERVISOR-DRAFT-001
kind: benchmark-reference-candidate
state: supervisor-draft
authority: active-work-evidence
work: LECTOR-PRODUCTION-FIT-BENCH
fixture: CR-ESPARZA-MINUTES-001
protocol: CANARIO-LECTOR-FIT-BENCH-REFERENCE-PROTOCOL-FREEZE-002
method: CANARIO-LECTOR-FIT-BENCH-REFERENCE-AUTHORING-METHOD-001
recovered_from: 8f3a5e0fa0d19e80b8721fae6db3d151b4ec8902
---

# D1 semantic reference — supervisor draft v1

This is the supervising/cloud author's semantic reference candidate for the exact frozen D1 development fixture:

> Acta Sesión Ordinaria N.º 161 — 18 May 2026, Concejo Municipal de Esparza.

It is **not frozen gold** and is not eligible for A0–A5 scoring.

## Recovery boundary

D1 authoring crossed a conversation context limit before a final reference existed. The emergency checkpoint
`8f3a5e0fa0d19e80b8721fae6db3d151b4ec8902` correctly recorded itself as WIP/non-authoritative:

```text
runnable builder specs          328
separate fragment specs          78
valid prior final fact count     NONE
final reference                  NO
```

The 328 and 78 records are **not** added together as a prior semantic baseline because the separate fragment
could overlap or revise the runnable builder. A later narrative count around 380 was also not reproducibly
materialized. This v1 therefore does not pretend to continue an artifact that did not exist.

Recovery used the exact frozen D1 Representation, structure-local sentence coordinates and 61-unit inventory.
Known incomplete/evidence-shifted carriers were re-authored from source, the missing M02–V05 tail was authored
from source, and the complete result then received omission-only and reverse-semantic/evidence-context passes.
The machine-readable review record is `D1_SUPERVISING_AUTHOR_ADVERSARIAL_REVIEW_V1.json`.

## Final draft size

```text
facts                              660
evidence targets                  1240
semantic carriers                   36
frozen units                        61
cross-unit facts                   250
CTX-01 facts                       221
multi-evidence facts               517
supervising-author findings         38
unresolved semantic structures       0
```

`CTX-01` is deliberately narrower than the cross-unit fact count. Under the frozen protocol it is bound only
when faithful interpretation consumes required context outside the fact's local frozen unit/semantic segment;
a fact merely touching more than one unit does not automatically exercise CTX.

## Identity boundary

The draft remains bound to the exact F2 D1 identities:

- primary PDF SHA256 `ffb354c67d8b56ebf265884c820a98fee27015cadaac3ea1011069f7969b8bfd`;
- Representation SHA256 `02d1578cfc44097c6e5e802880919ff6f7a18bd2105330035959c4cccd467ea1`;
- benchmark scope SHA256 `25d3bb9dd604109e1d01b7465f11c88a35a2adb26a388a0dd4ef48842cb9c3a5`;
- unit inventory SHA256 `0a2f76f1e737acb82a3430b7d6a7b1394525d9502dc4163298d45e3d6f4cf3de`;
- unit count `61`;
- exact recovery transport SHA256 `ace4020b156888474ef7097b98e405756abbb1e1d06366165ab796d1593a5fbf`.

The full frozen 151,940-character Representation remains the benchmark scope.

## Recovery and adversarial review

The self-adversarial review records 38 findings:

```text
PASS_1_RECOVERY   19
PASS_2_OMISSION    5
PASS_3_REVERSE    14
```

The recovery pass does not assert a semantic delta from a nonexistent prior final reference. It records instead
which recoverable WIP carriers had to be re-authored and which source tail had never reached a reproducible
final build.

Representative repairs include:

- decomposing the four distinct CCPJ support requests in C04;
- rebuilding C05 from the complete CGR complaint/pool discussion rather than retaining shifted selectors;
- re-authoring C06, C07, C10, C12, U03 and M01 where WIP evidence or decomposition was unreliable;
- authoring the missing M02–M07 and V01–V05 tail from the frozen source;
- restoring the stated purpose of the Gollo fair, the published origin of the ZMT controversy, formal receipt
  of C14 and the resolved speed-reducer status in V01;
- repairing antecedent evidence for school identities, route 756, expediente 23.898, the 12 June date and
  DFOE-LOC-0239;
- splitting M03's final notification and Administration-transfer actions instead of counting one combined
  proposition twice;
- preserving the source's literal `miércoles 20` / `miércoles` temporal wording where the source itself does
  not state a month inside the relevant assertion.

## Final quality invariants

Author-time validation over the final materialized JSON reports:

```text
FID-01 bindings                         0
all-15 capability templates             0
duplicate canonical notes               0
duplicate reverse-audit notes           0
generic qualifier placeholders          0
string-valued false qualifiers           0
note == single evidence                 0
empty/zero evidence                      0
scope escapes                            0
structure escapes                        0
mid-word selector boundaries             0
facts without units                      0
unknown capability IDs                   0
unaccounted units                        0
unaccounted structures                   0
material carriers without facts          0
```

All 1,240 evidence targets reopen by exact Representation coordinates and selected-text SHA256 in the author-time
validator. `U0007` is the only frozen unit without a material fact; its entire content is the isolated page marker
`1`, so it is explicitly classified `NO_MATERIAL_CIVIC_FACT` rather than silently ignored.

This is still an author-time check, not the independent local mechanical certification required by the protocol.

## Review boundary

This draft and its adversarial review were written by the same supervising/cloud author. The review is explicitly
**self-adversarial, not materially independent**.

```text
supervising_author_adversarial_review = complete
local_mechanical_certification_v1     = pending
independent_semantic_review            = still required
reference_frozen                       = false
```

Local execution may reopen selectors/hashes, run repository checks, reparent the exact semantic delta if needed,
create bundles and push the unchanged candidate. It may not rewrite D1 semantics.

## Leakage / maturity

```text
formal_A0_A5_output_seen             = false
formal_candidate_scores_seen         = false
Acta_160_semantics_inspected         = false
H2_selected_or_inspected             = false
thresholds_frozen                    = false
production_implementation_authorized = false
```

A successful local mechanical certification advances evidence only. It does not freeze D1, authorize candidate
lane execution, or substitute for the materially independent big-model semantic review.
