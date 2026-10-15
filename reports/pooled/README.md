# Shared LP implementation and internal review

Date: 2026-10-15. Baseline: `35f1d928b12282c0f0ba8a05d9ea270219f823af`. Scope: the AAA smart contracts, keeper, event schema, production inventory gate and documentation. The user explicitly selected shared LP per pool. The separate website/server were not changed. No public-chain contracts were deployed and no transactions were signed or sent.

This is an internal engineering/security review by Codex with separate AI-agent review. It is **not an independent audit or approval for funded deployment**. Earlier per-NFT architecture and test sources are preserved in [history](../history/per-nft-tests/); earlier passing reports do not validate this rewrite.

## Result and accounting

One stable bucket owns one physical LP position per registered pool/strategy. NFTs hold canonical nonredeemable shares and retain individual funded fee balances. Harvest, compounding and rebalancing act once per bucket, without iterating over NFT holders. Contribution, custody and reward ledgers remain separate.

Paid dormant minting remains exactly 0.05 ETH and creates no LP, Power or fees. Activation requires at least $500 of net new, measured deployed LP, conservatively excluding incumbent idle and fresh compounding value. Permanent top-ups buy shares against current incumbent NAV rather than historical contributions. Zero NAV with outstanding shares, zero issuance and supply above 1e36 revert.

Entry harvests earlier fees and entry-swap fees before shares change. Existing LP quantities are valued again after balancing so their repricing stays with incumbents. Owner checkpoints precede share changes; collective checkpoints precede Power changes. The owner allocation follows bucket shares, collective rewards follow lifetime contribution Power, and only the designated 10% compounds. Donations and the other fee reserves cannot become share-purchase principal. NFT transfers preserve shares and unclaimed rights; claims work while maintenance is paused.

Whole-bucket version-3 migrations preserve canonical membership and Power, freeze new shares while scheduled/remote, and carry cumulative remote owner/collective allocations including unsent reserves. A home return cannot admit new shares or release principal again until all those old allocations are funded home. Maintenance, transfers and funded claims remain possible. Destination pools require permanent reservations; distinct buckets cannot merge implicitly. Repeated A->B->C->A->B and return/new-join/revisit scenarios pass with a real controller/router and mock provider.

The former `position(nftId)` ABI is removed. NFT consumers read `nftStatus`, `nftBucket`, `sharesOf`, `contributionUSD` and Rewards; physical custody comes from `group(bucketId)`. Maintenance IDs and fee-controller IDs are buckets. `bucketCount/bucketAt` provide bounded keeper discovery with a durable fair cursor. Legacy NFT-list configuration/state is rejected without automatically discarding pending transactions. [Full architecture](../../docs/ARCHITECTURE.md).

## Executed verification

| Check | Result | Evidence |
|---|---|---|
| Offline Solidity | 234 passed, zero failed, one intentional opt-in fork setup skip; 18 suites | [complete run](final-tests-gas.log) |
| Stateful stress | 256 runs x 256 depth = 65,536 scheduled handler calls; zero unexpected reverts; two tests passed | [command/seed](extended-invariants.json), [log](extended-invariants.log) |
| Python | 216 total; 212 portable Windows tests passed without skips; four unchanged Unix-only assertions retained for Ubuntu CI | [summary](python-windows-portable.json), [log](python-windows-portable.log) |
| Actual Uniswap dependency fork | Eight passed, zero failed/skipped, including shared-Vault entry/pricing and one-LP rebalance | [fork log](robinhood-fork-tests.log) |
| Standard EVM sizes | All 17 modules pass EIP-170/EIP-3860; Vault runtime 23,591 / initcode 24,463 bytes, runtime margin 985 | [sizes/templates](module-sizes.json), [build](final-build.log) |
| Slither 0.11.6 | 86 contracts / 102 detectors, 139 individually reviewed findings: 72 conditional false positives, 52 accepted risks, 15 informational | [raw normalized output](slither-final.json), [source-bound review](../production/slither-review.json), [log](slither-final.log) |
| Separate High/Medium review | All 83 findings reviewed individually with source identities and rationales | [review](high-medium-secondary-review.json), [notes](high-medium-secondary-review.md) |
| Retained Forge warnings | 41 casts and six test-only unchecked transfers reviewed; no suppressions added | [47 dispositions](forge-lint-review.json) |
| Production manifest | Schema 3 requires shared-pool identity and reviewed source/destination reservations; supplied template remains blocked | [blocked result](production-config-check.json) |

Fuzz tests use 1,000 cases each. The local stateful handler covers mint, activation, top-up, harvest, claim, transfer, pause, donations, compounding and rebalance with real custody/reward modules behind a fake venue. Ineligible calls may return without changing state; handler-call count is not a count of successful user transactions. Multi-chain stateful testing with an actual SDK remains absent.

The pinned Robinhood fork uses block 88,544,093 / hash `0xc44dc8c95c6011b991312179f532935c2d94e4f21b84899d23896fd0fe01d490`, checks eight deployed runtime identities, and exercises actual PosM/PoolManager/Permit2/StateView, ZZZ and WETH. Adapter/shared-Vault operations use a DIFFERENT hookless pool initialized only on the fork, synthetic $1 feeds and a mock access controller. The requested native-ETH/Pons pool is verified and rejected; this is not its reward integration. Archive access is read-only, paced and uncached on disk. New entry tests explicitly verify post-swap incumbent LP repricing and exclusion of historical fees from new shares.

The one-pool rebalance workload measured **824,795 execution gas at 1, 100 and 1,000 NFTs**, with one replacement LP in every case. [All workloads](gas-measurements.json). Venue/policy/tokens are mocks; fixture construction, intrinsic/calldata gas and refunds are excluded. These values establish local scaling, not real Uniswap execution costs or profitability.

The final compiler remains Solidity 0.8.26 / Cancun / via IR / optimizer runs 1 / Yul optimizer disabled. No production EVM size limit was raised, no library delegatecall or extra authority was introduced. Shared private guards, balance reads and maintenance helpers remove duplicated code. The obsolete per-NFT physical-LP getter was replaced by explicit NFT/bucket reads. Deployment headroom and real execution cost still require independent review.

## Remaining economic and release gates

- Sub-ten-unit fee dust settles entirely to incumbent owner rewards before membership changes/departure. This prevents later shares receiving old dust but is a deliberate exception to exact 50/30/10/10 splitting. Up to nine RAW units need not be economically negligible for a low-decimal/high-unit-value asset; holders can trigger settlement through top-ups. Token admission must review monetary value and frequency, or redesign rounding before admitting exposed assets.
- The 30% collective policy uses Power at funded publication/delivery time, rather than historical swap-time weights. Timing, permanently depreciated contributions and contributions to other buckets need economic review.
- A delayed/lost remote reward transport can block new contributions and another outbound release after return. There is no authority bypass that discards old owner liabilities. Actual provider authentication, backing, retries and operational recovery remain unproved by mocks.
- The selected Robinhood ZZZ/native-ETH Pons market has zero conventional LP fees. Native/hook settlement and the deferred Pons-share/new-pool reward choice remain unsupported; no hypothetical 0.30% revenue is assumed here.
- Production ZZZ valuation/outage policy, recipient/authority wallets, real keeper/signing and multi-chain staging, destination code/authority review, independent audit and remediation remain required. The example production inventory intentionally fails. Publication does not authorize funded use.

All static-analysis dispositions are conditional on the documented fixed module graph, admitted ordinary ERC-20 behavior, defensible oracle configuration and authenticated provider/destination behavior. Coverage and passing tests are evidence within that scope, not proof that every possible sequence or future chain/provider is safe.
