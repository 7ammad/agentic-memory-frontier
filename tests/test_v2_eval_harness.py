from cem_eval.v2_eval_harness import (
    V2_ACCEPTANCE_BATTERY_IDS,
    V2_EVAL_SUITE_NAMES,
    run_v2_eval_harness,
)


def test_v2_eval_harness_runs_all_named_phase9_suites(tmp_path):
    report = run_v2_eval_harness(tmp_path)

    assert report.verdict == "PASS"
    assert [row.suite_name for row in report.rows] == list(V2_EVAL_SUITE_NAMES)
    assert report.suite_count == 7
    assert report.case_count == len(V2_ACCEPTANCE_BATTERY_IDS)
    assert report.pass_count == report.case_count
    assert report.fail_count == 0
    assert report.false_block_count == 0
    assert report.false_block_budget == 0
    assert report.acceptance_battery_ids == list(V2_ACCEPTANCE_BATTERY_IDS)
    assert all(row.pass_count == row.case_count for row in report.rows)
    assert all(row.receipt_ids for row in report.rows)
    assert "reasoning" not in report.audit_summary()


def test_v2_eval_harness_proves_non_repeat_and_silent_steering(tmp_path):
    report = run_v2_eval_harness(tmp_path)

    non_repeat = report.row_by_suite("NonRepeatEval")

    assert non_repeat.pass_count == non_repeat.case_count
    assert {"V2-SEED-001", "V2-SEED-002", "V2-SEED-005", "V2-SEED-006", "V2-SEED-007", "V2-SEED-008"} <= set(
        non_repeat.acceptance_ids
    )
    assert non_repeat.primary_metric_name == "non_repeat_success_rate"
    assert non_repeat.primary_metric_value == 1.0
    assert non_repeat.secondary_metrics["silent_steer_count"] >= 1
    assert non_repeat.secondary_metrics["blocked_repeat_count"] >= 1
    assert non_repeat.secondary_metrics["downgrade_receipt_count"] >= 1


def test_v2_eval_harness_tracks_false_block_budget_and_valid_neighbors(tmp_path):
    report = run_v2_eval_harness(tmp_path)

    false_block = report.row_by_suite("FalseBlockEval")
    approved = report.row_by_suite("ApprovedExperimentEval")

    assert report.false_block_count == 0
    assert false_block.primary_metric_name == "false_block_rate"
    assert false_block.primary_metric_value == 0.0
    assert false_block.acceptance_ids == ["V2-SEED-003"]
    assert approved.acceptance_ids == ["V2-SEED-004"]
    assert approved.secondary_metrics["mistake_invariant_count"] == 0


def test_v2_eval_harness_proves_transfer_boundaries_supersession_multi_agent_and_pollution(tmp_path):
    report = run_v2_eval_harness(tmp_path)

    skill = report.row_by_suite("SkillTransferEval")
    supersession = report.row_by_suite("SupersessionEval")
    multi_agent = report.row_by_suite("MultiAgentConflictEval")
    pollution = report.row_by_suite("ContextPollutionEval")

    assert skill.acceptance_ids == ["V2-SEED-009", "V2-SEED-010"]
    assert skill.secondary_metrics["skill_transfer_count"] == 1
    assert skill.secondary_metrics["skill_false_transfer_count"] == 0
    assert supersession.acceptance_ids == ["V2-SEED-011"]
    assert supersession.secondary_metrics["superseded_match_count"] == 0
    assert multi_agent.acceptance_ids == ["V2-SEED-012"]
    assert multi_agent.secondary_metrics["scope_pollution_detected_count"] == 1
    assert pollution.acceptance_ids == ["V2-SEED-013"]
    assert pollution.secondary_metrics["low_authority_enforced_rule_count"] == 0
