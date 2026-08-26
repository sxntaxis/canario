# AGENTS.md

> **Documentación para asistentes de IA — canario v1.0**
>
> Antes de trabajar con este proyecto, leé este archivo completo.
> Contiene todo lo que un modelo de lenguaje necesita para configurar,
> ejecutar y extender el pipeline correctamente.

---

## Product identity and scope invariant

**Canario is not an acta processor.** The historical municipal-acta workflow is the
first mature deployment and a useful fixture family, but it is not the architectural
boundary. The durable product ingests heterogeneous public/civic evidence, including
PDF/DOCX/HTML, reports, correspondence, budgets, contracts, regulations, datasets,
images, audio/video recordings, and derived transcripts or structured Representations.
Unknown future record types must remain possible.

The generic path is:

```text
source terrain / file / recording / dataset
-> Artifact custody
-> one or more typed Representations
-> Lector semantic proposals
-> Fichero
```

Hard rules for agents/contributors:

- never put acta vocabulary/layout (`ARTÍCULO`, `SE ACUERDA`, municipal speaker roles,
  session closing formulas, etc.) into a generic core boundary or generic benchmark;
- source/document-format heuristics may exist only in an explicitly named adapter/profile
  and may not silently become universal truth, completeness, or segmentation rules;
- a benchmark over one record class cannot certify a broad Canario capability; broad
  certification requires a heterogeneous reference corpus;
- text offsets are not a universal evidence model. Tables keep typed row/cell evidence;
  recordings require timed media evidence, normally strengthened by a transcript anchor;
- do not flatten audio/table/image evidence into plain text merely because the first
  implementation knows how to score text; missing modality support is a capability gap to
  implement, not a reason to redefine the source;
- `machine-only` remains a valid durable production state. Human gold/adjudication is an
  engineering cost for representative benchmark fixtures, not a production review queue.

The product was renamed from **ActaKit** to **Canario** during pre-release specifically
to remove an accidental minutes-only framing. Historical contract/fixture IDs such as
`ACTAKIT-ARCH-001` and `AKF-*` retain their identifiers for provenance and stable
reference; the legacy prefix does **not** define current product scope.

## Política de pre-release y compatibilidad de schema

**Canario está en pre-release. No hay usuarios ni instalaciones públicas cuya base
de datos deba conservar compatibilidad entre commits.** Hasta que el proyecto
declare explícitamente una frontera de compatibilidad (como mínimo una release
Beta pública, o una declaración equivalente en `docs/STATUS.md`), el schema
SQLite se **rebaselina en `0001`** cuando el diseño cambia.

Reglas para agentes y contribuidores durante pre-release:

- no crear `0002`, `0003`, ... para preservar bases de desarrollo desechables;
- editar la especificación/SQL de `0001` cuando el cambio sea correcto para el
  producto, y volver a pasar freeze review + certificación del runtime;
- una base local de desarrollo puede recrearse desde cero; no es autoridad de
  compatibilidad;
- no añadir compatibilidad legado, migraciones puente ni transforms de upgrade
  solo por conservar estados pre-release;
- `application_id` permanece estable; `user_version` puede seguir en `1` mientras
  el baseline canónico siga siendo `0001`;
- la historia incremental de migraciones empieza **solo después** de la frontera
  de compatibilidad pública. Desde ese punto, las bases de usuarios reales deben
  poder actualizarse sin reset destructivo.

Cambiar `0001` no significa saltarse los gates: cualquier cambio de SQL sigue
requiriendo la revisión/certificación que corresponda antes de convertirse en
autoridad de producción.

## Ingress / Source Connector architecture

The current `scripts/scrape_actas.py` is a **legacy/source-specific adapter**, not
the architectural template for acquisition. Future source integrations must
implement the accepted `docs/INGRESS.md` boundary:

```text
source-specific terrain
-> SourceConnector
-> CaptureEnvelope
-> InboxPort
-> DepositWriter
-> Depósito
```

Rules for agents/contributors:

- do not put Esparza/CMS/HTML/API/browser assumptions in `canario.ingress`;
- Source Connectors stop at `InboxPort` and do not call `DepositWriter`, SQLite,
  ArchiveObject, CivicDocument, Claim, Entity, FTS, or review writers directly;
- connector code reports observations/bytes, not semantic document truth;
- Canario owns canonical Source binding, connector attribution, persistence IDs,
  validation state and custody policy;
- discovery is connector-private: there is no universal `scrape()` or
  `discover()` requirement;
- absence in one run is never deletion evidence; run coverage must remain
  explicit (`unknown`, `incremental`, `complete_inventory`);
- connector checkpoints are opaque to core and durable checkpoint storage is not
  added until a real source proves it necessary;
- PDF/DOCX/OCR/table/transcript extraction is **not** a Source Connector concern;
  it starts later at the Mesa de trabajo Representation boundary;
- plugin installation/discovery mechanics are deliberately unfrozen; do not add
  a registry/framework merely because the SPI exists.

The old Markdown processing `inbox/` is unrelated to the architectural source
Inbox.

## Mesa de trabajo / Representation Processor policy

The processor state-of-the-art research package lives at
`notebook/research/workbench/processors/`. The Civic Processor Bench is closed and
the generic `WORKBENCH-001` boundary in `canario/processors/` is independently
certified on the exact registered SQLite 3.53.4 runtime. Concrete adapters must
land as bounded units on that frozen boundary rather than redesigning custody,
QualityEvidence, scope or egress around one backend.
The accepted reference path is a curated built-in escalation ladder, not a
processor marketplace:

```text
 D0/D1 deterministic/native (Poppler/pdftotext)
-> OCRmyPDF + Tesseract
-> bounded official Codex CLI escalation
-> human review
```

Rules for agents/contributors:

- processor rung/capability and execution venue are separate concepts;
- deterministic extraction is preferred before expensive AI, but AI rungs may run
  **locally or in explicitly authorized cloud** depending on source policy,
  available hardware, benchmarked quality, latency and cost;
- official Codex CLI authenticated through a ChatGPT subscription is the reference
  cloud/agent executor; Docling, heavyweight local AI and provider APIs remain
  optional venues;
- OpenAI-compatible `base_url + api_key + model` endpoints are an escape-hatch
  transport convention only. They are **not** assumed to implement every OpenAI
  endpoint/parameter/modality; capability declaration/probing is required;
- API keys/tokens are host secrets. Never store secret values in SQLite,
  ProcessRun/evidence payloads, logs, benchmark fixtures/results, or derivative
  Representations;
- cloud processing is explicit data egress. Record non-secret provider/model/
  endpoint/request-template identity plus the fact/scope of egress and deployment
  retention/data-control profile; never infer zero retention from API use alone;
- no-egress/restricted source policy can forbid cloud completely;
- restricted/no-egress deployments fall back to local deterministic processing plus
  human review;
- Codex CLI owns ChatGPT authentication. Canario must never inspect or store those
  credentials;
- page/block escalation is allowed; no universal backend/model winner is frozen;
- no universal numeric `confidence` spans OCR/document/VLM/audio engines. Preserve
  typed processor-attributable QualityEvidence and let policy decide
  `ACCEPT | ESCALATE | QUARANTINE_REVIEW`;
- original custody is immutable and AI output never authenticates itself as source
  evidence.

The generic boundary requires exact target-backed ProcessRun inputs,
typed/namespaced `QualityEvidence`, a separate durable quality decision, explicit
egress provenance, immutable custody and visible failure/escalation. Processor
implementations never receive SQLite/archive authority. `PROCESSOR-DIRECT-001` is
independently certified for Poppler native PDF extraction. `PROCESSOR-OCR-001` uses OCRmyPDF + Tesseract under explicit `whole:v1` /
`pdf_page:v1` scope, skip-text preservation for mixed PDFs, bounded local execution,
and conservative `ocr.needs_visual_review:v1=true`; both D1 and D2 are independently
certified.
`PROCESSOR-CODEX-001` is independently certified and satisfies only one exact
`pdf_page:v1` visual-transcription request through the official Codex CLI after explicit
egress authorization. Its v2 output contract requires the transcript to remain
page-complete even when table structure is also emitted; tables supplement rather
than replace canonical text, and deterministic cross-channel coverage rejects
internally inconsistent output before derivatives are accepted. It uses a dedicated
private keyring-backed CODEX_HOME and private scratch HOME; bundled/user/admin skills
are excluded from the transcription execution, and Canario never reads ChatGPT
credentials or exposes whole-document cloud scope.

Exact developer-host fingerprinting is not durable project evidence. Do not persist
hostname, username, exact kernel/distribution build, exact CPU/GPU model, total
RAM/swap, device IDs, home paths, or environment dumps unless a narrowly scoped
certification proves that exact fact is itself required. Prefer tool/runtime
identity and process-scoped resource measurements.

## Lector / Fichero semantic extraction policy

`LECTOR-001` is independently certified and integrated at merge
`98c2d60387fd7ec176033563566f62c59123587d`. The generic semantic boundary lives in
`canario/lector/`; `SemanticExtractor` backends are untrusted/replaceable and
`LectorWriter` is the bounded canonical authority for the exact LECTOR-001 output
surface.

Rules for agents/contributors:

- `machine-only` is a valid durable/searchable review state, not a review queue or
  ingestion debt; absence of human review must remain explicit;
- production ingestion must not require claim-by-claim approval merely to make
  evidence-backed Claims searchable;
- human review is demand/policy driven (important use, publication, conflict,
  anomaly, correction), and no machine/rule extractor may fabricate it;
- every extracted Claim has exact reopenable evidence and ProcessRun provenance;
- Claim text is not global identity/deduplication authority; stable replay is by the
  exact ProcessRun identity contract;
- LECTOR-001 cannot create/merge canonical Entities by name, write human reviews,
  revise/retract historical Claims, invent Tag vocabulary, publish outputs, or
  perform canonical cutover;
- broad ClaimRelations created during `claim_extract` are same-run only and obey the
  candidate/basis rules in `notebook/implementation/LECTOR_001_DESIGN.md`;
- the deterministic `STRUCTURED-REASONING-FIT-BENCH` is certified at
  `0f9a71e5acb0f093469571d59c896eab0c03c4c2`; `STRUCTURED-VERIFIER-FIT-BENCH` Phase D
  measured material decomposition value and selected a minimum Canario-native
  Derivation -> Verification split. Final local closure certification is pending. The prior
  LECTOR-002 semantic campaign is
  superseded and must be re-scoped before replacement reference work. Acta 161 is
  case `CR-ESPARZA-MINUTES-001` and cannot establish general extraction quality by itself;
- LECTOR-002 fixture genre labels are optional `benchmark_archetypes`, not registered
  Canario document classes. Do not create an exhaustive `DocumentType`/`case_class`
  taxonomy to make the benchmark green;
- the executable LECTOR-002 gate measures an explicit, revisable matrix of Representation,
  evidence and semantic-stress capabilities. A new real-world failure mode extends that
  matrix; it does not require inventing a universal record class;
- each declared capability states its verification mode. Representation/evidence invariants
  use deterministic proof from frozen bytes and exact reopening; semantic-stress capabilities
  require a frozen, human-approved semantic reference plus candidate adjudication. The active
  reference workflow may use declared AI assistance, but it must preserve explicit human approval
  and keep tested-extractor output unseen until the reference is frozen. Do not create annotation
  work for a property that can be mechanically certified;
- the benchmark must report `certification_scope = declared_capabilities_only` and
  `universal_support_claimed = false`. No finite corpus certifies every possible future
  document, container or medium;
- the canonical text-case harness uses only generic Representation structure. Any
  acta/language/source-specific heuristic must live in an explicitly scoped helper and
  cannot define corpus completeness;
- current fixture-selection archetypes (minutes, report/audit, correspondence,
  normative/contractual, structured data, timed media) are useful stress sources, not
  ontology. Coverage is accepted only through appropriate typed evidence evaluators;
- benchmark assistance must be explicit provenance, never silently presented as independent
  human gold. The historical mode is `human_ai_assisted`: assistant proposals require explicit human
  approval, exact evidence must reopen mechanically, and `needs_adjudication` remains unresolved
  until a later review. Do not inspect a tested extractor's output for a case before that case's
  semantic reference is frozen. If reference assistant and tested extractor share a model/family/
  provider, or independence is unknown, record that limitation and require an independent
  second-review sample before treating semantic PASS as strong certification evidence.
- LECTOR-002 semantic reference uses independent `gold_scope_state`, `gold_state`,
  `adjudication_state`, and per-capability `semantic_verification` with an immutable
  result digest. Gold/adjudication alone never verifies a semantic capability;
  thresholds freeze after gold counts and before tested extractor output.
- Structured-data reference may use a deterministic structural sample, which proves only
  that selected scope. Longform completeness uses full source order. Review packets must keep
  non-selected units explicitly `unjudged` and must contain no candidates or truths before
  review. `semantic_model_calls=0` in the frozen scope records that the scope was fixed before
  assistance; later AI assistance is declared separately in reference provenance.

### Semantic operation boundaries after SOTA review

`Lector` answers only: **what does this source assert or explicitly contain?** Newly computed sums,
comparisons and joins belong to Derivation; deciding what a proposition and bounded evidence justify
belongs to Verification. These are semantic boundaries, not mandatory human workflow stages.

The accepted reconciliation lives in
`notebook/implementation/DERIVATION_VERIFICATION_RECONCILIATION.md` and closes the prior persistence
question with:

```text
SINGLE_EXECUTION_GRAPH__SOURCE_EVIDENCE_NOT_EXECUTION_LINEAGE
```

Rules for agents/contributors:

- certified `ProcessRun` remains Representation-processing / existing semantic-extraction
  provenance; do not overload it as a generic analytical run;
- `DerivationRun` is a distinct immutable analytical attempt over ordered exact
  RepresentationTargets and one exact untrusted program/query;
- every successful DerivationRun has one typed `DerivationResult`; exact reusable result slices are
  `DerivationResultTarget`s with explicit per-target source-lineage state;
- do not force cross-source analytical results into `Representation`; Representation remains in one
  Artifact custody chain;
- `VerificationRun` binds one proposition to an explicit bounded scope + Source Authority, records
  every Derivation attempted and which exact result target(s) were consumed, and separates
  execution outcome from epistemic verdict/sufficiency;
- `insufficient_evidence` is a completed epistemic result, never an alias for timeout/crash/query or
  tool failure;
- `EvidenceLink` remains ClaimRevision -> exact source RepresentationTarget. Derivation lineage and
  Verification evidence are execution records and must not be copied into Claim evidence
  automatically;
- a `derived_inference` Claim must name its exact DerivationResultTarget. Active `supports` evidence
  must trace to source-contribution lineage for that target; independent `challenges` evidence is
  allowed;
- `Assessment` is an optional attributable durable judgment on a ClaimRevision, distinct from
  review and lifecycle. Verification-based Assessment requires the same exact ClaimRevision and an
  explicit policy for machine/rule promotion;
- no automatic Claim, EvidenceLink or Assessment promotion is authorized;
- egress/provider/model facts remain non-secret replaceable execution provenance, never Source
  Authority or civic identity;
- analytical/verification content-bearing records participate in explicit purge expansion and
  shared ArchiveObject safety just like existing custody-bearing records.

Phase D used the dedicated keyring-backed official Codex CLI / ChatGPT subscription profile with
`gpt-5.6-terra`, zero semantic retries and no paid/API fallback. The measured decision remains
`DECOMPOSITION_VALUE_PROVEN__DESIGN_MINIMUM_CANARIO_DECOMPOSITION`; native Thucy remains
non-imported/non-executed/non-vendored and future metered provider profiles remain allowed but are
not automatic fallback or semantic authority.

## ¿Qué es Canario?

Canario convierte evidencia pública heterogénea en conocimiento cívico trazable.
Preserva los bytes originales, deriva Representations adecuadas al medio, propone Claims
con evidencia exacta y provenance, y permite buscarlas/revisarlas sin fingir que una IA
las confirmó humanamente.

Actas municipales son hoy la fuente con mayor dogfood e historial legado, pero un informe
de auditoría, un presupuesto tabular, un oficio, un contrato, un dataset o una grabación
son ciudadanos de primera clase del mismo sistema. La pregunta del core no es “¿cómo se
procesa un acta?”, sino “¿cómo se preserva, representa y cita correctamente esta evidencia
para extraer información útil sin perder su naturaleza?”.

**Idioma del proyecto:** la documentación de producto puede usar español/inglés técnico.
Los adaptadores o perfiles lingüísticos pueden especializarse, pero el core no asume
español costarricense ni lenguaje municipal como contrato universal.

---

## Project Layout and legacy boundary

The durable Canario architecture lives in the package/docs/tests below. Start here for new
core work:

```text
canario/
  ingress/        terrain-neutral acquisition boundary
  deposit/        custody
  processors/     Representation/Workbench processors
  lector/         semantic extraction boundary
  persistence/    canonical SQLite authority
  connectors/     explicitly source-specific adapters

docs/            accepted/current architecture and contracts
notebook/         research, certification evidence, implementation records
tests/            executable invariants
```

The top-level `scripts/`, `skills/`, `config.example.yaml`, Hilo/Tablero vocabulary and
acta directories belong primarily to the **legacy municipal-acta workflow**. They remain
because that workflow is real operator history and useful regression evidence. Do not copy
their municipality/acta assumptions into `canario/` merely because they are numerous or
older. A new generic feature should normally be justified from `docs/` contracts and real
heterogeneous fixtures first.

Historical Notebook records may still say ActaKit or reference the old `actakit/` package
path. Treat those as provenance describing the tree at the time of the recorded proof, not
as current naming instructions.

---

## Legacy municipal-acta workflow reference

The remainder of this section documents the preserved pre-Canario acta/Hilo workflow.
It is operational reference, not the universal architecture.

### Legacy `config.yaml`

Archivo central del pipeline. Copiar desde `config.example.yaml`:

```yaml
municipio: "Atenas"                    # Nombre del cantón
vault_root: "./mi-vault"               # Raíz del vault (cada comunidad define)

hilos:
  bloques:
    - nombre: "GobernanzaLocal"
      hilos:
        - "Concejo Municipal y Funcionamiento"
        - "Auditoría y Control Interno"
        - ...
  alias:
    "Viejo nombre": "Nombre oficial"

scraping:
  url_base: "https://municipalidad-atenas.go.cr"
  secciones:
    concejo:
      path: "/actas-concejo"

procesamiento:
  actas_dir: "actas/procesadas"
  hilos_dir: "hilos"
```

### enrutamiento.yaml

El archivo más específico del cantón. Define **señales** (palabras clave,
instituciones, leyes, lugares) que mapean contenido a hilos temáticos.

```yaml
hilos:
  - nombre: "Concejo Municipal y Funcionamiento"
    señales:
      - "regidor"
      - "alcalde"
      - "sesión ordinaria"
      - "sesión extraordinaria"
      - "acta de sesión"
  - nombre: "Auditoría y Control Interno"
    señales:
      - "CGR"
      - "contraloría"
      - "informe de auditoría"
      - "hallazgo"
```

**Para un nuevo municipio:** ejecutar `bash scripts/run_bootstrap.sh` genera
automáticamente un `enrutamiento.yaml` desde las actas existentes.

---

## Pipeline — 5 etapas

### Etapa 0: Scraping

```bash
python scripts/scrape_actas.py --config config.yaml
python scripts/scrape_actas.py --config config.yaml --section concejo
python scripts/scrape_actas.py --config config.yaml --dry-run  # solo listar
```

Descarga PDFs desde el CMS de la municipalidad. Genera:
- PDFs en `actas/descargadas/[seccion]/`
- `inventario_actas.csv` en el directorio de salida

**Dependencias:** `requests`, `beautifulsoup4`

---

### Etapa 1: Extracción de texto

```bash
python scripts/pdftotext_actas.py \
    --input-dir actas/descargadas \
    --output-dir _texto_md \
    --vault actas/descargadas
```

Convierte PDFs/DOCXs a texto plano Markdown. Genera archivos `.md`
en `_texto_md/` con el texto extraído.

**Dependencias:** `poppler-utils` (pdftotext), `python-docx`

**Seguridad:** No sobreescribe archivos existentes a menos que `--force`.
Backups automáticos antes de sobreescritura.

---

### Etapa 2: Procesamiento (AI o humano)

**Usar `skills/procesar-acta/SKILL.md`** como guía de trabajo.

El resultado es un borrador en el inbox que, tras revisión humana, se
mueve al directorio de actas procesadas (`actas/procesadas/`).

**Formato de salida:** Los borradores nuevos usan el frontmatter v2 de
`skills/_formato-intermedio.md`. Las actas históricas sin frontmatter se
mantienen como formato legado compatible. El cuerpo Markdown que consume el
integrador usa:
```markdown
# Acta N° 123 — Sesión Ordinaria — 27 de abril del 2026

## Episodios
### → Hilo: `Movilidad, Red Vial y Transporte Público`
#### 2026-04-27 — Título del episodio
Contenido estructurado...
> Fuente: Acta N° 123, ...

## Tablero de anuncios
- Anuncio 1
- Anuncio 2
```

El formato exacto está especificado en `_formato-intermedio.md`.

---

### Etapa 3: Tablero y clasificación

```bash
# Extraer anuncios del tablero
python scripts/extract_tablero.py \
    --actas-dir actas/procesadas \
    --output ./datos/_anuncios_data.json

# Generar episodios desde clasificaciones
python scripts/generate_anuncios.py \
    --anuncios ./datos/_anuncios_data.json \
    --clasificaciones ./datos/_clasificaciones.json \
    --output ./datos/_episodios_generados.json \
    --candidatos ./datos/_candidatos_con_texto_completo.json

# Aplicar graduación (mover anuncios → episodios en actas)
python scripts/aplicar_graduacion.py \
    --actas-dir actas/procesadas \
    --herramientas-dir ./datos
    # --reset  # restaurar desde backup y reprocesar
```

**Idempotencia:** `aplicar_graduacion.py` detecta si los episodios ya
fueron agregados y los omite. Usar `--reset` para restaurar desde
backup y reprocesar desde cero.

---

### Etapa 4: Integración en hilos

```bash
python scripts/integrate_hilos.py --config config.yaml
```

Lee todas las actas procesadas y agrega únicamente episodios no presentes en
los Hilos existentes. No borra resúmenes, contexto heredado, Readmes ni otros
materiales curatoriales. `--rebuild --force-delete` es destructivo y debe
usarse solo sobre salidas desechables.

**Formato de hilo:**
```markdown
### YYYY-MM-DD — Título del episodio

Contenido del episodio...

> Fuente: Acta N° 123, 27 de abril del 2026, ...
```

**Seguridad:** No sigue symlinks. Usa `O_NOFOLLOW` en todas las
operaciones de escritura. Revisar siempre `--dry-run` antes de integrar.

---

## Extracción de entidades

`scripts/entity_index.py` provee extracción de entidades vía regex,
sin depender de APIs externas.

### Instituciones costarricenses

Incluye ~50 instituciones CR con acrónimos y nombres completos:
CGR, CCSS, MEP, ICE, ASADA, ARESEP, etc.

### Patrones de leyes

```
Ley N° 7794        → Ley 7794 (Concejo Municipal)
Ley No. 8422        → Ley 8422 (Ordenamiento Territorial)
Ley 833             → Ley 833 (corta, 3 dígitos)
```

### Lugares

Distritos, cantones, provincias, ríos, rutas. Todos calibrados
para топонимы costarricenses (con soporte para acentos y variantes).

### Roles

Alcalde, síndico, regidor, presidente municipal, auditor interno,
gestor jurídico, tesorero municipal, etc.

---

## Canonical Format — Formato intermedio

El formato de las actas procesadas está especificado en
`skills/_formato-intermedio.md`. Todo procesamiento debe producir
output que cumpla este contrato.

**Estructura básica v2:**

```markdown
---
version_formato: 2
fuente_tipo: actas
fuente_id: Acta N° 123
fecha_fuente: 2026-04-27
estado: aprobado
episodios:
  - episodio_id: acta-123-art-iii-item-4-vialidad
    fecha: 2026-04-27
    titulo: Título del episodio
    hilo_destino: Movilidad, Red Vial y Transporte Público
    tipo: evidencia
    cuerpo: Contenido estructurado...
    cita: Acta N° 123, 27 de abril del 2026, Artículo III, ítem 4.
    fuente:
      archivo: 3 Fuentes/Municipalidad/Actas/concejo/acta_123.pdf
      articulo: III
      item: 4
      pagina: null
---
# Acta N° {num} — {tipo sesión} — {fecha en español}

## Episodios
### → Hilo: `{Hilo canónico}`
#### {YYYY-MM-DD} — {título del episodio}
{contenido estructurado}
> Fuente: Acta N° {num}, {fecha}, ...

## Tablero de anuncios
- {anuncio 1}
- {anuncio 2}
```

---

## Configurar para un nuevo municipio

### Paso 1 — Clonar y configurar

```bash
git clone https://github.com/sxntaxis/canario.git
cd canario
cp config.example.yaml config.yaml
# Editar: municipio, url_base, scraping.secciones
```

### Paso 2 — Bootstrap (recomendado)

```bash
# Requiere al menos 1 acta ya procesada en actas/procesadas/
bash scripts/run_bootstrap.sh
# Genera bootstrap/bootstrap_summary.json y bootstrap_report.md
```

### Paso 3 — Revisar taxonomía

```bash
# Revisar los outputs
cat bootstrap/bootstrap_report.md
cat bootstrap/bootstrap_summary.json

# Ajustar signals en enrutamiento.yaml
```

### Paso 4 — Procesar

```bash
# Descargar nuevas actas
python scripts/scrape_actas.py --config config.yaml

# Extraer texto
python scripts/pdftotext_actas.py --input-dir actas/descargadas

# Procesar actas (usar skills/procesar-acta/SKILL.md)

# Integrar
python scripts/integrate_hilos.py --config config.yaml
```

---

## Script reference

| Script | Entrada | Salida | Flags importantes |
|---|---|---|---|
| `scrape_actas.py` | URL municipal | PDFs + CSV | `--config`, `--section`, `--dry-run`, `--years` |
| `pdftotext_actas.py` | PDFs/DOCX | `.md` texto | `--input-dir`, `--output-dir`, `--vault`, `--force` |
| `extract_tablero.py` | Actas procesadas | JSON anuncios | `--actas-dir`, `--output` |
| `generate_anuncios.py` | Anuncios + clasificaciones | Episodios JSON | `--anuncios`, `--clasificaciones`, `--output` |
| `aplicar_graduacion.py` | Episodios + actas | Actas editadas | `--actas-dir`, `--herramientas-dir`, `--reset` |
| `integrate_hilos.py` | Actas procesadas | Hilos `.md` | `--config`, `--dry-run` |
| `bootstrap_hilos.py` | Actas procesadas | Reporte + JSON | `--actas-dir`, `--output`, `--lugares` |
| `generate_enrutamiento.py` | Bootstrap JSON | `enrutamiento.yaml` | `--input`, `--output` |
| `setup_municipio.py` | JSON de investigación | Config local | `--municipio`, `--lugares-json`, `--guide` |

---

## Common issues and solutions

### "No se encontraron actas" en scrape_actas

El sitio web de la municipalidad cambió su estructura. Revisar
los selectores CSS en `scraping.selectores` del config.yaml o usar
`--section` para especificar la ruta manualmente.

### pdftotext devuelve texto vacío

某些 PDFs están escaneados (imágenes, no texto). Se necesita OCR.
Solución temporal: procesar manualmente o usar `python-docx` para
DOCX únicamente.

### Bootstrap genera Coverage bajo (<60%)

Significa que la taxonomía semilla no cubre los temas de las actas.
Soluciones:
1. Procesar más actas (más datos = mejor clustering)
2. Agregar signals a `SEED_HILOS` en `scripts/bootstrap_hilos.py`
3. Crear nuevos hilos para topics detectados pero no clasificados

### apply_graduacion.py corrompe actas al re-ejecutar

Usar `--reset` para restaurar desde el último backup automático
(`actas/procesadas/bak_graduacion/`).

### Errores de encoding en textos

Todos los scripts usan `encoding='utf-8'` explicitado. Si hay
caracteres extraños, verificar que el archivo de entrada esté en UTF-8.

---

## Dependencias del sistema

```bash
# Linux
sudo apt install poppler-utils

# macOS
brew install poppler

# Python
pip install -r requirements.txt
```

`requirements.txt`:
- `pyyaml` — parsing de configuración
- `requests` — scraping HTTP
- `beautifulsoup4` — parsing HTML
- `python-docx` — extracción de DOCX

---

## Notas de seguridad

- No seguir symlinks en operaciones de escritura (mitigado en todos los scripts)
- Path traversal mitigado en nombres de archivo generados
- No hay command injection已知 — todos los subprocess usan listas, no shell strings
- Datos de producción siempre en vault local, nunca en el repo

---

## Referencias cruzadas

| Tema | Archivo |
|---|---|
| Formato de actas procesadas | `skills/_formato-intermedio.md` |
| Workflow de procesamiento AI | `skills/procesar-acta/SKILL.md` |
| Configuración completa | `config.example.yaml` |
| Patrones de entidades | `scripts/entity_index.py` (docstring) |
| Historial de cambios | `CHANGELOG.md` |

---

_Last reviewed: 2026-08-24 — canario prerelease_
_Questions? Open a GitHub Issue or read the source._
