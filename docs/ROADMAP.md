# Engineering roadmap

The v0.2 source candidate and Python test evidence are available. This roadmap orders the remaining work; it does not assign dates or claim release approval.

## 1. Establish a reproducible build

Resolve and review dependencies, retain a lockfile, pin upstream and CI revisions, compile all Solidity modules/tests/scripts, check runtime and initcode sizes, and execute the Foundry unit/fuzz suite. Reproduce off-chain tests on the supported Unix environment.

## 2. Prove custody and reward accounting

Add stateful EVM invariants and adversarial tokens, callbacks, NFT receivers, and oracle behavior. Verify fee/principal separation, idle attribution, reward funding, rounding, checkpointing, and position replacement across arbitrary operation sequences.

## 3. Validate real Uniswap operation

Use pinned-block fork tests against actual supported PositionManager, PoolManager, Permit2, and StateView deployments. Exercise mint, increase, collection, close, swaps, approvals, callbacks, donations, and failure paths. Measure rebalancing and all-asset checkpoint costs at realistic collection sizes.

## 4. Decide economics and migration scope

Approve or redesign lifetime-contribution Power, settlement-time collective weights, remote/in-flight eligibility, reward-asset limits, and one-hop immutable routes. Model timing incentives, manipulated valuations, depreciated positions, strategy costs, and token eligibility.

## 5. Implement production transport and operations

Select and independently review a bridge-specific `IZZZTransport`, establish token and supply semantics, and test two-chain authentication, backing, duplication, ordering, delays, retries, acknowledgements, pauses, and provider failures. Exercise real signer/RPC behavior and indexer backfill/reorg recovery on a test network.

## 6. Complete independent review before release

Obtain an independent security audit, verify remediation, review deployment configuration, and satisfy every item in the [release checklist](RELEASE_CHECKLIST.md) before funded use.

## Later product work

A custom Uniswap v4 hook, NFT attributes/levels, Enhanced status, a hosted dashboard/API, multi-hop buybacks, and broader future-chain migration require separately designed and reviewed implementations. They are not included features of this candidate.
