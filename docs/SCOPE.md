# Canario scope invariant

Canario is an evidence-first civic-record system, not a municipal-minutes product and not
a finite taxonomy of civic document types.

## Universal boundary

```text
Source -> Artifact -> Representation -> Lector -> Fichero
```

`Artifact` preserves acquired evidence. `Representation` expresses a processable view of
that evidence without erasing its medium. A source may be a PDF, office document, webpage,
image, table/dataset, audio/video recording, archive/container, or another future format.

Generic core code may depend on typed contracts such as media type, Representation kind,
scope, evidence locator, custody and provenance. It may **not** depend on incidental layout,
vocabulary, or a supposedly exhaustive document-genre enum.

A hybrid source can legitimately yield several typed Representations. Canario does not need
a single globally correct answer to "what kind of document is this?" before preserving and
processing its evidence.

## Specialization boundary

Source/document/language-specific logic is allowed when useful, but it must be visibly
scoped as an adapter/profile. Examples include an Esparza CMS connector, a Costa Rican
municipal-minutes layout profile, or a Spanish civic attention helper. Such a profile may
improve processing; it cannot define what the generic core means by an Artifact, Claim,
evidence, completeness or review.

Specializations are capabilities/helpers, not required members of a universal document
classification tree.

## Evidence follows the medium

- text: exact quote + character/context locator;
- table/data: exact row/cell/path + observed values;
- image/PDF: page/region/visual locator as applicable;
- audio/video: start/end time, with transcript anchor when available.

A transcript is a derivative Representation, not a replacement for the original recording.

## Benchmark law

No finite corpus can certify "all document types" or universal future support. LECTOR-002
therefore measures a declared, revisable matrix of **capabilities and failure modes** across
heterogeneous real fixtures.

Fixture genre labels such as `institutional_minutes`, `audit_report`, `correspondence` or
`contract` are descriptive `benchmark_archetypes` only. They are not Canario Artifact
classes, need no exhaustive registry and may overlap.

The executable benchmark gate is capability coverage: Representation fidelity, typed
evidence reopening and semantic stress dimensions. Verification follows the nature of the
capability: structural Representation/evidence properties are proved deterministically from
frozen bytes and locator reopening; semantic-understanding capabilities require independent
human gold plus adjudication. Human review is not used to certify facts that machines can
prove exactly. New real-world formats should extend the matrix when they expose a materially
new failure mode rather than forcing the product into an ever-growing document-type enum.

The benchmark must always state:

```text
certification_scope = declared_capabilities_only
universal_support_claimed = false
```

Acta 161 is retained as the first real semantic fixture because it is frozen and useful. It
has no authority to introduce acta-specific segmentation rules or to define the universe of
records Canario can accept.
