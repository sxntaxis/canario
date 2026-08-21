---
id: ACTAKIT-ESPARZA-CONNECTOR-001
kind: implementation-record
state: local-proof-pass-target-runtime-certification-required
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

## Local evidence

At this checkpoint the available environment uses SQLite 3.46.1, so it cannot
close the registered target-runtime gate. Before commit, the complete local suite
must remain green and `0001` must remain byte-identical to the certified freeze.

## Coverage caveat

A `complete_inventory` result means complete traversal of the configured CMS
listings, not proof that the municipality has published every expected written
record or that no later session exists on another channel.

## Next gate

Run the complete repository + ingress + Esparza connector proofs on exact SQLite
3.53.4. Only after that certification may a real network shadow run be treated as
dogfood evidence. Canonical cutover remains separate and unauthorized.
