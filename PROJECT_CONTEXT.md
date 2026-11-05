# PoPL current project context

Reviewed5November2026. Pre-window baseline main c7dad14; verify actual local/remote
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
words. Fresh royalty3/recovery2/canonicalV7/schema12/reporting4;17modules/18helpers.
Old V6/header/runtime/profile/journal/receipt boundaries remain explicit.

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
and fractions. Zero initial participants leave funds unallocated for later
explicit governance decision. allocateAllUnallocated(asset,reviewHash) allocates
all eligible unallocated whole units of ONE admitted currency at current active
weights; no swap/payout/recipient/sweep. Partial allocation remains. Unsupported
receipts require review/admission; no reconstructed receipt-time entitlement.

Original currencies only: ETH stays ETH, WETH stays WETH, USDC stays USDC. No
royalty converter/unwrap/approval/price route; separate LP conversion preserved.
Current owner inherits all unpaid rights.32total NFT/asset/ledger claim entries,
selected healthy currencies avoid one failed payout reverting an atomic batch.
Per-currency failure cohorts/fractions preserved. Default16ERC20+ETH capacity can
only increase through governance to64ERC20+ETH after gas/service review. Review
hash is NOT a gas proof. No unlimited/frozen-token/zero-rounding-reserve promise.

CanonicalV7 royalty header five words includes end/capacity; source requires open/
finalized window and every initial currency synchronized before capture. Old V6
peers rejected early. Import never reopens sale/grace; parked/principal wire shapes
do not imply runtime compatibility. Emergency/terminal LP recovery is independent.

## Evidence, records and environments

Current scoped report: reports/royalty-launch-window-20261105/VERIFICATION.md.
51production/31dependency sources,42normal gates,479internal static contexts
(103current/376exact reuse).125distinct selected EVM successes across explicit
one-hour stages, including1000NFT/fuzz and actual local-v4/canonical cases.
183affected Python checks and71reference/static/publication checks at recorded
stages;157website read/unsigned tests. Counts/scopes not casually summed.
36contracts/809functions/36constructors/12receivers;857operator examples,0gaps.
No whole-suite/public CI/actual target gas/marketplace/uptime/independent approval.

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
