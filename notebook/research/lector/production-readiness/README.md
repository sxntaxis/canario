# Canario Lector production-readiness research package v1

State: **research evidence only — no implementation authorization**

Baseline: `ce07da9466a638738c845f7fba152a47e9987a59`

Researched through: `2026-08-27`

This package follows `notebook/research/PACKAGE_PROTOCOL.md`:

```text
Source Books
-> claims/evidence
-> fit matrix
-> transfers
-> gap audit
-> synthesis
-> fit-bench design candidate
```

It intentionally does **not** contain production code, a model prompt, benchmark gold, or an
implementation candidate.

## Books

- `B01-canario-authority`
- `B02-claimify`
- `B03-claim-quality-metrics`
- `B04-decomposition-context`
- `B05-long-document-processing`
- `B06-langextract`
- `B07-openie-evaluation`
- `B08-structured-output-reliability`
- `B09-source-fidelity`
- `B10-spanish-domain-transfer`

## Synthesis

- `synthesis/claims.csv`
- `synthesis/fit-matrix.csv`
- `synthesis/transfers.csv`
- `synthesis/gap-audit.md`
- `synthesis/BOOK.md`
- `synthesis/FIT_BENCH_DESIGN_CANDIDATE.md`

## Repository preservation note

The complete Source Books, claim ledgers, fit matrix, transfers and gap audit are preserved byte-for-byte in:

```text
source-package-v1.tar.xz
SHA256 0d18bdb07949ba77bbf1494d3f4d0834226345e1328eda1a2b022c41ddf412b1
```

`MANIFEST.json` is copied out for inspection. The archive remains **research evidence only**; the active Work is the authorization surface.
