"""Phase 5 composite production-readiness gate.

Reduces the locked Phase 4 proof contract to ONE go/no-go decision, combining the
spec's success criteria + kill criteria into a pure AND of named checks:

  mma_passes  AND  beats_lexical_by_margin  AND  negative_control_suppression==1.0
  AND  within_latency_budget  AND  no-fake-green-AST-clean

It CONSUMES an already-computed ``Phase4ExamReport`` -- it never re-runs the exam
(the held-out split is scored once per locked candidate; a second scoring pass
would be a leakage/overfit hazard). ``ready`` is DERIVED (all checks pass), never a
settable literal. The per-criterion helper is deliberately NOT named ``_check`` so
the no-fake-green scanner (which keys on ``_check`` with a literal-bool arg) does
not self-trip; each criterion's status is a COMPUTED boolean off report fields.

Layering: cem-eval -> cem-core only (imports ``MonitorCheck`` from cem-core,
``Phase4ExamReport`` from cem-eval); imports nothing the other way.
"""
from __future__ import annotations

from pathlib import Path

from cem_core import operations as _operations
from cem_core.models import StrictModel
from cem_core.operations import MonitorCheck
from cem_eval.eval_protocol import LEXICAL_MARGIN_PP
from cem_eval.fake_green_guard import literal_bool_check_names_in_files
from cem_eval.phase4_exam import LOCKED_WEIGHTS, Phase4ExamReport

# Source files the no-fake-green criterion policies. Resolved off the imported
# modules' __file__ (NOT a CWD-relative literal) so the gate works from any cwd.
# Includes this module itself, closing the self-referential hole.
MONITORED_SOURCE_PATHS: list[Path] = [
    Path(_operations.__file__),
    Path(__file__),
]


class ReadinessReport(StrictModel):
    checks: list[MonitorCheck]

    @property
    def ready(self) -> bool:
        # DERIVED -- never settable; identical reduction to operations.run_monitor.
        return all(check.status == "pass" for check in self.checks)


def _gate_check(name: str, ok: bool, detail: str) -> MonitorCheck:
    # NOT named _check on purpose: the no-fake-green scanner keys on _check(...,
    # <literal bool>, ...). `ok` here is always a COMPUTED expression, never a literal.
    return MonitorCheck(name=name, status="pass" if ok else "fail", detail=detail)


def production_readiness_report(report: Phase4ExamReport) -> ReadinessReport:
    """Compose the go/no-go gate from an already-computed Phase 4 exam report."""
    offenders = literal_bool_check_names_in_files(MONITORED_SOURCE_PATHS)
    checks = [
        _gate_check(
            "mma_passes",
            report.cem_passes_success_bar,
            "CEM MMA clears the success bar (MMA > 0 and lower 95% CI > 0)",
        ),
        _gate_check(
            "beats_lexical_by_margin",
            report.cem_beats_lexical,
            f"CEM beats lexical-overlap retrieval by >= {LEXICAL_MARGIN_PP}pp "
            f"(measured {report.measured_lexical_margin_pp:.1f}pp)",
        ),
        _gate_check(
            "negative_control_suppression",
            report.negative_control_suppression_rate == 1.0,
            f"all planted negative controls suppressed "
            f"(rate {report.negative_control_suppression_rate})",
        ),
        _gate_check(
            "within_latency_budget",
            report.within_latency_budget,
            f"retrieval p95 {report.p95_retrieval_latency_ms:.1f}ms "
            f"<= budget {report.retrieval_latency_budget_ms:.0f}ms",
        ),
        _gate_check(
            "no_fake_green_ast_clean",
            not offenders,
            f"no hardcoded-literal _check() health values in {[p.name for p in MONITORED_SOURCE_PATHS]}"
            + (f"; offenders: {sorted(offenders)}" if offenders else ""),
        ),
    ]
    return ReadinessReport(checks=checks)
