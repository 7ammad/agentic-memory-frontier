from cem_core.attribution import ErrorAttributor, SuccessAttributor, attribute_experience_record
from cem_core.models import DecisionIntent, ExperienceGraphRecord


def _intent(
    *,
    proposed_action: str,
    expected_outcome: str,
    applicable_authority: str = "owner_instruction",
    approval_state: str = "not_required",
    experiment_state: str = "not_experiment",
    evidence_ids: list[str] | None = None,
) -> DecisionIntent:
    return DecisionIntent(
        agent_id="codex",
        session_id="session_1",
        task_id="task_1",
        proposed_action=proposed_action,
        action_kind="decision",
        expected_outcome=expected_outcome,
        applicable_authority=applicable_authority,
        authority_refs=evidence_ids or ["directive_1"],
        approval_state=approval_state,
        experiment_state=experiment_state,
        runtime_surface="codex-desktop",
        evidence_ids=evidence_ids or ["directive_1"],
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


def test_error_attributor_marks_general_owner_correction_as_non_repeat_mistake():
    record = _record(
        decision=_intent(
            proposed_action="scope the owner correction to Waki only",
            expected_outcome="route general Codex/AMS behavior correction to the control-plane invariant lane",
            evidence_ids=["directive_808f20ac409845ac8d111e10ffe5ad0e"],
        ),
        actual_outcome="owner said this is not Waki; it is a general Codex/AMS behavior failure",
        outcome_status="failure",
        scope_candidate="project",
    )

    attribution = ErrorAttributor().classify(record)

    assert attribution.attribution_class == "mistake"
    assert attribution.scope_candidate == "global_agent_behavior"
    assert attribution.non_repeat_candidate is True
    assert attribution.invariant_candidate is True
    assert attribution.approved_experiment_exclusion is False
    assert attribution.skill_candidate is False
    assert attribution.evidence_ids == [
        "directive_808f20ac409845ac8d111e10ffe5ad0e",
        "trace_1",
    ]
    assert "reasoning" not in attribution.audit_summary()


def test_error_attributor_excludes_owner_approved_experiment_failure_from_mistakes():
    record = _record(
        decision=_intent(
            proposed_action="run a risky but approved attribution experiment",
            expected_outcome="experiment may fail while still following the agreed process",
            applicable_authority="owner_instruction",
            approval_state="owner_approved",
            experiment_state="approved_experiment",
            evidence_ids=["directive_experiment_approved"],
        ),
        actual_outcome="experiment followed the process but failed to improve the metric",
        outcome_status="failure",
        scope_candidate="task",
    )

    attribution = ErrorAttributor().classify(record)

    assert attribution.attribution_class == "approved_experiment_failure"
    assert attribution.non_repeat_candidate is False
    assert attribution.invariant_candidate is False
    assert attribution.approved_experiment_exclusion is True


def test_error_attributor_keeps_approved_tradeoff_out_of_mistake_lane():
    record = _record(
        decision=_intent(
            proposed_action="choose the faster implementation with a disclosed quality tradeoff",
            expected_outcome="tradeoff is accepted because it protects the release date",
            applicable_authority="owner_instruction",
            approval_state="owner_approved",
            experiment_state="not_experiment",
            evidence_ids=["directive_tradeoff_approved"],
        ),
        actual_outcome="the accepted tradeoff shipped with the known limitation",
        outcome_status="partial",
        scope_candidate="task",
    )

    attribution = ErrorAttributor().classify(record)

    assert attribution.attribution_class == "acceptable_tradeoff"
    assert attribution.non_repeat_candidate is False
    assert attribution.invariant_candidate is False
    assert attribution.needs_owner_review is False


def test_success_attributor_marks_reusable_success_as_skill_candidate():
    record = _record(
        decision=_intent(
            proposed_action="run AMS startup brief before implementation",
            expected_outcome="the task starts with scoped memory evidence before edits",
            applicable_authority="system_instruction",
            evidence_ids=["directive_startup_gate"],
        ),
        actual_outcome="startup brief returned allow and evidence ids before edits",
        outcome_status="success",
        scope_candidate="agent",
    )

    attribution = SuccessAttributor().classify(record)

    assert attribution.attribution_class == "success"
    assert attribution.skill_candidate is True
    assert attribution.non_repeat_candidate is False
    assert attribution.invariant_candidate is False


def test_unattributable_failure_stays_unresolved_without_authority():
    record = _record(
        decision=_intent(
            proposed_action="guess whether a task succeeded",
            expected_outcome="guess is correct",
            applicable_authority="unknown",
            evidence_ids=["trace_weak"],
        ),
        actual_outcome="the outcome failed but no authority proves it was wrong",
        outcome_status="failure",
        scope_candidate="unknown",
    )

    attribution = attribute_experience_record(record)

    assert attribution.attribution_class == "unresolved"
    assert attribution.non_repeat_candidate is False
    assert attribution.invariant_candidate is False
    assert attribution.needs_owner_review is True
