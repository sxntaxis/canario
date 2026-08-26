---
id: CANARIO-BOOK-APACHE_ARROW-001
type: research-source-book
state: research-complete-for-synthesis
authority: evidence
created: 2026-08-25
updated: 2026-08-25
researched_through: 2026-08-25
canario_baseline: a1d212c84830b3a0558dd4d1d9354cf10ac7a362
source_ledger: sources.csv
claim_ledger: claims.csv
---

# Apache Arrow

## Question

Should Arrow/Parquet become Canario's canonical structured evidence format or an interoperability layer?

## Evidence horizon

Current primary project/security documentation through 2026-08-25. This is a
bounded fit/security audit, not a performance benchmark.

## Claim ledger synopsis

- **ARR-C001:** Arrow is a language-independent columnar memory/interchange format optimized for analytical scans and zero-copy sharing. **Canario:** Strong bridge between typed projections and analytical engines if scale/interoperability requires it.
- **ARR-C002:** Arrow record batches carry schemas and typed arrays but do not preserve spreadsheet workbook semantics such as formulas, formatting, merged geometry, or source cell identity by themselves. **Canario:** Arrow cannot replace Canario's source-faithful typed spreadsheet Representation.
- **ARR-C003:** Arrow is a data format/toolbox rather than a source-authority or claim-verification system. **Canario:** Use only as derivative/interchange substrate, never as evidence semantics.

## Bounded transfer

**DEFER as a first-class dependency. Keep Arrow-compatible projection design in mind; adopt it when measured scale or multi-engine interchange makes zero-copy columnar exchange valuable.**

## Do not import

Do not replace the current typed source Representation with Arrow merely for performance. Source fidelity and analysis layout are separate concerns.

## Residual risk / unresolved question

At what dataset size/engine boundary does Arrow/Parquet materially reduce cost enough to justify another durable derivative format?

## Closure verdict

Research-complete for the fit-bench design gate. Runtime selection still requires
the civic fixture benchmark described in synthesis.
