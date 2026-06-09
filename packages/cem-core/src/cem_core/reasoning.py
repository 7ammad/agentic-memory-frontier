from __future__ import annotations

from dataclasses import dataclass

from .models import ActionDecisionReceipt, ApplicableAuthority, PolicyVerdict, ReasoningControlReceipt

_ESCALATION_ORDER = {
    "allow": 0,
    "steer": 1,
    "warn": 2,
    "ask": 3,
    "block": 4,
}
_DOWNGRADE_AUTHORITIES = {
    "owner_instruction",
    "system_instruction",
    "developer_instruction",
}


@dataclass(frozen=True)
class ReasoningController:
    def control(
        self,
        receipt: ActionDecisionReceipt,
        *,
        requested_verdict: PolicyVerdict | None = None,
        downgrade_reason: str | None = None,
        downgrade_authority: ApplicableAuthority | None = None,
    ) -> ReasoningControlReceipt:
        if requested_verdict is None or requested_verdict == receipt.verdict:
            return _standard_control(receipt)

        if _is_escalation(receipt.verdict, requested_verdict):
            return _control_receipt(
                receipt,
                final_verdict=requested_verdict,
                ams_effect=_effect_for(requested_verdict),
                user_visible=requested_verdict in {"ask", "block", "override_allowed"},
                downgrade_allowed=False,
                override_receipt_required=False,
                authority=downgrade_authority,
                summary=f"Escalated verdict from {receipt.verdict} to {requested_verdict}.",
            )

        if _is_allowed_downgrade(receipt, requested_verdict, downgrade_reason, downgrade_authority):
            return _control_receipt(
                receipt,
                final_verdict=requested_verdict,
                ams_effect="override" if requested_verdict == "override_allowed" else _effect_for(requested_verdict),
                user_visible=True,
                downgrade_allowed=True,
                override_receipt_required=True,
                authority=downgrade_authority,
                summary=f"Downgrade allowed by {downgrade_authority}: {downgrade_reason}",
            )

        return _control_receipt(
            receipt,
            final_verdict=receipt.verdict,
            ams_effect=_effect_for(receipt.verdict),
            user_visible=True,
            downgrade_allowed=False,
            override_receipt_required=True,
            authority=downgrade_authority,
            summary="Downgrade rejected: block/ask/steer cannot be silently reduced without explicit authority and reason.",
        )


def _standard_control(receipt: ActionDecisionReceipt) -> ReasoningControlReceipt:
    final_verdict = receipt.verdict
    user_visible = receipt.user_visible or final_verdict in {"ask", "block", "override_allowed"}
    return _control_receipt(
        receipt,
        final_verdict=final_verdict,
        ams_effect=_effect_for(final_verdict),
        user_visible=user_visible,
        downgrade_allowed=False,
        override_receipt_required=final_verdict in {"block", "ask", "override_allowed"},
        authority=None,
        summary=_summary_for(receipt, final_verdict),
    )


def _is_escalation(current: PolicyVerdict, requested: PolicyVerdict) -> bool:
    if current not in _ESCALATION_ORDER or requested not in _ESCALATION_ORDER:
        return False
    return _ESCALATION_ORDER[requested] > _ESCALATION_ORDER[current]


def _is_allowed_downgrade(
    receipt: ActionDecisionReceipt,
    requested: PolicyVerdict,
    downgrade_reason: str | None,
    downgrade_authority: ApplicableAuthority | None,
) -> bool:
    if receipt.verdict not in {"block", "ask", "steer", "warn"}:
        return False
    return (
        requested == "override_allowed"
        and bool(downgrade_reason)
        and downgrade_authority in _DOWNGRADE_AUTHORITIES
    )


def _control_receipt(
    receipt: ActionDecisionReceipt,
    *,
    final_verdict: PolicyVerdict,
    ams_effect: str,
    user_visible: bool,
    downgrade_allowed: bool,
    override_receipt_required: bool,
    authority: ApplicableAuthority | None,
    summary: str,
) -> ReasoningControlReceipt:
    return ReasoningControlReceipt(
        action_receipt_id=receipt.receipt_id,
        original_verdict=receipt.verdict,
        final_verdict=final_verdict,
        ams_effect=ams_effect,
        matched_experience_ids=receipt.source_ids,
        authority=authority,
        user_visible=user_visible,
        receipt_available=True,
        downgrade_allowed=downgrade_allowed,
        override_receipt_required=override_receipt_required,
        summary=summary,
        evidence_ids=[receipt.receipt_id, *receipt.evidence_ids],
    )


def _effect_for(verdict: PolicyVerdict) -> str:
    if verdict == "steer":
        return "changed_action"
    if verdict == "block":
        return "blocked_action"
    if verdict in {"ask", "warn"}:
        return "visible_intervention"
    if verdict == "override_allowed":
        return "override"
    return "none"


def _summary_for(receipt: ActionDecisionReceipt, verdict: PolicyVerdict) -> str:
    if verdict == "steer":
        return "Silently steered matched experience under the hood."
    if verdict == "block":
        return f"Blocked action: {receipt.reason}"
    if verdict == "ask":
        return f"Owner input required: {receipt.reason}"
    if verdict == "override_allowed":
        return f"Override receipt available: {receipt.reason}"
    return receipt.reason
