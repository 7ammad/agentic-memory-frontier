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

The current V0 benchmark report is in [docs/cem-0-benchmark-report.md](docs/cem-0-benchmark-report.md).

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
  "fixture_case_count": 17,
  "proposed_count": 18,
  "quarantined_count": 6,
  "promoted_count": 11,
  "false_memory_resistance": 1.0,
  "contradiction_precision": 1.0,
  "contradiction_recall": 1.0,
  "false_quarantine_rate": 0.0,
  "no_memory": {
    "metrics": {
      "action_brief_card_count": 0,
      "audit_completeness_rate": 0.0
    }
  },
  "full_context": {
    "trusted_false_memory_count": 7,
    "expected_action_delta": 0.0,
    "metrics": {
      "action_brief_relevance_recall": 1.0,
      "action_brief_pollution_rate": 0.6111111111111112,
      "audit_completeness_rate": 0.0
    }
  },
  "vanilla_vector_memory": {
    "trusted_false_memory_count": 3,
    "expected_action_delta": 0.4696969696969697,
    "metrics": {
      "action_brief_card_count": 10,
      "action_brief_relevance_recall": 0.8333333333333334,
      "action_brief_pollution_rate": 0.4,
      "memory_harm_rate": 0.4,
      "scoped_memory_suppression": 0.75,
      "audit_completeness_rate": 0.0
    }
  },
  "time_aware_vector_memory": {
    "trusted_false_memory_count": 3,
    "expected_action_delta": 0.4696969696969697,
    "metrics": {
      "action_brief_card_count": 10,
      "action_brief_relevance_recall": 0.8333333333333334,
      "action_brief_pollution_rate": 0.4,
      "memory_harm_rate": 0.4,
      "scoped_memory_suppression": 0.75,
      "audit_completeness_rate": 0.0
    }
  },
  "raw_trace_retrieval": {
    "trusted_false_memory_count": 7,
    "expected_action_delta": 0.0,
    "metrics": {
      "action_brief_relevance_recall": 1.0,
      "action_brief_pollution_rate": 0.6111111111111112,
      "scoped_memory_suppression": 0.0,
      "expired_memory_suppression": 0.0,
      "audit_completeness_rate": 0.0
    }
  },
  "summary_reflection": {
    "trusted_false_memory_count": 5,
    "expected_action_delta": -0.06060606060606066,
    "metrics": {
      "action_brief_relevance_recall": 0.6666666666666666,
      "action_brief_pollution_rate": 0.6153846153846154,
      "scoped_memory_suppression": 0.25,
      "expired_memory_suppression": 0.0,
      "audit_completeness_rate": 0.0
    }
  },
  "unvalidated_memory": {
    "trusted_false_memory_count": 7,
    "expected_action_delta": 0.36363636363636365,
    "metrics": {
      "promoted_count": 18,
      "extraction_precision": 1.0,
      "extraction_recall": 1.0,
      "extraction_f1": 1.0,
      "action_brief_card_count": 14,
      "action_brief_relevance_recall": 1.0,
      "action_brief_pollution_rate": 0.5,
      "memory_harm_rate": 0.5,
      "scoped_memory_suppression": 1.0,
      "expired_memory_suppression": 1.0,
      "evidence_consolidation_count": 0,
      "max_evidence_support_count": 1,
      "audit_completeness_rate": 0.0
    }
  },
  "human_curated_runbook": {
    "trusted_false_memory_count": 0,
    "expected_action_delta": 1.0,
    "metrics": {
      "false_memory_resistance": 1.0,
      "action_brief_card_count": 6,
      "action_brief_relevance_recall": 1.0,
      "action_brief_pollution_rate": 0.0,
      "memory_harm_rate": 0.0,
      "audit_completeness_rate": 0.0
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
      "promoted_count": 11,
      "extraction_precision": 1.0,
      "extraction_recall": 1.0,
      "extraction_f1": 1.0,
      "contradiction_precision": 1.0,
      "contradiction_recall": 1.0,
      "action_brief_card_count": 6,
      "action_brief_relevance_recall": 1.0,
      "action_brief_pollution_rate": 0.0,
      "memory_harm_rate": 0.0,
      "scoped_memory_suppression": 1.0,
      "expired_memory_suppression": 1.0,
      "evidence_consolidation_count": 1,
      "max_evidence_support_count": 2,
      "audit_completeness_rate": 1.0,
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
        "expected_action_delta_delta": 1.0606060606060606,
        "workflow_success_delta": 1.0,
        "trusted_false_memory_reduction": 5,
        "action_brief_card_reduction": 7
      },
      "vanilla_vector_memory": {
        "false_memory_resistance_delta": 1.0,
        "expected_action_delta_delta": 0.5303030303030303,
        "workflow_success_delta": 1.0,
        "trusted_false_memory_reduction": 3,
        "action_brief_card_reduction": 4
      },
      "time_aware_vector_memory": {
        "false_memory_resistance_delta": 1.0,
        "expected_action_delta_delta": 0.5303030303030303,
        "workflow_success_delta": 1.0,
        "trusted_false_memory_reduction": 3,
        "action_brief_card_reduction": 4
      },
      "unvalidated_memory": {
        "false_memory_resistance_delta": 1.0,
        "expected_action_delta_delta": 0.6363636363636364,
        "workflow_success_delta": 1.0,
        "trusted_false_memory_reduction": 7,
        "action_brief_card_reduction": 8
      },
      "human_curated_runbook": {
        "false_memory_resistance_delta": 0.0,
        "expected_action_delta_delta": 0.0,
        "workflow_success_delta": 0.0,
        "trusted_false_memory_reduction": 0,
        "action_brief_card_reduction": 0
      }
    },
    "workflow_rows": {
      "no_memory": false,
      "full_context": false,
      "vanilla_vector_memory": false,
      "time_aware_vector_memory": false,
      "raw_trace_retrieval": false,
      "summary_reflection": false,
      "unvalidated_memory": false,
      "human_curated_runbook": true,
      "cem0_validation": true
    }
  }
}
```

The markdown report includes baseline rows, a CEM-0 row, CEM-0-vs-baseline deltas, extraction quality, contradiction detection, memory harm, a held-out workflow section, an audit coverage section, and action-brief utility columns for relevance recall, pollution rate, scoped-memory suppression, expired-memory suppression, evidence consolidation, max support, and audit completeness.

Run tests:

```powershell
python -m pytest
```
