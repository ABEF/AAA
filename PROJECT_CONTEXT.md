# PoPL current project context

Reviewed5November2026. Audit baseline main967370f; verify actual local/remote
heads before claiming publication. Read AGENTS.md, README.md, the sole TODO.md,
docs/WORK_HANDOFF.md and docs/OPERATOR_MANUAL.md. Production NOT APPROVED.

## Current architecture and economics

1,000 ERC721 NFTs; fixed600Commun/300Rare/100Legendary draw quotas. Native ETH and
one fixed ZZZ for contributions/LP/buyback/holder return. Default activation100USD,
growth5USD/direct mint0.05ETH; future minima/payout policy remain bounded and
governed. Two independent USD sources per priced asset,3% agreement. Default
contribution2%/LP conversion1%/maintenance3%, governed ceilings10%, gas separate;
additional execution loss1% after known directional fees and default5% idle are
different guards. Fixed80/10/5/5 actual LP receipts: owner/equal active collective/
compound/ZZZ buyback-burn. Rarity affects royalties only, not LP shares.

Accounting6/custody5/portfolio2/maintenance3/confirmation3/compound4/emergency2,
LP-routing2/pricing2/Entry3/review2/direct governance2/fee-intake1. Position eight
words. Fresh royalty4/recovery2/canonicalV8/schema13/reporting5;17modules/18helpers.
Old V7/V6/header/runtime/profile/journal/receipt boundaries remain explicit.

One contribution pool at a time, <=4logical historical buckets. One main or
optional main+ONE residual in same ETH/ZZZ pool, Vault owns both NFTs. At replacement
main>=60%/residual<=40%, not perpetual target; residual half-side5000bps, positive
spacing gap, desired mode OFF by default. Both legs always count in valuation/
harvest/closure. Entrants fund MAIN only; no incumbent/residual/compound subsidy,
recenter or clock reset; actual marginal LP and aggregate shares must reconcile.

Ordinary85%centre-to-boundary same-side physical+independent reference,600second
sample/300maxgap/240source polling, durable60–300jitter after initial hard12hours.
Paid enrollment begins near eligibility; pending-first recovery, reset receipts
and provenance remain. Hourly harvest independent. Compound interval independent
after max(lastCompound,lastRebalance); automation waits for in-range/below-trigger
main/no pending geometry. Existing authenticated internal-harvest coalescing stays.

One human operator/governance, separate limited keeper key. Direct governance,
no timelock. Sealed implementations/parents/token identities fixed; bounded
policies/routes remain governed. Paused manual emergency2 can optionally bypass
financial guards and risk nearly all principal, never an automated fallback.
Terminal governance holder return closes both legs into actual ETH+ZZZ and pays
current NFT owners in bounded direct batches; no custody-address exit/bridge or
principal reopening. Claims/royalties/transfers remain. Canonical replacement is
separate, same-chain, reviewed verified source retirement/backing, never post-exit.

## Royalty opening and currency capacity

Final user choice: ONE HOUR (3600seconds), superseding the24-hour draft. Governance
NFT.setMintEnd mirrors final OpenSea sale stage. Unset/past end rejects minting;
future revisions allowed only while the OLD end has not passed. No mint after
close, no sellout assumption, no clock pause or administrator extension afterward.
Claims open at end+3600. NFTs whose activation finishes strictly before cutoff
share the initial admitted-currency pool at rarity1/2/3. Late activations get only
future receipts. A delayed first transaction cannot change the cutoff cohort.
Normal sync/claim/activation materializes allocation: no keeper/opening transaction
prerequisite. LP claims are independent. No deadline on DORMANT cards by user choice.

openingPool is separate from constructor/preadmission prefunds, earned liabilities
and exact ticket backing. Zero initial participants leave funds unallocated for later
explicit governance decision. allocateAllUnallocated(asset,reviewHash) allocates
all eligible unallocated whole units of ONE admitted currency at current active
weights; no swap/payout/recipient/sweep. Partial allocation remains. Unsupported
receipts require review/admission; no reconstructed receipt-time entitlement.

Original currencies only: ETH stays ETH, WETH stays WETH, USDC stays USDC. No
royalty converter/unwrap/approval/price route; separate LP conversion preserved.
Current owner inherits all unpaid rights.32total NFT/asset/ledger claim entries,
selected healthy currencies avoid one failed payout reverting an atomic batch.
Per-currency failure cohorts and previously allocated exact units stay protected. Default16ERC20+ETH capacity can
only increase through governance to64ERC20+ETH after gas/service review. Review
hash is NOT a gas proof. No universal frozen-token/unknown-currency payout promise; allocated rounding units are exactly assigned.

CanonicalV8 royalty header five words includes end/capacity; source requires open/
finalized window and every initial currency synchronized before capture. Old V7/V6
peers rejected early. Import never reopens sale/grace; parked/principal wire shapes
do not imply runtime compatibility. Emergency/terminal LP recovery is independent.

## Exact-unit audit and evidence

The user approved exact-unit allocation. GCD-normalized captured rarity tickets
and a per-currency rotating cursor assign every allocated raw unit; no fresh
royalty scaled index/fraction reserve. StartsONE-based, backend offsetsZERO-based;
original-source EVM logs/getters/V8 export rows verify that boundary. Claims/imports
are not income; only generic RoyaltiesAllocated credits fresh earnings once.
V8 preserves activation order and whole accrued liabilities, flattened in frozen
view without deleting source books. Old codecs/checkpoints remain historical.

Mint reviews bind sale end/revision plus core policy and NFT/receiver; callback
and restore-to-revive checks protect them. Cancelled-importer royalties recover
only after complete abort restoration, through authenticated lineage to reviewed
current active weights; target governance controls recovery, no chosen recipient.
The existing fixed VaultCanonical companion verifies one hop read-only.

Factory uses fixed constructor-derived stored creation payload/hash to fit normal
runtime size; high one-time deployment gas remains a target release gate. Default
optional royalty sync gas1m, not a fixed charge. Expanding to64 currencies needs
worst-case gas/service/API qualification, even though inventory13 accepts97 token
records. No source publication is operating or independent approval.

Current scoped record: reports/last24h-audit-20261105/VERIFICATION.md and evidence.
It distinguishes prior failures/empty attempts, final source runs, actual source
producer/consumer evidence, exact unchanged reuse and missing live qualification.
Historical royalty-window3 counts never establish current4 evidence.

Test maintenance also reconciles current opening/rounding/profile assumptions,
closed-sale handoffs and nonvacuous stateful claims; explicit historical tests
remain. Aggregate16×1M optional failures exceed a12M operation envelope, so actual
currency count/provider gas qualification remains open; no live budget was raised.
See reports/last24h-audit-20261105/TEST_MAINTENANCE.md and its scoped follow-up receipts.

One Todo ledger docs/project-todo.json generates TODO.md. Keep feature/roadmap/
release/operator/context linked with source/evidence. Original reports immutable;
repository memory is not global personal memory or a background synchronization.
Source/checkpoint semantics changed: reviewed rebuild/re-pin, never relabel old
artifacts. Older research/failures retain original scope.

Main only. Preserve four protected dirty files in handoff, all Anvil8902 holdings,
dist overlays, pending/nonce/receipt/spend journals, shared signer and user-paused
heartbeat. Popldemo is simulation; separately served poplint is current3/unconfigured,
not fresh source8/accounting6. Public DEPLOYMENT null; browser signing Anvil-only.
No deployment/seal/public transaction/site/server/service/reset/signing change.

Open release gates: actual OpenSea drop/all mint-path/final-end binding, currencies,
dual feeds/routes/VRF/authorities, expanded gas/API/history/checkpoint workloads,
matching source8 services/site, storage/restore/long-lived history, independent
audit/remediation. Capacity64 and current source tests do not close these gates.
