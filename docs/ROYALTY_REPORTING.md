# Royalty balances, eligibility and conversion history

The confirmed read API can report native ETH, earned non-ETH balances and deferred
currency eligibility separately. Conversion history records changes of denomination;
it does not increase claimed totals or earned revenue. This is backend source
support, not a deployed API or a live website integration.

## Enable the current ledger profile

The schema-2 read API has a separate optional `royalty_reporting` profile.
For the current governed converter, use reporting **schema 2** with its exact
runtime pin:

```json
"royalty_reporting": {
  "schema": 2,
  "converter": {
    "address": "<ledger-bound converter address>",
    "code_hash": "<reviewed deployed-runtime Keccak-256>"
  }
}
```

These are unusable placeholders. Reporting schema 2 requires a non-null converter
pin; it reads `conversionLossBps()` and verifies the hard ceiling of 1,000 bps.
The current conversion default is 100 bps (1%), governed up to 1,000 bps (10%), with
network gas separate. The observed setting is not a swap quote or permission to
execute. Typed routes, feed review and stricter caller/venue minima still apply;
see [conversion routes](TYPED_V4_ROUTES.md) and
[execution-loss controls](EXECUTION_LOSS_POLICY.md).

Use only the matching reviewed royalty-ledger/runtime ABI. The service verifies
existing module, asset, lifecycle, chain, deployment-anchor and canonical-hash
pins. It reads `canonicalController`, `activationCount`, `activationOrdinal`,
`eligibleCount`, `eligibleFor` and `converter`. Missing core getters are an
incompatible profile, not an optional currency outage. Never select profiles
from token names or silently probe arbitrary versions.

| Reporting selection | Supported meaning |
| --- | --- |
| Schema 2 with exact non-null converter pin | Current governed converter binding, enable state, operating cap and hard cap |
| Schema 1 with `converter: null` | Eligibility and isolated balances without verified converter status; usable only when the ledger supports the required core getters |
| Schema 1 with converter pin | Historical fixed 100 bps converter ABI; it cannot verify the current 1,000 bps ceiling |
| Profile omitted | Original strict per-asset reads; `royalty_reporting.available` is false |

A null/mismatched pin makes converter status unavailable; it does not hide
otherwise verified balances or authorize a conversion. Predecessors never inherit
this optional current profile automatically. A profile or API rollback does not
change any on-chain converter, eligibility or already executed transaction.

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

## Inactive reward integrity

Validated never-activated NFTs cannot report positive available LP or royalty
claims, with or without this optional profile. Rarity determines known x1/x2/x3
weight; activation starts eligibility without retroactive royalties. Unreadable
currencies stay unavailable/null. Activated NFTs retain owed rewards while
parked/outbound or after a market-value downgrade. Current LP inventory must
actually include native ETH first. See [current backend verification](../reports/backend-remediation-20261026/VERIFICATION.md).

## Native custody history and recovery

The current source accepts a delayed native eligibility prefix only with a
verified nonzero `custodyNonce(address(0))` and consistent cohort counts/weights.
This getter and `eligibleWeight` / `totalWeight` are required only when that
native prefix lags. Old pinned runtimes lacking the required getter fail closed.
This eligibility check is shared by both reporting profiles; it is not an
on-chain upgrade.

During external native custody, `claimable` intentionally reverts. Display ETH
unavailable/null, the NFT's known royalty weight and deferred eligibility;
preserve available LP and healthy-currency balances. The native prefix may still
lag just after full return, before the next ordinary sync. Do not manufacture
zero balances, old earnings or retroactive eligibility.

Earnings replay now authenticates `RoyaltyCustodyExited` and
`RoyaltyCustodyReturned` from the pinned ledger with exact topic/data structure,
admitted currency, unique exit ID, recipient and amount. A matching full return
restores backing without adding income. Native deferral is accepted only inside
an observed native custody interval. Full earnings reconciliation stays
unavailable while backing is external or events are missing/inconsistent; after
return it verifies the ordinary cohort recovery and current chain balances.

For a rollout, preserve original databases/configuration and back up raw history.
Replay into a separate database from the earliest affected custody interval,
retaining all anchors and intervening logs; compare both incumbent/new NFT
results and chain reconciliation before switching clients. Do not reset history,
infer missing events or repair a running service automatically. Read-service
rollback restores the prior release/configuration, not on-chain custody state.
See [fix and limits](../reports/day-readiness-20261025/royalty-matrix.md).

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
ingestion; this is not a cryptographic log-completeness or finality proof.
Processed 24h/all-time earnings and current-price USD marks use the separate
[earnings profile](EARNINGS_HISTORY.md); they are not conversion-history totals.
Only reviewed same-chain lineage is supported. See
[history trust boundaries](FRONTEND_HISTORY.md) and
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
