from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, Field

from .halumem_runner import HaluMemCEM0EvalResult
from .longmemeval_v2_runner import LongMemEvalV2CEM0EvalResult
from .memoryarena_runner import MemoryArenaCEM0EvalResult
from .synthetic_corruption import SyntheticEvalResult

TReportResult = TypeVar("TReportResult", bound=BaseModel)


class ExternalBenchmarkReportRow(BaseModel):
    suite_name: str
    source_path: str
    item_count_label: str
    item_count: int
    proposed_count: int
    trusted_count: int
    quarantined_count: int
    output_count: int
    primary_metric_name: str
    primary_metric_value: float
    secondary_metrics: dict[str, float] = Field(default_factory=dict)
    decision_reason_counts: dict[str, int] = Field(default_factory=dict)


class ExternalBenchmarkReport(BaseModel):
    suite_name: str = "cem0_external_benchmarks"
    suite_count: int
    total_proposed_count: int
    total_trusted_count: int
    total_quarantined_count: int
    rows: list[ExternalBenchmarkReportRow]


def build_external_benchmark_report(
    *,
    halumem: HaluMemCEM0EvalResult | None = None,
    memoryarena: MemoryArenaCEM0EvalResult | None = None,
    longmemeval_v2: LongMemEvalV2CEM0EvalResult | None = None,
) -> ExternalBenchmarkReport:
    rows: list[ExternalBenchmarkReportRow] = []
    if halumem is not None:
        rows.append(_halumem_report_row(halumem))
    if memoryarena is not None:
        rows.append(_memoryarena_report_row(memoryarena))
    if longmemeval_v2 is not None:
        rows.append(_longmemeval_v2_report_row(longmemeval_v2))
    return ExternalBenchmarkReport(
        suite_count=len(rows),
        total_proposed_count=sum(row.proposed_count for row in rows),
        total_trusted_count=sum(row.trusted_count for row in rows),
        total_quarantined_count=sum(row.quarantined_count for row in rows),
        rows=rows,
    )


def build_external_benchmark_report_from_json_files(
    *,
    halumem_result_path: str | Path | None = None,
    memoryarena_result_path: str | Path | None = None,
    longmemeval_v2_result_path: str | Path | None = None,
) -> ExternalBenchmarkReport:
    return build_external_benchmark_report(
        halumem=(
            _load_runner_result(halumem_result_path, HaluMemCEM0EvalResult)
            if halumem_result_path is not None
            else None
        ),
        memoryarena=(
            _load_runner_result(memoryarena_result_path, MemoryArenaCEM0EvalResult)
            if memoryarena_result_path is not None
            else None
        ),
        longmemeval_v2=(
            _load_runner_result(longmemeval_v2_result_path, LongMemEvalV2CEM0EvalResult)
            if longmemeval_v2_result_path is not None
            else None
        ),
    )


def render_external_benchmark_report_markdown(report: ExternalBenchmarkReport) -> str:
    lines = [
        f"# {report.suite_name} Report",
        "",
        "| Suite | Items | Proposed | Trusted | Quarantined | Outputs | Primary metric | Value | Decision reasons |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |",
    ]
    for row in report.rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.suite_name,
                    f"{row.item_count} {row.item_count_label}",
                    str(row.proposed_count),
                    str(row.trusted_count),
                    str(row.quarantined_count),
                    str(row.output_count),
                    row.primary_metric_name,
                    _format_float(row.primary_metric_value),
                    _format_reason_counts(row.decision_reason_counts),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Secondary Metrics", ""])
    for row in report.rows:
        lines.append(f"### {row.suite_name}")
        if row.secondary_metrics:
            for name, value in row.secondary_metrics.items():
                lines.append(f"- `{name}`: {_format_float(value)}")
        else:
            lines.append("- none")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


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
            "## Extraction Quality",
            "",
            "| Run | Precision | Recall | F1 |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for row in [*report.baseline_rows, report.cem0_row]:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.name,
                    _format_float(row.extraction_precision),
                    _format_float(row.extraction_recall),
                    _format_float(row.extraction_f1),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Contradiction Detection",
            "",
            "| Run | Precision | Recall |",
            "| --- | ---: | ---: |",
        ]
    )
    for row in [*report.baseline_rows, report.cem0_row]:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.name,
                    _format_float(row.contradiction_precision),
                    _format_float(row.contradiction_recall),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Memory Harm",
            "",
            "| Run | Harm rate |",
            "| --- | ---: |",
        ]
    )
    for row in [*report.baseline_rows, report.cem0_row]:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.name,
                    _format_float(row.memory_harm_rate),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Action Influence",
            "",
            "| Run | Influence rate |",
            "| --- | ---: |",
        ]
    )
    for row in [*report.baseline_rows, report.cem0_row]:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.name,
                    _format_float(row.action_influence_rate),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Latency",
            "",
            "| Run | p95 write ms | p95 retrieval ms |",
            "| --- | ---: | ---: |",
        ]
    )
    for row in [*report.baseline_rows, report.cem0_row]:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.name,
                    _format_float(row.p95_write_latency_ms),
                    _format_float(row.p95_retrieval_latency_ms),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Token Accounting",
            "",
            "| Run | Tokens per write | Tokens per retrieval |",
            "| --- | ---: | ---: |",
        ]
    )
    for row in [*report.baseline_rows, report.cem0_row]:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.name,
                    _format_float(row.tokens_per_write),
                    _format_float(row.tokens_per_retrieval),
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


def _halumem_report_row(result: HaluMemCEM0EvalResult) -> ExternalBenchmarkReportRow:
    return ExternalBenchmarkReportRow(
        suite_name=result.suite_name,
        source_path=result.source_path,
        item_count_label="sessions",
        item_count=result.session_count,
        proposed_count=result.proposed_count,
        trusted_count=result.trusted_count,
        quarantined_count=result.quarantined_count,
        output_count=result.trusted_score.candidate_memory_count,
        primary_metric_name="trusted_extraction_f1",
        primary_metric_value=result.trusted_score.extraction_f1,
        secondary_metrics={
            "proposed_extraction_precision": result.proposed_score.extraction_precision,
            "proposed_extraction_recall": result.proposed_score.extraction_recall,
            "proposed_extraction_f1": result.proposed_score.extraction_f1,
            "trusted_extraction_precision": result.trusted_score.extraction_precision,
            "trusted_extraction_recall": result.trusted_score.extraction_recall,
            "trusted_update_recall": result.trusted_score.update_recall,
            "trusted_qa_evidence_recall": result.trusted_score.qa_evidence_recall,
            "trusted_hallucinated_memory_count": float(result.trusted_score.hallucinated_memory_count),
            "trusted_omitted_memory_count": float(result.trusted_score.omitted_memory_count),
        },
        decision_reason_counts=_reason_counts(result.decision_reason_codes),
    )


def _memoryarena_report_row(result: MemoryArenaCEM0EvalResult) -> ExternalBenchmarkReportRow:
    return ExternalBenchmarkReportRow(
        suite_name=result.suite_name,
        source_path=result.source_path,
        item_count_label="tasks",
        item_count=result.task_count,
        proposed_count=result.proposed_count,
        trusted_count=result.trusted_count,
        quarantined_count=result.quarantined_count,
        output_count=result.action_brief_prediction_count,
        primary_metric_name="progress_score",
        primary_metric_value=result.score.progress_score,
        secondary_metrics={
            "task_success_rate": result.score.task_success_rate,
            "correct_subtask_count": float(result.score.correct_subtask_count),
            "subtask_count": float(result.score.subtask_count),
            "fully_solved_task_count": float(result.score.fully_solved_task_count),
        },
        decision_reason_counts=_reason_counts(result.decision_reason_codes),
    )


def _longmemeval_v2_report_row(result: LongMemEvalV2CEM0EvalResult) -> ExternalBenchmarkReportRow:
    return ExternalBenchmarkReportRow(
        suite_name=result.suite_name,
        source_path=result.source_path,
        item_count_label="questions",
        item_count=result.question_count,
        proposed_count=result.proposed_count,
        trusted_count=result.trusted_count,
        quarantined_count=result.quarantined_count,
        output_count=result.action_brief_answer_count,
        primary_metric_name="exact_match_accuracy",
        primary_metric_value=result.answer_score.exact_match_accuracy,
        secondary_metrics={
            "answered_count": float(result.answer_score.answered_count),
            "exact_match_count": float(result.answer_score.exact_match_count),
            "haystack_member_precision": result.retrieval_score.haystack_member_precision,
            "question_coverage_rate": result.retrieval_score.question_coverage_rate,
            "in_haystack_retrieved_count": float(result.retrieval_score.in_haystack_retrieved_count),
            "out_of_haystack_retrieved_count": float(result.retrieval_score.out_of_haystack_retrieved_count),
        },
        decision_reason_counts=_reason_counts(result.decision_reason_codes),
    )


def _load_runner_result(path: str | Path, model: type[TReportResult]) -> TReportResult:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    payload = raw.get("result", raw) if isinstance(raw, dict) else raw
    return model.model_validate(payload)


def _reason_counts(decision_reason_codes: dict[str, list[str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for reason_codes in decision_reason_codes.values():
        for code in reason_codes:
            counts[code] = counts.get(code, 0) + 1
    return dict(sorted(counts.items()))


def _format_reason_counts(reason_counts: dict[str, int]) -> str:
    if not reason_counts:
        return "none"
    return ", ".join(f"{name}={count}" for name, count in reason_counts.items())
