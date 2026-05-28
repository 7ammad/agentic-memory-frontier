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
StartupStatus = Literal["allow", "block"]

AMS_DOMAIN_SCOPE = "agentic-memory-system"
GLOBAL_BEHAVIOR_SCOPE = "codex-behavior"


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


class RecordScopeSummary(StrictModel):
    total_card_count: int
    total_atom_count: int
    total_directive_count: int
    ams_card_count: int
    ams_atom_count: int
    ams_directive_count: int
    global_behavior_directive_count: int
    other_directive_count: int


class PhaseStatus(StrictModel):
    completed_through: str
    current_phase: str
    status: str
    next_step: str
    ready_for_next_phase: bool
    open_followups: list[str]


class StartupLimits(StrictModel):
    max_directives: int
    max_cards: int
    max_evidence: int
    max_tokens: int


class StartupBriefRun(StrictModel):
    brief_id: str = Field(default_factory=lambda: new_id("brief"))
    generated_at: datetime = Field(default_factory=utc_now)
    root: str
    status: StartupStatus
    monitor_id: str
    task_description: str
    domain_scope: str | None
    task_family: str | None
    limits: StartupLimits
    phase: PhaseStatus
    scope: RecordScopeSummary
    required_directives: dict[str, bool]
    recommended_next_actions: list[str]
    evidence_ids: list[str]
    estimated_tokens: int
    block_reasons: list[str]


class MonitorRun(StrictModel):
    run_id: str = Field(default_factory=lambda: new_id("monitor"))
    generated_at: datetime = Field(default_factory=utc_now)
    root: str
    deep: bool
    status: MonitorStatus
    scope: RecordScopeSummary
    phase: PhaseStatus
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
    scope = record_scope_summary(root)
    phase = phase_status()
    checks.append(_check("root_exists", root.exists(), str(root)))
    checks.append(_check("sqlite_exists", (root / "cem.sqlite").exists(), str(root / "cem.sqlite")))
    checks.append(_check("directives_file_exists", (root / "directives.json").exists(), str(root / "directives.json")))

    checks.append(_check("minimum_ams_directives", scope.ams_directive_count >= 6, f"{scope.ams_directive_count} AMS directives"))
    checks.append(_check("learned_ams_card_present", scope.ams_card_count >= 1, f"{scope.ams_card_count} AMS cards"))
    checks.append(
        _check(
            "global_behavior_separated",
            scope.ams_directive_count + scope.global_behavior_directive_count + scope.other_directive_count
            == scope.total_directive_count,
            (
                f"{scope.ams_directive_count} AMS directives, "
                f"{scope.global_behavior_directive_count} global behavior directives, "
                f"{scope.other_directive_count} other directives"
            ),
        )
    )

    brief = retrieve_brief(root, "continue building Agentic Memory System", domain_scope=AMS_DOMAIN_SCOPE)
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
    run = MonitorRun(root=str(root), deep=deep, status=status, scope=scope, phase=phase, checks=checks)
    _write_monitor_records(root, run)
    return run


def dashboard_status(root: Path | None = None) -> dict[str, Any]:
    root = _root(root)
    init_memory(root)
    scope = record_scope_summary(root)
    return {
        "root": str(root),
        "card_count": scope.total_card_count,
        "atom_count": scope.total_atom_count,
        "directive_count": scope.total_directive_count,
        "scope": scope.model_dump(mode="json"),
        "phase": phase_status().model_dump(mode="json"),
        "latest_migration": _load_json(root / "migration-latest.json"),
        "latest_monitor": _load_json(root / "monitor-latest.json"),
        "latest_startup_brief": _load_json(root / "startup-brief-latest.json"),
    }


def startup_brief(
    root: Path | None = None,
    *,
    description: str,
    domain_scope: str | None = AMS_DOMAIN_SCOPE,
    task_family: str | None = None,
    max_directives: int = 8,
    max_cards: int = 5,
    max_evidence: int = 20,
    max_tokens: int = 900,
) -> StartupBriefRun:
    root = _root(root)
    monitor = run_monitor(root, deep=False)
    brief = retrieve_brief(
        root,
        description,
        domain_scope=domain_scope,
        task_family=task_family,
        max_cards=max_cards,
    )
    directives = brief["directives"][:max_directives]
    directive_actions = [directive["content"] for directive in directives]
    experience_actions = brief["experience"]["recommended_next_actions"]
    recommended_actions = _cap_items_by_token_budget(directive_actions + experience_actions, max_tokens)
    evidence_ids = ([directive["directive_id"] for directive in directives] + brief["experience"]["evidence_links"])[:max_evidence]

    action_text = "\n".join(recommended_actions).lower()
    required_directives = {
        "waki_boundary": "waki" in action_text,
        "verification_rule": "pytest" in action_text and "synthetic" in action_text,
        "todo_rule": "todo.md" in action_text,
    }
    block_reasons: list[str] = []
    if monitor.status != "pass":
        block_reasons.append(f"monitor_failed:{monitor.run_id}")
    for name, present in required_directives.items():
        if not present:
            block_reasons.append(f"missing_required_directive:{name}")

    run = StartupBriefRun(
        root=str(root),
        status="block" if block_reasons else "allow",
        monitor_id=monitor.run_id,
        task_description=description,
        domain_scope=domain_scope,
        task_family=task_family,
        limits=StartupLimits(
            max_directives=max_directives,
            max_cards=max_cards,
            max_evidence=max_evidence,
            max_tokens=max_tokens,
        ),
        phase=phase_status(),
        scope=record_scope_summary(root),
        required_directives=required_directives,
        recommended_next_actions=recommended_actions,
        evidence_ids=evidence_ids,
        estimated_tokens=_estimate_tokens("\n".join(recommended_actions)),
        block_reasons=block_reasons,
    )
    _write_startup_brief_records(root, run)
    return run


def record_scope_summary(root: Path | None = None) -> RecordScopeSummary:
    root = _root(root)
    cards = list_memory(root, kind="cards")["cards"]
    atoms = list_memory(root, kind="atoms")["atoms"]
    directives = list_memory(root, kind="directives")["directives"]
    return RecordScopeSummary(
        total_card_count=len(cards),
        total_atom_count=len(atoms),
        total_directive_count=len(directives),
        ams_card_count=sum(1 for card in cards if _card_is_ams_scoped(card)),
        ams_atom_count=sum(1 for atom in atoms if _atom_is_ams_scoped(atom)),
        ams_directive_count=sum(1 for directive in directives if _directive_is_ams_scoped(directive)),
        global_behavior_directive_count=sum(1 for directive in directives if _directive_is_global_behavior(directive)),
        other_directive_count=sum(
            1
            for directive in directives
            if not _directive_is_ams_scoped(directive) and not _directive_is_global_behavior(directive)
        ),
    )


def phase_status() -> PhaseStatus:
    return PhaseStatus(
        completed_through="AMS v1.1 Monitor-0: migration ledger, monitor ledger, and dashboard are live",
        current_phase="AMS v1.2 Memory Use Controller",
        status="active",
        next_step="verify global ams-memory MCP availability after Codex runtime restart",
        ready_for_next_phase=True,
        open_followups=[
            "verify global ams-memory MCP availability after Codex runtime restart",
            "attach startup brief ids to agent work records",
            "add latency budget enforcement to the startup controller",
        ],
    )


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


def _write_startup_brief_records(root: Path, run: StartupBriefRun) -> None:
    root.mkdir(parents=True, exist_ok=True)
    _append_jsonl(root / "startup-brief-runs.jsonl", run.model_dump(mode="json"))
    _write_json(root / "startup-brief-latest.json", run.model_dump(mode="json"))
    (root / "startup-brief-latest.md").write_text(_render_startup_brief_markdown(run), encoding="utf-8")


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
        f"- phase: `{run.phase.current_phase}`",
        f"- ams_cards: `{run.scope.ams_card_count}`",
        f"- ams_atoms: `{run.scope.ams_atom_count}`",
        f"- ams_directives: `{run.scope.ams_directive_count}`",
        f"- global_behavior_directives: `{run.scope.global_behavior_directive_count}`",
        f"- other_directives: `{run.scope.other_directive_count}`",
        "",
        "## Checks",
        "",
    ]
    for check in run.checks:
        lines.append(f"- `{check.status}` `{check.name}`: {check.detail}")
    return "\n".join(lines) + "\n"


def _render_startup_brief_markdown(run: StartupBriefRun) -> str:
    lines = [
        "# AMS Startup Brief Latest",
        "",
        f"- brief_id: `{run.brief_id}`",
        f"- status: `{run.status}`",
        f"- monitor_id: `{run.monitor_id}`",
        f"- phase: `{run.phase.current_phase}`",
        f"- task: {run.task_description}",
        f"- estimated_tokens: `{run.estimated_tokens}`",
        f"- evidence_ids: `{len(run.evidence_ids)}`",
        "",
        "## Required Directives",
        "",
    ]
    for name, present in run.required_directives.items():
        lines.append(f"- `{name}`: `{present}`")
    if run.block_reasons:
        lines.extend(["", "## Block Reasons", ""])
        for reason in run.block_reasons:
            lines.append(f"- `{reason}`")
    lines.extend(["", "## Recommended Actions", ""])
    for action in run.recommended_next_actions:
        lines.append(f"- {action}")
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


def _card_is_ams_scoped(card: dict[str, Any]) -> bool:
    return card.get("use_when") == AMS_DOMAIN_SCOPE


def _atom_is_ams_scoped(atom: dict[str, Any]) -> bool:
    return atom.get("domain_scope") == AMS_DOMAIN_SCOPE


def _directive_is_ams_scoped(directive: dict[str, Any]) -> bool:
    if directive.get("domain_scope") == AMS_DOMAIN_SCOPE:
        return True
    source = str(directive.get("source") or "")
    content = str(directive.get("content") or "")
    return "Agentic Memory System" in source or "Causal Experience Memory" in content or "CEM-0" in content


def _directive_is_global_behavior(directive: dict[str, Any]) -> bool:
    return directive.get("domain_scope") == GLOBAL_BEHAVIOR_SCOPE or directive.get("scope") == "global"


def _cap_items_by_token_budget(items: list[str], max_tokens: int) -> list[str]:
    selected: list[str] = []
    used = 0
    for item in items:
        cost = _estimate_tokens(item)
        if selected and used + cost > max_tokens:
            break
        if cost > max_tokens:
            words = item.split()
            selected.append(" ".join(words[:max_tokens]))
            break
        selected.append(item)
        used += cost
    return selected


def _estimate_tokens(text: str) -> int:
    return len(text.split())


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
