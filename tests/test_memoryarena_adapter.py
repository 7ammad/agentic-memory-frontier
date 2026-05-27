import json

from cem_eval import (
    load_memoryarena_dataset,
    memoryarena_tasks_to_agent_traces,
    score_memoryarena_predictions,
    score_memoryarena_reference_upper_bound,
    summarize_memoryarena_dataset,
)


def test_memoryarena_adapter_loads_structured_task_rows(tmp_path):
    dataset_path = tmp_path / "bundled_shopping.json"
    dataset_path.write_text(json.dumps([_bundled_shopping_task()]), encoding="utf-8")

    dataset = load_memoryarena_dataset(dataset_path, domain="bundled_shopping")
    summary = summarize_memoryarena_dataset(dataset_path, domain="bundled_shopping")
    traces = memoryarena_tasks_to_agent_traces(dataset)

    assert summary.task_count == 1
    assert summary.subtask_count == 2
    assert summary.background_count == 0
    assert summary.domain_counts == {"bundled_shopping": 1}
    assert dataset.tasks[0].task_id == "42"
    assert dataset.tasks[0].subtasks[0].question == "Find almond flour."
    assert dataset.tasks[0].subtasks[0].answer == {
        "target_asin": "B00TUDFEW2",
        "attributes": ["Almond Flour", "Gluten Free"],
    }
    assert len(traces) == 1
    assert traces[0].trace_id == "memoryarena-bundled_shopping-42"
    assert traces[0].agent_id == "memoryarena-source"
    assert traces[0].environment["domain"] == "memoryarena"
    assert traces[0].environment["memoryarena_domain"] == "bundled_shopping"
    assert traces[0].turns[0].role == "user"
    assert traces[0].turns[1].role == "environment"
    assert "ANSWER:" in traces[0].turns[1].content


def test_memoryarena_adapter_handles_backgrounds_and_scores_predictions(tmp_path):
    dataset_path = tmp_path / "formal_reasoning_math.jsonl"
    dataset_path.write_text(json.dumps(_formal_reasoning_task()) + "\n", encoding="utf-8")
    dataset = load_memoryarena_dataset(dataset_path, domain="formal_reasoning_math")

    summary = summarize_memoryarena_dataset(dataset_path, domain="formal_reasoning_math")
    score = score_memoryarena_predictions(
        dataset,
        {
            "paper-7": [
                "x = 2",
                "wrong answer",
            ]
        },
    )
    traces = memoryarena_tasks_to_agent_traces(dataset)

    assert summary.task_count == 1
    assert summary.subtask_count == 2
    assert summary.background_count == 2
    assert score.task_count == 1
    assert score.subtask_count == 2
    assert score.correct_subtask_count == 1
    assert score.fully_solved_task_count == 0
    assert score.progress_score == 0.5
    assert score.task_success_rate == 0.0
    assert traces[0].turns[0].role == "system"
    assert "Definition A" in traces[0].turns[0].content
    assert "Definition B" in traces[0].turns[0].content


def test_memoryarena_reference_upper_bound_scores_clean(tmp_path):
    dataset_dir = tmp_path / "memoryarena"
    dataset_dir.mkdir()
    (dataset_dir / "bundled_shopping.json").write_text(
        json.dumps([_bundled_shopping_task()]),
        encoding="utf-8",
    )
    (dataset_dir / "formal_reasoning_math.jsonl").write_text(
        json.dumps(_formal_reasoning_task()) + "\n",
        encoding="utf-8",
    )
    dataset = load_memoryarena_dataset(dataset_dir)

    score = score_memoryarena_reference_upper_bound(dataset)

    assert score.task_count == 2
    assert score.subtask_count == 4
    assert score.correct_subtask_count == 4
    assert score.fully_solved_task_count == 2
    assert score.progress_score == 1.0
    assert score.task_success_rate == 1.0


def _bundled_shopping_task():
    return {
        "id": 42,
        "questions": [
            "Find almond flour.",
            "Find vanilla extract.",
        ],
        "answers": [
            {
                "target_asin": "B00TUDFEW2",
                "attributes": ["Almond Flour", "Gluten Free"],
            },
            {
                "target_asin": "B08957C9ZH",
                "attributes": ["Vanilla", "Extract"],
            },
        ],
    }


def _formal_reasoning_task():
    return {
        "id": "paper-7",
        "paper_name": "memory-paper",
        "backgrounds": [
            "Definition A: x is the smallest valid value.",
            "Definition B: y must be greater than x.",
        ],
        "questions": [
            "What is x?",
            "What is y?",
        ],
        "answers": [
            "x = 2",
            "y = 3",
        ],
    }
