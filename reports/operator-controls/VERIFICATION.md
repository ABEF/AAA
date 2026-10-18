# Operator-control verification - 2026-10-19

**Local development evidence; release remains NOT APPROVED.**
Baseline main: `a99b54b2b84c3e78fc77dcce5528f5739731a8cb`.
Read the [internal review](REVIEW.md) and [operator manual](../../docs/OPERATOR_MANUAL.md).

## Implemented

- Governance can restrict an admitted pool through `disablePool` without
  token/oracle/wrapper/venue calls. Selected flags can only be cleared; enabling
  still uses full `configure` / `configureNative` validation.
- Governance can pause/resume new NFT mints through `setMintPaused`. Minting
  checks before request creation and after the receiver callback. Original
  fulfillment/finalization and existing NFT/LP rights keep their own guards.
- Confirmed protocol/readiness responses expose the separate mint switch and
  combined mint-control availability. No fallback treats a missing getter as open.
- The manual, central Todo, feature/release references and repository context
  document exact permissions, recovery, successor configuration and limitations.

## Scoped evidence

| Check | Result and scope |
| --- | --- |
| [Affected Solidity coverage](solidity-verification.json) | **140 distinct passing cases**. Initial run: 139 passes, one fixture failure. Corrected control suites: 12 passes; 128 other successful cases retained only after complete compiler-dependency comparison. This is combined scoped coverage, not one fresh complete regression. |
| [Read API checks](python-verification.json), [log](python-tests.log) | **100 passes** on an isolated published HEAD snapshot plus four intended Python edits. Protocol, readiness, lifecycle, lineage and history behavior; mock RPC and local HTTP only. Unrelated drafts were excluded. |
| [Normal production sizes and bindings](size-gates.json), [build receipt](build-receipt.json) | **30 object size gates pass, all 39 production sources bound** to current compiler metadata. NFT runtime/initcode object: 23,502/43,281 bytes; Registry: 12,292/33,898. Vault is unchanged at 24,557 runtime bytes, leaving 19. Constructor arguments need separate allowance. |
| [Fresh Slither execution](static-execution.json), [review coverage](static-review-summary.json) | **378 matched expressions**: 157 false positives, 75 accepted risks, 146 informational. Affected NFT/Registry rationales were updated, coverage passes, five corrupted-review mutations reject. No independent audit claim. |
| [ABI entries](abi-check.json), [change scope](scope.json) | Two changed production sources: NFT and PoolRegistry. The other 37 production Solidity sources are byte-for-byte unchanged. New functions/events/getter are in the actual compiled ABI. |

The new tests cover sealed exact governance versus guardian/keeper/bootstrap/
unprivileged calls; disablement with reverting price/token/venue dependencies;
idempotent/selective stops; failed and successful full-validation reopen;
global pause and canonical locks; callback pause rollback; no spent mint payment
or new request while paused; pending original reveal; existing activation,
top-up, rebalance, transfer, LP claim and royalty claim; and rejected activation/
top-up while pool deposits are stopped without removing prior rights.

The single failed test impersonated the NFT owner for only the next call, which
was the royalty-ledger getter. The subsequent claim correctly rejected the test
contract. A diagnostic trace confirmed this; the fixture now retains owner
impersonation through the claim. Production code and the expected payout were
unchanged. [Initial](initial-receipt.json) and [corrected](controls-receipt.json)
receipts are retained. Only the new control suites needed rerunning.

The first size command compiled and printed sizes but could not finalize its
Foundry cache in the sandbox. A cached retry with tooling-cache access exited
zero without source changes. The [original diagnostic](build-cache-diagnostic.json)
is preserved. [Raw receipt hashes and external locations](raw-evidence.json)
identify the exact native outputs; successful results are not assembled from
partial failed executions.

## Limits and release work

These checks use local mocks for prices, venue and VRF; the sealed-controller
tests use the real controller. No public transaction, production wallet,
target-chain outage rehearsal, website/server update or monitor restart occurred.
Unchanged broad suites and selected-pool forks were not repeated. Earlier full
regressions retain their original source scope. Exact-commit Ubuntu CI must be
checked independently of local verification.

The [operator instructions](../../docs/OPERATOR_MANUAL.md#stop-controls) explicitly
retain preparation/canonical locks, global-pause separation, full re-enable
validation and reviewed successor mint-pause state. Immediate governance remains
a trust boundary; repeated permitted maintenance losses retain the user-selected
per-operation cap only. No provider swap, reroll, pending-request carry, principal
withdrawal or new role was added.

Actual runtime manifests, authority/provider configuration, service and wallet
rehearsals, royalty-token outage isolation, migration completion where applicable,
and independent audit/remediation remain in the [central Todo](../../TODO.md).
This internal review does not certify exploit absence or production readiness.
