# Quality evidence, not universal confidence

ActaKit must **not** define `confidence: float` as a cross-processor truth. Existing engines expose
fundamentally different signals and even projects that publish 0..1 scores warn that their numbers are
internal or model-specific.

## Proposed conceptual shape

```text
QualityEvidence
├── processor_id / processor_version / model_id
├── execution_venue      # deterministic_local | ml_local | cloud
├── provider_id? / endpoint_profile?   # non-secret identities only
├── scope               # document/page/block/time span
├── signal_name         # namespaced, stable ActaKit key
├── observed_value      # typed value or bounded JSON payload
├── interpretation      # optional processor-specific grade/warning
└── provenance          # ProcessRun + Representation locator

QualityDecision
├── ACCEPT
├── ESCALATE
└── QUARANTINE_REVIEW
```

The policy evaluator consumes multiple QualityEvidence rows plus format/source policy. It is allowed to
change across pre-release without rewriting source evidence.

## Useful signal families

- digital text: character/page coverage, replacement-character ratio, empty-page ratio, text-density anomalies;
- layout: reading-order violations, overlap/column anomalies, detected block coverage;
- OCR: Tesseract word-confidence distribution, orientation confidence, engine warnings, language plausibility;
- Docling: categorical `POOR/FAIR/GOOD/EXCELLENT` grades and named component grades; keep numeric internals namespaced;
- tables: row/column/cell structural checks, TEDS-like fixture score, impossible/empty cell ratios;
- multimodal AI: constrained-schema validity, missing/extra regions, cross-processor disagreement, hallucinated-token/field checks;
- cloud execution: provider/model/request-template identity, latency, reported usage/cost inputs, bytes/pages egressed, retention/data-control profile name;
- Mistral OCR: provider page/block/word confidence retained under provider namespace;
- ASR: language probability, avg log probability, no-speech probability, compression ratio, word probabilities, VAD coverage;
- diarization: covered speech time, overlaps, speaker-turn alignment with transcript timestamps.

## Policy examples

`ACCEPT` can mean “native text has high page coverage, sane Unicode and reopenable anchors”; it does not
mean “confidence > .92”. `ESCALATE` can be triggered by any documented failure mode. `QUARANTINE_REVIEW`
is correct when models disagree on consequential content or all automated rungs remain weak.

A later implementation may summarize typed evidence to an operator-facing grade, but the underlying
signals must remain inspectable and processor-attributable.


## Credentials are not QualityEvidence

API keys/tokens are bearer secrets and have no evidentiary value. They must never be stored in
QualityEvidence, ProcessRun configuration, SQLite, benchmark fixtures or logs. A future host may resolve a
non-secret credential slot/reference through environment variables, an OS secret service or deployment
secret manager; the resolved secret value stays outside the processor/provenance payload.

Likewise, `OpenAI-compatible` is transport metadata, not a quality grade. The actual provider/server/model
must still identify its capabilities and produce normal QualityEvidence.
