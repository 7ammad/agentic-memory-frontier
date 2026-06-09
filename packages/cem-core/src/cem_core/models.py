from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, TypeAlias
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

JsonPrimitive: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonPrimitive | list[JsonPrimitive] | dict[str, JsonPrimitive]


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourceSpan(StrictModel):
    turn_id: str
    start: int
    end: int
    text: str


class ConfidenceInterval(StrictModel):
    low: float
    high: float


ExpectedActionDeltaSource = Literal[
    "none",
    "observational_unverified",
    "probe_verified",
    "heldout_eval",
]


class TraceTurn(StrictModel):
    turn_id: str = Field(default_factory=lambda: new_id("turn"))
    index: int
    timestamp: datetime = Field(default_factory=utc_now)
    role: Literal["user", "assistant", "tool", "environment", "system"]
    content: str
    tool_name: str | None = None
    tool_input: dict[str, JsonValue] | None = None
    tool_output: dict[str, JsonValue] | None = None
    observation_ref: str | None = None
    artifact_refs: list[str] = Field(default_factory=list)


class AgentTrace(StrictModel):
    trace_id: str = Field(default_factory=lambda: new_id("trace"))
    session_id: str
    agent_id: str
    task_id: str | None = None
    started_at: datetime = Field(default_factory=utc_now)
    ended_at: datetime | None = None
    turns: list[TraceTurn]
    final_outcome: Literal["success", "failure", "partial", "unknown"] = "unknown"
    outcome_score: float | None = None
    environment: dict[str, JsonValue] = Field(default_factory=dict)


ActionKind = Literal["message", "tool_use", "file_edit", "command", "external_send", "decision", "other"]
ApplicableAuthority = Literal[
    "owner_instruction",
    "system_instruction",
    "developer_instruction",
    "project_docs",
    "verified_experience",
    "best_practice",
    "current_evidence",
    "logic",
    "unknown",
]
ApprovalState = Literal["not_required", "owner_approved", "owner_rejected", "pending", "implicit", "unknown"]
ExperimentState = Literal["not_experiment", "approved_experiment", "unapproved_experiment", "unknown"]
ExperienceScopeCandidate = Literal[
    "global_agent_behavior",
    "agent",
    "project",
    "task",
    "multi_agent",
    "unknown",
]
AttributionClass = Literal[
    "mistake",
    "approved_experiment_failure",
    "acceptable_tradeoff",
    "success",
    "unresolved",
]


class DecisionIntent(StrictModel):
    decision_id: str = Field(default_factory=lambda: new_id("decision"))
    trace_id: str | None = None
    turn_id: str | None = None
    agent_id: str
    session_id: str
    task_id: str | None = None
    proposed_action: str = Field(min_length=1)
    action_kind: ActionKind
    expected_outcome: str = Field(min_length=1)
    applicable_authority: ApplicableAuthority
    authority_refs: list[str] = Field(default_factory=list)
    approval_state: ApprovalState
    experiment_state: ExperimentState
    runtime_surface: str = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)
    captured_at: datetime = Field(default_factory=utc_now)


class ExperienceGraphRecord(StrictModel):
    record_id: str = Field(default_factory=lambda: new_id("experience"))
    decision: DecisionIntent
    actual_outcome: str | None = None
    outcome_status: Literal["success", "failure", "partial", "unknown"] = "unknown"
    scope_candidate: ExperienceScopeCandidate = "unknown"
    outcome_evidence_ids: list[str] = Field(default_factory=list)
    attribution_status: Literal["unattributed", "pending", "attributed"] = "pending"
    inference_receipt_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now)

    def audit_summary(self) -> dict[str, object]:
        evidence_ids = [*self.decision.evidence_ids, *self.outcome_evidence_ids]
        return {
            "record_id": self.record_id,
            "decision_id": self.decision.decision_id,
            "agent_id": self.decision.agent_id,
            "task_id": self.decision.task_id,
            "applicable_authority": self.decision.applicable_authority,
            "scope_candidate": self.scope_candidate,
            "outcome_status": self.outcome_status,
            "evidence_ids": evidence_ids,
        }


class ExperienceAttribution(StrictModel):
    attribution_id: str = Field(default_factory=lambda: new_id("attribution"))
    record_id: str
    decision_id: str
    attribution_class: AttributionClass
    scope_candidate: ExperienceScopeCandidate
    authority_basis: ApplicableAuthority
    authority_refs: list[str] = Field(default_factory=list)
    non_repeat_candidate: bool = False
    invariant_candidate: bool = False
    skill_candidate: bool = False
    approved_experiment_exclusion: bool = False
    needs_owner_review: bool = False
    confidence: float = Field(ge=0.0, le=1.0)
    receipt_summary: str = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)
    created_at: datetime = Field(default_factory=utc_now)

    def audit_summary(self) -> dict[str, object]:
        return {
            "attribution_id": self.attribution_id,
            "record_id": self.record_id,
            "decision_id": self.decision_id,
            "attribution_class": self.attribution_class,
            "scope_candidate": self.scope_candidate,
            "authority_basis": self.authority_basis,
            "non_repeat_candidate": self.non_repeat_candidate,
            "invariant_candidate": self.invariant_candidate,
            "skill_candidate": self.skill_candidate,
            "approved_experiment_exclusion": self.approved_experiment_exclusion,
            "needs_owner_review": self.needs_owner_review,
            "confidence": self.confidence,
            "evidence_ids": self.evidence_ids,
        }


InvariantEnforcement = Literal["steer", "block", "steer_or_block"]
SupersessionStatus = Literal["active", "superseded", "retired"]
SkillPromotionStatus = Literal["candidate", "verified", "rejected"]
SituationSourceType = Literal["invariant", "skill"]
SituationMatchType = Literal[
    "exact_repeat",
    "paraphrase_repeat",
    "skill_transfer",
    "valid_neighbor",
    "no_match",
]
PolicyVerdict = Literal[
    "allow",
    "steer",
    "warn",
    "ask",
    "block",
    "override_allowed",
    "degraded_allow",
]
BoundaryStatus = Literal["interceptable", "non_interceptable", "unknown"]
AMSEffect = Literal["none", "changed_action", "blocked_action", "visible_intervention", "override"]


class BehaviorInvariant(StrictModel):
    invariant_id: str = Field(default_factory=lambda: new_id("invariant"))
    source_attribution_id: str
    source_record_id: str
    authority: ApplicableAuthority
    scope: ExperienceScopeCandidate
    trigger: str = Field(min_length=1)
    forbidden_repeat: str = Field(min_length=1)
    corrected_action: str = Field(min_length=1)
    enforcement: InvariantEnforcement
    evidence_ids: list[str] = Field(min_length=1)
    supersession_status: SupersessionStatus = "active"
    created_at: datetime = Field(default_factory=utc_now)

    def audit_summary(self) -> dict[str, object]:
        return {
            "invariant_id": self.invariant_id,
            "source_attribution_id": self.source_attribution_id,
            "source_record_id": self.source_record_id,
            "authority": self.authority,
            "scope": self.scope,
            "enforcement": self.enforcement,
            "evidence_ids": self.evidence_ids,
            "supersession_status": self.supersession_status,
        }


class SkillCandidate(StrictModel):
    skill_id: str = Field(default_factory=lambda: new_id("skill"))
    source_attribution_id: str
    source_record_id: str
    transfer_scope: ExperienceScopeCandidate
    preconditions: list[str] = Field(default_factory=list)
    procedure: list[str] = Field(min_length=1)
    expected_result: str = Field(min_length=1)
    failure_boundaries: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(min_length=1)
    when_not_to_apply: list[str] = Field(default_factory=list)
    promotion_status: SkillPromotionStatus = "candidate"
    created_at: datetime = Field(default_factory=utc_now)

    def audit_summary(self) -> dict[str, object]:
        return {
            "skill_id": self.skill_id,
            "source_attribution_id": self.source_attribution_id,
            "source_record_id": self.source_record_id,
            "transfer_scope": self.transfer_scope,
            "promotion_status": self.promotion_status,
            "evidence_ids": self.evidence_ids,
        }


class SituationMatch(StrictModel):
    match_id: str = Field(default_factory=lambda: new_id("match"))
    decision_id: str
    source_id: str
    source_type: SituationSourceType
    match_type: SituationMatchType
    fires: bool
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)
    created_at: datetime = Field(default_factory=utc_now)

    def audit_summary(self) -> dict[str, object]:
        return {
            "match_id": self.match_id,
            "decision_id": self.decision_id,
            "source_id": self.source_id,
            "source_type": self.source_type,
            "match_type": self.match_type,
            "fires": self.fires,
            "confidence": self.confidence,
            "reason": self.reason,
            "evidence_ids": self.evidence_ids,
        }


class RuntimeInterceptionBoundary(StrictModel):
    boundary_id: str = Field(default_factory=lambda: new_id("boundary"))
    action_kind: ActionKind
    runtime_surface: str = Field(min_length=1)
    interceptable: bool
    supported_verdicts: list[PolicyVerdict] = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)
    created_at: datetime = Field(default_factory=utc_now)


class ActionDecisionReceipt(StrictModel):
    receipt_id: str = Field(default_factory=lambda: new_id("receipt"))
    decision_id: str
    original_action: str = Field(min_length=1)
    action_to_execute: str | None = None
    verdict: PolicyVerdict
    downstream_action_allowed: bool
    user_visible: bool
    boundary_status: BoundaryStatus
    boundary_id: str | None = None
    match_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    reason: str = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)
    created_at: datetime = Field(default_factory=utc_now)

    def audit_summary(self) -> dict[str, object]:
        return {
            "receipt_id": self.receipt_id,
            "decision_id": self.decision_id,
            "verdict": self.verdict,
            "downstream_action_allowed": self.downstream_action_allowed,
            "user_visible": self.user_visible,
            "boundary_status": self.boundary_status,
            "boundary_id": self.boundary_id,
            "match_ids": self.match_ids,
            "source_ids": self.source_ids,
            "evidence_ids": self.evidence_ids,
        }


class ReasoningControlReceipt(StrictModel):
    reasoning_receipt_id: str = Field(default_factory=lambda: new_id("reasoning"))
    action_receipt_id: str
    original_verdict: PolicyVerdict
    final_verdict: PolicyVerdict
    ams_effect: AMSEffect
    matched_experience_ids: list[str] = Field(default_factory=list)
    authority: ApplicableAuthority | None = None
    user_visible: bool
    receipt_available: bool = True
    downgrade_allowed: bool = False
    override_receipt_required: bool = False
    summary: str = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)
    created_at: datetime = Field(default_factory=utc_now)

    def audit_summary(self) -> dict[str, object]:
        return {
            "reasoning_receipt_id": self.reasoning_receipt_id,
            "action_receipt_id": self.action_receipt_id,
            "original_verdict": self.original_verdict,
            "final_verdict": self.final_verdict,
            "ams_effect": self.ams_effect,
            "matched_experience_ids": self.matched_experience_ids,
            "authority": self.authority,
            "user_visible": self.user_visible,
            "receipt_available": self.receipt_available,
            "downgrade_allowed": self.downgrade_allowed,
            "override_receipt_required": self.override_receipt_required,
            "evidence_ids": self.evidence_ids,
        }


class ExperienceAtom(StrictModel):
    atom_id: str = Field(default_factory=lambda: new_id("atom"))
    source_trace_ids: list[str]
    source_turn_ids: list[str]
    source_spans: list[SourceSpan]
    source_artifacts: list[str] = Field(default_factory=list)
    source_agent_id: str
    source_session_id: str
    extracted_by_model: str
    extraction_prompt_version: str
    epistemic_type: Literal[
        "observation",
        "user_claim",
        "tool_output",
        "assistant_hypothesis",
        "derived_claim",
        "preference",
        "instruction",
        "skill",
        "failure_mode",
        "contradiction",
        "invalidation_event",
    ]
    content: str
    domain_scope: str | None = None
    task_family: str | None = None
    state_preconditions: list[str] = Field(default_factory=list)
    action_or_strategy: str | None = None
    observed_outcome: str | None = None
    causal_hypothesis: str | None = None
    observed_at: datetime = Field(default_factory=utc_now)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    superseded_by: list[str] = Field(default_factory=list)
    last_confirmed_at: datetime | None = None
    confidence_score: float = 0.5
    support_count: int = 1
    contradiction_links: list[str] = Field(default_factory=list)
    exception_boundary: list[str] = Field(default_factory=list)
    retrieval_cues: list[str] = Field(default_factory=list)
    recommended_use: str | None = None
    verification_probe_ids: list[str] = Field(default_factory=list)
    promotion_status: Literal[
        "proposed",
        "candidate",
        "verified",
        "deprecated",
        "quarantined",
    ] = "proposed"
    quarantine_reason: str | None = None


class ExperienceCard(StrictModel):
    card_id: str = Field(default_factory=lambda: new_id("card"))
    title: str
    use_when: str
    do: list[str] = Field(default_factory=list)
    do_not: list[str] = Field(default_factory=list)
    check_first: list[str] = Field(default_factory=list)
    evidence_atom_ids: list[str]
    confidence_score: float
    known_exceptions: list[str] = Field(default_factory=list)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    tested_by_probe_ids: list[str] = Field(default_factory=list)
    last_validated_at: datetime | None = None
    action_brief_template: str
    promotion_status: Literal[
        "candidate",
        "verified",
        "deprecated",
        "superseded",
        "quarantined",
    ] = "candidate"
    measured_lift: float | None = None
    measured_lift_ci: ConfidenceInterval | None = None
    verification_result_ids: list[str] = Field(default_factory=list)
    deactivated_at: datetime | None = None
    deactivated_reason: str | None = None
    superseded_by_card_ids: list[str] = Field(default_factory=list)
    contradicts_card_ids: list[str] = Field(default_factory=list)

    @field_validator("valid_from", "valid_until")
    @classmethod
    def _ensure_utc_aware(cls, value: datetime | None) -> datetime | None:
        # Coerce naive validity bounds (legacy storage / external writes) to UTC
        # so _card_in_scope can compare them against an offset-aware current_time.
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


class TaskContext(StrictModel):
    task_id: str | None = None
    session_id: str | None = None
    description: str
    domain_scope: str | None = None
    task_family: str | None = None
    current_time: datetime = Field(default_factory=utc_now)

    @field_validator("current_time")
    @classmethod
    def _ensure_utc_aware(cls, value: datetime) -> datetime:
        # A client (MCP/CLI) may supply current_time as a tz-less ISO string,
        # which parses offset-naive. Card validity bounds are offset-aware
        # (utc_now), so coerce naive input to UTC to keep scope comparisons valid.
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


class ActionBrief(StrictModel):
    task_id: str | None = None
    applicable_card_ids: list[str]
    why_applicable: list[str]
    preconditions_to_check: list[str]
    recommended_next_actions: list[str]
    risks_and_failure_modes: list[str]
    stale_or_contested_memory_ids_to_ignore: list[str]
    evidence_links: list[str]
    confidence_score: float
    expected_action_delta: float | None = None
    brief_id: str = Field(default_factory=lambda: new_id("brief"))
    influence_id: str | None = None
    scorer_version: str | None = None
    expected_action_delta_source: ExpectedActionDeltaSource = "none"
    score_breakdown_by_card: dict[str, dict[str, float]] = Field(default_factory=dict)


class TraceReceipt(StrictModel):
    trace_id: str
    turn_count: int
    stored_at: datetime = Field(default_factory=utc_now)


class ValidationResult(StrictModel):
    atom_id: str
    check_name: str
    passed: bool
    reason: str
    created_at: datetime = Field(default_factory=utc_now)


class ValidationDecision(StrictModel):
    atom_id: str
    decision: Literal["candidate", "quarantined"]
    reason_codes: list[str] = Field(default_factory=list)
    metric_labels: list[str] = Field(default_factory=list)
    explanation: str
    contradiction_links: list[str] = Field(default_factory=list)
    confidence_score: float
    validation_results: list[ValidationResult]
    created_at: datetime = Field(default_factory=utc_now)


class MemoryAudit(StrictModel):
    memory_id: str
    memory_kind: Literal["atom", "card"]
    source_trace_ids: list[str]
    source_turn_ids: list[str]
    source_agent_ids: list[str]
    source_session_ids: list[str]
    confidence_score: float
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    evidence_atom_count: int
    validation_check_names: list[str]
    validation_results: list[ValidationResult]
    validation_decision: ValidationDecision | None = None
    promotion_status: str
    quarantine_reason: str | None = None


class VerificationProbe(StrictModel):
    probe_id: str = Field(default_factory=lambda: new_id("probe"))
    kind: Literal["held_out_replay", "staleness", "contradiction", "negative_control"]
    target_card_id: str | None = None
    target_atom_id: str | None = None
    control_definition: str
    threshold: float
    status: Literal["scheduled", "run", "skipped"] = "scheduled"
    created_at: datetime = Field(default_factory=utc_now)


class VerificationResult(StrictModel):
    result_id: str = Field(default_factory=lambda: new_id("vresult"))
    probe_id: str
    card_id: str
    measured_lift: float
    measured_lift_ci: ConfidenceInterval | None = None
    passed: bool
    evidence_pointer: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class ActionBriefRecord(StrictModel):
    brief_id: str = Field(default_factory=lambda: new_id("brief"))
    task_id: str | None = None
    candidate_card_ids: list[str] = Field(default_factory=list)
    selected_card_ids: list[str] = Field(default_factory=list)
    score_breakdown_by_card: dict[str, dict[str, float]] = Field(default_factory=dict)
    scorer_version: str
    expected_action_delta_source: ExpectedActionDeltaSource = "none"
    influence_id: str
    created_at: datetime = Field(default_factory=utc_now)


class ActionInfluenceEvent(StrictModel):
    influence_id: str
    brief_id: str
    task_id: str | None = None
    action_taken: str | None = None
    outcome: Literal["success", "failure", "partial", "unknown"] = "unknown"
    observed_post_brief_delta: float | None = None
    counterfactual_method: str | None = None
    baseline_comparison: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
