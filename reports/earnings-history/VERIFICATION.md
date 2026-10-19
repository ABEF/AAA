# Earnings history - scoped verification, 2026-10-19

**Development evidence; release remains NOT APPROVED.** Baseline main:
`83d844d506f062a4fa3cc98b6614762e51ff3d68`. Git determines publication. No
Solidity, website, server, paused monitor or public-chain state changed.

Implemented [collection/per-NFT processed earnings](../../docs/EARNINGS_HISTORY.md)
and the user's current-price USD policy. Raw LP individual/collective and royalty
income stays separate from principal, current balances, payouts and conversions.
Exact indexed accounting, deferred royalty cohorts and complete configured
same-chain epochs are reconstructed and reconciled against confirmed state.

## Checks actually performed

| Evidence | Result and scope |
| --- | --- |
| [Source, ABI and test mapping](source-and-abi.json) | 186 unique affected Python tests have passing current-body evidence across three scoped runs; not one clean full regression |
| [Affected run](affected.json), [log](affected.log) | 166 passed, two harness/fixture errors: missing dormant ordinal RPC fixture and a mistyped work-limit suite name |
| [Corrections and request limits](supplemental.json), [log](supplemental.log) | 18 passed: corrected dormant fixture plus the actual 17-test request-limit suite |
| [Additional edge checks](edge.json), [log](edge.log) | Two passed: pre-mint collection and supervised earnings dispatch |
| Existing production build reuse | All 40 production Solidity source hashes and build settings still match [royalty conversion evidence](../royalty-conversion/VERIFICATION.md); compiled metadata reused, no rebuild or unchanged Solidity test rerun |
| Actual ABI compatibility | All 15 replayed event layouts and 17 added read-getter layouts checked against that source-bound compiled ABI |

The 28 new earnings tests include 1,000 NFTs sharing one pool; separate share,
equal-membership and royalty weights; top-ups; ownership transfers; raw-unit
rounding and exact 24-hour boundary; quarantine; both normal and canonical
royalty recovery order; same-chain retirement/import continuity; real SQLite and
byte-level RPC fixtures; missing events, runtime/index drift and expiry; conversion
and payout reconciliation; price policy changes; read HTTP and worker dispatch.

Earlier development attempts are retained externally and summarized in
[development-attempts.json](development-attempts.json): an unknown valid ID was
initially expected as HTTP 400 instead of 404; the dormant fixture omitted its
ordinal lookups; the expiry fixture did not initially exceed the configured age.
Those were fixture/assertion corrections. The earnings implementation did not
change to weaken validation. Passing unchanged checks were reused by exact source
hash and test-body/helper comparison instead of repeated for bookkeeping.

Test trees contain published HEAD plus the intended earnings delta. The mixed
server's older unsigned-action draft and unrelated route/history-test/artwork
drafts are excluded from publication and testing. All checks are local, with
controlled RPC fixtures; they are not Robinhood service qualification or green CI.

## Internal review

Reviewed the raw event decoder, activation event order, reward-index fractions,
fee dust, deferred royalty recovery, conversion accounting, canonical import
boundaries, price policy checks, HTTP dispatch and work limits. The principal
review conclusions are:

- The API has no signer or state-changing RPC. Its accounting cannot alter funds.
- Source income remains in its original denomination after conversion; payouts
  and imports cannot increase earned totals. The buyer sees the NFT's complete
  history, including amounts earlier owners already claimed.
- Canonical royalty settlement emits recovery before the receipt event even
  though the receipt uses the old cohort. Frozen replay defers that membership
  change until the receipt; normal synchronization uses the ordinary event order.
- Current Oracle/feed/storage pins and fresh canonical headers are required for
  USD marks. Unavailable prices return null; request-budget failures remain fatal.
- Matching on-chain indexes and NFT balances catch many incomplete histories,
  but do not prove absolute log completeness. Reviewed ingestion remains a trust
  boundary, particularly for collection gross/reserve figures.

This is an internal review, not an independent audit. Unsupported successor
economics and cross-chain history fail outside the supported profile. Actual
large-history latency, real dependency outages, provider/price qualification,
live frontend integration and operating rehearsals remain open in the
[central task](../../TODO.md#task-financial-history). The strict earnings endpoint
does not promise currency-outage isolation; the separate balance endpoint does.
