---
id: CANARIO-LECTOR-PRODUCTION-READINESS-SYNTHESIS-001
type: research-synthesis
state: research-complete-for-fit-bench-design
authority: evidence
created: 2026-08-27
updated: 2026-08-27
researched_through: 2026-08-27
baseline: ce07da9466a638738c845f7fba152a47e9987a59
---

# Lector production-readiness research synthesis

## Executive conclusion

The research does **not** authorize a production broad extractor.

It does establish that the premature vertical experiment's implicit design —

```text
whole long Representation
-> one large model call
-> big JSON containing many Claims
-> exact quote validation
```

— is not a defensible production default.

Across claim-extraction evaluation, OpenIE, long-document processing, structured extraction, source
fidelity and Spanish-domain evidence, the recurring failures are:

```text
omission / low coverage
context loss from over-decomposition
ambiguity guessed instead of preserved
long-context lost-in-the-middle behavior
cross-chunk dependency/conflict
semantic duplicates and conflicting paraphrases
schema breadth / output-format sensitivity
source-grounded-looking claims that still overstate evidence
parametric world knowledge "correcting" the source
language/domain transfer failures
```

## ELI5

The Lector should not behave like:

```text
"Read this 40-page PDF and tell me everything important."
```

Nor like:

```text
"Cut it into 100 pieces, ask 100 independent questions, concatenate the answers."
```

The leading hypothesis is closer to:

```text
1. divide the faithful Representation into deterministic, source-preserving units;
2. give each unit enough bounded surrounding/structural context to understand it;
3. extract broad civic propositions while explicitly refusing unresolved ambiguity;
4. ground every proposition in exact source evidence;
5. audit the source units for material civic content that the first extraction missed;
6. target repair only at uncovered material;
7. reconcile duplicates/conflicts/qualifiers across unit boundaries;
8. hand the bounded drafts to the already-certified LECTOR-001 writer.
```

That is a **hypothesis to measure**, not implementation authorization.

## Decision candidate

```text
BROAD_LECTOR_MECHANISM_NOT_SELECTED
RUN_CANARIO_NATIVE_LECTOR_FIT_BENCH
```

The fit bench should compare the same model/provider and frozen sources across:

- **A0** whole-document one-shot baseline;
- **A1** one-pass structure-aware chunk baseline;
- **A2** repeated independent chunk passes;
- **A3** Claimify-inspired contextual selection/disambiguation/decomposition;
- **A4** fixed Canario pipeline: contextual extraction + explicit coverage audit + targeted repair +
  semantic reconciliation;
- **A5** heavier dynamic agentic decomposition as a challenger only.

The goal is not to reward complexity. The selected production mechanism is the **simplest lane that
passes the frozen semantic gates**.

## Proposed replacement LECTOR-002 capability families

### Text semantic quality

- `semantic:civic_coverage`
- `semantic:civic_focus`
- `semantic:source_entailment`
- `semantic:self_sufficient_minimality`
- `semantic:attribution_preservation`
- `semantic:conditions_exceptions_scope`
- `semantic:negation_modality`
- `semantic:temporal_preservation`
- `semantic:quantitative_exactness`
- `semantic:ambiguity_handling`
- `semantic:cross_unit_context`
- `semantic:duplicate_reconciliation`
- `semantic:source_fidelity_counterfactual`

Names are candidates, not contracts.

### Evidence quality

Keep deterministic typed evidence gates already established:

- exact text target reopening;
- correct evidence membership for each reference fact;
- multi-evidence support where necessary;
- source/page/span presentation projection tested separately from semantic authority.

### Structured / media lanes

Do **not** flatten these into the text campaign.

- Tables: explicit source values may be extracted as claims where useful, but numerical/cross-table
  composition remains Derivation/Verification.
- Media: semantic text extraction normally operates over a timed transcript Representation; timed
  evidence remains media evidence.
- Image/layout semantics not preserved in a faithful Representation require a modality-specific
  Lector lane, not silent text substitution.

## Reference design

Reuse the strong historical anti-leakage order:

```text
freeze source bytes + Representation + deterministic scope
-> build human-approved semantic reference without tested extractor output
-> represent reference as semantic fact-equivalence objects, not one required wording
-> bind each fact to exact evidence and mandatory qualifiers/capabilities
-> inspect reference counts
-> freeze scoring/threshold policy
-> only then run A0–A5
-> adjudicate candidate facts against frozen reference
-> score per fixture + per capability
```

When the reference assistant and tested extractor share a model/provider family, require an
independent second-review sample before a semantic PASS is treated as strong evidence.

## Metrics

Do not collapse readiness into one number.

Primary semantic gates:

1. **Coverage / recall** over frozen reference facts.
2. **Focus / precision** against the frozen definition of material civic information.
3. **Source entailment / faithfulness** for every emitted Claim.
4. **Context preservation**: attribution, conditions, exceptions, negation, temporal and quantitative
   qualifiers.
5. **Self-sufficiency + minimality**, not maximum atomization.
6. **Ambiguity behavior**: unresolved cases preserved/abstained, never guessed.
7. **Evidence correctness**: exact target reopens and actually supports the proposition.
8. **Duplicate/conflict reconciliation** across overlapping/context units.

Secondary operational metrics:

- model calls;
- source bytes/egress;
- prompt/output bytes or tokens where observable;
- latency;
- failures/timeouts;
- run-to-run variance;
- cost only where the execution venue exposes it reliably.

No average may hide a failed capability or Spanish fixture.

## Fixture strategy

Use benchmark archetypes only to select stress sources.

Recommended semantic text fixtures:

- **Acta 161**: long Spanish institutional minutes; full-source scope already prepared historically.
- **INCOP correspondence**: attribution + conditions/exceptions/cross-references; existing frozen scope.
- add at least one **Spanish normative/contractual** source with dense conditions, definitions and
  internal references;
- add at least one **report/audit/technical** source with findings, recommendations, quantities and
  mixed narrative structure.

Keep **Acta 160** out of the extraction benchmark. It was selected for the interrupted vertical and
should remain a natural **post-selection holdout**:

```text
fit bench chooses Lector
-> freeze production candidate
-> then Acta 160 end-to-end vertical
```

This is stronger evidence against acta/fixture overfitting.

Structured table and timed-media cases remain separate declared-capability lanes.

## What to do with the quarantined vertical findings

Re-evaluate later, under the selected Work:

- initial active Claim FTS projection appears worth a focused invariant check;
- Poppler page ordinal as a derived UI projection appears plausible;
- the specific Codex whole-document extractor is **not** retained as a candidate design;
- the Acta-160 harness may be useful only after conversion into a holdout vertical proof.

## What is explicitly not authorized

- no production broad extractor;
- no prompt freeze;
- no Codex-specific architecture;
- no benchmark gold generation yet;
- no product-schema change;
- no dynamic agent framework;
- no MCP/GUI work;
- no Phase-6/WP7 certification.

## Next Work candidate

After governance reconciliation is accepted, the next owner-authorized Work should be:

```text
LECTOR-PRODUCTION-FIT-BENCH
```

Scope: freeze the replacement capability/reference design and measure A0–A5 (or a justified reduced
set) on extractor-blind real fixtures.

Implementation of the winning production extractor is a **later Work**, activated only after the fit
bench's explicit design decision.
