from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from .kernel import CEM
from .local_memory import (
    default_root,
    init_memory,
    list_memory,
    pin_directive,
    remember_experience,
    retrieve_brief,
    run_eval,
)
from .models import StrictModel, new_id, utc_now

MigrationAction = Literal["pin", "remember", "skip"]
MonitorStatus = Literal["pass", "fail"]


class MigrationItem(StrictModel):
    item_id: str
    action: MigrationAction
    content: str
    source: str
    reason: str
    kind: str | None = None
    outcome: str | None = None
    domain_scope: str | None = "agentic-memory-system"
    task_family: str | None = "codex-memory-migration"


class MigrationRun(StrictModel):
    run_id: str = Field(default_factory=lambda: new_id("migration"))
    generated_at: datetime = Field(default_factory=utc_now)
    source_path: str
    applied: bool
    pin_count: int
    remember_count: int
    skip_count: int
    applied_pin_count: int = 0
    applied_remember_count: int = 0
    existing_count: int = 0
    items: list[MigrationItem]


class MonitorCheck(StrictModel):
    name: str
    status: MonitorStatus
    detail: str


class MonitorRun(StrictModel):
    run_id: str = Field(default_factory=lambda: new_id("monitor"))
    generated_at: datetime = Field(default_factory=utc_now)
    root: str
    deep: bool
    status: MonitorStatus
    checks: list[MonitorCheck]


def build_codex_memory_migration_run(
    root: Path | None = None,
    *,
    memory_base: Path | None = None,
) -> MigrationRun:
    root = _root(root)
    source_path = _memory_registry_path(memory_base)
    section = _agentic_memory_section(source_path)
    items = _migration_items_from_section(section, source_path)
    run = MigrationRun(
        source_path=str(source_path),
        applied=False,
        pin_count=sum(1 for item in items if item.action == "pin"),
        remember_count=sum(1 for item in items if item.action == "remember"),
        skip_count=sum(1 for item in items if item.action == "skip"),
        items=items,
    )
    _write_migration_records(root, run)
    return run


def apply_codex_memory_migration(
    root: Path | None = None,
    *,
    memory_base: Path | None = None,
) -> MigrationRun:
    root = _root(root)
    init_memory(root)
    dry_run = build_codex_memory_migration_run(root, memory_base=memory_base)
    applied_pin_count = 0
    applied_remember_count = 0
    existing_count = 0

    for item in dry_run.items:
        if item.action == "pin":
            result = pin_directive(
                root,
                item.content,
                source=item.source,
                scope="codex-memory",
                domain_scope=item.domain_scope,
                task_family=item.task_family,
            )
            if result["created"]:
                applied_pin_count += 1
            else:
                existing_count += 1
        elif item.action == "remember":
            if _card_exists(root, item.content, item.domain_scope):
                existing_count += 1
                continue
            remember_experience(
                root,
                item.content,
                kind=item.kind or "skill",
                outcome=item.outcome or "success",
                domain_scope=item.domain_scope,
                task_family=item.task_family,
            )
            applied_remember_count += 1

    applied = dry_run.model_copy(
        update={
            "run_id": new_id("migration"),
            "generated_at": utc_now(),
            "applied": True,
            "applied_pin_count": applied_pin_count,
            "applied_remember_count": applied_remember_count,
            "existing_count": existing_count,
        }
    )
    _write_migration_records(root, applied)
    return applied


def run_monitor(
    root: Path | None = None,
    *,
    deep: bool = False,
) -> MonitorRun:
    root = _root(root)
    init_memory(root)
    checks: list[MonitorCheck] = []
    checks.append(_check("root_exists", root.exists(), str(root)))
    checks.append(_check("sqlite_exists", (root / "cem.sqlite").exists(), str(root / "cem.sqlite")))
    checks.append(_check("directives_file_exists", (root / "directives.json").exists(), str(root / "directives.json")))

    directives = list_memory(root, kind="directives")["directives"]
    cards = list_memory(root, kind="cards")["cards"]
    checks.append(_check("minimum_directives", len(directives) >= 6, f"{len(directives)} directives"))
    checks.append(_check("learned_card_present", len(cards) >= 1, f"{len(cards)} cards"))

    brief = retrieve_brief(root, "continue building Agentic Memory System", domain_scope="agentic-memory-system")
    actions = "\n".join(brief["recommended_next_actions"]).lower()
    checks.append(_check("brief_has_waki_boundary", "waki" in actions, "Waki boundary present"))
    checks.append(_check("brief_has_verification_rule", "pytest" in actions and "synthetic" in actions, "verification rule present"))
    checks.append(_check("brief_has_todo_rule", "todo.md" in actions, "TODO continuation rule present"))

    if deep:
        eval_result = run_eval(root)["result"]
        metrics_ok = (
            eval_result["false_memory_resistance"] == 1.0
            and eval_result["contradiction_recall"] == 1.0
            and eval_result["false_quarantine_rate"] == 0.0
        )
        checks.append(_check("deep_synthetic_eval", metrics_ok, "synthetic corruption metrics checked"))

    status: MonitorStatus = "pass" if all(check.status == "pass" for check in checks) else "fail"
    run = MonitorRun(root=str(root), deep=deep, status=status, checks=checks)
    _write_monitor_records(root, run)
    return run


def dashboard_status(root: Path | None = None) -> dict[str, Any]:
    root = _root(root)
    init_memory(root)
    cards = list_memory(root, kind="cards")["cards"]
    atoms = list_memory(root, kind="atoms")["atoms"]
    directives = list_memory(root, kind="directives")["directives"]
    return {
        "root": str(root),
        "card_count": len(cards),
        "atom_count": len(atoms),
        "directive_count": len(directives),
        "latest_migration": _load_json(root / "migration-latest.json"),
        "latest_monitor": _load_json(root / "monitor-latest.json"),
    }


def _migration_items_from_section(section: str, source_path: Path) -> list[MigrationItem]:
    source = str(source_path)
    items = [
        MigrationItem(
            item_id=_stable_id("pin", "active foundation"),
            action="pin",
            content="Keep Agentic Memory System centered on Causal Experience Memory, not commodity memory storage.",
            source=source,
            reason="explicit CEM foundation directive from Codex memory registry",
        ),
        MigrationItem(
            item_id=_stable_id("pin", "write path wedge"),
            action="pin",
            content="Prioritize write-path quality: quarantine false, stale, unsupported, contradictory, and hypothesis-only memories before trust.",
            source=source,
            reason="explicit first-wedge directive from Codex memory registry",
        ),
        MigrationItem(
            item_id=_stable_id("pin", "v0 boundary"),
            action="pin",
            content="Preserve the V0 boundary: marker extraction and simple contradiction detection are fixtures until stronger eval-backed implementations exist.",
            source=source,
            reason="explicit anti-overclaim directive from Codex memory registry",
        ),
        MigrationItem(
            item_id=_stable_id("pin", "platform drift"),
            action="pin",
            content="Do not let MCP, database, dashboard, or platform work outrun the CEM proof and usable operator loop.",
            source=source,
            reason="explicit anti-drift directive from Codex memory registry",
        ),
        MigrationItem(
            item_id=_stable_id("remember", "rerun verification"),
            action="remember",
            content="run pytest and synthetic eval before claiming CEM or AMS memory changes are complete",
            source=source,
            reason="verified prior workflow lesson from Codex memory registry",
            kind="skill",
            outcome="success",
            task_family="verification",
        ),
        MigrationItem(
            item_id=_stable_id("skip", "old snapshot counts"),
            action="skip",
            content="Do not import stale CEM-0 snapshot counts from the legacy Codex memory registry.",
            source=source,
            reason="old verification counts are snapshot-specific and may be stale",
            domain_scope=None,
            task_family=None,
        ),
    ]
    if "C:\\Dev\\Builds\\Waki" in section:
        items.append(
            MigrationItem(
                item_id=_stable_id("skip", "waki section"),
                action="skip",
                content="Skip unrelated Waki memory during Agentic Memory System migration.",
                source=source,
                reason="migration is scoped to Agentic Memory System only",
                domain_scope=None,
                task_family=None,
            )
        )
    return items


def _write_migration_records(root: Path, run: MigrationRun) -> None:
    root.mkdir(parents=True, exist_ok=True)
    _append_jsonl(root / "migration-runs.jsonl", run.model_dump(mode="json"))
    _write_json(root / "migration-latest.json", run.model_dump(mode="json"))
    (root / "migration-latest.md").write_text(_render_migration_markdown(run), encoding="utf-8")


def _write_monitor_records(root: Path, run: MonitorRun) -> None:
    root.mkdir(parents=True, exist_ok=True)
    _append_jsonl(root / "monitor-runs.jsonl", run.model_dump(mode="json"))
    _write_json(root / "monitor-latest.json", run.model_dump(mode="json"))
    (root / "monitor-latest.md").write_text(_render_monitor_markdown(run), encoding="utf-8")


def _render_migration_markdown(run: MigrationRun) -> str:
    lines = [
        "# AMS Migration Latest",
        "",
        f"- run_id: `{run.run_id}`",
        f"- applied: `{run.applied}`",
        f"- source: `{run.source_path}`",
        f"- pins: `{run.pin_count}`",
        f"- remembers: `{run.remember_count}`",
        f"- skips: `{run.skip_count}`",
        f"- applied_pins: `{run.applied_pin_count}`",
        f"- applied_remembers: `{run.applied_remember_count}`",
        f"- existing: `{run.existing_count}`",
        "",
        "## Items",
        "",
    ]
    for item in run.items:
        lines.append(f"- `{item.action}` `{item.item_id}`: {item.content} ({item.reason})")
    return "\n".join(lines) + "\n"


def _render_monitor_markdown(run: MonitorRun) -> str:
    lines = [
        "# AMS Monitor Latest",
        "",
        f"- run_id: `{run.run_id}`",
        f"- status: `{run.status}`",
        f"- deep: `{run.deep}`",
        f"- root: `{run.root}`",
        "",
        "## Checks",
        "",
    ]
    for check in run.checks:
        lines.append(f"- `{check.status}` `{check.name}`: {check.detail}")
    return "\n".join(lines) + "\n"


def _agentic_memory_section(source_path: Path) -> str:
    text = source_path.read_text(encoding="utf-8")
    marker = "# Task Group: C:\\Dev\\Builds\\Agentic Memory System"
    start = text.find(marker)
    if start < 0:
        raise ValueError(f"Agentic Memory System section not found in {source_path}")
    next_group = text.find("\n# Task Group:", start + len(marker))
    if next_group < 0:
        return text[start:]
    return text[start:next_group]


def _memory_registry_path(memory_base: Path | None) -> Path:
    base = memory_base or Path.home() / ".codex" / "memories"
    path = base / "MEMORY.md"
    if not path.exists():
        raise ValueError(f"Codex memory registry not found: {path}")
    return path


def _root(root: Path | None) -> Path:
    return (root or default_root()).expanduser().resolve()


def _check(name: str, passed: bool, detail: str) -> MonitorCheck:
    return MonitorCheck(name=name, status="pass" if passed else "fail", detail=detail)


def _card_exists(root: Path, content: str, domain_scope: str | None) -> bool:
    cem = CEM(root)
    use_when = domain_scope or "similar task context"
    return any(card.title == content[:80] and card.use_when == use_when for card in cem.store.list_cards())


def _stable_id(action: str, content: str) -> str:
    digest = hashlib.sha256(f"{action}:{content}".encode("utf-8")).hexdigest()[:16]
    return f"migration_item_{digest}"


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
