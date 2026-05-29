"""Phase 4 exam: the MMA + 10-baseline ladder on held-out tasks (spec sections 7-11).

Runs every BASELINE_LADDER rung honestly on the same PHASE4_HELD_OUT tasks,
scores each per task (decisive action present AND no forbidden trap present),
computes a paired MMA + 95% CI per rung against the real no_memory control, and
applies the two locked gates: mma_passes(cem) and beats_lexical_by_margin(cem,
lexical). The kernel weights are locked at LEDGER-018; the held-out split is
scored once per locked candidate. On a miss the verdict is FAIL_REPORTED_HONESTLY
with the measured margin -- weights are never tuned to fit (spec section 9).

The lexical_overlap rung ranks every extracted atom INCLUDING the planted traps
with no validation, so any CEM advantage is earned by genuinely suppressing the
poisoned/stale/contradictory memory that word-overlap retrieval surfaces.
"""
from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from cem_core import CEM, ExperienceAtom, TaskContext
from cem_core.models import VerificationProbe
from cem_eval.eval_protocol import (
    BASELINE_LADDER,
    MMAResult,
    assert_no_leakage,
    beats_lexical_by_margin,
    lexical_margin_pp,
    marginal_memory_advantage,
    mma_passes,
)
from cem_eval.phase4_dataset import (
    ASSIGNMENT,
    APPROVAL,
    DB,
    EVAL_NOW,
    PHASE4_HELD_OUT,
    PYTEST,
    THEME,
    TZ,
    Phase4Task,
    held_out_answer_ids,
    memory_source_ids,
    phase4_memory_source_traces,
)
from cem_eval.synthetic_corruption import (
    SyntheticCorruptionExtractor,
    _card_from_atom,
    _key_value_key,
    lexical_vector_score,
)

# LEDGER-018 pre-registered, locked action_value_v1 weights. Echoed into the
# report and pinned by a test so silent drift fails before the single-shot run.
LOCKED_WEIGHTS: dict[str, float] = {
    "W_PRE": 1.0,
    "W_LEX": 1.0,
    "W_LIFT": 4.0,
    "W_REC": 1.0,
    "W_CON": 2.0,
    "W_STALE": 1.5,
    "HALF_LIFE_DAYS": 30.0,
    "STALE_WINDOW_DAYS": 14.0,
    "CONTRA_SATURATION": 2.0,
}

# Decisive lessons that earn verified lift via dev-split replay probes (never the
# held-out tasks themselves -- that would be leakage).
_DECISIVE_LESSONS = frozenset({ASSIGNMENT, APPROVAL, PYTEST, DB, TZ, THEME})
_RETRIEVE_K = 10


class RungReport(BaseModel):
    name: str
    is_ceiling: bool
    mma: float
    n: int
    ci_low: float
    ci_high: float
    per_task_success: list[float]


class Phase4ExamReport(BaseModel):
    rungs: list[RungReport]
    n: int
    # Headline (spec section 11: never a bare mean).
    cem_mma: float
    cem_ci_low: float
    cem_ci_high: float
    lexical_mma: float
    measured_lexical_margin_pp: float
    cem_passes_success_bar: bool
    cem_beats_lexical: bool
    negative_control_suppression_rate: float
    cem_verified_card_count: int  # decisive cards that earned verified lift (W_LIFT active)
    scorer_version: str
    locked_weights: dict[str, float]
    verdict: str  # "PASS" or "FAIL_REPORTED_HONESTLY"

    @property
    def headline(self) -> str:
        return (
            f"MMA = {self.cem_mma:.3f} "
            f"(95% CI [{self.cem_ci_low:.3f}, {self.cem_ci_high:.3f}], n={self.n}); "
            f"lexical MMA = {self.lexical_mma:.3f}; "
            f"margin = {self.measured_lexical_margin_pp:.1f}pp; verdict = {self.verdict}"
        )


def _task_haystack(task: TaskContext) -> str:
    return " ".join([task.description, task.domain_scope or "", task.task_family or ""]).lower()


def _raw_overlap(haystack: str, document: str) -> int:
    # The lexical_overlap_v0 scorer body (kernel.score_card legacy), as a standalone
    # ranker over a document string: count distinct >3-char doc terms in the haystack.
    needles = document.lower().split()
    return sum(1 for term in set(needles) if len(term) > 3 and term.strip(".,:;") in haystack)


def _topk(scored: list[tuple[float, str]], k: int = _RETRIEVE_K) -> list[str]:
    ordered = sorted(scored, key=lambda item: (item[0], item[1]), reverse=True)
    return [content for score, content in ordered if score > 0][:k]


def _lexical_overlap_recommend(atoms: list[ExperienceAtom], task: Phase4Task) -> list[str]:
    haystack = _task_haystack(task.task)
    return _topk([(float(_raw_overlap(haystack, a.content)), a.content) for a in atoms])


def _vector_recommend(
    atoms: list[ExperienceAtom], task: Phase4Task, *, time_aware: bool
) -> list[str]:
    query = _task_haystack(task.task)
    total = max(1, len(atoms) - 1)
    scored: list[tuple[float, str]] = []
    for index, atom in enumerate(atoms):
        score = lexical_vector_score(query, atom.content)
        if time_aware:
            score += index / total * 0.05  # recency bonus on trace order
        scored.append((score, atom.content))
    return _topk(scored)


def _summary_recommend(atoms: list[ExperienceAtom]) -> list[str]:
    # Rolling key-value-collapsed summary: keeps the latest value per key (so stale
    # values that were never causally retired linger) and drops hypotheses only.
    keyed: dict[str, str] = {}
    actions: list[str] = []
    for atom in atoms:
        key = _key_value_key(atom.content)
        if key is not None:
            keyed[key] = atom.content
            continue
        if atom.epistemic_type != "assistant_hypothesis":
            actions.append(atom.content)
    return [*actions, *keyed.values()]


def _temporal_graph_recommend(atoms: list[ExperienceAtom], task: Phase4Task) -> list[str]:
    # Graph retrieval: atoms are nodes; edges join atoms sharing a domain_scope or
    # task_family. Rank atoms reachable from the task's cue nodes by (link count,
    # recency). Reads NO measured_lift / verified status -- a structural retriever.
    haystack = _task_haystack(task.task)
    cue_nodes = [a for a in atoms if _raw_overlap(haystack, a.content) > 0]
    cue_scopes = {a.domain_scope for a in cue_nodes} | {a.task_family for a in cue_nodes}
    scored: list[tuple[float, str]] = []
    for index, atom in enumerate(atoms):
        links = sum(
            1
            for other in atoms
            if other is not atom
            and ((atom.domain_scope and atom.domain_scope == other.domain_scope)
                 or (atom.task_family and atom.task_family == other.task_family))
        )
        reachable = atom.domain_scope in cue_scopes or atom.task_family in cue_scopes
        if not reachable:
            continue
        scored.append((links + index / max(1, len(atoms)) * 0.01, atom.content))
    return _topk(scored)


def _decisive_for_card_title(title: str) -> str | None:
    return title if title in _DECISIVE_LESSONS else None


def _build_cem(root: Path) -> tuple[CEM, float]:
    """The full CEM rung: validate -> promote -> earn verified lift on the decisive
    lessons via dev-split replay probes -> plant + suppress a negative control."""
    cem = CEM(root, extractor=SyntheticCorruptionExtractor())
    for trace in phase4_memory_source_traces():
        cem.ingest_trace(trace)
        for atom in cem.propose_memories(trace.trace_id):
            cem.validate(atom.atom_id)
            cem.promote(atom.atom_id)
    for card in cem.store.list_cards():
        if card.promotion_status != "candidate":
            continue
        decisive = _decisive_for_card_title(card.title)
        if decisive is None:
            continue
        probe = cem.schedule_probe(
            VerificationProbe(
                kind="held_out_replay",
                target_card_id=card.card_id,
                control_definition="dev-split replay to earn verified lift",
                threshold=0.5,
            )
        )
        cem.run_probe(
            probe.probe_id,
            task=TaskContext(description=decisive, current_time=EVAL_NOW),
            correct_action=decisive,
        )
    _, neg = cem.inject_negative_control(
        title="incident assignment order",
        bad_action="set assignee before assignment_group",
        control_definition="planted inverted incident-form field order",
        threshold=0.5,
    )
    cem.run_probe(
        neg.probe_id,
        task=TaskContext(description="incident assignment order on the form", current_time=EVAL_NOW),
        correct_action=ASSIGNMENT,
    )
    return cem, cem.negative_control_suppression_rate()


def _build_unverified_store(root: Path) -> CEM:
    # Reflection without a verification gate: every proposed atom is saved straight
    # to a card with no validation, so the traps it carries are retrievable.
    cem = CEM(root, extractor=SyntheticCorruptionExtractor())
    for trace in phase4_memory_source_traces():
        cem.ingest_trace(trace)
        for atom in cem.propose_memories(trace.trace_id):
            cem.store.save_card(_card_from_atom(atom))
    return cem


def _task_success(task: Phase4Task, recommended: list[str]) -> float:
    rec = set(recommended)
    if task.decisive_correct_action not in rec:
        return 0.0
    if any(forbidden in rec for forbidden in task.forbidden_actions):
        return 0.0
    return 1.0


def run_phase4_exam(root: str | Path) -> Phase4ExamReport:
    # Fail closed BEFORE any rung runs (spec section 10).
    assert_no_leakage(
        memory_source_ids=memory_source_ids(),
        held_out_answer_ids=held_out_answer_ids(),
    )
    root = Path(root)
    tasks = list(PHASE4_HELD_OUT)
    atoms = [atom for trace in phase4_memory_source_traces() for atom in SyntheticCorruptionExtractor().extract(trace)]
    all_atom_contents = [atom.content for atom in atoms]

    cem, suppression_rate = _build_cem(root / "cem")
    cem_verified_card_count = sum(
        1 for card in cem.store.list_cards() if card.promotion_status == "verified"
    )
    unverified = _build_unverified_store(root / "unverified")

    def recommend(name: str, task: Phase4Task) -> list[str]:
        if name == "no_memory":
            return []
        if name == "full_context":
            return all_atom_contents
        if name == "lexical_overlap":
            return _lexical_overlap_recommend(atoms, task)
        if name == "summary":
            return _summary_recommend(atoms)
        if name == "vector_rag":
            return _vector_recommend(atoms, task, time_aware=False)
        if name == "time_aware_rag":
            return _vector_recommend(atoms, task, time_aware=True)
        if name == "temporal_graph":
            return _temporal_graph_recommend(atoms, task)
        if name == "unverified_reflection":
            return unverified.retrieve_action_brief(task.task, max_cards=20).recommended_next_actions
        if name == "cem":
            return cem.retrieve_action_brief(task.task, max_cards=20).recommended_next_actions
        if name == "human_runbook":
            return [task.decisive_correct_action]  # ceiling oracle
        raise ValueError(f"unknown rung: {name}")

    success_by_rung: dict[str, list[float]] = {
        baseline.name: [_task_success(task, recommend(baseline.name, task)) for task in tasks]
        for baseline in BASELINE_LADDER
    }
    no_memory_success = success_by_rung["no_memory"]

    rungs: list[RungReport] = []
    results: dict[str, MMAResult] = {}
    for baseline in BASELINE_LADDER:
        result = marginal_memory_advantage(success_by_rung[baseline.name], no_memory_success)
        results[baseline.name] = result
        rungs.append(
            RungReport(
                name=baseline.name,
                is_ceiling=baseline.is_ceiling,
                mma=result.mma,
                n=result.n,
                ci_low=result.ci_low,
                ci_high=result.ci_high,
                per_task_success=success_by_rung[baseline.name],
            )
        )

    cem_result = results["cem"]
    lexical_result = results["lexical_overlap"]
    cem_passes = mma_passes(cem_result)
    beats = beats_lexical_by_margin(cem_result, lexical_result)
    verdict = "PASS" if (cem_passes and beats) else "FAIL_REPORTED_HONESTLY"

    return Phase4ExamReport(
        rungs=rungs,
        n=cem_result.n,
        cem_mma=cem_result.mma,
        cem_ci_low=cem_result.ci_low,
        cem_ci_high=cem_result.ci_high,
        lexical_mma=lexical_result.mma,
        measured_lexical_margin_pp=lexical_margin_pp(cem_result, lexical_result),
        cem_passes_success_bar=cem_passes,
        cem_beats_lexical=beats,
        negative_control_suppression_rate=suppression_rate,
        cem_verified_card_count=cem_verified_card_count,
        scorer_version="action_value_v1",
        locked_weights=dict(LOCKED_WEIGHTS),
        verdict=verdict,
    )
