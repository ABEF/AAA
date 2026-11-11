# Assigned contract finding IDs

All60 rows are individually reassessed in [FINDINGS.json](FINDINGS.json). This index is navigation, not a closure table.

| ID | Original claim | Current Todo IDs |
| --- | --- | --- |
| historical/FB-01 | Complete unsigned activation preparation and actual marginal LP | `activation-quotes`, `activation-assets`, `reviewed-contribution-policy` |
| historical/FB-15 | Same-chain lifecycle and complete predecessor claim continuity | `security-chain-recovery` |
| historical/FB-22 | Holder escrow compatibility preflight | `holder-preflight`, `security-chain-recovery` |
| historical/HC-01 | Permanent four-bucket reservation must count unused destinations before capacity is consumed | `shared-custody`, `destination-slots` |
| historical/HC-02 | Immediate governance is an accepted authority model, not a remaining zero-delay timelock feature | `immediate-governance`, `security-governance`, `authorities-prices` |
| historical/HC-03 | One immutable ZZZ identity must bind contribution, native pool admission, buyback and holder return before seal | `lp-only-simplification`, `shared-custody`, `creator-market-controls` |
| historical/HC-05 | Different-pair composition epochs and issuer-token executors are not current release features | `lp-only-simplification`, `shared-custody`, `creator-market-controls` |
| historical/HC-07 | Preserving a contract owner address does not guarantee successor NFT compatibility | `security-chain-recovery`, `holder-preflight`, `destination-slots` |
| historical/HC-09 | Failed or hostile admitted currencies can still block exact whole-ledger capture, funding or rollback | `asset-liveness-dust`, `security-dependencies`, `migration-framework` |
| historical/HC-10 | Replace external custody-address exit with terminal proportional current-owner ETH/ZZZ return | `custody-composition`, `native-custody-recovery`, `security-ownership-rewards` |
| historical/HC-11 | Terminal holder exit ends LP principal activity but preserves NFT transfers, future royalties and earned reward liabilities | `native-custody-recovery`, `migration-framework`, `asset-liveness-dust` |
| historical/HC-12 | Native ETH must be actual native custody and settlement, not a cosmetic name over WETH balances | `lp-only-simplification`, `shared-custody`, `creator-market-controls` |
| historical/HC-13 | ETH-only holder reward display requires real funded conversion, not relabelling ZZZ reward liabilities | `reward-ledgers`, `security-ownership-rewards`, `lp-eth-settlement` |
| historical/HC-17 | 80/10/5/5 is credited from actual harvested receipts, not executed by user claims | `reward-ledgers`, `security-ownership-rewards`, `lp-eth-settlement` |
| historical/HC-19 | Whole-maintenance budgets must capture attributable starting principal before harvest and callbacks | `lp-execution-routing`, `lp-eth-settlement`, `governed-loss-limits`, `creator-input-liquidity` |
| historical/HC-20 | Activation/growth minimums and caller-bound execution floors must be enforced on-chain | `activation-quotes`, `activation-assets`, `reviewed-contribution-policy` |
| historical/HC-21 | Two USD sources require bounded disagreement and independent provenance, not a mean or target-pool fallback | `price-security`, `dual-price-qualification`, `creator-zzz-price` |
| historical/HC-23 | A dated public price observation or quoted fee is not a configured, qualified PoPL feed | `dual-price-qualification`, `authorities-prices`, `creator-zzz-price` |
| historical/HC-24 | Total loss, venue slippage, source disagreement, additional loss and caller maximum are different controls | `lp-execution-routing`, `lp-eth-settlement`, `governed-loss-limits`, `creator-input-liquidity` |
| historical/HC-25 | Known directional v4 trading fees must be separated from additional execution deterioration | `lp-execution-routing`, `lp-eth-settlement`, `governed-loss-limits`, `creator-input-liquidity` |
| historical/HC-26 | Reviewed LP execution venues are independent of the LP destination and may be reconfigured after seal | `lp-execution-routing`, `lp-eth-settlement`, `governed-loss-limits`, `creator-input-liquidity` |
| historical/HC-27 | Contribution callbacks and marginal LP measurement must isolate entrant funds from incumbent NAV | `security-share-accounting`, `custody-composition` |
| historical/HC-29 | Atomic routing must quote liquidity after own withdrawal and avoid two real balancing swaps | `lp-execution-routing`, `lp-eth-settlement`, `governed-loss-limits`, `creator-input-liquidity` |
| historical/HC-30 | Manual ±25/±50 ZZZ-price width is distinct from an automatic volatility policy and raw inverse pool ratio | `rebalance-confirmation-buffer`, `security-external-manipulation`, `security-keeper-manipulation` |
| historical/HC-31 | Ordinary upkeep is outside-only after hard cooldown, not a one-percent centre movement strategy | `lp-execution-routing`, `security-keeper-manipulation`, `security-external-manipulation` |
| historical/HC-34 | The rebalance confirmation buffer is sampled evidence with strict gap resets, not continuous history | `rebalance-confirmation-buffer`, `keeper-recovery`, `security-external-manipulation` |
| historical/HC-35 | A local pump/dump alone must not satisfy the ordinary range-exit trigger | `rebalance-confirmation-buffer`, `security-external-manipulation`, `security-keeper-manipulation` |
| historical/HC-36 | Manual emergency rebalancing intentionally has different optional financial guards and must never become an automatic fallback | `security-governance`, `post-seal-configuration`, `manual-emergency-rebalance` |
| historical/HC-37 | Bounded execution, cooldown and independent samples reduce but do not eliminate profitable external or keeper manipulation | `security-keeper-manipulation`, `security-external-manipulation`, `audit-release` |
| historical/HC-38 | Safe simplification retains callback/reentrancy/canonical barriers and historical codecs that still protect live boundaries | `lp-only-simplification`, `shared-custody`, `creator-market-controls` |
| historical/HC-46 | Exact asset settlement and post-callback authorization are structural safeguards, not optional economic controls | `security-share-accounting`, `custody-composition` |
| historical/HC-47 | Buyback scheduling fairness and burn target must be real and independent of holder claims | `reward-ledgers`, `security-ownership-rewards`, `lp-eth-settlement` |
| historical/HC-48 | Funded receipts and matching runtime hashes do not prove organic revenue or immutable upstream behavior | `price-security`, `dual-price-qualification`, `creator-zzz-price` |
| historical/HC-50 | Fresh fixed-pair Entry retains v3 plumbing with no useful executable contribution combination | `activation-quotes`, `activation-assets`, `reviewed-contribution-policy` |
| historical/HC-52 | Mint-only pause and local pool stop must work without querying failed prices or token dependencies | `security-governance`, `post-seal-configuration`, `manual-emergency-rebalance` |
| historical/HC-53 | A late callback-funded receipt historically allowed entrant overclaim unless incumbent checkpoints followed the last mutation | `security-share-accounting`, `custody-composition` |
| historical/OP-13 | Deferred terminal payout receivers could monopolize the serial keeper lane | `migration-framework`, `custody-composition` |
| historical/OP-16 | Confirmation enrollment during cooldown and persistent evidence limits | `rebalance-confirmation-buffer`, `security-external-manipulation` |
| historical/OP-21 | Keeper/external trader manipulation and repeated allowed losses are not solved by cadence | `security-keeper-manipulation`, `security-external-manipulation` |
| historical/OP-25 | Long-term state, failed dependencies and bounded custody capacity | `security-chain-recovery`, `asset-liveness-dust`, `destination-slots` |
| historical/OP-27 | Fresh Entry v3 route branch has no useful ETH/fixed-ZZZ contribution path | `lp-only-simplification`, `activation-quotes` |
| historical/OP-30 | Conditional overlapping financial floors do not justify blanket removal | `security-strategy`, `operation-review`, `liquidity-placement-idle` |
| historical/OP-31 | Old destination reservation race after capacity filled | `destination-slots` |
| historical/OPS-RS-00-2 | ## Independent NFT reward calculation | `security-ownership-rewards`, `financial-history` |
| historical/OPS-RS-06-1 | ## Operating interface and compatibility | `migration-framework`, `keeper-guardrails` |
| historical/OPS-RS-09-2 | ### Core-C2: the buyback maximum used the lower input USD mark | `lp-eth-settlement`, `security-dependencies` |
| historical/OPS-RS-09-3 | ## Explicit residual risks, not invented fixes | `fair-draw`, `asset-liveness-dust`, `security-ownership-rewards` |
| historical/OPS-RS-11-1 | ## Previous decisions challenged | `lp-execution-routing`, `rebalance-confirmation-buffer`, `security-governance` |
| historical/OPS-RS-12-1 | ## Functional boundary | `reviewed-contribution-policy` |
| historical/OPS-RS-12-2 | ## Normal object limits and exclusions | `activation-assets`, `deployment-initcode` |
| historical/OPS-RS-15-1 | ## Material findings and implemented responses | `reviewed-contribution-policy`, `security-integration` |
| historical/OPS-RS-15-2 | ## Remaining risks and work | `dual-price-qualification`, `metadata-ops`, `audit-release` |
| historical/OPS-RS-17-1 | ## Findings and repairs | `rebalance-confirmation-buffer` |
| historical/OPS-RS-20-2 | ## Useful failures and their limits | `activation-assets`, `mainnet-fork` |
| historical/OPS-RS-21-2 | ## Limits requiring further work | `lp-execution-routing`, `liquidity-placement-idle`, `operation-review`, `testnet-rehearsal` |
| historical/OPS-RS-31-1 | ## Verdict on the royalty consolidation | `security-ownership-rewards`, `asset-liveness-dust` |
| historical/OPS-RS-31-3 | ## Final publication review: deferred native credit guard | `royalty-eth-settlement`, `security-ownership-rewards` |
| historical/OPS-RS-41-1 | ## Reviewed financial paths | `security-share-accounting`, `security-dependencies` |
| historical/OPS-RS-41-2 | ## Feed agreement is not execution feasibility | `dual-price-qualification`, `operation-review`, `activation-quotes` |
| historical/OPS-RS-43-1 | # Current readiness after the full internal audit | `activation-assets`, `fair-draw`, `opensea-mint`, `host-services`, `audit-release` |
