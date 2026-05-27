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

The default extractor and contradiction detector are deterministic strategies for reproducible CEM-0 fixtures. They are replaceable kernel interfaces, not the final reasoning layer.

The public foundation is in [research/2026-05-27-plan-1-causal-experience-memory-foundation.md](research/2026-05-27-plan-1-causal-experience-memory-foundation.md).

The implementation kickoff spec is in [specs/2026-05-27-cem-0-memguard-kernel-spec.md](specs/2026-05-27-cem-0-memguard-kernel-spec.md).

## CEM-0 Quick Smoke

Run the current synthetic corruption eval:

```powershell
python scripts/run_synthetic_eval.py
```

Current expected signal:

```json
{
  "proposed_count": 4,
  "quarantined_count": 2,
  "promoted_count": 2,
  "false_memory_resistance": 1.0,
  "contradiction_recall": 1.0,
  "false_quarantine_rate": 0.0,
  "unvalidated_memory": {
    "trusted_false_memory_count": 2,
    "metrics": {
      "promoted_count": 4,
      "action_brief_card_count": 4
    }
  },
  "cem0_validation": {
    "trusted_false_memory_count": 0,
    "metrics": {
      "promoted_count": 2,
      "action_brief_card_count": 2
    }
  }
}
```

Run tests:

```powershell
python -m pytest
```
