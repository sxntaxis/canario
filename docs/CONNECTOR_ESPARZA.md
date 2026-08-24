---
id: ACTAKIT-CONNECTOR-ESPARZA-001
kind: source-connector-contract
state: certified-bounded-shadow-dogfood-pass
created: 2026-08-21
authority: implementation
parent_contract: ACTAKIT-INGRESS-001
summary: First real SourceConnector consumer of INGRESS-001 for the Municipalidad de Esparza CMS, isolated to shadow custody.
---

# Esparza CMS Source Connector

## Role

`canario.connectors.esparza.EsparzaCmsConnector` is the first real consumer of
`ACTAKIT-INGRESS-001`. It is deliberately source-specific and is **not** a new
shape for the Inbox SPI.

```text
Municipalidad de Esparza CMS
        |
        | private HTML/CMS terrain
        v
EsparzaCmsConnector
        |
        | CaptureEnvelope only
        v
InboxPort -> DepositInbox -> DepositWriter -> shadow Depósito
```

The connector module does not import `canario.deposit`, SQLite, semantic
repositories, Hilos, or the legacy scraper.

## Current official source surfaces

The connector's default inventory scope is the three CMS surfaces already used by
the legacy Esparza tooling:

```text
/articulo/230/actas-concejo-municipal
/articulo/609/actas-de-comisiones
/articulo/231/actas-junta-vial
```

The default download endpoint is source-specific CMS terrain:

```text
/files/folder/<source filename>
```

These paths live only in the Esparza connector configuration. They do not enter
`CaptureEnvelope`, `InboxPort`, or any shared source abstraction.

## Preserve discovery evidence instead of inventing metadata

The CMS listing contains source-specific labels such as year, title, filename,
CSS class and the `openDocumentArticle(...)` hook. INGRESS-001 intentionally has
no generic metadata bag for these concepts.

Therefore each listing page is itself deposited as original HTML evidence before
it is parsed. The connector may use the labels privately to discover downloads,
but it does not promote them to CivicDocument or Inbox fields.

```text
listing HTML ----> CaptureEnvelope(response_body)
      |
      +-- private parse --> resource URL
                              |
                              +--> CaptureEnvelope(primary bytes)
```

If the known `ul.fileTree` / `openDocumentArticle(...)` structure stops matching,
the captured listing remains in custody and the connector raises
`EsparzaSourceStructureError`. Plausible-but-wrong empty inventory is forbidden.

## HTTP and failure semantics

The connector uses bounded source-private HTTP behavior:

- HTTP(S) only;
- redirects are followed manually;
- redirects may not leave the configured Esparza host / `www` alias;
- response bytes are bounded before entering the in-memory `CapturePayload`;
- timeouts/transport/oversize failures become failed Acquisition observations;
- `404` and `410` become `not_found` observations;
- non-success response bodies may be preserved as `response_body` evidence;
- a `200` HTML body returned where a listed resource was requested is preserved
  and marked `unexpected_html_payload` instead of being treated as a document;
- an empty successful resource response is marked failed;
- ZIP-like bytes are not guessed to be DOCX merely because the legacy source
  often used DOCX. Unknown ZIP containers remain `application/zip` unless the
  transport supplies a more specific type.

Individual resource failures do not erase the rest of an inventory run.

## Coverage

The connector advertises `pull + inventory`, not checkpointing.

It returns `complete_inventory` only when using the unfiltered default three
sections with no year or document-count limit. In that mode, every listing was
successfully parsed and every discovered resource was attempted. A resource may
still have an honest `failed`/`not_found` Acquisition; coverage describes
inventory traversal, not successful content availability.

Any section/year/document-limit dogfood run returns `coverage='unknown'`.
Absence in such a run is never deletion evidence.

`complete_inventory` is only a claim about traversal of the configured CMS
listing surfaces at that observation time. It is **not** evidence that every
meeting has a published written acta, that the archive is legally complete, or
that no newer session exists elsewhere. Source completeness and civic-record
completeness remain separate questions.

## Shadow host

`scripts/run_esparza_shadow.py` is a temporary host/integration harness, not the
plugin API. It requires an explicit `--shadow-root` and writes only:

```text
<shadow-root>/
  canario.sqlite3
  archive/
  source-binding.json
```

`source-binding.json` retains the host-owned canonical Source ID and creation
timestamp across runs. It is not a connector checkpoint. If the database exists
but this binding is missing, the host fails instead of silently minting a second
Source identity.

The production SQLite runtime guard remains active; there is no shadow-only
runtime bypass.

## Explicit non-goals

This unit does not:

- modify `scripts/scrape_actas.py`;
- write the legacy vault/download tree;
- alter Hilo/Markdown behavior;
- import historical files;
- create CivicDocuments/Claims/Entities/reviews/FTS semantics;
- run PDF/DOCX/OCR extraction;
- add durable connector checkpoints;
- freeze Python plugin discovery/entry-point packaging;
- authorize canonical cutover.

The legacy scraper and the Source Connector can therefore run side-by-side for
comparison without either path being declared canonical.
