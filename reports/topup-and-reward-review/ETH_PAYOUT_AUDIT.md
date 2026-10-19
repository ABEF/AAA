# ETH-only holder payouts: current implementation gap

Reviewed 2026-10-19. The user requires NFT holder rewards in native ETH. The
current candidate does **not** meet that requirement for LP rewards. This is a
functional/economic integration gap, not evidence of a stolen balance or an
authorization bypass. Production remains NOT APPROVED.

## Trace of actual funds

| Boundary | Current behavior | Consequence |
| --- | --- | --- |
| [LiquidityManager](../../src/ZZZLiquidityManager.sol), `collect` / `_finishNativeCredit` | Native venue receipts are wrapped into the reviewed accounting token. The other side remains its original pool token. | For ZZZ/native ETH, accounting uses ZZZ and WETH; native venue support does not mean native holder payouts. |
| [Creator RewardReceiver](../../src/ZZZRewardReceiver.sol), `sync` | Creator ETH receipts are wrapped; admitted pair currencies forward unchanged to FeeController. | Even an ETH creator payment can become a WETH LP liability. |
| [FeeController](../../src/ZZZFeeController.sol), `_distribute` / `_credit` | Fixed 80/10/5/5 is applied per source currency; the 80% and 10% are credited to Rewards in that currency. | Neither the owner nor the collective part is converted to ETH. Compound/buyback reserves remain separate. |
| [Rewards](../../src/ZZZRewards.sol), `_claim` | Checkpoints the individual and collective indices, debits the same currency liability and calls `ExactToken.push(token, owner, amount)`. Admitted assets must have contract code. | There is no native-ETH balance, ZZZ swap, WETH unwrap or LP conversion hook in this ledger. |
| [ClaimRouter](../../src/ZZZClaimRouter.sol), `claimBatch` | Authenticates current ownership and calls each ledger's `claimFor`. Ledgers pay the owner directly. | Batching is not conversion. The router has neither conversion authority nor custody of those payouts. |
| [RoyaltyRewards](../../src/ZZZRoyaltyRewards.sol), `convertBatch` and [RoyaltyConverter](../../src/ZZZRoyaltyConverter.sol) | Keeper checkpoints royalty source balances, converts bounded batches and credits ETH to the same NFTs. | This converter is bound to the royalty ledger; it cannot spend or convert the LP ledger's assets. Direct source-currency royalty claims remain supported, so the entire protocol does not enforce an ETH-only claim policy either. |
| [Keeper royalty job](../../keeper/royalties.py) | Optional royalty conversion only. | No scheduler configuration turns it into LP conversion. |
| [Website local renderer](https://github.com/ABEF/AAA-website/blob/main/local-view.js) | Reports actual claimable currencies separately. | TEST-1 plus ETH is honest about this fixture; replacing TEST-1 with ETH would falsely describe the asset received. |

The current local pool is two generic mock ERC20s. TEST-1 is its API label; it
is not a deployed ZZZ, WETH, USDC or USDG contract. Named production-like local
assets and routing need their own fixture and verification. A cosmetic rename
would not test wrapping, decimals, source approvals or conversion behavior.

## Read-only reproduction

[Claim trace](claim-currency-trace.json): `debug_traceCall` of the real local
ClaimRouter on Anvil 31337, with one active NFT and its current owner. It pays
`17575258928655673749` raw units of the local ERC20 and
`4166666666666666` wei in native royalties. The claimable getters remain unchanged
after the trace. **No claim transaction was broadcast.** The trace binds the
block and inspected source hashes; it is not a new full-contract regression or
proof of a live Robinhood route.

Separate user-requested test funding added 100,000 mock input tokens to wallet A
through the local token operator's `mint` function, after chain/genesis/code/role,
simulation and gas checks. Balance moved from 84,568 to 184,568 at that receipt.
This changes a disposable wallet balance, not NFT LP/reward accounting. See the
[funding receipt](local-input-funding.json). Existing NFTs, prior claims and chain
state were retained; no token symbol or asset identity was rewritten.

## Required design boundaries

The implementation belongs to [the central task](../../TODO.md#task-lp-eth-settlement).
No converter, fee policy or source-claim restriction is added by this audit.

The recommended boundary is the holder reward ledger, after the fixed split:
checkpoint each NFT's already-earned individual and collective source balances,
batch conversion of that bounded set, and credit the exact received ETH back to
those same NFTs. Keep the two income categories distinguishable for history.
Do not distribute the output using current LP shares or current active membership;
activation, top-ups and transfers can change those between earning and conversion.
Do not reapply 80/10/5/5 to conversion output, or spend principal, the 5% compound
reserve, buyback reserve, orphaned funds or another NFT's backing.

Exact reviewed WETH unwrapping requires no swap. Other assets require approved
routes, independent fresh prices, bounded minimum output/deadline, exact transfer
deltas, cleared approvals and reentrancy/ownership/lifecycle checks. A proposed
1% LP-conversion cap, gas separate, needs an explicit decision: the existing 1%
activation and royalty-conversion limits do not silently configure LP conversion.

Define the public claim policy and outage recovery before implementation: a
pending/failed swap must remain visibly backed in its source currency, not become
a fabricated ETH balance or silently lose an NFT's entitlement. ETH-only default
UX and a direct source-currency recovery path are different decisions. Preserve
fractions/dust, all pending and converted balances through same-chain handoff,
and history across transfers and future replacements. Conversion is not new
income or a payout; only actual claims increase lifetime paid amounts.

Complete this before sealing: the current LP ledger/router cannot acquire a new
conversion path by changing a route or keeper configuration. Review runtime and
constructor sizes, bounded batch gas, keeper outage/restart, failed wrappers,
tokens/routes/oracles, simultaneous claims/transfers/conversions, and source-to-ETH
accounting. Existing unrelated suites were not rerun for this source-only audit.
