import json

from cem_eval import (
    load_longmemeval_v2_dataset,
    longmemeval_v2_trajectories_to_agent_traces,
    score_longmemeval_v2_answers,
    score_longmemeval_v2_reference_upper_bound,
    score_longmemeval_v2_retrieval,
    summarize_longmemeval_v2_dataset,
)


def test_longmemeval_v2_adapter_loads_questions_trajectories_and_haystacks(tmp_path):
    dataset_root = _write_lme_fixture(tmp_path)

    dataset = load_longmemeval_v2_dataset(dataset_root)
    summary = summarize_longmemeval_v2_dataset(dataset_root)
    traces = longmemeval_v2_trajectories_to_agent_traces(dataset)

    assert summary.question_count == 2
    assert summary.trajectory_count == 2
    assert summary.state_count == 3
    assert summary.haystack_count == 2
    assert summary.screenshot_ref_count == 4
    assert summary.domain_counts == {"enterprise": 1, "web": 1}
    assert summary.question_type_counts == {
        "environment_gotchas": 1,
        "workflow_knowledge": 1,
    }
    assert dataset.haystacks["lme_v2_small"] == {
        "q-1": ["traj-gitlab", "traj-servicenow"],
        "q-2": ["traj-servicenow"],
    }
    assert len(traces) == 2
    assert traces[0].trace_id == "lme-v2-traj-gitlab"
    assert traces[0].agent_id == "longmemeval-v2-source"
    assert traces[0].environment["domain"] == "longmemeval-v2"
    assert traces[0].turns[0].role == "system"
    assert traces[0].turns[1].role == "environment"
    assert traces[0].turns[1].artifact_refs == ["screenshots/gitlab-0.png"]
    assert traces[0].turns[2].role == "assistant"


def test_longmemeval_v2_adapter_scores_answers_and_retrieval(tmp_path):
    dataset_root = _write_lme_fixture(tmp_path)
    dataset = load_longmemeval_v2_dataset(dataset_root)

    answer_score = score_longmemeval_v2_answers(
        dataset,
        {
            "q-1": "open the approvals tab",
            "q-2": "wrong answer",
        },
    )
    retrieval_score = score_longmemeval_v2_retrieval(
        dataset,
        {
            "q-1": ["traj-gitlab", "traj-unknown"],
            "q-2": ["traj-servicenow"],
        },
        haystack_name="lme_v2_small",
    )

    assert answer_score.question_count == 2
    assert answer_score.answered_count == 2
    assert answer_score.exact_match_count == 1
    assert answer_score.exact_match_accuracy == 0.5
    assert retrieval_score.question_count == 2
    assert retrieval_score.questions_with_haystack == 2
    assert retrieval_score.covered_question_count == 2
    assert retrieval_score.retrieved_trajectory_count == 3
    assert retrieval_score.in_haystack_retrieved_count == 2
    assert retrieval_score.out_of_haystack_retrieved_count == 1
    assert round(retrieval_score.haystack_member_precision, 3) == 0.667
    assert retrieval_score.question_coverage_rate == 1.0


def test_longmemeval_v2_reference_upper_bound_scores_clean(tmp_path):
    dataset_root = _write_lme_fixture(tmp_path)
    dataset = load_longmemeval_v2_dataset(dataset_root)

    score = score_longmemeval_v2_reference_upper_bound(dataset)

    assert score.question_count == 2
    assert score.answered_count == 2
    assert score.exact_match_count == 2
    assert score.exact_match_accuracy == 1.0


def _write_lme_fixture(tmp_path):
    dataset_root = tmp_path / "longmemeval-v2"
    dataset_root.mkdir()
    questions = [
        {
            "id": "q-1",
            "domain": "web",
            "environment": "gitlab",
            "question_type": "workflow_knowledge",
            "question": "Where should the reviewer approve the merge request?",
            "image": None,
            "answer": "Open the approvals tab",
            "eval_function": "exact_match",
        },
        {
            "id": "q-2",
            "domain": "enterprise",
            "environment": "servicenow",
            "question_type": "environment_gotchas",
            "question": "What field must be set first?",
            "image": "question_screenshots/q-2.png",
            "answer": "Set assignment group first",
            "eval_function": "exact_match",
        },
    ]
    trajectories = [
        {
            "id": "traj-gitlab",
            "domain": "web",
            "environment": "gitlab",
            "goal": "Review a merge request.",
            "outcome": "success",
            "start_url": "https://example.test/gitlab",
            "states": [
                {
                    "state_index": 0,
                    "step": 0,
                    "url": "https://example.test/gitlab/mr/1",
                    "action": "click approvals tab",
                    "thought": "approval settings are hidden under approvals",
                    "accessibility_tree": "button Approvals",
                    "screenshot": "screenshots/gitlab-0.png",
                },
                {
                    "state_index": 1,
                    "step": 1,
                    "url": "https://example.test/gitlab/mr/1/approvals",
                    "action": "approve",
                    "thought": "approval is now possible",
                    "accessibility_tree": "button Approve",
                    "screenshot": "screenshots/gitlab-1.png",
                },
            ],
        },
        {
            "id": "traj-servicenow",
            "domain": "enterprise",
            "environment": "servicenow",
            "goal": "Submit an incident.",
            "outcome": "failure",
            "start_url": "https://example.test/servicenow",
            "states": [
                {
                    "state_index": 0,
                    "step": 0,
                    "url": "https://example.test/servicenow/incident",
                    "action": "set assignee before assignment group",
                    "thought": "this order causes the assignee field to lock",
                    "accessibility_tree": "input assignment_group input assignee",
                    "screenshot": "screenshots/sn-0.png",
                }
            ],
        },
    ]
    haystack_root = dataset_root / "haystacks"
    haystack_root.mkdir()
    (dataset_root / "questions.jsonl").write_text(
        "\n".join(json.dumps(item) for item in questions) + "\n",
        encoding="utf-8",
    )
    (dataset_root / "trajectories.jsonl").write_text(
        "\n".join(json.dumps(item) for item in trajectories) + "\n",
        encoding="utf-8",
    )
    (haystack_root / "lme_v2_small.json").write_text(
        json.dumps({"q-1": ["traj-gitlab", "traj-servicenow"], "q-2": ["traj-servicenow"]}),
        encoding="utf-8",
    )
    return dataset_root
