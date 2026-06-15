from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .models import (
    ActionDecisionReceipt,
    BehaviorInvariant,
    DecisionIntent,
    RuntimeInterceptionBoundary,
    SituationMatch,
    SkillCandidate,
)

if TYPE_CHECKING:
    from .kernel import CEM


@dataclass(frozen=True)
class PolicyBindingLayer:
    def decide(
        self,
        decision: DecisionIntent,
        *,
        matches: list[SituationMatch],
        invariants: list[BehaviorInvariant],
        skills: list[SkillCandidate],
        boundaries: list[RuntimeInterceptionBoundary],
    ) -> ActionDecisionReceipt:
        boundary = _boundary_for(decision, boundaries)
        fired = [match for match in matches if match.fires]
        if not fired:
            return _receipt(
                decision,
                verdict="allow",
                downstream_action_allowed=True,
                user_visible=False,
                boundary=boundary,
                matches=[],
                source_ids=[],
                action_to_execute=decision.proposed_action,
                reason="no active invariant or skill match fired",
            )

        if boundary is None or not boundary.interceptable:
            return _receipt(
                decision,
                verdict="degraded_allow",
                downstream_action_allowed=True,
                user_visible=True,
                boundary=boundary,
                matches=fired,
                source_ids=[match.source_id for match in fired],
                action_to_execute=decision.proposed_action,
                reason="matched policy but runtime boundary cannot intercept this action class",
            )

        invariant_by_id = {invariant.invariant_id: invariant for invariant in invariants}
        skill_by_id = {skill.skill_id: skill for skill in skills}

        invariant_match = next((match for match in fired if match.source_type == "invariant"), None)
        if invariant_match is not None:
            invariant = invariant_by_id[invariant_match.source_id]
            if invariant.enforcement == "block" or "steer" not in boundary.supported_verdicts:
                return _receipt(
                    decision,
                    verdict="block",
                    downstream_action_allowed=False,
                    user_visible=True,
                    boundary=boundary,
                    matches=[invariant_match],
                    source_ids=[invariant.invariant_id],
                    action_to_execute=None,
                    reason="blocked known repeat before downstream execution",
                )
            return _receipt(
                decision,
                verdict="steer",
                downstream_action_allowed=True,
                user_visible=False,
                boundary=boundary,
                matches=[invariant_match],
                source_ids=[invariant.invariant_id],
                action_to_execute=invariant.corrected_action,
                reason="silently steered known repeat to corrected action",
            )

        skill_match = next((match for match in fired if match.source_type == "skill"), None)
        if skill_match is not None:
            skill = skill_by_id[skill_match.source_id]
            return _receipt(
                decision,
                verdict="steer",
                downstream_action_allowed=True,
                user_visible=False,
                boundary=boundary,
                matches=[skill_match],
                source_ids=[skill.skill_id],
                action_to_execute=skill.procedure[0],
                reason="silently steered toward matched skill procedure",
            )

        return _receipt(
            decision,
            verdict="allow",
            downstream_action_allowed=True,
            user_visible=False,
            boundary=boundary,
            matches=fired,
            source_ids=[match.source_id for match in fired],
            action_to_execute=decision.proposed_action,
            reason="matches fired but no binding policy applied",
        )


@dataclass(frozen=True)
class ActionDecisionPoint:
    cem: CEM

    def decide(
        self,
        decision: DecisionIntent,
        *,
        boundaries: list[RuntimeInterceptionBoundary],
    ) -> ActionDecisionReceipt:
        for boundary in boundaries:
            self.cem.store.save_runtime_interception_boundary(boundary)
        matches = self.cem.match_situation(decision)
        receipt = PolicyBindingLayer().decide(
            decision,
            matches=matches,
            invariants=self.cem.store.list_behavior_invariants(),
            skills=self.cem.store.list_skill_candidates(),
            boundaries=boundaries,
        )
        self.cem.store.save_action_decision_receipt(receipt)
        return receipt


def _boundary_for(
    decision: DecisionIntent,
    boundaries: list[RuntimeInterceptionBoundary],
) -> RuntimeInterceptionBoundary | None:
    for boundary in boundaries:
        if boundary.action_kind == decision.action_kind and boundary.runtime_surface == decision.runtime_surface:
            return boundary
    return None


def _receipt(
    decision: DecisionIntent,
    *,
    verdict: str,
    downstream_action_allowed: bool,
    user_visible: bool,
    boundary: RuntimeInterceptionBoundary | None,
    matches: list[SituationMatch],
    source_ids: list[str],
    action_to_execute: str | None,
    reason: str,
) -> ActionDecisionReceipt:
    evidence_ids = _evidence_ids(decision, boundary, matches)
    return ActionDecisionReceipt(
        decision_id=decision.decision_id,
        original_action=decision.proposed_action,
        action_to_execute=action_to_execute,
        verdict=verdict,
        downstream_action_allowed=downstream_action_allowed,
        user_visible=user_visible,
        boundary_status=_boundary_status(boundary),
        boundary_id=boundary.boundary_id if boundary is not None else None,
        match_ids=[match.match_id for match in matches],
        source_ids=source_ids,
        reason=reason,
        evidence_ids=evidence_ids,
    )


def _boundary_status(boundary: RuntimeInterceptionBoundary | None) -> str:
    if boundary is None:
        return "unknown"
    if boundary.interceptable:
        return "interceptable"
    return "non_interceptable"


def _evidence_ids(
    decision: DecisionIntent,
    boundary: RuntimeInterceptionBoundary | None,
    matches: list[SituationMatch],
) -> list[str]:
    seen: set[str] = set()
    evidence_ids: list[str] = []
    for evidence_id in [
        *decision.evidence_ids,
        *(boundary.evidence_ids if boundary is not None else []),
        *[match.match_id for match in matches],
        *[evidence_id for match in matches for evidence_id in match.evidence_ids],
    ]:
        if evidence_id not in seen:
            seen.add(evidence_id)
            evidence_ids.append(evidence_id)
    return evidence_ids or [decision.decision_id]
