---
id: ACTAKIT-STATUS-001
kind: status
state: ESPARZA_CONNECTOR_001_IMPLEMENTED_CERTIFIED__BOUNDED_SHADOW_DOGFOOD_PASS
created: 2026-08-19
updated: 2026-08-21
authority: operating
release_phase: prerelease
schema_compatibility_boundary: not-established
summary: INGRESS-001 and the first real Esparza Source Connector are certified with bounded shadow dogfood; canonical cutover, historical import, and semantic writers remain prohibited.
related:
  - ACTAKIT-ARCH-001
  - ACTAKIT-ROADMAP-001
  - ACTAKIT-INGRESS-001
  - ACTAKIT-CONNECTOR-ESPARZA-001
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
Inbox -> Depósito -> Mesa de trabajo -> Lector -> Fichero
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
-> certified INGRESS-001 Source Connector SPI + Inbox
-> certified Esparza connector and bounded real network shadow dogfood
-> Mesa de trabajo Representation processors later
-> semantic writers and explicit canonical-cutover gate later
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

## INGRESS-001 current boundary

`docs/INGRESS.md` is accepted. The implementation lives in `actakit/ingress/` and
proves that HTML-inventory, incremental JSON-API, and manual-push fixtures all
terminate at one `InboxPort` without importing their terrain into the core DTO.

The bridge is intentionally one-way:

```text
SourceConnector -> CaptureEnvelope -> InboxPort -> DepositWriter
```

Connector code does not receive `DepositWriter` or canonical Source/persistence
identity. `DepositInbox` is host-bound to those core concerns. Specialized
connector failures propagate while already accepted custody remains preserved.

This boundary is certified on the exact SQLite 3.53.4 runtime. The certification
does not authorize adapting the real Esparza source. Plugin packaging and durable
connector-run/checkpoint persistence remain unfrozen.

## Current Prohibitions

- No canonical-data cutover or historical mass import is authorized yet.
- No legacy Markdown/Hilo rewrite is authorized by migration `0001`.
- No semantic Fichero, Claim, review, purge, or archive/GC writer is authorized
  beyond the bounded Depósito custody writer certified in this checkpoint.
- The Esparza Source Connector is certified only as a bounded shadow-mode SPI
  consumer. Its two dogfood runs do not modify the current scraper/Hilo path and
  are not canonical. Coverage is unknown because the runs were intentionally
  filtered and bounded; historical import and cutover remain unauthorized.
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
