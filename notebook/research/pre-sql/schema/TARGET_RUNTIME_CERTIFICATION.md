---
id: ACTAKIT-SQLITE-TARGET-RUNTIME-CERTIFICATION-001
type: target-runtime-certification
state: pass
authority: evidence
created: 2026-08-21
runtime: sqlite-3.53.4
source_id: 2026-07-24 19:02:57 bf7c7f30031888f4e796e429ab3978879485813aaca6f641c7b33e4e09459bcc
migration_authorized: false
---

# SQLite 3.53.4 target-runtime certification

## Result

**PASS_TARGET_SQLITE_RUNTIME_CERTIFICATION**

The complete candidate proof suite passed under the disposable target library
built from the official SQLite 3.53.4 amalgamation. The corrected CR-031 restore
connection contract passed the clean-machine restore, FTS rebuild, purge, WAL,
and VACUUM checks.

Certification timestamp: `2026-08-21T12:08:23-06:00`
Platform class: Linux x86_64
Starting commit: `863edaaed76bd5f3a49f3a896bafd167a5efdc7a`

## Environment

The supported certification interpreter was Python `3.11.14`. The venv was
created outside the repository and was disposable. It installed the repository
requirements unchanged plus certification-only packages.

| Package | Version |
|---|---|
| PyYAML | 6.0.1 |
| requests | 2.31.0 |
| beautifulsoup4 | 4.12.3 |
| python-docx | 1.1.0 |
| pytest | 9.0.2 |
| PyMuPDF | 1.28.2 |
| pdfplumber | 0.11.9 |
| pdfminer.six | 20251230 |
| Pillow | 12.3.0 |

`pip check` passed, all required imports passed, and pytest collection found 3
tests. All `scripts/*.py` and certification proof scripts compiled successfully.

## SQLite build

Official artifact: `sqlite-amalgamation-3530400.zip`

```text
SHA3-256: 628a44cfe82c66aed1ccbbe85a562d2e33ebe64b3288981ed76285612227934e
sqlite3.c SHA3-256: 67f423e9ebbbdc473cbc4772c872ee6b89f31fde4ed0279a5c25d5f65c043a16
```

Compiler: GCC `16.1.1 20260728`

Build command:

```text
cc -O2 -fPIC -shared -Wl,-soname,libsqlite3.so.0 \
  -DSQLITE_ENABLE_FTS5 -DSQLITE_THREADSAFE=1 \
  -o libsqlite3.so.0 sqlite3.c -ldl -lpthread -lm
```

The library was loaded only through `LD_LIBRARY_PATH` from a temporary
directory. System SQLite was not replaced or modified.

```text
sqlite_version: 3.53.4
SQLITE_SOURCE_ID: 2026-07-24 19:02:57 bf7c7f30031888f4e796e429ab3978879485813aaca6f641c7b33e4e09459bcc
```

Relevant compile capabilities:

```text
ENABLE_FTS5
THREADSAFE=1
WAL available
foreign keys available
triggers available
```

The runtime contract also passed functional STRICT, FTS5, WAL, foreign-key,
`synchronous=FULL`, `trusted_schema=OFF`, and `secure_delete=ON` checks.

## Commands and results

All proof commands used the same clean checkout, Python 3.11.14 venv, and target
SQLite library through `env LD_LIBRARY_PATH="$TARGET_SQLITE_LIB"`.

```text
python -m pip check                                      PASS
python -m pytest --collect-only -q                        PASS (3 tests)
python -m py_compile scripts/*.py and proof scripts       PASS
prove_runtime_contract.py                                 PASS sqlite=3.53.4
python -m pytest -q                                       PASS (3 passed)
pre-freeze scratch proof (renamed to prove_migration_0001_spec.py)          PASS; 54 STRICT tables; 16/16 fixtures
prove_selectors.py                                        PASS; real PDF/text/table artifact
prove_storage_operations.py                               PASS
prove_runtime_contract.py                                 PASS sqlite=3.53.4
git diff --check                                          PASS
```

Selector proof output:

```text
source_pdf_sha256=192da0e99878aa310a906f381f3bb25c9678934743b1b7563df747e05a8eb4f3
pdf_page_ordinal=2
text_representation_sha256=c306c454037ecfdd43dfd606309786d3a54b5679c221e3e119146180148de53f
text_offsets=0:49
table_rows=6:6
```

Storage proof output:

```text
shared_archive_backup_manifest=PASS
clean_machine_restore_and_fts_rebuild=PASS
purge_manifest_archive_fts_wal_vacuum=PASS
pre_purge_wal_contained_sentinel=true
prepurge_backup_scope=OUT_OF_SCOPE_RETAINS_PREPURGE_MATERIAL
target_runtime_repeat=PASS
```

PyMuPDF and pdfplumber were installed only in a disposable certification
environment and were not added to ActaKit project/runtime dependencies.

Migration `0001` remains unauthorized.

## Post-freeze recertification

This section records the post-freeze rerun after reconciling the sibling freeze
delta onto the runtime-certified lineage.

```text
reconciled_parent: 6deafab40d40ea3f70e5e8c96433015ac5e54f6b
freeze_delta: afb72626743628c26a07fe5ea6058302e791b726
spec_sha256: 31cac5ccc3440ce555242ba288317df527bb30949b2142026d8ceb2805d3adfc
sqlite_version: 3.53.4
sqlite_source_id: 2026-07-24 19:02:57 bf7c7f30031888f4e796e429ab3978879485813aaca6f641c7b33e4e09459bcc
```

Post-freeze results:

```text
MIGRATION_0001_SPEC_PROOF=PASS sqlite=3.53.4 strict_tables=54 fts_tables=3
critical_invariants=16/16 PASS
semantic_fixture_storage=16/16 REPRESENTABLE
MIGRATION_FREEZE_PROOF=PASS sqlite=3.53.4
schema_inventory=PASS strict_tables=54 fts_tables=3 app_triggers=0
rowid_strategy=PASS ordinary_rowid_tables=54 without_rowid=0
index_inventory=PASS explicit=114 exact_duplicates=0 simple_prefix_redundancy=0
foreign_key_child_plans=PASS checked=118 scans=0
sql_json_dependency=ABSENT
SELECTOR_ARTIFACT_PROOF=PASS
STORAGE_OPERATION_PROOF=PASS sqlite=3.53.4
clean_machine_restore_and_fts_rebuild=PASS
purge_manifest_archive_fts_wal_vacuum=PASS
target_runtime_repeat=PASS
RUNTIME_CONTRACT=PASS sqlite=3.53.4
```

The freeze specification is certified for authorization review. This remains a
design/evidence result: system SQLite was not replaced, certification-only
dependencies were not added to ActaKit, and migration `0001` was not created or
authorized.
