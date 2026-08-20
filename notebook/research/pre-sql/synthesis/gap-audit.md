# Second-pass gap audit

## 1. Coverage verdict

**Verdict: sufficient for the pre-SQL semantic decision.**

The second pass did not reveal a missing architectural family large enough to justify extending the source horizon before fixtures. It did reveal three bounded refinements: raw entity mentions, selector/state evidence location, and a rich-relation promotion rule.

Coverage by pending ActaKit decision:

| Decision | Evidence families | Status |
|---|---|---|
| Source vs acquisition vs bytes | WARC, Memento, OCFL, Paperless | covered |
| Original vs derived representation | Paperless, Zotero, DocumentCloud, Akoma | covered |
| Civic document identity/version/format | Akoma, ELI, RiC, Open States | covered |
| Evidence locator | Web Annotation, IIIF, ALTO, DocumentCloud | strongly covered |
| Provenance | PROV, PREMIS, WARC, FtM | strongly covered |
| Claim semantics | Wikidata, FtM, Plaza audit | covered with one fixture question |
| Claim relations / graph shape | FtM, Popolo, ORG, SQLite | strongly covered |
| Entity identity/reconciliation | OpenRefine, OpenSanctions, Open States, FtM | strongly covered |
| Operator review/bulk workflow | OpenRefine, Paperless, DocumentCloud, Tropy | covered |
| Query/search baseline | SQLite, Datasette | covered |
| Local taxonomy | SKOS, Tropy, Paperless | covered |
| Outputs/interchange | Frictionless, BagIt, Datasette | covered for boundary; package ecosystem deliberately deferred |
| Validation | SHACL principle + operational schemas | covered at principle level |
| Privacy/purge collision | OCFL/DocumentCloud + ActaKit policy requirement | identified; policy decision remains |

## 2. Remaining open decisions before SQL

These are now **fixture questions**, not invitations for another broad standards sweep:

1. **Claim scope:** does a real civic claim need structured validity/jurisdiction fields, or do proposition + anchors suffice?
2. **EntityMention shape:** what minimum data preserves raw mention and supports unresolved/candidate/confirmed resolution without duplicating claim text?
3. **Rich relation threshold:** which first real fixture demonstrates promotion from direct relation to typed association/event?
4. **Document identity edge:** when one PDF contains several semantically independent documents, do we create multiple CivicDocuments or parts?
5. **Acquisition minimum:** which transport/source metadata is required for ordinary municipal web/PDF sources?
6. **Purge semantics:** what minimum tombstone/audit information can remain after a lawful deletion of restricted bytes?
7. **Evidence selector bundle:** which selectors are mandatory/recommended for PDF, text, spreadsheet, media and JSON baseline fixtures?
8. **Review write semantics:** how does one batch command preserve per-record decisions and atomic failure behavior?

## 3. Deliberately deferred research

Do not extend this Book now for:

- graph databases/Neo4j benchmarks;
- RDF stores or SPARQL architecture;
- vector databases/embedding retrieval;
- federation/signing/key management;
- multi-user enterprise authorization;
- output package registries/marketplaces;
- national civic/topic ontologies;
- full OCFL repository implementation;
- complete Akoma/ELI/RiC conformance;
- daemon/RPC topology.

Those topics become legitimate only after a real requirement crosses the documented boundary.

## 4. Anti-confirmation check

The study actively looked for evidence that would overturn the current design.

- **Graph DB:** no source showed a canton-scale need; Web Annotation explicitly allows non-graph implementations and SQLite supports bounded recursive traversal. No reversal.
- **RDF/ontology core:** standards offer interoperability but operational systems routinely use ordinary databases and explicit typed models. No reversal.
- **Strict human approval:** operational tools normalize bulk/semi-automatic workflows; no reversal.
- **Closed document taxonomy:** operational tools and civic systems preserve unknown/raw classification. No reversal.
- **One generic relation table:** FtM/ORG/Popolo show rich relationship objects when attributes matter. The baseline needs a promotion rule, not a universal edge model.
- **No unresolved entity record:** reconciliation systems strongly contradict this. This is the clearest missing pre-SQL pressure.

## 5. Stop condition

The Book stops here because new sources are now repeating mechanisms already represented in the ledgers. The remaining uncertainty is empirical: whether concrete ActaKit fixtures fit the candidate abstractions cleanly.

**Next evidence step:** build/describe the pre-SQL fixtures, then revise the conceptual model only where a fixture breaks it. SQL comes after that.
