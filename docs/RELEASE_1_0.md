---
id: ACTAKIT-RELEASE-001
kind: release-plan
state: proposed-for-acceptance
created: 2026-08-19
authority: roadmap-proposal
summary: Minimal operational and evidence gates for a durable self-contained Canario 1.0.
related:
  - ACTAKIT-ARCH-001
  - ACTAKIT-ROADMAP-001
  - ACTAKIT-IMPLEMENTATION-001
---

# 1.0 Release Plan

## Version Identity First

The repository already contains a changelog entry labelled `1.0.0`. Before a
new stable release, determine whether that version was actually distributed. A
published version number is never reused. This plan therefore describes the
**next stable durable release**, even if its final number must be greater than
`1.0.0`.

## What Stable Means

Stable means one local installation can reliably:

```text
acquire public civic records
preserve original evidence
create usable representations
extract broad traceable claims
search machine-only and reviewed material distinctly
review strictly, in batch, or by supervision
correct without erasing history
run queries and follow stored claim connections
build outputs
back up and restore
```

Stable does **not** mean every horizon feature exists.

## Deployment Assumption

The reference deployment is a normal organization-controlled Linux machine with
local attached storage. One operator is normal; a second operator is supported
organizationally but not required for routine operation. Many consumers may use
read-only outputs/search through whatever local interface is provided.

SQLite database/WAL files remain on local attached storage, not network shares or
sync folders. Original evidence lives in the Canario archive.

A daemon, public server, container image, federation keys, or multi-user identity
provider is not a stable-release requirement unless implementation experience
proves it necessary.

## Operator Capabilities

Canario needs actions, not a fictional staffing chart:

```text
administer installation
operate acquisition/processing
review/correct records
configure outputs
export/publish when allowed
read/search
```

The same person may perform all operator actions. Every consequential action
remains attributable.

## Security Baseline

Stable must address the actual local/document threats:

| Threat | Required control |
|---|---|
| Hostile/changing source site | bounded source policy, redirect/host checks, size/media limits, provenance |
| Malicious document | maintained parsers, no document-controlled shell/network behavior, resource bounds |
| Path/symlink mistakes | safe path handling, atomic writes, traversal/symlink tests |
| Prompt injection | source material is data; Lector has no implicit shell/secrets/publication authority |
| Accidental destructive write | core-owned canonical writes, revision history, targeted replay/stale guards where needed, backups |
| Privacy harm | sensitive-output defaults, explicit publication policy, traceable source/evidence |
| Data loss | verified backup/restore and archive/database consistency checks |

Supply-chain hardening should be proportionate to the supported installation
method. Provide dependency pinning/hashes and release checks appropriate to that
method; do not require three packaging ecosystems merely to satisfy a checklist.

## Backup and Restore

Provide one documented backup command/process that creates a consistent snapshot
of:

- SQLite state;
- referenced archive objects;
- configuration/taxonomies/output definitions needed to interpret the state;
- manifest/checksums.

Provide one documented restore/verify process on a clean location/machine.

A backup that cannot be restored is not release evidence.

## Output and Sharing Boundary

Stable supports local outputs and exporters over the bounded read model. A
portable/shareable package format is optional until multiple real outputs or
installations justify a compatibility contract.

Inter-installation civic-data exchange, signed peer trust, federation, and public
network services are horizon features, not GA gates.

## Compatibility

Version independently only where a real compatibility boundary exists:

```text
application
SQLite schema
canonical record contracts
configuration
Output Type/export contracts
```

Do not create version systems for protocols/packages that do not yet exist.

Schema migration must preserve evidence, claim history, review state, and output
references. Upgrade/restore behavior is tested on realistic fixtures.

## Test and Evidence Program

| Layer | Required proof |
|---|---|
| Semantic contracts | IDs, revisions, document typing, locators, review policy, corrections |
| Acquisition/extraction | normal, changed, duplicate, malformed, unknown, hostile inputs |
| Claim extraction | high-volume supervised extraction with stable provenance/evidence |
| Review | strict, batch, supervised; sensitive/public trigger cases |
| Query | text/entity/tag/date/status retrieval, explicit relation traversal, and evidence resolution |
| Outputs | Hilo/Episode output plus one tiny non-Episode proof over same Fichero |
| Failure/recovery | interruption, disk/permission failure, corrupt/missing archive object, restore |
| Security/privacy | paths, prompt injection, restricted output, destructive-operation guards |
| Operator journey | one person can acquire -> inspect -> search -> review/correct -> output -> backup |

Fixtures are synthetic or deliberately approved for testing. Current production
working directories are never release fixtures.

## Stable Release Gates

| Gate | Evidence |
|---|---|
| Version identity | no published version number is reused |
| Scope | documentation accurately explains what Canario is and is not |
| Integrity | no unresolved critical evidence/claim lineage or data-loss defect |
| Traceability | claims resolve to exact evidence in multiple representation types |
| Volume | broad claim extraction works without mandatory one-by-one approval |
| Review | strict/batch/supervised semantics demonstrated |
| Degradation | unknown/malformed documents preserve honest partial state |
| Query | obscure facts and a real relation chain are retrievable without AI rediscovery |
| Output boundary | Hilo/Episode and a tiny non-Episode proof work without core schema coupling |
| Recovery | clean restore verifies database + archive consistency |
| Security/privacy | baseline threat tests pass; sensitive outputs fail safely |
| Operations | one supported install/update/backup/restore workflow is documented |
| Real use | at least one real canton/operator completes a meaningful civic work cycle |
| Approval | named maintainer/operator accepts the evidence and release |

## Not Required for Stable

- federation or signed peer packages;
- two-person approval for every release/action;
- root/online signing-key hierarchy;
- public hosting;
- public API/automation adapters;
- OCI plus wheel plus source package simultaneously;
- specialized graph/vector database;
- multi-tenant role system;
- historical bulk migration.

These can be excellent future features. They do not prove the core works.
