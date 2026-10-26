# Backend fee-breakdown remediation

**Production remains NOT APPROVED.** The user asked to work on backend defects,
then focused the request on the fee breakdown. This implementation repairs
financial-report integrity in the existing backend. It changes no Solidity,
revenue split, entitlement, custody authority, signing policy or deployment.

Initial main is `30eb4df0473b732da6c604192807c24856873e2f`, after the previous
full-audit fixes. Current accounting 3, direct governance 2, fee intake 1 and
same-chain local canonical V4 remain explicit. Historical profiles keep their
reviewed behavior. Fourteen unrelated dirty files and other untracked artifacts
remain preserved; owned memory/document additions are staged separately.

## Implemented corrections

| Confirmed defect | Failure and consequence | Correction / evidence |
| --- | --- | --- |
| Allocation and funded-credit histories were independent | A forged `FeesAllocated(100,0)` → `(200,0)` inflated collection gross/compound/buyback totals while the actual holder credit remained 80/10. Missing allocation logs and a wrong actual fee version could also pass. | Explicit fee-intake 1 requires the real module version and exact same-transaction/bucket/currency credit pairing. Allocation of 20*n requires 16*n individual and 2*n collective; dust settlement matches its exact individual-only credit. [History findings](HISTORY.md). |
| Carried dust was not checked against the actual cutoff | Changing only remainder 0 → 19 reported gross 119 instead of 100 while actual FeeController dust was zero. | Query the touched fee keys at the pinned epoch cutoff and require exact dust, including zero. Only the known native currency argument is admitted for this getter. [Counterexample](lp-dust-counterexample.json). |
| Impossible dormant claims were accepted | A verified never-activated NFT with zero shares/bucket/weight could report positive LP or royalty claims. | Reject any available nonzero balance for that validated inactive NFT, with or without optional royalty reporting. Null currency failures remain unavailable. Parked/outbound activated NFTs retain their rewards. [Profile review](PROFILE.md). |
| Current native LP inventory could omit ETH | Accounting 3 accepted a Rewards list lacking its mandatory first ETH currency when descriptors otherwise covered the union. | Require actual ETH first for current accounting 3; never synthesize a row. Historical profiles retain their reviewed inventories. [Profile review](PROFILE.md). |
| Wallet totals swallowed malformed core values | `ProjectionError` is a `RpcError`; the summary caught its own malformed Boolean/ABI or contradictory availability error and returned a partial successful chunk. It could also count impossible inactive credits. | Preserve ProjectionError/WorkLimit as fatal; genuine view outages still null the affected metric. One extra pinned weight read per current NFT rejects inactive nonzero LP/ETH without heavy per-card replay. [Operations review](OPERATIONS.md). |

These are high-confidence **P2 reporting/integration integrity defects**, not
demonstrations of an on-chain withdrawal or entitlement exploit. Honest valid
data keeps the same amounts; contradictory/missing evidence now fails explicitly.
Source changes are limited to five backend modules: `earnings.py`,
`earnings_replay.py`, `wallet_earnings.py`, `service.py` and `portfolio.py`.

## What the fee breakdown means

| Display / API quantity | Included | Excluded / important distinction |
| --- | --- | --- |
| NFT LP rewards | Its individual LP-share entitlement plus its equal activated-NFT collective entitlement | Collection gross fees, compounding and buyback reserves; rarity has no LP effect. |
| NFT royalties | Its funded, eligible rarity-weighted royalty entitlement | The activation contribution and royalties for earlier ineligible periods. |
| Ready to claim in ETH | Current native LP ledger plus current native royalty ledger for the same NFT/block; both legs must exist and be readable | Unconverted source tokens, past payouts and earnings history. No unrelated raw token units are added to ETH. |
| NFT 24h / all-time earnings | Processed individual LP + collective LP + royalties attributed to that NFT, including amounts already claimed by previous owners | A claim, conversion, transfer or custody return is not new income. History is attached to the NFT, not the wallet's holding duration. |
| Collection LP allocation | Gross LP receipts and separate holder, collective, compound and buyback allocations | Royalty receipts are a separate stream; allocated holder funding may include retained rounding fractions and is not an exact sum of immediately claimable NFT whole units. |
| USD earned history | Originally earned currencies marked at the current confirmed prices, per the user's existing decision | Not historic USD, realized conversion proceeds or current claimable ETH value. Missing prices for nonzero amounts remain unavailable. |

Pending unsynchronized royalties may already be included in current contract
claimable before entering **processed** earnings history. That existing timing
rule is unchanged: the 24h clock is processing/allocation time, not an inferred
marketplace-sale or bank-receipt timestamp. No receipt time or price is invented.

## Independent worked example and top-up

The test deliberately makes LP shares **1:3:2** and royalty weights **3:1:2**.
For 600 units of actual LP revenue and 600 units of separately received royalties
in the same currency:

| NFT | Individual LP | Equal collective | Royalty share | NFT total |
| --- | ---: | ---: | ---: | ---: |
| 11 | 80 | 20 | 300 | 400 |
| 22 | 240 | 20 | 100 | 360 |
| 33 | 160 | 20 | 200 | 380 |

NFTs receive **1,140** units: 540 LP + 600 royalties. The other **60** units
remain 30 compounding + 30 buyback. No reserve becomes claimable NFT income.
Adding 300 shares to NFT 11 changes future LP shares to 4:3:2 while royalty
weights stay 3:1:2 and previous earnings remain unchanged. After another 900 LP
and 600 royalty units, cumulative totals are **1,050 / 730 / 770**. These are
independently asserted raw-unit examples, not a yield forecast or live balance.

## Verification and operating impact

The final affected sweep passes **167 distinct methods**, including 31 new
regressions and 136 affected existing methods, in 29.563s. All five changed
implementations, tests and imported fixture hashes remain unchanged during it.
No duplicates, skips or errors. Earlier reproductions and focused runs are
retained, not added to that final count. See [verification](VERIFICATION.md).

The API response schemas and endpoints are unchanged. Current fee-intake 1
now requires actual `FEE_INTAKE_VERSION() == 1`, its existing dust getter and
complete seven-emitter history at each pinned cutoff. Historical fee-intake 0
does not silently inherit these requirements. Same-chain import/activation and
per-epoch reset are tested without counting imported funding as new earnings.

Summary adds one current-profile weight read per selected NFT; dust checks add
one read per observed fee key per epoch. Existing asset/bucket/event/request/RPC
and freshness bounds remain. Requests that cannot complete reject, never return
partial totals as complete. Actual provider latency and operating limits still
need qualification.

Before a hosted rollout, retain original databases/configuration, build a
separate reviewed replay/checkpoint copy, compare known NFTs/collection/current
balances and independent raw history, then qualify actual provider/resource
budgets. A mismatch is evidence to investigate; do not edit logs, reset history,
change profiles or guess zero to make it pass. No running service or database
was upgraded in this task.

## Remaining limits

Head state and event arithmetic do not prove all historical log completeness
or ordering against a coherent dishonest provider/operator. An isolated omitted
fee-only receipt on a previously unobserved key has no reward-index signal;
intermediate dust manipulation that restores the true final remainder still
requires authentic complete logs to exclude. Use the existing independently
reviewed provider/window-audit and ingestion gates; this patch is not a proof
of receipts or finality.

Current website profile-3 integration, actual feeds/routes/VRF/authorities,
OpenSea, token/burn/venue qualification, operating rehearsals and independent
audit remain open. No website source/build/server, public RPC/financial
transaction/deployment/seal, existing Anvil/NFT/LP/balance/journal or monitor
action occurred. Public DEPLOYMENT remains null; signing stays Anvil-only.
Publication is recorded separately after verifying the actual remote heads.
