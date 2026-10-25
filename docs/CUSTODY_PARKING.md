# Paused custody parking

Parking closes a shared LP and keeps its actual underlying currencies inside the
immutable Vault. It is a governed recovery action when normal price-dependent
upkeep cannot run. Parking itself pays no holder or administrator; the separate
[trusted custody exit](GOVERNED_CUSTODY_HANDOFF.md) has different authorization.

Current [Position3](POSITION_V3.md) uses None0/Active1/Outbound2/Dormant3/Parked4.
`Parked` is value4, not historical value6. Bucket identity, NFT shares, membership
and accrued rights remain attached; LP token ID becomes zero and returned
principal is attributed to that bucket's idle ledger. Closed LP earns no fees.

## Authorization and input review

The system must be sealed, canonically operating and paused. The actual selected
governance wallet calls `Migration.park(ParkingRequest)` directly; Access has no
scheduler, executor or canceller role. Guardian can pause, but cannot park or
receive assets. Reviewed parking may drain preparation while canonical freeze
still blocks ordinary custody mutation.

The request binds bucket/pool, exact LP token ID, total shares, contribution USD,
custody epoch, parking nonce, ordered accounting currencies, raw close minima,
deadline and nonzero review hash. At least one raw minimum must be positive for
a genuinely one-sided LP. Deadline must be current and no more than ten minutes
ahead. The review hash records provenance, not automatic independent approval.

A pending custody plan blocks parking. LP rebalancing, changed shares, epoch,
contributions, pool/currencies or nonce invalidates stale authorization. There
are no remote home/location fields to copy into the request. Nonce increments
before external work; failure reverts nonce, principal and fee changes together.

Governance may advance `invalidateParking(bucket)` to invalidate unused request
data. To abandon an unsent custody plan use `Migration.cancel(id)`; to end a
preparation notice use `AccessController.cancelPreparation(hash)`. None reverses
completed transfers or restarts an LP, and no queued-operation cancellation exists.

## Exact price-independent close

Parking reads no USD or sequencer price. Creator-payment inbox synchronization
has been removed. Native close/harvest/parking does not call WETH or its policy.
Actual venue bindings, position ownership/key and typed settlement still apply.

Vault harvests old fees into their existing reward/reserve domains, closes the
LP, and records the actual new attributed idle. Migration compares only those
close deltas with the reviewed raw minima. Prior idle, Vault donations and
compound held in Fees cannot fill a close shortfall. Fees are not relabelled as
principal. Any failed token transfer, settlement or callback reverts the operation.

## Resume or choose another action

While parked, activation into the bucket, top-ups, compounding and keeper
rebalancing remain disabled. Existing principal remains nonredeemable.

| Next action | Requirements |
| --- | --- |
| `Migration.resume` | Unpaused operating state, no pending custody plan, enabled reviewed destination with the same ordered pair, fresh prices/strategy and normal deployment/loss/idle guards. It may reuse the old pool. |
| Normal custody `approve` / `exit` | Separately reviewed paused source snapshot, exact custodian and original aggregate/output floors. Convert attributed principal to fixed ZZZ; actual swaps/feeds must work. |
| Explicit raw custody `approve` / `exit` | Separate raw approval and positive raw minima; sends actual ETH/ZZZ without swap or USD reads. Custodian risk is accepted; no normal USD floor is promised. |
| Same-chain whole-collection handoff | Resolve external custody, freeze/export local V4 ownership and both reward ledgers, preserve exact backing, then activate one reviewed successor. This is not a bridge. |

Resume releases only designated compound and redeploys actual principal; stale
prices or venue failure leave the bucket parked with unchanged shares. Returning
external custody restores parked assets and does not automatically unpause or
reopen the LP. External issuer migration/bridging happens under the chosen
custodian's control; a replacement ZZZ requires fresh reviewed deployment.

## Holder rights and limits

Parking preserves ownership, fixed traits, LP shares, rarity royalty weight and
equal collective eligibility. Current holders retain funded LP/royalty claims;
transfers carry accrued unclaimed and future rights. No creator-payment inbox or
synthetic continued LP income exists. Current marked LP value is unavailable
while parked; metadata uses its labelled Activated fallback without inventing a
USD value or revoking activation.

No contract can force a failed PoolManager, frozen/nontransferable token, broken
recipient or halted chain to return assets. Raw mode avoids price/swap dependency,
not venue settlement or exact-token requirements. Historical custody/native2/
delayed-governance evidence retains its recorded source scope; [current review](../reports/architecture-pruning-20261025/REVIEW.md)
records later changes separately. Actual raw minima/snapshots, authority review,
real operating gas/recovery and independent audit remain release gates. This
manual authorizes no deployment or public transaction.
