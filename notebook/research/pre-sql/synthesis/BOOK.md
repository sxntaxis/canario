---
id: ACTAKIT-PRE-SQL-SYNTHESIS-001
type: research-synthesis
state: review
authority: evidence
created: 2026-08-20
updated: 2026-08-20
researched_through: 2026-08-20
actakit_baseline: 59bab9de30bbf2aa1eec96dddaee3cded31a9f3a
claim_ledger: claims.csv
scenario_ledger: scenario-matrix.csv
collision_ledger: collisions.csv
transfer_ledger: transfers.csv
gap_audit: gap-audit.md
---

# Pre-SQL synthesis — standards-informed, not standards-stacked

## Verdict

The external research does **not** justify replacing the current ActaKit direction. It refines it.

ActaKit should keep one small relational core and borrow proven semantics at its boundaries:

```text
Source -> Acquisition -> Artifact -> Representation -> CivicDocument
                                      |
                                      +-> EvidenceLink -> Claim
                                                          |
                                                          +-> EntityMention -> Entity
                                                          +-> ClaimRelation

Claims + entities + relations -> Queries -> Outputs
```

The strongest refinements before SQL are:

1. **Evidence locators:** follow Web Annotation's resource + selector + state idea; do not invent one brittle locator per document type.
2. **Raw mention before identity:** preserve the source string before resolving it to a canonical Entity; unresolved is valid data.
3. **Simple relation vs rich association:** direct claim relations stay simple; when role/time/amount belongs to the relation itself, promote it to a typed association/event rather than stuffing attributes into a generic edge.
4. **Custody degrades gracefully; specialized interpretation fails loudly:** preserve unknown material and generic representations, but do not let a broken profile emit plausible structured garbage.
5. **Original bytes remain separate from OCR/redactions/annotations:** derivative processing is regenerable; evidence custody is not silently rewritten.
6. **Consequential provenance only:** persist lineage that can change meaning or auditability; do not canonicalize every function call.
7. **SQLite remains the baseline:** recursive traversal + explicit relational tables + FTS are enough to test the canton-scale model; graph DB/RDF stack remains unjustified.
8. **Bulk/supervised operation is normal:** one or two operators need batch correction/reconciliation without losing per-record attribution.
9. **Standards belong at semantic and interoperability boundaries:** PROV, Akoma, ELI, SKOS, SHACL, IIIF/ALTO can guide mappings without dictating the runtime topology.

## What the source Books collectively reject

- a universal `nodes/edges` graph store;
- one JSON mega-table for every future locator/profile/relation;
- mandatory RDF/OWL/XML internally;
- perfect document typing before ingestion;
- perfect entity resolution before a claim is useful;
- treating AI/model runs as factual evidence;
- silently inferring transitive or co-occurrence relations;
- overwriting source artifacts with processed/public versions;
- enterprise role topology for a one-operator deployment;
- making every operation a permanent event record;
- installing a separate search/graph/vector database before fixtures prove SQLite inadequate.

## Why the Plaza audit matters

Plaza's historical correctness audit is a direct warning: a pipeline may have valid raw evidence, successful processing, and apparently structured output while identity or segmentation is semantically wrong. ActaKit therefore cannot certify a design only because schemas validate or parsers return records. Pre-SQL fixtures must assert identity, evidence location, relation meaning, and correction behavior against the original artifact.

## Research stop condition

The source horizon now covers the pending semantic decisions from multiple directions: formal standards, long-running civic/investigative systems, operator document tools, archival/preservation practice, and SQLite itself. The second-pass gap audit found no missing architectural family large enough to justify another broad sweep before fixtures.

The next evidence step is **fixtures, not SQL and not more generic browsing**. Research resumes only when a fixture exposes a specific unresolved mechanism or a later requirement crosses a documented horizon boundary.
