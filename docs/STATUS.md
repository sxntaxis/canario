---
id: ACTAKIT-STATUS-001
kind: status
state: migration-0001-authorized-for-bounded-implementation
created: 2026-08-19
updated: 2026-08-21
authority: operating
summary: The semantic model and SQLite 0001 freeze are accepted and certified; bounded implementation of migration 0001 is authorized while canonical cutover remains prohibited.
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

## Accepted Architecture Baseline

The semantic authority for the durable core is accepted in:

- `ARCHITECTURE.md`;
- `CONTRACTS.md`;
- `DATA_MODEL.md`.

ActaKit remains a self-contained civic-record system using:

```text
Depósito -> Mesa de trabajo -> Lector -> Fichero
         -> Mesa de control -> Consultas -> Salidas
```

The SQLite candidate then passed deep pre-SQL research, adversarial critical
review, exact-artifact selector proofs, operational backup/restore/purge proofs,
a physical migration-freeze review, and post-freeze certification on the exact
registered SQLite 3.53.4 source ID.

## Active Edge

```text
accepted semantic contracts
-> certified MIGRATION_0001_SPEC.sql
-> bounded production implementation of migration/bootstrap 0001
-> implementation proof on exact SQLite 3.53.4
-> semantic-core/repository integration
-> explicit canonical-cutover gate later
```

Migration `0001` implementation is authorized by
`notebook/research/pre-sql/schema/MIGRATION_0001_AUTHORIZATION.md` only for the
fresh-database bootstrap/runtime boundary. The frozen SQL hash is:

```text
31cac5ccc3440ce555242ba288317df527bb30949b2142026d8ceb2805d3adfc
```

No production code may silently alter that SQL contract. A changed specification
must return to freeze review and target-runtime recertification.

## Current Prohibitions

- No canonical-data cutover or historical mass import is authorized yet.
- No legacy Markdown/Hilo rewrite is authorized by migration `0001`.
- No acquisition, Claim, review, purge, or archive writer is authorized merely
  because the empty schema can now be implemented.
- No daemon/RPC/federation implementation is justified yet.
- No automatic public publication.
- No claim may conceal whether it is machine-only or human-reviewed.
- No AI output may serve as factual source evidence for its own claim.
- No individual political-preference profiling or targeted-persuasion use.

## Planning Documents

`ROADMAP.md`, `IMPLEMENTATION_PLAN.md`, and `RELEASE_1_0.md` remain planning
artifacts. Their future work packages do not expand this authorization. The
current authority for migration `0001` is the accepted semantic contract, the
certified freeze, and the bounded authorization record.
