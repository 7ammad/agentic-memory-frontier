import pytest

from cem_eval.eval_protocol import (
    BASELINE_LADDER,
    LEXICAL_MARGIN_PP,
    MMAResult,
    assert_no_leakage,
    beats_lexical_by_margin,
    lexical_margin_pp,
    marginal_memory_advantage,
    mma_passes,
)


def test_mma_is_paired_delta_with_ci_and_n():
    memory = [1.0, 1.0, 0.0, 1.0]
    no_memory = [0.0, 1.0, 0.0, 0.0]
    result = marginal_memory_advantage(memory, no_memory)
    assert isinstance(result, MMAResult)
    assert result.n == 4
    assert result.mma == pytest.approx(0.5)
    assert result.ci_low <= result.mma <= result.ci_high


def test_mma_rejects_unpaired_inputs():
    with pytest.raises(ValueError):
        marginal_memory_advantage([1.0, 0.0], [1.0])


def test_baseline_ladder_has_all_ten_and_human_runbook_is_ceiling():
    names = {b.name for b in BASELINE_LADDER}
    assert names == {
        "no_memory",
        "full_context",
        "lexical_overlap",
        "summary",
        "vector_rag",
        "time_aware_rag",
        "temporal_graph",
        "unverified_reflection",
        "cem",
        "human_runbook",
    }
    ceiling = {b.name for b in BASELINE_LADDER if b.is_ceiling}
    must_beat_lexical = {b.name for b in BASELINE_LADDER if b.name == "lexical_overlap"}
    assert ceiling == {"human_runbook"}
    assert LEXICAL_MARGIN_PP == 5.0
    assert must_beat_lexical == {"lexical_overlap"}


def test_leakage_guard_fails_on_overlap():
    # Failure canary: overlapping memory-source and held-out answer ids must raise.
    with pytest.raises(ValueError):
        assert_no_leakage(memory_source_ids={"a", "b"}, held_out_answer_ids={"b", "c"})
    # disjoint sets pass
    assert assert_no_leakage(memory_source_ids={"a"}, held_out_answer_ids={"c"}) is None


def test_mma_passes_requires_positive_lower_ci():
    # Failure canary for the success-bar gate (spec section 9): a positive mean
    # whose 95% CI straddles zero must NOT pass.
    clean = MMAResult(mma=0.3, n=10, ci_low=0.1, ci_high=0.5)
    straddles_zero = MMAResult(mma=0.3, n=10, ci_low=-0.05, ci_high=0.65)
    assert mma_passes(clean) is True
    assert mma_passes(straddles_zero) is False


def test_beats_lexical_by_margin_boundary():
    # The >=5pp gate (spec section 9): CEM must beat the lexical-overlap baseline by
    # at least LEXICAL_MARGIN_PP percentage points of held-out task success. Lock the
    # >= comparison and the *100 pp unit conversion at the exact boundary.
    lexical = MMAResult(mma=0.40, n=20, ci_low=0.30, ci_high=0.50)

    def cem_at(delta_pp: float) -> MMAResult:
        mma = lexical.mma + delta_pp / 100.0
        return MMAResult(mma=mma, n=20, ci_low=mma - 0.1, ci_high=mma + 0.1)

    assert beats_lexical_by_margin(cem_at(0.0), lexical) is False  # 0pp
    assert beats_lexical_by_margin(cem_at(4.9), lexical) is False  # below the bar
    assert beats_lexical_by_margin(cem_at(5.0), lexical) is True  # exact boundary passes
    assert beats_lexical_by_margin(cem_at(5.1), lexical) is True
    # the companion reporter returns the measured gap in pp (so a near-miss is visible)
    assert lexical_margin_pp(cem_at(4.9), lexical) == pytest.approx(4.9)
    assert lexical_margin_pp(cem_at(0.0), lexical) == pytest.approx(0.0)
