# Canario

> Evidence-first civic intelligence over heterogeneous public records.

[![CI](https://github.com/sxntaxis/canario/actions/workflows/ci.yml/badge.svg)](https://github.com/sxntaxis/canario/actions)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: AGPL-3.0](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)](LICENSE)
[![License: CC-BY-4.0](https://img.shields.io/badge/license-CC--BY-4.0-blue.svg)](LICENSE.CC-BY)

> **Pre-release:** there is no public schema/API compatibility boundary yet. See
> `docs/STATUS.md` and `AGENTS.md`.

## Qué es

**Canario** adquiere y preserva evidencia pública, genera Representations adecuadas a
cada medio y extrae información cívica trazable hacia un Fichero consultable. Una Claim
machine-only puede ser útil inmediatamente si conserva fuente, locator y provenance; la
revisión humana se exige cuando el uso/policy lo requiera, no para vaciar una cola de
ingestión.

El producto **no está limitado a actas ni a PDFs**. El modelo incluye, entre otros:

- actas, agendas, resoluciones, oficios, informes y auditorías;
- presupuestos, contrataciones, contratos, tablas y datasets;
- reglamentos, planes y correspondencia;
- imágenes y documentos escaneados;
- grabaciones de audio/video y transcripts derivados con evidencia temporal.

La vieja canalización municipal de actas sigue en el repositorio porque es el primer
workflow desplegado y conserva valor operativo/histórico. Es **legacy/source-specific**,
no la plantilla para nuevas capacidades. `AGENTS.md` contiene el guardrail de scope que
todo agente debe leer antes de modificar el core.

## Current capability boundary

| Layer | Current state | Scope note |
|---|---|---|
| Ingress / custody | Generic boundary + Esparza connector | Connectors may acquire arbitrary bytes/metadata |
| Workbench | Generic processor substrate; PDF native/OCR/Codex visual adapters | Audio transcription is not implemented yet |
| Lector | Generic semantic contracts/writer | Runtime evidence reopening currently covers text quotes + table ranges |
| LECTOR-002 | Heterogeneous corpus work in progress | Acta 161 is one case, never the broad benchmark by itself |

A missing modality is treated as an explicit capability gap. Canario must not coerce an
audio/table/image source into a text-only abstraction simply because a current adapter or
benchmark is easier to implement that way.

## Arquitectura

> The current file pipeline is stable for existing work. The accepted durable
> civic-record architecture and implementation gates are in
> [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md),
> [`docs/ROADMAP.md`](docs/ROADMAP.md), and [`docs/STATUS.md`](docs/STATUS.md).
> The accepted core contracts plus the current implementation plan/distribution gates
> are in [`docs/CONTRACTS.md`](docs/CONTRACTS.md),
> [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md),
> [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md), and
> [`docs/RELEASE_1_0.md`](docs/RELEASE_1_0.md).

La arquitectura durable se explica con ocho conceptos nativos:

```text
Inbox -> Depósito -> Mesa de trabajo -> Lector -> Fichero
                  -> Mesa de control -> Consultas -> Salidas
```

El **Inbox** es la frontera de ingreso: HTML, APIs, browser automation, feeds,
filesystem o carga manual pueden usar Source Connectors completamente distintos,
pero todos terminan en el mismo `CaptureEnvelope -> InboxPort`. El scraper actual
de Esparza es una herramienta legado y futuro connector, no el molde del core.
Ver [`docs/INGRESS.md`](docs/INGRESS.md).

Estas metáforas son lenguaje de producto/documentación; no obligan a usar esos
nombres en el árbol de código. `Episode`/`Hilo` pasan a ser conceptos de una
Salida, no requisitos del núcleo universal.

**Pipeline de archivos legado/actual (preservado durante la transición):**

```
┌──────────────┐   ┌───────────────┐   ┌─────────────────┐
│  Scrapeo      │──→│  Extracción    │──→│  Procesamiento   │
│  scrape_actas │   │  pdftotext      │   │  skill AI / humano │
└──────────────┘   └───────────────┘   └─────────────────┘
                                               │
                       ┌────────────────────────┘
                       ↓
┌──────────────┐   ┌───────────────┐   ┌─────────────────┐
│  Tablero      │──→│  Clasificación │──→│  Graduación      │
│  extract      │   │  generate      │   │  aplicar          │
└──────────────┘   └───────────────┘   └─────────────────┘
                                               │
─────────────────────── INTEGRACIÓN ─────────────────────────
                       ↓
          ┌──────────────────────────┐
          │  Integración             │
          │  integrate_hilos         │
          └──────────────────────────┘
                       │
          ┌────────────┴────────────┐
          ↓                         ↓
   [hilos/*.md]            [actas procesadas]
```

**Flujo de datos:**

```
[sitio web municipal]
      ↓ scrape_actas.py
[PDFs en actas/descargadas/]
      ↓ pdftotext_actas.py
[_texto_md/] ← texto plano
      ↓ procesar-acta (skill AI o humano)
[borrador en inbox/] ← revisión humana
      ↓ aprobación
[acta procesada en actas/procesadas/]
      ↓                          ↕
  integrate_hilos.py       extract_tablero.py
      ↓                          ↓
[hilos/]           [anuncios → clasificación → graduación]
```

---

## Características principales

| Característica | Descripción |
|---|---|
| **Scraping automático** | Descarga actas desde el CMS de la municipalidad sin API |
| **Extracción sin API** | pdftotext + python-docx, sin costos de API externa |
| **Procesamiento con IA** | Skill para asistentes AI con formato intermedio verificable |
| **Bootstrap automático** | Genera taxonomía de hilos desde las actas existentes |
| **Multi-municipalidad** | Configuración extensible para cualquier cantón costarricense |
| **Entidades CR** | Patrones para instituciones, leyes, lugares y roles costarricenses |
| **Idempotencia** | Los scripts se pueden ejecutar múltiples veces sin corrupto |
| **Seguridad** | Sin command injection, symlink protection, path traversal mitigado |

---

## Primeros pasos

### 1 — Clonar e instalar

```bash
git clone https://github.com/sxntaxis/canario.git
cd canario
pip install -r requirements.txt

# Dependencia del sistema (Linux/macOS)
sudo apt install poppler-utils   # Linux
brew install poppler             # macOS
```

### 2 — Configurar para tu municipalidad

```bash
cp config.example.yaml config.yaml
# Editar config.yaml con el nombre del cantón, URL del sitio, paths
```

### 3 — Ejecutar bootstrap (opcional, recomendado)

```bash
# Genera la taxonomía de hilos automáticamente desde tus actas existentes
bash scripts/run_bootstrap.sh
```

### 4 — Procesar actas

```bash
# 0. Descargar PDFs
python scripts/scrape_actas.py --config config.yaml

# 1. Extraer texto
python scripts/pdftotext_actas.py --input-dir actas/descargadas --vault actas/descargadas

# 2. Procesar con IA → seguir skills/procesar-acta/SKILL.md

# 3. Extraer tablero de anuncios
python scripts/extract_tablero.py --actas-dir actas/procesadas

# 4. Integrar en hilos
python scripts/integrate_hilos.py --config config.yaml
```

---

## Para LLMs y asistentes AI

> **Importante:** Antes de trabajar con este proyecto, leé `AGENTS.md`.
> Ese archivo contiene toda la información que un modelo de lenguaje
> necesita para configurar, ejecutar y extender el pipeline correctamente.

Breve resumen de los archivos clave:

| Archivo | Propósito |
|---|---|
| `AGENTS.md` | Documentación universal para cualquier LLM |
| `skills/procesar-acta/SKILL.md` | Workflow de procesamiento de actas |
| `skills/procesar-acta/config/ejemplo/enrutamiento.yaml` | Taxonomía de ejemplo |
| `config.example.yaml` | Configuración base del pipeline |
| `_formato-intermedio.md` | Contrato de formato entre etapas |

---

## Estructura del proyecto

```
canario/
├── README.md                    ← este archivo
├── AGENTS.md                    ← documentación para LLMs
├── LICENSE                      ← AGPL v3 (código fuente)
├── LICENSE.CC-BY                ← CC-BY 4.0 (documentación)
├── requirements.txt             ← dependencias Python
├── config.example.yaml           ← configuración de ejemplo
├── FIX_ROADMAP.md               ← registro de cambios
│
├── scripts/                     ← pipeline CLI
│   ├── scrape_actas.py          ← descarga PDFs del sitio municipal
│   ├── pdftotext_actas.py       ← extrae texto de PDFs/DOCX
│   ├── extract_tablero.py       ← extrae anuncios de actas procesadas
│   ├── generate_anuncios.py     ← genera episodios desde clasificaciones
│   ├── aplicar_graduacion.py    ← gradúa anuncios a episodios en actas
│   ├── merge_clasificaciones.py ← fusiona clasificaciones de múltiples fuentes
│   │
│   ├── entity_index.py          ← extracción de entidades (regex CR)
│   ├── bootstrap_hilos.py       ← bootstrap automático de taxonomía
│   ├── generate_enrutamiento.py ← genera enrutamiento.yaml desde bootstrap
│   ├── integrate_hilos.py       ← integra episodios en archivos de hilo
│   ├── setup_municipio.py       ← descubrimiento LLM de lugares locales
│   └── run_bootstrap.sh         ← orquestación del bootstrap
│
└── skills/                      ← instrucciones para asistentes AI
    ├── _formato-intermedio.md   ← contrato de formato entre skills
    ├── _principios-compartidos.md
    ├── procesar-acta/           ← procesamiento de actas
    │   ├── SKILL.md
    │   └── config/ejemplo/
    │       ├── enrutamiento.yaml
    │       ├── fuentes.yaml
    │       └── inbox.yaml
    ├── tejer-hilo/SKILL.md      ← integración en hilos
    └── procesar-prensa/SKILL.md ← prensa y comunicados
```

---

## Scripts principales

| Script | Qué hace |
|---|---|
| `scrape_actas.py` | Descarga actas en PDF/DOCX desde el sitio municipal |
| `pdftotext_actas.py` | Convierte PDFs y DOCXs a texto plano |
| `bootstrap_hilos.py` | Extrae entidades + clasifica + propone nueva taxonomía |
| `generate_enrutamiento.py` | Convierte el output del bootstrap en `enrutamiento.yaml` |
| `extract_tablero.py` | Extrae el tablero de anuncios de actas ya procesadas |
| `generate_anuncios.py` | Genera episodios desde clasificaciones de anuncios |
| `aplicar_graduacion.py` | Mueve anuncios clasificados a episodios en las actas |
| `integrate_hilos.py` | Reconstruye archivos de hilo desde episodios de actas |
| `setup_municipio.py` | Guía de investigación asistida por LLM para nuevos cantones |

---

## Licencia

**Código fuente:** [AGPL v3](LICENSE) — publicado por sxntaxis.

**Documentación y contenido creativo:** [CC-BY 4.0](LICENSE.CC-BY) — atribuación requerida.

---

## Autor

**sxntaxis** — https://github.com/sxntaxis

Preguntas, issues y contribuciones bienvenidas a través de GitHub Issues.
