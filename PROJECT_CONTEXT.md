# PoPL current project context

Reviewed3November2026; authority-change source base main `db8033ec5f193e472ff70ac82197d8ad1570461a`.
[Instructions](AGENTS.md), [README](README.md), [sole Todo](TODO.md),
[operator manual](docs/OPERATOR_MANUAL.md) and [findings](docs/AUDIT_FINDINGS.md)
own current context. Exact publication status comes from Git, not this date.
**Undeployed; production NOT APPROVED.** This is repository memory, not a timeline.

## Current source candidate

Use the [identity table](docs/POSITION_V6.md): accounting6/Portfolio2/maintenance3/
confirmation3/compound4/custody5/emergency2/LP-routing2; direct Entry-routing3,
pricing2/review-policy2/governance2/fee1/ProtocolPolicy1. Inventory schema10 has
17modules and20helpers. Canonical V6/eight Position words do not imply runtime
compatibility. Historical custody4/schema9/direct Entry3 and routed Entry2/schema8
remain explicit inspection only.

Only native ETH and one deployment-fixed ZZZ enter principal. Entry has no
pre-Vault conversion, route catalogue, receiver or conversion child; it forwards
exact original input to Vault balancing and marginal main-LP verification.
Separate LP/royalty converters retain their reviewed routes/helpers. Source8 is
an integration label; ACCOUNTING_VERSION remains6, not8, and no deployment upgraded.

Default one main; optional one residual in the same pool, both Vault-owned.
Default main>=60%/residual<=40% at replacement, not continuously maintained weights.
Main floor may rise6000–9999bps; residual width defaults half the corresponding
main side with a positive full tick-spacing gap(default1). Mixed/filled/outside
residuals remain valued and harvested. Modefalse requests a guarded merge; it
does not erase backing or deactivate NFT royalty/collective membership.

Contributions checkpoint incumbents, spend entrant funds only, increase main
only, verify actual marginal deployed LP and issue shares at aggregate net NAV.
They never recenter, reset clocks or modify residual liquidity. Existing idle,
compound, fees or donations cannot subsidize entrant execution floors.

Ordinary trigger85% actual centre-to-boundary ZZZ-in-ETH distance, same-side
physical/reference corroboration,600-second sampled window/maxgap300,
240-second source checks and fresh durable60–300-second service jitter after
initial hard12hours. Raw checks can occur during cooldown; paid observations
start near eligibility. Manual geometry is a distinct cooldown-gated exception.
Sampling is not continuous history or attack immunity. Compound has its own
interval and keeper waits below the threshold/in-range/no pending geometry.

<a id="manual-portfolio-controls"></a>

## Current authority boundary

Fresh custody5/schema10 keeps owner LP/royalty reward claims and owner principal
fallback. Only governance allocates/distributes terminal principal; the submitting
wallet pays batch gas. Keeper principal_distribution must stay disabled on5.
Explicit API/keeper/lineage versions reject silent4→5 adoption; historical runtime,
config and pending records remain separate. See [permissions](docs/ACCESS_PERMISSIONS.md).
Current [verification](reports/authority-audit-20261103/VERIFICATION.md) binds52/31
sources/dependencies,43normal gates,471static records (19current/452reuse),14distinct
selected EVM successes across scopes and25corrected Python methods. Migration39
runtime margin; other key sizes unchanged. Earlier direct-Entry measurements
below retain custody4 source scope. No full suite/production approval is implied.

## Rights, management and recovery

Actual hourly harvested receipts from both legs fund fixed80/10/5/5 individual /
equal activated collective / compound / fixed-ZZZ buyback-burn. Harvest, claims,
conversion, compound and buyback are separate. Royalties use actual eligible
receipts and Commun1/Rare2/Legendary3. Current owners retain old unclaimed rights;
earned, claimable and claimed differ. Conversion/import/claim is not new income.

One human governance/operator, direct authorization without timelock; keeper
key is separately limited. Reviewed policy allows future mint/entry/payee,
gas/idle/display terms and drained VRF rotation without changing old rights.
Default100USD/5USD minima,0.05ETH direct mint,3% source agreement and2%/1%/3%
contribution/conversion/maintenance limits remain. Governance ceilings10% are
normal economic bounds; separate additional-loss default1% after actual fees
and idle defaults5% retain distinct purposes. Emergency bypass is separately
explicit and can lose nearly all principal.

Paused closeResidual harvests both, closes only residual into bucket idle and
preserves main/shares/clocks/policy. No payout/swap/automatic reinvestment.
Parking/movement close both. Terminal collective exit returns actual ETH+ZZZ and
designated compound by frozen shares to current owners in bounded direct batches;
claims/transfers/future royalties continue. Rewards/buyback backing stay separate.
No external custody address, reopening, integrated bridge, mutable ZZZ identity
or post-exit canonical replacement. Pre-exit same-chain canonical V6 requires
all residuals closed; whole-chain/post-halt recovery is not implemented.

## Current implementation and verification boundary

[Feature/evidence reference](docs/IMPLEMENTATION_STATUS.md) owns capability detail;
[consolidated findings](docs/AUDIT_FINDINGS.md) maps history to current mechanisms
and remaining tasks. Original reports/failures/pins remain immutable. The prior
custody4 [Entry3 evidence](reports/direct-entry-v3-20261103/VERIFICATION.md) has52 production /
31dependency sources,43normal gates,471static records and reference37/818/37/13
with no note gaps.28 distinct selected EVM and314 Python successes span recorded
stages; no full current suite/CI/live operating approval is claimed.

Entry runtime18581→9863 and Registry creation42736→22526. Vault635/Budget237/
Migration20/Balancer360 were the prior custody4 exact-source margins. All earlier
counts/measurements are historical. Recheck source pins/advisories before reuse.

## What remains

Actual independent feeds, routes/depth, supported VRF, authorities, OpenSea primary
mint, metadata hosting, source8 API/keeper/website configs and operations, target
gas/economics, history archive scaling and independent audit/remediation remain
open under the [central Todo](TODO.md). Cumulative loss budgets and automatic
volatility analysis were not selected.60/40 is an approved tradeoff, not an
optimized/proven profitable strategy. No manipulation/proxy/availability guarantee.

## Boundaries and preservation

Main only. Popldemo is simulation; poplint is separately served current3/read-and-
prepare with absent reviewed deployment config. Source8 does not update either.
Public DEPLOYMENT stays null; signing Anvil-only. Preserve Anvil8902/NFTs/LP/
balances/journals, website sources/builds/services and the user-paused heartbeat.

Four unrelated dirty tracked files remain byte-identical and excluded:
reports/source-checks.json, scripts/run-fork-checks.py,
tests_python/test_fork_runner.py, tests_python/test_frontend_history.py.
Current authority-change originals and exact hashes are external under
`authority-audit-20261103`, recorded in [handoff](docs/WORK_HANDOFF.md).
