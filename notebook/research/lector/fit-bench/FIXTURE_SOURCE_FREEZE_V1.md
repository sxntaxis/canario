# Lector fit-bench fixture/source freeze v1

State: **complete for development fixtures D1-D4**
Work: `LECTOR-PRODUCTION-FIT-BENCH`
Baseline: `61ce4daf6364494b534a50060fea14ca3a81c140`

This record freezes source, Representation, benchmark scope, and generic unit identities before
semantic reference construction. It contains no semantic gold, candidate output, model output, or
assessment. D1-D4 are development/reference-design fixtures only.

## Leakage ledger

```text
formal_candidate_output_seen = false
acta160_semantics_inspected = false
semantic_gold_generated = false
production_implementation_authorized = false
```

Acta 160 remains untouched. No H2 holdout is selected. `FID-01` controlled counterexample fixture
remains `PENDING`.

## Frozen fixtures

### D1 — CR-ESPARZA-MINUTES-001

- Role: `development`
- Title: Acta Sesión Ordinaria N.º 161 — 18 May 2026
- Issuer: Municipalidad de Esparza
- Authority/locator: official municipal listing, `https://muniesparza.go.cr/articulo/230/actas-concejo-municipal`; historical download filename `e0256fdf-3714-40f5-ae10-aff18f0ca95e.pdf`
- Retrieval/provenance: reused immutable historical pack; artifact `art_01a03587-66c7-7840-9afb-a22b59447091`; deterministic Representation `rep_01a0358f-0d7b-78bf-b2ae-1c11cc5e1c8b`; ProcessRun `prun_01a0358f-0bc8-71cd-aa15-2b4846e62c96`
- Primary source: 760485 bytes, SHA256 `ffb354c67d8b56ebf265884c820a98fee27015cadaac3ea1011069f7969b8bfd`
- Representation: `text/plain`, 154866 bytes / 151940 chars, SHA256 `02d1578cfc44097c6e5e802880919ff6f7a18bd2105330035959c4cccd467ea1`; Poppler `pdftotext`, recorded processor `poppler.pdf_text` 26.01.0, quality `accept/native_text_present`
- Scope: `full_source_order`; scope SHA256 `25d3bb9dd604109e1d01b7465f11c88a35a2adb26a388a0dd4ef48842cb9c3a5`
- Units: SHA256 `0a2f76f1e737acb82a3430b7d6a7b1394525d9502dc4163298d45e3d6f4cf3de`, 61 units, historical generic inventory
- Language: `es`
- Capability intent: `COV-01`, `ATR-01`, `CTX-01`, `TMP-01`, `REC-01`, `EVD-01`, `LANG-ES-01`
- Source pack: `/mnt/Tokyo/Lab/tmp/sxntax/actakit-lector002-acta161-source-pack.tar.gz`, SHA256 `394a10ef1234a2d7f5f97ce8dbaf595f840987b679258460ace0ac44248a1e41`
- State: `FROZEN`
- Limitations: historically collected; not an independent final holdout; historical semantic worksheets/gold are superseded and not reused.

### D2 — CR-INCOP-CORRESPONDENCE-001

- Role: `development`
- Title: CR-INCOP-PE-0073-2025, dated 2025-03-04
- Issuer: Instituto Costarricense de Puertos del Pacífico
- Authority/locator: official document URL, `https://www.incop.go.cr/wp-content/uploads/general/ModPtoCaldera/DocumentosExpediente/46-CR-INCOP-PE-0073-2025-Sol-Autorizacion%20Ministerio%20Hacienda.pdf`
- Retrieval/provenance: reused immutable historical source pack; retrieved `2026-08-25T20:07:05Z`; collection state `READY`
- Primary source: 407921 bytes, SHA256 `058e6b1b4dbe25431f5914f8ba80d6fe13f53fb55e2971ad86c6c24c0786c207`
- Representation: `text/plain`, 4803 bytes / 4630 chars, SHA256 `81c44e666a763269f97dbe13b11dcb0c91cbbbb42da80e28322c8edcbdaa1549`; deterministic Poppler native-text derivative; historical pack does not record executable version
- Scope: `full_source_order`; scope SHA256 `d0aadc5903154dac5759754c9aacc3322a854746fe9a1d2220f3ec590ee0cc71`
- Units: SHA256 `c5a41b4b7a01ab5dd56a33d08d224d3a66cf0aa679664629c41cf98535229aca`, 17 units
- Language: `es`
- Capability intent: `ATR-01`, `SCP-01`, `MOD-01`, `CTX-01`, `EVD-01`, `LANG-ES-01`
- Source pack: `/home/sxntax/Downloads/canario-lector002-capability-fixtures/CR-INCOP-CORRESPONDENCE-001-source-pack.tar.gz`, SHA256 `235bc6590e19eeb7ffadccd60a535b9ecbeb67c4b87b6db6f268d1b4c746cc1b`
- State: `FROZEN`
- Limitations: exact historical Representation identity is retained; processor version was not recorded in the historical manifest; no semantic interpretation, truth rows, or tested extractor output.

### D3 — CR-ESPARZA-PROCUREMENT-REGULATION-001

- Role: `development`
- Title: Reglamento interno de contratación pública de la Municipalidad de Esparza y del Comité Cantonal de Deportes y Recreación de Esparza
- Issuer: Municipalidad de Esparza
- Authority/locator: official municipal current download, `https://muniesparza.go.cr/files/folder/afd068ff-c888-4a53-8191-5caab152ee3d.pdf`, listed at `https://muniesparza.go.cr/articulo/515/reglamentos-municipales`
- Retrieval/provenance: HTTP 200, `application/pdf`, retrieved `2026-08-27T21:30:22Z`; PDF creation date 2025-04-10; official La Gaceta N.º 69, 10 April 2025; Articles 1–54 verified
- Primary source: 653922 bytes, SHA256 `d6aed7b952ac8b6b1770dcbf957471390016507ef8ee2c98553f52ba5f579c59`
- Representation: `text/plain`, 71816 bytes / 70202 chars, SHA256 `3a32786f91a312b2dadae8e7e8af9349396886ca30bfc22d4dccbeb705799d28`; `pdftotext -enc UTF-8`, Poppler `26.01.0`; 11 pages/form-feed representation
- Scope: exact bounded subdocument, char offsets `[939, 66065)`, byte offsets `[972, 67591)`, pages 1–11; start anchor `MUNICIPALIDAD DE ESPARZA\nHabiéndose cumplido`; end anchor `1 vez.—( IN2025938982 ).`; selected text SHA256 `676e7b78bddc8f928481e95bcd15816a0cb827e5e9ae71e3226f4f709fef6d81`
- Units: SHA256 `b744773c22ee862904052db0ee19bcbdf3674d5935016054795ad38705a87253`, 37 units, generic structure-only partition
- Selection: `exact_bounded_subdocument`; preceding/following unrelated publication text is outside scope; no semantic importance heuristic used
- Language: `es`
- Capability intent: `SCP-01`, `MOD-01`, `TMP-01`, `CTX-01`, `EVD-01`, `LANG-ES-01`
- Source pack: `/home/sxntax/Downloads/canario-lector-fit-bench-f2-source-packs/D3-CR-ESPARZA-PROCUREMENT-REGULATION-001.tar.gz`, SHA256 `abafceed74ace547859ae91f72c07ce4b9d85a01792127a80cb80b555133f047`
- State: `FROZEN`
- Limitations: municipal download is an official La Gaceta extract with adjacent issue material; the benchmark scope is only the deterministic regulation subdocument. January 2025 stale-version publication was excluded.

### D4 — CR-CGR-SANTA-ANA-PROCUREMENT-AUDIT-001

- Role: `development`
- Title: Informe de auditoría sobre la gestión de contratación pública en la Municipalidad de Santa Ana; Informe n.º DFOE-LOC-IAD-00011-2024, 28 June 2024
- Publisher: Contraloría General de la República
- Authority/locator: official PDF, `https://cgrfiles.cgr.go.cr/publico/docs_cgr/2024/SIGYD_D/SIGYD_D_2024012846.pdf`
- Retrieval/provenance: HTTP 200, `application/pdf`, retrieved `2026-08-27T21:30:22Z`; `pdfinfo` reports 28 pages and 1911828 bytes
- Primary source: 1911828 bytes, SHA256 `587e4ba2ca65c4a3f453471434ca69b41ba71fe59ae64897590b1fc6c44c97fe`
- Representation: `text/plain`, 61507 bytes / 60155 chars, SHA256 `324dfd50e4cee6619bf0f8cbce223004bc34bd9d980cad90823f3a195111893d`; `pdftotext -enc UTF-8`, Poppler `26.01.0`; 28 pages/form-feed representation
- Scope: `full_source_order`, char/byte offsets `[0, 60155)` / `[0, 61507)`, pages 1–28; scope SHA256 `324dfd50e4cee6619bf0f8cbce223004bc34bd9d980cad90823f3a195111893d`
- Units: SHA256 `b4c45ebccf7bfc4ec02d902aaa96b7f968bcc07719b40ceef28c79985bf1c5b4`, 260 units, generic structure-only partition
- Language: `es`
- Capability intent: `COV-01`, `ENT-01`, `ATR-01`, `SCP-01`, `TMP-01`, `QTY-01`, `CTX-01`, `REC-01`, `EVD-01`, `LANG-ES-01`
- Source pack: `/home/sxntax/Downloads/canario-lector-fit-bench-f2-source-packs/D4-CR-CGR-SANTA-ANA-PROCUREMENT-AUDIT-001.tar.gz`, SHA256 `eb729446edb1c698cc0ea3ecc6e92a1cf3cf217a24bea6320c744e919699f7ae`
- State: `FROZEN`
- Limitations: native extraction artifacts are retained as evidence; no semantic correction or section sampling applied.

## Generic unit rule

D3 and D4 use `partition_source()` from `notebook/implementation/lector_002_benchmark.py` at baseline
`61ce4daf6364494b534a50060fea14ca3a81c140`. The inspected semantics are page separators, blank-line
block starts and bounded continuation splits only; no institution, acta, legal keyword or semantic
attention heuristic is used.

## Next gate

F3: human-approved semantic reference construction. Thresholds remain unfrozen, and formal A0–A5
execution remains prohibited.
