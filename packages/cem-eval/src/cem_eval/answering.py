from __future__ import annotations

import json
import re
from collections.abc import Sequence
from typing import Any

ANSWER_SYNTHESIS_PROMPT_VERSION = "cem-answer-synthesis-v1"

_TOKEN_RE = re.compile(r"[a-z0-9_]+")


def synthesize_answer(question: str, evidence_candidates: Sequence[Any]) -> str | None:
    """Local proxy answer synthesis over retrieved memory snippets.

    This is intentionally small and auditable. Official benchmark answering still
    belongs behind the official evaluator boundary; this layer prevents local
    runners from treating raw Action Brief recommendations as final answers.
    """

    candidates = [_stringify(candidate).strip() for candidate in evidence_candidates]
    candidates = [candidate for candidate in candidates if candidate]
    if not candidates:
        return None

    ranked = sorted(
        candidates,
        key=lambda candidate: (
            -_overlap_score(question, candidate),
            len(candidate),
            candidate.lower(),
        ),
    )
    best = ranked[0]
    if "=" in best:
        key, value = best.split("=", 1)
        if _tokens(key) & _tokens(question):
            return value.strip()
    return best


def _overlap_score(question: str, candidate: str) -> int:
    question_tokens = _tokens(question)
    candidate_tokens = _tokens(candidate)
    return len(question_tokens & candidate_tokens)


def _tokens(value: str) -> set[str]:
    return {token for token in _TOKEN_RE.findall(value.lower()) if len(token) > 2}


def _stringify(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
