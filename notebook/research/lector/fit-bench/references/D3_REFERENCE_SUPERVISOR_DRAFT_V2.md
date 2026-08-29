---
id: CANARIO-LECTOR-FIT-BENCH-D3-REFERENCE-SUPERVISOR-DRAFT-002
kind: benchmark-reference-candidate
state: supervisor-draft
authority: active-work-evidence
work: LECTOR-PRODUCTION-FIT-BENCH
fixture: CR-ESPARZA-PROCUREMENT-REGULATION-001
protocol: CANARIO-LECTOR-FIT-BENCH-REFERENCE-PROTOCOL-FREEZE-002
method: CANARIO-LECTOR-FIT-BENCH-REFERENCE-AUTHORING-METHOD-001
supersedes: CANARIO-LECTOR-FIT-BENCH-D3-REFERENCE-SUPERVISOR-DRAFT-001
---

# D3 semantic reference — supervisor draft v2

This is the supervising/cloud author's revised semantic reference candidate for the exact frozen D3
development fixture:

> Reglamento interno de contratación pública de la Municipalidad de Esparza y del Comité Cantonal
> de Deportes y Recreación de Esparza, frozen current version dated 10 April 2025.

It is **not frozen gold** and is not eligible for A0–A5 scoring.

## Why v2 exists

After local mechanical certification of v1, the supervising/cloud author performed a fresh
source→reference and reference→source adversarial review over all 54 articles and all 294 v1 facts.

That review found 48 localized findings:

- 30 minimality/decomposition repairs;
- 12 semantic/qualifier rewrites;
- 6 findings requiring both split and semantic rewrite.

The revised draft contains 350 facts. The increase is a consequence of separating genuinely
independent actions, actors, modalities, conditions, and procedural stages; it is not a target count.

The full non-independent review record is
`D3_SUPERVISING_AUTHOR_ADVERSARIAL_REVIEW_V1.json`.

## Identity boundary

The JSON companion remains bound to the exact F2 identities:

- primary source SHA256 `d6aed7b952ac8b6b1770dcbf957471390016507ef8ee2c98553f52ba5f579c59`;
- Representation SHA256 `3a32786f91a312b2dadae8e7e8af9349396886ca30bfc22d4dccbeb705799d28`;
- benchmark scope SHA256 `676e7b78bddc8f928481e95bcd15816a0cb827e5e9ae71e3226f4f709fef6d81`;
- unit inventory SHA256 `b744773c22ee862904052db0ee19bcbdf3674d5935016054795ad38705a87253`.

The January 2025 stale publication remains excluded.

## Review boundary

This v2 review was performed by the same supervising/cloud author that wrote v1. It is deliberately
recorded as **self-adversarial, not materially independent**.

Therefore:

```text
supervising_author_adversarial_review = complete
local_mechanical_certification_v2 = pending
independent_semantic_review = still required
reference_frozen = false
```

A small local model must not be used as a substitute for the independent semantic-review gate.
Local execution remains limited to mechanical certification, exact source evidence, tests, bundles,
and unchanged push.

## Article 27 primary-source ambiguity

The exact primary PDF itself was mechanically inspected after v1. The y)/z) region is malformed or
ambiguous in the primary source as well as the frozen Representation.

The draft therefore preserves:

```text
D3-UQ-0001
Article 27
A27-y / A27-z
NEEDS_ADJUDICATION
```

No semantic repair is inferred from missing text.

## Leakage / maturity

```text
reference_state = SUPERVISOR_DRAFT
formal_A0_A5_output_seen = false
formal_candidate_scores_seen = false
Acta_160_semantics_inspected = false
H2_selected_or_inspected = false
thresholds_frozen = false
production_implementation_authorized = false
```

The next permissible machine task is mechanical certification of this exact v2 candidate. A
successful mechanical certification still does not freeze the reference.
