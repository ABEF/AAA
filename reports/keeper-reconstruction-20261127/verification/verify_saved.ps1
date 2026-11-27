param([switch]$UseSavedPrivateReview)
$ErrorActionPreference = 'Stop'
$repo = 'C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2'
$private = 'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/keeper-reconstruction-20261127/private'
$review = Join-Path $repo 'cache-keeper-reconstruction-20261127/review'
$inputs = [ordered]@{}
function Need($condition, $label) { if (-not $condition) { throw ('Saved evidence refused: ' + $label) } }
function Sha([byte[]]$raw) { return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($raw)).ToLowerInvariant() }
function Same($left, $right) { return (ConvertTo-Json -InputObject $left -Compress -Depth 64) -ceq (ConvertTo-Json -InputObject $right -Compress -Depth 64) }
function Bytes([string]$path, [int]$maximum = 65536) {
    $item = Get-Item -LiteralPath $path -Force
    Need (-not $item.PSIsContainer -and -not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -and $item.Length -le $maximum) 'bounded regular input'
    $raw = [IO.File]::ReadAllBytes($path)
    Need ($raw.Length -eq $item.Length -and $raw.Length -le $maximum) 'complete input read'
    $script:inputs[$path.Replace('\','/').Replace($private, 'PRIVATE').Replace($repo, 'REPOSITORY')] = [ordered]@{bytes=$raw.Length; sha256=(Sha $raw)}
    return ,$raw
}
function Json([string]$path, [int]$maximum = 65536) { return [Text.Encoding]::UTF8.GetString((Bytes $path $maximum)) | ConvertFrom-Json -AsHashtable }

# Read-only Windows handle metadata, independent of application/helper code.
if (-not $UseSavedPrivateReview) { Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
public static class SavedKitFileInfo {
 [StructLayout(LayoutKind.Sequential)] public struct Info {
  public uint Attributes, CreationLow, CreationHigh, AccessLow, AccessHigh, WriteLow, WriteHigh;
  public uint Volume, SizeHigh, SizeLow, Links, IndexHigh, IndexLow;
 }
 [DllImport("kernel32.dll", SetLastError=true)] public static extern bool GetFileInformationByHandle(IntPtr h, out Info info);
}
'@
}
function PrivateFile([string]$path, [int]$maximum) {
    $before = Get-Item -LiteralPath $path -Force
    Need (-not $before.PSIsContainer -and -not ($before.Attributes -band [IO.FileAttributes]::ReparsePoint) -and $before.Length -gt 0 -and $before.Length -le $maximum) 'private file shape'
    $stream = [IO.File]::Open($path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
    try {
        $first = New-Object SavedKitFileInfo+Info
        Need ([SavedKitFileInfo]::GetFileInformationByHandle($stream.SafeFileHandle.DangerousGetHandle(), [ref]$first)) 'handle metadata'
        Need ($first.Links -eq 1 -and ($first.IndexHigh -ne 0 -or $first.IndexLow -ne 0)) 'private single link and inode'
        $raw = [byte[]]::new([int]$before.Length)
        $at = 0
        while ($at -lt $raw.Length) { $count = $stream.Read($raw, $at, $raw.Length-$at); Need ($count -gt 0) 'private complete read'; $at += $count }
        Need ($stream.ReadByte() -eq -1) 'private size bound'
        $after = New-Object SavedKitFileInfo+Info
        Need ([SavedKitFileInfo]::GetFileInformationByHandle($stream.SafeFileHandle.DangerousGetHandle(), [ref]$after)) 'final handle metadata'
        Need ($first.Volume -eq $after.Volume -and $first.IndexHigh -eq $after.IndexHigh -and $first.IndexLow -eq $after.IndexLow -and $after.Links -eq 1 -and $first.SizeLow -eq $after.SizeLow -and $first.SizeHigh -eq $after.SizeHigh -and $first.WriteLow -eq $after.WriteLow -and $first.WriteHigh -eq $after.WriteHigh) 'stable private metadata'
        return [ordered]@{bytes=$raw.Length; sha256=(Sha $raw); links=$after.Links; volume=$after.Volume; inode_high=$after.IndexHigh; inode_low=$after.IndexLow}
    } finally { $stream.Dispose() }
}

if ($UseSavedPrivateReview) {
    $report = Json (Join-Path $review 'SAVED_EVIDENCE_REVIEW.json')
    Need ($report.success -eq $true -and $report.private_kit.files -eq 49 -and $report.private_kit.bytes -eq 820029 -and $report.private_kit.proof_sha256 -eq '8411480086dfe7586308dd33edd5823b7500ccffc5a9e07e8dbfd2beb69fb39c' -and $report.private_kit.Windows_single_link_handle_metadata_checked -eq $true) 'prior independent private rehash receipt'
    $normalizedInputs = [ordered]@{}
    foreach ($entry in $report.inputs.GetEnumerator()) { $normalizedInputs[$entry.Key.Replace('\','/').Replace($private,'PRIVATE').Replace($repo,'REPOSITORY')]=$entry.Value }
    $report.inputs=$normalizedInputs
} else {
$proofPath = Join-Path $private 'campaign-001/proof/KIT_PROOF-004.json'
$proofRaw = Bytes $proofPath
Need ((Sha $proofRaw) -eq '8411480086dfe7586308dd33edd5823b7500ccffc5a9e07e8dbfd2beb69fb39c') 'authoritative final proof pin'
$proof = [Text.Encoding]::UTF8.GetString($proofRaw) | ConvertFrom-Json -AsHashtable
$cli = Json (Join-Path $private 'campaign-001/proof/FINAL_CLI_EXECUTION.json')
Need ($cli.exit_code -eq 0 -and $cli.helper_sha256 -eq 'd1819f24c0735d1b61b961b20140e7ec2caaa83e1b4329fceba90e23bb27e5c2' -and $cli.app_or_test_bodies_executed -eq 0 -and $cli.stderr_bytes -eq 0) 'final changed CLI success'
$cliOutput = Json (Join-Path $private 'campaign-001/proof/FINAL_CLI.stdout')
Need ($cliOutput.ok -eq $true -and $cliOutput.proof_sha256 -eq (Sha $proofRaw) -and $cliOutput.total_bytes -eq 820029) 'CLI proof binding'
Need ($proof.ok -eq $true -and $proof.file_count -eq 49 -and $proof.source_file_count -eq 41 -and $proof.files.Count -eq 49) 'kit closed count'
$kit = Join-Path $private 'campaign-001/kit'
$physical = @(Get-ChildItem -LiteralPath $kit -Recurse -File -Force)
Need ($physical.Count -eq 49) 'private physical file count'
$privateRows = [ordered]@{}; $total = 0
foreach ($name in $proof.files.Keys) {
    Need ($name -notmatch '(^/|\\|(^|/)\.\.(/|$))') 'fixed relative kit path'
    $record = PrivateFile (Join-Path $kit $name) 1048576
    Need ($record.bytes -eq $proof.files[$name].bytes -and $record.sha256 -eq $proof.files[$name].sha256) 'private exact hash/length'
    $privateRows[$name] = $record; $total += $record.bytes
}
Need ($total -eq 820029 -and $total -eq $proof.total_bytes) 'private total bytes'
Need ($proof.source13_sha256.Count -eq 13 -and $proof.source19_sha256.Count -eq 19) 'original source maps'

$negativePath = Join-Path $private 'campaign-002/fetch-negative/RESULT-negative.json'
$negativeRaw = Bytes $negativePath
Need ($negativeRaw.Length -eq 3714 -and (Sha $negativeRaw) -eq 'ad5813b9433039f5cf35925988bc673833b4b5c7f7a237d3e8a5ca21d9d0390d') 'passed negative pin'
$negative = [Text.Encoding]::UTF8.GetString($negativeRaw) | ConvertFrom-Json -AsHashtable
$positive = Json (Join-Path $private 'campaign-002/fetch-complete/RESULT-complete.json')
Need ($negative.success -eq $true -and $negative.calls.Count -eq 1 -and $negative.native_refusal_before_restore -eq $true -and $negative.calls[0].returncode -eq 1 -and $negative.calls[0].parsed.fixed_native_refusal -eq 'invalid_input' -and $negative.calls[0].parsed.restoration_outputs_absent -eq $true) 'one missing-config native refusal'
Need ($positive.success -eq $true -and $positive.calls.Count -eq 4 -and $positive.all_adoption_flags_false -eq $true -and $positive.signer_material_absent -eq $true) 'four positive native operations'
$expectedScripts = @('keeper-recovery.py','keeper-recovery.py','keeper-sidecar-recovery.py','keeper-sidecar-recovery.py')
$expectedActions = @('verify','restore','verify','restore')
for ($index=0; $index -lt 4; $index++) {
    $call = $positive.calls[$index]
    Need ($call.script -eq $expectedScripts[$index] -and $call.action -eq $expectedActions[$index] -and $call.returncode -eq 0 -and $call.stderr_bytes -eq 0 -and (Same $call.python_flags @('-I','-S','-B'))) 'native fixed command result'
}
Need ($positive.calls[0].parsed.manifest_or_plan_sha256 -eq $proof.nested_manifest_sha256 -and $positive.calls[1].parsed.manifest_or_plan_sha256 -eq $positive.native_restore_plan_sha256 -and $positive.calls[2].parsed.manifest_sha256 -eq $proof.outer_manifest_sha256 -and $positive.calls[3].parsed.restore_plan_sha256 -eq $positive.sidecar_restore_plan_sha256) 'native output plan binding'
$mapping = @{'keeper-state.json'='package/selected/journal.json'; 'scheduler/selected.json'='package/selection.json'; 'alerts/state.json'='package/alert-state.json'; 'selected/manifest.json'='package/selected/manifest.json'; 'selected/journal.json'='package/selected/journal.json'}
foreach ($name in $mapping.Keys) { Need ($positive.restored_files[$name].bytes -eq $proof.files[$mapping[$name]].bytes -and $positive.restored_files[$name].sha256 -eq $proof.files[$mapping[$name]].sha256) 'recorded restored raw binding' }
$observer = Json (Join-Path $kit 'package/alert-state.json')
Need ($positive.sequence -eq $observer.sequence -and (Same $positive.pending_summary $observer.pending) -and (Same $positive.outbox_ids @($observer.outbox | ForEach-Object {$_.event_id}))) 'exact observer history'
foreach ($result in @($negative,$positive)) {
    foreach ($flag in @('readiness_approved','production_approved','canonical_state_verified','operational_freshness_approved','asof_clock_override','old_policy_changed','source_services_started')) { Need ($result[$flag] -is [bool] -and $result[$flag] -eq $false) ('false flag ' + $flag) }
    Need ($result.RPC_calls -eq 0 -and $result.public_transactions -eq 0 -and $result.test_bodies_run -eq 0 -and $result.operating_policy_max_backup_age_seconds -eq 900 -and $result.new_review_max_age_seconds -eq 86400) 'unchanged policy and zero live actions'
    Need ($result.isolation.root_directory_is_new -eq $true -and $result.isolation.host_opt_mounted -eq $false -and $result.isolation.original_operating_state_absent -eq $true -and $result.isolation.source_files_verified -eq 41 -and $result.isolation.actual_second_host -eq $false -and $result.isolation.OS_disaster_recovery_proved -eq $false -and $result.isolation.external_runtime_mounts.Count -eq 18 -and -not (Same $result.isolation.old_source_manifest_inode_pair $result.isolation.new_source_manifest_inode_pair)) 'fresh root scope'
    Need ($result.original_capture_times.outer -eq 1795723324 -and $result.actual_wallclock_epoch - $result.original_capture_times.outer -eq $result.capture_ages_seconds.outer -and $result.capture_ages_seconds.outer -gt 900 -and $result.capture_ages_seconds.outer -le 86400) 'actual historical age'
}
$runtimePath = Join-Path $private 'campaign-002/export/RUNTIME_REVIEW.json'
$runtimeRaw = Bytes $runtimePath
Need ((Sha $runtimeRaw) -eq '3025d86be5de48fd1643ddd53819fe3ef1d9268dca689749827ad399247abdb6') 'actual runtime pin'
Need ($positive.isolation.external_runtime_sha256 -eq (Sha $runtimeRaw) -and $negative.isolation.external_runtime_sha256 -eq (Sha $runtimeRaw)) 'both root runtime bindings'
$continuation = Json (Join-Path $private 'campaign-002/start-complete-continuation/EXECUTION.json')
Need ($continuation.exit_code -eq 0 -and $continuation.continuation_sha256 -eq '8bb549d88b8704afcfd73d0c4f8d408e4e6c16281ab82538a6467714759ff082' -and $continuation.preserved_controller_sha256 -eq 'f102550ea30927350c5b815fda020ccf4ea6a23fae00379668af8ccba351f10e' -and $continuation.passed_negative_result_sha256 -eq (Sha $negativeRaw) -and $continuation.installer_or_negative_called -eq $false) 'separate continuation provenance'
$install = Json (Join-Path $private 'campaign-002/fetch-install/INSTALL.json')
$final = Json (Join-Path $private 'campaign-002/fetch-final/FINAL.json')
Need ($install.original_unchanged -eq $true -and $install.outer_private_directory_uid -eq 0 -and $install.outer_private_directory_mode -eq 448 -and $install.input_files.Count -eq 49 -and $install.desktop_proof_sha256 -eq (Sha $proofRaw)) 'private install chain'
foreach ($field in @('source_manifest_sha256','source_files','references','retained_original_files','old_lock_metadata','old_source_manifest_inode_pair')) { Need (Same $install.original_before[$field] $final.original_after[$field]) ('original preservation ' + $field) }
Need ($final.original_unchanged -eq $true -and $final.new_groups_empty -eq $true -and $final.old_four_groups_fenced -eq $true -and $final.original_after.retained_original_files.Count -eq 8) 'original state and cleanup'
Need ($positive.new_empty_locks.Count -eq 2 -and $positive.new_locks_disjoint_from_originals -eq $true) 'new lock count'
$lockIds = @()
foreach ($lock in $positive.new_empty_locks) { Need ($lock.bytes -eq 0 -and $lock.links -eq 1 -and $lock.uid -eq 65534 -and $lock.mode -eq 384) 'new lock metadata'; $lockIds += "$($lock.device):$($lock.inode)" }
Need (($lockIds | Select-Object -Unique).Count -eq 2) 'new lock uniqueness'
foreach ($old in $install.original_before.old_lock_metadata) { Need ($lockIds -notcontains "$($old[0]):$($old[1])") 'new lock old disjoint' }
foreach ($state in $final.units.Values) { Need ($state.group_empty -eq $true -and $state.after_stop.MainPID -eq '0') 'new stopped group' }
$c824 = Json (Join-Path $private 'campaign-001/status-001/SANITIZED_RESULT.json')
$c824Final = Json (Join-Path $private 'campaign-001/fetch-final/FINAL.json')
Need ($c824.units.negative.properties.ExecMainStatus -eq '127' -and $c824.units.negative.result_present -eq $false -and $c824.units.complete.result_present -eq $false -and $c824.units.complete.properties.LoadState -eq 'not-found' -and $c824Final.new_groups_empty -eq $true -and $c824Final.original_unchanged -eq $true) 'retained zero-native c824 failure'

$report = [ordered]@{
 schema=1; kind='independent_saved_reconstruction_evidence_review'; success=$true
 activity=@{application_imports=0; native_calls=0; server_calls=0; network_requests=0; test_bodies=0; application_or_prior_helper_reruns=0}
 private_kit=@{files=49; source_files=41; bytes=$total; independently_rehashed=$true; Windows_single_link_handle_metadata_checked=$true; proof_sha256=(Sha $proofRaw); metadata=$privateRows}
 native=@{negative_calls=1; positive_calls=4; positive_seconds=$positive.elapsed_seconds; positive_age_seconds=$positive.capture_ages_seconds.outer; all_adoption_flags_false=$true; signer_absent=$true; RPC_calls=0; public_transactions=0}
 preservation=@{original_selected_files=8; original_source_files=41; original_references_and_locks_unchanged=$true; c824_groups_empty=$true; c825_groups_empty=$true}
 retained_failures=@{c824_startup_exit127_zero_worker_results=$true; original_export_metadata_refusal_retained=$true; original_Windows_DirEntry_refusal_retained=$true; corrected5d_direct_refusal_cause='uncaptured'; traced5d_success_is_separate=$true; original_c825_float_gate_refusal_retained=$true}
 scope='Finite same-server application/layout reconstruction with explicit external OS runtime. No second host, OS disaster recovery, canonical transaction truth, physical durability, cross-host fencing or production readiness is proved.'
 independent_physical_restored_output_rehash=$false
 restored_output_review='Recorded Linux worker raw equality assertions, hashes and lengths reconcile to independently rehashed desktop inputs; raw server restored outputs were not independently fetched/rehashed.'
 host_preservation='Separate five-service-state comparison remains to be checked against the final curated report; no claim about every host byte.'
 inputs=$inputs
}
}

# This second phase checks newly curated records and the final five-state host
# comparison. -UseSavedPrivateReview reuses the already completed independent
# private-file rehash; it does not repeat native/application/helper work.
$public = Join-Path $repo 'reports/keeper-reconstruction-20261127'
$publicProofRaw = Bytes (Join-Path $public 'evidence/desktop/KIT_PROOF.json')
Need ((Sha $publicProofRaw) -eq $report.private_kit.proof_sha256) 'curated proof exact copy'
$publicProof = [Text.Encoding]::UTF8.GetString($publicProofRaw) | ConvertFrom-Json -AsHashtable
$sourceCount = 0
foreach ($name in $publicProof.files.Keys) {
    if (-not $name.StartsWith('source/')) { continue }
    $relative = $name.Substring(7)
    Need ($relative -match '^(keeper|zzz_ops|scripts|tests_python)/[A-Za-z0-9_-]+\.py$') 'source relative path'
    $sourceRaw = Bytes (Join-Path $repo $relative) 1048576
    Need ($sourceRaw.Length -eq $publicProof.files[$name].bytes -and (Sha $sourceRaw) -eq $publicProof.files[$name].sha256) 'current source41 bytes'
    $sourceCount++
}
$gitHead = (& git -C $repo rev-parse HEAD 2>$null).Trim()
$release = Json (Join-Path $public 'preparation/desktop/RELEASE_PREPARATION.json')
Need ($sourceCount -eq 41 -and $release.source_commit -eq 'a418a567abbc3c0b7c6dd8425ef31306e8e48f17' -and $gitHead -eq $release.source_commit -and $release.release_files -eq 41) 'original Git/source origin'
foreach ($pair in @(
    @('campaign-002/fetch-negative/RESULT-negative.json','evidence/campaign-002/fetch-negative/RESULT-negative.json'),
    @('campaign-002/fetch-complete/RESULT-complete.json','evidence/campaign-002/fetch-complete/RESULT-complete.json'),
    @('campaign-002/fetch-install/INSTALL.json','evidence/campaign-002/fetch-install/INSTALL.json'),
    @('campaign-002/fetch-final/FINAL.json','evidence/campaign-002/fetch-final/FINAL.json'),
    @('campaign-002/start-complete-continuation/EXECUTION.json','evidence/campaign-002/start-complete-continuation/EXECUTION.json'),
    @('campaign-002/export/RUNTIME_REVIEW.json','evidence/campaign-002/export/RUNTIME_REVIEW.json'),
    @('campaign-001/status-001/SANITIZED_RESULT.json','evidence/campaign-001/status-001/SANITIZED_RESULT.json'),
    @('campaign-001/fetch-final/FINAL.json','evidence/campaign-001/fetch-final/FINAL.json'))) {
    $copied = Bytes (Join-Path $public $pair[1])
    Need ((Sha $copied) -eq $report.inputs['PRIVATE/'+$pair[0]].sha256) 'curated saved-record exact copy'
}
$controller = Bytes (Join-Path $public 'preparation/c825/remote_capsule.py')
$combined = Bytes (Join-Path $public 'preparation/c825/continuation/complete_continuation.py')
Need ($controller.Length -eq 56751 -and (Sha $controller) -eq 'f102550ea30927350c5b815fda020ccf4ea6a23fae00379668af8ccba351f10e' -and $combined.Length -eq 61737 -and (Sha $combined) -eq '8bb549d88b8704afcfd73d0c4f8d408e4e6c16281ab82538a6467714759ff082') 'preserved and continuation source pins'
$prefixBytes = [Text.Encoding]::UTF8.GetByteCount("__name__='_preserved_c825_controller'`n")
for ($offset=0; $offset -lt $controller.Length; $offset++) { Need ($controller[$offset] -eq $combined[$prefixBytes+$offset]) 'exact preserved controller slice' }
$outcomes = Json (Join-Path $public 'review/ORIGINAL_OUTCOMES.json')
$outcomeMap = @{}; foreach ($row in $outcomes.outcomes) {$outcomeMap[$row.id]=$row}
Need ($outcomeMap.c824_negative_startup.status -eq 'NONPASS' -and $outcomeMap.'5d_desktop_direct_preflight'.status -eq 'refused' -and $outcomeMap.'5d_desktop_direct_preflight'.reason.StartsWith('uncaptured') -and $outcomeMap.d181_structured_CLI.status -eq 'pass' -and $outcomeMap.c825_original_complete_gate.status -eq 'refused') 'retained distinct helper outcomes'
$hostReview = Json (Join-Path $public 'verification/HOST_PRESERVATION.json')
$hostRoot = 'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/history-export-20261124/host-preservation'
$hostBeforeRaw = Bytes (Join-Path $hostRoot 'before-019/HOST_SNAPSHOT.json')
$hostFinalRaw = Bytes (Join-Path $hostRoot 'final-019/HOST_SNAPSHOT.json')
Need ((Sha $hostBeforeRaw) -eq $hostReview.before_snapshot_sha256 -and (Sha $hostFinalRaw) -eq $hostReview.final_snapshot_sha256) 'host snapshot raw pins'
$hostBefore = [Text.Encoding]::UTF8.GetString($hostBeforeRaw) | ConvertFrom-Json -AsHashtable
$hostFinal = [Text.Encoding]::UTF8.GetString($hostFinalRaw) | ConvertFrom-Json -AsHashtable
Need ($hostBefore.existing_units.Count -eq 5 -and $hostFinal.existing_units.Count -eq 5 -and $hostBefore.snapshot_complete -eq $true -and $hostFinal.snapshot_complete -eq $true -and $hostBefore.service_actions -eq 0 -and $hostFinal.service_actions -eq 0) 'five saved host states'
$observerChanges = 0
for ($unitIndex=0; $unitIndex -lt 5; $unitIndex++) {
    $beforeUnit=$hostBefore.existing_units[$unitIndex]; $afterUnit=$hostFinal.existing_units[$unitIndex]
    Need ($beforeUnit.unit -eq $afterUnit.unit -and (Same @($beforeUnit.properties.Keys) @($afterUnit.properties.Keys))) 'same five host units'
    foreach ($field in $beforeUnit.properties.Keys) {
        if ($beforeUnit.properties[$field] -ceq $afterUnit.properties[$field]) { continue }
        Need ($beforeUnit.unit -eq 'zzz-stage-observer.service' -and $field -eq 'InvocationID') 'no nonambient host-state difference'
        $observerChanges++
    }
}
Need ($observerChanges -eq 1 -and $hostReview.success -eq $true -and $hostReview.non_ambient_difference_count -eq 0 -and $hostReview.ignored_observer_invocation_count -eq 1 -and $hostReview.existing_units_checked -eq 5 -and $hostBefore.all_seven_owned_labs_stopped -eq $true -and $hostFinal.all_seven_owned_labs_stopped -eq $true) 'exact host scope'
$publishedCount=0
foreach ($file in Get-ChildItem -LiteralPath $public -Recurse -File -Force) {
    Need ($file.Extension -ne '.raw' -and $file.Name -notin @('manifest.json','journal.json','selection.json','alert-state.json','policy.json','keeper-config.json')) 'no raw operational file published'
    $publishedCount++
    if ($file.Extension -ne '.json') { continue }
    $value = Json $file.FullName 1048576; $stack=[Collections.Generic.Stack[object]]::new(); $stack.Push($value)
    while ($stack.Count -gt 0) {
        $entry=$stack.Pop()
        if ($entry -is [Collections.IDictionary]) {
            foreach ($keyName in $entry.Keys) { Need ($keyName -notin @('raw_base64','desktop_proof_base64','password','private_key','mnemonic')) 'no raw or secret JSON fields published'; $stack.Push($entry[$keyName]) }
        } elseif ($entry -is [array]) { foreach($child in $entry) {$stack.Push($child)} }
    }
}
$report.host_preservation = [ordered]@{existing_service_states=5; nonambient_differences=0; disclosed_observer_invocation_changes=1; private_snapshots_independently_rehashed=$true; exact_property_comparison=$true; whole_host_byte_equality_claimed=$false}
$report.curated_checks = [ordered]@{saved_records_match_independently_reviewed_private_inputs=$true; current_original_source_files=41; Git_source_origin=$gitHead; continuation_preserved_slice_independently_equal=$true; original_outcomes_retained=$true; published_files_checked=$publishedCount; raw_operational_files_published=0; forbidden_raw_secret_JSON_fields=0}
foreach ($entry in $inputs.GetEnumerator()) { $report.inputs[$entry.Key]=$entry.Value }
$report.verifier_source_sha256 = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
$output = Join-Path $public 'verification/RECONSTRUCTION_VERIFICATION.json'
Need (-not (Test-Path -LiteralPath $output)) 'new independent report'
[IO.File]::WriteAllText($output, (ConvertTo-Json -InputObject $report -Depth 64) + "`n", [Text.UTF8Encoding]::new($false))
Write-Output ('Saved evidence PASS:49 private files/820029 bytes independently rehashed;1 negative+4 positive native records;original8 files and41 sources preserved;both labs stopped;5 host states/0 nonambient/1 observer change.')
