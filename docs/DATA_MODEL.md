---
id: ACTAKIT-DATA-001
kind: conceptual-data-model
state: proposed-for-acceptance
created: 2026-08-20
authority: architecture-proposal
summary: Table-oriented conceptual model separating civic document semantics from evidence representation and locator semantics.
related:
  - ACTAKIT-ARCH-001
  - ACTAKIT-CONTRACTS-001
  - ACTAKIT-IMPLEMENTATION-001
---

# Conceptual Data Model

## Purpose

This document makes the proposed architecture concrete enough to review before
writing SQLite migrations. It is **not** the final SQL schema. It freezes the
meaning and relationships that the first schema must preserve.

The central rule is:

```text
what a civic document means
!= how its bytes are represented
!= how evidence is located inside that representation
```

A new or malformed document type must not cause evidence loss. Conversely,
being able to preserve a file does not mean the system can approve claims from
it before a reviewer has a verifiable locator.

## Core Shape

The model is intentionally not one linear pipeline. Evidence custody and civic
interpretation meet through explicit links:

```text
Source -> SourceRun -> SourceCapture -> Artifact -> Representation
                                      \-> CivicDocument

CivicDocument -> DocumentPart
CivicCollection -> CollectionMembership -> CivicDocument

Claim -> ClaimRevision -> EvidenceLink
                           |-> Representation + typed locator
                           |-> CivicDocument (context, optional)
                           \-> DocumentPart (context, optional)

ReviewDecision -> immutable subject revision/hash
```

A single artifact may contain more than one civic document. A civic document may
have more than one representation. Neither relationship changes the immutable
source bytes.

## Table Families

These names are illustrative but deliberately close to likely SQLite tables.

| Table family | Important fields | Why it exists |
|---|---|---|
| `sources` | `source_id`, issuer/owner, authority class | Stable identity for a source family. |
| `source_policies` | `source_id`, policy revision, allowed hosts/types, retention/privacy rules, status | Human-approved acquisition/disclosure rules. |
| `source_runs` | run ID, pinned policy revision, scope, times, outcome, checkpoint | One bounded inspection attempt. |
| `source_captures` | run ID, source-local ID, requested/final URI, retrieval time, declared metadata, artifact/failure | Preserves each observed resource and provenance. |
| `artifacts` | artifact ID, SHA-256, bytes, detected media type, archive locator, custody state | Immutable acquired bytes. |
| `representations` | representation ID, parent artifact/representation, representation kind, digest, media type, generator/process, quality | Original, extracted text, OCR, table, transcript, redacted derivative, etc. |
| `civic_documents` | document ID, normalized/display identity, normalized type, subtype, profile, type confidence/basis, issuer, date object, language, visibility, revision | Reviewed civic meaning independent of file format. |
| `document_source_observations` | document ID, source capture ID, supplied title/type/identifier/date text, bounded metadata hash | Preserves exactly how each source described the document; conflicting labels can coexist. |
| `document_profile_data` | document ID, `profile_schema` such as `acta:v1`, validated profile payload | Type-specific fields without a new SQL table for every bureaucratic label. |
| `document_anchors` | document ID, representation ID, typed locator | Shows which region/representation constitutes that civic document when one artifact contains several documents. |
| `document_parts` | part ID, document ID, parent part, kind, ordinal, title | Optional semantic structure inside one document. |
| `document_part_anchors` | part ID, representation ID, typed locator | Locates a semantic part in one or more representations. |
| `civic_collections` | collection ID, kind, title/external ID, issuer/context, revision | Groups documents when the civic object is a case/file/package rather than one document. |
| `collection_memberships` | collection ID, document ID, relation, order, provenance/review | E.g. an `expediente` containing oficio, informe, resolución and annexes. |
| `process_runs` | process ID, exact inputs/hashes, executor/model/prompt/config versions, outputs, diagnostics | Makes extraction/OCR/AI/import/render occurrences attributable. |
| `proposals` | proposal ID, process/human origin, proposed subject/value, status | AI/human candidates have no canonical effect before review. |
| `claims` | stable claim ID, current revision pointer/lifecycle | Stable identity of one proposition across correction. |
| `claim_revisions` | claim ID + revision, exact text, classification, temporal scope, attribution, sensitivity, epistemic state, hash | Corrections preserve history instead of overwriting prose. |
| `evidence_links` | claim revision, relation, representation ID, locator kind/version/payload, optional document/part context, state | Exact support/contradiction/context/quotation/mention. |
| `review_decisions` | subject type/ID/revision/hash, reviewer, role, decision, rationale, time | Human authority attaches to the exact thing reviewed. |
| `episodes` / `episode_claims` | episode fields + included claim revisions | Reader-oriented grouping over approved claims. |
| `hilos` / `hilo_memberships` | topic identity + reviewed episode/claim relation | Thematic projection without duplicating canonical content. |
| `corrections` | subject, prior/new revision, correction kind, reason, authority | Explicit supersession/retraction/redaction lineage. |
| `publication_snapshots` | immutable record/revision set, audience/tier, build hashes, approvals | Citable release state. |
| `operation_receipts` | operation ID, canonical request hash, result, actor/role | Replay safety and mutation audit. |

The final schema may merge small tables or split hot paths after measurement, but
it must not collapse the semantic boundaries above merely to reduce table count.

## Civic Document Typing

Document typing has three separate observations:

```text
source_supplied_type   what one attributable source observation called it
normalized_type        ActaKit's reviewed broad civic type
profile_schema         optional domain-specific structure
```

Example:

```yaml
source_supplied_type: "Informe especial"
normalized_type: informe
subtype: auditoria
profile_schema: informe:v1
type_confidence: high
type_basis: human_review
```

Each source label is preserved in its source observation even when another
source disagrees or the reviewed classification differs. Reclassification
creates a new document revision/decision; it does not rewrite source history.

### Initial normalized vocabulary

The initial broad vocabulary is intentionally small:

```text
acta, agenda, convocatoria, acuerdo, resolucion, oficio, informe,
dictamen, presupuesto, plan, reglamento_ordenanza, aviso_publico,
correspondencia, comunicado_prensa, contrato, dataset, grabacion, otro
```

Before review, `normalized_type` may remain `unknown`. `otro` is the reviewed
safe fallback, not an error. It requires the source label when available and
review before type-specific assumptions are made.

A new profile is justified only when the parent type cannot cleanly express
required invariants, validation, or behavior. Different bureaucratic titles do
not automatically deserve different tables or profiles.

### Profiles

Profiles are versioned validated payloads, for example:

```text
acta:v1      session body/type/date/number, articles/items, agreements
informe:v1   reporting body, covered period, findings/recommendations
oficio:v1    sender, recipient, office number, subject, references
presupuesto:v1 fiscal period and budget-specific descriptors
```

Common, frequently queried semantics remain columns on `civic_documents`.
Profile-only fields live in a validated versioned payload initially. A field is
promoted to normalized relational structure only when real query/integrity needs
justify it.

## Collections and Hybrid Material

An `expediente` is normally a collection, not one giant document:

```text
expediente
  -> oficio
  -> informe
  -> resolución
  -> plano/anexo
```

Therefore `expediente` and a procurement/`contratacion` process belong
initially to `civic_collections`, not the `CivicDocument` type list. Other
collection kinds may include a session packet or dossier. Individual notices,
decisions, contracts, reports, and annexes inside them remain documents.

A PDF that physically concatenates several documents does not force them into
one semantic document. One artifact/representation can be anchored to several
`CivicDocument` records. `DocumentPart` is reserved for meaningful internal
parts of one document, not used as a substitute for recognizing embedded
standalone documents.

## Typed Evidence Locators

Locator semantics follow the **representation**, not the civic document type.
An acta can be PDF, HTML, scan, transcript, or table; each uses the locator that
matches the representation actually cited.

Every `EvidenceLink` includes:

```yaml
claim_revision: clm_...@3
relation: supports | contradicts | contextualizes | quotes | mentions
representation_id: rep_...
locator_kind: pdf | text | spreadsheet | image | media | json | xml
locator_version: 1
locator_payload: {...validated for kind/version...}
document_id: doc_...       # optional context
document_part_id: part_... # optional context
```

The locator payload is versioned and validated. It is **not** arbitrary JSON.

### Initial locator contracts

| Locator | Required anchor | Stronger verification when available |
|---|---|---|
| `pdf:v1` | page/folio; region when text is unavailable | exact quote and/or article/item labels when actually present |
| `text:v1` | start/end offsets in a named hashed text representation | exact quote + prefix/suffix |
| `spreadsheet:v1` | sheet/table + cell/range or row/header coordinates | quoted values + value hash |
| `image:v1` | image/page + bounding region | linked OCR/text representation and quote |
| `media:v1` | start/end time | transcript representation + text locator |
| `json:v1` | JSON Pointer/path | observed value/value hash |
| `xml:v1` | XPath or equivalent stable path | observed value/value hash |

`article`, `item`, `agreement`, `budget line`, etc. are **semantic structure
labels**, not universal locator requirements. They may strengthen a locator or
identify a `DocumentPart`, but the core evidence model does not assume every
source has them.

### Unknown representation

Unknown/malformed bytes may still be preserved as an artifact and source
capture. They do not need a new civic type to be retained.

However, a direct factual claim cannot become accepted until at least one
supporting representation has a locator contract that a reviewer can verify.
This separates safe custody from evidentiary sufficiency:

```text
can preserve it != can cite it well enough to approve a factual claim
```

## Examples

### Acta PDF

```yaml
document:
  normalized_type: acta
  profile_schema: acta:v1
evidence_link:
  representation: rep_pdf_180
  locator_kind: pdf
  locator_payload:
    page: 14
    article: IV
    item: 3
    exact_quote: "..."
```

### Budget spreadsheet

```yaml
document:
  normalized_type: presupuesto
  profile_schema: presupuesto:v1
evidence_link:
  representation: rep_xlsx_2027
  locator_kind: spreadsheet
  locator_payload:
    sheet: "Programa II"
    row: 143
    columns: ["Partida", "Monto"]
    quoted_values:
      Partida: "5.02.01"
      Monto: "₡25.800.000"
```

### Mislabelled source document

```yaml
source_supplied_type: "Informe"
normalized_type: resolucion
type_confidence: high
type_basis: human_review
```

Both observations remain attributable.

### New unknown civic type

```yaml
source_supplied_type: "Certificación de disponibilidad presupuestaria"
normalized_type: unknown
profile_schema: generic:v1
```

The artifact and representations can be preserved before classification. After
review, the document may become `otro` or a later recognized type. Claims,
evidence links, and review machinery do not require a schema migration; a future
`certificacion:v1` profile can be introduced without changing the original
artifact or laundering prior classification.

## Schema Gate Before SQLite

Before Work Package 3 writes a migration, the accepted SQL design must show for
each table/constraint:

- primary and foreign keys;
- immutable versus revisioned fields;
- uniqueness/idempotency constraints;
- nullable fields and why;
- locator payload validation path;
- delete/restrict behavior (no implicit cascade that destroys evidence history);
- indexes justified by actual first-slice queries;
- how unknown document/representation types fail safely;
- how a claim revision resolves to a fixed representation and artifact digest.

Architecture acceptance therefore does not authorize improvising the schema.
The conceptual model is accepted first; SQL is reviewed as the next concrete
boundary before persistent implementation.
