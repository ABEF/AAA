**Current policy, 2026-10-24:** [Typed v4 conversions](TYPED_V4_ROUTES.md) and
[governed execution-loss limits](EXECUTION_LOSS_POLICY.md) are implemented in the
undeployed candidate. Defaults are 1% contribution, 1% conversion and 3% maintenance;
immediate governance may set each category up to a hard 10%. Existing stricter
venue/caller minima remain. Pending normal custody approvals retain their original
absolute floor. Earlier fixed-cap or v3-only descriptions below retain their
historical/default scope. Actual routes, services and independent audit remain open.

# Royalty balances, eligibility and conversion history

The confirmed read API can report native ETH, earned non-ETH balances and deferred
currency eligibility separately. Conversion history records changes of denomination;
it does not increase claimed totals or earned revenue. This is backend source
support, not a deployed API or a live website integration.

## Enable the current ledger profile

In the reviewed schema-2 API configuration, add this optional field:

```json
"royalty_reporting": {
  "schema": 1,
  "converter": null
}
```

Use it only with the reviewed current royalty-ledger runtime/ABI. Existing module,
asset, lifecycle, chain, deployment-anchor and canonical-hash pins remain required.
The profile calls `canonicalController`, `activationCount`, `activationOrdinal`,
`eligibleCount`, `eligibleFor` and `converter`; an old ledger lacking those methods
is incompatible, not a recoverable currency outage. Do not infer a profile from
a familiar token name or silently probe arbitrary contract versions.

To verify converter status too, replace `null` with an object containing exactly
`address` (the ledger's bound nonzero converter address) and `code_hash` (its
reviewed deployed-runtime Keccak-256, including immutables). No placeholder address
or hash is supplied. A null/mismatched pin makes converter status unavailable; it
does not hide otherwise verified balances or create permission to convert.
The API verifies the helper's ledger/controller binding, enabled flag and fixed
100-basis-point execution limit. Network gas is separate.

Without this profile, existing strict per-asset reads continue and
`royalty_reporting.available` is false. This avoids interpreting old contracts
through a new ABI. History replay is independent of the opt-in; predecessor
deployments never inherit the current converter/profile automatically.

## Response fields

`GET /v1/nfts/{token_id}` retains exact decimal raw-unit strings. ETH is represented
by the zero address and 18 decimals. Do not combine raw units of different assets.

| Field | Meaning and consumer rule |
| --- | --- |
| `claimable.royalties[].raw` | Current contract-view claimable amount for this NFT/currency, or null when unavailable. Native ETH already includes any unclaimed conversion credits. |
| `available`, `asset_verified`, `reason` on each balance | A failed reviewed token runtime/decimal check or failed claimable view is explicit. Display unavailable, never zero. Error reasons are fixed strings, not raw provider responses. |
| `eligible`, `eligibility` | `inactive` before activation; `eligible` for an admitted currency; `deferred` when activation succeeded but membership for that currency waits for recovery. Rarity still sets x1/x2/x3; it does not change while registration waits. |
| `unconverted_raw` | For non-ETH only, the current source-currency claimable amount. This is not a queued swap, an ETH quote or an additional balance to add to `raw`. Native ETH uses null. |
| `royalty_reporting.balances_complete` | Whether all royalty balance views are available at this snapshot. Eligibility can remain readable while a balance is unavailable. |
| `royalty_reporting.converter` | Verified binding/enable control when configured; unavailable with a reason otherwise. It does not qualify routes, prices, keeper operation or gas. `next_execution_at` stays null. |
| `previously_claimed` | Lifetime actual LP and royalty payouts, per asset and NFT, including past owners and complete verified same-chain predecessors. Conversion credits are excluded. |
| `royalty_conversions` | Lifetime source amounts converted and ETH credited, per source asset, event counts and latest event provenance. This is neither remaining claimable funds nor newly earned revenue. |

Under this profile the same explicit availability fields also apply to
`claimable.lp`: if a currency is used by both ledgers, a failed token verification
affects both balances. Healthy currencies remain readable. Unknown admitted assets,
bad core modules, impossible eligibility counts, lifecycle locks, stale/reorged
snapshots and request work-limit failures reject the complete response. No partial
response survives the final canonicality/freshness checks. Wallet inventory and
transaction validation retain their stricter paths; this profile is limited to
the single-NFT balance view and does not authorize a financial action.

Deferred membership is checked against the ledger's activation ordinal and
currency eligibility prefix. On recovery the contract protects earlier receipts,
then admits waiting NFTs for future receipts. The API reports that state; reading
it does not submit `sync`, activate an NFT or execute conversion.

## History and amounts that must not be counted twice

The indexer schema includes `RoyaltyConverted` and currency eligibility/control
events. Financial history replays the exact `RoyaltyConverted` signature and
indexed fields only from the configured royalty ledger. It verifies admitted
source currency, minted NFT identity and canonical log structure against complete
confirmed raw history. Optional decoded event labels are not trusted.

For example, conversion of 10 units of an NFT's earned currency into 0.005 ETH
changes the denomination of that entitlement. `previously_claimed` is unchanged.
Only a later actual `Claimed` payout adds to its cumulative paid total. The ETH
claimable view already contains the conversion credit, so never add lifetime
`eth_credited_raw` to it. A sale changes the owner of unclaimed rights; it does not
erase this NFT's historical claims or conversion records.

When history is complete, conversion records include source amount, ETH amount,
event count and the last ledger/block/hash/timestamp/transaction/log index. Existing
raw-log ingestion can supply records even if an older decoder labelled them
unknown. Zero-per-NFT rounding outputs are permitted; they are not fabricated
claims. Matching same-chain retirement/activation boundaries permit merging up to
the configured predecessor limit, including historical currencies absent from the
current deployment. Missing lineage returns unavailable lifetime totals; invalid
configured lineage or incomplete ingestion rejects the projection.

The operator-maintained SQLite store and pinned RPC are still trusted for complete
ingestion; this is not a cryptographic log-completeness or finality proof. Gross
earned revenue, 24-hour/all-time USD pricing and cross-chain history remain outside
this feature. See [history trust boundaries](FRONTEND_HISTORY.md) and
[predecessor verification](FRONTEND_LINEAGE.md).

## Operating and recovery procedure

1. Review current runtime/ABI pins, admitted currencies, the optional converter
   pin, and the exact API release. Back up API configuration and complete indexer
   data. Keep keys and RPC credentials outside reports and Git.
2. Enable the profile in a local/staged configuration and query a dormant NFT,
   eligible NFT and deferred-currency case. Verify separate ETH/source balances,
   null failure states, converter disabled/unavailable states and history fields.
   Use [local API operation](FRONTEND_API.md#local-operation-and-verification).
3. Publish the reviewed service configuration only after client compatibility,
   actual provider/archive support and operating qualification. Source support
   does not change a running server automatically. Do not infer that a displayed
   enabled converter will execute at a promised time.
4. On currency failure, keep its unavailable amount explicit and investigate the
   runtime/decimals/call fault. Do not automatically replace pins to accept drift.
   After reviewed recovery, query fresh state. Currency synchronization and
   conversion use the separate [settlement procedure](ROYALTY_SETTLEMENT.md).
5. On stale/incomplete history, recover/backfill/reconcile the original indexer
   coverage and retirement cutoffs. Do not delete data or reset the start block
   to manufacture zero lifetime claims. An old decoder label alone needs no raw
   database reset; incomplete raw ingestion does require reviewed backfill.
6. To roll back reporting, remove the profile or restore a compatible verified
   API release/configuration and disable dependent UI features. Legacy reads may
   fail on a broken currency; they must not pretend to show eligibility. API
   rollback does not reverse conversion, claims or any on-chain state.

The [operator manual](OPERATOR_MANUAL.md), [scoped verification](../reports/royalty-reporting/VERIFICATION.md)
and [central Todo](../TODO.md#task-royalty-reporting) define operating and release
boundaries. No signer, broadcasting, service deployment or website modification is
part of this change.
