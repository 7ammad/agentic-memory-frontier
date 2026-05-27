from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from cem_core import AgentTrace, TraceTurn


class HaluMemMemoryPoint(BaseModel):
    user_id: str
    session_id: str
    index: str
    memory_content: str
    memory_type: str | None = None
    memory_source: str | None = None
    is_update: bool = False
    original_memories: list[str] = Field(default_factory=list)
    importance: float | None = None
    timestamp: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class HaluMemQuestion(BaseModel):
    user_id: str
    session_id: str
    question: str
    answer: str | None = None
    evidence_memory_contents: list[str] = Field(default_factory=list)
    difficulty: str | None = None
    question_type: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class HaluMemSession(BaseModel):
    user_id: str
    session_id: str
    dialogue: list[dict[str, Any]]
    memory_points: list[HaluMemMemoryPoint]
    questions: list[HaluMemQuestion]
    start_time: str | None = None
    end_time: str | None = None
    dialogue_token_length: int | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class HaluMemDataset(BaseModel):
    source_path: str
    sessions: list[HaluMemSession]

    @property
    def memory_points(self) -> list[HaluMemMemoryPoint]:
        return [point for session in self.sessions for point in session.memory_points]

    @property
    def questions(self) -> list[HaluMemQuestion]:
        return [question for session in self.sessions for question in session.questions]


class HaluMemDatasetSummary(BaseModel):
    source_path: str
    user_count: int
    session_count: int
    dialogue_turn_count: int
    memory_point_count: int
    update_memory_point_count: int
    qa_pair_count: int
    primary_memory_point_count: int
    interference_memory_point_count: int


class HaluMemExtractionScore(BaseModel):
    reference_memory_count: int
    candidate_memory_count: int
    matched_memory_count: int
    hallucinated_memory_count: int
    omitted_memory_count: int
    extraction_precision: float
    extraction_recall: float
    extraction_f1: float
    update_recall: float
    qa_evidence_recall: float


def load_halumem_dataset(path: str | Path) -> HaluMemDataset:
    source = Path(path)
    raw_users = _load_raw_records(source)
    sessions: list[HaluMemSession] = []
    for user_index, raw_user in enumerate(raw_users):
        sessions.extend(_sessions_from_user(raw_user, user_index))
    return HaluMemDataset(source_path=str(source), sessions=sessions)


def summarize_halumem_dataset(path: str | Path) -> HaluMemDatasetSummary:
    dataset = load_halumem_dataset(path)
    users = {session.user_id for session in dataset.sessions}
    memory_points = dataset.memory_points
    return HaluMemDatasetSummary(
        source_path=dataset.source_path,
        user_count=len(users),
        session_count=len(dataset.sessions),
        dialogue_turn_count=sum(len(session.dialogue) for session in dataset.sessions),
        memory_point_count=len(memory_points),
        update_memory_point_count=len([point for point in memory_points if point.is_update]),
        qa_pair_count=len(dataset.questions),
        primary_memory_point_count=len(
            [point for point in memory_points if (point.memory_source or "").lower() == "primary"]
        ),
        interference_memory_point_count=len(
            [point for point in memory_points if (point.memory_source or "").lower() == "interference"]
        ),
    )


def halumem_sessions_to_agent_traces(dataset: HaluMemDataset) -> list[AgentTrace]:
    traces: list[AgentTrace] = []
    for session in dataset.sessions:
        turns = [_turn_from_halumem_dialogue(index, item) for index, item in enumerate(session.dialogue)]
        traces.append(
            AgentTrace(
                trace_id=f"halumem-{_safe_id(session.session_id)}",
                session_id=session.session_id,
                agent_id="halumem-source",
                task_id="halumem-memory-session",
                turns=turns,
                final_outcome="unknown",
                environment={
                    "domain": "halumem",
                    "user_id": session.user_id,
                    "source_path": dataset.source_path,
                },
            )
        )
    return traces


def score_halumem_extraction(
    dataset: HaluMemDataset,
    candidates_by_session: Mapping[str, Sequence[str]],
) -> HaluMemExtractionScore:
    reference_by_session = {
        session.session_id: {_normalize_text(point.memory_content) for point in session.memory_points}
        for session in dataset.sessions
    }
    update_reference_by_session = {
        session.session_id: {
            _normalize_text(point.memory_content)
            for point in session.memory_points
            if point.is_update
        }
        for session in dataset.sessions
    }
    evidence_by_session = {
        session.session_id: {
            _normalize_text(content)
            for question in session.questions
            for content in question.evidence_memory_contents
        }
        for session in dataset.sessions
    }
    candidate_by_session = {
        session_id: {_normalize_text(content) for content in contents if content.strip()}
        for session_id, contents in candidates_by_session.items()
    }

    reference_count = sum(len(items) for items in reference_by_session.values())
    candidate_count = sum(len(items) for items in candidate_by_session.values())
    matched_count = 0
    hallucinated_count = 0
    omitted_count = 0
    update_matched_count = 0
    update_reference_count = 0
    evidence_matched_count = 0
    evidence_reference_count = 0

    for session_id, reference_items in reference_by_session.items():
        candidate_items = candidate_by_session.get(session_id, set())
        matched_count += len(reference_items & candidate_items)
        hallucinated_count += len(candidate_items - reference_items)
        omitted_count += len(reference_items - candidate_items)

        update_items = update_reference_by_session.get(session_id, set())
        update_reference_count += len(update_items)
        update_matched_count += len(update_items & candidate_items)

        evidence_items = evidence_by_session.get(session_id, set())
        evidence_reference_count += len(evidence_items)
        evidence_matched_count += len(evidence_items & candidate_items)

    precision = _ratio(matched_count, candidate_count)
    recall = _ratio(matched_count, reference_count)
    return HaluMemExtractionScore(
        reference_memory_count=reference_count,
        candidate_memory_count=candidate_count,
        matched_memory_count=matched_count,
        hallucinated_memory_count=hallucinated_count,
        omitted_memory_count=omitted_count,
        extraction_precision=precision,
        extraction_recall=recall,
        extraction_f1=_ratio(2 * precision * recall, precision + recall),
        update_recall=_ratio(update_matched_count, update_reference_count),
        qa_evidence_recall=_ratio(evidence_matched_count, evidence_reference_count),
    )


def score_halumem_reference_upper_bound(dataset: HaluMemDataset) -> HaluMemExtractionScore:
    return score_halumem_extraction(
        dataset,
        {
            session.session_id: [point.memory_content for point in session.memory_points]
            for session in dataset.sessions
        },
    )


def _load_raw_records(source: Path) -> list[dict[str, Any]]:
    if source.is_dir():
        records: list[dict[str, Any]] = []
        for child in sorted(source.iterdir()):
            if child.suffix.lower() in {".json", ".jsonl"}:
                records.extend(_load_raw_records(child))
        return records

    if source.suffix.lower() == ".jsonl":
        with source.open("r", encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]

    if source.suffix.lower() == ".json":
        with source.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return _records_from_payload(payload)

    raise ValueError(f"Unsupported HaluMem dataset file type: {source}")


def _records_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("data", "records", "users"):
            nested = payload.get(key)
            if isinstance(nested, list):
                return [item for item in nested if isinstance(item, dict)]
        return [payload]
    raise ValueError("HaluMem payload must be a JSON object, list, or JSONL records.")


def _sessions_from_user(raw_user: dict[str, Any], user_index: int) -> list[HaluMemSession]:
    user_id = _text_value(raw_user, "uuid", "user_id", "id") or f"user-{user_index}"
    raw_sessions = _list_value(raw_user.get("sessions"))
    if not raw_sessions and _looks_like_session(raw_user):
        raw_sessions = [raw_user]

    sessions: list[HaluMemSession] = []
    for session_index, raw_session in enumerate(raw_sessions):
        if not isinstance(raw_session, dict):
            continue
        session_id = _text_value(raw_session, "session_id", "id", "uuid")
        if session_id is None:
            session_id = f"{user_id}:session-{session_index}"
        memory_points = [
            _memory_point_from_raw(user_id, session_id, point_index, point)
            for point_index, point in enumerate(_list_value(_first_present(raw_session, "memory_points", "memories")))
            if isinstance(point, dict)
        ]
        questions = [
            _question_from_raw(user_id, session_id, question)
            for question in _list_value(_first_present(raw_session, "questions", "qa_pairs"))
            if isinstance(question, dict)
        ]
        sessions.append(
            HaluMemSession(
                user_id=user_id,
                session_id=session_id,
                dialogue=[
                    item
                    for item in _list_value(_first_present(raw_session, "dialogue", "dialogues", "turns"))
                    if isinstance(item, dict)
                ],
                memory_points=memory_points,
                questions=questions,
                start_time=_text_value(raw_session, "start_time", "started_at"),
                end_time=_text_value(raw_session, "end_time", "ended_at"),
                dialogue_token_length=_int_value(raw_session.get("dialogue_token_length")),
                raw=raw_session,
            )
        )
    return sessions


def _memory_point_from_raw(
    user_id: str,
    session_id: str,
    point_index: int,
    raw_point: dict[str, Any],
) -> HaluMemMemoryPoint:
    memory_content = _text_value(raw_point, "memory_content", "content", "text", "memory")
    if memory_content is None:
        memory_content = ""
    original_memories = [
        item
        for item in (_list_value(raw_point.get("original_memories")) or _list_value(raw_point.get("original_memory")))
        if isinstance(item, str)
    ]
    return HaluMemMemoryPoint(
        user_id=user_id,
        session_id=session_id,
        index=_text_value(raw_point, "index", "id") or str(point_index),
        memory_content=memory_content,
        memory_type=_text_value(raw_point, "memory_type", "type"),
        memory_source=_text_value(raw_point, "memory_source", "source"),
        is_update=_bool_value(raw_point.get("is_update")),
        original_memories=original_memories,
        importance=_float_value(raw_point.get("importance")),
        timestamp=_text_value(raw_point, "timestamp", "created_at"),
        raw=raw_point,
    )


def _question_from_raw(user_id: str, session_id: str, raw_question: dict[str, Any]) -> HaluMemQuestion:
    evidence_memory_contents = [
        evidence
        for evidence_item in _list_value(raw_question.get("evidence"))
        if isinstance(evidence_item, dict)
        if (evidence := _text_value(evidence_item, "memory_content", "content", "text", "memory")) is not None
    ]
    return HaluMemQuestion(
        user_id=user_id,
        session_id=session_id,
        question=_text_value(raw_question, "question", "query") or "",
        answer=_text_value(raw_question, "answer", "expected_answer"),
        evidence_memory_contents=evidence_memory_contents,
        difficulty=_text_value(raw_question, "difficulty"),
        question_type=_text_value(raw_question, "question_type", "type"),
        raw=raw_question,
    )


def _turn_from_halumem_dialogue(index: int, raw_turn: dict[str, Any]) -> TraceTurn:
    role = (_text_value(raw_turn, "role", "speaker") or "environment").lower()
    if role not in {"user", "assistant", "tool", "environment", "system"}:
        role = "environment"
    turn_index = _int_value(raw_turn.get("dialogue_turn"))
    return TraceTurn(
        index=index if turn_index is None else turn_index,
        role=role,  # type: ignore[arg-type]
        content=_text_value(raw_turn, "content", "text", "utterance") or "",
        timestamp=_parse_timestamp(_text_value(raw_turn, "timestamp", "created_at")),
    )


def _looks_like_session(raw: dict[str, Any]) -> bool:
    return any(key in raw for key in ("dialogue", "dialogues", "turns", "memory_points", "questions"))


def _first_present(raw: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in raw:
            return raw[key]
    return None


def _text_value(raw: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = raw.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            return value
        return str(value)
    return None


def _list_value(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _int_value(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float_value(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _parse_timestamp(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        pass

    for pattern in ("%b %d, %Y, %H:%M:%S", "%B %d, %Y, %H:%M:%S"):
        try:
            return datetime.strptime(value, pattern).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return datetime.now(timezone.utc)


def _normalize_text(value: str) -> str:
    return " ".join(value.lower().split())


def _safe_id(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in value)


def _ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator
