from __future__ import annotations

from dataclasses import dataclass

from .models import BehaviorInvariant, SupersessionEvent


@dataclass(frozen=True)
class SupersessionLedger:
    def supersede_invariant(
        self,
        invariant: BehaviorInvariant,
        *,
        source: str,
        reason: str,
        evidence_ids: list[str],
    ) -> SupersessionEvent:
        invariant.supersession_status = "superseded"
        return SupersessionEvent(
            target_id=invariant.invariant_id,
            target_type="invariant",
            source=source,
            reason=reason,
            reversible=True,
            evidence_ids=_evidence_ids(invariant.invariant_id, invariant.evidence_ids, evidence_ids),
        )

    def reverse_invariant_supersession(
        self,
        invariant: BehaviorInvariant,
        event: SupersessionEvent,
        *,
        reason: str,
        evidence_ids: list[str],
    ) -> SupersessionEvent:
        invariant.supersession_status = "active"
        return SupersessionEvent(
            target_id=invariant.invariant_id,
            target_type="invariant",
            source="current_owner_instruction",
            reason=reason,
            reversible=True,
            reverses_supersession_id=event.supersession_id,
            evidence_ids=_evidence_ids(invariant.invariant_id, invariant.evidence_ids, evidence_ids),
        )

    def record_owner_override(
        self,
        invariant: BehaviorInvariant,
        *,
        reason: str,
        evidence_ids: list[str],
    ) -> SupersessionEvent:
        return self.supersede_invariant(
            invariant,
            source="owner_approved_override",
            reason=reason,
            evidence_ids=evidence_ids,
        )


def _evidence_ids(target_id: str, existing: list[str], incoming: list[str]) -> list[str]:
    seen: set[str] = set()
    evidence_ids: list[str] = []
    for evidence_id in [target_id, *existing, *incoming]:
        if evidence_id not in seen:
            seen.add(evidence_id)
            evidence_ids.append(evidence_id)
    return evidence_ids
