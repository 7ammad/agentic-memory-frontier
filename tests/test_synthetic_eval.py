from cem_eval import run_synthetic_corruption_eval


def test_synthetic_corruption_eval_exercises_write_path(tmp_path):
    result = run_synthetic_corruption_eval(tmp_path)

    assert result.fixture_case_count == 11
    assert result.proposed_count == 11
    assert result.quarantined_count == 4
    assert result.promoted_count == 6
    assert result.contradiction_detected
    assert result.hypothesis_quarantined
    assert result.action_brief_card_count == 6
    assert result.false_memory_resistance == 1.0
    assert result.contradiction_recall == 1.0
    assert result.false_quarantine_rate == 0.0
    assert result.unvalidated_memory.metrics.false_memory_resistance == 0.0
    assert result.unvalidated_memory.trusted_false_memory_count == 5
    assert result.cem0_validation.trusted_false_memory_count == 0
    assert result.cem0_validation.decision_reason_codes["database=mysql"] == ["contradiction"]
    assert "assistant_hypothesis" in result.cem0_validation.decision_reason_codes[
        "user always wants us to skip tests"
    ]
    assert result.cem0_validation.decision_reason_codes["production deploy already finished"] == ["unsupported"]
    assert result.cem0_validation.metrics.stale_memory_suppression == 1.0
    assert result.cem0_validation.metrics.false_memory_resistance_by_risk == {
        "assistant_hypothesis": 1.0,
        "contradiction": 1.0,
        "stale_preference": 1.0,
        "unsupported": 1.0,
    }
    assert result.cem0_validation.metrics.valid_memory_retention_by_risk == {
        "valid_failure_mode": 1.0,
        "valid_instruction": 1.0,
        "valid_preference": 1.0,
        "valid_skill": 1.0,
    }
    assert result.unvalidated_memory.metrics.action_brief_card_count > result.action_brief_card_count
