---
id: CANARIO-LECTOR-FIT-BENCH-D1-REFERENCE-SUPERVISOR-DRAFT-003
kind: benchmark-reference-candidate
state: supervisor-draft
authority: active-work-evidence
work: LECTOR-PRODUCTION-FIT-BENCH
fixture: CR-ESPARZA-MINUTES-001
protocol: CANARIO-LECTOR-FIT-BENCH-REFERENCE-PROTOCOL-FREEZE-002
method: CANARIO-LECTOR-FIT-BENCH-REFERENCE-AUTHORING-METHOD-001
supersedes: CANARIO-LECTOR-FIT-BENCH-D1-REFERENCE-SUPERVISOR-DRAFT-002
---

# D1 semantic reference — supervisor draft v3

D1 v3 repairs the mechanically certified D1 v2 after its fresh-context secondary semantic audit.

It is **not frozen gold** and is not eligible for formal A0–A5 scoring.

## Review result

```text
v2 structures / units             36 / 61
v2 facts / evidence targets      700 / 1473
source->reference disputes         0
reference->source disputes        23
EVIDENCE_INSUFFICIENT             19
CONTEXT_ERROR                      3
SOURCE_FIDELITY_ERROR              1
```

All 23 disputes were accepted after reopening the exact frozen source. No new material assertion was added.
Thirty-three v2 facts were retired/replaced because their semantic note itself needed to become
self-sufficient; evidence-only repairs retain their IDs. Genuine source ambiguity remains explicit, including
C06 `ellos`.

## Final v3 inventory

```text
facts                             700
evidence targets                 1566
structures / units                 36 / 61
cross-unit facts                  381
CTX-01 facts                      348
AMB-01 facts                        6
multi-evidence facts              599
retired v2 / replacement v3       33 / 33
unresolved disputes                 0
```

Frozen identities remain unchanged:

```text
PDF            ffb354c67d8b56ebf265884c820a98fee27015cadaac3ea1011069f7969b8bfd
Representation 02d1578cfc44097c6e5e802880919ff6f7a18bd2105330035959c4cccd467ea1
scope          25d3bb9dd604109e1d01b7465f11c88a35a2adb26a388a0dd4ef48842cb9c3a5
units          0a2f76f1e737acb82a3430b7d6a7b1394525d9502dc4163298d45e3d6f4cf3de / 61
```

`U0007` remains `NO_MATERIAL_CIVIC_FACT` because it contains only the isolated page marker `1`.

Author-time reopening reports zero duplicate IDs/semantic notes/reverse-audit notes, empty evidence, selector
hash failures, scope/structure escapes, mid-word boundaries, unit-map failures, unknown capability IDs,
`FID-01` bindings, unaccounted units/structures, or unresolved review disputes.

The next gate is exact local mechanical certification of v3, followed by another fresh semantic audit.
