# Attributed idle, dust and reinvestment

The undeployed candidate uses a contribution default of **2%**, LP/royalty
conversion **1%**, ordinary maintenance **3%**; gas is separate. Governance may
change each within its existing hard 10% maximum. These are ceilings, not targets,
market-loss insurance or permission to sweep balances. Read actual deployed
settings and preserve captured operation and raw-output minima.

## Reduce idle before accepting it

Fresh LP routing2 compares up to four explicitly reviewed ETH/ZZZ execution
venues using bounded reverted actual-core quotes. Single mode selects useful
deployed value; hybrid mode seeks a smallest qualifying sampled swap with a
final active main meeting the configured floor (default60%, hardminimum60%)
and residual below its complementary ceiling (default40%) of retained
principal, including idle, at captured prices. Both use **zero or one** real
balancing swap. A fee-aware seed, depth/post-swap ratio and 0.1% retained-value
early stop replace the old two-pass loop. This does not promise a global optimum
or zero idle. [Policy and configuration](LP_EXECUTION_POLICY.md).

Each swap keeps exact approvals, raw input/output deltas, typed venue binding,
fresh pricing and output minimums. Final source-price/policy/LP checks still run.
An existing LP's self-generated fees are harvested separately before increasing
liquidity; they cannot be misclassified as new principal.

The contribution floor counts **marginal deployed LP**, not idle, old principal,
unclaimed fees or donations. At the current 2% default, conservative $100 input
requires at least $98 of new LP; $5 growth requires at least $4.90. Any retained
idle still belongs to the NFT-share bucket and is included in current NAV. Thus
undeployed value and execution loss are different, even though both consume the
deployed-LP allowance. The separate whole-bucket idle ceiling defaults5%, independently governed for
entry and maintenance within0–40%. Increasing it never relaxes marginal LP or
loss floors. Captured policy/revisions prevent callback widening.

If an operation cannot satisfy all guards, the complete transaction reverts.
A separately confirmed ERC20 approval and spent network gas are not undone by
a later failed activation transaction. Reprepare using current balances and
allowance; do not repeat a successful approval blindly.

## What each residual balance means

| Balance | Owner/purpose | Permitted handling |
| --- | --- | --- |
| Vault `Position.idle0/idle1` | Principal attributed to that shared bucket and its NFT shares | Reinvest through guarded compounding/rebalance; collective holder return includes it in actual ETH/ZZZ principal. |
| Fees' designated compound reserve | The fixed 5% LP-compounding allocation | Release only through the fixed compound path into the same bucket. It is not claimable operator revenue. |
| Buyback reserve | Fixed 5% buyback/burn purpose | Use the governed, bounded buyback worker and actual burn evidence; no dust transfer to a treasury. |
| Per-NFT reward fractions and global division residuals | Backing for exact reward accounting | Carry/checkpoint under the existing ledger, including through transfer/handoff. Never round them into an operator sweep. |
| Small LP fee receipt dust | Existing fee allocation/membership semantics | Keep reserved and settle under incumbent weights before membership changes; historical raw-unit exceptions need asset-specific economic review. |
| Royalties, quarantines and orphaned receipts | Separate royalty domains/cohorts | Convert only earned balances under the royalty converter. No external-custodian drain remains; quarantine is not distributable surplus. |
| Raw prefunds, accidental tokens or unsolicited ETH | Unclassified or explicitly quarantined funds | Never infer permission from contract balance. They cannot subsidize an entrant, pay another bucket or be swept. Unsupported assets may remain inaccessible. |

A universal `clear()` or `sendEverything()` would blur these ownership domains.
This candidate deliberately adds neither. Governance-triggered collective return
distributes only classified principal to NFT owners, not to an operator address.
See [holder return and recovery boundaries](HOLDER_COLLECTIVE_EXIT.md).

## Reinvest idle without a new fee receipt

An authorized keeper calls the existing
`Compounder.compound(bucket,minimumLiquidity,deadline)`. The Vault may now use
that bucket's attributed idle even when no fresh compound reserve is available.
It captures starting prices/principal and the current maintenance cap before
harvest, adds only actually released designated compound, and checks retained
LP plus idle afterward at that same price vector. The stricter venue idle-loss
guard, actual LP increase and captured maintenance idle ceiling(default5%) still apply. NFT shares are unchanged.

Fresh maintenance policy3 requires Budget `IDLE_COMPOUNDING_VERSION()==4`. Every
standalone compound, including idle-only work or work requiring no swap, waits
until `max(lastCompound(bucket), Position.lastRebalance) + compoundInterval(poolId)`.
The independent pool interval defaults to 3600 seconds; governance tunes it through
`setCompoundInterval(poolId,seconds)` within 600 seconds-7 days, without resetting clocks.
This includes the wait after initial LP creation or replacement. It also yields
when `Strategy.needsRebalance(bucket)` is true or
`Strategy.keeperRangeTarget(poolId)` offers an approved adaptive selection.
`compoundReady(bucket)` exposes this decision; it does not grant keeper authority
or replace pause/lifecycle, simulation, price, gas or execution guards.

Rebalance eligibility still uses `lastRebalance` alone: a recent compound cannot
postpone an eligible rebalance. Harvesting, funded claims and ordinary user
activation/top-ups do not acquire this standalone-compound wait. Their normal
guards remain. Entry harvests/checkpoints old fees and releases old compound into
incumbent idle/NAV, but only swaps and deploys the entrant's own exact budget.
Old idle/compound remains available for subsequent guarded maintenance. It
cannot satisfy the entrant's marginal LP floor. If accumulated incumbent idle
exceeds the separate whole-bucket ceiling, compound it before accepting new
entries; do not use a new depositor to bypass that safety limit.
A failed compound rolls back `lastCompound` and all changes. This checkpoint is
local operating state, not an imported NFT entitlement. Explicit historical
accounting1/2/3 deployments retain their original capability1 behavior.

`Compounded` reports newly released compound reserve, which may be zero for
idle-only work. Reinvesting principal, moving pools and converting/claiming rewards
are not new earnings. Actual LP/raw balances and existing history events must be
used to reconcile the operation.

Keeper scheduling is separately opt-in. Fresh accounting6 requires
`idle_compounding_budget` and its exact reviewed runtime pin for every due
compound, including reserve-only jobs. Fresh policy3 verifies capability4, mutual Vault
binding and `compoundReady`; a missing/old helper is not silently accepted.
Configure reviewed Budget/runtime pins,
positive raw thresholds for **both actual currencies** and an explicit interval;
do not sum ETH-wei and ZZZ units or use a common raw threshold as economic value.
Honor both confirmed local intervals and the on-chain compound decision. Defaults do not enable idle
scheduling or automatic range selection in any running service.
Fresh keeper source also waits at the main’s 85% physical threshold, outside
its actual range, or while width/mode/active residual geometry is pending,
including during rebalance cooldown. Main and residual remain fully valued;
compound increases only the existing main and does not rebuild the residual.
Idle may consequently wait and can reach the separate 5% contribution-blocking
ceiling. Missing physical evidence does not authorize a swap or stop independent
due harvesting. See [coordination/review](KEEPER_COORDINATION.md) and
[exact keeper setup and stop/restart](RANGE_POLICY_UPDATES.md).

If an approved adaptive selection is available but local adaptive scheduling is
disabled, compounding waits. Enable the reviewed range job or deliberately
review/disable its on-chain policy; do not bypass the priority guard.

Stop new automatic idle attempts by disabling `maintenance.compound_idle` (or
all compound scheduling with `maintenance.compound=false`), then reconcile any
already submitted hash. These settings do not cancel a pending transaction.
Pause protocol maintenance or disable pool operations through the existing
authorized controls during an incident. Restore only after dependency/policy,
backing, runtime and pending-journal review; never reset a journal to force work.

## Requested execution improvements

[Current execution policy](LP_EXECUTION_POLICY.md) now implements reviewed venue
selection independently of the LP target, bounded depth-aware sizing and entrant
isolation. [Scoped review](../reports/atomic-routing-20261028/REVIEW.md) distinguishes
these source changes from real economic/route qualification. Contributions keep
the current LP ID/ticks and preserve old fee membership/share value. Attributed
idle remains reinvestable through the guarded compound path above; no generic
sweep is needed or authorized. Enabled keeper scheduling must include reviewed
idle thresholds if contribution-released reserves are to be picked up while no
fresh fees arrive. Actual thresholds/gas remain to be qualified.

## Qualification boundary

The earlier [scoped verification](../reports/liquidity-operations-20261025/VERIFICATION.md)
separates actual installed-v4 local execution from substituted feeds, tokens,
VRF and maximum-state gas fixtures; it does not verify later capability3 timing.
That earlier maintenance-policy evidence is historical. Current profile6
[portfolio evidence](../reports/optional-portfolio-20261030/VERIFICATION.md) records
local actual-v4-core and scoped offline checks without qualifying live services.
Real depth/ticks, dual sources, route costs,
MEV/turnover, keeper profitability, exact-release size/gas and independent audit
remain release requirements. Wider ranges and ten-minute checks do not guarantee
continuous in-range liquidity. No public deployment or service change is authorized.
