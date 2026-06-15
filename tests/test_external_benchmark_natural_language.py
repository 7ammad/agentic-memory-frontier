import json

import pytest

from cem_eval import (
    BenchmarkZeroOutputError,
    build_external_benchmark_report_from_json_files,
    run_halumem_cem0_eval,
    run_longmemeval_v2_cem0_eval,
    run_memoryarena_cem0_eval,
)


def test_halumem_runner_defaults_to_natural_language_extraction(tmp_path):
    dataset_path = tmp_path / "halumem_natural.json"
    dataset_path.write_text(
        json.dumps(
            [
                {
                    "uuid": "natural-user",
                    "sessions": [
                        {
                            "session_id": "natural-session",
                            "dialogue": [
                                {
                                    "role": "user",
                                    "content": "Please remember database=postgres for this project.",
                                }
                            ],
                            "memory_points": [
                                {
                                    "index": "1",
                                    "memory_content": "database=postgres",
                                    "memory_source": "primary",
                                }
                            ],
                            "questions": [
                                {
                                    "question": "Which database should be used?",
                                    "answer": "postgres",
                                    "evidence": [{"memory_content": "database=postgres"}],
                                }
                            ],
                        }
                    ],
                }
            ]
        ),
        encoding="utf-8",
    )

    result = run_halumem_cem0_eval(dataset_path, tmp_path / "cem")

    assert result.proposed_count == 1
    assert result.trusted_count == 1
    assert result.trusted_score.extraction_f1 == 1.0
    assert result.qa_answer_count == 1
    assert result.qa_score.exact_match_accuracy == 1.0
    assert result.metric_scope == "local_proxy"
    assert result.official_evaluator_status == "not_wired"


def test_memoryarena_runner_synthesizes_answers_from_retrieved_memory(tmp_path):
    dataset_path = tmp_path / "memoryarena_natural.json"
    dataset_path.write_text(
        json.dumps(
            [
                {
                    "id": "approval-task",
                    "questions": ["Which action should open approvals tab for the merge request?"],
                    "answers": ["open approvals tab"],
                }
            ]
        ),
        encoding="utf-8",
    )

    result = run_memoryarena_cem0_eval(
        dataset_path,
        tmp_path / "cem",
        domain="workflow_nav",
    )

    assert result.proposed_count == 1
    assert result.action_brief_prediction_count == 1
    assert result.predictions_by_task == {"workflow_nav:approval-task": ["open approvals tab"]}
    assert result.score.progress_score == 1.0
    assert result.answer_synthesis_prompt_version == "cem-answer-synthesis-v1"
    assert result.metric_scope == "local_proxy"


def test_longmemeval_v2_runner_synthesizes_answers_from_retrieved_memory(tmp_path):
    dataset_root = tmp_path / "longmemeval-v2-natural"
    dataset_root.mkdir()
    haystack_root = dataset_root / "haystacks"
    haystack_root.mkdir()
    (dataset_root / "questions.jsonl").write_text(
        json.dumps(
            {
                "id": "q-approval",
                "domain": "web",
                "environment": "gitlab",
                "question_type": "workflow_knowledge",
                "question": "Which action should open approvals tab for the merge request?",
                "answer": "open approvals tab",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (dataset_root / "trajectories.jsonl").write_text(
        json.dumps(
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
                        "action": "open approvals tab",
                        "accessibility_tree": "button Approvals",
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (haystack_root / "lme_v2_small.json").write_text(
        json.dumps({"q-approval": ["traj-gitlab"]}),
        encoding="utf-8",
    )

    result = run_longmemeval_v2_cem0_eval(
        dataset_root,
        tmp_path / "cem",
        haystack_name="lme_v2_small",
    )

    assert result.proposed_count >= 1
    assert result.action_brief_answer_count == 1
    assert result.answers_by_question == {"q-approval": "open approvals tab"}
    assert result.answer_score.exact_match_accuracy == 1.0
    assert result.retrieval_score.question_coverage_rate == 1.0
    assert result.answer_synthesis_prompt_version == "cem-answer-synthesis-v1"
    assert result.metric_scope == "local_proxy"


def test_external_benchmark_report_fails_zero_outputs_by_default(tmp_path):
    halumem_result = tmp_path / "halumem-zero.json"
    halumem_result.write_text(
        json.dumps(
            {
                "result": {
                    "suite_name": "halumem_cem0",
                    "source_path": "real/halumem.jsonl",
                    "session_count": 1,
                    "proposed_count": 0,
                    "trusted_count": 0,
                    "quarantined_count": 0,
                    "proposed_score": _empty_halumem_score(reference_count=1),
                    "trusted_score": _empty_halumem_score(reference_count=1),
                    "decision_reason_codes": {},
                    "qa_answer_count": 0,
                    "qa_score": {
                        "question_count": 1,
                        "answered_count": 0,
                        "exact_match_count": 0,
                        "exact_match_accuracy": 0.0,
                    },
                    "answers_by_question": {},
                    "metric_scope": "local_proxy",
                    "official_evaluator_status": "not_wired",
                    "official_evaluator_name": "HaluMem eval toolkit",
                    "official_evaluator_source": "https://github.com/MemTensor/HaluMem/tree/main/eval",
                }
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(BenchmarkZeroOutputError, match="halumem_cem0"):
        build_external_benchmark_report_from_json_files(halumem_result_path=halumem_result)


def _empty_halumem_score(*, reference_count):
    return {
        "reference_memory_count": reference_count,
        "candidate_memory_count": 0,
        "matched_memory_count": 0,
        "hallucinated_memory_count": 0,
        "omitted_memory_count": reference_count,
        "extraction_precision": 0.0,
        "extraction_recall": 0.0,
        "extraction_f1": 0.0,
        "update_recall": 0.0,
        "qa_evidence_recall": 0.0,
    }
