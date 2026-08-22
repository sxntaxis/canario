---
id: ACTAKIT-BOOK-BROAD_PARSERS-001
type: research-source-book
state: research-complete-for-selection-gate
authority: evidence
created: 2026-08-21
updated: 2026-08-21
researched_through: 2026-08-21
actakit_baseline: 02b5c3c9efad9207397c077d53aafac9f206cc86
source_ledger: sources.csv
claim_ledger: claims.csv
---

# Broad document parsers: Apache Tika and Unstructured

## Question

What do mature broad-format parsing systems teach about format coverage and strategy routing?

## Audit basis

Current supported-format and partition-strategy documentation.

## Evidence horizon

- **BRD-S001 — Apache Tika 3.2.3 supported formats:** Broad detection/extraction across office, PDF, markup, archives and media metadata. **Boundary:** Tika emphasizes broad parsing and metadata rather than page-layout fidelity.
- **BRD-S002 — Apache Tika project:** Mature Java parser ecosystem under Apache project governance. **Boundary:** Java process/runtime cost is an ActaKit deployment consideration, not a defect in Tika.
- **BRD-S003 — Unstructured open-source partitioning:** Partition functions route formats and expose auto/fast/hi_res/ocr_only PDF strategies. **Boundary:** Product and hosted features may exceed open-source local behavior.

## Claim ledger synopsis

- **BRD-C001:** Broad format detection/extraction is a solved problem family; ActaKit need not hand-write every office/archive parser. **ActaKit:** Prefer mature libraries or converters for common formats.
- **BRD-C002:** Unstructured already formalizes fast/high-resolution/OCR routing as different strategies. **ActaKit:** Escalation is established practice; ActaKit should own a civic-specific policy rather than inventing the idea.
- **BRD-C003:** Broad parser breadth and high-fidelity document understanding are different optimization targets. **ActaKit:** A catch-all parser can be fallback/detector without becoming the highest-quality processor for every format.
- **BRD-C004:** A Java-centric runtime would materially enlarge ActaKit deployment if Tika were core. **ActaKit:** Keep Tika as reference/fallback candidate unless Civic Bench demonstrates unique value.

## Bounded transfer

Adopt the lesson: route by format and quality; reuse mature broad parsers where they outperform bespoke code. Evaluate rather than default to a broad-parser runtime.

## Do not import

Do not duplicate Unstructured/Tika abstractions wholesale or use format breadth as proof of extraction quality.

## Residual risk / unresolved question

Need benchmark on Office/HTML/CSV fixtures to decide whether Docling alone covers the useful breadth.

## Closure verdict

**reference-and-benchmark** for the WP4C selection horizon. This Book is evidence, not implementation authorization.
