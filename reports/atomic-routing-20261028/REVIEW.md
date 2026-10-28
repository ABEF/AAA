# Atomic LP execution: implementation and internal review

Fresh undeployed candidate,28October2026; **production NOT APPROVED**.
[Verification](VERIFICATION.md) owns executed checks and exact source scope.
This is the implementation of the user's remaining LP execution requests,
not an independent audit or authorization to deploy/operate anything.

## Scope and adaptations

Keep native ETH and the one fixed ZZZ, NFT ownership/economic rights,
80/10/5/5, separate royalties, collective holder return and same-chain boundaries.
Keep policy2's hard initial12hours, outside-or-deliberate-width eligibility,
manual widths, durable service jitter and independent hourly harvest/compound
interval. Do not add volatility analysis, time-sliced replacement, new currencies,
an arbitrary executor, custody recipient or automatic loss-policy relaxation.

The important architectural distinction is between the **LP destination** and
the **swap execution venue**. Another admitted venue must not create another
holder pool, change share ownership or move custody. Compare useful final deployed
value at one independent price vector, rather than headline fee, TVL, raw liquidity
units or a venue's own claimed USD price. Qualify observed state separately from
provider authenticity and adverse transaction ordering.

## Material changes

| Finding | Implemented correction |
| --- | --- |
| Vault balancing always used its own LP pool, including after removing its depth. | Immutable Manager-created `ZZZLPBalancer`, explicit catalog of up to four admitted native ETH/fixed-ZZZ static hookless v4 pools; compare after the old LP is closed and use the selected route atomically. |
| An approximate fee-aware plan plus a second actual correction could incur unnecessary swaps/idle. | Fee-aware seed and bounded reverted actual-core search, scoring useful deployed USD and checking predicted post-swap ratio. Zero/one actual swap; retain the no-swap candidate and0.1% retained-value early stop. |
| Midpoint-only sizing left0.336894idle in a strict thin-market test; an infeasible initial seed could also hide smaller valid quotes. | Safeguarded residual interpolation with midpoint fallback improves convergence without another actual swap. Output/spot feasibility reduces the input ceiling before ratio sizing; zero-valued dust increases the lower bound. The existing0.01dust assertion and monetary guards are unchanged. |
| A public contribution could trade/deploy incumbent idle/compound. | Exact entrant-only balance and mint/increase budgets. Old idle/compound stays attributed and in incumbent NAV; the marginal deployed baseline is repriced old physical LP only. |
| Incorrect reported output or raw prefunds could obscure balancing accounting. | Manager preserves exact prefunds/refunds/recipient outputs; Vault independently reconciles raw net deltas and clears approvals. Retained idle remains owned by bucket shares. |
| A callback could change/restore route policy, source data or target orientation around quoting/refunds/approval resets. | Monotonic Registry/catalog revisions, full policy/source/derived-tick fingerprints, context spanning Vault approvals/balance/resets, exact quote-to-swap output/post-price and unchanged physical LP ownership/ticks/liquidity. |
| The hard200bps venue ceiling contradicted approved economic configurability. | User-approved1-1000bps governed venue boundary. Operating values are unchanged; the tighter target/route, caller, captured contribution/maintenance and spot guards still apply. |
| Readers assumed the earlier whole-idle contribution formula. | Explicit `lp_routing_version:1`, authenticated parent/helper/core/state runtimes and same-block metadata, entrant/capped-put witnesses and new physical-LP-only baseline. Historical0 retains its equations/200bps bound. Metadata stays request-local. |
| Router observation failure could couple unrelated work to swaps. | Independently due harvesting continues under its own guards; buyback retains its separate route. Saved pending recovery precedes new helper metadata checks, while new balance work still requires them. |
| The expanded Manager temporarily exceeded EIP-170 by143bytes. | Shared private context validation removes duplicated decoding without dropping guards; normal unchanged size gates are rerun. The failed artifact is retained. |

## Quote and settlement boundary

Uniswap's full [V4Quoter](https://github.com/Uniswap/v4-periphery/blob/main/src/lens/V4Quoter.sol)
warns against expensive on-chain use. This implementation uses a small typed
callback with bounded work/gas, not the full general quoter or unbounded search.
The immutable core, exact pending payload, full input consumption and exact custom
revert shape are authenticated. Quoting deliberately reverts price/ticks/fees/
transient deltas and settles no funds. Successful outer execution settles only
the chosen swap. See the [official unlock/delta model](https://developers.uniswap.org/docs/protocols/v4/guides/unlock-callback-and-deltas).

The Manager pulls only the supplied budget before choosing a plan, checks context
after the pull, executes to the fixed Vault, checks actual quoted output/spot,
refunds only unused supplied funds and rechecks policy/physical LP state afterward.
The Vault's approval/reset context and raw deltas cover callbacks outside Manager.
Original Entry source/caller caps and Pricing's three NAV checkpoints still run.
Approvals do not activate; the actual LP increase and final accounting must succeed
in the same transaction. Failure reverts transfers, swaps, LP and share changes;
network gas and a separately confirmed earlier approval are not refunded by revert.

`BalancePlanned` is route metadata, never income. Reverted candidate logs do not
become funded history; a failed outer operation also reverts the final plan event.
The successful Manager independently checks the exact output. Existing buyback,
Entry and reward-conversion routing remain separate and are not advertised as
using this LP solver.

## Accounting and operational boundaries

Pre-entry/own-entry fees still settle under old membership before new shares.
Compound belongs to old principal/share NAV, not a contribution subsidy. Entry
may release it into old attributed idle without reinvesting it; scheduled guarded
compounding can use it later, including without new fees. Configure reviewed
per-currency idle thresholds to avoid stranding useful idle in an unscheduled job.
If incumbent idle would breach the existing5% whole-bucket ceiling, compound first;
the entrant must not be forced to finance or trade it. Collective exit includes
classified idle/compound. No general sweep, dust recipient or external custodian.

Governance can reconfigure compatible admitted venues/solver after sealing;
empty catalog disables swaps without a hidden target fallback. It cannot add
another token, hook, arbitrary router or recipient through this helper. Monetary
limits, source agreement, spot deviation, dust ceiling, work bounds and caller
minimums are distinct. See [operator procedure](../../docs/OPERATOR_MANUAL.md#add-or-remove-an-execution-pool-after-sealing)
and [execution policy](../../docs/LP_EXECUTION_POLICY.md).

Source publication does not upgrade old contracts or services. Existing Anvil,
NFTs/LP/balances, saved journals, website sources/dist/servers, public signing
policy and paused monitor remain unchanged. The four unrelated tracked drafts
are preserved and excluded from publication.

## Remaining risks and release work

- Best **sampled** valid deployed result among the reviewed list; not a globally
  optimal or exact mathematical optimizer, nor gas-adjusted economic optimality.
- Quote simulations cost gas. Maximum catalog/search settings, deep tick crossing,
  gas-estimation/trace budgets and full maximum-state calls need target qualification.
  The configured quote bound may skip an otherwise usable venue; never auto-widen.
- Independent feed provenance, proxy/upstream controls, actual route depth/fees,
  token behavior and Robinhood ordering remain unqualified. Agreement is not
  independence; same-pool spot is not its own USD safety reference.
- Cooldowns/jitter and bounded losses reduce discretion; they do not prove MEV
  immunity, keeper profitability, continuous in-range fees or absence of cumulative
  turnover loss. No24hour or cumulative-loss breaker was silently added.
- Current inventory/frontend/service/profile4 qualification, OpenSea/VRF,
  production authorities, operating rehearsals and independent audit/remediation
  remain open. The blocked inventory scaffold is not approval.
