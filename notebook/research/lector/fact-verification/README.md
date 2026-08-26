---
id: CANARIO-RESEARCH-LECTOR-FACTVER-001
type: research-package
state: research-complete-for-architecture-gate
authority: evidence
created: 2026-08-25
updated: 2026-08-25
researched_through: 2026-08-25
baseline: a1d212c84830b3a0558dd4d1d9354cf10ac7a362
---

# Claim extraction, structured reasoning, and verification SOTA audit

This package pauses LECTOR-002 implementation to test Canario's current direction
against established work in claim verification, structured-data reasoning, evidence
retrieval, hybrid-document verification, temporal verification, and human-facing
evidence attribution.

The research question is not "which paper should Canario copy?" It is:

> Which parts of Canario are genuinely product-specific, which benchmark or
> reasoning mechanisms already have mature prior art, and where should Canario
> reuse or benchmark external systems rather than build a private substitute?

## Boundary

Canario's full evidence pipeline remains broader than the systems studied here:

```text
acquisition -> custody -> typed Representation -> source-claim extraction
            -> derived analysis / verification -> Fichero / review / outputs
```

Most external systems begin with a claim and an already-accessible evidence corpus.
They therefore cannot replace Canario's custody, Representation, source-authority,
or heterogeneous-ingress architecture. They can, however, invalidate bespoke
approaches inside the semantic reasoning and verification layers.

## Source Books

- `claimdb/`
- `thucy/`
- `frame-guided-oecd/`
- `feverous/`
- `findver/`
- `scitab/`
- `averitec/`
- `tsver/`
- `casefacts/`
- `claimver/`

Supporting works and lineage references are catalogued in
`notebook/research/references.bib` and `notebook/research/LITERATURE_MAP.md`.

## Synthesis

See `synthesis/BOOK.md` and the machine-readable ledgers beside it.

No implementation authorization is implied by this package. The promotion path
remains:

```text
Source Books
-> synthesis
-> fixtures / counterexamples / fit experiments
-> explicit design decision
-> contracts
-> implementation
```
