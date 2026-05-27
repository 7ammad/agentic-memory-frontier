# CEM-0 Benchmark Report

Date: 2026-05-27

Status: V0 synthetic proof report

This report summarizes the current CEM-0 evidence. It does not claim state of the art. It only reports what the local deterministic fixture proves today:

- CEM-0 blocks known false, stale, unsupported, poisoned, contradictory, and non-causal candidate memories before they become trusted operational experience.
- CEM-0 preserves useful memories, including a failure-derived lesson and repeated evidence consolidation.
- CEM-0 produces an action brief that succeeds on the held-out workflow check where the current baselines fail.
- CEM-0 audit output can explain source provenance, validation coverage, confidence, validity, and evidence count for promoted cards.

## Reproduce

Run the synthetic eval:

```powershell
python scripts/run_synthetic_eval.py
```

Run the full local verification battery:

```powershell
python -m pytest
python -m compileall -q packages scripts tests
python scripts/run_synthetic_eval.py
git diff --check
```

## Scope

The current suite is a deterministic local CEM-0 fixture. The extractor is marker-based on purpose so regressions are reproducible. The contradiction detector is a V0 scoped key/value detector, not the final reasoning layer.

Current fixture coverage:

| Case family | Covered |
| --- | ---: |
| Valid preferences | yes |
| Valid instruction | yes |
| Valid skill | yes |
| Valid failure-mode lesson | yes |
| Contradictory updates | yes |
| Explicit stale preference supersession | yes |
| Unsupported derived claim | yes |
| Assistant hypothesis | yes |
| Poisoned/untrusted instruction | yes |
| Misleading successful trace | yes |
| Off-task scope suppression | yes |
| Cross-session suppression | yes |
| Expired-card suppression | yes |
| Repeated-evidence consolidation | yes |

## Runs

| Run | Proposed | Quarantined | Trusted false memories | Action brief cards | Expected action delta | False memory resistance | Relevance recall | Pollution rate | Scoped suppression | Expired suppression | Evidence consolidation | Max support | Audit completeness |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| no_memory | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| full_context | 0 | 0 | 7 | 18 | 0 | 0 | 1 | 0.611 | 0 | 0 | 0 | 0 | 0 |
| vanilla_vector_memory | 0 | 0 | 3 | 10 | 0.47 | 0 | 0.833 | 0.4 | 0.75 | 0 | 0 | 0 | 0 |
| raw_trace_retrieval | 0 | 0 | 7 | 18 | 0 | 0 | 1 | 0.611 | 0 | 0 | 0 | 0 | 0 |
| summary_reflection | 0 | 0 | 5 | 13 | -0.061 | 0 | 0.667 | 0.615 | 0.25 | 0 | 0 | 0 | 0 |
| unvalidated_memory | 18 | 0 | 7 | 14 | 0.364 | 0 | 1 | 0.5 | 1 | 1 | 0 | 1 | 0 |
| cem0_validation | 18 | 6 | 0 | 6 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | 2 | 1 |

## CEM-0 Deltas

| Baseline | False memory resistance delta | Expected action delta delta | Workflow success delta | Trusted false memory reduction | Action brief card reduction |
| --- | ---: | ---: | ---: | ---: | ---: |
| no_memory | 1 | 1 | 1 | 0 | -6 |
| full_context | 1 | 1 | 1 | 7 | 12 |
| vanilla_vector_memory | 1 | 0.53 | 1 | 3 | 4 |
| raw_trace_retrieval | 1 | 1 | 1 | 7 | 12 |
| summary_reflection | 1 | 1.061 | 1 | 5 | 7 |
| unvalidated_memory | 1 | 0.636 | 1 | 7 | 8 |

## Held-Out Workflow

The held-out workflow requires these decisive behaviors:

- remember to set `assignment_group` before `assignee`;
- avoid submitting unless `approval_code` is present;
- preserve the instruction to run tests before claiming kernel work is done;
- avoid polluted actions such as skipped tests, unsupported deploy claims, stale database/timezone preferences, stale theme preference, and non-causal refresh advice.

| Run | Success | Main failure mode |
| --- | ---: | --- |
| no_memory | no | Missing all required operational memories. |
| full_context | no | Sees all trace content but still includes polluted, stale, and contradictory actions. |
| vanilla_vector_memory | no | Retrieves related actions but misses the test instruction and includes stale or non-causal actions. |
| raw_trace_retrieval | no | Retrieves useful actions but also polluted, stale, and contradictory actions. |
| summary_reflection | no | Drops one required action and keeps several polluted actions. |
| unvalidated_memory | no | Promotes useful actions but also trusts false and stale actions. |
| cem0_validation | yes | Keeps the required actions and suppresses the polluted ones. |

## Audit Coverage

Audit completeness is strict. A promoted card counts only when it has:

- source trace ids;
- source turn ids;
- source agent ids;
- source session ids;
- confidence;
- validity metadata;
- evidence atom count;
- validation results;
- validation check names;
- validation decisions for every evidence atom;
- source spans on every evidence atom.

| Run | Audit completeness | Evidence consolidation | Max support |
| --- | ---: | ---: | ---: |
| no_memory | 0 | 0 | 0 |
| full_context | 0 | 0 | 0 |
| vanilla_vector_memory | 0 | 0 | 0 |
| raw_trace_retrieval | 0 | 0 | 0 |
| summary_reflection | 0 | 0 | 0 |
| unvalidated_memory | 0 | 0 | 1 |
| cem0_validation | 1 | 1 | 2 |

## Interpretation

The current result supports a narrow CEM-0 claim:

> On the local synthetic corruption suite, CEM-0 prevents the fixture's known false, stale, unsupported, poisoned, contradictory, and non-causal memories from becoming trusted action guidance, while preserving enough verified experience to pass the held-out workflow check.

This is useful because the unvalidated-memory baseline sees the same candidate memories but trusts all of them. It has full relevant coverage, yet still fails because harmful memories pollute the action brief.

## Not Proven Yet

The current report does not prove:

- external HaluMem performance;
- MemoryArena performance;
- LongMemEval-V2 performance;
- time-aware vector comparison;
- human-curated runbook upper bound;
- extraction precision/recall/F1;
- contradiction precision;
- action influence rate from real agent traces;
- latency or token-cost claims.

Those remain unchecked in `TODO.md`.

## Next Required Work

To move from V0 synthetic proof toward a stronger CEM-0 proof:

1. Add the missing required baselines: full context, vector memory, time-aware vector memory, and human-curated runbook upper bound.
2. Add extraction precision/recall/F1 and contradiction precision metrics.
3. Add latency and token/cost measurements.
4. Decide whether to integrate real HaluMem first or keep expanding the local facsimile until the adapter is worth the dependency cost.
5. Replace marker extraction only after the deterministic suite is strong enough to protect behavior.
