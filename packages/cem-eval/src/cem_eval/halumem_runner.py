from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from cem_core import CEM, DeterministicExtractor, ExperienceAtom, MemoryExtractor, NaturalLanguageExtractor, TaskContext

from .answering import ANSWER_SYNTHESIS_PROMPT_VERSION, synthesize_answer
from .halumem_adapter import (
    HaluMemAnswerScore,
    HaluMemDataset,
    HaluMemExtractionScore,
    halumem_question_key,
    halumem_sessions_to_agent_traces,
    load_halumem_dataset,
    score_halumem_extraction,
    score_halumem_qa_answers,
)
from .official_evaluators import official_evaluator_scaffold
from .synthetic_corruption import SyntheticEvalResult, run_synthetic_corruption_eval


class HaluMemFacsimileResult(BaseModel):
    suite_name: str
    source_suite_name: str
    extraction_false_memory_resistance: float
    update_recall: float
    memory_qa_action_delta: float
    baseline_action_delta: float
    cem0_quarantined_count: int
    trusted_false_memory_count: int


class HaluMemCEM0EvalResult(BaseModel):
    suite_name: str
    source_path: str
    metric_scope: str = "local_proxy"
    official_evaluator_status: str = "not_wired"
    official_evaluator_name: str
    official_evaluator_source: str
    session_count: int
    proposed_count: int
    trusted_count: int
    quarantined_count: int
    proposed_score: HaluMemExtractionScore
    trusted_score: HaluMemExtractionScore
    qa_answer_count: int = 0
    qa_score: HaluMemAnswerScore
    answers_by_question: dict[str, str] = {}
    answer_synthesis_prompt_version: str = ANSWER_SYNTHESIS_PROMPT_VERSION
    decision_reason_codes: dict[str, list[str]]


def run_halumem_facsimile_eval(root: str | Path) -> HaluMemFacsimileResult:
    synthetic = run_synthetic_corruption_eval(root)
    return halumem_facsimile_from_synthetic(synthetic)


def halumem_facsimile_from_synthetic(synthetic: SyntheticEvalResult) -> HaluMemFacsimileResult:
    return HaluMemFacsimileResult(
        suite_name="halumem_local_facsimile",
        source_suite_name=synthetic.report.suite_name,
        extraction_false_memory_resistance=synthetic.cem0_validation.metrics.false_memory_resistance,
        update_recall=synthetic.cem0_validation.metrics.stale_memory_suppression,
        memory_qa_action_delta=synthetic.cem0_validation.expected_action_delta,
        baseline_action_delta=synthetic.unvalidated_memory.expected_action_delta,
        cem0_quarantined_count=synthetic.cem0_validation.quarantined_count,
        trusted_false_memory_count=synthetic.cem0_validation.trusted_false_memory_count,
    )


def run_halumem_cem0_eval(
    dataset_path: str | Path,
    root: str | Path,
    *,
    extractor: MemoryExtractor | None = None,
    fixture_mode: bool = False,
) -> HaluMemCEM0EvalResult:
    dataset = load_halumem_dataset(dataset_path)
    return run_halumem_cem0_eval_from_dataset(
        dataset,
        root,
        extractor=extractor,
        fixture_mode=fixture_mode,
    )


def run_halumem_cem0_eval_from_dataset(
    dataset: HaluMemDataset,
    root: str | Path,
    *,
    extractor: MemoryExtractor | None = None,
    fixture_mode: bool = False,
) -> HaluMemCEM0EvalResult:
    cem = CEM(root, extractor=extractor or _default_extractor(fixture_mode=fixture_mode))
    proposed_by_session: dict[str, list[str]] = {}
    decision_reason_codes: dict[str, list[str]] = {}

    for trace in halumem_sessions_to_agent_traces(dataset):
        cem.ingest_trace(trace)
        atoms = cem.propose_memories(trace.trace_id)
        proposed_by_session.setdefault(trace.session_id, []).extend(atom.content for atom in atoms)
        for atom in atoms:
            decision = cem.validate(atom.atom_id)
            decision_reason_codes[atom.content] = decision.reason_codes
            cem.promote(atom.atom_id)

    stored_atoms = cem.store.list_atoms()
    trusted_atoms = [
        atom
        for atom in stored_atoms
        if atom.promotion_status in {"candidate", "verified"}
    ]
    trusted_by_session = _contents_by_session(trusted_atoms)
    answers_by_question: dict[str, str] = {}
    for session in dataset.sessions:
        for question_index, question in enumerate(session.questions):
            brief = cem.retrieve_action_brief(
                TaskContext(
                    task_id=halumem_question_key(session.session_id, question_index),
                    session_id=session.session_id,
                    description=question.question,
                    domain_scope="halumem",
                    task_family="halumem-memory-session",
                ),
                max_cards=5,
            )
            answer = synthesize_answer(question.question, brief.recommended_next_actions)
            if answer is not None:
                answers_by_question[halumem_question_key(session.session_id, question_index)] = answer
    quarantined_count = len(
        [atom for atom in stored_atoms if atom.promotion_status == "quarantined"]
    )
    scaffold = official_evaluator_scaffold("halumem_cem0")
    return HaluMemCEM0EvalResult(
        suite_name="halumem_cem0",
        source_path=dataset.source_path,
        metric_scope="local_proxy",
        official_evaluator_status=scaffold.status,
        official_evaluator_name=scaffold.official_evaluator_name,
        official_evaluator_source=scaffold.official_evaluator_source,
        session_count=len(dataset.sessions),
        proposed_count=sum(len(contents) for contents in proposed_by_session.values()),
        trusted_count=len(trusted_atoms),
        quarantined_count=quarantined_count,
        proposed_score=score_halumem_extraction(dataset, proposed_by_session),
        trusted_score=score_halumem_extraction(dataset, trusted_by_session),
        qa_answer_count=len(answers_by_question),
        qa_score=score_halumem_qa_answers(dataset, answers_by_question),
        answers_by_question=answers_by_question,
        answer_synthesis_prompt_version=ANSWER_SYNTHESIS_PROMPT_VERSION,
        decision_reason_codes=decision_reason_codes,
    )


def _contents_by_session(atoms: list[ExperienceAtom]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for atom in atoms:
        grouped.setdefault(atom.source_session_id, []).append(atom.content)
    return grouped


def _default_extractor(*, fixture_mode: bool) -> MemoryExtractor:
    return DeterministicExtractor() if fixture_mode else NaturalLanguageExtractor()
