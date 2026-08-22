# Civic Processor Bench — required before WORKBENCH-001 freeze

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
- OpenAI current multimodal model candidate on the **same** explicitly egress-safe hard subset;
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

The OpenAI run must use a host-provided API credential and never write the key into fixtures, benchmark
results or provenance. Benchmark artifacts record only non-secret provider/model/request-template identity
and the applicable provider data-control/retention profile observed for the run.

## Gate

Do not freeze or implement the production processor ladder until the benchmark produces a decision table
for each rung, including exact versions/models/licenses/providers, execution-venue policy, resource/egress
budgets and escalation thresholds. The final D4/D5 decision must explicitly state when a weak host should
prefer cloud instead of attempting heavyweight local AI.
Research can nominate candidates; Civic Processor Bench chooses the shipped defaults.
