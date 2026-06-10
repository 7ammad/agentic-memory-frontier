import pytest

from cem_core.models import (
    ActionBriefRecord,
    ActionDecisionReceipt,
    ActionInfluenceEvent,
    BehaviorInvariant,
    DecisionIntent,
    ExperienceAttribution,
    ExperienceGraphRecord,
    ReasoningControlReceipt,
    RuntimeInterceptionBoundary,
    SharedExperienceEnvelope,
    SituationMatch,
    SkillCandidate,
    SupersessionEvent,
    MultiAgentGovernanceReceipt,
    VerificationProbe,
    VerificationResult,
)
from cem_core.storage import InMemoryStore, SQLiteStore


def _stores(tmp_path):
    return [SQLiteStore(tmp_path / "db"), InMemoryStore()]


def test_probe_and_result_roundtrip_in_both_backends(tmp_path):
    for store in _stores(tmp_path):
        probe = VerificationProbe(
            kind="negative_control",
            target_card_id="card_x",
            control_definition="injected false memory must not promote",
            threshold=0.0,
        )
        store.save_probe(probe)
        assert store.get_probe(probe.probe_id) == probe

        result = VerificationResult(
            probe_id=probe.probe_id, card_id="card_x", measured_lift=0.1, passed=True
        )
        store.save_verification_result(result)
        assert store.list_verification_results("card_x") == [result]


def test_brief_record_and_influence_event_roundtrip(tmp_path):
    for store in _stores(tmp_path):
        record = ActionBriefRecord(
            scorer_version="phase0", influence_id="influence_1", task_id="t1"
        )
        store.save_action_brief_record(record)
        assert store.get_action_brief_record(record.brief_id) == record

        event = ActionInfluenceEvent(influence_id="influence_1", brief_id=record.brief_id)
        store.save_action_influence_event(event)
        assert store.list_action_influence_events("influence_1") == [event]


def test_experience_graph_record_roundtrip_in_both_backends(tmp_path):
    for store in _stores(tmp_path):
        intent = DecisionIntent(
            agent_id="codex",
            session_id="session_1",
            task_id="task_1",
            proposed_action="run codex --version",
            action_kind="command",
            expected_outcome="command exits successfully",
            applicable_authority="current_evidence",
            approval_state="not_required",
            experiment_state="not_experiment",
            runtime_surface="ams-guarded-command",
            evidence_ids=["control_1"],
        )
        record = ExperienceGraphRecord(
            decision=intent,
            actual_outcome="command exited 0",
            outcome_status="success",
            scope_candidate="task",
            outcome_evidence_ids=["trace_1"],
        )

        store.save_experience_graph_record(record)

        assert store.get_experience_graph_record(record.record_id) == record
        assert store.list_experience_graph_records() == [record]


def test_experience_attribution_roundtrip_in_both_backends(tmp_path):
    for store in _stores(tmp_path):
        attribution = ExperienceAttribution(
            record_id="experience_1",
            decision_id="decision_1",
            attribution_class="mistake",
            scope_candidate="global_agent_behavior",
            authority_basis="owner_instruction",
            authority_refs=["directive_1"],
            non_repeat_candidate=True,
            invariant_candidate=True,
            confidence=0.9,
            receipt_summary="Owner correction proves this is a non-repeat candidate.",
            evidence_ids=["directive_1", "trace_1"],
        )

        store.save_experience_attribution(attribution)

        assert store.get_experience_attribution(attribution.attribution_id) == attribution
        assert store.list_experience_attributions() == [attribution]


def test_phase3_invariant_and_skill_roundtrip_in_both_backends(tmp_path):
    for store in _stores(tmp_path):
        invariant = BehaviorInvariant(
            source_attribution_id="attribution_1",
            source_record_id="experience_1",
            authority="owner_instruction",
            scope="global_agent_behavior",
            trigger="equivalent situation match",
            forbidden_repeat="scope general correction to project noun",
            corrected_action="route correction to codex-harness",
            enforcement="steer_or_block",
            evidence_ids=["attribution_1", "directive_1"],
        )
        skill = SkillCandidate(
            source_attribution_id="attribution_2",
            source_record_id="experience_2",
            transfer_scope="agent",
            preconditions=["authority_basis=system_instruction"],
            procedure=["run startup brief before edits"],
            expected_result="memory evidence loaded",
            failure_boundaries=["do not apply when owner supersedes"],
            evidence_ids=["attribution_2", "trace_2"],
            when_not_to_apply=["missing authority evidence"],
        )

        store.save_behavior_invariant(invariant)
        store.save_skill_candidate(skill)

        assert store.get_behavior_invariant(invariant.invariant_id) == invariant
        assert store.list_behavior_invariants() == [invariant]
        assert store.get_skill_candidate(skill.skill_id) == skill
        assert store.list_skill_candidates() == [skill]


def test_situation_match_roundtrip_in_both_backends(tmp_path):
    for store in _stores(tmp_path):
        match = SituationMatch(
            decision_id="decision_1",
            source_id="invariant_1",
            source_type="invariant",
            match_type="paraphrase_repeat",
            fires=True,
            confidence=0.78,
            reason="paraphrase repeat matched invariant markers",
            evidence_ids=["decision_1", "invariant_1"],
        )

        store.save_situation_match(match)

        assert store.get_situation_match(match.match_id) == match
        assert store.list_situation_matches() == [match]


def test_action_decision_receipt_roundtrip_in_both_backends(tmp_path):
    for store in _stores(tmp_path):
        receipt = ActionDecisionReceipt(
            decision_id="decision_1",
            original_action="repeat known mistake",
            action_to_execute="use corrected action",
            verdict="steer",
            downstream_action_allowed=True,
            user_visible=False,
            boundary_status="interceptable",
            boundary_id="boundary_1",
            match_ids=["match_1"],
            source_ids=["invariant_1"],
            reason="silently steered known repeat to corrected action",
            evidence_ids=["decision_1", "match_1", "invariant_1"],
        )

        store.save_action_decision_receipt(receipt)

        assert store.get_action_decision_receipt(receipt.receipt_id) == receipt
        assert store.list_action_decision_receipts() == [receipt]


def test_runtime_interception_boundary_roundtrip_in_both_backends(tmp_path):
    for store in _stores(tmp_path):
        boundary = RuntimeInterceptionBoundary(
            action_kind="decision",
            runtime_surface="codex-desktop",
            interceptable=True,
            supported_verdicts=["allow", "steer", "block", "degraded_allow"],
            evidence_ids=["boundary_1"],
        )

        store.save_runtime_interception_boundary(boundary)

        assert store.get_runtime_interception_boundary(boundary.boundary_id) == boundary
        assert store.list_runtime_interception_boundaries() == [boundary]


def test_reasoning_control_receipt_roundtrip_in_both_backends(tmp_path):
    for store in _stores(tmp_path):
        receipt = ReasoningControlReceipt(
            action_receipt_id="receipt_1",
            original_verdict="block",
            final_verdict="override_allowed",
            ams_effect="override",
            matched_experience_ids=["invariant_1"],
            authority="owner_instruction",
            user_visible=True,
            receipt_available=True,
            downgrade_allowed=True,
            override_receipt_required=True,
            summary="Downgrade allowed by owner instruction.",
            evidence_ids=["receipt_1", "invariant_1"],
        )

        store.save_reasoning_control_receipt(receipt)

        assert store.get_reasoning_control_receipt(receipt.reasoning_receipt_id) == receipt
        assert store.list_reasoning_control_receipts() == [receipt]


def test_supersession_event_roundtrip_in_both_backends(tmp_path):
    for store in _stores(tmp_path):
        event = SupersessionEvent(
            target_id="invariant_1",
            target_type="invariant",
            source="current_owner_instruction",
            reason="owner superseded this invariant",
            evidence_ids=["invariant_1", "directive_1"],
        )

        store.save_supersession_event(event)

        assert store.get_supersession_event(event.supersession_id) == event
        assert store.list_supersession_events() == [event]


def test_shared_experience_governance_roundtrip_in_both_backends(tmp_path):
    for store in _stores(tmp_path):
        invariant = BehaviorInvariant(
            source_attribution_id="attribution_1",
            source_record_id="experience_1",
            authority="owner_instruction",
            scope="global_agent_behavior",
            trigger="equivalent situation match",
            forbidden_repeat="scope general behavior failure as project-specific",
            corrected_action="route to codex-harness",
            enforcement="steer_or_block",
            evidence_ids=["attribution_1"],
        )
        envelope = SharedExperienceEnvelope(
            writer_agent_id="codex",
            recipient_agent_id="cursor-agent",
            experience=invariant,
            writer_authority="owner_instruction",
            visibility="all_agents",
            ownership="owner",
            requested_scope="global_agent_behavior",
            provenance_ids=["directive_owner"],
        )
        receipt = MultiAgentGovernanceReceipt(
            envelope_id=envelope.envelope_id,
            writer_agent_id="codex",
            recipient_agent_id="cursor-agent",
            verdict="accept",
            recipient_applicability="applicable",
            promoted_scope="global_agent_behavior",
            reason="accepted",
            evidence_ids=[envelope.envelope_id],
        )

        store.save_shared_experience_envelope(envelope)
        store.save_multi_agent_governance_receipt(receipt)

        assert store.get_shared_experience_envelope(envelope.envelope_id) == envelope
        assert store.list_shared_experience_envelopes() == [envelope]
        assert store.get_multi_agent_governance_receipt(receipt.governance_receipt_id) == receipt
        assert store.list_multi_agent_governance_receipts() == [receipt]


def test_missing_probe_raises_keyerror(tmp_path):
    for store in _stores(tmp_path):
        with pytest.raises(KeyError):
            store.get_probe("nope")
