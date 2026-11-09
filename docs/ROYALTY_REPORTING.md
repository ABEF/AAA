# Original-currency royalty balances and history

**Mint-profile boundary:** reader/service versions named in this guide retain
their explicit profiles. In particular, source9/schema16/V9 is not V10. The new [SeaDrop mint2/schema17/V10 source](OPENSEA_MINT.md)
adds original-recipient mint books and needs matching reviewed consumers
before adoption. Existing services, checkpoints, journals, served sites and
Anvil signing are not upgraded or relabeled by the new source.


Fresh accounting7 reporting5 authenticates ROYALTY_SETTLEMENT_VERSION4, the exact
runtime and canonicalV9. Use `"royalty_reporting":{"schema":5,"converter":null}`.
Historical accounting6/reporting5/V8 retains the same royalty allocation rules
under its separately pinned graph; the version labels are not interchangeable.
Royalties stay in original units: no converter, unwrap, route, feed or keeper
is required for a raw claim. LP conversion remains independent.

| Reporting | Royalty capability | Scope |
| --- | --- | --- |
|5|4|Current GCD-normalized whole-unit allocation and one-hour opening. |
|4|3|Historical opening window with scaled royalty fractions. |
|3|2|Historical original-currency allocation without the opening window. |
|1/2|Earlier|Their separately pinned conversion/custody semantics only. |

Never relabel old runtimes, histories, transaction journals or checkpoints.

## Balances and opening state

Read separate addresses, raw amounts, decimals and symbols. WETH is not ETH;
never add incompatible raw currencies. Missing reads/metadata stay unavailable,
not zero. Missing USD prices do not prevent supported original-unit claims.

Opening status contains configured, mint_end, claims_open_at, claims_open,
activation_window_seconds3600 and status. Both backend and website check the
deadline/flag against the SAME confirmed snapshot timestamp. An inconsistent
flag or a positive locked royalty claim is rejected. Dormant cards show no
deadline. LP-only balances and claims remain independent of the royalty lock.

Use effectiveEligibleCount for the cutoff/outage cohort. Fresh NFT views read
ticketStart and allocationCursor, not removed royalty index/SCALE/fraction
getters. Source ticketStart is ONE-based(first1,dormant0); internal replay/checkpoint
`ticket_offsets` are ZERO-based. Convert only at the explicit source boundary.
The currency cursor is zero-based raw weight, not an NFT ticket start. Old readers
retain their explicit getter sets.

## Exact earned and paid history

For settlement4, RoyaltiesAllocated is the sole income-credit event. Reconstruct
the captured activation prefix, its GCD-normalized weights, original ticket
mapping and raw cursor. The receipt, InitialRoyaltiesAllocated and recovery
events also record provenance/lifecycle, but never credit that income again.
Claims, transfers and canonical import are not new income. Claims alone record
actual paid amounts. Current ownership carries all unpaid rights.

Replay independently checks q/remainder rotation and raw cursor divisibility;
pending initial/ordinary receipts are projected under the actual captured
cohort. GCD normalization preserves ideal whole-unit shares when all are integral;
nonintegral mixed cohorts use deterministic rotation, not nearest rounding per NFT.
See [the exact rule](EXACT_ROYALTY_ALLOCATION.md).

Historical6 checkpoint1 preserves original activation order, ticket starts,
currency cursors, opening/cutoff state and whole royalty units. Fresh7 rejects
checkpoint1 and uses complete raw replay or explicit reviewed checkpoint2, which
preserves those royalty4 rights alongside exact LP trees/phase/direct credits.
Historical scaled LP books remain historical; fresh7 LP rewards use their
separate exact-unit trees. Compare any admitted checkpoint against raw replay
under that checkpoint's original profile, not by relabelling its seed.
Semantic source changes require reviewed rebuild/re-pin. The full rolling24-hour
earnings period stays86,400seconds; it is not the one-hour opening window.

## Lineage, capacity and unsigned claims

Each predecessor declares its OWN royalty_reporting schema and runtime pins;
no omitted/inherited field may turn V9 into a V8 or older reader. Matching new
peers carry accounting7/V9/reporting5. Historical peers keep their own declared profiles.
Existing lineage/workload release limitations remain; a profile declaration is
not operating qualification.

Current inventory16 permits65royalty currencies includingETH and66 combined
token records for the fixed ETH/ZZZ pair plus royalty-only currencies. Historical
inventory13 retains its own97-record bound; neither raises the API work budget.
Operating ERC20 capacity starts16 and can increase to64 only after review. Work,
RPC/history/checkpoint budgets are not raised automatically. A new admission
requires reviewed client descriptors and a separately authorized configuration
rollout; raw claims need no USD feed.

The router still permits32selected NFT/currency/ledger entries. Simulate exact
claims and use smaller healthy batches if gas or a currency failure prevents
one batch. Failed selected payouts revert atomically; LP-only claims remain a
separate choice. Source helpers understand reporting5 and the fresh7 fixed-child
graph; the production inventory pins19 callable helpers plus2 inert data children.
Complete source9/fresh7 site integration/qualification remains open; the served
current3 site is unchanged and public signing stays disabled.

See [settlement/operator steps](ROYALTY_SETTLEMENT.md), [claim router](CLAIM_ROUTER.md),
[window](ROYALTY_LAUNCH_WINDOW.md) and [current audit](../reports/last24h-audit-20261105/REVIEW.md).
No existing service/site/deployment is updated by source publication.
