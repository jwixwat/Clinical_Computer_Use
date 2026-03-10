param(
  [Parameter(Mandatory = $true)]
  [string]$SessionId,
  [switch]$SkipContinue,
  [switch]$SkipLifecycle,
  [switch]$SkipCleanupDryRun
)

$ErrorActionPreference = "Stop"

function Invoke-Cli {
  param(
    [Parameter(Mandatory = $true)]
    [string[]]$Args
  )
  python -m clinical_computer_use.main @Args
}

function Assert-PathExists {
  param(
    [Parameter(Mandatory = $true)]
    [string]$PathValue
  )
  if (-not (Test-Path -LiteralPath $PathValue)) {
    throw "Missing expected path: $PathValue"
  }
}

Write-Host "== N0/N1 live smoke start =="
Write-Host "SessionId: $SessionId"

$traceDir = Join-Path "traces" $SessionId
Assert-PathExists -PathValue $traceDir

Write-Host "`n[1] Summarize run (baseline)"
$summaryRaw = Invoke-Cli -Args @("summarize-run", $SessionId)
$summary = (($summaryRaw | Out-String) | ConvertFrom-Json)

if (-not $summary.objective_type) { throw "objective_type missing in summarize output." }
if (-not $summary.version_bundle) { throw "version_bundle missing in summarize output." }
if (-not $summary.lifecycle_state) { throw "lifecycle_state missing in summarize output." }
if (-not $summary.compact_context) { throw "compact_context missing in summarize output." }

Write-Host "Baseline summarize fields present."

Write-Host "`n[2] Verify expected trace artifacts"
$requiredFiles = @(
  "run_state.json",
  "version_bundle.json",
  "lifecycle_state.json",
  "artifact_policy.json",
  "artifact_manifest.jsonl",
  "events.jsonl"
)
foreach ($f in $requiredFiles) {
  Assert-PathExists -PathValue (Join-Path $traceDir $f)
}
Write-Host "Required files exist."

Write-Host "`n[3] Apply correction + re-summarize"
Invoke-Cli -Args @("apply-correction", $SessionId, "Not that one. Not a chart note. Documents first. Checkpoint now.") | Out-Host
$summary2Raw = Invoke-Cli -Args @("summarize-run", $SessionId)
$summary2 = (($summary2Raw | Out-String) | ConvertFrom-Json)

if ($summary2.contract_history_count -lt 1) {
  throw "contract_history_count did not increase after correction."
}
if (-not ($summary2.disallowed_artifact_classes -contains "chart_note")) {
  throw "chart_note not present in disallowed_artifact_classes after correction."
}
if (-not $summary2.preferred_surfaces -or $summary2.preferred_surfaces[0] -ne "documents") {
  throw "preferred_surfaces does not reflect Documents-first after correction."
}
Write-Host "Correction mutation checks passed."

if (-not $SkipContinue) {
  Write-Host "`n[4] Continue run and inspect resume events"
  Invoke-Cli -Args @("continue-agent-task", $SessionId, "--max-steps", "2") | Out-Host
  $eventsPath = Join-Path $traceDir "events.jsonl"
  $events = Get-Content -LiteralPath $eventsPath -ErrorAction Stop
  $resumeEvents = $events | Select-String "bind_and_agent_task_resumed|resume_restore_attempted|resume_restore_succeeded|resume_restore_failed|completion_verifier_decision"
  if (-not $resumeEvents) {
    throw "No resume-related events found after continue."
  }
  Write-Host "Continue/resume checks passed."
}

Write-Host "`n[5] Handoff surface check"
$handoffRaw = Invoke-Cli -Args @("handoff-run", $SessionId)
$handoff = (($handoffRaw | Out-String) | ConvertFrom-Json)
if (-not $handoff.task_understanding) { throw "handoff.task_understanding missing." }
if (-not $handoff.operational_understanding) { throw "handoff.operational_understanding missing." }
if ($null -eq $handoff.where_looked) { throw "handoff.where_looked missing." }
if ($null -eq $handoff.findings) { throw "handoff.findings missing." }
if ($null -eq $handoff.uncertainties) { throw "handoff.uncertainties missing." }
if ($null -eq $handoff.approval_needed) { throw "handoff.approval_needed missing." }
Write-Host "Handoff checks passed."

if (-not $SkipLifecycle) {
  Write-Host "`n[6] Lifecycle stop/archive and blocked continue"
  Invoke-Cli -Args @("stop-run", $SessionId, "--reason", "n0n1_smoke_stop") | Out-Host
  Invoke-Cli -Args @("archive-run", $SessionId, "--reason", "n0n1_smoke_archive") | Out-Host

  $continueBlocked = $false
  try {
    Invoke-Cli -Args @("continue-agent-task", $SessionId, "--max-steps", "1") | Out-Host
  } catch {
    $continueBlocked = $true
  }
  if (-not $continueBlocked) {
    throw "Continue after archive did not fail as expected."
  }
  Write-Host "Lifecycle checks passed."
}

Write-Host "`n[7] Artifact governance checks"
$policyPath = Join-Path $traceDir "artifact_policy.json"
$manifestPath = Join-Path $traceDir "artifact_manifest.jsonl"
Assert-PathExists -PathValue $policyPath
Assert-PathExists -PathValue $manifestPath
$manifestCount = (Get-Content -LiteralPath $manifestPath -ErrorAction Stop).Count
if ($manifestCount -lt 1) {
  throw "artifact_manifest.jsonl is empty."
}
Write-Host "Manifest entries: $manifestCount"

if (-not $SkipCleanupDryRun) {
  Invoke-Cli -Args @("cleanup-artifacts", "--older-than-days", "3650", "--dry-run") | Out-Host
  Write-Host "Cleanup dry-run executed."
}

Write-Host "`n== N0/N1 live smoke completed successfully =="
