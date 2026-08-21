---
id: ACTAKIT-SQLITE-MIGRATION-0001-AUTH-001
kind: migration-authorization
state: migration-0001-implemented-and-certified
created: 2026-08-21
authority: implementation-gate
migration_authorized: true
canonical_cutover_authorized: false
production_writers_authorized: false
---

# Migration 0001 Authorization Review

## Decision

```text
MIGRATION_0001_AUTHORIZATION:
PASS_BOUNDED_IMPLEMENTATION_AUTHORIZED
```

ActaKit may now implement production migration/bootstrap `0001` **only** for the
frozen fresh-database SQLite contract described below. This is not authorization
to move existing civic data into SQLite or to make SQLite the active canonical
writer for the current pipeline.

## Authoritative evidence

Authorization is based on the reconciled certified lineage:

```text
freeze-certified HEAD:
cf70e673a445570812c736ede36797bbb0e896ae

MIGRATION_0001_SPEC.sql SHA256:
31cac5ccc3440ce555242ba288317df527bb30949b2142026d8ceb2805d3adfc

SQLite runtime:
3.53.4

SQLITE_SOURCE_ID:
2026-07-24 19:02:57 bf7c7f30031888f4e796e429ab3978879485813aaca6f641c7b33e4e09459bcc
```

The post-freeze campaign passed:

- runtime contract and exact source-ID registry check;
- 54 ordinary `STRICT` tables and 3 FTS5 virtual tables;
- 16/16 semantic fixtures;
- atomic bootstrap and injected-failure rollback;
- wrong-file rejection and read-only-open behavior;
- closed vocabularies and SQL/core invariant boundary;
- 114 explicit indexes with no exact/simple-prefix redundancy;
- 118/118 FK child lookup paths without table scan in the proof workload;
- exact PDF/text/table selector reopening;
- shared-byte custody/purge behavior;
- backup -> clean-machine restore -> FTS rebuild;
- archive/FTS/WAL/VACUUM purge maintenance;
- final target-runtime contract repeat.

There is no earlier canonical ActaKit SQLite schema or canonical dataset to
upgrade. `0001` is therefore a fresh-install migration, not a legacy data
conversion.

## Governance prerequisite closed

`ROADMAP.md` requires the semantic architecture to be accepted before a persistent
canonical migration begins. `ARCHITECTURE.md`, `CONTRACTS.md`, and
`DATA_MODEL.md` had stale `proposed-for-acceptance` metadata even though the
entire pre-SQL/freeze campaign already treated those meanings as accepted
contract authority. This authorization checkpoint reconciles those three states
to `accepted`.

Planning artifacts (`ROADMAP.md`, `IMPLEMENTATION_PLAN.md`, `RELEASE_1_0.md`) do
not themselves become implementation authority and remain plans.

## What is authorized

The next implementation unit may add only the persistence bootstrap necessary to
materialize and open schema version 1:

1. a production migration artifact for `0001` whose SQL is byte-identical to the
   frozen `MIGRATION_0001_SPEC.sql` and therefore retains its SHA256;
2. a migration/bootstrap runner that:
   - accepts only a truly fresh SQLite target (`application_id=0`,
     `user_version=0`, no user schema);
   - establishes the writable connection contract before migration;
   - executes the exact specification in one `BEGIN IMMEDIATE` transaction;
   - writes `application_id=0x414B4954` and `user_version=1` as the final schema
     writes already present in the frozen SQL;
   - rolls back cleanly on any failure;
   - reopens and verifies markers, integrity, FK integrity and expected inventory;
3. writable and read-only authority openers implementing the frozen connection
   contract;
4. a fail-closed SQLite runtime registry/capability guard. Initially, the only
   certified runtime is the exact upstream SQLite 3.53.4 source ID above. A newer
   SQLite version is not implicitly accepted merely because its version number is
   greater;
5. narrowly scoped tests/proofs for fresh install, interrupted install, reopen,
   wrong-file rejection, read-only behavior and frozen-spec identity.

A migration runner seeing the already-valid ActaKit schema version 1 may verify
and open it; it must not replay `0001`, use `INSERT OR REPLACE`, or “repair” an
unknown/partial foreign database into looking valid.

## Frozen-spec rule

Authorization attaches to the exact SQL bytes, not merely the current table
count or an approximate schema.

```text
sha256(MIGRATION_0001_SPEC.sql)
=
31cac5ccc3440ce555242ba288317df527bb30949b2142026d8ceb2805d3adfc
```

The production migration must either consume that exact artifact or contain an
exact byte copy whose hash is asserted in tests. Maintaining two independently
editable SQL sources is not authorized.

Any change to table definitions, indexes, CHECKs, FKs, FTS definitions,
`application_id`, `user_version`, or other SQL bytes **voids this authorization**.
Such a change must return through:

```text
critical issue evidence (if applicable)
-> migration freeze review
-> exact target-runtime recertification
-> authorization review
```

## Explicitly not authorized

This checkpoint does **not** authorize:

- importing or migrating existing Markdown/Hilo/operator data into SQLite;
- switching current scripts to canonical SQLite writes;
- repository implementations for Source/Artifact/Document/Claim/Entity/etc.;
- archive-object file writes or moving existing evidence into the archive;
- acquisition/extraction/AI ingestion into the new schema;
- review/purge application services;
- destructive cleanup of current files;
- a daemon, RPC service, public API or federation;
- schema `0002`;
- loosening the registered SQLite runtime contract;
- changing the frozen SQL during implementation for convenience.

Those require their own implementation/gate evidence.

## Implementation acceptance gate

Authorization is consumed only when the implementation demonstrates, on the
exact certified SQLite 3.53.4 runtime:

```text
frozen spec hash unchanged
fresh bootstrap PASS
injected-failure rollback PASS
wrong/foreign DB rejection PASS
version-1 reopen PASS
read-only opener PASS
schema inventory 54 STRICT + 3 FTS5 PASS
foreign_key_check PASS
integrity_check PASS
runtime contract PASS
repo tests PASS
```

The implementation checkpoint must also prove that no existing file/Markdown
pipeline behavior or civic data was modified merely by adding persistence
bootstrap support.

## Verdict

No unresolved semantic, physical-schema, runtime, restore, purge, or governance
blocker remains for implementing the bounded `0001` bootstrap.

The bounded implementation at
`ac098b5ab56afe802f4f7271d790fa1c0696d6cf` has now passed this acceptance gate.
The result is recorded in
`MIGRATION_0001_IMPLEMENTATION_CERTIFICATION.md`. The authorization is consumed
only for the fresh-database bootstrap/runtime boundary; it does not authorize
canonical cutover or production semantic writers.

```text
migration_authorized: true
canonical_cutover_authorized: false
production_writers_authorized: false
```

The next authorized work is **implementation of migration/bootstrap `0001` only**.
