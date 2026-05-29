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


def test_negative_control_is_suppressed_never_verified(tmp_path):
    # Design 4.2 negative control: a planted false memory (plausible enough to be
    # retrieved, but recommending the WRONG action) must be deprecated and removed
    # from retrieval by its probe, never promoted. Suppression rate must be 100%.
    cem = CEM(tmp_path)
    bad_card, probe = cem.inject_negative_control(
        title="incident assignment order",
        bad_action="set assignee before assignment_group",
        control_definition="planted false memory: inverted incident-form field order",
        threshold=0.5,
    )

    # The false memory is retrievable before the probe runs.
    pre = cem.retrieve_action_brief(_held_out_task("incident assignment order on the form"))
    assert bad_card.card_id in pre.applicable_card_ids

    result = cem.run_probe(
        probe.probe_id,
        task=_held_out_task("incident assignment order on the form"),
        correct_action="set assignment_group before assignee",
    )
    assert not result.passed

    suppressed = cem.store.get_card(bad_card.card_id)
    assert suppressed.promotion_status == "deprecated"
    assert suppressed.deactivated_at is not None
    assert cem.negative_control_suppression_rate() == 1.0

    # The suppressed control is gone from retrieval.
    post = cem.retrieve_action_brief(_held_out_task("incident assignment order on the form"))
    assert bad_card.card_id not in post.applicable_card_ids


def test_suppression_rate_drops_when_negative_control_leaks_to_verified(tmp_path):
    # Failure canary for the suppression metric: if a negative control ever reaches
    # verified (the runner failed to catch it), the rate must fall below 1.0. A
    # metric that always returns 1.0 is not a gate -- this proves it detects a leak.
    cem = CEM(tmp_path)
    bad_card, probe = cem.inject_negative_control(
        title="incident assignment order",
        bad_action="set assignee before assignment_group",
        control_definition="planted false memory",
        threshold=0.5,
    )
    assert cem.negative_control_suppression_rate() == 1.0

    # Simulate a leak: a passing result slips through and verifies the bad card.
    cem.apply_verification_result(
        VerificationResult(
            probe_id=probe.probe_id,
            card_id=bad_card.card_id,
            measured_lift=1.0,
            passed=True,
        )
    )
    assert cem.store.get_card(bad_card.card_id).promotion_status == "verified"
    assert cem.negative_control_suppression_rate() < 1.0
