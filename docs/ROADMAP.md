# Engineering roadmap

> Updated 2026-10-16: $100 original gross source value activates only if at least 99% becomes marginal deployed LP; network gas is separate. Atomic source entry and governed paused parking join the native adapter, bounded claims and read API as implemented candidates. Other accepted economics/NFT rules are unchanged. Actual routes/services, staging and independent audit remain open. See the [feature and evidence reference](IMPLEMENTATION_STATUS.md). Historical evidence retains its source scope.

The development candidate implements paid dormant mint/activation, shared LP per pool with nonredeemable NFT shares, pool-level upkeep, repeated whole-bucket custody migration with timelocked future-route onboarding, immutable creator-payment intake, equal membership, quota-based VRF reveal, dynamic metadata and a separate funded royalty receiver. The [reward-funding verification](../reports/reward-funding/README.md) predates the current alignment changes. The [shared-pool review](../reports/pooled/README.md) and [earlier implementation evidence](../reports/IMPLEMENTATION_UPDATE.md) remain scoped to their own revisions; they do not validate the changed reward entrypoints. This roadmap explains engineering sequence and dependencies. All task status and acceptance criteria live in the [central Todo](../TODO.md); this page does not maintain another progress list or assign dates.

The [2026-10-14 readiness pass](../reports/PRODUCTION_READINESS.md) adds immutable dependency/action pins, working keeper calldata submission, pending-state and file-write hardening, stateful EVM accounting, full Slither triage, six real dependency fork checks, collection/asset gas workloads and an offline production inventory gate. These earlier development milestones do not close the current alignment, verifiable-randomness availability, live transport, oracle, staging and independent-review work.

## 1. Establish a reproducible build

Retain and reproduce the recorded dependency lockfile, compiler profile, unit/fuzz results, and standard runtime/initcode size checks. Review package contents and pin remaining upstream/CI references to immutable revisions. Benchmark execution gas under the size-oriented optimizer profile and preserve enough production deployment margin. Reproduce off-chain tests on the supported Unix environment.

## 2. Prove custody and reward accounting

Extend the new independent integer-ledger stateful handler beyond its current local custody/reward scope. Existing unit/fuzz and stateful tests cover mint, activation, top-ups, harvest, owner changes, claims, pauses, donations, compounding and rebalance. Add full multi-chain stateful and real provider failure behavior; existing repeated migration tests still use a mock transport. Review coverage rather than treating a passing run as proof of every possible sequence.

## 3. Validate real Uniswap operation

Use pinned-block fork tests against actual supported PositionManager, PoolManager, Permit2, and StateView deployments. Exercise mint, increase, collection, close, swaps, approvals, callbacks, donations, and failure paths. Measure rebalancing and all-asset checkpoint costs at realistic collection sizes.

The historical fixed-block suite used a different hookless pool. The new selected-native/Pons candidate preserves the physical PoolKey, normalizes only accounting to WETH, checks reviewed runtimes/wiring and handles native settlement without spending prefunds. Actual selected-pool fork tests now cover that path; preserve their exact source/block scope and complete the full current-source fork/gas/strategy qualification. This is not generic hook approval or permission to deploy. Mock-venue collection/asset workloads do not establish target-pool operating costs.

Independently qualify the implemented immutable [atomic Entry](ACTIVATION_ENTRY.md): original-source gross valuation, exact received balances, current-owner intent and one full 1% execution/undeployed bound across conversion and LP deployment. Register and rehearse actual ZZZ/ETH/USDG routes and supply a funded reviewed USDC route before enabling it. Reject quotes that cannot meet the bound; do not subsidize them with incumbent LP, idle or compound assets.

Rehearse [custody parking](CUSTODY_PARKING.md) through the sealed two-day timelock: global pause, exact bucket snapshot, close-only raw-token minimums, nonce cancellation/expiry and honest Parked custody reporting. Prove fresh-oracle resume and reviewed parked migration retain funding/legacy-liability barriers. Price-feed and inbox independence does not bypass actual venue, wrapper or token failures.

## 4. Validate the accepted economics and NFT lifecycle

Independently review equal activated-NFT membership, collection/delivery-time collective allocation for unharvested/remote rewards, processing-time creator receipts, incumbent pending/indexed/dust settlement, remote/in-flight eligibility and reward-asset limits. Model timing incentives, manipulated valuations, depreciated positions, strategy costs, and token eligibility. Review the implemented repeated-hop custody epochs, ordered home-location ACKs, canonical returns, legacy reward budgets, and post-seal append-only route governance against adversarial operation sequences.

The user reports creator revenue sharing proportional to PoPL liquidity. Exact [sampled measurement tools](REVENUE_SHARE.md) now propose fee-weighted active share (preferred with complete reliable fee observations) or time-weighted active share; neither is creator-approved yet or reconstructs exact intra-swap v4 fee attribution. Confirm the base, window, sampling, payout asset/frequency and rounding; implement the complete hook-event/trace parser and reconcile actual receipts. Only funded, processed payments enter the existing 80/10/5/5 indexes. Native custody support does not confer Pons revenue rights. The website's assumed conventional-fee example remains hypothetical. See [external funding](EXTERNAL_REWARDS.md).

Before paid minting, establish actual supported-chain VRF, subscription backing and measured callback/failure recovery. Quotas/inventory and current-value evolution have local tests, but mock VRF does not establish Robinhood service support. The eight-color/58-palette/four-pattern library covers 2,784 artwork states; its verified IPFS upload bundle is prepared, not pinned. Choose redundant hosting, verify the final CID and every renderer path, then stage the already-implemented market-driven watcher with real feeds and marketplace caches. Marketplace royalty payment remains voluntary. The immutable 32-operation [claim router](CLAIM_ROUTER.md) now batches LP and royalty claims; independently qualify worst-case gas, owner callbacks and frontend chunking.

The [confirmed API](FRONTEND_API.md) reads real NFT state and both funded ledgers. Its optional [history extension](FRONTEND_HISTORY.md) now provides wallet inventory and all-time per-NFT/asset LP-plus-royalty claims from exact confirmed raw-log replay, with canonical ownership/count checks. Host and rehearse it, independently reconcile ingestion completeness, and finish gross lifetime/24h fee attribution/USD projections. Replace website simulations only after a reviewed deployment exists.

## 5. Implement production transport and operations

Real bridge transport is a later activation phase, not a requirement to enable at initial launch. An independently approved [migration-disabled launch](OPERATIONS.md#migration-disabled-initial-launch) retains the other security and operating requirements; current progress stays in the [migration tasks](../TODO.md#future-migration).

The fixed router and append-only future-provider onboarding framework are implemented. Select and independently review bridge-specific `IZZZTransportProvider` wrappers, establish equivalent-token and supply semantics, and test canonical-to-satellite, satellite-to-satellite, canonical return, and revisited destinations against actual providers. Exercise authentication, backing, duplication, ordered home notifications, absent-hop epochs, delays, retries, legacy rewards after departure, pauses, and provider failures. Review every future destination's code and authorities before timelocked route onboarding. Exercise real signer/RPC behavior and indexer backfill/reorg recovery on a test network.

Before enabling a real bridge, independently qualify the implemented permanent destination capacity admission and real provider recovery. Reservations and historical custody share four permanent slots; aliases and returns reuse them. Source governance must still authenticate the reviewed destination and confirmed admission. The [architecture evolution design](ARCHITECTURE_EVOLUTION.md) separates different-pair conversion, fixed-home remote custody and canonical NFT/ledger relocation. Home-chain creator-funded 5% compound reserves still wait for custody to return unless a separately reviewed funded remote reinvestment design is added. Task status remains in the central Todo.

## 6. Complete independent review before release

Obtain an independent security audit, verify remediation, review deployment configuration, and satisfy the applicable [central release criteria](../TODO.md#task-audit-release) before recording final approval in the [release record](RELEASE_CHECKLIST.md).

## Later product work

Selected-pool native custody, atomic source entry, governed custody parking, bounded claims, the read API and measurement calculator are implemented candidates, not external-service completion. Actual input routes, complete live projections, production VRF/feeds/authorities, immutable publication, testnet operating rehearsals and independent audit remain initial release work. Use all three release-test layers: local security/accounting, actual selected-pool Robinhood mainnet fork and Robinhood Testnet operation; Sepolia is supplementary. Multi-hop buybacks and satellite deposits remain later extensions. Future bridging can remain disabled initially and be added through the fixed timelocked framework after provider qualification.
