from __future__ import annotations

from dataclasses import dataclass

from .models import ExperienceAttribution, ExperienceGraphRecord


V2_ATTRIBUTION_SEED_CORPUS = {
    "V2-SEED-001": "general behavior correction should classify as mistake and global_agent_behavior",
    "V2-SEED-004": "approved experiment failure should not become a mistake invariant",
    "V2-ATTR-TRADEOFF": "approved tradeoff should not become a mistake invariant",
    "V2-ATTR-SUCCESS": "successful reusable workflow should become a skill candidate",
    "V2-ATTR-UNRESOLVED": "low-authority failed outcome should stay unresolved",
}

_MISTAKE_AUTHORITIES = {
    "owner_instruction",
    "system_instruction",
    "developer_instruction",
    "project_docs",
    "verified_experience",
    "best_practice",
    "current_evidence",
    "logic",
}


@dataclass(frozen=True)
class ErrorAttributor:
    """Deterministic Phase 2 attribution for non-success outcomes."""

    def classify(self, record: ExperienceGraphRecord) -> ExperienceAttribution:
        if record.outcome_status == "success":
            return SuccessAttributor().classify(record)

        if _is_approved_experiment_failure(record):
            return _attribution(
                record,
                attribution_class="approved_experiment_failure",
                receipt_summary="Owner-approved experiment failed without becoming a mistake invariant.",
                approved_experiment_exclusion=True,
                confidence=0.95,
            )

        if _is_acceptable_tradeoff(record):
            return _attribution(
                record,
                attribution_class="acceptable_tradeoff",
                receipt_summary="Owner-approved tradeoff produced the known limitation without becoming a mistake invariant.",
                confidence=0.88,
            )

        if _is_unresolved(record):
            return _attribution(
                record,
                attribution_class="unresolved",
                receipt_summary="Outcome lacks enough authority evidence to classify as a mistake.",
                needs_owner_review=True,
                confidence=0.5,
            )

        return _attribution(
            record,
            attribution_class="mistake",
            receipt_summary="Outcome contradicted applicable authority and is a non-repeat candidate.",
            non_repeat_candidate=True,
            invariant_candidate=True,
            confidence=0.9,
        )


@dataclass(frozen=True)
class SuccessAttributor:
    """Deterministic Phase 2 attribution for successful outcomes."""

    def classify(self, record: ExperienceGraphRecord) -> ExperienceAttribution:
        if record.outcome_status != "success":
            return ErrorAttributor().classify(record)

        return _attribution(
            record,
            attribution_class="success",
            receipt_summary="Outcome matched the expected result and can be considered for skill transfer.",
            skill_candidate=True,
            confidence=0.86,
        )


def attribute_experience_record(record: ExperienceGraphRecord) -> ExperienceAttribution:
    if record.outcome_status == "success":
        return SuccessAttributor().classify(record)
    return ErrorAttributor().classify(record)


def _is_approved_experiment_failure(record: ExperienceGraphRecord) -> bool:
    return (
        record.outcome_status in {"failure", "partial"}
        and record.decision.experiment_state == "approved_experiment"
        and record.decision.approval_state == "owner_approved"
    )


def _is_acceptable_tradeoff(record: ExperienceGraphRecord) -> bool:
    text = " ".join(
        [
            record.decision.proposed_action,
            record.decision.expected_outcome,
            record.actual_outcome or "",
        ]
    ).lower()
    return (
        record.outcome_status in {"failure", "partial"}
        and record.decision.approval_state == "owner_approved"
        and record.decision.experiment_state == "not_experiment"
        and ("tradeoff" in text or "known limitation" in text)
    )


def _is_unresolved(record: ExperienceGraphRecord) -> bool:
    return (
        record.outcome_status == "unknown"
        or record.decision.applicable_authority == "unknown"
        or not record.decision.evidence_ids
        or record.decision.applicable_authority not in _MISTAKE_AUTHORITIES
    )


def _attribution(
    record: ExperienceGraphRecord,
    *,
    attribution_class: str,
    receipt_summary: str,
    non_repeat_candidate: bool = False,
    invariant_candidate: bool = False,
    skill_candidate: bool = False,
    approved_experiment_exclusion: bool = False,
    needs_owner_review: bool = False,
    confidence: float,
) -> ExperienceAttribution:
    return ExperienceAttribution(
        record_id=record.record_id,
        decision_id=record.decision.decision_id,
        attribution_class=attribution_class,
        scope_candidate=_resolved_scope_candidate(record),
        authority_basis=record.decision.applicable_authority,
        authority_refs=record.decision.authority_refs,
        non_repeat_candidate=non_repeat_candidate,
        invariant_candidate=invariant_candidate,
        skill_candidate=skill_candidate,
        approved_experiment_exclusion=approved_experiment_exclusion,
        needs_owner_review=needs_owner_review,
        confidence=confidence,
        receipt_summary=receipt_summary,
        evidence_ids=_evidence_ids(record),
    )


def _evidence_ids(record: ExperienceGraphRecord) -> list[str]:
    seen: set[str] = set()
    evidence_ids: list[str] = []
    for evidence_id in [*record.decision.evidence_ids, *record.outcome_evidence_ids]:
        if evidence_id not in seen:
            seen.add(evidence_id)
            evidence_ids.append(evidence_id)
    return evidence_ids or [record.record_id]


def _resolved_scope_candidate(record: ExperienceGraphRecord) -> str:
    text = " ".join(
        [
            record.decision.proposed_action,
            record.decision.expected_outcome,
            record.actual_outcome or "",
        ]
    ).lower()
    general_behavior_markers = (
        "general codex",
        "codex/ams behavior",
        "control-plane",
        "global behavior",
        "not waki",
        "not project-specific",
    )
    if any(marker in text for marker in general_behavior_markers):
        return "global_agent_behavior"
    return record.scope_candidate
