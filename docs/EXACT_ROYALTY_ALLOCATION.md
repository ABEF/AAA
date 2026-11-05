# Exact-unit royalty allocation

Fresh royalty settlement4 / recovery2, reporting5, inventory13 and canonicalV8.
This is an undeployed source candidate; production is **NOT APPROVED**. Existing
royalty3 deployments/readers, checkpoints and journals are not upgraded or relabeled.

## Why the accounting changed

The previous scaled index could leave whole raw units permanently reserved after
all holders claimed. For example, three weight3 NFTs receiving three raw units
could each show zero, although each ideal entitlement was exactly one. Repeated
tiny synchronizations could also pay less than one combined receipt. Preserving
backing alone did not establish complete claimability.

The user approved a new deterministic whole-unit allocation rule. Fresh royalty4
has no royalty index, paid-index or fractional-unit reserve. LP reward fractions
and explicitly historical royalty ledgers keep their own semantics.

## The rule

Activation permanently assigns an NFT a consecutive interval of rarity tickets:
Commun1, Rare2, Legendary3. Tickets follow successful activation order, not mint
order or current wallet ownership. `ticketStart` is ONE-based (first1; dormant0);
backend `ticket_offsets` are explicitly zero-based and must convert at the wire.
The rotation cursor uses zero-based raw weighted coordinates. The current owner owns the interval's unpaid
rights. Growing LP adds no tickets.

First divide the captured cohort's weights by their greatest common divisor
`G` (1,2or3). Three Legendary NFTs therefore each have one effective ticket,
rather than three adjacent effective tickets. This preserves exact proportional
shares whenever all those shares are representable in whole raw units.

For an actual allocation of `A` raw units to `U = W / G` effective tickets:

1. Every effective ticket receives `A / U` whole units, using integer division.
2. The remaining `A % U` units go one per effective ticket, starting at that
   currency's normalized cursor, wrapping at `U`.
3. Only the remainder advances the cursor. Claims and NFT transfers do not.

For weights1 and2 and a one-unit receipt, exactly one ticket receives that unit.
Across a complete three-unit rotation their allocations are1 and2. Dividing a
receipt into smaller allocations has the same final result while eligibility
stays fixed. Three Legendary NFTs receiving three units get one each. Changing
the eligible cohort can change future rounding recipients. The stored cursor
uses raw ticket coordinates and remains divisible by the applicable divisor.

This guarantees whole-unit assignment, not exact fractional proportionality for
every tiny receipt. An NFT can receive up to its normalized ticket count in one remainder
rotation. Public timing, donations and activation order can influence which NFT
receives the next indivisible unit. Review the value of one raw unit before
admitting low-decimal/high-value currencies; no rounding scheme can divide it.

## Backing and implementation

A bounded internal tree stores **outstanding**, rather than lifetime, units.
It is compiled into the ledger, not a new deployed helper or authority. Allocation
touches bounded ticket intervals; there is no per-receipt loop over1,000 NFTs.
An NFT reads/consumes at most four effective tickets across the bounded
normalization books, preserving earlier cohort allocations. A claim removes its outstanding
units and any imported accrued units before the exact current-owner payout.

Keeping outstanding values avoids cumulative-index overflow after enormous
receipt/claim cycles. All monetary additions remain checked. The maximum tree
capacity and actual ticket bounds are engineering limits, not gas qualification.

For each admitted currency in ordinary operation:

`accounted = liabilities + orphaned + openingPool`

`actual balance = accounted + pending receipts`

Allocated liabilities equal outstanding ticket units plus imported accrued units.
After every eligible owner claims, an otherwise empty allocated pool has zero
liability and zero allocated raw-unit remainder. Pending, initial-held and
explicitly unallocated money are different categories and must not be swept.

## Minting, the one-hour window and outages

The [launch window](ROYALTY_LAUNCH_WINDOW.md) is unchanged: final mint end plus
3,600seconds, strict pre-cutoff activations, no deadline notice on dormant cards.
LP rewards remain independent. Fresh mint reviews bind both the core mint policy
and the NFT/receiver/sale-end/revision through the Vault's six-word fingerprint.
Every sale-end setter increments its revision, including same-value changes;
restoring an earlier end cannot revive an old review. The final check follows
the mint-payment callback as well. Use the getter, never the core Policy hash alone.

Initial allocation uses the cutoff ticket prefix. A late activation cannot enter
it. An unreadable optional currency retains its previous eligible prefix; its
unseen receipts are assigned before waiting NFTs join future allocations.

Plain ERC20 transfers do not notify this ledger of their individual arrival
times. The first successful post-cutoff synchronization allocates its held pool
plus receipts discovered then under the recorded cutoff/outage rule. This is
not reconstructed transfer-time eligibility. Register reviewed currencies before
the sale and synchronize recovered currencies promptly.

No keeper opening job or royalty swap is required. Timestamp passage establishes
eligibility; a synchronization or owner claim performs accounting on-chain.

## What still requires an operator action

| Balance category | Disposition |
| --- | --- |
| Mint/grace opening pool | Allocated lazily after opening to the cutoff cohort. |
| Initial pool with zero cutoff participants | Explicit governance allocation after eligible holders exist; never awarded automatically to the first later activation. |
| Constructor/preadmission funds | Review/admit the currency, then explicitly allocate at current active weights. |
| Ordinary allocated units | Current owner claims the original currency directly or through the bounded claim router. |
| Unreadable or frozen token | Isolate its failure; recover only if the token permits it. No universal payout guarantee. |
| Cancelled replacement receipts | After complete funded abort, current verified target governance reviews recovery into its active ledger and current weights; existing orphaned funds stay separate. Follow authenticated retired hops when needed. |
| Unknown token not yet discovered/admitted | Discover the exact address, review it and configure admission/clients; it cannot be automatically enumerated by the receiver. |

Use governance `allocateAllUnallocated(asset,reviewHash)` for all eligible
unallocated units of one admitted currency. It never spends another currency,
principal, opening pool or already-earned liability. Partial allocation remains
explicit. No beneficiary can be invented when no NFT has activated.

The user-approved capacity starts16ERC20 plusETH and can increase to64 after
review. This finite bound and pathological tokens remain release constraints.
Exact allocation does not mean every possible incoming token is transferable or
that temporarily held/unallocated money disappears without its required action.

## Operating gas and claims

Fresh ProtocolPolicy defaults optional royalty synchronization to1,000,000gas
per isolated currency, within its existing100,000–1,000,000 governed bounds.
The previous250,000 default was too small for cold exact-allocation paths.
Lowering the budget can defer a healthy currency because accounting ran out of
gas. Review actual receipts and simulate before lowering it.

Aggregate gas remains distinct:16full1M failures alone exceed a12M operation,
and many healthy worst-case pending allocations can also exceed that envelope.
For healthy backlog, a permissionless `sync(asset)` transaction can account one
currency before a fresh activation quote, without a swap or payout. Re-simulate
after confirmation; new receipts can add work again. This is optional maintenance,
not a prerequisite keeper worker for royalty claims. Broken tokens and maximum
currency populations still require actual operating/gas qualification.

This is a forwarded ceiling, not a fixed charge. Individual claims use wallet
gas estimation; the Oracle's source-read gas limit is not a royalty claim limit.
The router still permits at most32entries, but a worst-case32-entry batch is not
guaranteed to fit every chain/provider/UI gas budget. Select smaller healthy
currency/NFT batches when necessary. A failed selected payout reverts the atomic
batch; LP-only and other healthy-currency claims remain separate choices.

Measured local fixture gas is not target-chain acceptance. Cold/faulted activation
at the chosen currency population, maximum claims, canonical export/import and
API/history workloads require qualification before expanding capacity.

## Canonical replacement and history

V8 retains the five-word header, but royalty asset rows carry the allocation
cursor. NFT weight rows carry the exact activation ordinal and ticket start;
NFT/currency rows carry accrued whole units. V7 peers are rejected.

Frozen export flattens the source's accrued plus ticket rights through bounded
view rows. It does not require one transaction checkpointing all NFTs/currencies.
The source tree remains intact for abort; the successor imports flat accrued
rights with an empty tree. Import validates unique complete ticket/ordinal
coverage, matching rarity and each currency's summed claims against liabilities.
Ticket mapping and cursor are preserved despite mint and activation order differing.

The existing completed-opening/every-initial-currency synchronization requirement
remains. A permanently broken currency can block whole-collection handoff; LP
parking/terminal return is independent and does not make that currency payable.

`RoyaltiesAllocated` is the sole fresh-profile income-allocation event. Receipt,
initial-opening and unallocated-allocation events also describe lifecycle, but
must not credit the same income again. Claims/imports/transfers are not income.
Reporting5 authenticates settlement4, original units, ticket starts and cursors.
Every lineage peer declares its own profile. Old checkpoints require reviewed
rebuild/re-pin; the rolling24-hour earnings period stays86,400seconds.

See the [operator manual](OPERATOR_MANUAL.md), [original-currency procedure](ROYALTY_SETTLEMENT.md),
[reporting](ROYALTY_REPORTING.md) and [current audit](../reports/last24h-audit-20261105/REVIEW.md).
