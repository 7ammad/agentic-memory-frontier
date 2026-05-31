from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
AMS = ROOT / "scripts" / "ams.py"
INSTALLER = ROOT / "scripts" / "install-ams-codex-entrypoint.ps1"


def test_installed_codex_entrypoint_blocks_before_original_shim(tmp_path):
    powershell = shutil.which("powershell")
    if os.name != "nt" or powershell is None:
        pytest.skip("Codex entrypoint installer smoke is Windows PowerShell-only")

    bin_dir = tmp_path / "npm"
    bin_dir.mkdir()
    target = bin_dir / "codex.ps1"
    sentinel = tmp_path / "raw-shim-ran.txt"
    root = tmp_path / "ams"

    target.write_text(
        "\n".join(
            [
                "param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args = @())",
                "Set-Content -LiteralPath $env:RAW_SENTINEL -Value ($Args -join '|')",
                "exit 0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (bin_dir / "codex.cmd").write_text("@ECHO off\r\nREM original cmd shim\r\n", encoding="utf-8")
    (bin_dir / "codex").write_text("#!/bin/sh\n# original shell shim\n", encoding="utf-8")
    _seed_ams_root(root)

    install = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(INSTALLER),
            "-Workspace",
            str(ROOT),
            "-TargetPath",
            str(target),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert install.returncode == 0, install.stderr
    assert "AMS_CODEX_ENTRYPOINT_WRAPPER" in target.read_text(encoding="utf-8")
    assert "wslpath -w" in (bin_dir / "codex").read_text(encoding="utf-8")
    assert (bin_dir / "codex.ams-original.ps1").exists()
    assert (bin_dir / "codex.ams-original.cmd").exists()
    assert (bin_dir / "codex.ams-original").exists()

    env = os.environ.copy()
    env["AMS_ROOT"] = str(root)
    env["RAW_SENTINEL"] = str(sentinel)

    allowed = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(target),
            "exec",
            "continue building Agentic Memory System with verification",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )

    assert allowed.returncode == 0, allowed.stderr
    assert sentinel.read_text(encoding="utf-8").strip() == (
        "exec|continue building Agentic Memory System with verification"
    )

    sentinel.unlink()
    blocked = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(target),
            "exec",
            "we already said no scaffolding; stop and record this correction",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )

    assert blocked.returncode == 12
    assert "AMS_RUNTIME_CONTROL_EXIT: 12" in blocked.stdout
    assert "AMS_GUARD_BLOCKED: downstream command was not invoked" in blocked.stdout
    assert not sentinel.exists()


def test_codex_entrypoint_installer_can_restore_original_shim(tmp_path):
    powershell = shutil.which("powershell")
    if os.name != "nt" or powershell is None:
        pytest.skip("Codex entrypoint installer smoke is Windows PowerShell-only")

    bin_dir = tmp_path / "npm"
    bin_dir.mkdir()
    target = bin_dir / "codex.ps1"
    original = "Write-Output 'ORIGINAL CODEX SHIM'\n"
    target.write_text(original, encoding="utf-8")

    install = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(INSTALLER),
            "-Workspace",
            str(ROOT),
            "-TargetPath",
            str(target),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert install.returncode == 0, install.stderr

    uninstall = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(INSTALLER),
            "-TargetPath",
            str(target),
            "-Uninstall",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert uninstall.returncode == 0, uninstall.stderr
    assert target.read_text(encoding="utf-8") == original


def _seed_ams_root(root: Path) -> None:
    _ams(
        root,
        "bootstrap-codex",
        "--workspace",
        str(ROOT),
        "--json",
    )
    _ams(
        root,
        "remember",
        "run python scripts/ams.py brief before continuing Agentic Memory System work",
        "--kind",
        "skill",
        "--outcome",
        "success",
        "--domain",
        "agentic-memory-system",
        "--task-family",
        "ams-usage",
        "--json",
    )


def _ams(root: Path, *args: str) -> None:
    process = subprocess.run(
        [sys.executable, str(AMS), "--root", str(root), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert process.returncode == 0, process.stderr
