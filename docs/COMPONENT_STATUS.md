# Component implementation status

The current development candidate includes paid dormant mint/activation, timelocked future-route onboarding, and repeated custody migration. Current compiler, size-gate, and test evidence is recorded in [the implementation update](../reports/IMPLEMENTATION_UPDATE.md). [Earlier CI repair evidence](../reports/CI_REPAIR.md) describes its own earlier revision. These checks do not establish full EVM branch/invariant coverage, real Uniswap/bridge integration, an independent audit, or funded-deployment approval. The remaining qualifications below still apply.

The [current readiness review](../reports/PRODUCTION_READINESS.md) supersedes those earlier verification counts: local accounting invariants, static-analysis triage, real Uniswap dependency fork flows, a 23,662-byte vault and collection/32-asset gas benchmarks are now present. It does not establish full coverage, selected Pons-market support, a live bridge or an independent audit.

| Contract | Current implementation | Remaining qualification |
|---|---|---|
| `ZZZVault.sol` | Exactly 0.05 ETH dormant mint; immutable isolated proceeds recipient; owner activation with at least $500 actually deployed LP; permanent top-ups; idle ledger; harvesting/compounding/replacement; repeated outbound/inbound states; private helper refactor saves 777 bytes | Full selected-market/provider lifecycle; independent review of 914-byte runtime margin and live gas economics |
| `ZZZNFT.sol` | OpenZeppelin ERC-721, safe mint/transfer, owner-based economic rights; imports retain the canonical NFT | Stateful receiver/reentrancy and integration coverage; no NFT-chain migration |
| `ZZZLiquidityManager.sol` | Explicit v4 mint/increase/zero-decrease collection/burn actions, per-NFT custody checks, bounded Permit2 approvals, authenticated swap callback; ordinary deployed-dependency flows passed a pinned fork | Native currency/Pons hook support absent; real pricing/adversarial integration and deployment review remain |
| `ZZZRewards.sol` | Funded individual/collective claims, cumulative index, fractional carry and zero-Power reserves; integer-ledger EVM invariants and 32-funded-asset benchmark | Collection-time economics approval; maximum-asset live operating costs and full multi-chain invariant scope |
| `ZZZPower.sol` | Contribution-USD weights; mandatory pre-change checkpoints; hard total-weight bound | Economic formula approval; no age/rarity score or market-value rebasing |
| `ZZZFeeController.sol` | 5/3/1/1 allocation, rounding carry, isolated reserves; immutable remote asset provenance; funded satellite dust; old remote budgets deliverable after custody leaves | Real multi-token solvency, provider delivery and long-operation invariant coverage |
| `ZZZStrategy.sol` | Oracle-relative tick ranges, deviation/cooldown policy, existing-range compounding composition, slippage checks | Backtesting, gas, volatility and MEV analysis |
| `ZZZCompounder.sol` | Keeper-only coordinator; vault pulls and reinvests its own fee budget | Real swap/fee/rounding integration |
| `ZZZBuyback.sol` | Bounded direct buyback or direct burn; supply and balance reduction checks; actual Robinhood ZZZ local burn tested on fork | No multi-hop; wrapped/global cross-chain supply and real buyback pricing/routes still require review |
| `ZZZMigration.sol` | Repeated governance proposals and two-day move delay; frozen v2 departure identities; custody epochs; ordered canonical location history; historical reward paths; onward/return imports without new Power | Provider finality/recovery, destination review, and multi-chain adversarial/stateful integration |
| `ZZZBridgeAdapter.sol` | V2 source/route/nonce validation, exact funding, replay protection, typed transport interface with immutable endpoint | No production bridge-provider transport is bundled |
| `ZZZMigrationReceiver.sol` | Separate receipt/activation/retry; immutable accepted snapshots; distinct previous-source and canonical-location ACKs; canonical asset-order handling | Destination/per-provider integration and ordered delivery recovery; no arbitrary refund |
| `ZZZAccessController.sol` | Timelock, fixed minimum delay, separated keeper/guardian powers, frozen module bindings | Governance/feed/provider trust remains; no general upgrade path |
| `ZZZOracle.sol` | External USD feed normalization, freshness/round checks, sequencer checks and quote conversion | Approved sources must actually exist and have the correct denomination |
| `ZZZPoolRegistry.sol` | Approved identities/tokens, bounded fee/range/deviation/slippage parameters | Eligibility is governance policy, not an automatic scam detector |
| `ZZZMigrationRegistry.sol` | Append-only route identities; timelocked post-seal new-route onboarding; canonical remote-only graph edges; disable/re-enable | Governance must review future destinations/token/provider semantics; notice alone cannot guarantee permanent custody |

## Off-chain components

| Component | Current implementation | Validation |
|---|---|---|
| Keeper | Dry-run default; simulations; gas/daily budget caps; isolated external signer; durable nonce/pending state; transaction/receipt identity checks; serial execution; legacy reward routes after LP departure; valid positional cast calldata | RPC/process and pinned CLI parsing tests run; no live signing, provider recovery rehearsal or deployment |
| Indexer | Read-only RPC; confirmed blocks; atomic SQLite cursor/log storage; bounded reorg rollback; event decoding and NFT ownership projection | Mocked RPC/reorg tests run; no production RPC backfill/load test |

The indexer stores canonical raw events and decoded fields; it is not a complete hosted dashboard/API. Migration proposal/execution/activation/acknowledgement require deliberate operator calls; the keeper does not autonomously choose a new chain.

The requested Robinhood ZZZ/native-ETH hooked pool remains unsupported by the current ERC20/ERC20 hookless adapter. Its project reward integration is undecided. Repeated migration supports equivalent assets in nominal units, not unrelated asset conversion, satellite user top-ups, or moving the economic NFT off its canonical chain.
