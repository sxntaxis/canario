---
id: ACTAKIT-PRE-SQL-FIXTURE-VERDICT-001
type: research-fixture-verdict
state: review
authority: evidence
created: 2026-08-20
architecture_baseline: 59bab9de30bbf2aa1eec96dddaee3cded31a9f3a
research_baseline: f790517ea7dd16796a1484289275ff4ddc93cc84
---

# Fixture verdict before SQLite

## Verdict

The consolidated architecture survives the first semantic fixture pass **without
requiring a graph database, daemon, universal event log, or output/plugin
registry**. The fixtures do expose four decisions that should be resolved before
migration `0001` is designed.

## Proven fit

The current boundaries are sufficient for:

```text
Source -> Acquisition -> Artifact -> Representation -> CivicDocument
Claim -> EvidenceLink
Claim -> Entity/Tag anchors
ClaimRevision -> ClaimRelation -> ClaimRevision
ReviewDecision over exact revisions/sets
Queries -> independent Outputs
```

The cases also validate the intended negative rules:

- URL is not artifact identity;
- absence is not deletion;
- parser success is not semantic correctness;
- unknown is valid;
- co-occurrence is not a claim relation;
- traversal inference is not canonical memory;
- claim correction does not rewrite old relation endpoints;
- Hilo/Episode is not universal core;
- backup is not SQLite alone.

## Four decisions exposed by fixtures

### 1. Raw mention before Entity — **must resolve before SQL**

`AKF-007` and `AKF-008` show that the existing `Entity` + observed labels wording
is not precise enough. ActaKit needs a provenance-preserving record for the
*occurrence in source material* before canonical identity resolution.

Working name: `EntityMention`.

Minimum semantics:

```text
exact observed text
where it occurred
which claim/representation context exposed it
optional candidate/resolved Entity
origin/process
review/reconciliation state when applicable
```

The final name/table shape is not decided here.

### 2. Entity merge/split lineage — **must choose a minimal mechanism**

`AKF-009` proves that aliases alone are insufficient. A later reconciliation can
merge identities or split one mistaken identity into several. Old claim anchors
must remain explainable.

Do not build an identity graph. Do choose a minimal append-only reconciliation
lineage before schema freeze.

### 3. Rich relationship promotion — **boundary required; full feature may defer**

`AKF-013` confirms the research transfer from ORG/FollowTheMoney: a relationship
with role/time/amount can carry civic meaning independent of either endpoint.
That does not mean every edge becomes an object.

Before SQL, document a migration-safe rule:

```text
simple proposition-to-proposition meaning -> ClaimRelation
shared retrieval subject -> Entity/Tag anchor
relationship with independent attributes/identity -> typed Association/Event
```

The first schema may defer concrete Association/Event tables if no 1.0 proof
requires them, provided ClaimRelation is not designed as a JSON junk drawer that
blocks later promotion.

### 4. Purge/tombstone policy — **policy decision before public/custody promises**

`AKF-016` exposes a tension between immutable evidence language and lawful or
safety-driven deletion. This does not block the conceptual Fichero or first SQL
model, but architecture/release documentation must not promise absolute
immutability until the policy is explicit.

## Pre-SQL question coverage

| Existing pre-SQL pressure | Fixture evidence | Result |
|---|---|---|
| PDF + exact locator | AKF-001 | fit |
| repeated acquisition / changed bytes / absence | AKF-002 | fit |
| unknown/malformed material | AKF-003 | fit |
| one artifact -> many documents | AKF-004 | fit; optional structure |
| non-PDF locator | AKF-005 | fit |
| supervised + batch review | AKF-006 | fit |
| entity aliases/identity | AKF-007..009 | **needs EntityMention + merge/split decision** |
| relation origin/basis/revision endpoints | AKF-010 | fit |
| no edge explosion + bounded traversal | AKF-011 | fit |
| evidence challenges vs claim contradicts | AKF-012 | fit |
| Hilo vs non-Episode output | AKF-014 | fit |
| backup/restore | AKF-015 | concept fits; operational proof post-schema |
| rich attributed relation | AKF-013 | **promotion boundary needed** |
| lawful purge/public derivative | AKF-016 | **policy open** |

## Artifact-backed proof requirement

Synthetic cases are insufficient to certify parser/locator correctness. Before
implementation is declared semantically proven, the required cases in
`proof-requirements.csv` must be backed by real public civic artifacts or a
controlled captured equivalent. The artifact source may be any supported
installation; no external workspace is an ActaKit dependency.

## Recommended next patch

Do **not** write SQLite yet.

Make one bounded design patch that:

1. promotes raw `EntityMention` semantics into Architecture/Contracts/Data Model;
2. specifies minimal merge/split reconciliation lineage;
3. states the simple-relation -> rich-association promotion boundary without
   implementing a universal association ontology;
4. clarifies immutable-by-default custody versus explicit purge/tombstone policy;
5. updates the pre-SQL gate to cite these fixtures.

Then review the architecture once more against `AKF-001..016`. If no semantic
fixture remains structurally open, schema design may begin.
