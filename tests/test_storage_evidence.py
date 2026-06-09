import pytest

from cem_core.models import (
    ActionBriefRecord,
    ActionInfluenceEvent,
    BehaviorInvariant,
    DecisionIntent,
    ExperienceAttribution,
    ExperienceGraphRecord,
    SkillCandidate,
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


def test_missing_probe_raises_keyerror(tmp_path):
    for store in _stores(tmp_path):
        with pytest.raises(KeyError):
            store.get_probe("nope")
