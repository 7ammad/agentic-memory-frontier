"""Locked CEM-1 evaluation contract (spec sections 7, 9, 10, 11).

This module fixes the proof contract BEFORE any scorer tuning. Phase 4 runs the
exam against this contract; it does not get to move these definitions.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# Pre-registered margin: CEM must beat lexical-overlap retrieval by >= this many
# percentage points of held-out task success (spec section 9), or the
# causal-retrieval thesis is unproven.
LEXICAL_MARGIN_PP: float = 5.0


@dataclass(frozen=True)
class Baseline:
    name: str
    description: str
    is_ceiling: bool = False  # ceiling = upper-bound reference, NOT a must-beat gate


# Spec section 7 — all baselines run honestly on the same held-out tasks.
BASELINE_LADDER: tuple[Baseline, ...] = (
    Baseline("no_memory", "No memory access; the MMA control/denominator."),
    Baseline("full_context", "All allowed prior trace material within the budget; no selectivity."),
    Baseline("lexical_overlap", "Current word-overlap retrieval; CEM must beat it by LEXICAL_MARGIN_PP."),
    Baseline("summary", "Rolling summary of prior traces injected as context."),
    Baseline("vector_rag", "Embedding-similarity retrieval over the trace/card corpus."),
    Baseline("time_aware_rag", "Vector RAG with recency weighting / temporal filtering."),
    Baseline("temporal_graph", "Graph retrieval over entity/event/time links; no causal scorer."),
    Baseline("unverified_reflection", "Self-generated lessons with no verification gate."),
    Baseline("cem", "The full CEM kernel."),
    Baseline("human_runbook", "Hand-written ideal playbook.", is_ceiling=True),
)


@dataclass(frozen=True)
class MMAResult:
    mma: float
    n: int
    ci_low: float
    ci_high: float


def marginal_memory_advantage(
    memory_success: list[float],
    no_memory_success: list[float],
    *,
    z: float = 1.96,
) -> MMAResult:
    """Paired task-level MMA with a 95% CI (spec section 11 forbids a bare mean)."""
    if len(memory_success) != len(no_memory_success):
        raise ValueError("MMA requires paired per-task results of equal length.")
    if not memory_success:
        raise ValueError("MMA requires at least one task.")
    deltas = [m - b for m, b in zip(memory_success, no_memory_success)]
    n = len(deltas)
    mma = sum(deltas) / n
    if n == 1:
        return MMAResult(mma=mma, n=n, ci_low=mma, ci_high=mma)
    var = sum((d - mma) ** 2 for d in deltas) / (n - 1)
    se = math.sqrt(var / n)
    return MMAResult(mma=mma, n=n, ci_low=mma - z * se, ci_high=mma + z * se)


def mma_passes(result: MMAResult) -> bool:
    """Success bar (spec section 9): MMA > 0 AND lower 95% CI > 0."""
    return result.mma > 0.0 and result.ci_low > 0.0


def assert_no_leakage(*, memory_source_ids: set[str], held_out_answer_ids: set[str]) -> None:
    """Spec section 10: memory-source traces and held-out answers must be disjoint."""
    overlap = memory_source_ids & held_out_answer_ids
    if overlap:
        raise ValueError(f"Leakage: memory source overlaps held-out answers: {sorted(overlap)}")


def lexical_margin_pp(cem_result: MMAResult, lexical_result: MMAResult) -> float:
    """The measured CEM-over-lexical advantage in percentage points of task success.

    Reported even on a miss so a near-miss (e.g. 4.9pp) is visible, never hidden.
    """
    return (cem_result.mma - lexical_result.mma) * 100.0


def beats_lexical_by_margin(
    cem_result: MMAResult,
    lexical_result: MMAResult,
    *,
    margin_pp: float = LEXICAL_MARGIN_PP,
) -> bool:
    """Spec section 9 kill criterion: CEM must beat the lexical-overlap baseline by
    >= ``margin_pp`` percentage points of held-out task success, else the
    causal-retrieval (read-path) thesis is unproven.

    The measured margin is rounded to 6 decimal places before the comparison so an
    exact-boundary margin (e.g. 0.45 - 0.40 == 0.0499...9 in float) is not defeated
    by floating-point noise; 1e-6 pp is far finer than any real n-task measurement.
    """
    return round(lexical_margin_pp(cem_result, lexical_result), 6) >= margin_pp
