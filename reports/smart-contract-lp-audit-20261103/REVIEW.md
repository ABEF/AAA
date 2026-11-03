# Smart-contract audit: LP management, accounting and recovery

Reviewed3November2026 against main `e0ea4dcd4762c1c4016b7861bbacc42c2c1d72dd`.
Internal source review and targeted execution; **production NOT APPROVED**.
The [audit prompt](AUDIT_PROMPT.md) was built from the operating model and
[primary guidance](KNOWLEDGE.md), challenged twice, then executed. The
[coverage](COVERAGE.md) and [verification](VERIFICATION.md) distinguish body
review, AST inventory, new execution and exact unchanged-source evidence.

## Result and material observations

No new exploitable production-contract defect was established in this pass.
That is a scoped finding, not a guarantee that no vulnerability exists. No
production Solidity, economics, permissions, profile or deployed state changed.
Two composed actual-core regression tests and the operating/evidence records
were added. Do not weaken a guard merely because a valid operation is unavailable.

| Observation | Consequence and disposition |
| --- | --- |
| Residual gap admission is not placement feasibility. | A positive gap can satisfy the setter's absolute tick-domain bound yet leave no usable interval within the proposed main side. A new actual-core test admits such a gap, witnesses failure, proves exact rollback of the old two-leg account, then disables mode and successfully merges. Preflight geometry and the complete operation; an impossible second leg is not a reason to bypass custody or deployment floors. |
| Price-dependent NAV and raw rights have different availability. | A new actual-core journey invalidates all four synthetic USD feeds for one minute. NAV becomes unavailable, while actual two-leg fee collection, exact80/10/5/5 accounting, partial raw claims and paused residual-only closure remain usable. Recovery restores valuation and later guarded merge. This proves that scenario, not recovery from a failed core or fixed ZZZ token. |
| Optional Entry conversion is a fresh-release simplification candidate. | Both permitted contribution currencies already are the pool currencies. Converting the entire input before Vault balancing can introduce a redundant round trip. Entry's v3 branch cannot execute a fresh native-ETH/fixed-ZZZ pair route under its native/source/output restrictions; generic synthetic route tests do not qualify that pair. Removal needs an explicit fresh interface/profile and matching consumers. No removal was made; separate royalty/LP conversion remains useful and must not be deleted with it. |
| Bounded routing protects execution, not universal liveness. | Quote search uses reviewed venues after withdrawal and rejects inactive new-main candidates. A narrow budget, insufficient remaining depth, high directional fee, infeasible gap or finite search can still make every candidate fail. Failure is atomic; another approved venue/settings review or the documented raw recovery path is needed. It does not prove a global optimum. |
| Service policy is not contract authority. | Jitter and the compound wait below the adjustment threshold are keeper-service behavior. Manual authorized calls retain their actual on-chain guards; they do not acquire service-only restrictions. Do not claim the contract enforces an off-chain wait or that it prevents every keeper/external manipulation. |
| Known compiler-bug review needs current disclosures. | The official current list associates six disclosures with0.8.26. Current settings/source patterns do not establish an applicable trigger: see [assessment](compiler-assessment.json). This is conditional source analysis, not proof of compiler correctness; re-evaluate on any source/dependency/settings change. No silent toolchain upgrade. |
| Irreversible setup concern was checked and refuted. | Access.seal already requires canonical-chain NFT randomness configuration, fixed contribution/exit ZZZ identity and a valid mint recipient. It does not prove that the configured VRF subscription/provider actually works; that remains qualification. |
| Emergency and governance remain powerful by design. | Paused governance may explicitly bypass financial guards; nearly all principal can be lost. Code hashes do not freeze a proxy's implementation or prove a reviewed dependency honest. Direct governance has no delay, and repeated individually permitted maintenance losses have no cumulative on-chain breaker. Preserve these accepted trust boundaries in disclosures and rehearsals. |
| Object headroom remains tight. | Exact-source reused normal gates leave Migration20 bytes, Budget237 and Vault635. These are not edit capacity, constructor-argument qualification or target-chain gas estimates. No size result was rerun merely for test/document changes. |

## LP account and operation review

One logical bucket owns independently accounted NFT shares of one main and at
most one residual LP NFT. Both physical positions remain Vault-owned in the same
native-ETH/fixed-ZZZ pool. Raw liquidity across different ranges is never added
as value. Both actual currency amounts, attributed idle and designated compound
must be included in the relevant NAV. Rewards and buyback backing are separate.

| Action | Expected behavior and reviewed boundary |
| --- | --- |
| Activate / grow | Check owner/traits/minima/current contribution destination and exact reviewed policy. Checkpoint incumbents, receive only entrant funds, balance into the existing main, harvest incumbent fees generated by that swap, verify marginal deployed LP/net NAV, then issue shares. No residual-L change, recenter or rebalance-clock reset. Whole transaction rolls back on swap/mint/refund/callback failure. |
| Mint / reveal | Exact future sale terms and recipient fingerprint; finite1000 draw/600-300-100 quotas without replacement; authenticated original VRF request, ordered finalization, no pending reroll. Runtime pinning is not provider honesty. OpenSea primary-sale integration is still a release task. |
| Hourly harvest | Collect both registered legs through typed zero-decrease/TAKE_PAIR actions; classify actual receipts once. Fixed80% individual/10% equal-active/5% compound/5% buyback allocation, with split dust/fractions retained under their existing rules. No swap, automatic burn or payout triggered by harvesting. |
| Claim | Spend already-funded current-owner liabilities; dormant NFTs do not dilute collective rewards. Partial/repeated claims do not change another NFT's entitlement, principal, LP mode or clocks. NFT transfers carry unclaimed rights. Raw claims do not require USD valuation; a failed currency/recipient can still prevent its own transfer. |
| Convert rewards | Exact per-NFT ledger debit/output credit, approved venue and policy, actual ETH receipt and unchanged identity/backing. Conversion is not new earned income. Non-ETH raw rewards remain non-ETH until a successful qualified conversion. |
| Compound | Reinvest only attributed idle/designated compound into the existing main; never entrant funds or buyback/reward liabilities. Existing residual stays included but is not increased. Independent compound interval uses max(lastCompound,lastRebalance). The service waits for an in-range main below the adjustment threshold and no pending geometry. |
| Buyback | Spend only the designated reserve, acquire the fixed ZZZ and verify actual burn/supply reduction. ETH is swapped first when an approved route qualifies; reserving5% at harvest is not itself a burn. |
| Ordinary adjustment |85% actual centre-to-boundary distance in ZZZ-in-ETH price space; physical/reference corroboration, sampled600 seconds/maxgap300, hard initial12 hours and fresh service jitter. Close both, quote after withdrawal, perform at most one balancing swap and mint an actually active main. Recheck financial/allocation/custody context after callbacks. |
| Single / optional hybrid | Default single. Hybrid requires main>=configured floor(default60%) and at most one residual from the corresponding leftover side, default half-side width and positive spacing gap.60/40 is a replacement-time bound, not a continuous portfolio ratio. Mixed/filled/outside residual remains owned, valued and harvested. |
| Change mode / width | Desired policy is distinct from physical positions and applied revision. A setter creates no LP. Disable requests a later guarded whole merge. Changed/restored policy invalidates old evidence; same-value mode is not a cancellation shortcut. Explicit geometry change is the cooldown-gated trigger exception. |
| Close only residual | Paused governance with exact physical/control fingerprint, source pool, raw minima, shared parking nonce/custody epoch. Harvest both, close associated residual into Vault-attributed idle; preserve main/shares/clock. No wallet payout, swap or implicit mode change. Set mode off first to stay single. |
| Same-pair move / park / resume | Close both legs and preserve one share account. Source controls are compared with the captured source pool, not the destination. Raw parking needs no USD quote; guarded redeployment still needs valid prices/routes/budgets. Failed external token/core can prevent even raw movement. |
| Manual emergency | Separate paused-governance exact manifest, explicit optional financial checks, structural ownership/settlement retained, no generic arbitrary recipient. Scoped emergency context must clear in the same successful transaction; failure reverts it. This is not keeper automation fallback. |
| Terminal holder return | Paused governance starts an irreversible no-swap exit; close both legs and designated compound, allocate actual ETH/ZZZ by NFT shares, push bounded isolated batches to current owners. Failed recipients remain individually unpaid/retryable; earned rewards/buyback reserves are separate. Transfers/future royalties/old claims continue; LP and canonical replacement cannot reopen. |
| Canonical same-chain replacement | Parked zero-residual domain, exact semantic/runtime/config admission and finite source-authenticated rows/backing. Atomic source retirement/destination activation, fully backed abort, no integrated bridge or external custody recipient. A failed required asset can block backing; no administrator-created ownership rows or post-halt recovery. |

## Adversarial and long-term conclusions

Review followed input bounds/units, mathematical rounding, grants/revocations,
pause/preparation/terminal transitions and callback order across each component.
Actual debt/spend, stored core ticks, LP IDs/owner, allowance reset, prefunds,
per-NFT fractions, late compound, source controls and exact raw receipts remain
separate checks. Repetition around external calls protects different moments.

A local pump alone is insufficient for ordinary sampled readiness, but a
correlated/manipulated reference or a multi-minute market move can satisfy it.
Gross/additional-loss/spot floors constrain a transaction rather than eliminating
all attacker profit, LVR, impermanent loss or repeated permitted losses. Service
jitter is not cryptographic unpredictability or protected transaction inclusion.

Declared feed independence must be established outside the contract. Real
liquidity/depth, source freshness/outages, sequencer behavior, venue protocol
fees, gas, token transfer behavior, VRF funding and marketplace receipts require
actual qualification. Non-tax/non-rebase exact-transfer assumptions, rejecting
receivers and all1000-NFT/maximum-currency operating costs remain relevant.

## Changes and remaining decisions

Added the two focused EVM journeys, current compiler/source-construct assessment,
per-function review inventory, operating/recovery guidance and central records.
No production safeguard was removed, loosened or relabelled as stronger proof.

The redundant Entry-layer removal is awaiting the explicit profile/consumer
decision; it is recorded in the sole Todo. Independent source6 services/site,
reviewed dual feeds/routes/VRF, authorities, OpenSea, permanent artwork hosting,
target gas/economics, real operating/recovery rehearsals and independent audit
with remediation remain open. Historical reports retain their source scopes.
