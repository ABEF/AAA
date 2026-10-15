# Release checklist - NOT APPROVED

Updated 2026-10-15. Checked development items identify implemented code and recorded internal evidence; they do not approve deployment or real funds. Unchecked production gates require actual integration, release-specific evidence and independent qualification. The [Implemented / Todo checklist](IMPLEMENTATION_STATUS.md) records feature status. Current evidence is in [release hardening](../reports/release-hardening/README.md). Earlier artwork, website-alignment and other reports retain their exact source scope.

## Completed development work

- [x] Implement the accepted mint, activation, shared-pool, 80/10/5/5, equal collective membership, rarity, artwork and separate royalty rules. See the [component map](COMPONENT_STATUS.md) for source boundaries; selected-market compatibility remains separate.
- [x] Add permissionless metadata notifications for at most 50 inclusive mint ordinals, emitting each actual hashed token ID without price reads or custody changes. Targeted Solidity tests cover bounds, atomic failure, pause, transfers and valuation outages.
- [x] Add an optional confirmed-block metadata watcher using the keeper's existing simulation, serial signer, budgets and pending recovery. It is disabled by default; initial observation and successful notification remain distinct states.
- [x] Record a read-only [selected-market feasibility review](../reports/release-hardening/selected-market-review.md), including two-provider fixed-block observations and the required native settlement/accounting design. This is not a compatible adapter or an independent audit.
- [x] Run fresh pinned internal Slither against the metadata source change: 179 findings, individually reviewed with zero unresolved review entries. Retain source/configuration hashes and coverage checks; independent audit remains open.
- [x] Run the complete local offline suite: 342 Solidity passes, one expected fork setup skip, and 372 portable Python passes; four unchanged Unix-only cases remain for Ubuntu. The focused keeper run passes 109 tests, with separate internal execution of ten regression cases.
- [x] Check all 20 normal runtime/initcode objects and the 318,466-gas cold 50-token notification workload. Constructor-argument allowance, actual-venue gas and the Vault's 169-byte runtime margin still need release qualification.

## Source, toolchain and economics

- [ ] Reproduce all Solidity/Python tests for the final frozen production release on supported Ubuntu, retaining exact source revision, compiler settings and full logs. Candidate CI and earlier green CI for `5febe70` do not validate future source changes.
- [ ] Compile every contract/test/script and check normal runtime/initcode limits and current gas; small Vault/FeeController margins require explicit review.
- [ ] Independently review the final source-bound Slither triage and accepted risks, refreshing analysis if source changes. Completed internal triage does not close the external audit gate.
- [ ] Independently verify isolated 0.05 ETH mint proceeds, the 1,000-NFT cap, exact 600/300/100 quotas, atomic failure and no reroll/trait override.
- [ ] Independently verify $100 marginal actually deployed activation, incumbent NAV pricing, entry-swap fees, callbacks, pending/dust barriers, top-ups and nonredeemability.
- [ ] Independently verify 80/10/5/5 funding, 90% remote delivery, equal collective membership and index/fractional solvency across transfers, entries and migrations.
- [ ] Review the economic value of at most 19 raw units settled before membership changes, asset decimals and holder-triggerable entry frequency.

## NFT randomness, royalties and metadata

- [ ] Independently verify actual supported proof-verifying coordinator code/key/subscription/confirmations/gas and service availability on the deployment chain. An ABI or mock is not verification.
- [ ] Stage real requests, out-of-order callbacks, strict mint-order reveal, subscription outages, reorg/finality and permanent early-request blocking recovery. No cancellation/reroll/admin bypass exists.
- [ ] Verify canonical sealing rejects missing randomness configuration; verify content root and every artwork/metadata path against an independently reviewed immutable catalog.
- [ ] Independently review the 5% ERC-2981 request and 100% eligible royalty redistribution in the separate immutable ETH/ERC20 ledger at activated rarity weights 1/2/3. Marketplace payment remains voluntary.
- [ ] Inventory all royalty assets and review exact transfers, rebases, mutable authority, prefund/zero-member quarantine, pending settlement, claim callbacks, fractional/global dust, transfer rights and activation outage behavior.
- [ ] Configure OpenSea creator earnings to the actual `NFT.royaltyRewards()` helper at 5%, verify collection-administration access and each admitted payout asset, and stage a paid sale through receipt, weighted claim and NFT transfer. The current contract requests optional earnings; it does not implement ERC-721-C enforcement.
- [ ] Stage live oracle/NAV thresholds, downward evolution and remote/stale unavailable labels; claims and migration must remain independent of metadata price reads.
- [ ] Stage the implemented watcher with actual feeds, reviewed NFT runtime pins, RPC limits, confirmation recovery and gas budgets. Publish/pin the complete 2,784-state artwork manifest and independently verify its root, every path and actual marketplace rendering/ERC-4906 cache refresh.

## Market, valuation and operating integration

- [ ] Implement and independently review the selected native-ETH/Pons-hook LP market, or explicitly exclude it. Keep current rejection guards until complete; creator funding does not make custody compatible.
- [ ] Supply reviewed feeds, decimals, denomination, heartbeat/sequencer/outage policy and admitted tokens on every chain.
- [ ] Review ZZZ/USDC activation routing if the target pool has different assets; current arbitrary-input routing is absent.
- [ ] Quote and test enough gross input to produce at least $100 net deployed LP after execution costs/slippage; validate any live wallet bulk-claim approach against the single-NFT/single-asset claim ABI.
- [ ] Stage actual Uniswap swaps/entry/maintenance, malicious token/callback behavior, exact approvals/settlement, stale prices, donations and failures.
- [ ] Qualify gas for 1/100/1,000 NFTs and maximum actual assets/inboxes; prove upkeep scales by shared pool. Backtest range, trigger, cooldown, slippage, impermanent loss, MEV and operating cost. Production strategy parameters remain unset.
- [ ] Review creator inboxes, optional wrappers, discretionary payment terms, processing-time eligibility and maximum-16-inbox costs. Creator payment frequency and percentage remain undecided.
- [ ] Stage keeper keystore isolation, nonce/receipt recovery, RPC failover, budgets, indexer backfill/reorgs, alerts and Unix state locking. The supplied systemd unit defaults to dry run.
- [ ] Integrate actual wallet transactions and confirmed website balances/history, including the separate royalty ledger. Review any bulk approach against today's single-NFT/single-asset claim entrypoints.

## Migration, governance and independent release review

The user has not selected production governance, guardian, keeper or mint-recipient addresses and explicitly requested leaving these gates open. Do not substitute example addresses or infer deployment authorization.

The provider/delivery gates apply before enabling real migration. An explicitly reviewed migration-disabled initial launch may instead satisfy the empty-policy/route requirements in [operations](OPERATIONS.md#migration-disabled-initial-launch); governance, ordinary custody, audit and staging gates still apply.

- [ ] Independently review real provider SDK wrappers, backing/equivalent token semantics, channels, finality, exact funding and recovery.
- [ ] Stage canonical -> satellite -> satellite -> home -> revisit with actual providers, duplicate/reordered/forged/underfunded receipts, ACK epochs, pauses, old-policy and historical reward paths.
- [ ] Verify destination reservations, frozen canonical shares/membership, no remint/principal refund, legacy liability barriers, and governance trust for every new destination.
- [ ] Select and verify multisig/keeper/guardian/mint-recipient authorities, fixed timelock and module bindings; prohibit mint/LP/royalty receiver collisions.
- [ ] Complete an independent external security audit, remediation verification and separate deployment/configuration review, then limited staging with approved limits.

The schema-4 production inventory must include current economics, NFT helper/randomness/asset observations and authentic release/staging evidence. Its blocked state is intentional; an offline consistency pass never authorizes deployment, sealing, signing or real funds.
