---
id: ACTAKIT-BOOK-DOCUMENTCLOUD-DEEP-001
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

# DocumentCloud

## Question

What do newsroom document workflows teach about OCR, redaction and publication?

## Deep-audit basis

Production document platform documents irreversible redaction and derived/public representation behavior.

## Evidence horizon

- **AKS-S028 — DocumentCloud API / notes:** Bulk upload/process/OCR/search; page/region notes; original hash; irreversible redaction warning
- **AKS-S049 — DocumentCloud FAQ:** Original saved separately; OCR/text extraction; forced OCR/redaction can destroy metadata/text layer; private/public states differ
- **AKS-S050 — DocumentCloud Add-Ons:** Bulk metadata/tag/reprocess/visibility operations are first-class; redaction failure detection is explicit
- **AKS-S089 — DocumentCloud API redaction semantics:** Redaction flattens/reprocesses pages, strips metadata and is irreversible; users are advised to retain originals

## Claim ledger synopsis

- **AKS-C030:** Irreversible redaction/modification requires preserving original separately if provenance matters. **ActaKit:** Public/redacted representation must not overwrite custody artifact.
- **AKS-C059:** Public publishing and internal custody have different safety requirements. **ActaKit:** Publication/redaction remains Output/Export policy, not mutation of original evidence.
- **AKS-C069:** OCR, page text and redaction can alter or replace derived/public representations while the original needs separate custody if provenance matters. **ActaKit:** Treat OCR/redacted/public copies as Representations or Outputs, never silent replacement of the acquired Artifact.
- **AKS-C070:** High-volume document work benefits from bulk processing/tagging/review surfaces, while source-context notes can remain page/region-specific. **ActaKit:** Design operator actions as bulk-capable from the start, but preserve per-claim/per-relation evidence location.
- **AKS-C112:** Redaction is destructive to the processed copy and strips metadata; retaining the original is explicitly recommended. **ActaKit:** Redaction/publication creates a derivative Representation/Output and never mutates the custody Artifact.

## Bounded transfer

Keep original custody artifact; redaction/OCR/page edits create derivatives; operator surfaces can be bulk-capable.

## Do not copy

Do not copy cloud/service topology or make publishing authority implicit.

## Schema pressure / expensive mistake avoided

Public/redacted outputs are separate from source Artifact; locators bind to the specific representation.

## Residual risk

Cloud product behavior is evidence for workflow scars, not deployment architecture.

## Closure verdict

Deep-audited for the pre-SQL decision horizon. This Book contributes evidence and constraints; it does not independently authorize schema or implementation changes.
