# Derivation / Verification / Claim / Evidence reconciliation

State: **DESIGN ACCEPTED — PRERELEASE `0001` REBASELINE AUTHORIZED NEXT**

Authority chain:

```text
post-SOTA operation split:       516ddd613bf58ef412d59bf4600652c8045c9c6b
G3 structured-reasoning proof:   0f9a71e5acb0f093469571d59c896eab0c03c4c2
Phase-D verifier closure:        5e9c9e9186983f68bbe2a2d3db9c78095d11fd81
Phase-D merge baseline:          310d060cc1ced3640892a0dc29a7fbcb2c010920
G3 verdict:                      FIRST_CLASS_DERIVATION_REQUIRED
Phase-D verdict:                 DECOMPOSITION_VALUE_PROVEN__DESIGN_MINIMUM_CANARIO_DECOMPOSITION
reconciliation verdict:          SINGLE_EXECUTION_GRAPH__SOURCE_EVIDENCE_NOT_EXECUTION_LINEAGE
```

## Purpose

This unit closes the last semantic design gate before the prerelease `0001` schema is
rebaselined again. It reconciles the six concepts that were previously correct in isolation but
not yet jointly frozen:

```text
ProcessRun
DerivationRun / DerivationResult
VerificationRun
ClaimRevision origin
EvidenceLink
Assessment
```

The goal is **one inspectable execution graph with no duplicated authority**. Canario must be able
to explain:

1. what source material existed;
2. what machine/rule/human operation transformed or analyzed it;
3. what exact analytical result was produced;
4. what proposition was verified against what bounded scope;
5. what source evidence supports/challenges a durable Claim;
6. what later attributable judgment, if any, was recorded about that Claim.

Those are related facts, not interchangeable records.

## Decision summary

The accepted graph is:

```text
Artifact custody
  -> Representation
       -> RepresentationTarget

RepresentationTarget(s)
  -> DerivationRun
       -> DerivationResult
            -> DerivationResultTarget
                 -> source-contribution lineage -> RepresentationTarget(s)

bounded Verification scope + SourceAuthorityScope(s)
  -> VerificationRun
       -> ordered DerivationRun/DerivationResultTarget uses
       -> exact verification evidence -> RepresentationTarget(s)
       -> verdict + explicit sufficiency + abstention/execution outcome

DerivationResultTarget
  -> optional ClaimRevision(kind=derived_inference)
       -> EvidenceLink(s) -> source RepresentationTarget(s)

ClaimRevision
  -> optional Assessment
       -> optional exact VerificationRun basis
```

The key rule is:

> **Execution lineage is not civic evidence.**

A query/program, DerivationRun, DerivationResult, VerificationRun, model trace, or Assessment is
never a substitute for source evidence. Durable Claim evidence continues to reopen against exact
source `RepresentationTarget`s through `EvidenceLink`.

## 1. Non-overlapping responsibilities

| Record | Durable reason to exist | Must not become |
|---|---|---|
| `ProcessRun` | provenance for Representation processing and existing bounded semantic extraction/writes | a generic analytical query record |
| `DerivationRun` | immutable attempt to execute one exact bounded analytical program/query over ordered canonical evidence scopes | a source-evidence link or Claim |
| `DerivationResult` | exact typed output identity for one successful DerivationRun | a `Representation` merely to obtain storage identity |
| `DerivationResultTarget` | exact selectable slice of a DerivationResult used by lineage, Claim origin, or Verification | a source locator |
| `VerificationRun` | immutable execution evaluating one proposition against one explicit bounded scope | Claim lifecycle or durable truth state |
| `ClaimRevision` | durable proposition with revision history and attributable origin | an execution trace |
| `EvidenceLink` | correctable civic relation from exact ClaimRevision to exact source evidence | derivation lineage or verifier trace |
| `Assessment` | optional attributable durable judgment about an exact ClaimRevision | human review, claim lifecycle, or objective truth score |

`ReviewDecision` remains orthogonal: it judges whether a stored semantic row/revision is accepted,
rejected, or needs work. An `Assessment` judges the proposition against evidence. A reviewer may
accept a ClaimRevision as a faithful stored proposition while separately assessing it as refuted.

## 2. ProcessRun remains frozen to its certified boundary

`ProcessRun` keeps the Workbench/Lector semantics already certified:

```text
exact RepresentationTarget inputs
-> processor / semantic extraction implementation
-> terminal execution
-> QualityEvidence / QualityDecision where applicable
-> material Representation or semantic outputs attributable to that run
```

No generic `operation_run`, polymorphic execution table, or universal operation receipt is added.
The three run families may share implementation patterns in code, but their SQL authority remains
typed because their invariants differ.

A ProcessRun may produce a Representation later consumed by a DerivationRun. A semantic ProcessRun
may also phrase or promote a derived Claim, but it does not replace the exact DerivationResultTarget
that is the Claim's analytical origin.

## 3. DerivationRun

A `DerivationRun` is one immutable analytical execution attempt. Re-executing the same program over
the same inputs creates a **new run ID**. Program/input/result digests may support cache policy but
are not canonical run identity.

Minimum record semantics:

```text
derivation_runs
  id PK
  operation_kind                    -- query | program | rule | other_registered
  implementation_key
  implementation_version
  execution_venue
  configuration_hash nullable
  model_provider nullable
  model_name nullable
  executor_key
  executor_version
  executor_source_id nullable
  sandbox_profile_key
  sandbox_profile_version
  program_kind                      -- sql | expression | script | other_registered
  program_text                      -- exact retained non-secret executable specification
  program_sha256
  started_at
  finished_at
  outcome                           -- success | failed
  error_code nullable
  created_at
```

Rules:

- `success` requires no error and exactly one valid `DerivationResult`;
- `failed` requires a bounded error code and no result;
- executor-enforced truncation/resource cutoff is failure, not a silently partial result;
- an intentional SQL `LIMIT` is part of the exact program and may succeed;
- generated program text is untrusted input to the executor;
- secrets, transient credential material, user home paths, and ambient environment dumps never
  enter the retained program/configuration;
- model/provider fields identify planning/orchestration when a model proposed the executable;
  executor identity remains separate so “model wrote SQL” never means “model executed SQL”.

### Ordered inputs

```text
derivation_run_inputs
  derivation_run_id FK
  ordinal
  representation_id FK
  representation_target_id FK
  PRIMARY KEY(derivation_run_id, ordinal)
```

The target must belong to the stated Representation. Order is execution provenance even for a
mathematically commutative operation.

The first schema does **not** add ClaimRevision inputs or DerivationResult-to-DerivationResult
chaining. A general program can consume multiple original bounded scopes; a real fixture must prove
a need for recursive derivation graphs before that complexity is added.

## 4. DerivationResult is not Representation

A successful derivation may combine multiple Artifacts/Representations. Existing
`Representation` correctly belongs to one Artifact custody chain, so analytical results must not be
forced into `Representation` merely to obtain a durable byte/result identity.

Use one result record per successful run:

```text
derivation_results
  id PK
  derivation_run_id FK UNIQUE
  result_kind                       -- scalar | table | structured | binary | other_registered
  schema_key
  schema_version
  inline_payload_json nullable      -- bounded canonical typed payload
  archive_object_id FK nullable     -- larger/material result bytes
  content_sha256
  byte_size
  availability                      -- available | purged
  created_at
  purged_at nullable
```

Exactly one payload mode is used while retained: bounded inline canonical payload or an
`ArchiveObject`. `content_sha256` identifies exact result serialization, not civic identity.

### Result targets

A result needs the same “exact slice, reusable identity” discipline that source Representations
already gained from `RepresentationTarget`:

```text
derivation_result_targets
  id PK
  derivation_result_id FK
  selector_kind
  selector_version
  selector_payload_json
  lineage_state                 -- exact | partial | unavailable | none
  availability                  -- available | purged
  created_at
  purged_at nullable
```

Registered examples may include `whole:v1`, `scalar:v1`, `table_row:v1`, `table_cell:v1`, or a
validated structured path. Selector JSON remains a bounded kind/version seam, not arbitrary state.

Lineage completeness belongs to the **result target**, not the whole result, because a table may
have exact lineage for some rows/cells while another slice is only partially traceable:

- `exact`: all source contribution targets for this exact result target are known;
- `partial`: some real source contribution lineage is retained but completeness is not proven;
- `unavailable`: the target is source-dependent but trustworthy fine lineage cannot be recovered;
- `none`: the executor proves that this target is not source-dependent (for example a constant
  expression). Such a result can be a valid computation but cannot masquerade as evidence-backed
  civic analysis.

### Result-to-source lineage

```text
derivation_result_lineage
  derivation_result_target_id FK
  representation_target_id FK
  created_at
  PRIMARY KEY(derivation_result_target_id, representation_target_id)
```

Presence means **source contribution**, not merely nearby context. Every lineage source target must
be equal to or selector-contained by an input scope of the owning DerivationRun. Targets with
`exact` or `partial` lineage may have lineage rows; `unavailable` and `none` targets may not
fabricate them.

The lineage table has no second locator payload: source location lives once in
`RepresentationTarget`, and result location lives once in `DerivationResultTarget`.

## 5. VerificationRun

A `VerificationRun` evaluates one exact proposition against one explicit bounded evidence scope.
It may bind to an existing ClaimRevision or operate ad hoc without creating a Claim.

```text
verification_runs
  id PK
  claim_revision_id FK nullable
  proposition_text
  implementation_key
  implementation_version
  execution_venue
  configuration_hash nullable
  model_provider nullable
  model_name nullable
  scope_profile_key
  scope_profile_version
  scope_payload_json
  started_at
  finished_at
  outcome                         -- completed | failed
  error_code nullable
  verdict nullable                -- supported | contradicted | insufficient_evidence
  sufficiency_state nullable      -- sufficient | insufficient
  sufficiency_profile_key nullable
  sufficiency_profile_version nullable
  sufficiency_payload_json nullable
  abstention_reason_code nullable
  created_at
```

Core validation requires:

```text
completed + supported/contradicted
  -> sufficiency_state = sufficient
  -> no abstention reason

completed + insufficient_evidence
  -> sufficiency_state = insufficient
  -> bounded abstention reason required

failed
  -> no verdict
  -> no epistemic sufficiency result
  -> bounded execution error required
```

Tool/query/model failure is therefore never encoded as `insufficient_evidence`.

If `claim_revision_id` is present, `proposition_text` must be the exact normalized proposition of
that revision under the verifier input contract. An ad-hoc run may remain ad hoc indefinitely.

### Verification scope and Source Authority

The verifier's available terrain is explicit rather than inferred from what its tools happened to
return:

```text
verification_scope_targets
  verification_run_id FK
  ordinal
  representation_target_id FK
  PRIMARY KEY(verification_run_id, ordinal)

verification_authority_scopes
  verification_run_id FK
  ordinal
  source_authority_scope_id FK
  PRIMARY KEY(verification_run_id, ordinal)
```

`scope_profile_* + scope_payload_json` records the bounded coverage contract needed for questions
such as negative/absence evidence. `SourceAuthorityScope` says what kind of statement the source
can evidence; the scope profile says what subset/inventory was actually considered. Neither is a
trust score.

A Derivation used by the verifier may not silently expand that scope. Every Derivation input target
must be equal to or selector-contained by one Verification scope target, and the represented source
must be compatible with an explicit authority scope when the proposition requires one.

### Exact derivation uses

```text
verification_derivation_steps
  verification_run_id FK
  ordinal
  derivation_run_id FK
  use_state                         -- attempted | consumed
  derivation_result_target_id FK nullable
  PRIMARY KEY(verification_run_id, ordinal)
```

Every Derivation invoked inside the verification is listed. `consumed` means its exact result
target influenced the final verifier and therefore requires an available `DerivationResultTarget`
belonging to the stated run. `attempted` preserves a failed or ultimately unused analytical attempt
without pretending its result supported the verdict. A failed Derivation has no result target. The
final verifier cannot hide SQL/query work in an opaque model trace.

A cached/reused Derivation is legal: the VerificationRun references the exact prior run/result it
actually consumed. Cache reuse does not manufacture a new execution record.

### Verification evidence set

Verification evidence is an execution result and therefore remains separate from Claim
`EvidenceLink`:

```text
verification_evidence_items
  verification_run_id FK
  ordinal
  representation_target_id FK
  role                            -- supports | challenges | context
  PRIMARY KEY(verification_run_id, ordinal)
```

Every item must be inside the Verification scope. It may be directly inspected source evidence or
source evidence reachable through a referenced DerivationResultTarget's lineage.

The verifier does **not** create/correct Claim EvidenceLinks merely by returning evidence. Promotion
is a separate attributable semantic write.

## 6. Claim origin after reconciliation

`ClaimRevision.process_run_id` remains the origin for machine/rule source extraction and other
existing semantic generation. Add one nullable exact analytical-origin reference:

```text
claim_revisions.derivation_result_target_id FK nullable
```

Rules:

- `claim_kind=derived_inference` requires an available `DerivationResultTarget`;
- non-derived Claim kinds must not use that field;
- a derived Claim may also carry `process_run_id` when a distinct semantic process materially
  authored/normalized the Claim wording, but ProcessRun is **not** its analytical basis;
- human promotion of an exact analytical result can have `origin_kind=human`, no ProcessRun, and
  the required DerivationResultTarget;
- a Derivation result never becomes a Claim automatically.

This gives one exact provenance path:

```text
ClaimRevision(kind=derived_inference)
  -> DerivationResultTarget
  -> DerivationResult
  -> DerivationRun
  -> ordered source scopes + exact program
```

No polymorphic `origin_type/origin_id` table is introduced.

## 7. EvidenceLink remains source evidence

`EvidenceLink` keeps its current meaning:

```text
exact ClaimRevision
-> supports | challenges | contextualizes | quotes | mentions
-> exact source RepresentationTarget
```

For `derived_inference` Claims, core validation adds a stronger invariant:

- active `supports` evidence must overlap source contribution lineage for the Claim's exact
  DerivationResultTarget;
- a broader citation target may contain the exact contributing target when the selector contract
  proves containment (for example a row citation containing contributing cells);
- `challenges` may legitimately come from independent source evidence outside the derivation, so it
  retains the ordinary EvidenceLink rule rather than being forced into derivation lineage;
- `contextualizes`/`quotes`/`mentions` retain their ordinary source-evidence semantics and do not
  claim causal contribution merely by existing;
- unavailable derivation lineage may still permit a machine-only derived Claim to exist, but it
  cannot be treated as evidence-backed merely because the query returned the expected number.

The executable query/program is never written as EvidenceLink evidence.

Verification evidence is never copied into EvidenceLink automatically. A later policy/human action
may create or correct EvidenceLinks, with its own existing origin/review provenance, after checking
that the source targets satisfy these invariants.

## 8. Assessment is not review and not lifecycle

The now-proven Verification boundary justifies freezing the optional durable `Assessment` shape,
without authorizing automatic writes.

An Assessment targets one exact ClaimRevision:

```text
assessments
  id PK
  supersedes_assessment_id FK nullable
  claim_revision_id FK
  judgment                         -- supported | contested | refuted | unresolved
  origin_kind                      -- machine | rule | human
  assessor_key                     -- attributable human/policy identity, non-secret
  verification_run_id FK nullable
  policy_key nullable
  policy_version nullable
  rationale nullable
  created_at
```

Rules:

- an Assessment never changes Claim lifecycle;
- it is not a confidence score or Canario declaration of objective truth;
- multiple assessors/policies may disagree and coexist;
- changing one assessor/policy's judgment appends a same-ClaimRevision superseding Assessment; the successor must retain the same `assessor_key`, and when either row is policy-backed it must retain the same `policy_key` lineage (with `policy_version` allowed to advance explicitly);
- if a VerificationRun is the basis, it must itself bind to the same ClaimRevision;
- an ad-hoc VerificationRun cannot become Assessment basis retroactively for a different Claim;
- every machine/rule Assessment requires an exact same-Claim `verification_run_id` plus an explicit registered `policy_key`/`policy_version`; human Assessments may be entered without a VerificationRun when their rationale/evidence basis is otherwise attributable;
- no Phase-D result authorizes such auto-promotion in production.

Initial judgment semantics:

- `supported`: assessor accepts that available evidence supports the proposition;
- `refuted`: assessor accepts that available evidence contradicts the proposition;
- `contested`: materially conflicting credible evidence/judgments remain;
- `unresolved`: assessor records that a durable conclusion is not justified.

These intentionally do not collapse one-to-one onto Verification verdicts. A policy may map a
specific `supported`/`contradicted`/`insufficient_evidence` run into an Assessment only when its
rules are explicit and attributable.

### Assessment vs ReviewDecision

```text
ClaimReview(accepted)
  = “this stored ClaimRevision is an acceptable/correct semantic record”

Assessment(refuted)
  = “this exact proposition is judged false/unsupported on the cited verification basis”
```

Both can be true simultaneously. Keeping them separate prevents “reviewed” from becoming a truth
flag.

## 9. Egress and provider provenance

Derivation and Verification receive typed egress records analogous to ProcessRun without creating a
polymorphic execution table:

```text
derivation_run_egress
verification_run_egress
```

Each stores only non-secret bytes-egressed/profile/template/endpoint facts. Credentials,
CODEX_HOME/keyring paths, tokens, account identity, and ambient environment remain outside SQLite.

Provider/model identity is replaceable execution provenance. It is never Source Authority and never
part of Claim identity.

## 10. Replay, cache, correction, and source evolution

### Retry vs re-execution

Persistence retries reuse a preallocated run/result ID only when the immutable payload is byte-for-
byte/field-for-field identical. A fresh analytical or verification execution gets a new run ID even
when program, inputs, model and result happen to match.

### Cache

A deterministic cache may reuse an existing successful DerivationRun only under an explicit cache
policy that verifies exact inputs/program/executor identity and retained result availability. A
VerificationRun then references that existing run/result target. Cache keys are implementation
tools, not civic identity.

### Source correction / new Representation

A corrected/reprocessed source creates new Representation identity/targets under existing custody
rules. Historical DerivationRuns and VerificationRuns keep their exact old inputs. They are not
silently retargeted or “invalidated in place”. New analysis creates new runs; a changed durable
proposition creates a new ClaimRevision.

### Program/verifier bug

Never mutate an old run. Record a new execution under the corrected implementation/configuration.
If a durable Claim or Assessment must change, use existing Claim revision or Assessment
supersession semantics.

## 11. Purge and tombstone consequences

Analytical/verification records can retain copied proposition text, executable literals, result
payloads, selector payloads, and rationale. The purge vocabulary must therefore add these
content-bearing families:

```text
derivation_run
derivation_run_egress
derivation_result
derivation_result_target
verification_run
verification_run_egress
assessment
```

Pure FK/ordinal joins (`derivation_run_inputs`, result lineage, verification scope/authority,
derivation uses, verification evidence) are deterministic execution closure and are reported by
per-table cleanup counts rather than given fake generic purge IDs.

Purge rules:

- `DerivationResult` may retain only an allowed opaque tombstone after its inline/archive payload,
  digest/size as required, and selectors are scrubbed;
- active `derived_inference` Claims require their analytical origin to remain attributable and
  available enough for the applicable policy. If a no-tombstone purge removes that origin, the
  dependent ClaimRevision/EvidenceLinks must be included in the frozen purge plan rather than left
  falsely reproducible;
- a minimal VerificationRun tombstone may preserve opaque identity and terminal execution status but
  not proposition/sufficiency/evidence payload that the purge is meant to remove;
- an Assessment whose required Verification basis cannot lawfully retain even a tombstone must be
  included in the same purge closure;
- existing archive shared-byte rules apply to archive-backed DerivationResults exactly as they do to
  other ArchiveObject consumers: core availability checks must treat retained DerivationResults as
  real ArchiveObject references, and physical bytes cannot be claimed erased while another retained
  logical record still references them.

No purge is inferred from ordinary source disappearance or a later failed run.

## 12. Schema delta authorized for the next unit

The next prerelease `0001` rebaseline is authorized to implement **only** this reconciled delta:

```text
ADD typed execution/result families
  derivation_runs
  derivation_run_egress
  derivation_run_inputs
  derivation_results
  derivation_result_targets
  derivation_result_lineage
  verification_runs
  verification_run_egress
  verification_scope_targets
  verification_authority_scopes
  verification_derivation_steps
  verification_evidence_items
  assessments

ALTER conceptually
  claim_revisions += derivation_result_target_id nullable + kind/origin invariants
  purge_target_kind += the seven content-bearing families listed above

KEEP
  ProcessRun semantics
  Representation same-Artifact custody semantics
  EvidenceLink source-evidence semantics
  ReviewDecision semantics
  Claim lifecycle semantics
  SourceAuthorityScope semantics
```

The implementation may choose exact column names/indexes after mechanical SQLite review, but it may
not collapse these distinctions or introduce a generic polymorphic run/evidence/assessment table.

## 13. Required mechanical proofs for the rebaseline

The `0001` implementation/certification unit must prove at least:

1. a successful DerivationRun has exactly one retained typed result and a failed run has none;
2. Derivation input/result-target ownership cannot cross runs/results through FK-valid but
   semantically impossible rows;
3. every lineage target belongs to an input scope of the owning DerivationRun;
4. result targets with `lineage_state=none|unavailable` cannot fabricate source-contribution rows;
5. a derived Claim cannot reference a result target from an unrelated/purged result;
6. non-derived Claims cannot misuse analytical-origin fields;
7. Verification `consumed` derivation-step targets belong to the stated successful DerivationRun,
   while failed/unused attempts cannot masquerade as consumed evidence;
8. Verification scopes cannot be silently expanded by Derivation inputs or evidence items;
9. failed Verification has no epistemic verdict; insufficient evidence is reachable only from a
   completed run with explicit insufficiency + abstention reason;
10. an Assessment based on Verification can target only the same exact ClaimRevision; machine/rule Assessments require that Verification basis plus registered policy identity, and supersession cannot jump assessor/policy lineage;
11. ClaimReview and Assessment can coexist with intentionally different meanings;
12. active `supports` evidence for a derived Claim can be mechanically traced to its exact
    DerivationResultTarget source lineage under registered selector containment rules, while
    independent `challenges` evidence remains legal;
13. rerun creates new run identity while persistence retry remains idempotent;
14. purge expansion includes every new content-bearing family and does not falsely claim archive
    byte erasure under shared references;
15. backup/restore, FK check, FTS rebuild, WAL/PRAGMA invariants and exact SQLite 3.53.4 certification
    remain green after the rebaseline.

## 14. Explicit non-goals / deferred only when proven necessary

This reconciliation does **not** authorize:

- Thucy role classes or a multi-agent runtime;
- a generic `OperationRun` supertable;
- DerivationRun recursive chaining;
- ClaimRevision as a Derivation input before a fixture proves it;
- storing every analytical result as a Representation;
- automatic Claim creation from a Derivation;
- automatic EvidenceLink creation from Verification;
- automatic Assessment promotion;
- mutable “current verification” or global truth columns;
- confidence scores spanning heterogeneous verifiers;
- a provider/model dependency or automatic metered fallback.

These are not TODOs owed to the architecture. They remain absent until a real use/proof requires
them.

## 15. Closure

This unit closes the conceptual gate that Phase D intentionally left open:

```text
DERIVATION_VERIFICATION_RECONCILIATION_PASS
SINGLE_EXECUTION_GRAPH__SOURCE_EVIDENCE_NOT_EXECUTION_LINEAGE
```

The next work is no longer conceptual decomposition. It is the bounded prerelease `0001` rebaseline
plus mechanical/runtime certification of this exact delta. No production verifier behavior is
required to freeze the persistence contract, but no production Derivation/Verification writer may
land before that rebaseline passes.
