from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .models import BehaviorInvariant, ExperienceAttribution, ExperienceGraphRecord, SkillCandidate

AuthorityLane = Literal[
    "current_owner_instruction",
    "system_instruction",
    "developer_instruction",
    "project_docs",
    "confirmed_behavior_invariant",
    "verified_experience_card",
    "best_practice_evidence",
    "learned_card",
    "current_task_context",
]

_AUTHORITY_RANK: dict[AuthorityLane, int] = {
    "current_owner_instruction": 0,
    "system_instruction": 1,
    "developer_instruction": 2,
    "project_docs": 3,
    "confirmed_behavior_invariant": 4,
    "verified_experience_card": 5,
    "best_practice_evidence": 6,
    "learned_card": 7,
    "current_task_context": 8,
}


@dataclass(frozen=True)
class AuthorityEvidence:
    evidence_id: str
    authority_lane: AuthorityLane
    content: str
    is_stale: bool = False


@dataclass(frozen=True)
class AuthorityScopeResolver:
    def choose_highest(self, evidence: list[AuthorityEvidence]) -> AuthorityEvidence:
        if not evidence:
            raise ValueError("authority evidence is required")
        return min(evidence, key=lambda item: (_AUTHORITY_RANK[item.authority_lane], item.is_stale))

    def promote_scope(self, scope: str, *, winning_authority: AuthorityLane, recurrence_count: int = 1) -> str:
        if winning_authority == "current_owner_instruction":
            return "global_agent_behavior"
        if recurrence_count >= 2:
            return "global_agent_behavior"
        return scope


@dataclass(frozen=True)
class BehaviorInvariantCompiler:
    def compile(
        self,
        record: ExperienceGraphRecord,
        attribution: ExperienceAttribution,
    ) -> BehaviorInvariant | None:
        if attribution.attribution_class != "mistake" or not attribution.invariant_candidate:
            return None

        return BehaviorInvariant(
            source_attribution_id=attribution.attribution_id,
            source_record_id=record.record_id,
            authority=attribution.authority_basis,
            scope=attribution.scope_candidate,
            trigger="equivalent situation match",
            forbidden_repeat=record.decision.proposed_action,
            corrected_action=record.decision.expected_outcome,
            enforcement="steer_or_block",
            evidence_ids=_evidence_ids(record, attribution),
        )


@dataclass(frozen=True)
class SkillCompiler:
    def compile(
        self,
        record: ExperienceGraphRecord,
        attribution: ExperienceAttribution,
    ) -> SkillCandidate | None:
        if attribution.attribution_class != "success" or not attribution.skill_candidate:
            return None

        return SkillCandidate(
            source_attribution_id=attribution.attribution_id,
            source_record_id=record.record_id,
            transfer_scope=attribution.scope_candidate,
            preconditions=[
                f"authority_basis={attribution.authority_basis}",
                f"runtime_surface={record.decision.runtime_surface}",
            ],
            procedure=[record.decision.proposed_action],
            expected_result=record.decision.expected_outcome,
            failure_boundaries=[
                "do not apply when approval state, authority, or runtime surface differs",
            ],
            evidence_ids=_evidence_ids(record, attribution),
            when_not_to_apply=[
                "missing authority evidence",
                "different runtime surface",
                "owner instruction supersedes this skill",
            ],
        )


def _evidence_ids(record: ExperienceGraphRecord, attribution: ExperienceAttribution) -> list[str]:
    seen: set[str] = set()
    evidence_ids: list[str] = []
    for evidence_id in [
        attribution.attribution_id,
        *attribution.evidence_ids,
        *record.decision.evidence_ids,
        *record.outcome_evidence_ids,
    ]:
        if evidence_id not in seen:
            seen.add(evidence_id)
            evidence_ids.append(evidence_id)
    return evidence_ids or [record.record_id]
