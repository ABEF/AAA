# Unsigned off-host backup round-trip — execution plan

Baseline: `a1b1a5ab4f3f334305b34a4761952d5c215a3a96`.
This is a transport/possession and returned-review-folder check, not approval
for live restoration, host-loss recovery or second-server signer failover.

## Reuse and trust

Use the existing stopped c821 synthetic sidecar package and its nested selected
journal backup. Do not recapture, rewrite or initialize any original state.
Trusted outer/nested manifest, policy, configuration and payload expectations
come from the separately retained SOURCE_RESULT in this pinned Git revision.
That trust record is distinct from the incoming packet and desktop package.

Only five exact files may leave Ubuntu: outer manifest, selected record, alert
state, nested manifest and nested journal. No policy, configuration, signer,
health file or other directory entry is exported. Raw packages and wire captures
stay in a separate ignored desktop store outside the source checkout and Git
publication. Publish only explicitly sanitized metadata and review evidence.

## New bounded operating composition

1. Read-only export: verify original c821 service groups fenced and exact source
   package bytes/inventory stable before and after capture. Leave original
   services, locks and journals alone.
2. Persist the five exact files on the desktop. Independently re-read and verify
   them against the trusted record, including identity, selected generation,
   pending nonce/cost data, event IDs, sequence and observed pending clock.
   Windows hash/structure checks do not claim POSIX or native-core validation.
3. Build the return input from those persisted desktop files and its independently
   reviewed receipt. Upload into one fresh private Ubuntu lab. No server-original
   package fallback, source edits, secret copying or runtime adoption is allowed.
4. Run the existing journal verify/restore and sidecar verify/restore CLIs under
   a signer-masked, network-isolated account. Use separately retained original
   policy/configuration/release/layout read-only; write only exclusive new review
   folders. Compare every restored raw byte, stored accounting/history, new lock
   inodes and all false readiness/adoption/freshness flags.
5. Stop the new owned job, verify original files/fences again and compare the
   separate before/after existing host snapshots. Independently reconcile saved
   sanitized evidence before accepting the result. Preserve any original failure.

## Actual time and limits

The old operating policy's900-second backup freshness remains unchanged. These
retained packages are older and must not be described as operationally fresh.
The existing CLIs require a separate caller-selected recovery age: review this
unsigned exercise with86400 seconds and trusted original capture floors. Keep
real wall-clock time and original timestamps; do not backdate verification or
create a new manifest to make old data appear fresh. Internal nested historical
integrity checks remain the existing implementation, not current freshness proof.

Keep native16MiB/60-second budgets and the existing64KiB bounded transport
capture. If the fixed packet exceeds its reviewed framing/output limits, refuse
without truncation, automatic increases or partial publication. Reuse completed
component proofs; run only this missing round-trip and necessary new-boundary
checks. No RPC, transaction, deployment, sealing or desktop-monitor restart.

Actual host loss, independent second-host execution and fencing, off-site
disaster-domain/encryption assurance, real notification delivery and sustained
operation remain separate acceptance work.
