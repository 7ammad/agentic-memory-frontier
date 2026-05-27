from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from cem_core import CEM, MemoryExtractor, TaskContext

from .memoryarena_adapter import (
    MemoryArenaDataset,
    MemoryArenaScore,
    load_memoryarena_dataset,
    memoryarena_tasks_to_agent_traces,
    score_memoryarena_predictions,
)


class MemoryArenaCEM0EvalResult(BaseModel):
    suite_name: str
    source_path: str
    task_count: int
    proposed_count: int
    trusted_count: int
    quarantined_count: int
    action_brief_prediction_count: int
    score: MemoryArenaScore
    predictions_by_task: dict[str, list[str]]
    decision_reason_codes: dict[str, list[str]]


def run_memoryarena_cem0_eval(
    dataset_path: str | Path,
    root: str | Path,
    *,
    domain: str | None = None,
    extractor: MemoryExtractor | None = None,
) -> MemoryArenaCEM0EvalResult:
    dataset = load_memoryarena_dataset(dataset_path, domain=domain)
    return run_memoryarena_cem0_eval_from_dataset(dataset, root, extractor=extractor)


def run_memoryarena_cem0_eval_from_dataset(
    dataset: MemoryArenaDataset,
    root: str | Path,
    *,
    extractor: MemoryExtractor | None = None,
) -> MemoryArenaCEM0EvalResult:
    cem = CEM(root, extractor=extractor)
    proposed_count = 0
    decision_reason_codes: dict[str, list[str]] = {}

    for trace in memoryarena_tasks_to_agent_traces(dataset):
        cem.ingest_trace(trace)
        atoms = cem.propose_memories(trace.trace_id)
        proposed_count += len(atoms)
        for atom in atoms:
            decision = cem.validate(atom.atom_id)
            decision_reason_codes[atom.content] = decision.reason_codes
            cem.promote(atom.atom_id)

    predictions_by_task: dict[str, list[str]] = {}
    for task in dataset.tasks:
        task_context = TaskContext(
            task_id=task.task_id,
            session_id=f"memoryarena-{task.domain}-{task.task_id}",
            description=" ".join([subtask.question for subtask in task.subtasks]),
            domain_scope="memoryarena",
            task_family=f"memoryarena-{task.domain}",
        )
        brief = cem.retrieve_action_brief(task_context, max_cards=max(1, len(task.subtasks)))
        predictions_by_task[task.task_id] = brief.recommended_next_actions[: len(task.subtasks)]

    stored_atoms = cem.store.list_atoms()
    trusted_count = len(
        [atom for atom in stored_atoms if atom.promotion_status in {"candidate", "verified"}]
    )
    quarantined_count = len(
        [atom for atom in stored_atoms if atom.promotion_status == "quarantined"]
    )
    prediction_count = sum(len(predictions) for predictions in predictions_by_task.values())
    return MemoryArenaCEM0EvalResult(
        suite_name="memoryarena_cem0",
        source_path=dataset.source_path,
        task_count=len(dataset.tasks),
        proposed_count=proposed_count,
        trusted_count=trusted_count,
        quarantined_count=quarantined_count,
        action_brief_prediction_count=prediction_count,
        score=score_memoryarena_predictions(dataset, predictions_by_task),
        predictions_by_task=predictions_by_task,
        decision_reason_codes=decision_reason_codes,
    )
