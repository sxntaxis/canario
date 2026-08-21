---
id: ACTAKIT-DEPOSIT-WRITER-IMPL-001
kind: implementation-evidence
state: local-proof-pass-target-runtime-reconciliation-required
created: 2026-08-21
authority: implementation-evidence
deposit_writer_implemented: true
deposit_writer_target_runtime_certified: false
canonical_cutover_authorized: false
semantic_fichero_writers_authorized: false
---

# Depósito Writer Implementation Evidence

## Implemented boundary

The first canonical civic-data writer is implemented only for the Depósito
custody graph authorized in `DEPOSIT_WRITER_AUTHORIZATION.md`:

```text
Source
  -> SourceLocator
  -> Acquisition
  -> AcquisitionArtifact -> Artifact -> ArchiveObject
                                  -> original Representation
```

No existing scraper, extraction, Markdown, Hilo, Claim, Entity, review, purge or
output path calls this writer yet.

## Production modules

```text
actakit/deposit/
  ids.py
  models.py
  archive.py
  writer.py
```

The public `DepositWriter` uses `open_writable_v1` by default, so production
writes inherit the already-certified SQLite runtime/source-ID guard. Tests inject
the private no-runtime-check bootstrap opener only because this cloud environment
loads SQLite 3.46.1; target-runtime certification remains a separate gate.

## IDs and timestamps

Core-generated stable IDs use readable prefixes plus RFC 9562-compatible UUIDv7
bit layout. Current prefixes in this unit are:

```text
src_
sloc_
acq_
aob_
art_
rep_
```

Canonical timestamps are validated as UTC RFC3339 text with subsecond precision.
Operation objects are immutable dataclasses so a retry can reuse the exact IDs,
timestamps and payload.

## Archive implementation

`EvidenceArchive` uses deterministic SHA-256 keys:

```text
objects/<sha256[0:2]>/<sha256>.bin
```

New bytes are:

1. hashed from the supplied immutable bytes;
2. written to a same-directory temporary file created with `O_EXCL` and
   `O_NOFOLLOW` where available;
3. fsynced;
4. re-read and hash/size verified;
5. atomically hard-linked into the final digest path;
6. followed by directory fsync;
7. re-verified from the final path.

Existing final objects are never trusted by filename: they are opened without
following symlinks where supported, required to be regular files, and re-hashed
before reuse.

A captured source filename or URL never controls an archive filesystem path.

## Cross-filesystem/SQLite failure ordering

A capture verifies or materializes required bytes before its SQLite
`BEGIN IMMEDIATE`, then revalidates content identity under the write lock before
inserting canonical rows.

This ordering deliberately prefers a harmless filesystem orphan over the unsafe
inverse state of committed canonical rows whose evidence bytes never became
materialized.

On an ordinary caught transaction failure the writer removes only a file that:

- this operation newly created; and
- still has no available ArchiveObject row referencing that same storage key.

A pre-existing/shared object is never compensation-deleted. A crash orphan at a
deterministic content key is verified and adopted by a later identical capture.
Temporary crash debris/GC remains a later health-maintenance concern; it is not
canonical data.

## Retry/idempotency behavior

For an existing Acquisition ID, retry succeeds only when the complete stored
immutable observation and Artifact/original-Representation payload set matches.
The physical ArchiveObject ID is content-deduplicated and therefore may be an
older shared identity rather than the retry object's unused candidate AOB ID.

A changed observation, Artifact set, representation metadata, digest, byte size,
or archive availability under the same stable operation IDs fails closed.
`INSERT OR REPLACE` is not used.

## Physical deduplication behavior

Repeated identical payloads:

```text
new Acquisition
new logical Artifact
new original Representation
existing verified ArchiveObject
```

This works both across separate acquisitions and for duplicate payloads inside a
single acquisition observation.

Changed bytes at the same SourceLocator produce a new digest/ArchiveObject.

## Local proof results

Available cloud runtime:

```text
SQLite 3.46.1
```

Production runtime certification therefore remains pending; the following tests
use an injected schema-v1 connection factory solely to exercise domain/write
logic without weakening the production default runtime guard.

Current local results:

```text
python -m pytest -q
27 passed

Depósito-specific tests
16 passed

MIGRATION_0001_SPEC_PROOF
PASS — 54 STRICT tables, 3 FTS5, 16/16 fixtures

MIGRATION_FREEZE_PROOF
PASS — 114 explicit indexes, 118 FK paths / 0 scans

SELECTOR_ARTIFACT_PROOF
PASS

STORAGE_OPERATION_PROOF
PASS — backup/clean restore/FTS/purge/WAL/VACUUM

git diff --check
PASS
```

The Depósito tests cover:

- UUIDv7-compatible prefixed IDs;
- Source exact retry and ID collision;
- SourceLocator reuse and conflicting-kind rejection;
- successful full custody graph;
- explicit `pending` validation state (fixity does not auto-promote to verified);
- failed observation with no bytes;
- failed observation retaining a response body Artifact;
- equal bytes across captures -> distinct logical custody + shared AOB;
- retry of a capture that deduplicated onto an older ArchiveObject;
- changed bytes at the same locator -> different AOB;
- exact operation replay;
- changed payload under same operation IDs -> fail closed;
- corrupt existing archive bytes -> fail closed;
- transaction rollback + cleanup of newly created unreferenced bytes;
- rollback never deleting pre-existing shared bytes;
- crash-orphan final bytes verified/adopted by a later capture;
- multiple payloads in one Acquisition with intra-operation dedup;
- Source/SourceLocator cross-association rejection before archive write;
- content-address final-path symlink rejection.

## Unchanged boundaries

This implementation does not:

- change schema-v1 SQL;
- add dependencies;
- read/write current civic production data;
- integrate `scripts/scrape_actas.py`;
- create derived Representations or ProcessRuns;
- create RepresentationTargets or evidence links;
- create CivicDocuments or Claims;
- perform purge or orphan GC;
- change backup format;
- authorize canonical cutover.

## Lineage/revalidation requirement

This implementation delta descends from:

```text
ac098b5ab56afe802f4f7271d790fa1c0696d6cf
```

through the bounded Depósito authorization commit. The operator-reported exact
SQLite 3.53.4 bootstrap implementation certification is the sibling commit:

```text
d43d6b6435e20136951ee5a81a6d79da4c68e006
```

The final Depósito certification must apply this delta onto `d43d6b6`, preserve
`MIGRATION_0001_IMPLEMENTATION_CERTIFICATION.md`, and rerun the entire suite using
the exact registered SQLite 3.53.4 source ID.

Until that succeeds:

```text
deposit_writer_implemented: true
deposit_writer_target_runtime_certified: false
canonical_cutover_authorized: false
semantic_fichero_writers_authorized: false
```
