from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from .synthetic_corruption import (
    MemoryRunResult,
    run_synthetic_corruption_eval,
    workflow_report_row_from_run,
)


class WorkflowGotchaAttempt(BaseModel):
    run_name: str
    success: bool
    failure_reasons: list[str]


class WorkflowGotchaDemoResult(BaseModel):
    attempts: list[WorkflowGotchaAttempt]


def run_workflow_gotcha_demo(root: str | Path) -> WorkflowGotchaDemoResult:
    synthetic = run_synthetic_corruption_eval(root)
    return WorkflowGotchaDemoResult(
        attempts=[
            _attempt_from_run(synthetic.no_memory),
            _attempt_from_run(synthetic.full_context),
            _attempt_from_run(synthetic.raw_trace_retrieval),
            _attempt_from_run(synthetic.summary_reflection),
            _attempt_from_run(synthetic.unvalidated_memory),
            _attempt_from_run(synthetic.cem0_validation),
        ]
    )


def _attempt_from_run(run: MemoryRunResult) -> WorkflowGotchaAttempt:
    row = workflow_report_row_from_run(run)
    return WorkflowGotchaAttempt(
        run_name=row.name,
        success=row.success,
        failure_reasons=row.failure_reasons,
    )
