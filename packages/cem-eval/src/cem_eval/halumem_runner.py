from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from cem_core import CEM, ExperienceAtom, MemoryExtractor

from .halumem_adapter import (
    HaluMemDataset,
    HaluMemExtractionScore,
    halumem_sessions_to_agent_traces,
    load_halumem_dataset,
    score_halumem_extraction,
)
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
    session_count: int
    proposed_count: int
    trusted_count: int
    quarantined_count: int
    proposed_score: HaluMemExtractionScore
    trusted_score: HaluMemExtractionScore
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
) -> HaluMemCEM0EvalResult:
    dataset = load_halumem_dataset(dataset_path)
    return run_halumem_cem0_eval_from_dataset(dataset, root, extractor=extractor)


def run_halumem_cem0_eval_from_dataset(
    dataset: HaluMemDataset,
    root: str | Path,
    *,
    extractor: MemoryExtractor | None = None,
) -> HaluMemCEM0EvalResult:
    cem = CEM(root, extractor=extractor)
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
    quarantined_count = len(
        [atom for atom in stored_atoms if atom.promotion_status == "quarantined"]
    )
    return HaluMemCEM0EvalResult(
        suite_name="halumem_cem0",
        source_path=dataset.source_path,
        session_count=len(dataset.sessions),
        proposed_count=sum(len(contents) for contents in proposed_by_session.values()),
        trusted_count=len(trusted_atoms),
        quarantined_count=quarantined_count,
        proposed_score=score_halumem_extraction(dataset, proposed_by_session),
        trusted_score=score_halumem_extraction(dataset, trusted_by_session),
        decision_reason_codes=decision_reason_codes,
    )


def _contents_by_session(atoms: list[ExperienceAtom]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for atom in atoms:
        grouped.setdefault(atom.source_session_id, []).append(atom.content)
    return grouped
