# Native ETH architecture: implementation specification

2026-10-24. The user requires robustness and efficiency over preserving existing
code. The selected venue is native ETH/ZZZ. Keep wrapping only for an operation
that actually uses a wrapped asset. This document is a specification, not a claim
the native redesign is implemented or production-approved.

## Asset identity and backing

- Native currency is `address(0)`, with18 decimals and its own reviewed USD feed.
  It is not relabeled WETH. Future WETH is a distinct ERC20, with a separately
  reviewed proxy policy whenever wrapping/unwrapping is actually required.
- Vault principal/idle, FeeController compound/buyback/dust, Rewards liabilities
  and royalty liabilities are separate native balances in separate custody domains.
  An ETH balance alone is never sufficient evidence of a new contribution/income.
- Payable ingress must match the exact declared native amount once per operation.
  ERC20 ingress requires zero unrelated ETH. Forced ETH, prefunds and receipts from
  unrelated operations must not subsidize principal, execution loss or liabilities.
- Native sends use checks/effects/interactions, existing reentrancy/lifecycle guards
  and exact source deltas. Rejecting recipient/callback failures revert the complete
  operation. No arbitrary sweep, automatic resend or relaxed loss budget.

## Required end-to-end flows

| Flow | Native requirement |
| --- | --- |
| ETH activation/growth | Entry forwards exact ETH to Vault; Vault funds typed v4 settlement directly. No WETH allowance, deposit or withdraw. |
| ZZZ activation/growth | Exact ZZZ approval; typed ZZZ/native-ETH swap; actual LP and99% marginal contribution guard. |
| Other input currencies | Reviewed typed routes only. A route that requires WETH may wrap/unwrap at its boundary; its failure cannot block native LP recovery or unrelated inputs. |
| Fee collection | Real ETH credits enter FeeController directly and receive80/10/5/5 classification. No keeper conversion is needed for already-native holder fees. |
| Rewards | Native owner/collective indices preserve old-weight accrual, fractions and transfers; direct native receipts coexist with previously converted native credits. |
| ZZZ fee conversion | User reconfirmed the1% limit on2026-10-24; gas stays separate. The selected approximately1.101% venue needs a cheaper route at reference prices; do not invent one or loosen the cap. |
| Compound/buyback | Spend only the classified5% reserve through typed native settlement. Keeper gas is external. |
| Fee-tier move | Atomic same-native-pair close/redeploy, actual destination depth and one fixed3% starting-price budget. |
| ETH/WETH pool move | Explicit exact1:1 boundary conversion using a reviewed wrapper; distinct asset/idle accounting, composition epoch and historical reserve rights. No implicit identity normalization. |
| Normal custody exit | Close actual LP, preserve accrued fees, enforce stricter swap and aggregate floors, consolidate to ZZZ and send only approved principal. |
| Raw custody exit | Close and send native ETH plus ZZZ without calling WETH, swapping or reading USD prices. Exact reviewed raw minima; no USD guarantee. |
| Recovery/local completion | Actual ETH/token funding, declared units and actual LP backing; no synthetic return receipt. |
| Whole-collection handoff | Carry native principal, fees, indices/fractions, reserves and quarantines exactly once. Native asset zero must not be confused with missing data. |

## Review and qualification

Inventory all payable ABI/call-value changes, constructor casts, zero-address
sentinels, receives/callbacks, canonical funding/protection slots, historical
currencies and original-source contribution contexts. Update API/indexer/keeper
configuration and unsigned preparation without widening the Anvil-only signer.
Never silently interpret the old WETH-accounting profile as this new profile.

Required focused tests include exact/extra/missing ETH, reverted LP/swap/claim,
forced ETH and prefunds, recipient rejection/reentrancy, fee/compound separation,
membership timing, transfer/unclaimed rights, native/wrapped pool changes, wrapper
failure with successful raw native exit, canonical abort/backing and code sizes.
Old evidence remains source-bound; changing these paths justifies fresh affected
coverage. Do not repeat unchanged suites merely to inflate counts.

Current checkpoint: [hookless-pool evidence](../reports/hookless-pool/VERIFICATION.md).
The native redesign needs its own source-bound verification before any release.
