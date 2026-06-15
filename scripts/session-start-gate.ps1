param(
    [string]$Workspace = "C:\Dev\Builds\Agentic Memory System"
)

$ErrorActionPreference = "Stop"

function Warn-SessionGate {
    param(
        [string]$Message
    )
    Write-Output "SESSION_GATE_DEGRADED: $Message"
    Write-Output "SESSION_GATE_MEMORY_ROOT: C:\Users\7amma\.codex\memory\cem"
    exit 0
}

$amsScript = Join-Path $Workspace "scripts\ams.py"
if (-not (Test-Path $amsScript)) {
    Warn-SessionGate "missing ams.py at $amsScript"
}

function Invoke-AmsCli {
    param([string[]]$Arguments)

    function Invoke-SelectedPython {
        param([string]$PythonPath, [string[]]$PythonArguments)
        $previousSkip = $env:AMS_SKIP_PROJECT_PYTHON
        $env:AMS_SKIP_PROJECT_PYTHON = "1"
        try {
            & $PythonPath $amsScript @PythonArguments
        } finally {
            if ($null -eq $previousSkip) {
                Remove-Item Env:\AMS_SKIP_PROJECT_PYTHON -ErrorAction SilentlyContinue
            } else {
                $env:AMS_SKIP_PROJECT_PYTHON = $previousSkip
            }
        }
    }

    $pythonCandidates = @(
        (Join-Path $Workspace ".venv\Scripts\python.exe"),
        (Join-Path $Workspace ".venv\Scripts\python.cmd"),
        (Join-Path $Workspace ".venv\bin\python")
    )
    foreach ($python in $pythonCandidates) {
        if (Test-Path -LiteralPath $python) {
            Invoke-SelectedPython -PythonPath $python -PythonArguments $Arguments
            return
        }
    }

    $projectFile = Join-Path $Workspace "pyproject.toml"
    $uv = Get-Command "uv" -ErrorAction SilentlyContinue
    if ((Test-Path -LiteralPath $projectFile) -and ($null -ne $uv)) {
        $previousSkip = $env:AMS_SKIP_PROJECT_PYTHON
        $env:AMS_SKIP_PROJECT_PYTHON = "1"
        try {
            & $uv.Source "run" "--project=$Workspace" "python" $amsScript @Arguments
            return
        } finally {
            if ($null -eq $previousSkip) {
                Remove-Item Env:\AMS_SKIP_PROJECT_PYTHON -ErrorAction SilentlyContinue
            } else {
                $env:AMS_SKIP_PROJECT_PYTHON = $previousSkip
            }
        }
    }

    & python $amsScript @Arguments
}

$output = Invoke-AmsCli @("startup-brief", "continue building Agentic Memory System", "--domain", "agentic-memory-system", "--json") 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Output $output
    Warn-SessionGate "unable to build AMS startup brief"
}

try {
    $brief = $output | ConvertFrom-Json
} catch {
    Write-Output $output
    Warn-SessionGate "unable to parse AMS startup brief"
}
if (($null -eq $brief) -or ($null -eq $brief.status)) {
    Write-Output $output
    Warn-SessionGate "AMS startup brief returned no status"
}
if ($brief.status -eq "block") {
    Write-Output "SESSION_GATE_BLOCK_REASONS: $($brief.block_reasons -join ', ')"
    Warn-SessionGate "AMS startup brief reported block outside runtime-control"
}

if ($brief.status -eq "degraded") {
    Write-Output "SESSION_GATE_DEGRADED: startup brief allowed with warnings"
    Write-Output "SESSION_GATE_DEGRADED_REASONS: $($brief.degraded_reasons -join ', ')"
} elseif ($brief.status -eq "allow") {
    Write-Output "SESSION_GATE_PASS: startup brief allowed"
} else {
    Write-Output $output
    Warn-SessionGate "unknown AMS startup brief status $($brief.status)"
}
Write-Output "SESSION_GATE_MEMORY_ROOT: C:\Users\7amma\.codex\memory\cem"
Write-Output "SESSION_GATE_BRIEF_ID: $($brief.brief_id)"
Write-Output "SESSION_GATE_MONITOR_ID: $($brief.monitor_id)"
Write-Output "SESSION_GATE_EVIDENCE_IDS: $($brief.evidence_ids -join ', ')"
exit 0
