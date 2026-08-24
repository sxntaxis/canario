# Canario scope invariant

Canario is an evidence-first civic-record system, not a municipal-minutes product.

## Universal boundary

```text
Source -> Artifact -> Representation -> Lector -> Fichero
```

`Artifact` preserves acquired evidence. `Representation` expresses a processable view of
that evidence without erasing its medium. A source may be a PDF, office document, webpage,
image, table/dataset, audio/video recording, or another future format.

Generic core code may depend on typed contracts such as media type, Representation kind,
scope, evidence locator, custody and provenance. It may **not** depend on incidental layout
or vocabulary of the first source family.

## Specialization boundary

Source/document/language-specific logic is allowed when useful, but it must be visibly
scoped as an adapter/profile. Examples include an Esparza CMS connector, a Costa Rican
municipal-minutes layout profile, or a Spanish civic attention helper. Such a profile may
improve processing; it cannot define what the generic core means by a document, Claim,
evidence, completeness, or review.

## Evidence follows the medium

- text: exact quote + character/context locator;
- table/data: exact row/cell/path + observed values;
- image/PDF: page/region/visual locator as applicable;
- audio/video: start/end time, with transcript anchor when available.

A transcript is a derivative Representation, not a replacement for the original recording.

## Benchmark law

No single document type, municipality, language pattern, or modality can certify a broad
Canario extractor. LECTOR-002 therefore uses a heterogeneous reference corpus. Each case
may have a typed evaluator, and broad certification remains blocked until the required case
classes and evidence modes are independently gold-frozen and adjudicated.

Acta 161 is retained as the first real semantic case because it is frozen and useful. It has
no authority to introduce acta-specific segmentation rules into the corpus harness.
