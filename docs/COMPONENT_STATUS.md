## Pricing-V2 component delta - 2026-10-24

Oracle now creates a fixed [ContributionPricing helper](../src/ZZZContributionPricing.sol).
It binds dual-source snapshots to Entry/Budget/Vault factual settlement. The
current inventory has15 fixed helpers, explicit pricing2/accounting2/routing2,
and user-selected3% price agreement distinct from execution caps. See
[design/operator boundary](PRICE_SECURITY.md), [feature reference](IMPLEMENTATION_STATUS.md)
and [source-scoped verification](../reports/price-security/VERIFICATION.md).
Actual services and release approval remain open; historical tables retain scope.

## Native V2 inventory and preflight - 2026-10-24

[Current schema-5 preflight](PRODUCTION_PREFLIGHT.md) validates native/V4 bindings,
actual versus approved runtime pins and current governed limits. A separate
bounded read-only observer captures a canonical snapshot without upgrading review
status. Legacy schema 4 stays historical; missing actual public addresses,
prices/routes/VRF/services and audit evidence remain release blockers. No signer,
Solidity, website/service, existing Anvil/journal or monitor change follows.

**Current policy, 2026-10-24:** [Typed v4 conversions](TYPED_V4_ROUTES.md) and
[governed execution-loss limits](EXECUTION_LOSS_POLICY.md) are implemented in the
undeployed candidate. Defaults are 1% contribution, 1% conversion and 3% maintenance;
immediate governance may set each category up to a hard 10%. Existing stricter
venue/caller minima remain. Pending normal custody approvals retain their original
absolute floor. Earlier fixed-cap or v3-only descriptions below retain their
historical/default scope. Actual routes, services and independent audit remain open.

## Bounded operating controls - 2026-10-24

The [current control candidate](../reports/post-seal-controls/VERIFICATION.md)
adds governance-only future VRF gas/confirmation settings and a buyback operating
limit within its immutable hard ceiling. Pending draws, fixed provider settings,
canonical economic records and backing are preserved. Actual services/provider
limits and independent review remain open; older entries retain their source scope.

# Component implementation status

**Native V2 update (2026-10-24):** the [implemented candidate and evidence](../reports/native-eth-port/VERIFICATION.md)
carry actual ETH through Entry, manager/Vault, indexed rewards, reserves, native
raw exit and canonical funding/abort. API/keeper profiles explicitly select the
accounting version. Atomic ETH/WETH conversion, legacy V1 import, native website
profile, production inventory/services and independent audit remain open.
Earlier dated entries retain their original code/evidence scope.

**2026-10-24 selected-pool checkpoint:** [hookless ETH/ZZZ selection](POOL_SELECTION.md), atomic `moveFunds`, normal/raw custody exits and [scoped evidence](../reports/hookless-pool/VERIFICATION.md) supersede current Pons admission. The subsequent [native ETH candidate](NATIVE_ETH_ARCHITECTURE.md) is implemented with the limits above; [bounded post-seal operating controls](POST_SEAL_POLICY.md) are implemented candidates; actual service/inventory qualification remains open.

**Current candidate (2026-10-23):** [governed custody handoff](GOVERNED_CUSTODY_HANDOFF.md) replaces the legacy LP v3 bridge/pair executor. Whole-collection handoff remains separate. Normal all-ZZZ exit, explicitly approved raw emergency exit and separate royalty-currency custody are local candidates; real finality/remote accounting, the updated production inventory and independent qualification remain open. Earlier descriptions/evidence retain their historical scope. [Verification](../reports/custody-handoff/VERIFICATION.md).

## Historical pair-conversion candidate - superseded 2026-10-23

[`ZZZPairMigration` (retired)](../reports/history/retired-v3-contracts/ZZZPairMigration.sol.txt), created by Migration, adds
governed typed same-chain conversion. Vault/Budget/canonical companions retain
fixed custody, loss and epoch boundaries; Fees keeps old reward currencies and
selected historical compound. See [operator procedure](PAIR_MIGRATION.md) and
[current scoped evidence](../reports/pair-composition/VERIFICATION.md). Real route,
cross-chain and independent qualification remain open; production is NOT APPROVED.

**2026-10-17 handoff candidate:** the current source adds the six-domain
[same-chain canonical handoff](CANONICAL_HANDOFF.md), including atomic cutoff
capture, bounded ordered settlement, exact state/backing import, restored abort
and atomic source retirement/replacement activation. That historical revision sealed 20
modules; the governed-custody candidate instead seals 16 and removes the old LP transport roles. Current verification
is recorded [separately](../reports/canonical-handoff/VERIFICATION.md); the dated
receipts below do not verify these changes. Cross-chain closure, finalized proof,
lineage/transport and independent qualification remain open. No deployment is approved.

**2026-10-16 candidate update; undeployed and not production approved.** Activation accepts at least **$100 original gross source value** and requires at least **99% as genuinely marginal deployed LP**, excluding incumbent principal/idle/compound assets; network gas is separate. The immutable Entry binds that source budget through typed conversion into the Vault. Governed paused parking adds a source-oracle-independent close into Vault custody. Other rules remain 80/10/5/5 LP revenue, equal activated-NFT collective shares, 1,000 NFTs with exact 600 Commun / 300 Rare / 100 Legendary quotas, VRF reveal, current-value evolution and separate 5% requested marketplace royalties. See the [feature and evidence reference](IMPLEMENTATION_STATUS.md).

The earlier [release-hardening verification](../reports/release-hardening/README.md) covers bounded metadata notifications and the optional watcher: 342 offline Solidity passes, one expected fork setup skip and 20 size gates. Its [static analysis](../reports/release-hardening/static-analysis/README.md) reviewed 179 findings internally. These counts and size margins predate the new native adapter, claim router and 1% entry policy; they are not fresh verification of this candidate. Targeted selected-market fork tests have been added, but complete current-source tests, size/gas checks, static review and exact-revision CI must be checked separately. No internal pass replaces an independent audit.

Previous [integration/recovery evidence](../reports/release-progress/README.md) records 430 local Solidity passes, 478 portable Python passes, 17 actual selected-pool fork passes, 22 size gates and 210 individually reviewed Slither findings. Those receipts predate Entry and parking. Release-specific Ubuntu CI, production services/staging and external audit remain open.

Current [gap-hardening evidence](../reports/gap-hardening/README.md) records 488 Solidity passes, 488 portable Python passes, 20 selected native/Pons plus nine secondary fork passes, 23 size gates, 29 production source bindings and 220 fresh internally reviewed Slither findings. Actual fork fixtures, two offline fork setup skips and four Unix-only Python cases remain explicitly scoped. Real routing/services, final-release staging and independent audit remain open.

The [website-alignment evidence](../reports/website-alignment/README.md), [reward-funding review](../reports/reward-funding/README.md), [pooled review](../reports/pooled/README.md), [earlier readiness review](../reports/PRODUCTION_READINESS.md) and historical CI reports retain their own source/revision scope. The live-dependency fork and extended accounting stress profile were not rerun locally for the final artwork source. Actual integrations, staged operation and independent audit remain required; no funded deployment is approved.

| Component | Current candidate implementation | Remaining qualification |
|---|---|---|
| `ZZZCanonicalHandoff.sol` | Six-domain captured cutoffs, ordered settlement, eight-row export/import, exact classified funding, restored abort and one atomic successor | Worst-case gas, interruption/callback review, successor admission, canonical cross-chain finality and independent audit |
| `ZZZNFTCanonical.sol` / `ZZZVaultCanonical.sol` / `ZZZFeesCanonical.sol` | Sealed owner-bound codecs and typed import/custody hooks; exact traits, shares, fractions and original identity | Complete source-bound accounting verification, contract-owner compatibility and operational relaying |
| `ZZZRoyaltyFactory.sol` / `ZZZRewardReceiverFactory.sol` | Immutable automatic factories for the NFT royalty ledger and classified creator inboxes | Deployment/owner bindings, native and token dependency behavior and successor receipt continuity |
| `ZZZVault.sol` | Exact 0.05 ETH Dormant mint; $100 source-bound activation with the captured marginal-LP floor (99% at default1%); same limit on additions; nonredeemable shares; oracle-independent paused close into Parked custody and guarded resume | Independent accounting review, target-venue gas and staged recovery; no guarantee against failed external assets or venues |
| `ZZZNFT.sol` | ERC-721/2981/4906; 1,000 cap; ordered quota/inventory VRF draws; immutable traits and royalty/metadata/claim helpers | Actual proof-verifying coordinator, funded subscription, callback/failure rehearsal and independently reviewed permanent artwork root |
| `ZZZNFTMetadata.sol` | Read-only current marked principal/idle/compound NAV by NFT share; four evolution states; price-driven downgrades; explicit unavailable valuation; 58 palettes and four patterns selecting 2,784 supported artwork states | Permanent asset publication, live pricing and marketplace cache integration; bounded notifications and watcher are implemented but need staged operation |
| `ZZZRoyaltyRewards.sol` | Separate funded royalty ledger, 1/2/3 weights, optional-asset eligibility isolation, and paused per-currency custody exit with full original-asset return | External custody temporarily suspends that currency; no ETH substitution or remote ledger remapping; independent review remains open |
| `ZZZLiquidityManager.sol` | Typed v4 mint/increase/collect/burn/swap; exact direct native funding/settlement for admitted static hookless native ETH/ZZZ pools on pinned Robinhood dependencies; real venue key preserved and prefunds isolated | Complete selected-pool fork lifecycle, adverse callback/price/funding behavior, gas and strategy qualification; generic native/hook support is not authorized |
| `ZZZClaimRouter.sol` | Immutable NFT-created helper; up to 32 mixed NFT/asset/ledger claims; duplicate rejection, current-owner checks, direct payouts and atomic rollback | Target-chain worst-case gas, frontend chunking/simulation, staged claims and independent review; no arbitrary targets or payout recipients |
| `ZZZActivationAssets.sol` | Immutable registry-created helper; append-only governed source policies; add/disable/re-enable, code/decimal/feed checks on enable, dependency-independent disable | Proxy/token authority review, exact deployment inventory and operating qualification remain required |
| `ZZZActivationEntry.sol` | Immutable Registry-created helper; owner-authenticated direct/native/typed single-hop v3/v4 inputs; original-source USD budget bound to exact Vault call; approvals/context callback isolation and atomic rollback | Actual route/funding/feed qualification, complete route-policy history, immutable binding review, combined selected-pool execution and wallet/Testnet rehearsal |
| `ZZZRewards.sol` | Funded owner rewards by bucket shares; collective rewards by equal activated membership; index fractions and current-owner claims; current offline unit/fuzz/default-invariant suites pass | Independent accounting review, delayed-collection economics and target-chain maximum admitted-asset costs |
| `ZZZMembership.sol` | Exactly one collective share per activated canonical NFT; pre-activation checkpoint; no top-up/rarity/age weighting; bounded canonical funded-dust settlement including Parked buckets | Qualify actual Entry/venue costs at the reduced immutable 4-historical-bucket cap and persistence through every custody state |
| `ZZZFeeController.sol` | Twenty-unit 16/2/1/1 allocation; segregated reserves; remote provenance; immutable creator inbox factory; exact funded intake and entry synchronization | Independent review, admitted token/wrapper behavior and actual Entry/venue costs with four reachable inboxes; separate factory ceiling remains 16 |
| `ZZZRewardReceiver.sol` | Immutable original bucket/pair and optional native wrapper; plain payments; permissionless processing; prefund quarantine | Helper is not a replaceable module; unsupported assets have no rescue; dependency outages can block entry |
| `ZZZStrategy.sol` / `ZZZCompounder.sol` | Oracle-relative ranges, deviation/cooldown/slippage policy; keeper coordinates Vault reinvestment of its own budget | Backtesting, volatility, MEV, gas and real settlement/rounding economics |
| `ZZZBuyback.sol` | Bounded direct buyback/burn with acquired-balance and supply checks; separately governed reviewed future ZZZ target | No arbitrary multi-hop; actual token, routes, feed, burn behavior and operator coordination need qualification |
| `ZZZMigration.sol` / `ZZZCustodyValidation.sol` | Atomic same-accounting-pair `moveFunds`; governed exact-snapshot all-ZZZ or explicit raw custody exit; local holding and one-time destination binding; actual funded local completion/full recovery; immutable read-only admission helper | Recipient custody is trusted; real finality, remote accounting, target routes, backend state and updated inventory remain unqualified |
| `ZZZAccessController.sol` | Zero-delay governed configuration, keeper/guardian permissions and 16 fixed sealed module bindings; retired LP bridge roles cannot be bound | Governance and external dependencies remain trust boundaries; no ordinary implementation rebinding after seal |
| `ZZZOracle.sol` / `ZZZPoolRegistry.sol` | USD normalization and freshness checks; explicit runtime-pinned native-pool admission; real `get` and actual-currency `accounting` assets, with native ETH at zero | Reliable denominated feeds/outage policy; actual native markets and production inventory remain unqualified |
| `frontend_api/` | Unhosted confirmed NFT/wallet/collection reads; complete same-chain allocation/claim/conversion history, bounded 24h/lifetime earnings at current prices and typed unsigned preparation | Actual native/pricing-V2 deployment/profile, provider/history/price/trace qualification, proxy/load/finality/recovery staging and public wallet/OpenSea integration remain open; no API signer |
| `zzz_ops/revenue_share.py` | Exact time-weighted and per-asset fee-weighted sampled active-liquidity proposals, receipt/dust reports and pinned actual-position collector | Creator approval, complete hook-event parser, source authenticity/completeness, receipt reconciliation and operating tests |

## Off-chain operation and integration boundaries

The keeper discovers buckets and performs maintenance once per physical LP group, rather than once per NFT. Entry settlement additionally scans bounded canonical bucket dust and creator inboxes; this does not turn ongoing rebalancing into 1,000 NFT transactions. Keeper configuration/state now identifies `shared-pools-v2`; old state requires deliberate reconciliation without deleting pending transactions. Real signing and recovery still need staged network evidence.

The reorg-aware indexer, [confirmed API](FRONTEND_API.md) and optional [wallet/lifetime-claims replay](FRONTEND_HISTORY.md) are implemented but unhosted. The API pins deployment/helpers/runtime and EIP-1898 blocks; history requires actual NFT-creation coverage through the exact target. Missing history is unavailable, not zero. Bounded lifetime/24h allocated earnings and current-price USD reporting are implemented candidates; actual complete history/pricing remains unqualified, and SQLite ingestion completeness remains an operator trust boundary. The public website is still simulated. Notifications/watcher exist but need real runtime/feed/signer staging and marketplace testing. The verified artwork bundle is prepared, **not uploaded or pinned**. Migration remains deliberate governance/operator work.

Published/indexed rewards, pending creator inboxes and funded canonical dust are settled for incumbents before entry. Unharvested venue fees and undelivered remote rewards retain collection/delivery-time collective membership; creator funds use processing-time membership. Separate royalty receipts use their activated rarity weights. Historical USD estimates are not funded liabilities or proof of entitlement.

The selected Robinhood hookless native ETH/ZZZ adapter is implemented as a candidate, with production admission still blocked by release gates. Target inputs are ZZZ, ETH, USDC and USDG. The immutable [Entry](ACTIVATION_ENTRY.md) now authenticates original-source value through an admitted typed route into actual native ETH/ZZZ accounting; a quote or separate swap cannot substitute for this atomic binding. Actual route funding and fees must meet the captured whole-route contribution limit (default1%, governed maximum10%). USDC routing remains unavailable pending a funded reviewed route. Conventional fees earned by this LP fund its 80/10/5/5 allocation. Historical creator-sharing [measurement proposals](REVENUE_SHARE.md) are optional and are not launch dependencies. Production VRF, bridge backing, authorities, deployment and independent audit remain open. Equivalent-asset migrations do not move the NFT or permit arbitrary conversion.
