# Canario governance reconciliation

Kind: work
Status: candidate
Created: 2026-08-27

## Goal

Restore a truthful current frontier and explicit consequential-Work authorization boundary before any further product implementation.

## Pressure

After REVIEW-002 merged, roadmap sequence was treated as permission to begin the first vertical proof. The vertical immediately exposed that Canario has a certified LECTOR-001 semantic boundary but no currently selected/certified production broad-Claim extractor, while LECTOR-002 is explicitly superseded and requires re-scope. A Codex extractor was then prototyped before that research/design gate was reopened.

This proves a governance defect: planning/predecessor completion was being used as implicit successor authorization.

## Scope

- adopt the small-project Salsa authority/frontier/Work separation without importing Stereo's heavier state engine;
- add a compact `AGENT_MAP.toml` for deterministic authority/routing/proof entrypoints;
- make `docs/STATUS.md` a concise present-tense frontier rather than a historical reconstruction surface;
- record that REVIEW-002 is merged and the current schema authority is its certified `0001`;
- mark broad production Lector readiness as an open prerequisite and WP7/Phase 6 vertical as planned but not authorized;
- record the Lector production-readiness Research Interrupt in Notebook working evidence;
- harden `AGENTS.md` so roadmap/planning/candidate/closure never auto-authorize successor Work.

## Non-goals

- no Lector implementation or provider selection;
- no resurrection/certification of the quarantined Codex vertical experiment;
- no Phase-6 vertical execution;
- no GUI, MCP/tool API, query/output implementation, or source cutover;
- no generic Program/state engine, EIS clone, or duplicate governance database;
- no Salsa runtime dependency inside Canario.

## Acceptance

- a fresh agent can answer from the declared frontier: what is accepted, what is reality, what is working evidence, what Work is authorized, what is blocked, and what may happen next;
- `ROADMAP` and `IMPLEMENTATION_PLAN` are visibly planning, not permission;
- no product implementation is active after this candidate;
- the next possible product edge is a separately approved Lector production-readiness Discovery/Research Work;
- the current schema/review status matches merged `main` rather than the pre-merge REVIEW-002 candidate;
- Notebook remains working/research evidence and owns no global authority;
- no source/test/runtime files change in this Work.

## Proof obligations

- TOML parses; all declared repo paths exist;
- candidate diff is governance/docs only;
- no Lector/Review/product source diff;
- `git diff --check` passes;
- declared package smoke remains valid;
- current `origin/main` remains the REVIEW-002 merge authority during review.

## Closure / next authorization

Candidate review must be explicit. Acceptance of this governance Work does **not** activate the next Lector Work. After acceptance, the owner may separately authorize a Lector production-readiness Discovery/Research Work that re-scopes LECTOR-002 before any extractor implementation.
