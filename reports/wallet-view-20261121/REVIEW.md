# Complete wallet financial view: fixes and controlled qualification

21 November 2026. Contract baseline:
`08209ce8190e5c28c8854480ac3cd48a96568d33`.
Website baseline: `7271b79cfc330616d2278f87c0110bd239e669c3`.
Website source published: [`ceb6066`](https://github.com/ABEF/AAA-website/commit/ceb6066e180ce9e71ea915afe26f22997f09b0cd). [Exact published source hashes](PUBLICATION.json) retain the recorded stage boundaries.

**Captured financial reads and independent loading are implemented. 83 distinct
NEW JavaScript methods pass across explicit stages. New backend journeys for
1,17 and1,000 holdings reconcile LP, funded ETH and earnings without changing
accounting or existing operating limits.** Actual hosting/provider freshness,
full normal F6/V10 and maximum currency capacity are not approved by this work.

## Confirmed issues fixed

| ID | Issue and consequence | Implementation |
| --- | --- | --- |
| WV-01 | Financial methods retained caller-owned IDs/provenance through awaits. Mutation could retarget later reads or alter the returned identity. Direct `api.cancel()` also did not invalidate standalone metrics. No ordinary UI mutation or on-chain exploit was established. | Capture/clone complete schema2 inventory before asynchronous work; validate nonzero owner, chain, NFT, count/order and digest; retain revision/parent-abort checks throughout. |
| WV-02 | Financial freshness was checked before asynchronous RPC/native verification. A late final response could be returned after expiry; summary comparison also omitted timestamp equality. | Remaining-anchor expiry timer, full page timestamp binding, guards after awaited reads/verification and immediately before return, plus final canonical/deployment identity checks. |
| WV-03 | The view waited for all LP/ETH summary pages before even starting earnings, consuming the shared anchor's freshness and delaying an independently healthy metric. | Start the two financial branches together. Each branch keeps serial16-ID pages, giving at most two financial HTTP requests per wallet refresh. Publish only each complete result; failure in one does not hide the other. |
| WV-04 | An empty complete inventory could accept a malformed positive LP or ETH summary. Backend normally emits zero, but the consumer accepted the contradiction. | Refuse a positive amount only when captured inventory is empty. Null handling, zero and every nonempty calculation stay unchanged. Two NEW methods reproduce and verify the fix. |

The [website reader](https://github.com/ABEF/AAA-website/blob/main/deployment-api.js)
and [view](https://github.com/ABEF/AAA-website/blob/main/deployment-view.js) retain
all current-owner/sequence/controller gates. Account changes, cancellation,
expiry or missing pages never produce a partial portfolio sum or invented zero.
This is a per-wallet financial-read bound, not a new global server allowance.

## Exact accounting preserved

The existing raw-first earnings calculation is retained: sum exact original raw
amounts per asset/metric across complete matching pages, then apply current-price
USD rounding. Individual LP, collective LP and royalties stay separate until the
display sums their valued metrics. No principal, compound/buyback reserve,
conversion credit, claim or import is counted as additional earned income.

Missing LP and ETH amounts independently make that metric unavailable. Nonzero
unpriced earnings remain unavailable in USD, while genuine zero raw amounts can
value to zero without a price. Original currencies and exact decimals remain.

**Wallet claimable scope remains ETH-only**, as the existing summary endpoint
and label specify. Pending ZZZ LP and original-currency ERC20 royalties are not
relabeled ETH or silently summed into it; those claimables remain separately
shown per NFT. Whole-wallet source-token claimable totals are not introduced or
qualified here. Historical earnings belong to NFTs held at the captured block,
including earlier owners' history, not personal wallet tenure.

Inventory and financial chunks share a fixed confirmed block. Individual cards
retain independently confirmed latest snapshots. These are not claimed to be
an atomic whole-portfolio snapshot. New action preparation still obtains its
own fresh review.

## New actual backend producer journeys

The new producer executes production `Projection`, SQLite `History`,
`ExactReplay`, price verification, ownership pages, summary pages and wallet
earnings. Only neutral graph setup is reused; no old test method or population
is executed. The newly owned database contains deterministic raw logs and is
removed afterward. There is no checkpoint or existing DB/journal migration.

| Current holdings | Actual handler requests | Total RPC reads | Maximum reads / request | Largest JSON response | Slowest request |
| --- | ---: | ---: | ---: | ---: | ---: |
|1|4|790|261|7,497 bytes|0.157s|
|17|7|1,861|546|8,734 bytes|0.589s|
|1,000|190|67,388|546|8,743 bytes|0.999s|

The1,000 case has6,034 raw logs across90 blocks, all NFTs activated with equal
100shares and rarity1, and three priced descriptors: ETH, fixed ZZZ and a
six-decimal royalty currency. Runtime/views/prices/physical geometry and RPC
transport are explicitly synthetic V9/source9 fixtures, not a normal F6 EVM
deployment. Each request preserves25seconds/1,024 RPC/2,048 POST work budgets
and1MiB result screening; the isolated history profile allows10,000 events for
the6,034-event input. No existing configuration or source limit is changed.

Independent literal expectations include:

- Per asset,96n individual and12n collective LP earnings; designated compound
  and buyback portions stay outside holder earnings.
- ETH and token royalties31n each. The full86,400-second window excludes the
  exact cutoff block and includes the next one:48n/6n LP plus13n royalties.
- The first NFT converts108 source units into54 ETH units, claims162 native LP
  units and31 native royalty units, then transfers to the current owner.
  Neither conversion nor claims add earned income. Remaining wallet ETH
  claimable is139(n-1).
- LP summary is1000e18*n+n(n+1)/2. Raw values and per-asset USD floors agree with
  independently specified marks and decimals.

The1,000 handler requests take89.157s in total when measured serially in the
controlled producer:14.025s ownership,21.956s summaries,53.094s earnings, plus
protocol. The producer clock is fixed. Network round trips, real workers,
card reads and real advancing-chain freshness are not qualified by those
numbers. The website's saved-response consumption is likewise not a latency
benchmark. The complete actual provider/host pipeline remains open.

## Default HTTP admission blocks the maximum wallet

A new clock-controlled check of actual `ClientAdmission` confirms the unchanged
one-read/second, burst12 policy. Even an ideal client can admit at most132 reads
in120 inclusive seconds. The1,000-NFT protocol+ownership+summary+earnings journey
needs at least190 API requests, excluding cards and other reads; its earliest
last read is178seconds. The website permits at most120seconds of snapshot age.

Therefore **the default single-client end-to-end1,000-NFT HTTP view cannot
finish**, even with zero provider/CPU latency. Controlled DTO/replay passes do
not close that gate. All-read token sharing and the new asynchronous branches
do not grant extra capacity. Keep existing admission, freshness and completeness
checks. Review a bounded combined/selected read strategy that reduces request
count, with exact ownership/rights and independently unavailable metrics, before
qualifying the maximum wallet. This work does not introduce that new API wire.
`ADMISSION_BOUND.json` in the archive binds the exact admission source and result.

Fast smaller-wallet bursts can also receive429; the current consumer has no
automatic read-admission pacing/backoff. Qualify that coordination with other
tabs/clients and the existing ingress policy separately. A client scheduler
alone cannot solve the190-request/120-second lower bound and must never evade
the server's shared identity or rate budget.

## Maximum-currency refusal retained

The new65-royalty-currency/16-NFT earnings request correctly stops at exactly
1,024 RPC reads. Royalty `check_paid` reads alone require65*16=1,040 calls,
before graph, ownership, prices or other reconciliation. This is a concrete
capacity limit under the current fixed16-NFT earnings page.

The Todo retains bounded financial selection/currency-workload qualification as
open. Do not raise limits, enable unqualified operating currency capacity or
return partial earnings to disguise the refusal. This work does not add a new
cursor/wire profile or change entitlements.

## JavaScript verification and exact evidence stages

[Archive manifest](EVIDENCE.json) binds41 exact members in the
[public evidence archive](EVIDENCE.zip), including original fixture failures,
producer sources/results, complete DTOs, raw Node TAP and fixture derivation.
Archive SHA256: `b427ec5e30a2579cf84aeecc17fd779b59e56a1dfa57be12a0e472055ecb7bff`.

| Stage | Actual result | Boundary |
| --- | --- | --- |
| Backend01/02 | New fixture setup failures retained | Missing synthetic mint-end revision, then missing exact historical NFT deployment-code reply; production checks were never bypassed |
| Backend03 |1-NFT journey passes | First successful producer source; reused, not repeated in stage04 |
| Backend04 |17/1,000 journeys and65-currency refusal pass | Same corrected source; independent arithmetic and per-request budgets |
| Node01 |78 NEW methods pass;3 fail on missing producer files | Intended filter did not defer those3. Original selection metadata is corrected by the archive's `NODE_SELECTION_ERRATA.json`; TAP is authoritative |
| Node02 |Only those3 producer-consumer methods pass | Portable fixtures derived from successful production Python DTOs; earlier78 are not rerun |
| Empty guard red/green |Two NEW contradictions fail before the fix and pass afterward | Only one empty-inventory refusal is added; exact before/after source proof preserves nonempty arithmetic. Earlier81 methods are not repeated |

The83 distinct methods cover source9/source10 wire workloads, exact BigInt and
6/9/18/36-decimal rounding, missing prices/currencies/pages, owner/chain/NFT/
configuration/hash/time/digest drift, capture mutation, revision/cancellation,
deadline/reorg/final-verification races and independent branch settlement.
Separate controlled source9/source10 production constructor/native-reader/NFT
validator compositions use saved synthetic DTOs. The three new producer-consumer
cases use actual newly produced Python DTOs with an explicitly isolated native
graph seam and labeled header/genesis supplements. These scopes are not combined
into a claim of normal F6/V10 EVM or live provider acceptance.

No old test module is imported by the new Node file. Only safe fixture helpers
are used. Existing test bodies and saved historical fixtures are unchanged.
The maintained future selection adds the new file. No unchanged browser,
contract, Python suite, compiler, fork or previously passing method was rerun.

## Operator, documentation and preserved state

See the [operator procedure](../../docs/OPERATOR_MANUAL.md#complete-wallet-financial-view).
The existing portfolio/history tasks record this progress and the currency
limit; all83 IDs/statuses remain. Current API/profile/site docs, roadmap,
feature/findings, repository memory and website guidance distinguish the
controlled qualification from remaining deployment/provider/host work.

No backend/contract source, accounting rule, original-currency right, history
window, API wire, checkpoint identity, gas/fee/loss limit or authority changes.
Shared signer and both null public configurations remain byte-identical;
source9/source10 are unsigned and ordinary signing stays Anvil-only.
No site build, deployment, service/chain action, old DB/journal rewrite or
heartbeat restart occurred. Original edited documentation was archived outside
Git; four unrelated dirty contract files remain byte-identical and unstaged.

The final source-stage proof is `EMPTY_GUARD_SCOPE.json` in the archive. Final
83 passes mean the original78, the later3 producer consumers, and2 new
empty-wallet refusals, not one repeated whole-file run.
