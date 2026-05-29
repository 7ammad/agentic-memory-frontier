# PreToolUse runtime gate hook for the Correction Capture Controller (§12).
#
# Wire this as the agent runtime's PreToolUse hook. It consults the resume gate and
# DENIES continuation while a correction is unresolved. The exit code carries the
# decision:
#   0  = allow (gate clear)
#   11 = deny (resume gate armed; clear it via `correction resume --approved-by`)
#
# Fail-closed: any non-zero exit means DENY. Mirrors session-start-gate.ps1; takes no
# stdin and captures STDOUT ONLY (no `2>&1`). Branches on $LASTEXITCODE, not on JSON.
#
# [UNVERIFIED] The Claude Code / Codex PreToolUse exit-code + stdout contract must be
# confirmed by a live runtime smoke test before this hook is trusted in production.
param(
    [string]$Workspace = "C:\Dev\Builds\Agentic Memory System"
)

$ErrorActionPreference = "Stop"

$amsScript = Join-Path $Workspace "scripts\ams.py"
if (-not (Test-Path $amsScript)) {
    Write-Error "HOOK_GATE_FAIL: missing ams.py at $amsScript"
    exit 11
}

$out = & python $amsScript correction hook-gate --json
$code = $LASTEXITCODE

Write-Output "HOOK_DECISION_GATE_EXIT: $code"
if ($out) { Write-Output $out }
exit $code
