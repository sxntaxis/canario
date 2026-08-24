# AGENTS.md

> **Documentación para asistentes de IA — actakit v1.0**
>
> Antes de trabajar con este proyecto, leé este archivo completo.
> Contiene todo lo que un modelo de lenguaje necesita para configurar,
> ejecutar y extender el pipeline correctamente.

---

## Política de pre-release y compatibilidad de schema

**ActaKit está en pre-release. No hay usuarios ni instalaciones públicas cuya base
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

- do not put Esparza/CMS/HTML/API/browser assumptions in `actakit.ingress`;
- Source Connectors stop at `InboxPort` and do not call `DepositWriter`, SQLite,
  ArchiveObject, CivicDocument, Claim, Entity, FTS, or review writers directly;
- connector code reports observations/bytes, not semantic document truth;
- ActaKit owns canonical Source binding, connector attribution, persistence IDs,
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
the generic `WORKBENCH-001` boundary in `actakit/processors/` is independently
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
- Codex CLI owns ChatGPT authentication. ActaKit must never inspect or store those
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
`PROCESSOR-CODEX-001` is the current candidate and may satisfy only one exact
`pdf_page:v1` visual-transcription request through the official Codex CLI after explicit
egress authorization. Its v2 output contract requires the transcript to remain
page-complete even when table structure is also emitted; tables supplement rather
than replace canonical text, and deterministic cross-channel coverage rejects
internally inconsistent output before derivatives are accepted. It uses a dedicated
private keyring-backed CODEX_HOME and private scratch HOME; bundled/user/admin skills
are excluded from the transcription execution, and ActaKit never reads ChatGPT
credentials or exposes whole-document cloud scope.

Exact developer-host fingerprinting is not durable project evidence. Do not persist
hostname, username, exact kernel/distribution build, exact CPU/GPU model, total
RAM/swap, device IDs, home paths, or environment dumps unless a narrowly scoped
certification proves that exact fact is itself required. Prefer tool/runtime
identity and process-scoped resource measurements.

## ¿Qué es actakit?

actakit procesa actas del Conceho Municipal de Costa Rica y las convierte
en conocimiento estructurado: hilos temáticos, hallazgos y memoria
documental verificable.

Cada acta pasa por 5 etapas: scraping → extracción de texto → procesamiento
clasificado → extracción de anuncios → integración en hilos. El resultado
son archivos `.md` por tema (hilo) que agrupan todos los episodios
relacionados de múltiples actas, con atribuación completa.

**Idioma del proyecto:** Español (documentación, código, configuración).
Los patrones de extracción están calibrados para español costarricense.

---

## Project Layout

```
actakit/
├── scripts/
│   ├── scrape_actas.py          # Etapa 0: descargar PDFs
│   ├── pdftotext_actas.py       # Etapa 1: texto plano
│   ├── extract_tablero.py        # Etapa 3: extraer anuncios
│   ├── generate_anuncios.py     # Etapa 3: generar episodios
│   ├── aplicar_graduacion.py     # Etapa 4: mover anuncios a episodios
│   ├── merge_clasificaciones.py # Fusionar clasificaciones
│   │
│   ├── entity_index.py           # Extracción de entidades (regex)
│   ├── bootstrap_hilos.py        # Bootstrap de taxonomía
│   ├── generate_enrutamiento.py  # Generar enrutamiento.yaml
│   ├── integrate_hilos.py         # Etapa 5: integrar en hilos
│   ├── setup_municipio.py         # Guía para nuevos cantones
│   └── run_bootstrap.sh          # Orquestación bootstrap
│
├── skills/                       # Instrucciones para procesamiento AI
│   ├── _formato-intermedio.md    # Contrato de formato entre etapas
│   ├── _principios-compartidos.md
│   ├── procesar-acta/            # Skill principal de procesamiento
│   │   ├── SKILL.md
│   │   └── config/ejemplo/
│   │       ├── enrutamiento.yaml # Taxonomía de hilos (palabras clave)
│   │       ├── fuentes.yaml
│   │       └── inbox.yaml
│   ├── tejer-hilo/               # Integración en hilos
│   └── procesar-prensa/           # Prensa y comunicados
│
├── config.example.yaml           # Configuración base
└── requirements.txt               # Dependencias Python
```

---

## Configuración

### config.yaml

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
git clone https://github.com/sxntaxis/actakit.git
cd actakit
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

_Last reviewed: 2026-06-28 — actakit v1.0_
_Questions? Open a GitHub Issue or read the source._
