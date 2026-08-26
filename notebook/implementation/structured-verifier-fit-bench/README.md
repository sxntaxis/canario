# Structured Verifier Fit Bench

State: **measured; minimum Canario decomposition selected; locally certified**

Parent:

```text
0f9a71e5acb0f093469571d59c896eab0c03c4c2
```

This subtree is Phase D evidence only. It compares `simple_codex` with
`thucy_bounded_codex_runtime_adapted` over the exact deterministic Esparza projection and
hardened SQLite executor.

The current campaign uses the already qualified subscription-backed Codex pattern with
`gpt-5.6-terra` by default. Metered OpenAI API, OpenRouter and other provider profiles remain
architecturally allowed but deferred; this campaign has no automatic paid/API fallback.

The external Thucy package is not imported, executed, forked or vendored. Its exact prompts
are parsed at runtime from the verified external checkout.

Raw campaign outputs remain outside git. Phase D completed with zero semantic retries and no worker
failures. The design interpretation selects
`DECOMPOSITION_VALUE_PROVEN__DESIGN_MINIMUM_CANARIO_DECOMPOSITION`: evidence retrieval/backing
improved materially, while verdict accuracy did not and execution cost rose substantially.
`RESULTS.md` records the bounded decision and exact decision-relevant deltas. Deterministic
test, commit and bundle certification is local and recorded in the closure results.
