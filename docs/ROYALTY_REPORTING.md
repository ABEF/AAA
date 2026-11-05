# Original-currency royalty balances and history

Fresh reporting schema3 authenticates `ROYALTY_SETTLEMENT_VERSION()==2` and the
reviewed ledger runtime. Use `"royalty_reporting":{"schema":3,"converter":null}`.
A converter pin is rejected. Legacy schemas1/2 remain explicit readers for older
deployments and historical conversion events; never relabel them as schema3.

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

Fresh settlement2 native ETH eligibility cannot be deferred: reporting3 rejects
a native eligible-count/activation-count mismatch without probing an old custody
getter. Optional ERC20 eligibility remains per currency. Legacy reporting1/2
retains its authenticated native-custody history checks for older runtimes; those
fields neither enable custody exits nor change the fresh profile.
