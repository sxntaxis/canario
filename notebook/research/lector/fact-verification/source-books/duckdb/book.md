---
id: CANARIO-BOOK-DUCKDB-001
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

# DuckDB

## Question

Is DuckDB an appropriate bounded analytical executor or canonical structured Representation for Canario?

## Evidence horizon

Current primary project/security documentation through 2026-08-25. This is a
bounded fit/security audit, not a performance benchmark.

## Claim ledger synopsis

- **DDB-C001:** DuckDB is an in-process analytical SQL database designed for OLAP and common analytical file formats. **Canario:** Strong candidate executor for derived structured analysis.
- **DDB-C002:** Direct XLSX reading infers headers, ranges and types and may stop at empty rows; empty cells and number formats influence inferred types. **Canario:** Do not use DuckDB's XLSX reader as Canario's canonical Representation authority.
- **DDB-C003:** DuckDB documentation explicitly warns that untrusted SQL should be treated like Bash/Python and sandboxed. **Canario:** Never run model-generated DuckDB SQL in the privileged Canario process.
- **DDB-C004:** DuckDB can access files/network/load extensions unless restricted; autoload/autoinstall/community extensions can be disabled. **Canario:** Any evaluator must run with external access/extensions disabled and OS/process isolation.
- **DDB-C005:** Threads, memory and temporary disk use can be bounded. **Canario:** Supports a bounded analytical executor profile suitable for benchmarking.

## Bounded transfer

**BENCHMARK as the leading analytical executor candidate, but only over a deterministic projection derived from Canario's canonical typed Representation. Run in a sandboxed process with extensions/network/file access constrained.**

## Do not import

Do not replace the canonical typed XLSX Representation with DuckDB's inferred XLSX import, and do not execute untrusted/model SQL in-process.

## Residual risk / unresolved question

Does DuckDB materially outperform a hardened SQLite executor on representative civic workloads enough to justify a new runtime dependency?

## Closure verdict

Research-complete for the fit-bench design gate. Runtime selection still requires
the civic fixture benchmark described in synthesis.
