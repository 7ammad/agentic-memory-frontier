from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from cem_core import CEM, MemoryExtractor, TaskContext

from .longmemeval_v2_adapter import (
    LongMemEvalV2AnswerScore,
    LongMemEvalV2Dataset,
    LongMemEvalV2RetrievalScore,
    load_longmemeval_v2_dataset,
    longmemeval_v2_trajectories_to_agent_traces,
    score_longmemeval_v2_answers,
    score_longmemeval_v2_retrieval,
)


class LongMemEvalV2CEM0EvalResult(BaseModel):
    suite_name: str
    source_path: str
    question_count: int
    trajectory_count: int
    proposed_count: int
    trusted_count: int
    quarantined_count: int
    action_brief_answer_count: int
    answer_score: LongMemEvalV2AnswerScore
    retrieval_score: LongMemEvalV2RetrievalScore
    answers_by_question: dict[str, str]
    retrieved_trajectory_ids_by_question: dict[str, list[str]]
    decision_reason_codes: dict[str, list[str]]


def run_longmemeval_v2_cem0_eval(
    dataset_path: str | Path,
    root: str | Path,
    *,
    haystack_name: str = "lme_v2_small",
    extractor: MemoryExtractor | None = None,
) -> LongMemEvalV2CEM0EvalResult:
    dataset = load_longmemeval_v2_dataset(dataset_path)
    return run_longmemeval_v2_cem0_eval_from_dataset(
        dataset,
        root,
        haystack_name=haystack_name,
        extractor=extractor,
    )


def run_longmemeval_v2_cem0_eval_from_dataset(
    dataset: LongMemEvalV2Dataset,
    root: str | Path,
    *,
    haystack_name: str = "lme_v2_small",
    extractor: MemoryExtractor | None = None,
) -> LongMemEvalV2CEM0EvalResult:
    cem = CEM(root, extractor=extractor)
    proposed_count = 0
    decision_reason_codes: dict[str, list[str]] = {}

    for trace in longmemeval_v2_trajectories_to_agent_traces(dataset):
        cem.ingest_trace(trace)
        atoms = cem.propose_memories(trace.trace_id)
        proposed_count += len(atoms)
        for atom in atoms:
            decision = cem.validate(atom.atom_id)
            decision_reason_codes[atom.content] = decision.reason_codes
            cem.promote(atom.atom_id)

    answers_by_question: dict[str, str] = {}
    retrieved_by_question: dict[str, list[str]] = {}
    for question in dataset.questions:
        brief = cem.retrieve_action_brief(
            TaskContext(
                task_id=question.question_id,
                description=question.question,
                domain_scope="longmemeval-v2",
                task_family=f"longmemeval-v2-{question.domain}",
            ),
            max_cards=5,
        )
        if brief.recommended_next_actions:
            answers_by_question[question.question_id] = brief.recommended_next_actions[0]
        retrieved_by_question[question.question_id] = _trajectory_ids_from_evidence(cem, brief.evidence_links)

    stored_atoms = cem.store.list_atoms()
    trusted_count = len(
        [atom for atom in stored_atoms if atom.promotion_status in {"candidate", "verified"}]
    )
    quarantined_count = len(
        [atom for atom in stored_atoms if atom.promotion_status == "quarantined"]
    )
    return LongMemEvalV2CEM0EvalResult(
        suite_name="longmemeval_v2_cem0",
        source_path=dataset.source_path,
        question_count=len(dataset.questions),
        trajectory_count=len(dataset.trajectories),
        proposed_count=proposed_count,
        trusted_count=trusted_count,
        quarantined_count=quarantined_count,
        action_brief_answer_count=len(answers_by_question),
        answer_score=score_longmemeval_v2_answers(dataset, answers_by_question),
        retrieval_score=score_longmemeval_v2_retrieval(
            dataset,
            retrieved_by_question,
            haystack_name=haystack_name,
        ),
        answers_by_question=answers_by_question,
        retrieved_trajectory_ids_by_question=retrieved_by_question,
        decision_reason_codes=decision_reason_codes,
    )


def _trajectory_ids_from_evidence(cem: CEM, evidence_links: list[str]) -> list[str]:
    trajectory_ids: list[str] = []
    for atom_id in evidence_links:
        atom = cem.store.get_atom(atom_id)
        for trace_id in atom.source_trace_ids:
            if trace_id.startswith("lme-v2-"):
                trajectory_ids.append(trace_id.removeprefix("lme-v2-"))
    return sorted(set(trajectory_ids))
