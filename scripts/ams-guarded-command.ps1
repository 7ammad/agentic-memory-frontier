param(
    [string]$Workspace = "C:\Dev\Builds\Agentic Memory System",
    [Parameter(Mandatory = $true)]
    [string]$Prompt,
    [Parameter(Mandatory = $true)]
    [string]$Command,
    [switch]$Quiet,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CommandArgs = @()
)

$ErrorActionPreference = "Stop"

$amsScript = Join-Path $Workspace "scripts\ams.py"
if (-not (Test-Path $amsScript)) {
    Write-Output "AMS_RUNTIME_CONTROL_DEGRADED: missing ams.py at $amsScript; downstream command will run"
    try {
        & $Command @CommandArgs
        exit $LASTEXITCODE
    } catch {
        [Console]::Error.WriteLine("AMS_GUARD_DOWNSTREAM_LAUNCH_FAIL: $($_.Exception.Message)")
        exit 127
    }
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

$startedAt = (Get-Date).ToUniversalTime().ToString("o")
$control = Invoke-AmsCli @("runtime-control", $Prompt, "--json")
$code = $LASTEXITCODE
$controlObject = $null
$controlId = $null
$governedRunId = $null
$controlStatus = $null
if ($control) {
    try {
        $controlObject = $control | ConvertFrom-Json
        $controlId = $controlObject.control_id
        $governedRunId = $controlObject.governed_run_id
        $controlStatus = $controlObject.status
    } catch {
        if (-not $Quiet) {
            Write-Output "AMS_TRACE_RECORD_FAIL: unable to parse runtime-control output: $_"
        }
    }
}

function Write-AmsPersistenceFailure {
    param([string]$Message)
    [Console]::Error.WriteLine($Message)
}

function Record-AmsRuntimeTrace {
    param(
        [int]$ObservedExitCode,
        [string]$EndedAt
    )

    if (-not $controlId) {
        Write-AmsPersistenceFailure "AMS_TRACE_RECORD_FAIL: missing runtime-control id"
        return
    }

    $traceArgs = @(
        "runtime-trace",
        "record",
        "--control-id",
        $controlId,
        "--command",
        $Command,
        "--exit-code",
        "$ObservedExitCode",
        "--started-at",
        $startedAt,
        "--ended-at",
        $EndedAt,
        "--json"
    )
    foreach ($arg in $CommandArgs) {
        $traceArgs += @("--command-arg=$arg")
    }

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $traceOutput = Invoke-AmsCli $traceArgs 2>&1
        $traceCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    if ($traceCode -ne 0) {
        Write-AmsPersistenceFailure "AMS_TRACE_RECORD_FAIL: $traceOutput"
    }
}

function Close-AmsGovernedRun {
    param(
        [int]$ObservedExitCode,
        [string]$ActionTaken
    )

    if (-not $governedRunId) {
        Write-AmsPersistenceFailure "AMS_GOVERNED_RUN_CLOSE_FAIL: missing governed-run id"
        return
    }

    $outcome = "failure"
    if ($ObservedExitCode -eq 0) {
        $outcome = "success"
    }

    $closeArgs = @(
        "governed-run",
        "close",
        "--receipt-id",
        $governedRunId,
        "--outcome",
        $outcome,
        "--action-taken",
        $ActionTaken,
        "--json"
    )
    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $closeOutput = Invoke-AmsCli $closeArgs 2>&1
        $closeCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    if ($closeCode -ne 0) {
        Write-AmsPersistenceFailure "AMS_GOVERNED_RUN_CLOSE_FAIL: $closeOutput"
    }
}

if ((-not $Quiet) -or $code -ne 0) {
    Write-Output "AMS_RUNTIME_CONTROL_EXIT: $code"
    if ($control) { Write-Output $control }
}

if (($code -ne 0) -and ($controlStatus -ne "block")) {
    Write-Output "AMS_RUNTIME_CONTROL_DEGRADED: runtime-control infrastructure failed without an action-safety block; downstream command will run"
}

if ($controlStatus -eq "block") {
    Record-AmsRuntimeTrace -ObservedExitCode $code -EndedAt ((Get-Date).ToUniversalTime().ToString("o"))
    Close-AmsGovernedRun -ObservedExitCode $code -ActionTaken "AMS guard blocked downstream command: $Command $($CommandArgs -join ' ')"
    Write-Output "AMS_GUARD_BLOCKED: downstream command was not invoked"
    if ($code -ne 0) {
        exit $code
    }
    exit 12
}

try {
    & $Command @CommandArgs
    $downstreamExitCode = $LASTEXITCODE
} catch {
    $downstreamExitCode = 127
    Record-AmsRuntimeTrace -ObservedExitCode $downstreamExitCode -EndedAt ((Get-Date).ToUniversalTime().ToString("o"))
    Close-AmsGovernedRun -ObservedExitCode $downstreamExitCode -ActionTaken "AMS guarded command failed to launch: $Command $($CommandArgs -join ' ')"
    [Console]::Error.WriteLine("AMS_GUARD_DOWNSTREAM_LAUNCH_FAIL: $($_.Exception.Message)")
    exit $downstreamExitCode
}

Record-AmsRuntimeTrace -ObservedExitCode $downstreamExitCode -EndedAt ((Get-Date).ToUniversalTime().ToString("o"))
Close-AmsGovernedRun -ObservedExitCode $downstreamExitCode -ActionTaken "AMS guarded command: $Command $($CommandArgs -join ' ')"
exit $downstreamExitCode
