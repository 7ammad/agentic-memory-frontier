"""§12 -- live runtime hooks for the Correction Capture Controller.

Wires correction capture into a LIVE agent runtime beyond the manual CLI:

- ``hook_on_user_prompt_submit`` (UserPromptSubmit-style): classify the prompt; on a
  detected correction, capture it and return a BLOCK; on a benign prompt, ALLOW with
  zero side effects.
- ``hook_on_pre_tool_use_gate`` (PreToolUse-style): DENY continuation while the resume
  gate is armed, until the existing ``correction resume`` (human-approved) clears it.

This module is the pure, runtime-agnostic decision core: it returns a ``HookDecision``
and never touches stdin/stdout/exit codes (the CLI adapter does that) and never names
any specific runtime's payload schema (the PowerShell wrappers project that). It lives
in cem-core beside ``correction_capture`` and never imports cem-eval.

There is deliberately NO resume capability here: the gate clears ONLY via
``correction_capture.resume_correction`` (which requires ``approved_by``), so an agent
cannot self-clear a block.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field

from .correction_capture import (
    CorrectionCategory,
    capture_correction,
    classify_correction,
    correction_gate_status,
)
from .models import StrictModel

# Process exit codes shared by the CLI mapping, the PowerShell wrappers, and tests.
# 0 = allow; non-zero = block. 2 matches the CLI's existing ValueError -> exit 2.
HOOK_EXIT_ALLOW = 0
HOOK_EXIT_BLOCK = 10  # a live correction was captured this prompt
HOOK_EXIT_GATE_BLOCKED = 11  # the resume gate is armed; continuation denied
HOOK_EXIT_PARSE_ERROR = 2  # malformed hook payload

HOOK_SOURCE_PROMPT = "runtime:user-prompt-submit"


class HookDecision(StrictModel):
    hook: Literal["user_prompt_submit", "pre_tool_use"]
    decision: Literal["allow", "block"]
    categories: list[CorrectionCategory] = Field(default_factory=list)
    event_id: str | None = None
    gate_status: Literal["clear", "blocked"]
    active_event_id: str | None = None
    hook_exit_code: int


def hook_on_user_prompt_submit(
    root: Path | None,
    prompt_text: str,
    *,
    session_id: str | None = None,
    affected_files: list[str] | None = None,
    source: str = HOOK_SOURCE_PROMPT,
) -> HookDecision:
    """Auto-capture a correction from a live user prompt and BLOCK; ALLOW otherwise.

    Classifies FIRST and short-circuits a benign prompt to ALLOW with NO side effects
    (no event written, no gate armed, no memory init) -- calling capture_correction
    unconditionally would raise on an empty classification and wrongly block every prompt.
    """
    if not classify_correction(prompt_text):
        return HookDecision(
            hook="user_prompt_submit",
            decision="allow",
            categories=[],
            gate_status="clear",
            hook_exit_code=HOOK_EXIT_ALLOW,
        )
    event = capture_correction(
        root,
        prompt_text,
        affected_files=affected_files or [],
        source=source,
        session_id=session_id,
    )
    return HookDecision(
        hook="user_prompt_submit",
        decision="block",
        categories=list(event.categories),
        event_id=event.event_id,
        gate_status="blocked",
        active_event_id=event.event_id,
        hook_exit_code=HOOK_EXIT_BLOCK,
    )


def hook_on_pre_tool_use_gate(root: Path | None) -> HookDecision:
    """DENY continuation while the resume gate is armed; ALLOW when clear.

    Reads the gate via ``correction_gate_status`` (which lazily materializes the gate
    file on a fresh root, satisfying Monitor-0's controller-wired dependency) and FAILS
    CLOSED (block) on any read/parse error -- a corrupt gate is treated as armed, never
    silently allowed.
    """
    try:
        gate = correction_gate_status(root)
    except Exception:
        return HookDecision(
            hook="pre_tool_use",
            decision="block",
            gate_status="blocked",
            hook_exit_code=HOOK_EXIT_GATE_BLOCKED,
        )
    if gate.status == "blocked":
        return HookDecision(
            hook="pre_tool_use",
            decision="block",
            gate_status="blocked",
            active_event_id=gate.active_event_id,
            hook_exit_code=HOOK_EXIT_GATE_BLOCKED,
        )
    return HookDecision(
        hook="pre_tool_use",
        decision="allow",
        gate_status="clear",
        hook_exit_code=HOOK_EXIT_ALLOW,
    )
