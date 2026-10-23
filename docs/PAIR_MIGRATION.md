# Local LP pair conversion

This is an **undeployed contract candidate**, not permission to move real funds.
The fixed [`ZZZPairMigration`](../src/ZZZPairMigration.sol) companion implements
atomic same-chain principal conversion through admitted pools supported by the
existing Uniswap v4 liquidity adapter. It does not execute arbitrary routers,
calldata, recipients, bridges or future venue implementations.

## Accounting boundary

| Category | Treatment |
| --- | --- |
| Shared principal and attributed idle | Close into accounted old tokens, convert and redeploy into the selected destination. |
| Designated 5% compounding | Pull current-pair and selected historical reserves belonging to this bucket; convert under the same budget. Unselected historical currencies stay backed in Fees. |
| Individual and collective rewards already allocated | Remain backed and claimable in their original currency, attached to the same NFT. No resplitting. |
| Royalties and buyback reserves | Remain in their separate ledgers. Never migration inputs or loss subsidies. |
| Donations or another bucket's balances | Excluded. The helper restores every pre-existing token balance exactly. |
| Late creator payments | The original append-only inbox still accepts its immutable original pair. Normal receipt-time allocation continues after the move. |

The operation preserves the bucket ID, home identity, NFT ownership, each NFT's
shares, total shares, contribution history and royalty eligibility. A successful
conversion increments `Vault.migrationBudget().compositionEpoch(bucket)`.

At the first guarded checkpoint, fresh oracle prices and decimals are cached
for source, destination and every typed route currency. Historical reserves in
those currencies are selected for conversion; unrelated currencies are not read
or pulled. No later price update can lower the comparison denominator.
The final **deployed LP plus attributed idle must retain at least 97%** of
starting principal plus compound actually released, at that same price vector.
Deployed LP must be nonzero and attributed idle at most 5%. Existing venue,
spot, per-leg swap/deployment and raw transfer guards also remain. Gas is separate.
An earlier parking close, market loss before the snapshot and asynchronous bridge
delivery are outside this atomic execution budget.

Unselected historical reserves remain unchanged in Fees, excluded from both
sides of the execution comparison. Retaining them cannot subsidize a bad trade,
and avoids forcing more than eight swap legs or querying an unrelated failed
token/feed just to move healthy principal. They still count in share/NAV pricing.

Each swap has an exact input and a nonzero minimum output. The helper verifies
actual balances after every leg, clears each exact temporary approval, and
requires no accounted balance outside the destination pair at completion. A
failed leg, stale review, unknown currency, failed mint or violated budget
reverts custody, fee settlement, reservations, approvals and epoch together.

## Operator procedure

1. Obtain `helper = Migration.pairMigration()` from the reviewed deployment.
   Verify controller, helper `migration()`, runtime hashes, Vault/Budget and
   canonical companion bindings. This is created in Migration's constructor;
   it is not a replaceable router. Include it in the deployment inventory before
   sealing and inspect normal runtime/initcode limits including constructor args.
2. Admit and qualify the destination and conversion pools, tokens and fresh USD
   feeds. Every route currency must be an admitted Rewards asset. The current
   fixed liquidity adapter must support each actual PoolKey/native wrapper/hook.
   An activation Entry route is not a principal-conversion route. Decide new-pool
   creator-payment terms and funded payout currencies separately.
3. Read one confirmed snapshot: bucket, source pool, physical LP ID, total
   shares, composition epoch, actual LP/idle, compound reserves in **all admitted
   currencies**, pending source inbox payments, and enabled route/destination
   policies. Confirm local Active/Parked custody, settled old remote obligations,
   no active bridge plan, and available destination reservation/capacity.
4. Through immediate governance, call `helper.execute(Request)` with the exact
   snapshot, destination, nonzero minimum LP, review hash and deadline within
   ten minutes. `steps` contains at most eight
   `(pool, zeroForOne, amountIn, minimumOut)` tuples. Tokens are the Registry's
   ordered **accounting** currencies (native normalized by the reviewed adapter).
   Each raw input must fit uint128 and the bucket's tracked available balance.
   Quote the selected reserves and pending harvests: unconverted source leftovers revert.
5. Simulate the **complete call**, inspect actual swaps/LP amounts, the fixed-price
   3% result, gas separately, allowance cleanup, unchanged NFT shares/rights and
   noninterference with other buckets and donations. Renew the review after
   source LP, shares, epoch, quote or deadline changes. Do not split the sequence
   into standalone close/transfer/swap transactions.
6. Verify the successful receipt and `PairMigrated`/`Rebalanced`, physical LP
   ownership and actual amounts, zero old idle classification, destination idle,
   unchanged shares, correct incremented epoch, empty transient execution context,
   original inbox and both reward ledgers. A reverted receipt is not a partial move.
7. Deliberately switch the Registry's sole contribution pool and reviewed input
   routes when ready. Moving custody alone does not enable new activations in
   the destination. Preserve the old inbox and all historical reward/conversion
   paths; do not relabel old assets as the new pair.

### Late compounding and ongoing operation

After a pair change, a late old-currency receipt can create a new 5% compound
reserve. Until consolidated, it remains backed in Fees. Its oracle value is
included in incumbent share pricing and NFT marked NAV, while it cannot count
as a new contributor's marginal 99% deployed LP. Missing historical prices fail
closed rather than silently diluting incumbents. All admitted historical fee
dust is settled before collective membership changes.

Use a freshly reviewed `execute(Request)` with the **same destination as the
current pool** to consolidate those reserves: the same atomic guards apply, and
the existing LP is closed/reopened. Ordinary `movePool` still rejects a same-pool
request and a different ordered pair; only the authenticated companion context
permits this conversion. Consider actual gas and small-reserve economics before
executing. Do not take reserve funds out manually or charge that execution loss
to claimable owner fees. Ordinary rebalancing/compounding retains its original path.

Use ordinary maintenance when no historical conversion is needed. Every successful
companion call records a composition epoch, even if the destination pair is
unchanged; it has no reset-to-zero path and conservatively disables V3 bridging.

### Failure, stopping and recovery

Global pause stops new conversions. Governance can disable new pool operations
or deposits independently; reopening requires normal validation. Inspect failed
receipts and unchanged LP/ledger state, fix the actual route/feed/policy issue,
then prepare a fresh review. There is no persistent half-complete helper request
to resume, resend, cancel or sweep. A failed external token/venue may still prevent
execution. For a source price outage, use the separate reviewed **paused parking**
procedure with exact raw close minimums; resume conversion only with valid prices.

An unrelated failed old inbox can block the active harvest path. Parking omits
that inbox; a parked conversion may leave its historical currency unselected
and move healthy current principal without reading that token/feed. Preserve
the old entitlement and repair its service separately. This does not bypass
failed source/destination tokens, wrappers, prices or venues actually needed
by the chosen conversion.

Do not delete old funding addresses. They accept only their original pair; this
change does not add arbitrary new payout currencies or a new creator agreement.
New pool fees collected by the venue use the destination accounting pair and
the existing 80/10/5/5 allocation. Review ETH reward-settlement routes for each
new reward currency independently.

## Replacement and bridge limits

Same-chain canonical group records now include the authenticated composition
epoch. Imported parked idle is classified by the **current pool's accounting
pair**, while immutable historical home currencies remain unchanged. Both sides
of a reviewed handoff must support this record format; it is not a retroactive
upgrade of an older deployment.

Version-3 bridge messages encode only two home currencies. Principal bridge
proposals are therefore **disabled once a composition epoch is nonzero**, even
if the pair later returns to the original tokens. Returning does not erase
historical currency obligations. New authenticated message/accounting boundaries,
destination admission/finality and real transport rehearsals remain pre-seal work.
This local feature does not complete future-chain collection migration.

Verification and remaining scope: [local evidence](../reports/pair-composition/VERIFICATION.md).
Task status: [central Todo](../TODO.md#task-custody-composition).
