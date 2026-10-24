# Native ETH architecture: implementation specification

2026-10-24. The user requires robustness and efficiency over preserving existing
code. The selected venue is native ETH/ZZZ. Keep wrapping only for an operation
that actually uses a wrapped asset. This document is a specification, not a claim
the native redesign is implemented or production-approved.

## Asset identity and backing

- Native currency is `address(0)`, with 18 decimals and its own reviewed USD feed.
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

## Adversarial design review - 2026-10-24

The broader native redesign is included in the [internal audit](../reports/daily-security-20261024/REVIEW.md).
Its implementation does not exist yet. These requirements are release blockers
for a native-accounting candidate, not claims that the current WETH checkpoint
already meets them. Complete the port across the bound modules before enabling
a native deployment profile; do not combine incompatible old and new modules.

| Boundary | Required design and implementation | Current code that needs adaptation |
| --- | --- | --- |
| Native versus missing identity | Permit zero only as an explicitly admitted currency. Keep zero forbidden for contract targets, owners, configured ZZZ and missing dependencies. An unconfigured `currentZZZ` must not make a raw ETH exit report ETH as `sentZZZ`. Bind native output identity to the real pool, not an arbitrary zero field. | `ZZZMigration`, `ZZZCustodyValidation`, `ZZZOracle`, `ZZZActivationAssets`, Entry and backend codecs |
| Native fee accrual | Feed native receipts through both individual and equal-collective indices, checkpoints and fractions. Preserve already converted ETH credits and liabilities without counting them again as earnings. Settling old weights before activation/top-up remains mandatory. | `ZZZRewards._checkpoint`, `_checkpointOwner`, `_creditPool`, `claimable` and `canonicalImport` currently treat ETH as conversion-only |
| Historical reserves and NAV | Native compound and dust must remain incumbent backing after moving to a WETH pool. Include all admitted assets, including the 33rd native/32-ERC20 slot, in bounded accounting. Missing ETH cannot dilute existing shares or downgrade metadata as a verified zero. | `ZZZMigrationBudget.historicalCompoundValue`, `ZZZMembership.settleDust`, Vault share pricing and metadata valuation |
| Typed funding | Validate the whole declared native value once at the actual funding ingress. Subtract incoming value from starting balance baselines; ERC20 operations reject extra ETH. Match Entry, Vault, manager and fee-credit call values and exact outputs; existing prefunds cannot fill a shortfall. | Entry, Vault activation/growth, LiquidityManager, Fees/Rewards credits, Migration return/completion, API preparation and child-call traces |
| Two-stage canonical funding | Handoff first transfers backing into the destination companion, then acknowledges it with zero `msg.value`; abort uses the reverse protocol. Receive, classify and forward the already transferred native amount once. Do not require `msg.value == amount` at an acknowledgment that is not the funding call. Preserve partial funding and exact abort restoration. | `ZZZCanonicalHandoff.fund/returnFunds`, `ZZZVaultCanonical.canonicalAccept`, `ZZZFeesCanonical.canonicalAccept` and restore hooks |
| Separate backing domains | Export/import native Vault principal, Fees reserves/dust/quarantine, Rewards and royalties independently. Include asset zero where old codecs skip/reject it, and update finite inventory bounds. A contract balance cannot fund two captured rows or cover another domain's liability. | Vault/Fees canonical capture/import/release and `ZZZCanonicalLedger` funding verification |
| Receiver cutoff/protection | If token0 is ETH, do not also count it in a separate `protectedNative` or cutoff slot. Native funding follows the actual currency identity, not the old assumption that only receiver slot 2 can receive ETH. | RewardReceiver capture/settle/protection/release, FeesCanonical receiver rows, FeeController receiver funding |
| Transitive wrapper independence | Raw native close, harvest, fee classification, idle accounting, approval, exit and full recovery must all work when the optional wrapper or its policy fails. Avoid wrapper calls in Registry accounting as well as settlement. A wrapper failure may stop an explicitly requested WETH operation, not unrelated native recovery. | Registry `_nativeBindings/accounting`, manager close/collect, Fees/Rewards, Vault parking and Migration exit/recovery |
| Versioned state and history | Bind an on-chain accounting/schema version and a per-deployment backend profile. Keep old WETH as WETH, including historical fees and claims; do not inherit new currency semantics into predecessor epochs. Qualify old-source import and abort explicitly; a new native source cannot be sent to an old codec that rejects its indices. | Canonical `SCHEMA`/commitments, NFT and reward codecs, `frontend_api/lineage.py`, deployment inventory and history replay |
| Backend and wallet boundary | Encode native currency arguments explicitly while rejecting zero contract targets. Native USD pricing must not require a WETH token code hash. Verify exact ETH value on the root operation and typed child calls. Keep gas separate, approvals ERC20-only and the signer Anvil-only. | API service codecs, activation config/preparation/trace, earnings prices, deployment profile and confirmation checks |
| Claims and callbacks | Preserve effects before native payment, reentrancy/lifecycle guards and current-owner checks before each ClaimRouter leg. A rejecting contract owner reverts atomically; there is no administrator payout redirect. Preserve transfers and both reward streams through callbacks and replacements. | Rewards, RoyaltyRewards, ClaimRouter, NFT ownership hooks and native send primitives |

### Donations and actual receipts

Typed LP operations can isolate the expected native amount from prefunds and
unexpected/forced ETH; unexpected funds cannot subsidize principal or execution
loss. A plain balance-based royalty or external-revenue inbox cannot distinguish
forced ETH from a donation. Keep its documented prefund/quarantine/cohort rules:
actual eligible receipts are allocated by those rules, not by an invented proof
of sender or marketplace origin. The ETH balance alone never proves a specific
trade, royalty agreement or typed LP execution occurred.

### Focused native acceptance boundaries

Require actual source-bound evidence for: missing/extra value and existing
prefunds; partial settlement and rollback; receipt classification; native owner
and collective fractions across activation/transfer/top-up; historical compound
after ETH/WETH moves; partial canonical funding and abort; zero-asset identity
and unconfigured ZZZ; duplicate receiver protection; old/new schema rejection;
recipient callbacks; and successful raw native exit/recovery with a deliberately
failed wrapper. Test current native prices and metadata from actual attributed LP.
Mocked API traces do not replace the typed on-chain cases. Prior WETH-checkpoint
passes do not close these native implementation requirements.
