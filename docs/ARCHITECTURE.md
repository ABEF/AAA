# Shared permanent-liquidity architecture

**Undeployed candidate; production NOT APPROVED.** The current source uses native
ETH accounting V6, direct governance V2 and the LP-only same-chain canonical V6
schema. This fresh-deployment ABI/storage change does not upgrade existing Anvil
contracts or reinterpret their historical profiles. See [profile boundaries](POSITION_V6.md)
and [current feature/evidence boundaries](IMPLEMENTATION_STATUS.md). Earlier
[pruning review](../reports/architecture-pruning-20261025/REVIEW.md) remains historical.

Governance may configure contribution, conversion and maintenance loss limits
within hard 10% ceilings; defaults are 2%/1%/3%, gas separate. Captured operation
policy, stronger caller/venue minima and
backing remain. [Exact controls](EXECUTION_LOSS_POLICY.md), [typed routes](TYPED_V4_ROUTES.md).


The collection uses one shared contribution pool at a time, initially the [selected hookless native ETH/ZZZ pool](POOL_SELECTION.md), not one pool per NFT. Historical buckets and supported future venue moves retain their original accounting identities. `ZZZVault.MAX_BUCKETS = 4` limits all historical bucket registrations, including imports; returning an existing bucket or migrating it to another reviewed pool does not allocate a new bucket. This bounds incumbent-dust settlement without changing reward accounting or the 1,000 NFT cap. Actual Entry, venue, token and maximal target-chain gas still require qualification.

Pool reservations now permanently admit a bucket into the same four-slot set.
Aliases and returns reuse their slot; reserved None-state entries have no
principal or shares and are skipped by maintenance. Admission does not qualify market depth, conversion routes or service operation. See [evolution and trust boundaries](ARCHITECTURE_EVOLUTION.md)
and its [source-scoped evidence](../reports/architecture-evolution/VERIFICATION.md). Current selected-pool changes have separate [verification](../reports/hookless-pool/VERIFICATION.md).

Current undeployed candidate: 1,000 NFTs; exact 600/300/100 random rarities; 0.05 ETH dormant mint; $100 original gross source activation with the captured contribution floor (98% at default 2%) and gas separate; 80/10/5/5 LP allocation; equal activated collective membership; separate 5% marketplace royalties. See the [feature and evidence reference](IMPLEMENTATION_STATUS.md).

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

[Entry](../src/ZZZActivationEntry.sol) and the converter base share an internal
read-only [v3 venue validator](../src/libraries/ZZZV3VenueValidation.sol), while
keeping their own admission and runtime-pin checks. The two concrete reward
converters inherit [one neutral implementation](../src/base/ZZZRewardConverter.sol)
but retain separate immutable ledgers, storage and balances. No external linked library, shared funds or generic executor is introduced.
The fixed LP PositionExecutor above has only typed Manager-controlled actions.

Private NFT and bucket identifiers and handoff phase/domain constants are now
explicit; wire phase values and financial ordering are unchanged. See the
[refactor comparison](../reports/auditability-refactor-20261025/VERIFICATION.md).

## Identity and custody

Only the canonical chain issues NFTs. Minting forwards the charge separately, requests verifiable randomness and creates a dormant ERC-721 with no LP or rewards. Mint and payment/request failures roll back atomically. The NFT enforces the 1,000 cap and excludes royalty/mint-receiver collisions. Before canonical sealing, the randomness configuration must exist; actual provider availability remains a deployment gate.

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

Activation requires revealed traits and at least $100 original gross source value, with the captured contribution floor (at default 2%, at least 98%) actually deployed as marginal oracle-valued LP, excluding incumbent idle/compound value. The immutable Registry-created [Entry](ACTIVATION_ENTRY.md) accepts only reviewed ZZZ or native ETH, with exact native forwarding for the selected native pool, or reviewed typed single-hop v3/v4 conversion into one actual accounting currency. V4 native routes require no wrapper; v3/unwrap paths retain their explicit wrapper dependencies. It binds current ownership, exact Vault calldata and original measured source USD through a callback-safe context. Separate conversion and LP legs share one captured allowance; they cannot each consume a new loss budget. Actual routes, liquidity and feeds need qualification; arbitrary calldata/conversion is not supported. The same NFT may receive permanent additions from $5 in original gross source value at current share NAV, with the same aggregate bound; a higher configured pool minimum still applies. After placement no more than 5% measured principal NAV may remain idle. Pool limits, fresh valuation, minimum liquidity and deadline guards remain.

Before share/membership changes, the Vault settles already-funded local dust
and harvests both current bucket legs. Entrant-only swaps/deployment increase the
existing main; incumbent residual, idle and compound remain in its aggregate NAV.
Contributions do not recenter the portfolio or reset its rebalance clock. Sub-twenty-unit dust settles to existing owner shares. Entry swaps are followed by settlement so their fees belong to incumbents; old LP is revalued after balancing. Fresh 5% compounding belongs to incumbent NAV. Final LP updates, actual marginal deployed-LP and dust guards precede owner checkpoint and share issuance.

First shares equal measured net principal USD; later shares round down as `supply * netNewUSD / (incumbentNAV + historicalCompoundValue)`. Historical non-current compounding stays incumbent backing and cannot subsidize the new contribution's captured deployed-LP floor. Zero-NAV/zero-share/cap violations revert. Donations, unclaimed rewards and buyback reserves do not buy shares. After successful issuance the Vault activates one `ZZZMembership` share for an initially dormant NFT and notifies the fixed NFT, which joins its separate rarity royalty ledger. Optional royalty-currency faults defer that currency's eligibility without undoing otherwise valid activation; the earlier cohort is protected. Other failed contribution checks roll back atomically. A top-up never adds collective/royalty weight.

**Reviewed signing boundary:** Entry/Pricing bind the caller maximum; a higher governed cap cannot silently widen a signed review. Actual source/route/feed and wallet qualification remain release gates.

## Funded LP rewards

Twenty raw units split16owner/2collective/1compound/1buyback. Owner indexes are pool/token-specific and use nonredeemable shares. Collective indexes are token-wide and give each activated canonical NFT one equal share. Eligibility persists through price declines, transfers and migration. Before the one-time membership is enabled, all published indexes are checkpointed. No Power module or USD reward weighting remains.

At most 32 admitted ERC20 LP assets plus the native ETH settlement asset bound checkpoint loops; native ETH now supports indexed venue income alongside already converted credits, without counting conversion as new income. Fractions carry per NFT; global division dust stays reserved. Smaller receipts carry and the maximum 19 raw-unit membership dust exception requires asset-specific economic review. No administrator can withdraw reward, orphan, compound or principal balances outside their constrained purpose. Claims remain available during operational pause.

The selected pool's actual earned venue fees fund this allocation when harvested; Uniswap's protocol fee is not PoPL revenue. Creator-payment inboxes and remote-fee intake are removed; only the bound Vault can allocate actual local LP receipts. Unsolicited donations remain unclassified/quarantined, not new holder income.

After collective exit reaches Ready (principal allocated), governance can still
validate ETH/fixed-ZZZ swap venues with deposits disabled for remaining buyback
reserves. Closing/Allocating remain locked; all native/feed/asset checks remain.
This does not reopen principal or access Migration-held payouts. Actual burn
keeps its ordinary keeper/unpause/execution controls. [Procedure](OPERATOR_MANUAL.md#restore-a-buyback-venue-after-collective-exit).

## NFT royalties and metadata

The NFT owns immutable royalty/metadata helpers. ERC-2981 requests 5% sale royalties payable directly to the separate receiver; 100% of eligible receipts is reserved for activated rarity weights 1/2/3. Native ETH and up to 16 reviewed ERC20 assets use funded indexes, pre-join pending synchronization and current-owner claims. There is no LP revenue split or arbitrary administrator sweep in this ledger. No external royalty-custody exit or administrator drain exists; eligibility and receipts continue after LP exit. Pre-admission/constructor/zero-eligibility funds are quarantined.

VRF callbacks only store request-bound words. Permissionless reveal follows mint order, drawing without replacement to exact 600/300/100 quotas. A separate word draws a fixed artwork entry without replacement within that rarity. Eight base colors form 58 palettes, combined with four patterns: Flowing arcs, Segmented panels, Orbital rings and Twin circuit routes. Rarity, palette and pattern remain immutable; palette/pattern do not affect rewards, while rarity sets only the separate royalty weight. The 1,000-entry inventory has 200 monochrome, 500 bicolor and 300 tricolor slots, each with the 60/30/10 rarity mix; identical palette/pattern/rarity finishes occur at most four times and all 100 Legendary looks are unique. Missing earlier fulfillment blocks later reveal; no reroll/cancellation bypass exists. [NFT details](NFT_METADATA.md).

The renderer selects among 2,784 supported palette/pattern/rarity/evolution SVG states, separate from the NFT supply. It values current local LP amounts, attributed idle and compound budgets using approved oracles, multiplied by shares/supply. Enhanced starts at $1,000 and Singularity at $10,000; market losses can downgrade artwork. Parked custody or stale dependencies report unavailable, with labelled fallback art. Terminal Exited status has verified zero LP and explicit `LP exited` metadata, while royalty eligibility survives. Metadata never gates claims/migration. Reveal/contributions emit ERC-4906 notifications. Permissionless per-token and bounded ordinal-range calls notify actual hashed IDs without price reads. An optional confirmed-block watcher uses the existing keeper's serial budgeted transaction path; permanent content publication, staged watcher operation and marketplace cache integration remain production work.

## Maintenance and migration

Hourly harvest operates once per bucket, collecting both legs and applying the
unchanged 80/10/5/5 allocation without a holder loop or balancing swap. Claims do
not run compounding or buybacks. Compounding has its separate governed interval
(default one hour); ordinary keeper automation waits for an in-range main with
no pending width/mode/threshold adjustment. Harvest remains independent.

LP routing2 compares up to four reviewed ETH/ZZZ venues independently of the LP
destination, using actual-core quotes after the old portfolio is removed. Ordinary
hybrid replacement retains as much passive inventory as possible, swapping only
for its 60% main floor when needed; search is bounded, not a global optimality
promise. Actual mints and Budget recheck captured utilization/loss/idle limits.
Manual width/mode changes may apply after cooldown even while the main is inside.
Automatic preapproved two-width policy stays disabled by default and cannot
coexist with required independent-reference confirmation. Policy changes never
create a sweep or new recipient. [Execution decisions](LP_EXECUTION_POLICY.md),
[optional portfolio](OPTIONAL_PORTFOLIO_IMPLEMENTATION.md). Pooling does not remove
impermanent loss, fees, adverse selection or MEV.

`Migration.moveFunds` atomically closes and deploys actual LP in another admitted pool with the same ordered accounting pair. Current native accounting preserves actual ETH identity and supports same-native-pair fee-tier changes. ETH/WETH atomic conversion is unsupported and rejected; WETH can be used only by separately reviewed conversion routes, not LP admission. One captured starting-price maintenance floor covers the complete move (3% loss by default, governed up to 10%), with gas separate; NFT shares and original bucket identity remain unchanged. Destination contributions and conversion routes are switched deliberately after verifying the resulting LP.

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
LP or canonical replacement; V5 handoff is allowed only before exit. Normal
same-pair pool moves/parking remain before exit. Production Registry no longer
admits ERC20-only LP pairs; other assets remain possible conversion venues or
royalty currencies, not principal pool currencies.

## Security domains and operational state

| Domain | Holds authority or value | Required separation |
| --- | --- | --- |
| Principal | Vault/manager custody, per-NFT nonredeemable shares, attributed idle/compound | Actual LP units and raw balances back NAV. Reward reserves, donations and prefunds cannot finance a newcomer. |
| LP liabilities | Fees classification and Rewards individual/equal-collective indices | Only actual received funds create income; compound/buyback reserves are not holder claimable. |
| Royalties | NFT-created separate receiver and rarity-weighted ledger | Only active eligibility; native/currency fractions and deferred cohorts survive transfers and conversion. |
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
addresses are not proof of independent prices. The [internal audit](../reports/preproduction-audit-20261025/REVIEW.md)
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

The [same-chain canonical handoff](CANONICAL_HANDOFF.md) freezes ownership and accounting, imports exact state and classified backing, and atomically retires the source/activates one replacement. It supports exact abort restoration before retirement and late funding afterward. Current schema is `ZZZ_CANONICAL_SAME_CHAIN_ADAPTABLE_POLICY_V6`; older schemas are rejected. Exact group records are 12 words / 384 bytes, with malformed/trailing layouts rejected. Funds transfer before zero-value acknowledgment, with separate Vault, Fees, Rewards and royalty backing. It requires revealed mints, parked local custody, complete classified accounting and `lpExitStarted == false`. It remains
permanently blocked after collective LP exit begins. No integrated future-chain transport or post-halt recovery is provided. Missing immutable capabilities require a separately reviewed replacement while the source works, not a configuration edit.

Production LP admission supports initialized static hookless native ETH/fixedZZZ fee tiers on pinned Robinhood dependencies. Generic ERC20-only LP admission is removed; separate conversion venues retain their own explicit checks. The selected pool has a static 1.002% LP fee and a recorded approximately 1.101% combined swap fee; only actual earned LP fees are PoPL revenue. Actual ETH identity is preserved. Other native pairs, dynamic native fees, hooks and pairs without fixed ZZZ are rejected.

Use the [feature/evidence reference](IMPLEMENTATION_STATUS.md) for completed checks
and their exact source scopes, and the [callable reference](CONTRACT_FUNCTIONS.md)
for the current public surface. Historical test counts, bytecode sizes and old
profiles are evidence for their recorded revision, not release approval.

[Native custody](NATIVE_ETH_ARCHITECTURE.md) uses WETH only for reviewed operations
that actually need it. Earlier [native V2 evidence](../reports/native-eth-port/VERIFICATION.md)
predates current accounting V6 and retains that source scope. Atomic ETH/WETH
conversion and old-schema import are unsupported. Actual route/provider/inventory
qualification remains open. ZZZ conversion at the default 1% needs a cheaper
qualified route; the selected pool does not qualify at reference prices. Actual
independent feeds, proof-verifying VRF, authority wallets, OpenSea primary mint,
native wallet/service operation, maximal gas/strategy economics, recovery
rehearsals and independent audit/remediation remain open. Production NOT APPROVED.
