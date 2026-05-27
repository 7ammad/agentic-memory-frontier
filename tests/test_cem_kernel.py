from collections.abc import Sequence

from cem_core import AgentTrace, CEM, ContradictionMatch, ExperienceAtom, TaskContext, TraceTurn


def test_trace_ingest_extract_validate_promote_and_retrieve(tmp_path):
    cem = CEM(tmp_path)
    trace = AgentTrace(
        session_id="s1",
        agent_id="codex",
        task_id="incident-form",
        turns=[
            TraceTurn(
                index=0,
                role="environment",
                content="SKILL: select assignment_group before assignee unless the assignee field stays locked",
            )
        ],
        final_outcome="success",
        environment={"domain": "servicenow-like"},
    )

    receipt = cem.ingest_trace(trace)
    assert receipt.turn_count == 1

    atoms = cem.propose_memories(trace.trace_id)
    assert len(atoms) == 1
    assert atoms[0].source_spans[0].text.startswith("select assignment_group")

    results = cem.validate(atoms[0].atom_id)
    assert all(result.passed for result in results)

    card = cem.promote(atoms[0].atom_id)
    assert card is not None

    brief = cem.retrieve_action_brief(
        TaskContext(
            description="Need to submit servicenow-like incident form with assignment_group and assignee",
            domain_scope="servicenow-like",
        )
    )
    assert brief.applicable_card_ids == [card.card_id]
    assert "select assignment_group before assignee" in brief.recommended_next_actions[0]


def test_contradiction_is_quarantined_with_audit_trail(tmp_path):
    cem = CEM(tmp_path)
    trace_one = AgentTrace(
        session_id="s1",
        agent_id="codex",
        turns=[TraceTurn(index=0, role="user", content="PREFERENCE: database=postgres")],
    )
    trace_two = AgentTrace(
        session_id="s1",
        agent_id="codex",
        turns=[TraceTurn(index=1, role="user", content="PREFERENCE: database=mysql")],
    )

    cem.ingest_trace(trace_one)
    first = cem.propose_memories(trace_one.trace_id)[0]
    cem.validate(first.atom_id)

    cem.ingest_trace(trace_two)
    second = cem.propose_memories(trace_two.trace_id)[0]
    cem.validate(second.atom_id)

    second_after = cem.store.get_atom(second.atom_id)
    assert second_after.promotion_status == "quarantined"
    assert "contradicts active memory" in (second_after.quarantine_reason or "")

    audit = cem.audit(second.atom_id)
    assert audit.quarantine_reason is not None
    assert any(result.check_name == "contradiction" and not result.passed for result in audit.validation_results)


def test_assistant_hypothesis_cannot_promote_without_evidence(tmp_path):
    cem = CEM(tmp_path)
    trace = AgentTrace(
        session_id="s1",
        agent_id="codex",
        turns=[TraceTurn(index=0, role="assistant", content="HYPOTHESIS: user hates tests")],
    )

    cem.ingest_trace(trace)
    atom = cem.propose_memories(trace.trace_id)[0]
    cem.validate(atom.atom_id)

    assert cem.promote(atom.atom_id) is None
    stored = cem.store.get_atom(atom.atom_id)
    assert stored.promotion_status == "quarantined"
    assert "assistant hypothesis" in (stored.quarantine_reason or "")


class EmptyExtractor:
    def extract(self, trace: AgentTrace) -> list[ExperienceAtom]:
        return []


class NoopContradictionDetector:
    def find_conflicts(
        self,
        atom: ExperienceAtom,
        active_atoms: Sequence[ExperienceAtom],
    ) -> ContradictionMatch | None:
        return None


def test_extractor_strategy_can_be_swapped(tmp_path):
    cem = CEM(tmp_path, extractor=EmptyExtractor())
    trace = AgentTrace(
        session_id="s1",
        agent_id="codex",
        turns=[TraceTurn(index=0, role="user", content="PREFERENCE: database=postgres")],
    )

    cem.ingest_trace(trace)

    assert cem.propose_memories(trace.trace_id) == []


def test_contradiction_strategy_can_be_swapped(tmp_path):
    cem = CEM(tmp_path, contradiction_detector=NoopContradictionDetector())
    trace_one = AgentTrace(
        session_id="s1",
        agent_id="codex",
        turns=[TraceTurn(index=0, role="user", content="PREFERENCE: database=postgres")],
    )
    trace_two = AgentTrace(
        session_id="s1",
        agent_id="codex",
        turns=[TraceTurn(index=1, role="user", content="PREFERENCE: database=mysql")],
    )

    cem.ingest_trace(trace_one)
    first = cem.propose_memories(trace_one.trace_id)[0]
    cem.validate(first.atom_id)
    cem.ingest_trace(trace_two)
    second = cem.propose_memories(trace_two.trace_id)[0]
    cem.validate(second.atom_id)

    stored = cem.store.get_atom(second.atom_id)
    assert stored.promotion_status == "candidate"
    assert stored.quarantine_reason is None
