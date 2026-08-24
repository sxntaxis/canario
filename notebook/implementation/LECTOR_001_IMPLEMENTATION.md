# LECTOR-001 — implementation record

**Start HEAD:** `22790895a0e3a106127385d681975db73230990d`  
**Parent state:** `PROCESSOR_CODEX_001_CODEX_CLI_SUBSCRIPTION_IMPLEMENTED_AND_CERTIFIED`  
**Candidate state:** `LECTOR_001_IMPLEMENTED__CERTIFICATION_PENDING`

## Production code

LECTOR-001 adds the backend-neutral semantic extraction boundary:

```text
actakit/lector/contracts.py
actakit/lector/registry.py
actakit/lector/locators.py
actakit/lector/writer.py
actakit/lector/host.py
```

`SemanticExtractor` implementations receive immutable Representation bytes and
exact scoped targets only. `LectorHost` performs curated backend selection;
`LectorWriter` remains the sole canonical persistence authority.

The writer atomically records terminal ProcessRun provenance, ordered exact inputs,
optional non-secret egress provenance, newly allocated Claim identities/revision 1,
EvidenceLinks, EntityMentions, resolution candidates, existing-Tag assignments,
candidate/direct existing-Entity anchors, same-run ClaimRelations and exact relation
basis.

## Canonical replay

A stable `process_run_id` is the replay identity. Reusing it with identical
capability/configuration/ordered inputs/egress policy returns the already committed
semantic receipt without invoking the backend again. Changing immutable identity
produces `LectorIdentityCollision`.

New ProcessRun IDs deliberately create new civic Claim identities even when claim
text is identical. Text is not a global identity or dedupe key.

Receipts preserve `(claim_id, revision_id)` and `(relation_id, revision_id)` pairs
rather than independent sorted ID arrays.

## Evidence integrity

`TargetRef` proposals are validated using the existing `TargetRegistry`, bounded by
the exact input scope and reopened against retained bytes before use. Current
runtime-reopenable proposals are `text_quote:v1` and `table_range:v1`.

Selector registration occurs inside the semantic transaction. A false locator,
unknown Tag/Entity, authority violation or downstream SQL failure rolls back the
ProcessRun, proposed targets and semantic rows together.

Canonical duplicate detection runs after selector normalization/reuse, preventing
semantically identical selector JSON with different whitespace/key formatting from
creating duplicate evidence or relation basis rows.

## Authority controls

The writer enforces a narrower authority surface than raw SQL:

- machine/rule extraction cannot resolve `attribution_entity_id`;
- machine/rule direct Entity anchors are candidate only;
- Entity mentions remain raw occurrences; resolution candidates do not create
  `MentionResolutionRevision`;
- machine ClaimRelations are candidate only;
- active rule relations require source-evidence or mechanical-identity basis;
- source-evidence relations require exact source basis;
- claim_extract relations are same-run only;
- Claim lifecycle derives from input custody, not backend output;
- failed ProcessRuns cannot persist semantic outputs;
- review tables are never written by LECTOR-001.

## Resource bounds

Both registry and writer enforce descriptor bounds. Writer-side aggregate result
bounds cover claims, evidence links, mentions, resolution candidates, Tag links,
Entity anchors, ClaimRelations and relation basis targets in addition to input
bytes/scopes.

## Egress

An egress extractor requires explicit authorization and cannot process restricted
custody. It must report actual source/evidence attachment bytes handed to the
external executor; zero is valid before external handoff. Local extractors cannot
report egress. Policy/profile/template/endpoint identity is replay-stable.

No credentials are representable in the semantic request/result contracts.

## SQLite

No schema rebaseline was required. Candidate and migration-spec SQL remain exact:

```text
5226c873487d9bd05fc62b7a1f323d6e804b003cc4e08bd2fe2b531adb6057bb
```

No `0002` exists.

Portable schema proofs on the development runtime report:

```text
MIGRATION_0001_SPEC_PROOF=PASS
MIGRATION_FREEZE_PROOF=PASS
STORAGE_OPERATION_PROOF=PASS
58 STRICT / 3 FTS5 / 118 indexes / 127 FK child plans / 0 scans
```

The exact registered SQLite 3.53.4 runtime remains an independent certification
gate rather than being claimed by the cloud development container.

## Focused implementation proof

Focused tests cover, among other cases:

- rich Claim/Evidence/Mention/Tag/EntityAnchor/Relation transaction;
- replay without reinvocation and replay without the historical adapter installed;
- identity collision on changed exact scope;
- false-locator atomic rollback;
- narrow-scope anti-expansion and exact-target reuse;
- unresolved mention + candidate resolution without canonical resolution;
- unknown Entity/Tag fail-closed;
- attribution and Entity-anchor authority boundaries;
- machine/rule ClaimRelation promotion rules and symmetric canonicalization;
- restricted custody + cloud ineligibility;
- positive and zero egress provenance + immutable replay policy;
- exact ordered ProcessRun inputs;
- writer-side result bounds;
- partial semantic result persistence;
- identical claim text under new ProcessRun remains distinct;
- canonical duplicate detection after selector normalization;
- exact structured table-row reopening;
- concurrent exactly-once canonical commit boundary;
- 300-Claim machine-only volume + replay with zero fabricated reviews.

No real LLM claim extractor is part of LECTOR-001. The first real broad civic
extractor is intentionally a separate benchmark/product unit after this persistence
and authority boundary is certified.
