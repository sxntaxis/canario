# Deep Source-Book Audit Closure

**State:** PASS for beginning a *schema candidate design only*.

No SQLite migration, production schema, or implementation is authorized by this research closure.

## Closure rule

Each of the 29 Books was individually revisited against primary/normative evidence, implementation/real-use evidence where applicable, scars/errata/evolution, local claim ledgers, bounded transfer, explicit do-not-copy boundaries, schema pressure, and residual risk. Standards without product-style scars were evaluated using conformance/implementation/evolution evidence instead of invented failure stories.

## Book status

- `akoma-ntoso` — **deep-audited** — 3 sources / 4 claims
- `alto` — **deep-audited** — 3 sources / 2 claims
- `bagit` — **deep-audited** — 2 sources / 3 claims
- `datasette` — **deep-audited** — 5 sources / 3 claims
- `documentcloud` — **deep-audited** — 4 sources / 5 claims
- `eli` — **deep-audited** — 3 sources / 2 claims
- `followthemoney` — **deep-audited** — 4 sources / 5 claims
- `frictionless-data-package` — **deep-audited** — 2 sources / 2 claims
- `iiif` — **deep-audited** — 4 sources / 3 claims
- `memento` — **deep-audited** — 3 sources / 2 claims
- `method` — **deep-audited** — 6 sources / 6 claims
- `ocfl` — **deep-audited** — 2 sources / 3 claims
- `openrefine` — **deep-audited** — 2 sources / 3 claims
- `opensanctions` — **deep-audited** — 4 sources / 5 claims
- `openstates` — **deep-audited** — 5 sources / 6 claims
- `paperless-ngx` — **deep-audited** — 4 sources / 5 claims
- `popolo` — **deep-audited** — 2 sources / 2 claims
- `premis` — **deep-audited** — 2 sources / 2 claims
- `prov` — **deep-audited** — 2 sources / 3 claims
- `records-in-contexts` — **deep-audited** — 3 sources / 3 claims
- `shacl` — **deep-audited** — 2 sources / 3 claims
- `skos` — **deep-audited** — 2 sources / 3 claims
- `sqlite` — **deep-audited** — 7 sources / 7 claims
- `tropy` — **deep-audited** — 4 sources / 2 claims
- `w3c-org` — **deep-audited** — 2 sources / 2 claims
- `warc` — **deep-audited** — 3 sources / 3 claims
- `web-annotation` — **deep-audited** — 3 sources / 5 claims
- `wikidata` — **deep-audited** — 6 sources / 7 claims
- `zotero` — **deep-audited** — 3 sources / 3 claims

## Transversal result

- The research supports **graph-shaped relational data in SQLite**, not a graph database.
- It supports a small universal civic core plus typed/versioned extension profiles, not a national ontology.
- It supports raw evidence/mentions before normalization and reconciliation.
- It supports direct relations plus selective promotion to rich associations, not generic triples.
- It makes acquisition, storage bootstrap, backup, search-index rebuild, parser failure and purge semantics part of correctness.

## Remaining gaps

The remaining material uncertainties are no longer “which general architecture pattern should ActaKit use?” They are schema-shape and implementation questions that must be answered with the existing semantic fixtures plus concrete SQL constraints/query plans and later real-artifact proof fixtures. Examples: exact cardinalities/nullability, revision table shape, selector payload schema, association subtype representation, FTS tables/triggers/rebuild strategy, expected indexes, and backup/restore commands.

## Gate

**DEEP_RESEARCH_GATE: PASS**

Authorized next activity: **design a candidate SQLite schema and test it against the fixtures/research pressures.**

Not authorized: production migration, destructive legacy rewrite, daemon, federation, public publication, or canonical-data cutover.
