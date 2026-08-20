---
id: ACTAKIT-BOOK-DOCUMENTCLOUD-001
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

# DocumentCloud — source-context review, OCR, regions, and redaction scars

## Question

What newsroom-scale document handling patterns transfer to civic evidence review?

## Evidence horizon

- **AKS-S028 — DocumentCloud API / notes:** Bulk upload/process/OCR/search; page/region notes; original hash; irreversible redaction warning
- **AKS-S049 — DocumentCloud FAQ:** Original saved separately; OCR/text extraction; forced OCR/redaction can destroy metadata/text layer; private/public states differ
- **AKS-S050 — DocumentCloud Add-Ons:** Bulk metadata/tag/reprocess/visibility operations are first-class; redaction failure detection is explicit

## Source-backed findings

- **AKS-C030:** Irreversible redaction/modification requires preserving original separately if provenance matters.
- **AKS-C059:** Public publishing and internal custody have different safety requirements.
- **AKS-C069:** OCR, page text and redaction can alter or replace derived/public representations while the original needs separate custody if provenance matters.
- **AKS-C070:** High-volume document work benefits from bulk processing/tagging/review surfaces, while source-context notes can remain page/region-specific.

## ActaKit pressure

- **AKS-C030:** Public/redacted representation must not overwrite custody artifact.
- **AKS-C059:** Publication/redaction remains Output/Export policy, not mutation of original evidence.
- **AKS-C069:** Treat OCR/redacted/public copies as Representations or Outputs, never silent replacement of the acquired Artifact.
- **AKS-C070:** Design operator actions as bulk-capable from the start, but preserve per-claim/per-relation evidence location.

## Boundaries / do not cargo-cult

- **AKS-S028:** Hosted newsroom platform and publication model are not ActaKit architecture
- **AKS-S049:** Hosted newsroom account/publication model is not ActaKit core
- **AKS-S050:** Add-on/plugin ecosystem should not be copied into 1.0 core

## Disposition

This Book is evidence for the transversal synthesis. It does not independently authorize an architecture or implementation change.
