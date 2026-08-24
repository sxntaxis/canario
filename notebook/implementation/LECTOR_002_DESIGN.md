# LECTOR-002 — first real broad civic Claim extractor

State: **DESIGN / IMPLEMENTATION ACTIVE**

Base authority:

```text
main = 98c2d60387fd7ec176033563566f62c59123587d
LECTOR-001 = independently certified and integrated
0001 SHA256 = 5226c873487d9bd05fc62b7a1f323d6e804b003cc4e08bd2fe2b531adb6057bb
```

## Purpose

LECTOR-001 proved the semantic write boundary. LECTOR-002 must prove that a real
backend can turn one long official civic record into a useful broad set of
machine-only Claims without weakening evidence, provenance, identity or review
semantics.

The first target is the Municipalidad de Esparza official written archive entry:

```text
Acta Sesión Ordinaria N° 161
18 de mayo de 2026
official archive: /articulo/230/actas-concejo-municipal
```

The official archive still exposes Acta 161 as the newest written 2026 Concejo
record observed at design time. The source-specific connector resolves the hidden
CMS filename at runtime; the bench freezes the exact downloaded artifact SHA256
before any model run.

## Layering

LECTOR-002 does **not** read the PDF visually.

```text
official PDF
  -> Depósito
  -> Workbench
     -> direct/OCR/Codex visual only as needed
  -> accepted text Representation
  -> CodexClaimExtractor
  -> SemanticResult
  -> certified LectorWriter
  -> machine-only Fichero
```

Document-fidelity work remains in Mesa de trabajo. Semantic interpretation starts
only from an accepted readable Representation.

## Reference backend candidate

The first real candidate is the official Codex CLI through the already-qualified
subscription-backed execution venue:

```text
extractor key:      codex.claim_extract_text
capability:         claim_extract
origin:             machine
venue:              subscription_agent
provider:           openai
reference model:    gpt-5.6-sol
reference CLI:      codex-cli 0.149.0
input media:        text/plain
input kinds:        extracted_text | ocr_text | transcript | normalized_text
scope:              whole:v1 exactly one
requires egress:    yes
```

This selection is a candidate, not a declaration that Codex is a universal Lector
winner. LECTOR-001 keeps the backend replaceable.

## Security / prompt-injection boundary

The civic source is untrusted data. It is never concatenated as an instruction
that can override product policy.

The executor receives:

1. a static product-owned instruction/template;
2. one bounded JSON value whose `source_text` member contains the exact input text;
3. one bounded JSON output schema;
4. no repository, user home, arbitrary skills, shell, web, browser, plugins,
   apps, hooks, image generation or multi-agent capability.

The dedicated keyring-backed Codex profile and private scratch-HOME requirements
from PROCESSOR-CODEX-001 are reused as policy, but LECTOR-002 does not modify the
certified visual processor.

Credentials remain owned by Codex CLI and are never inspected or represented by
ActaKit.

## Model output is draft data

The model does not receive or choose canonical IDs.

Each candidate claim contains bounded fields equivalent to:

```yaml
local_key: c17
kind: source_assertion | derived_inference | verification_question
text: normalized atomic proposition
evidence:
  - exact_quote: exact copied source text
    relation: supports | quotes | contextualizes | challenges
mentions:
  - observed_text: exact source occurrence
    evidence_quote: exact quote containing the occurrence
attribution_text: optional source speaker/body text
temporal_start: optional
temporal_end: optional
sensitive: boolean
quantitative: boolean
```

Same-result ClaimRelations may also be proposed under the LECTOR-001 rules.
Entity resolution, Entity creation/reconciliation, human review, correction of
historical Claims and cross-document relation inference remain out of scope.

## Evidence adapter rule

The model is **never trusted for offsets**.

For each returned exact quote the adapter searches the exact decoded source text:

```text
0 matches  -> contract-invalid claim
1 match    -> adapter creates text_quote:v1 with deterministic start/end offsets
>1 matches -> ambiguous unless bounded context makes exactly one occurrence resolvable
```

The resulting `TargetRef` is still reopened again by LectorWriter before commit.
This is intentional defense in depth.

A source assertion cannot survive if its supporting/quoted evidence cannot reopen.

## Atomicity policy

Prefer recoverability over editorial summaries.

One Claim should express one proposition that can independently need:

- evidence,
- correction,
- retrieval,
- relation,
- review.

Do not split a single proposition merely because it contains a name/date/amount.
Do split independent decisions, commitments, findings, requests, quantities or
responsibilities that could later change independently.

Examples:

```text
BAD:
"El Concejo aprobó el proyecto, asignó ₡25 millones y pidió a AyA coordinar."
  # three independently useful propositions fused

GOOD:
A. "El Concejo aprobó el proyecto."
B. "El Concejo asignó ₡25 millones al proyecto."
C. "El acta dispone que AyA coordine las obras."
```

## Civic relevance policy

Broad extraction favors future recoverability.

Material positive classes include:

- decisions, votes and agreements;
- requests, commitments and responsibilities;
- budgets, amounts, quantities and transfers;
- deadlines and material dates;
- projects, public works and services;
- contracts/procurement and public resources;
- reported problems/complaints;
- institutional responses;
- findings, recommendations and outcomes;
- material statements by identifiable actors;
- retrieval-relevant institutions, people, places, projects and legal instruments.

Procedural/noise classes normally excluded:

- routine approval/reading of prior minutes with no material objection;
- greetings and ceremonial closure;
- minute of silence;
- routine recess;
- purely formal motion of order;
- bare "se da por recibido" with no consequence;
- attendance/quorum bookkeeping unless itself material to a civic question.

The old `skills/procesar-acta` policy is evidence for this distinction, but
LECTOR-002 produces Claims rather than Hilo/Episode prose.

## Independent quality truth

The real Acta 161 bench must create truth **before inspecting candidate model
output**.

Truth rows are atomic civic propositions and include:

```text
truth_id
article/item label when available
importance = must | material | optional
canonical proposition
one or more exact source quotes
expected relevant EntityMention strings
noise = false
```

A separate procedural-noise inventory samples material that must not become
ordinary civic Claims.

Truth is not generated from the candidate extractor output.

## Frozen quality metrics

### Hard integrity gates

All must pass:

```text
schema-valid model result                         = 100%
persisted Claim evidence reopening                = 100%
unsupported persisted Claims                      = 0
claims with fabricated human review               = 0
name-equality Entity resolution                   = 0
restricted source egress                          = 0
replay duplicate explosion                        = 0
```

### Civic quality gates

For the frozen full-document truth set:

```text
must-capture proposition recall                   = 100%
all material proposition recall                   >= 0.90
unsupported / materially distorted claim rate     = 0
relevance precision excluding procedural noise    >= 0.95
relevant EntityMention recall                     >= 0.90
over-merged material proposition rate             <= 0.05
materially redundant/duplicate claim rate         <= 0.05
```

Over-splitting is reviewed separately because several narrow Claims may be useful
without being duplicates. It fails only when the split loses proposition meaning
or creates misleading fragments.

No universal numeric "confidence" is introduced into canonical Claims.

## Operational measurements

The real run records:

```text
exact artifact SHA256
exact accepted text Representation SHA256
Codex CLI/model identity
configuration hash
request-template hash
output-schema hash
source bytes egressed
wall latency
peak process-tree RSS where measurable
input characters
raw candidate Claim count
persisted Claim count
rejected-invalid quote count
truth recall/precision metrics
```

Host fingerprinting is prohibited. Do not persist hostname, username, CPU/GPU,
RAM totals, kernel build, personal paths or environment dumps.

## Failure semantics

```text
pre-handoff failure
  -> failed ProcessRun, egress_bytes=0, no Claims

schema-invalid / malformed response
  -> failed ProcessRun, truthful error code, no Claims

some candidate claims have invalid/ambiguous evidence
  -> reference candidate fails the run rather than silently dropping them during
     certification; a future explicit partial policy requires its own proof

valid output, quality benchmark below threshold
  -> implementation not certified even though the adapter contract works
```

For the certification candidate, silent model-output salvage is deliberately
forbidden. Quality errors must remain visible.

## Scope exclusions

LECTOR-002 does not authorize:

- historical mass import;
- canonical Esparza cutover;
- human review workflow;
- Claim correction/retraction;
- cross-document ClaimRelation discovery;
- Entity creation/resolution/reconciliation;
- arbitrary Tag creation;
- Hilo migration/output rewrites;
- provider API fallback;
- heavyweight local LLM/VLM fallback.

## Gate

LECTOR-002 closes only when:

1. the adapter passes deterministic contract/security/replay tests;
2. Acta 161 is fetched from the official source and frozen by exact hash;
3. an independently prepared full-document truth/noise set is frozen before the
   candidate model output is scored;
4. the exact qualified Codex CLI/model run satisfies all hard integrity and civic
   quality thresholds;
5. persisted Claims reopen to exact evidence through LECTOR-001;
6. replay does not reinvoke Codex or duplicate semantic rows;
7. the candidate remains unchanged through independent certification.
