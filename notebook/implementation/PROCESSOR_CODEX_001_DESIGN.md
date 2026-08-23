# PROCESSOR-CODEX-001 — bounded Codex CLI visual-transcription design

**Start authority:** `49d337ddbfae0be32a351e5adb37063bbaabe528`  
**Parent gate:** `PROCESSOR_OCR_001_OCRMYPDF_TESSERACT_IMPLEMENTED_AND_CERTIFIED`

## Purpose

Land the reference D4/D5 subscription-backed visual transcription adapter on the
certified Workbench boundary. The adapter is not a general Codex agent host. It
transcribes **one explicit `pdf_page:v1` target per ProcessRun** after D2 has
already established that the page remains review-bound.

Reference path:

```text
D1 native -> D2 OCR -> exact pdf_page:v1 -> Codex CLI -> ACCEPT or D6 review
```

`whole:v1` and multi-page cloud attempts are deliberately unsupported. This is a
product privacy boundary: only the page that requires escalation can be handed to
the subscription executor.

## Executor identity

```text
processor key:     codex.visual_transcribe_pdf_page
capability:        visual_transcribe
venue:             subscription_agent
input:             application/pdf
scope:             pdf_page:v1 exactly one
outputs:           transcript, table
reference CLI:     official Codex 0.149.0
reference model:   gpt-5.6-sol
provider identity: openai
endpoint profile:  openai_codex_subscription
```

Codex is treated as an **agent executor**, not an OpenAI-compatible API. ActaKit
never reads, copies, refreshes or persists ChatGPT credentials.

## Dedicated authentication/profile boundary

Production execution requires a dedicated non-default `CODEX_HOME` owned by the
official CLI, private (`0700` on POSIX), and configured to use OS keyring credential
storage. The adapter fails closed when that profile contains:

```text
auth.json
config.toml
user skills under CODEX_HOME/skills (except CLI-managed .system cache material)
ambient /etc/codex/skills on POSIX
```

The child Codex process receives an empty private `HOME`; this prevents ambient
`~/.agents/skills` and ordinary user-home configuration from entering the
execution context. The exec command also sets `skills.bundled.enabled=false`, so
CLI-managed `.system` skills are not loaded into this transcription session. The dedicated profile path is runtime-only and never enters
configuration hashes, ProcessRun rows or quality evidence.

## Cloud execution sandbox

The command fixes:

```text
codex exec
--strict-config
--ephemeral
--ignore-user-config
--ignore-rules
--sandbox read-only
--skip-git-repo-check
--model gpt-5.6-sol
--output-schema <bounded schema>
--output-last-message <private scratch output>
--cd <private scratch>
--image <one rendered page PNG>
```

Config overrides disable shell/unified-exec, multi-agent, plugins/apps, web
search, browser/computer/image-generation and the local image-view feature. The
Codex 0.149.0 config contract exposes `view_image` under `[features]`, so the
qualified override is `features.view_image=false`; no unsupported `tools.view_image`
field is used. Lifecycle hooks are disabled as an unnecessary execution surface. The exact static override list is part of the adapter configuration hash, so changing Codex execution policy changes durable configuration identity. Stdout
and stderr are discarded. The result accepted by ActaKit is only the final JSON
value validated against the product contract.

This is defense in depth, not an assertion that `read-only` alone confines all
host reads. The stronger boundary is that Codex starts with a scratch working
home/directory containing only the bounded page attachment, static output schema
and result target; the original PDF is deleted before executor handoff.

## Rendering and egress

Rendering happens locally through trusted Poppler `pdfinfo` + `pdftoppm` at a
fixed DPI. The adapter validates page count and projected megapixels before
rendering and caps the resulting PNG size.

Only the rendered page PNG is document source material handed to the egress
executor. `process_run_egress.bytes_egressed` is therefore defined operationally
as **source/evidence payload bytes handed to the external executor**, not total
on-wire protocol traffic. This quantity is reproducible and privacy-relevant;
Codex transport framing/compression is intentionally not guessed.

A cloud-capable processor may fail *before* executor handoff. Such an attempt must
still retain its terminal ProcessRun and egress-policy provenance with
`bytes_egressed = 0`. This requirement exposed a generic prerelease schema bug and
requires a minimal `0001` rebaseline from `> 0` to `>= 0`.

## Request authorization

Before any cloud invocation, all of the following must match trusted adapter
configuration:

```text
egress.allowed = true
policy_profile != no_egress
data_control_profile != no_egress
endpoint_profile = openai_codex_subscription
request_template_hash = exact product prompt SHA-256
configuration_hash = exact adapter configuration SHA-256
```

The Workbench registry already excludes egress processors for restricted
Artifacts. The adapter adds no credential fields and no mechanism to override a
provider URL, executable, model path or command flags from document data.

## Prompt/output contract

The prompt requests document representation processing only:

- exact visible transcription;
- no civic interpretation/entities/claims;
- no normalization or invented unreadable text;
- uncertainty recorded explicitly;
- table rows only when visually supported;
- schema-only output.

The schema permits exactly one page object:

```text
page_id
transcription
uncertain_spans[]
tables[].rows[][]
```

All arrays/strings and total result bytes are bounded.

Canonical derivatives:

```text
transcription -> Representation kind transcript / text/plain UTF-8
tables        -> Representation kind table / application/json UTF-8
```

Both inherit the source Representation language when known. Empty valid output
creates no material derivative and cannot be accepted.

## QualityEvidence / policy

Registered signals:

```text
core.output_nonempty:v1
multimodal.schema_valid:v1
multimodal.uncertain_span_count:v1
multimodal.uncertain_spans:v1
multimodal.transcription_character_count:v1
multimodal.table_count:v1
```

There is no universal confidence. The existing reference policy accepts visual
transcription only when the schema is valid, uncertainty count is zero, and a
material derivative exists. Otherwise it ends in `QUARANTINE_REVIEW`; there is
no automatic rung after Codex in the reference path.

## Resource/security bounds

- one page / one scope per ProcessRun;
- bounded input PDF, document page count, rendered megapixels, PNG bytes and JSON output;
- bounded transcription/uncertainty/table structure;
- local render timeout, Codex timeout and whole-attempt deadline;
- Codex launched in a new POSIX process group and killed as a group on timeout;
- local helper environment is deterministic/minimal;
- Codex environment contains only locale, minimal PATH, private HOME/TMPDIR,
  dedicated CODEX_HOME, and narrowly required keyring/TLS plumbing;
- API keys, proxy variables, arbitrary CODEX_* variables and account identity are
  not inherited;
- no direct SQLite/archive writes from the processor.

## Certification standard

The implementation environment has no Codex CLI/auth and therefore does not
self-certify this cloud adapter. Independent certification must use the exact
qualified Codex CLI/model and exact SQLite 3.53.4 runtime, then run two bounded
public civic pages:

1. TSE skew/noise controlled page with independent text + table truth;
2. exact-hash Esparza page 4 with independent natural-layout truth.

The certification candidate must remain immutable.
