# D1 v9 Closure Audit

**Verdict:** `CLOSURE_LOCAL_REPAIRS_ONLY`  
**Hard findings:** 3  
**Systemic class found:** no

## Custody and independence

- Fixture: `CR-ESPARZA-MINUTES-001`
- Candidate commit: `807c49c7768f435405b760104fb90a14e5b06064`
- Candidate tree: `2cd668be6d1ad1c54d4b0874001a8d0ffa660a31`
- Reference: `88bf2160fd286116bd9501778b03b39febdac5bedfc9be02355c3b18541b40a7` (3848773 bytes; 788 facts; 2031 evidence targets)
- Frozen source representation: `02d1578cfc44097c6e5e802880919ff6f7a18bd2105330035959c4cccd467ea1` (154866 bytes; 151940 characters; 61 units)
- Reviewer: OpenAI / GPT-5.6 Sol
- `independence_strength = WEAK_OR_UNKNOWN`
- `strong_independent_gate_satisfied = false`
- `human_independent_gate_satisfied = false`

## Phase 1 — full source→reference sweep

Completed **61/61** units. Checkpoint SHA256: `71086f41146e2cfee52e704662e17fa991e143a8a3f9a4eee582d75495242720`.

### D1-V9-CLOSURE-P1-0001 — PROCEDURAL_ACTION_AGENT_OMISSION

- Direction: `SOURCE_TO_REFERENCE`
- Affected fact IDs: `D1-F0074`, `D1-F0075`, `D1-F0076`, `D1-F0077`
- Evidence: `U0014` chars `20115–20385`
- Problem: The index preserves the proposed response content and the invoice attachment, but omits Olivier López’s procedural direction that the Secretaría be the actor that responds to the Contraloría in those terms.
- Source-grounded reason: The source explicitly assigns the response action to “la Secretaría”. D1-F0074–D1-F0076 encode what should be communicated and D1-F0077 encodes the attachment, but none preserves that response-agent assignment. The later formal agreement likewise preserves Concejo communication plus the Secretaría attachment, not this discussion-level direction that the Secretaría respond.
- Systemic-class candidate: no

### D1-V9-CLOSURE-P1-0002 — UNCERTAINTY_REASON_OMISSION

- Direction: `SOURCE_TO_REFERENCE`
- Affected fact IDs: `D1-F0084`
- Evidence: `U0015` chars `21382–21559`
- Problem: Flor Cubero’s explicit uncertainty that they did not know who filed the complaint—and its role as the reason direct response was problematic—is absent from the index.
- Source-grounded reason: D1-F0084 preserves Flor Cubero’s proposal to make the explanation reach the community and complainant(s), while D1-F0086–D1-F0088 separately preserve Olivier López’s later possibilities about anonymity and who might know the complainant. None preserves Flor’s own “no sabemos quién la interpuso” uncertainty and reason.
- Systemic-class candidate: no

### D1-V9-CLOSURE-P1-0003 — FORMAL_FINALITY_OMISSION

- Direction: `SOURCE_TO_REFERENCE`
- Affected fact IDs: none (missing standalone fact)
- Evidence: `U0061` chars `151623–151762`
- Problem: The formal adjournment of the session, including its 21:07 time and 18 May 2026 date, is not represented by any canonical fact.
- Source-grounded reason: The source explicitly records final procedural status and exact time/date. Searches across all 788 canonical semantic notes found no fact representing the session’s finalization or 21:07 adjournment.
- Systemic-class candidate: no

## Phase 2 — stratified reverse audit

Completed **125/125** sampled legacy facts. **0 hard reverse findings**; **0 suspected systemic classes**. Embedded evidence hash mismatches: **0**. Checkpoint SHA256: `7e1f599b9376bc914d5252e16fc3f1961afd4fc1df990397cfca4a607a341a02`.

## Phase 3 — v9 repair regression

Completed **10/10** regression rows. All ten prior v8 findings are `RESOLVED_IN_V9`; **0 hard regression findings**.

| # | Prior finding | v9 fact(s) | Classification |
|---:|---|---|---|
| 1 | `D1-V8-S02-IR-0001` | `D1-F0154`, `D1-F0832` | `RESOLVED_IN_V9` |
| 2 | `D1-V8-S02-IR-0002` | `D1-F0833` | `RESOLVED_IN_V9` |
| 3 | `D1-V8-S02-IR-0003` | `D1-F0714` | `RESOLVED_IN_V9` |
| 4 | `D1-V8-S02-IR-0004` | `D1-F0174` | `RESOLVED_IN_V9` |
| 5 | `D1-V8-S02-IR-0005` | `D1-F0194` | `RESOLVED_IN_V9` |
| 6 | `D1-V8-S03-IR-0001` | `D1-F0834` | `RESOLVED_IN_V9` |
| 7 | `D1-V8-S04-IR-0001` | `D1-F0360` | `RESOLVED_IN_V9` |
| 8 | `D1-V8-S04-IR-0002` | `D1-F0361` | `RESOLVED_IN_V9` |
| 9 | `D1-V8-S05-IR-0001` | `D1-F0835` | `RESOLVED_IN_V9` |
| 10 | `D1-V8-S06-IR-0001` | `D1-F0836` | `RESOLVED_IN_V9` |

## Systemic-class analysis

The three confirmed defects are localized and semantically distinct: one procedural response-agent omission, one uncertainty/reason omission, and one formal adjournment/finality omission. They do not establish at least three confirmed affected facts across at least two structures/source regions for the same underlying failure, and no shared unbounded authoring transformation is demonstrated by multiple confirmed examples.

## Recommended next action

```text
Perform one bounded source-only repair pass for exactly these findings.
Mechanically certify the repaired reference.
DO NOT run another broad D1 semantic audit.
Then proceed to governance closure/freeze decision.
```
