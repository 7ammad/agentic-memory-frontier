from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from cem_core import CEM, DeterministicExtractor, MemoryExtractor, NaturalLanguageExtractor, TaskContext

from .answering import ANSWER_SYNTHESIS_PROMPT_VERSION, synthesize_answer
from .memoryarena_adapter import (
    MemoryArenaDataset,
    MemoryArenaScore,
    load_memoryarena_dataset,
    memoryarena_prediction_key,
    memoryarena_tasks_to_agent_traces,
    score_memoryarena_predictions,
)
from .official_evaluators import official_evaluator_scaffold


class MemoryArenaCEM0EvalResult(BaseModel):
    suite_name: str
    source_path: str
    metric_scope: str = "local_proxy"
    official_evaluator_status: str = "not_wired"
    official_evaluator_name: str
    official_evaluator_source: str
    task_count: int
    proposed_count: int
    trusted_count: int
    quarantined_count: int
    action_brief_prediction_count: int
    score: MemoryArenaScore
    predictions_by_task: dict[str, list[str]]
    answer_synthesis_prompt_version: str = ANSWER_SYNTHESIS_PROMPT_VERSION
    decision_reason_codes: dict[str, list[str]]


def run_memoryarena_cem0_eval(
    dataset_path: str | Path,
    root: str | Path,
    *,
    domain: str | None = None,
    extractor: MemoryExtractor | None = None,
    fixture_mode: bool = False,
) -> MemoryArenaCEM0EvalResult:
    dataset = load_memoryarena_dataset(dataset_path, domain=domain)
    return run_memoryarena_cem0_eval_from_dataset(
        dataset,
        root,
        extractor=extractor,
        fixture_mode=fixture_mode,
    )


def run_memoryarena_cem0_eval_from_dataset(
    dataset: MemoryArenaDataset,
    root: str | Path,
    *,
    extractor: MemoryExtractor | None = None,
    fixture_mode: bool = False,
) -> MemoryArenaCEM0EvalResult:
    cem = CEM(root, extractor=extractor or _default_extractor(fixture_mode=fixture_mode))
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
        prediction_key = memoryarena_prediction_key(task)
        task_context = TaskContext(
            task_id=prediction_key,
            session_id=f"memoryarena-{task.domain}-{task.task_id}",
            description=" ".join([subtask.question for subtask in task.subtasks]),
            domain_scope="memoryarena",
            task_family=f"memoryarena-{task.domain}",
        )
        brief = cem.retrieve_action_brief(task_context, max_cards=max(1, len(task.subtasks)))
        predictions: list[str] = []
        for subtask in task.subtasks:
            answer = synthesize_answer(subtask.question, brief.recommended_next_actions)
            if answer is not None:
                predictions.append(answer)
        predictions_by_task[prediction_key] = predictions[: len(task.subtasks)]

    stored_atoms = cem.store.list_atoms()
    trusted_count = len(
        [atom for atom in stored_atoms if atom.promotion_status in {"candidate", "verified"}]
    )
    quarantined_count = len(
        [atom for atom in stored_atoms if atom.promotion_status == "quarantined"]
    )
    prediction_count = sum(len(predictions) for predictions in predictions_by_task.values())
    scaffold = official_evaluator_scaffold("memoryarena_cem0")
    return MemoryArenaCEM0EvalResult(
        suite_name="memoryarena_cem0",
        source_path=dataset.source_path,
        metric_scope="local_proxy",
        official_evaluator_status=scaffold.status,
        official_evaluator_name=scaffold.official_evaluator_name,
        official_evaluator_source=scaffold.official_evaluator_source,
        task_count=len(dataset.tasks),
        proposed_count=proposed_count,
        trusted_count=trusted_count,
        quarantined_count=quarantined_count,
        action_brief_prediction_count=prediction_count,
        score=score_memoryarena_predictions(dataset, predictions_by_task),
        predictions_by_task=predictions_by_task,
        answer_synthesis_prompt_version=ANSWER_SYNTHESIS_PROMPT_VERSION,
        decision_reason_codes=decision_reason_codes,
    )


def _default_extractor(*, fixture_mode: bool) -> MemoryExtractor:
    return DeterministicExtractor() if fixture_mode else NaturalLanguageExtractor()
