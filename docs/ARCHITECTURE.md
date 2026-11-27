# Shared permanent-liquidity architecture

**Undeployed candidate; production NOT APPROVED.** The current source uses native
ETH accounting7 / LP-allocation1, direct governance V2 and the same-chain canonical V10
schema. This fresh-deployment ABI/storage change does not upgrade existing Anvil
contracts or reinterpret their historical profiles. See [profile boundaries](POSITION_V7.md)
and [current feature/evidence boundaries](IMPLEMENTATION_STATUS.md). Earlier
[pruning review](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/architecture-pruning-20261025/REVIEW.md) remains historical.

Governance may configure contribution, conversion and maintenance loss limits
within hard 10% ceilings; defaults are 3%/1%/3%, gas separate. Captured operation
policy, stronger caller/venue minima and
backing remain. [Exact controls](EXECUTION_LOSS_POLICY.md), [typed routes](TYPED_V4_ROUTES.md).


The collection uses one shared contribution pool at a time, not one pool per NFT. Final production-pool selection is deferred; the [existing hookless native ETH/ZZZ integration target](POOL_SELECTION.md) retains its dated evidence. Historical buckets and supported future venue moves retain their original accounting identities. `ZZZVault.MAX_BUCKETS = 4` limits all historical bucket registrations, including imports; returning an existing bucket or migrating it to another reviewed pool does not allocate a new bucket. This bounds incumbent-dust settlement without changing reward accounting or the 1,000 NFT cap. Actual Entry, venue, token and maximal target-chain gas still require qualification.

Pool reservations now permanently admit a bucket into the same four-slot set.
Aliases and returns reuse their slot; reserved None-state entries have no
principal or shares and are skipped by maintenance. Admission does not qualify market depth, conversion routes or service operation. See [evolution and trust boundaries](ARCHITECTURE_EVOLUTION.md)
and its [source-scoped evidence](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/architecture-evolution/VERIFICATION.md). Current selected-pool changes have separate [verification](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/hookless-pool/VERIFICATION.md).

Current undeployed candidate:1,000 NFTs; exact600/300/100 random rarities; free TEAM and governed-price AL/public dormant mints(default0.05ETH gross, gas separate); $100 original gross source activation with the captured contribution floor (97% at default 3%) and gas separate; 80/10/5/5 LP allocation; equal activated collective membership; separate 5% marketplace royalties. See the [feature and evidence reference](IMPLEMENTATION_STATUS.md).

Paused governance [same-main consolidation](OPERATOR_MANUAL.md#same-main-residual-consolidation)
closes only the residual, reinvests attributed idle and applies modeOFF without
changing main ID/ticks/shares/centre/rebalance clock. New residual-reinvest1
participants and inventory17 require matching runtime review; old14 stays explicit.

The internal [exact-unit LP engine](EXACT_LP_ALLOCATION.md) is connected to Rewards, post-write Vault/Membership hooks, whole claims/conversion and canonicalV10. Its immutable constructor-created [RewardsCanonical](../src/ZZZRewardsCanonical.sol) handles typed capture/import/backing outside the near-limit parent. No generic executor, arbitrary recipient or delegatecall is added. Earlier6/V8 runtimes and journals retain their original interpretation.

## Shared implementation boundaries

Fresh maintenance3/confirmation3 distinguishes the 85%-of-centre-to-boundary
price condition from execution readiness. Actual rounded main bounds are
interpreted in ZZZ-in-ETH price; physical and independent reference must confirm
the same side. The selected 600-second sampled window may accumulate during the
hard initial twelve-hour cooldown. The source checks every 240 seconds with a
reviewed maximum 300-second confirmed gap; gap 0 stops ordinary sampled readiness.
Both conditions precede a durable 60–300-second keeper delay. A return inside,
side/policy/portfolio change or stale evidence resets the candidate. These are
sampled observations, not uninterrupted price proof or MEV immunity.

The fresh graph uses fixed companions to satisfy normal runtime/initcode limits:

| Component | Responsibility and boundary |
| --- | --- |
| NFT + predeployed Metadata + fixed SeaDropMint | Three-argument NFT constructor binds the renderer; the helper is bound once before seal/any mint. It tracks original-recipient/phase quotas and authenticates zero-ETH SeaDrop callbacks, without sale proceeds or LP custody. |
| Strategy + standalone PortfolioPolicy | Reviewed manual ranges, 85% price geometry, desired single/two-leg mode and revisions. No funds or trading authority. |
| Standalone Confirmation | Bounded samples and readiness; the sealed controller fixes its sole Strategy parent. |
| Vault + standalone MigrationBudget | Principal/share accounting, exact backing and captured contribution/maintenance/utilization floors. |
| Manager + fixed PositionExecutor | Typed balancing coordination and at most two physical LPs. Executor alone performs the fixed PosM mint/increase/collect/burn actions; Vault owns both NFTs and grants exact per-NFT approval. |
| Standalone Balancer + fixed BalanceMath | Up to four reviewed actual-core quote venues, bounded sizing and stateless arithmetic; no generic action/recipient or permanent custody. |

Optional mode starts disabled. Default residual geometry is half of the
corresponding new main side (`5000`); governance may review a fraction from 1 to 10000. A 50–150
main around 100 therefore places a residual toward 75–100 or 100–125, with at least
one full tick-spacing gap from spot. Full-side geometry remains configurable.
At an eligible whole replacement, harvest/close both, combine attributed
principal/idle/released compound, use zero or one bounded swap only as needed,
then mint the main and at most one residual atomically. At actual post-cost
captured USD marks, main must hold at least 60% and residual at most 40%; this is
not a forced 40% allocation or a continuous active-capital guarantee. The residual
may mix/fill/unfill until the next complete cycle. Disabling records a desired
single state; both remain accounted until a guarded atomic merge succeeds.

Budget retains original source controls through a same-pair move; Manager binds
the destination independently. All normal oracle, exact settlement, retained
value, idle, caller and venue guards remain. A separate paused governance-only
[manual emergency](EMERGENCY_REBALANCE.md) capability2 may deliberately bypass
selected financial/timing checks. It cannot become a keeper fallback or arbitrary
custody call and can cause near-total economic loss. Economic/gas/provider and
actual operating qualification remain open.

The converter base retains an internal
read-only [v3 venue validator](../src/libraries/ZZZV3VenueValidation.sol), while
retaining per-ledger admission and runtime-pin checks. The two concrete reward
converters inherit [one neutral implementation](../src/base/ZZZRewardConverter.sol)
but retain separate immutable ledgers, storage and balances. No external linked library, shared funds or generic executor is introduced.
The fixed LP PositionExecutor above has only typed Manager-controlled actions.

Private NFT and bucket identifiers and handoff phase/domain constants are now
explicit; wire phase values and financial ordering are unchanged. See the
[refactor comparison](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/auditability-refactor-20261025/VERIFICATION.md).

## Identity and custody

Only the canonical chain issues NFTs. On fresh Mint2, pinned SeaDrop validates the free-team or paid AL/public transaction, then calls the NFT with zero ETH. The NFT records canonical hashed IDs, requests one original two-word verifiable result per NFT and safely mints dormant ERC-721s with no LP or rewards. SeaDrop then pays the actual platform fee and creator net; any mint/payment/request failure rolls the transaction back atomically. Actual OpenSea custom-drop onboarding and fee/payer/provider operation remain unqualified. The NFT enforces the 1,000 cap and excludes royalty/mint-receiver collisions. Before canonical sealing, the randomness configuration must exist; actual provider availability remains a deployment gate.

Each approved pool has one bucket, one physical main LP NFT and at most one
associated residual in the same pool. Many collection NFTs share this bounded
portfolio; there are not two physical positions per holder. Bucket identity derives from the original chain/Vault/initial pool; each economic NFT has its own canonical identity, bucket association and nonredeemable shares. These stable identifiers do not require copied remote custody fields. `group(bucketId)` now returns eight local fields: poolId, lpTokenId, idle0, idle1, depositUSD, centerX96, lastRebalance and status. Local statuses are `None=0`, `Active=1`, `Outbound=2`, `Dormant=3`, `Parked=4`, `Exited=5`; `Outbound=2` is reserved. Pool keys supply actual currencies; bound modules, snapshots and exact backing supply authorization. `nftBucket`, `sharesOf`, `contributionUSD` expose rights/history. `amounts(actualId)` is physical, while `portfolioAmounts(main)` aggregates both.
Stable portfolio fingerprints bind actual IDs/full keys/ticks and exclude mutable
liquidity; execution fingerprints add current liquidity. Never add raw liquidity
units from different ranges or sum shared principal once per holder. Contribution USD is not current NAV or a reward weight.

Native ETH and the deployment's fixed ZZZ are the only contribution inputs.
Production admission accepts only initialized pinned static hookless native
ETH/fixedZZZ pools, including reviewed fee-tier replacements. Generic ERC20/WETH
LP admission is removed so all funded buckets remain returnable as ETH+ZZZ.
Separate conversion venues do not become principal pools or new user inputs.
Stablecoins may be admitted separately as marketplace royalty currencies.

`poolBucket` permanently reserves venues for their buckets. Governance reviews destination capacity before a supported same-pair move. Distinct buckets do not merge. NFT transfers change the current claimant without changing shares, membership, rarity or accrued balances. Operators cannot claim as owners. Holders cannot redeem principal during normal operation; governance can trigger collective holder return.

## Entry and membership

Activation defaults to at least100USD original ETH/fixed-ZZZ source value (future-governed policy minima), with the captured contribution floor(default3%,at least97%) actually deployed as marginal oracle-valued MAIN LP. Registry-created direct [Entry3](ACTIVATION_ENTRY.md) forwards the exact pair input to the fixed Vault; no pre-Vault route/conversion child exists. Vault performs reviewed ratio balancing and LP placement within the one captured source budget. Owner/context, dual-price/policy, exact allowance/balance and actual marginal LP checks remain. Growth defaults5USD under the same rules and stronger pool minima; current governed idle limits remain independent. Only the LP reward converter retains reviewed v3/v4 routes; royalties are claimed in their original currency. Actual input/venue/token/feed/gas qualification remains open.

Before share/membership changes, the Vault settles already-funded local dust
and harvests both current bucket legs. Entrant-only swaps/deployment increase the
existing main; incumbent residual, idle and compound remain in its aggregate NAV.
Contributions do not recenter the portfolio or reset its rebalance clock. Sub-twenty-unit dust settles to existing owner shares. Vault entry-balancing swaps are followed by settlement so their fees belong to incumbents; old LP is revalued after balancing. Fresh 5% compounding belongs to incumbent NAV. Final LP updates, actual marginal deployed-LP and dust guards precede owner checkpoint and share issuance.

First shares equal measured net principal USD; later shares round down as `supply * netNewUSD / (incumbentNAV + historicalCompoundValue)`. Historical non-current compounding stays incumbent backing and cannot subsidize the new contribution's captured deployed-LP floor. Zero-NAV/zero-share/cap violations revert. Donations, unclaimed rewards and buyback reserves do not buy shares. After successful issuance the Vault activates one `ZZZMembership` share for an initially dormant NFT and notifies the fixed NFT, which joins its separate rarity royalty ledger. Optional royalty-currency faults defer that currency's eligibility without undoing otherwise valid activation; the earlier cohort is protected. Other failed contribution checks roll back atomically. A top-up never adds collective/royalty weight.

**Reviewed signing boundary:** Entry/Pricing bind the caller maximum; a higher governed cap cannot silently widen a signed review. Actual source/route/feed and wallet qualification remain release gates.

## Funded LP rewards

Twenty raw units split16owner/2collective/1compound/1buyback. Individual whole-unit books are bucket/asset-specific and use nonredeemable shares. The collective whole-unit book gives each activated canonical NFT one equal share. Eligibility persists through price declines, transfers and migration. Vault/Membership hooks settle existing funded rights before authenticated weight changes. No Power module or USD reward weighting remains.

Fresh accounting7 LP rewards admit exactly native ETH and the deployment's fixed ZZZ, with whole-unit liabilities and separately preserved pending/high/low fairness phases. Those phases are not money or reserved fractional claims. Same-NFT conversion preserves existing components and does not create new income. Fee-split dust and zero-participant orphan funds remain separately classified; no administrator can withdraw reward, orphan, compound or principal balances outside their constrained purpose. Claims remain available during operational pause. Historical fractional codecs remain explicit inspection profiles. Marketplace royalties have separate reviewed capacity, initially16 ERC20 currencies and expandable to64 plus ETH; that capacity is not LP-asset admission. See [exact LP allocation](EXACT_LP_ALLOCATION.md).

The selected pool's actual earned venue fees fund this allocation when harvested; Uniswap's protocol fee is not PoPL revenue. Creator-payment inboxes and remote-fee intake are removed; only the bound Vault can allocate actual local LP receipts. Unsolicited donations remain unclassified/quarantined, not new holder income.

After collective exit reaches Ready (principal allocated), governance can still
validate ETH/fixed-ZZZ swap venues with deposits disabled for remaining buyback
reserves. Closing/Allocating remain locked; all native/feed/asset checks remain.
This does not reopen principal or access Migration-held payouts. Actual burn
keeps its ordinary keeper/unpause/execution controls. [Procedure](OPERATOR_MANUAL.md#restore-a-buyback-venue-after-collective-exit).

## NFT royalties and metadata

Fresh royalty settlement4/recovery2 pays each admitted currency as received.
There is no royalty converter, swap or unwrap. Governance may allocate only
reviewed admitted unallocated units in the SAME currency at current active
rarity weights using `allocateUnallocated(asset,amount,reviewHash)`. Previously
earned/deferred ticket rights remain excluded. Unsupported currencies require
review/admission first;ERC20 capacity starts16 and can be increased up to64 plus ETH after review. Original-currency claims
need no price feed; optional USD reporting and LP reward conversion are separate.
See [current settlement](ROYALTY_SETTLEMENT.md).

VRF callbacks only store request-bound words. Permissionless reveal follows mint order, drawing without replacement to exact 600/300/100 quotas. A separate word draws a fixed artwork entry without replacement within that rarity. Eight base colors form 58 palettes, combined with four patterns: Flowing arcs, Segmented panels, Orbital rings and Twin circuit routes. Rarity, palette and pattern remain immutable; palette/pattern do not affect rewards, while rarity sets only the separate royalty weight. The 1,000-entry inventory has 200 monochrome, 500 bicolor and 300 tricolor slots, each with the 60/30/10 rarity mix; identical palette/pattern/rarity finishes occur at most four times and all 100 Legendary looks are unique. Missing earlier fulfillment blocks later reveal; no reroll/cancellation bypass exists. [NFT details](NFT_METADATA.md).

The renderer selects among 2,784 supported palette/pattern/rarity/evolution SVG states, separate from the NFT supply. It values current local LP amounts, attributed idle and compound budgets using approved oracles, multiplied by shares/supply. Enhanced starts at $1,000 and Singularity at $10,000; market losses can downgrade artwork. Parked custody or stale dependencies report unavailable, with labelled fallback art. Terminal Exited status has verified zero LP and explicit `LP exited` metadata, while royalty eligibility survives. Metadata never gates claims/migration. Reveal/contributions emit ERC-4906 notifications. Permissionless per-token and bounded ordinal-range calls notify actual hashed IDs without price reads. An optional confirmed-block watcher uses the existing keeper's serial budgeted transaction path; permanent content publication, staged watcher operation and marketplace cache integration remain production work.

## Maintenance and migration

Hourly harvest operates once per bucket, collecting both legs and applying the
unchanged 80/10/5/5 allocation without a holder loop or balancing swap. Claims do
not run compounding or buybacks. Compounding has its separate governed interval
(default one hour); ordinary keeper automation waits for an in-range main with
no pending width/mode/threshold adjustment. Harvest remains independent.

Current LP routing3/execution-price1 compares up to four reviewed ETH/ZZZ venues independently of the LP
destination, using actual-core quotes after the old portfolio is removed. Ordinary
hybrid replacement retains as much passive inventory as possible, swapping only
for its 60% main floor when needed; search is bounded, not a global optimality
promise. Actual mints and Budget recheck captured utilization/loss/idle limits.
Manual width/mode changes may apply after cooldown even while the main is inside.
Automatic preapproved two-width policy stays disabled by default and cannot
coexist with required independent-reference confirmation. Policy changes never
create a sweep or new recipient. [Execution decisions](LP_EXECUTION_POLICY.md),
[optional portfolio](OPERATOR_MANUAL.md#portfolio-management-controls). Pooling does not remove
impermanent loss, fees, adverse selection or MEV.

`Migration.moveFunds` atomically closes and deploys actual LP in another admitted pool with the same ordered accounting pair. Current native accounting preserves actual ETH identity and supports same-native-pair fee-tier changes. ETH/WETH atomic conversion is unsupported and rejected; WETH can be used only by separately reviewed conversion routes, not LP admission. One captured starting-price maintenance floor covers the complete move (3% loss by default, governed up to 10%), with gas separate; NFT shares and original bucket identity remain unchanged. Destination contributions and reviewed Vault balancing venues are switched deliberately after verifying the resulting LP; earned-conversion routes remain separate.

[Collective holder exit](HOLDER_COLLECTIVE_EXIT.md) replaces external custody
release/consolidation/recovery and royalty drains. A paused governance action
permanently blocks new mint/principal work through a Vault reentrancy barrier.
Each native ETH/fixedZZZ bucket is harvested, dust settled, pending compound
included and both LPs closed into exact classified holder backing. NFT shares and
membership remain so earned rewards and future royalties survive. Bounded
ordinal apportionment reconciles every raw unit; isolated direct payout batches
read current owners and retain failed liabilities for owner fallback.

Exited5 is distinct from Dormant3. Attached LP value becomes known zero, while
principal return is a separate ledger, never fee income. Unpause cannot reopen
LP or canonical replacement; current V10 handoff is allowed only before exit. Normal
same-pair pool moves/parking remain before exit. Production Registry no longer
admits ERC20-only LP pairs; other assets remain possible conversion venues or
royalty currencies, not principal pool currencies.

## Security domains and operational state

| Domain | Holds authority or value | Required separation |
| --- | --- | --- |
| Principal | Vault/manager custody, per-NFT nonredeemable shares, attributed idle/compound | Actual LP units and raw balances back NAV. Reward reserves, donations and prefunds cannot finance a newcomer. |
| LP liabilities | Fees classification and Rewards individual/equal-collective whole-unit books | Only actual received funds create income; compound/buyback reserves are not holder claimable. |
| Royalties | NFT-created separate receiver and rarity-weighted ledger | Only active eligibility; exact original-currency units and deferred cohorts survive transfers; no royalty conversion exists. |
| Immediate governance | Compatible policies, roles, collective shutdown and reviewed pre-exit replacement code | A compromised quorum can approve unsafe prices/settings or replacement code. Sealing and limits do not remove this accepted trust. |
| Keeper and services | Bounded upkeep, unsigned preparation, confirmed views | No owner claim privilege, governance configuration or public signing authority follows from running a service. RPC history and availability still need qualification. |
| Canonical lifecycle | Preparation/freeze/settlement/import/funding/abort/retirement | Exactly one active canonical deployment; no old-schema relabel, duplicate backing, unfunded activation or finality override. |

Ordinary pause stops ordinary contributions/maintenance, while already funded
claims remain available. Governance can irreversibly begin holder return while paused; a guardian pause
alone cannot start it. External principal/royalty custody exits are removed.
Pool deposit/operation stops, mint-only pause and keeper stop are separate controls.
See the [stop/restart matrix](OPERATOR_MANUAL.md#stop-controls).

Do not promise that liquidity always earns, preserves USD value or can always be
recovered. Range exits, repeated bounded execution loss, dependency/proxy failure,
rejecting receivers and a halted source chain are distinct risks. Two configured
addresses are not proof of independent prices. The [internal audit](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/preproduction-audit-20261025/REVIEW.md)
separates inspected code, improved composition tests, accepted trust and live gates.

## Release and trust boundaries

The current core has **17 contracts: the controller and 16 required sealed modules**, including Membership and four canonical handoff modules. Fixed companions, configured converters and executors require [inventory](DEPLOYMENT_ADDRESSES.md); creator inboxes and old bridge/receiver/routes/transport IDs are removed. Sealing fixes core bindings and verifies companion owners and the one source/exit ZZZ identity.

Governance V2 is the selected wallet calling configuration/recovery functions
directly. A Safe applies its own signatures and nonces; PoPL has no timelock,
predecessor queue, generic executor or OpenZeppelin role grants. Governance
replacement requires proposal and acceptance; a zero proposal cancels. Handover
is blocked during preparation, frozen and retired states. Keeper/guardian roles
and the current accepted mint recipient remain separate. Bootstrap authority disappears
on seal. Governance approval cannot prove replacement code or dependencies safe;
immediate governance remains an accepted trust boundary. No arbitrary custody
recipient is available in the current source.

The [same-chain canonical handoff](CANONICAL_HANDOFF.md) freezes ownership and accounting, imports exact state and classified backing, and atomically retires the source/activates one replacement. It supports exact abort restoration before retirement and late funding afterward. Current schema is `ZZZ_CANONICAL_SAME_CHAIN_EXACT_LP_SEADROP_V10`; older schemas are rejected. Exact group records are 12 words / 384 bytes, with malformed/trailing layouts rejected. Funds transfer before zero-value acknowledgment, with separate Vault, Fees, Rewards and royalty backing. It requires revealed mints, parked local custody, complete classified accounting and `lpExitStarted == false`. It remains
permanently blocked after collective LP exit begins. No integrated future-chain transport or post-halt recovery is provided. Missing immutable capabilities require a separately reviewed replacement while the source works, not a configuration edit.

Production LP admission supports initialized static hookless native ETH/fixedZZZ fee tiers on pinned Robinhood dependencies. Generic ERC20-only LP admission is removed; separate conversion venues retain their own explicit checks. The existing integration target has a static 1.002% LP fee and a dated approximately 1.101% combined swap fee; final production-pool selection is deferred; only actual earned LP fees are PoPL revenue. Actual ETH identity is preserved. Other native pairs, dynamic native fees, hooks and pairs without fixed ZZZ are rejected.

Use the [feature/evidence reference](IMPLEMENTATION_STATUS.md) for completed checks
and their exact source scopes, and the [callable reference](CONTRACT_FUNCTIONS.md)
for the current public surface. Historical test counts, bytecode sizes and old
profiles are evidence for their recorded revision, not release approval.

[Native custody](NATIVE_ETH_ARCHITECTURE.md) uses WETH only for reviewed operations
that actually need it. Earlier [native V2 evidence](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/native-eth-port/VERIFICATION.md)
predates current accounting7 and retains that source scope. Atomic ETH/WETH
conversion and old-schema import are unsupported. Actual route/provider/inventory
qualification remains open. ZZZ conversion at the default 1% needs a cheaper
qualified route; the recorded integration target does not qualify at reference prices. Actual
independent feeds, proof-verifying VRF, authority wallets, OpenSea primary mint,
native wallet/service operation, maximal gas/strategy economics, recovery
rehearsals and independent audit/remediation remain open. Production NOT APPROVED.

## Exact royalty source boundary

Royalty4/reporting5/schema17/canonicalV10 uses internal whole-unit allocation.
The allocator adds no deployed helper; Factory storage2 adds exactly two inert
code-data children outside the20 callable-helper roles. RoyaltyFactory stores only fixed
compiled creation bytes, authenticates them with immutable royaltyCodeHash,
then creates the typed caller's ledger and binds its fixed controller. No caller
supplies code, salt, recipient or execution payload. Code storage reduces
constructor gas; exact target deployment still requires qualification.
[Storage format](FACTORY_CODE_STORAGE.md), [exact rule](EXACT_ROYALTY_ALLOCATION.md).

## Component responsibilities

This source responsibility map consolidates the former component-status page.
Current assessment is in [CURRENT_REVIEW](../reports/CURRENT_REVIEW.md);
the callable and operator references retain exact inputs, outputs and permissions.

### Ownership, entry and custody

| Component | Current job | Remaining qualification |
| --- | --- | --- |
| [AccessController](../src/ZZZAccessController.sol) | Direct governance2, keeper/guardian permissions,16 sealed module bindings, two-step wallet handover and irreversible `lpExitStarted`. | Actual authorities, recovery, configuration/code trust and operating acceptance. |
| [ProtocolPolicy](../src/ZZZProtocolPolicy.sol) | Fixed bound noncustodial policy helper for scoped future terms/gas/metadata/drainedVRF controls. | Independent economic/authority/provider/gas review; runtime/config pins and rehearsal. |
| [Vault](../src/ZZZVault.sol) | Records hashed dormant identities for the authenticated zero-ETH NFT mint callback; direct paid mint cannot bypass a bound Mint2 helper. Governed minima(default$100/$5), shared LP/per-NFT shares and exact principal settlement to fixed Migration remain. New principal work ends permanently at exit. | Actual venue behavior, accounting/callback composition, maximal gas and independent review. |
| [ActivationAssets](../src/ZZZActivationAssets.sol) | One pre-seal fixed ZZZ plus native ETH, source-policy review and dependency-independent disabling. | Actual token/proxy/runtime/decimals and independent feed evidence. |
| [PoolRegistry](../src/ZZZPoolRegistry.sol) | One contribution pool, pinned static hookless native ETH/fixedZZZ LP admission and supported fee-tier replacements. Generic ERC20 LP admission is removed. After terminal Ready, validated deposits-disabled venues may be restored/admitted for buyback reserves; principal stays closed. | Actual initialized pools, venue bindings, execution depth and deposit/operation controls. |
| [ActivationEntry](../src/ZZZActivationEntry.sol) | Direct Entry3: current owner, exact pair input/fixed Vault call, captured USD/caller loss maximum, exact approvals and callback-safe context; no preliminary conversion child/routes. | Actual input/balancing funding, matching fresh browser/API profile and target-chain execution. |
| [LiquidityManager](../src/ZZZLiquidityManager.sol) | Typed v4 mint/increase/collect/close/swap, actual key/ticks/liquidity and exact native settlement; isolates prefunds. | Actual dependencies, adverse composition, strategy costs and maximal gas. |
| [LPBalancer](../src/ZZZLPBalancer.sol) | Separately deployed fixed-controller companion; LP routing3/execution-price1 compares 0–4 reviewed ETH/ZZZ venues with bounded reverted actual-core quotes; historical LP2 remains a separate profile. Its arithmetic child sizes single-main or minimum qualifying hybrid swaps; zero/one actual swap. | Actual depth, gas, source/route controls and ordering economics; exact reciprocal parent/helper/runtime pins. |
| [LPPositionExecutor](../src/ZZZLPPositionExecutor.sol), [LPBalanceMath](../src/ZZZLPBalanceMath.sol) | Fixed typed physical-operation and arithmetic children. Main/at most one residual stay Vault-owned in the same pool; no third leg, arbitrary recipient or new human role. | All-leg composition, maximal gas and exact immutable graph. |
| [ContributionPricing](../src/ZZZContributionPricing.sol) | Captures dual-source prices/policy before funds move and measures actual marginal LP. | Actual independent source policies and real routes/depth. |
| [MigrationBudget](../src/ZZZMigrationBudget.sol) | Captured ordinary contribution/maintenance floors, physical placement, idle accounting and loss checks; scoped manual emergency context with explicit retained checks. | Independent economic review and installed-venue gas/behavior; financial bypass accepts governance risk. |

Position7 retains the same eight local fields as historical6: poolId,lpTokenId,idle0,idle1,depositUSD,centerX96,
lastRebalance,status. Statuses None0/Active1/reservedOutbound2/Dormant3/Parked4/
Exited5 are explicit; old profiles keep old meanings. At most four historical/
reserved buckets are permanently admitted. Many NFTs share a bucket with one main and optionally one residual;
maintenance is per bucket, not per 1,000 NFTs. Both physical token amounts back
NAV. Contributions increase only the current main; all-leg harvest/close cannot
leave an auxiliary behind.

### Income, claims and upkeep

| Component | Current job | Remaining qualification |
| --- | --- | --- |
| [FeeController](../src/ZZZFeeController.sol) | Actual LP receipts only, fixed80/10/5/5 and separate compound/buyback/dust classification. | Currency rounding, actual collection and independent accounting review. |
| [Rewards](../src/ZZZRewards.sol) | Share-weighted individual plus equal activated collective whole-unit books and current-owner claims. | Actual recipients, complete history and worst-case currency gas. |
| [Membership](../src/ZZZMembership.sol) | One equal collective share per activated NFT, preserved through transfer/LP exit so past entitlements survive. | Bounded dust/checkpoint costs and complete handoff composition. |
| [LPRewardConverter](../src/ZZZLPRewardConverter.sol) | Converts only earned balances into the same NFTs' ETH credits, without new-income double counting. | Cheaper qualified ZZZ route at default 1%, latency, gas and operation. |
| [RoyaltyRewards](../src/ZZZRoyaltyRewards.sol) | Settlement4 original-currency royalties: GCD-normalized rarity tickets, exact whole-unit allocation, opening/outage cohorts and current-owner claims. Recovery2 allocates reviewed unallocated units without swaps; future royalties continue after LP exit. | Actual marketplace currencies/receipts, raw-unit fairness, maximum-state gas and failure/recovery behavior. |
| [ClaimRouter](../src/ZZZClaimRouter.sol) | Up to 32 mixed ledger claims, actual owner and atomic rollback. Principal return is a separate Migration payout. | Gas, frontend chunking and real receiver acceptance. |
| [Oracle](../src/ZZZOracle.sol) | Two-source USD bounds, freshness/fingerprint and 3% disagreement; reviewed sequencer policy. | Independent sources, proxies/common-mode/uptime and provider support. |
| [Optional Pyth source](../src/ZZZPythPriceFeed.sol) | Immutable bounded price/time/confidence reader, no funds/updater. | Actual Core/source/provider and updater review. |
| [Strategy](../src/ZZZStrategy.sol),[Compounder](../src/ZZZCompounder.sol) | Trigger/cooldown/range and attributed reinvestment before exit; optional reviewed +/-25/50% width policy. | Volatility, MEV, gas and real strategy operations. |
| [RebalanceConfirmation](../src/ZZZRebalanceConfirmation.sol), [PortfolioPolicy](../src/ZZZPortfolioPolicy.sol) | Fixed-controller Strategy companions; confirmation3 requires same-side physical/reference crossing of 85% of centre-to-main-boundary ZZZ-in-ETH price distance. Portfolio2 controls optional mode/geometry and monotonic review revisions. | Selected 600/300 sampled window, 240-second checks, 60–300-second service jitter and hard initial 12-hour cooldown; actual timing/gas and independent sources remain unqualified. |
| [Buyback](../src/ZZZBuyback.sol) | Spend only buyback reserve, acquire fixed ZZZ, verify actual supply burn; governed operating ceiling. | Actual conversion/burn, price policy and funded operation. |

Defaults contribution 3%/conversion 1%/maintenance 3%, maxima 10%, gas separate.
Stronger caller/venue guards remain. Raw holder principal return has no aggregate
USD-loss promise. Source currency stays source currency until actually converted.

### NFT, holder return and replacement

| Component | Current job | Remaining qualification |
| --- | --- | --- |
| [NFT](../src/ZZZNFT.sol) | ERC721/2981/4906,1,000 cap, authenticated dormant SeaDrop issuance, one original two-word VRF request per NFT, exact quota/inventory draw and immutable revealed traits/transferable ownership. | Actual VRF, custom OpenSea onboarding and operating acceptance. |
| [SeaDropMint](../src/ZZZSeaDropMint.sol) | Pre-seal-bound fixed NFT/SeaDrop policy, reviewed phase quotas and exact original-recipient lifetime books. TEAM is free; AL/public use the governed gross price(default0.05ETH). SeaDrop pays actual fee/creator net atomically; the helper holds neither proceeds nor LP. | Actual proofs, windows, wallet/batch limits, platform fee/payers, source-matching runtime/configuration and operation. |
| [NFTMetadata](../src/ZZZNFTMetadata.sol) | Predeploy with the same controller and pass to the three-argument NFT constructor. Current LP NAV selects four visual stages; unavailable data stays explicit. Exited LP has verifiedzero and terminal `LP exited` stage4 using existing artwork. | Permanent hosting, feed/cache refresh and current-profile display. |
| [Factories](../src/ZZZRoyaltyFactory.sol),[Assets factory](../src/ZZZActivationAssetsFactory.sol) | Fixed typed helper creation and parent/controller bindings; RoyaltyFactory storage2 reconstructs unchanged ledger code from2 immutable inert data children. | Schema17/mint2/reinvest1 release inventory, actual returned code/runtime/initcode and target gas. |
| [Migration](../src/ZZZMigration.sol),[parking validation](../src/ZZZCustodyValidation.sol) | Before exit, same-pair moves/reversible parking and separate paused-governance [manual emergency redeployment](EMERGENCY_REBALANCE.md). Terminal exit allocates actual ETH/ZZZ by shares with bounded current-owner payouts/fallback. | Economic bypass trusts governance and can lose almost all principal. Maximal gas, services/UI, operation and independent review remain open; no custodian/bridge/return ingress. |
| [CanonicalHandoff](../src/ZZZCanonicalHandoff.sol) | Six-domain same-chain capture/import/backing, funded abort and atomic source retirement/replacement activation, only before LP exit. | Exact V10 compatible peers, original-recipient/phase import, escrow cutover, funding/interruption/gas and independent review. |
| [NFTCanonical](../src/ZZZNFTCanonical.sol),[VaultCanonical](../src/ZZZVaultCanonical.sol),[FeesCanonical](../src/ZZZFeesCanonical.sol),[RewardsCanonical](../src/ZZZRewardsCanonical.sol) | Sealed typed codecs for ownership, shares, exact LP pending/phase/direct books and classified backing. The principal V6-format group rows and exact LP V9-format rows are retained within V10; NFT rows additionally preserve original mint recipients/phases independently of current owners. | Actual source/successor manifest and complete operated rehearsal. |

Rarity affects royalties only; color/pattern affect neither ledger. Exited NFTs
retain transfers, earned rewards and future royalty rights; unpaid principal
follows current ownership until permanently marked paid. Current V10 canonical
replacement cannot run after exit starts because its importer does not carry
terminal payout accounting. No integrated bridge, remote ledger or post-halt
recovery is provided. [Exit details](HOLDER_COLLECTIVE_EXIT.md).

### Services and evidence

The [typed operator preparers](MANUAL_LP_PREPARATION.md) authenticate current
governance and custody, fetch request hashes, and simulate exact unsigned manual
management and collective-return steps. They are not an executor or keeper;
batch gas/output limits and operator receipt reconciliation remain explicit.
[Source-scoped verification](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/operator-management-20261109/VERIFICATION.md).


Keeper scheduling, simulation, nonce/receipt recovery and monitoring are off-chain;
contracts enforce principal rules. Indexer/API use confirmed state, explicit
profiles and complete pinned history. Missing pricing/history stays unavailable.
Earnings alone may use reviewed [checkpoint3](EARNINGS_CHECKPOINTS.md) for an
authenticated accounting7 lineage: one exact epoch cursor plus raw later events,
with the full rolling day retained. A separate offline importer can extend a
reviewed compatible exact2/shorter3 prefix into a matching graph without changing
the semantic readers/builder. The separate [history recovery tool](HISTORY_RECOVERY.md) snapshots all retained raw rows and exact checkpoint/review bytes, verifies integrity and restores new files only. Other readers remain raw; actual archive retention and maximum-workload/host operation remain open.
Fresh V10 backend reads/owned claims explicitly select mint_integration_version2
on accounting7 with fixed SeaDrop/helper pins. Omitted/default1 stays V9;
source9 website configuration, served accounting3 poplint and old local
deployments are not relabelled or upgraded. Public deployment stays
null, browser signing Anvil-only, popldemo unchanged.

Actual feeds/routes/VRF/authorities, OpenSea, artwork hosting, accounting7 wallet/
service acceptance, target gas/strategy/operations and independent audit remain
open. Earlier [reports](../reports/CURRENT_REVIEW.md#evidence-and-history) do not verify later source changes.
Maintain the [callable reference](CONTRACT_FUNCTIONS.md) for ABI/permission changes.
