from __future__ import annotations

from pathlib import Path

from .contradiction import ContradictionDetector
from .extractor import DeterministicExtractor, MemoryExtractor
from .models import (
    ActionBrief,
    AgentTrace,
    ExperienceAtom,
    ExperienceCard,
    MemoryAudit,
    TaskContext,
    TraceReceipt,
    utc_now,
)
from .storage import SQLiteStore
from .validator import MemoryValidator


class CEM:
    def __init__(
        self,
        root: str | Path,
        *,
        extractor: MemoryExtractor | None = None,
        contradiction_detector: ContradictionDetector | None = None,
    ) -> None:
        self.store = SQLiteStore(Path(root))
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
            atom.promotion_status = "verified"
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
        atom.promotion_status = "verified"
        self.store.save_atom(atom)
        self.store.save_card(card)
        return card

    def retrieve_action_brief(self, task: TaskContext, *, max_cards: int = 5) -> ActionBrief:
        cards = self.store.list_cards()
        scored = sorted(
            ((score_card(card, task), card) for card in cards),
            key=lambda item: item[0],
            reverse=True,
        )
        selected = [card for score, card in scored if score > 0][:max_cards]
        confidence = max((card.confidence_score for card in selected), default=0.0)
        return ActionBrief(
            task_id=task.task_id,
            applicable_card_ids=[card.card_id for card in selected],
            why_applicable=[f"matched task terms with '{card.title}'" for card in selected],
            preconditions_to_check=[item for card in selected for item in card.check_first],
            recommended_next_actions=[item for card in selected for item in card.do],
            risks_and_failure_modes=[item for card in selected for item in card.do_not],
            stale_or_contested_memory_ids_to_ignore=[],
            evidence_links=[atom_id for card in selected for atom_id in card.evidence_atom_ids],
            confidence_score=confidence,
            expected_action_delta=None,
        )

    def audit(self, memory_id: str) -> MemoryAudit:
        try:
            atom = self.store.get_atom(memory_id)
            return MemoryAudit(
                memory_id=atom.atom_id,
                memory_kind="atom",
                source_trace_ids=atom.source_trace_ids,
                source_turn_ids=atom.source_turn_ids,
                validation_results=self.store.list_validations(atom.atom_id),
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
                validation_results=validations,
                validation_decision=decisions[0] if len(decisions) == 1 else None,
                promotion_status="verified",
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


def score_card(card: ExperienceCard, task: TaskContext) -> int:
    haystack = " ".join([task.description, task.domain_scope or "", task.task_family or ""]).lower()
    needles = " ".join([card.title, card.use_when, card.action_brief_template]).lower().split()
    return sum(1 for term in set(needles) if len(term) > 3 and term.strip(".,:;") in haystack)
