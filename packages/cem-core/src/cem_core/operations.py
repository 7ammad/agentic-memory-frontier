from __future__ import annotations

import hashlib
import json
import os
import re
import tomllib
from datetime import datetime, timezone
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
from .attribution import attribute_experience_record
from .compilers import BehaviorInvariantCompiler, SkillCompiler
from .kernel import CEM, card_is_inactive
from .local_memory import (
    default_root,
    init_memory,
    list_memory,
    pin_directive,
    remember_experience,
    retrieve_brief,
    run_eval,
)
from .models import (
    AgentTrace,
    BehaviorInvariant,
    DecisionIntent,
    ExperienceAttribution,
    ExperienceCard,
    ExperienceGraphRecord,
    SkillCandidate,
    StrictModel,
    TraceTurn,
    new_id,
    utc_now,
)

MigrationAction = Literal["pin", "remember", "skip"]
MaintenanceStatus = Literal["pass", "warn", "fail"]
MonitorStatus = Literal["pass", "fail"]
StartupStatus = Literal["allow", "degraded", "block"]

AMS_DOMAIN_SCOPE = "agentic-memory-system"
GLOBAL_BEHAVIOR_SCOPE = "codex-behavior"
RUNTIME_CONTROL_EXIT_BLOCK = 12
AMS_ACRONYM_PATTERN = re.compile(r"(?<![a-z0-9])ams(?![a-z0-9])")


def _startup_status(block_reasons: list[str], degraded_reasons: list[str]) -> StartupStatus:
    if block_reasons:
        return "block"
    if degraded_reasons:
        return "degraded"
    return "allow"


def _status_allows_work(status: StartupStatus) -> bool:
    return status in ("allow", "degraded")


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
    degraded_reasons: list[str] = Field(default_factory=list)


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
    degraded_reasons: list[str] = Field(default_factory=list)
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
    degraded_reasons: list[str] = Field(default_factory=list)
    runtime_exit_code: int


class RuntimeTraceRun(StrictModel):
    trace_id: str
    generated_at: datetime = Field(default_factory=utc_now)
    root: str
    control_id: str
    runtime_control_status: StartupStatus
    startup_brief_id: str
    governed_run_id: str | None
    monitor_id: str
    session_id: str
    task_description: str
    domain_scope: str | None
    task_family: str | None
    command: str
    command_args: list[str]
    downstream_invoked: bool
    observed_exit_code: int
    final_outcome: Literal["success", "failure", "partial", "unknown"]
    decision_id: str
    experience_record_id: str
    attribution_id: str
    attribution_class: Literal[
        "mistake",
        "approved_experiment_failure",
        "acceptable_tradeoff",
        "success",
        "unresolved",
    ]
    invariant_id: str | None = None
    skill_id: str | None = None
    proposed_atom_count: int
    proposed_atom_ids: list[str]
    source_turn_ids: list[str]


class MaintenanceItem(StrictModel):
    memory_id: str
    memory_kind: Literal["card", "atom"]
    status: MaintenanceStatus
    reason: str
    action: str
    promotion_status: str
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    last_validated_at: datetime | None = None
    age_days: float | None = None
    related_memory_ids: list[str] = Field(default_factory=list)


class MaintenanceSummary(StrictModel):
    active_card_count: int
    inactive_card_count: int
    expired_active_count: int
    stale_active_count: int
    contradicted_active_count: int
    pending_atom_count: int
    stale_pending_atom_count: int
    review_item_count: int


class MaintenanceRun(StrictModel):
    run_id: str = Field(default_factory=lambda: new_id("maintenance"))
    generated_at: datetime = Field(default_factory=utc_now)
    root: str
    status: MaintenanceStatus
    stale_after_days: int
    pending_atom_after_days: int
    summary: MaintenanceSummary
    items: list[MaintenanceItem]


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


def maintenance_review(
    root: Path | None = None,
    *,
    stale_after_days: int = 90,
    pending_atom_after_days: int = 14,
) -> MaintenanceRun:
    root = _root(root)
    if stale_after_days < 1:
        raise ValueError("stale_after_days must be at least 1.")
    if pending_atom_after_days < 1:
        raise ValueError("pending_atom_after_days must be at least 1.")

    init_memory(root)
    cem = CEM(root)
    now = utc_now()
    cards = cem.store.list_cards()
    atoms = cem.store.list_atoms()
    card_evidence_atom_ids = {atom_id for card in cards for atom_id in card.evidence_atom_ids}
    items: list[MaintenanceItem] = []
    expired_active_ids: set[str] = set()
    stale_active_ids: set[str] = set()
    contradicted_active_ids: set[str] = set()
    stale_pending_atom_ids: set[str] = set()

    for card in cards:
        if card_is_inactive(card):
            continue
        if _is_before(card.valid_until, now):
            expired_active_ids.add(card.card_id)
            items.append(
                MaintenanceItem(
                    memory_id=card.card_id,
                    memory_kind="card",
                    status="fail",
                    reason="active card is past valid_until and must not be treated as fresh memory",
                    action="run ams audit on this card, then supersede, deactivate, or extend validity with fresh evidence",
                    promotion_status=card.promotion_status,
                    valid_from=card.valid_from,
                    valid_until=card.valid_until,
                    last_validated_at=card.last_validated_at,
                    age_days=_age_days(_card_validation_anchor(card), now),
                )
            )
        else:
            validation_anchor = _card_validation_anchor(card)
            age_days = _age_days(validation_anchor, now)
            if validation_anchor is None:
                stale_active_ids.add(card.card_id)
                items.append(
                    MaintenanceItem(
                        memory_id=card.card_id,
                        memory_kind="card",
                        status="warn",
                        reason="active card has no validation freshness anchor",
                        action="run ams audit on this card and refresh it with trace-backed evidence before trusting it as fresh",
                        promotion_status=card.promotion_status,
                        valid_from=card.valid_from,
                        valid_until=card.valid_until,
                        last_validated_at=card.last_validated_at,
                        age_days=None,
                    )
                )
            elif age_days is not None and age_days >= stale_after_days:
                stale_active_ids.add(card.card_id)
                items.append(
                    MaintenanceItem(
                        memory_id=card.card_id,
                        memory_kind="card",
                        status="warn",
                        reason=f"active card has not been validated for {age_days:.1f} days",
                        action="run ams audit on this card and schedule a staleness probe or refresh it with new trace evidence",
                        promotion_status=card.promotion_status,
                        valid_from=card.valid_from,
                        valid_until=card.valid_until,
                        last_validated_at=card.last_validated_at,
                        age_days=age_days,
                    )
                )
        if card.contradicts_card_ids:
            contradicted_active_ids.add(card.card_id)
            items.append(
                MaintenanceItem(
                    memory_id=card.card_id,
                    memory_kind="card",
                    status="warn",
                    reason="active card has contradiction links that need operator review",
                    action="run ams audit on both linked memories and decide whether to keep scoped coexistence or supersede one side",
                    promotion_status=card.promotion_status,
                    valid_from=card.valid_from,
                    valid_until=card.valid_until,
                    last_validated_at=card.last_validated_at,
                    age_days=_age_days(_card_validation_anchor(card), now),
                    related_memory_ids=list(card.contradicts_card_ids),
                )
            )

    pending_atom_count = 0
    for atom in atoms:
        if atom.atom_id in card_evidence_atom_ids:
            continue
        if atom.promotion_status not in {"proposed", "candidate"}:
            continue
        pending_atom_count += 1
        age_days = _age_days(atom.last_confirmed_at or atom.observed_at, now)
        if age_days is None or age_days < pending_atom_after_days:
            continue
        stale_pending_atom_ids.add(atom.atom_id)
        items.append(
            MaintenanceItem(
                memory_id=atom.atom_id,
                memory_kind="atom",
                status="warn",
                reason=f"pending atom has waited {age_days:.1f} days without promotion, rejection, or quarantine",
                action="run ams audit on this atom, then confirm, reject, or promote it through normal validation",
                promotion_status=atom.promotion_status,
                valid_from=atom.valid_from,
                valid_until=atom.valid_until,
                last_validated_at=atom.last_confirmed_at,
                age_days=age_days,
                related_memory_ids=atom.source_trace_ids,
            )
        )

    status: MaintenanceStatus
    if any(item.status == "fail" for item in items):
        status = "fail"
    elif any(item.status == "warn" for item in items):
        status = "warn"
    else:
        status = "pass"

    summary = MaintenanceSummary(
        active_card_count=sum(1 for card in cards if not card_is_inactive(card)),
        inactive_card_count=sum(1 for card in cards if card_is_inactive(card)),
        expired_active_count=len(expired_active_ids),
        stale_active_count=len(stale_active_ids),
        contradicted_active_count=len(contradicted_active_ids),
        pending_atom_count=pending_atom_count,
        stale_pending_atom_count=len(stale_pending_atom_ids),
        review_item_count=len(items),
    )
    run = MaintenanceRun(
        root=str(root),
        status=status,
        stale_after_days=stale_after_days,
        pending_atom_after_days=pending_atom_after_days,
        summary=summary,
        items=items,
    )
    _write_maintenance_records(root, run)
    return run


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
    surfaces = memory_surface_report(root)
    checks.append(
        _check(
            "memory_surfaces_reconciled",
            surfaces.reconciled,
            _memory_surface_check_detail(surfaces),
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
    maintenance = maintenance_review(root)
    maintenance_detail = _maintenance_check_detail(maintenance)
    checks.append(
        _check(
            "maintenance_surface_present",
            (root / "maintenance-latest.json").exists(),
            f"{maintenance.status} {maintenance.run_id}; {maintenance_detail}",
        )
    )
    checks.append(
        _check(
            "maintenance_no_blocking_risks",
            maintenance.status != "fail",
            maintenance_detail,
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
        "latest_runtime_trace": _load_json(root / "runtime-trace-latest.json"),
        "latest_experience_graph_record": _load_json(root / "experience-graph-latest.json"),
        "latest_experience_attribution": _load_json(root / "experience-attribution-latest.json"),
        "latest_behavior_invariant": _load_json(root / "behavior-invariant-latest.json"),
        "latest_skill_candidate": _load_json(root / "skill-candidate-latest.json"),
        "latest_maintenance": _load_json(root / "maintenance-latest.json"),
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
    requires_ams_bootstrap_directives = domain_scope in (None, AMS_DOMAIN_SCOPE)
    required_directives = {
        "waki_boundary": True if not requires_ams_bootstrap_directives else "waki" in action_text,
        "verification_rule": True
        if not requires_ams_bootstrap_directives
        else "pytest" in action_text and "synthetic" in action_text,
        "todo_rule": True if not requires_ams_bootstrap_directives else "todo.md" in action_text,
    }
    block_reasons: list[str] = []
    degraded_reasons: list[str] = []
    if monitor.status != "pass":
        degraded_reasons.append(f"monitor_failed:{monitor.run_id}")
    for name, present in required_directives.items():
        if not present:
            reason = f"missing_required_directive:{name}"
            degraded_reasons.append(reason)

    receipt_id = new_id("run")
    run = StartupBriefRun(
        root=str(root),
        status=_startup_status(block_reasons, degraded_reasons),
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
        degraded_reasons=degraded_reasons,
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
        degraded_reasons=degraded_reasons,
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
    if _status_allows_work(receipt.status):
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
    """Build an enforceable AMS allow/degraded/block decision for a launcher.

    Codex command hooks currently report non-zero exits as hook failures but still
    continue. This control path is owned by AMS instead: a caller must run it before
    invoking the downstream command and must not invoke that command when
    runtime-control returns an action-safety block.
    """
    root = _root(root)
    prompt_decision = hook_on_user_prompt_submit(
        root,
        description,
        session_id=session_id,
        affected_files=affected_files or [],
    )
    gate_decision = hook_on_pre_tool_use_gate(root)

    block_reasons: list[str] = []
    degraded_reasons: list[str] = []
    startup_brief_id = "startup_brief_unavailable"
    governed_run_id: str | None = None
    monitor_id = "monitor_unavailable"
    evidence_ids: list[str] = []
    try:
        startup = startup_brief(
            root,
            description=description,
            domain_scope=domain_scope,
            task_family=task_family,
        )
        startup_brief_id = startup.brief_id
        governed_run_id = startup.governed_run_id
        monitor_id = startup.monitor_id
        evidence_ids = startup.evidence_ids
        if startup.status == "block":
            for reason in startup.block_reasons:
                block_reasons.append(f"startup_blocked:{reason}")
        for reason in startup.degraded_reasons:
            degraded_reasons.append(f"startup_degraded:{reason}")
    except Exception as exc:
        degraded_reasons.append(f"startup_brief_failed:{type(exc).__name__}:{exc}")
    if prompt_decision.decision == "block":
        block_reasons.append(f"correction_prompt_blocked:{prompt_decision.event_id}")
    if gate_decision.decision == "block":
        block_reasons.append(f"resume_gate_blocked:{gate_decision.active_event_id or 'unknown'}")

    status = _startup_status(block_reasons, degraded_reasons)
    run = RuntimeControlRun(
        root=str(root),
        cwd=str(Path.cwd().resolve()),
        enforcement="external_guard",
        status=status,
        task_description=description,
        domain_scope=domain_scope,
        task_family=task_family,
        session_id=session_id,
        startup_brief_id=startup_brief_id,
        governed_run_id=governed_run_id,
        monitor_id=monitor_id,
        prompt_decision=prompt_decision,
        gate_decision=gate_decision,
        evidence_ids=evidence_ids,
        block_reasons=block_reasons,
        degraded_reasons=degraded_reasons,
        runtime_exit_code=HOOK_EXIT_ALLOW if _status_allows_work(status) else RUNTIME_CONTROL_EXIT_BLOCK,
    )
    _write_runtime_control_records(root, run)
    return run


def record_runtime_trace(
    root: Path | None = None,
    *,
    control_id: str,
    command: str,
    command_args: list[str] | None = None,
    observed_exit_code: int,
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
) -> RuntimeTraceRun:
    root = _root(root)
    init_memory(root)
    command_args = command_args or []
    command = command.strip()
    if not command:
        raise ValueError("Runtime trace command must not be empty.")

    control = _load_runtime_control_run(root, control_id)
    downstream_invoked = _status_allows_work(control.status)
    final_outcome: Literal["success", "failure", "partial", "unknown"] = (
        "success" if downstream_invoked and observed_exit_code == 0 else "failure"
    )
    session_id = control.session_id or control.governed_run_id or control.control_id
    task_id = control.governed_run_id or control.control_id
    trace_started_at = started_at or control.generated_at
    trace_ended_at = ended_at or utc_now()
    control_summary = (
        f"AMS_RUNTIME_CONTROL: {control.status} {control.control_id}; "
        f"startup_brief={control.startup_brief_id}; "
        f"governed_run={control.governed_run_id}; monitor={control.monitor_id}"
    )
    command_summary = (
        f"COMMAND: {command}"
        + (f" {' '.join(command_args)}" if command_args else "")
        + f"\nINVOKED: {downstream_invoked}\nEXIT_CODE: {observed_exit_code}"
    )
    trace = AgentTrace(
        session_id=session_id,
        agent_id="codex",
        task_id=task_id,
        started_at=trace_started_at,
        ended_at=trace_ended_at,
        turns=[
            TraceTurn(
                index=0,
                timestamp=control.generated_at,
                role="user",
                content=control.task_description,
            ),
            TraceTurn(
                index=1,
                timestamp=control.generated_at,
                role="system",
                content=control_summary,
            ),
            TraceTurn(
                index=2,
                timestamp=trace_ended_at,
                role="tool" if downstream_invoked else "environment",
                content=command_summary,
                tool_name=Path(command).name,
                tool_input={"command": command, "args": command_args},
                tool_output={"exit_code": observed_exit_code, "invoked": downstream_invoked},
            ),
        ],
        final_outcome=final_outcome,
        outcome_score=1.0 if final_outcome == "success" else 0.0,
        environment={
            "domain": control.domain_scope or AMS_DOMAIN_SCOPE,
            "cwd": control.cwd,
            "trace_source": "ams-guarded-command",
            "runtime_control_id": control.control_id,
            "runtime_control_status": control.status,
            "startup_brief_id": control.startup_brief_id,
            "governed_run_id": control.governed_run_id,
            "monitor_id": control.monitor_id,
            "evidence_ids": control.evidence_ids,
            "block_reasons": control.block_reasons,
            "degraded_reasons": control.degraded_reasons,
            "command": command,
            "command_args": command_args,
            "observed_exit_code": observed_exit_code,
            "downstream_invoked": downstream_invoked,
        },
    )
    cem = CEM(root)
    cem.ingest_trace(trace)
    command_text = command + (f" {' '.join(command_args)}" if command_args else "")
    decision = DecisionIntent(
        trace_id=trace.trace_id,
        turn_id=trace.turns[2].turn_id,
        agent_id="codex",
        session_id=session_id,
        task_id=task_id,
        proposed_action=command_text,
        action_kind="command",
        expected_outcome=(
            "downstream command should complete successfully"
            if downstream_invoked
            else "blocked command should not execute downstream"
        ),
        applicable_authority="current_evidence",
        authority_refs=[control.control_id, control.startup_brief_id, control.monitor_id],
        approval_state="not_required",
        experiment_state="not_experiment",
        runtime_surface="ams-guarded-command",
        evidence_ids=[control.control_id, control.startup_brief_id, control.monitor_id, *control.evidence_ids],
    )
    experience_record = ExperienceGraphRecord(
        decision=decision,
        actual_outcome=(
            f"downstream_invoked={downstream_invoked}; observed_exit_code={observed_exit_code}; final_outcome={final_outcome}"
        ),
        outcome_status=final_outcome,
        scope_candidate="task",
        outcome_evidence_ids=[trace.trace_id],
    )
    attribution = attribute_experience_record(experience_record)
    experience_record.attribution_status = "attributed"
    experience_record.inference_receipt_id = attribution.attribution_id
    cem.store.save_experience_graph_record(experience_record)
    cem.store.save_experience_attribution(attribution)
    invariant = BehaviorInvariantCompiler().compile(experience_record, attribution)
    if invariant is not None:
        cem.store.save_behavior_invariant(invariant)
    skill = SkillCompiler().compile(experience_record, attribution)
    if skill is not None:
        cem.store.save_skill_candidate(skill)
    atoms = cem.propose_memories(trace.trace_id)
    run = RuntimeTraceRun(
        trace_id=trace.trace_id,
        root=str(root),
        control_id=control.control_id,
        runtime_control_status=control.status,
        startup_brief_id=control.startup_brief_id,
        governed_run_id=control.governed_run_id,
        monitor_id=control.monitor_id,
        session_id=session_id,
        task_description=control.task_description,
        domain_scope=control.domain_scope,
        task_family=control.task_family,
        command=command,
        command_args=command_args,
        downstream_invoked=downstream_invoked,
        observed_exit_code=observed_exit_code,
        final_outcome=final_outcome,
        decision_id=decision.decision_id,
        experience_record_id=experience_record.record_id,
        attribution_id=attribution.attribution_id,
        attribution_class=attribution.attribution_class,
        invariant_id=invariant.invariant_id if invariant is not None else None,
        skill_id=skill.skill_id if skill is not None else None,
        proposed_atom_count=len(atoms),
        proposed_atom_ids=[atom.atom_id for atom in atoms],
        source_turn_ids=[turn.turn_id for turn in trace.turns],
    )
    _write_runtime_trace_records(root, run)
    _write_experience_graph_records(root, experience_record)
    _write_experience_attribution_records(root, attribution)
    if invariant is not None:
        _write_behavior_invariant_records(root, invariant)
    if skill is not None:
        _write_skill_candidate_records(root, skill)
    return run


def memory_surface_report(
    root: Path | None = None,
    *,
    config_path: Path | None = None,
    memory_base: Path | None = None,
) -> MemorySurfaceReport:
    root = _root(root)
    config_path = (
        config_path
        or _env_path("AMS_CODEX_CONFIG_PATH")
        or (Path.home() / ".codex" / "config.toml")
    ).expanduser().resolve()
    memory_base = (
        memory_base
        or _env_path("AMS_MEMORY_BASE")
        or (Path.home() / ".codex" / "memories")
    ).expanduser().resolve()
    config = _load_toml(config_path)
    native_codex_memories_disabled = _native_codex_memories_disabled(config)
    servers = config.get("mcp_servers", {}) if isinstance(config.get("mcp_servers", {}), dict) else {}
    ams_server = servers.get("ams-memory") if isinstance(servers.get("ams-memory"), dict) else None
    codex_server = servers.get("codex-memory") if isinstance(servers.get("codex-memory"), dict) else None
    latest_migration = _load_latest_applied_migration(root)
    legacy_registry = memory_base / "MEMORY.md"
    migration_matches_legacy = bool(
        latest_migration
        and latest_migration.get("applied") is True
        and _same_path(latest_migration.get("source_path"), legacy_registry)
    )

    ams_root = _server_configured_root(ams_server)
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

    codex_configured_as_secondary = codex_server is not None and ams_matches_root
    if codex_configured_as_secondary:
        codex_detail = "configured only as secondary legacy/bridge input; AMS guarded startup is primary"
    elif ams_matches_root:
        codex_detail = "optional secondary legacy/bridge input is not configured; AMS guarded startup is primary"
    else:
        codex_detail = "not configured or AMS primary root is not established"
    codex_surface = MemorySurface(
        name="codex-memory",
        role="secondary" if codex_configured_as_secondary else "unconfigured",
        status="pass" if codex_configured_as_secondary else "warn",
        configured=codex_server is not None,
        source_path=_server_env_string(codex_server, "CODEX_MEMORY_DB_PATH"),
        detail=codex_detail,
    )

    native_role: Literal["secondary_import_source", "unconfigured"] = (
        "secondary_import_source" if legacy_registry.exists() else "unconfigured"
    )
    if native_codex_memories_disabled:
        native_status: Literal["pass", "warn", "fail"] = "pass"
        if migration_matches_legacy and latest_migration:
            native_detail = (
                "native Codex Memories disabled by Codex config; "
                f"latest applied migration imports this registry via {latest_migration['run_id']}"
            )
        elif legacy_registry.exists():
            native_detail = (
                "native Codex Memories disabled by Codex config; registry is inactive default memory "
                "and may only be used as AMS-pointed evidence/migration input"
            )
        else:
            native_detail = "native Codex Memories disabled by Codex config; legacy registry not present"
    else:
        native_status = "pass" if migration_matches_legacy else ("warn" if legacy_registry.exists() else "pass")
        native_detail = (
            f"latest applied migration imports this registry via {latest_migration['run_id']}"
            if migration_matches_legacy and latest_migration
            else (
                "legacy registry exists but latest applied AMS migration does not point at it"
                if legacy_registry.exists()
                else "legacy registry not present"
            )
        )
    native_surface = MemorySurface(
        name="native-codex-memory",
        role=native_role,
        status=native_status,
        configured=legacy_registry.exists(),
        source_path=str(legacy_registry) if legacy_registry.exists() else None,
        detail=native_detail,
    )

    surfaces = [ams_surface, codex_surface, native_surface]
    reconciled = ams_surface.status == "pass" and (
        native_codex_memories_disabled
        or (codex_surface.role == "secondary" and native_surface.status == "pass")
    )
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
            "AMS v1 product lock is accepted; AMS V2 Phase 9 eval harness is complete with NonRepeatEval, FalseBlockEval, ApprovedExperimentEval, SkillTransferEval, SupersessionEval, MultiAgentConflictEval, and ContextPollutionEval"
        ),
        current_phase="AMS V2 Phase 10 - Operator proof and release lock",
        status="active",
        next_step=(
            "implement one-command V2 operator proof, dashboard/monitor V2 release status, audit docs, review prompts, and product-lock update"
        ),
        ready_for_next_phase=False,
        open_followups=[
            "V2 Phase 10 operator proof and release lock implementation is pending",
            "V2 independent review receipt remains pending until Phase 10",
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


def _write_runtime_trace_records(root: Path, run: RuntimeTraceRun) -> None:
    root.mkdir(parents=True, exist_ok=True)
    _append_jsonl(root / "runtime-trace-runs.jsonl", run.model_dump(mode="json"))
    _write_json(root / "runtime-trace-latest.json", run.model_dump(mode="json"))
    (root / "runtime-trace-latest.md").write_text(_render_runtime_trace_markdown(run), encoding="utf-8")


def _write_experience_graph_records(root: Path, record: ExperienceGraphRecord) -> None:
    root.mkdir(parents=True, exist_ok=True)
    _append_jsonl(root / "experience-graph-runs.jsonl", record.model_dump(mode="json"))
    _write_json(root / "experience-graph-latest.json", record.model_dump(mode="json"))
    (root / "experience-graph-latest.md").write_text(_render_experience_graph_markdown(record), encoding="utf-8")


def _write_experience_attribution_records(root: Path, attribution: ExperienceAttribution) -> None:
    root.mkdir(parents=True, exist_ok=True)
    _append_jsonl(root / "experience-attribution-runs.jsonl", attribution.model_dump(mode="json"))
    _write_json(root / "experience-attribution-latest.json", attribution.model_dump(mode="json"))
    (root / "experience-attribution-latest.md").write_text(
        _render_experience_attribution_markdown(attribution),
        encoding="utf-8",
    )


def _write_behavior_invariant_records(root: Path, invariant: BehaviorInvariant) -> None:
    root.mkdir(parents=True, exist_ok=True)
    _append_jsonl(root / "behavior-invariant-runs.jsonl", invariant.model_dump(mode="json"))
    _write_json(root / "behavior-invariant-latest.json", invariant.model_dump(mode="json"))
    (root / "behavior-invariant-latest.md").write_text(
        _render_behavior_invariant_markdown(invariant),
        encoding="utf-8",
    )


def _write_skill_candidate_records(root: Path, skill: SkillCandidate) -> None:
    root.mkdir(parents=True, exist_ok=True)
    _append_jsonl(root / "skill-candidate-runs.jsonl", skill.model_dump(mode="json"))
    _write_json(root / "skill-candidate-latest.json", skill.model_dump(mode="json"))
    (root / "skill-candidate-latest.md").write_text(
        _render_skill_candidate_markdown(skill),
        encoding="utf-8",
    )


def _write_maintenance_records(root: Path, run: MaintenanceRun) -> None:
    root.mkdir(parents=True, exist_ok=True)
    _append_jsonl(root / "maintenance-runs.jsonl", run.model_dump(mode="json"))
    _write_json(root / "maintenance-latest.json", run.model_dump(mode="json"))
    (root / "maintenance-latest.md").write_text(_render_maintenance_markdown(run), encoding="utf-8")


def _load_runtime_control_run(root: Path, control_id: str) -> RuntimeControlRun:
    runs_path = root / "runtime-control-runs.jsonl"
    if not runs_path.exists():
        raise ValueError(f"Runtime control receipt not found: {control_id}")
    for line in reversed(runs_path.read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        payload = json.loads(line)
        if payload.get("control_id") == control_id:
            return RuntimeControlRun.model_validate(payload)
    raise ValueError(f"Runtime control receipt not found: {control_id}")


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
    if run.degraded_reasons:
        lines.extend(["", "## Degraded Reasons", ""])
        for reason in run.degraded_reasons:
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
    if receipt.degraded_reasons:
        lines.extend(["", "## Degraded Reasons", ""])
        for reason in receipt.degraded_reasons:
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
    if run.degraded_reasons:
        lines.extend(["", "## Degraded Reasons", ""])
        for reason in run.degraded_reasons:
            lines.append(f"- `{reason}`")
    return "\n".join(lines) + "\n"


def _render_runtime_trace_markdown(run: RuntimeTraceRun) -> str:
    lines = [
        "# AMS Runtime Trace Latest",
        "",
        f"- trace_id: `{run.trace_id}`",
        f"- control_id: `{run.control_id}`",
        f"- runtime_control_status: `{run.runtime_control_status}`",
        f"- final_outcome: `{run.final_outcome}`",
        f"- observed_exit_code: `{run.observed_exit_code}`",
        f"- downstream_invoked: `{run.downstream_invoked}`",
        f"- startup_brief_id: `{run.startup_brief_id}`",
        f"- governed_run_id: `{run.governed_run_id}`",
        f"- monitor_id: `{run.monitor_id}`",
        f"- session_id: `{run.session_id}`",
        f"- command: `{run.command}`",
        f"- command_args: `{len(run.command_args)}`",
        f"- decision_id: `{run.decision_id}`",
        f"- experience_record_id: `{run.experience_record_id}`",
        f"- attribution_id: `{run.attribution_id}`",
        f"- attribution_class: `{run.attribution_class}`",
        f"- invariant_id: `{run.invariant_id}`",
        f"- skill_id: `{run.skill_id}`",
        f"- proposed_atoms: `{run.proposed_atom_count}`",
    ]
    if run.proposed_atom_ids:
        lines.extend(["", "## Proposed Atoms", ""])
        for atom_id in run.proposed_atom_ids:
            lines.append(f"- `{atom_id}`")
    return "\n".join(lines) + "\n"


def _render_experience_graph_markdown(record: ExperienceGraphRecord) -> str:
    audit = record.audit_summary()
    lines = [
        "# AMS V2 Experience Graph Latest",
        "",
        f"- record_id: `{record.record_id}`",
        f"- decision_id: `{record.decision.decision_id}`",
        f"- action_kind: `{record.decision.action_kind}`",
        f"- authority: `{record.decision.applicable_authority}`",
        f"- scope_candidate: `{record.scope_candidate}`",
        f"- outcome_status: `{record.outcome_status}`",
        f"- attribution_status: `{record.attribution_status}`",
        f"- inference_receipt_id: `{record.inference_receipt_id}`",
        f"- runtime_surface: `{record.decision.runtime_surface}`",
        f"- evidence_ids: `{len(audit['evidence_ids'])}`",
    ]
    return "\n".join(lines) + "\n"


def _render_experience_attribution_markdown(attribution: ExperienceAttribution) -> str:
    lines = [
        "# AMS V2 Experience Attribution Latest",
        "",
        f"- attribution_id: `{attribution.attribution_id}`",
        f"- record_id: `{attribution.record_id}`",
        f"- decision_id: `{attribution.decision_id}`",
        f"- attribution_class: `{attribution.attribution_class}`",
        f"- scope_candidate: `{attribution.scope_candidate}`",
        f"- authority_basis: `{attribution.authority_basis}`",
        f"- non_repeat_candidate: `{attribution.non_repeat_candidate}`",
        f"- invariant_candidate: `{attribution.invariant_candidate}`",
        f"- skill_candidate: `{attribution.skill_candidate}`",
        f"- approved_experiment_exclusion: `{attribution.approved_experiment_exclusion}`",
        f"- needs_owner_review: `{attribution.needs_owner_review}`",
        f"- evidence_ids: `{len(attribution.evidence_ids)}`",
    ]
    return "\n".join(lines) + "\n"


def _render_behavior_invariant_markdown(invariant: BehaviorInvariant) -> str:
    lines = [
        "# AMS V2 Behavior Invariant Latest",
        "",
        f"- invariant_id: `{invariant.invariant_id}`",
        f"- source_attribution_id: `{invariant.source_attribution_id}`",
        f"- authority: `{invariant.authority}`",
        f"- scope: `{invariant.scope}`",
        f"- enforcement: `{invariant.enforcement}`",
        f"- supersession_status: `{invariant.supersession_status}`",
        f"- evidence_ids: `{len(invariant.evidence_ids)}`",
    ]
    return "\n".join(lines) + "\n"


def _render_skill_candidate_markdown(skill: SkillCandidate) -> str:
    lines = [
        "# AMS V2 Skill Candidate Latest",
        "",
        f"- skill_id: `{skill.skill_id}`",
        f"- source_attribution_id: `{skill.source_attribution_id}`",
        f"- transfer_scope: `{skill.transfer_scope}`",
        f"- promotion_status: `{skill.promotion_status}`",
        f"- preconditions: `{len(skill.preconditions)}`",
        f"- procedure_steps: `{len(skill.procedure)}`",
        f"- when_not_to_apply: `{len(skill.when_not_to_apply)}`",
        f"- evidence_ids: `{len(skill.evidence_ids)}`",
    ]
    return "\n".join(lines) + "\n"


def _render_maintenance_markdown(run: MaintenanceRun) -> str:
    lines = [
        "# AMS Maintenance Latest",
        "",
        f"- run_id: `{run.run_id}`",
        f"- status: `{run.status}`",
        f"- root: `{run.root}`",
        f"- stale_after_days: `{run.stale_after_days}`",
        f"- pending_atom_after_days: `{run.pending_atom_after_days}`",
        f"- active_cards: `{run.summary.active_card_count}`",
        f"- inactive_cards: `{run.summary.inactive_card_count}`",
        f"- expired_active: `{run.summary.expired_active_count}`",
        f"- stale_active: `{run.summary.stale_active_count}`",
        f"- contradicted_active: `{run.summary.contradicted_active_count}`",
        f"- pending_atoms: `{run.summary.pending_atom_count}`",
        f"- stale_pending_atoms: `{run.summary.stale_pending_atom_count}`",
        "",
        "## Review Items",
        "",
    ]
    if not run.items:
        lines.append("- none")
    for item in run.items:
        lines.append(f"- `{item.status}` `{item.memory_kind}` `{item.memory_id}`: {item.reason} -> {item.action}")
        if item.related_memory_ids:
            lines.append(f"  - related: `{', '.join(item.related_memory_ids)}`")
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


def _maintenance_check_detail(run: MaintenanceRun) -> str:
    return (
        f"status={run.status}; "
        f"expired_active={run.summary.expired_active_count}; "
        f"stale_active={run.summary.stale_active_count}; "
        f"contradicted_active={run.summary.contradicted_active_count}; "
        f"inactive={run.summary.inactive_card_count}; "
        f"stale_pending_atoms={run.summary.stale_pending_atom_count}"
    )


def _memory_surface_check_detail(report: MemorySurfaceReport) -> str:
    if report.reconciled:
        details: list[str] = []
        for surface in report.surfaces:
            if surface.name == "ams-memory":
                details.append(f"ams-memory {surface.role}")
            elif surface.name == "codex-memory":
                if surface.role == "secondary":
                    details.append("codex-memory optional secondary configured")
                else:
                    details.append("codex-memory optional bridge unconfigured")
            elif surface.name == "native-codex-memory":
                if "disabled by Codex config" in surface.detail:
                    details.append("native Codex memory disabled/import-only")
                elif surface.status == "pass":
                    details.append("native import current")
        return "reconciled: " + "; ".join(details)
    details = [
        f"{surface.name}={surface.status}/{surface.role}: {surface.detail}"
        for surface in report.surfaces
        if surface.status != "pass" or surface.role == "unconfigured"
    ]
    return "not reconciled; " + "; ".join(details)


def _as_utc_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _is_before(value: datetime | None, now: datetime) -> bool:
    value = _as_utc_datetime(value)
    return value is not None and value < now


def _age_days(anchor: datetime | None, now: datetime) -> float | None:
    anchor = _as_utc_datetime(anchor)
    if anchor is None:
        return None
    return round(max(0.0, (now - anchor).total_seconds() / 86400.0), 1)


def _card_validation_anchor(card: ExperienceCard) -> datetime | None:
    return card.last_validated_at or card.valid_from


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
    phrase_markers = (
        "agentic memory system",
        "causal experience memory",
        "cem-0",
        "waki",
        "todo.md",
        "synthetic eval",
        "deterministic extractor",
        "contradiction detector",
    )
    return any(marker in haystack for marker in phrase_markers) or AMS_ACRONYM_PATTERN.search(haystack) is not None


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


def _load_latest_applied_migration(root: Path) -> dict[str, Any] | None:
    runs_path = root / "migration-runs.jsonl"
    if runs_path.exists():
        for line in reversed(runs_path.read_text(encoding="utf-8").splitlines()):
            if not line.strip():
                continue
            payload = json.loads(line)
            if payload.get("applied") is True:
                return payload
    latest = _load_json(root / "migration-latest.json")
    if latest and latest.get("applied") is True:
        return latest
    return None


def _env_path(name: str) -> Path | None:
    value = os.environ.get(name)
    return Path(value) if value else None


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


def _server_configured_root(server: dict[str, Any] | None) -> Path | None:
    return (
        _server_env_path(server, "AMS_ROOT")
        or _server_env_path(server, "CEM_ROOT")
        or _server_arg_path(server, "--root")
    )


def _native_codex_memories_disabled(config: dict[str, Any]) -> bool:
    features = config.get("features")
    memories = config.get("memories")
    features = features if isinstance(features, dict) else {}
    memories = memories if isinstance(memories, dict) else {}
    return (
        features.get("memories") is False
        and memories.get("generate_memories") is False
        and memories.get("use_memories") is False
    )


def _server_arg_path(server: dict[str, Any] | None, flag: str) -> Path | None:
    if not server:
        return None
    args = server.get("args")
    if not isinstance(args, list):
        return None
    for index, raw_arg in enumerate(args):
        arg = str(raw_arg)
        if arg == flag and index + 1 < len(args):
            return Path(str(args[index + 1])).expanduser().resolve()
        prefix = f"{flag}="
        if arg.startswith(prefix):
            return Path(arg[len(prefix):]).expanduser().resolve()
    return None


def _same_path(left: str | Path | None, right: str | Path | None) -> bool:
    if left is None or right is None:
        return False
    return Path(left).expanduser().resolve() == Path(right).expanduser().resolve()
