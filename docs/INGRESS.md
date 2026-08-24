---
id: ACTAKIT-INGRESS-001
kind: architecture-contract
state: accepted
accepted: 2026-08-21
created: 2026-08-21
authority: architecture
summary: Terrain-neutral Source Connector SPI and Inbox ingress port separating arbitrary external source geography from canonical Depósito custody.
related:
  - ACTAKIT-ARCH-001
  - ACTAKIT-CONTRACTS-001
  - ACTAKIT-STATUS-001
---

# Source Connectors and the Inbox

## Design law

> **Outside the Inbox, geography varies. Inside the Inbox, Canario is standard.**

The current Esparza scraper is one source-specific acquisition strategy. It is
not the shape from which future acquisition architecture is derived.

An HTML scraper, REST/GraphQL client, browser automation flow, RSS reader, SFTP
reader, filesystem watcher, manual drop, webhook receiver, or future transport
may all be valid **Source Connectors**. Their private mechanics may differ
completely. They become interchangeable because they terminate at the same
**Inbox ingress port**.

In technical terms this is a Ports-and-Adapters boundary plus a small plugin SPI.
The connector is an inbound adapter and anti-corruption layer; the Inbox is the
core-owned ingress port.

```text
external terrain
  HTML | API | browser | feed | filesystem | manual | ...
       \     |       |       |        |       /
             Source Connector
                    |
              CaptureEnvelope
                    |
             Inbox / IngressPort
================ CORE BOUNDARY ================
                    |
               DepositWriter
                    |
                 Depósito
                    |
             Mesa de trabajo
                    |
                  Lector
                    |
                  Fichero
```

The legacy Markdown processing `inbox/` used by the old pipeline is a different
editorial concept. `Inbox` in this contract means the **source-ingress boundary**.

## Vocabulary

| Canario term | Technical concept | Owns |
|---|---|---|
| **Source Connector** | inbound adapter / plugin SPI implementation | source-specific discovery, auth, fetching, retries, pagination, browser/API mechanics |
| **Inbox** | ingress port | validation/translation from boundary DTOs into canonical custody writes |
| `CaptureEnvelope` | boundary DTO/message | one observed retrieval outcome plus zero or more captured payloads |
| `CapturePayload` | boundary byte payload | captured bytes plus bounded observed transport metadata |
| Connector descriptor | SPI identity/capabilities | stable connector key/version and generic host-relevant capabilities |
| Connector checkpoint | opaque plugin state | plugin-specific resume state; the core does not interpret it |
| Depósito | durable landing/custody layer | canonical Source/Acquisition/Artifact/ArchiveObject/original Representation |

## The socket shape

A connector may submit only terrain-neutral acquisition facts:

```text
CaptureEnvelope
  observed_at
  outcome
  locator?          value + open locator kind
  http_status?      only when the transport actually has one
  error_code?
  payloads[]
    bytes
    role
    observed filename/url?
    media type/language/charset hints?
```

The boundary deliberately does **not** contain:

```text
municipality
acta number
session type
article/item
council member
HTML selector
API pagination shape
Playwright/browser state
GraphQL schema
source-specific document ontology
Claim/Entity/Tag semantics
```

If a connector knows a source label such as `"Acta 47"`, that is not permission
to create a `CivicDocument` or semantic Claim at ingress. Important source
metadata that cannot yet be represented honestly must remain in preserved source
material until a bounded canonical observation contract exists; it is never
silently promoted or discarded as semantic truth.

### Why there is no universal `metadata: dict`

A generic metadata bag would make the socket look flexible while quietly turning
it into an untyped dumping ground for the first connector's concepts. INGRESS-001
therefore admits only bounded custody observations already understood by the core.
Source-specific listing/API metadata should be preserved in the captured source
response when evidentially important, or promoted later through an explicit typed
contract once multiple real sources prove the need. Operational hints such as an
ETag/cursor may remain connector-private unless retention is justified.

This is loss-avoidance by preserving source material, **not** permission to throw
away useful metadata. It is a refusal to canonicalize semantics before their
boundary is understood.

## Ownership inversion

A connector does not choose canonical source identity, adapter attribution,
custody validation state, or persistence IDs.

Canario binds the Inbox to:

```text
one canonical Source
+ one ConnectorDescriptor(key, version)
+ core-owned Inbox policy
```

Then connector code sees only `InboxPort.accept(CaptureEnvelope)`.

The current implementation therefore stamps `adapter_key`/`adapter_version` from
the host binding, assigns canonical IDs inside Canario, creates incoming
Artifacts as `validation_state='pending'`, and applies availability from
core-owned Inbox policy. A connector cannot self-certify its bytes as verified.

## Discovery is not the universal interface

The SPI does **not** require `discover()` or `scrape()`.

Some terrains naturally use discovery followed by acquisition; others are push
sources and have nothing to discover:

```text
HTML index       discover links -> fetch
REST API         cursor/page -> fetch
RSS              entries -> fetch
browser portal   navigate -> click/download
filesystem       event/listing -> open
manual upload    already has payload
webhook          payload arrives directly
```

The universal operation is delivery into the Inbox, not the method used to find
material.

`SourceConnector.run(context)` is therefore intentionally broad: the connector
owns its terrain and pushes zero or more `CaptureEnvelope` values into the Inbox.

## Capabilities, coverage, and checkpoints

Capabilities describe host-relevant behavior rather than website technology:

```text
pull
push
inventory
incremental
checkpointing
```

The first run-result coverage vocabulary is:

```text
unknown
incremental
complete_inventory
```

This distinction is required because **absence in one run is never deletion
proof**. A connector claiming `complete_inventory` must explicitly advertise the
inventory capability; an incremental connector must not imply complete source
coverage.

Checkpoints are opaque bytes. Examples may internally represent a page cursor,
RSS GUID, source watermark, object key, or browser-specific token. The Canario
core passes them through but does not parse or assign civic meaning to them.
INGRESS-001 does not yet add durable checkpoint/run tables; persistence will be
added only when a real connector proves that need.

## Failure semantics

Specialized source logic must fail loudly when its assumptions stop matching the
source. Silent plausible-but-wrong structured acquisition is worse than a failed
connector run.

At the same time, fail-loud does not mean deleting already preserved evidence:

```text
connector accepts capture A -> custody committed
connector later encounters unexpected structure -> raises
capture A remains preserved
missing B/C are not interpreted as deletion
```

A failed/not-found observation may contain zero payloads. An unsuccessful
transport may also preserve a response body when useful; outcome and payload
presence are independent facts.

## Source connectors stop at Inbox

A Source Connector is forbidden from directly performing canonical writes below
the boundary. It must not:

- write SQLite tables;
- call `DepositWriter` directly;
- create ArchiveObjects or canonical Artifacts itself;
- create derived Representations/ProcessRuns;
- classify CivicDocuments;
- create Claims, Entities, Tags, relations, reviews, or FTS entries;
- infer deletion from scrape absence.

The host/core owns the `DepositInbox -> DepositWriter` bridge.

This is an architectural ownership rule, not a Python security sandbox. A hostile
plugin running in-process could import arbitrary modules; connector trust and
sandboxing are separate future concerns if third-party untrusted plugins become a
real product requirement.

## Source connectors are not Representation processors

Acquisition terrain and content processing are separate extension axes:

```text
Source Connector                    Representation processor
----------------                    ------------------------
where/how material is obtained      how captured bytes become inspectable forms
HTML/API/browser/filesystem         PDF text extraction
manual/feed/etc.                    OCR
                                    DOCX parsing
                                    spreadsheet/table view
                                    transcript
```

The Source Connector ends after original custody. The Mesa de trabajo begins
from retained original Representations. A PDF parser must not know how Esparza's
website paginates; an Esparza connector must not own PDF extraction semantics.

## Plugin packaging is deliberately not frozen

INGRESS-001 freezes the **SPI shape and ownership boundary**, not installation or
plugin discovery mechanics. Python entry points, local configuration, bundled
connectors, subprocess isolation, or another loader may be chosen later without
changing the Inbox contract.

The current in-process `bytes` payload transport is likewise an implementation
choice of the bounded writer, not a declaration that future large-media
connectors must buffer unlimited material in memory. A real large-object source
must prove resource/streaming requirements before that transport mechanism is
frozen.

## First proving connectors

The SPI is tested against deliberately incompatible fake terrains:

1. HTML inventory/pull;
2. incremental JSON API with opaque checkpoint;
3. manual push/drop.

They all produce the same Inbox contract and canonical custody graph. This proof
exists specifically so the Esparza scraper cannot become the architectural
template.

The first real connector may be Esparza, but it is a **consumer of INGRESS-001**,
not its reference model. Initial real integration must run in shadow mode and
must not change the legacy Markdown/Hilo pipeline or authorize canonical cutover.
