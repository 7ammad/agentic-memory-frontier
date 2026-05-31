from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import Field

from .local_memory import default_root, init_memory, pin_directive, remember_experience, retrieve_brief
from .models import StrictModel, new_id, utc_now

CorrectionCategory = Literal[
    "workflow_violation",
    "premature_implementation",
    "scope_trimming",
    "source_skipping",
    "generic_framing",
    "memory_miss",
    "fake_completion",
    "repeated_drift",
    "approval_gate_violation",
]
CorrectionRouteTarget = Literal[
    "ams_directive",
    "cem_candidate_experience_atom",
    "project_ledger_entry",
    "stale_or_contradicted_memory",
    "human_approval_gate",
]
CorrectionRouteStatus = Literal["written", "pending", "skipped"]
CorrectionResumeStatus = Literal["blocked", "resumed"]
CorrectionGateStatus = Literal["clear", "blocked"]

AMS_DOMAIN_SCOPE = "agentic-memory-system"
GLOBAL_BEHAVIOR_SCOPE = "codex-behavior"
MISTAKE_CAPTURE_TASK_FAMILY = "mistake-capture"


class CorrectionRoute(StrictModel):
    target: CorrectionRouteTarget
    status: CorrectionRouteStatus
    detail: str
    ids: list[str] = Field(default_factory=list)


class CorrectionEvent(StrictModel):
    event_id: str = Field(default_factory=lambda: new_id("correction"))
    detected_at: datetime = Field(default_factory=utc_now)
    root: str
    source: str = "manual"
    user_text: str
    mistake: str
    categories: list[CorrectionCategory]
    affected_files: list[str] = Field(default_factory=list)
    affected_actions: list[str] = Field(default_factory=list)
    stale_memory_ids: list[str] = Field(default_factory=list)
    route_targets: list[CorrectionRouteTarget]
    routes: list[CorrectionRoute] = Field(default_factory=list)
    resume_required: bool = True
    resume_status: CorrectionResumeStatus = "blocked"
    resume_token: str = Field(default_factory=lambda: new_id("resume"))
    domain_scope: str | None = AMS_DOMAIN_SCOPE
    task_family: str | None = MISTAKE_CAPTURE_TASK_FAMILY
    session_id: str | None = None


class CorrectionGate(StrictModel):
    status: CorrectionGateStatus
    updated_at: datetime = Field(default_factory=utc_now)
    active_event_id: str | None = None
    resume_token: str | None = None
    reason: str | None = None


class CorrectionResumeReceipt(StrictModel):
    event_id: str
    resumed_at: datetime = Field(default_factory=utc_now)
    approved_by: str
    note: str | None = None
    gate: CorrectionGate


class CorrectionControllerSummary(StrictModel):
    root: str
    event_count: int
    latest_event_id: str | None
    active_gate: bool
    active_event_id: str | None
    latest_event_path: str
    event_log_path: str
    gate_path: str


_CATEGORY_PATTERNS: dict[CorrectionCategory, tuple[str, ...]] = {
    "workflow_violation": (
        r"\bi shouldn't have to tell you this\b",
        r"\bworkflow\b.*\bviolat",
        r"\bviolat(?:ed|ion)\b",
        r"\bwrong order\b",
        r"\bexecution-order\b",
        r"\bexecution order\b",
    ),
    "premature_implementation": (
        r"\bbuilding before planning\b",
        r"\bimplement(?:ing|ation)? before (?:the )?plan",
        r"\bscaffold(?:ed|ing)? before (?:the )?plan",
        r"\bplan first\b",
        r"\bbefore (?:the )?plan was approved\b",
        r"\bfull plan (?:was )?approved\b",
    ),
    "scope_trimming": (
        r"\btrim(?:med|ming)? it\b",
        r"\btrim(?:med|ming)? .*scope\b",
        r"\btoo conservative\b",
        r"\bskeleton\b",
        r"\bwater(?:ed)? down\b",
    ),
    "source_skipping": (
        r"\bdidn't read (?:the )?source\b",
        r"\bdid not read (?:the )?source\b",
        r"\bskipp(?:ed|ing) (?:the )?source\b",
        r"\bread (?:the )?(?:real )?source\b",
        r"\bsource[- ]skipping\b",
    ),
    "generic_framing": (
        r"\bhalf[- ]baked\b",
        r"\bgeneric\b",
        r"\bvague\b",
        r"\bplaceholder\b",
    ),
    "memory_miss": (
        r"\bsave this to memory\b",
        r"\bremember this\b",
        r"\bmemory miss\b",
        r"\byou forgot\b",
    ),
    "fake_completion": (
        r"\bclaim(?:ed|ing)? completion\b",
        r"\bsaid (?:it was )?done\b",
        r"\bwithout verification\b",
        r"\bdidn't verify\b",
        r"\bdid not verify\b",
        r"\bfake completion\b",
    ),
    "repeated_drift": (
        r"\bwe already said no\b",
        r"\balready told you\b",
        r"\bagain\b",
        r"\brepeated\b",
        r"\bkept doing\b",
    ),
    "approval_gate_violation": (
        r"\bapproval\b",
        r"\bapproved\b",
        r"\bwithout asking\b",
        r"\bpermission\b",
        r"\bgate\b",
    ),
}

_CATEGORY_PRIORITY: tuple[CorrectionCategory, ...] = (
    "premature_implementation",
    "approval_gate_violation",
    "source_skipping",
    "scope_trimming",
    "fake_completion",
    "memory_miss",
    "repeated_drift",
    "workflow_violation",
    "generic_framing",
)


def capture_correction(
    root: Path | None,
    user_text: str,
    *,
    affected_files: list[str] | None = None,
    affected_actions: list[str] | None = None,
    stale_memory_ids: list[str] | None = None,
    source: str = "manual",
    domain_scope: str | None = AMS_DOMAIN_SCOPE,
    task_family: str | None = MISTAKE_CAPTURE_TASK_FAMILY,
    session_id: str | None = None,
    project_ledger: Path | None = None,
) -> CorrectionEvent:
    root = _root(root)
    init_memory(root)
    affected_files = affected_files or []
    affected_actions = affected_actions or []
    stale_memory_ids = stale_memory_ids or []
    _reject_waki_paths([Path(item) for item in affected_files])
    if project_ledger is not None:
        _reject_waki_paths([project_ledger])

    categories = classify_correction(user_text)
    if not categories:
        raise ValueError("No correction signal detected. Add clearer correction text before recording memory.")

    event = CorrectionEvent(
        root=str(root),
        source=source,
        user_text=user_text,
        mistake=_mistake_summary(categories, user_text),
        categories=categories,
        affected_files=affected_files,
        affected_actions=affected_actions,
        stale_memory_ids=stale_memory_ids,
        route_targets=_route_targets(categories, stale_memory_ids),
        domain_scope=domain_scope,
        task_family=task_family,
        session_id=session_id,
    )
    event.routes = _apply_routes(root, event, project_ledger=project_ledger)
    _write_correction_event(root, event)
    _write_gate(
        root,
        CorrectionGate(
            status="blocked",
            active_event_id=event.event_id,
            resume_token=event.resume_token,
            reason=event.mistake,
        ),
    )
    return event


def classify_correction(user_text: str) -> list[CorrectionCategory]:
    normalized = _normalize(user_text)
    categories: list[CorrectionCategory] = []
    for category in _CATEGORY_PRIORITY:
        patterns = _CATEGORY_PATTERNS[category]
        if any(re.search(pattern, normalized) for pattern in patterns):
            categories.append(category)

    if "premature_implementation" in categories and "workflow_violation" not in categories:
        categories.append("workflow_violation")
    if "approval_gate_violation" in categories and "workflow_violation" not in categories:
        categories.append("workflow_violation")
    if "repeated_drift" in categories and "memory_miss" not in categories:
        categories.append("memory_miss")
    return categories


def correction_gate_status(root: Path | None = None) -> CorrectionGate:
    root = _root(root)
    path = _gate_path(root)
    if not path.exists():
        gate = CorrectionGate(status="clear")
        _write_gate(root, gate)
        return gate
    return CorrectionGate.model_validate_json(path.read_text(encoding="utf-8"))


def resume_correction(
    root: Path | None,
    event_id: str,
    *,
    approved_by: str,
    note: str | None = None,
) -> CorrectionResumeReceipt:
    root = _root(root)
    gate = correction_gate_status(root)
    if gate.status == "blocked" and gate.active_event_id != event_id:
        raise ValueError(f"Correction resume gate is blocked by {gate.active_event_id}, not {event_id}.")

    cleared = CorrectionGate(status="clear")
    receipt = CorrectionResumeReceipt(
        event_id=event_id,
        approved_by=approved_by,
        note=note,
        gate=cleared,
    )
    _mark_event_resumed(root, event_id)
    _append_jsonl(_resume_log_path(root), receipt.model_dump(mode="json"))
    _write_gate(root, cleared)
    return receipt


def list_corrections(root: Path | None = None, *, limit: int = 20) -> dict[str, object]:
    root = _root(root)
    events = _load_events(root)
    if limit > 0:
        events = events[-limit:]
    return {
        "root": str(root),
        "events": [event.model_dump(mode="json") for event in events],
        "gate": correction_gate_status(root).model_dump(mode="json"),
    }


def correction_controller_summary(root: Path | None = None) -> CorrectionControllerSummary:
    root = _root(root)
    gate = correction_gate_status(root)
    events = _load_events(root)
    latest_event_id = events[-1].event_id if events else None
    return CorrectionControllerSummary(
        root=str(root),
        event_count=len(events),
        latest_event_id=latest_event_id,
        active_gate=gate.status == "blocked",
        active_event_id=gate.active_event_id,
        latest_event_path=str(_latest_event_path(root)),
        event_log_path=str(_event_log_path(root)),
        gate_path=str(_gate_path(root)),
    )


def correction_rule_surfaces_in_brief(root: Path | None = None) -> bool:
    root = _root(root)
    brief = retrieve_brief(
        root,
        "continue Correction Capture Controller mistake-capture work with resume gate",
        domain_scope=AMS_DOMAIN_SCOPE,
        task_family=MISTAKE_CAPTURE_TASK_FAMILY,
    )
    actions = "\n".join(brief["recommended_next_actions"]).lower()
    return "correction" in actions and "resume" in actions


def _apply_routes(root: Path, event: CorrectionEvent, *, project_ledger: Path | None) -> list[CorrectionRoute]:
    routes: list[CorrectionRoute] = []
    if "ams_directive" in event.route_targets:
        directive = pin_directive(
            root,
            _directive_content(event),
            source=f"Correction Capture Controller {event.event_id}",
            scope="global",
            domain_scope=GLOBAL_BEHAVIOR_SCOPE,
            task_family=MISTAKE_CAPTURE_TASK_FAMILY,
        )
        routes.append(
            CorrectionRoute(
                target="ams_directive",
                status="written" if directive["created"] else "skipped",
                detail="directive pinned" if directive["created"] else "matching directive already existed",
                ids=[str(directive["directive"]["directive_id"])],
            )
        )

    if "cem_candidate_experience_atom" in event.route_targets:
        remembered = remember_experience(
            root,
            _cem_failure_content(event),
            kind="failure",
            outcome="failure",
            domain_scope=event.domain_scope,
            task_family=event.task_family,
            session_id=event.session_id,
        )
        ids = [str(remembered["trace_id"])]
        ids.extend(str(atom["atom_id"]) for atom in remembered["atoms"])
        ids.extend(str(card["card_id"]) for card in remembered["promoted_cards"])
        routes.append(
            CorrectionRoute(
                target="cem_candidate_experience_atom",
                status="written",
                detail=(
                    f"{remembered['proposed_count']} proposed, "
                    f"{remembered['promoted_count']} promoted, "
                    f"{remembered['quarantined_count']} quarantined"
                ),
                ids=ids,
            )
        )

    if "project_ledger_entry" in event.route_targets:
        if project_ledger is None:
            routes.append(
                CorrectionRoute(
                    target="project_ledger_entry",
                    status="pending",
                    detail="project ledger path was not supplied",
                )
            )
        else:
            _append_project_ledger_entry(project_ledger, event)
            routes.append(
                CorrectionRoute(
                    target="project_ledger_entry",
                    status="written",
                    detail=str(project_ledger),
                    ids=[event.event_id],
                )
            )

    if "stale_or_contradicted_memory" in event.route_targets:
        status: CorrectionRouteStatus = "written" if event.stale_memory_ids else "pending"
        detail = (
            "stale or contradicted memory ids linked"
            if event.stale_memory_ids
            else "no stale memory ids supplied; review required"
        )
        routes.append(
            CorrectionRoute(
                target="stale_or_contradicted_memory",
                status=status,
                detail=detail,
                ids=event.stale_memory_ids,
            )
        )

    routes.append(
        CorrectionRoute(
            target="human_approval_gate",
            status="written",
            detail="resume gate blocked until explicit approval",
            ids=[event.resume_token],
        )
    )
    return routes


def _route_targets(
    categories: list[CorrectionCategory],
    stale_memory_ids: list[str],
) -> list[CorrectionRouteTarget]:
    targets: list[CorrectionRouteTarget] = [
        "ams_directive",
        "cem_candidate_experience_atom",
        "project_ledger_entry",
    ]
    if "memory_miss" in categories or "repeated_drift" in categories or stale_memory_ids:
        targets.append("stale_or_contradicted_memory")
    targets.append("human_approval_gate")
    return targets


def _mistake_summary(categories: list[CorrectionCategory], user_text: str) -> str:
    if "premature_implementation" in categories:
        return "Agent started implementation or scaffolding before the requested plan/approval gate was satisfied."
    if "source_skipping" in categories:
        return "Agent acted without reading the required source first."
    if "scope_trimming" in categories:
        return "Agent trimmed a high-conviction system request into a smaller or generic shape."
    if "fake_completion" in categories:
        return "Agent claimed completion before required verification."
    if "repeated_drift" in categories:
        return "Agent repeated behavior that had already been corrected or rejected."
    if "memory_miss" in categories:
        return "Agent missed a correction or directive that should have been remembered."
    if "approval_gate_violation" in categories:
        return "Agent crossed an approval gate without explicit approval."
    if "generic_framing" in categories:
        return "Agent produced generic or underdeveloped work where source-grounded execution was required."
    return f"Agent workflow correction detected: {user_text.strip()}"


def _directive_content(event: CorrectionEvent) -> str:
    category_text = ", ".join(event.categories)
    return (
        f"When a live user correction is detected ({category_text}), stop the active lane, "
        "name the mistake plainly, record affected files/actions, route the event to AMS/CEM/project ledger "
        "as appropriate, and require explicit resume approval before continuing. "
        f"Latest trigger: {event.mistake}"
    )


def _cem_failure_content(event: CorrectionEvent) -> str:
    affected = ""
    if event.affected_files:
        affected = " Affected files: " + ", ".join(event.affected_files) + "."
    actions = ""
    if event.affected_actions:
        actions = " Affected actions: " + "; ".join(event.affected_actions) + "."
    return (
        "avoid continuing after live correction; stop work, name the violation, record affected files/actions, "
        "route the correction, and require explicit resume. "
        f"Mistake: {event.mistake}{affected}{actions}"
    )


def _append_project_ledger_entry(path: Path, event: CorrectionEvent) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
    else:
        existing = "# Project Ledger\n"
    title = event.categories[0].replace("_", " ")
    files = event.affected_files or ["(none recorded)"]
    actions = event.affected_actions or ["(none recorded)"]
    entry = [
        "",
        f"## LEDGER-CORRECTION-{event.detected_at:%Y%m%d}-{event.event_id[-8:]} - {title}",
        "",
        f"- Date: {event.detected_at.date().isoformat()}",
        "- Type: mistake",
        "- Status: active",
        f"- Source: Correction Capture Controller `{event.event_id}`",
        f"- Summary: {event.mistake}",
        "- Files:",
    ]
    entry.extend(f"  - `{item}`" for item in files)
    entry.append("- Affected actions:")
    entry.extend(f"  - {item}" for item in actions)
    entry.extend(
        [
            "- Verification: Correction event recorded and resume gate opened.",
            "- Follow-up: Resume only after explicit approval.",
            "",
        ]
    )
    entry_text = "\n".join(entry)
    marker = "\n## Open Follow-Ups"
    if marker in existing:
        before, after = existing.split(marker, 1)
        path.write_text(before.rstrip() + "\n" + entry_text + marker + after, encoding="utf-8")
        return
    path.write_text(existing.rstrip() + "\n" + entry_text, encoding="utf-8")


def _load_events(root: Path) -> list[CorrectionEvent]:
    path = _event_log_path(root)
    if not path.exists():
        return []
    events: list[CorrectionEvent] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        events.append(CorrectionEvent.model_validate_json(line))
    return events


def _mark_event_resumed(root: Path, event_id: str) -> None:
    events = _load_events(root)
    matched = False
    updated_events: list[CorrectionEvent] = []
    for event in events:
        if event.event_id == event_id:
            event = event.model_copy(update={"resume_status": "resumed"})
            matched = True
        updated_events.append(event)
    if not matched:
        raise ValueError(f"Correction event not found: {event_id}")

    path = _event_log_path(root)
    lines = [event.model_dump_json() for event in updated_events]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    latest = updated_events[-1] if updated_events else None
    if latest is not None:
        _latest_event_path(root).write_text(json.dumps(latest.model_dump(mode="json"), indent=2), encoding="utf-8")


def _write_correction_event(root: Path, event: CorrectionEvent) -> None:
    root.mkdir(parents=True, exist_ok=True)
    payload = event.model_dump(mode="json")
    _append_jsonl(_event_log_path(root), payload)
    _latest_event_path(root).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_gate(root: Path, gate: CorrectionGate) -> None:
    root.mkdir(parents=True, exist_ok=True)
    _gate_path(root).write_text(gate.model_dump_json(indent=2), encoding="utf-8")


def _root(root: Path | None) -> Path:
    return (root or default_root()).expanduser().resolve()


def _event_log_path(root: Path) -> Path:
    return root / "correction-events.jsonl"


def _latest_event_path(root: Path) -> Path:
    return root / "correction-latest.json"


def _gate_path(root: Path) -> Path:
    return root / "correction-resume-gate.json"


def _resume_log_path(root: Path) -> Path:
    return root / "correction-resume-runs.jsonl"


def _append_jsonl(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _reject_waki_paths(paths: list[Path]) -> None:
    forbidden = Path("C:/Dev/Builds/Waki").resolve()
    for path in paths:
        resolved = path.expanduser().resolve()
        try:
            resolved.relative_to(forbidden)
        except ValueError:
            continue
        raise ValueError("Refusing to read or write C:\\Dev\\Builds\\Waki from this workspace.")
