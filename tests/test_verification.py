"""Phase 2b verification & promotion behavior (design doc section 4.2).

The verified lifecycle is evidence-gated: a candidate card becomes ``verified``
only when a verification probe measures real lift over a no-memory control, and
injected negative controls must be suppressed (deprecated, never promoted). Each
behavior is driven test-first with a failure canary proving the gate bites.
"""
from cem_core import AgentTrace, CEM, TaskContext, TraceTurn, VerificationProbe, VerificationResult


def _skill_trace(content: str, *, session: str = "s1", index: int = 0) -> AgentTrace:
    return AgentTrace(
        session_id=session,
        agent_id="codex",
        turns=[TraceTurn(index=index, role="environment", content=f"SKILL: {content}")],
        final_outcome="success",
    )


def _promote_skill(cem: CEM, content: str, *, index: int = 0):
    trace = _skill_trace(content, index=index)
    cem.ingest_trace(trace)
    atom = cem.propose_memories(trace.trace_id)[0]
    cem.validate(atom.atom_id)
    card = cem.promote(atom.atom_id)
    assert card is not None
    return card


def _held_out_task(description: str) -> TaskContext:
    # session_id=None -> a held-out replay in a fresh session; global scope.
    return TaskContext(session_id=None, description=description)


def test_held_out_replay_probe_verifies_card_with_measured_lift(tmp_path):
    # A grounded card that recommends the decisive action on a held-out task
    # yields lift 1.0 over a no-memory control, so the probe earns verification:
    # promotion_status flips to verified, measured_lift is stored, and the result
    # id is linked. This is the ONLY path to verified (design 4.2 hard rule).
    cem = CEM(tmp_path)
    card = _promote_skill(cem, "set assignment_group before assignee")
    assert card.promotion_status == "candidate"

    probe = cem.schedule_probe(
        VerificationProbe(
            kind="held_out_replay",
            target_card_id=card.card_id,
            control_definition="no-memory control cannot recommend the decisive action",
            threshold=0.5,
        )
    )
    result = cem.run_probe(
        probe.probe_id,
        task=_held_out_task("set assignment_group before assignee on the incident"),
        correct_action="set assignment_group before assignee",
    )

    assert result.passed
    assert result.measured_lift == 1.0
    verified = cem.store.get_card(card.card_id)
    assert verified.promotion_status == "verified"
    assert verified.measured_lift == 1.0
    assert result.result_id in verified.verification_result_ids


def test_held_out_replay_probe_does_not_verify_card_without_lift(tmp_path):
    # Failure canary for the promotion gate: the same grounded card run against a
    # held-out task whose decisive action it does NOT recommend yields zero lift,
    # so the probe must FAIL and the card must stay candidate. If promotion were
    # asserted rather than earned, this card would verify and the assertion bites.
    cem = CEM(tmp_path)
    card = _promote_skill(cem, "set assignment_group before assignee")

    probe = cem.schedule_probe(
        VerificationProbe(
            kind="held_out_replay",
            target_card_id=card.card_id,
            control_definition="no-memory control",
            threshold=0.5,
        )
    )
    result = cem.run_probe(
        probe.probe_id,
        task=_held_out_task("rotate the production database credentials safely"),
        correct_action="rotate credentials using the sealed secret store",
    )

    assert not result.passed
    assert result.measured_lift == 0.0
    still_candidate = cem.store.get_card(card.card_id)
    assert still_candidate.promotion_status == "candidate"
    assert still_candidate.measured_lift is None
