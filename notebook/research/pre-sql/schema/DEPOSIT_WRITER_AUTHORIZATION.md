---
id: ACTAKIT-DEPOSIT-WRITER-AUTH-001
kind: writer-authorization
state: authorized-bounded-implementation
created: 2026-08-21
authority: implementation-gate
deposit_writer_authorized: true
canonical_cutover_authorized: false
semantic_fichero_writers_authorized: false
---

# Depósito Writer Authorization Review

## Decision

```text
DEPOSIT_WRITER_AUTHORIZATION:
PASS_BOUNDED_DEPOSITO_IMPLEMENTATION_AUTHORIZED
```

ActaKit may implement its first canonical civic-data writer, limited to the
**Depósito custody ingress**. This authorization rests on the frozen/certified
schema-v1 bootstrap and does not authorize the current scraper/Markdown/Hilo
pipeline to write the new store.

The bounded writer may materialize only this graph:

```text
Source
  -> SourceLocator
  -> Acquisition
  -> AcquisitionArtifact -> Artifact -> ArchiveObject
                                  -> original Representation
```

`SourceAuthorityScope` may remain empty in this unit; it becomes operationally
relevant when source assertions/claims are admitted. No document or semantic
Fichero writer is authorized here.

## Why this is the next coherent unit

A certified empty database is not yet evidence custody. The smallest complete
write vertical is one acquisition observation plus the exact bytes it produced.
It proves the schema's most important preservation distinction before any Lector
or Claim code depends on it:

```text
same bytes twice -> distinct Acquisition/Artifact custody identities
                  -> one shared ArchiveObject is permitted

same locator, changed bytes -> new Acquisition/Artifact
                            -> different ArchiveObject
```

This unit also proves that failures/absence are durable observations and never
delete prior evidence.

## Authorized API behavior

The implementation may provide explicit core operations for:

1. registering a stable `Source`;
2. registering/reusing a `SourceLocator` within that Source;
3. recording one `Acquisition` with zero or more captured byte payloads;
4. materializing each captured payload as one logical `Artifact` plus exactly one
   `original` Representation;
5. content-addressing, hashing, verifying and physically deduplicating bytes via
   `ArchiveObject`;
6. opening the schema-v1 writer only through the already-certified persistence
   runtime guard.

The writer accepts bytes and bounded adapter metadata. Network discovery/fetching
remains outside this core operation; later source adapters call the core after an
observation has occurred.

## Stable identity and retry contract

The implementation must follow the frozen MFR-016 contract:

- IDs and timestamps are allocated before the canonical write transaction;
- public/core-generated record IDs use readable prefixes plus UUIDv7-compatible
  opaque values;
- retrying the same operation reuses those IDs/timestamps;
- an existing ID is success only when its complete immutable payload is the same;
- a different payload under the same ID is a hard identity collision;
- canonical writes never use `INSERT OR REPLACE`.

Physical deduplication is the deliberate exception to “every preallocated ID is
materialized”: when an available ArchiveObject with the same verified SHA-256
already exists, the new Artifact references that existing physical identity and
the operation's unused candidate ArchiveObject ID is not inserted.

## Filesystem/SQLite atomicity boundary

SQLite and the evidence filesystem cannot participate in one atomic transaction.
The authorized ordering therefore minimizes the dangerous failure mode:

```text
compute digest
-> inspect any existing ArchiveObject + verify its bytes
-> atomically materialize missing content-addressed bytes
-> BEGIN IMMEDIATE
-> revalidate custody prerequisites
-> insert/reuse ArchiveObject metadata
-> insert Acquisition/Artifact/original Representation rows
-> validate cross-row custody invariants
-> COMMIT
```

This guarantees that a committed canonical row never intentionally points to
bytes that were planned but not durably materialized.

A process crash between byte materialization and DB commit may leave an
**unreferenced content-addressed file**. That is acceptable orphan state: it
contains no canonical civic assertion and a later identical capture can verify
and reuse it. A later health/GC operation may detect such files.

For an ordinary caught transaction failure, the implementation should remove
only files that this operation newly created and that remain unreferenced by an
available ArchiveObject row. It must never delete a pre-existing/shared object as
compensation.

## Archive contract

For this unit, the physical key is deterministic:

```text
objects/<first-two-sha256-hex>/<full-sha256>.bin
```

Required behavior:

- SHA-256 and byte length are computed from the actual supplied bytes;
- existing content at the expected key is always re-hashed before reuse;
- a missing/corrupt file behind an existing available ArchiveObject is an
  integrity failure, not something silently repaired;
- new files become visible atomically only after their complete contents are
  written and fsynced;
- symlink/non-regular-file targets are rejected;
- file paths are derived from digest, never source-controlled filenames/URLs;
- the archive root is supplied/configured by ActaKit and is not stored as an
  absolute deployment dependency in canonical records.

## Acquisition semantics

`outcome` retains the closed schema vocabulary. The core does not infer outcome
from HTTP status and does not forbid bytes on an unsuccessful outcome: for
example, a response body may itself be useful evidence of what was observed.

Every captured payload records explicitly:

- acquisition role;
- observed filename/URL when present;
- media type when known;
- Artifact validation state;
- retained availability (`available` or `restricted`);
- original Representation language/charset when known.

The writer must not manufacture `verified` merely because SHA-256 fixity passed;
content validation and physical fixity are different axes.

## Required acceptance evidence

The bounded implementation must prove at least:

```text
source exact retry PASS
source ID collision FAIL-CLOSED
locator reuse within Source PASS
successful acquisition with bytes PASS
failed/not-found acquisition without bytes PASS
same bytes twice -> distinct Artifact + shared ArchiveObject PASS
same locator changed bytes -> distinct ArchiveObject PASS
same operation exact retry -> no duplicate rows/files PASS
same operation ID + changed payload -> FAIL-CLOSED
existing archive byte corruption -> FAIL-CLOSED
transaction failure -> no canonical partial rows PASS
transaction failure -> newly-created unreferenced bytes cleaned PASS
one original Representation per retained Artifact PASS
current schema/freeze/storage proofs remain PASS
existing Markdown/Hilo behavior unchanged PASS
```

## Explicitly not authorized

This checkpoint does **not** authorize:

- changing `0001.sql` or the frozen spec;
- automatic ingestion from the existing scraper;
- importing historical files/operator data;
- source-authority-scope inference;
- derived Representations or ProcessRuns;
- RepresentationTargets/evidence locators;
- CivicDocuments/classification;
- Claims, entities, tags, relations or review;
- purge execution or GC;
- backup-format changes;
- canonical Hilo cutover;
- schema `0002`;
- daemon/RPC/public API work.

## Lineage note

This authorization is being developed as a delta from implementation HEAD
`ac098b5ab56afe802f4f7271d790fa1c0696d6cf`. The operator-reported exact-runtime
implementation certification is `d43d6b6435e20136951ee5a81a6d79da4c68e006`,
which adds certification/status evidence but does not alter the bounded bootstrap
code. Before final target-runtime certification of this writer, the delta must be
reconciled onto `d43d6b6` so that historical certification evidence remains in
the authoritative lineage.

## Verdict

```text
deposit_writer_authorized: true
canonical_cutover_authorized: false
semantic_fichero_writers_authorized: false
```
