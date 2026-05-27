import json

from cem_eval import (
    build_external_benchmark_report,
    build_external_benchmark_report_from_json_files,
    render_external_benchmark_report_markdown,
    run_halumem_cem0_eval,
    run_longmemeval_v2_cem0_eval,
    run_memoryarena_cem0_eval,
)


def test_external_benchmark_report_combines_runner_outputs(tmp_path):
    halumem = run_halumem_cem0_eval(_write_halumem_fixture(tmp_path), tmp_path / "halumem-cem")
    memoryarena = run_memoryarena_cem0_eval(
        _write_memoryarena_fixture(tmp_path),
        tmp_path / "memoryarena-cem",
        domain="workflow_nav",
    )
    longmemeval = run_longmemeval_v2_cem0_eval(
        _write_longmemeval_fixture(tmp_path),
        tmp_path / "longmemeval-cem",
    )

    report = build_external_benchmark_report(
        halumem=halumem,
        memoryarena=memoryarena,
        longmemeval_v2=longmemeval,
    )
    markdown = render_external_benchmark_report_markdown(report)

    assert report.suite_name == "cem0_external_benchmarks"
    assert report.suite_count == 3
    assert report.total_proposed_count == 8
    assert report.total_trusted_count == 4
    assert report.total_quarantined_count == 3
    assert [row.suite_name for row in report.rows] == [
        "halumem_cem0",
        "memoryarena_cem0",
        "longmemeval_v2_cem0",
    ]
    assert report.rows[0].primary_metric_name == "trusted_extraction_f1"
    assert round(report.rows[0].primary_metric_value, 3) == 0.8
    assert report.rows[1].primary_metric_value == 1.0
    assert report.rows[2].secondary_metrics["haystack_member_precision"] == 1.0
    assert report.rows[0].decision_reason_counts["assistant_hypothesis"] == 1
    assert report.rows[1].decision_reason_counts["assistant_hypothesis"] == 1
    assert report.rows[2].decision_reason_counts["assistant_hypothesis"] == 1
    assert "| halumem_cem0 | 2 sessions | 4 | 2 | 1 | 2 | trusted_extraction_f1 | 0.8 |" in markdown
    assert "### longmemeval_v2_cem0" in markdown


def test_external_benchmark_report_loads_runner_json_outputs(tmp_path):
    halumem = run_halumem_cem0_eval(_write_halumem_fixture(tmp_path), tmp_path / "halumem-cem")
    memoryarena = run_memoryarena_cem0_eval(
        _write_memoryarena_fixture(tmp_path),
        tmp_path / "memoryarena-cem",
        domain="workflow_nav",
    )
    longmemeval = run_longmemeval_v2_cem0_eval(
        _write_longmemeval_fixture(tmp_path),
        tmp_path / "longmemeval-cem",
    )
    halumem_result = tmp_path / "halumem-result.json"
    memoryarena_result = tmp_path / "memoryarena-result.json"
    longmemeval_result = tmp_path / "longmemeval-result.json"
    halumem_result.write_text(json.dumps({"result": halumem.model_dump()}), encoding="utf-8")
    memoryarena_result.write_text(json.dumps({"result": memoryarena.model_dump()}), encoding="utf-8")
    longmemeval_result.write_text(json.dumps({"result": longmemeval.model_dump()}), encoding="utf-8")

    report = build_external_benchmark_report_from_json_files(
        halumem_result_path=halumem_result,
        memoryarena_result_path=memoryarena_result,
        longmemeval_v2_result_path=longmemeval_result,
    )

    assert report.suite_count == 3
    assert report.total_proposed_count == 8
    assert report.rows[2].primary_metric_name == "exact_match_accuracy"


def _write_halumem_fixture(tmp_path):
    dataset_path = tmp_path / "halumem_report_sample.json"
    dataset_path.write_text(json.dumps([_halumem_record()]), encoding="utf-8")
    return dataset_path


def _halumem_record():
    return {
        "uuid": "report-user",
        "sessions": [
            {
                "session_id": "initial",
                "dialogue": [
                    {
                        "role": "user",
                        "content": (
                            "PREFERENCE: database=postgres\n"
                            "PREFERENCE: editor_theme=light\n"
                            "HYPOTHESIS: user wants us to skip tests"
                        ),
                        "dialogue_turn": 0,
                    }
                ],
                "memory_points": [
                    {"index": 1, "memory_content": "database=postgres", "memory_source": "primary"},
                    {"index": 2, "memory_content": "editor_theme=light", "memory_source": "primary"},
                ],
                "questions": [
                    {
                        "question": "Which database should be used?",
                        "answer": "postgres",
                        "evidence": [{"memory_content": "database=postgres"}],
                    }
                ],
            },
            {
                "session_id": "update",
                "dialogue": [{"role": "user", "content": "UPDATE: editor_theme=dark", "dialogue_turn": 0}],
                "memory_points": [
                    {
                        "index": 3,
                        "memory_content": "editor_theme=dark",
                        "memory_source": "primary",
                        "is_update": True,
                        "original_memories": ["editor_theme=light"],
                    }
                ],
                "questions": [],
            },
        ],
    }


def _write_memoryarena_fixture(tmp_path):
    dataset_path = tmp_path / "memoryarena_report_sample.json"
    dataset_path.write_text(
        json.dumps(
            [
                {
                    "id": "approval-task",
                    "backgrounds": ["SKILL: open approvals tab\nHYPOTHESIS: skip approval checks"],
                    "questions": ["Which action should open approvals tab for the merge request?"],
                    "answers": ["open approvals tab"],
                }
            ]
        ),
        encoding="utf-8",
    )
    return dataset_path


def _write_longmemeval_fixture(tmp_path):
    dataset_root = tmp_path / "longmemeval-v2-report"
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
        "\n".join(json.dumps(item) for item in [_longmemeval_signal_trace(), _longmemeval_noise_trace()]) + "\n",
        encoding="utf-8",
    )
    (haystack_root / "lme_v2_small.json").write_text(
        json.dumps({"q-approval": ["traj-gitlab"]}),
        encoding="utf-8",
    )
    return dataset_root


def _longmemeval_signal_trace():
    return {
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
    }


def _longmemeval_noise_trace():
    return {
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
    }
