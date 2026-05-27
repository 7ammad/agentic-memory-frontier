from cem_eval import (
    render_synthetic_eval_markdown,
    run_halumem_facsimile_eval,
    run_synthetic_corruption_eval,
    run_workflow_gotcha_demo,
)


def test_synthetic_corruption_eval_exercises_write_path(tmp_path):
    result = run_synthetic_corruption_eval(tmp_path)

    assert result.fixture_case_count == 16
    assert result.proposed_count == 17
    assert result.quarantined_count == 6
    assert result.promoted_count == 10
    assert result.contradiction_detected
    assert result.hypothesis_quarantined
    assert result.action_brief_card_count == 6
    assert result.false_memory_resistance == 1.0
    assert result.contradiction_recall == 1.0
    assert result.false_quarantine_rate == 0.0
    assert result.no_memory.metrics.action_brief_card_count == 0
    assert result.no_memory.action_brief_recommended_actions == []
    assert result.no_memory.expected_action_delta == 0.0
    assert result.report.suite_name == "synthetic_corruption"
    assert [row.name for row in result.report.baseline_rows] == [
        "no_memory",
        "raw_trace_retrieval",
        "summary_reflection",
        "unvalidated_memory",
    ]
    assert result.report.cem0_row.name == "cem0_validation"
    assert result.report.cem0_row.expected_action_delta == 1.0
    comparisons = {row.baseline_name: row for row in result.report.comparison_rows}
    assert comparisons["unvalidated_memory"].false_memory_resistance_delta == 1.0
    assert round(comparisons["unvalidated_memory"].expected_action_delta_delta, 3) == 0.7
    assert comparisons["unvalidated_memory"].trusted_false_memory_reduction == 7
    assert comparisons["unvalidated_memory"].action_brief_card_reduction == 8
    assert round(comparisons["summary_reflection"].expected_action_delta_delta, 3) == 1.033
    assert result.raw_trace_retrieval.trusted_false_memory_count == 7
    assert result.raw_trace_retrieval.metrics.action_brief_card_count == 17
    assert result.raw_trace_retrieval.metrics.action_brief_relevance_recall == 1.0
    assert round(result.raw_trace_retrieval.metrics.action_brief_pollution_rate, 3) == 0.588
    assert result.raw_trace_retrieval.metrics.scoped_memory_suppression == 0.0
    assert result.raw_trace_retrieval.expected_action_delta == 0.0
    assert result.summary_reflection.trusted_false_memory_count == 5
    assert result.summary_reflection.metrics.action_brief_card_count == 12
    assert round(result.summary_reflection.metrics.action_brief_relevance_recall, 3) == 0.667
    assert round(result.summary_reflection.metrics.action_brief_pollution_rate, 3) == 0.583
    assert round(result.summary_reflection.metrics.scoped_memory_suppression, 3) == 0.333
    assert round(result.summary_reflection.expected_action_delta, 3) == -0.033
    assert result.unvalidated_memory.proposed_count == 17
    assert result.unvalidated_memory.metrics.promoted_count == 17
    assert result.unvalidated_memory.metrics.action_brief_card_count == 14
    assert result.unvalidated_memory.metrics.action_brief_relevance_recall == 1.0
    assert result.unvalidated_memory.metrics.action_brief_pollution_rate == 0.5
    assert result.unvalidated_memory.metrics.scoped_memory_suppression == 1.0
    assert result.unvalidated_memory.metrics.evidence_consolidation_count == 0
    assert result.unvalidated_memory.metrics.max_evidence_support_count == 1
    assert result.unvalidated_memory.metrics.false_memory_resistance == 0.0
    assert result.unvalidated_memory.trusted_false_memory_count == 7
    assert round(result.unvalidated_memory.expected_action_delta, 3) == 0.3
    assert result.cem0_validation.metrics.promoted_count == 10
    assert result.cem0_validation.metrics.action_brief_card_count == 6
    assert result.cem0_validation.metrics.action_brief_relevance_recall == 1.0
    assert result.cem0_validation.metrics.action_brief_pollution_rate == 0.0
    assert result.cem0_validation.metrics.scoped_memory_suppression == 1.0
    assert result.cem0_validation.metrics.evidence_consolidation_count == 1
    assert result.cem0_validation.metrics.max_evidence_support_count == 2
    assert result.cem0_validation.trusted_false_memory_count == 0
    assert result.cem0_validation.expected_action_delta == 1.0
    assert result.cem0_validation.decision_reason_codes["database=mysql"] == ["contradiction"]
    assert result.cem0_validation.decision_reason_codes["report_format=csv"] == []
    assert result.cem0_validation.decision_reason_codes["report_format=json"] == []
    assert result.cem0_validation.decision_reason_codes["manual smoke tests before launch"] == []
    assert "assistant_hypothesis" in result.cem0_validation.decision_reason_codes[
        "user always wants us to skip tests"
    ]
    assert "unsupported" in result.cem0_validation.decision_reason_codes["production deploy already finished"]
    assert result.cem0_validation.decision_reason_codes["skip pytest before claiming kernel changes are done"] == [
        "untrusted_source"
    ]
    assert result.cem0_validation.decision_reason_codes[
        "click refresh before submitting workflow-gotchas form"
    ] == ["non_causal"]
    assert result.cem0_validation.metrics.stale_memory_suppression == 1.0
    assert result.cem0_validation.metrics.false_memory_resistance_by_risk == {
        "assistant_hypothesis": 1.0,
        "contradiction": 1.0,
        "misleading_success": 1.0,
        "poisoned_instruction": 1.0,
        "stale_preference": 1.0,
        "unsupported": 1.0,
    }
    assert result.cem0_validation.metrics.valid_memory_retention_by_risk == {
        "valid_failure_mode": 1.0,
        "valid_instruction": 1.0,
        "valid_preference": 1.0,
        "valid_skill": 1.0,
    }
    assert "set assignment_group before assignee" in result.cem0_validation.action_brief_recommended_actions
    assert (
        "avoid submitting workflow-gotchas form unless approval_code is present"
        in result.cem0_validation.action_brief_recommended_actions
    )
    assert "editor_theme=dark" in result.cem0_validation.action_brief_recommended_actions
    assert "editor_theme=light" not in result.cem0_validation.action_brief_recommended_actions
    assert (
        "click refresh before submitting workflow-gotchas form"
        not in result.cem0_validation.action_brief_recommended_actions
    )
    assert (
        "skip pytest before claiming kernel changes are done"
        not in result.cem0_validation.action_brief_recommended_actions
    )
    assert "manual smoke tests before launch" not in result.cem0_validation.action_brief_recommended_actions
    assert "editor_theme=light" in result.unvalidated_memory.action_brief_recommended_actions
    assert (
        "click refresh before submitting workflow-gotchas form"
        in result.unvalidated_memory.action_brief_recommended_actions
    )
    assert (
        "skip pytest before claiming kernel changes are done"
        in result.unvalidated_memory.action_brief_recommended_actions
    )
    assert result.unvalidated_memory.metrics.action_brief_card_count > result.action_brief_card_count


def test_synthetic_eval_markdown_report(tmp_path):
    result = run_synthetic_corruption_eval(tmp_path)

    markdown = render_synthetic_eval_markdown(result)

    assert "# synthetic_corruption Report" in markdown
    assert "| no_memory | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |" in markdown
    assert "| raw_trace_retrieval | 0 | 0 | 7 | 17 | 0 | 0 | 1 | 0.588 | 0 | 0 | 0 |" in markdown
    assert "| summary_reflection | 0 | 0 | 5 | 12 | -0.033 | 0 | 0.667 | 0.583 | 0.333 | 0 | 0 |" in markdown
    assert "| unvalidated_memory | 17 | 0 | 7 | 14 | 0.3 | 0 | 1 | 0.5 | 1 | 0 | 1 |" in markdown
    assert "| cem0_validation | 17 | 6 | 0 | 6 | 1 | 1 | 1 | 0 | 1 | 1 | 2 |" in markdown
    assert "## CEM-0 Comparison" in markdown
    assert "| summary_reflection | 1 | 1.033 | 5 | 6 |" in markdown
    assert "| unvalidated_memory | 1 | 0.7 | 7 | 8 |" in markdown
    assert "`database=mysql`: contradiction" in markdown


def test_halumem_facsimile_maps_operation_metrics(tmp_path):
    result = run_halumem_facsimile_eval(tmp_path)

    assert result.suite_name == "halumem_local_facsimile"
    assert result.source_suite_name == "synthetic_corruption"
    assert result.extraction_false_memory_resistance == 1.0
    assert result.update_recall == 1.0
    assert result.memory_qa_action_delta == 1.0
    assert round(result.baseline_action_delta, 3) == 0.3
    assert result.cem0_quarantined_count == 6
    assert result.trusted_false_memory_count == 0


def test_workflow_gotcha_demo_scores_action_briefs(tmp_path):
    result = run_workflow_gotcha_demo(tmp_path)
    attempts = {attempt.run_name: attempt for attempt in result.attempts}

    assert attempts["no_memory"].success is False
    assert attempts["raw_trace_retrieval"].success is False
    assert attempts["summary_reflection"].success is False
    assert attempts["unvalidated_memory"].success is False
    assert attempts["cem0_validation"].success is True
