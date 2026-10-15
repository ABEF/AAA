# Release gate — NOT APPROVED

The website-alignment revision changes economics, membership, NFTs, royalty accounting and metadata. Historical279test/160finding reports validate earlier sources only. Record fresh evidence in [website alignment](../reports/website-alignment/README.md); do not treat its internal checks as an independent audit.

## Source, toolchain and economics

- [ ] Reproduce all current Solidity/Python tests on supported Ubuntu, retaining exact source revision, compiler settings and full logs.
- [ ] Compile every contract/test/script and check normal runtime/initcode limits and current gas; small Vault/FeeController margins require explicit review.
- [ ] Run fresh pinned Slither and individually triage every finding against current source hashes, with separate internal review and independent external audit still required.
- [ ] Verify0.05ETHmint proceeds remain separate,1,000NFTcap and exact600/300/100quota conservation, atomic failure and no reroll/trait override.
- [ ] Verify$100marginal actually deployed activation, incumbent NAV pricing, entry-swap fees, callbacks, pending/dust barriers, top-ups and nonredeemability.
- [ ] Verify80/10/5/5funding,90%remote delivery, equal collective membership and old-index/fractional solvency across transfers/entries/migrations.
- [ ] Review19raw-unit dust economics per asset and holder-triggerable entry frequency, low decimals and high unit values.

## NFT randomness, royalties and metadata

- [ ] Independently verify actual supported proof-verifying coordinator code/key/subscription/confirmations/gas and service availability on the deployment chain. An ABI or mock is not verification.
- [ ] Stage real requests, out-of-order callbacks, strict mint-order reveal, subscription outages, reorg/finality and permanent early-request blocking recovery. No cancellation/reroll/admin bypass exists.
- [ ] Verify canonical sealing rejects missing randomness configuration; verify content root and every artwork/metadata path against an independently reviewed immutable catalog.
- [ ] Review5%ERC2981request and100%funded holder redistribution in a separate immutable ETH/ERC20 ledger at activated rarity weights1/2/3. Marketplace payment remains voluntary.
- [ ] Inventory all royalty assets and review exact transfers, rebases, mutable authority, prefund/zero-member quarantine, pending settlement, claim callbacks, fractional/global dust, transfer rights and activation outage behavior.
- [ ] Review live oracle/NAV thresholds, downward evolution, remote/stale unavailable labels and marketplace/indexer ERC4906refresh behavior; claims/migration must not depend on metadata price reads.

## Market, valuation and operating integration

- [ ] Implement/review the selected native-ETH/Pons-hook LP market, or explicitly exclude it; creator funding does not make its adapter compatible.
- [ ] Supply reviewed feeds, decimals, denomination, heartbeat/sequencer/outage policy and admitted tokens on every chain.
- [ ] Review ZZZ/USDC activation routing if the target pool has different assets; current arbitrary-input routing is absent.
- [ ] Stage actual Uniswap swaps/entry/maintenance, malicious token/callback behavior, exact approvals/settlement, stale prices, donations and failures.
- [ ] Benchmark1/100/1,000NFTs and maximum assets; prove upkeep scales by pool. Backtest range/cooldown/slippage, impermanent loss, MEV and real operating cost.
- [ ] Review all creator inboxes, optional native wrappers, discretionary payment terms, global synchronization availability and maximum16inbox costs.
- [ ] Review keeper keystore isolation, nonce/receipt recovery, actual RPC/signer operation, indexer backfill/reorgs, alerts and supported Unix state locking.

## Migration, governance and independent release review

- [ ] Independently review real provider SDK wrappers, backing/equivalent token semantics, channels, finality, exact funding and recovery.
- [ ] Stage canonical→satellite→satellite→home→revisit with actual providers, duplicate/reordered/forged/underfunded receipts, ACK epochs, pauses, old-policy and historical reward paths.
- [ ] Verify destination reservations, frozen canonical shares/membership, no remint/principal refund, legacy liability barriers, and governance trust for every new destination.
- [ ] Select and verify multisig/keeper/guardian/mint-recipient authorities, fixed timelock and module bindings; prohibit mint/LP/royalty receiver collisions.
- [ ] Complete an independent external security audit, remediation verification and separate deployment/configuration review, then limited staging with approved limits.

Schema4production inventory must include current economics, NFT helper/randomness/asset observations and authentic release/staging evidence. Its ready state is offline consistency only; it never authorizes deployment, sealing, signing or real funds.
