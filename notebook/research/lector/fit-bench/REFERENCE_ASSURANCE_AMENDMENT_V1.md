---
id: REFERENCE-ASSURANCE-AMENDMENT-001
kind: benchmark-reference-governance-amendment
state: FROZEN
created: 2026-08-30
authority: LECTOR-PRODUCTION-FIT-BENCH
supersedes: reference-state/assurance coupling in REFERENCE_PROTOCOL_FREEZE_V2
---

# Reference assurance amendment v1

## Decision

Reference **immutability** and reference **independence assurance** are separate axes.

`REFERENCE_PROTOCOL_FREEZE_V2.md` remains authoritative for source fidelity, semantic inclusion, evidence, leakage, review, dispute handling and candidate-defect behavior except where this amendment explicitly changes the lifecycle/assurance coupling.

The benchmark now recognizes:

```text
FROZEN_INTERNAL
FROZEN_STRONG
```

### `FROZEN_INTERNAL`

An immutable development reference whose semantics are sufficiently saturated for controlled internal fit-bench use, but whose materially-independent reviewer gate is not satisfied.

Required:

- frozen source, Representation, scope and unit inventory;
- exhaustive supervising-author source-order/reference construction;
- exact local mechanical certification of all evidence selectors;
- all known semantic-review disputes source-adjudicated to zero unresolved hard findings;
- at least one mature bidirectional semantic review performed blind to formal tested output;
- explicit closure evidence showing no demonstrated systemic error class after bounded final review;
- broad semantic iteration closed by an explicit stop rule;
- formal candidate output/scores unseen;
- independence limitation recorded truthfully;
- immutable canonical semantic digest and evidence-reopening proof.

Consequences:

- counts/capability distribution may be inspected after this freeze;
- threshold policy may be derived from reference-only information once the other required development references are equivalently frozen;
- formal development A0–A5 runs may later use the fixture after all benchmark pre-run gates close;
- resulting evidence is `INTERNAL_FIT_EVIDENCE`, not strong materially-independent selection evidence;
- this state does not authorize production implementation or provider/model lock-in.

### `FROZEN_STRONG`

A frozen reference that also satisfies the materially-independent semantic-review path required by v2. Evidence from this state may contribute to strong final selection certification subject to the other benchmark/holdout gates.

## Strong-selection boundary

A `FROZEN_INTERNAL` fixture may influence development comparison, mechanism design rejection and threshold setting, but **a final selection may not be called strong solely from overlapping-author/reviewer evidence**.

If strong material independence remains unavailable at final selection time, the project must make a separate explicit governance decision about promotion risk. It may not silently reinterpret `WEAK_OR_UNKNOWN` as independence.

## Reference-defect rule

The v2 `REFERENCE_DEFECT` rule remains unchanged. Candidate output that reveals a frozen-reference defect invalidates that fixture's formal score for the affected round. Repair requires an explicit Reference-Defect Research Interrupt, re-freeze, and threshold/rerun handling as applicable.

`FROZEN_INTERNAL` is therefore immutable for ordinary iteration, not infallible.

## D1 application

`CR-ESPARZA-MINUTES-001` qualifies for `FROZEN_INTERNAL` after D1 v10 because:

- 61/61 units and 36 structures are accounted;
- 789 facts / 2,035 exact evidence targets mechanically reopen;
- all accumulated review disputes are source-adjudicated with zero unresolved findings;
- the mature sharded v8 review covered 61/61 units, 783/783 reverse facts and 2,019/2,019 evidence targets;
- the v9 closure audit swept 61/61 units, audited a deterministic 125/125 reverse sample, regression-checked 10/10 repairs, found only three localized defects and no systemic class;
- v10 repaired exactly those three closure findings and passed exact mechanical certification;
- formal A0–A5 outputs/scores remain unseen;
- Acta 160 and H2 remain untouched;
- independence remains `WEAK_OR_UNKNOWN`; strong/human gates remain false.

No further broad D1 semantic audit is authorized by this amendment.
