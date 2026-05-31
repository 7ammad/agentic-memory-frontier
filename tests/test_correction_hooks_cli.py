"""§12 live runtime hooks -- CLI adapter tests.

Drives `cem_core.cli.main` with argv + monkeypatched stdin and asserts the
process exit code carries the decision, stdout stays pure JSON (no traceback),
unknown runtime keys are tolerated, and the human-approval invariant holds (no
agent-callable resume surface). Each test is RED-first.
"""
from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from cem_core import cli
from cem_core.correction_capture import _event_log_path, _root
from cem_core.correction_hooks import (
    HOOK_EXIT_ALLOW,
    HOOK_EXIT_BLOCK,
    HOOK_EXIT_GATE_BLOCKED,
    HOOK_EXIT_PARSE_ERROR,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run(argv, stdin_text, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin_text))
    return cli.main(argv)


class _BytesStdin:
    """A stdin stub exposing a binary .buffer, like the real runtime stdin (and
    unlike io.StringIO) -- so the strict utf-8-sig byte decode path is exercised."""

    def __init__(self, data: bytes):
        self.buffer = io.BytesIO(data)


def test_hook_prompt_cli_rejects_invalid_utf8(tmp_path, monkeypatch, capsys):
    # Garbled (invalid UTF-8) input must be cleanly REJECTED (exit 2), not silently
    # mangled into an accepted correction via errors="replace". The 0xff byte inside
    # the string would, under errors="replace", become U+FFFD and parse as a valid
    # correction prompt (block, exit 10) -- a strict decode rejects it cleanly.
    monkeypatch.setattr("sys.stdin", _BytesStdin(b'{"prompt_text": "we already said no\xff"}'))
    with pytest.raises(SystemExit) as exc:
        cli.main(["--root", str(tmp_path), "correction", "hook-prompt", "--json"])
    assert exc.value.code == HOOK_EXIT_PARSE_ERROR
    assert not _event_log_path(_root(tmp_path)).exists()


def test_hook_prompt_cli_allows_with_unknown_runtime_keys(tmp_path, monkeypatch, capsys):
    payload = {
        "prompt_text": "list the kernel files",
        "session_id": "s1",
        "transcript_path": "x",
        "hook_event_name": "UserPromptSubmit",
        "cwd": ".",
    }
    code = _run(["--root", str(tmp_path), "correction", "hook-prompt", "--json"], json.dumps(payload), monkeypatch)
    assert code == HOOK_EXIT_ALLOW
    out = json.loads(capsys.readouterr().out)  # stdout is pure JSON
    assert out["decision"] == "allow"
    assert not _event_log_path(_root(tmp_path)).exists()


def test_prompt_wrapper_maps_live_codex_user_prompt_payload(tmp_path):
    powershell = shutil.which("powershell")
    if os.name != "nt" or powershell is None:
        pytest.skip("PowerShell runtime wrapper smoke is Windows-only")

    root = tmp_path / "ams"
    payload = {
        "session_id": "019e7d48-f0b9-7a60-8d1a-03ec4b4a62de",
        "turn_id": "019e7d48-f3a0-7ee3-b72a-8aafe7e8f603",
        "transcript_path": None,
        "cwd": str(REPO_ROOT),
        "hook_event_name": "UserPromptSubmit",
        "model": "gpt-5.5",
        "permission_mode": "bypassPermissions",
        "prompt": "we already said no scaffolding; stop and record this correction",
    }
    env = os.environ.copy()
    env["AMS_ROOT"] = str(root)

    process = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(REPO_ROOT / "scripts" / "correction-hook-prompt.ps1"),
            "-Workspace",
            str(REPO_ROOT),
        ],
        input=json.dumps(payload),
        text=True,
        encoding="utf-8",
        capture_output=True,
        env=env,
        cwd=REPO_ROOT,
        timeout=30,
    )

    assert process.returncode == HOOK_EXIT_BLOCK
    event = json.loads((root / "correction-latest.json").read_text(encoding="utf-8"))
    assert event["user_text"] == payload["prompt"]
    assert event["session_id"] == payload["session_id"]


def test_hook_prompt_cli_blocks_on_correction(tmp_path, monkeypatch, capsys):
    code = _run(
        ["--root", str(tmp_path), "correction", "hook-prompt", "--json"],
        json.dumps({"prompt_text": "we already said no"}),
        monkeypatch,
    )
    assert code == HOOK_EXIT_BLOCK
    out = json.loads(capsys.readouterr().out)
    assert out["decision"] == "block"
    assert out["event_id"]


def test_hook_prompt_cli_tolerates_utf8_bom(tmp_path, monkeypatch, capsys):
    # PowerShell 5.1 prepends a UTF-8 BOM when piping a string to a native command,
    # so the decoded stdin starts with ﻿. The hook must tolerate it (strip it)
    # rather than fail to parse. Reproduces the live PS-pipe condition at text level.
    code = _run(
        ["--root", str(tmp_path), "correction", "hook-prompt", "--json"],
        "﻿" + json.dumps({"prompt_text": "we already said no"}) + "\r\n",
        monkeypatch,
    )
    assert code == HOOK_EXIT_BLOCK
    assert json.loads(capsys.readouterr().out)["decision"] == "block"


def test_hook_prompt_cli_parse_error_exits_2_no_event(tmp_path, monkeypatch, capsys):
    with pytest.raises(SystemExit) as exc:
        _run(["--root", str(tmp_path), "correction", "hook-prompt", "--json"], "{not json", monkeypatch)
    assert exc.value.code == HOOK_EXIT_PARSE_ERROR
    assert capsys.readouterr().out == ""  # no traceback / no partial JSON on stdout
    assert not _event_log_path(_root(tmp_path)).exists()


def test_hook_prompt_cli_rejects_waki_affected_files(tmp_path, monkeypatch, capsys):
    payload = {"prompt_text": "we already said no", "affected_files": ["C:/Dev/Builds/Waki/x.py"]}
    with pytest.raises(SystemExit) as exc:
        _run(["--root", str(tmp_path), "correction", "hook-prompt", "--json"], json.dumps(payload), monkeypatch)
    assert exc.value.code == HOOK_EXIT_PARSE_ERROR  # ValueError -> exit 2 path
    assert not _event_log_path(_root(tmp_path)).exists()


def test_hook_gate_cli_exit_codes(tmp_path, monkeypatch, capsys):
    # Fresh root -> allow (0); after a capture -> gate-blocked (11).
    code_fresh = _run(["--root", str(tmp_path), "correction", "hook-gate", "--json"], "", monkeypatch)
    assert code_fresh == HOOK_EXIT_ALLOW
    capsys.readouterr()
    cli.main(["--root", str(tmp_path), "correction", "capture", "we already said no", "--json"])
    capsys.readouterr()
    code_blocked = _run(["--root", str(tmp_path), "correction", "hook-gate", "--json"], "", monkeypatch)
    assert code_blocked == HOOK_EXIT_GATE_BLOCKED


def test_no_agent_self_resume_surface_exists():
    # Human-approval invariant: there is no agent-callable resume hook. The gate
    # clears ONLY via `correction resume --approved-by`.
    parser = cli.build_parser()
    correction_action = next(
        a for a in parser._subparsers._group_actions[0].choices["correction"]._subparsers._group_actions
        if a.dest == "correction_command"
    )
    choices = set(correction_action.choices)
    assert "hook-resume" not in choices
    assert {"hook-prompt", "hook-gate", "resume"} <= choices


def test_emit_does_not_misroute_hook_decision(capsys):
    # A HookDecision dict (carries active_event_id) must render via the hook emitter,
    # NOT the gate emitter -- the 'hook' discriminator is matched first.
    payload = {
        "hook": "pre_tool_use",
        "decision": "block",
        "categories": [],
        "event_id": None,
        "gate_status": "blocked",
        "active_event_id": "correction_abc",
        "hook_exit_code": HOOK_EXIT_GATE_BLOCKED,
    }
    cli._emit(payload, as_json=False)
    out = capsys.readouterr().out
    assert out.startswith("hook:")
    assert "correction_gate:" not in out
