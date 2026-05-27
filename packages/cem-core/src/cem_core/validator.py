from __future__ import annotations

from datetime import timedelta

from .models import ExperienceAtom, ValidationResult, utc_now
from .storage import SQLiteStore


class MemoryValidator:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def validate(self, atom_id: str) -> list[ValidationResult]:
        atom = self.store.get_atom(atom_id)
        results = [
            self._source_span_check(atom),
            self._grounding_check(atom),
            self._epistemic_check(atom),
            self._confidence_check(atom),
        ]
        contradiction_result = self._contradiction_check(atom)
        results.append(contradiction_result)

        failed = [result for result in results if not result.passed]
        if failed:
            atom.promotion_status = "quarantined"
            atom.quarantine_reason = "; ".join(result.reason for result in failed)
        else:
            atom.promotion_status = "candidate"
            atom.valid_from = atom.valid_from or atom.observed_at
            atom.valid_until = atom.valid_until or _default_valid_until(atom)

        self.store.save_atom(atom)
        for result in results:
            self.store.save_validation(result)
        return results

    def _source_span_check(self, atom: ExperienceAtom) -> ValidationResult:
        passed = bool(atom.source_spans and atom.source_turn_ids and atom.source_trace_ids)
        return ValidationResult(
            atom_id=atom.atom_id,
            check_name="source_span_presence",
            passed=passed,
            reason="source spans present" if passed else "candidate has no source span evidence",
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

    def _contradiction_check(self, atom: ExperienceAtom) -> ValidationResult:
        key, value = contradiction_pair(atom.content)
        if key is None:
            return ValidationResult(
                atom_id=atom.atom_id,
                check_name="contradiction",
                passed=True,
                reason="no contradiction key detected",
            )

        conflicting_ids: list[str] = []
        for other in self.store.list_atoms():
            if other.atom_id == atom.atom_id or other.promotion_status == "quarantined":
                continue
            other_key, other_value = contradiction_pair(other.content)
            if other_key == key and other_value != value:
                conflicting_ids.append(other.atom_id)

        if conflicting_ids:
            atom.contradiction_links = sorted(set(atom.contradiction_links + conflicting_ids))
            self.store.save_atom(atom)
            return ValidationResult(
                atom_id=atom.atom_id,
                check_name="contradiction",
                passed=False,
                reason=f"contradicts active memory for key '{key}'",
            )

        return ValidationResult(
            atom_id=atom.atom_id,
            check_name="contradiction",
            passed=True,
            reason="no active contradiction detected",
        )


def contradiction_pair(content: str) -> tuple[str | None, str | None]:
    normalized = content.strip().lower()
    for separator in ("=", " is ", " -> "):
        if separator in normalized:
            left, right = normalized.split(separator, 1)
            key = left.strip(" .,:;")
            value = right.strip(" .,:;")
            if key and value:
                return key, value
    return None, None


def _default_valid_until(atom: ExperienceAtom):
    if atom.epistemic_type == "preference":
        return utc_now() + timedelta(days=180)
    if atom.epistemic_type == "instruction":
        return utc_now() + timedelta(days=365)
    return None
