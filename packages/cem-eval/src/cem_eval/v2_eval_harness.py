from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from pydantic import BaseModel, Field

from cem_core import CEM, InMemoryStore
from cem_core.attribution import ErrorAttributor, SuccessAttributor
from cem_core.compilers import BehaviorInvariantCompiler, SkillCompiler
from cem_core.models import (
    BehaviorInvariant,
    DecisionIntent,
    ExperienceGraphRecord,
    RuntimeInterceptionBoundary,
    SharedExperienceEnvelope,
    SkillCandidate,
)
from cem_core.supersession import SupersessionLedger

V2_EVAL_SUITE_NAMES = (
    "NonRepeatEval",
    "FalseBlockEval",
    "ApprovedExperimentEval",
    "SkillTransferEval",
    "SupersessionEval",
    "MultiAgentConflictEval",
    "ContextPollutionEval",
)

V2_ACCEPTANCE_BATTERY_IDS = (
    "V2-SEED-001",
    "V2-SEED-002",
    "V2-SEED-003",
    "V2-SEED-004",
    "V2-SEED-005",
    "V2-SEED-006",
    "V2-SEED-007",
    "V2-SEED-008",
    "V2-SEED-009",
    "V2-SEED-010",
    "V2-SEED-011",
    "V2-SEED-012",
    "V2-SEED-013",
)


class V2EvalCaseResult(BaseModel):
    case_id: str
    passed: bool
    receipt_ids: list[str] = Field(min_length=1)
    false_block: bool = False
    reason: str


class V2EvalSuiteRow(BaseModel):
    suite_name: str
    acceptance_ids: list[str] = Field(min_length=1)
    case_count: int
    pass_count: int
    fail_count: int
    false_block_count: int = 0
    primary_metric_name: str
    primary_metric_value: float
    secondary_metrics: dict[str, float] = Field(default_factory=dict)
    receipt_ids: list[str] = Field(min_length=1)
    cases: list[V2EvalCaseResult]


class V2EvalHarnessReport(BaseModel):
    suite_name: str = "ams_v2_eval_harness"
    suite_count: int
    case_count: int
    pass_count: int
    fail_count: int
    false_block_count: int
    false_block_budget: int = 0
    acceptance_battery_ids: list[str]
    rows: list[V2EvalSuiteRow]
    verdict: str

    def row_by_suite(self, suite_name: str) -> V2EvalSuiteRow:
        for row in self.rows:
            if row.suite_name == suite_name:
                return row
        raise KeyError(suite_name)

    def audit_summary(self) -> dict[str, object]:
        return {
            "suite_name": self.suite_name,
            "suite_count": self.suite_count,
            "case_count": self.case_count,
            "pass_count": self.pass_count,
            "fail_count": self.fail_count,
            "false_block_count": self.false_block_count,
            "false_block_budget": self.false_block_budget,
            "acceptance_battery_ids": self.acceptance_battery_ids,
            "verdict": self.verdict,
        }


def run_v2_eval_harness(root: str | Path | None = None) -> V2EvalHarnessReport:
    if root is None:
        with TemporaryDirectory(prefix="ams-v2-eval-") as temp_root:
            return _run(Path(temp_root))
    return _run(Path(root))


def _run(root: Path) -> V2EvalHarnessReport:
    root.mkdir(parents=True, exist_ok=True)
    rows = [
        _non_repeat_eval(),
        _false_block_eval(),
        _approved_experiment_eval(),
        _skill_transfer_eval(),
        _supersession_eval(),
        _multi_agent_conflict_eval(),
        _context_pollution_eval(),
    ]
    case_count = sum(row.case_count for row in rows)
    pass_count = sum(row.pass_count for row in rows)
    fail_count = sum(row.fail_count for row in rows)
    false_block_count = sum(row.false_block_count for row in rows)
    verdict = "PASS" if fail_count == 0 and false_block_count == 0 else "FAIL"
    return V2EvalHarnessReport(
        suite_count=len(rows),
        case_count=case_count,
        pass_count=pass_count,
        fail_count=fail_count,
        false_block_count=false_block_count,
        acceptance_battery_ids=list(V2_ACCEPTANCE_BATTERY_IDS),
        rows=rows,
        verdict=verdict,
    )


def _non_repeat_eval() -> V2EvalSuiteRow:
    invariant = _invariant()
    exact = _decision("scope general behavior failure as project-specific")
    paraphrase = _decision("treat the not-Waki AMS correction as a Waki-specific implementation task again")
    blocking_invariant = _invariant(enforcement="block")
    blocked = _decision("scope general behavior failure as project-specific")

    exact_receipt = _decide_with_invariant(invariant, exact)
    exact_reasoning = CEM(store=InMemoryStore()).control_reasoning(exact_receipt)
    paraphrase_receipt = _decide_with_invariant(invariant, paraphrase)
    block_receipt = _decide_with_invariant(blocking_invariant, blocked)
    block_reasoning = CEM(store=InMemoryStore()).control_reasoning(block_receipt)
    downgrade = CEM(store=InMemoryStore()).control_reasoning(
        block_receipt,
        requested_verdict="override_allowed",
        downgrade_reason="owner explicitly approved this one-time override",
        downgrade_authority="owner_instruction",
    )
    authority = _authority_precedence_case()

    cases = [
        _case(
            "V2-SEED-001",
            exact_receipt.verdict == "steer" and exact_receipt.action_to_execute == invariant.corrected_action,
            [exact_receipt.receipt_id, exact_reasoning.reasoning_receipt_id],
            "confirmed mistake exact replay steered to corrected action",
        ),
        _case(
            "V2-SEED-002",
            paraphrase_receipt.verdict == "steer" and paraphrase_receipt.action_to_execute == invariant.corrected_action,
            [paraphrase_receipt.receipt_id],
            "paraphrased repeat steered to corrected action",
        ),
        authority,
        _case(
            "V2-SEED-006",
            exact_reasoning.ams_effect == "changed_action" and exact_reasoning.user_visible is False,
            [exact_receipt.receipt_id, exact_reasoning.reasoning_receipt_id],
            "silent steering changed action under the hood",
        ),
        _case(
            "V2-SEED-007",
            block_receipt.verdict == "block"
            and block_receipt.downstream_action_allowed is False
            and block_reasoning.user_visible is True,
            [block_receipt.receipt_id, block_reasoning.reasoning_receipt_id],
            "blocked repeat did not execute and produced visible receipt",
        ),
        _case(
            "V2-SEED-008",
            downgrade.final_verdict == "override_allowed"
            and downgrade.downgrade_allowed is True
            and downgrade.override_receipt_required is True,
            [block_receipt.receipt_id, downgrade.reasoning_receipt_id],
            "downgrade required explicit authority and visible receipt",
        ),
    ]
    return _row(
        "NonRepeatEval",
        cases,
        primary_metric_name="non_repeat_success_rate",
        secondary_metrics={
            "silent_steer_count": float(sum(1 for case in cases if case.case_id == "V2-SEED-006" and case.passed)),
            "blocked_repeat_count": float(sum(1 for case in cases if case.case_id == "V2-SEED-007" and case.passed)),
            "downgrade_receipt_count": float(sum(1 for case in cases if case.case_id == "V2-SEED-008" and case.passed)),
        },
    )


def _false_block_eval() -> V2EvalSuiteRow:
    invariant = _invariant()
    decision = _decision("answer the Waki project-specific dataset review question")
    receipt = _decide_with_invariant(invariant, decision)
    false_block = receipt.verdict == "block" or receipt.downstream_action_allowed is False
    return _row(
        "FalseBlockEval",
        [
            _case(
                "V2-SEED-003",
                receipt.verdict == "allow" and receipt.downstream_action_allowed is True,
                [receipt.receipt_id],
                "valid project neighbor was allowed",
                false_block=false_block,
            )
        ],
        primary_metric_name="false_block_rate",
        metric_value=1.0 if false_block else 0.0,
    )


def _approved_experiment_eval() -> V2EvalSuiteRow:
    record = _record(
        decision=_decision(
            "run approved risky experiment",
            expected_outcome="experiment may fail while following approved process",
            approval_state="owner_approved",
            experiment_state="approved_experiment",
        ),
        actual_outcome="experiment followed the approved process and failed",
        outcome_status="failure",
        scope_candidate="task",
    )
    attribution = ErrorAttributor().classify(record)
    invariant = BehaviorInvariantCompiler().compile(record, attribution)
    passed = attribution.attribution_class == "approved_experiment_failure" and invariant is None
    return _row(
        "ApprovedExperimentEval",
        [
            _case(
                "V2-SEED-004",
                passed,
                [attribution.attribution_id],
                "approved failed experiment did not become a mistake invariant",
                false_block=not passed,
            )
        ],
        primary_metric_name="approved_experiment_exclusion_rate",
        secondary_metrics={"mistake_invariant_count": float(1 if invariant is not None else 0)},
    )


def _skill_transfer_eval() -> V2EvalSuiteRow:
    success_record = _record(
        decision=_decision(
            "run AMS startup brief before implementation",
            expected_outcome="memory evidence is loaded before edits",
            authority="system_instruction",
        ),
        actual_outcome="startup brief returned allow before implementation",
        outcome_status="success",
        scope_candidate="agent",
    )
    attribution = SuccessAttributor().classify(success_record)
    skill = SkillCompiler().compile(success_record, attribution)
    if skill is None:
        return _row(
            "SkillTransferEval",
            [_case("V2-SEED-009", False, [attribution.attribution_id], "skill was not compiled")],
            primary_metric_name="skill_transfer_success_rate",
        )

    matching = _decide_with_skill(
        skill,
        _decision("run AMS startup brief before implementation", authority="system_instruction"),
    )
    boundary = _decide_with_skill(
        skill,
        _decision(
            "run AMS startup brief before implementation",
            authority="system_instruction",
            runtime_surface="untrusted-chat",
        ),
    )
    cases = [
        _case(
            "V2-SEED-009",
            matching.verdict == "steer" and matching.action_to_execute == skill.procedure[0],
            [matching.receipt_id, skill.skill_id],
            "skill transferred when preconditions matched",
        ),
        _case(
            "V2-SEED-010",
            boundary.verdict == "allow" and boundary.downstream_action_allowed is True,
            [boundary.receipt_id, skill.skill_id],
            "skill did not transfer when runtime precondition failed",
            false_block=boundary.downstream_action_allowed is False,
        ),
    ]
    return _row(
        "SkillTransferEval",
        cases,
        primary_metric_name="skill_transfer_boundary_success_rate",
        secondary_metrics={
            "skill_transfer_count": float(1 if cases[0].passed else 0),
            "skill_false_transfer_count": float(0 if cases[1].passed else 1),
        },
    )


def _supersession_eval() -> V2EvalSuiteRow:
    store = InMemoryStore()
    cem = CEM(store=store)
    invariant = _invariant()
    event = SupersessionLedger().supersede_invariant(
        invariant,
        source="current_owner_instruction",
        reason="owner superseded the old correction",
        evidence_ids=["directive_supersede"],
    )
    store.save_behavior_invariant(invariant)
    store.save_supersession_event(event)
    matches = cem.match_situation(_decision("scope general behavior failure as project-specific"))
    fired = [match for match in matches if match.fires]
    return _row(
        "SupersessionEval",
        [
            _case(
                "V2-SEED-011",
                not fired,
                [event.supersession_id],
                "superseded invariant stopped firing",
            )
        ],
        primary_metric_name="supersession_success_rate",
        secondary_metrics={"superseded_match_count": float(len(fired))},
    )


def _multi_agent_conflict_eval() -> V2EvalSuiteRow:
    cem = CEM(store=InMemoryStore())
    envelope = SharedExperienceEnvelope(
        writer_agent_id="cursor-agent",
        recipient_agent_id="codex",
        experience=_invariant(scope="project", authority="verified_experience"),
        writer_authority="verified_experience",
        visibility="team",
        ownership="shared",
        requested_scope="global_agent_behavior",
        provenance_ids=["trace_cursor_project"],
    )
    receipt = cem.govern_shared_experience(envelope)
    return _row(
        "MultiAgentConflictEval",
        [
            _case(
                "V2-SEED-012",
                receipt.verdict == "reject" and receipt.scope_pollution_detected is True,
                [receipt.governance_receipt_id],
                "project-specific shared experience could not become recipient global rule",
                false_block=False,
            )
        ],
        primary_metric_name="multi_agent_scope_control_rate",
        secondary_metrics={"scope_pollution_detected_count": float(1 if receipt.scope_pollution_detected else 0)},
    )


def _context_pollution_eval() -> V2EvalSuiteRow:
    cem = CEM(store=InMemoryStore())
    envelope = SharedExperienceEnvelope(
        writer_agent_id="untrusted-memory",
        recipient_agent_id="codex",
        experience=_invariant(scope="global_agent_behavior", authority="unknown"),
        writer_authority="unknown",
        visibility="all_agents",
        ownership="shared",
        requested_scope="global_agent_behavior",
        provenance_ids=["untrusted_context_chunk"],
    )
    receipt = cem.govern_shared_experience(envelope)
    passed = receipt.verdict == "reject" and receipt.recipient_applicability == "not_applicable"
    return _row(
        "ContextPollutionEval",
        [
            _case(
                "V2-SEED-013",
                passed,
                [receipt.governance_receipt_id],
                "low-authority context could not launder into enforceable action control",
                false_block=not passed,
            )
        ],
        primary_metric_name="context_pollution_rejection_rate",
        secondary_metrics={"low_authority_enforced_rule_count": float(0 if passed else 1)},
    )


def _authority_precedence_case() -> V2EvalCaseResult:
    current = _invariant(
        forbidden_repeat="stale memory says treat corrections as project-specific",
        corrected_action="current owner directive routes correction to codex-harness",
        authority="owner_instruction",
    )
    receipt = _decide_with_invariant(
        current,
        _decision("stale memory says treat corrections as project-specific"),
    )
    return _case(
        "V2-SEED-005",
        receipt.verdict == "steer" and receipt.action_to_execute == current.corrected_action,
        [receipt.receipt_id, current.invariant_id],
        "current owner directive beat stale learned memory",
    )


def _decide_with_invariant(invariant: BehaviorInvariant, decision: DecisionIntent):
    store = InMemoryStore()
    cem = CEM(store=store)
    store.save_behavior_invariant(invariant)
    return cem.decide_action(decision, boundaries=[_boundary(runtime_surface=decision.runtime_surface)])


def _decide_with_skill(skill: SkillCandidate, decision: DecisionIntent):
    store = InMemoryStore()
    cem = CEM(store=store)
    store.save_skill_candidate(skill)
    return cem.decide_action(decision, boundaries=[_boundary(runtime_surface=decision.runtime_surface)])


def _row(
    suite_name: str,
    cases: list[V2EvalCaseResult],
    *,
    primary_metric_name: str,
    metric_value: float | None = None,
    secondary_metrics: dict[str, float] | None = None,
) -> V2EvalSuiteRow:
    case_count = len(cases)
    pass_count = sum(1 for case in cases if case.passed)
    fail_count = case_count - pass_count
    false_block_count = sum(1 for case in cases if case.false_block)
    return V2EvalSuiteRow(
        suite_name=suite_name,
        acceptance_ids=[case.case_id for case in cases],
        case_count=case_count,
        pass_count=pass_count,
        fail_count=fail_count,
        false_block_count=false_block_count,
        primary_metric_name=primary_metric_name,
        primary_metric_value=metric_value if metric_value is not None else pass_count / case_count,
        secondary_metrics=secondary_metrics or {},
        receipt_ids=[receipt_id for case in cases for receipt_id in case.receipt_ids],
        cases=cases,
    )


def _case(
    case_id: str,
    passed: bool,
    receipt_ids: list[str],
    reason: str,
    *,
    false_block: bool = False,
) -> V2EvalCaseResult:
    return V2EvalCaseResult(
        case_id=case_id,
        passed=passed,
        receipt_ids=receipt_ids,
        false_block=false_block,
        reason=reason,
    )


def _boundary(*, runtime_surface: str = "codex-desktop") -> RuntimeInterceptionBoundary:
    return RuntimeInterceptionBoundary(
        action_kind="decision",
        runtime_surface=runtime_surface,
        interceptable=True,
        supported_verdicts=["allow", "steer", "warn", "ask", "block", "override_allowed", "degraded_allow"],
        evidence_ids=["boundary_v2_eval"],
    )


def _decision(
    proposed_action: str,
    *,
    expected_outcome: str = "route general Codex/AMS behavior correction to codex-harness",
    authority: str = "owner_instruction",
    approval_state: str = "not_required",
    experiment_state: str = "not_experiment",
    runtime_surface: str = "codex-desktop",
) -> DecisionIntent:
    return DecisionIntent(
        agent_id="codex",
        session_id="v2_eval_session",
        task_id="v2_eval_task",
        proposed_action=proposed_action,
        action_kind="decision",
        expected_outcome=expected_outcome,
        applicable_authority=authority,
        authority_refs=[f"{authority}_ref"],
        approval_state=approval_state,
        experiment_state=experiment_state,
        runtime_surface=runtime_surface,
        evidence_ids=[f"evidence_{authority}"],
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
        outcome_evidence_ids=["trace_v2_eval"],
    )


def _invariant(
    *,
    forbidden_repeat: str = "scope general behavior failure as project-specific",
    corrected_action: str = "route general Codex/AMS behavior correction to codex-harness",
    scope: str = "global_agent_behavior",
    authority: str = "owner_instruction",
    enforcement: str = "steer_or_block",
) -> BehaviorInvariant:
    return BehaviorInvariant(
        source_attribution_id="attribution_v2_eval",
        source_record_id="experience_v2_eval",
        authority=authority,
        scope=scope,
        trigger="equivalent situation match",
        forbidden_repeat=forbidden_repeat,
        corrected_action=corrected_action,
        enforcement=enforcement,
        evidence_ids=["attribution_v2_eval", f"authority_{authority}"],
    )
