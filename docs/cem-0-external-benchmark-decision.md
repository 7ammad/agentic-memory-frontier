# CEM-0 External Benchmark Decision

Date: 2026-05-27

Status: HaluMem first

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

That runner ingests HaluMem sessions as traces, runs CEM-0's current `ingest -> propose -> validate -> promote` write path, and reports separate scores for proposed candidates versus final trusted memory.

## What This Does Not Claim

This is not a published HaluMem benchmark score yet.

The current adapter and runner prove local ingestion, write-path execution, and scoring against the official-style schema. A real benchmark result still requires running CEM-0 or a wrapped memory system over the downloaded HaluMem dataset and comparing against baselines.

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

This is not a full MemoryArena result yet. It is the local adapter layer needed before wiring real agent execution and CEM-0 action-brief ablations over MemoryArena tasks.

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

This is not a full LongMemEval-V2 benchmark result yet. It is the local adapter layer needed before CEM-0 can compare action briefs, raw trajectory retrieval, and unvalidated memory against the real web-environment tasks.
