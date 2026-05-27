import json

from cem_eval import run_longmemeval_v2_cem0_eval


def test_longmemeval_v2_cem0_runner_scores_answers_and_retrieval(tmp_path):
    dataset_root = _write_lme_runner_fixture(tmp_path)

    result = run_longmemeval_v2_cem0_eval(
        dataset_root,
        tmp_path / "cem",
        haystack_name="lme_v2_small",
    )

    assert result.suite_name == "longmemeval_v2_cem0"
    assert result.question_count == 1
    assert result.trajectory_count == 2
    assert result.proposed_count == 2
    assert result.trusted_count == 1
    assert result.quarantined_count == 1
    assert result.action_brief_answer_count == 1
    assert result.answers_by_question == {"q-approval": "open approvals tab"}
    assert result.answer_score.question_count == 1
    assert result.answer_score.answered_count == 1
    assert result.answer_score.exact_match_count == 1
    assert result.answer_score.exact_match_accuracy == 1.0
    assert result.retrieved_trajectory_ids_by_question == {"q-approval": ["traj-gitlab"]}
    assert result.retrieval_score.questions_with_haystack == 1
    assert result.retrieval_score.covered_question_count == 1
    assert result.retrieval_score.in_haystack_retrieved_count == 1
    assert result.retrieval_score.out_of_haystack_retrieved_count == 0
    assert result.retrieval_score.haystack_member_precision == 1.0
    assert result.retrieval_score.question_coverage_rate == 1.0
    assert "assistant_hypothesis" in result.decision_reason_codes["skip approval checks"]


def _write_lme_runner_fixture(tmp_path):
    dataset_root = tmp_path / "longmemeval-v2"
    dataset_root.mkdir()
    haystack_root = dataset_root / "haystacks"
    haystack_root.mkdir()
    questions = [
        {
            "id": "q-approval",
            "domain": "web",
            "environment": "gitlab",
            "question_type": "workflow_knowledge",
            "question": "Which action should open approvals tab for the merge request?",
            "answer": "open approvals tab",
            "eval_function": "exact_match",
        }
    ]
    trajectories = [
        {
            "id": "traj-gitlab",
            "domain": "web",
            "environment": "gitlab",
            "goal": "Review a merge request.",
            "outcome": "success",
            "states": [
                {
                    "state_index": 0,
                    "step": 0,
                    "url": "https://example.test/gitlab/mr/1",
                    "action": "SKILL: open approvals tab",
                    "accessibility_tree": "button Approvals",
                }
            ],
        },
        {
            "id": "traj-noise",
            "domain": "web",
            "environment": "gitlab",
            "goal": "Guess the approval flow.",
            "outcome": "partial",
            "states": [
                {
                    "state_index": 0,
                    "step": 0,
                    "url": "https://example.test/gitlab/mr/2",
                    "thought": "HYPOTHESIS: skip approval checks",
                    "accessibility_tree": "button Merge",
                }
            ],
        },
    ]
    (dataset_root / "questions.jsonl").write_text(
        "\n".join(json.dumps(item) for item in questions) + "\n",
        encoding="utf-8",
    )
    (dataset_root / "trajectories.jsonl").write_text(
        "\n".join(json.dumps(item) for item in trajectories) + "\n",
        encoding="utf-8",
    )
    (haystack_root / "lme_v2_small.json").write_text(
        json.dumps({"q-approval": ["traj-gitlab"]}),
        encoding="utf-8",
    )
    return dataset_root
