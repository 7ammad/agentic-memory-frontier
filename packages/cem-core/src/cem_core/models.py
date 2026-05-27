from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, TypeAlias
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

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


class TaskContext(StrictModel):
    task_id: str | None = None
    description: str
    domain_scope: str | None = None
    task_family: str | None = None
    current_time: datetime = Field(default_factory=utc_now)


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


class MemoryAudit(StrictModel):
    memory_id: str
    memory_kind: Literal["atom", "card"]
    source_trace_ids: list[str]
    source_turn_ids: list[str]
    validation_results: list[ValidationResult]
    promotion_status: str
    quarantine_reason: str | None = None
