---
id: ACTAKIT-ESPARZA-CONNECTOR-001
kind: implementation-record
state: ESPARZA_CONNECTOR_001_IMPLEMENTED_CERTIFIED__BOUNDED_SHADOW_DOGFOOD_PASS
created: 2026-08-21
authority: implementation
parent: ACTAKIT-INGRESS-001
schema_changed: false
canonical_cutover_authorized: false
historical_import_authorized: false
semantic_writers_authorized: false
---

# ESPARZA-CONNECTOR-001 — real Source Connector in shadow mode

## Purpose

Prove the accepted terrain-neutral Inbox against the first real, source-specific
consumer without changing the socket or the legacy pipeline.

## Production surface

```text
actakit/connectors/esparza.py
scripts/run_esparza_shadow.py
```

The SourceConnector itself imports only the accepted ingress boundary plus its
private HTTP/HTML dependencies. The shadow runner is the host that binds Source,
`DepositInbox`, `DepositWriter`, database and archive paths.

## Anti-bias decision

The connector preserves each CMS listing page as an original HTML capture before
parsing it. Source labels (`year`, `title`, source filename, CSS class) therefore
remain recoverable from source evidence without becoming generic Inbox metadata.

## Local proof matrix

The tests cover:

- listing + resource through the same Inbox;
- fail-loud structure change after listing custody;
- same locator observed later with changed bytes;
- duplicate source listing / shared physical bytes with distinct provenance;
- `404`/`410` and HTML login/error body handling;
- filtered run cannot claim complete inventory;
- default unfiltered scope can claim complete inventory;
- oversize/transport failure becomes an Acquisition instead of fake content;
- unknown ZIP container is not guessed to be DOCX;
- cross-host redirect rejection before follow;
- same-host redirect with final observed URL retained;
- stable host-owned Source identity in shadow state;
- source-binding tamper rejection;
- section-filter validation.

## Certified evidence

The exact registered SQLite 3.53.4 runtime certification passed. The complete
repository suite passed (`51 passed`) and the Esparza-specific suite passed
(`16 passed`). Frozen `0001` remains byte-identical with SHA256
`31cac5ccc3440ce555242ba288317df527bb30949b2142026d8ceb2805d3adfc`.

## Coverage caveat

A `complete_inventory` result means complete traversal of the configured CMS
listings, not proof that the municipality has published every expected written
record or that no later session exists on another channel.

## Bounded shadow result

After Gate A, a bounded real-network run against the official CMS was executed
twice with `section=concejo`, `year=2026`, and `max_documents=3`. Both runs
returned `ESPARZA_SHADOW_RUN=PASS coverage=unknown emitted=4`. The first run
retained one listing HTML acquisition and three PDF resource acquisitions. The
second run reused the same host-owned Source binding and locators while adding
new observation history. All artifacts remained `pending`; no semantic rows were
written. Full hashes and custody counts are in
`ESPARZA_CONNECTOR_001_CERTIFICATION.md`.

Canonical cutover, historical import, and semantic writers remain unauthorized.
