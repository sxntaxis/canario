# PROCESSOR-CODEX-001 — independent certification request

**Expected parent HEAD:** `49d337ddbfae0be32a351e5adb37063bbaabe528`  
**Candidate state:** `PROCESSOR_CODEX_001_IMPLEMENTED__CERTIFICATION_PENDING`  
**Candidate `0001` SHA256:** `5226c873487d9bd05fc62b7a1f323d6e804b003cc4e08bd2fe2b531adb6057bb`

Treat the candidate as immutable. A certification failure is reported, not
patched in place.

## Required runtime/executor

```text
registered upstream SQLite 3.53.4 exact source ID
Codex CLI 0.149.0
model gpt-5.6-sol
Poppler pdfinfo/pdftoppm coherent version
dedicated non-default CODEX_HOME, mode 0700 on POSIX
OS keyring auth owned by Codex CLI
no auth.json/config.toml/user skills in that profile
bundled skills disabled for the transcription exec
```

Do not inspect or print credential/account values.

## Mandatory real production proof

Generate the existing TSE controlled variants and run:

```bash
python notebook/implementation/prove_processor_codex_001.py \
  --codex-home "$ACTAKIT_CODEX_HOME" \
  --controlled-variants "$WORK/control/controlled-variants.json" \
  --natural-esparza /exact/hash-verified/esparza.pdf
```

The proof performs only two source-page Codex attempts:

1. TSE skew/noise controlled page: exact required-span recall `1.0`, CER <= `0.03`,
   exact independently curated table-row recall `1.0`, cell fidelity `1.0`, zero
   uncertain spans;
2. natural Esparza page 4: exact source SHA256, required-span recall `1.0`,
   CER <= `0.03`, zero uncertain spans.

Both must pass through the production Workbench/Writer path and retain positive
source-attachment egress bytes plus exact model/config/template/policy provenance.

## Schema/regression gate

Repeat exact-runtime migration-spec/freeze/storage proofs and the entire project
test suite. This simultaneously certifies the minimal prerelease
`bytes_egressed >= 0` rebaseline and proves DIRECT/OCR/Workbench regressions
remain green.

Do not create `0002`.

## Required security audit

Verify at minimum:

- exactly one `pdf_page:v1`; no whole/multi-page cloud run;
- restricted/no-egress is rejected before Codex invocation;
- endpoint/profile/template/config identities must match;
- source PDF is absent before Codex starts;
- child HOME is private scratch and CODEX_HOME is dedicated;
- no auth.json/config/user/admin skills are accepted;
- CLI user config/rules ignored; shell, multi-agent, plugins/apps, web/browser/
  computer/image-generation surfaces disabled using only Codex 0.149.0-qualified
  config keys; `features.view_image=false` is present and unsupported
  `tools.view_image`/redundant `tools.web_search` overrides are absent; lifecycle hooks are disabled; the exact static Codex override list contributes to `configuration_hash`;
- stdout/stderr are not canonical logs;
- subprocess does not inherit API keys/proxies/arbitrary CODEX_* values;
- local rendering and cloud execution have byte/page/megapixel/output/time limits;
- timeout terminates Codex process group;
- schema-invalid/uncertain/empty material cannot be accepted;
- pre-egress failure truthfully records `0` source bytes;
- post-handoff failure records bounded attachment bytes;
- no credentials/account/quota data enters SQLite/Representations/QualityEvidence;
- replay cannot issue a duplicate cloud request;
- no provider-API/Docling/local-VLM adapter was added.

Only then promote to:

```text
PROCESSOR_CODEX_001_CODEX_CLI_SUBSCRIPTION_IMPLEMENTED_AND_CERTIFIED
```
