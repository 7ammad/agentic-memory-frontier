import pytest
from cem_eval.vertical_loop import run_vertical_loop


def test_vertical_loop_runs_end_to_end_on_real_objects(tmp_path):
    report = run_vertical_loop(tmp_path)
    assert report.n >= 1
    assert report.trace_count >= 1
    assert report.atom_count >= 1
    assert report.card_count >= 1
    assert report.brief_record_count == report.n
    assert report.influence_event_count == report.n
    assert report.mma is not None
    assert report.ci_low <= report.mma <= report.ci_high
    assert report.scorer_version == "lexical_overlap_v0"


def test_vertical_loop_leakage_guard_bites(tmp_path):
    # Failure canary: if a held-out answer id leaks into the memory source,
    # the runner's leakage guard must raise (not silently score).
    with pytest.raises(ValueError):
        run_vertical_loop(tmp_path, inject_leakage=True)
