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
# [VERIFIED 2026-05-31] Codex CLI 0.128 invokes PreToolUse before shell tools, but
# a non-zero command-hook exit is reported as "hook failed" and the tool still
# runs. Keep this as a gate decision surface for runtimes that enforce command
# hooks; do not treat it as Codex blocking until an enforceable runtime path is
# added.
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
