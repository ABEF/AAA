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
