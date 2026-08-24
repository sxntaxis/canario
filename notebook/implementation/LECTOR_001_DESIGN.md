# LECTOR-001 — Semantic extraction boundary

State: **IMPLEMENTED — CERTIFICATION PENDING**

Base authority:

```text
main = 22790895a0e3a106127385d681975db73230990d
PROCESSOR-CODEX-001 = certified and integrated
```

## ELI5

Mesa de trabajo answers **“can ActaKit read this source faithfully?”**. Lector
answers **“what does the readable source say?”**. Fichero stores those propositions
with exact evidence and provenance. Mesa de control later answers **“what has a
human reviewed/corrected?”**.

```text
PDF / source bytes
    -> faithful Representation
    -> Lector backend (rules/model/human)
    -> semantic drafts
    -> core validation/writer
    -> machine/rule/human-origin Fichero rows
    -> later human review
```

Canonical does **not** mean human-approved. It means durable, attributable,
evidence-backed and invariant-preserving.

## Ownership boundary

A `SemanticExtractor` is replaceable/untrusted. It receives immutable bytes plus
exact `RepresentationTarget` scopes. It does not receive SQLite, archive write
authority, review authority, publication authority, entity-reconciliation
authority, credentials, or ambient tools merely because it extracts semantics.

The core allocates canonical opaque IDs and owns persistence through
`LectorWriter`; `LectorHost` owns selection/orchestration.

## Initial claim_extract outputs

LECTOR-001 may persist:

- new `Claim` + revision 1;
- exact `EvidenceLink`;
- raw `EntityMention`;
- `MentionResolutionCandidate` only against an already-existing Entity;
- `ClaimTagLink` only against an already-existing Tag;
- direct `ClaimEntityLink` only against an explicitly supplied existing Entity,
  with machine/rule output remaining candidate;
- `ClaimRelation` revision 1 only between claims created by the same result/run;
- exact relation source/context basis targets;
- terminal `ProcessRun`, ordered exact `process_run_inputs`, and non-secret egress
  provenance when the selected extractor requires egress.

It does **not** own:

- Entity creation by name, merge/split or reconciliation;
- `MentionResolutionRevision`;
- human reviews/actions;
- arbitrary Tag vocabulary creation;
- revision/retraction/correction of existing claims;
- CivicDocument identity;
- Hilo/output writes;
- cross-run/cross-document ClaimRelation comparison.

The last restriction is provenance-driven: a future `claim_relate` process
comparing historical ClaimRevisions must durably declare those semantic inputs
instead of pretending a Representation-only ProcessRun read them.

## Replay and identity

Never deduplicate civic propositions by text.

```text
same process_run_id + same exact ordered inputs/config/egress identity
    -> replay committed semantic receipt; do not reinvoke backend

same process_run_id + different immutable identity
    -> hard identity collision

new process_run_id
    -> new attributable semantic attempt, even if claim text is identical
```

Opaque civic IDs are core-owned. `ClaimDraft.local_key` exists only to connect
claims inside one backend result before canonical IDs exist. Receipts preserve
canonical identity pairs:

```text
PersistedClaim(claim_id, revision_id)
PersistedClaimRelation(relation_id, revision_id)
```

No separately sorted parallel ID arrays are used.

Concurrent callers can still both invoke an external extractor before one commit
wins. LECTOR-001 therefore guarantees **exactly-once canonical commit**, not
exactly-once external execution. A future multi-worker/cloud semantic service may
justify a pre-handoff lease/reservation.

## Evidence and exact locator reopening

An extractor never writes arbitrary locator JSON directly to `EvidenceLink`. It
returns a `TargetRef` pointing to either:

```text
existing RepresentationTarget ID
OR
proposed selector kind/version/payload
```

For a proposal, core must:

1. validate the selector using `TargetRegistry`;
2. prove it does not expand beyond the declared ProcessRun input scope;
3. reopen it deterministically against the exact retained Representation bytes;
4. reuse an identical canonical target or allocate a core-owned `rtgt_`;
5. only then write the semantic link.

LECTOR-001 can create/reopen:

- `text_quote:v1` — exact offsets or one uniquely resolvable exact+context match;
- `table_range:v1` — exact rows/observed values reopened from structured JSON.

It does not introduce a second PDF/image/media renderer. Pre-existing canonical
targets may be reused when already established by the appropriate subsystem.

Every extracted Claim requires evidence. A `source_assertion` requires at least
one **active** `supports` or `quotes` link.

Pure contracts reject obvious duplicates early; `LectorWriter` repeats duplicate
checking after target canonicalization so differently formatted JSON that resolves
to the same target cannot create duplicate evidence, mentions or relation basis.

## Authority rules stronger than SQL

The SQL schema is intentionally broader than one writer. LECTOR-001 narrows it:

- Claim lifecycle is core-owned:
  - available input -> `active`;
  - restricted input -> `restricted`;
- a new extractor link may be `candidate|active`, never born `rejected`;
- machine/rule output cannot set `attribution_entity_id`; preserve
  `attribution_text` + raw EntityMention instead;
- human attribution Entity IDs must already exist;
- machine/rule direct Entity anchors remain candidate;
- one Entity may carry distinct claim roles, but an identical `(entity, role)`
  anchor cannot repeat within one result;
- machine ClaimRelations remain candidate;
- rule ClaimRelations may be active only with `source_evidence` or
  `mechanical_identity` basis;
- `source_evidence` requires at least one exact `source_basis` target;
- `context` alone is not proof;
- symmetric `contradicts` / `same_matter_as` relations are stored once with
  canonical endpoint ordering;
- claim extraction relations can reference only claims created by the same
  ProcessRun.

Entity resolution remains separate from extraction. Same-name matching is never
canonical identity resolution.

## Bounded result contract

Every extractor descriptor declares bounded inputs and outputs. The registry uses
input bounds for eligibility, and the writer rechecks them before persistence.
LECTOR-001 bounds include:

```text
input bytes
input scopes
claims
evidence links
entity mentions
mention resolution candidates
tag assignments
entity anchors
claim relations
relation basis targets
```

This prevents a backend from bypassing registry selection and submitting an
unbounded semantic result directly to the writer.

## Process outcome and partial state

`ProcessRun.outcome` keeps technical completion separate from human review:

```text
success  -> complete extractor attempt
partial  -> exact evidence-backed semantic rows may persist with bounded error_code
failed   -> provenance may persist, but zero semantic output rows
```

A partial result is not synthetic approval. Human review remains absent until a
real review row exists.

## Egress and restricted custody

Cloud/agent semantic extraction uses the same non-secret `process_run_egress`
contract as Workbench:

- restricted input is ineligible for egress;
- explicit authorization is required;
- an egress extractor must report source bytes handed to the external executor;
- zero is valid for failure before external handoff;
- non-egress extractors cannot report egress bytes;
- replay requires the same durable egress policy identity.

No credential values enter requests, ProcessRuns or semantic rows.

## SQLite result

No schema change was justified. LECTOR-001 fits the already-certified prerelease
baseline:

```text
0001.sql SHA256
5226c873487d9bd05fc62b7a1f323d6e804b003cc4e08bd2fe2b531adb6057bb
```

No `0002` exists.

The existing semantic tables and `process_run_id` indexes support transactionally
writing and efficiently reconstructing replay receipts.

## Functional volume proof

The focused implementation suite includes a 300-Claim machine-only batch over one
ProcessRun. It proves:

- all 300 claims persist with exact evidence;
- no human review rows are fabricated;
- replay returns the same canonical claim/revision identities;
- the extractor is not reinvoked on stable replay;
- no text-based global deduplication collapses a new ProcessRun.

This is a boundary/volume proof, not a claim-quality benchmark. A real broad
Esparza extractor is a later unit after LECTOR-001 certification.
