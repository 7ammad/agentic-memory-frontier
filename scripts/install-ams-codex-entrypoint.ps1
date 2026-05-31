param(
    [string]$Workspace = "C:\Dev\Builds\Agentic Memory System",
    [string]$TargetPath = (Join-Path $env:APPDATA "npm\codex.ps1"),
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"

$marker = "AMS_CODEX_ENTRYPOINT_WRAPPER"
$target = [System.IO.Path]::GetFullPath($TargetPath)
$binDir = Split-Path -Parent $target
$ps1Backup = Join-Path $binDir "codex.ams-original.ps1"
$cmdTarget = Join-Path $binDir "codex.cmd"
$cmdBackup = Join-Path $binDir "codex.ams-original.cmd"
$shTarget = Join-Path $binDir "codex"
$shBackup = Join-Path $binDir "codex.ams-original"

function Copy-Back {
    param([string]$Backup, [string]$Destination)
    if (Test-Path -LiteralPath $Backup) {
        Copy-Item -LiteralPath $Backup -Destination $Destination -Force
        Write-Output "restored: $Destination"
    }
}

function Backup-Original {
    param([string]$Original, [string]$Backup, [string]$Marker)
    if (-not (Test-Path -LiteralPath $Original)) { return }
    $text = Get-Content -LiteralPath $Original -Raw
    if ($text -match [regex]::Escape($Marker)) {
        if (-not (Test-Path -LiteralPath $Backup)) {
            throw "Refusing to overwrite wrapped entrypoint without backup: $Original"
        }
        return
    }
    if (-not (Test-Path -LiteralPath $Backup)) {
        Copy-Item -LiteralPath $Original -Destination $Backup
        Write-Output "backup: $Backup"
    }
}

function Escape-SingleQuoted {
    param([string]$Value)
    return $Value.Replace("'", "''")
}

if (-not (Test-Path -LiteralPath $target)) {
    throw "Codex PowerShell shim not found: $target"
}

if ($Uninstall) {
    Copy-Back -Backup $ps1Backup -Destination $target
    Copy-Back -Backup $cmdBackup -Destination $cmdTarget
    Copy-Back -Backup $shBackup -Destination $shTarget
    exit 0
}

Backup-Original -Original $target -Backup $ps1Backup -Marker $marker
Backup-Original -Original $cmdTarget -Backup $cmdBackup -Marker $marker
Backup-Original -Original $shTarget -Backup $shBackup -Marker $marker

$workspaceLiteral = Escape-SingleQuoted ([System.IO.Path]::GetFullPath($Workspace))
$rawLiteral = Escape-SingleQuoted $ps1Backup

$psWrapper = @"
# $marker
param(
    [Parameter(ValueFromRemainingArguments = `$true)]
    [string[]]`$Args = @()
)

`$workspace = '$workspaceLiteral'
`$guard = Join-Path `$workspace 'scripts\ams-guarded-command.ps1'
`$raw = '$rawLiteral'

if (`$env:AMS_CODEX_BYPASS -eq '1') {
    & `$raw @Args
    exit `$LASTEXITCODE
}

if (-not (Test-Path -LiteralPath `$guard)) {
    Write-Error "AMS_CODEX_ENTRYPOINT_FAIL: missing guarded launcher at `$guard"
    exit 12
}

`$prompt = 'codex interactive launch'
if (`$Args.Count -gt 0) {
    `$prompt = 'codex ' + (`$Args -join ' ')
}

& `$guard -Workspace `$workspace -Prompt `$prompt -Command `$raw -Quiet -CommandArgs `$Args
exit `$LASTEXITCODE
"@

$cmdWrapper = @"
@ECHO off
REM $marker
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0codex.ps1" %*
EXIT /b %ERRORLEVEL%
"@

$shWrapper = @"
#!/bin/sh
# $marker
basedir=`$(dirname "`$(echo "`$0" | sed -e 's,\\,/,g')")
case ``uname`` in
    *CYGWIN*|*MINGW*|*MSYS*)
        if command -v cygpath > /dev/null 2>&1; then
            basedir=``cygpath -w "`$basedir"``
        fi
    ;;
esac

if [ "``uname``" = "Linux" ] && [ -r /proc/version ] && grep -qi microsoft /proc/version; then
  if command -v wslpath > /dev/null 2>&1; then
    basedir=``wslpath -w "`$basedir"``
  fi
fi

if command -v pwsh > /dev/null 2>&1; then
  exec pwsh -NoProfile -ExecutionPolicy Bypass -File "`$basedir/codex.ps1" "`$@"
elif command -v powershell.exe > /dev/null 2>&1; then
  exec powershell.exe -NoProfile -ExecutionPolicy Bypass -File "`$basedir/codex.ps1" "`$@"
else
  echo "AMS_CODEX_ENTRYPOINT_FAIL: PowerShell is required for the AMS Codex entrypoint" >&2
  exit 12
fi
"@

Set-Content -LiteralPath $target -Value $psWrapper -Encoding UTF8
Write-Output "installed: $target"

if (Test-Path -LiteralPath $cmdTarget) {
    Set-Content -LiteralPath $cmdTarget -Value $cmdWrapper -Encoding ASCII
    Write-Output "installed: $cmdTarget"
}

if (Test-Path -LiteralPath $shTarget) {
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($shTarget, $shWrapper.Replace("`r`n", "`n"), $utf8NoBom)
    Write-Output "installed: $shTarget"
}
