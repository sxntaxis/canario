# Civic Processor Bench — closure evidence for WORKBENCH-001

Public benchmarks establish that strong processors exist; they do not answer which stack is best for
ActaKit's civic sources. Build a small, adversarial, legally usable fixture corpus before production
processor implementation is frozen.

## Minimum corpus

1. born-digital Esparza acta PDF;
2. multi-column digital PDF;
3. table-heavy municipal PDF;
4. clean image-only scan;
5. skewed/rotated/noisy scan;
6. low-DPI photocopy;
7. mixed native-text + scanned-page PDF;
8. image-only PDF with stamps/signatures;
9. handwriting-heavy note/form/receipt-like civic material when lawfully available;
10. malformed/truncated PDF;
11. DOCX with headings/lists/tables;
12. XLSX/CSV with multiple tables/sheets;
13. HTML with meaningful hierarchy/links;
14. later: audio/video only when a real source enters scope.

## Ground truth

For each applicable fixture retain:

- normalized text excerpts and must-not-invent spans;
- page/word/block anchors where practical;
- expected reading order;
- key tables with row/cell truth;
- expected warnings/escalation decision;
- expected no-output/unsupported behavior for malformed material.

## Metrics

- normalized edit distance / CER / WER;
- page/content coverage and false insertion rate;
- reading-order error;
- table TEDS/structure/cell fidelity;
- coordinate/locator reopenability;
- hallucinated or fabricated text/fields;
- deterministic replay stability where the backend is deterministic;
- runtime, peak memory, GPU/CPU requirement and artifact-size expansion;
- escalation frequency and per-rung marginal cost;
- provenance completeness;
- cloud monetary cost, request count, latency and bytes/pages sent off-device;
- provider endpoint/retention mode recorded for each cloud run;
- host-local compute avoided by cloud escalation (wall time/RAM/VRAM comparison);
- failure isolation: original custody must survive all failures.

## Comparative runs

At minimum compare:

- Poppler native extraction;
- OCRmyPDF + Tesseract;
- Docling default structured pipeline;
- Docling with selected OCR backend on scans;
- PaddleOCR-VL on hard-document subset;
- Qwen3-VL-family local candidate on handwriting/weird-visual subset;
- official Codex CLI with ChatGPT subscription on the **same** explicitly egress-safe hard subset;
- optional Mistral OCR specialist on an explicitly egress-safe document subset;
- an OpenAI-compatible endpoint capability test (local vLLM or equivalent) to verify the transport escape hatch without assuming feature parity;
- pdfplumber diagnostics on table fixtures;
- MinerU/Marker as comparator runs where installation/license permits.


## Execution-venue comparison

For the difficult visual subset, report two paths separately:

```text
best local path
vs
best cloud path allowed by source policy
```

Do not manufacture a winner by forcing both through identical hardware assumptions. Record exact
model/provider snapshot, input rendering strategy, prompt/schema template, local hardware, cloud cost,
latency and egress bytes/pages. A cloud path is allowed to win because the target host is weak; a local
path is allowed to win because egress is forbidden or quality/cost is better.

The reference cloud run uses the official Codex CLI authenticated by the operator's ChatGPT subscription.
The CLI owns authentication and remote execution; the bench never reads or persists credential material.
Benchmark artifacts record only non-secret executor/model/request-template identity, selected input hashes,
egress bytes and execution policy. Separate OpenAI and Mistral API billing are optional future venues, not
requirements for the reference deployment.

## Bench implementation status

The executable research harness now lives at `notebook/research/workbench/processors/bench/`. Its first
controlled civic fixture uses the official TSE Esparza mayoralties page with manually curated truth and
deterministic scan/mixed/malformed derivatives. The initial Poppler/Tesseract/pdfplumber run is recorded
in `bench/results/local-controlled-baseline.json`; see `bench/BENCH_STATUS.md` for measured findings.

This closes the benchmark mechanics and the current generic-boundary evidence gate. It does not claim
the minimum corpus is representative of every civic format or that optional backends are selected.

## Gate

Freeze the generic Processor ladder only with a decision table covering the enabled reference path,
execution-venue policy, resource/egress budgets and explicit residual gaps. Optional backend pins and
quality thresholds remain per-deployment work. The current D4/D5 decision explicitly prefers bounded
Codex cloud escalation for approved public material on weak hosts, while no-egress deployments remain
local or human-review only.

## Current execution checkpoint

The controlled D1 baseline remains reproduced. D2 OCRmyPDF/Tesseract has corrected
page-level quality and process-tree RSS evidence. Official Codex CLI has a
schema-valid controlled run plus scored and diagnostic natural public pages with
independent truth for two pages. Spreadsheet structure is directly evidenced.
Docling footprint evidence records it as optional, not default. The result is
freeze-ready for the generic boundary, with specialized follow-up gaps recorded.
