# Release gate — NOT APPROVED

Every item below must be closed with evidence, not assumed from the presence of contract files. The [current reward-funding review](../reports/reward-funding/README.md) records development checks separately from the [earlier readiness review](../reports/PRODUCTION_READINESS.md) and historical reports. Checked development items have the scope stated below; the overall release remains blocked.

## Toolchain and reproducibility

- [x] Resolve/install locked npm/forge-std dependencies; hash-pin the separate Slither tool environment, including transitives.
- [x] Pin forge-std and CI actions to reviewed immutable hashes; reject modified forge-std checkouts and missing npm lockfiles.
- [x] Compile every contract, test and deployment script with Solidity 0.8.26/Cancun without compiler errors; retain Foundry lint output. Independent compiler/profile review remains required.
- [ ] Check mainnet runtime/initcode size and gas constraints without artificially raising production limits.
- [x] Run every offline Foundry unit/fuzz test and retain output; explicitly enable and separately report the actual network fork suite.
- [x] Add/run local stateful EVM invariants against an independent integer accounting model; retain handler counts/seed. This does not cover every provider or cross-chain sequence.
- [x] Run Slither 0.11.6 and individually triage its complete 160-finding output after adding external funding; a separate internal review covers all 91 High/Medium findings. CI checks source identity and review coverage. No independent audit is implied.

## Real protocol integration

- [ ] Pinned-block fork tests against actual supported PosM/PoolManager/Permit2/StateView deployments: mint, increase, collect, close, exact settlement, swap callback, permissions, donations and approval resets.
  Ordinary deployed-dependency operations, approval resets, shared entry/upkeep and wrapped-native funding passed nine fixed-block fork tests using a different hookless pool. Selected native/Pons pool integration, full adversarial dependency tests and production valuation remain incomplete.
- [ ] Fee/principal segregation across swaps that themselves earn fees; rounding and all-asset solvency after arbitrary operation sequences.
- [ ] Actual malicious-token and callback adversaries: additive/subtractive taxes, rebases, blacklists, false return values, recipient reentrancy and oracle manipulation.
- [ ] Actual NFT receiver callbacks, transfer/claim races and canonical-chain restrictions.
- [ ] Review exactly 0.05 ETH dormant issuance, immutable mint-proceeds routing, atomic payout/issuance failure, and owner activation with at least $500 actually deployed LP; prove mint income remains separate from principal, Power, and rewards.
- [ ] Verify reference feeds, decimals, denomination, heartbeat, sequencer behavior, price bounds and unsupported asset rejection on every chain.
- [ ] Benchmark one shared pool with 1/100/1,000+ NFT shareholders and all 32 reward assets; verify maintenance does not loop over NFTs.
  Candidate cold-execution workloads now cover 1/100/1,000 NFTs and 32 funded assets. Real AMM/network costs, strategy backtesting and economic viability are still unapproved.
- [ ] Validate the real ZZZ burn function and its global/cross-chain semantics; implement multi-hop routes or restrict supported fee assets honestly.

## Cross-chain security and scope

- [x] Implement a fixed router with append-only policies for future unknown providers and chains; test pending old-provider receipts, pin drift, exact funding and cross-provider replay. These tests use explicit mock SDK boundaries.
- [ ] Select, implement and independently review production `IZZZTransportProvider` SDK wrappers and their actual channels/backing.
- [ ] Verify append-only route identity, equivalent assets/identical decimals/nominal units, and counterpart code/proxy authorities for initial routes and every timelocked post-seal addition.
- [ ] Review governance notice/onboarding powers and canonical remote-only graph approval; a timelock does not prove that future code preserves permanent-principal custody. Confirm fixed module bindings and fixed router and append-only transport-policy compatibility with future routes. Review each wrapper and channel before timelocked enablement; an initially empty router may seal but cannot send.
- [ ] End-to-end real-provider canonical-to-satellite, onward, canonical-return, and revisit tests: delayed, duplicated, reordered, forged, underfunded and partially failed deliveries; pauses; provider upgrades; reorgs/finality failures.
- [ ] Validate v3 bucket/canonical identity, asset provenance and epochs, immutable accepted ACK snapshots, separate source-completion/home-location purposes, strictly ordered canonical locations and retry, absent-hop satellite epochs, and no NFT remint or Power addition on import.
- [ ] Reconcile historical reward paths and funded legacy reserves after custody leaves; test permanent token provenance, old-pool budgets, satellite migration dust, and rewards before/after each ACK.
- [ ] Specify provider-authenticated cancellation/refund/retry behavior that never creates user/admin principal redemption.
- [ ] Approve the implemented repeated equivalent-asset custody scope and its governance trust. Keep satellite user deposits, arbitrary asset conversion, NFT-chain moves, and cross-chain holder top-ups disabled unless separately implemented and reviewed.

## Economic and operating approval

- [ ] Approve lifetime-contribution Power, continued remote/in-flight eligibility, settlement-time collective rewards and 32-asset limit.
- [ ] Independently review creator-payment receivers, optional one-for-one native wrapping, exact funds, all-inbox pre-membership synchronization and maximum-16 gas costs. Approve processing-time share/Power weights, dust policy and discretionary payment terms without inferring a creator percentage. Verify the production receiver inventory and dependency outage behavior.
- [ ] Implement and review selected Robinhood native-ETH/Pons-hook LP custody, or explicitly exclude it. Its 0% core LP fee and recipient-based hook revenue do not establish proportional PoPL rewards; separate creator-payment intake does not make the pool adapter compatible.
- [ ] Model harvest/top-up timing, manipulated valuations, permanently depreciated positions and token eligibility attacks against collective rewards.
- [ ] Review timelocked governance/feed powers: non-redeemability does not eliminate governance-mediated economic loss.
- [ ] Backtest ranges/cooldowns, slippage, churn, rebalancing costs and MEV. Do not advertise guaranteed yield or protected principal.
- [ ] Review keeper signer isolation, actual `cast` CLI behavior, RPC trust, L2 fee estimates and ambiguous nonce recovery on a testnet.
- [ ] Reproduce indexer backfill/reorg handling against actual RPC providers and confirm alerting/recovery runbooks.
- [ ] Complete an independent external security audit and remediation verification, then a separately scoped deployment/configuration review.
- [ ] Use limited testnet exposure and carefully staged production limits only after the preceding gates close.

No signature, badge or status in this repository waives these gates. No live funds were deployed by this work.

- [ ] Independently audit shared NAV issuance, incumbent LP repricing, entry-swap fees, raw-unit dust exceptions, share fractions and funded liabilities.
- [ ] Exercise whole-pool migrations and cumulative remote-fee drain barriers with an actual provider; reserve each destination before route approval.

- [ ] Value nine raw units of every admitted fee token and approve the holder-triggerable dust-to-owner policy and top-up frequency; reject economically material rounding exposure or redesign it before admission.
