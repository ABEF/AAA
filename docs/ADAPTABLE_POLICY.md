# Configurable operating policy

Fresh accounting6 / ProtocolPolicy1 / Portfolio2 source candidate. **Production
NOT APPROVED.** This does not upgrade an existing deployment, worker, journal,
website or wallet signer. [Operator procedure](OPERATOR_MANUAL.md#future-operating-settings)
and [exact profile](POSITION_V6.md).

## What can change

The separately deployed `ZZZProtocolPolicy` is bound once by bootstrap through
`Access.bindProtocolPolicy(implementation)`, before its consumers are deployed.
Sealing checks its controller/version and mint recipient. The address stays fixed
after sealing; governance changes bounded values, not implementations or custody.
It holds no funds, grants no approvals and has no arbitrary executor or sweep.

| Control | Initial operating value | Governed bounds / effect |
| --- | --- | --- |
| Activation / growth minima | $100 / $5, USD18 | Each at least $1; growth no greater than activation. An admitted pool may impose a stronger minimum. Future contributions only; existing membership/shares remain. |
| Contribution idle ceiling | 500bps (5%) | 0–4000bps, independently captured for each entry. Does not relax the actual marginal deployed-LP floor, loss limits or caller minimum. |
| Maintenance idle ceiling | 500bps (5%) | 0–4000bps, captured with its scoped revision before mutation. Main/residual utilization and retained-value checks remain independent. |
| Principal payout gas | 180,000 per isolated owner call | 100,000–1,000,000; captured once per bounded payout batch. Tail reserve and per-owner failure isolation remain. |
| Oracle source-read gas | 500,000 per bounded upstream call | 100,000–1,000,000; exact return length, freshness, dual-source and identity checks remain. |
| Optional royalty sync gas | 250,000 per isolated currency | 100,000–1,000,000; underfunded outer calls revert; optional failure still defers only that currency without taking old royalties. |
| Direct mint price | 0.05 ETH gross | Positive uint128 wei. Fresh mint reviews bind price, recipient and current VRF policy. OpenSea primary mint integration remains unfinished. |
| Future mint recipient | Deployment-selected address | Propose, then candidate itself accepts. Zero proposal cancels. Protocol accounting/custody addresses are rejected; old payments never move. |
| Enhanced / Singularity display thresholds | $1,000 / $10,000 | Positive increasing uint128 USD18 values. Existing NFT appearance may change; traits, ownership, eligibility, rewards and shares do not. |
| VRF provider / subscription / lane / payment mode | Unconfigured until reviewed | Initial setup before seal; later planned rotation only when every minted draw has finalized. No pending retargeting, reroll or selected traits. |
| Main allocation, per pool | At least60%; residual at most40% | `PortfolioPolicy.configureMainAllocation`: 6000–9999bps. Use single mode for100% main; very strict hybrid floors may be unfillable. |
| Residual gap, per pool | One full tick-spacing | Positive uint24 spacings within the TickMath domain. The selected side must still fit its real rounded range at execution. |
| Manual main range | ±25% / ±50% examples | Registry permits half-width below10000bps, subject to its existing minimum, trigger/deviation, tick alignment/domain and execution constraints. Coupled admission means width must exceed100bps. |
| Maximum buyback trade | Constructor value | `Buyback.setMaximumTradeUSD`: positive uint128 USD18, not below the current operating limit. Operating limit may be zero. Fixed ZZZ/reserve ownership never changes. |

The $1 minima and gas bounds are engineering limits, **not economic or provider
qualification**. Lower future entry costs can change future collective/royalty
participation; review this economic effect before lowering minima. Zero idle
allowance can be impossible because of rounding. Higher allowances do not promise
useful deployment or better execution. These values must never be widened
automatically to make a quote, harvest, payout or maintenance operation pass.

The optional Pyth reader retains its own immutable300,000-gas upstream cap.
Replacing/reviewing that adapter through the existing feed-admission procedure
is separate from increasing Oracle's outer source-call budget.

## Scoped reviews and callbacks

Entry2 uses `executeReviewed(request,maximumLossBps,expectedContributionPolicy)`.
Read `ProtocolPolicy.entryFingerprint()` for the unsigned review. The full
operation captures the policy before token callbacks and checks it through final
Entry allowance reset. Contributions still spend only entrant funds, prove
marginal deployed LP, and price new shares against incumbent aggregate NAV.

Fresh direct mint is `Vault.mintDormant(expectedMintPolicy)`, with exact
`Vault.mintPrice()` as native value. Read `Vault.mintPolicyFingerprint()`; this
combines sale terms **and the complete current VRF policy/revision**. Stale reviews
fail, including a change followed by restoration. Captured recipient/price are
checked after NFT/recipient callbacks; failure rolls back the entire mint.
There is no fresh no-argument mint fallback. Historical deployments keep their
own selectors and transaction-recovery profiles.

Maintenance captures its own idle policy and starting USD vector. Changes during
close/swap/mint callbacks cannot weaken that operation. Cosmetic, mint and gas
changes do not reset LP samples; entry changes do not reset them either.
Maintenance changes and relevant per-pool geometry changes invalidate their own
evidence. Other pools' geometry does not masquerade as this pool's change.

`reviewHash` is a nonzero provenance commitment, not authorization or an on-chain
proof that a human reviewed a manifest. It differs from the exact contract policy
fingerprints supplied by user transaction reviews. Keep actual state, ABI/runtime
pins, simulation and receipts alongside the review artifact.

## Planned VRF rotation

Stop new mints; inspect original requests and ordered finalization. Require
`NFT.nextToFinalize()==NFT.mintedCount()+1`, qualify the replacement's chain,
coordinator/runtime, proofs, subscription consumer, funding, lane, confirmations,
callback limits and payment mode, then call `ProtocolPolicy.rotateRandomness`.
Verify generation/revision and resume only after a fresh request rehearsal.
Different providers may reuse IDs; the same provider cannot reuse a local ID.
Existing finalized traits and inventory draws never change.

Request creation pins coordinator runtime before/after callbacks. Pending
fulfillment remains authorized to the original coordinator address even if that
provider's runtime changes, so it can drain before rotation. Codehash does not
freeze a proxy's implementation or prove VRF security. Pending provider failure
cannot be repaired by selecting new random words or rotating around the drain
rule; provider recovery and production qualification remain necessary.

## What stays fixed

ETH and the one deployment ZZZ, 1000 supply and600/300/100 quotas, finalized
artwork/traits/root, 80/10/5/5 allocation, rarity royalty weights and5% marketplace
request, exact backing/reserve/share/owner accounting, terminal holder return,
no arbitrary custody recipient/sweep/bridge, and normal10% loss ceilings.
An unsealed importer is inert: configure policy before `prepareImport`.
The fresh V6 handoff binds the policy helper/runtime/configuration commitment and
requires matching cosmetic threshold values. V5 cannot be silently imported.

## Verification limits

Source changes require fresh normal size/constructor checks, source-bound ABI
documentation and focused callback/boundary/accounting verification. Actual
feeds/routes/VRF/authorities, OpenSea, target gas/economics, operating rehearsals
and independent audit/remediation remain release gates in the [sole Todo](../TODO.md).
