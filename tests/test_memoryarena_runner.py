import json

from cem_eval import run_memoryarena_cem0_eval


def test_memoryarena_cem0_runner_scores_action_brief_predictions(tmp_path):
    dataset_path = tmp_path / "memoryarena_action.json"
    dataset_path.write_text(json.dumps([_memoryarena_action_task()]), encoding="utf-8")

    result = run_memoryarena_cem0_eval(
        dataset_path,
        tmp_path / "cem",
        domain="workflow_nav",
    )

    assert result.suite_name == "memoryarena_cem0"
    assert result.task_count == 1
    assert result.proposed_count == 2
    assert result.trusted_count == 1
    assert result.quarantined_count == 1
    assert result.action_brief_prediction_count == 1
    assert result.predictions_by_task == {"approval-task": ["open approvals tab"]}
    assert result.score.task_count == 1
    assert result.score.subtask_count == 1
    assert result.score.correct_subtask_count == 1
    assert result.score.fully_solved_task_count == 1
    assert result.score.progress_score == 1.0
    assert result.score.task_success_rate == 1.0
    assert "assistant_hypothesis" in result.decision_reason_codes["skip approval checks"]


def _memoryarena_action_task():
    return {
        "id": "approval-task",
        "backgrounds": [
            "SKILL: open approvals tab\nHYPOTHESIS: skip approval checks",
        ],
        "questions": [
            "Which action should open approvals tab for the merge request?",
        ],
        "answers": [
            "open approvals tab",
        ],
    }
