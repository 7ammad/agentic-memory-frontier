from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from .synthetic_corruption import SyntheticEvalResult, run_synthetic_corruption_eval


class HaluMemFacsimileResult(BaseModel):
    suite_name: str
    source_suite_name: str
    extraction_false_memory_resistance: float
    update_recall: float
    memory_qa_action_delta: float
    baseline_action_delta: float
    cem0_quarantined_count: int
    trusted_false_memory_count: int


def run_halumem_facsimile_eval(root: str | Path) -> HaluMemFacsimileResult:
    synthetic = run_synthetic_corruption_eval(root)
    return halumem_facsimile_from_synthetic(synthetic)


def halumem_facsimile_from_synthetic(synthetic: SyntheticEvalResult) -> HaluMemFacsimileResult:
    return HaluMemFacsimileResult(
        suite_name="halumem_local_facsimile",
        source_suite_name=synthetic.report.suite_name,
        extraction_false_memory_resistance=synthetic.cem0_validation.metrics.false_memory_resistance,
        update_recall=synthetic.cem0_validation.metrics.stale_memory_suppression,
        memory_qa_action_delta=synthetic.cem0_validation.expected_action_delta,
        baseline_action_delta=synthetic.unvalidated_memory.expected_action_delta,
        cem0_quarantined_count=synthetic.cem0_validation.quarantined_count,
        trusted_false_memory_count=synthetic.cem0_validation.trusted_false_memory_count,
    )
