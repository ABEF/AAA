# Component implementation status

All 16 Solidity modules now compile and satisfy standard runtime/initcode size limits under the recorded build profile. The supplied mock-based unit/fuzz suite passes 70 tests. This does not establish full EVM branch/invariant coverage, real Uniswap/bridge integration, an independent audit, or funded-deployment approval. See [CI repair evidence](../reports/CI_REPAIR.md); the remaining qualifications below still apply.

| Contract | Current implementation | Remaining qualification |
|---|---|---|
| `ZZZVault.sol` | Non-redeemable custody; canonical-chain deposits; top-ups; idle ledger; minimum utilization; fee harvesting; compounding; replacement LPs; outbound/inbound states | Real Uniswap lifecycle, adversarial tokens/callbacks and runtime-size testing |
| `ZZZNFT.sol` | OpenZeppelin ERC-721, safe mint/transfer, owner-based economic rights | Dependency build and receiver/reentrancy EVM tests |
| `ZZZLiquidityManager.sol` | Explicit v4 mint/increase/zero-decrease collection/burn actions, per-NFT custody checks, bounded Permit2 approvals, authenticated swap callback | Full pinned-block v4 fork validation; not an arbitrary DEX adapter |
| `ZZZRewards.sol` | Funded individual/collective claims, cumulative index, fractional carry and zero-Power reserves | Collection-time economics; 32 assets; EVM invariant testing |
| `ZZZPower.sol` | Contribution-USD weights; mandatory pre-change checkpoints; hard total-weight bound | Economic formula approval; no age/rarity score or market-value rebasing |
| `ZZZFeeController.sol` | 5/3/1/1 fee-unit allocation, rounding carry, isolated reserves, remote reward budgets | Real multi-token solvency and bridge-delivery tests |
| `ZZZStrategy.sol` | Oracle-relative tick ranges, deviation/cooldown policy, existing-range compounding composition, slippage checks | Backtesting, gas, volatility and MEV analysis |
| `ZZZCompounder.sol` | Keeper-only coordinator; vault pulls and reinvests its own fee budget | Real swap/fee/rounding integration |
| `ZZZBuyback.sol` | Bounded direct buyback or direct burn; supply and balance reduction checks | No multi-hop; confirm authentic ZZZ and chain-specific burn semantics |
| `ZZZMigration.sol` | Governance proposals, delay, source exit, authenticated locations and reward paths | One-hop only; live transport/finality and recovery implementation |
| `ZZZBridgeAdapter.sol` | Source/route/nonce validation, exact funding, replay protection, typed transport interface | No production bridge-provider transport is bundled |
| `ZZZMigrationReceiver.sol` | Separate receipt, retained custody, LP activation/retry, reward delivery and acknowledgement | Destination/per-provider integration; no arbitrary refund |
| `ZZZAccessController.sol` | Timelock, fixed minimum delay, separated keeper/guardian powers, frozen module bindings | Governance/feed/provider trust remains; no general upgrade path |
| `ZZZOracle.sol` | External USD feed normalization, freshness/round checks, sequencer checks and quote conversion | Approved sources must actually exist and have the correct denomination |
| `ZZZPoolRegistry.sol` | Approved identities/tokens, bounded fee/range/deviation/slippage parameters | Eligibility is governance policy, not an automatic scam detector |
| `ZZZMigrationRegistry.sol` | Fixed pre-seal routes and token mappings; post-seal disable/re-enable | New arbitrary routes/chains intentionally prohibited |

## Off-chain components

| Component | Current implementation | Validation |
|---|---|---|
| Keeper | Dry-run default; simulations; gas/daily budget caps; encrypted external signer; durable nonce/pending state; receipt identity checks; serial execution | Mocked RPC/process tests run; no live signing or real network deployment |
| Indexer | Read-only RPC; confirmed blocks; atomic SQLite cursor/log storage; bounded reorg rollback; event decoding and NFT ownership projection | Mocked RPC/reorg tests run; no production RPC backfill/load test |

The indexer stores canonical raw events and decoded fields; it is not a complete hosted dashboard/API. Migration proposal/execution/activation/acknowledgement require deliberate operator calls; the keeper does not autonomously choose a new chain.
