---
id: ACTAKIT-SQLITE-FIXTURE-REVALIDATION-002
type: research-fixture-revalidation
state: ddl-shape-proof-pass-artifact-proof-required
authority: evidence
created: 2026-08-21
candidate_baseline: 8b98010b32f88ce64b616ea51cccb48058ad35bb
---

# Fixture revalidation after SQLite candidate critical review

## Verdict

**SEMANTIC FIXTURES: 16/16 FIT AT REVISED DESIGN LEVEL**

The disposable scratch DDL now also proves that all 16 fixture shapes can be
represented under real SQLite FK/CHECK/STRICT semantics. This still does not
certify real parser/selector behavior, archive operations, or the packaged SQLite
runtime.

| Fixture | Revised design result |
|---|---|
| AKF-001 | exact typed RepresentationTarget -> EvidenceLink |
| AKF-002 | independent Acquisition/Artifact custody; equal bytes may share ArchiveObject |
| AKF-003 | unknown document/profile remains valid; specialized interpretation fails loudly; corrected common document metadata is revisioned |
| AKF-004 | one representation can occur in multiple CivicDocuments without byte duplication |
| AKF-005 | table-range selector retains structural coordinates and observed values |
| AKF-006 | per-record reviews remain canonical; ReviewAction is only grouping context |
| AKF-007 | raw EntityMention is core and survives resolution independently |
| AKF-008 | same-name mentions remain unresolved/candidates until justified |
| AKF-009 | append-only reconciliation + supersession preserves candidate/merge/split lineage without mutation |
| AKF-010 | ClaimRelation binds exact ClaimRevisions and can cite exact source basis |
| AKF-011 | entity/tag anchors avoid co-occurrence cliques; tag correction is append-only; bounded relation queries preserve parallel edges and type-specific directionality |
| AKF-012 | evidence `challenges` stays distinct from proposition `contradicts` |
| AKF-013 | concrete RoleAssignment owns role/time; real TSE office-holder source proves the relationship shape; selector reopening remains a separate artifact gate |
| AKF-014 | Outputs/Hilo/Episode remain outside canonical civic schema |
| AKF-015 | backup boundary includes consistent DB + retained archive bytes + manifest; FTS rebuilds |
| AKF-016 | redaction is derivative; purge freezes exact targets and reports SQLite/FTS/archive/backup scope honestly |

## Assertions strengthened by review

The ledger now includes explicit assertions that:

- equal captured bytes may share physical ArchiveObject storage without sharing
  logical Artifact identity;
- a source-backed ClaimRelation can cite exact evidence independently from its
  endpoint ClaimRevisions;
- RoleAssignment is concrete in the first schema;
- SQL DELETE/ordinary FTS removal is not a completed purge claim;
- purge freezes an exact target manifest and expands content-bearing derivatives;
- backup scope is part of purge reporting;
- shared physical bytes cannot be claimed erased while an in-scope retained
  Artifact still requires them;
- node reachability and edge/path enumeration are distinct in the ClaimRelation
  multigraph;
- a wrong machine Tag anchor is rejected/corrected append-only rather than deleted;
- machine/rule semantic outputs retain exact ProcessRun identity;
- an Acquisition locator, when present, must belong to the same Source.

## Next gate

The disposable DDL gate passed. Next proof must use real/controlled civic
artifacts for selector/parser behavior and then certify archive+DB restore, purge
maintenance, and the actual >=3.51.3 packaged runtime. A failure reopens design;
it is not patched around in a production migration.
