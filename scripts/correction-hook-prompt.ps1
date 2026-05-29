# UserPromptSubmit runtime hook for the Correction Capture Controller (§12).
#
# Wire this as the agent runtime's UserPromptSubmit hook. It reads the runtime's
# hook payload from stdin, projects it onto AMS's generic {prompt_text, session_id}
# schema, and pipes that to the CLI. The exit code carries the decision:
#   0  = allow (no correction detected)
#   10 = block (a live correction was captured; the resume gate is now armed)
#   2  = parse/Waki error
#
# Mirrors session-start-gate.ps1 but: (1) pipes the payload via STDIN (not args),
# (2) captures STDOUT ONLY (no `2>&1` -- merging native-exe stderr corrupts the JSON
# stream), and (3) branches on $LASTEXITCODE, not on parsing JSON.
#
# [UNVERIFIED] The projection from the live Claude Code / Codex UserPromptSubmit
# payload onto {prompt_text, session_id} is a best-effort field mapping and MUST be
# confirmed by a live runtime smoke test before this hook is trusted in production.
param(
    [string]$Workspace = "C:\Dev\Builds\Agentic Memory System"
)

$ErrorActionPreference = "Stop"

$amsScript = Join-Path $Workspace "scripts\ams.py"
if (-not (Test-Path $amsScript)) {
    Write-Error "HOOK_PROMPT_FAIL: missing ams.py at $amsScript"
    exit 2
}

$raw = [Console]::In.ReadToEnd()

$promptText = ""
$sessionId = $null
try {
    $hook = $raw | ConvertFrom-Json
    # [UNVERIFIED] candidate field names for the runtime prompt + session id.
    if ($hook.PSObject.Properties.Name -contains "prompt") { $promptText = [string]$hook.prompt }
    elseif ($hook.PSObject.Properties.Name -contains "prompt_text") { $promptText = [string]$hook.prompt_text }
    if ($hook.PSObject.Properties.Name -contains "session_id") { $sessionId = [string]$hook.session_id }
} catch {
    # Non-JSON runtime payload: treat the raw text as the prompt.
    $promptText = $raw
}

$amsPayload = @{ prompt_text = $promptText; session_id = $sessionId } | ConvertTo-Json -Compress
$out = $amsPayload | & python $amsScript correction hook-prompt --json
$code = $LASTEXITCODE

Write-Output "HOOK_DECISION_PROMPT_EXIT: $code"
if ($out) { Write-Output $out }
exit $code
