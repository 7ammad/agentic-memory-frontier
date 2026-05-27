from __future__ import annotations

from .synthetic_corruption import SyntheticEvalResult


def render_synthetic_eval_markdown(result: SyntheticEvalResult) -> str:
    report = result.report
    lines = [
        f"# {report.suite_name} Report",
        "",
        f"Generated at: {report.generated_at.isoformat()}",
        "",
        "| Run | Proposed | Quarantined | Trusted false memories | Action brief cards | Expected action delta | False memory resistance | Relevance recall | Pollution rate | Scoped suppression | Expired suppression | Evidence consolidation | Max support | Audit completeness |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in [*report.baseline_rows, report.cem0_row]:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.name,
                    str(row.proposed_count),
                    str(row.quarantined_count),
                    str(row.trusted_false_memory_count),
                    str(row.action_brief_card_count),
                    _format_float(row.expected_action_delta),
                    _format_float(row.false_memory_resistance),
                    _format_float(row.action_brief_relevance_recall),
                    _format_float(row.action_brief_pollution_rate),
                    _format_float(row.scoped_memory_suppression),
                    _format_float(row.expired_memory_suppression),
                    str(row.evidence_consolidation_count),
                    str(row.max_evidence_support_count),
                    _format_float(row.audit_completeness_rate),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## CEM-0 Comparison",
            "",
            "| Baseline | False memory resistance delta | Expected action delta delta | Workflow success delta | Trusted false memory reduction | Action brief card reduction |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in report.comparison_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.baseline_name,
                    _format_float(row.false_memory_resistance_delta),
                    _format_float(row.expected_action_delta_delta),
                    _format_float(row.workflow_success_delta),
                    str(row.trusted_false_memory_reduction),
                    str(row.action_brief_card_reduction),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Audit Coverage",
            "",
            "| Run | Audit completeness | Evidence consolidation | Max support |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for row in [*report.baseline_rows, report.cem0_row]:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.name,
                    _format_float(row.audit_completeness_rate),
                    str(row.evidence_consolidation_count),
                    str(row.max_evidence_support_count),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Held-Out Workflow",
            "",
            "| Run | Success | Failure reasons |",
            "| --- | ---: | --- |",
        ]
    )
    for row in report.workflow_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.name,
                    "yes" if row.success else "no",
                    "; ".join(row.failure_reasons) if row.failure_reasons else "none",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## CEM-0 Decision Codes",
            "",
        ]
    )
    for content, reason_codes in result.cem0_validation.decision_reason_codes.items():
        if reason_codes:
            lines.append(f"- `{content}`: {', '.join(reason_codes)}")
    return "\n".join(lines) + "\n"


def _format_float(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")
