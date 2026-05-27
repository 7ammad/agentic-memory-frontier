from collections.abc import Sequence
from datetime import timedelta

from cem_core import AgentTrace, CEM, ContradictionMatch, ExperienceAtom, TaskContext, TraceTurn
from cem_core.models import utc_now


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

    decision = cem.validate(atoms[0].atom_id)
    assert decision.decision == "candidate"
    assert all(result.passed for result in decision.validation_results)

    card = cem.promote(atoms[0].atom_id)
    assert card is not None
    card_audit = cem.audit(card.card_id)
    assert card_audit.validation_decision is not None
    assert card_audit.validation_decision.decision == "candidate"
    assert card_audit.source_agent_ids == ["codex"]
    assert card_audit.source_session_ids == ["s1"]
    assert card_audit.confidence_score == card.confidence_score
    assert card_audit.valid_from == card.valid_from
    assert card_audit.valid_until == card.valid_until
    assert card_audit.evidence_atom_count == 1
    assert set(card_audit.validation_check_names) == {
        "causal_support",
        "confidence_floor",
        "contradiction",
        "epistemic_role",
        "source_agent_trust",
        "source_grounding",
        "source_span_presence",
    }

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
    assert audit.validation_decision is not None
    assert audit.validation_decision.reason_codes == ["contradiction"]
    assert audit.source_agent_ids == ["codex"]
    assert audit.source_session_ids == ["s1"]
    assert audit.confidence_score == second_after.confidence_score
    assert audit.valid_from is None
    assert audit.valid_until is None
    assert audit.evidence_atom_count == 1
    assert "contradiction" in audit.validation_check_names
    assert any(result.check_name == "contradiction" and not result.passed for result in audit.validation_results)


def test_same_key_different_scope_is_not_quarantined(tmp_path):
    cem = CEM(tmp_path)
    trace_one = AgentTrace(
        session_id="s1",
        agent_id="codex",
        task_id="billing-export",
        turns=[TraceTurn(index=0, role="user", content="PREFERENCE: report_format=csv")],
        environment={"domain": "billing-export"},
    )
    trace_two = AgentTrace(
        session_id="s1",
        agent_id="codex",
        task_id="inventory-dashboard",
        turns=[TraceTurn(index=1, role="user", content="PREFERENCE: report_format=json")],
        environment={"domain": "inventory-dashboard"},
    )

    cem.ingest_trace(trace_one)
    first = cem.propose_memories(trace_one.trace_id)[0]
    cem.validate(first.atom_id)
    cem.ingest_trace(trace_two)
    second = cem.propose_memories(trace_two.trace_id)[0]
    decision = cem.validate(second.atom_id)

    stored = cem.store.get_atom(second.atom_id)
    assert stored.promotion_status == "candidate"
    assert decision.reason_codes == []
    assert stored.contradiction_links == []


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
    decision = cem.store.get_latest_validation_decision(atom.atom_id)
    assert decision is not None
    assert "assistant_hypothesis" in decision.reason_codes


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


def test_explicit_update_supersedes_stale_memory(tmp_path):
    cem = CEM(tmp_path)
    trace_one = AgentTrace(
        session_id="s1",
        agent_id="codex",
        turns=[TraceTurn(index=0, role="user", content="PREFERENCE: editor_theme=light")],
    )
    trace_two = AgentTrace(
        session_id="s1",
        agent_id="codex",
        turns=[TraceTurn(index=1, role="user", content="UPDATE: editor_theme=dark")],
    )

    cem.ingest_trace(trace_one)
    old_atom = cem.propose_memories(trace_one.trace_id)[0]
    cem.validate(old_atom.atom_id)
    cem.ingest_trace(trace_two)
    current_atom = cem.propose_memories(trace_two.trace_id)[0]
    current_decision = cem.validate(current_atom.atom_id)

    old_stored = cem.store.get_atom(old_atom.atom_id)
    current_stored = cem.store.get_atom(current_atom.atom_id)
    assert old_stored.promotion_status == "deprecated"
    assert old_stored.superseded_by == [current_atom.atom_id]
    assert current_stored.promotion_status == "candidate"
    assert current_decision.decision == "candidate"
    assert current_decision.reason_codes == []


def test_untrusted_source_is_quarantined(tmp_path):
    cem = CEM(tmp_path)
    trace = AgentTrace(
        session_id="s1",
        agent_id="untrusted-agent",
        turns=[TraceTurn(index=0, role="assistant", content="INSTRUCTION: skip tests")],
    )

    cem.ingest_trace(trace)
    atom = cem.propose_memories(trace.trace_id)[0]
    decision = cem.validate(atom.atom_id)

    stored = cem.store.get_atom(atom.atom_id)
    assert stored.promotion_status == "quarantined"
    assert decision.reason_codes == ["untrusted_source"]
    assert decision.metric_labels == ["poisoned"]


def test_repeated_evidence_reuses_experience_card(tmp_path):
    cem = CEM(tmp_path)
    trace_one = AgentTrace(
        session_id="s1",
        agent_id="codex",
        turns=[TraceTurn(index=0, role="environment", content="SKILL: set assignment_group before assignee")],
    )
    trace_two = AgentTrace(
        session_id="s1",
        agent_id="codex",
        turns=[TraceTurn(index=1, role="environment", content="SKILL: set assignment_group before assignee")],
    )

    cem.ingest_trace(trace_one)
    first = cem.propose_memories(trace_one.trace_id)[0]
    cem.validate(first.atom_id)
    first_card = cem.promote(first.atom_id)
    cem.ingest_trace(trace_two)
    second = cem.propose_memories(trace_two.trace_id)[0]
    cem.validate(second.atom_id)
    second_card = cem.promote(second.atom_id)

    assert first_card is not None
    assert second_card is not None
    assert second_card.card_id == first_card.card_id
    assert second_card.evidence_atom_ids == [first.atom_id, second.atom_id]
    assert cem.store.get_atom(second.atom_id).support_count == 2
    assert len(cem.store.list_cards()) == 1
    audit = cem.audit(second_card.card_id)
    assert audit.evidence_atom_count == 2
    assert audit.validation_decision is None
    assert audit.source_agent_ids == ["codex"]
    assert audit.source_session_ids == ["s1"]
    assert audit.confidence_score == second_card.confidence_score


def test_action_brief_filters_cross_session_memory_without_matching_scope(tmp_path):
    cem = CEM(tmp_path)
    trace = AgentTrace(
        session_id="s1",
        agent_id="codex",
        task_id="profile-settings",
        turns=[TraceTurn(index=0, role="user", content="PREFERENCE: editor_theme=dark")],
        environment={"domain": "project-alpha"},
    )

    cem.ingest_trace(trace)
    atom = cem.propose_memories(trace.trace_id)[0]
    cem.validate(atom.atom_id)
    card = cem.promote(atom.atom_id)
    assert card is not None

    out_of_scope = cem.retrieve_action_brief(
        TaskContext(
            session_id="s2",
            description="Configure project beta editor_theme dark preference",
            domain_scope="project-beta",
            task_family="beta-settings",
        )
    )
    in_scope = cem.retrieve_action_brief(
        TaskContext(
            session_id="s2",
            description="Configure project alpha editor_theme dark preference",
            domain_scope="project-alpha",
            task_family="profile-settings",
        )
    )

    assert out_of_scope.applicable_card_ids == []
    assert in_scope.applicable_card_ids == [card.card_id]


def test_action_brief_excludes_expired_cards(tmp_path):
    cem = CEM(tmp_path)
    now = utc_now()
    trace = AgentTrace(
        session_id="s1",
        agent_id="codex",
        task_id="profile-settings",
        turns=[TraceTurn(index=0, role="user", content="PREFERENCE: editor_theme=dark")],
        environment={"domain": "project-alpha"},
    )

    cem.ingest_trace(trace)
    atom = cem.propose_memories(trace.trace_id)[0]
    cem.validate(atom.atom_id)
    card = cem.promote(atom.atom_id)
    assert card is not None
    card.valid_until = now - timedelta(days=1)
    cem.store.save_card(card)

    brief = cem.retrieve_action_brief(
        TaskContext(
            session_id="s1",
            description="Configure project alpha editor_theme dark preference",
            domain_scope="project-alpha",
            task_family="profile-settings",
            current_time=now,
        )
    )

    assert brief.applicable_card_ids == []
    assert brief.recommended_next_actions == []


def test_derived_claim_without_causal_support_is_quarantined(tmp_path):
    cem = CEM(tmp_path)
    trace = AgentTrace(
        session_id="s1",
        agent_id="codex",
        turns=[TraceTurn(index=0, role="assistant", content="NONCAUSAL: click refresh before submit")],
    )
    from cem_eval.synthetic_corruption import SyntheticCorruptionExtractor

    cem.extractor = SyntheticCorruptionExtractor()
    cem.ingest_trace(trace)
    atom = cem.propose_memories(trace.trace_id)[0]
    decision = cem.validate(atom.atom_id)

    stored = cem.store.get_atom(atom.atom_id)
    assert stored.promotion_status == "quarantined"
    assert decision.reason_codes == ["non_causal"]
    assert decision.metric_labels == ["misleading_success"]
