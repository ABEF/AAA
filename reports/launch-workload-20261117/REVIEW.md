# Launch workload: gas boundaries, claims and pre-seal review

Baseline main: `0736ce42d73f717ad62c43dabe55de70f8e82b8f`.

**The launch workload now has measured boundaries, including refusals. It is not
universally qualified at16 currencies.** Full operation estimates are stricter
than cold CALL-body measurements. All61 production Solidity sources, economic
rights, financial safeguards, gas defaults and existing environments remain
unchanged. The trusted normal build stays `seal-boundaries-20261117`.

## What improved

The unsigned pre-seal planner now explicitly requests the actual admitted
royalty currencies and current gas-policy reads. `assetCapacity=16` permits16
ERC20s plus ETH; it does not mean17 currencies are admitted or that every
workload fits20M. The new rows remain unverified and add no configuration,
admission, signing or seal call. [Implementation and four new checks](backend/REVIEW.md).

New controlled EVM workloads verify actual marginal LP, net share issuance,
unchanged range/rebalance clock, current-owner rights, exact-unit allocation,
reserve separation and atomic failure. New own-chain read-only RPC simulations
then measure naturally cold complete calls, estimates and exact full-padding
calls. No published provider or existing chain is used.

## Complete local contribution results

The current mint2 NFT is issued through the pinned SeaDrop fixture runtime,
with actual Entry/Vault/LP1/royalty4 and Uniswap v4 core/periphery. There are16
admitted test ERC20 royalty currencies plus ETH, one incumbent and one entrant.
The test sale is public-only; the intended team/allowlist/public launch phases
are not qualified by this gas fixture.
Authority, pool admission, Permit2, VRF, dual USD publications and market depth
are explicitly controlled. Local chain31337 is **not** Robinhood qualification.

| Captured state | Actual estimate plus full20% | Reviewed20M result |
| --- | ---: | --- |
| ETH activation, empty royalty inboxes |18,145,254|Fits |
| ETH activation, pending royalties |19,824,490|Fits in this state |
| ZZZ activation, pending royalties |20,316,681|Refused by the full-margin policy |
| ETH activation, first opening allocation |20,470,398|Refused by the full-margin policy |
| ETH activation, one full-budget currency fault |20,935,371|Refused by the full-margin policy |
| ETH activation,16 full-budget currency faults |No successful20M estimate|20M call refuses atomically |
| ETH growth, healthy currencies |16,379,076|Fits |
| ETH growth,16 faulting currencies |16,379,076|Fits |
| ZZZ growth, healthy currencies |16,821,302|Fits |

The16-fault activation completes only in a separately labelled32M diagnostic
call (29,419,722 traced gas). That does not admit32M, provide its full20% margin,
change defaults or prove affordability. Ordinary growth skips royalty activation
because the NFT already has its weight. It must not be charged a fictitious
16-currency enrollment loop.

The8 selected new contribution methods contain overlapping operation captures;
the9 unique RPC states are not9 additional features. Cold gasleft figures are
retained [separately](contributions/VERIFICATION.json). They exclude intrinsic
gas/refunds and retain same-test transaction-original storage limitations; they
do not substitute for these actual RPC estimates.

## Tested optional workflow: synchronize before activation

Existing `RoyaltyRewards.syncAll()` can move pending allocation out of the
activation transaction. Two NEW sequential, read-only local EVM workflows
preserve the exact activation calldata, expiry, market, LP, owners, shares and
fee reserves. The actual synchronization trace supplies the successor state;
there is no guessed tree flattening or deleted liability.

| Previously over-budget healthy state | Sync estimate plus20% /12M | Same entry after sync, estimate plus20% /20M |
| --- | ---: | ---: |
| ZZZ activation, pending receipts |2,175,852|18,637,445 |
| ETH activation, first opening allocation |2,826,374|18,145,254 |

Both stages pass their exact padded calls. Every one of the17 currencies keeps
the incumbent's1601 units and the late entrant's zero older entitlement. Only
the royalty ledger's captured storage changes; the simulated empty-code sync
caller's exact nonce increment is retained in the new owned genesis, never
adopted into a real wallet or journal. All nodes are stopped. [RPC and transition evidence](rpc/REVIEW.md).

This is an optional **separate operator-paid transaction**, not aggregate gas
savings or an additional required holder step. It adds no worker or automatic
submission. `syncAll` is atomic and a broken currency can make it revert; selected
healthy `sync(asset)` remains an existing separate function. New receipts,
activations or trading can change the next review: simulate the exact entry
again after confirmed synchronization. Neither every16-fault case nor arbitrary
maximum-state activation is fixed/qualified by these two workflows.

## Large royalty-accounting states

Four new **component-only** cases use the current exact-unit royalty ledger and
16 admitted currencies. Independent ticket arithmetic checks every incumbent's
units, newcomer exclusion, backing, recovery and subsequent future-only rights.

| Royalty activation component | Measured CALL-body gas |
| --- | ---: |
|811-NFT/1023-weight rotated allocation |11,814,101 |
|999-NFT/1499-weight rotated allocation |11,460,949 |
|811-NFT state with one full-budget currency fault |12,074,797 |
| First-opening allocation |6,407,404 |

These numbers are not additive to another host's gas or proof of complete
maximum-state entry feasibility. Phase, cursor, actual mixed rarity weights and
pending allocation matter, not only participant/currency counts. [Exact scope](tail/REVIEW.md).

## Claims, failure and bounded recovery

Three new cases construct1,000 actual NFTs, the600/300/100 rarity stock,
1,500 royalty tickets, four logical LP accounts and unequal per-NFT shares.
Actual transfers establish the current claimant. A declared typed accounting
writer seeds LP books; this is not physical liquidity or OpenSea acceptance.

- A pending19-entry royalty/LP selection refuses12M atomically.
- A stored19-entry selection succeeds at7,766,624 CALL-body gas.
- 32 stored LP entries across16 current-owner NFTs/four buckets refuse12M.
- Existing smaller selected batches recover exact payments without raising12M.
- A deliberately failing final royalty transfer reverses earlier payouts;
  healthy selected currencies and later recovery preserve every observed right.

The first calls start from cold funded setup state. Later recovery chunks are
functional bounded recovery in that test, not separate cold transaction/RPC
qualifications. Raw fixed-ZZZ LP recovery is included deliberately; normal
ETH-only settlement still needs its separately qualified conversion.
[Results and retained fixture failures](claims/REVIEW.md).

## Scope and evidence hygiene

There are19 distinct new focused methods:8 contribution,4 royalty-component,
3 claim and4 backend. Earlier stages and corrected-fixture reruns are not added
to that count. No unchanged old regression suite, normal production build,
static campaign or public provider campaign is rerun.

The first contribution fixture incorrectly recreated a sealed graph twice in
two methods; later methods retain one coherent graph. Initial gas events were
not captured and are not used as current measurements. A missing test-only
getter, excessive setup access recording and export-permission/configuration
failures are retained, rather than described as contract failures or passes.
Only an owned export-directory filesystem permission was temporarily added;
the exact original Foundry configuration was restored. Code generation and
financial/operating limits never changed. Large verbose raw traces remain
outside Git with exact hashes; public compact method summaries are explicitly
lossy. Current artifacts/source proofs and runtime-metadata limits are separate.

## What remains open

Q03 remains open for complete maximum-state **whole-graph** activation and
maintenance, optional residual/currency expansion and actual admitted-token
behavior. Passing a component test, simple16-currency state or body call does
not close it. Real feeds, bidirectional routes/depth, target provider/caps and
complete fees, authority/contract-wallet envelopes, live OpenSea/VRF/content,
service/website/recovery adoption and independent approval remain open.

No currency is admitted, capacity expanded, sync allowance lowered or gas profile
raised automatically. No claim right or liability is removed to obtain a fit.
Sites/services, Anvil8902, databases/journals, public-null configurations, shared
Anvil-only signer and the user-paused heartbeat remain unchanged.
