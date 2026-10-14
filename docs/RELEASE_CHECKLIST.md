# Release gate — NOT APPROVED

Every item below must be closed with evidence, not assumed from the presence of contract files.

## Toolchain and reproducibility

- [ ] Resolve/install exact dependencies on a networked development machine; verify package contents and lockfiles.
- [ ] Pin upstream Git revisions and CI actions to reviewed immutable hashes.
- [ ] Compile every contract, test and deployment script with Solidity 0.8.26/Cancun; fix all errors/warnings and review IR/optimizer choices.
- [ ] Check mainnet runtime/initcode size and gas constraints without artificially raising production limits.
- [ ] Run every Foundry unit/fuzz test; retain outputs and failing seeds, including the tests provided here.
- [ ] Add/run stateful EVM invariants and differential tests; Python models do not satisfy this gate.
- [ ] Run reviewed static analyzers and manually triage their full output.

## Real protocol integration

- [ ] Pinned-block fork tests against actual supported PosM/PoolManager/Permit2/StateView deployments: mint, increase, collect, close, exact settlement, swap callback, permissions, donations and approval resets.
- [ ] Fee/principal segregation across swaps that themselves earn fees; rounding and all-asset solvency after arbitrary operation sequences.
- [ ] Actual malicious-token and callback adversaries: additive/subtractive taxes, rebases, blacklists, false return values, recipient reentrancy and oracle manipulation.
- [ ] Actual NFT receiver callbacks, transfer/claim races and canonical-chain restrictions.
- [ ] Verify reference feeds, decimals, denomination, heartbeat, sequencer behavior, price bounds and unsupported asset rejection on every chain.
- [ ] Benchmark 1/100/1,000+ NFT positions and all 32 reward assets; decide whether independent LPs are economically viable.
- [ ] Validate the real ZZZ burn function and its global/cross-chain semantics; implement multi-hop routes or restrict supported fee assets honestly.

## Cross-chain security and scope

- [ ] Select, implement and independently review a production `IZZZTransport` integration.
- [ ] Verify immutable route identity, token equivalence/decimals and remote counterpart code/proxy authorities before sealing.
- [ ] End-to-end two-chain tests: delayed, duplicated, reordered, forged, underfunded and partially failed deliveries; ACK retries; rewards before/after ACK; pauses; bridge/provider upgrades; reorgs/finality failures.
- [ ] Specify provider-authenticated cancellation/refund/retry behavior that never creates user/admin principal redemption.
- [ ] Explicitly approve one-hop-only migration, no return/top-up flow and no arbitrary future route additions; redesign before sealing if those restrictions are unacceptable.

## Economic and operating approval

- [ ] Approve lifetime-contribution Power, continued remote/in-flight eligibility, settlement-time collective rewards and 32-asset limit.
- [ ] Model harvest/top-up timing, manipulated valuations, permanently depreciated positions and token eligibility attacks against collective rewards.
- [ ] Review timelocked governance/feed powers: non-redeemability does not eliminate governance-mediated economic loss.
- [ ] Backtest ranges/cooldowns, slippage, churn, rebalancing costs and MEV. Do not advertise guaranteed yield or protected principal.
- [ ] Review keeper signer isolation, actual `cast` CLI behavior, RPC trust, L2 fee estimates and ambiguous nonce recovery on a testnet.
- [ ] Reproduce indexer backfill/reorg handling against actual RPC providers and confirm alerting/recovery runbooks.
- [ ] Complete an independent external security audit and remediation verification, then a separately scoped deployment/configuration review.
- [ ] Use limited testnet exposure and carefully staged production limits only after the preceding gates close.

No signature, badge or status in this repository waives these gates. No live funds were deployed by this work.
