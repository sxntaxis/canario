# LECTOR-001 — independent certification request

**Expected parent HEAD:** `22790895a0e3a106127385d681975db73230990d`  
**Candidate state:** `LECTOR_001_IMPLEMENTED__CERTIFICATION_PENDING`  
**Required `0001` SHA256:** `5226c873487d9bd05fc62b7a1f323d6e804b003cc4e08bd2fe2b531adb6057bb`

Treat the candidate as immutable. A certification failure is reported, not patched
in place.

## Runtime gate

Use the registered exact upstream SQLite runtime:

```text
SQLite 3.53.4
source ID:
2026-07-24 19:02:57 bf7c7f30031888f4e796e429ab3978879485813aaca6f641c7b33e4e09459bcc
```

No Codex/model/network call is required for this certification.

## Mandatory deterministic proof

Under exact SQLite runtime run:

```bash
python notebook/research/pre-sql/schema/prove_runtime_contract.py
python notebook/research/pre-sql/schema/prove_migration_0001_spec.py
python notebook/research/pre-sql/schema/prove_migration_freeze.py
python notebook/research/pre-sql/schema/prove_storage_operations.py

PYTHONPATH=. pytest -q
PYTHONPATH=. pytest -q tests/test_lector_contracts.py tests/test_lector.py

python -m compileall -q actakit notebook/implementation
git diff --check
```

The focused suite must include the 300-Claim replay/volume proof and all authority,
locator, scope, egress and replay cases. Full-suite counts may grow only if the
candidate contains additional tests; failures are not accepted by weakening
coverage.

## Architecture/integrity audit

Verify at minimum:

1. `SemanticExtractor` receives no SQLite connection, archive writer, review or
   publication authority.
2. `LectorHost` checks replay before requiring the historical adapter to exist.
3. `LectorWriter` revalidates descriptor input/output/resource limits even after
   registry selection.
4. stable replay identity is ProcessRun + exact ordered inputs/config/egress policy,
   never claim text.
5. changed immutable replay identity is a hard collision.
6. canonical receipts preserve Claim/ClaimRevision and Relation/RelationRevision
   identity pairs.
7. every extracted Claim has evidence; source assertions require active
   supports/quotes evidence.
8. proposed selector JSON is typed/versioned and reopened against retained bytes.
9. proposed targets cannot expand a narrow ProcessRun scope.
10. locator creation and semantic rows commit/rollback atomically.
11. canonical duplicate detection occurs after selector normalization/reuse.
12. EntityMention observed text is preserved; same-name matching does not create or
    merge Entities.
13. resolution candidates reference existing Entities but do not create
    `MentionResolutionRevision`.
14. Tag assignments reference existing Tags; the extractor cannot invent vocabulary.
15. machine/rule attribution cannot directly resolve an Entity.
16. machine/rule direct Entity anchors remain candidate.
17. machine ClaimRelations remain candidate.
18. active rule relations require source-evidence or mechanical-identity basis.
19. source-evidence relations require exact `source_basis`.
20. symmetric ClaimRelations store one canonical direction.
21. claim_extract ClaimRelations reference only claims created in the same run.
22. Claim lifecycle derives from available/restricted custody, not backend choice.
23. failed ProcessRuns persist no semantic outputs; partial runs may preserve exact
    evidence-backed semantic output with bounded error code.
24. no review table is written by LECTOR-001; machine-only is not synthetic approval.
25. restricted input cannot egress.
26. egress extractors require explicit authorization and actual byte count; zero is
    valid before handoff.
27. non-egress extractors cannot report egress bytes.
28. credentials/account identity are absent from request/result/persistence contracts.
29. result counts are bounded for claims/evidence/mentions/candidates/tags/anchors/
    relations/basis targets.
30. concurrent same-run execution yields one canonical semantic batch, while docs do
    not overclaim exactly-once external invocation.
31. 300 machine-only claims can persist/replay without fabricated human review or
    duplicate explosion.
32. `0001` and `MIGRATION_0001_SPEC.sql` remain exact and no `0002` exists.
33. existing WORKBENCH/DIRECT/OCR/CODEX and ingress/deposit regressions remain green.
34. no real LLM/backend-specific claim-extraction policy is smuggled into this generic
    boundary.

Required result:

```text
34/34 LECTOR-001 ARCHITECTURE/INTEGRITY PASS
```

Only then promote to:

```text
LECTOR_001_SEMANTIC_EXTRACTION_BOUNDARY_IMPLEMENTED_AND_CERTIFIED
```
