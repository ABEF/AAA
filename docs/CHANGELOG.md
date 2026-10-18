# Range-policy application - 2026-10-18

Timelocked range-width changes now make ordinary keeper rebalance eligible after
cooldown without requiring price movement. Current physical ticks are compared
at the stored center, avoiding drift churn. Existing Vault safeguards, shares and
reward ledgers remain unchanged. Confirmed backend context exposes both trigger
causes. See [design](RANGE_POLICY_UPDATES.md) and [scoped verification](../reports/range-policy/VERIFICATION.md).
Production parameters/services and independent qualification remain open.

# Product alignment candidate — 2026-10-15

## 2026-10-18 - Dynamic liquidity and rebalance budget

Added the explicitly approved 3% aggregate ordinary-rebalance cap, a metadata
spot/oracle guard, current-LP/share-denominator API context and out-of-range
contribution warnings with honest eligibility timing. Original-source 1%, gas
separation and reward economics remain. See [review/evidence](../reports/dynamic-liquidity/VERIFICATION.md).

Undeployed breaking development changes, with verification and release gates recorded in [the alignment review](../reports/website-alignment/README.md). This is not an upgrade of deployed contracts.

- $100 net-deployed activation; 80/10/5/5 funded LP allocation; equal activated-NFT collective membership replaces Power.
- A capped 1,000-NFT collection with exact 600/300/100 rarities drawn through fixed-coordinator verifiable randomness requests and ordered finalization.
- Separate 5% requested marketplace royalties, distributing actual admitted receipts at activated rarity weights 1/2/3.
- Dynamic metadata based on current attributed LP NAV, including valuation-unavailable handling and $1,000/$10,000 artwork thresholds.
- Shared physical LP custody remains per pool, with an initial single-pool intent and a 16-historical-bucket registration cap to bound global entry settlement. Future migrations reuse an existing bucket.
- Production market/native-token routing, actual VRF/bridge provider setup, authority selection, staging and independent audit remain open. The public website remains a simulation.

The following entry is preserved as historical prototype-review evidence.

# v0.2 versus the supplied prototype

This is a breaking source rewrite, not an upgrade transaction or migration of an existing deployed system. No prior live deployment is assumed.

- Kept all sixteen named modules while replacing circular fixed-constructor dependencies with a bootstrap-and-seal controller registry.
- Adopted OpenZeppelin ERC-721, SafeERC20, reentrancy protection, math and timelock primitives.
- Added typed Uniswap v4 PosM action encoding, fee collection, exact settlement, per-NFT approvals and swap callback authentication.
- Replaced ambiguous token balances with per-NFT idle principal, aggregate custody totals, funded rewards and segregated fee budgets.
- Added canonical-chain issuance restrictions, explicit migration locations, principal custody transitions, funded/replay-protected messages and retryable destination activation.
- Added reward-index checkpoints, fractional carry, ten-unit fee allocation, remote reward return accounting and a documented Power policy.
- Added oracle-relative tick calculation, swaps on deposit/top-up/compound, a post-placement deployment-utilization check, and fee collection after swaps into an existing LP.
- Implemented direct buyback/burn source with actual supply/balance checks and explicitly documented multi-hop/global-burn limitations.
- Replaced TypeScript skeletons with standard-library Python keeper/indexer implementations, durable transaction state and SQLite reorg recovery.
- Added real executable Python tests, unexecuted Foundry tests, local-only deployment source, CI/build scripts, detailed scope limitations and a security self-review.

No claims about successful Solidity compilation, real Uniswap execution, live bridging or independent audit were added.
