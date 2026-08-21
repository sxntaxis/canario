---
id: ACTAKIT-INGRESS-IMPL-001
kind: implementation-evidence
state: ingress-001-implemented-and-certified
created: 2026-08-21
authority: implementation-evidence
related:
  - ACTAKIT-INGRESS-001
  - ACTAKIT-DEPOSIT-WRITER-AUTH-001
---

# INGRESS-001 — Connector SPI + Inbox implementation evidence

## Scope

INGRESS-001 implements the source-ingress socket **without adapting any real
source**. The purpose is specifically to prevent the existing Esparza scraper
from becoming the hidden reference architecture.

Implemented production surface:

```text
actakit/ingress/
  models.py   terrain-neutral DTOs/descriptors/run result
  spi.py      InboxPort + SourceConnector protocol + host runner
  inbox.py    core-owned DepositInbox -> DepositWriter bridge
```

No schema change was required. `0001` remains byte-identical to its certified
pre-release baseline.

## Boundary proved

```text
connector-private terrain
        ↓
CaptureEnvelope / CapturePayload
        ↓
InboxPort
======== core ownership ========
        ↓
DepositInbox
        ↓
DepositWriter
        ↓
Depósito
```

Connector constructors cannot supply the preallocated canonical Acquisition,
Artifact, ArchiveObject or Representation identities. Those fields are allocated
inside the ActaKit boundary and are `init=False` implementation state, while
reusing the same immutable envelope still produces an exact retry at the
certified Depósito idempotency boundary.

`DepositInbox` is created by the host with:

- canonical `SourceRegistration`;
- exact `ConnectorDescriptor(key, version)`;
- core-owned `InboxPolicy`.

The connector therefore cannot choose canonical Source identity, spoof its
adapter key/version through an envelope, or self-promote incoming bytes from
`pending` to `verified`.

## Terrain-neutral proof matrix

Synthetic connectors are deliberately unlike each other:

| Fixture connector | Private topology | Generic capability/result |
|---|---|---|
| HTML inventory | pull from HTML/link shape | `pull + inventory`, `complete_inventory` |
| JSON API | cursor-driven incremental API | `pull + incremental + checkpointing`, opaque checkpoint |
| Manual drop | push/local material | `push`, coverage `unknown` |

All three deliver the same `CaptureEnvelope` type and land in the same canonical
Source/Locator/Acquisition/Artifact/original-Representation custody graph.

The DTO field audit explicitly rejects Esparza/municipality/acta/HTML/API/
selector/browser/pagination/session/article concepts from the socket shape.

## Reverse audit against the current Esparza-oriented scraper

`scripts/scrape_actas.py` was inspected only after the socket existed. Its current
record shape includes `seccion`, `year`, `title`, `uuid`, `ext`, `filename`, `url`
and `css_class`. The audit did **not** change the SPI:

- `url` maps naturally to an observed locator/URL;
- `filename` and transport media hints map to bounded payload observations;
- downloaded bytes map to `CapturePayload`;
- `seccion/year/title/uuid/css_class` are source-specific discovery semantics and
  do not become Inbox fields merely because Esparza has them.

If those discovery labels must later be canonical evidence, the connector can
preserve the listing/API response bytes and a later typed observation contract can
be justified. INGRESS-001 intentionally does not add a generic metadata bag.

The existing scraper's streaming download loop also exposed that the current
`CapturePayload.data: bytes` transport is not a final large-object contract. That
is recorded as an implementation boundary rather than prematurely adding a
streaming framework before a real large source requires one.

## Run/checkpoint semantics

The host runner validates only generic claims that matter outside a connector:

- descriptor of connector and bound Inbox must match;
- input/output checkpoints require `checkpointing` capability;
- `complete_inventory` requires `inventory` capability;
- `incremental` coverage requires `incremental` capability;
- reported emitted count must equal envelopes actually accepted by Inbox.

Checkpoint bytes are passed through unchanged. INGRESS-001 does not create a
checkpoint table or assign semantics to their contents.

## Failure behavior

Connector exceptions are not swallowed. A proving connector commits one capture,
then encounters unexpected source structure and raises. Result:

```text
accepted acquisition/artifact retained: PASS
connector failure propagated: PASS
absence/deletion inference: NONE
```

This implements the existing Open States / ELI lessons: specialized source logic
fails loudly, and coverage/freshness is not inferred from a single crawl.

## Deliberate non-goals

INGRESS-001 does not authorize or implement:

- Esparza integration;
- network/browser fetching in core;
- plugin package discovery/entry-point registry;
- durable connector run/checkpoint persistence;
- historical import;
- source authority inference;
- Representation extraction/OCR;
- CivicDocument/Claim/Fichero writers;
- canonical cutover.

The current `CapturePayload.data: bytes` mechanism matches the already-certified
bounded Depósito writer. It is not a commitment that future large-media adapters
must buffer unlimited objects in memory; streaming/resource limits must be proven
by a real source before that transport mechanism is frozen.

## Certified proof

Commands/results on the exact registered SQLite 3.53.4 runtime:

```text
python -m pytest -q tests/test_ingress_spi.py       8 passed
python -m pytest -q                                 35 passed
MIGRATION_0001_SPEC_PROOF                           PASS; 54 STRICT + 3 FTS5; 16/16 fixtures
MIGRATION_FREEZE_PROOF                              PASS; 118 FK paths / 0 scans
SELECTOR_ARTIFACT_PROOF                             PASS
STORAGE_OPERATION_PROOF                             PASS
git diff --check                                   PASS
```

Production/frozen SQL remains byte-identical:

```text
31cac5ccc3440ce555242ba288317df527bb30949b2142026d8ceb2805d3adfc
```

The exact runtime gate is now closed. Full evidence is recorded in
`INGRESS_001_CERTIFICATION.md`; the real source connector remains a separate
shadow-mode review.
