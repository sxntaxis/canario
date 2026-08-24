---
id: ACTAKIT-BOOK-SHACL-DEEP-001
type: research-source-book
state: deep-audited
authority: evidence
created: 2026-08-20
updated: 2026-08-20
researched_through: 2026-08-20
actakit_baseline: 59bab9de30bbf2aa1eec96dddaee3cded31a9f3a
source_ledger: sources.csv
claim_ledger: claims.csv
---

# SHACL

## Question

What does a mature validation language teach about extension validation?

## Deep-audit basis

W3C validation model separates data from validation results and exposes resource/recursion/conformance limits.

## Evidence horizon

- **AKS-S032 — SHACL:** Validation shapes separated from data model
- **AKS-S097 — SHACL 1.2 Core draft and test suite:** Shows continued validation-language evolution and links an explicit conformance test suite

## Claim ledger synopsis

- **AKS-C034:** Validation constraints can be a separate layer from the data vocabulary. **ActaKit:** Profiles/locators/outputs should have versioned validators rather than arbitrary JSON.
- **AKS-C058:** Typed/versioned validation contracts are a safer extension mechanism than arbitrary payloads. **ActaKit:** Locator/profile/output config schemas must be versioned and validated.
- **AKS-C130:** Validation standards continue to evolve with explicit test suites; conformance results are bounded by the shapes/tests executed. **ActaKit:** Treat validation reports as versioned process evidence, never as approval or truth state.

## Bounded transfer

Versioned validators for locator/profile/output payloads; validation result is evidence about shape conformance, not truth.

## Do not copy

Do not adopt RDF/SHACL runtime for core validation.

## Schema pressure / expensive mistake avoided

Extensible payloads need discriminator+schema version and bounded validator execution.

## Residual risk

Specific validator technology remains an implementation decision.

## Closure verdict

Deep-audited for the pre-SQL decision horizon. This Book contributes evidence and constraints; it does not independently authorize schema or implementation changes.
