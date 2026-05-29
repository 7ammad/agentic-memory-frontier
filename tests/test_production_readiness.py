"""Phase 5 hardening: the composite production-readiness gate.

Combines the locked Phase 4 success criteria into ONE go/no-go: mma_passes +
beats_lexical_by_margin + negative_control_suppression_rate==1.0 +
within_latency_budget + the no-fake-green AST guard. `ready` is DERIVED
(all checks pass), never a settable literal. Each criterion has a one-field-flip
canary: if `ready` were hardcoded True, flipping a field would not turn it False,
so these canaries also refute "all(True) by construction".
"""
from __future__ import annotations

import pytest

from cem_eval.phase4_exam import LOCKED_WEIGHTS, Phase4ExamReport, run_phase4_exam
from cem_eval.production_readiness import (
    MONITORED_SOURCE_PATHS,
    ReadinessReport,
    production_readiness_report,
)


def _passing_report(**overrides) -> Phase4ExamReport:
    """A Phase4ExamReport with every readiness criterion at its PASSING value;
    tests flip exactly one field via overrides to prove each criterion bites."""
    fields = dict(
        rungs=[],
        n=12,
        cem_mma=0.833,
        cem_ci_low=0.613,
        cem_ci_high=1.054,
        lexical_mma=0.083,
        measured_lexical_margin_pp=75.0,
        cem_passes_success_bar=True,
        cem_beats_lexical=True,
        negative_control_suppression_rate=1.0,
        cem_verified_card_count=5,
        p95_retrieval_latency_ms=13.0,
        retrieval_latency_budget_ms=50.0,
        within_latency_budget=True,
        scorer_version="action_value_v1",
        locked_weights=dict(LOCKED_WEIGHTS),
        verdict="PASS",
    )
    fields.update(overrides)
    return Phase4ExamReport(**fields)


def _status(report: ReadinessReport, name: str) -> str:
    return next(c.status for c in report.checks if c.name == name)


def test_readiness_passes_on_fully_passing_report():
    result = production_readiness_report(_passing_report())
    assert isinstance(result, ReadinessReport)
    assert result.ready is True
    assert all(c.status == "pass" for c in result.checks)


def test_readiness_mma_check_bites():
    result = production_readiness_report(_passing_report(cem_passes_success_bar=False))
    assert result.ready is False
    assert _status(result, "mma_passes") == "fail"


def test_readiness_beats_lexical_check_bites():
    result = production_readiness_report(_passing_report(cem_beats_lexical=False))
    assert result.ready is False
    assert _status(result, "beats_lexical_by_margin") == "fail"


def test_readiness_suppression_check_bites_at_0_99():
    # Exact-equality (==1.0) on an integer ratio -- no epsilon softening of the
    # 100%-suppression kill criterion.
    result = production_readiness_report(_passing_report(negative_control_suppression_rate=0.99))
    assert result.ready is False
    assert _status(result, "negative_control_suppression") == "fail"


def test_readiness_latency_check_bites():
    result = production_readiness_report(_passing_report(within_latency_budget=False))
    assert result.ready is False
    assert _status(result, "within_latency_budget") == "fail"


def test_readiness_composes_real_exam_report():
    # Integration: drive the gate from a REAL exam run (not hand-built bools), so a
    # genuine regression in any deterministic criterion would flip a real field.
    # Asserts the deterministic checks pass; does NOT hard-assert the timing-coupled
    # latency flag True (worst-of-12 wall-clock would flake on a loaded box).
    import tempfile

    report = run_phase4_exam(tempfile.mkdtemp())
    result = production_readiness_report(report)
    for name in ("mma_passes", "beats_lexical_by_margin", "negative_control_suppression", "no_fake_green_ast_clean"):
        assert _status(result, name) == "pass", name
    # ready is the pure AND of all checks (incl. the latency flag for this run).
    assert result.ready == all(c.status == "pass" for c in result.checks)


def test_readiness_no_fake_green_check_bites(monkeypatch):
    # The no_fake_green criterion must reflect the SHARED scanner's result: when the
    # scanner reports any offender, the gate fails. Monkeypatch the scanner (no need
    # to corrupt the real module) to prove the wiring bites.
    import cem_eval.production_readiness as pr

    monkeypatch.setattr(pr, "literal_bool_check_names_in_files", lambda paths: {"planted_offender"})
    result = production_readiness_report(_passing_report())
    assert result.ready is False
    assert _status(result, "no_fake_green_ast_clean") == "fail"


def test_monitored_source_paths_include_operations_and_self():
    # The no-fake-green criterion must police the gate module itself (closing the
    # self-referential hole), plus the original operations.py target.
    names = {p.name for p in MONITORED_SOURCE_PATHS}
    assert "operations.py" in names
    assert "production_readiness.py" in names
