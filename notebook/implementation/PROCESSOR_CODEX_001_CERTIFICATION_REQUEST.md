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

Qualified v2 contract identities:

```text
request_template_hash: b10745051bffc0ddded6fd08e30a8947154ccb8e71dce4fd35d0a9c9c27fee84
output_schema_hash:     8c8c369cf18f4269c72ca2293db6cb3556d6db8a2f9f3f103dca16aa4543a72a
configuration_hash:     6650c221ee5ef2a0a499fe4af83e460ffaa715e883ed1049c4948b76f4eddc31
```

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
   independently curated table-row recall `1.0`, cell fidelity `1.0`,
   `false_cell_count == 0`, zero uncertain spans. Table-row recovery follows the
   frozen research metric: all expected cells must match in position; extra
   non-empty cells fail, while trailing empty padding is ignored;
2. natural Esparza page 4: exact source SHA256, required-span recall `1.0`,
   CER <= `0.03`, zero uncertain spans.

Both must pass through the production Workbench/Writer path and retain positive
source-attachment egress bytes plus exact model/config/template/policy provenance.
The TSE proof still compares complete page truth against the `transcript` derivative;
it must not reconstruct missing transcript text from the separate table derivative.

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
- `codex_visual_transcription_v2` requires page-complete transcript text including
  readable table cells, while `tables` remains supplemental structure;
- `multimodal.table_text_coverage:v1` is deterministic cross-channel evidence and
  any value below `1.0` fails as `codex_contract_invalid` with no derivative;
- pre-egress failure truthfully records `0` source bytes;
- post-handoff failure records bounded attachment bytes;
- no credentials/account/quota data enters SQLite/Representations/QualityEvidence;
- replay cannot issue a duplicate cloud request;
- no provider-API/Docling/local-VLM adapter was added.

Only then promote to:

```text
PROCESSOR_CODEX_001_CODEX_CLI_SUBSCRIPTION_IMPLEMENTED_AND_CERTIFIED
```
