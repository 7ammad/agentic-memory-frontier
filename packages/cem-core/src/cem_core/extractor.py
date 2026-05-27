from __future__ import annotations

from typing import Protocol

from .models import AgentTrace, ExperienceAtom, SourceSpan, TraceTurn

MARKERS = {
    "FACT:": "observation",
    "PREFERENCE:": "preference",
    "INSTRUCTION:": "instruction",
    "SKILL:": "skill",
    "FAILURE:": "failure_mode",
    "HYPOTHESIS:": "assistant_hypothesis",
    "UPDATE:": "invalidation_event",
}


class MemoryExtractor(Protocol):
    def extract(self, trace: AgentTrace) -> list[ExperienceAtom]: ...


class DeterministicExtractor:
    """Marker-based extractor for reproducible CEM-0 fixtures."""

    def __init__(
        self,
        *,
        model_name: str = "deterministic-marker-extractor",
        prompt_version: str = "cem-0-marker-v1",
    ) -> None:
        self.model_name = model_name
        self.prompt_version = prompt_version

    def extract(self, trace: AgentTrace) -> list[ExperienceAtom]:
        atoms: list[ExperienceAtom] = []
        for turn in trace.turns:
            atoms.extend(self._extract_turn(trace, turn))
        return atoms

    def _extract_turn(self, trace: AgentTrace, turn: TraceTurn) -> list[ExperienceAtom]:
        atoms: list[ExperienceAtom] = []
        search_from = 0
        for line in turn.content.splitlines():
            stripped = line.strip()
            marker = next((item for item in MARKERS if stripped.startswith(item)), None)
            if marker is None:
                search_from += len(line) + 1
                continue

            content = stripped.removeprefix(marker).strip()
            start = turn.content.find(content, search_from)
            end = start + len(content)
            source_span = SourceSpan(
                turn_id=turn.turn_id,
                start=start,
                end=end,
                text=content,
            )
            epistemic_type = MARKERS[marker]
            confidence = 0.35 if epistemic_type == "assistant_hypothesis" else 0.75
            atoms.append(
                ExperienceAtom(
                    source_trace_ids=[trace.trace_id],
                    source_turn_ids=[turn.turn_id],
                    source_spans=[source_span],
                    source_artifacts=turn.artifact_refs,
                    source_agent_id=trace.agent_id,
                    source_session_id=trace.session_id,
                    extracted_by_model=self.model_name,
                    extraction_prompt_version=self.prompt_version,
                    epistemic_type=epistemic_type,  # type: ignore[arg-type]
                    content=content,
                    domain_scope=str(trace.environment.get("domain", "")) or None,
                    task_family=trace.task_id,
                    observed_at=turn.timestamp,
                    confidence_score=confidence,
                    retrieval_cues=_cue_terms(content),
                    state_preconditions=_extract_preconditions(content),
                    action_or_strategy=_extract_action(content),
                    observed_outcome=trace.final_outcome,
                    causal_hypothesis=content if epistemic_type in {"skill", "failure_mode"} else None,
                )
            )
            search_from = end
        return atoms


def _cue_terms(content: str) -> list[str]:
    return sorted({term.strip(".,:;()[]").lower() for term in content.split() if len(term) > 3})


def _extract_preconditions(content: str) -> list[str]:
    lower = content.lower()
    if "unless" in lower:
        return [content[lower.index("unless") + len("unless") :].strip()]
    if "requires" in lower:
        return [content[lower.index("requires") + len("requires") :].strip()]
    return []


def _extract_action(content: str) -> str | None:
    lower = content.lower()
    for marker in ("do ", "select ", "set ", "avoid ", "check "):
        if lower.startswith(marker):
            return content
    return None
