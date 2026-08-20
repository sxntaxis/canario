---
id: ACTAKIT-STATUS-001
kind: status
state: architecture-revision-proposed
created: 2026-08-19
authority: operating
summary: Current acta pipeline remains intact while a self-contained civic-record architecture is being reviewed before persistent canonical implementation.
related:
  - ACTAKIT-ARCH-001
  - ACTAKIT-ROADMAP-001
---

# Current Status

## Current Implementation

The repository currently implements the file/Markdown acta pipeline. Existing
operator data and curated Hilos are preserved; no mass regeneration or migration
is authorized by the architecture proposal.

One existing canton configuration contains deployment-specific absolute paths.
Those paths are legacy deployment configuration, **not** target product
dependencies. The future durable core must operate from its own configurable
storage without requiring any named external workspace or application.

## Current Source Checkpoint

The existing source investigation found the official written Concejo archive at
Acta 161 dated 2026-05-18 while the municipality's official video publication
showed later sessions through Session 180 in August 2026. The videos establish
that later sessions occurred; they do not establish the exact content or
approval status of unavailable written actas.

This source gap remains a useful real-world proof case for the future model:
source occurrence, source authority, artifact acquisition, and formal written
record are not interchangeable.

## Architecture Revision Under Review

The current proposal now defines ActaKit as a self-contained civic-record system
using this native product language:

```text
Depósito -> Mesa de trabajo -> Lector -> Fichero
         -> Mesa de control -> Consultas -> Salidas
```

Key revisions awaiting acceptance:

- claims may exist machine-only and searchable before human review;
- extraction aims for broad civic relevance, not only editorial highlights;
- review supports strict, batch, and supervised modes;
- one operator is the default organizational assumption;
- Episode/Hilo move out of the universal core into an Output Type;
- queries become first-class read operations;
- Output Types are extensible/shareable without sharing civic data;
- daemon/RPC/federation/public APIs move to the horizon;
- product architecture no longer depends on external named workspaces/services.

## Active Edge

```text
review/accept architecture revision
-> validate pre-SQL model with realistic fixtures
-> design first SQLite schema
-> implement semantic kernel
-> implement local custody/Fichero
-> prove one new acta end to end
```

## Prohibitions Until Acceptance

- No persistent canonical SQLite schema is authorized by these proposal docs.
- No daemon/RPC/federation implementation is justified yet.
- No automatic public publication.
- No historical mass rewrite.
- No claim may conceal whether it is machine-only or human-reviewed.
- No AI output may serve as factual source evidence for its own claim.
- No individual political-preference profiling or targeted-persuasion use.

## Planning Documents

The proposed design is defined by `ARCHITECTURE.md`, `CONTRACTS.md`,
`DATA_MODEL.md`, `ROADMAP.md`, `IMPLEMENTATION_PLAN.md`, and
`RELEASE_1_0.md`. Acceptance authorizes the semantic direction and the next
pre-SQL/schema work, not every horizon feature mentioned there.
