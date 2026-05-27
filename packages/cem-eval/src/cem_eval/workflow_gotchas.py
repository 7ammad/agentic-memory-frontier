from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from .synthetic_corruption import MemoryRunResult, run_synthetic_corruption_eval


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
            _attempt_from_run(synthetic.raw_trace_retrieval),
            _attempt_from_run(synthetic.summary_reflection),
            _attempt_from_run(synthetic.unvalidated_memory),
            _attempt_from_run(synthetic.cem0_validation),
        ]
    )


def _attempt_from_run(run: MemoryRunResult) -> WorkflowGotchaAttempt:
    actions = set(run.action_brief_recommended_actions)
    failure_reasons: list[str] = []
    if "set assignment_group before assignee" not in actions:
        failure_reasons.append("missing assignment_group-before-assignee precondition")
    if "avoid submitting workflow-gotchas form unless approval_code is present" not in actions:
        failure_reasons.append("missing approval_code failure lesson")
    if "run pytest before claiming kernel changes are done" not in actions:
        failure_reasons.append("missing test-before-claiming-done instruction")

    polluted_actions = [
        "user always wants us to skip tests",
        "production deploy already finished",
        "skip pytest before claiming kernel changes are done",
        "click refresh before submitting workflow-gotchas form",
        "database=mysql",
        "timezone=UTC",
        "editor_theme=light",
    ]
    for polluted_action in polluted_actions:
        if polluted_action in actions:
            failure_reasons.append(f"polluted action present: {polluted_action}")

    return WorkflowGotchaAttempt(
        run_name=run.name,
        success=not failure_reasons,
        failure_reasons=failure_reasons,
    )
