---
id: ACTAKIT-STATUS-001
kind: status
state: deposit-writer-implemented-and-certified
created: 2026-08-19
updated: 2026-08-21
authority: operating
release_phase: prerelease
schema_compatibility_boundary: not-established
summary: The semantic model, SQLite 0001 bootstrap, and bounded Depósito custody writer are certified; canonical cutover and semantic Fichero writers remain prohibited.
related:
  - ACTAKIT-ARCH-001
  - ACTAKIT-ROADMAP-001
---

# Current Status

## Pre-release compatibility policy

ActaKit is **pre-release**. There is currently no public/beta compatibility
commitment and no user SQLite fleet whose historical schema must be preserved.
Until `release_phase` is explicitly advanced to `beta` (or a later
compatibility-bearing release) in this operating-status document:

- `0001` is the mutable/rebaselinable schema baseline;
- a correct schema change updates `MIGRATION_0001_SPEC.sql` and production
  `0001.sql`, then repeats the applicable freeze/runtime/implementation proofs;
- development databases may be recreated from a fresh `0001`;
- do **not** create sequential `0002`/`0003`/... migrations merely to carry
  pre-release development state forward;
- do **not** add legacy-compatibility code for unreleased schema shapes.

The migration-history compatibility obligation begins only at the explicit
compatibility boundary. From that boundary onward, existing user data becomes an
upgrade constraint and schema evolution must use forward migrations instead of
rebasing historical `0001`.

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
-> certified implementation proof on exact SQLite 3.53.4
-> certified bounded Depósito custody writer
-> source-adapter integration/shadow-ingestion review
-> Mesa de trabajo and semantic writers later
-> explicit canonical-cutover gate later
```

Migration `0001` implementation was authorized by
`notebook/research/pre-sql/schema/MIGRATION_0001_AUTHORIZATION.md` only for the
fresh-database bootstrap/runtime boundary and is now certified by
`notebook/research/pre-sql/schema/MIGRATION_0001_IMPLEMENTATION_CERTIFICATION.md`.
The frozen SQL hash is:

```text
31cac5ccc3440ce555242ba288317df527bb30949b2142026d8ceb2805d3adfc
```

No production code may silently alter that SQL contract. A changed specification
must return to freeze review and target-runtime recertification.

The implementation certification does not authorize canonical cutover or
production semantic writers. The bounded Depósito writer is now certified by
`notebook/research/pre-sql/schema/DEPOSIT_WRITER_CERTIFICATION.md`.

## Current Prohibitions

- No canonical-data cutover or historical mass import is authorized yet.
- No legacy Markdown/Hilo rewrite is authorized by migration `0001`.
- No semantic Fichero, Claim, review, purge, or archive/GC writer is authorized
  beyond the bounded Depósito custody writer certified in this checkpoint.
- No current scraper integration, shadow ingestion, or historical import is
  authorized by this checkpoint.
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
