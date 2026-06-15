from __future__ import annotations

import re
from dataclasses import dataclass

from .models import BehaviorInvariant, DecisionIntent, SituationMatch, SkillCandidate

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "before",
    "is",
    "it",
    "of",
    "or",
    "the",
    "this",
    "to",
}
_GENERAL_BEHAVIOR_MARKERS = (
    "general behavior",
    "general codex",
    "codex/ams",
    "ams correction",
    "not-waki",
    "not waki",
    "control-plane",
)
_PROJECT_NEIGHBOR_MARKERS = (
    "project-specific",
    "dataset review question",
    "implementation issue",
)


@dataclass(frozen=True)
class SituationMatcher:
    def match_decision(
        self,
        decision: DecisionIntent,
        *,
        invariants: list[BehaviorInvariant],
        skills: list[SkillCandidate],
    ) -> list[SituationMatch]:
        matches: list[SituationMatch] = []
        for invariant in invariants:
            matches.append(self._match_invariant(decision, invariant))
        for skill in skills:
            matches.append(self._match_skill(decision, skill))
        return matches

    def _match_invariant(self, decision: DecisionIntent, invariant: BehaviorInvariant) -> SituationMatch:
        decision_text = decision.proposed_action
        if _owner_approved_changed_context(decision):
            return _match(
                decision,
                source_id=invariant.invariant_id,
                source_type="invariant",
                match_type="valid_neighbor",
                fires=False,
                confidence=0.9,
                reason="owner-approved changed context suppresses invariant firing",
                evidence_ids=invariant.evidence_ids,
            )

        if _valid_project_neighbor(decision_text):
            return _match(
                decision,
                source_id=invariant.invariant_id,
                source_type="invariant",
                match_type="valid_neighbor",
                fires=False,
                confidence=0.86,
                reason="project-specific valid neighbor does not match global behavior invariant",
                evidence_ids=invariant.evidence_ids,
            )

        if _normalize(decision_text) == _normalize(invariant.forbidden_repeat):
            return _match(
                decision,
                source_id=invariant.invariant_id,
                source_type="invariant",
                match_type="exact_repeat",
                fires=True,
                confidence=1.0,
                reason="exact repeat of forbidden invariant action",
                evidence_ids=invariant.evidence_ids,
            )

        similarity = _similarity(decision_text, invariant.forbidden_repeat)
        if _paraphrased_general_behavior_repeat(decision_text, invariant) or similarity >= 0.62:
            return _match(
                decision,
                source_id=invariant.invariant_id,
                source_type="invariant",
                match_type="paraphrase_repeat",
                fires=True,
                confidence=max(0.72, min(0.94, similarity + 0.25)),
                reason="paraphrase repeat matched invariant markers and shared action terms",
                evidence_ids=invariant.evidence_ids,
            )

        return _match(
            decision,
            source_id=invariant.invariant_id,
            source_type="invariant",
            match_type="no_match",
            fires=False,
            confidence=0.0,
            reason="decision did not match invariant trigger",
            evidence_ids=invariant.evidence_ids,
        )

    def _match_skill(self, decision: DecisionIntent, skill: SkillCandidate) -> SituationMatch:
        preconditions_hold = _skill_preconditions_hold(decision, skill)
        procedure_text = " ".join(skill.procedure)
        procedure_match = _normalize(decision.proposed_action) == _normalize(procedure_text)
        similarity = _similarity(decision.proposed_action, procedure_text)

        if not preconditions_hold:
            return _match(
                decision,
                source_id=skill.skill_id,
                source_type="skill",
                match_type="valid_neighbor",
                fires=False,
                confidence=0.88,
                reason="skill procedure is similar but required precondition is not satisfied",
                evidence_ids=skill.evidence_ids,
            )

        if procedure_match or similarity >= 0.58:
            return _match(
                decision,
                source_id=skill.skill_id,
                source_type="skill",
                match_type="skill_transfer",
                fires=True,
                confidence=1.0 if procedure_match else max(0.7, similarity),
                reason="skill preconditions and procedure match the decision",
                evidence_ids=skill.evidence_ids,
            )

        return _match(
            decision,
            source_id=skill.skill_id,
            source_type="skill",
            match_type="no_match",
            fires=False,
            confidence=0.0,
            reason="decision did not match skill procedure",
            evidence_ids=skill.evidence_ids,
        )


def _match(
    decision: DecisionIntent,
    *,
    source_id: str,
    source_type: str,
    match_type: str,
    fires: bool,
    confidence: float,
    reason: str,
    evidence_ids: list[str],
) -> SituationMatch:
    return SituationMatch(
        decision_id=decision.decision_id,
        source_id=source_id,
        source_type=source_type,
        match_type=match_type,
        fires=fires,
        confidence=confidence,
        reason=reason,
        evidence_ids=[*decision.evidence_ids, *evidence_ids],
    )


def _owner_approved_changed_context(decision: DecisionIntent) -> bool:
    return decision.approval_state == "owner_approved" and "changed context" in decision.proposed_action.lower()


def _valid_project_neighbor(text: str) -> bool:
    lower = text.lower()
    has_project_marker = any(marker in lower for marker in _PROJECT_NEIGHBOR_MARKERS) or "waki" in lower
    has_general_marker = any(marker in lower for marker in _GENERAL_BEHAVIOR_MARKERS)
    has_correction_marker = "correction" in lower or "scope" in lower or "scop" in lower
    return has_project_marker and not has_general_marker and not has_correction_marker


def _paraphrased_general_behavior_repeat(text: str, invariant: BehaviorInvariant) -> bool:
    lower = text.lower()
    invariant_text = f"{invariant.forbidden_repeat} {invariant.corrected_action}".lower()
    return (
        invariant.scope == "global_agent_behavior"
        and any(marker in lower for marker in _GENERAL_BEHAVIOR_MARKERS)
        and ("waki-specific" in lower or "project-specific" in lower or "implementation task" in lower)
        and ("general" in invariant_text or "codex/ams" in invariant_text)
    )


def _skill_preconditions_hold(decision: DecisionIntent, skill: SkillCandidate) -> bool:
    for precondition in skill.preconditions:
        if precondition.startswith("authority_basis="):
            expected = precondition.split("=", 1)[1]
            if decision.applicable_authority != expected:
                return False
        elif precondition.startswith("runtime_surface="):
            expected = precondition.split("=", 1)[1]
            if decision.runtime_surface != expected:
                return False
    return True


def _normalize(text: str) -> str:
    return " ".join(_tokens(text))


def _tokens(text: str) -> set[str]:
    return {token for token in _TOKEN_RE.findall(text.lower()) if token not in _STOPWORDS}


def _similarity(left: str, right: str) -> float:
    left_tokens = _tokens(left)
    right_tokens = _tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
