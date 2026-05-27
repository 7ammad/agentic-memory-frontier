# Agentic Memory Frontier

Research and build workspace for Causal Experience Memory.

The core thesis:

> Memory is not storage. Memory is verified experience that improves future action.

CEM-0 is the first kernel: it ingests agent traces, extracts typed candidate memories, validates them before storage, quarantines bad memories, promotes verified experience cards, and returns action briefs instead of raw memory dumps.

Current build focus:

- write-path quality;
- source-grounded Experience Atoms;
- contradiction and stale-memory quarantine;
- auditability and provenance;
- evals that compare against unvalidated memory baselines.

The public foundation is in [research/2026-05-27-plan-1-causal-experience-memory-foundation.md](research/2026-05-27-plan-1-causal-experience-memory-foundation.md).

The implementation kickoff spec is in [specs/2026-05-27-cem-0-memguard-kernel-spec.md](specs/2026-05-27-cem-0-memguard-kernel-spec.md).

## CEM-0 Quick Smoke

Run the current synthetic corruption eval:

```powershell
python scripts/run_synthetic_eval.py
```

Run tests:

```powershell
python -m pytest
```
