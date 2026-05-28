from __future__ import annotations

import json
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from .kernel import CEM
from .models import AgentTrace, StrictModel, TaskContext, TraceTurn, new_id, utc_now

MemoryKind = Literal["fact", "preference", "instruction", "skill", "failure", "hypothesis"]
MemoryOutcome = Literal["success", "failure", "partial", "unknown"]
ListKind = Literal["cards", "atoms", "directives"]

MARKER_BY_KIND: dict[MemoryKind, str] = {
    "fact": "FACT",
    "preference": "PREFERENCE",
    "instruction": "INSTRUCTION",
    "skill": "SKILL",
    "failure": "FAILURE",
    "hypothesis": "HYPOTHESIS",
}

ROLE_BY_KIND: dict[MemoryKind, Literal["user", "assistant", "tool", "environment", "system"]] = {
    "fact": "environment",
    "preference": "user",
    "instruction": "user",
    "skill": "environment",
    "failure": "environment",
    "hypothesis": "assistant",
}


class LocalMemoryConfig(StrictModel):
    agent_id: str = "codex"
    current_session_id: str = Field(default_factory=lambda: new_id("session"))


class Directive(StrictModel):
    directive_id: str = Field(default_factory=lambda: new_id("directive"))
    content: str
    source: str = "manual"
    scope: str = "global"
    domain_scope: str | None = None
    task_family: str | None = None
    active: bool = True
    created_at: datetime = Field(default_factory=utc_now)


def default_root() -> Path:
    configured = os.environ.get("AMS_ROOT") or os.environ.get("CEM_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.home() / ".codex" / "memory" / "cem").resolve()


def init_memory(root: Path | None = None, *, agent_id: str = "codex") -> dict[str, Any]:
    root = _root(root)
    root.mkdir(parents=True, exist_ok=True)
    CEM(root)
    if not _config_path(root).exists():
        _save_config(root, LocalMemoryConfig(agent_id=agent_id))
    if not _directives_path(root).exists():
        _save_directives(root, [])
    config = _load_config(root)
    return {
        "root": str(root),
        "agent_id": config.agent_id,
        "current_session_id": config.current_session_id,
        "card_count": len(CEM(root).store.list_cards()),
        "atom_count": len(CEM(root).store.list_atoms()),
        "directive_count": len(_load_directives(root)),
    }


def current_session(root: Path | None = None) -> dict[str, Any]:
    root = _ensure_initialized(root)
    config = _load_config(root)
    return {"root": str(root), "current_session_id": config.current_session_id}


def new_session(root: Path | None = None) -> dict[str, Any]:
    root = _ensure_initialized(root)
    config = _load_config(root)
    config.current_session_id = new_id("session")
    _save_config(root, config)
    return {"root": str(root), "current_session_id": config.current_session_id}


def remember_experience(
    root: Path | None,
    content: str,
    *,
    kind: MemoryKind,
    outcome: MemoryOutcome,
    domain_scope: str | None = None,
    task_family: str | None = None,
    session_id: str | None = None,
    agent_id: str | None = None,
) -> dict[str, Any]:
    root = _ensure_initialized(root)
    config = _load_config(root)
    marker = MARKER_BY_KIND[kind]
    trace = AgentTrace(
        session_id=session_id or config.current_session_id,
        agent_id=agent_id or config.agent_id,
        task_id=task_family,
        turns=[
            TraceTurn(
                index=0,
                role=ROLE_BY_KIND[kind],
                content=f"{marker}: {content}",
            )
        ],
        final_outcome=outcome,
        environment={"domain": domain_scope} if domain_scope else {},
    )

    cem = CEM(root)
    receipt = cem.ingest_trace(trace)
    atoms = cem.propose_memories(receipt.trace_id)
    promoted_cards: list[dict[str, Any]] = []
    atom_results: list[dict[str, Any]] = []

    for atom in atoms:
        decision = cem.validate(atom.atom_id)
        card = cem.promote(atom.atom_id)
        stored_atom = cem.store.get_atom(atom.atom_id)
        atom_result = {
            "atom_id": stored_atom.atom_id,
            "content": stored_atom.content,
            "epistemic_type": stored_atom.epistemic_type,
            "status": stored_atom.promotion_status,
            "decision": decision.decision,
            "reason_codes": decision.reason_codes,
            "quarantine_reason": stored_atom.quarantine_reason,
        }
        atom_results.append(atom_result)
        if card is not None:
            promoted_cards.append(
                {
                    "card_id": card.card_id,
                    "title": card.title,
                    "use_when": card.use_when,
                    "do": card.do,
                    "confidence_score": card.confidence_score,
                    "evidence_atom_ids": card.evidence_atom_ids,
                }
            )

    return {
        "root": str(root),
        "trace_id": receipt.trace_id,
        "session_id": trace.session_id,
        "agent_id": trace.agent_id,
        "proposed_count": len(atoms),
        "promoted_count": len(promoted_cards),
        "quarantined_count": sum(1 for item in atom_results if item["status"] == "quarantined"),
        "atoms": atom_results,
        "promoted_cards": promoted_cards,
    }


def pin_directive(
    root: Path | None,
    content: str,
    *,
    source: str = "manual",
    scope: str = "global",
    domain_scope: str | None = None,
    task_family: str | None = None,
) -> dict[str, Any]:
    root = _ensure_initialized(root)
    directives = _load_directives(root)
    for directive in directives:
        if (
            directive.active
            and directive.content == content
            and directive.source == source
            and directive.scope == scope
            and directive.domain_scope == domain_scope
            and directive.task_family == task_family
        ):
            return {"root": str(root), "created": False, "directive": directive.model_dump(mode="json")}

    directive = Directive(
        content=content,
        source=source,
        scope=scope,
        domain_scope=domain_scope,
        task_family=task_family,
    )
    directives.append(directive)
    _save_directives(root, directives)
    return {"root": str(root), "created": True, "directive": directive.model_dump(mode="json")}


def bootstrap_codex(root: Path | None, *, workspace: Path) -> dict[str, Any]:
    root = _ensure_initialized(root)
    workspace = workspace.resolve()
    _reject_waki(workspace)
    directive_specs = [
        (
            "Never read or write files under C:\\Dev\\Builds\\Waki from this workspace.",
            workspace / "AGENTS.md",
        ),
        (
            "Keep the active thesis centered on Causal Experience Memory: memory is verified experience that improves future action.",
            workspace / "README.md",
        ),
        (
            "Run pytest and the synthetic eval before claiming Agentic Memory System work is complete.",
            workspace / "README.md",
        ),
        (
            "Use TODO.md as the ordered continuation rail; do the first unchecked item before later work.",
            workspace / "TODO.md",
        ),
        (
            "Do not claim state-of-the-art for CEM-0 or AMS v1.",
            workspace / "TODO.md",
        ),
        (
            "Treat the deterministic extractor and contradiction detector as V0 fixtures, not the final reasoning layer.",
            workspace / "README.md",
        ),
    ]
    results = [
        pin_directive(
            root,
            content,
            source=str(source),
            scope="workspace",
        )
        for content, source in directive_specs
    ]
    return {
        "root": str(root),
        "workspace": str(workspace),
        "created_count": sum(1 for item in results if item["created"]),
        "existing_count": sum(1 for item in results if not item["created"]),
        "directives": [item["directive"] for item in results],
    }


def retrieve_brief(
    root: Path | None,
    description: str,
    *,
    domain_scope: str | None = None,
    task_family: str | None = None,
    session_id: str | None = None,
    task_id: str | None = None,
    max_cards: int = 5,
) -> dict[str, Any]:
    root = _ensure_initialized(root)
    cem = CEM(root)
    task = TaskContext(
        task_id=task_id,
        session_id=session_id,
        description=description,
        domain_scope=domain_scope,
        task_family=task_family,
    )
    experience = cem.retrieve_action_brief(task, max_cards=max_cards)
    directives = [
        directive
        for directive in _load_directives(root)
        if directive.active and _directive_matches(directive, description, domain_scope, task_family)
    ]
    directive_rows = [directive.model_dump(mode="json") for directive in directives]
    recommended_actions = [directive.content for directive in directives] + experience.recommended_next_actions
    evidence_links = [directive.directive_id for directive in directives] + experience.evidence_links
    return {
        "root": str(root),
        "task_id": task_id,
        "description": description,
        "directives": directive_rows,
        "experience": experience.model_dump(mode="json"),
        "recommended_next_actions": recommended_actions,
        "preconditions_to_check": experience.preconditions_to_check,
        "evidence_links": evidence_links,
        "confidence_score": experience.confidence_score,
    }


def list_memory(root: Path | None, *, kind: ListKind = "cards") -> dict[str, Any]:
    root = _ensure_initialized(root)
    cem = CEM(root)
    if kind == "cards":
        return {
            "root": str(root),
            "cards": [
                {
                    "card_id": card.card_id,
                    "title": card.title,
                    "use_when": card.use_when,
                    "do": card.do,
                    "confidence_score": card.confidence_score,
                    "evidence_count": len(card.evidence_atom_ids),
                }
                for card in cem.store.list_cards()
            ],
        }
    if kind == "atoms":
        return {
            "root": str(root),
            "atoms": [
                {
                    "atom_id": atom.atom_id,
                    "content": atom.content,
                    "epistemic_type": atom.epistemic_type,
                    "status": atom.promotion_status,
                    "domain_scope": atom.domain_scope,
                    "task_family": atom.task_family,
                    "quarantine_reason": atom.quarantine_reason,
                }
                for atom in cem.store.list_atoms()
            ],
        }
    return {
        "root": str(root),
        "directives": [directive.model_dump(mode="json") for directive in _load_directives(root)],
    }


def audit_memory(root: Path | None, memory_id: str) -> dict[str, Any]:
    root = _ensure_initialized(root)
    try:
        audit = CEM(root).audit(memory_id)
        return {"root": str(root), "kind": audit.memory_kind, "audit": audit.model_dump(mode="json")}
    except KeyError:
        for directive in _load_directives(root):
            if directive.directive_id == memory_id:
                return {"root": str(root), "kind": "directive", "audit": directive.model_dump(mode="json")}
    raise KeyError(f"Memory not found: {memory_id}")


def run_eval(root: Path | None) -> dict[str, Any]:
    from cem_eval import run_synthetic_corruption_eval

    root = _ensure_initialized(root)
    eval_root = root / "eval-runs" / new_id("synthetic")
    result = run_synthetic_corruption_eval(eval_root)
    return {"root": str(root), "eval_root": str(eval_root), "result": result.model_dump(mode="json")}


def _ensure_initialized(root: Path | None) -> Path:
    root = _root(root)
    if not _config_path(root).exists() or not _directives_path(root).exists():
        init_memory(root)
    return root


def _root(root: Path | None) -> Path:
    return (root or default_root()).expanduser().resolve()


def _config_path(root: Path) -> Path:
    return root / "config.json"


def _directives_path(root: Path) -> Path:
    return root / "directives.json"


def _load_config(root: Path) -> LocalMemoryConfig:
    return LocalMemoryConfig.model_validate_json(_config_path(root).read_text(encoding="utf-8"))


def _save_config(root: Path, config: LocalMemoryConfig) -> None:
    _config_path(root).write_text(config.model_dump_json(indent=2), encoding="utf-8")


def _load_directives(root: Path) -> list[Directive]:
    path = _directives_path(root)
    if not path.exists():
        return []
    return [Directive.model_validate(item) for item in json.loads(path.read_text(encoding="utf-8"))]


def _save_directives(root: Path, directives: list[Directive]) -> None:
    payload = [directive.model_dump(mode="json") for directive in directives]
    _directives_path(root).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _directive_matches(
    directive: Directive,
    description: str,
    domain_scope: str | None,
    task_family: str | None,
) -> bool:
    if directive.domain_scope is None and directive.task_family is None:
        return True
    if directive.domain_scope is not None and directive.domain_scope == domain_scope:
        return True
    if directive.task_family is not None and directive.task_family == task_family:
        return True
    haystack = description.lower()
    if directive.domain_scope and directive.domain_scope.replace("-", " ") in haystack:
        return True
    if directive.task_family and directive.task_family.replace("-", " ") in haystack:
        return True
    return _has_directive_token_overlap(directive, description)


_TOKEN_RE = re.compile(r"[a-z0-9]+")
_DIRECTIVE_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "do",
    "for",
    "from",
    "if",
    "in",
    "into",
    "is",
    "it",
    "not",
    "of",
    "on",
    "or",
    "the",
    "this",
    "to",
    "use",
    "when",
    "with",
}


def _has_directive_token_overlap(directive: Directive, description: str) -> bool:
    """Return True when a scoped directive is lexically relevant to a task.

    Domain/task exact matches remain the primary route. This fallback catches
    global behavior directives whose domain labels are not known to the caller
    yet but whose content clearly names the task family, e.g. "unified KB",
    "tool registry", "Hermes/Kai", or "organizational AI layer".
    """
    task_tokens = _meaningful_tokens(description)
    if not task_tokens:
        return False
    directive_tokens = _meaningful_tokens(
        " ".join(
            part
            for part in [
                directive.content,
                directive.source,
                directive.domain_scope or "",
                directive.task_family or "",
            ]
            if part
        )
    )
    if not directive_tokens:
        return False
    return len(task_tokens & directive_tokens) >= 3


def _meaningful_tokens(text: str) -> set[str]:
    tokens: set[str] = set()
    for raw in _TOKEN_RE.findall(text.lower()):
        token = raw[:-1] if len(raw) > 4 and raw.endswith("s") else raw
        if len(token) < 3 or token in _DIRECTIVE_STOPWORDS:
            continue
        tokens.add(token)
    return tokens


def _reject_waki(path: Path) -> None:
    forbidden = Path("C:/Dev/Builds/Waki").resolve()
    try:
        path.relative_to(forbidden)
    except ValueError:
        return
    raise ValueError("Refusing to read or write C:\\Dev\\Builds\\Waki from this workspace.")
