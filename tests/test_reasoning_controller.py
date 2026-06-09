from cem_core import CEM, InMemoryStore
from cem_core.models import ActionDecisionReceipt, ReasoningControlReceipt
from cem_core.reasoning import ReasoningController


def _receipt(
    *,
    verdict: str,
    user_visible: bool,
    reason: str = "policy reason",
    source_ids: list[str] | None = None,
) -> ActionDecisionReceipt:
    return ActionDecisionReceipt(
        decision_id="decision_1",
        original_action="repeat known mistake",
        action_to_execute=None if verdict == "block" else "corrected action",
        verdict=verdict,
        downstream_action_allowed=verdict != "block",
        user_visible=user_visible,
        boundary_status="interceptable",
        boundary_id="boundary_1",
        match_ids=["match_1"],
        source_ids=source_ids or ["invariant_1"],
        reason=reason,
        evidence_ids=["decision_1", "match_1", "invariant_1"],
    )


def test_reasoning_controller_keeps_silent_steering_under_the_hood():
    decision = _receipt(verdict="steer", user_visible=False, reason="silently steered known repeat")

    control = ReasoningController().control(decision)

    assert control.ams_effect == "changed_action"
    assert control.final_verdict == "steer"
    assert control.user_visible is False
    assert control.receipt_available is True
    assert control.downgrade_allowed is False
    assert "raw_reasoning" not in control.model_dump()
    assert "reasoning" not in control.audit_summary()


def test_reasoning_controller_forces_block_visibility():
    decision = _receipt(verdict="block", user_visible=False, reason="blocked known repeat")

    control = ReasoningController().control(decision)

    assert control.final_verdict == "block"
    assert control.user_visible is True
    assert control.ams_effect == "blocked_action"
    assert "blocked" in control.summary.lower()


def test_reasoning_controller_rejects_silent_block_to_allow_downgrade():
    decision = _receipt(verdict="block", user_visible=True, reason="blocked known repeat")

    control = ReasoningController().control(
        decision,
        requested_verdict="allow",
        downgrade_reason=None,
        downgrade_authority=None,
    )

    assert control.final_verdict == "block"
    assert control.downgrade_allowed is False
    assert control.user_visible is True
    assert control.override_receipt_required is True
    assert "downgrade rejected" in control.summary.lower()


def test_reasoning_controller_allows_explicit_owner_authorized_downgrade_with_visible_receipt():
    decision = _receipt(verdict="block", user_visible=True, reason="blocked known repeat")

    control = ReasoningController().control(
        decision,
        requested_verdict="override_allowed",
        downgrade_reason="owner explicitly approved this one-time override",
        downgrade_authority="owner_instruction",
    )

    assert control.final_verdict == "override_allowed"
    assert control.downgrade_allowed is True
    assert control.user_visible is True
    assert control.override_receipt_required is True
    assert control.authority == "owner_instruction"
    assert "one-time override" in control.summary


def test_reasoning_control_receipt_roundtrip_excludes_hidden_reasoning():
    receipt = ReasoningControlReceipt(
        action_receipt_id="receipt_1",
        original_verdict="block",
        final_verdict="block",
        ams_effect="blocked_action",
        matched_experience_ids=["invariant_1"],
        authority="owner_instruction",
        user_visible=True,
        receipt_available=True,
        downgrade_allowed=False,
        override_receipt_required=True,
        summary="Blocked known repeat.",
        evidence_ids=["receipt_1", "invariant_1"],
    )

    assert ReasoningControlReceipt.model_validate_json(receipt.model_dump_json()) == receipt
    assert "hidden" not in receipt.audit_summary()
    assert "reasoning" not in receipt.audit_summary()


def test_cem_control_reasoning_persists_receipt():
    store = InMemoryStore()
    cem = CEM(store=store)
    decision = _receipt(verdict="block", user_visible=True, reason="blocked known repeat")

    control = cem.control_reasoning(decision)

    assert control.final_verdict == "block"
    assert store.get_reasoning_control_receipt(control.reasoning_receipt_id) == control
