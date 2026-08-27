# REVIEW-002 — Human ClaimRevision control

State: **IMPLEMENTED CANDIDATE — EXACT SQLITE + NATURAL ESPARZA CONTROL PROOF PENDING**

Baseline authority:

```text
REVIEW-001 merge:             971b9bbfa4af7868b17de46b99d13a3c69dad219
previous frozen 0001 SHA256:  8d6f793e1c976221311bd73ffe03bdaa2907e9508e7c0f5fad59131a02dc9f96
candidate 0001 SHA256:        55b05a11f129cfbe1ffd199bcb6774ef8096f46424ebca6f43c169cb3eef7356
```

## Product purpose

REVIEW-001 records what a human decided about one exact ClaimRevision. REVIEW-002 adds a distinct
operation for changing the canonical Claim history itself without rewriting old civic records:

```text
current ClaimRevision + exact prepared snapshot
-> operator opens/inspects evidence through REVIEW-001
-> correct | restrict | unrestrict | retract
-> new human ClaimRevision
-> explicit old -> new supersession lineage
-> attributable ClaimRevisionAction
```

Review and mutation remain separate durable facts, but the product has one operator and no useful
meaning for “I corrected this from evidence but have not reviewed my correction.” Therefore `correct`
is one atomic operator action that creates both the new human ClaimRevision and a fresh `accepted`
ClaimReview targeting that exact result. The predecessor review is never inherited.

## Why the schema changes

The existing ClaimRevision schema could record `origin_kind='human'`, but that only says a human was
the semantic origin. It could not durably answer:

- who performed the canonical correction/restriction;
- what operation they performed;
- which exact source/result revisions the action connected;
- why it was done;
- whether a persistence retry is the exact same immutable request.

Using `ReviewAction` for this would falsely equate **reviewer** with **editor**. REVIEW-002 therefore
proves the need for one narrow durable family:

```text
ClaimRevisionAction
  id
  claim_id
  source_revision_id
  result_revision_id
  action = correct | restrict | unrestrict | retract
  actor
  rationale?
  review_action_id?  # required for correct; null for lifecycle-only actions
  request_sha256
  created_at
```

The table is not a generic OperationRun or universal audit log. It exists only for human canonical
ClaimRevision control actions whose meaning must survive as part of civic history.

Because Canario remains pre-release, this is a recertified `0001` rebaseline rather than `0002`.

## Core contracts

### Prepared snapshot

`ReviewReader.prepare_claim_control()` returns an exact `ClaimControlSnapshot` over the current
revision and the current non-superseded candidate/active EvidenceLinks, ClaimEntityLinks and
ClaimTagLinks. Its SHA-256 excludes only the derived `current` bit so an exact persistence replay can
still validate the immutable source snapshot after a successful supersession.

The writer reopens that snapshot inside one `BEGIN IMMEDIATE`. If the revision, evidence or selected
metadata changed after preview, the write fails before a new revision/action is committed.

### Correction

`correct` is a complete human-authored semantic replacement for a non-derived current ClaimRevision.
It may change:

- `claim_kind` among the explicitly human-correctable non-derived kinds;
- proposition text;
- attribution entity/text;
- temporal scope;
- sensitive/quantitative flags.

The operator explicitly selects which already-inspected current EvidenceLinks, ClaimEntityLinks and
ClaimTagLinks remain applicable. The selected IDs must be a subset of the prepared source snapshot.
The correction cannot fabricate new evidence or anchors in this operation.

A `source_assertion` correction must retain at least one active `supports` or `quotes` EvidenceLink.
A no-op semantic correction is rejected.

`derived_inference` cannot be human-corrected through this path. A changed derived proposition needs
a real new `DerivationResultTarget`; allowing a human button to manufacture that origin would falsify
analytical provenance.

### Lifecycle actions

`restrict`, `unrestrict`, and `retract` copy the current proposition/metadata/evidence into a new
human revision and change only the lifecycle state:

```text
active     --restrict-->   restricted
restricted --unrestrict--> active
active|restricted --retract--> retracted
```

All current source EvidenceLinks/ClaimEntityLinks/ClaimTagLinks are carried for lifecycle-only
mutations so the historical basis stays inspectable.

An `active` result is allowed only if every carried EvidenceLink still resolves to an available
RepresentationTarget, Representation and Artifact inside the same write transaction. `unrestrict`
therefore cannot declassify a Claim whose evidence remains restricted or purged.

## Correction implies a fresh review

REVIEW-002 never copies predecessor `ClaimReview` rows. Instead, because correction is performed by
the single operator after inspecting evidence, `correct` creates a **new** acceptance for the exact
result revision in the same `BEGIN IMMEDIATE`:

```text
revision 1 -- needs_work / accepted / unreviewed
      |
      +-- human correct from inspected evidence
              |
              +--> revision 2 (human)
              +--> ReviewAction -> ClaimReview(revision 2, accepted)
```

After supersession:

- revision 1 keeps its historical review state but is no longer current or strict-ready;
- revision 2 is immediately human-reviewed;
- if revision 2 is `active`, it is strict-ready without asking the operator to approve their own
  evidence-based correction a second time.

Lifecycle-only actions (`restrict | unrestrict | retract`) do **not** fabricate epistemic review.

## Search/privacy behavior

`claim_fts` is derived search state, not civic history. Whenever a Claim is corrected, restricted,
unrestricted or retracted, REVIEW-002 removes every FTS row for that Claim and then inserts only the
new revision if it is current and `active`.

This prevents older superseded text from leaking through search after restriction/retraction while
leaving the canonical ClaimRevision chain intact.

## Relation/evidence boundaries

REVIEW-002 deliberately does not retarget existing ClaimRelations. A relation whose endpoint was
revision 1 remains an exact historical relation to revision 1; whether revision 2 needs a replacement
relation is a separate semantic decision.

Likewise, correction may only retain/remove evidence already present in the prepared snapshot. Adding
new EvidenceLinks, repairing locator provenance, or changing relation graphs belongs to dedicated
bounded operations rather than being hidden inside proposition editing.

## Replay and identity

`ClaimRevisionControlRequest` preallocates stable IDs for both the action and result revision. The
canonical request SHA-256 binds:

- source revision + exact prepared snapshot SHA-256;
- actor;
- action;
- correction payload where applicable;
- rationale;
- action ID;
- result revision ID.

A retry with the same immutable payload replays exactly. Any occupied action/result identity with
different content fails closed.

## Purge integration

`claim_revision_action` is added to the closed `purge_targets.record_kind` vocabulary because actor
and rationale can themselves contain material covered by a purge policy. The operational storage
proof now creates and removes a Claim with real human correction lineage and verifies archive/FTS/WAL/
VACUUM behavior after purge.

## Candidate schema identity

Portable freeze/storage proofs currently pass with:

```text
MIGRATION_0001_SPEC.sql == canario/persistence/migrations/0001.sql
SHA256:                 55b05a11f129cfbe1ffd199bcb6774ef8096f46424ebca6f43c169cb3eef7356
ordinary STRICT tables: 72
FTS5 virtual tables:     3
application triggers:    0
explicit indexes:        137
FK child paths checked:  155
FK child table scans:    0
0002:                    absent
```

Exact SQLite 3.53.4 certification remains mandatory before merge.

## Natural proof

`notebook/implementation/prove_claim_revision_control.py` reuses the exact official Acta 161 PDF and
production Poppler extraction. It deliberately creates one controlled incorrect machine Claim:

```text
wrong:     La página menciona ... de Esparta.
evidence:  Comité Cantonal de la Persona Joven de Esparza
corrected: La página menciona ... de Esparza.
```

The proof must establish:

1. the old machine revision receives a real `needs_work` review;
2. the exact retained `text_quote:v1` evidence reopens;
3. `correct` creates revision 2 with `origin_kind='human'` plus one attributable action;
4. revision 1 remains in history and becomes non-current;
5. revision 2 does not inherit revision 1 review; the correction transaction creates its own fresh
   `accepted` ReviewAction/ClaimReview;
6. revision 2 is immediately human-reviewed and strict-ready while active;
7. the ClaimRevisionAction durably references that correction ReviewAction;
8. FTS contains only the current corrected active text;
9. action/request identity and persistence counts are exact.

The typo is controlled proof input, not an extraction benchmark or new semantic gold.

## Explicit no-goals

REVIEW-002 does not implement:

- GUI/CLI presentation;
- creation of entirely new evidence during correction;
- EvidenceLink correction/unlink workflows;
- automatic ClaimRelation endpoint retargeting;
- relation/entity/document mutation workflows;
- correction of `derived_inference` without a real Derivation;
- automatic approval of arbitrary human-authored revisions outside the explicit evidence-based `correct` action;
- public redaction/release of restricted source bytes;
- generic audit/event/operation tables;
- multi-user permissions or staffing roles.
