from pathlib import Path

from cem_core import operations
from cem_core.correction_capture import CorrectionControllerSummary


def _check_status(monitor: operations.MonitorRun, name: str) -> str:
    for check in monitor.checks:
        if check.name == name:
            return check.status
    raise AssertionError(f"monitor check not found: {name}")


def _unwired_summary(root: Path) -> CorrectionControllerSummary:
    # A controller bound to a DIFFERENT memory root than the monitor serves:
    # corrections captured there would never surface in this root's briefs.
    foreign = root.parent / "foreign-memory-store"
    return CorrectionControllerSummary(
        root=str(foreign),
        event_count=0,
        latest_event_id=None,
        active_gate=False,
        active_event_id=None,
        latest_event_path=str(foreign / "correction-latest.json"),
        event_log_path=str(foreign / "correction-events.jsonl"),
        gate_path=str(foreign / "correction-resume-gate.json"),
    )


def test_correction_controller_wired_gate_fails_when_unwired(tmp_path, monkeypatch):
    # Failure canary: the correction_controller_wired gate must go RED when the
    # correction controller is bound to a different memory root than the monitor
    # serves. Before the fix this check was hardcoded True and could never fail.
    monkeypatch.setattr(
        operations,
        "correction_controller_summary",
        lambda root: _unwired_summary(Path(root)),
    )
    monitor = operations.run_monitor(tmp_path)
    assert _check_status(monitor, "correction_controller_wired") == "fail"


def test_correction_controller_wired_gate_passes_for_healthy_root(tmp_path):
    # A freshly initialized root binds the controller correctly, so the gate is
    # GREEN even with zero corrections captured yet.
    monitor = operations.run_monitor(tmp_path)
    assert _check_status(monitor, "correction_controller_wired") == "pass"
