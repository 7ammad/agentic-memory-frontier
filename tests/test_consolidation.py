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


def _pref_trace(marker: str, key_value: str, *, index: int, domain: str) -> AgentTrace:
    return AgentTrace(
        session_id="s1",
        agent_id="codex",
        task_id="ide-config",
        turns=[TraceTurn(index=index, role="user", content=f"{marker} {key_value}")],
        environment={"domain": domain},
    )


def test_newer_atom_supersedes_stale_card_and_removes_it_from_retrieval(tmp_path):
    # Design 4.4 temporal supersession: a contradicting newer atom must set the
    # stale card's superseded_by/deactivated fields AND remove it from retrieval
    # -- not merely a link. Atom-level supersession already exists; this drives
    # the card-level half.
    cem = CEM(tmp_path)

    old = _pref_trace("PREFERENCE:", "editor_theme=light", index=0, domain="ide-settings")
    cem.ingest_trace(old)
    old_atom = cem.propose_memories(old.trace_id)[0]
    cem.validate(old_atom.atom_id)
    card_a = cem.promote(old_atom.atom_id)
    assert card_a is not None

    new = _pref_trace("UPDATE:", "editor_theme=dark", index=1, domain="ide-settings")
    cem.ingest_trace(new)
    new_atom = cem.propose_memories(new.trace_id)[0]
    cem.validate(new_atom.atom_id)
    card_b = cem.promote(new_atom.atom_id)
    assert card_b is not None
    assert card_b.card_id != card_a.card_id

    # Card-level supersession fields are set on the stale card.
    stale = cem.store.get_card(card_a.card_id)
    assert stale.promotion_status == "superseded"
    assert stale.deactivated_at is not None
    assert stale.deactivated_reason is not None
    assert stale.superseded_by_card_ids == [card_b.card_id]

    # The stale card is gone from retrieval; the current card is still served.
    brief = cem.retrieve_action_brief(
        TaskContext(
            session_id="s2",
            description="configure editor_theme preference",
            domain_scope="ide-settings",
        )
    )
    assert card_a.card_id not in brief.applicable_card_ids
    assert card_b.card_id in brief.applicable_card_ids


def test_contradicting_cards_are_cross_linked_and_both_survive(tmp_path):
    # Design 4.4 contradiction links (distinct from temporal supersession): two
    # claims on the same key with different values that live in DIFFERENT
    # operational scopes are not a temporal replacement -- neither supersedes the
    # other, and same-scope quarantine does not fire (cross-scope). They must both
    # promote AND be bidirectionally linked so 4.1's contradiction penalty (Phase
    # 3) has real input. If linking is absent the contradicts_card_ids assertions
    # bite.
    cem = CEM(tmp_path)

    light = _pref_trace("PREFERENCE:", "editor_theme=light", index=0, domain="team-a")
    cem.ingest_trace(light)
    light_atom = cem.propose_memories(light.trace_id)[0]
    cem.validate(light_atom.atom_id)
    card_light = cem.promote(light_atom.atom_id)
    assert card_light is not None

    dark = _pref_trace("PREFERENCE:", "editor_theme=dark", index=1, domain="team-b")
    cem.ingest_trace(dark)
    dark_atom = cem.propose_memories(dark.trace_id)[0]
    # Cross-scope: validation must NOT quarantine the second claim.
    decision = cem.validate(dark_atom.atom_id)
    assert decision.decision == "candidate"
    card_dark = cem.promote(dark_atom.atom_id)
    assert card_dark is not None
    assert card_dark.card_id != card_light.card_id

    linked_light = cem.store.get_card(card_light.card_id)
    linked_dark = cem.store.get_card(card_dark.card_id)
    # Bidirectional contradiction link.
    assert card_dark.card_id in linked_light.contradicts_card_ids
    assert card_light.card_id in linked_dark.contradicts_card_ids
    # Both remain active -- a contradiction link coexists, it does not supersede.
    assert linked_light.promotion_status == "candidate"
    assert linked_dark.promotion_status == "candidate"


def test_unrelated_cards_are_not_contradiction_linked(tmp_path):
    # Over-link canary: two cards whose claims share no key must stay unlinked.
    # If the link predicate is too loose this gains a spurious link and bites.
    cem = CEM(tmp_path)

    theme = _pref_trace("PREFERENCE:", "editor_theme=light", index=0, domain="team-a")
    cem.ingest_trace(theme)
    theme_atom = cem.propose_memories(theme.trace_id)[0]
    cem.validate(theme_atom.atom_id)
    card_theme = cem.promote(theme_atom.atom_id)

    font = _pref_trace("PREFERENCE:", "font_size=14", index=1, domain="team-b")
    cem.ingest_trace(font)
    font_atom = cem.propose_memories(font.trace_id)[0]
    cem.validate(font_atom.atom_id)
    card_font = cem.promote(font_atom.atom_id)

    assert cem.store.get_card(card_theme.card_id).contradicts_card_ids == []
    assert cem.store.get_card(card_font.card_id).contradicts_card_ids == []
