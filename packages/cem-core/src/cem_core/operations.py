from __future__ import annotations

import hashlib
import json
import tomllib
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from .correction_capture import (
    CorrectionControllerSummary,
    correction_controller_summary,
    correction_rule_surfaces_in_brief,
)
from .correction_hooks import (
    HOOK_EXIT_ALLOW,
    HookDecision,
    hook_on_pre_tool_use_gate,
    hook_on_user_prompt_submit,
)
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
RUNTIME_CONTROL_EXIT_BLOCK = 12


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


class MemorySurface(StrictModel):
    name: str
    role: Literal["primary", "secondary", "secondary_import_source", "unconfigured"]
    status: Literal["pass", "warn", "fail"]
    configured: bool
    source_path: str | None
    detail: str


class MemorySurfaceReport(StrictModel):
    generated_at: datetime = Field(default_factory=utc_now)
    root: str
    config_path: str
    memory_base: str
    reconciled: bool
    surfaces: list[MemorySurface]


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
    governed_run_id: str | None = None
    action_brief_id: str | None = None
    influence_id: str | None = None
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


class GovernedRunReceipt(StrictModel):
    receipt_id: str = Field(default_factory=lambda: new_id("run"))
    generated_at: datetime = Field(default_factory=utc_now)
    root: str
    cwd: str
    status: StartupStatus
    startup_brief_id: str
    action_brief_id: str | None = None
    influence_id: str | None = None
    monitor_id: str
    task_description: str
    domain_scope: str | None
    task_family: str | None
    evidence_ids: list[str]
    block_reasons: list[str]
    closed: bool = False
    outcome: Literal["success", "failure", "partial", "unknown"] | None = None
    finalized_at: datetime | None = None
    influence_ids: list[str] = Field(default_factory=list)


class RuntimeControlRun(StrictModel):
    control_id: str = Field(default_factory=lambda: new_id("control"))
    generated_at: datetime = Field(default_factory=utc_now)
    root: str
    cwd: str
    enforcement: Literal["external_guard"]
    status: StartupStatus
    task_description: str
    domain_scope: str | None
    task_family: str | None
    session_id: str | None
    startup_brief_id: str
    governed_run_id: str | None
    monitor_id: str
    prompt_decision: HookDecision
    gate_decision: HookDecision
    evidence_ids: list[str]
    block_reasons: list[str]
    runtime_exit_code: int


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


def _correction_controller_wired(summary: CorrectionControllerSummary, root: Path) -> bool:
    """True when the correction controller is bound to the active memory root.

    Falsifiable: a controller resolved against a different root would capture
    corrections that never surface in this root's briefs. The resume gate file is
    the controller's persistent record anchor, materialized under root.

    Caller contract: the gate file is created lazily by ``correction_gate_status``
    (invoked inside ``correction_controller_summary``), so callers must have built
    ``summary`` via ``correction_controller_summary`` before this predicate runs;
    otherwise the existence check returns a spurious ``False`` on a healthy root.
    """
    gate_file = Path(summary.gate_path).resolve()
    return summary.root == str(root) and gate_file.parent == root and gate_file.exists()


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
    correction_summary = correction_controller_summary(root)
    checks.append(
        _check(
            "correction_controller_wired",
            _correction_controller_wired(correction_summary, root),
            (
                f"{correction_summary.event_count} correction events recorded; "
                f"latest={correction_summary.latest_event_id}; gate={correction_summary.gate_path}"
            ),
        )
    )
    checks.append(
        _check(
            "correction_resume_gate_clear",
            not correction_summary.active_gate,
            (
                "no active correction resume gate"
                if not correction_summary.active_gate
                else f"blocked by {correction_summary.active_event_id}"
            ),
        )
    )
    checks.append(
        _check(
            "brief_has_correction_capture_rule",
            correction_rule_surfaces_in_brief(root),
            "correction capture directive surfaces in action brief",
        )
    )

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
    surfaces = memory_surface_report(root)
    return {
        "root": str(root),
        "card_count": scope.total_card_count,
        "atom_count": scope.total_atom_count,
        "directive_count": scope.total_directive_count,
        "scope": scope.model_dump(mode="json"),
        "memory_surfaces": surfaces.model_dump(mode="json"),
        "phase": phase_status().model_dump(mode="json"),
        "latest_migration": _load_json(root / "migration-latest.json"),
        "latest_monitor": _load_json(root / "monitor-latest.json"),
        "latest_startup_brief": _load_json(root / "startup-brief-latest.json"),
        "latest_governed_run": _load_json(root / "governed-run-latest.json"),
        "latest_runtime_control": _load_json(root / "runtime-control-latest.json"),
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
    experience_actions = brief["recommended_next_actions"][len(brief["directives"]) :]
    recommended_actions = _cap_items_by_token_budget(directive_actions + experience_actions, max_tokens)
    evidence_ids = ([directive["directive_id"] for directive in directives] + brief["experience"]["evidence_links"])[:max_evidence]
    action_brief_id = brief["experience"].get("brief_id")
    influence_id = brief["experience"].get("influence_id")

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

    receipt_id = new_id("run")
    run = StartupBriefRun(
        root=str(root),
        status="block" if block_reasons else "allow",
        governed_run_id=receipt_id,
        action_brief_id=action_brief_id,
        influence_id=influence_id,
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
    receipt = GovernedRunReceipt(
        receipt_id=receipt_id,
        root=str(root),
        cwd=str(Path.cwd().resolve()),
        status=run.status,
        startup_brief_id=run.brief_id,
        action_brief_id=action_brief_id,
        influence_id=influence_id,
        monitor_id=monitor.run_id,
        task_description=description,
        domain_scope=domain_scope,
        task_family=task_family,
        evidence_ids=evidence_ids,
        block_reasons=block_reasons,
    )
    _write_governed_run_records(root, receipt)
    _write_startup_brief_records(root, run)
    return run


def close_governed_run(
    root: Path | None = None,
    *,
    receipt_id: str | None = None,
    outcome: Literal["success", "failure", "partial", "unknown"],
    action_taken: str | None = None,
    observed_post_brief_delta: float | None = None,
    baseline_comparison: str | None = None,
) -> GovernedRunReceipt:
    root = _root(root)
    receipt = _load_governed_run_receipt(root, receipt_id)
    if receipt.closed:
        return receipt

    influence_ids = list(receipt.influence_ids)
    if receipt.status == "allow":
        if not receipt.action_brief_id or not receipt.influence_id:
            raise ValueError(
                f"governed run {receipt.receipt_id} cannot close influence: missing action_brief_id or influence_id"
            )
        event = CEM(root).close_influence(
            receipt.action_brief_id,
            action_taken=action_taken,
            outcome=outcome,
            observed_post_brief_delta=observed_post_brief_delta,
            baseline_comparison=baseline_comparison,
        )
        if event.influence_id not in influence_ids:
            influence_ids.append(event.influence_id)

    closed = receipt.model_copy(
        update={
            "closed": True,
            "outcome": outcome,
            "finalized_at": utc_now(),
            "influence_ids": influence_ids,
        }
    )
    _write_governed_run_records(root, closed)
    return closed


def runtime_control(
    root: Path | None = None,
    *,
    description: str,
    domain_scope: str | None = AMS_DOMAIN_SCOPE,
    task_family: str | None = None,
    session_id: str | None = None,
    affected_files: list[str] | None = None,
) -> RuntimeControlRun:
    """Build an enforceable AMS allow/block decision for an external launcher.

    Codex command hooks currently report non-zero exits as hook failures but still
    continue. This control path is owned by AMS instead: a caller must run it before
    invoking the downstream command and must not invoke that command when the exit
    code is non-zero.
    """
    root = _root(root)
    prompt_decision = hook_on_user_prompt_submit(
        root,
        description,
        session_id=session_id,
        affected_files=affected_files or [],
    )
    startup = startup_brief(
        root,
        description=description,
        domain_scope=domain_scope,
        task_family=task_family,
    )
    gate_decision = hook_on_pre_tool_use_gate(root)

    block_reasons: list[str] = []
    if prompt_decision.decision == "block":
        block_reasons.append(f"correction_prompt_blocked:{prompt_decision.event_id}")
    if gate_decision.decision == "block":
        block_reasons.append(f"resume_gate_blocked:{gate_decision.active_event_id or 'unknown'}")
    for reason in startup.block_reasons:
        block_reasons.append(f"startup_blocked:{reason}")

    status: StartupStatus = "block" if block_reasons else "allow"
    run = RuntimeControlRun(
        root=str(root),
        cwd=str(Path.cwd().resolve()),
        enforcement="external_guard",
        status=status,
        task_description=description,
        domain_scope=domain_scope,
        task_family=task_family,
        session_id=session_id,
        startup_brief_id=startup.brief_id,
        governed_run_id=startup.governed_run_id,
        monitor_id=startup.monitor_id,
        prompt_decision=prompt_decision,
        gate_decision=gate_decision,
        evidence_ids=startup.evidence_ids,
        block_reasons=block_reasons,
        runtime_exit_code=HOOK_EXIT_ALLOW if status == "allow" else RUNTIME_CONTROL_EXIT_BLOCK,
    )
    _write_runtime_control_records(root, run)
    return run


def memory_surface_report(
    root: Path | None = None,
    *,
    config_path: Path | None = None,
    memory_base: Path | None = None,
) -> MemorySurfaceReport:
    root = _root(root)
    config_path = (config_path or (Path.home() / ".codex" / "config.toml")).expanduser().resolve()
    memory_base = (memory_base or (Path.home() / ".codex" / "memories")).expanduser().resolve()
    config = _load_toml(config_path)
    servers = config.get("mcp_servers", {}) if isinstance(config.get("mcp_servers", {}), dict) else {}
    ams_server = servers.get("ams-memory") if isinstance(servers.get("ams-memory"), dict) else None
    codex_server = servers.get("codex-memory") if isinstance(servers.get("codex-memory"), dict) else None
    latest_migration = _load_json(root / "migration-latest.json")
    legacy_registry = memory_base / "MEMORY.md"
    migration_matches_legacy = bool(
        latest_migration
        and latest_migration.get("applied") is True
        and _same_path(latest_migration.get("source_path"), legacy_registry)
    )

    ams_root = _server_env_path(ams_server, "AMS_ROOT")
    ams_matches_root = ams_root is not None and _same_path(str(ams_root), root)
    ams_surface = MemorySurface(
        name="ams-memory",
        role="primary" if ams_matches_root else "unconfigured",
        status="pass" if ams_matches_root else "fail",
        configured=ams_server is not None,
        source_path=str(ams_root) if ams_root else None,
        detail=(
            "configured as primary AMS MCP for this root"
            if ams_matches_root
            else "missing or points at a different AMS root"
        ),
    )

    codex_surface = MemorySurface(
        name="codex-memory",
        role="secondary" if codex_server is not None and ams_matches_root else "unconfigured",
        status="pass" if codex_server is not None and ams_matches_root else "warn",
        configured=codex_server is not None,
        source_path=_server_env_string(codex_server, "CODEX_MEMORY_DB_PATH"),
        detail=(
            "configured only as secondary legacy/bridge input; AMS guarded startup is primary"
            if codex_server is not None and ams_matches_root
            else "not configured or AMS primary root is not established"
        ),
    )

    native_surface = MemorySurface(
        name="native-codex-memory",
        role="secondary_import_source" if legacy_registry.exists() else "unconfigured",
        status="pass" if migration_matches_legacy else ("warn" if legacy_registry.exists() else "pass"),
        configured=legacy_registry.exists(),
        source_path=str(legacy_registry) if legacy_registry.exists() else None,
        detail=(
            f"latest applied migration imports this registry via {latest_migration['run_id']}"
            if migration_matches_legacy and latest_migration
            else (
                "legacy registry exists but latest applied AMS migration does not point at it"
                if legacy_registry.exists()
                else "legacy registry not present"
            )
        ),
    )

    surfaces = [ams_surface, codex_surface, native_surface]
    reconciled = ams_surface.status == "pass" and codex_surface.role == "secondary" and native_surface.status == "pass"
    return MemorySurfaceReport(
        root=str(root),
        config_path=str(config_path),
        memory_base=str(memory_base),
        reconciled=reconciled,
        surfaces=surfaces,
    )


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
        completed_through=(
            "AMS product lock: kernel, MCP bridge, startup gate, hook wrappers, memory surface reconciliation, and governed-run close/finalize are live"
        ),
        current_phase="AMS Primary Runtime Adoption",
        status="active",
        next_step="add automatic real trace intake from ordinary Codex work",
        ready_for_next_phase=False,
        open_followups=[
            "add real trace intake from ordinary Codex work",
        ],
    )


def _migration_items_from_section(section: str, source_path: Path) -> list[MigrationItem]:
    source = str(source_path)
    items = [
        MigrationItem(
            item_id=_stable_id("pin", "active foundation"),
            action="pin",
            content="Keep AMS centered on verified experience that improves future action, not commodity memory storage.",
            source=source,
            reason="explicit AMS foundation directive from Codex memory registry",
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
            content="Do not let MCP, database, dashboard, or platform work outrun the AMS proof and usable operator loop.",
            source=source,
            reason="explicit anti-drift directive from Codex memory registry",
        ),
        MigrationItem(
            item_id=_stable_id("remember", "rerun verification"),
            action="remember",
            content="run pytest and synthetic eval before claiming AMS memory changes are complete",
            source=source,
            reason="verified prior workflow lesson from Codex memory registry",
            kind="skill",
            outcome="success",
            task_family="verification",
        ),
        MigrationItem(
            item_id=_stable_id("skip", "old snapshot counts"),
            action="skip",
            content="Do not import stale historical snapshot counts from the legacy Codex memory registry.",
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


def _write_governed_run_records(root: Path, receipt: GovernedRunReceipt) -> None:
    root.mkdir(parents=True, exist_ok=True)
    _append_jsonl(root / "governed-run-runs.jsonl", receipt.model_dump(mode="json"))
    _write_json(root / "governed-run-latest.json", receipt.model_dump(mode="json"))
    (root / "governed-run-latest.md").write_text(_render_governed_run_markdown(receipt), encoding="utf-8")


def _load_governed_run_receipt(root: Path, receipt_id: str | None) -> GovernedRunReceipt:
    if receipt_id is None:
        payload = _load_json(root / "governed-run-latest.json")
        if payload is None:
            raise ValueError("No governed run receipt exists to close.")
        return GovernedRunReceipt.model_validate(payload)

    runs_path = root / "governed-run-runs.jsonl"
    if not runs_path.exists():
        raise ValueError(f"Governed run receipt not found: {receipt_id}")
    for line in reversed(runs_path.read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        payload = json.loads(line)
        if payload.get("receipt_id") == receipt_id:
            return GovernedRunReceipt.model_validate(payload)
    raise ValueError(f"Governed run receipt not found: {receipt_id}")


def _write_runtime_control_records(root: Path, run: RuntimeControlRun) -> None:
    root.mkdir(parents=True, exist_ok=True)
    _append_jsonl(root / "runtime-control-runs.jsonl", run.model_dump(mode="json"))
    _write_json(root / "runtime-control-latest.json", run.model_dump(mode="json"))
    (root / "runtime-control-latest.md").write_text(_render_runtime_control_markdown(run), encoding="utf-8")


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
        f"- governed_run_id: `{run.governed_run_id}`",
        f"- action_brief_id: `{run.action_brief_id}`",
        f"- influence_id: `{run.influence_id}`",
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


def _render_governed_run_markdown(receipt: GovernedRunReceipt) -> str:
    lines = [
        "# AMS Governed Run Latest",
        "",
        f"- receipt_id: `{receipt.receipt_id}`",
        f"- status: `{receipt.status}`",
        f"- startup_brief_id: `{receipt.startup_brief_id}`",
        f"- action_brief_id: `{receipt.action_brief_id}`",
        f"- influence_id: `{receipt.influence_id}`",
        f"- monitor_id: `{receipt.monitor_id}`",
        f"- cwd: `{receipt.cwd}`",
        f"- task: {receipt.task_description}",
        f"- evidence_ids: `{len(receipt.evidence_ids)}`",
        f"- closed: `{receipt.closed}`",
        f"- outcome: `{receipt.outcome}`",
        f"- finalized_at: `{receipt.finalized_at}`",
        f"- influence_ids: `{len(receipt.influence_ids)}`",
    ]
    if receipt.block_reasons:
        lines.extend(["", "## Block Reasons", ""])
        for reason in receipt.block_reasons:
            lines.append(f"- `{reason}`")
    return "\n".join(lines) + "\n"


def _render_runtime_control_markdown(run: RuntimeControlRun) -> str:
    lines = [
        "# AMS Runtime Control Latest",
        "",
        f"- control_id: `{run.control_id}`",
        f"- status: `{run.status}`",
        f"- enforcement: `{run.enforcement}`",
        f"- runtime_exit_code: `{run.runtime_exit_code}`",
        f"- startup_brief_id: `{run.startup_brief_id}`",
        f"- governed_run_id: `{run.governed_run_id}`",
        f"- monitor_id: `{run.monitor_id}`",
        f"- prompt_decision: `{run.prompt_decision.decision}`",
        f"- gate_decision: `{run.gate_decision.decision}`",
        f"- cwd: `{run.cwd}`",
        f"- task: {run.task_description}",
        f"- evidence_ids: `{len(run.evidence_ids)}`",
    ]
    if run.block_reasons:
        lines.extend(["", "## Block Reasons", ""])
        for reason in run.block_reasons:
            lines.append(f"- `{reason}`")
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
    if directive.get("domain_scope") == GLOBAL_BEHAVIOR_SCOPE:
        return False
    if directive.get("scope") == "global":
        return False
    source = str(directive.get("source") or "")
    content = str(directive.get("content") or "")
    haystack = f"{source}\n{content}".casefold()
    markers = (
        "agentic memory system",
        "ams",
        "causal experience memory",
        "cem-0",
        "waki",
        "todo.md",
        "synthetic eval",
        "deterministic extractor",
        "contradiction detector",
    )
    return any(marker in haystack for marker in markers)


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


def _load_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _server_env_string(server: dict[str, Any] | None, name: str) -> str | None:
    if not server:
        return None
    env = server.get("env")
    if not isinstance(env, dict):
        return None
    value = env.get(name)
    return str(value) if value is not None else None


def _server_env_path(server: dict[str, Any] | None, name: str) -> Path | None:
    value = _server_env_string(server, name)
    if value is None:
        return None
    return Path(value).expanduser().resolve()


def _same_path(left: str | Path | None, right: str | Path | None) -> bool:
    if left is None or right is None:
        return False
    return Path(left).expanduser().resolve() == Path(right).expanduser().resolve()
