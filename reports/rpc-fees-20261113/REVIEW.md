# Robinhood tracing and complete-fee qualification

13 November2026; baseline `0330a98a0be91c979fcba291258eb6019e528b1f`.
**Pinax now has an actual canonical trace/log witness. Target fee components
and receipts are reconciled. A future-only keeper fix avoids a proven fee
accounting mismatch. Full production provider/PoPL fee approval remains open.**

No contract, financial safeguard, gas default, live service/configuration/site,
browser signer, existing Anvil/journal or paused heartbeat changed. Only the
explicit keeper source opt-in and its new focused tests/runner entry are added.

## What was established

| Area | Actual evidence | Qualification boundary |
| --- | --- | --- |
| Trace/log interface | Pinax4663, exact retained WETH runtime, canonical-hash discarded approve0, expected Approval log through unchanged production helper | Actual method witness; not full provider or deployment approval |
| Canonical controls | Matching before/after numbered/hash headers; missing hashes rejected by call, estimate and trace | Point-in-time RPC observations, not consensus/finality proof |
|20M/24M fields | Both accepted on cheap calls/estimates; explicit execution parameters32M | Not demonstrated numerical full-work/provider capacity; synthetic header2^50 is not capacity |
| Posting fees | Ten exact previously captured payloads passed to L1-only NodeInterface estimation | Real target data-fee components; no public execution of undeployed PoPL |
| Inclusive total | Actual full approval components, independently rechecked inclusion header and two genuine ordinary receipts | Nitro model/observations, not complete PoPL operation quotes |
| Future keeper fees | New explicit profile2,14focused methods and one unsigned installed-Cast construction | Source candidate; no actual signer, broadcast, deployment or operating acceptance |

[Network observations](network/REVIEW.md), [fee analysis](fees/REVIEW.md),
[software boundary](software/README.md), [verification](VERIFICATION.md).

The tracing witness is a500,000-gas zero-ETH simulation; its actual gas is33,237.
It changes no real allowance. WETH is only the existing probe token, not another
contribution asset. Mainnet PoPL is undeployed; neither an empty account at a
local Entry address nor an injected code/state override was used as a fake
complete financial-operation result.

## The fee defect and narrow correction

At canonical block113263446 (09:50:48UTC), an actual type2 transaction with a
50,000,000wei priority cap paid the20,100,000wei base fee. `getCollectTips()` was
false. The generic Ethereum helper instead derives70,100,000wei. For56,722gas,
that is3,976,212,200,000wei instead of the observed1,140,112,200,000wei:
**2,836,100,000,000wei of overstatement**. It can unnecessarily consume daily
budget; it does not transfer that difference out of the wallet.

Changing all fee calculations to trust `receipt.effectiveGasPrice` or assuming
one mutable Nitro tip policy forever would weaken verification. Instead,
explicit future `submission_fee_profile:2` is limited to Robinhood4663,
`receipt_fee_policy:"included"`, and zero separate L1 allowance. It fixes
**type2 / priority0 / the captured max fee** through initial simulation,
estimation, final LP simulation and Cast arguments. Zero priority gives the
canonical base price under either tip-collection setting. Recovery requires
that actual signed shape and a receipt price matching canonical base.

The new pending `fee_review` schema2 adds exactly
`execution_fee_model:"eip1559_zero_tip"`. Original schema1 records remain original,
even under a new future configuration. Omission/profile1 retains its original
order, command and accounting. The generic Ethereum helper is byte-identical.
No allowance, nonce, gas-price, transaction/day, value, balance, runtime,
authority, deadline, callback, financial or pending-first control is relaxed.
No automatic fee bump, resend, profile upgrade or unsafe fallback is added.

The installed Cast1.4.4 builder produced one strictly decoded **unsigned** type2
transaction for chain4663 with priority0 and fixed fields. It used no key,
keystore, wallet or public endpoint. This verifies the builder/flag boundary,
not actual signing, broadcast, inclusion or host qualification. New tests use
an inert signer and the genuine zero-tip public receipt with a clearly synthetic
test journal; they do not claim PoPL submitted that transaction.

## Complete fees, without double counting

Robinhood/Nitro estimates include the L1 posting component in total gas.
`gasEstimateComponents` exposes total gas, L1 gas, prospective L2 price and L1
price; the L1-only getter does not execute the destination. The ten payload
observations now contain nonzero posting gas (546–1,062units), demonstrating
that earlier zero snapshots were not a permanent waiver.

An inclusive total must not have another L1 charge added. NodeInterface's
prospective price, the inclusion header base fee and a later `eth_gasPrice`
need not be identical. Keep their times/contexts separate. Fee history is
observational, not an approved future price cap. Full20% contribution and25%
keeper padding,20M/24M ceilings and all operator fee/funding/day limits remain.

The [fee results](fees/RESULTS.json) preserve components and exact calculations.
They do not label Anvil execution gas multiplied by a live price as a real
Robinhood PoPL quote. An approved fee-review hash and spending ceilings cannot
be invented from a successful small witness.

## Failures, reuse and release limits

There were56new RPC attempts:50valid results, three explicit missing-hash RPC
errors, one Triport HTTP403 and two restricted-network transport failures.
The restricted failures remain separate from the permitted campaign; the403
was not retried or bypassed. Previous denied endpoints/methods were not retried.
No chain-wide outage or provider independence is inferred. [Exact index](network/RPC.json).

All previous contract traces,100-source normal build and static evidence are
reused only for unchanged source. No unchanged Solidity, Python or browser suite,
normal/static build or local fork was rerun. Fourteen new keeper methods passed;
the runner lists965methods and executes zero during inventory. Source/data
hashes bracket those results, with baseline and post-fix evidence kept separate.

The existing `keeper.probe` remains the reusable tool. No duplicate CLI was
introduced. Its full activation_api_v1 pass is not claimed: the observed genesis
hash is not an independently reviewed input pin, and further profile/history/
service checks remain. The trace-specific missing-hash wording is preserved as
an explicit rejection while the strict generic classifier still calls that
wording unclassified; no arbitrary error is promoted to success.

Still required: independent genesis/full provider profile; real numerical
call/estimate/trace capacity and response/time/archive/plan reliability; complete
exact PoPL estimates against deployed or separately authorized target state;
independent feeds/routes/depth; representative maximum workload; explicit fee
ceilings and approved configuration/source/consumer; actual signer/host/recovery,
OpenSea/VRF/authorities and independent review. Source publication adopts nothing.

Use the [operator procedure](../../docs/OPERATOR_MANUAL.md#robinhood-rpc-fees)
and [sole Todo](../../TODO.md). Do not roll old source onto schema2 pending,
rewrite old spend/reviews, reset journals or widen caps to obtain a pass.
