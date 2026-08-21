---
id: ACTAKIT-PRESQL-DEEP-AUDIT-CHECKPOINT-001
type: research-checkpoint
state: in-progress
authority: evidence-work
created: 2026-08-20
updated: 2026-08-20
baseline: 7b291c89a0caf4e006c2583b90cb049aa232ad15
schema_authorized: false
---

# Pre-SQL deep Source Book audit — checkpoint

## Status

The pre-SQL research gate is **REOPENED**.

The existing 29 Source Books are useful scaffolding, but their previous `state: complete` must not be interpreted as proof that each object was deeply audited. Several Books were initially created from only one source and/or had no source-local claims. That is insufficient before freezing an expensive storage model.

**SQLite schema design and implementation remain unauthorized.**

## Closure rule for each Source Book

A Book earns `deep-audited` only after the audit records, as applicable:

1. primary/normative source;
2. implementation or real-use evidence;
3. scars, errata, changes, migration pressure, or conformance evidence;
4. source-local claim ledger;
5. bounded transfer to ActaKit;
6. explicit `do not copy` boundary;
7. schema pressure / expensive mistake avoided;
8. residual risk or unresolved uncertainty.

For standards, operational scars may not exist in the same sense as a product. In that case the Book must use implementation reports, conformance evidence, errata, revisions, or interoperability experience rather than inventing failure evidence.

## Method

The deep pass is Book-first, synthesis-second:

```text
Source Book
  -> sources
  -> source-local claims
  -> implementation/scars
  -> transfer
  -> do-not-copy
  -> schema pressure
  -> residual risk

29 audited Books
  -> cross-Book collisions
  -> cross-Book scenario matrix
  -> rejected architectures
  -> expensive-mistake ledger
  -> schema-specific gap audit
```

No Book is closed merely because its `book.md` exists.

## Findings surfaced during the second pass so far

These are checkpoint findings, not yet a replacement for the individual Book ledgers.

### SQLite

The future SQLite design must be evaluated as an operational system, not a feature checklist. The second pass surfaced concrete pressures around:

- foreign-key enforcement being connection policy rather than something ActaKit can assume globally;
- WAL/checkpoint behavior and the risk of long-lived readers delaying checkpoint progress;
- consistent backup/restore of a live database;
- FTS as a rebuildable retrieval structure rather than evidence authority;
- version-specific SQLite defects/fixes as a reason to define and verify a minimum supported version rather than saying only “SQLite”.

Transfer pressure: schema design must include connection bootstrap, transaction/backup assumptions, integrity checks, and rebuildability of secondary indexes.

### Zotero

Long-running application practice reinforces the boundary that canonical writes should go through ActaKit semantics rather than arbitrary external SQL. Direct database reads may be tolerable as an advanced/debugging surface; direct writes can bypass application invariants.

Transfer pressure: keep one canonical mutation boundary even if the first implementation is a CLI/core rather than a daemon.

### OpenRefine

Reconciliation supports preserving the source value while attaching a resolved identity/candidate judgment separately. It also demonstrates that batch human review can be an interface/workflow operation without requiring a heavyweight `ReviewBatch` domain object.

Transfer pressure: preserve `EntityMention` before resolution; batch review should not force batch-shaped canonical records.

### OpenSanctions / Nomenklatura

Entity acquisition and entity resolution/deduplication are distinct concerns. Canonical identities can be merged or split later, and reconciliation decisions need not destroy the observed source values.

Transfer pressure: entity resolution must be reversible/auditable; canonical IDs cannot be inferred solely from display names.

### FollowTheMoney

Investigative data modeling reinforces two boundaries:

- provenance can exist at finer granularity than whole-record provenance, but that granularity has real complexity cost;
- a relation with meaningful attributes (role, period, percentage, amount, etc.) often deserves its own association/event-like record rather than an overloaded generic edge.

Transfer pressure: keep simple `ClaimRelation` simple; provide a promotion path when the relation itself acquires domain meaning.

### Web Annotation

Selectors and resource state remain the strongest precedent for durable evidence targeting. Exact quote + context and/or positional selectors can coexist, and selectors are separate from the resource being targeted. The model is graph-shaped without requiring a graph database implementation.

Transfer pressure: ActaKit locators should be standards-informed, representation-aware, and redundant where useful; do not invent acta-specific locator semantics as the universal substrate.

### SKOS

Hierarchy semantics distinguish direct relationships from their transitive closure.

Transfer pressure: store direct relations and derive traversal/closure at query time; do not materialize every implied edge.

### PROV / PREMIS

Both reinforce selective, semantic provenance rather than a universal “everything is an event” log. PREMIS particularly demonstrates that preservation systems choose which events matter; PROV demonstrates explicit entity/activity/agent distinctions where provenance needs that depth.

Transfer pressure: avoid universal event sourcing and universal operation receipts. Persist events that alter custody, identity, approved interpretation, or other meaningful state.

### SHACL

Validation results are distinct from the data being validated. A validation PASS does not turn a claim into truth, and validation mechanisms can have implementation limits of their own.

Transfer pressure: keep structural validation separate from evidence/review semantics.

### OCFL

Immutable/versioned preservation has an exceptional deletion problem: legal or policy-driven purge cannot be hand-waved away by saying “immutable forever”.

Transfer pressure: retain immutable-by-default custody plus explicit purge/tombstone semantics; do not make routine correction behave like purge.

### Frictionless Data Package

Portable manifests can include paths/URLs that become active security inputs when consumed.

Transfer pressure: future shared Outputs/import packages need explicit resource-access policy; an installed Output must not gain arbitrary URL/file-fetch authority merely because a manifest references it.

### Popolo / W3C ORG

Civic organization models repeatedly encounter the point where a simple person-organization edge is insufficient because role, post, dates, or historical context belong to the relationship itself.

Transfer pressure: retain a small core relationship vocabulary and the already-planned promotion path to association/event records when real attributes demand it.

### ELI

Legal/public-information interoperability distinguishes identity/version/format, and later work added explicit coverage/freshness concerns: discovering metadata is not the same as knowing a corpus is complete or current.

Transfer pressure: ActaKit source acquisition must represent both observed captures and source-monitoring completeness/freshness uncertainty; absence from one crawl is not deletion.

### Tropy

Structured metadata templates and local tags can coexist, and focused regions/selections can carry their own notes/metadata without forcing every selection to become a new source document.

Transfer pressure: profiles remain optional; local taxonomy remains valid; `DocumentPart`/selection-like structure should be used only where it adds meaning.

### Memento / web archiving

A source URI and a particular observation/capture are not the same identity. Longitudinal web archives also demonstrate that archive URLs and replay metadata can change independently from the underlying historical observation.

Transfer pressure: preserve acquisition/capture identity separately from source URI and civic-document identity.

### Paperless-ngx

Operational document systems distinguish logical documents, original files, derived/archive versions, checksums, OCR/text and backup concerns.

Transfer pressure: backup/restore must define the complete authority boundary (`database + original custody + required derived state`) and explicitly classify which derivatives are regenerable.

### Open States

Mature civic scrapers prefer visible parser failure over silently accepting structurally unexpected source data. Their data models also preserve raw source names alongside resolved people/organizations when resolution exists.

Transfer pressure: acquisition should degrade gracefully, but specialized interpretation must fail loudly; preserve raw mentions before reconciliation.

## Expensive mistakes already strongly indicated

The deep audit is not complete, but the following are already strong negative constraints for the future schema/implementation:

- do not make a graph database or RDF store the canonical baseline;
- do not create a universal `nodes/edges` schema;
- do not use filenames, source numbers, URLs, or display names as canonical identity;
- do not rewrite raw mentions when entity reconciliation changes;
- do not allow arbitrary external SQL writes to canonical storage;
- do not treat FTS/search indexes as authority;
- do not overwrite originals with OCR, redaction, normalized text, or other derivatives;
- do not infer deletion from absence in a source observation;
- do not materialize all transitive/co-occurrence edges;
- do not make parser “resilience” silently guess unexpected source structure;
- do not define backup as a blind file copy of a live database;
- do not let future Output/package manifests imply arbitrary network/filesystem access;
- do not equate validation, citation, machine extraction, or source authority with truth;
- do not introduce universal event sourcing solely for auditability.

## What this checkpoint does NOT establish

This checkpoint does **not** establish:

- that any of the 29 Books is fully deep-audited;
- a final minimum SQLite version;
- a final schema;
- final relation/entity tables;
- final backup implementation;
- final Output/plugin security model;
- authorization to implement storage.

The next research work remains: complete all 29 Book audits, reconcile their claim ledgers, run the schema-pressure/collision synthesis, and issue a PASS/NO PASS gap audit before any candidate SQL schema is drafted.
