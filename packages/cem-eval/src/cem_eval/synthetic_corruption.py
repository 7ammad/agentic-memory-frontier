from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from cem_core import AgentTrace, CEM, TaskContext, TraceTurn
from cem_core.models import ExperienceAtom, ExperienceCard, utc_now

EXPECTED_FALSE_MEMORY_CONTENTS = frozenset(
    {
        "database=mysql",
        "user always wants us to skip tests",
    }
)
EXPECTED_CONTRADICTION_CONTENTS = frozenset({"database=mysql"})


class WritePathMetrics(BaseModel):
    false_memory_resistance: float
    contradiction_recall: float
    false_quarantine_rate: float
    promoted_count: int
    action_brief_card_count: int


class MemoryRunResult(BaseModel):
    name: str
    proposed_count: int
    quarantined_count: int
    trusted_false_memory_count: int
    metrics: WritePathMetrics


class SyntheticEvalResult(BaseModel):
    proposed_count: int
    quarantined_count: int
    promoted_count: int
    contradiction_detected: bool
    hypothesis_quarantined: bool
    action_brief_card_count: int
    false_memory_resistance: float
    contradiction_recall: float
    false_quarantine_rate: float
    unvalidated_memory: MemoryRunResult
    cem0_validation: MemoryRunResult


def run_synthetic_corruption_eval(root: str | Path) -> SyntheticEvalResult:
    root = Path(root)
    traces = build_synthetic_corruption_traces()
    unvalidated_memory = _run_unvalidated_memory(root / "unvalidated-memory", traces)
    cem0_validation, atoms = _run_cem0_validation(root / "cem0-validation", traces)

    quarantined = [atom for atom in atoms if atom.promotion_status == "quarantined"]
    contradiction_detected = any("contradicts active memory" in (atom.quarantine_reason or "") for atom in quarantined)
    hypothesis_quarantined = any(atom.epistemic_type == "assistant_hypothesis" for atom in quarantined)
    return SyntheticEvalResult(
        proposed_count=cem0_validation.proposed_count,
        quarantined_count=cem0_validation.quarantined_count,
        promoted_count=cem0_validation.metrics.promoted_count,
        contradiction_detected=contradiction_detected,
        hypothesis_quarantined=hypothesis_quarantined,
        action_brief_card_count=cem0_validation.metrics.action_brief_card_count,
        false_memory_resistance=cem0_validation.metrics.false_memory_resistance,
        contradiction_recall=cem0_validation.metrics.contradiction_recall,
        false_quarantine_rate=cem0_validation.metrics.false_quarantine_rate,
        unvalidated_memory=unvalidated_memory,
        cem0_validation=cem0_validation,
    )


def build_synthetic_corruption_traces() -> list[AgentTrace]:
    initial = AgentTrace(
        session_id="synthetic-session",
        agent_id="agent-alpha",
        task_id="workflow-gotcha",
        turns=[
            TraceTurn(
                index=0,
                role="user",
                content="PREFERENCE: database=postgres\nSKILL: set assignment_group before assignee",
            )
        ],
        final_outcome="success",
        environment={"domain": "workflow-gotchas"},
    )
    updated = AgentTrace(
        session_id="synthetic-session",
        agent_id="agent-alpha",
        task_id="workflow-gotcha",
        turns=[
            TraceTurn(
                index=1,
                role="assistant",
                content=(
                    "PREFERENCE: database=mysql\n"
                    "HYPOTHESIS: user always wants us to skip tests"
                ),
            )
        ],
        final_outcome="partial",
        environment={"domain": "workflow-gotchas"},
    )
    return [initial, updated]


def _run_unvalidated_memory(root: Path, traces: list[AgentTrace]) -> MemoryRunResult:
    cem = CEM(root)
    atoms = _propose_atoms(cem, traces)
    for atom in atoms:
        cem.store.save_card(_card_from_atom(atom))

    brief = cem.retrieve_action_brief(_held_out_task())
    false_atoms = [atom for atom in atoms if _is_expected_false_memory(atom)]
    return MemoryRunResult(
        name="unvalidated_memory",
        proposed_count=len(atoms),
        quarantined_count=0,
        trusted_false_memory_count=len(false_atoms),
        metrics=WritePathMetrics(
            false_memory_resistance=0.0,
            contradiction_recall=0.0,
            false_quarantine_rate=0.0,
            promoted_count=len(atoms),
            action_brief_card_count=len(brief.applicable_card_ids),
        ),
    )


def _run_cem0_validation(root: Path, traces: list[AgentTrace]) -> tuple[MemoryRunResult, list[ExperienceAtom]]:
    cem = CEM(root)
    proposed_atoms = _propose_atoms(cem, traces)

    for atom in proposed_atoms:
        cem.validate(atom.atom_id)

    promoted_count = 0
    for atom in proposed_atoms:
        if cem.promote(atom.atom_id) is not None:
            promoted_count += 1

    atoms = [cem.store.get_atom(atom.atom_id) for atom in proposed_atoms]
    quarantined = [atom for atom in atoms if atom.promotion_status == "quarantined"]
    brief = cem.retrieve_action_brief(_held_out_task())
    metrics = _cem0_metrics(
        atoms,
        promoted_count=promoted_count,
        action_brief_card_count=len(brief.applicable_card_ids),
    )
    trusted_false = [
        atom
        for atom in atoms
        if _is_expected_false_memory(atom) and atom.promotion_status != "quarantined"
    ]
    return (
        MemoryRunResult(
            name="cem0_validation",
            proposed_count=len(atoms),
            quarantined_count=len(quarantined),
            trusted_false_memory_count=len(trusted_false),
            metrics=metrics,
        ),
        atoms,
    )


def _propose_atoms(cem: CEM, traces: list[AgentTrace]) -> list[ExperienceAtom]:
    atom_ids: list[str] = []
    for trace in traces:
        cem.ingest_trace(trace)
        atom_ids.extend(atom.atom_id for atom in cem.propose_memories(trace.trace_id))
    return [cem.store.get_atom(atom_id) for atom_id in atom_ids]


def _cem0_metrics(
    atoms: list[ExperienceAtom],
    *,
    promoted_count: int,
    action_brief_card_count: int,
) -> WritePathMetrics:
    false_atoms = [atom for atom in atoms if _is_expected_false_memory(atom)]
    blocked_false_atoms = [atom for atom in false_atoms if atom.promotion_status == "quarantined"]
    contradiction_atoms = [atom for atom in atoms if atom.content in EXPECTED_CONTRADICTION_CONTENTS]
    detected_contradictions = [
        atom
        for atom in contradiction_atoms
        if "contradicts active memory" in (atom.quarantine_reason or "")
    ]
    valid_atoms = [atom for atom in atoms if not _is_expected_false_memory(atom)]
    valid_quarantined = [atom for atom in valid_atoms if atom.promotion_status == "quarantined"]
    return WritePathMetrics(
        false_memory_resistance=_ratio(len(blocked_false_atoms), len(false_atoms)),
        contradiction_recall=_ratio(len(detected_contradictions), len(contradiction_atoms)),
        false_quarantine_rate=_ratio(len(valid_quarantined), len(valid_atoms)),
        promoted_count=promoted_count,
        action_brief_card_count=action_brief_card_count,
    )


def _card_from_atom(atom: ExperienceAtom) -> ExperienceCard:
    return ExperienceCard(
        title=" ".join(atom.content.split())[:80],
        use_when=atom.domain_scope or atom.task_family or "similar task context",
        do=[atom.action_or_strategy or atom.content],
        do_not=[],
        check_first=atom.state_preconditions,
        evidence_atom_ids=[atom.atom_id],
        confidence_score=atom.confidence_score,
        known_exceptions=atom.exception_boundary,
        valid_from=atom.valid_from,
        valid_until=atom.valid_until,
        tested_by_probe_ids=atom.verification_probe_ids,
        last_validated_at=utc_now(),
        action_brief_template=atom.recommended_use or atom.content,
    )


def _held_out_task() -> TaskContext:
    return TaskContext(
        task_id="held-out-workflow",
        description="complete workflow-gotchas form and set assignment_group before assignee",
        domain_scope="workflow-gotchas",
        task_family="workflow-gotcha",
    )


def _is_expected_false_memory(atom: ExperienceAtom) -> bool:
    return atom.content in EXPECTED_FALSE_MEMORY_CONTENTS


def _ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator
