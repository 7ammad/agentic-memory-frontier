"""Phase 4 exam canaries: the MMA + 10-baseline ladder on held-out tasks."""
import pytest

from cem_core import kernel
from cem_eval import phase4_exam
from cem_eval.eval_protocol import MMAResult, beats_lexical_by_margin
from cem_eval.phase4_dataset import (
    PHASE4_HELD_OUT,
    PYTEST_TRAP,
    phase4_memory_source_traces,
)
from cem_eval.phase4_exam import LOCKED_WEIGHTS, run_phase4_exam


@pytest.fixture(scope="module")
def report(tmp_path_factory):
    return run_phase4_exam(tmp_path_factory.mktemp("phase4"))


def test_exam_passes_with_honest_margin(report):
    # Headline: CEM clears the success bar AND beats lexical by >= 5pp, and it
    # dominates every HONEST baseline (the human_runbook ceiling is excluded).
    assert report.verdict == "PASS"
    assert report.cem_passes_success_bar is True
    assert report.cem_beats_lexical is True
    assert report.measured_lexical_margin_pp >= 5.0
    honest = [r.mma for r in report.rungs if not r.is_ceiling and r.name != "cem"]
    assert report.cem_mma > max(honest)


def test_all_ten_rungs_present_and_ceiling_excluded(report):
    from cem_eval.eval_protocol import BASELINE_LADDER

    assert {r.name for r in report.rungs} == {b.name for b in BASELINE_LADDER}
    assert all(r.n == len(PHASE4_HELD_OUT) for r in report.rungs)  # nothing dropped/sampled
    ceilings = [r.name for r in report.rungs if r.is_ceiling]
    assert ceilings == ["human_runbook"]
    # the ceiling outscores CEM yet the verdict is still PASS -> never a gate.
    human = next(r for r in report.rungs if r.name == "human_runbook")
    assert human.mma >= report.cem_mma
    assert report.verdict == "PASS"


def test_no_memory_denominator_is_real_zero(report):
    # The MMA control is a real empty-recommend, not a hardcoded literal.
    no_memory = next(r for r in report.rungs if r.name == "no_memory")
    assert no_memory.mma == 0.0
    assert no_memory.per_task_success == [0.0] * len(PHASE4_HELD_OUT)


def test_negative_control_suppression_is_total(report):
    # A planted negative control reaching verified would trip the section 9
    # false-memories-pass kill criterion.
    assert report.negative_control_suppression_rate == 1.0


def test_weights_pinned_to_ledger_018(report):
    # Detect silent weight drift before the single-shot held-out run.
    assert kernel.W_PRE == 1.0
    assert kernel.W_LEX == 1.0
    assert kernel.W_LIFT == 4.0
    assert kernel.W_REC == 1.0
    assert kernel.W_CON == 2.0
    assert kernel.W_STALE == 1.5
    assert kernel.HALF_LIFE_DAYS == 30.0
    assert kernel.STALE_WINDOW_DAYS == 14.0
    assert kernel.CONTRA_SATURATION == 2.0
    assert report.locked_weights == LOCKED_WEIGHTS
    assert LOCKED_WEIGHTS == {
        "W_PRE": kernel.W_PRE,
        "W_LEX": kernel.W_LEX,
        "W_LIFT": kernel.W_LIFT,
        "W_REC": kernel.W_REC,
        "W_CON": kernel.W_CON,
        "W_STALE": kernel.W_STALE,
        "HALF_LIFE_DAYS": kernel.HALF_LIFE_DAYS,
        "STALE_WINDOW_DAYS": kernel.STALE_WINDOW_DAYS,
        "CONTRA_SATURATION": kernel.CONTRA_SATURATION,
    }


def test_cem_rung_earns_verified_lift(report):
    # Regression guard: the CEM rung must actually earn verified lift (W_LIFT=4.0
    # active), not pass on trap-suppression alone. If _decisive_for_card_title
    # drift silenced the probes, this drops to 0 and fails.
    assert report.cem_verified_card_count >= 1


def test_lexical_rung_surfaces_trap_cem_suppresses(report):
    # Isolation + validation value: on a pytest task the lexical_overlap rung
    # surfaces the poisoned 'skip pytest' trap (no validation), while CEM does not.
    idx = next(i for i, t in enumerate(PHASE4_HELD_OUT) if t.task_id == "pytest-before-done")
    pytest_task = PHASE4_HELD_OUT[idx]
    atoms = [
        atom
        for trace in phase4_memory_source_traces()
        for atom in phase4_exam.SyntheticCorruptionExtractor().extract(trace)
    ]
    lexical = phase4_exam._lexical_overlap_recommend(atoms, pytest_task)
    assert PYTEST_TRAP in lexical  # word-overlap retrieval is fooled by the trap

    # CEM-suppression side: at the same task the lexical rung FAILS (trap present)
    # while the CEM rung SUCCEEDS (success requires the trap absent AND the decisive
    # action present) -- the trap is genuinely suppressed by CEM, not surfaced.
    lexical_rung = next(r for r in report.rungs if r.name == "lexical_overlap")
    cem_rung = next(r for r in report.rungs if r.name == "cem")
    assert lexical_rung.per_task_success[idx] == 0.0
    assert cem_rung.per_task_success[idx] == 1.0


def test_dataset_no_verbatim_task_statement_in_source():
    # Leakage lint: a held-out task STATEMENT must never appear verbatim in the
    # memory source (no memorized task->answer pairs). The id-namespace gate is
    # necessary but not sufficient.
    source_text = "\n".join(
        turn.content for trace in phase4_memory_source_traces() for turn in trace.turns
    ).lower()
    for task in PHASE4_HELD_OUT:
        assert task.task.description.lower() not in source_text


def test_margin_gate_bites_when_cem_equals_lexical():
    # A no-op scorer (causal == similarity) must NOT pass: equal MMA -> gate False.
    equal = MMAResult(mma=0.5, n=12, ci_low=0.3, ci_high=0.7)
    assert beats_lexical_by_margin(equal, equal) is False


def test_leakage_gate_aborts_before_any_rung(tmp_path, monkeypatch):
    # Force an overlapping id between the memory source and the held-out answers:
    # run_phase4_exam must raise from assert_no_leakage BEFORE building any rung
    # (fail-closed). Both id sets are monkeypatched because the fixture mints fresh
    # uuids per call (the real guard is namespace-disjoint by construction).
    monkeypatch.setattr(phase4_exam, "memory_source_ids", lambda: {"dup-id"})
    monkeypatch.setattr(phase4_exam, "held_out_answer_ids", lambda: {"dup-id"})
    with pytest.raises(ValueError):
        run_phase4_exam(tmp_path)
