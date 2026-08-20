---
id: ACTAKIT-BOOK-ZOTERO-001
type: research-source-book
state: complete
authority: evidence
created: 2026-08-20
updated: 2026-08-20
researched_through: 2026-08-20
actakit_baseline: 59bab9de30bbf2aa1eec96dddaee3cded31a9f3a
source_ledger: sources.csv
claim_ledger: claims.csv
---

# Zotero — annotations remain separate from source evidence

## Question

How should analyst annotations/claims remain linked to but separate from source documents?

## Evidence horizon

- **AKS-S027 — Zotero PDF reader / annotations:** Annotations stored separately from PDF; links reopen source context; source file remains intact
- **AKS-S048 — Zotero annotations in database:** Annotations are stored separately from PDFs to avoid file conflicts; export can embed them later

## Source-backed findings

- **AKS-C068:** Separating annotations from source PDFs avoids rewriting evidence while still allowing exact navigation back to source context.

## ActaKit pressure

- **AKS-C068:** Claims/review annotations should remain database records linked to immutable evidence representations, with export embedding only as a derivative output.

## Boundaries / do not cargo-cult

- **AKS-S027:** Bibliographic model is not ActaKit claim model
- **AKS-S048:** Zotero bibliographic/sync model is not ActaKit claim authority

## Disposition

This Book is evidence for the transversal synthesis. It does not independently authorize an architecture or implementation change.
