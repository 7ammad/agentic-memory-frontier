from cem_core import AgentTrace, CEM, TaskContext, TraceTurn
from cem_core.storage import SQLiteStore


def _seed_card(cem):
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
    return cem.promote(atom.atom_id)


def test_brief_is_enriched_and_delta_is_sourced(tmp_path):
    cem = CEM(tmp_path)
    _seed_card(cem)
    brief = cem.retrieve_action_brief(
        TaskContext(description="set assignment_group before assignee")
    )
    assert brief.applicable_card_ids, "expected the seeded card to be selected"
    assert brief.influence_id is not None
    assert brief.scorer_version == "lexical_overlap_v0"
    assert brief.expected_action_delta_source == "observational_unverified"
    assert brief.expected_action_delta is not None
    assert set(brief.score_breakdown_by_card) == set(brief.applicable_card_ids)
    for feats in brief.score_breakdown_by_card.values():
        assert "lexical_overlap" in feats


def test_brief_with_no_cards_has_none_delta_and_none_source(tmp_path):
    cem = CEM(tmp_path)  # empty store, nothing selected
    brief = cem.retrieve_action_brief(
        TaskContext(description="totally unrelated topic xyzzy")
    )
    assert brief.applicable_card_ids == []
    assert brief.expected_action_delta is None
    assert brief.expected_action_delta_source == "none"


def test_brief_never_presents_untagged_delta(tmp_path):
    # Failure canary: a non-None delta must always be sourced (never the old
    # hardcoded-None placeholder, never an untagged number).
    cem = CEM(tmp_path)
    _seed_card(cem)
    brief = cem.retrieve_action_brief(
        TaskContext(description="set assignment_group before assignee")
    )
    if brief.expected_action_delta is not None:
        assert brief.expected_action_delta_source != "none"
    # and Phase 1 never claims causal verification it does not have
    assert brief.expected_action_delta_source != "probe_verified"


def test_retrieval_persists_action_brief_record(tmp_path):
    cem = CEM(tmp_path)
    _seed_card(cem)
    brief = cem.retrieve_action_brief(
        TaskContext(description="set assignment_group before assignee")
    )
    # a fresh kernel over the SAME root must find the persisted record
    reopened = CEM(store=SQLiteStore(tmp_path))
    record = reopened.store.get_action_brief_record(brief.brief_id)
    assert record.influence_id == brief.influence_id
    assert record.selected_card_ids == brief.applicable_card_ids
    assert set(record.candidate_card_ids) >= set(record.selected_card_ids)
    assert record.scorer_version == "lexical_overlap_v0"
    assert record.expected_action_delta_source == brief.expected_action_delta_source
