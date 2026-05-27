from cem_core import (
    AgentTrace,
    CEM,
    InMemoryStore,
    MultiAgentTrustPolicy,
    TraceTurn,
    build_shared_trace_envelope,
    import_shared_trace,
)


def test_trusted_shared_trace_can_promote_experience():
    cem = CEM(store=InMemoryStore())
    trace = _shared_trace(sender_agent_id="agent-alpha")
    envelope = build_shared_trace_envelope(
        trace,
        sender_agent_id="agent-alpha",
        recipient_agent_id="codex",
    )

    receipt = import_shared_trace(
        cem,
        envelope,
        trust_policy=MultiAgentTrustPolicy(trusted_agent_ids=["agent-alpha"]),
    )
    atom = cem.propose_memories(receipt.trace_receipt.trace_id)[0]
    decision = cem.validate(atom.atom_id)
    card = cem.promote(atom.atom_id)

    assert receipt.trusted_sender is True
    assert receipt.imported_agent_id == "agent-alpha"
    assert decision.decision == "candidate"
    assert card is not None
    assert card.do == ["open approvals tab"]


def test_untrusted_shared_trace_is_quarantined_by_existing_write_path():
    cem = CEM(store=InMemoryStore())
    trace = _shared_trace(sender_agent_id="agent-beta")
    envelope = build_shared_trace_envelope(
        trace,
        sender_agent_id="agent-beta",
        recipient_agent_id="codex",
    )

    receipt = import_shared_trace(cem, envelope)
    atom = cem.propose_memories(receipt.trace_receipt.trace_id)[0]
    decision = cem.validate(atom.atom_id)

    assert receipt.trusted_sender is False
    assert receipt.imported_agent_id == "untrusted-agent-beta"
    assert decision.decision == "quarantined"
    assert decision.reason_codes == ["untrusted_source"]
    assert cem.store.get_atom(atom.atom_id).promotion_status == "quarantined"


def test_shared_trace_hash_mismatch_is_rejected():
    cem = CEM(store=InMemoryStore())
    envelope = build_shared_trace_envelope(
        _shared_trace(sender_agent_id="agent-alpha"),
        sender_agent_id="agent-alpha",
        recipient_agent_id="codex",
    )
    envelope.body_hash = "not-the-real-hash"

    try:
        import_shared_trace(
            cem,
            envelope,
            trust_policy=MultiAgentTrustPolicy(trusted_agent_ids=["agent-alpha"]),
        )
    except ValueError as exc:
        assert "body_hash does not match" in str(exc)
    else:
        raise AssertionError("Tampered shared trace envelope should be rejected.")


def test_sender_trace_agent_mismatch_is_not_trusted():
    cem = CEM(store=InMemoryStore())
    trace = _shared_trace(sender_agent_id="agent-alpha")
    envelope = build_shared_trace_envelope(
        trace,
        sender_agent_id="agent-beta",
        recipient_agent_id="codex",
    )

    receipt = import_shared_trace(
        cem,
        envelope,
        trust_policy=MultiAgentTrustPolicy(trusted_agent_ids=["agent-beta"]),
    )

    assert receipt.trusted_sender is False
    assert receipt.imported_agent_id == "untrusted-agent-beta"


def _shared_trace(*, sender_agent_id: str) -> AgentTrace:
    return AgentTrace(
        session_id="shared-session",
        agent_id=sender_agent_id,
        task_id="approval-flow",
        turns=[TraceTurn(index=0, role="environment", content="SKILL: open approvals tab")],
        final_outcome="success",
        environment={"domain": "workflow-nav"},
    )
