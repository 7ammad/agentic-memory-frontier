from cem_eval import run_synthetic_corruption_eval


def test_synthetic_corruption_eval_exercises_write_path(tmp_path):
    result = run_synthetic_corruption_eval(tmp_path)

    assert result.proposed_count == 4
    assert result.quarantined_count >= 2
    assert result.promoted_count >= 1
    assert result.contradiction_detected
    assert result.hypothesis_quarantined
    assert result.action_brief_card_count >= 1
    assert result.false_memory_resistance == 1.0
    assert result.contradiction_recall == 1.0
    assert result.false_quarantine_rate == 0.0
    assert result.unvalidated_memory.metrics.false_memory_resistance == 0.0
    assert result.unvalidated_memory.trusted_false_memory_count == 2
    assert result.cem0_validation.trusted_false_memory_count == 0
    assert result.unvalidated_memory.metrics.action_brief_card_count > result.action_brief_card_count
