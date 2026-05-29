"""§12 live runtime hooks -- pure decision-core tests (no CLI, no PowerShell).

The hooks wire the Correction Capture Controller into a live agent runtime beyond
the manual CLI: a UserPromptSubmit-style hook auto-captures a correction and BLOCKS,
and a PreToolUse-style gate hook DENIES continuation while the resume gate is armed.
The core is runtime-agnostic and returns a HookDecision; the runtime adapter (CLI +
PowerShell) is thin. Every test is RED-first and watched to fail for the right reason.
"""
from __future__ import annotations

from cem_core import operations
from cem_core.correction_capture import (
    _event_log_path,
    _gate_path,
    _root,
    capture_correction,
    classify_correction,
    correction_gate_status,
    resume_correction,
)
from cem_core.correction_hooks import (
    HOOK_EXIT_ALLOW,
    HOOK_EXIT_BLOCK,
    HOOK_EXIT_GATE_BLOCKED,
    HookDecision,
    hook_on_pre_tool_use_gate,
    hook_on_user_prompt_submit,
)

BLOCKING_PROMPT = "we already said no to that"  # matches repeated_drift
BENIGN_PROMPT = "list the files in the kernel package"  # matches no category


def _check_status(run, name: str) -> str:
    return next(c.status for c in run.checks if c.name == name)


def test_hook_user_prompt_blocks_records_event_and_arms_gate(tmp_path):
    decision = hook_on_user_prompt_submit(tmp_path, BLOCKING_PROMPT)
    assert isinstance(decision, HookDecision)
    assert decision.decision == "block"
    assert decision.event_id is not None
    assert decision.gate_status == "blocked"
    assert decision.active_event_id == decision.event_id
    assert decision.hook_exit_code == HOOK_EXIT_BLOCK
    # Side effects on disk: the correction was actually recorded and the gate armed.
    root = _root(tmp_path)
    lines = [ln for ln in _event_log_path(root).read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 1
    gate = correction_gate_status(tmp_path)
    assert gate.status == "blocked"
    assert gate.active_event_id == decision.event_id


def test_hook_user_prompt_benign_allows_with_no_event_and_clear_gate(tmp_path):
    # The single most important canary: a benign prompt must classify-FIRST and
    # short-circuit to ALLOW with ZERO side effects. Calling capture_correction
    # unconditionally would raise on the empty classification and block every prompt.
    assert classify_correction(BENIGN_PROMPT) == []
    decision = hook_on_user_prompt_submit(tmp_path, BENIGN_PROMPT)
    assert decision.decision == "allow"
    assert decision.categories == []
    assert decision.event_id is None
    assert decision.gate_status == "clear"
    assert decision.hook_exit_code == HOOK_EXIT_ALLOW
    assert not _event_log_path(_root(tmp_path)).exists()


def test_hook_gate_denies_continuation_while_active(tmp_path):
    capture_correction(tmp_path, BLOCKING_PROMPT)
    decision = hook_on_pre_tool_use_gate(tmp_path)
    assert decision.decision == "block"
    assert decision.gate_status == "blocked"
    assert decision.active_event_id is not None
    # A DIFFERENT code than prompt-capture-block, so the wrapper can distinguish.
    assert decision.hook_exit_code == HOOK_EXIT_GATE_BLOCKED


def test_hook_gate_fails_closed_on_corrupt_gate_file(tmp_path):
    gate_path = _gate_path(_root(tmp_path))
    gate_path.parent.mkdir(parents=True, exist_ok=True)
    gate_path.write_text("{not valid json", encoding="utf-8")
    decision = hook_on_pre_tool_use_gate(tmp_path)
    assert decision.decision == "block"  # FAIL CLOSED, never crash, never allow
    assert decision.hook_exit_code == HOOK_EXIT_GATE_BLOCKED


def test_hook_gate_initializes_gate_file_on_fresh_root_and_keeps_monitor_wired(tmp_path):
    decision = hook_on_pre_tool_use_gate(tmp_path)
    assert decision.decision == "allow"
    assert _gate_path(_root(tmp_path)).exists()  # lazily created via correction_gate_status
    run = operations.run_monitor(tmp_path, deep=False)
    assert _check_status(run, "correction_controller_wired") == "pass"


def test_hook_resume_clears_gate_deny_to_allow_end_to_end(tmp_path):
    event = capture_correction(tmp_path, BLOCKING_PROMPT)
    assert hook_on_pre_tool_use_gate(tmp_path).decision == "block"
    resume_correction(tmp_path, event.event_id, approved_by="Hammad")
    after = hook_on_pre_tool_use_gate(tmp_path)
    assert after.decision == "allow"
    assert after.gate_status == "clear"
    assert after.hook_exit_code == HOOK_EXIT_ALLOW


def test_monitor0_bridge_hook_block_then_resume(tmp_path):
    # Single source of truth: the live hook and the manual CLI / session-start gate
    # share ONE gate. A hook BLOCK must fail Monitor-0 exactly as a manual capture does.
    decision = hook_on_user_prompt_submit(tmp_path, BLOCKING_PROMPT)
    run = operations.run_monitor(tmp_path, deep=False)
    assert _check_status(run, "correction_resume_gate_clear") == "fail"
    resume_correction(tmp_path, decision.event_id, approved_by="Hammad")
    run2 = operations.run_monitor(tmp_path, deep=False)
    assert _check_status(run2, "correction_resume_gate_clear") == "pass"
