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
    Write-Error "AMS_GUARD_FAIL: missing ams.py at $amsScript"
    exit 12
}

$startedAt = (Get-Date).ToUniversalTime().ToString("o")
$control = & python $amsScript runtime-control $Prompt --json
$code = $LASTEXITCODE
$controlObject = $null
$controlId = $null
if ($control) {
    try {
        $controlObject = $control | ConvertFrom-Json
        $controlId = $controlObject.control_id
    } catch {
        if (-not $Quiet) {
            Write-Output "AMS_TRACE_RECORD_FAIL: unable to parse runtime-control output: $_"
        }
    }
}

function Record-AmsRuntimeTrace {
    param(
        [int]$ObservedExitCode,
        [string]$EndedAt
    )

    if (-not $controlId) {
        if (-not $Quiet) {
            Write-Output "AMS_TRACE_RECORD_FAIL: missing runtime-control id"
        }
        return
    }

    $traceArgs = @(
        $amsScript,
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

    $traceOutput = & python @traceArgs 2>&1
    $traceCode = $LASTEXITCODE
    if (($traceCode -ne 0) -and (-not $Quiet)) {
        Write-Output "AMS_TRACE_RECORD_FAIL: $traceOutput"
    }
}

if ((-not $Quiet) -or $code -ne 0) {
    Write-Output "AMS_RUNTIME_CONTROL_EXIT: $code"
    if ($control) { Write-Output $control }
}

if ($code -ne 0) {
    Record-AmsRuntimeTrace -ObservedExitCode $code -EndedAt ((Get-Date).ToUniversalTime().ToString("o"))
    Write-Output "AMS_GUARD_BLOCKED: downstream command was not invoked"
    exit $code
}

& $Command @CommandArgs
$downstreamExitCode = $LASTEXITCODE
Record-AmsRuntimeTrace -ObservedExitCode $downstreamExitCode -EndedAt ((Get-Date).ToUniversalTime().ToString("o"))
exit $downstreamExitCode
