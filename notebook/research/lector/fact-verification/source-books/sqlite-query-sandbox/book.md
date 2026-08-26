---
id: CANARIO-BOOK-SQLITE_QUERY_SANDBOX-001
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

# SQLite as bounded analytical executor

## Question

Can Canario's already-pinned SQLite runtime provide a sufficient and safer first structured reasoning executor?

## Evidence horizon

Current primary project/security documentation through 2026-08-25. This is a
bounded fit/security audit, not a performance benchmark.

## Claim ledger synopsis

- **SQLQ-C001:** SQLite supports aggregates, joins and window functions sufficient for many compositional structured queries. **Canario:** A simple SQLite baseline can test whether a second analytical engine is actually needed.
- **SQLQ-C002:** SQLite's authorizer can reject disallowed operations during statement preparation, including restricting an untrusted query surface. **Canario:** A verifier executor can whitelist read-only operations rather than trusting generated SQL.
- **SQLQ-C003:** SQLite recommends defensive/trusted-schema controls and disables extension loading by default. **Canario:** Canario can construct a hardened ephemeral query connection with a comparatively small attack surface.
- **SQLQ-C004:** The progress handler can interrupt long queries. **Canario:** Supports deterministic step/time budgeting in addition to process-level limits.
- **SQLQ-C005:** Official guidance still treats untrusted SQL/database input as a security-sensitive boundary. **Canario:** Use isolation and limits even with SQLite; authorizer is defense-in-depth, not proof of harmlessness.

## Bounded transfer

**ADOPT as the mandatory simple baseline because Canario already pins/certifies SQLite. Build the first fit bench with an ephemeral read-only relational projection, authorizer, defensive settings, extension loading off, progress/OS limits. Only add DuckDB if measured capability/performance justifies it.**

## Do not import

Do not query Canario's canonical application database directly with model-generated SQL. Create a purpose-built projection with no semantic write authority.

## Residual risk / unresolved question

Which exact SQLite authorizer allowlist and query budget cover benchmark cases without creating an accidental generic code-execution surface?

## Closure verdict

Research-complete for the fit-bench design gate. Runtime selection still requires
the civic fixture benchmark described in synthesis.
