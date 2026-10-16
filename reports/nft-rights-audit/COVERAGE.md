# Economic-rights coverage map

This is a functional coverage map, not a statement/branch coverage percentage.
Executed counts, seeds and source bindings are in the verification report.
All new Solidity scenarios use explicit test-only dependencies where noted.

| Requirement | Primary suites | What is checked / limits |
|---|---|---|
| Canonical identity, quotas and one shared LP | `CollectionScale`, `NFTMetadata`, `PooledEntry` | 1,000 hashed IDs, separate ordinal mapping, exact 600/300/100 revealed quotas, unchanged immutable traits, one shared bucket; VRF service is mocked. |
| Current-owner claims and transfer ordering | `NFTOwnershipRights`, `ClaimRouter`, `NFTRoyalties`, `PooledRewards` | Approved operators cannot claim; successive transfers preserve unclaimed balances; former owners rejected; claim-before-sale and sale-before-claim outcomes. |
| Contract recipients | `NFTOwnershipRights`, `ClaimRouter`, `OracleAndTransfers` | New receiver claims during ERC721 callback; rejection rolls back ownership and payouts; reentry, native refund, failed payout and callback transfer between batch entries. |
| Complete funded allocations | `CollectionScale`, `RewardsAndFees`, `PooledRewards`, `GlobalMembershipDust`, `ExternalRewards` | 80/10/5/5, bucket-proportional individual / equal collective, repeated receipts, fractions, sub-20-unit incumbent dust, entrants excluded from locally pending receipts. |
| Independent royalties | `CollectionScale`, `NFTRoyalties`, `NFTRightsInvariants` | Actual receipts, 1/2/3 weights, shared LP/royalty currency in separate ledgers, native and 6-decimal assets, prefund quarantine, sticky eligibility, no repeat claims. |
| All-NFT payout exercise | `CollectionScale` | 1,000 activated NFTs, 991 initial owners, ten LP contribution sizes, five streams claimed by every NFT, half through router / half directly, transfers with every stream outstanding. Aggregate fixture work is not a single transaction gas benchmark. |
| Principal and shares | `VaultAccounting`, `PooledEntry`, `PooledSecurity`, `ProductionInvariants` | Donations excluded, exact idle attribution, post-fee NAV share pricing, compounding does not issue shares, rebalance replaces venue LP without replacing NFT identity. |
| Real burn path | `BuybackExecution` | Real Buyback/FeeController/Rewards/Oracle/Strategy/LiquidityManager; direct burn and direct approved-pair swap; measured supply reduction, exact reserve consumption, donations/allowances isolated, 1,000 fuzz inputs. Share ledger, tokens, authority and v4 settlement are fixtures. |
| Failed buyback | `BuybackExecution` | Swap/slippage/feed/deadline/role/pause failure, wrong/disabled pool, partial/no-op/reverting burn, input transfer failure, pre/post-swap deviation, reentry, atomic ledger/custody rollback, retry and unrelated claims. |
| Stateful combined rights | `NFTRightsInvariants` | Eight NFTs, 11 bounded handler selectors, both LP assets and native/6-decimal royalties, activation/top-ups, transfers, pause, maintenance and direct/mixed claims; identity, funding, weights and quarantine. Handler calls can legitimately be no-ops. Conservation is not an independent randomized fairness oracle. |
| Activation source and execution limits | `ActivationEntry`, `AtomicActivationIntegration`, `ActivationAssets`, `EntryExecutionBudget`, `VaultAccounting` | Original-source $100 gross / 99% deployed rule, callback boundaries, disabled/re-enabled assets, exact ingress and conversion context; actual production route/price qualification remains open. |
| Population and multi-dimension gas | `CollectionScale`, `ProductionGas`, `ClaimRouter`, `CombinedCapacityGas`, `BucketCapacity` | Individual operations at 1 vs 1,000 NFTs; bounded 32 mixed claims; separate four-bucket / 32 LP-asset / 17 royalty-slot fixture. No universal production-token/venue gas guarantee. |
| Roles, seal and configuration | `AccessController`, `BridgeSecurity`, `BridgeRouterSecurity`, Python production-config tests | Timelock/guardian/keeper boundaries, immutable bindings, invalid configuration rejection. Actual production authorities are unset. |
| Parking and remote rights | `CustodyParking`, `ParkedRewards`, `ReceiverAndRemoteFees`, `MultiHopMigration`, `FutureChainMigration`, `ReservationCapacity` | Current-owner funded claims survive custody states; snapshots, backing, nonce/epoch/replay guards, old receipt paths. Reservation-capacity regression proves an unresolved blocker, not safe bridging. |
| Token/feed failures | `OracleAndTransfers`, `NativeWrapperPolicy`, `SequencerPolicy`, `NFTOwnershipRights`, `NFTRoyalties` | Exact transfers, stale/deviating prices, wrapper policy, unsupported/taxed/rebasing assets, admitted broken royalty token blocks new activation while healthy claims remain available. |
| Operations / frontend API | Python suites and existing keeper process receipts | Read/unsigned-intent validation, history, bounded RPC, journal/recovery, locked snapshots and monitoring. Prior Ubuntu/process rehearsals retain their original source scope. No live website signing, marketplace payment or public-chain deployment is implied. |

## Deliberate boundaries

- There is no deactivation API; no test should invent one. Market-value changes
  affect artwork, not previously established reward eligibility.
- Transactions are ordered. A marketplace snapshot cannot reserve a seller's
  unclaimed fees; an atomic minimum-balance purchase condition is not implemented.
- The selected Pons pool's creator revenue is funded separately from conventional
  LP fees. Mock fee receipts do not prove creator payment terms or execution.
- The 32-operation full-population benchmark spans 16 NFTs and two revenue assets
  (LP token0 and native royalties), not 32 different token implementations.
- Gas deltas exclude intrinsic/calldata gas and refunds. The aggregate setup and
  1,000-claim correctness scenario deliberately pauses gas metering.
- No coverage percentage, formal proof, independent audit, universal external
  recovery, economic return or production readiness is claimed.
