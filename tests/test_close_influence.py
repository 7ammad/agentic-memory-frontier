from cem_core import AgentTrace, CEM, TaskContext, TraceTurn


def _brief(cem):
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
    brief = cem.retrieve_action_brief(
        TaskContext(description="set assignment_group before assignee")
    )
    return brief, card


def test_close_influence_writes_observational_event(tmp_path):
    cem = CEM(tmp_path)
    brief, _ = _brief(cem)
    event = cem.close_influence(
        brief.brief_id,
        action_taken="set assignment_group",
        outcome="success",
        observed_post_brief_delta=0.2,
    )
    assert event.influence_id == brief.influence_id
    assert event.brief_id == brief.brief_id
    assert event.observed_post_brief_delta == 0.2
    assert event.counterfactual_method is not None  # documents it is observational
    stored = cem.store.list_action_influence_events(brief.influence_id)
    assert len(stored) == 1 and stored[0].outcome == "success"


def test_close_influence_never_verifies_a_card(tmp_path):
    # Failure canary: a post-brief outcome is observational, never causal — it
    # must not promote or set measured lift on any card.
    cem = CEM(tmp_path)
    brief, card = _brief(cem)
    cem.close_influence(
        brief.brief_id,
        action_taken="x",
        outcome="success",
        observed_post_brief_delta=0.9,
    )
    reloaded = cem.store.get_card(card.card_id)
    assert reloaded.promotion_status == "candidate"
    assert reloaded.measured_lift is None
