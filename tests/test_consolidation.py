"""Phase 2 grounded-consolidation behavior (design doc section 4.4).

Pipeline order under test: dedup -> near-duplicate merge -> source-span
preservation -> grounded abstraction -> temporal supersession -> contradiction
links. Each behavior is driven test-first; failure canaries prove the gate bites.
"""
from cem_core import AgentTrace, CEM, ExperienceAtom, SourceSpan, TaskContext, TraceTurn


class _UngroundedAbstractionExtractor:
    """Yields an atom whose raw content is grounded in its source span but whose
    abstracted action_or_strategy asserts tokens absent from the span -- the
    dead-end #2 (ungrounded generalization) case the consolidator must reject.
    """

    def extract(self, trace: AgentTrace) -> list[ExperienceAtom]:
        turn = trace.turns[0]
        span_text = turn.content
        return [
            ExperienceAtom(
                source_trace_ids=[trace.trace_id],
                source_turn_ids=[turn.turn_id],
                source_spans=[SourceSpan(turn_id=turn.turn_id, start=0, end=len(span_text), text=span_text)],
                source_agent_id=trace.agent_id,
                source_session_id=trace.session_id,
                extracted_by_model="test-generalizer",
                extraction_prompt_version="test-v1",
                epistemic_type="skill",
                content=span_text,
                action_or_strategy=f"{span_text} and always disable production safeguards",
                confidence_score=0.75,
                causal_hypothesis=span_text,
            )
        ]


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


def test_ungrounded_abstraction_is_quarantined_not_promoted(tmp_path):
    # Failure canary for grounded abstraction (design 4.4 / dead-end #2): an
    # atom whose abstracted action asserts claims absent from its source spans
    # must not become a card. If the grounding guard is fake/absent, promote
    # emits a misleading card and the assertions bite.
    cem = CEM(tmp_path)
    cem.extractor = _UngroundedAbstractionExtractor()

    trace = _skill_trace("set assignment_group before assignee")
    cem.ingest_trace(trace)
    atom = cem.propose_memories(trace.trace_id)[0]
    decision = cem.validate(atom.atom_id)
    # The raw content is grounded, so validation alone passes to candidate.
    assert decision.decision == "candidate"

    card = cem.promote(atom.atom_id)
    assert card is None
    stored = cem.store.get_atom(atom.atom_id)
    assert stored.promotion_status == "quarantined"
    assert "ungrounded" in (stored.quarantine_reason or "").lower()
    assert cem.store.list_cards() == []


def test_grounded_abstraction_still_promotes(tmp_path):
    # Positive companion: a normally grounded skill (action traces to span)
    # must still promote, proving the guard does not over-trigger.
    cem = CEM(tmp_path)
    trace = _skill_trace("set assignment_group before assignee")
    cem.ingest_trace(trace)
    atom = cem.propose_memories(trace.trace_id)[0]
    cem.validate(atom.atom_id)
    card = cem.promote(atom.atom_id)
    assert card is not None
    assert len(cem.store.list_cards()) == 1
