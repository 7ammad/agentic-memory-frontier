from datetime import timedelta

from cem_core import CEM, AgentTrace, TaskContext, TraceTurn
from cem_core.models import utc_now


def _seed_card_with_validity(cem: CEM):
    trace = AgentTrace(
        session_id="s1",
        agent_id="codex",
        turns=[
            TraceTurn(
                index=0,
                role="environment",
                content="SKILL: set assignment_group before assignee",
            )
        ],
        final_outcome="success",
    )
    cem.ingest_trace(trace)
    atom = cem.propose_memories(trace.trace_id)[0]
    cem.validate(atom.atom_id)
    card = cem.promote(atom.atom_id)
    # Force an offset-aware validity window so _card_in_scope performs a
    # datetime comparison against task.current_time.
    card.valid_from = utc_now() - timedelta(days=1)
    card.valid_until = utc_now() + timedelta(days=1)
    cem.store.save_card(card)
    return card


def test_retrieve_action_brief_tolerates_naive_current_time(tmp_path):
    # Regression: an MCP/CLI client may supply current_time as a timezone-less
    # ISO string, which Pydantic parses offset-naive. Cards carry offset-aware
    # validity bounds (from utc_now()), so the scope comparison used to raise
    # "can't compare offset-naive and offset-aware datetimes".
    cem = CEM(tmp_path)
    _seed_card_with_validity(cem)
    task = TaskContext.model_validate(
        {
            "description": "set assignment_group before assignee",
            "current_time": "2026-05-29T12:00:00",
        }
    )
    # Before the fix this raised TypeError on the offset-aware/naive comparison.
    brief = cem.retrieve_action_brief(task)
    assert brief.task_id == task.task_id
    assert task.current_time.tzinfo is not None  # normalized to offset-aware
