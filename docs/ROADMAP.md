# Engineering roadmap

> Accepted current rules: $100 measured deployed-LP activation, 80/10/5/5 LP revenue, equal activated-NFT collective membership, a 1,000-NFT cap with exact 600/300/100 rarity quotas, VRF reveal, current-value artwork evolution and separate 5% marketplace royalties. Fresh verification is in progress; historical reports retain their source/revision scope.

The development candidate implements paid dormant mint/activation, shared LP per pool with nonredeemable NFT shares, pool-level upkeep, repeated whole-bucket custody migration with timelocked future-route onboarding, immutable creator-payment intake, equal membership, quota-based VRF reveal, dynamic metadata and a separate funded royalty receiver. The [reward-funding verification](../reports/reward-funding/README.md) predates the current alignment changes. The [shared-pool review](../reports/pooled/README.md) and [earlier implementation evidence](../reports/IMPLEMENTATION_UPDATE.md) remain scoped to their own revisions; they do not validate the changed reward entrypoints. This roadmap orders the remaining release work; it does not assign dates or claim release approval.

The [2026-10-14 readiness pass](../reports/PRODUCTION_READINESS.md) adds immutable dependency/action pins, working keeper calldata submission, pending-state and file-write hardening, stateful EVM accounting, full Slither triage, six real dependency fork checks, collection/asset gas workloads and an offline production inventory gate. These earlier development milestones do not close the current alignment, verifiable-randomness availability, live transport, oracle, staging and independent-review work.

## 1. Establish a reproducible build

Retain and reproduce the recorded dependency lockfile, compiler profile, unit/fuzz results, and standard runtime/initcode size checks. Review package contents and pin remaining upstream/CI references to immutable revisions. Benchmark execution gas under the size-oriented optimizer profile and preserve enough production deployment margin. Reproduce off-chain tests on the supported Unix environment.

## 2. Prove custody and reward accounting

Extend the new independent integer-ledger stateful handler beyond its current local custody/reward scope. Existing unit/fuzz and stateful tests cover mint, activation, top-ups, harvest, owner changes, claims, pauses, donations, compounding and rebalance. Add full multi-chain stateful and real provider failure behavior; existing repeated migration tests still use a mock transport. Review coverage rather than treating a passing run as proof of every possible sequence.

## 3. Validate real Uniswap operation

Use pinned-block fork tests against actual supported PositionManager, PoolManager, Permit2, and StateView deployments. Exercise mint, increase, collection, close, swaps, approvals, callbacks, donations, and failure paths. Measure rebalancing and all-asset checkpoint costs at realistic collection sizes.

The new fixed Robinhood block/hash suite exercises ordinary typed settlement against deployed dependencies, authentic token burns and ETH/USD reads. It rejects the selected native/Pons market and uses a different hookless pool created only on the fork. Mock-venue gas workloads cover 1/100/1,000 NFTs and 32 funded assets; live venue/backtesting/MEV and operating-cost approval remain outstanding.

## 4. Validate the accepted economics and NFT lifecycle

Independently review equal activated-NFT membership, collection/delivery-time collective allocation for unharvested/remote rewards, processing-time creator receipts, incumbent pending/indexed/dust settlement, remote/in-flight eligibility and reward-asset limits. Model timing incentives, manipulated valuations, depreciated positions, strategy costs, and token eligibility. Review the implemented repeated-hop custody epochs, ordered home-location ACKs, canonical returns, legacy reward budgets, and post-seal append-only route governance against adversarial operation sequences.

The selected funding direction is creator payments to an immutable per-bucket receiver, with actual processed funds using the existing 80/10/5/5 indexes. Review processing-time weights, voluntary payment terms, all-inbox membership synchronization, constructor prefund quarantine, optional native wrapping and dependency outages. No creator percentage or guaranteed proportional hook revenue is inferred. The zero-core-fee Robinhood native-ETH/Pons pool still requires its separate native settlement and hook-aware LP adapter integration; the website's assumed 0.30% conventional-fee example remains hypothetical. See [external funding](EXTERNAL_REWARDS.md).

Before paid minting, establish actual supported-chain verifiable randomness: reviewed proof-verifying coordinator/code, subscription backing, key/finality/callback settings and staged fulfillment. Verify strict mint-order draws exhaust exactly 600 Commun / 300 Rare / 100 Legendary allocations. Rehearse the head-of-line failure risk without adding rerolls or manual overrides. Publish and pin the reviewed artwork root, and test current-value evolution/downgrades and explicit unavailable remote/oracle states. The 5% marketplace request and activated 1/2/3 holder royalty pool need separate funded accounting/token/reentrancy review; marketplace payment is not guaranteed. Expanded solid/bicolor/tricolor artwork is design work, not an implemented production asset library.

## 5. Implement production transport and operations

The fixed router and append-only future-provider onboarding framework are implemented. Select and independently review bridge-specific `IZZZTransportProvider` wrappers, establish equivalent-token and supply semantics, and test canonical-to-satellite, satellite-to-satellite, canonical return, and revisited destinations against actual providers. Exercise authentication, backing, duplication, ordered home notifications, absent-hop epochs, delays, retries, legacy rewards after departure, pauses, and provider failures. Review every future destination's code and authorities before timelocked route onboarding. Exercise real signer/RPC behavior and indexer backfill/reorg recovery on a test network.

## 6. Complete independent review before release

Obtain an independent security audit, verify remediation, review deployment configuration, and satisfy every item in the [release checklist](RELEASE_CHECKLIST.md) before funded use.

## Later product work

A custom/native-ETH Uniswap v4 liquidity integration, expanded NFT artwork, a hosted dashboard/API, multi-hop buybacks, and satellite user deposits require separately designed and reviewed implementations. Future-chain route onboarding and repeated equivalent-asset custody hops are implemented in the development candidate; they still require real transport/deployment validation and do not move the NFT between chains or provide general asset conversion.
