from cem_core import CEM, InMemoryStore
from cem_core.models import BehaviorInvariant, DecisionIntent
from cem_core.supersession import SupersessionLedger


def _invariant() -> BehaviorInvariant:
    return BehaviorInvariant(
        source_attribution_id="attribution_1",
        source_record_id="experience_1",
        authority="owner_instruction",
        scope="global_agent_behavior",
        trigger="equivalent situation match",
        forbidden_repeat="scope general behavior failure as project-specific",
        corrected_action="route general Codex/AMS behavior correction to codex-harness",
        enforcement="steer_or_block",
        evidence_ids=["attribution_1", "directive_1"],
    )


def _decision() -> DecisionIntent:
    return DecisionIntent(
        agent_id="codex",
        session_id="session_7",
        task_id="task_7",
        proposed_action="scope general behavior failure as project-specific",
        action_kind="decision",
        expected_outcome="future action is selected correctly",
        applicable_authority="owner_instruction",
        authority_refs=["directive_current"],
        approval_state="not_required",
        experiment_state="not_experiment",
        runtime_surface="codex-desktop",
        evidence_ids=["directive_current"],
    )


def test_supersession_marks_invariant_inactive_and_auditable():
    invariant = _invariant()

    event = SupersessionLedger().supersede_invariant(
        invariant,
        source="current_owner_instruction",
        reason="owner superseded the old correction",
        evidence_ids=["directive_new_owner"],
    )

    assert invariant.supersession_status == "superseded"
    assert event.supersession_id.startswith("supersession_")
    assert event.target_id == invariant.invariant_id
    assert event.target_type == "invariant"
    assert event.reversible is True
    assert "directive_new_owner" in event.evidence_ids
    assert "reasoning" not in event.audit_summary()


def test_superseded_invariant_stops_firing_on_next_equivalent_decision():
    store = InMemoryStore()
    cem = CEM(store=store)
    invariant = _invariant()
    event = SupersessionLedger().supersede_invariant(
        invariant,
        source="current_owner_instruction",
        reason="owner superseded the old correction",
        evidence_ids=["directive_new_owner"],
    )
    store.save_behavior_invariant(invariant)
    store.save_supersession_event(event)

    matches = cem.match_situation(_decision())

    assert matches == []


def test_reversing_supersession_reactivates_invariant():
    store = InMemoryStore()
    cem = CEM(store=store)
    invariant = _invariant()
    ledger = SupersessionLedger()
    event = ledger.supersede_invariant(
        invariant,
        source="current_owner_instruction",
        reason="owner superseded the old correction",
        evidence_ids=["directive_new_owner"],
    )
    reversal = ledger.reverse_invariant_supersession(
        invariant,
        event,
        reason="owner restored the invariant",
        evidence_ids=["directive_restore"],
    )
    store.save_behavior_invariant(invariant)
    store.save_supersession_event(event)
    store.save_supersession_event(reversal)

    matches = cem.match_situation(_decision())

    assert invariant.supersession_status == "active"
    assert reversal.reverses_supersession_id == event.supersession_id
    assert len(matches) == 1
    assert matches[0].fires is True


def test_owner_override_creates_auditable_supersession_event_without_deleting_evidence():
    invariant = _invariant()

    event = SupersessionLedger().record_owner_override(
        invariant,
        reason="owner approved a one-time exception",
        evidence_ids=["reasoning_receipt_1"],
    )

    assert event.source == "owner_approved_override"
    assert event.target_id == invariant.invariant_id
    assert event.reversible is True
    assert invariant.invariant_id in event.evidence_ids
    assert "reasoning_receipt_1" in event.evidence_ids
