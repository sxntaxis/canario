---
id: ACTAKIT-PRE-SQL-FIXTURE-REVALIDATION-001
type: research-fixture-revalidation
state: pass
authority: evidence
created: 2026-08-20
fixture_checkpoint: b0dc51dd6f50a98cdbec52d28b092a55c2ecd098
architecture_patch: same-commit
---

# Pre-SQL semantic fixture revalidation

## Verdict

**PRE_SQL_STRUCTURAL_GATE: PASS**

The bounded architecture patch resolves the four structural questions exposed by
`AKF-001..016` without adding a graph database, universal event log, daemon,
generic association ontology, or absolute-immutability promise.

This pass is **semantic**, not operational. Real civic artifacts are still needed
to prove parser/locator behavior, and backup/restore cannot be operationally
certified until storage exists.

## Fixture results

| Fixture | Result after patch | Why |
|---|---|---|
| AKF-001 exact PDF evidence | PASS | EvidenceLink remains representation-specific. |
| AKF-002 acquisition history | PASS | Source/observation/artifact remain separate; absence is not deletion. |
| AKF-003 unknown/malformed | PASS | Generic custody degrades gracefully; specialized interpretation must not guess. |
| AKF-004 one artifact/many documents | PASS | Artifact identity remains independent from CivicDocument identity. |
| AKF-005 spreadsheet locator | PASS | Locator contract stays typed by representation. |
| AKF-006 supervised/batch review | PASS | Machine-only records remain valid; batch action need not create a ReviewBatch subsystem. |
| AKF-007 raw entity mention | PASS — resolved | `EntityMention` is now core and preserves observed text before resolution. |
| AKF-008 same-name people | PASS | Raw mentions may remain unresolved; name equality is not identity. |
| AKF-009 rename/merge/split | PASS — resolved | Minimal append-only `EntityReconciliation` lineage is defined; old links are not rewritten. |
| AKF-010 relation vs claim correction | PASS | ClaimRelation remains revision-bound and historically stable. |
| AKF-011 shared anchor/traversal | PASS | Shared anchors do not create pairwise edges; traversal remains bounded/query-time. |
| AKF-012 evidence challenge vs contradiction | PASS | EvidenceLink and ClaimRelation retain separate semantics. |
| AKF-013 rich relationship | PASS — boundary resolved | ClaimRelation is deliberately narrow; attributed relationships promote to typed Association/Event when a real fixture requires it. Concrete tables are deferred. |
| AKF-014 Hilo/non-Episode output | PASS | Episode/Hilo remain outside core. |
| AKF-015 backup/restore corpus | PASS conceptually | Canonical backup boundary is DB + evidence archive + integrity relations; operational restore proof is post-schema. |
| AKF-016 redaction/purge | PASS — policy boundary resolved | Custody is immutable-by-default, `restricted != purged`, purge is explicit, and tombstones retain only lawful non-sensitive audit facts. |

## Resolved decisions

### EntityMention

Core semantic record. Minimum invariant: exact observed source text and exact
representation occurrence survive independently of any candidate/resolved
Entity. Resolution can remain absent and cannot overwrite the mention.

### Entity merge/split lineage

Use a narrow append-only identity reconciliation record with input/output entity
IDs, attribution, time, and basis/rationale. Merges may inform current retrieval;
splits do not trigger silent historical mass retargeting. This is not a generic
identity graph.

### Rich relationship promotion

```text
shared subject only                         -> Entity/Tag anchor
simple proposition-to-proposition meaning  -> ClaimRelation
relationship with own role/time/amount/etc -> typed Association/Event
```

The promotion boundary is architectural. A universal Association/Event schema is
not required in migration `0001` without a proving 1.0 use case.

### Purge/tombstone

Normal operations never mutate acquired bytes. Redaction creates derivatives.
Exceptional lawful/safety purge removes scoped bytes and derived copies/indexes.
A tombstone is optional and minimal: it may preserve only non-sensitive audit
facts that policy/law allow. It must not retain prohibited material indirectly.

## Remaining proof, not structural design

The structural pre-SQL gate is closed. Remaining evidence work belongs to later
implementation proof:

1. artifact-backed parser/locator fixtures listed in `proof-requirements.csv`;
2. real SQLite query/index/constraint tests once a schema candidate exists;
3. operational backup/restore and purge propagation tests once storage exists;
4. a real attributed relationship fixture before concrete Association/Event
   tables are introduced.

## Next authorized design step

A SQLite schema **candidate** may now be designed against these contracts and
`AKF-001..016`. Schema design must remain reviewable separately from production
implementation/migration authorization.
