# Unsigned keeper backup: desktop possession and Ubuntu return

Baseline: `a1b1a5ab4f3f334305b34a4761952d5c215a3a96`, 26 November 2026.
Production is **not approved**. This is one new transport/restore composition,
with no production-code changes or unchanged test-body runs.

## Result and exact scope

The five files of the existing c821 unsigned package were exported from its
stopped Ubuntu lab, saved on the Windows desktop, independently checked against
previously published pins, then returned from those persisted desktop files to
the new c823 Ubuntu lab. The existing journal and sidecar verify/restore CLIs
all succeeded. Both outputs are new **review-only** folders; no live state was
installed or adopted.

| New evidence | Observed result |
| --- | --- |
| Exact desktop package | Five files, 15,046 bytes; complete outer and nested manifest pins match |
| Transport | Export response21,188 bytes; returned input23,891 bytes, each below64KiB |
| Independent desktop proof | `75d2189e6e5ecc177d6836a8dc01fb3b598a3a60f187f3a727bdbad751d2b878` |
| Native Ubuntu operations | Journal verify/restore and sidecar verify/restore: four successes in one worker,0.452s total |
| Restored records | Keeper journal plus four sidecar records match the returned inputs byte-for-byte |
| History and accounting | Stored pending intent/hash, nonce, spending, receipt anchor, event ID, sequence and pending `first_seen` preserved |
| Coordination files | Two new empty private locks, distinct from each other and both unchanged original lock inodes |
| Isolation | Unprivileged worker, private network/AF_UNIX only, original release/runtime read-only, two distinct unreadable root-owned signer masks |
| Cleanup | New unit stopped/empty; four original c821 groups remain fenced; original source/configuration/policy/package hashes unchanged |
| Existing host state | Settled readback matches five existing service states:0 nonambient differences,1 disclosed observer invocation-ID change |

The c821 journal/outbox is a **synthetic fixture**, including its pending hash
and accounting values. This proves exact storage and transport of that history,
not that the synthetic transaction exists on-chain or that this backup is the
latest canonical journal. The previous [actual keeper/timer composition](../ubuntu-keeper-composition-20261126/REVIEW.md)
retains its separate actual local transaction and recovery scope.

## Trust, privacy and time

Trust was copied from a Git blob at the baseline revision, before receiving the
package: [original SOURCE_RESULT](../keeper-sidecar-recovery-20261126/evidence/c821/fetch-6/SOURCE_RESULT.json),
SHA-256 `9bec125bedd73b6f80cb3f316a7822aa09aeb9198927ca8d901c476f3798c371`.
It is separate from incoming manifests and their claimed checksums. The outer
manifest pin is `a9dea475a22014c7eb5fcf965896eb691a2ba5c8de352e0c23d6fd1611dbb05b`;
the nested journal manifest pin is `911d98ef86b1cd229378ae15ac685e8ce67285c0035c8cf670dfca3cccc5d0d1`.
The [provenance record](verification/TRUST_PROVENANCE.json) binds that source.

Raw packages and SSH captures remain in a separate ignored private desktop
store outside this checkout. Only explicitly allowlisted sanitized receipts,
hashes and review helpers are published. Configuration, original policy and
keeper signer material are never exported. The original separately retained
release/configuration/layout remains available read-only on Ubuntu; this
exercise does not reconstruct it after host loss.

Actual wall-clock age was7,719 seconds during the Ubuntu check, exceeding the
unchanged900-second operating backup freshness policy. The existing recovery
CLIs used an explicit86,400-second **historical review** allowance and original
capture floor1795723324. No clock override, new capture, timestamp rewrite or
manifest regeneration occurred. Operational freshness, readiness, canonical
truth, installation, service adoption and restored lock ownership all remain
unapproved. Native16MiB/60-second tool budgets stay unchanged.

## Preparation corrections and retained failures

These were new campaign-helper/environment corrections, not keeper defects:

1. The first SSH attempt failed locally with connection permission denied.
   The network-enabled process then refused the new task folder's restrictive
   Windows permissions before connecting. Access was added only for the two
   local execution accounts in this new private store; owner/System/administrator
   entries were retained, with no public grant. The wrapper now inherits that
   protected parent on Windows; POSIX0700 behavior is unchanged. The original
   wrapper and independent AST comparison are preserved.
2. The first desktop verifier refused the pinned historical report's finite
   `elapsed_seconds` decimal. The corrected helper permits only that nonnegative
   root duration **after** the exact trusted raw-report hash check. All five
   package JSON decodes still reject decimals/constants. The original helper,
   failed outcome and independent affected-code review are retained.
3. The first final host snapshot caught the existing periodic observer running.
   Its original comparison remains [NONPASS](verification/ORIGINAL_HOST_COMPARISON_NONPASS.json),
   with five live-observer differences. A separate settled readback later
   [passes](verification/HOST_PRESERVATION.json). No observer was stopped or
   reconfigured, and no new ignore rules were introduced.

Pre-execution review also strengthened the new witness: closed bounded package
inventories, stable bounded file reads, returned proof/member bindings, native
CLI-output-to-plan hashes and new-versus-original lock identity checks. No
existing component suite was rerun to validate these new boundaries.

## Verification and preservation

The [saved worker result](evidence/c823/fetch-result/RESULT.json) records the four
actual commands, real capture ages, output hashes and false adoption flags.
The [desktop proof](evidence/desktop/DESKTOP_PROOF.json),
[import receipt](evidence/c823/fetch-install/INSTALL.json) and
[stopped-state receipt](evidence/c823/fetch-final/FINAL.json) establish the
bounded transport/restore chain. [Independent reconciliation](verification/OFFHOST_VERIFICATION.json)
checks these saved records; it does not rerun application or test bodies.

All41 original lab source rows match the baseline. Production Python/Solidity,
the thirteen daemon and nineteen scheduler source identities, financial/resource
limits, workload plan and test selectors are unchanged. Reuse the current
[191-file/2,137-definition/279-lambda inventory](../keeper-sidecar-recovery-20261126/FUNCTION_INVENTORY.json);
F6 remains61/39/4 source/dependency/control maps and1,021 ABI rows. No duplicate
unchanged inventory is generated. The83 stable Todo IDs/statuses are retained.

No RPC calls, transactions, deployment, sealing, existing-service restart,
website rollout, Anvil reset, journal adoption or desktop-monitor restart were
performed. Only the new unsigned c823 unit was started and stopped. The four
unrelated dirty tracked files and prior report artifacts remain untouched.

## What remains open

This closes a bounded **desktop possession and same-server return** partition.
It does not close Q06/P20/P21 as whole packages. Independent second-host
execution, old-host/signer fencing and restart paths, current canonical
transaction reconciliation, separately protected configuration/signer recovery,
off-site disaster-domain/encryption/durability policy, real alert/host-down
delivery, sustained operation and independent release approval remain open.

Use the [operator procedure](../../docs/OPERATOR_MANUAL.md#off-host-backup-transfer-and-review)
and [recovery guide](../../docs/KEEPER_SIDECAR_RECOVERY.md). A passing unsigned
restore is not permission to start a live keeper.
