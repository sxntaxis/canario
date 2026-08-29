---
id: ACTAKIT-STATUS-001
kind: status
state: LECTOR_PRODUCTION_FIT_BENCH_ACTIVE
created: 2026-08-19
updated: 2026-08-28
authority: operating-frontier
release_phase: prerelease
schema_compatibility_boundary: not-established
summary: LECTOR-PRODUCTION-FIT-BENCH is the single active Work. F1 semantics, F2 D1-D4 fixture identities, and reference protocol v2 are frozen; F3 reference authorship is active. No production broad-Lector implementation, provider lock-in, threshold freeze, A0-A5 run, or first vertical is authorized.
---

# Current Status

`docs/STATUS.md` is the compact present-tense frontier. It routes current work; it does not replace accepted architecture, source/tests/runtime reality, or Notebook research evidence.

## Re-entry

Read in this order:

```text
AGENTS.md
AGENT_MAP.toml
docs/STATUS.md
docs/work/20260827-lector-production-fit-bench.md
only the authority/evidence routed for that Work
```

Do not reconstruct permission from chats, branch names, roadmap ordering, completed PRs, or historical Notebook material.

## Published authority

Current accepted `main` after F2 fixture/source freeze merge PR #12:

```text
da3854bd25f3129244ae49d8cd79a16a2c777ad6
```

Governance candidate topic:

```text
797ca957a9363c51cbbbbc3c68052b70c0cd246b
```

REVIEW-002 remains certified/merged at:

```text
ce07da9466a638738c845f7fba152a47e9987a59
```

Current prerelease `0001` schema authority remains unchanged:

```text
SHA256 55b05a11f129cfbe1ffd199bcb6774ef8096f46424ebca6f43c169cb3eef7356
72 STRICT tables / 3 FTS5 / 137 explicit indexes / 155 FK child paths / 0 scans
0002 absent
```

## Current capability state

### Certified / merged substrate

- Depósito custody and INGRESS-001 Source Connector boundary;
- Esparza connector bounded real-network shadow ingestion;
- WORKBENCH-001 Representation-processing substrate;
- Poppler direct PDF, OCRmyPDF/Tesseract OCR, and bounded one-page Codex visual transcription adapters;
- LECTOR-001 semantic extraction **boundary/runtime**;
- Derivation / Verification schema + runtime, structured SQLite consumer and minimum structured verifier orchestration;
- REVIEW-001 Claim review backend;
- REVIEW-002 append-only human Claim correction/restriction/retraction backend;
- governance authority/frontier/Work reconciliation through PR #9.

### Important gates still open

**Broad production Lector is not closed.** No production mechanism has been selected. The active fit bench exists specifically to decide whether A0, A1, A2, A3, A4, A5, or no tested lane earns selection.

**Mesa de control product UX is not closed.** Backend mechanics exist; no human GUI/TUI is claimed complete.

**First vertical is not authorized.** Acta 160 remains a post-selection natural holdout and may not be used to tune the Lector.

## Frontier

```text
active product Work: docs/work/20260827-lector-production-fit-bench.md
research basis: notebook/research/lector/production-readiness/
Research Interrupt: resolved_to_fit_bench
production broad-Lector implementation: BLOCKED
first end-to-end Acta-160 vertical: PLANNED / BLOCKED
```

The active Work may freeze benchmark semantics/reference policy, prepare development fixtures, construct and independently audit semantic references, build bounded benchmark mechanics, and later run the declared A0-A5 comparison under its proof obligations. F3 currently uses the cloud-author/local-certifier split from `AGENTS.md`: semantic/reference writing belongs to the supervising author; the local agent performs mechanical source/hash/evidence/test certification. It may not promote a winner into production code.

## Explicitly unauthorized now

- production broad-Claim extractor implementation or provider/model architectural lock-in;
- treating A4, A5, Codex, or any other lane as selected before benchmark evidence;
- using Acta 160 semantic contents for tuning;
- certification/publication of the quarantined Phase-6 Codex extractor experiment;
- first vertical execution/certification;
- schema rebaseline unless benchmark mechanics unexpectedly prove a canonical invariant is missing, in which case stop for separate design review;
- canonical source cutover or historical mass import;
- query/output/Hilo implementation merely because it follows on the roadmap;
- GUI/MCP/tool-interface work;
- `0002` or compatibility scaffolding before the public compatibility boundary.

## Pre-release schema rule

Canario still has no public compatibility-bearing database fleet. Correct schema changes rebaseline `0001` and repeat applicable proofs. The active fit bench does not presently authorize a schema change.

## Planning is not authorization

`docs/ROADMAP.md`, `docs/IMPLEMENTATION_PLAN.md`, and `docs/RELEASE_1_0.md` describe horizons and gates. Their ordering never activates Work. The only active Work is the one named in the Frontier above.
