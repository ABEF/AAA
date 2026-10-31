# Paused custody parking

Parking closes a shared LP and keeps its actual underlying currencies inside the
immutable Vault. It is a governed recovery action when normal price-dependent
upkeep cannot run. Parking pays no holder or administrator. The separate
[collective holder exit](HOLDER_COLLECTIVE_EXIT.md) permanently ends LP operation
and returns actual ETH/ZZZ to NFT owners; no external custodian receives principal.

Fresh [Position6](POSITION_V6.md) uses None0/Active1/reserved Outbound2/Dormant3/
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

Custody4 uses the appended nonzero `portfolioHash` field: read
`LiquidityManager.executionPortfolioFingerprint(mainId)` at the reviewed block.
It binds both actual physical IDs, full keys/bounds, custody and current liquidity.
Do not substitute stable `portfolioFingerprint`, a copied profile3 tuple or a
handmade hash. A main increase or residual change invalidates this stronger manifest.

The request binds bucket/pool, exact main LP token ID, total shares, contribution USD,
custody epoch, parking nonce, ordered accounting currencies, raw close minima,
deadline and nonzero review hash. At least one raw minimum must be positive for
a genuinely one-sided LP. Deadline must be current and no more than ten minutes
ahead. The review hash records provenance, not automatic independent approval.

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

## Exact price-independent close

Parking reads no USD or sequencer price. Native close/harvest/parking does not
call a wrapper or a creator-payment inbox.
Actual venue bindings, position ownership/key and typed settlement still apply.

Vault harvests old fees from both legs into their existing reward/reserve domains,
closes every actual main/residual LP, and records the actual new attributed idle. Migration compares only those
close deltas with the reviewed raw minima. Prior idle, Vault donations and
compound held in Fees cannot fill a close shortfall. Fees are not relabelled as
principal. Any failed token transfer, settlement or callback reverts the operation.

## Resume or choose another action

While parked, activation into the bucket, top-ups, compounding and keeper
rebalancing remain disabled. Existing principal remains nonredeemable.

| Next action | Requirements |
| --- | --- |
| `Migration.resume(bucket,pool,minimumLiquidity,deadline)` | Unpaused operating state before collective exit; enabled reviewed destination with the same native ETH/fixed-ZZZ pair, fresh prices/strategy and normal deployment/loss/idle guards. It may reuse the old pool. |
| `Migration.beginCollectiveExit(reviewHash)` | Governance starts irreversible retirement while paused; close every bucket with reviewed raw minima, allocate principal and directly distribute ETH/ZZZ to current owners. A parked bucket contributes its attributed idle and designated compound. Follow the [bounded exit procedure](HOLDER_COLLECTIVE_EXIT.md). |
| Same-chain whole-collection handoff | Before collective exit only, use compatible canonical V6 peers to preserve ownership, parked principal, both reward ledgers and exact classified backing. Follow the [handoff procedure](CANONICAL_HANDOFF.md). |

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
[earlier pruning review](../reports/architecture-pruning-20261025/REVIEW.md).
Use the [holder-exit guide](HOLDER_COLLECTIVE_EXIT.md) for current terminal return.
Actual raw minima/snapshots, authority review,
real operating gas/recovery and independent audit remain release gates. This
manual authorizes no deployment or public transaction.
