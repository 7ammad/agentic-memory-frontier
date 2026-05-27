from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from cem_core import AgentTrace, TraceTurn


class LongMemEvalV2Question(BaseModel):
    question_id: str
    domain: str
    environment: str
    question_type: str
    question: str
    image: str | None = None
    answer: Any = None
    eval_function: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class LongMemEvalV2State(BaseModel):
    state_index: int
    step: int | None = None
    url: str | None = None
    action: str | None = None
    thought: str | None = None
    accessibility_tree: str | None = None
    screenshot: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class LongMemEvalV2Trajectory(BaseModel):
    trajectory_id: str
    domain: str
    environment: str
    goal: str
    outcome: str
    start_url: str | None = None
    states: list[LongMemEvalV2State]
    raw: dict[str, Any] = Field(default_factory=dict)


class LongMemEvalV2Dataset(BaseModel):
    source_path: str
    questions: list[LongMemEvalV2Question]
    trajectories: list[LongMemEvalV2Trajectory]
    haystacks: dict[str, dict[str, list[str]]] = Field(default_factory=dict)

    @property
    def trajectories_by_id(self) -> dict[str, LongMemEvalV2Trajectory]:
        return {trajectory.trajectory_id: trajectory for trajectory in self.trajectories}


class LongMemEvalV2DatasetSummary(BaseModel):
    source_path: str
    question_count: int
    trajectory_count: int
    state_count: int
    haystack_count: int
    screenshot_ref_count: int
    domain_counts: dict[str, int]
    question_type_counts: dict[str, int]


class LongMemEvalV2AnswerScore(BaseModel):
    question_count: int
    answered_count: int
    exact_match_count: int
    exact_match_accuracy: float


class LongMemEvalV2RetrievalScore(BaseModel):
    haystack_name: str
    question_count: int
    questions_with_haystack: int
    covered_question_count: int
    retrieved_trajectory_count: int
    in_haystack_retrieved_count: int
    out_of_haystack_retrieved_count: int
    haystack_member_precision: float
    question_coverage_rate: float


def load_longmemeval_v2_dataset(path: str | Path) -> LongMemEvalV2Dataset:
    root = Path(path)
    questions_path = root / "questions.jsonl" if root.is_dir() else root
    trajectories_path = root / "trajectories.jsonl" if root.is_dir() else root.with_name("trajectories.jsonl")
    haystack_root = root / "haystacks" if root.is_dir() else root.parent / "haystacks"
    questions = [_question_from_raw(item) for item in _read_jsonl(questions_path)]
    trajectories = [_trajectory_from_raw(item) for item in _read_jsonl(trajectories_path)]
    return LongMemEvalV2Dataset(
        source_path=str(root),
        questions=questions,
        trajectories=trajectories,
        haystacks=_load_haystacks(haystack_root),
    )


def summarize_longmemeval_v2_dataset(path: str | Path) -> LongMemEvalV2DatasetSummary:
    dataset = load_longmemeval_v2_dataset(path)
    domain_counts: dict[str, int] = {}
    question_type_counts: dict[str, int] = {}
    for question in dataset.questions:
        domain_counts[question.domain] = domain_counts.get(question.domain, 0) + 1
        question_type_counts[question.question_type] = question_type_counts.get(question.question_type, 0) + 1
    question_screenshot_count = len([question for question in dataset.questions if question.image])
    trajectory_screenshot_count = len(
        [
            state
            for trajectory in dataset.trajectories
            for state in trajectory.states
            if state.screenshot
        ]
    )
    return LongMemEvalV2DatasetSummary(
        source_path=dataset.source_path,
        question_count=len(dataset.questions),
        trajectory_count=len(dataset.trajectories),
        state_count=sum(len(trajectory.states) for trajectory in dataset.trajectories),
        haystack_count=sum(len(mapping) for mapping in dataset.haystacks.values()),
        screenshot_ref_count=question_screenshot_count + trajectory_screenshot_count,
        domain_counts=dict(sorted(domain_counts.items())),
        question_type_counts=dict(sorted(question_type_counts.items())),
    )


def longmemeval_v2_trajectories_to_agent_traces(dataset: LongMemEvalV2Dataset) -> list[AgentTrace]:
    traces: list[AgentTrace] = []
    for trajectory in dataset.trajectories:
        turns: list[TraceTurn] = [
            TraceTurn(
                index=0,
                role="system",
                content=f"GOAL: {trajectory.goal}\nSTART_URL: {trajectory.start_url or ''}".strip(),
            )
        ]
        for state in trajectory.states:
            if state.accessibility_tree or state.url or state.screenshot:
                turns.append(
                    TraceTurn(
                        index=len(turns),
                        role="environment",
                        content=_state_observation(state),
                        observation_ref=state.url,
                        artifact_refs=[state.screenshot] if state.screenshot else [],
                    )
                )
            if state.action or state.thought:
                turns.append(
                    TraceTurn(
                        index=len(turns),
                        role="assistant",
                        content=_state_action(state),
                    )
                )
        traces.append(
            AgentTrace(
                trace_id=f"lme-v2-{_safe_id(trajectory.trajectory_id)}",
                session_id=f"lme-v2-{trajectory.trajectory_id}",
                agent_id="longmemeval-v2-source",
                task_id=f"longmemeval-v2-{trajectory.domain}",
                turns=turns,
                final_outcome=_outcome(trajectory.outcome),
                environment={
                    "domain": "longmemeval-v2",
                    "lme_v2_domain": trajectory.domain,
                    "lme_v2_environment": trajectory.environment,
                    "source_path": dataset.source_path,
                },
            )
        )
    return traces


def score_longmemeval_v2_answers(
    dataset: LongMemEvalV2Dataset,
    answers_by_question: Mapping[str, Any],
) -> LongMemEvalV2AnswerScore:
    exact_matches = 0
    answered = 0
    for question in dataset.questions:
        if question.question_id not in answers_by_question:
            continue
        answered += 1
        if _canonical_answer(answers_by_question[question.question_id]) == _canonical_answer(question.answer):
            exact_matches += 1
    return LongMemEvalV2AnswerScore(
        question_count=len(dataset.questions),
        answered_count=answered,
        exact_match_count=exact_matches,
        exact_match_accuracy=_ratio(exact_matches, len(dataset.questions)),
    )


def score_longmemeval_v2_retrieval(
    dataset: LongMemEvalV2Dataset,
    retrieved_trajectory_ids_by_question: Mapping[str, Sequence[str]],
    *,
    haystack_name: str = "lme_v2_small",
    k: int | None = None,
) -> LongMemEvalV2RetrievalScore:
    haystack = dataset.haystacks.get(haystack_name, {})
    questions_with_haystack = 0
    covered_questions = 0
    retrieved_count = 0
    in_haystack_count = 0
    out_of_haystack_count = 0

    for question in dataset.questions:
        allowed = set(haystack.get(question.question_id, []))
        if allowed:
            questions_with_haystack += 1
        retrieved = list(retrieved_trajectory_ids_by_question.get(question.question_id, []))
        if k is not None:
            retrieved = retrieved[:k]
        if retrieved:
            covered_questions += 1
        for trajectory_id in retrieved:
            retrieved_count += 1
            if trajectory_id in allowed:
                in_haystack_count += 1
            else:
                out_of_haystack_count += 1

    return LongMemEvalV2RetrievalScore(
        haystack_name=haystack_name,
        question_count=len(dataset.questions),
        questions_with_haystack=questions_with_haystack,
        covered_question_count=covered_questions,
        retrieved_trajectory_count=retrieved_count,
        in_haystack_retrieved_count=in_haystack_count,
        out_of_haystack_retrieved_count=out_of_haystack_count,
        haystack_member_precision=_ratio(in_haystack_count, retrieved_count),
        question_coverage_rate=_ratio(covered_questions, len(dataset.questions)),
    )


def score_longmemeval_v2_reference_upper_bound(dataset: LongMemEvalV2Dataset) -> LongMemEvalV2AnswerScore:
    return score_longmemeval_v2_answers(
        dataset,
        {question.question_id: question.answer for question in dataset.questions},
    )


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _load_haystacks(root: Path) -> dict[str, dict[str, list[str]]]:
    if not root.exists():
        return {}
    haystacks: dict[str, dict[str, list[str]]] = {}
    for child in sorted(root.glob("*.json")):
        with child.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        haystacks[child.stem] = {
            str(question_id): [str(item) for item in _list_value(trajectory_ids)]
            for question_id, trajectory_ids in raw.items()
        }
    return haystacks


def _question_from_raw(raw: dict[str, Any]) -> LongMemEvalV2Question:
    return LongMemEvalV2Question(
        question_id=_text_value(raw, "id", "question_id") or "",
        domain=_text_value(raw, "domain") or "",
        environment=_text_value(raw, "environment") or "",
        question_type=_text_value(raw, "question_type", "type") or "",
        question=_text_value(raw, "question") or "",
        image=_text_value(raw, "image"),
        answer=raw.get("answer"),
        eval_function=_text_value(raw, "eval_function"),
        raw=raw,
    )


def _trajectory_from_raw(raw: dict[str, Any]) -> LongMemEvalV2Trajectory:
    return LongMemEvalV2Trajectory(
        trajectory_id=_text_value(raw, "id", "trajectory_id") or "",
        domain=_text_value(raw, "domain") or "",
        environment=_text_value(raw, "environment") or "",
        goal=_text_value(raw, "goal") or "",
        outcome=(_text_value(raw, "outcome") or "unknown").lower(),
        start_url=_text_value(raw, "start_url"),
        states=[
            _state_from_raw(index, item)
            for index, item in enumerate(_list_value(raw.get("states")))
            if isinstance(item, dict)
        ],
        raw=raw,
    )


def _state_from_raw(index: int, raw: dict[str, Any]) -> LongMemEvalV2State:
    return LongMemEvalV2State(
        state_index=_int_value(raw.get("state_index")) or index,
        step=_int_value(raw.get("step")),
        url=_text_value(raw, "url"),
        action=_text_value(raw, "action"),
        thought=_text_value(raw, "thought"),
        accessibility_tree=_text_value(raw, "accessibility_tree"),
        screenshot=_text_value(raw, "screenshot"),
        raw=raw,
    )


def _state_observation(state: LongMemEvalV2State) -> str:
    return "\n".join(
        item
        for item in (
            f"URL: {state.url}" if state.url else "",
            f"ACCESSIBILITY_TREE: {state.accessibility_tree}" if state.accessibility_tree else "",
            f"SCREENSHOT: {state.screenshot}" if state.screenshot else "",
        )
        if item
    )


def _state_action(state: LongMemEvalV2State) -> str:
    return "\n".join(
        item
        for item in (
            state.thought or "",
            state.action or "",
        )
        if item
    )


def _outcome(value: str) -> str:
    if value in {"success", "failure", "partial", "unknown"}:
        return value
    return "unknown"


def _canonical_answer(value: Any) -> str:
    if isinstance(value, str):
        return " ".join(value.lower().split())
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _list_value(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _text_value(raw: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = raw.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            return value
        return str(value)
    return None


def _int_value(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_id(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in value)


def _ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator
