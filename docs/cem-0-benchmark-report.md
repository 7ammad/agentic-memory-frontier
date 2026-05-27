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
| time_aware_vector_memory | 0 | 0 | 3 | 10 | 0.47 | 0 | 0.833 | 0.4 | 0.75 | 0 | 0 | 0 | 0 |
| raw_trace_retrieval | 0 | 0 | 7 | 18 | 0 | 0 | 1 | 0.611 | 0 | 0 | 0 | 0 | 0 |
| summary_reflection | 0 | 0 | 5 | 13 | -0.061 | 0 | 0.667 | 0.615 | 0.25 | 0 | 0 | 0 | 0 |
| unvalidated_memory | 18 | 0 | 7 | 14 | 0.364 | 0 | 1 | 0.5 | 1 | 1 | 0 | 1 | 0 |
| human_curated_runbook | 0 | 0 | 0 | 6 | 1 | 1 | 1 | 0 | 1 | 1 | 0 | 0 | 0 |
| cem0_validation | 18 | 6 | 0 | 6 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | 2 | 1 |

## CEM-0 Deltas

| Baseline | False memory resistance delta | Expected action delta delta | Workflow success delta | Trusted false memory reduction | Action brief card reduction |
| --- | ---: | ---: | ---: | ---: | ---: |
| no_memory | 1 | 1 | 1 | 0 | -6 |
| full_context | 1 | 1 | 1 | 7 | 12 |
| vanilla_vector_memory | 1 | 0.53 | 1 | 3 | 4 |
| time_aware_vector_memory | 1 | 0.53 | 1 | 3 | 4 |
| raw_trace_retrieval | 1 | 1 | 1 | 7 | 12 |
| summary_reflection | 1 | 1.061 | 1 | 5 | 7 |
| unvalidated_memory | 1 | 0.636 | 1 | 7 | 8 |
| human_curated_runbook | 0 | 0 | 0 | 0 | 0 |

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
| time_aware_vector_memory | no | Recency changes which stale action is retrieved but still misses the test instruction and keeps contradictions. |
| raw_trace_retrieval | no | Retrieves useful actions but also polluted, stale, and contradictory actions. |
| summary_reflection | no | Drops one required action and keeps several polluted actions. |
| unvalidated_memory | no | Promotes useful actions but also trusts false and stale actions. |
| human_curated_runbook | yes | Curated upper bound contains exactly the required actions. |
| cem0_validation | yes | Keeps the required actions and suppresses the polluted ones. |

## Extraction Quality

Extraction quality is measured against the synthetic fixture labels before validation. It is only meaningful for runs that propose candidate atoms.

| Run | Precision | Recall | F1 |
| --- | ---: | ---: | ---: |
| no_memory | 0 | 0 | 0 |
| full_context | 0 | 0 | 0 |
| vanilla_vector_memory | 0 | 0 | 0 |
| time_aware_vector_memory | 0 | 0 | 0 |
| raw_trace_retrieval | 0 | 0 | 0 |
| summary_reflection | 0 | 0 | 0 |
| unvalidated_memory | 1 | 1 | 1 |
| human_curated_runbook | 0 | 0 | 0 |
| cem0_validation | 1 | 1 | 1 |

## Contradiction Detection

Contradiction precision is measured over validator decisions. The denominator is every atom labeled with the `contradiction` reason code; the numerator is only fixture-labeled true contradictions. The scoped `report_format=csv` and `report_format=json` memories are the current negative-control pair: same key, different domains, no contradiction label.

| Run | Precision | Recall |
| --- | ---: | ---: |
| no_memory | 0 | 0 |
| full_context | 0 | 0 |
| vanilla_vector_memory | 0 | 0 |
| time_aware_vector_memory | 0 | 0 |
| raw_trace_retrieval | 0 | 0 |
| summary_reflection | 0 | 0 |
| unvalidated_memory | 0 | 0 |
| human_curated_runbook | 0 | 0 |
| cem0_validation | 1 | 1 |

## Memory Harm

Memory harm rate is the fraction of recommended actions that are false, stale, expired, or out of scope for the held-out task. It is action-facing: a memory only counts as harmful here if it reaches the brief.

| Run | Harm rate |
| --- | ---: |
| no_memory | 0 |
| full_context | 0.611 |
| vanilla_vector_memory | 0.4 |
| time_aware_vector_memory | 0.4 |
| raw_trace_retrieval | 0.611 |
| summary_reflection | 0.615 |
| unvalidated_memory | 0.5 |
| human_curated_runbook | 0 |
| cem0_validation | 0 |

## Action Influence

Action influence rate is the fraction of held-out decisive actions present in the brief. It does not imply success by itself: baselines can include decisive actions and still fail if harmful memory pollutes the same brief.

| Run | Influence rate |
| --- | ---: |
| no_memory | 0 |
| full_context | 1 |
| vanilla_vector_memory | 0.667 |
| time_aware_vector_memory | 0.667 |
| raw_trace_retrieval | 1 |
| summary_reflection | 1 |
| unvalidated_memory | 1 |
| human_curated_runbook | 1 |
| cem0_validation | 1 |

## Latency

The synthetic eval now emits `p95_write_latency_ms` and `p95_retrieval_latency_ms` for every run. Values are local-run dependent, so this static report does not pin exact milliseconds. The write-path samples cover CEM ingestion, proposal, validation, promotion, and unvalidated card writes. The retrieval samples cover action-selection or Action Brief generation.

## Token Accounting

The synthetic eval now emits `tokens_per_write` and `tokens_per_retrieval`. These are deterministic regex-token counts over the local fixture, not vendor billing tokens. They are useful for regression comparison while the extractor is marker-based.

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
| time_aware_vector_memory | 0 | 0 | 0 |
| raw_trace_retrieval | 0 | 0 | 0 |
| summary_reflection | 0 | 0 | 0 |
| unvalidated_memory | 0 | 0 | 1 |
| human_curated_runbook | 0 | 0 | 0 |
| cem0_validation | 1 | 1 | 2 |

## Interpretation

The current result supports a narrow CEM-0 claim:

> On the local synthetic corruption suite, CEM-0 prevents the fixture's known false, stale, unsupported, poisoned, contradictory, and non-causal memories from becoming trusted action guidance, while preserving enough verified experience to pass the held-out workflow check.

This is useful because the unvalidated-memory baseline sees the same candidate memories but trusts all of them. It has full relevant coverage, yet still fails because harmful memories pollute the action brief.

## External Benchmark Adapter

The HaluMem decision is locked in [cem-0-external-benchmark-decision.md](cem-0-external-benchmark-decision.md): HaluMem comes first because it directly tests extraction, update, and QA hallucination at the write-path layer.

CEM-0 now includes a local HaluMem adapter that can load JSON, JSONL, or directories of JSON/JSONL files, normalize sessions and memory points, convert sessions into `AgentTrace` records, and score candidate extracted memories against HaluMem reference memory points.

Smoke command:

```powershell
python scripts/run_halumem_adapter.py path\to\halumem.json
```

CEM-backed write-path command:

```powershell
python scripts/run_halumem_cem0_eval.py path\to\halumem.json
```

CEM-0's HaluMem runner ingests HaluMem sessions as traces, runs `ingest -> propose -> validate -> promote`, and reports separate proposed-candidate and trusted-memory extraction scores.

CEM-0 also includes a local MemoryArena-style adapter that can load JSON, JSONL, or directories of JSON/JSONL files, normalize ordered subtasks from `questions`, `answers`, and `backgrounds`, convert tasks into `AgentTrace` records, and score predictions with progress score and task success rate.

Smoke command:

```powershell
python scripts/run_memoryarena_adapter.py path\to\memoryarena.json --domain bundled_shopping
```

CEM-backed action-brief command:

```powershell
python scripts/run_memoryarena_cem0_eval.py path\to\memoryarena.json --domain bundled_shopping
```

CEM-0's MemoryArena runner ingests tasks as traces, runs the write path, retrieves Action Brief recommendations, and scores those recommendations against expected subtask answers.

CEM-0 also includes a local LongMemEval-V2 adapter that loads a dataset root with `questions.jsonl`, `trajectories.jsonl`, and optional `haystacks/*.json`, converts trajectories into `AgentTrace` records, and scores exact answers plus haystack-member retrieval.

Smoke command:

```powershell
python scripts/run_longmemeval_v2_adapter.py path\to\longmemeval-v2
```

## Not Proven Yet

The current report does not prove:

- external HaluMem performance;
- MemoryArena performance;
- LongMemEval-V2 performance;
- action influence measurement from real agent traces;
- vendor token-cost claims.

Those remain unchecked in `TODO.md`.

## Next Required Work

To move from V0 synthetic proof toward a stronger CEM-0 proof:

1. Run the CEM-backed HaluMem runner on the downloaded real dataset and compare proposed versus trusted memory scores.
2. Add CEM-backed MemoryArena and LongMemEval-V2 runners for action-coupling and trajectory-retrieval ablations.
3. Replace marker extraction only after the deterministic suite is strong enough to protect behavior.
