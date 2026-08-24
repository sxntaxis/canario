---
id: ACTAKIT-INGRESS-CERTIFICATION-001
kind: implementation-certification
state: ingress-001-implemented-and-certified
created: 2026-08-21
authority: evidence
input_head: aae886df2d0e1b16c987248576807a3d164b1c5b
canonical_cutover_authorized: false
historical_import_authorized: false
semantic_fichero_writers_authorized: false
---

# INGRESS-001 certification

## Result

**PASS_INGRESS_001_CERTIFICATION**

The terrain-neutral Connector SPI and host-owned `DepositInbox` are certified on
the exact registered SQLite 3.53.4 runtime. The certified bridge is:

```text
SourceConnector -> CaptureEnvelope -> InboxPort -> DepositWriter
```

Input HEAD: `aae886df2d0e1b16c987248576807a3d164b1c5b`
Parent: `909230ee72abe99fe7ed14effde11bf23aa848c6`
Certification timestamp: `2026-08-21T14:37:18-06:00`
Platform class: Linux x86_64

## Frozen runtime and SQL

```text
SQLite: 3.53.4
SQLITE_SOURCE_ID: 2026-07-24 19:02:57 bf7c7f30031888f4e796e429ab3978879485813aaca6f641c7b33e4e09459bcc
amalgamation SHA3-256: 628a44cfe82c66aed1ccbbe85a562d2e33ebe64b3288981ed76285612227934e
sqlite3.c SHA3-256: 67f423e9ebbbdc473cbc4772c872ee6b89f31fde4ed0279a5c25d5f65c043a16
compile capabilities: ENABLE_FTS5, THREADSAFE=1, WAL/FK/triggers available
```

Production/frozen `0001` remains byte-identical:

```text
SHA256: 31cac5ccc3440ce555242ba288317df527bb30949b2142026d8ceb2805d3adfc
```

## Environment and regression

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
pytest collection: PASS; 35 tests
repo pytest: PASS; 35 passed
ingress pytest: PASS; 8 passed
runtime contract: PASS
migration spec proof: PASS; 54 STRICT, 3 FTS5, 16/16 fixtures
migration freeze proof: PASS; 114 indexes, 118 FK paths / 0 scans
selectors: PASS
storage/backup/restore/purge: PASS
production ingress smoke: PASS
final runtime contract: PASS
git diff --check: PASS
```

## Architecture boundary audit

PASS. `models.py` and `spi.py` are terrain-neutral and expose no Esparza,
municipality, acta, HTML selector, browser, pagination, session, article, or
item schema. `SourceConnector` sees only `ConnectorContext` and `InboxPort`.

`DepositInbox` owns Source binding, adapter attribution, canonical IDs, initial
validation policy, and the bridge to `DepositWriter`. Connector DTO constructors
cannot accept canonical persistence IDs; descriptor key/version/capabilities are
host-bound and not envelope-supplied. Coverage, checkpoint, and emitted-count
claims are validated by `run_connector`, and connector exceptions propagate.

No plugin registry, entry-point framework, durable connector run/checkpoint schema,
Esparza connector, semantic writer, purge/GC path, or schema change was added.

## Explicit scope

```text
Real Esparza/source integration: NOT IMPLEMENTED
Canonical cutover: NOT AUTHORIZED
Historical import: NOT AUTHORIZED
Semantic Fichero writers: NOT AUTHORIZED
Schema changed: NO
System SQLite replaced: NO
```

The next edge is a separate Esparza Source Connector implementation in shadow
mode. That connector is not part of this certification.
