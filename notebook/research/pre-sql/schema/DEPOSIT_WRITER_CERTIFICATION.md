---
id: ACTAKIT-DEPOSIT-WRITER-CERTIFICATION-001
kind: deposit-writer-certification
state: deposit-writer-implemented-and-certified
created: 2026-08-21
authority: evidence
starting_lineage: d43d6b6435e20136951ee5a81a6d79da4c68e006
authorization_commit: 28ce757
implementation_commit: eb25de6
canonical_cutover_authorized: false
semantic_fichero_writers_authorized: false
historical_import_authorized: false
---

# Depósito writer certification

## Result

**PASS_DEPOSIT_WRITER_CERTIFICATION**

The bounded canonical Depósito custody writer is certified on the exact
registered SQLite 3.53.4 runtime. The certified boundary is:

```text
Source -> SourceLocator -> Acquisition
      -> AcquisitionArtifact -> Artifact -> ArchiveObject
                                      -> original Representation
```

Starting certification lineage: `d43d6b6435e20136951ee5a81a6d79da4c68e006`

Authorization commit: `28ce757` (`4975d6bed049d33123b04c9855db43ae9985e455`)

Reconciled implementation HEAD before certification documentation:
`eb25de6` (`dd6aff0998233487b7f4757cfb71db2f20f93a6b`)

Certification timestamp: `2026-08-21T14:37:18-06:00`
Host: Linux `7.1.5-1-cachyos` x86_64

## Frozen migration identity

Production and frozen SQL remain byte-identical:

```text
production: actakit/persistence/migrations/0001.sql
frozen:     notebook/research/pre-sql/schema/MIGRATION_0001_SPEC.sql
SHA256:     31cac5ccc3440ce555242ba288317df527bb30949b2142026d8ceb2805d3adfc
```

No schema `0002` or production migration change was made.

## Environment and runtime

```text
Python: 3.11.14
PyYAML: 6.0.1
requests: 2.31.0
beautifulsoup4: 4.12.3
python-docx: 1.1.0
pytest: 9.0.2
PyMuPDF: 1.28.2
pdfplumber: 0.11.9
pdfminer.six: 20251230
Pillow: 12.3.0

SQLite: 3.53.4
SQLITE_SOURCE_ID: 2026-07-24 19:02:57 bf7c7f30031888f4e796e429ab3978879485813aaca6f641c7b33e4e09459bcc
amalgamation SHA3-256: 628a44cfe82c66aed1ccbbe85a562d2e33ebe64b3288981ed76285612227934e
sqlite3.c SHA3-256: 67f423e9ebbbdc473cbc4772c872ee6b89f31fde4ed0279a5c25d5f65c043a16
compile capabilities: ENABLE_FTS5, THREADSAFE=1, WAL/FK/triggers available
```

`pip check` passed. Certification-only packages remained in the disposable
environment and were not added to project requirements. System SQLite was not
replaced or modified.

## Certification results

```text
pip check                                           PASS
pytest --collect-only                               PASS; 27 tests
prove_runtime_contract.py                           PASS; sqlite=3.53.4
pytest -q                                           PASS; 27 passed
  Depósito tests                                    PASS; 16 passed
prove_migration_0001_spec.py                        PASS; 54 STRICT; 3 FTS5; 16/16 fixtures
prove_migration_freeze.py                           PASS; 114 indexes; 118 FK paths / 0 scans
prove_selectors.py                                  PASS; real PDF/text/table artifact
prove_storage_operations.py                         PASS; backup/restore/FTS/purge/WAL/VACUUM
production Depósito smoke                            PASS
prove_runtime_contract.py (final)                   PASS; sqlite=3.53.4
git diff --check                                    PASS
```

The public smoke used `ensure_schema_v1`, `DepositWriter`, the default
`open_writable_v1`, and the real runtime guard. It proved exact operation retry,
shared bytes with distinct logical artifacts, changed-byte identity, failed
observations, integrity/FK checks, and archive file materialization.

The custody test suite also passed corrupt-archive rejection, transaction
rollback, cleanup/adoption of unreferenced or crash-orphan bytes, symlink
rejection, cross-Source locator rejection, response-body retention, and
multi-payload deduplication.

## Scope and prohibitions

No current civic production data or scraper behavior was modified. The writer
does not create Claims, CivicDocuments, Entities, Tags, relations, reviews,
derived Representations, ProcessRuns, purge/GC behavior, or Hilo output state.

```text
System SQLite replaced: NO
Existing civic data modified: NO
Current scraper/Hilo behavior changed: NO
Canonical cutover authorized: NO
Semantic Fichero writers authorized: NO
Historical import authorized: NO
```

This certification proves bounded Depósito custody ingress only. It does not
mark the entire persistence work package complete or authorize canonical
cutover.
