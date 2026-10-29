# Configuration changes and recovery boundaries

The undeployed candidate uses [accounting4 / custody3 / canonical V5](POSITION_V4.md).
Sealing fixes code, bindings and the single ZZZ identity. Governance changes
supported policy directly, without a timelock; it cannot rewrite NFT rights or
send principal/royalties to a custodian. Production is **NOT APPROVED**.

## What can change

| Need | Current supported action and limit |
| --- | --- |
| Rotate governance | Current wallet calls `Access.proposeGovernance`, proposed wallet calls `acceptGovernance`. No delay; zero proposal cancels. Keepers, guardians and mint recipient do not rotate with it. |
| Stop minting only | Governance `NFT.setMintPaused(true)`; existing transfers, LP and claims continue. It does not cancel an already requested reveal. |
| Stop ordinary economic activity | Governance/guardian pauses; only governance unpauses. Claims and transfers remain while canonical state is operating. Pause does not undo terminal LP exit. |
| Enable/disable ETH or fixed ZZZ contributions | Source-policy controls in `PoolRegistry.activationAssets()`. Identity is configured once before seal; no third input or replacement ZZZ setter. Source disable does not revoke earned rights. |
| Disable an admitted pool during an outage | `PoolRegistry.disablePool(poolId,stopDeposits,stopOperations)` only clears flags without token, oracle or venue reads. Re-enabling before terminal exit requires full `configureNative` validation. |
| Change contribution pool or fee tier | Admit an initialized, pinned, static hookless native ETH/fixedZZZ destination using `configureNative`. Only one contribution pool can be enabled. LP movement and contribution/route cutover are separate reviewed steps. |
| Move the existing LP | Before collective exit, `Migration.moveFunds(bucket,pool,minimumLiquidity,deadline)` atomically closes/redeploys the same actual ETH/ZZZ pair under the captured maintenance budget. Shares and bucket identity remain. No WETH/other-pair destination or external recipient. |
| Change standalone compound cadence | Budget3 `setCompoundInterval(poolId,seconds)`,600seconds-7days/default3600; no clock/backing rewrite. Service scheduling may add delay; JSON changes need controlled restart. |
| Change sampled rebalance confirmation | Fixed Strategy helper `configure(seconds,gap,reviewHash)`; duration60seconds-7days, gap0(stopped) or at most half duration. Selected900/300; every greater gap restarts with no grace. Reconfiguration invalidates samples, not hard cooldown or manual-width exception. [Procedure](OPERATOR_MANUAL.md#configure-rebalance-confirmation). |
| Change range/trigger/cooldown | Governance updates supported pool parameters/orientation; policy2 applies actual ticks after cooldown on physical range exit or explicit desired-range change. The movement field does not trigger policy2 upkeep. Optional reviewed keeper policy selects only +/-25% or +/-50% ZZZ-price-in-ETH widths. See [range procedure](OPERATOR_MANUAL.md#range-and-strategy). |
| Change execution-loss limits | Budget contribution/maintenance and separate converters are bounded at 10%; defaults2%/3% and1%. Captured policy, stronger caller/venue minima and gas separation remain. [Exact procedure](EXECUTION_LOSS_POLICY.md). |
| Rotate a conversion route | Admit/enable a reviewed pinned typed route; a conversion venue is not an LP contribution pool or a new input identity. Already-earned entitlements remain with the same NFTs. |
| Replace USD feeds or sequencer feed | Review new sources, independence/runtime/proxy controls, ages and disagreement. `Oracle.setDualFeed` requires both sources; selected disagreement tolerance3%. Sequencer replacement cannot disable an installed safeguard by setting zero. No peg/spot/missing-source fallback. |
| Tune randomness requests | Future confirmation/callback settings only; provider/lane/subscription/payment mode are fixed. Original pending requests cannot be rerolled. |
| Tune buyback amount | `Buyback.setOperatingTradeUSD` ranges from zero through immutable `maxTradeUSD`; zero stops buys. Target ZZZ is immutable, and reserves cannot be sent to governance. |
| Rotate service host/RPC | Preserve original deployment identity, versioned configuration, pending intents, nonce and receipt journals. A config edit does not upgrade deployed code. [Recovery](KEEPER_RECOVERY.md). |

### Manual paused recovery

Fresh confirmation2 adds reviewed same-side independent-reference corroboration;
governance may change it through `setRequireReferenceExit`, invalidating samples.
Automatic keeper width policies cannot coexist with enabled protection.

Fresh emergency capability1 separately permits paused governance to call
`Migration.emergencyRebalance(request)`, including from Parked custody, with
explicit optional economic safeguards. No keeper/holder/automatic fallback may
use it. This retains Vault custody and NFT shares/rewards but trusts governance
with potentially near-total trading loss when financial checks are off.
No arbitrary recipient/call or terminal reopening is added.
[Exact controls and recovery](EMERGENCY_REBALANCE.md).

## Pause, park, resume or permanently exit

**Parking is reversible; collective holder exit is irreversible.** Before exit,
paused governance can use `Migration.park` with exact LP/share/epoch/nonce and raw
close minima. It harvests and closes into attributed Vault idle without USD
oracle reads. Old idle, donations and pending compound cannot satisfy parking's
close-only minima. Actual venue/token/runtime checks still apply. Resume uses an
admitted same-pair destination and fresh guarded deployment, retaining the
captured maintenance budget.

For permanent shutdown, paused governance calls
`Migration.beginCollectiveExit(reviewHash)`. Each bucket closes without swaps,
then exact principal is apportioned by NFT shares and paid in bounded direct
batches to current owners. Pending compound joins principal; earned LP rewards,
royalties and buyback reserve stay separate. Failed recipients retain backed
rights and an owner-only fallback. [Complete operator steps](HOLDER_COLLECTIVE_EXIT.md).
Unpause cannot reopen minting, contributions, maintenance or canonical replacement.

No `exit` to a chosen address, all-ZZZ consolidation, `completeLocal`, `recover`,
royalty-custody drain, bridge or generic sweep remains. A token issuer migration
cannot be executed on holders' behalf by a custody wallet: holders receive the
actual old ETH/ZZZ and handle any issuer exchange themselves. New ZZZ or another
chain requires a fresh reviewed project; no existing rights move automatically.

## Whole-collection replacement

Before `lpExitStarted`, compatible [same-chain canonical V5 handoff](CANONICAL_HANDOFF.md)
can carry NFT ownership, shares, both ledgers and exact backing to one reviewed
replacement. It requires complete reveals, parked buckets, authenticated records,
funded legs and atomic retirement/activation; partial failure requires exact
abort restoration. Governance's choice of successor code remains trusted.

After collective exit starts, that handoff is permanently blocked because its
importer does not carry the terminal principal-payout ledger. No admin-only
reopening, post-halt recovery or cross-chain transport exists.

Actual feeds/routes/VRF/authorities, OpenSea, accounting4 services/UI, target gas,
operating rehearsals and independent review remain [open](../TODO.md). Historical
reports and deployed Anvil profiles keep their original scope and code.
