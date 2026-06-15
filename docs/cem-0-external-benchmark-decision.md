# CEM-0 External Benchmark Decision

Date: 2026-05-27
Updated: 2026-06-15

Status: post-V2 external benchmark capability phase active

## Decision

Integrate real HaluMem dataset support now.

Keep MemoryArena and LongMemEval-V2 queued after HaluMem.

## Why

HaluMem is the closest external benchmark to the CEM-0 wedge. It decomposes memory evaluation into memory extraction, memory update, and memory question answering. That maps directly to CEM-0's current proof surface: prevent false, stale, unsupported, and contradictory memories from entering trusted operational experience.

MemoryArena and LongMemEval-V2 are relevant, but they test broader memory-action and environment-experience behavior. They should come after the HaluMem adapter because they need stronger action-loop and long-trajectory evaluation machinery.

## Source Check

- HaluMem repo: https://github.com/MemTensor/HaluMem
- HaluMem dataset card: https://huggingface.co/datasets/IAAR-Shanghai/HaluMem
- MemoryArena project: https://memoryarena.github.io/
- LongMemEval-V2 project: https://xiaowu0162.github.io/longmemeval-v2/
- LongMemEval-V2 dataset: https://huggingface.co/datasets/xiaowu0162/longmemeval-v2

## 2026-06-15 Reality Check

The first real downloaded public-data run exposed a structural zero: the
external runners inherited the marker-only `DeterministicExtractor`, so natural
language benchmark text produced no atoms and every downstream output was empty.
That result is now treated as a failed capability measurement, not a baseline.

Verified zero-output run:

- HaluMem local proxy: 0 proposed/trusted/output and 14,919 omitted reference
  memory points.
- MemoryArena local proxy: 0 proposed/trusted/output across 4,850 subtasks.
- LongMemEval-V2 local proxy: 0 proposed/trusted/output across 451 questions.

Repair direction:

- non-fixture external runners default to the grounded
  `NaturalLanguageExtractor`;
- deterministic marker extraction remains available only through fixture mode;
- answer-producing runners now synthesize local proxy answers from retrieved
  memory instead of comparing raw Action Brief actions as final answers;
- unified reports prefix proxy metrics with `local_proxy_*` and include official
  evaluator source/status fields;
- report generation fails on zero proposed/output counts unless the caller
  explicitly marks a fixture, proxy diagnostic, or no-extractor diagnostic.

## Current Implementation Slice

CEM-0 now has a local HaluMem adapter that:

- loads HaluMem-style JSON, JSONL, or directories of JSON/JSONL files;
- normalizes users, sessions, dialogue turns, memory points, update links, and QA evidence;
- converts HaluMem dialogue sessions into `AgentTrace` records for the kernel;
- scores candidate extracted memories against HaluMem reference memory points with extraction precision, recall, F1, hallucinated count, omitted count, update recall, and QA evidence recall;
- provides a reference upper-bound score for adapter sanity checks;
- includes a CLI smoke command:

```powershell
python scripts/run_halumem_adapter.py path\to\halumem.json
```

The HaluMem slice now also includes a CEM-backed runner:

```powershell
python scripts/run_halumem_cem0_eval.py path\to\halumem.json
```

That runner ingests HaluMem sessions as traces, runs CEM-0's current `ingest -> propose -> validate -> promote` write path, reports separate scores for proposed candidates versus final trusted memory, and synthesizes local proxy QA answers from retrieved trusted memory.

## What This Does Not Claim

This is not a published HaluMem benchmark score yet.

The current adapter and runner prove local ingestion, write-path execution,
local proxy extraction scoring, and local proxy QA scoring against the
official-style schema. A real HaluMem benchmark result still requires the
released HaluMem eval toolkit, its memory-system wrapper contract, and the
required model/service credentials.

## MemoryArena Adapter Slice

CEM-0 also has a local MemoryArena-style adapter that:

- loads MemoryArena JSON, JSONL, or directories of JSON/JSONL files;
- normalizes task `id`, ordered `questions`, expected `answers`, and optional `backgrounds`;
- converts each task into an `AgentTrace` with task questions and answer feedback;
- scores predictions with progress score and task success rate;
- provides a reference upper-bound score for adapter sanity checks;
- includes a CLI smoke command:

```powershell
python scripts/run_memoryarena_adapter.py path\to\memoryarena.json --domain bundled_shopping
```

The MemoryArena slice now also includes a CEM-backed runner:

```powershell
python scripts/run_memoryarena_cem0_eval.py path\to\memoryarena.json --domain bundled_shopping
```

That runner ingests MemoryArena tasks as traces, runs CEM-0's current write path, retrieves Action Brief recommendations for each task, synthesizes local proxy answers from retrieved memory, and scores those answers against expected subtask answers.

This is not a full MemoryArena result yet. It is the local adapter and proxy
runner layer needed before wiring the official MemoryArena environment gym and
agent loop.

## LongMemEval-V2 Adapter Slice

CEM-0 also has a local LongMemEval-V2 adapter that:

- loads a dataset root with `questions.jsonl`, `trajectories.jsonl`, and optional `haystacks/*.json`;
- normalizes questions, environments, question types, trajectory states, browser actions, screenshots, and haystack maps;
- converts trajectories into `AgentTrace` records with observation and action turns;
- scores exact answer predictions against reference answers;
- scores retrieval outputs against configured haystack membership;
- provides a reference upper-bound score for adapter sanity checks;
- includes a CLI smoke command:

```powershell
python scripts/run_longmemeval_v2_adapter.py path\to\longmemeval-v2
```

The LongMemEval-V2 slice now also includes a CEM-backed runner:

```powershell
python scripts/run_longmemeval_v2_cem0_eval.py path\to\longmemeval-v2
```

That runner ingests LongMemEval-V2 trajectories as traces, runs CEM-0's current write path, retrieves Action Brief evidence for each question, synthesizes local proxy answers, and scores both exact answers and retrieved trajectory IDs against the configured haystack.

This is not a full LongMemEval-V2 benchmark result yet. It is the local adapter
and proxy runner layer needed before CEM-0 can run the official evaluator,
checksum validation, answer evaluator, and latency runner.

## Unified External Report Slice

CEM-0 now has a unified external benchmark report object and CLI:

```powershell
python scripts/run_external_benchmark_report.py --halumem-result halumem.json --memoryarena-result memoryarena.json --longmemeval-v2-result longmemeval.json --markdown
```

The report combines saved CEM-backed runner outputs into one machine-readable
object with suite counts, proposed/trusted/quarantined totals, local-proxy
primary metrics, secondary metric maps, validation reason-code counts, and
official-evaluator provenance fields. It is a reporting layer over local proxy
runner output, not a claim of official benchmark performance.
