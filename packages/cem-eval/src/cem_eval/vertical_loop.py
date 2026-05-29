"""Minimal end-to-end CEM vertical-loop runner (Phase 1).

Drives the whole loop on real persisted objects -- ingest -> atom ->
validate -> candidate card -> brief -> influence event -- and computes a
minimal Marginal Memory Advantage via the locked eval protocol. This is a
skeleton smoke that proves the pipe carries water end-to-end; it is NOT the
Phase 4 baseline-ladder exam. The deterministic extractor and lexical
scorer are deliberately kept (the action-value scorer is Phase 3).
"""
from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from cem_core import CEM, AgentTrace, TaskContext, TraceTurn, VerificationProbe
from cem_eval.eval_protocol import assert_no_leakage, marginal_memory_advantage

SCORER_VERSION = "action_value_v1"

# Held-out decisive actions double as the seeded skill content. The toy agent
# "succeeds" on a task iff the retrieved brief recommends its decisive action;
# the no-memory control has no brief and always scores 0.
HELD_OUT: tuple[str, ...] = (
    "set assignment_group before assignee",
    "run pytest before claiming kernel changes are done",
)


class VerticalLoopReport(BaseModel):
    mma: float
    n: int
    ci_low: float
    ci_high: float
    trace_count: int
    atom_count: int
    card_count: int
    verified_card_count: int
    negative_control_suppression_rate: float
    brief_record_count: int
    influence_event_count: int
    scorer_version: str


def run_vertical_loop(root: str | Path, *, inject_leakage: bool = False) -> VerticalLoopReport:
    cem = CEM(root)
    memory_source_ids: set[str] = set()

    # 1-4: ingest -> propose atoms -> validate -> promote to candidate card.
    seeded_cards: dict[str, str] = {}  # card_id -> decisive action it encodes
    for i, decisive in enumerate(HELD_OUT):
        trace = AgentTrace(
            session_id=f"seed-{i}",
            agent_id="codex",
            turns=[TraceTurn(index=0, role="environment", content=f"SKILL: {decisive}")],
            final_outcome="success",
        )
        cem.ingest_trace(trace)
        memory_source_ids.add(trace.trace_id)
        for atom in cem.propose_memories(trace.trace_id):
            cem.validate(atom.atom_id)
            card = cem.promote(atom.atom_id)
            if card is not None:
                seeded_cards[card.card_id] = decisive

    # 5-6: evidence-gated verification. Each candidate is probed on a held-out
    # replay against its own decisive action; passing earns verified (the only
    # path to verified per design 4.2). A planted negative control is injected
    # and probed; recommending the wrong action, it fails and is suppressed.
    for card_id, decisive in seeded_cards.items():
        probe = cem.schedule_probe(
            VerificationProbe(
                kind="held_out_replay",
                target_card_id=card_id,
                control_definition="no-memory control cannot recommend the decisive action",
                threshold=0.5,
            )
        )
        cem.run_probe(
            probe.probe_id,
            task=TaskContext(session_id=None, description=decisive),
            correct_action=decisive,
        )

    bad_card, neg_probe = cem.inject_negative_control(
        title="incident assignment order",
        bad_action="set assignee before assignment_group",
        control_definition="planted false memory: inverted incident-form field order",
        threshold=0.5,
    )
    cem.run_probe(
        neg_probe.probe_id,
        task=TaskContext(session_id=None, description="incident assignment order on the form"),
        correct_action="set assignment_group before assignee",
    )

    # Leakage guard (spec section 10): memory sources and held-out answer ids
    # must be disjoint. inject_leakage is the negative control.
    held_out_answer_ids = {f"answer::{i}" for i in range(len(HELD_OUT))}
    if inject_leakage:
        memory_source_ids |= {"answer::0"}
    assert_no_leakage(memory_source_ids=memory_source_ids, held_out_answer_ids=held_out_answer_ids)

    # 7-9: retrieve brief, "act", close influence | memory vs no-memory control.
    memory_success: list[float] = []
    no_memory_success: list[float] = []
    brief_ids: list[str] = []
    influence_ids: list[str] = []
    for decisive in HELD_OUT:
        brief = cem.retrieve_action_brief(TaskContext(description=decisive))
        brief_ids.append(brief.brief_id)
        if brief.influence_id is not None:
            influence_ids.append(brief.influence_id)
        hit = 1.0 if decisive in brief.recommended_next_actions else 0.0
        memory_success.append(hit)
        no_memory_success.append(0.0)
        cem.close_influence(
            brief.brief_id,
            action_taken=decisive,
            outcome="success" if hit else "failure",
            observed_post_brief_delta=hit,
        )

    mma = marginal_memory_advantage(memory_success, no_memory_success)
    # Counts come from real persisted state, not loop counters. card_count is
    # active cards only -- the suppressed negative control is deactivated and
    # must not inflate the seeded-card tally.
    all_cards = cem.store.list_cards()
    active_card_count = sum(1 for card in all_cards if card.deactivated_at is None)
    verified_card_count = sum(1 for card in all_cards if card.promotion_status == "verified")
    brief_record_count = sum(1 for brief_id in brief_ids if _record_persisted(cem, brief_id))
    influence_event_count = sum(
        len(cem.store.list_action_influence_events(influence_id))
        for influence_id in influence_ids
    )
    return VerticalLoopReport(
        mma=mma.mma,
        n=mma.n,
        ci_low=mma.ci_low,
        ci_high=mma.ci_high,
        trace_count=len(memory_source_ids),
        atom_count=len(cem.store.list_atoms()),
        card_count=active_card_count,
        verified_card_count=verified_card_count,
        negative_control_suppression_rate=cem.negative_control_suppression_rate(),
        brief_record_count=brief_record_count,
        influence_event_count=influence_event_count,
        scorer_version=SCORER_VERSION,
    )


def _record_persisted(cem: CEM, brief_id: str) -> bool:
    try:
        cem.store.get_action_brief_record(brief_id)
        return True
    except KeyError:
        return False
