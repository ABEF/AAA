# Exact-unit royalty allocation

Royalty4/recovery2/reporting5 was introduced in inventory13/canonicalV8 and is
retained inside current inventory17/mint2/canonicalV10. See the [current profile](POSITION_V7.md).
This is an undeployed source candidate; production is **NOT APPROVED**. Historical
deployments/readers, checkpoints and journals are not upgraded or relabeled.

## Why the accounting changed

The previous scaled index could leave whole raw units permanently reserved after
all holders claimed. For example, three weight3 NFTs receiving three raw units
could each show zero, although each ideal entitlement was exactly one. Repeated
tiny synchronizations could also pay less than one combined receipt. Preserving
backing alone did not establish complete claimability.

The user approved a new deterministic whole-unit allocation rule. Fresh royalty4
has no royalty index, paid-index or fractional-unit reserve. Fresh accounting7
LP rewards also use exact-unit allocation in a separate engine. Historical LP6
fractions and older royalty ledgers keep their original semantics.

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

Fresh allocation2 uses cumulative complete rounds, a rotating cursor and immutable enrollment snapshots. Historical payload3/4 used a ticket tree; payload5 retains its separately pinned round-book representation. The library is compiled into the ledger, not a new deployed helper or authority. Each receipt updates constant-size state without scanning holders or retaining payment history. Each currency records at most1,000 increasing enrollment boundaries; a scalar claim finds its birth cohort in at most10 binary-search steps, evaluates its normalized books and subtracts its prior paid coordinate. Imported accrued remains separate.

For effective prefixW, cursorC and receiptA, add `A/W + (C + A%W >= W ? 1 : 0)` complete rounds and set cursor to `(C + A%W)%W`. Each ticket receives `deltaRounds + [ticket <= newCursor] - [ticket <= oldCursor]`. This telescopes across append-only cohorts. Snapshot new entrants after old receipts; the initial opening cohort instead enrolls before its held pool is credited. Homogeneous Rare/Legendary books transition only to unit1 and retain their old rights. New-book initial cursor offsets create no phantom income.

Only lifetime round, gross and paid coordinates wrap modulo2^256; these are not cash balances. Each monetary credit first reserves checked same-currency liability. Claims remain bounded by actual liability, with checked aggregate payouts, backing debits and exact transfers. Imported accrued payouts never become new-book paid debt.

Rarity weights, scalar claims/events and flattened canonical records remain unchanged. Private storage changes: require fresh `ROYALTY_ALLOCATION_VERSION()==2`, explicit factory payload6 and exact reviewed runtime/source pins. Never reinterpret a historical raw tree or payload5 round book. Settlement remains4, recovery2 and reporting5. After every entitled owner claims, allocated liability is zero; internal coordinates need not be zero. This append-only design is specific to royalties; mutable LP shares retain their separate engine.

Current private allocation2 packs223 coefficient bits with a full-width uint256 spill, retaining modulo2^256 logical rounds/gross/paid coordinates. Cursor fields and asset status count/weight/cursor use16-bit fields; validated production bounds remain1,000NFTs and3,000rarity tickets. The one-hour opening, fault cohorts, enrollment history, checked monetary liabilities and every original-currency entitlement are unchanged. This is a fresh storage representation, not a hot-copy migration. See the [current packing and gas review](../reports/activation-final-six-20261118/REVIEW.md).

See the [round-accounting design review](../reports/royalty-rounds-20261118/ROUND_ACCOUNTING_REVIEW.md). The prior [Q03 tree implementation](../reports/q03-activation-gas-20261117/REVIEW.md) and rejected prefix-envelope experiment retain their original evidence. Population/currency capacities are engineering limits, not gas approval.

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

Fresh activation caps only the optional token `balanceOf` STATICCALL through `ProtocolPolicy.royaltyBalanceGas()`: default50,000gas, governed10,000-1,000,000. The complete-sync maximum remains1M. Funding is proved either for the complete frame or independently for the configured read plus120k before that STATICCALL. Only32return bytes are copied; valid trailing ABI data is accepted. A fully funded short/reverting/OOG/under-backed read produces the ledger's own exact4-byte unavailable signal and defers that currency. Token revert bytes never supply that signal. Other failed partial frames revert the entire activation rather than changing entitlements after caller-induced gas starvation. Ordinary sync, claims and canonical balance reads retain their existing paths.

The self-only `syncForActivation(asset,readLimits)` helper receives the captured cap in the low32bits and authenticated full-frame witness in bit32. External callers cannot supply or bypass that witness. These are internal gas units/flags, not token values or operator inputs.

A higher cap or currency capacity requires renewed full-workload qualification. The selected non-live [32M contribution candidate](../config/activation-gas-32m.candidate.json) admits estimates up to26,666,666 with full20% padding. Each contribution still requires separate fee/funding checks and successful padded-call simulation. Legacy12M defaults and recorded20M fixture results retain their own scope; a reviewed profile requires explicit adoption. A cap is a maximum, not a promise the full amount can be forwarded inside the complete frame. Cheap reads do not fail merely because the configured maximum is high.

Permissionless `sync(asset)` remains optional maintenance; no pre-sync transaction, receipt queue or new keeper worker is required by the accounting design. It preserves the captured old-cohort rule without swaps or payouts. `syncAll` is atomic and can fail for a broken currency. Neither prior synchronization nor a capacity setting substitutes for a fresh complete estimate.

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
The source books remain intact for abort; the successor imports flat accrued rights with empty books and preserves the cursor as an initial offset. Import validates unique complete ticket/ordinal
coverage, matching rarity and each currency's summed claims against liabilities.
Ticket mapping and cursor are preserved despite mint and activation order differing.

On a fresh replacement, publicly synchronized pre-import ETH/ERC20 receipts may already be in its opening pool. Import clears that old opening classification and counts the actual target prefund once as orphaned, separately from imported earned liabilities. The checked source identity and source-accounted-plus-prefund overflow bound remain. This prevents duplicate prefund accounting from blocking a correctly backed import; it does not award target prefunds to the imported cohort automatically. See the [prefund regression](../reports/royalty-rounds-20261118/synced-prefund/REVIEW.md).

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
[reporting](ROYALTY_REPORTING.md) and [historical royalty audit](../reports/last24h-audit-20261105/REVIEW.md).
