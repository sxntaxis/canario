---
id: ACTAKIT-ESPARZA-CONNECTOR-CERTIFICATION-001
kind: implementation-certification
state: ESPARZA_CONNECTOR_001_IMPLEMENTED_CERTIFIED__BOUNDED_SHADOW_DOGFOOD_PASS
created: 2026-08-21
authority: evidence
start_head: 111a790a19fee7b98ff0950514e1de7ed1345981
parent_ingress: 3357d7a46b7873864c45df5448f6812c66c33434
canonical_cutover_authorized: false
historical_import_authorized: false
semantic_writers_authorized: false
legacy_scraper_hilo_behavior_changed: false
---

# ESPARZA-CONNECTOR-001 certification

## Outcome

**PASS_ESPARZA_CONNECTOR_001_CERTIFICATION_AND_SHADOW_DOGFOOD**

Gate A exact-runtime certification passed before Gate B was started. The bounded
real-network shadow run then passed twice against the official Esparza CMS.

## Gate A: exact-runtime certification

Input bundle SHA256:

```text
e52bdd392ea5ae35151735a426c5c5a9277f5dc38059b269d4ae9a6f9aa80a94
```

Input HEAD: `111a790a19fee7b98ff0950514e1de7ed1345981`
Parent: `3357d7a46b7873864c45df5448f6812c66c33434`

Frozen/production `0001` is unchanged:

```text
SHA256: 31cac5ccc3440ce555242ba288317df527bb30949b2142026d8ceb2805d3adfc
```

Python and dependency versions:

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
pip check: PASS
pytest collection: 51 tests collected
```

SQLite target:

```text
SQLite: 3.53.4
SQLITE_SOURCE_ID: 2026-07-24 19:02:57 bf7c7f30031888f4e796e429ab3978879485813aaca6f641c7b33e4e09459bcc
sqlite-amalgamation-3530400.zip SHA3-256: 628a44cfe82c66aed1ccbbe85a562d2e33ebe64b3288981ed76285612227934e
sqlite3.c SHA3-256: 67f423e9ebbbdc473cbc4772c872ee6b89f31fde4ed0279a5c25d5f65c043a16
compile capabilities: ENABLE_FTS5, THREADSAFE=1, WAL, foreign keys, triggers
```

Regression and proof results under the target library:

```text
runtime contract: PASS
repo pytest: PASS; 51 passed
Esparza-specific pytest: PASS; 16 passed
migration spec proof: PASS; 54 STRICT, 3 FTS5, 16/16 fixtures
migration freeze proof: PASS; 114 indexes, 118 FK paths, 0 scans
selectors: PASS
storage/backup/restore/purge: PASS
final runtime contract: PASS
git diff --check: PASS
```

Architecture boundary audit: PASS. `actakit/connectors/esparza.py` imports only
the ingress DTO/SPI plus private HTTP/HTML dependencies. It does not import or
call Depósito, persistence, SQLite, `DepositWriter`, semantic writers, or the
legacy scraper. It terminates at `ConnectorContext.inbox`. The host harness alone
binds `SourceRegistration`, `DepositInbox`, `DepositWriter`, and `ensure_schema_v1`.

No plugin registry, entry-point mechanism, durable checkpoint schema, or schema
change was added.

## Gate B: bounded real-network shadow dogfood

The disposable root was:

```text
/tmp/actakit-esparza-shadow-dogfood-20260821
```

The literal script-path invocation first exposed a host invocation issue
(`ModuleNotFoundError: No module named 'actakit'`) because the script directory,
not the checkout root, was placed on `sys.path`. No source or code was changed.
The same command was rerun with `PYTHONPATH=.` as an environment-only fix, using
the same cert venv and SQLite target library.

Command scope:

```text
section=concejo
year=2026
max_documents=3
rate_limit_seconds=1
coverage=unknown
```

Run 1 and run 2 both returned:

```text
ESPARZA_SHADOW_RUN=PASS coverage=unknown emitted=4
legacy_scraper_hilo_behavior=UNCHANGED
canonical_cutover=NOT_AUTHORIZED
```

Run 1 custody summary:

```text
Sources: 1
Source: kind=web, name=Municipalidad de Esparza -- CMS
Source ID: src_01a026b4-fb6a-7754-b161-a25dceb115f5
Acquisitions: 4
Artifacts: 4
ArchiveObjects: 4
Artifacts pending: 4
CivicDocuments: 0
Claims: 0
Entities: 0
semantic review/relation writes: 0
```

All four acquisitions used `adapter_key=cr.muniesparza.cms` and
`adapter_version=1`. One listing-page acquisition retained HTML response-body
bytes. Three document-resource acquisitions succeeded with retained PDF bytes.

| Locator | Outcome/status | Filename | Artifact | Content SHA-256 |
|---|---|---|---:|---|
| `https://muniesparza.go.cr/articulo/230/actas-concejo-municipal` | success/200 | none | response_body, pending | `5dc79c94bbf74587f04560eed0f7915590aa8a46d57de4c699eadfd42ac7c07f` |
| `https://muniesparza.go.cr/files/folder/e0256fdf-3714-40f5-ae10-aff18f0ca95e.pdf` | success/200 | `e0256fdf-3714-40f5-ae10-aff18f0ca95e.pdf` | primary, pending | `ffb354c67d8b56ebf265884c820a98fee27015cadaac3ea1011069f7969b8bfd` |
| `https://muniesparza.go.cr/files/folder/d120b950-9b1e-4c76-ab34-dd6c145fbcac.pdf` | success/200 | `d120b950-9b1e-4c76-ab34-dd6c145fbcac.pdf` | primary, pending | `687ac7713bc453b5087b9a03dee8f7b8860c7817e824892646e6570df6000802` |
| `https://muniesparza.go.cr/files/folder/b23455e7-f4f6-4071-b12b-246099d7b9af.pdf` | success/200 | `b23455e7-f4f6-4071-b12b-246099d7b9af.pdf` | primary, pending | `3971da3d99760d1b62389fd02bbd18be27628f668a78880af80f89bbe0b16e70` |

Run 2/source-binding summary:

```text
Source ID unchanged: PASS
logical Source rows: 1
source locators: 4, reused rather than duplicated
new acquisitions: 4; total observations: 8
new artifacts: 4; total artifacts: 8
ArchiveObjects: 5; identical physical bytes may deduplicate independently
all artifacts pending: PASS
```

The repeated poll preserved observation history and did not overwrite prior
Acquisition/Artifact provenance. No civic metadata was inferred from titles.

## Explicit scope and prohibitions

```text
Dogfood root was outside the repository and legacy paths: PASS
Legacy paths modified: NO
System SQLite replaced: NO
Schema changed: NO
Legacy scraper/Hilo behavior changed: NO
Canonical cutover authorized: NO
Historical import authorized: NO
Semantic writers authorized: NO
```

This certification covers only the bounded shadow adapter and custody evidence.
It does not authorize canonical data cutover, historical import, extraction/OCR,
semantic document/claim/entity writes, or plugin packaging.
