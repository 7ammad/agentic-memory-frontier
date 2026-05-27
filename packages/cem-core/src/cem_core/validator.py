from __future__ import annotations

from datetime import timedelta

from .contradiction import ContradictionDetector, KeyValueContradictionDetector
from .models import ExperienceAtom, ValidationDecision, ValidationResult, utc_now
from .storage import CEMStore


class MemoryValidator:
    def __init__(
        self,
        store: CEMStore,
        *,
        contradiction_detector: ContradictionDetector | None = None,
    ) -> None:
        self.store = store
        self.contradiction_detector = contradiction_detector or KeyValueContradictionDetector()

    def validate(self, atom_id: str) -> ValidationDecision:
        atom = self.store.get_atom(atom_id)
        results = [
            self._source_span_check(atom),
            self._source_agent_check(atom),
            self._grounding_check(atom),
            self._epistemic_check(atom),
            self._confidence_check(atom),
            self._causal_support_check(atom),
        ]
        contradiction_result = self._contradiction_check(atom)
        results.append(contradiction_result)

        decision = build_validation_decision(atom, results)
        if decision.decision == "quarantined":
            atom.promotion_status = "quarantined"
            atom.quarantine_reason = decision.explanation
        else:
            atom.promotion_status = "candidate"
            atom.quarantine_reason = None
            atom.valid_from = atom.valid_from or atom.observed_at
            atom.valid_until = atom.valid_until or _default_valid_until(atom)

        self.store.save_atom(atom)
        for result in results:
            self.store.save_validation(result)
        self.store.save_validation_decision(decision)
        return decision

    def _source_span_check(self, atom: ExperienceAtom) -> ValidationResult:
        passed = bool(atom.source_spans and atom.source_turn_ids and atom.source_trace_ids)
        return ValidationResult(
            atom_id=atom.atom_id,
            check_name="source_span_presence",
            passed=passed,
            reason="source spans present" if passed else "candidate has no source span evidence",
        )

    def _source_agent_check(self, atom: ExperienceAtom) -> ValidationResult:
        passed = not atom.source_agent_id.startswith("untrusted")
        return ValidationResult(
            atom_id=atom.atom_id,
            check_name="source_agent_trust",
            passed=passed,
            reason="source agent trusted" if passed else "source agent is not trusted for memory promotion",
        )

    def _grounding_check(self, atom: ExperienceAtom) -> ValidationResult:
        span_text = " ".join(span.text for span in atom.source_spans).lower()
        passed = atom.content.lower() in span_text or span_text in atom.content.lower()
        return ValidationResult(
            atom_id=atom.atom_id,
            check_name="source_grounding",
            passed=passed,
            reason="content grounded in cited span" if passed else "content is not grounded in cited span",
        )

    def _epistemic_check(self, atom: ExperienceAtom) -> ValidationResult:
        passed = atom.epistemic_type != "assistant_hypothesis"
        return ValidationResult(
            atom_id=atom.atom_id,
            check_name="epistemic_role",
            passed=passed,
            reason=(
                "epistemic role can be promoted"
                if passed
                else "assistant hypothesis requires independent evidence before promotion"
            ),
        )

    def _confidence_check(self, atom: ExperienceAtom) -> ValidationResult:
        passed = atom.confidence_score >= 0.5
        return ValidationResult(
            atom_id=atom.atom_id,
            check_name="confidence_floor",
            passed=passed,
            reason="confidence above floor" if passed else "confidence below promotion floor",
        )

    def _causal_support_check(self, atom: ExperienceAtom) -> ValidationResult:
        passed = (
            atom.epistemic_type != "derived_claim"
            or atom.causal_hypothesis is not None
            or bool(atom.verification_probe_ids)
        )
        return ValidationResult(
            atom_id=atom.atom_id,
            check_name="causal_support",
            passed=passed,
            reason=(
                "causal support not required or present"
                if passed
                else "derived claim lacks causal support or verification probe"
            ),
        )

    def _contradiction_check(self, atom: ExperienceAtom) -> ValidationResult:
        active_atoms = [
            other
            for other in self.store.list_atoms()
            if other.atom_id != atom.atom_id and other.promotion_status in {"candidate", "verified"}
        ]
        match = self.contradiction_detector.find_conflicts(atom, active_atoms)
        if match is None:
            return ValidationResult(
                atom_id=atom.atom_id,
                check_name="contradiction",
                passed=True,
                reason="no active contradiction detected",
            )

        atom.contradiction_links = sorted(set(atom.contradiction_links + match.conflicting_atom_ids))
        if atom.epistemic_type == "invalidation_event":
            self._supersede_conflicts(atom, match.conflicting_atom_ids)
            self.store.save_atom(atom)
            return ValidationResult(
                atom_id=atom.atom_id,
                check_name="temporal_supersession",
                passed=True,
                reason="supersedes stale active memory",
            )

        self.store.save_atom(atom)
        return ValidationResult(
            atom_id=atom.atom_id,
            check_name="contradiction",
            passed=False,
            reason=match.reason,
        )

    def _supersede_conflicts(self, atom: ExperienceAtom, conflicting_atom_ids: list[str]) -> None:
        for conflicting_atom_id in conflicting_atom_ids:
            other = self.store.get_atom(conflicting_atom_id)
            other.promotion_status = "deprecated"
            other.superseded_by = sorted(set(other.superseded_by + [atom.atom_id]))
            self.store.save_atom(other)


def build_validation_decision(
    atom: ExperienceAtom,
    results: list[ValidationResult],
) -> ValidationDecision:
    failed = [result for result in results if not result.passed]
    reason_codes = [_reason_code(result) for result in failed]
    metric_labels = sorted({_metric_label(code) for code in reason_codes})
    if failed:
        explanation = "quarantined: " + "; ".join(result.reason for result in failed)
        decision = "quarantined"
    else:
        explanation = "candidate: all validation checks passed"
        decision = "candidate"
    return ValidationDecision(
        atom_id=atom.atom_id,
        decision=decision,
        reason_codes=reason_codes,
        metric_labels=metric_labels,
        explanation=explanation,
        contradiction_links=atom.contradiction_links,
        confidence_score=atom.confidence_score,
        validation_results=results,
    )


def _reason_code(result: ValidationResult) -> str:
    if result.check_name == "source_span_presence":
        return "missing_source_span"
    if result.check_name == "source_grounding":
        return "unsupported"
    if result.check_name == "source_agent_trust":
        return "untrusted_source"
    if result.check_name == "epistemic_role":
        return "assistant_hypothesis"
    if result.check_name == "confidence_floor":
        return "low_confidence"
    if result.check_name == "causal_support":
        return "non_causal"
    if result.check_name == "contradiction":
        return "contradiction"
    return f"failed_{result.check_name}"


def _metric_label(reason_code: str) -> str:
    if reason_code in {"missing_source_span", "unsupported"}:
        return "unsupported"
    if reason_code == "assistant_hypothesis":
        return "assistant_hypothesis"
    if reason_code == "contradiction":
        return "contradiction"
    if reason_code == "untrusted_source":
        return "poisoned"
    if reason_code == "low_confidence":
        return "low_confidence"
    if reason_code == "non_causal":
        return "misleading_success"
    return "validation_failure"


def _default_valid_until(atom: ExperienceAtom):
    if atom.epistemic_type == "preference":
        return utc_now() + timedelta(days=180)
    if atom.epistemic_type == "instruction":
        return utc_now() + timedelta(days=365)
    return None
