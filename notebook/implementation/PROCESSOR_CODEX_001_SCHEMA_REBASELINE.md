# PROCESSOR-CODEX-001 — prerelease `0001` egress rebaseline

**Parent certified `0001` SHA256:** `adf14a5006565197af3acf57c5cfc213510ba94217beb650403acbaf363b975a`  
**New candidate SHA256:** `5226c873487d9bd05fc62b7a1f323d6e804b003cc4e08bd2fe2b531adb6057bb`  
**State:** `IMPLEMENTED__INDEPENDENT_CERTIFICATION_PENDING`

## Defect found by first real egress backend

WORKBENCH-001 originally required:

```sql
bytes_egressed > 0
```

for every `process_run_egress` row. That assumption is wrong for a terminal
attempt whose selected processor is egress-capable but fails during local bounded
preparation before the external executor receives source material. Examples are:

```text
page out of range
render geometry over limit
local renderer failure
rendered attachment over byte limit
attempt deadline reached before executor handoff
```

Dropping the ProcessRun would lose exact attempted scope and failure provenance;
claiming positive bytes would falsify egress evidence.

## Rebaseline

The only SQL semantic change is:

```sql
bytes_egressed INTEGER NOT NULL CHECK (bytes_egressed >= 0)
```

Interpretation:

```text
0    = egress-capable attempt terminated before source/evidence payload handoff
> 0  = measured source/evidence payload bytes handed to external executor
```

The field is not total TCP/HTTP protocol traffic. Adapters must never fabricate
wire-byte precision they cannot observe.

No table, column, index, FK, target vocabulary or other schema shape changes.
Physical inventory remains:

```text
58 STRICT tables
3 FTS5 virtual tables
118 explicit indexes
127 FK child paths
0 FK child scans
```

No `0002` exists because ActaKit is pre-release.

## Regression proof

Workbench tests prove that a zero-byte failed cloud attempt:

- persists its exact ProcessRun and target;
- persists egress policy/data-control/template/endpoint identity;
- contains no derivative;
- replays without re-invoking the removed backend;
- rejects changed policy identity under the same ProcessRun ID.

Negative egress bytes still fail at the SQL and Python contract layers.

The previous WORKBENCH/DIRECT/OCR certifications remain historical evidence for
their candidate hash. Independent PROCESSOR-CODEX-001 certification must repeat
runtime/migration/storage and full regression tests against this new candidate
hash before it becomes current schema authority.
