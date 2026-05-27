from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from .models import ExperienceAtom


@dataclass(frozen=True)
class ContradictionMatch:
    conflicting_atom_ids: list[str]
    reason: str


class ContradictionDetector(Protocol):
    def find_conflicts(
        self,
        atom: ExperienceAtom,
        active_atoms: Sequence[ExperienceAtom],
    ) -> ContradictionMatch | None: ...


class KeyValueContradictionDetector:
    """Deterministic V0 detector for fixture-friendly key/value claims."""

    def find_conflicts(
        self,
        atom: ExperienceAtom,
        active_atoms: Sequence[ExperienceAtom],
    ) -> ContradictionMatch | None:
        key, value = contradiction_pair(atom.content)
        if key is None:
            return None

        conflicting_ids: list[str] = []
        for other in active_atoms:
            if not _same_operational_scope(atom, other):
                continue
            other_key, other_value = contradiction_pair(other.content)
            if other_key == key and other_value != value:
                conflicting_ids.append(other.atom_id)

        if not conflicting_ids:
            return None

        return ContradictionMatch(
            conflicting_atom_ids=sorted(set(conflicting_ids)),
            reason=f"contradicts active memory for key '{key}'",
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


def _same_operational_scope(left: ExperienceAtom, right: ExperienceAtom) -> bool:
    if left.domain_scope and right.domain_scope and left.domain_scope != right.domain_scope:
        return False
    if left.task_family and right.task_family and left.task_family != right.task_family:
        return False
    return True
