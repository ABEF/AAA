# Engineering roadmap

The development candidate implements paid dormant mint/activation and repeated custody migration with timelocked future-route onboarding. [Current implementation evidence](../reports/IMPLEMENTATION_UPDATE.md) records its checks separately from historical reports. This roadmap orders the remaining release work; it does not assign dates or claim release approval.

The [2026-10-14 readiness pass](../reports/PRODUCTION_READINESS.md) adds immutable dependency/action pins, working keeper calldata submission, pending-state and file-write hardening, stateful EVM accounting, full Slither triage, six real dependency fork checks, collection/asset gas workloads and an offline production inventory gate. These development milestones do not close the remaining economic, live transport, oracle, staging and independent-review work.

## 1. Establish a reproducible build

Retain and reproduce the recorded dependency lockfile, compiler profile, unit/fuzz results, and standard runtime/initcode size checks. Review package contents and pin remaining upstream/CI references to immutable revisions. Benchmark execution gas under the size-oriented optimizer profile and preserve enough production deployment margin. Reproduce off-chain tests on the supported Unix environment.

## 2. Prove custody and reward accounting

Extend the new independent integer-ledger stateful handler beyond its current local custody/reward scope. Existing unit/fuzz and stateful tests cover mint, activation, top-ups, harvest, owner changes, claims, pauses, donations, compounding and rebalance. Add full multi-chain stateful and real provider failure behavior; existing repeated migration tests still use a mock transport. Review coverage rather than treating a passing run as proof of every possible sequence.

## 3. Validate real Uniswap operation

Use pinned-block fork tests against actual supported PositionManager, PoolManager, Permit2, and StateView deployments. Exercise mint, increase, collection, close, swaps, approvals, callbacks, donations, and failure paths. Measure rebalancing and all-asset checkpoint costs at realistic collection sizes.

The new fixed Robinhood block/hash suite exercises ordinary typed settlement against deployed dependencies, authentic token burns and ETH/USD reads. It rejects the selected native/Pons market and uses a different hookless pool created only on the fork. Mock-venue gas workloads cover 1/100/1,000 NFTs and 32 funded assets; live venue/backtesting/MEV and operating-cost approval remain outstanding.

## 4. Decide economics and migration scope

Approve or redesign lifetime-contribution Power, settlement-time collective weights, remote/in-flight eligibility, and reward-asset limits. Model timing incentives, manipulated valuations, depreciated positions, strategy costs, and token eligibility. Review the implemented repeated-hop custody epochs, ordered home-location ACKs, canonical returns, legacy reward budgets, and post-seal append-only route governance against adversarial operation sequences.

Decide the reward source and integration for the selected Robinhood native-ETH/Pons-hook pool. Its zero core LP fee does not give external LPs proportional hook revenue; the old 0.30% website example is not a usable actual fee model. Native settlement and hook-aware integration are still absent.

## 5. Implement production transport and operations

The fixed router and append-only future-provider onboarding framework are implemented. Select and independently review bridge-specific `IZZZTransportProvider` wrappers, establish equivalent-token and supply semantics, and test canonical-to-satellite, satellite-to-satellite, canonical return, and revisited destinations against actual providers. Exercise authentication, backing, duplication, ordered home notifications, absent-hop epochs, delays, retries, legacy rewards after departure, pauses, and provider failures. Review every future destination's code and authorities before timelocked route onboarding. Exercise real signer/RPC behavior and indexer backfill/reorg recovery on a test network.

## 6. Complete independent review before release

Obtain an independent security audit, verify remediation, review deployment configuration, and satisfy every item in the [release checklist](RELEASE_CHECKLIST.md) before funded use.

## Later product work

A custom/native-ETH Uniswap v4 integration and reward model, NFT attributes/levels, Enhanced status, a hosted dashboard/API, multi-hop buybacks, and satellite user deposits require separately designed and reviewed implementations. Future-chain route onboarding and repeated equivalent-asset custody hops are implemented in the development candidate; they still require real transport/deployment validation and do not move the NFT between chains or provide general asset conversion.
