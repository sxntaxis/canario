# LECTOR-001 — Semantic extraction boundary (development checkpoint)

State: **IN PROGRESS — NOT IMPLEMENTED/CERTIFIED**

Base authority:

```text
main = 22790895a0e3a106127385d681975db73230990d
PROCESSOR-CODEX-001 = certified and integrated
```

This checkpoint freezes the semantic boundary decisions recovered after the
initial LECTOR-001 development workspace was lost. It intentionally preserves the
contracts/selector-reopening work before completing the canonical writer/host.

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

A SemanticExtractor is replaceable/untrusted. It must not receive SQLite, archive
write authority, review authority, publication authority, entity-reconciliation
authority, credentials, or arbitrary tools merely because it extracts semantics.

The core allocates canonical opaque IDs and owns persistence.

## Initial claim_extract outputs

LECTOR-001 may persist, once the writer is completed:

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

The last restriction is provenance-driven, not a feature omission: a future
`claim_relate` process comparing historical ClaimRevisions must durably declare
those semantic inputs instead of pretending a Representation-only ProcessRun read
them.

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
claims inside one backend result before canonical IDs exist. Mention/relation local
keys were deliberately removed because they had no consumer and would become
speculative pseudo-identity.

Receipts must preserve pairs such as:

```text
PersistedClaim(claim_id, revision_id)
PersistedClaimRelation(relation_id, revision_id)
```

Do not return separately sorted parallel ID arrays.

## Evidence and exact locator reopening

An extractor never writes arbitrary locator JSON directly to EvidenceLink. It
returns `TargetRef`:

```text
existing RepresentationTarget ID
OR
proposed selector kind/version/payload
```

For a proposal, core must:

1. validate the typed/versioned selector with `TargetRegistry`;
2. prove it belongs inside the declared ProcessRun input scope;
3. reopen it deterministically against the exact retained Representation bytes;
4. reuse an identical canonical target or allocate an opaque `rtgt_`;
5. only then write semantic links.

LECTOR-001 can currently create/reopen:

- `text_quote:v1` — exact offsets or uniquely resolved exact+context;
- `table_range:v1` — exact rows/observed values reopened from structured JSON.

It does not introduce a second PDF/image/media renderer. Exact pre-existing targets
of those kinds may be reused when already created by the appropriate subsystem.

Every automatically extracted Claim requires evidence. A `source_assertion`
requires at least one **active** `supports` or `quotes` link.

## Authority rules stronger than SQL

The SQL schema is intentionally broader than one writer. LECTOR-001 narrows it:

- Claim lifecycle is core-owned:
  - available input -> `active`;
  - restricted input -> `restricted`;
- a new extractor link may be `candidate|active`, never born `rejected`;
- machine/rule output cannot set `attribution_entity_id`; preserve
  `attribution_text` + raw EntityMention instead;
- machine/rule direct Entity anchors remain candidate;
- machine ClaimRelations remain candidate;
- rule ClaimRelations may be active only with `source_evidence` or
  `mechanical_identity` basis;
- `source_evidence` requires at least one exact `source_basis` target;
- `context` alone is not proof;
- symmetric `contradicts` / `same_matter_as` relations are stored once with
  canonical endpoint ordering.

Entity resolution is deliberately separate from extraction. Same-name matching is
not identity.

## Concurrency boundary

Stable ProcessRun identity can guarantee **exactly-once canonical commit**, not
necessarily exactly-once external invocation. Two concurrent callers may both
invoke an expensive backend before one wins the commit/replay race. A future
multi-worker/cloud-semantic deployment may justify a pre-handoff lease/reservation;
LECTOR-001 must not claim that guarantee prematurely.

## SQLite result so far

No schema change has been justified. The first semantic writer is designed to fit
the already-certified pre-release baseline:

```text
0001.sql SHA256
5226c873487d9bd05fc62b7a1f323d6e804b003cc4e08bd2fe2b531adb6057bb
```

No `0002` is authorized.

Existing semantic tables already provide the required physical families and
`process_run_id` indexes for efficient replay reconstruction.

## Work already proven before checkpoint recovery

The earlier development workspace reached a 25-test focused Lector suite and a
full regression of 147 tests + 2 subtests before its final cleanup pass. That
runtime workspace was subsequently lost, so those numbers are **historical
working evidence, not certification evidence for this reconstructed checkpoint**.

The tested behaviors included rich transactional semantic output, replay and
identity collision, rollback on false locator, narrow-scope enforcement,
unresolved mentions, no name-equality identity creation, candidate entity
resolution, Tag/Entity existence checks, attribution/anchor authority limits,
relation promotion rules, symmetric relation canonicalization, restriction/egress
policy, concurrency canonical replay, identical-text/new-run separation, and exact
table-range reopening.

## Checkpoint scope

This recovered checkpoint intentionally contains:

- backend-neutral contracts;
- explicit curated extractor registry;
- deterministic locator reopening;
- focused tests for those reconstructed pieces;
- this design authority.

Still to reconstruct/finish before `LECTOR-001_IMPLEMENTED`:

1. `LectorWriter` atomic canonical persistence + replay receipts;
2. `LectorHost` selection/orchestration and result bounds;
3. transaction-level SQLite tests covering the previously proven cases;
4. duplicate-output validation inside one SemanticResult;
5. full current regression after reconstruction;
6. exact SQLite migration/freeze/storage proofs;
7. implementation record + independent certification request/bundle.

No real LLM claim extractor belongs in this unit. After this boundary is certified,
the next unit can exercise it with a real Esparza acta and inspect broad claims and
citations rather than changing canonical semantics during model integration.
