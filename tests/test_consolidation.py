"""Phase 2 grounded-consolidation behavior (design doc section 4.4).

Pipeline order under test: dedup -> near-duplicate merge -> source-span
preservation -> grounded abstraction -> temporal supersession -> contradiction
links. Each behavior is driven test-first; failure canaries prove the gate bites.
"""
from cem_core import AgentTrace, CEM, TaskContext, TraceTurn


def _skill_trace(content: str, *, session: str = "s1", index: int = 0) -> AgentTrace:
    return AgentTrace(
        session_id=session,
        agent_id="codex",
        turns=[TraceTurn(index=index, role="environment", content=f"SKILL: {content}")],
        final_outcome="success",
    )


def test_near_duplicate_atoms_merge_into_one_card(tmp_path):
    # Two skills phrase the same lesson with different surface wording in the
    # same scope. Exact-title matching would create two cards; near-duplicate
    # consolidation must collapse them into one card carrying both as evidence.
    cem = CEM(tmp_path)

    trace_one = _skill_trace("set assignment_group before assignee on the incident form")
    cem.ingest_trace(trace_one)
    first = cem.propose_memories(trace_one.trace_id)[0]
    cem.validate(first.atom_id)
    first_card = cem.promote(first.atom_id)

    trace_two = _skill_trace(
        "assignment_group must be set before assignee on incident forms", index=1
    )
    cem.ingest_trace(trace_two)
    second = cem.propose_memories(trace_two.trace_id)[0]
    cem.validate(second.atom_id)
    second_card = cem.promote(second.atom_id)

    assert first_card is not None
    assert second_card is not None
    assert second_card.card_id == first_card.card_id
    assert first.atom_id in second_card.evidence_atom_ids
    assert second.atom_id in second_card.evidence_atom_ids
    assert len(cem.store.list_cards()) == 1


def test_distinct_lessons_do_not_falsely_merge(tmp_path):
    # Failure canary for over-merge: two unrelated skills in the same default
    # scope must stay separate cards. If the near-duplicate threshold is too
    # loose this collapses to one card and the assertion bites.
    cem = CEM(tmp_path)

    trace_one = _skill_trace("set assignment_group before assignee")
    cem.ingest_trace(trace_one)
    first = cem.propose_memories(trace_one.trace_id)[0]
    cem.validate(first.atom_id)
    cem.promote(first.atom_id)

    trace_two = _skill_trace("run pytest before claiming kernel changes are done", index=1)
    cem.ingest_trace(trace_two)
    second = cem.propose_memories(trace_two.trace_id)[0]
    cem.validate(second.atom_id)
    cem.promote(second.atom_id)

    assert len(cem.store.list_cards()) == 2
