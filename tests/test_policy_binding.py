from cem_core import CEM, InMemoryStore
from cem_core.matching import SituationMatcher
from cem_core.models import BehaviorInvariant, DecisionIntent, RuntimeInterceptionBoundary, SkillCandidate
from cem_core.policy import ActionDecisionPoint, PolicyBindingLayer


def _decision(
    proposed_action: str,
    *,
    action_kind: str = "decision",
    runtime_surface: str = "codex-desktop",
) -> DecisionIntent:
    return DecisionIntent(
        agent_id="codex",
        session_id="session_3",
        task_id="task_3",
        proposed_action=proposed_action,
        action_kind=action_kind,
        expected_outcome="action is governed before execution",
        applicable_authority="owner_instruction",
        authority_refs=["directive_current"],
        approval_state="not_required",
        experiment_state="not_experiment",
        runtime_surface=runtime_surface,
        evidence_ids=["directive_current"],
    )


def _invariant(*, enforcement: str = "steer_or_block") -> BehaviorInvariant:
    return BehaviorInvariant(
        source_attribution_id="attribution_1",
        source_record_id="experience_1",
        authority="owner_instruction",
        scope="global_agent_behavior",
        trigger="equivalent situation match",
        forbidden_repeat="scope general behavior failure as project-specific",
        corrected_action="route general Codex/AMS behavior correction to codex-harness",
        enforcement=enforcement,
        evidence_ids=["attribution_1", "directive_1"],
    )


def _skill() -> SkillCandidate:
    return SkillCandidate(
        source_attribution_id="attribution_2",
        source_record_id="experience_2",
        transfer_scope="agent",
        preconditions=["authority_basis=owner_instruction", "runtime_surface=codex-desktop"],
        procedure=["run AMS startup brief before implementation"],
        expected_result="memory evidence is loaded before edits",
        evidence_ids=["attribution_2", "trace_2"],
        when_not_to_apply=["missing authority evidence"],
    )


def _interceptable_boundary() -> RuntimeInterceptionBoundary:
    return RuntimeInterceptionBoundary(
        action_kind="decision",
        runtime_surface="codex-desktop",
        interceptable=True,
        supported_verdicts=["allow", "steer", "warn", "ask", "block", "override_allowed", "degraded_allow"],
        evidence_ids=["boundary_codex_desktop"],
    )


def test_policy_binding_silently_steers_known_repeat_before_execution():
    decision = _decision("scope general behavior failure as project-specific")
    invariant = _invariant()
    match = SituationMatcher().match_decision(decision, invariants=[invariant], skills=[])[0]

    receipt = PolicyBindingLayer().decide(
        decision,
        matches=[match],
        invariants=[invariant],
        skills=[],
        boundaries=[_interceptable_boundary()],
    )

    assert receipt.verdict == "steer"
    assert receipt.downstream_action_allowed is True
    assert receipt.action_to_execute == invariant.corrected_action
    assert receipt.original_action == decision.proposed_action
    assert receipt.user_visible is False
    assert receipt.boundary_status == "interceptable"
    assert match.match_id in receipt.match_ids
    assert invariant.invariant_id in receipt.source_ids
    assert "reasoning" not in receipt.audit_summary()


def test_policy_binding_blocks_when_invariant_requires_block():
    decision = _decision("scope general behavior failure as project-specific")
    invariant = _invariant(enforcement="block")
    match = SituationMatcher().match_decision(decision, invariants=[invariant], skills=[])[0]

    receipt = PolicyBindingLayer().decide(
        decision,
        matches=[match],
        invariants=[invariant],
        skills=[],
        boundaries=[_interceptable_boundary()],
    )

    assert receipt.verdict == "block"
    assert receipt.downstream_action_allowed is False
    assert receipt.action_to_execute is None
    assert receipt.user_visible is True
    assert "blocked" in receipt.reason.lower()


def test_policy_binding_records_non_interceptable_boundary_honestly():
    decision = _decision("scope general behavior failure as project-specific", action_kind="external_send")
    invariant = _invariant(enforcement="block")
    match = SituationMatcher().match_decision(decision, invariants=[invariant], skills=[])[0]
    boundary = RuntimeInterceptionBoundary(
        action_kind="external_send",
        runtime_surface="codex-desktop",
        interceptable=False,
        supported_verdicts=["allow", "warn", "degraded_allow"],
        evidence_ids=["boundary_external_send_unwired"],
    )

    receipt = PolicyBindingLayer().decide(
        decision,
        matches=[match],
        invariants=[invariant],
        skills=[],
        boundaries=[boundary],
    )

    assert receipt.verdict == "degraded_allow"
    assert receipt.downstream_action_allowed is True
    assert receipt.boundary_status == "non_interceptable"
    assert receipt.user_visible is True
    assert "cannot intercept" in receipt.reason.lower()


def test_policy_binding_steers_to_skill_when_skill_match_fires():
    decision = _decision("run AMS startup brief before implementation")
    skill = _skill()
    match = SituationMatcher().match_decision(decision, invariants=[], skills=[skill])[0]

    receipt = PolicyBindingLayer().decide(
        decision,
        matches=[match],
        invariants=[],
        skills=[skill],
        boundaries=[_interceptable_boundary()],
    )

    assert receipt.verdict == "steer"
    assert receipt.action_to_execute == "run AMS startup brief before implementation"
    assert receipt.downstream_action_allowed is True
    assert receipt.user_visible is False


def test_action_decision_point_persists_receipts_through_cem():
    store = InMemoryStore()
    cem = CEM(store=store)
    invariant = _invariant()
    decision = _decision("scope general behavior failure as project-specific")
    store.save_behavior_invariant(invariant)

    receipt = ActionDecisionPoint(cem).decide(decision, boundaries=[_interceptable_boundary()])

    assert receipt.verdict == "steer"
    assert store.get_action_decision_receipt(receipt.receipt_id) == receipt
    assert store.get_runtime_interception_boundary(receipt.boundary_id).interceptable is True


def test_cem_decision_then_reasoning_control_keeps_silent_steer_quiet():
    store = InMemoryStore()
    cem = CEM(store=store)
    invariant = _invariant()
    decision = _decision("scope general behavior failure as project-specific")
    store.save_behavior_invariant(invariant)

    decision_receipt = cem.decide_action(decision, boundaries=[_interceptable_boundary()])
    reasoning_receipt = cem.control_reasoning(decision_receipt)

    assert decision_receipt.verdict == "steer"
    assert reasoning_receipt.ams_effect == "changed_action"
    assert reasoning_receipt.user_visible is False
    assert store.get_reasoning_control_receipt(reasoning_receipt.reasoning_receipt_id) == reasoning_receipt
