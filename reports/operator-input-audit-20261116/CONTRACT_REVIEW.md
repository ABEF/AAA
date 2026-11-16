# Core operator-contract source review

This is source inspection of the current operator/custody/execution/LP-reward
paths, not a fresh EVM campaign or independent security approval. No production
Solidity change was justified by a confirmed reproducible defect in this scope.
Existing source-scoped evidence remains historical; no unchanged suite, compiler,
static analyzer, live market, service or deployment was rerun for this record.

`contract-coverage.json` enumerates every exact callable ABI row of the reviewed
contracts, including reads, inherited methods, constructor and receive hooks.
The original source-bound function reference supplies exact input/output types,
nested ABI order and documented roles. Enumeration is not execution coverage.
Each row records its reviewed family, source pin and input-freshness obligations;
method-specific constraints below take precedence over family summaries.

## Findings and limits

1. **Protective stale physical reviews are intentional.** Parking, residual close
   and emergency/consolidation hashes include physical position liquidity and
   economic identity. A holder contribution before inclusion can invalidate such
   a review without stealing assets. Re-read/reprepare after the operation settles;
   do not remove physical identity checks to make a stale manifest pass.
2. **Live compound policy is partly a service policy.** `ZZZLPBalanceMath.compoundReady`
   enforces the separate interval and yields to raw rebalance/range selection, but
   does not impose the keeper's stricter below-threshold/in-range policy throughout
   the rebalance cooldown. A compromised authorized keeper can attempt a contract-
   permitted compound that the maintained service would skip. Financial/custody
   guards remain. This is an existing authority/policy limit, not proof of theft
   and not silently redesigned in this review.
3. **Spot references remain manipulable assumptions.** Two source addresses and
   declared independence IDs do not establish real economic independence. A
   same-core principal destination is excluded from captured reference use;
   an external reference can serve as execution venue only through authenticated
   exact own-transition proof. Actual independent markets/depth remain unqualified.
4. **Emergency permissions deliberately accept financial loss.** A paused current
   governance caller may omit economic bits; an unpriced request is not bounded
   by ordinary loss caps. No keeper/public caller receives this permission. Raw
   paths still require actual admitted native ETH/fixed ZZZ, custody, accounting,
   positive added/replacement liquidity, caller output floors, lifecycle and
   callback validation. They cannot repair a broken token/core or reopen exit.
5. **No universal payout guarantee.** A reverting/blacklisting ZZZ, unusable core,
   unreachable owner or permanently rejecting receiver can prevent delivery.
   Bounded automatic payout isolates failures and retains backing; actual owners
   have a separate recipient-selecting recovery path. A transfer during a payout
   cannot redefine the already-authenticated payment recipient retroactively.
6. **`maxPositionUSD` is cumulative contribution accounting.**
   `ZZZVaultCanonical.validateContribution` checks
   `Vault.contributionUSD(id) + inputUSD <= config.maxPositionUSD`; it is not a
   current marked-to-market NAV ceiling, collection cap or cap on future price
   appreciation. Contributions never recenter the main or modify residual L.
7. **Force is not an always-success guarantee.** An unchanged main may be inactive
   or unable to accept an inventory within the chosen floors. Guarded same-main
   consolidation rejects unsuitable placement. Full replacement/parking/terminal
   return are distinct tools, not automatic unsafe fallbacks.

## Call chain and inclusion-time input rules

| Exact action | Inputs and authoritative source | State changes and actual execution behavior |
| --- | --- | --- |
| `Access.bind`, `bindProtocolPolicy`, `seal` | Reviewed controller/module addresses, exact runtime and controller getter; immutable constructor graph | Bootstrap only; one-time binding. Seal requires fixed token identities, mint recipient and canonical-chain randomness. It does not prove market/provider/host qualification. No old deployment adoption. |
| `Access.proposeGovernance`, `acceptGovernance`, `setKeeper`, `setGuardian` | Explicit reviewed wallet address, current governance/pending/bootstrap/role reads | Separate roles; governance is not automatically keeper. Pending acceptance prevents typo transfer. Preparation/canonical rules must be inspected before rotation. |
| `Access.setPaused` | Boolean; current authority, pause and lifecycle reads | Guardian can pause only; governance unpauses. Pause does not stop Uniswap trading and cannot undo terminal exit or canonical locks. |
| `ProtocolPolicy` setters | Typed reviewed future values, domain-specific current tuple/revision/fingerprint | Bounds and scoped revisions; cosmetics/gas/sale differ from LP controls. Entry/maintenance hashes change only their terms, and gas fingerprint changes captured execution controls. No custody recipient or arbitrary executor. |
| `Oracle.setDualFeed`, `setSequencerFeed`, `setExecutionSource` | Exact source addresses/runtimes, complete source policy, round/decimals/age and genuine independence review | Enabling validates live observations; replacing a broken old source does not require that old source. Source disable avoids source dependency. New source IDs/revisions prevent A-to-B-to-A context reuse. |
| `Assets.configureZZZ`, `setAsset` | Fixed ZZZ runtime and exact decimals; native ETH uses the explicit native identity pin | ZZZ binds once pre-seal. Disable does not call token/feed; re-enable validates current code/decimals/prices. Token ticker is never identity; no third contribution asset. |
| `Registry.configureNative` | Full PoolConfig/PoolKey, initialized pool ID, native deployment pins, USD feeds and current limits | Same exact ETH/ZZZ pair, static hookless fee and valid spacing. One contribution destination; admitted historical custody stays. Re-enable requires full validation; source disabled by operator is not silently re-enabled. |
| `Registry.disablePool` | Existing bytes32 ID and disable-deposits/disable-operations booleans | True means disable; false leaves current flag, not enable. No price/token/core read. Deposit disable clears selected contribution destination. |
| `Portfolio.setMode`, `configureResidualSide`, `configureMainAllocation`, `configureResidualGap`, `setTriggerBps` | Current pool, current policy/revision, reviewed width/spacing/BPS choice | Setters change desired policy, not immediate physical custody. Enabled geometry changes become pending. Main floor 6000..9999BPS; residual half-side default 5000BPS; gap positive full spacings; actual representability may reject later. |
| `Strategy.setRangeOrientation`, `setKeeperRangePolicy`, `applyKeeperRange` | Pool ID, explicit orientation, current/reference prices and actual rule inputs | Human-price orientation1 inverts raw pool ratio. Optional keeper-range policy and required same-side reference confirmation cannot be enabled together. Keeper width application uses deterministic admitted policy, not arbitrary supplied width. |
| `Confirmation.configure`, `setRequireReferenceExit` | Reviewed duration/gap/require-reference setting; actual operating inclusion delays | Duration60..7days; gap may be0 to stop, otherwise <=duration/2. Every reconfiguration invalidates samples. Reference-required and active adaptive range policies are incompatible by design. |
| `Confirmation.observe`, `resetObservation` | Logical bucket ID; current onchain source/control/position identity | Only keeper writes observations. Side, identity, gap, fault, manual exception and missing configuration determine record/reset. Ordinary pause blocks observe but reset remains separate. Samples are not uninterrupted history. |
| `Vault.rebalance` | Actual logical bucket, positive raw minimum NEW main L, inclusion deadline | Keeper-only; normal eligibility/confirmation/financial checks. Closes both old legs and opens new active main, optional single residual. All assets/shares at inclusion are included; no stale offchain token amounts supplied. Post-callback keeper/pause recheck remains. |
| `Migration.moveFunds`, `resume` | Logical bucket, admitted destination bytes32 pool, positive minimum new main L, deadline | Governance-only normal guards. These ABIs do not freeze an offchain custody hash: inclusion-time bucket backing is used. Move closes both; resume begins Parked. Must explicitly manage contribution cutover separately. |
| `Migration.park` | Exact ParkingRequest with bucket, pool, main, total shares, depositUSD, epoch, nonce, tokens, raw floors, deadline, reviewHash, physical portfolioHash | Paused drain-governance path can run during preparation; canonical/terminal rules remain. Native/core close, no swap/USD dependency. Growth/earlier custody changes stale the snapshot; external swaps alone do not move bounds/L. Both legs become attributed idle. |
| `Migration.closeResidual` | Same complete ParkingRequest; positive or explicitly zero raw residual-only receipt floors | Paused governance; harvest both, burn registered residual only. Main ID/ticks/L/clock/shares remain; idle increases by actual proceeds. Shared nonce/epoch advance. Desired residual mode is unchanged. |
| `Migration.consolidateResidual(request,false)` | Current `consolidationCustodyHash`, exact existing main ticks, checks14, zero explicit swap fields, positive ADDED main L, fresh deadline/review | Same main ID/range/centre/lastRebalance; closes residual and reinvests attributed idle automatically. No designated FeeController compound release. Main must be suitable. Completion atomically disables desired residual mode and advances control/nonce/epoch/compound state. |
| `Migration.consolidateResidual(request,true)` | Same operation-specific hash/ticks but explicit reviewed mask, swap venue/direction/raw input/output or coherent no-swap | Still same-main; accepts explicitly omitted financial constraints, never recentering. Does not need a second later call to LP. Positive added L/identity/backing remain. Pause remains. |
| `Migration.emergencyRebalance` | Current `emergencyCustodyHash`, reviewed replacement ticks, legal mask, exact optional swap fields, minimum NEW main L/deadline/review | Current paused governance; full replacement from Active/Parked, never a keeper fallback. A current pool may be reused; no unreviewed pair. It does not disable future residual policy itself. No additional user action for its redeployment. |
| `Budget.setLossLimits`, `setCompoundInterval` | Loss BPS0..1000; interval600..604800seconds for admitted pool | Governance, no in-flight snapshot; financial caps capture at operation start. Interval and lastCompound remain distinct from lastRebalance. Zero loss is exact protection, not disabled protection. |
| `Vault.collectFees` | Logical bucket and inclusion-time deadline | Public live active-bucket operation; harvests both legs. No swap, no L/range replacement, no compound or buyback. External public timing must not be described as keeper-exclusive. |
| `Compounder.compound` | Keeper, logical bucket, positive ADDED main L, deadline | Independent compound interval; harvest and release bucket compound, balance/increase existing main. Existing idle participates; designated fees/claims never pass through keeper. Changes during callback fail authority/policy/accounting checks. |
| `Buyback.setMaximumTradeUSD`, `setOperatingTradeUSD`, `execute` | USD18 max/operating bound; input ETH/fixedZZZ reserve amount, pool and deadline | Zero operating limit stops without feeds. Execute budgets at upper input USD bound, acquires fixed ZZZ if input ETH and verifies actual supply/balance reduction. Direct ZZZ burn also currently needs valid USD pricing for trade budget. |
| `Rewards.addAsset`, `bindConverter` | Same fixed deployment ZZZ and fixed-ledger converter identities | One-time pre-seal pair book/converter setup. No post-seal third LP currency, arbitrary recipient or replaceable converter. Source/route policy remains governed separately. |
| `Converter.configureWrapper`, `addRoute`, `addV4Route`, `setRouteEnabled`, `setEnabled`, `setConversionLossBps` | Complete exact route/dependency/runtime/review tuple, explicit native output pin; optional wrapper requires18decimals | Native-v4 and optional historical v3/wrapper paths are distinct. Global/route disable avoids dependencies; enabling checks current dependency. No arbitrary recipient, principal input or royalty conversion. Ceiling1000BPS; caller floors remain stronger. |
| `Rewards.convertBatch` | Keeper; sorted unique exact NFT IDs<=32, fixed ZZZ, reviewed route, minimumETH and deadline | Take actual per-NFT individual/collective rights at inclusion, convert aggregate exact input, assign every output unit cumulatively back to same NFTs. Transfer does not lose credits; no beneficiary list chosen by keeper. Conversion is not new earnings. Batchcount is not gas approval. |
| `Migration.beginCollectiveExit` | Nonzero reviewed irreversible decision; paused governance; all funded buckets and minted count read live | Terminal lock barriers reject callback entry; snapshot every funded bucket. No external custody address/swap/USD requirement. Empty zero-principal collection does not enter settlement. |
| `Migration.closeBucket` | Snapshotted bucket, raw total principal ETH/ZZZ floors, deadline | Governance closes actual positions/idle/designated compound; before/after exact deltas exclude prefunds. Existing earned rewards and buyback reserves stay separate. Last bucket advances to allocation only if no residual remains. |
| `Migration.allocatePrincipal` | Count1..32; read current phase/cursor rather than supply offchain start | Governance progresses at inclusion-time cursor, immutable mint order and cumulative share floors. Dormant zero-share NFTs skipped with explicit consistency checks. Totals must equal every bucket exactly before Ready. |
| `Migration.distributePrincipal` | Explicit NFT ID array1..32; current unpaid ledger and configured payout gas | Governance pushes CURRENT owner per isolated inner call. Return is success count, not paid prefix. Duplicate/already-paid/zero cases skip; gas boundary can stop early. Query events/current state before next batch. |
| `Migration.claimPrincipal` | Actual current NFT owner and explicit recovery recipient | Holder-only exceptional recovery; not governance's automatic distribution and not an ERC721 approval permission. Fixed entitlement follows transfer; paid set before external transfer and all failure rolls back. |

## Emergency retained-check matrix

| Bit | Retains | Interaction |
| --- | --- | --- |
|1|Raw trigger/cooldown|Independent of bit16; Active candidate required, so Parked request cannot retain it.|
|2|Independent live prices/spot checks|Priced capture uses exact own-transition proof and fresh source controls.|
|4|USD loss, execution quality and idle protection|Needs USD even if bit2 omitted; positive caller output/L floors always bind.|
|8|Operations-enabled flags|Asset/core/position identity checks remain even when omitted.|
|16|Still-valid sampled confirmation|Independent of bit1; paused evidence can expire; Parked cannot retain it.|

`checks`0..31 is the legal five-bit domain. Zero/8-only has no price scope;
checking any of2/4 captures reviewed source bounds before mutable execution.
`minimumOut`/amountIn<=int128.max avoids signed core-delta overflow.
Mask14 is exactly2+4+8; it does not mean bypass14checks.

## Input/state observations checked against implementation

- Existing main/residual `lower`/`upper` bounds remain unchanged by ordinary
  external swaps. `slot0.sqrtPriceX96`, tick, inventory and fees do change.
- Full PoPL ID, mint ordinal, logical bucket, physical LP NFT ID and PoolID are
  different domains. `collectFees`/rebalance arguments are bucket IDs.
- `minimumLiquidity` is raw `uint128` L: added L for compound/consolidation,
  newly minted main L for replacement; never USD or sum of L across ranges.
- Native ETH is address0 with18decimals. ZZZ raw units use the admitted actual
  decimals; Registry fixed runtime/pair checks are distinct from token tickers.
- USD is18decimals; range/threshold/loss use BPS10000; Uniswap LP/protocol fees
  use pips1000000 and directional combined fee. Native pin is not runtime hash.
- Deadlines are Unixseconds and must satisfy now<=deadline<=now+600 at inclusion.
  Review-artifact expiry is not universally encoded in every contract ABI.
- reviewHash is reviewed evidence attribution; custodyHash/portfolioHash/policy
  fingerprints are typed state commitments, never interchangeable permissions.
- Solidity static reads cannot mutate state; token/periphery/native callbacks
  are actual mutable boundaries. External transaction ordering occurs before/
  after one atomic call, not between its close/swap/mint instructions.
- Same-core quote-state authentication includes tick/fees/L; minting a nonreference
  destination can deliberately change L afterward under exact scoped rules.
- No test result is inferred merely from generated inventory or source review.

## Economic/adversarial conclusions requiring qualification

An outsider may trade before/after maintenance; no code hash, random timer,
source agreement or per-operation floor proves MEV immunity. Current bounds
constrain execution, not future inventory price or cumulative turnover. A
profitable attack needs net profit after swap/protocol fees, gas, borrowing and
unwind; LP mark-to-market loss alone does not establish extraction.

The equal collective10% share deliberately rewards each activated NFT rather
than each dollar. More activated NFTs can obtain more collective eligibility
subject to minimum funding/mint costs; changing that is economic redesign.
Public harvesting and donation timing allocate only actually received funds;
sub20raw-unit dust is explicitly credited to incumbent individual LP rights at
entry/cutoff barriers rather than an administrator sweep.

Cold/max-state gas, genuine price independence/depth, target-market behavior,
actual operator/contract-wallet envelopes, OpenSea/provider reliability and
independent security approval remain open. This review does not qualify them.
