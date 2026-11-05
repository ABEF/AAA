# Royalties claimed in their original currencies

User decision5November2026; baseline main bce897c. Fresh undeployed settlement2/
recovery2 candidate, **not production approved**. LP conversion, NFT weights,
principal custody and all installed services/sites/Anvil/journals are unchanged.

| Change | Result |
| --- | --- |
| Royalty swaps removed | No fresh converter contract, stored converter, binding, batch conversion, unwrap, approvals or swap-recovery selector in RoyaltyRewards. ETH/WETH/USDC and other admitted units remain their original currency. |
| Unallocated allocation | Governance `allocateUnallocated(asset,amount,reviewHash)` moves only admitted orphaned units into liabilities/index in the SAME currency at current active rarity weights. No external recipient, payout, price, route or swap. Existing earned/deferred/fraction backing is excluded. |
| Preserved entitlements | Independent per-currency indices, actual backing, Commun1/Rare2/Legendary3, incumbent checkpoints, outage cohorts, current ownership and fractions remain. Growth adds no royalty weight. |
| Mixed claims | Existing32-entry ClaimRouter pays LP and royalty claims in one atomic owner transaction. Original-currency claim requires no ERC20 approval. A failing selected payout reverts the batch; the owner reviews healthy entries separately. |
| Explicit source boundaries | Schema11 has18helpers, settlement2/recovery2; reporting3 requires converter:null and exact capability/runtime. Fresh keeper royalty_settlement_version2 rejects conversion settings/new royalty-swap submission. Legacy defaults/readers/events/journals remain separate. |
| Reporting/history | Separate raw currency quantities; no pending-ETH label, quote or conversion clock. Same-currency UnallocatedRoyaltiesAllocated credits income once; old conversion/recovery events remain historical. Semantic-source changes invalidate old earnings checkpoints until reviewed rebuild/re-pin. |
| Website source | Reviews/selects original-currency royalty entries, validates exact approved currency metadata and displays simulated payouts. LP token conversion remains separate. Legacy profiles keep their former selection; signer/public deployment boundaries unchanged. |
| Operator/docs | Exact admission/sync/claim/allocation inputs, limits, failure/restart boundaries and full callable examples updated with sole Todo/features/profile/release/context. |

## Material limits and changed tradeoffs

Unsupported receipts must now be reviewed/admitted before same-currency allocation.
Admission remains append-only16ERC20 plus ETH. The old recovery1 could swap an
unsupported token without consuming a slot; that path is deliberately removed.
Do not admit spam or promise unlimited/universal token recovery. Capacity after
long-lived operation/terminal exit and pathological-token handling remain explicit
release-review concerns in the owning Todo; no arbitrary sweep is added.

Holders now bear the currency exposure they claim. No guaranteed ETH value is
promised for non-ETH royalties. Missing prices leave USD reporting unavailable,
not the raw claim. Frozen/blacklisted/taxed/rebasing/unreadable currencies can
still fail their own operations. Healthy currencies retain separate accounting.
New currency admission needs reviewed API/website descriptors; no automatic
provider/config deployment is inferred from the contract call.

The fresh royalty storage layout changes when converter storage is removed.
Canonical row format remains compatible, but runtime/storage identity is never
inferred from accounting6 or tuple shape. Existing deployed code cannot acquire
settlement2 through a config edit. Historical royalty-conversion implementations
are retained only in test/historical and exact Git history, not production src.

## Verification and remaining qualification

[Verification](VERIFICATION.md) and [evidence](evidence.json) record selected EVM,
Python, website, normal-size and strict internal static results with failed/
corrected stages preserved. These are not a whole-suite, real marketplace, target
gas/uptime, public CI or independent approval. No public transaction, deployment,
sealing, website/server/service change, Anvil reset or journal/signer change.
