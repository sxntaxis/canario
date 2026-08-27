# REVIEW-001 — Claim review workflow core

State: **IMPLEMENTED CANDIDATE — EXACT SQLITE + NATURAL ESPARZA REVIEW PROOF PENDING**

Baseline authority:

```text
structured verifier orchestration merge: e5a0485dac2db7e5eff61b3cee1dc11c20ae5858
frozen 0001 SHA256:                 8d6f793e1c976221311bd73ffe03bdaa2907e9508e7c0f5fad59131a02dc9f96
```

## Purpose

WP6 / Mesa de control begins with review decisions over exact ClaimRevisions. The first production
unit deliberately does **not** add UI, staffing roles, a heavyweight ReviewBatch entity, or new SQL.
It exposes the minimum safe core that a CLI/GNOME/web operator surface can call later:

```text
current machine/rule ClaimRevisions for one Representation
-> deterministic review queue / exact subject fingerprint
-> operator opens exact retained evidence
-> one strict | batch | supervised ReviewAction
-> exact per-ClaimReview decisions
-> derived machine-only / human-reviewed / strict-ready state
```

Review remains separate from Claim lifecycle. A human `rejected` review does not silently rewrite
`claim_revisions.lifecycle`; correction/restriction lineage is a following review unit.

## Product surface

`canario.review` adds:

- `ReviewReader` for deterministic review queues, current review state, and exact evidence reopening;
- `ReviewWriter` as sole canonical writer for `review_actions` + `claim_reviews`;
- typed `ClaimReviewActionRequest` / `ClaimReviewDraft` contracts;
- typed deterministic `ClaimBatch` with selection-policy identity and subject-set SHA-256;
- `ClaimBatchReviewRequest` with one default decision plus explicit per-subject exceptions;
- immutable receipts and exact replay/collision behavior.

The existing frozen tables are sufficient. `0001` is unchanged and no `0002` exists.

## Review semantics

### Supervised

Unreviewed machine/rule Claims remain valid records. `ReviewReader.claim_state()` exposes
`machine_only=True` until a real human decision exists. No synthetic acceptance row is written.

### Strict

`strict_ready` is derived only when the exact current revision is `lifecycle='active'` and its latest
human ClaimReview decision is `accepted`. Absence of review, `needs_work`, or `rejected` is not
strict-ready.

### Batch

A batch is a deterministic ordered set of exact current machine/rule ClaimRevisions that have current
active evidence on one exact Representation. Accepted/rejected completed subjects leave the default
queue; `needs_work` may remain for a later pass.

One ReviewAction may cover the whole exact set. Membership is still durable because every subject
receives an explicit `claim_reviews` row linked to the same action. A heavyweight ReviewBatch table
is therefore not required for this first gate.

## Concurrency and stale-write boundary

Batch submission re-checks, inside the same `BEGIN IMMEDIATE` as the write, that every subject:

1. is still the exact current ClaimRevision;
2. still has current active evidence on the Representation used to prepare the batch.

If a Claim was superseded or its current evidence moved, the entire action fails before any review
row is written. Stable ReviewAction IDs replay only when actor/mode/note and every exact decision
match; an occupied ID with different content fails closed.

## Exact evidence opening

`ReviewReader.open_claim()` resolves each current active EvidenceLink through its exact
RepresentationTarget and retained ArchiveObject. Archive digest/size authority is reverified before
bytes are read.

Supported first-unit previews:

- `text_quote:v1`: exact quote + bounded context/offset metadata after deterministic reopening;
- `table_range:v1`: exact structural coordinates + observed represented values after reopening;
- `media:v1`: exact bounded time span + transcript anchor when present after reopening;
- `whole:v1`: retained digest + byte size.

Unknown/non-reopenable fine-grained selectors fail closed rather than pretending locator metadata is
verified evidence.

## Natural proof

`notebook/implementation/prove_review_workflow_core.py` reuses the already-frozen official Esparza
Acta 161 PDF:

```text
SHA256: ffb354c67d8b56ebf265884c820a98fee27015cadaac3ea1011069f7969b8bfd
bytes: 760485
page: 4
```

The proof intentionally does not benchmark extraction semantics. It:

1. captures the exact natural PDF through Depósito;
2. runs the already-certified production Poppler page-4 processor;
3. creates one controlled machine `source_assertion` anchored to the unique exact phrase
   `Comité Cantonal de la Persona Joven de Esparza` in the extracted Representation;
4. proves the Claim begins machine-only and not strict-ready;
5. reopens the exact evidence from retained bytes;
6. prepares a deterministic one-subject batch;
7. records one real human-style batch acceptance action;
8. proves the same exact revision becomes human-reviewed and strict-ready;
9. proves exactly one ReviewAction + one ClaimReview were persisted.

The controlled Claim exists only to exercise REVIEW-001 against natural evidence; it is not new
semantic gold and makes no extraction-quality claim.

## Explicit no-goals

This unit does not implement:

- Claim correction/supersession or privacy restriction mutation;
- relation/entity/document review writers;
- a universal review policy engine;
- saved review queues;
- UI/CLI presentation;
- multi-user roles/permissions;
- synthetic review decisions;
- schema changes.

The next review unit should add human ClaimRevision correction/restriction with explicit lineage and
safe metadata/evidence carry rules, using REVIEW-001 as the decision/read foundation.
