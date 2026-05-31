param(
    [string]$Workspace = "C:\Dev\Builds\Agentic Memory System",
    [Parameter(Mandatory = $true)]
    [string]$Prompt,
    [Parameter(Mandatory = $true)]
    [string]$Command,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CommandArgs = @()
)

$ErrorActionPreference = "Stop"

$amsScript = Join-Path $Workspace "scripts\ams.py"
if (-not (Test-Path $amsScript)) {
    Write-Error "AMS_GUARD_FAIL: missing ams.py at $amsScript"
    exit 12
}

$control = & python $amsScript runtime-control $Prompt --json
$code = $LASTEXITCODE

Write-Output "AMS_RUNTIME_CONTROL_EXIT: $code"
if ($control) { Write-Output $control }

if ($code -ne 0) {
    Write-Output "AMS_GUARD_BLOCKED: downstream command was not invoked"
    exit $code
}

& $Command @CommandArgs
exit $LASTEXITCODE
