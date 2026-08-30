# Canario Lector production fit bench

Kind: work
Status: active
Created: 2026-08-27
Activated: 2026-08-27
Authority: owner-approved after governance merge 45997d5088f88ef75e00f08a310e84292a4a077b

## ELI5

Canario already has the safe pipe that accepts semantic proposals and stores evidence-backed Claims.

What it does **not** yet know is the best way to read a long civic source comprehensively.

This Work does not build the final Lector. It runs a controlled contest:

```text
same sources
same frozen reference
same model/provider where possible
same evidence rules

A0 simple whole-document read
A1 local chunks
A2 repeated local passes
A3 contextual staged extraction
A4 contextual extraction + explicit coverage repair + reconciliation
A5 dynamic/agentic decomposition challenger
```

The **simplest approach that passes every frozen semantic gate wins**.

Only a later separately authorized Work may implement that winner as the production broad Lector.

## Goal

Select or reject a production orchestration strategy for broad civic source extraction using a
Canario-native, leakage-resistant fit bench.

## Pressure

LECTOR-001 certifies the bounded extraction/persistence boundary but explicitly does not certify
semantic quality. The superseded LECTOR-002 campaign was stopped before replacement gold because its
structured semantic capability model conflated extraction, retrieval, composition and verification.
That reasoning split has since been resolved and certified.

The interrupted first vertical then exposed the remaining open gate: no production broad-Claim
extractor has been selected or certified.

Research through 2026-08-27 shows that:

- schema-valid output and exact quotes do not establish completeness or faithfulness;
- whole-document long-context calls can omit material facts;
- naive independent chunking can destroy dependencies/context;
- maximal atomization can remove necessary meaning;
- repeated passes can improve recall but may repeat systematic blind spots;
- structured-output breadth can itself degrade semantic quality;
- LLMs can silently "correct" source material from parametric knowledge;
- English performance does not establish Spanish institutional performance.

## Authority / prerequisites

Activation prerequisite satisfied: governance reconciliation is accepted/merged through PR #9 at `45997d5088f88ef75e00f08a310e84292a4a077b`.

Research basis:
- current accepted Canario contracts and LECTOR-001;
- historical/superseded LECTOR-002 corpus and reference protocol;
- `CANARIO-LECTOR-PRODUCTION-READINESS-SYNTHESIS-001`;
- its Source Books, fit matrix, gap audit and adversarial review.

## Scope

### 1. Freeze replacement benchmark semantics

Define exact candidate capability IDs for at least:

- civic coverage / recall;
- civic focus / precision;
- source entailment / faithfulness;
- self-sufficient minimality;
- attribution preservation;
- conditions / exceptions / scope;
- negation / modality;
- temporal preservation;
- quantitative exactness;
- ambiguity behavior;
- cross-unit context;
- duplicate/conflict reconciliation;
- source-fidelity counterfactuals.

These names remain provisional until this Work freezes them.

### 2. Freeze reference protocol

Use the current leakage controls frozen in `notebook/research/lector/fit-bench/REFERENCE_PROTOCOL_FREEZE_V2.md`:

```text
freeze source + Representation + scope + units
-> supervising-author source-exhaustive reference
-> omission-only + reverse semantic audit
-> local mechanical evidence/hash certification
-> materially independent semantic audit
-> reference freeze
-> inspect fact counts
-> threshold freeze
-> only then tested extraction
```

The project owner is not required to perform fact-by-fact clerical annotation. Human review is reserved for unresolved reference disputes/ambiguity or bounded independent spot-checks. Reference entries remain semantic fact-equivalence objects, not one mandatory sentence.

### 3. Freeze development versus holdout split

Development/reference-design:
- Acta 161;
- existing INCOP correspondence;
- selected Spanish normative/contractual source;
- selected report/audit/technical source.

Typed structured/media capabilities remain separate lanes.

Natural holdouts:
- Acta 160 is reserved for the post-selection end-to-end vertical;
- at least one non-minutes Spanish civic holdout must be selected/frozen before production candidate
  finalization.

Holdout semantic contents may not be used for tuning.

### 4. Run mechanism comparison

Required baseline/challenger set unless research proves a lane strictly redundant before candidate
output is seen:

- A0 whole-document one-shot;
- A1 deterministic structure-aware units, one pass;
- A2 repeated independent unit passes;
- A3 contextual selection/disambiguation/decomposition;
- A4 contextual extraction + explicit coverage audit + targeted repair + semantic reconciliation;
- A5 dynamic agentic decomposition/optimization challenger.

### 5. Measure quality and cost separately

Primary hard semantic dimensions:
- reference-fact coverage;
- material-civic focus;
- unsupported/overstated Claim rate;
- qualifier/context errors;
- ambiguity guesses;
- evidence-support errors;
- duplicate/conflict reconciliation;
- Spanish fixture results.

Operational evidence:
- model calls;
- input/output/egress bytes or tokens where observable;
- latency;
- execution failures/timeouts;
- run-to-run variance;
- monetary cost only when reliably observable.

No global average may hide a failed required capability.

## Narrow first benchmark output

The first model-facing extraction lane should request only:

```text
candidate-local-key
proposition
exact evidence target proposal(s)
optional source attribution text
optional temporal scope
lane-specific ambiguity diagnostic when needed
```

Do not require the same call to resolve canonical Entities, create taxonomy, classify documents,
produce rich ClaimRelations, assess truth, or perform derived computation.

Those may be measured as later enrichment lanes only after Claim quality is understood.

## Product constraints

- Lector answers only what the source asserts/explicitly contains.
- Parametric/world knowledge may not silently correct source assertions.
- Tables/media retain typed Representation/evidence semantics.
- Numerical/cross-table composition stays in Derivation.
- Verification verdicts stay in Verification.
- Machine-only remains a normal durable state.
- No human review is fabricated by the benchmark.
- No finite document taxonomy is introduced.

## Non-goals

- no production extractor implementation;
- no provider/model architectural lock-in;
- no schema rebaseline unless benchmark mechanics unexpectedly prove a canonical invariant is missing,
  in which case stop for separate design review;
- no Phase-6/WP7 vertical certification;
- no GUI/MCP/query/output implementation;
- no dynamic agent framework adoption simply because A5 exists;
- no mass historical ingestion.

## Anti-overfitting rule

If a natural holdout exposes a material new failure:

```text
candidate fails
-> record the failure mode
-> revise benchmark/design
-> select a NEW untouched holdout
```

The failed holdout cannot be reused as independent certification evidence for the revised candidate.

## Selection rule

Select the **simplest lane that clears every hard frozen semantic gate**.

Examples:

```text
A0 passes all gates -> select A0
A0 fails, A1 passes -> select A1
A4 passes -> A5 remains out of production even if slightly better on a soft aggregate
```

More complexity is justified only by a measured failure that the simpler lane cannot satisfy.

## Proof obligations

Before tested lanes run:
- source/Representation/scope identities frozen;
- reference complete, supervisor-authored, mechanically certified, independently semantically audited, and frozen;
- exact reference evidence reopens;
- candidate output unseen during reference construction;
- thresholds/policy frozen;
- provider/model/config identities fixed per comparison;
- development/holdout separation recorded.

After runs:
- complete per-fixture/per-capability results;
- candidate-to-reference adjudication complete;
- semantic result digests immutable;
- operational measurements reported separately;
- repeated-run variance reported where stochastic execution is material;
- selection decision names what evidence caused every rejected simpler lane to fail.

## Exit states

Success:

```text
LECTOR_PRODUCTION_FIT_BENCH_PASS
SELECT_<LANE>
```

or, if no candidate is sufficient:

```text
LECTOR_PRODUCTION_FIT_BENCH_NO_SUITABLE_LANE
```

Either result is valid research.

## Closure / next authorization

A PASS may propose a production broad-Lector implementation Work.

It does **not** authorize that implementation automatically.

The first end-to-end Acta-160 vertical remains a later post-selection proof.

## Progress — F3 semantic reference construction

F1 benchmark semantics remain frozen. The original fact-by-fact human-approval reference protocol was superseded before any formal A0-A5 output was seen. Current protocol authority is `REFERENCE_PROTOCOL_FREEZE_V2.md`, which uses supervisor authorship, local mechanical certification, and a materially independent semantic audit before reference freeze.

F2 D1-D4 fixture/source/Representation/scope freeze is complete and merged through PR #12 at `da3854bd25f3129244ae49d8cd79a16a2c777ad6`. Exact development fixture identities remain in `FIXTURE_SOURCE_FREEZE_V1.md` and its canonical JSON companion.

F3 is active. Semantic/reference writing is owned by the supervising/cloud author. The local execution agent is limited to source-pack access, mechanical evidence/hash validation, repository tests, bundle verification, and exact push unless explicitly authorized otherwise. `REFERENCE_AUTHORING_METHOD_V1.md` records the anti-slop method.

Formal A0-A5 output/scores remain unseen, Acta 160 and H2 remain untouched, references and thresholds remain unfrozen, and production implementation remains unauthorized.

### F3 progress — D3 supervisor draft v2

The cloud-authored D3 v1 draft was mechanically certified unchanged at
`2e8b1e440eb074ed9fb79b822d617d41b6bd7aa7`: exact source/Representation/scope/unit identities,
452 selectors, repository checks, and the 341-passed/2-skipped/5-subtest baseline all passed. The
primary PDF independently confirmed that Article 27 y)/z) is itself malformed/ambiguous rather
than merely a Representation defect.

The supervising/cloud author then performed a fresh adversarial source→reference and
reference→source review over all 54 articles and all 294 v1 facts. That review found 48 localized
semantic/minimality defects and produced
`references/D3_REFERENCE_SUPERVISOR_DRAFT_V2.json`, with 350 facts. The complete non-independent
review record is `references/D3_SUPERVISING_AUTHOR_ADVERSARIAL_REVIEW_V1.json`. The v1 draft is
retired from the live tree and remains available in Git history.

This author review does **not** satisfy the materially independent semantic-review gate: it was
performed by the same supervising/cloud author. A small local model must not substitute for that
gate. Local execution may mechanically certify the exact v2 selectors/hashes/tests and return
failures unchanged; a later independent big-model review is still required before reference freeze.

Article 27 y)/z) remains explicitly `D3-UQ-0001 / NEEDS_ADJUDICATION`; no semantics are inferred from
the missing/malformed primary text.

Formal A0-A5 output/scores remain unseen, Acta 160 and H2 remain untouched, thresholds and reference
remain unfrozen, and production broad-Lector implementation remains unauthorized.

### F3 progress — D4 supervisor draft v2

The cloud-authored D4 v1 draft was mechanically certified unchanged at
`c4fddeca4996254b6c8609ee586a1ad695c9f5f3`: exact source/Representation/scope/unit identities,
187 selectors, repository checks, and the 341-passed/2-skipped/5-subtest baseline all passed. That
mechanical certification also returned exact primary-PDF evidence establishing that paragraph 2.13
contains `10` followed by superscript footnote marker `4`, not the quantity `104` produced by the
linear text Representation. D4 v1 is therefore preserved in Git evidence but is **not mergeable** as
semantic reference authority.

The supervising/cloud author rebuilt and re-audited D4 from the complete frozen scope. The final
`references/D4_REFERENCE_SUPERVISOR_DRAFT_V2.json` contains 289 facts, 368 evidence targets, 150
structure carriers and complete accounting for all 260 frozen units. The accompanying
`references/D4_SUPERVISING_AUTHOR_ADVERSARIAL_REVIEW_V1.json` records 98 findings across four
source-order/omission/reverse-semantic/primary-source passes. No semantic structures remain
unresolved after two primary-source adjudications.

`D4-PSA-0001` resolves the footnote-4 extraction artifact from the exact frozen primary PDF: 10
exception procedures, broken down 5 provider-unique + 4 indeterminate repairs + 1 artistic/cultural/
intellectual goods or services. `D4-PSA-0002` preserves an internal source wording conflict for the
same 9-case finding: the executive summary says `acto motivado`, while Cuadro n.° 2 visibly prints
`activo motivado`. The latter remains `AMB-01`/`REC-01` evidence rather than being silently corrected.
Exact byte-identical confirmation of that table wording in the frozen source-pack PDF is still a local
mechanical certification check; local execution may report literal evidence but may not alter D4
semantics.

The author-time D4-v2 quality audit reports zero empty evidence, scope escapes, unknown capabilities,
unaccounted units/structures, generic qualifier placeholders, generic/blank reverse-audit notes,
all-15 capability templates, FID-01 bindings, or material carriers without facts. A final selector-
boundary pass also found zero selectors beginning or ending inside a word. Local execution must still
reopen all 368 selectors against the exact frozen source pack and run repository tests before the v2
candidate can be published.

This author review is explicitly **not materially independent**. A later independent big-model
semantic review remains required before D4 can freeze; a small local model must not substitute for
that gate.

Formal A0-A5 output/scores remain unseen, Acta 160 and H2 remain untouched, thresholds and references
remain unfrozen, and production broad-Lector implementation remains unauthorized.


### F3 progress — D1 supervisor draft v1

The D1 authoring session hit a conversation context boundary before a final reference existed. Emergency
checkpoint `8f3a5e0fa0d19e80b8721fae6db3d151b4ec8902` preserved the exact frozen D1 inputs plus 328
runnable semantic specs and 78 separate fragment records, explicitly as WIP/non-authoritative. Those two
record counts are not treated as a prior fact count because overlap/revision was possible, and the later
narrative ~380 state was not fully materialized.

The supervising/cloud author recovered from the exact frozen Representation rather than inventing continuity.
Known incomplete/evidence-shifted carriers C04/C05/C06/C07/C10/C12/U03/M01 were re-authored source-first,
the missing M02–M07 and V01–V05 tail was authored from source, and a final 61-unit omission-only plus
reference→source reverse-semantic/evidence-context audit was completed.

`references/D1_REFERENCE_SUPERVISOR_DRAFT_V1.json` now contains 660 facts, 1,240 exact evidence targets,
36 semantic carriers and explicit accounting for all 61 frozen units. `U0007` contains only a page marker and
is classified `NO_MATERIAL_CIVIC_FACT`. The reference binds 221 facts to CTX-01 only where required context
leaves the local frozen unit/semantic segment; same-unit antecedents do not receive CTX by template.

`references/D1_SUPERVISING_AUTHOR_ADVERSARIAL_REVIEW_V1.json` records 38 reproducible supervising-author
findings: 19 recovery findings, 5 final omission findings and 14 reverse/evidence-context findings. These are
not claimed to reproduce the 19 narrative findings mentioned before the context cut. Final author-time validation
reports zero duplicate canonical notes, duplicate reverse-audit notes, empty evidence, scope/structure escapes,
mid-word selector boundaries, unknown capabilities, generic qualifier placeholders, FID-01 bindings, unaccounted
units/structures or material carriers without facts. All 1,240 selected-text hashes reopen against the frozen
Representation.

This author review is explicitly non-independent. Local mechanical certification of the exact D1-v1 candidate
is still pending, followed by materially independent big-model semantic review before any D1 freeze. Formal
A0–A5 output/scores remain unseen, Acta 160 and H2 remain untouched, thresholds remain unfrozen, and production
broad-Lector implementation remains unauthorized.

### F3 progress — D1 supervisor draft v2

D1 v1 was mechanically certified unchanged at `6aac2af5802996b8c17c612107f6771e0e612318`. A separate clean-context semantic review committed at `eaf74f8f65c5f98b79afaa185bc75baa24ac094c` then audited all 36 structures, 61 frozen units, 660 facts and 1,240 evidence targets and returned `REFERENCE_DISPUTE` with 61 hard findings. The reviewer was also OpenAI GPT-5.6 Sol, so the review truthfully records `WEAK_OR_UNKNOWN` independence and does not satisfy the strong materially-independent gate.

The supervising/cloud author adjudicated all 61 findings from the exact frozen source: 61 accepted, 0 rejected, 0 unresolved. `references/D1_INDEPENDENT_REVIEW_ADJUDICATION_V1.json` is the canonical resolution record. The resulting `references/D1_REFERENCE_SUPERVISOR_DRAFT_V2.json` contains 700 facts and 1,473 evidence targets across the same 36 carriers and 61 units. The v2 delta restores 40 omitted material assertions, repairs systematic named-speaker and formal-decision evidence, preserves the U04 rationale/proposal/acceptance distinctions, and resolves V05 deictic project/bridge/paradero context to the exact Mata de Limón source context.

D1 v1 is retired from the live reference tree and remains in Git history. D1 v2 is still unfrozen. It requires fresh local mechanical certification and a fresh semantic audit; the prior review cannot certify a reference version it never saw. Formal A0–A5 output/scores remain unseen, Acta 160 and H2 remain untouched, thresholds remain unfrozen, and production broad-Lector implementation remains unauthorized.

### F3 progress — D1 supervisor draft v3

D1 v2 was mechanically certified unchanged at `bf59bddcfe2a4027c86507491f782aa9fe027b7c`. A fresh-context
secondary semantic audit then completed a blind source→reference and reference→source pass before reading any
prior review material. It covered all 36 structures, 61 frozen units, 700 v2 facts and 1,473 evidence targets
and returned `REFERENCE_DISPUTE` with 23 hard findings: 19 `EVIDENCE_INSUFFICIENT`, three `CONTEXT_ERROR`
and one `SOURCE_FIDELITY_ERROR`. Critically, the source-order pass found **zero additional material
source→reference omissions**. The reviewer was again OpenAI GPT-5.6 Sol, so the audit remains
`WEAK_OR_UNKNOWN` independence and does not satisfy the strong materially-independent gate.

The supervising/cloud author reopened all 23 disputes against the exact frozen Representation and accepted all
23, with zero rejected or unresolved. `references/D1_SECONDARY_REVIEW_ADJUDICATION_V2.json` is the canonical
resolution record. D1 v3 preserves the 700-fact material inventory, expands semantically sufficient evidence
binding, and retires/replaces 33 v2 facts whose semantic notes still required source-resolved antecedents or
explicit ambiguity. The source-local `Rolnald Robles` label is resolved only via the same source's attendance
roster, and the C06 `ellos` reference is now preserved as unresolved ambiguity rather than guessed as Laura
Fernández's team.

`references/D1_REFERENCE_SUPERVISOR_DRAFT_V3.json` remains `SUPERVISOR_DRAFT`. It requires exact local
mechanical certification and another fresh semantic audit before any D1 freeze. Formal A0–A5 output/scores
remain unseen, Acta 160 and H2 remain untouched, thresholds remain unfrozen, and production broad-Lector
implementation remains unauthorized.

### F3 progress — D1 supervisor draft v4

D1 v3 was mechanically certified unchanged at `f67be88dd34231f472e8bf485aba72760eeb36a0`. A third fresh-context semantic audit completed the required blind source→reference and reference→source passes across all 36 structures, 61 frozen units, 700 v3 facts and 1,566 evidence targets before opening prior-review material. It returned `REFERENCE_DISPUTE` with 14 hard findings: two missing material assertions, one modality error, one quantitative error and ten evidence-insufficiency findings. The reviewer remained OpenAI GPT-5.6 Sol, so independence is still `WEAK_OR_UNKNOWN`. Reviewer-side repository delivery timed out after semantic completion; the two exact review artifacts were therefore preserved byte-identically by the supervising author before v4 authorship.

The supervising/cloud author reopened all 14 findings against the exact frozen Representation and accepted all 14, with zero rejected or unresolved. `references/D1_TERTIARY_REVIEW_ADJUDICATION_V3.json` is the canonical adjudication record. D1 v4 restores Stephannie Quesada’s road-attention expectation/reason and the explicit prior port-reserve relation of expediente 23.898, repairs the pool-regulation modality, and binds normalized calendar dates to exact dated source/session evidence. The tertiary quantity finding also exposed a deeper authoring defect: v3’s `25`/`10` school totals were arithmetic derivations and the two aggregate list facts were under-decomposed. V4 therefore retires those two facts and represents all 35 enumerated educational-center rows individually, without derived totals. The resulting candidate contains **735 facts and 1,694 exact evidence targets** across the same 36 semantic carriers and 61 frozen units.

`references/D1_REFERENCE_SUPERVISOR_DRAFT_V4.json` remains `SUPERVISOR_DRAFT`. It requires exact local mechanical certification and another fresh semantic audit before any D1 freeze. Formal A0–A5 output/scores remain unseen, Acta 160 and H2 remain untouched, thresholds remain unfrozen, and production broad-Lector implementation remains unauthorized.

### F3 progress — D1 supervisor draft v5

D1 v4 was mechanically certified unchanged at `44291aa54f96492d02cc4e9c9f8e4d0bb9ddd770`. A fourth
fresh-context semantic audit then completed the blind 36-structure / 61-unit / 735-fact / 1,694-evidence
pass and returned `QUATERNARY_AUDIT_PASS_NO_DISPUTES`; that clean review is preserved at
`5456898a78082061ca6536dd0bd74373fea95cf0`. The reviewer was still OpenAI GPT-5.6 Sol, so the clean
result remains `WEAK_OR_UNKNOWN` independence and does not satisfy the materially-independent gate.

A deterministic 30-decision human-independence spot-check packet was then generated without using prior
review findings for selection. The owner explicitly delegated those decisions back to the supervising OpenAI
model. That review is therefore preserved as **AI-assisted supplemental defect-finding evidence**, not as a
human review and not as material independence. `references/D1_AI_ASSISTED_BOUNDED_SPOTCHECK_V4.json`
records `REFERENCE_DISPUTE` with 13 hard groups: three reference→source evidence/attribution defects, nine
source→reference omissions exposed inside the sampled forward units, and one wrong unit classification family.

The supervising/cloud author adjudicated all 13 findings source-only: 13 accepted, 0 rejected, 0 unresolved.
`references/D1_AI_ASSISTED_BOUNDED_SPOTCHECK_ADJUDICATION_V4.json` is the canonical resolution record.
D1 v5 contains **744 facts and 1,727 evidence targets**. It restores nine explicit actor positions,
recommendations, proposals, procedural/status assertions; binds the missing M02 future-request antecedent and
C06 Laura-agreement sentence; binds same-source PRE identity evidence to eight normalized Stephannie-Quesada
facts; and narrows the overbroad C01 context selector that crossed three content-free numeric extraction units.
`U0003`, `U0004`, `U0005` and `U0007` are now `NO_MATERIAL_CIVIC_FACT`; their exact frozen contents are only
`9`, `10`, `11` and `1` respectively.

The author-time v5 validator reports 744 unique facts, 1,727 reopenable evidence targets, 36 structures, 61
units, 411 cross-unit facts, 378 `CTX-01`, eight `AMB-01`, 50 `QTY-01`, 649 multi-evidence facts, zero selector
hash/range/structure/unit failures, zero mid-word selector boundaries, zero duplicate canonical/reverse-audit
notes, zero `FID-01` bindings and zero unresolved structures/adjudications. D1 v5 remains `SUPERVISOR_DRAFT`.
Exact local mechanical certification and a fresh semantic audit are required before any freeze discussion; the
human/material-independence gate remains unsatisfied. Formal A0-A5 output/scores remain unseen, Acta 160 and H2
remain untouched, thresholds remain unfrozen, and production broad-Lector implementation remains unauthorized.

### F3 progress — D1 supervisor draft v6

D1 v5 was mechanically certified unchanged at `e1ebb27f646ca54546bf2b5aff75f09b28b29ffb`. A fifth
fresh-context semantic audit, preserved at `42f82be473e447176bde912625229dc2151f76c8`, completed the blind
36-structure / 61-unit / 61-unit-state / 744-fact / 1,727-evidence pass before opening prior semantic-review
artifacts. It returned `REFERENCE_DISPUTE` with **30 hard groups**: 13 source→reference omissions, 15
evidence-insufficiency groups and two capability-binding errors. The reviewer remained OpenAI GPT-5.6 Sol, so
independence remains `WEAK_OR_UNKNOWN`; the human/material-independence gate is still unsatisfied.

The supervising/cloud author reopened all 30 findings against the exact frozen source and accepted all 30,
with zero rejected or unresolved. `references/D1_QUINARY_REVIEW_ADJUDICATION_V5.json` is the canonical
source-only adjudication record. One reviewer problem statement misnamed Heriberto Alvarado Méndez as
“Heriberto González”; the omission itself is valid and v6 preserves the exact source speaker. Two omission
groups contain separable speech acts, so the 13 source→reference groups produce 15 new material facts.

D1 v6 contains **759 facts and 1,939 exact evidence targets**. The principal repair is systemic rather than
fact-by-fact: facts whose canonical actor/institution identity was more specific than their local evidence now
bind exact same-source roster/header/provenance resolvers. V6 also binds the first-hand-information purpose on
D1-F0466, the explicit recommendation heading on D1-F0586, adds `TMP-01` to D1-F0511/D1-F0519, and adds
`SCP-01` to D1-F0748. Unit-state decisions remain 57 `MATERIAL_FACTS` / four
`NO_MATERIAL_CIVIC_FACT` (`U0003`, `U0004`, `U0005`, `U0007`).

The author-time v6 validator reports 759 unique facts, 1,939 reopenable evidence targets, 36 structures, 61
units, 536 cross-unit facts, 505 `CTX-01`, nine `AMB-01`, 52 `QTY-01`, 716 multi-evidence facts, zero
selector hash/range/structure/unit failures, zero mid-word selector boundaries, zero duplicate canonical or
reverse-audit notes, zero `FID-01` bindings and zero unresolved quinary adjudications. D1 v6 remains
`SUPERVISOR_DRAFT`. Exact local mechanical certification and a fresh semantic audit are required before any
freeze decision. Formal A0-A5 output/scores remain unseen, Acta 160 and H2 remain untouched, thresholds remain
unfrozen, and production broad-Lector implementation remains unauthorized.

### F3 progress — D1 supervisor draft v7

D1 v6 was mechanically certified unchanged at `87cc3a1eeef8b95f49abb2a671f84f7653040883`. A sixth fresh-context semantic audit then completed the blind 36-structure / 61-unit / 61-unit-state / 759-fact / 1,939-evidence pass, including a 759-row identity/provenance matrix and source-wide lexical/semantic forcing scan, before opening prior review history. It returned `REFERENCE_DISPUTE` with **22 hard groups**: 18 source→reference omissions, two attribution errors, one qualifier error and one modality error. All 30 quinary-v5 findings were independently regression-checked as `RESOLVED_IN_V6`. The senary reviewer remained OpenAI GPT-5.6 Sol, so independence remains `WEAK_OR_UNKNOWN`; the strong/human independence gates remain unsatisfied.

The reviewer completed the two canonical senary artifacts but its execution wrapper expired during repository delivery. The supervising/cloud author preserved those exact uploaded artifacts byte-for-byte, ran the full canonical repository suite successfully (`341 passed, 2 skipped, 5 subtests passed`), and recorded them without altering semantic content at preservation commit `4dc3c3e9299aa52acccb4bd7de25b6b2dd938687`. This commit is delivery/custody preservation by the supervisor, not evidence that the reviewer itself completed Git delivery.

The supervising/cloud author reopened all 22 senary findings against the exact frozen Representation and accepted all 22, with zero rejected or unresolved. `references/D1_SENARY_REVIEW_ADJUDICATION_V6.json` is the canonical source-only adjudication record. Three omission groups contain source-separable propositions: recurrence versus causal explanation, the President's respect/non-devaluation/commitment statements, and two distinct public-safety status assessments. The 18 source→reference groups therefore produce **22 new material facts**. The four reverse groups are repaired in place: exact CGR correspondence provenance is bound to D1-F0051–D1-F0054; D1-F0310 regains its district-resource condition and `podría/sería` force; D1-F0784 preserves source `me parece` as evaluative `consideró`; and D1-F0622/D1-F0623/D1-F0624/D1-F0693 bind the exact `Concejo Municipal de Esparza` resolver.

D1 v7 contains **781 facts and 2,007 exact evidence targets** across the same 36 structures and 61 frozen units. The author-time v7 validator reports 555 cross-unit facts, 525 `CTX-01`, ten `AMB-01`, 54 `QTY-01`, 743 multi-evidence facts, zero selector hash/range/structure/unit failures, zero mid-word selector boundaries, unique canonical and reverse-audit notes, four unchanged non-material page-marker units (`U0003`, `U0004`, `U0005`, `U0007`), and 22 accepted / zero rejected / zero unresolved senary adjudications.

D1 v7 remains `SUPERVISOR_DRAFT`. Exact local mechanical certification and another fresh semantic audit are required before any freeze decision. Formal A0–A5 output/scores remain unseen, Acta 160 and H2 remain untouched, thresholds remain unfrozen, and production broad-Lector implementation remains unauthorized.

### F3 progress — D1 supervisor draft v8

D1 v7 was mechanically certified at `a400b5982d47f37756a5bf072a60f6ba208a5841`. A fresh septenary audit was then attempted with a stronger source-first method requiring a sealed source assertion ledger before opening the reference. The reviewer verified exact custody and produced a 61-unit preliminary ledger with 781 assertions, but after opening v7 discovered that the ledger had incorrectly omitted the explicit request `Que diga qué fue lo que encontró.` even though v7 correctly represents it as `D1-F0795`. The clean source-ledger anti-anchoring claim is therefore invalid: `reference_anchoring_contamination=true`; prior semantic-review history remained unopened (`history_anchoring_contamination=false`). The reviewer stopped rather than falsely claiming the full septenary contract, and did not create final septenary review artifacts, tests, commit, or bundle.

The supervising/cloud author recorded this aborted execution explicitly in `references/D1_SEPTENARY_ABORTED_EXECUTION_V7.json` / `.md`, without treating it as a completed semantic audit. Seven definite reverse defects reported before the stop were reopened against the exact frozen Representation. The reviewer had also named several unresolved forward candidates; the supervisor source-reopened those named candidates and confirmed only three additional hard groups: omission of Olivier López's proposal to copy Auditoría together with Contraloría so they could answer the complainant (`D1-SA-0090`), omission of Ronald Robles's explicit negative evaluation that people working to provide the service should not have to face situations of that type (`D1-SA-0100`), and the missing attached reason/contrast in `D1-F0785`. Other event/program rows mentioned only as unresolved potentials are intentionally not promoted to findings.

`references/D1_SEPTENARY_ABORTED_EXECUTION_ADJUDICATION_V7.json` records **10 ACCEPT / 0 REJECT / 0 UNRESOLVED** among this confirmed partial set. V8 repairs eight existing facts in place (`D1-F0079`, `D1-F0493`, `D1-F0734`, `D1-F0810`, `D1-F0811`, `D1-F0827`, `D1-F0828`, `D1-F0785`) and adds two new material facts (`D1-F0830`, `D1-F0831`). The repairs bind missing topic/identity/provenance antecedents, remove the unsupported `fuera de comisión` strengthening, bind the bianual-Games agreement subject, and restore the source-visible reason attached to the mayor's Contraloría/association evaluation.

D1 v8 contains **783 facts and 2,019 exact evidence targets** across the same 36 structures and 61 frozen units. It remains `SUPERVISOR_DRAFT`. Exact local mechanical certification and a genuinely fresh semantic audit remain required before any freeze decision. Formal A0–A5 output/scores remain unseen, Acta 160 and H2 remain untouched, thresholds remain unfrozen, and production broad-Lector implementation remains unauthorized.

### F3 progress — D1 supervisor draft v9

D1 v8 was mechanically certified unchanged at `98ca3fbc84f6d35a0ba52068b98da4ea10ec1aad`. To avoid another monolithic-context failure, the next semantic review used six frozen-unit-aligned source-only/audit shards plus a fresh reconciliation worker. The first reconciliation exposed an S01 review-kit reopening defect for 12 reverse-owned facts; S01 alone was rerun using its already-sealed source ledger and the full exact frozen Representation. The replacement S01 audit passed 156/156 facts and 384/384 evidence targets with zero findings. The final reconciliation R2 therefore has complete declared coverage: **61/61 frozen units, 783/783 reverse facts, 2,019/2,019 evidence targets and 241/241 source assertions**, with no unresolved reopening blocker and no declared shard-history contamination.

`references/D1_SHARDED_SEMANTIC_REVIEW_V8_RECONCILED_R2.json` records the final `REFERENCE_DISPUTE`: **10 hard groups** — five `MISSING_MATERIAL_ASSERTION`, three `MODALITY_ERROR` and two `QUALIFIER_ERROR`; directionally five source→reference, three reference→source and two both-direction. All ten v8 repairs independently pass regression. The reviewers were Terra/OpenAI-family workers, so independence remains truthfully `WEAK_OR_UNKNOWN`; source-only sealing improves leakage control but does not satisfy the strong material-independence gate.

The supervising/cloud author reopened all ten R2 findings against the exact frozen source and accepted all ten, with zero rejected or unresolved. `references/D1_SHARDED_REVIEW_ADJUDICATION_V8.json` is the canonical source-only adjudication record. V9 adds five material facts: the Expo Feria post-inauguration lunch (`D1-F0832`), Ronald Robles's public 30-May dance invitation (`D1-F0833`), Flor María Cubero's statement that resolving some matters does not eliminate the commission's pending work (`D1-F0834`), the President's separate procedural receipt/direction on the CCCI request (`D1-F0835`), and the formal unanimous/final Futsala U-8 recognition-preparation transfer (`D1-F0836`).

Six existing facts are repaired in place: `D1-F0154` now retains the invitation's explicit confirmation channels; `D1-F0714` preserves desiderative `Quisiera confirmar` rather than completed self-confirmation; `D1-F0174` drops unsupported `administrativas`; `D1-F0194` restores the third stated reason that Christian Tercero was more familiar with the topic; and `D1-F0360`/`D1-F0361` preserve `consideró importante solicitar` rather than direct-request force.

D1 v9 contains **788 facts and 2,031 exact evidence targets** across the same 36 structures and 61 frozen units. The author-time v9 validator reports 559 cross-unit facts, 529 `CTX-01`, ten `AMB-01`, 54 `QTY-01`, 750 multi-evidence facts, exact source/hash/range/structure/unit reopening for all 2,031 targets, zero mid-word boundaries on the authored delta, unique fact/canonical/reverse-audit notes, unchanged non-material page-marker units (`U0003`, `U0004`, `U0005`, `U0007`), and **10 ACCEPT / 0 REJECT / 0 UNRESOLVED** sharded-R2 adjudications. D1 v9 remains `SUPERVISOR_DRAFT`; exact local mechanical certification is required before the next semantic/freeze gate. Formal A0–A5 output/scores remain unseen, Acta 160 and H2 remain untouched, thresholds remain unfrozen, and production broad-Lector implementation remains unauthorized.
