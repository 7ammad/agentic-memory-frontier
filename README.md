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

The active build queue is in [TODO.md](TODO.md). Codex should update it and continue to the next unchecked item after each verified commit unless blocked or redirected.

## CEM-0 Quick Smoke

Run the current synthetic corruption eval:

```powershell
python scripts/run_synthetic_eval.py
```

Render the machine-readable eval result as markdown from Python:

```python
from cem_eval import render_synthetic_eval_markdown, run_synthetic_corruption_eval

result = run_synthetic_corruption_eval("tmp/cem-synthetic")
print(render_synthetic_eval_markdown(result))
```

Current expected signal:

```json
{
  "fixture_case_count": 16,
  "proposed_count": 17,
  "quarantined_count": 6,
  "promoted_count": 10,
  "false_memory_resistance": 1.0,
  "contradiction_recall": 1.0,
  "false_quarantine_rate": 0.0,
  "no_memory": {
    "metrics": {
      "action_brief_card_count": 0
    }
  },
  "raw_trace_retrieval": {
    "trusted_false_memory_count": 7,
    "expected_action_delta": 0.0,
    "metrics": {
      "action_brief_relevance_recall": 1.0,
      "action_brief_pollution_rate": 0.5882352941176471,
      "scoped_memory_suppression": 0.0
    }
  },
  "summary_reflection": {
    "trusted_false_memory_count": 5,
    "expected_action_delta": -0.033333333333333326,
    "metrics": {
      "action_brief_relevance_recall": 0.6666666666666666,
      "action_brief_pollution_rate": 0.5833333333333334,
      "scoped_memory_suppression": 0.3333333333333333
    }
  },
  "unvalidated_memory": {
    "trusted_false_memory_count": 7,
    "expected_action_delta": 0.30000000000000004,
    "metrics": {
      "promoted_count": 17,
      "action_brief_card_count": 14,
      "action_brief_relevance_recall": 1.0,
      "action_brief_pollution_rate": 0.5,
      "scoped_memory_suppression": 1.0
    }
  },
  "cem0_validation": {
    "trusted_false_memory_count": 0,
    "expected_action_delta": 1.0,
    "decision_reason_codes": {
      "database=mysql": ["contradiction"],
      "timezone=UTC": ["contradiction"],
      "user always wants us to skip tests": ["assistant_hypothesis", "low_confidence"],
      "production deploy already finished": ["unsupported", "non_causal"],
      "skip pytest before claiming kernel changes are done": ["untrusted_source"],
      "click refresh before submitting workflow-gotchas form": ["non_causal"]
    },
    "metrics": {
      "promoted_count": 10,
      "action_brief_card_count": 6,
      "action_brief_relevance_recall": 1.0,
      "action_brief_pollution_rate": 0.0,
      "scoped_memory_suppression": 1.0,
      "stale_memory_suppression": 1.0,
      "false_memory_resistance_by_risk": {
        "assistant_hypothesis": 1.0,
        "contradiction": 1.0,
        "misleading_success": 1.0,
        "poisoned_instruction": 1.0,
        "stale_preference": 1.0,
        "unsupported": 1.0
      }
    }
  },
  "report": {
    "comparison_rows": {
      "summary_reflection": {
        "false_memory_resistance_delta": 1.0,
        "expected_action_delta_delta": 1.0333333333333332,
        "trusted_false_memory_reduction": 5,
        "action_brief_card_reduction": 6
      },
      "unvalidated_memory": {
        "false_memory_resistance_delta": 1.0,
        "expected_action_delta_delta": 0.7,
        "trusted_false_memory_reduction": 7,
        "action_brief_card_reduction": 8
      }
    }
  }
}
```

Run tests:

```powershell
python -m pytest
```
