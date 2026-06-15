from __future__ import annotations

import re

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


class NaturalLanguageExtractor:
    """Grounded natural-language extractor for non-fixture benchmark lanes.

    The deterministic marker extractor remains the exact fixture path. This
    extractor delegates marked turns to it unchanged, then applies conservative
    span-preserving heuristics to unmarked natural-language traces so external
    benchmark runners have a real write path without model credentials.
    """

    def __init__(
        self,
        *,
        model_name: str = "natural-language-heuristic-extractor",
        prompt_version: str = "cem-natural-language-v1",
        marker_extractor: DeterministicExtractor | None = None,
    ) -> None:
        self.model_name = model_name
        self.prompt_version = prompt_version
        self.marker_extractor = marker_extractor or DeterministicExtractor()

    def extract(self, trace: AgentTrace) -> list[ExperienceAtom]:
        atoms: list[ExperienceAtom] = []
        seen: set[str] = set()
        for turn in trace.turns:
            marker_atoms = self.marker_extractor._extract_turn(trace, turn)
            if marker_atoms:
                for atom in marker_atoms:
                    seen.add(atom.content.lower())
                atoms.extend(marker_atoms)
                continue
            for candidate in _natural_candidates(turn):
                content = candidate.content.strip()
                if not content:
                    continue
                dedupe_key = content.lower()
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                source_span = SourceSpan(
                    turn_id=turn.turn_id,
                    start=candidate.start,
                    end=candidate.end,
                    text=turn.content[candidate.start : candidate.end],
                )
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
                        epistemic_type=candidate.epistemic_type,
                        content=content,
                        domain_scope=str(trace.environment.get("domain", "")) or None,
                        task_family=trace.task_id,
                        observed_at=turn.timestamp,
                        confidence_score=candidate.confidence,
                        retrieval_cues=_cue_terms(content),
                        state_preconditions=_extract_preconditions(content),
                        action_or_strategy=_extract_action(content)
                        or (content if candidate.epistemic_type == "skill" else None),
                        observed_outcome=trace.final_outcome,
                        causal_hypothesis=content if candidate.epistemic_type in {"skill", "failure_mode"} else None,
                    )
                )
        return atoms


class _NaturalCandidate:
    def __init__(
        self,
        *,
        content: str,
        start: int,
        end: int,
        epistemic_type: str,
        confidence: float,
    ) -> None:
        self.content = content
        self.start = start
        self.end = end
        self.epistemic_type = epistemic_type
        self.confidence = confidence


_KEY_VALUE_RE = re.compile(r"(?<![\w.-])([A-Za-z][\w.-]{1,40})\s*=\s*([^\s,.;:]+)")
_ANSWER_RE = re.compile(r"(?im)^\s*ANSWER:\s*(?P<answer>.+?)\s*$")
_PREFERENCE_RE = re.compile(
    r"\b(?:I|we|user)\s+(?:prefer|prefers|like|likes|love|loves|want|wants)\s+(?P<preference>[^.\n;]+)",
    re.IGNORECASE,
)
_IS_RE = re.compile(
    r"\b(?P<subject>(?:my|the|this|that|user|agent)?\s*[A-Za-z][\w_ -]{1,40})\s+is\s+(?P<object>[^.\n;]+)",
    re.IGNORECASE,
)
_ACTION_PREFIXES = (
    "approve",
    "book",
    "buy",
    "check",
    "choose",
    "click",
    "find",
    "navigate",
    "open",
    "run",
    "search",
    "select",
    "set",
    "submit",
    "use",
)
_NON_MEMORY_PREFIXES = (
    "accessibility_tree:",
    "goal:",
    "screenshot:",
    "start_url:",
    "url:",
)


def _natural_candidates(turn: TraceTurn) -> list[_NaturalCandidate]:
    candidates: list[_NaturalCandidate] = []
    candidates.extend(_answer_candidates(turn.content))
    candidates.extend(_key_value_candidates(turn.content))
    candidates.extend(_preference_candidates(turn.content))
    candidates.extend(_is_candidates(turn.content))
    candidates.extend(_action_candidates(turn))
    return _dedupe_candidates(candidates)


def _answer_candidates(content: str) -> list[_NaturalCandidate]:
    candidates: list[_NaturalCandidate] = []
    for match in _ANSWER_RE.finditer(content):
        start = match.start("answer")
        end = match.end("answer")
        answer = content[start:end].strip()
        if answer:
            candidates.append(
                _NaturalCandidate(
                    content=answer,
                    start=start,
                    end=end,
                    epistemic_type="tool_output",
                    confidence=0.8,
                )
            )
    return candidates


def _key_value_candidates(content: str) -> list[_NaturalCandidate]:
    candidates: list[_NaturalCandidate] = []
    for match in _KEY_VALUE_RE.finditer(content):
        start = match.start()
        end = match.end()
        key = match.group(1).strip()
        value = match.group(2).strip()
        if key and value:
            candidates.append(
                _NaturalCandidate(
                    content=f"{key}={value}",
                    start=start,
                    end=end,
                    epistemic_type="preference",
                    confidence=0.75,
                )
            )
    return candidates


def _preference_candidates(content: str) -> list[_NaturalCandidate]:
    candidates: list[_NaturalCandidate] = []
    for match in _PREFERENCE_RE.finditer(content):
        start = match.start("preference")
        end = match.end("preference")
        preference = content[start:end].strip()
        if preference:
            candidates.append(
                _NaturalCandidate(
                    content=preference,
                    start=start,
                    end=end,
                    epistemic_type="preference",
                    confidence=0.65,
                )
            )
    return candidates


def _is_candidates(content: str) -> list[_NaturalCandidate]:
    candidates: list[_NaturalCandidate] = []
    for match in _IS_RE.finditer(content):
        end = match.end()
        subject_prefix_length = _subject_prefix_length(match.group("subject"))
        start = match.start("subject") + subject_prefix_length
        statement = content[start:end].strip()
        subject = _clean_subject(match.group("subject"))
        if not subject or subject in {"this", "that", "it"}:
            continue
        candidates.append(
            _NaturalCandidate(
                content=statement,
                start=start,
                end=end,
                epistemic_type="observation",
                confidence=0.6,
            )
        )
    return candidates


def _action_candidates(turn: TraceTurn) -> list[_NaturalCandidate]:
    candidates: list[_NaturalCandidate] = []
    if turn.role not in {"assistant", "environment", "tool"}:
        return candidates
    search_from = 0
    for raw_line in turn.content.splitlines():
        stripped = raw_line.strip()
        start = turn.content.find(stripped, search_from)
        end = start + len(stripped)
        search_from += len(raw_line) + 1
        if not stripped or len(stripped) > 160:
            continue
        lower = stripped.lower()
        if lower.startswith(_NON_MEMORY_PREFIXES) or lower.startswith("answer:"):
            continue
        if lower.startswith(_ACTION_PREFIXES):
            candidates.append(
                _NaturalCandidate(
                    content=stripped,
                    start=start,
                    end=end,
                    epistemic_type="skill",
                    confidence=0.65,
                )
            )
    return candidates


def _dedupe_candidates(candidates: list[_NaturalCandidate]) -> list[_NaturalCandidate]:
    deduped: list[_NaturalCandidate] = []
    seen: set[tuple[int, int, str]] = set()
    for candidate in candidates:
        key = (candidate.start, candidate.end, candidate.content.lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def _clean_subject(value: str) -> str:
    subject = " ".join(value.lower().split())
    for prefix in ("my ", "the ", "this ", "that ", "user ", "agent "):
        if subject.startswith(prefix):
            subject = subject.removeprefix(prefix)
    return subject.strip()


def _subject_prefix_length(value: str) -> int:
    lower = value.lower()
    leading_spaces = len(value) - len(value.lstrip())
    stripped_lower = lower.lstrip()
    for prefix in ("my ", "the ", "this ", "that ", "user ", "agent "):
        if stripped_lower.startswith(prefix):
            return leading_spaces + len(prefix)
    return leading_spaces
