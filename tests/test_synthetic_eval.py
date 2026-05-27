from cem_eval import run_synthetic_corruption_eval


def test_synthetic_corruption_eval_exercises_write_path(tmp_path):
    result = run_synthetic_corruption_eval(tmp_path)

    assert result.proposed_count == 4
    assert result.quarantined_count >= 2
    assert result.promoted_count >= 1
    assert result.contradiction_detected
    assert result.hypothesis_quarantined
    assert result.action_brief_card_count >= 1
