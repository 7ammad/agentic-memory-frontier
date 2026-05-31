from cem_core.models import (
    ActionBriefRecord,
    ActionInfluenceEvent,
    ConfidenceInterval,
    VerificationProbe,
    VerificationResult,
)


def test_verification_probe_roundtrips_and_defaults_status():
    probe = VerificationProbe(
        kind="held_out_replay",
        target_card_id="card_x",
        control_definition="no-memory control on held-out task T",
        threshold=0.05,
    )
    assert probe.probe_id.startswith("probe_")
    assert probe.status == "scheduled"
    assert VerificationProbe.model_validate_json(probe.model_dump_json()) == probe


def test_verification_result_carries_ci_and_pass_flag():
    result = VerificationResult(
        probe_id="probe_x",
        card_id="card_x",
        measured_lift=0.12,
        measured_lift_ci=ConfidenceInterval(low=0.02, high=0.22),
        passed=True,
        evidence_pointer="influence_123",
    )
    assert result.result_id.startswith("vresult_")
    assert result.measured_lift_ci.low == 0.02
    assert VerificationResult.model_validate_json(result.model_dump_json()) == result


def test_action_brief_record_and_influence_event_link_by_influence_id():
    record = ActionBriefRecord(
        task_id="t1",
        candidate_card_ids=["card_a", "card_b"],
        selected_card_ids=["card_a"],
        score_breakdown_by_card={"card_a": {"precondition_match": 1.0}},
        scorer_version="phase0-contract",
        expected_action_delta_source="none",
        influence_id="influence_123",
    )
    event = ActionInfluenceEvent(
        influence_id="influence_123",
        brief_id=record.brief_id,
        task_id="t1",
        action_taken="selected assignment_group first",
        outcome="success",
        observed_post_brief_delta=0.3,
    )
    assert record.brief_id.startswith("brief_")
    assert event.influence_id == record.influence_id
    assert ActionBriefRecord.model_validate_json(record.model_dump_json()) == record
    assert ActionInfluenceEvent.model_validate_json(event.model_dump_json()) == event


def test_confidence_interval_rejects_extra_fields():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ConfidenceInterval(low=0.0, high=1.0, mean=0.5)


def test_action_brief_new_fields_default_safely():
    from cem_core.models import ActionBrief

    brief = ActionBrief(
        applicable_card_ids=[],
        why_applicable=[],
        preconditions_to_check=[],
        recommended_next_actions=[],
        risks_and_failure_modes=[],
        stale_or_contested_memory_ids_to_ignore=[],
        evidence_links=[],
        confidence_score=0.0,
    )
    assert brief.brief_id.startswith("brief_")
    assert brief.influence_id is None
    assert brief.scorer_version is None
    assert brief.expected_action_delta_source == "none"
    assert brief.score_breakdown_by_card == {}


def test_experience_card_lifecycle_fields_default_to_candidate():
    from cem_core.models import ExperienceCard

    card = ExperienceCard(
        title="t",
        use_when="w",
        evidence_atom_ids=["atom_1"],
        confidence_score=0.5,
        action_brief_template="do x",
    )
    assert card.promotion_status == "candidate"
    assert card.measured_lift is None
    assert card.measured_lift_ci is None
    assert card.verification_result_ids == []
    assert card.deactivated_at is None
    assert card.deactivated_reason is None
    assert card.superseded_by_card_ids == []


def test_old_shape_card_json_loads_with_defaults():
    # Backward-compat canary: a card persisted before Phase 0 (no new fields)
    # must still load, defaulting to candidate.
    from cem_core.models import ExperienceCard

    legacy = (
        '{"card_id":"card_legacy","title":"t","use_when":"w","do":[],"do_not":[],'
        '"check_first":[],"evidence_atom_ids":["atom_1"],"confidence_score":0.5,'
        '"known_exceptions":[],"valid_from":null,"valid_until":null,'
        '"tested_by_probe_ids":[],"last_validated_at":null,"action_brief_template":"do x"}'
    )
    card = ExperienceCard.model_validate_json(legacy)
    assert card.promotion_status == "candidate"
    assert card.measured_lift is None
