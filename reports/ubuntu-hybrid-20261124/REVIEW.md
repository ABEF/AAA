# Ubuntu keeper: one → two → one — 24 November 2026

## Result

The new c800 isolated functional check passes **one main → main plus one
residual → one active main** through the unchanged stock keeper, real Cast
transactions and canonical receipt recovery. It uses **5,662/6,000 requests**,
21 setup transactions and two keeper transactions. No production implementation,
authority, financial policy, gas limit or journal format changes were required.

The 338-request remainder is only 5.63% of the lab budget; this is a finite
directed pass, not provider-capacity, maximum-state or sustained-operation approval.
The [state record](STATE.json), [original runtime result](evidence/c800/RESULT.json)
and [evidence manifest](verification/EVIDENCE_MANIFEST.json) retain exact scope.

All 190 copied production members match published
`e20e5d602dd59226e3dfb2f03ee2d206d0b8f9e8`; unrelated dirty files are excluded.
Frozen F6 remains 61 project sources/39 dependencies/4 build controls and 1,021
ABI rows. Existing source inventory stays authoritative; no build or unchanged
test body was rerun.

## Actual lifecycle

| Stage | Confirmed behavior |
| --- | --- |
| Initial state | One Vault-owned main, ID4331098; two existing activated NFTs and their rights are preserved |
| Request ON | Governance `PortfolioPolicy.setMode(pool,true,reviewHash)` changes desired geometry only; paired views show no principal/reward movement |
| Apply ON | Stock keeper persists a fresh85-second jitter, then ordinary `Vault.rebalance` burns4331098 and opens main4331099 plus residual4331100 |
| Validate two legs | Exact pool keys, positive liquidity, Vault ownership, separate rounded token amounts and stable/execution fingerprints reconcile; main is active and residual is initially one-sided |
| Move the market | A new genuine core trade enters the residual's interior. The same two IDs/liquidity remain, with the residual now mixed ETH/ZZZ; four controlled feeds are refreshed |
| Request OFF | Governance changes desired mode only; both legs remain attributed. An immediate stock cycle sends nothing and Strategy still refuses before the new hard12-hour minimum |
| Apply OFF | After the disclosed logical-time transition, the keeper persists a fresh234-second jitter and ordinarily replaces both legs with active main4331101 |
| Confirm | Both old LP NFTs emit burn transfers, the old association and global secondary count clear, desired/applied geometry match, pending clears, nonce advances0→1→2, and only two raw submissions occur |

The captured ON principal values are approximately60.1% main/39.9% residual,
including attributed idle in the denominator, meeting the configured minimum6000bps.
No raw liquidity values from different ranges are added. Configured half-side
width5000bps, containment and the positive tick-spacing gap are checked. The
allocation is an at-replacement bound; it is not continuously maintained60/40.
Residual creation is optional when mode is enabled, not guaranteed for all inventory.

Both deliberate mode changes use the existing geometry exception to the
600-second sampled market-trigger window. They retain the hard cooldown,
independently persisted jitter and all ordinary financial/custody checks.
The earlier successful ordinary-market sampled-window test is reused, not rerun
or relabelled as part of this case.

## Accounting and gas

Before/after vectors, actual logs, public signed transaction fields, inclusion
headers and stock fee observations are saved before final assertions. A separate
[read-only replay](evidence/INDEPENDENT_ACCOUNTING.json) verifies both receipts:
actual aggregate fees and old dust produce16/2/1/1 allocation units, funded
80% individual plus10% collective liabilities/claim totals,5% buyback reserves,
full old-plus-new designated compound release, and exact remaining dust/backing.

The ON harvest is546,220,834,665,161weiETH; it credits491,598,751,198,644wei to
holder rewards and retains1wei fee dust. OFF harvests92,163,426,046,337,710,873rawZZZ
from the mixed portfolio; holder credit is82,947,083,441,703,939,774rawZZZ and final
ZZZ dust is13raw units. Both post-replacement compound reserves are zero because
they were released into principal. Final rounding idle remains attributed/backed.
NFT owners, shares, membership, royalty weights and total shares stay unchanged;
earned rewards correctly increase. This is aggregate conservation, not a new
independent per-NFT Q128 phase-allocation proof or a new claim/conversion test.

| Operation | Estimate | Full25% allowance | Actual gas | Canonical cost, syntheticwei |
| --- | ---: | ---: | ---: | ---: |
| ON replacement |11,488,953|14,361,192|10,708,053|728,147,604|
| OFF merge |10,713,411|13,391,764|9,849,511|68,946,577|

Both allowances stay below24M. The5gwei quote ceiling,0.01ETH transaction and
0.05ETH shared/daily cost ceilings,12 confirmations,16MiB response bound,64KiB
Cast output and900 real-second/6,000-request lab budget remain. Charged price
comes from signed caps and canonical header; Anvil reports69/8wei where canonical
prices are68/7wei. The actual gas-only keeper debits and journal spend agree with
the canonical costs. This does not qualify Robinhood fees or adopt fee-profile2.

## Explicit clock and fixture boundaries

An actual Strategy read plus the stock no-send cycle confirm the hard43,200-second
cooldown; no paid early-rebalance transaction is sent. Its setting and
`lastRebalance` are not rewritten. A private module-local UTC facade advances exactly
43,200seconds once, only with no pending chain/journal work. It affects the
worker's monitor/confirmation/health clock references and coherent driver/log
timestamps. It never follows an RPC head or changes the host clock. The stock
freshness check first rejects the now-old head; only then do actual new blocks
and four fresh controlled feed rounds advance the model. Real monotonic time,
sleep, HTTP/Cast deadlines and the900-second work deadline remain unchanged.
See [recorded transition](evidence/c800/hybrid-LOGICAL_CLOCK_TRANSITION.json).

This is functional logical-time evidence, not twelve real hours, an unmodified
wall-clock daemon, continuous price history or a soak. Source-pinned state is
copied from an already-sealed39-instance/two-NFT local fixture; no new seal,
constructor/population journey or existing-chain mutation occurs. Reference
prices, external depth and low fee economics are controlled/synthetic.

The original c7ff attempt remains [failed](evidence/c7ff/RESULT.json):397 requests,
eight setup transactions and zero stock/raw transaction submissions. Its private
driver stopped governance impersonation before the Access.setKeeper setup send.
The new c800 driver explicitly restores that fixture authority immediately before
configuration, which stops it again afterward. Contract permissions stay intact.
Wallet-creation/address helper processes could already have run. A stronger
post-compound-zero assertion was also added in the new driver. Original helpers,
false aggregate and failure evidence remain unmodified. No production fix was
justified by that setup error. The separate local evidence collector's initial
missing gas-estimate key was corrected to use retained health reviews; it did
not run keeper work or change any runtime artifact.

## Operator impact, cleanup and remaining work

The [operator procedure](../../docs/OPERATOR_MANUAL.md#applying-on--off-through-ordinary-keeper-operations)
now makes the setter/execution distinction, waits, pending-state backing and
restart boundary explicit. The obsolete optional-portfolio profile pointer is
corrected to current profile7. There is no new function, input or deployment step.

Both newly owned units have empty process groups and stopped-state readbacks.
[Host comparison](evidence/HOST_PRESERVATION.json) preserves five original service
states and seven previously stopped labs, with zero non-ambient differences;
the pre-existing observer's invocation change is identified separately. Existing
sites, Anvil8902, keys, journals, checkpoints, public-null configuration and the
user-paused heartbeat are not adopted or changed.

Keep actual providers/markets/independent feeds/fees, maximum populations and
workloads, concurrent activation/growth/claims/transfers, hostile market/recipient
cases, different-key rotation, off-host fencing/restore, alerts, long-running
scheduling and independent audit/release approval open. This case does not test
manual/emergency/terminal exits or standalone hourly harvest/compound/burn/conversion.
There is no final post-OFF no-repeat or healthy-metadata cycle. Successful pending
recovery is checked in-process; interruption/restart during this hybrid flow is
not newly qualified. Q06/P20/P21 remain incomplete.
