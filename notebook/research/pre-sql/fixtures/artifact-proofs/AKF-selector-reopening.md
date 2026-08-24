---
id: ACTAKIT-SELECTOR-ARTIFACT-PROOF-001
type: representation-target-artifact-proof
state: pass
authority: evidence
created: 2026-08-21
fixtures: [AKF-001, AKF-005, AKF-013]
---

# Initial selector reopening proof — official TSE artifact

## Preserved public artifact

`alcaldias_pu.pdf` is the Tribunal Supremo de Elecciones publication **“ALCALDÍA
Y VICEALCALDÍAS ESPARZA — PROVINCIA: PUNTARENAS”**, associated with declaratory
resolution 2160-E11-2024 and the 2024–2028 municipal term.

Preserved artifact SHA-256:

```text
192da0e99878aa310a906f381f3bb25c9678934743b1b7563df747e05a8eb4f3
```

The proof targets physical page ordinal **2**, which contains the Esparza row for
Bienvenido Venegas Porras as Alcaldía plus the first and second vice-mayoral rows.
The source PDF is preserved beside this record so the proof does not require a
future network response.

## What was reopened

`pdf_page_quote:v1`:

```json
{
  "page_ordinal": 2,
  "exact": "ALCALDÍA 601420299 BIENVENIDO VENEGAS PORRAS PUSC"
}
```

The exact quote is found on physical page 2 after only the selector contract's
NFC + Unicode-whitespace-collapse normalization. No case folding, punctuation
substitution, dehyphenation, or OCR repair is used.

`text_quote:v1` targets the decoded UTF-8 text derivative. Its stored start/end
are 0-based Unicode-code-point offsets, start-inclusive/end-exclusive, and the
slice must equal the stored exact string byte-for-byte after decoding.

`table_range:v1` targets the table derivative from the same page. Row **6**
(1-based inclusive within that table Representation) reopens exactly as:

```text
ALCALDÍA | 601420299 | BIENVENIDO VENEGAS PORRAS | PUSC | ""
```

## Reproduction

Run:

```text
python notebook/research/pre-sql/fixtures/artifact-proofs/prove_selectors.py
```

Expected leading result:

```text
SELECTOR_ARTIFACT_PROOF=PASS
```

The script also prints hashes of the exact decoded-text and extracted-table
Representation bytes used by the proof. Those derivative hashes are evidence for
this candidate exercise, not a promise that a future parser version must emit the
same formatting; production ProcessRun provenance must identify the actual
extractor/version that created a canonical derivative.

## What this closes

This closes the candidate gate that the initial selector contracts must reopen a
real PDF location, an exact decoded-text span, and a real table row/value range.
Together with `AKF-013-role-assignment.md`, it also closes the exact evidence
locator portion of the real RoleAssignment proof.

It does **not** certify the final production PDF/table parser implementation or
all future selector families.
