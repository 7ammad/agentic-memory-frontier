param(
    [string]$Workspace = "C:\Dev\Builds\Agentic Memory System"
)

$ErrorActionPreference = "Stop"

$amsScript = Join-Path $Workspace "scripts\ams.py"
if (-not (Test-Path $amsScript)) {
    Write-Error "SESSION_GATE_FAIL: missing ams.py at $amsScript"
    exit 2
}

$output = & python $amsScript startup-brief "continue building Agentic Memory System" --domain agentic-memory-system --json 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "SESSION_GATE_FAIL: unable to build AMS startup brief"
    Write-Output $output
    exit 3
}

$brief = $output | ConvertFrom-Json
if ($brief.status -ne "allow") {
    Write-Error "SESSION_GATE_FAIL: AMS startup brief blocked execution"
    Write-Output "SESSION_GATE_BLOCK_REASONS: $($brief.block_reasons -join ', ')"
    exit 4
}

Write-Output "SESSION_GATE_PASS: startup brief allowed"
Write-Output "SESSION_GATE_MEMORY_ROOT: C:\Users\7amma\.codex\memory\cem"
Write-Output "SESSION_GATE_BRIEF_ID: $($brief.brief_id)"
Write-Output "SESSION_GATE_MONITOR_ID: $($brief.monitor_id)"
Write-Output "SESSION_GATE_EVIDENCE_IDS: $($brief.evidence_ids -join ', ')"
exit 0
