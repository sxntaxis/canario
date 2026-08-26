# LECTOR-002 Semantic Reference Protocol

State: **historical scope frozen; semantic campaign superseded; replacement reference not authorized**.

This protocol governs benchmark validation only. The frozen scope is a bounded benchmark
scope, not a product-ingestion ontology or a production review policy. `machine-only`
remains a valid production state.

## Current disposition after SOTA review

The prior LECTOR-002 campaign is preserved as historical evidence but is not an active
semantic certification gate. In particular, the 24-row structured-table semantic scope and
BATCH-001 are superseded/non-authoritative. Do not resume assisted reference construction,
generate replacement gold, inspect a tested extractor, or create candidates until the
structured reasoning architecture and fit bench have produced a replacement capability
design.

The next authorized work is deterministic projection/executor validation followed by a
bounded planner/verifier fit comparison. This protocol's freeze ordering remains useful for
any future replacement semantic campaign, but does not authorize that campaign now.

## Separate States

The corpus keeps four independent facts per semantic case:

```text
gold_scope_state: pending | frozen
adjudication_state: not_run | incomplete | complete
semantic_verification[capability]:
  state: not_run | passed | failed
  result_sha256: null for not_run, immutable result digest otherwise
```

The internal filenames still use `gold` for the frozen benchmark reference. That does **not**
mean objective truth about the world. A reference proposition records what the retained source
asserts or contains, with exact reopenable evidence.

Frozen reference and complete candidate adjudication never verify a capability by themselves.
A semantic capability is verified only when a covering case has an exact frozen scope, frozen
reference, complete adjudication, a `passed` state, and a valid result digest. The threshold
policy must also be frozen after reference counts are inspected and before the tested extractor
runs.

## Reference authority

The historical LECTOR-002 workflow was:

```text
human_ai_assisted
```

The project owner and an external conversational assistant may jointly interpret the already
frozen evidence. The assistant may explain, decompose, or propose reference wording. Nothing is
accepted until the human explicitly approves it. This is recorded as **AI-assisted reference**,
not independent human gold.

The critical anti-leakage boundary is temporal:

```text
freeze source + scope
-> export exact evidence batch
-> human + assistant review
-> explicit human approval
-> mechanically import/reopen evidence
-> freeze reference
-> inspect reference counts
-> freeze scoring thresholds
-> only then run the tested extractor
```

The tested extractor, its candidates, and its scores must remain unseen while the reference is
being built. A reference decision file declaring `tested_extractor_seen=true` is rejected.

The original scope manifests legitimately retain `semantic_model_calls=0`: that field proves the
**scope itself** was frozen before semantic assistance. Later semantic assistance is declared in
`reference_provenance.jsonl` and in the frozen reference manifest instead of rewriting scope
history.

## Truth binding

Every approved reference truth binds to one or more semantic capabilities through sorted,
semicolon-separated `capability_ids`. A bound capability must be declared semantic reference
coverage for that case. Deterministic capabilities cannot appear in truth bindings. Candidates
never declare capability success.

`semantic:multi_topic_longform` is scope-wide. Its recall denominator is all truths in the frozen
selected scope, so the reference does not invent a topic ontology merely to tag each proposition.
Other semantic capabilities derive membership from explicit truth bindings.

## Frozen scope

Each packet contains canonical `gold_scope.json` bound to exact source and units digests, the
selected-unit digest, selection policy, and semantic capabilities. Scoring requires those
identities to match.

Coverage includes every prepared unit:

```text
selected:
  truth_recorded | no_material_truth | needs_adjudication
non-selected:
  unjudged
```

`needs_adjudication` is explicit unresolved uncertainty and blocks reference freeze/scoring.
A sampled structured-table result reports total units, selected units, selection kind, and
fraction; it cannot claim full-workbook semantic recall.

Current scopes:

- minutes: 61/61, full source order;
- structured table: 24/211, deterministic structural sample, superseded/non-authoritative;
- correspondence: 17/17, full source order;
- timed media: no semantic reference burden in the current campaign.

## Primary review workflow: evidence batch -> chat -> approved decisions

The interactive `human-review` terminal helper is retired from the active workflow. The primary
path is batch exchange.

Export up to five pending selected units without semantic interpretation:

```bash
PYTHONPATH=. python notebook/implementation/lector_002_benchmark.py export-assisted-review \
  --packet /ruta/al/packet \
  --output /ruta/al/lote.md \
  --count 5
```

The Markdown contains exact source/scope identity plus readable evidence and local physical
context. Export performs no classification, suggestion, model call, truth generation, or packet
mutation.

The Markdown may then be uploaded to the conversational assistant. Human and assistant discuss
each unit. After the human explicitly approves the final decisions, the assistant can produce a
structured decision JSON with:

```text
version = lector-002-assisted-reference:v1
reference_mode = human_ai_assisted
assistant product + model label
human_approval.state = approved
human_approval.approved_at_utc
batch identity copied exactly from the export
per-unit human_approved = true
decision = truth_recorded | no_material_truth | needs_adjudication
zero or more approved truths as allowed by the decision
```

For text truths the decision includes an exact `evidence_quote`; the importer derives offsets and
requires that quote to occur exactly once inside the selected unit. For table truths, the importer
builds the typed full-row selector mechanically from the frozen Representation and validates it
through the production `table_range:v1` reopening path.

Import only after explicit human approval:

```bash
PYTHONPATH=. python notebook/implementation/lector_002_benchmark.py import-assisted-review \
  --packet /ruta/al/packet \
  --decisions /ruta/a/decisiones-aprobadas.json
```

Import refuses:

- wrong source/scope/batch identity;
- units outside the frozen scope;
- already-reviewed units;
- missing human approval;
- unsupported capability bindings;
- semantic truths without exact reopenable evidence;
- any declaration that the tested extractor was already seen.

The import updates only the working packet's coverage/reference files after a timestamped backup.
It never edits the canonical tarball and never writes candidates or assessments.

`reference_provenance.jsonl` records batch identity, assistant/model label, human approval, unit
IDs, decision-file digest, and `tested_extractor_seen=false`. Exact assistant build IDs need not be
invented when the product does not expose them; the visible model label is recorded and the
limitation remains explicit.

## Freeze ordering

```text
1. freeze source + scope
2. complete human-approved assisted reference
3. validate and freeze reference
4. inspect reference counts only
5. freeze semantic scoring thresholds/policy
6. record tested-extractor identity and run it
7. adjudicate candidates against the frozen reference
8. score against frozen thresholds
```

`review-status` remains mechanical only. It reports coverage progress and performs no semantic
interpretation.

For AI-assisted reference, `freeze-gold` is invoked with the provenance file:

```bash
PYTHONPATH=. python notebook/implementation/lector_002_benchmark.py freeze-gold \
  ... \
  --reference-provenance /ruta/al/packet/reference_provenance.jsonl
```

The frozen manifest then records:

```text
reviewer_authority = human_ai_assisted
semantic_model_assistance = true
reference_provenance_sha256
reference_assistant_models
reference_assistance_sessions
human_approval_required = true
tested_extractor_seen = false
```

A provenance file must cover the entire selected scope exactly before an assisted reference can
freeze.

## Independence limitation at semantic certification

AI-assisted reference is useful benchmark evidence, but it is not independent of the assisting
model. Before semantic capability certification, record the tested extractor's model/provider
identity and compare it with the reference-assistant identity.

If the extractor is the same model/family/provider, or the relationship cannot be established,
that limitation must be explicit and an independent second-review sample is required before a
semantic PASS may be treated as strong certification evidence. Do not silently describe assisted
reference as independent human gold.

This rule does not change deterministic evidence certification and does not make production Claims
require human review.
