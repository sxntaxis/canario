---
id: CANARIO-LECTOR-FIT-BENCH-D3-REFERENCE-SUPERVISOR-DRAFT-001
kind: benchmark-reference-candidate
state: supervisor-draft
authority: active-work-evidence
work: LECTOR-PRODUCTION-FIT-BENCH
fixture: CR-ESPARZA-PROCUREMENT-REGULATION-001
protocol: CANARIO-LECTOR-FIT-BENCH-REFERENCE-PROTOCOL-FREEZE-002
method: CANARIO-LECTOR-FIT-BENCH-REFERENCE-AUTHORING-METHOD-001
---

# D3 semantic reference — supervisor draft v1

This artifact is the supervising/cloud author's source-exhaustive semantic reference candidate for
the frozen D3 development fixture:

> Reglamento interno de contratación pública de la Municipalidad de Esparza y del Comité Cantonal
> de Deportes y Recreación de Esparza, current frozen version dated 10 April 2025.

It is **not frozen gold** and is not eligible for A0–A5 scoring.

## Identity boundary

The JSON companion is bound to the exact F2 identities:

- primary source SHA256 `d6aed7b952ac8b6b1770dcbf957471390016507ef8ee2c98553f52ba5f579c59`;
- Representation SHA256 `3a32786f91a312b2dadae8e7e8af9349396886ca30bfc22d4dccbeb705799d28`;
- benchmark scope SHA256 `676e7b78bddc8f928481e95bcd15816a0cb827e5e9ae71e3226f4f709fef6d81`;
- unit inventory SHA256 `b744773c22ee862904052db0ee19bcbdf3674d5935016054795ad38705a87253`.

The January 2025 stale publication remains excluded.

## Authoring boundary

The semantic propositions, qualifiers, capability bindings, structure exhaustion decisions, and
reverse semantic audit notes were authored by the supervising/cloud author under
`REFERENCE_AUTHORING_METHOD_V1.md`.

The local execution agent is not authorized to alter those semantics. Its next job is only to:

- recover and verify the exact D3 source pack;
- validate source/Representation/scope/unit identities;
- mechanically reopen every evidence selector;
- validate selector containment, hashes, unit references, JSON invariants, and repository tests;
- return any failure unchanged to the supervising author;
- push the exact candidate only if all mechanical checks pass.

## Explicit unresolved primary-text region

Article 27 contains a malformed y)/z) region in the frozen text Representation:

```text
Gestionar los trámites relacionados con modificaciones presupuestarias que se requieran para asumir
z) Vigente. El pago de la contratación.
```

The supervisor draft does **not** guess a proposition from that text. The region remains
`NEEDS_ADJUDICATION` and must be checked against the exact primary source during local mechanical
certification. A local agent may report the primary-source evidence, but may not silently author or
repair the semantic fact.

## Maturity / leakage

```text
reference_state = SUPERVISOR_DRAFT
local_mechanical_certification = pending
independent_semantic_review = required
reference_frozen = false
thresholds_frozen = false
formal_A0_A5_output_seen = false
formal_candidate_scores_seen = false
Acta_160_semantics_inspected = false
H2_selected_or_inspected = false
production_implementation_authorized = false
```

A successful local mechanical certification advances evidence only. It does not freeze this
reference. A materially independent semantic reviewer must still audit source→reference coverage and
reference→source faithfulness under Reference Protocol v2.
