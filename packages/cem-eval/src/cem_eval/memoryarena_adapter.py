from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from cem_core import AgentTrace, TraceTurn


class MemoryArenaSubtask(BaseModel):
    task_id: str
    domain: str
    subtask_index: int
    question: str
    answer: Any = None
    background: str | None = None


class MemoryArenaTask(BaseModel):
    task_id: str
    domain: str
    subtasks: list[MemoryArenaSubtask]
    raw: dict[str, Any] = Field(default_factory=dict)


class MemoryArenaDataset(BaseModel):
    source_path: str
    tasks: list[MemoryArenaTask]

    @property
    def subtasks(self) -> list[MemoryArenaSubtask]:
        return [subtask for task in self.tasks for subtask in task.subtasks]


class MemoryArenaDatasetSummary(BaseModel):
    source_path: str
    task_count: int
    subtask_count: int
    background_count: int
    domain_counts: dict[str, int]


class MemoryArenaScore(BaseModel):
    task_count: int
    subtask_count: int
    correct_subtask_count: int
    fully_solved_task_count: int
    progress_score: float
    task_success_rate: float


def load_memoryarena_dataset(path: str | Path, *, domain: str | None = None) -> MemoryArenaDataset:
    source = Path(path)
    tasks: list[MemoryArenaTask] = []
    for record_domain, raw_record in _load_raw_records(source, domain=domain):
        tasks.append(_task_from_raw(raw_record, domain=record_domain))
    return MemoryArenaDataset(source_path=str(source), tasks=tasks)


def summarize_memoryarena_dataset(path: str | Path, *, domain: str | None = None) -> MemoryArenaDatasetSummary:
    dataset = load_memoryarena_dataset(path, domain=domain)
    domain_counts: dict[str, int] = {}
    for task in dataset.tasks:
        domain_counts[task.domain] = domain_counts.get(task.domain, 0) + 1
    return MemoryArenaDatasetSummary(
        source_path=dataset.source_path,
        task_count=len(dataset.tasks),
        subtask_count=len(dataset.subtasks),
        background_count=len([subtask for subtask in dataset.subtasks if subtask.background]),
        domain_counts=dict(sorted(domain_counts.items())),
    )


def memoryarena_tasks_to_agent_traces(dataset: MemoryArenaDataset) -> list[AgentTrace]:
    traces: list[AgentTrace] = []
    for task in dataset.tasks:
        turns: list[TraceTurn] = []
        background = _task_background(task)
        if background:
            turns.append(
                TraceTurn(
                    index=len(turns),
                    role="system",
                    content=f"BACKGROUND: {background}",
                )
            )
        for subtask in task.subtasks:
            turns.append(
                TraceTurn(
                    index=len(turns),
                    role="user",
                    content=subtask.question,
                )
            )
            turns.append(
                TraceTurn(
                    index=len(turns),
                    role="environment",
                    content=f"ANSWER: {_canonical_answer(subtask.answer)}",
                )
            )
        traces.append(
            AgentTrace(
                trace_id=f"memoryarena-{_safe_id(task.domain)}-{_safe_id(task.task_id)}",
                session_id=f"memoryarena-{task.domain}-{task.task_id}",
                agent_id="memoryarena-source",
                task_id=f"memoryarena-{task.domain}",
                turns=turns,
                final_outcome="unknown",
                environment={
                    "domain": "memoryarena",
                    "memoryarena_domain": task.domain,
                    "source_path": dataset.source_path,
                },
            )
        )
    return traces


def score_memoryarena_predictions(
    dataset: MemoryArenaDataset,
    predictions_by_task: Mapping[str, Sequence[Any]],
) -> MemoryArenaScore:
    correct_subtasks = 0
    fully_solved_tasks = 0
    subtask_count = 0

    for task in dataset.tasks:
        predictions = list(predictions_by_task.get(task.task_id, []))
        task_correct = 0
        for subtask in task.subtasks:
            subtask_count += 1
            predicted = predictions[subtask.subtask_index] if subtask.subtask_index < len(predictions) else None
            if _answers_match(predicted, subtask.answer):
                correct_subtasks += 1
                task_correct += 1
        if task.subtasks and task_correct == len(task.subtasks):
            fully_solved_tasks += 1

    return MemoryArenaScore(
        task_count=len(dataset.tasks),
        subtask_count=subtask_count,
        correct_subtask_count=correct_subtasks,
        fully_solved_task_count=fully_solved_tasks,
        progress_score=_ratio(correct_subtasks, subtask_count),
        task_success_rate=_ratio(fully_solved_tasks, len(dataset.tasks)),
    )


def score_memoryarena_reference_upper_bound(dataset: MemoryArenaDataset) -> MemoryArenaScore:
    return score_memoryarena_predictions(
        dataset,
        {task.task_id: [subtask.answer for subtask in task.subtasks] for task in dataset.tasks},
    )


def _load_raw_records(source: Path, *, domain: str | None) -> list[tuple[str, dict[str, Any]]]:
    if source.is_dir():
        records: list[tuple[str, dict[str, Any]]] = []
        for child in sorted(source.iterdir()):
            if child.suffix.lower() in {".json", ".jsonl"}:
                records.extend(_load_raw_records(child, domain=domain or child.stem))
        return records

    inferred_domain = domain or source.stem
    if source.suffix.lower() == ".jsonl":
        with source.open("r", encoding="utf-8") as handle:
            return [
                (inferred_domain, json.loads(line))
                for line in handle
                if line.strip()
            ]

    if source.suffix.lower() == ".json":
        with source.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return [(inferred_domain, record) for record in _records_from_payload(payload)]

    raise ValueError(f"Unsupported MemoryArena dataset file type: {source}")


def _records_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("data", "records", "tasks", "test"):
            nested = payload.get(key)
            if isinstance(nested, list):
                return [item for item in nested if isinstance(item, dict)]
        return [payload]
    raise ValueError("MemoryArena payload must be a JSON object, list, or JSONL records.")


def _task_from_raw(raw_task: dict[str, Any], *, domain: str) -> MemoryArenaTask:
    task_id = _text_value(raw_task, "id", "task_id") or "task-0"
    questions = _list_value(raw_task.get("questions"))
    answers = _list_value(raw_task.get("answers"))
    backgrounds = _backgrounds(raw_task.get("backgrounds") or raw_task.get("background"))
    subtask_count = max(len(questions), len(answers), len(backgrounds), 1)

    subtasks: list[MemoryArenaSubtask] = []
    for index in range(subtask_count):
        subtasks.append(
            MemoryArenaSubtask(
                task_id=task_id,
                domain=domain,
                subtask_index=index,
                question=_stringify(questions[index]) if index < len(questions) else "",
                answer=answers[index] if index < len(answers) else None,
                background=_background_for_index(backgrounds, index),
            )
        )
    return MemoryArenaTask(
        task_id=task_id,
        domain=domain,
        subtasks=subtasks,
        raw=raw_task,
    )


def _backgrounds(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [_stringify(item) for item in value]
    return [_stringify(value)]


def _background_for_index(backgrounds: list[str], index: int) -> str | None:
    if not backgrounds:
        return None
    if len(backgrounds) == 1:
        return backgrounds[0]
    if index < len(backgrounds):
        return backgrounds[index]
    return None


def _task_background(task: MemoryArenaTask) -> str | None:
    backgrounds = [subtask.background for subtask in task.subtasks if subtask.background]
    if not backgrounds:
        return None
    return "\n\n".join(dict.fromkeys(backgrounds))


def _answers_match(predicted: Any, expected: Any) -> bool:
    return _canonical_answer(predicted) == _canonical_answer(expected)


def _canonical_answer(value: Any) -> str:
    if isinstance(value, str):
        return " ".join(value.lower().split())
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _list_value(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _text_value(raw: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = raw.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            return value
        return str(value)
    return None


def _stringify(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def _safe_id(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in value)


def _ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator
