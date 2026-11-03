# Collective holder exit: scale and mixed-wallet assurance

3November2026. Production source remains exactly main
`e26fc7425b40259e3ddc92404a50251a4ef1b2b9`: accounting6/custody5/Entry3/schema10.
Only tests, evidence and maintained guidance change. Undeployed; production
**NOT APPROVED**. No new withdrawal/recipient/sweep or management feature.

## What is confirmed locally

Each activated NFT retains its own shares and principal allocation. One wallet
may own many NFTs, including dormant tokens, different rarity/tiers and unequal
LP/top-up histories. The wallet gets the sum of its individual NFT allocations;
there is no per-wallet equality or rarity multiplier for principal. A dormant
NFT with zero shares gets no principal. Unpaid principal and unclaimed rewards
follow each NFT's current owner independently; previous reward claims do not
spend principal. Principal payment never counts as fee income.

Governance closes the main and optional residual, including attributed idle
and designated compound, without a balancing swap. Actual close deltas fund
settlement; earned LP/royalty balances, buyback reserves and prefunds remain
separate. For each bucket/asset the allocated amount for NFTi is:

`floor(returned * cumulativeShares_i / totalShares) - floor(returned * previousCumulativeShares / totalShares)`.

Immutable mint order and final share/asset reconciliation allocate every raw
unit. This returns current actual ETH+ZZZ, not original quantities or a promised
USD deposit floor. Every nonzero NFT allocation can be paid only once. Governance
pays/submits bounded batches; holders do nothing for an accepted direct payment.

## Useful gap repaired

The previously existing1000-NFT model had no LiquidityManager binding. Current
Migration correctly calls activeSecondaryCount when closing the final bucket;
two model tests reverted at that missing address before their allocation checks.
The trace established the missing fixture dependency. Added a test-only Manager
stub matching the model's parked/no-residual state. The production guard remains
unchanged. A new negative case leaves count1, checks final-close rollback and
continues only after the fixture count returns0. No production bug was inferred
from the stale model, and its failed attempts remain recorded.

## Verification outcomes

10 distinct selected behaviors pass across three explicit test-source stages;
one is a1000-case fuzz test, not1000 additional test methods. Four regressions
are new. Existing affected paths were selected; unrelated/full suites were not
repeated. [Campaigns and pins](campaigns.json), [reuse boundaries](reuse.json).

| Check | Observed local result and limit |
| --- | --- |
|1000 ordinal model/four historical buckets | Exact total allocation/delivery, zero-output bucket, dormant NFT and changed owner. It uses real Migration with modeled Vault/NFT/Access, not1000 real deposits. |
|1000 distinct holder addresses | Independently checks each NFT's cumulative-floor allocation and actual recipient ETH/ZZZ balances; all nonzero liabilities settle.999activated/1dormant. Addresses are synthetic local EOAs, not funded public wallets. |
|1000 NFTs across37 mixed wallets |201dormant/799activated, varying shares over four buckets. Each wallet's balances equal the sum of its NFTs; duplicate delivery pays nothing again. The model does not fake real rarity/evolution data. |
| Real NFT mixed-wallet composition | One initial wallet owns dormant Legendary, activated Commun/Rare/Legendary at three actual evolution tiers; another holds Rare. Exercise growth, earlier LP/royalty claims, transfer only one NFT after allocation, exact per-NFT and grouped-wallet payouts and remaining owner claims. Real Vault/NFT/Rewards/Royalty/Migration with deterministic venue/feeds/VRF and MockAccess. |
| Actual local v4 main+residual closure | Existing real PoolManager/PositionManager/StateView and typed LP execution close both physical IDs, deliver principal, retain royalties/transfers. A second case first closes residual into idle, then returns main+idle. Uses synthetic pool/token/feed/VRF/authority setup; not actual Robinhood pool/production services. |
| Inconsistent inventory/dependency rejection | Wrong-currency bucket fails before irreversible start; corrupted per-NFT share inventory cannot enter Ready or pay; registered residual prevents final close from committing. |
|1000 fuzz cases | Real Vault/NFT/reward/Migration composition with deterministic venue: varied contributions and fees conserve returned ETH/ZZZ and settle once. Same unchanged fuzz body and production pins; other test helpers changed later. |

Initial campaign:4methods,2passed/2failed (missing test Manager); the successful
fuzz case ran1000inputs. Corrected-scale campaign:5passed. Mixed/actual-core
campaign:4passed. Repeated method IDs are counted once, not13successes. Test
fixtures use the existing large test-only size allowance; this does not relax
normal production gates. Production/dependency/build pins match the existing
43normal gates/471static dispositions, reused without an unnecessary rerun.
The public callable reference and all function inputs/permissions remain unchanged.

## What is not guaranteed

Governance must finish every close/allocation/delivery batch and fund gas. A
successful batch can defer individual receivers; inspect per-NFT paid state and
PrincipalPaid/PrincipalDeferred, then retry unpaid nonzero allocations. Read NFT
IDs rather than confuse mint ordinals or wallet addresses with them. Group actual
receipt beneficiaries when reconciling wallets; gas or other transactions can
change wallet balances independently of principal.

The current direct-payment path cannot force a rejecting contract to accept
ETH. Its pair payout reverts in isolation and stays backed; owner-controlled
fallback remains. An escrow/dead/lost owner may be unable to recover. Broken
ZZZ/venues, lost governance and chain failures can delay or prevent completion.
No universal delivery or original-value guarantee is claimed.

Actual maximum-population target-chain gas, authority/service recovery, token
behavior and independent audit remain release gates. Local models and actual-core
composition complement each other; neither qualifies a real deployment. No
production source/API/keeper/site/service/Anvil/journal/signing/heartbeat changed.

[Full exit procedure](../../docs/HOLDER_COLLECTIVE_EXIT.md),
[operator reconciliation](../../docs/OPERATOR_MANUAL.md#reconcile-holders-with-several-nfts),
[owning task](../../TODO.md#task-custody-composition).
