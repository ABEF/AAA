# Real price-feed and swap-route qualification

**Read-only qualification completed; release admission remains blocked.** No
price pair or conversion route was enabled. All current safeguards, source code,
operating configuration, funds, services, sites, Anvil, journals, signer and
user-paused heartbeat are unchanged. Baseline: `509d4fd`.

The common Robinhood4663 snapshot is block110324511,
`0x49759bb8363ba4e95b5b090fd7bee113949b100ab1fa408a839603dc31f4e6b9`,
9November2026 **20:04:50UTC**. A separately labeled API3/liveness follow-up uses
block110332661 at20:18:44UTC. It never replaces the original market/price basis.
These are dated observations, not configured PoPL prices or permanent depth.

## Price sources

| Source | Actual evidence | Admission result |
| --- | --- | --- |
| Chainlink ETH/USD | $2125.61, updated20:02:37UTC, age133s. Both proxy addresses still point to the same aggregator. Current digest/event/getters reconcile10signers,10transmitters and f=3. | One candidate, not two independent sources. Actual operating maxAge, organizations/markets, full upstream/control and service review remain open. |
| Pyth Core ETH/USD | Stored $2241.72518 from7November; age229537s exceeds86400s. Spread against Chainlink is546.2675655bps, above300. Both live update-fee getters return0; unauthenticated current Hermes request returns401. | Reject stale/disagreeing observations. Zero on-chain fee is not a funded authenticated updater, data plan, gas budget or recovery qualification. |
| API3 ETH/USD: newly investigated | Real proxy/implementation/control graph and five authenticated90-day offers exist. Name binding/subscription and base observation are unset; reads revert or return an uninitialized timestamp. All292management leaves reconstruct the published/on-chain mapping root. | Inactive candidate. Its native compatibility proxy also returns round IDs0, which current PoPL correctly rejects. Activation/funding, liveness and a separately reviewed adapter would be needed if selected. No adapter or subscription was added. |
| Fixed ZZZ/USD | No exact-token match in refreshed checked Chainlink/Pyth/API3 catalogs. The tested API3 ZZZ name/offer/proxy are unavailable. | No two independently qualified correct-token USD sources established. Public-catalog absence is not proof that custom/private services do not exist. |

Exact controls, original timestamps, runtime pins, failures, offer parameters
and primary URLs are in [feed findings](feeds/FINDINGS.md) and
[machine-readable evidence](feeds/FEED_FINDINGS.json). API3 offer parameters are
native-wei duration-funding parameters, not guaranteed payable quotes or selected
PoPL policies. Sponsor balances, queues and gas remain separate. Literal admin
owner sets differ; that does not prove independent people, markets or publishers.

Chainlink's [uptime documentation](https://docs.chain.link/data-feeds/l2-sequencer-feeds)
does not list Robinhood and says expansion to additional networks has stopped.
A correct-chain outage policy needs an explicit review; no Arbitrum feed or
always-up substitute was invented. [Self-managed feeds](https://docs.chain.link/data-feeds/self-managed-feeds)
can be absent from public catalogs and have third-party publication/service
responsibilities. Labels alone do not establish a managed DON or independence.

The exact-token [LBank/XT market evidence](review/cex-findings.json) adds genuine
custom-provider leads. These are USDT markets, not USD oracles or on-chain swap
venues. Displayed near-mid liquidity is thin: the captured LBank book has only
about4USDT per side within3% of midpoint; XT about41/45USDT. Hidden liquidity,
actual fills, fees and future availability are unverified. USDT/USD conversion,
publisher quality, depth, administration and update arrangements still matter.
No exchange account, order, deposit, withdrawal or provider contact was made.

## Swap venues and actual size

The bounded follow-up finds no new direct native-v4 or v3/WETH pool/fee events
since the prior anchor. Four earlier pool states changed; selected pool501122…
did not. The current package contains95 hookless static v4 states:70 satisfy
the Registry's strict principal fee precondition;25 do not. The old inclusive
Balancer ceiling count71 is not full Registry admission. Fee exactly100000pips
fails the strict fee-versus-slippage rule; active-eight conclusions are unchanged.

All15 empty-active-L cheap venues were probed in both directions at14 vectors.
Zero activeL alone was not used to reject a pool: another4%-fee venue can cross
a gap for a tiny input, but its additional operation-sized quotes fail. Retain
191 decoded incomplete-input errors and19 other cheap-pool errors separately.
An unknown error is not proof of absent liquidity.

Selected-pool reverse capacity is exceptionally small: **388557raw ZZZ returns
1wei ETH**, while388558raw rejects the full-input request. These are raw units,
not whole ZZZ. Full-input quoter semantics and exact integer replay distinguish
this from an acceptable partial swap.

Alternative10018's physical ZZZ-per-ETH price is1.358280448times selected. Under
the existing500bps maximum spot/reference guard, both cannot pass ordinary
principal pre-swap checks against any shared reference at this snapshot. This
does not prohibit merely registering pools and does not apply to the separate
earned-reward converter. Among eight active principal fee candidates, only
selected and thin07ee2b… have overlapping necessary reference bands. Overlap is
not sufficient execution approval.

Some tiny reverse quotes are favorable enough to pass a **conditional**1% floor
using the selected-spot-derived sizing vector. They must not be erased or called
qualified USD execution. The largest observed passing output,36249908446wei ETH,
is about11.62times smaller than the421218000000wei **intrinsic-only basefee cost**
at this anchor, before any conversion work. This is not a paid or complete fee
quote. The keeper converts whole selected NFT entitlements; it does not invent
arbitrary dust slices to make a quote look executable.

[Final route evidence](routes/ROUTES_FINAL_v2.md) and the
[per-direction matrix](routes/route-matrix-final-v2.json) preserve696 quote calls,
including23 overlapping200k-gas rechecks. Twenty-two recheck outputs agree with
the earlier2M-gas calls; the remaining case already failed at2M. These are official
quoter observations, not the distinct production Balancer/converter transaction
or whole-operation gas acceptance. V3 earned conversion still needs a reviewed
nonzero immutable wrapper before sealing and matching manual/worker support;
native principal cannot use v3. No such choice was made.

## Safeguards and next steps

Contribution remains300bps/97% marginal deployed LP; conversion100bps,
maintenance300bps, additional execution100bps and source agreement300bps remain
separate. No swap/spot/idle/caller guard was changed. Two-source spread itself
uses execution margin: a hypothetical upper/lower ratio1.03 makes the97% floor
equal99.91% of lower-marked input, leaving only9bps before other costs. This is
an arithmetic illustration, not an actual approved price vector.

1. Obtain two defensible ZZZ USD source proposals with exact contracts, markets,
   independence/control evidence, original timestamps, publication/update service,
   costs and outages. Evaluate market depth rather than relying on ticker labels.
2. Resolve the ETH secondary service and chain-liveness policy. API3 is a concrete
   inactive option; Pyth needs authenticated fresh updates. Keep hard round/age
   checks and explicit adapter review.
3. Obtain economically useful executable depth at prices compatible with the
   selected destination and independent USD references. Then simulate complete
   activation/growth and earned conversion, including gas and current-owner rights.
4. Qualify a sustained archive/trace provider. The official RPC kept the anchor
   header but later refused its state after roughly11minutes; a bounded alternate
   provider rescued those reads. Neither observation approves a production service.

Quotes here use external liquidity only. No deployed PoPL LP was withdrawn;
future post-close depth, dominant-LP exposure and actual transactions remain
unqualified. There is no qualified independent USD vector, so neither successful
quotes nor the prior2% full-operation rejection can be relabeled as current3%
activation/growth acceptance. The [sole Todo](../../TODO.md) records these gates.
