# Collective LP exit to NFT holders

Fresh undeployed candidate: accounting **6**, custody **5**, canonical adaptable-policy
**V6**. Production is **NOT APPROVED**. External principal and royalty custody
exits are removed. Existing deployments are not upgraded or relabelled.

## Rights and authority

Governance may irreversibly end LP activity. Holders cannot redeem principal
during normal operation. After exit starts, minting, activation, growth,
rebalancing, resume and new LP deployment cannot reopen, even after unpause.
NFTs remain transferable; activated rarity weights keep sharing future royalties
actually received. Previously earned LP rewards and royalties remain claimable.

Each NFT receives its proportional share of the **actual ETH and fixed ZZZ**
returned by its shared bucket, not an individual Uniswap position NFT or a
guaranteed historical USD amount. Ordinary same-pair moves and reversible
parking remain before exit. Production LP admission is native ETH/fixed ZZZ
only, preventing admission of a future pair incompatible with holder return.
Earned-reward conversion venues remain separate from LP admission.

| Included in principal return | Preserved separately |
| --- | --- |
| Actual LP close proceeds and attributed idle | Already earned individual and collective LP rewards |
| Compounding already deployed and pending 5% compound reserve | Royalties and future royalty receipts |
| Every allocated raw unit, without an operator remainder | Designated 5% buyback reserve, reward dust, quarantines and unsolicited prefunds |

Final closing harvests fees first and applies the unchanged 80/10/5/5 split.
Pending compound joins principal; earned rewards do not. Shares, membership
and royalty eligibility remain recorded to preserve old entitlements. Each
bucket stops earning LP fees when closed; all LP earnings end after the last
close. Paying old rewards or converting their currency is not new LP income.

## Operator procedure

1. Verify accounting6/custody5/portfolio2 runtime pins, fixed ZZZ, chain, governance and
   canonical operating state. Inventory all historical buckets and NFT ordinals.
   Stop/reconcile pending keeper work using its original journal; never reset
   or repeat an unresolved transaction. Review the permanent shutdown decision.
2. Pause ordinary operations and call
   `Migration.beginCollectiveExit(reviewHash)` as governance. It validates all
   funded buckets before setting the irreversible `Access.lpExitStarted` lock
   through the Vault's reentrancy barrier. Guardian pause alone cannot start exit.
3. Simulate/call `closeBucket(bucketId,minimumETH,minimumZZZ,deadline)` for every
   snapshotted bucket. The operation harvests/closes both actual main/residual
   positions; no auxiliary may remain. Minimums are raw **total principal** including idle and
   pending compound; deadline is at most ten minutes. No swaps or USD oracle
   reads are required. Venue checks, exact deltas and minima remain. A failed
   transaction leaves that bucket unchanged; earlier closes stay closed. Repair
   the dependency/minimum issue and review again. There is no aggregate 3% USD
   promise on this raw return. Deliberate zero minima accept zero returned value.
4. Once `remainingBuckets=0`, governance calls `allocatePrincipal(maximum)` for
   1-32 immutable mint ordinals per transaction until phase `Ready`. Dormant NFTs
   receive nothing. Cumulative share apportionment assigns every raw unit in
   deterministic order; final totals must reconcile every bucket's shares and
   outputs. Transfers do not change ordinal order or shares.
5. Governance submits `distributePrincipal(nftIds)` for 1-32 IDs per transaction.
   Each current owner is read on-chain; the caller cannot redirect funds. The
   operator can run these batches without holder action. Gas is separate.
   Each payout is isolated and gas-bounded. A low-gas batch may stop early:
   inspect `PrincipalPaid`, `PrincipalDeferred` and `principalOf(id)`, then retry
   unpaid IDs. Do not assume every submitted ID was paid.
6. If a receiver rejects payment, its complete ETH+ZZZ payout reverts and stays
   backed; other owners still receive theirs. Retry, or the actual current owner
   calls `claimPrincipal(nftId,recipient)` for a compatible recipient. ERC721
   approval grants no redirect authority. There is no operator seizure/override.
7. Reconcile all allocations, payouts, remainingETH/remainingZZZ and actual
   backing. Unsolicited prefunds stay excluded and have no sweep. Continue NFT
   ownership, future royalty receipts and existing reward/royalty claims.

Fresh custody5 restricts both allocation and direct payout batches to governance,
with authority rechecked after the batch's external calls. The governance wallet
submitting each batch pays gas; holders need no action for accepted direct payouts.
Keep `principal_distribution` disabled in the ordinary keeper. Custody5 source
rejects an enabled keeper payout job; do not load the governance key onto its server.
Historical custody4 deployments retain their original permissionless batching and
keeper configuration. Existing journals must be recovered in their own profile.

**Reward claims are separate.** Current owners may still call Rewards/RoyaltyRewards
or the fixed ClaimRouter to claim their earned balances, before or after LP exit.
Governance cannot claim another owner's rewards or redirect their principal fallback.

## Restore a reserve swap venue after exit

After `exitPhase=Ready(3)`, all LP is closed and principal allocated; owner
payouts may remain pending. Governance can validate/re-enable an ETH/fixed-ZZZ
venue with `PoolRegistry.configureNative(fullConfig)` and
`depositsEnabled=false`. Closing/Allocating and deposits-enabled terminal
configurations reject. Full runtime/PoolKey/feed/asset/parameter checks remain.

This is reserve execution policy, not new principal custody: it cannot restart
minting, activation, growth, LP maintenance or principal return to a pool.
FeeController buyback funds remain separate from Migration-held principal.
Admission neither swaps nor pays anyone. To burn reserves, select/review the
keeper buyback job's pool, preserve pending work during controlled config reload,
and unpause ordinary operations if appropriate. The existing keeper grant,
budgets, prices, execution floors and actual fixed-ZZZ burn still apply. Unpause
does not reverse `lpExitStarted`. [Exact operator steps](OPERATOR_MANUAL.md#restore-a-buyback-venue-after-collective-exit).

## Transfers, status and recovery

`exitPhase`: Operating0, Closing1, Allocating2, Ready3. Accounting6 retains
`PositionStatus.Exited=5`; historical profiles keep their original meanings.
Closed NFTs show known zero attached LP and terminal `LP exited` metadata,
while remaining activated for royalties. Principal return is separate from
claimable rewards and generated-fee history; it is not new income.

The beneficiary is ERC721 ownerOf, which can be an escrow or smart contract,
not necessarily its beneficial user. Inventory contract owners before shutdown;
accepting ETH/ZZZ does not prove a contract can later release them. There is no
operator override to infer another recipient.

Unpaid principal follows the NFT's current owner. After payment a transfer does
not create a second payout. A sale-time estimate is not a guarantee of unpaid
principal at transfer time. NFT transfer callbacks cannot bypass paid markers.

Whole-collection canonical preparation/handoff is permanently blocked after
exit starts: the replacement importer does not carry this terminal principal
ledger and must not silently reopen LP, even after everyone is paid. A future
royalty-only successor needs separately reviewed implementation/schema support.

All snapshotted buckets must close before distribution becomes Ready. Losing
governance access or an irreparably broken venue/token during Closing can block
progress, including healthy buckets awaiting global reconciliation. There is no
unsafe administrator bypass or promise of recovery from any dependency failure.

Immediate governance configuration and reviewed successor-code approval remain
separate trust boundaries before exit; removing custody-address exits does not
prove every future approved replacement honest.

Native receivers may reject ETH; ZZZ transfer faults, token behavior, venue
outages and insufficient gas can still delay closing/payment. Exact checks fail
rather than erase liabilities. There is no automatic resend, swap fallback,
operator custody address, recovery-to-pool ingress or bridge.

Use [accounting6](POSITION_V6.md), [function reference](CONTRACT_FUNCTIONS.md),
[feature evidence](IMPLEMENTATION_STATUS.md) and [sole Todo](../TODO.md).
Existing Anvil/NFTs/LP/journals, popldemo and the accounting3 poplint artifact stay
unchanged. Website payout controls, actual inventory/service acceptance,
target-chain rehearsals and independent review remain release tasks. No public
deployment, sealing, transaction or service rollout is authorized by this work.
