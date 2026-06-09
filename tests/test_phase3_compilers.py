from cem_core.attribution import ErrorAttributor, SuccessAttributor
from cem_core.compilers import (
    AuthorityEvidence,
    AuthorityScopeResolver,
    BehaviorInvariantCompiler,
    SkillCompiler,
)
from cem_core.models import DecisionIntent, ExperienceGraphRecord


def _intent(
    *,
    proposed_action: str,
    expected_outcome: str,
    authority: str,
    evidence_id: str,
) -> DecisionIntent:
    return DecisionIntent(
        agent_id="codex",
        session_id="session_1",
        task_id="task_1",
        proposed_action=proposed_action,
        action_kind="decision",
        expected_outcome=expected_outcome,
        applicable_authority=authority,
        authority_refs=[evidence_id],
        approval_state="not_required",
        experiment_state="not_experiment",
        runtime_surface="codex-desktop",
        evidence_ids=[evidence_id],
    )


def _record(
    *,
    decision: DecisionIntent,
    actual_outcome: str,
    outcome_status: str,
    scope_candidate: str,
) -> ExperienceGraphRecord:
    return ExperienceGraphRecord(
        decision=decision,
        actual_outcome=actual_outcome,
        outcome_status=outcome_status,
        scope_candidate=scope_candidate,
        outcome_evidence_ids=["trace_1"],
    )


def test_behavior_invariant_compiler_turns_confirmed_mistake_into_scoped_invariant():
    record = _record(
        decision=_intent(
            proposed_action="scope the owner correction to Waki only",
            expected_outcome="route general Codex/AMS behavior correction to codex-harness",
            authority="owner_instruction",
            evidence_id="directive_808f20ac409845ac8d111e10ffe5ad0e",
        ),
        actual_outcome="owner said this is not Waki; it is a general Codex/AMS behavior failure",
        outcome_status="failure",
        scope_candidate="project",
    )
    attribution = ErrorAttributor().classify(record)

    invariant = BehaviorInvariantCompiler().compile(record, attribution)

    assert invariant is not None
    assert invariant.invariant_id.startswith("invariant_")
    assert invariant.authority == "owner_instruction"
    assert invariant.scope == "global_agent_behavior"
    assert invariant.enforcement == "steer_or_block"
    assert invariant.supersession_status == "active"
    assert "scope the owner correction to Waki only" in invariant.forbidden_repeat
    assert "route general Codex/AMS behavior correction to codex-harness" in invariant.corrected_action
    assert attribution.attribution_id in invariant.evidence_ids
    assert "reasoning" not in invariant.audit_summary()


def test_behavior_invariant_compiler_ignores_approved_experiment_failure():
    record = _record(
        decision=DecisionIntent(
            agent_id="codex",
            session_id="session_1",
            task_id="task_1",
            proposed_action="run approved risky experiment",
            action_kind="decision",
            expected_outcome="experiment may fail while following approved process",
            applicable_authority="owner_instruction",
            authority_refs=["directive_experiment"],
            approval_state="owner_approved",
            experiment_state="approved_experiment",
            runtime_surface="codex-desktop",
            evidence_ids=["directive_experiment"],
        ),
        actual_outcome="experiment followed the process and failed",
        outcome_status="failure",
        scope_candidate="task",
    )
    attribution = ErrorAttributor().classify(record)

    assert BehaviorInvariantCompiler().compile(record, attribution) is None


def test_skill_compiler_turns_confirmed_success_into_skill_candidate():
    record = _record(
        decision=_intent(
            proposed_action="run AMS startup brief before implementation",
            expected_outcome="memory evidence is loaded before edits",
            authority="system_instruction",
            evidence_id="directive_startup_gate",
        ),
        actual_outcome="startup brief returned allow before implementation",
        outcome_status="success",
        scope_candidate="agent",
    )
    attribution = SuccessAttributor().classify(record)

    skill = SkillCompiler().compile(record, attribution)

    assert skill is not None
    assert skill.skill_id.startswith("skill_")
    assert skill.transfer_scope == "agent"
    assert skill.promotion_status == "candidate"
    assert skill.preconditions == ["authority_basis=system_instruction", "runtime_surface=codex-desktop"]
    assert skill.procedure == ["run AMS startup brief before implementation"]
    assert skill.expected_result == "memory evidence is loaded before edits"
    assert "missing authority evidence" in skill.when_not_to_apply
    assert attribution.attribution_id in skill.evidence_ids


def test_authority_scope_resolver_prefers_current_owner_instruction_over_stale_memory():
    resolver = AuthorityScopeResolver()
    winner = resolver.choose_highest(
        [
            AuthorityEvidence(
                evidence_id="card_stale",
                authority_lane="learned_card",
                content="old learned behavior",
                is_stale=True,
            ),
            AuthorityEvidence(
                evidence_id="directive_owner",
                authority_lane="current_owner_instruction",
                content="current owner correction",
            ),
        ]
    )

    assert winner.evidence_id == "directive_owner"
    assert resolver.promote_scope("project", winning_authority="current_owner_instruction") == "global_agent_behavior"
    assert resolver.promote_scope("project", winning_authority="learned_card") == "project"
