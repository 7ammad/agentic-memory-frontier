from __future__ import annotations

from dataclasses import dataclass

from .models import (
    ApplicableAuthority,
    MultiAgentGovernanceReceipt,
    SharedExperienceEnvelope,
)

_AUTHORITY_RANK: dict[ApplicableAuthority, int] = {
    "owner_instruction": 0,
    "system_instruction": 1,
    "developer_instruction": 2,
    "project_docs": 3,
    "verified_experience": 4,
    "best_practice": 5,
    "current_evidence": 6,
    "logic": 7,
    "unknown": 8,
}


@dataclass(frozen=True)
class MultiAgentGovernanceLayer:
    def evaluate(
        self,
        envelope: SharedExperienceEnvelope,
        *,
        existing: list[SharedExperienceEnvelope] | None = None,
    ) -> MultiAgentGovernanceReceipt:
        existing = existing or []

        visibility_block = _visibility_blocks(envelope)
        if visibility_block is not None:
            return _receipt(
                envelope,
                verdict="reject",
                recipient_applicability="not_applicable",
                promoted_scope=None,
                scope_pollution_detected=False,
                conflict_receipt_required=True,
                reason=visibility_block,
            )

        pollution_reason = _scope_pollution_reason(envelope)
        if pollution_reason is not None:
            return _receipt(
                envelope,
                verdict="reject",
                recipient_applicability="not_applicable",
                promoted_scope=None,
                scope_pollution_detected=True,
                conflict_receipt_required=True,
                reason=pollution_reason,
            )

        conflict = _authority_conflict(envelope, existing)
        if conflict is not None:
            winner, loser = _winner_loser(envelope, conflict)
            return _receipt(
                envelope,
                verdict="conflict",
                recipient_applicability="needs_review",
                promoted_scope=None,
                scope_pollution_detected=False,
                conflict_receipt_required=True,
                winning_authority=winner.writer_authority,
                losing_authority=loser.writer_authority,
                conflict_agent_ids=[winner.writer_agent_id, loser.writer_agent_id],
                reason="conflicting cross-agent experience surfaced through authority-ranked receipt",
            )

        return _receipt(
            envelope,
            verdict="accept",
            recipient_applicability="applicable",
            promoted_scope=envelope.requested_scope,
            scope_pollution_detected=False,
            conflict_receipt_required=False,
            reason="shared experience accepted within declared authority and scope",
        )


def _visibility_blocks(envelope: SharedExperienceEnvelope) -> str | None:
    if envelope.visibility == "private" and envelope.writer_agent_id != envelope.recipient_agent_id:
        return "visibility constraint blocks private experience from cross-agent sharing"
    if envelope.ownership == "source_agent" and envelope.visibility == "private":
        return "ownership and visibility constrain recipient applicability"
    return None


def _scope_pollution_reason(envelope: SharedExperienceEnvelope) -> str | None:
    if (
        envelope.experience.scope != "global_agent_behavior"
        and envelope.requested_scope == "global_agent_behavior"
        and envelope.writer_authority != "owner_instruction"
    ):
        return "scope pollution: project/agent experience cannot silently become a global behavior rule"
    return None


def _authority_conflict(
    envelope: SharedExperienceEnvelope,
    existing: list[SharedExperienceEnvelope],
) -> SharedExperienceEnvelope | None:
    for candidate in existing:
        if candidate.recipient_agent_id != envelope.recipient_agent_id:
            continue
        if candidate.requested_scope != envelope.requested_scope:
            continue
        if candidate.experience.forbidden_repeat != envelope.experience.forbidden_repeat:
            continue
        if candidate.experience.corrected_action != envelope.experience.corrected_action:
            return candidate
    return None


def _winner_loser(
    envelope: SharedExperienceEnvelope,
    conflict: SharedExperienceEnvelope,
) -> tuple[SharedExperienceEnvelope, SharedExperienceEnvelope]:
    if _AUTHORITY_RANK[envelope.writer_authority] < _AUTHORITY_RANK[conflict.writer_authority]:
        return envelope, conflict
    return conflict, envelope


def _receipt(
    envelope: SharedExperienceEnvelope,
    *,
    verdict: str,
    recipient_applicability: str,
    promoted_scope: str | None,
    scope_pollution_detected: bool,
    conflict_receipt_required: bool,
    reason: str,
    winning_authority: ApplicableAuthority | None = None,
    losing_authority: ApplicableAuthority | None = None,
    conflict_agent_ids: list[str] | None = None,
) -> MultiAgentGovernanceReceipt:
    return MultiAgentGovernanceReceipt(
        envelope_id=envelope.envelope_id,
        writer_agent_id=envelope.writer_agent_id,
        recipient_agent_id=envelope.recipient_agent_id,
        verdict=verdict,
        recipient_applicability=recipient_applicability,
        promoted_scope=promoted_scope,
        scope_pollution_detected=scope_pollution_detected,
        conflict_receipt_required=conflict_receipt_required,
        winning_authority=winning_authority,
        losing_authority=losing_authority,
        conflict_agent_ids=conflict_agent_ids or [],
        reason=reason,
        evidence_ids=_evidence_ids(envelope),
    )


def _evidence_ids(envelope: SharedExperienceEnvelope) -> list[str]:
    seen: set[str] = set()
    evidence_ids: list[str] = []
    for evidence_id in [
        envelope.envelope_id,
        envelope.experience.invariant_id,
        *envelope.experience.evidence_ids,
        *envelope.provenance_ids,
    ]:
        if evidence_id not in seen:
            seen.add(evidence_id)
            evidence_ids.append(evidence_id)
    return evidence_ids
