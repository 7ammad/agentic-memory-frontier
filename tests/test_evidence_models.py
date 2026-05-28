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
