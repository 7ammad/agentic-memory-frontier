from cem_core import CEM, InMemoryStore
from cem_core.models import BehaviorInvariant
from cem_core.multi_agent_governance import (
    MultiAgentGovernanceLayer,
    SharedExperienceEnvelope,
)


def _invariant(*, scope: str = "project", authority: str = "verified_experience") -> BehaviorInvariant:
    return BehaviorInvariant(
        source_attribution_id="attribution_1",
        source_record_id="experience_1",
        authority=authority,
        scope=scope,
        trigger="equivalent situation match",
        forbidden_repeat="project-specific deployment assumption",
        corrected_action="check this project deployment docs first",
        enforcement="steer_or_block",
        evidence_ids=["attribution_1"],
    )


def test_project_specific_lesson_cannot_become_recipient_global_rule():
    envelope = SharedExperienceEnvelope(
        writer_agent_id="agent_a",
        recipient_agent_id="agent_b",
        experience=_invariant(scope="project"),
        writer_authority="verified_experience",
        visibility="team",
        ownership="source_agent",
        requested_scope="global_agent_behavior",
        provenance_ids=["trace_a"],
    )

    receipt = MultiAgentGovernanceLayer().evaluate(envelope)

    assert receipt.verdict == "reject"
    assert receipt.recipient_applicability == "not_applicable"
    assert receipt.scope_pollution_detected is True
    assert receipt.promoted_scope is None
    assert receipt.conflict_receipt_required is True
    assert "scope pollution" in receipt.reason.lower()
    assert "reasoning" not in receipt.audit_summary()


def test_global_owner_directive_can_apply_across_agents():
    envelope = SharedExperienceEnvelope(
        writer_agent_id="codex",
        recipient_agent_id="cursor-agent",
        experience=_invariant(scope="global_agent_behavior", authority="owner_instruction"),
        writer_authority="owner_instruction",
        visibility="all_agents",
        ownership="owner",
        requested_scope="global_agent_behavior",
        provenance_ids=["directive_owner"],
    )

    receipt = MultiAgentGovernanceLayer().evaluate(envelope)

    assert receipt.verdict == "accept"
    assert receipt.recipient_applicability == "applicable"
    assert receipt.promoted_scope == "global_agent_behavior"
    assert receipt.scope_pollution_detected is False
    assert receipt.conflict_receipt_required is False


def test_visibility_and_ownership_constraints_block_private_experience_sharing():
    envelope = SharedExperienceEnvelope(
        writer_agent_id="agent_a",
        recipient_agent_id="agent_b",
        experience=_invariant(scope="agent"),
        writer_authority="verified_experience",
        visibility="private",
        ownership="source_agent",
        requested_scope="agent",
        provenance_ids=["trace_private"],
    )

    receipt = MultiAgentGovernanceLayer().evaluate(envelope)

    assert receipt.verdict == "reject"
    assert receipt.recipient_applicability == "not_applicable"
    assert receipt.conflict_receipt_required is True
    assert "visibility" in receipt.reason.lower()


def test_conflicting_cross_agent_claim_surfaces_authority_ranked_receipt():
    layer = MultiAgentGovernanceLayer()
    existing = SharedExperienceEnvelope(
        writer_agent_id="codex",
        recipient_agent_id="cursor-agent",
        experience=_invariant(scope="global_agent_behavior", authority="owner_instruction"),
        writer_authority="owner_instruction",
        visibility="all_agents",
        ownership="owner",
        requested_scope="global_agent_behavior",
        provenance_ids=["directive_owner"],
    )
    incoming = SharedExperienceEnvelope(
        writer_agent_id="agent_a",
        recipient_agent_id="cursor-agent",
        experience=_invariant(scope="global_agent_behavior", authority="verified_experience"),
        writer_authority="verified_experience",
        visibility="all_agents",
        ownership="source_agent",
        requested_scope="global_agent_behavior",
        provenance_ids=["trace_agent_a"],
    )
    incoming.experience.corrected_action = "use agent_a preference instead"

    receipt = layer.evaluate(incoming, existing=[existing])

    assert receipt.verdict == "conflict"
    assert receipt.conflict_receipt_required is True
    assert receipt.winning_authority == "owner_instruction"
    assert receipt.losing_authority == "verified_experience"
    assert existing.writer_agent_id in receipt.conflict_agent_ids
    assert incoming.writer_agent_id in receipt.conflict_agent_ids


def test_cem_govern_shared_experience_persists_envelope_and_receipt():
    store = InMemoryStore()
    cem = CEM(store=store)
    envelope = SharedExperienceEnvelope(
        writer_agent_id="codex",
        recipient_agent_id="cursor-agent",
        experience=_invariant(scope="global_agent_behavior", authority="owner_instruction"),
        writer_authority="owner_instruction",
        visibility="all_agents",
        ownership="owner",
        requested_scope="global_agent_behavior",
        provenance_ids=["directive_owner"],
    )

    receipt = cem.govern_shared_experience(envelope)

    assert receipt.verdict == "accept"
    assert store.get_shared_experience_envelope(envelope.envelope_id) == envelope
    assert store.get_multi_agent_governance_receipt(receipt.governance_receipt_id) == receipt
