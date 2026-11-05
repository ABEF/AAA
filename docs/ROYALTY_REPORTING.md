# Original-currency royalty balances and history

Fresh reporting schema4 authenticates `ROYALTY_SETTLEMENT_VERSION()==3` and the
reviewed ledger runtime. Use `"royalty_reporting":{"schema":4,"converter":null}`.
A converter pin is rejected. Legacy schemas1/2/3 remain explicit readers for older
deployments and historical conversion events; never relabel them as schema4.

The API returns separate raw balances/decimals/symbols and currency eligibility.
Fresh balances say `settlement_mode:original_currency`, `claim_asset:<address>`
and `conversion_required:false`; `unconverted_raw` is null. WETH is not ETH.
There is no promised conversion timer or quote. The projection places these
balances in `claimable.royalties`; reporting holds the eligibility/status summary.

Missing token reads/metadata remain unavailable for that currency, rather than
zero. Missing USD prices do not prevent a raw claim. Never add raw amounts from
different currencies or label source tokens as ETH. Current-price USD display
is optional and must state unavailable when incomplete.

Claims are current-owner payouts. Conversion/import/transfer is not new income.
The new `UnallocatedRoyaltiesAllocated` first-credits its ORIGINAL currency at
current active weights once; it does not add another raw receipt or conversion.
Previously earned/deferred balances retain their original cohorts. Historical
RoyaltyConverted/recovery1 events remain decoded at their actual pinned emitters.
Semantic replay source changed: rebuild/review/re-pin earnings checkpoints;
never relabel old caches or invent missing history.

Unsigned claim preparation accepts each approved currency in a32-entry mixed
ClaimRouter batch, simulates exact inputs and records separate raw outputs.
The fresh website source includes original-currency royalty entries for schema3,
with explicit token amounts; large selections need smaller reviewed batches.
One failed selected token reverts the whole batch. Public signing remains disabled.

See [settlement/operator steps](ROYALTY_SETTLEMENT.md), [claims](CLAIM_ROUTER.md),
[current verification](../reports/royalties-in-kind-20261105/VERIFICATION.md).
No running API/site/service is changed by source publication.

<a id="current-native-eligibility-and-historical-custody"></a>

## Native eligibility and historical custody

Fresh settlement3 native ETH eligibility cannot be deferred: reporting4 rejects
a native eligible-count/activation-count mismatch without probing an old custody
getter. Optional ERC20 eligibility remains per currency. Legacy reporting1/2
retains its authenticated native-custody history checks for older runtimes; those
fields neither enable custody exits nor change the fresh profile.

## Sale-end window and expanded capacity

Reporting4 includes opening.configured, mint_end, claims_open_at, claims_open,
activation_window_seconds3600 and status open/locked/unconfigured. Locked
royalty balances must be zero spendable units; inconsistent responses fail
closed. LP balances remain independent. The reader authenticates capability3
and uses effectiveEligibleCount for the initial cohort during a currency fault.
Original raw claims need no price feed, conversion or keeper.

Fresh profile12/canonicalV7 allows at most65royalty currencies including ETH,
and97combined descriptors; old reporting3/legacy limits remain unchanged.
Work/RPC/checkpoint/transaction budgets are NOT automatically increased. An
operator must qualify expanded capacity workloads and update exact descriptors.
Mixed claims retain32entries; review selected currencies in multiple batches.

Earnings replay records the initial allocation once, not as a second receipt or
conversion. Claim reconciliation includes the backed pending opening pool only
after the deadline and only for the cutoff cohort. Event-credit history still
distinguishes processed credits from pending claimable receipts. Checkpoint
state includes the sale end, initial cutoff and allocated currencies; source
identity changes require reviewed rebuild/re-pin. See [window](ROYALTY_LAUNCH_WINDOW.md).
