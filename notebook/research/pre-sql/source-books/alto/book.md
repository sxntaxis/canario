---
id: ACTAKIT-BOOK-ALTO-DEEP-001
type: research-source-book
state: deep-audited
authority: evidence
created: 2026-08-20
updated: 2026-08-20
researched_through: 2026-08-20
actakit_baseline: 59bab9de30bbf2aa1eec96dddaee3cded31a9f3a
source_ledger: sources.csv
claim_ledger: claims.csv
---

# ALTO

## Question

What can production OCR-layout interchange teach representation/locator design?

## Deep-audit basis

LoC-maintained schema with multiple institutional implementations and reading-order scars.

## Evidence horizon

- **AKS-S034 — ALTO:** OCR text plus page/layout coordinates and processing metadata
- **AKS-S083 — ALTO implementers registry:** Lists production use by Library of Congress, Dutch National Library and others for search/highlighting/article tracking
- **AKS-S084 — ALTO reading-order issue #18:** OCR/XML element order was insufficient; explicit reading order was added because OCR can get flow wrong

## Claim ledger synopsis

- **AKS-C107:** ALTO has production use for OCR layout, highlighting, navigation and article tracking across major institutions. **ActaKit:** Support ALTO as an importable Representation when available instead of inventing a competing OCR-layout format.
- **AKS-C108:** OCR reading order cannot safely be inferred from XML element order; the format added explicit reading-order structures after real use. **ActaKit:** Represent/order text according to explicit parser evidence when available; storage order is not semantic order.

## Bounded transfer

Accept ALTO as optional OCR/layout Representation; preserve explicit geometry/reading order when supplied.

## Do not copy

Do not require ALTO output or infer reading order from XML order.

## Schema pressure / expensive mistake avoided

Representation metadata should capture format/schema version and parser/tool provenance.

## Residual risk

OCR engines and ALTO producers vary; proof fixtures must test real files.

## Closure verdict

Deep-audited for the pre-SQL decision horizon. This Book contributes evidence and constraints; it does not independently authorize schema or implementation changes.
