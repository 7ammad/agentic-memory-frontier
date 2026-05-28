from __future__ import annotations

from pathlib import Path

from .contradiction import ContradictionDetector
from .extractor import DeterministicExtractor, MemoryExtractor
from .models import (
    ActionBrief,
    ActionBriefRecord,
    AgentTrace,
    ExperienceAtom,
    ExperienceCard,
    MemoryAudit,
    TaskContext,
    TraceReceipt,
    VerificationResult,
    new_id,
    utc_now,
)
from .storage import CEMStore, SQLiteStore
from .validator import MemoryValidator


class CEM:
    def __init__(
        self,
        root: str | Path | None = None,
        *,
        store: CEMStore | None = None,
        extractor: MemoryExtractor | None = None,
        contradiction_detector: ContradictionDetector | None = None,
    ) -> None:
        if store is not None and root is not None:
            raise ValueError("Pass either root or store, not both.")
        if store is None:
            if root is None:
                raise ValueError("CEM requires a storage root or a store backend.")
            store = SQLiteStore(Path(root))
        self.store = store
        self.extractor = extractor or DeterministicExtractor()
        self.validator = MemoryValidator(
            self.store,
            contradiction_detector=contradiction_detector,
        )

    def ingest_trace(self, trace: AgentTrace) -> TraceReceipt:
        self.store.save_trace(trace)
        return TraceReceipt(trace_id=trace.trace_id, turn_count=len(trace.turns))

    def propose_memories(
        self,
        trace_id: str,
        *,
        strategy: str = "all",
    ) -> list[ExperienceAtom]:
        trace = self.store.get_trace(trace_id)
        atoms = self.extractor.extract(trace)
        selected_atoms: list[ExperienceAtom] = []
        for atom in atoms:
            if strategy != "all" and atom.epistemic_type != strategy:
                continue
            self.store.save_atom(atom)
            selected_atoms.append(atom)
        return selected_atoms

    def validate(self, atom_id: str, *, checks: set[str] | None = None):
        if checks:
            raise NotImplementedError("Named validation subsets are not wired in CEM-0.")
        return self.validator.validate(atom_id)

    def promote(self, atom_id: str) -> ExperienceCard | None:
        atom = self.store.get_atom(atom_id)
        if atom.promotion_status == "proposed":
            self.validate(atom_id)
            atom = self.store.get_atom(atom_id)
        if atom.promotion_status == "quarantined":
            return None
        if atom.promotion_status not in {"candidate", "verified"}:
            return None

        existing = self._matching_card(atom)
        if existing is not None:
            if atom.atom_id not in existing.evidence_atom_ids:
                existing.evidence_atom_ids.append(atom.atom_id)
            existing.confidence_score = max(existing.confidence_score, atom.confidence_score)
            existing.last_validated_at = utc_now()
            atom.support_count = len(existing.evidence_atom_ids)
            self.store.save_atom(atom)
            self.store.save_card(existing)
            return existing

        card = ExperienceCard(
            title=_title(atom.content),
            use_when=atom.domain_scope or atom.task_family or "similar task context",
            do=[atom.action_or_strategy or atom.content],
            do_not=[],
            check_first=atom.state_preconditions,
            evidence_atom_ids=[atom.atom_id],
            confidence_score=atom.confidence_score,
            known_exceptions=atom.exception_boundary,
            valid_from=atom.valid_from,
            valid_until=atom.valid_until,
            tested_by_probe_ids=atom.verification_probe_ids,
            last_validated_at=utc_now(),
            action_brief_template=atom.recommended_use or atom.content,
        )
        self.store.save_atom(atom)
        self.store.save_card(card)
        return card

    def apply_verification_result(self, result: VerificationResult) -> ExperienceCard:
        card = self.store.get_card(result.card_id)
        self.store.save_verification_result(result)
        if result.result_id not in card.verification_result_ids:
            card.verification_result_ids.append(result.result_id)
        if result.passed:
            card.promotion_status = "verified"
            card.measured_lift = result.measured_lift
            card.measured_lift_ci = result.measured_lift_ci
            card.last_validated_at = utc_now()
        self.store.save_card(card)
        return card

    def retrieve_action_brief(self, task: TaskContext, *, max_cards: int = 5) -> ActionBrief:
        in_scope = [card for card in self.store.list_cards() if self._card_in_scope(card, task)]
        scored = sorted(
            ((score_card(card, task), card) for card in in_scope),
            key=lambda item: item[0],
            reverse=True,
        )
        selected = [(score, card) for score, card in scored if score > 0][:max_cards]
        selected_cards = [card for _, card in selected]
        confidence = max((card.confidence_score for card in selected_cards), default=0.0)
        score_breakdown = {
            card.card_id: {"lexical_overlap": float(score)} for score, card in selected
        }
        if selected_cards:
            expected_delta: float | None = confidence
            delta_source = "observational_unverified"
        else:
            expected_delta = None
            delta_source = "none"
        influence_id = new_id("influence")
        brief = ActionBrief(
            task_id=task.task_id,
            applicable_card_ids=[card.card_id for card in selected_cards],
            why_applicable=[f"matched task terms with '{card.title}'" for card in selected_cards],
            preconditions_to_check=[item for card in selected_cards for item in card.check_first],
            recommended_next_actions=[item for card in selected_cards for item in card.do],
            risks_and_failure_modes=[item for card in selected_cards for item in card.do_not],
            stale_or_contested_memory_ids_to_ignore=[],
            evidence_links=[
                atom_id for card in selected_cards for atom_id in card.evidence_atom_ids
            ],
            confidence_score=confidence,
            expected_action_delta=expected_delta,
            influence_id=influence_id,
            scorer_version=SCORER_VERSION,
            expected_action_delta_source=delta_source,
            score_breakdown_by_card=score_breakdown,
        )
        self.store.save_action_brief_record(
            ActionBriefRecord(
                brief_id=brief.brief_id,
                task_id=task.task_id,
                candidate_card_ids=[card.card_id for card in in_scope],
                selected_card_ids=brief.applicable_card_ids,
                score_breakdown_by_card=score_breakdown,
                scorer_version=SCORER_VERSION,
                expected_action_delta_source=delta_source,
                influence_id=influence_id,
            )
        )
        return brief

    def _card_in_scope(self, card: ExperienceCard, task: TaskContext) -> bool:
        if card.valid_from is not None and card.valid_from > task.current_time:
            return False
        if card.valid_until is not None and card.valid_until < task.current_time:
            return False

        if task.session_id is None:
            return True

        atoms = [self.store.get_atom(atom_id) for atom_id in card.evidence_atom_ids]
        if any(atom.source_session_id == task.session_id for atom in atoms):
            return True

        for atom in atoms:
            if task.domain_scope and atom.domain_scope == task.domain_scope:
                return True
            if task.task_family and atom.task_family == task.task_family:
                return True
        return False

    def audit(self, memory_id: str) -> MemoryAudit:
        try:
            atom = self.store.get_atom(memory_id)
            validations = self.store.list_validations(atom.atom_id)
            return MemoryAudit(
                memory_id=atom.atom_id,
                memory_kind="atom",
                source_trace_ids=atom.source_trace_ids,
                source_turn_ids=atom.source_turn_ids,
                source_agent_ids=[atom.source_agent_id],
                source_session_ids=[atom.source_session_id],
                confidence_score=atom.confidence_score,
                valid_from=atom.valid_from,
                valid_until=atom.valid_until,
                evidence_atom_count=1,
                validation_check_names=[result.check_name for result in validations],
                validation_results=validations,
                validation_decision=self.store.get_latest_validation_decision(atom.atom_id),
                promotion_status=atom.promotion_status,
                quarantine_reason=atom.quarantine_reason,
            )
        except KeyError:
            card = self.store.get_card(memory_id)
            validations = [
                result
                for atom_id in card.evidence_atom_ids
                for result in self.store.list_validations(atom_id)
            ]
            decisions = [
                decision
                for atom_id in card.evidence_atom_ids
                if (decision := self.store.get_latest_validation_decision(atom_id)) is not None
            ]
            atoms = [self.store.get_atom(atom_id) for atom_id in card.evidence_atom_ids]
            return MemoryAudit(
                memory_id=card.card_id,
                memory_kind="card",
                source_trace_ids=sorted({trace_id for atom in atoms for trace_id in atom.source_trace_ids}),
                source_turn_ids=sorted({turn_id for atom in atoms for turn_id in atom.source_turn_ids}),
                source_agent_ids=sorted({atom.source_agent_id for atom in atoms}),
                source_session_ids=sorted({atom.source_session_id for atom in atoms}),
                confidence_score=card.confidence_score,
                valid_from=card.valid_from,
                valid_until=card.valid_until,
                evidence_atom_count=len(card.evidence_atom_ids),
                validation_check_names=sorted({result.check_name for result in validations}),
                validation_results=validations,
                validation_decision=decisions[0] if len(decisions) == 1 else None,
                promotion_status=card.promotion_status,
                quarantine_reason=None,
            )

    def confirm(self, memory_id: str) -> None:
        atom = self.store.get_atom(memory_id)
        atom.promotion_status = "candidate"
        atom.quarantine_reason = None
        atom.last_confirmed_at = utc_now()
        self.store.save_atom(atom)

    def reject(self, memory_id: str, reason: str) -> None:
        atom = self.store.get_atom(memory_id)
        atom.promotion_status = "quarantined"
        atom.quarantine_reason = reason
        self.store.save_atom(atom)

    def _matching_card(self, atom: ExperienceAtom) -> ExperienceCard | None:
        title = _title(atom.content)
        use_when = atom.domain_scope or atom.task_family or "similar task context"
        for card in self.store.list_cards():
            if card.title == title and card.use_when == use_when:
                return card
        return None


def _title(content: str) -> str:
    cleaned = " ".join(content.split())
    return cleaned[:80]


SCORER_VERSION = "lexical_overlap_v0"


def score_card(card: ExperienceCard, task: TaskContext) -> int:
    haystack = " ".join([task.description, task.domain_scope or "", task.task_family or ""]).lower()
    needles = " ".join([card.title, card.use_when, card.action_brief_template]).lower().split()
    return sum(1 for term in set(needles) if len(term) > 3 and term.strip(".,:;") in haystack)
