param(
    [string]$Workspace = "C:\Dev\Builds\Agentic Memory System"
)

$ErrorActionPreference = "Stop"

$workspacePath = [System.IO.Path]::GetFullPath($Workspace)
$amsScript = Join-Path $workspacePath "scripts\ams.py"
$failures = @()
$warnings = @()

function Add-Failure {
    param([string]$Message)
    $script:failures += $Message
}

function Add-Warning {
    param([string]$Message)
    $script:warnings += $Message
}

$pythonCandidates = @(
    (Join-Path $workspacePath ".venv\Scripts\python.exe"),
    (Join-Path $workspacePath ".venv\Scripts\python.cmd"),
    (Join-Path $workspacePath ".venv\bin\python")
)
$workspacePython = $null
foreach ($candidate in $pythonCandidates) {
    if (Test-Path -LiteralPath $candidate) {
        $workspacePython = [System.IO.Path]::GetFullPath($candidate)
        break
    }
}

$ambientPython = Get-Command "python" -ErrorAction SilentlyContinue
$ambientPath = $null
if ($null -ne $ambientPython) {
    $ambientPath = [System.IO.Path]::GetFullPath($ambientPython.Source)
}

if ($null -eq $workspacePython) {
    Add-Failure "workspace python is missing; run uv sync in $workspacePath"
} else {
    $importOutput = & $workspacePython -c "import sys, pydantic; print(sys.executable); print(pydantic.__version__)" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Add-Failure "workspace python cannot import pydantic: $importOutput"
    }
}

if (-not (Test-Path -LiteralPath $amsScript)) {
    Add-Failure "missing AMS script at $amsScript"
}

if ($null -eq $ambientPath) {
    Add-Warning "ambient python not found on PATH; AMS wrappers can still use workspace python"
} elseif ($null -ne $workspacePython -and $ambientPath -ne $workspacePython) {
    Add-Warning "ambient python differs from workspace python"
    if ($ambientPath.ToLowerInvariant().Contains("hermes")) {
        Add-Warning "ambient python appears to come from Hermes; AMS must continue using workspace python"
    }
}

if (($null -ne $ambientPath) -and (Test-Path -LiteralPath $amsScript)) {
    $smokeRoot = Join-Path $workspacePath "tmp\ams-env-doctor-smoke"
    $previousSkip = $env:AMS_SKIP_PROJECT_PYTHON
    try {
        Remove-Item Env:\AMS_SKIP_PROJECT_PYTHON -ErrorAction SilentlyContinue
        $smokeOutput = & $ambientPath $amsScript "--root" $smokeRoot "--json" "init" 2>&1
        if ($LASTEXITCODE -ne 0) {
            Add-Failure "direct ambient python AMS smoke failed: $smokeOutput"
        }
    } finally {
        if ($null -ne $previousSkip) {
            $env:AMS_SKIP_PROJECT_PYTHON = $previousSkip
        }
    }
}

$status = "pass"
if ($failures.Count -gt 0) {
    $status = "fail"
} elseif ($warnings.Count -gt 0) {
    $status = "warn"
}

Write-Output "AMS_ENV_DOCTOR_STATUS: $status"
Write-Output "AMS_ENV_DOCTOR_WORKSPACE: $workspacePath"
Write-Output "AMS_ENV_DOCTOR_WORKSPACE_PYTHON: $workspacePython"
Write-Output "AMS_ENV_DOCTOR_AMBIENT_PYTHON: $ambientPath"
foreach ($warning in $warnings) {
    Write-Output "AMS_ENV_DOCTOR_WARN: $warning"
}
foreach ($failure in $failures) {
    Write-Output "AMS_ENV_DOCTOR_FAIL: $failure"
}

if ($status -eq "fail") {
    exit 1
}
exit 0
