from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from cem_core import AgentTrace, CEM, TaskContext, TraceTurn


class SyntheticEvalResult(BaseModel):
    proposed_count: int
    quarantined_count: int
    promoted_count: int
    contradiction_detected: bool
    hypothesis_quarantined: bool
    action_brief_card_count: int


def run_synthetic_corruption_eval(root: str | Path) -> SyntheticEvalResult:
    cem = CEM(root)

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

    atom_ids: list[str] = []
    for trace in (initial, updated):
        cem.ingest_trace(trace)
        atom_ids.extend(atom.atom_id for atom in cem.propose_memories(trace.trace_id))

    for atom_id in atom_ids:
        cem.validate(atom_id)

    promoted_count = 0
    for atom_id in atom_ids:
        if cem.promote(atom_id) is not None:
            promoted_count += 1

    atoms = [cem.store.get_atom(atom_id) for atom_id in atom_ids]
    quarantined = [atom for atom in atoms if atom.promotion_status == "quarantined"]
    contradiction_detected = any("contradicts active memory" in (atom.quarantine_reason or "") for atom in quarantined)
    hypothesis_quarantined = any(atom.epistemic_type == "assistant_hypothesis" for atom in quarantined)
    brief = cem.retrieve_action_brief(
        TaskContext(
            task_id="held-out-workflow",
            description="complete workflow-gotchas form and set assignment_group before assignee",
            domain_scope="workflow-gotchas",
            task_family="workflow-gotcha",
        )
    )
    return SyntheticEvalResult(
        proposed_count=len(atom_ids),
        quarantined_count=len(quarantined),
        promoted_count=promoted_count,
        contradiction_detected=contradiction_detected,
        hypothesis_quarantined=hypothesis_quarantined,
        action_brief_card_count=len(brief.applicable_card_ids),
    )
