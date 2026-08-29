---
id: CANARIO-LECTOR-FIT-BENCH-D4-REFERENCE-SUPERVISOR-DRAFT-001
kind: benchmark-reference-candidate
state: supervisor-draft
authority: active-work-evidence
work: LECTOR-PRODUCTION-FIT-BENCH
fixture: CR-CGR-SANTA-ANA-PROCUREMENT-AUDIT-001
protocol: CANARIO-LECTOR-FIT-BENCH-REFERENCE-PROTOCOL-FREEZE-002
method: CANARIO-LECTOR-FIT-BENCH-REFERENCE-AUTHORING-METHOD-001
---

# D4 semantic reference — supervisor draft v1

This is the supervising/cloud author's semantic reference candidate for the exact frozen D4 development fixture:

> Informe de auditoría sobre la gestión de contratación pública en la Municipalidad de Santa Ana,
> informe n.° DFOE-LOC-IAD-00011-2024, Contraloría General de la República, 28 June 2024.

It is **not frozen gold** and is not eligible for A0–A5 scoring.

## Identity boundary

The draft is bound to the exact F2 identities:

- primary PDF SHA256 `587e4ba2ca65c4a3f453471434ca69b41ba71fe59ae64897590b1fc6c44c97fe`;
- Representation / benchmark-scope SHA256 `324dfd50e4cee6619bf0f8cbce223004bc34bd9d980cad90823f3a195111893d`;
- unit inventory SHA256 `b4c45ebccf7bfc4ec02d902aaa96b7f968bcc07719b40ceef28c79985bf1c5b4`;
- unit count `260`.

The full 28-page frozen report scope is used.

## Authoring and semantic passes

The supervising/cloud author read the exact frozen text scope in source order and authored the semantic propositions, qualifiers, capability bindings, evidence selections, structure ledger, omission pass, and reverse fact audit.

The resulting draft contains:

```text
facts                         185
structure carriers            142
frozen units                  260
evidence targets              187
cross-unit facts              101
multi-evidence facts            2
unresolved source regions       1
```

The reference covers the report's audit scope/method, procurement quantities, planning findings, the 15 ordinary-procedure table, exception-procedure findings, cited legal duties, control/corruption findings, conclusions, and dispositions 4.4–4.9 including their compliance dates.

Executive-summary statements are mapped to detailed facts when semantically equivalent. Assertions present only in executive-summary text remain explicit facts. Text-visible table rows are represented individually. Figure/image details that are absent from the frozen text Representation are not invented.

## Explicit unresolved source region

The extracted text preserves this footnote fragment:

```text
Cinco corresponden por proveedor único, cuatro por reparaciones indeterminadas y uno por bienes o servicios
artísticos, culturales e intelectuales
```

but does not preserve an unambiguous footnote marker/referent. It remains:

```text
D4-UQ-0001
FN4-EXCEPTION-BREAKDOWN
NEEDS_ADJUDICATION
```

The local mechanical certifier may inspect the exact frozen primary PDF and return the literal footnote marker/referent evidence. It may not write or repair the semantic reference.

## Review boundary

```text
supervising_author source-order pass     complete
supervising_author omission-only pass    complete
supervising_author reverse fact audit    complete
local mechanical certification           pending
independent semantic review               required / incomplete
reference frozen                          false
```

A small local model must not substitute for semantic authorship or the materially independent semantic-review gate. Local execution is limited to source/hash/selector verification, tests, exact source evidence, bundle transport, and unchanged push unless separately authorized.

## Leakage boundary

```text
formal A0-A5 output seen             false
formal candidate scores seen         false
Acta 160 semantics inspected         false
H2 selected or inspected             false
thresholds frozen                    false
production implementation authorized false
```
