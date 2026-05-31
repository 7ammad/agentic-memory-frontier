from __future__ import annotations

import json
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
    shell_wrapper = (bin_dir / "codex").read_text(encoding="utf-8")
    assert "wslpath -w" in shell_wrapper
    assert "prefer_powershell_exe=1" in shell_wrapper
    assert shell_wrapper.index('if [ "$prefer_powershell_exe" = "1" ]') < shell_wrapper.index("elif command -v pwsh")
    assert (bin_dir / "codex.ams-original.ps1").exists()
    assert (bin_dir / "codex.ams-original.cmd").exists()
    assert (bin_dir / "codex.ams-original").exists()

    env = _ams_env(root)
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


def test_codex_entrypoint_installer_refreshes_stale_backup_for_fresh_shim(tmp_path):
    powershell = shutil.which("powershell")
    if os.name != "nt" or powershell is None:
        pytest.skip("Codex entrypoint installer smoke is Windows PowerShell-only")

    bin_dir = tmp_path / "npm"
    bin_dir.mkdir()
    target = bin_dir / "codex.ps1"
    backup = bin_dir / "codex.ams-original.ps1"
    target.write_text("Write-Output 'NEW CODEX SHIM'\n", encoding="utf-8")
    backup.write_text("Write-Output 'OLD CODEX SHIM'\n", encoding="utf-8")

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
    assert "backup refreshed:" in install.stdout
    assert backup.read_text(encoding="utf-8") == "Write-Output 'NEW CODEX SHIM'\n"

    env = os.environ.copy()
    env["AMS_CODEX_BYPASS"] = "1"
    bypass = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(target),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )
    assert bypass.returncode == 0, bypass.stderr
    assert bypass.stdout.strip() == "NEW CODEX SHIM"


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
    memory_base = _legacy_memory_base(root.parent)
    _codex_config(root.parent, root)
    _ams(root, "migrate", "apply", "--memory-base", str(memory_base), "--json")


def _ams(root: Path, *args: str) -> None:
    process = subprocess.run(
        [sys.executable, str(AMS), "--root", str(root), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_ams_env(root),
        check=False,
    )
    assert process.returncode == 0, process.stderr


def _ams_env(root: Path) -> dict[str, str]:
    env = os.environ.copy()
    config_path = root.parent / "config.toml"
    memory_base = root.parent / "legacy-memory"
    if config_path.exists():
        env["AMS_CODEX_CONFIG_PATH"] = str(config_path)
    if memory_base.exists():
        env["AMS_MEMORY_BASE"] = str(memory_base)
    return env


def _legacy_memory_base(tmp_path: Path) -> Path:
    memory_base = tmp_path / "legacy-memory"
    memory_base.mkdir(exist_ok=True)
    (memory_base / "MEMORY.md").write_text(
        "\n".join(
            [
                "# Task Group: C:\\Dev\\Builds\\Agentic Memory System / CEM-0 foundation pivot",
                "scope: Agentic Memory System after the pivot away from universal onboarding.",
                "",
                "## Reusable knowledge",
                "- The project pivot is explicit: Causal Experience Memory.",
                "- The first implementation wedge is CEM-0 / MemGuard Kernel.",
                "- The immediate next-work queue is verification.",
            ]
        ),
        encoding="utf-8",
    )
    return memory_base


def _codex_config(tmp_path: Path, root: Path) -> Path:
    config_path = tmp_path / "config.toml"
    codex_db = tmp_path / "codex-memory" / "lancedb"
    config_path.write_text(
        "\n".join(
            [
                "[mcp_servers.ams-memory]",
                'command = "node"',
                "",
                "[mcp_servers.ams-memory.env]",
                f"AMS_ROOT = {json.dumps(str(root))}",
                "",
                "[mcp_servers.codex-memory]",
                'command = "node"',
                "",
                "[mcp_servers.codex-memory.env]",
                f"CODEX_MEMORY_DB_PATH = {json.dumps(str(codex_db))}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return config_path
