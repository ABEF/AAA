# Attributed idle, dust and reinvestment

The undeployed candidate uses a contribution default of **2%**, LP/royalty
conversion **1%**, ordinary maintenance **3%**; gas is separate. Governance may
change each within its existing hard 10% maximum. These are ceilings, not targets,
market-loss insurance or permission to sweep balances. Read actual deployed
settings and preserve captured operation and raw-output minima.

## Reduce idle before accepting it

The Vault plans against the actual market and performs **at most two** balancing
swaps. The second plan reads the actual post-first-swap state, including its new
price and position ratio. Corrections no greater than 1 bp of that bucket's
available input are skipped to avoid chasing precision dust. This is a bounded
improvement, not an optimal router or a guarantee of zero idle in every market.

Each swap keeps exact approvals, raw input/output deltas, typed venue binding,
fresh pricing and output minimums. Final source-price/policy/LP checks still run.
An existing LP's self-generated fees are harvested separately before increasing
liquidity; they cannot be misclassified as new principal.

The contribution floor counts **marginal deployed LP**, not idle, old principal,
unclaimed fees or donations. At the current 2% default, conservative $100 input
requires at least $98 of new LP; $5 growth requires at least $4.90. Any retained
idle still belongs to the NFT-share bucket and is included in current NAV. Thus
undeployed value and execution loss are different, even though both consume the
deployed-LP allowance. The separate 5% whole-bucket idle ceiling remains.

If an operation cannot satisfy all guards, the complete transaction reverts.
A separately confirmed ERC20 approval and spent network gas are not undone by
a later failed activation transaction. Reprepare using current balances and
allowance; do not repeat a successful approval blindly.

## What each residual balance means

| Balance | Owner/purpose | Permitted handling |
| --- | --- | --- |
| Vault `Position.idle0/idle1` | Principal attributed to that shared bucket and its NFT shares | Reinvest through guarded compounding/rebalance; collective holder return includes it in actual ETH/ZZZ principal. |
| Fees' designated compound reserve | The fixed 5% LP-compounding allocation | Release only through the fixed compound path into the same bucket. It is not claimable operator revenue. |
| Buyback reserve | Fixed5% buyback/burn purpose | Use the governed, bounded buyback worker and actual burn evidence; no dust transfer to a treasury. |
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
guard, actual LP increase and 5% idle ceiling still apply. NFT shares are unchanged.

Fresh accounting4 requires Budget `IDLE_COMPOUNDING_VERSION()==2`. Every
standalone compound, including idle-only work or work requiring no swap, waits
until `max(lastCompound(bucket), Position.lastRebalance) + minRebalanceInterval`.
This includes the wait after initial LP creation or replacement. It also yields
when `Strategy.needsRebalance(bucket)` is true or
`Strategy.keeperRangeTarget(poolId)` offers an approved adaptive selection.
`compoundReady(bucket)` exposes this decision; it does not grant keeper authority
or replace pause/lifecycle, simulation, price, gas or execution guards.

Rebalance eligibility still uses `lastRebalance` alone: a recent compound cannot
postpone an eligible rebalance. Harvesting, funded claims and ordinary user
activation/top-ups do not acquire this standalone-compound wait. Their normal
guards remain, including harvesting/reinvesting reserves inside contributions.
A failed compound rolls back `lastCompound` and all changes. This checkpoint is
local operating state, not an imported NFT entitlement. Explicit historical
accounting1/2/3 deployments retain their original capability1 behavior.

`Compounded` reports newly released compound reserve, which may be zero for
idle-only work. Reinvesting principal, moving pools and converting/claiming rewards
are not new earnings. Actual LP/raw balances and existing history events must be
used to reconcile the operation.

Keeper scheduling is separately opt-in. Fresh accounting4 requires
`idle_compounding_budget` and its exact reviewed runtime pin for every due
compound, including reserve-only jobs. It verifies capability2, mutual Vault
binding and `compoundReady`; a missing/old helper is not silently accepted.
Configure reviewed Budget/runtime pins,
positive raw thresholds for **both actual currencies** and an explicit interval;
do not sum ETH-wei and ZZZ units or use a common raw threshold as economic value.
Honor both confirmed local intervals and the on-chain compound decision. Defaults do not enable idle
scheduling or automatic range selection in any running service.
See [exact keeper setup and stop/restart](RANGE_POLICY_UPDATES.md).

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

[Current design review](LP_EXECUTION_POLICY.md) requests the best approved swap
venue independently of the LP target, a depth-aware normally-one-swap plan and
material-benefit-only residual correction. These are not implemented routing or
solver features. Current contributions already keep the LP ID/ticks but can
balance incumbent idle/compound; changing that requires preserving incumbent NAV,
old fee membership and actual marginal deployed accounting. Attributed idle is
already reinvestable through the guarded compound path above; no generic sweep
is needed or authorized. Per-currency thresholds already exist; actual economic
values remain to be qualified.

## Qualification boundary

The earlier [scoped verification](../reports/liquidity-operations-20261025/VERIFICATION.md)
separates actual installed-v4 local execution from substituted feeds, tokens,
VRF and maximum-state gas fixtures; it does not verify later capability2 timing.
Real depth/ticks, dual sources, route costs,
MEV/turnover, keeper profitability, exact-release size/gas and independent audit
remain release requirements. Wider ranges and ten-minute checks do not guarantee
continuous in-range liquidity. No public deployment or service change is authorized.
