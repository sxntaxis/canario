# D1 v8 Sharded Semantic Reconciliation

## Verdict

`REFERENCE_DISPUTE`

`s01_reopening_blocker: RESOLVED`

The six sealed audit packets establish complete mechanical coverage: 61/61 frozen units, 783/783 reverse facts, 2,019/2,019 evidence targets, 241/241 forward mapping rows, and six contiguous non-overlapping core ranges covering `[0,151940)`. All shard ledgers were sealed before reference exposure and declare no prior-review-history exposure.

S01 was rerun from the immutable replacement evidence only. It reports 41/41 mappings, 156/156 reverse PASS, 384/384 targets reopened and audited, zero findings, and PASS for all 12 listed prior-blocker facts. There is no unresolved S01 reopening blocker.

## Provenance

- v8 commit: `98ca3fbc84f6d35a0ba52068b98da4ea10ec1aad`
- v8 reference SHA256: `c440c76a70c31107f47d3df91701d971a75c18341ec2a8b41e328c801473a6db`
- v8 bundle SHA256: `53a5c3a7c1d375cfa43d71ec6c93cec8b95be04c4b79bd851d85a629b166e8ec`
- representation SHA256: `02d1578cfc44097c6e5e802880919ff6f7a18bd2105330035959c4cccd467ea1`
- kit authority-manifest SHA256: `17c2ca1c1ca7b01db6a5bd813a8ca839cff6e9d2112d858f4e1b5c07cadad7ec`
- global fact-index SHA256: `4961c17dd7263c7524d4e2363e6066be60d760e0dc1978dfb8e5647e89f2d51c`
- provisional blind merge SHA256: `3f704ff369b88eb6a4472ff8688169d1b1a1941e317cda5fc9245f907d40a080` (1,654 bytes)

S02-S06 evidence was consumed byte-for-byte from `unchanged-shards/`. The replacement S01 ledger and seal came only from `s01/`, and its audit only from `outputs/S01/`. The provisional blind merge was persisted before v7 history was opened. D1 v8 was not modified.

## Shard Coverage

| Shard | Assertions | Units | Facts | Targets | Verdict |
| --- | ---: | ---: | ---: | ---: | --- |
| S01 | 41 | 17 | 156 | 384 | `SHARD_PASS_NO_DISPUTES` |
| S02 | 33 | 8 | 89 | 227 | `REFERENCE_DISPUTE` |
| S03 | 67 | 10 | 142 | 379 | `REFERENCE_DISPUTE` |
| S04 | 36 | 7 | 88 | 256 | `REFERENCE_DISPUTE` |
| S05 | 27 | 9 | 165 | 428 | `REFERENCE_DISPUTE` |
| S06 | 37 | 10 | 143 | 345 | `REFERENCE_DISPUTE` |

S06 records 294 local-context reopens plus 51 exact resolver/provenance targets supplied out of local context and semantically sufficient. No shard reports an unresolved reopening blocker.

## Hard Findings

10 hard findings remain: 5 source-to-reference, 3 reference-to-source, and 2 both-direction. By type: 5 `MISSING_MATERIAL_ASSERTION`, 3 `MODALITY_ERROR`, and 2 `QUALIFIER_ERROR`.

| Finding | Direction | Type | Summary |
| --- | --- | --- | --- |
| S02-IR-0001 | source-to-reference | missing | F0154 omits offered lunch and confirmation channels. |
| S02-IR-0002 | source-to-reference | missing | F0156/F0157 omit the 30 May dance invitation. |
| S02-IR-0003 | both | modality | F0714 changes a request into completed confirmation. |
| S02-IR-0004 | reference-to-source | qualifier | F0174 adds an administrative limitation. |
| S02-IR-0005 | both | qualifier | F0194 omits Tercero's topic familiarity. |
| S03-IR-0001 | source-to-reference | missing | Omits that pending commission work remains. |
| S04-IR-0001 | reference-to-source | modality | F0360 changes considered-important ICE explanation into direct request. |
| S04-IR-0002 | reference-to-source | modality | F0361 changes considered-important ICE technical review into direct request. |
| S05-IR-0001 | source-to-reference | missing | Omits presidential CCCI-request direction. |
| S06-IR-0001 | source-to-reference | missing | Omits formal Futsala U-8 recognition-preparation transfer. |

## V8 Regression

All ten v7 accepted repairs pass regression: `D1-F0079`, `D1-F0493`, `D1-F0734`, `D1-F0810`, `D1-F0811`, `D1-F0827`, `D1-F0828`, `D1-F0830`, `D1-F0831`, and `D1-F0785` are each `PASS`. The ten current disputes are independent of that repair matrix.

## Independence And Blockers

Independence is `WEAK_OR_UNKNOWN`. Source-only sealing and delayed reference exposure support leakage control, but all six reviewers are Terra/OpenAI-family workers and do not establish strong material model/provider independence from the supervising author.

Blockers:

- Ten unresolved hard findings require reference adjudication or repair.
- Strong material independence is not established.
