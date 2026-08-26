# LECTOR-002 Typed Evidence Design

## Fixture audit

The frozen workbook is an XLSX with sheets, in order, `Egresos MD 1`, `Egresos MD 2`,
and `Egresos MD 3`. Their dimensions are `A1:C109`, `A1:C92`, and `A1:C10`.
All sheets are visible, have no merged ranges, and contain no formulas. The used
cells contain strings and numbers; blank cells remain distinguishable from absent
rows in the materialized rectangular sheet matrix. The official CSV is not a safe
semantic substitute because it discards workbook sheet identity and cell typing.

The media is an MP4 container with H.264 video (1280x720, 30000/1001 video timebase)
and AAC stereo audio (44.1 kHz). The retained format duration is 120.163265 seconds;
the audio stream is the longer stream. Canonical evidence uses integer microseconds,
half-open structurally bounded spans, and the exact retained-byte SHA-256. The media
processor records this metadata; Lector does not invoke ffprobe.

## Contract decisions

| Area | Classification | Decision |
| --- | --- | --- |
| `table_range:v1` | existing implementation gap | Keep the selector name as the bounded Lector form of the architecture-level `spreadsheet:v1` locator. Add sheet identity and typed cell values when reopening the structured-table Representation. |
| Table Representation | underspecified | Add a deterministic `canario.structured_table.v1` JSON shape with ordered sheets, dimensions, merged ranges, cell addresses, data types, formulas, and typed values. |
| Formula cells | existing contract sufficient after clarification | Formula text is preserved as a formula typed value. No cached value is invented or recalculated. |
| `media:v1` | missing runtime contract | Add integer `start_us`, `end_us`, trusted `duration_us`, and source SHA-256. Optional transcript anchors carry a complete target/quote/offset tuple. |
| Cross-Representation evidence | existing implementation gap | ProcessRun input targets may include explicitly scoped ancestor/descendant targets on the same Artifact. Evidence reopens against the target Representation bytes, never against the semantic input bytes by substitution. |
| SQLite schema | sufficient | `process_run_inputs` already stores `(representation_id, representation_target_id)` and evidence links already reference targets. No migration is required. |

## Boundary and lineage

The semantic invocation still receives exactly one source byte stream: the requested
Representation. Related targets are immutable scope snapshots, not archive authority.
For a transcript extractor to cite the parent recording, the media target must be
explicitly included in the ProcessRun input scope and must resolve to the same Artifact
through the retained parent/child lineage. Unrelated Artifacts and sibling lineages
are rejected. LectorWriter obtains target bytes only through the canonical archive and
reopens each target with its registered locator.

A later transcript is therefore a derivative Representation. Its text quote target
and the original recording's `media:v1` target remain separate evidence links. A media
anchor may reference a transcript target only when that target is complete and belongs
to the same retained lineage; this substrate does not generate transcript content.

## Benchmark boundary

The table and media evaluators prepare blank worksheets from the same canonical typed
Representation/locator contracts. Table units are sheet rows. Media units are uniform
ten-second windows covering the full retained duration; this is mechanical review
partitioning, not semantic completeness. Truth, candidates, assessments, and semantic
model calls remain empty/zero. The corpus represents the two collected capabilities but
the declared capability gate remains false until the human-approved semantic reference and adjudication exist.

## Dependency

`openpyxl==3.1.5` is pinned as an MIT runtime dependency. It materially avoids a
fragile hand-written Office Open XML parser and preserves workbook sheet, formula,
merge, and typed-cell semantics at the processor boundary.

## Post-checkpoint hardening review

Review of the first implementation checkpoint exposed four gaps before exact-runtime
certification. They are corrected in the follow-up commit rather than being deferred into
certification:

1. **Processor provenance must be observed, not asserted.** `MediaInspectionProcessor`
   now probes the selected `ffprobe` executable and records its actual version instead of
   hard-coding `ffprobe-8.1.2`.
2. **The media index must be deterministic.** `ffprobe`'s temporary `format.filename` is
   stripped from the canonical derivative, decimal duration is converted to integer
   microseconds with explicit decimal rounding, and repeated processing of identical bytes
   is regression-tested byte-for-byte.
3. **Media benchmark duration is trusted evidence, not a CLI assertion.** Typed media
   worksheet preparation/scoring now requires a canonical `canario.media_index.v1` whose
   `source_sha256` matches the retained media bytes; selectors must use that exact trusted
   digest and duration.
4. **Typed modes need real scorers, not preparation-only helpers.** `score-typed` now uses
   the production `TargetRegistry` plus runtime locator reopening for both `table_range:v1`
   and `media:v1`, then computes the same human-adjudication metrics as the text scorer.

The review also tightened typed-cell payload validation, media span reopening, and media
index ownership: a `media:v1` target is bound to an inspection derivative whose direct
parent is the exact targeted media Representation, rather than whichever media index was
most recently created for the Artifact.

## Exact-runtime certification follow-up: derived media duration integrity

The first exact-runtime certification attempt correctly blocked because a media-index
copy with an altered top-level `duration_us` was still accepted when its retained-source
digest remained correct. The flaw was not in span bounds; it was that `duration_us` had
been treated as an independently trusted field even though the canonical index also
retains ffprobe's `format.duration`.

The media-index contract now validates one shared invariant before benchmark or
Workbench use:

```text
duration_us == decimal_to_integer_microseconds(probe.format.duration)
```

The same validator also requires the exact retained-source SHA-256, canonical deterministic
JSON bytes, the expected top-level schema, and absence of ffprobe's execution-path
`format.filename`. `MediaInspectionProcessor` self-validates its derivative, the Workbench
validates the retained direct-child index before accepting `media:v1`, and LECTOR-002
worksheet preparation/scoring use that same validator. A changed top-level duration can no
longer become trusted merely because the media digest still matches.

This remains structural evidence: matching duration/digest proves the cited interval is
bounded to the inspected retained recording, not that any proposition is semantically
present in that interval.
