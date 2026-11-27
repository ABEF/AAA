# Paused custody parking

Parking closes a shared LP and keeps its actual underlying currencies inside the
immutable Vault. It is a governed recovery action when normal price-dependent
upkeep cannot run. Parking pays no holder or administrator. The separate
[collective holder exit](HOLDER_COLLECTIVE_EXIT.md) permanently ends LP operation
and returns actual ETH/ZZZ to NFT owners; no external custodian receives principal.

Fresh [Position7](POSITION_V7.md) uses None0/Active1/reserved Outbound2/Dormant3/
Parked4/Exited5. Parking is reversible; Exited is terminal. Bucket identity,
NFT shares, membership and accrued rights remain attached; main LP token ID and residual association become
zero and returned principal is attributed to that bucket's idle ledger. Closed
LP earns no fees.

<a id="authority-and-exact-authorization"></a>

## Authorization and input review

The system must be sealed, canonically operating and paused. The actual selected
governance wallet calls `Migration.park(ParkingRequest)` directly; Access has no
scheduler, executor or canceller role. Guardian can pause, but cannot park or
receive assets. Reviewed parking may drain preparation while canonical freeze
still blocks ordinary custody mutation.

Custody4 introduced, and fresh custody5 retains, the appended nonzero `portfolioHash` field: read
`LiquidityManager.executionPortfolioFingerprint(mainId)` at the reviewed block.
It binds both actual physical IDs, full keys/bounds, custody and current liquidity.
Do not substitute stable `portfolioFingerprint`, a copied profile3 tuple or a
handmade hash. A main increase or residual change invalidates this stronger manifest.

The request binds bucket/pool, exact main LP token ID, total shares, contribution USD,
custody epoch, parking nonce, ordered accounting currencies, raw close minima,
deadline and nonzero review hash. Current runtime permits explicit zero for
BOTH raw minima, including one-sided LP; this accepts the actual returned mix.
Every positive supplied minimum remains binding. Deadline must be current and
no more than ten minutes ahead. The review hash records provenance, not automatic
independent approval. Historical runtimes can differ despite sharing the tuple.

The request must still match those live fields. LP replacement, changed shares,
contributions, pool/currencies, epoch or nonce can invalidate it. It does not bind
every reserve balance or future market price. The fresh portfolio hash does bind
current physical liquidity; still review both token amounts and raw close minima. There are no remote home/location fields or
external-custody plans. Nonce increments before external work; failure reverts
nonce, principal and fee changes together. Parking is blocked once collective
exit starts.

Governance may advance `invalidateParking(bucket)` to invalidate unused request
data. To end a preparation notice, use `AccessController.cancelPreparation(hash)`.
Neither action restarts an LP or reverses completed work. There is no custody
`cancel`, `approve` or external-address `exit` function in this release.

## Prepare the exact call without signing

The [typed management preparer](MANUAL_LP_PREPARATION.md#custody-and-terminal-management-selections)
supports `park`, `close_residual` and guarded `resume`. Supply exact reviewed raw
floors or positive new-L minimum, bucket/destination and original expiry. It
fetches the14-word parking manifest, physical portfolio fingerprint, current
shares, nonce/epoch and source-bound review hash; no manual hash substitution is
needed. Raw close remains price-independent and does not require ordinary pool
operations readiness. Park can drain during preparation; residual-only close
requires preparation to be inactive. Both preserve the actual paused state.

Resume must be prepared separately while unpaused. It retains normal prices,
loss/idle/deployment guards and accepts the same or another compatible reviewed
pool; it is not an automatic force fallback. Deposits-disabled/operations-enabled
destinations can receive resumed existing LP. Existing bucket aliases cannot be
reassigned. The tool neither signs nor changes pause state, mode or pending work.
After actual execution inspect the receipt and source state before preparing
the next step. The earlier [source verification](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/operator-management-20261109/REVIEW.md)
retains its injected-RPC scope. The [earlier actual local rehearsal](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/manual-recovery-rehearsal-20261115/REVIEW.md)
includes a production-CLI park receipt followed by schema2 D14 recovery on the
same newly owned chain at `da24f65`; it does not approve a live provider or
deployment. The [current manual reference-swap fix](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/manual-reference-swap-fix-20261115/REVIEW.md)
has separate source/verification evidence.

## Exact price-independent close

Parking reads no USD or sequencer price. Native close/harvest/parking does not
call a wrapper or a creator-payment inbox.
Actual venue bindings, position ownership/key and typed settlement still apply.

Vault harvests old fees from both legs into their existing reward/reserve domains,
closes every actual main/residual LP, and records the actual new attributed idle. Migration compares only those
close deltas with the reviewed raw minima. Prior idle, Vault donations and
compound held in Fees cannot fill a close shortfall. Fees are not relabelled as
principal. Any failed token transfer, settlement or callback reverts the operation.

## Explicit raw floors and forced re-entry

Fresh source permits paused governance to set BOTH `minimum0` and `minimum1`
to zero, including for residual-only close. This deliberately accepts the actual
returned token mix; it is not a safe default recommendation. A positive submitted
floor still binds exactly. Market movement can turn a formerly two-sided LP
wholly into one currency without changing its fingerprint. All custody, current
physical-principal, actual receipt, nonce/epoch, deadline and reserve checks stay.

To put parked funds back into the CURRENT pool under explicitly selected
emergency protections, remain paused and prepare a fresh
`Migration.emergencyRebalance(request)`. The [schema2 Parked D preparer](MANUAL_LP_PREPARATION.md#parked-emergency-recovery-explicit-schema2)
fetches exact custody/control inputs and produces the same unsigned contract
call. Supply `schema:2`, `action:"D"`, `expected_position_status:"parked"`, reviewed
ticks, exact optional admitted swap, positive output/new-L floors and original
deadline. Explicitly select retained bits2/4/8; bits1/16 require an Active main
and cannot be retained here. Bit4 still needs USD sources without bit2. Mask0
bypasses every optional category and may accept severe loss or inactive placement;
it is never selected automatically. Mandatory governance/lifecycle, native-pair
admission, exact custody, balances, callbacks, caller floors and atomic rollback
remain. Funding comes only from attributed idle and designated compound, not
holder rewards/buyback/royalties. Recovery creates one main, stays paused and
requires actual receipt/post-state review before a separate unpause. See the
[force procedure](OPERATOR_MANUAL.md#force-close-and-redeploy-choose-the-correct-call).
Ordinary `resume` remains guarded and may choose another reviewed same-pair pool.
Old runtimes may reject both-zero floors despite sharing the same ABI/version;
verify exact source/runtime pins rather than relabeling installed contracts.

## Recovery outcome and current reference-swap protection

The [baseline local rehearsal](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/manual-recovery-rehearsal-20261115/REVIEW.md)
at `da24f65` verifies both-leg parking and Parked D14 recovery through production
CLIs, exact padded calls and included local receipts. Parking increments
`parkingNonce` by 1, preserves `custodyEpoch`, previous centre/rebalance time and
last compound, and leaves designated compound in Fees. Recovery releases only
designated compound with attributed idle, creates one Vault-owned main and
updates last rebalance to inclusion time; it does not increment either custody
counter or reset last compound. Shares, active/dormant rights, old claims,
buyback backing and protected prefunds remain separated.

Neither step unpauses. D also leaves desired residual mode unchanged: one
physical main does not prevent a later ordinary adjustment from creating a
residual. Set mode OFF through governance **before preparing** D if that is the
intended continuing policy. C consolidation instead completes mode OFF, advances
its control revision, increments both parking nonce/custody epoch and updates
last compound while preserving the main and rebalance clock.

Checks14 recovery still requires working financial protections. The baseline
traces reproduced the former reference-as-swap rejection. In the
[current source](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/manual-reference-swap-fix-20261115/REVIEW.md), retaining
bit2 or4 starts a whole-operation captured scope before the first emergency
fingerprint. Manager proves the exact caller-selected swap output/full core
post-state before settlement and revalidates live sources, controls and callbacks
through deployment/final fingerprint. Bit4 uses the starting USD vector even
without bit2; bit8 remains independent. Masks0/8 introduce no Oracle-health read,
and Parked still cannot retain Active-only bits1/16.

A reviewed external reference may now be the explicit swap venue without
removing financial guards. It still cannot be the same-core principal LP
destination. Manager-only nonsettling `quoteSwap` keeps structural admission and
does not itself restore a deliberately omitted operations flag; actual Manager
execution applies retained bit8. Real source-agreement, spot/loss/idle limits and
caller floors can still block a trade. No success or front-running guarantee,
route substitution or checks0 fallback is added. Explicit checks0 remains an
emergency choice that can accept near-total loss; mandatory custody, caller
floors and settlement checks remain.

Unchanged capability numbers do not identify the updated runtime. Review exact
fresh source/runtime/consumer pins and preserve old profiles, artifacts and
pending journals under their original identities; no installed instance changes.

At the historical `da24f65` baseline, Parked D14 uses 8,822,193 estimated gas, 11,027,742 with full 25% padding and
8,181,893 receipt gas. Explicit D0 uses 3,007,714 / 3,759,643 / 2,626,114 respectively.
Both passed the full 24M cap and exact padded call under a local 32M block bound.
These controlled token/feed/VRF/Permit2/depth and local-admission results do not
qualify real markets, target-chain fees, maximum workloads or production operation.
These values do not qualify the updated source; use its report for current gas.
Use the [historical gas/post-state table and current strictly owned-node reproduction](MANUAL_LP_PREPARATION.md#local-manual-recovery-rehearsal)
with `scripts/rehearse-manual-reference.py` and its matching new host;
no existing Anvil, journal or public funds are used by that helper.

## Resume or choose another action

While parked, activation into the bucket, top-ups, compounding and keeper
rebalancing remain disabled. Existing principal remains nonredeemable.

| Next action | Requirements |
| --- | --- |
| `Migration.resume(bucket,pool,minimumLiquidity,deadline)` | Unpaused operating state before collective exit; enabled reviewed destination with the same native ETH/fixed-ZZZ pair, fresh prices/strategy and normal deployment/loss/idle guards. It may reuse the old pool. |
| `Migration.beginCollectiveExit(reviewHash)` | Governance starts irreversible retirement while paused; close every bucket with reviewed raw minima, allocate principal and directly distribute ETH/ZZZ to current owners. A parked bucket contributes its attributed idle and designated compound. Follow the [bounded exit procedure](HOLDER_COLLECTIVE_EXIT.md). |
| Same-chain whole-collection handoff | Before collective exit only, use compatible canonical V10 peers to preserve ownership, parked principal, both reward ledgers and exact classified backing. Follow the [handoff procedure](CANONICAL_HANDOFF.md). |

Resume releases only designated compound and redeploys actual principal under
the supported source path; ordinary optional residual creation remains bound to
an authenticated replacement context, not an arbitrary Manager call. Verify the
resulting actual IDs and desired/applied geometry rather than assuming a residual.
Stale prices or venue failure leave the bucket parked with unchanged shares. Returning
to LP operation requires the explicit resume transaction; unpausing alone does
not reopen the LP. There is no all-ZZZ conversion exit, external custody deposit,
bridge or issuer-exchange executor. A replacement ZZZ requires fresh reviewed
deployment; collective exit returns the old assets to their NFT holders.

## Holder rights and limits

Parking preserves ownership, fixed traits, LP shares, rarity royalty weight and
equal collective eligibility. Current holders retain funded LP/royalty claims;
transfers carry accrued unclaimed and future rights. No creator-payment inbox or
synthetic continued LP income exists. Current marked LP value is unavailable
while parked; metadata uses its labelled Activated fallback without inventing a
USD value or revoking activation.

No contract can force a failed PoolManager, frozen/nontransferable token, broken
recipient or halted chain to return assets. Parking avoids price/swap dependency,
not venue settlement or exact-token requirements. Historical custody/native2/
delayed-governance evidence retains its recorded source scope, including the
[earlier pruning review](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/architecture-pruning-20261025/REVIEW.md).
Use the [holder-exit guide](HOLDER_COLLECTIVE_EXIT.md) for current terminal return.
Actual raw minima/snapshots, authority review, target-chain operating
gas/recovery beyond the controlled local rehearsal and independent audit remain
release gates. This manual authorizes no deployment or public transaction.
