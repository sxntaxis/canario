---
id: ACTAKIT-STATUS-001
kind: status
state: GOVERNANCE_RECONCILIATION_CANDIDATE
created: 2026-08-19
updated: 2026-08-27
authority: operating-frontier
release_phase: prerelease
schema_compatibility_boundary: not-established
summary: REVIEW-002 is certified and merged. No product implementation is currently authorized. Governance reconciliation is a candidate; broad production Lector readiness remains open and blocks the first end-to-end vertical.
---

# Current Status

`docs/STATUS.md` is the compact present-tense frontier. It routes current work; it does not replace accepted architecture, source/tests/runtime reality, or Notebook research evidence.

## Re-entry

Read in this order:

```text
AGENTS.md
AGENT_MAP.toml
docs/STATUS.md
active Work, if and only if one is explicitly active
only the authority/evidence routed for that Work
```

Do not reconstruct current permission from old chats, branch names, roadmap ordering, completed PRs, or historical Notebook material.

## Published authority

Current `main` after REVIEW-002:

```text
ce07da9466a638738c845f7fba152a47e9987a59
```

REVIEW-002 certified topic:

```text
5d145828a8724ca0ea8e6420e5d5e09de664f74c
```

Current prerelease `0001` schema authority:

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
- REVIEW-002 append-only human Claim correction/restriction/retraction backend.

### Important gates still open

**Broad production Lector is not closed.** LECTOR-001 proves the generic boundary and writer, not that a selected production extractor can recover a broad civic Claim set with acceptable semantic quality. The previous LECTOR-002 campaign is superseded and requires re-scope.

**Mesa de control product UX is not closed.** Review/correction backend mechanics are certified; no human GUI/TUI is being claimed complete. Backend-first sequencing is intentional.

**First vertical is not authorized.** It depends on broad production Lector readiness.

## Frontier

```text
active product Work: none
candidate governance Work: docs/work/20260827-canario-governance-reconciliation.md
blocker: Lector production-readiness Research Interrupt
working evidence: notebook/research/LECTOR_PRODUCTION_READINESS_INTERRUPT.md
planned later: first end-to-end acta vertical
```

The next possible product Work is **not implementation**. After this governance candidate is accepted, a separate owner-approved Lector production-readiness Discovery/Research Work may be activated.

## Explicitly unauthorized now

- any production broad-Claim extractor implementation or provider selection;
- certification/publication of the quarantined Phase-6 Codex extractor experiment;
- first vertical execution/certification;
- canonical source cutover or historical mass import;
- query/output/Hilo implementation merely because it follows on the roadmap;
- GUI/MCP/tool-interface work;
- `0002` or compatibility scaffolding before the public compatibility boundary.

## Pre-release schema rule

Canario still has no public compatibility-bearing database fleet. Correct schema changes rebaseline `0001` and repeat applicable proofs. Forward migrations begin only after an explicit Beta/public compatibility boundary.

## Planning is not authorization

`docs/ROADMAP.md`, `docs/IMPLEMENTATION_PLAN.md`, and `docs/RELEASE_1_0.md` describe horizons and gates. Their ordering never activates Work. `ready`, predecessor completion, certification, merge, or an empty frontier likewise do not authorize the next product change.
