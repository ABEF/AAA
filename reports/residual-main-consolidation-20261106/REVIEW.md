# Same-main residual consolidation and operator controls

6 November 2026. Baseline main `9025735fca5a6011bce3772f981881d66d3ea082`.
Undeployed candidate; production NOT APPROVED. [Executed prompt](PROMPT.md),
[operator matrix](OPERATING_MATRIX.md) and [verification](VERIFICATION.md).

## Implemented result

Governance can now pause and call
**`Migration.consolidateResidual(request, forced)`** to harvest/close only the
residual and reinvest attributed ETH/ZZZ idle into the **same main LP ID and
ticks**. It also repairs an earlier raw-close/no-residual state with positive
attributed idle. It never releases designated FeeController compound reserves,
changes shares/deposit/centre/lastRebalance, chooses an external recipient or
reopens terminal principal. Actual fees remain separate from reinvested principal.

Guarded `forced=false` requires checks14 and no explicit swap inputs: existing
reviewed routing chooses zero/one trade under fresh prices, actual in-range main,
captured retention/idle/execution limits and positive caller added-L floor.
It does not wait for keeper cooldown, sampled confirmation, service jitter or
standalone compound eligibility. Forced `true` uses the exact admitted swap and
explicitly retained mask0–31; structural custody/accounting/lifecycle remains.

Success atomically applies desired mode OFF, advances recovery nonce/epoch and
the compound clock, and invalidates stale timing controls even if already OFF
with no residual. The main rebalance clock stays unchanged. A separate desired
main-width/orientation mismatch stays pending. Pause remains ON; unpause is an
explicit operator decision. Complete inputs/examples are in the single
[operator manual](../../docs/OPERATOR_MANUAL.md#same-main-residual-consolidation).

## Findings and improvements

| Finding / concern | Correction or disposition |
| --- | --- |
| Raw residual close followed by ordinary compound was not a reliable permanent single-mode workflow. OFF left pending geometry; compound could wait indefinitely for whole replacement. | Added typed guarded/forced same-main operation and narrow verified OFF completion. Old raw close remains a separate recovery tool. |
| Closing the residual before the compound checkpoint would count already-valued principal twice. | Capture aggregate principal, harvest, checkpoint before residual closure; release no compound reserve. Reinvest exact attributed idle, then verify final captured-value/balances and actual L. |
| A main-preservation hash including L cannot remain unchanged after increase. | Freeze full main/accounting/control identity excluding only intended idle/L/residual changes; separately require positive added L, zero residual and exact global count decrement. |
| Existing sampled identity excludes L to preserve ordinary entrant growth; already-OFF idle-only manual swaps could retain old observations/jitter. | Successful policy completion always increments this pool's control/global revision. Geometry increments only ON→OFF; ordinary user growth is unchanged. |
| Factoring timing into a read-only helper initially changed the caller of `Confirmation.emergencyReady`. | Retained bit16 remains a DIRECT Budget→Confirmation call. Only public Strategy predicates moved. Two positive actual-source sampled-evidence controls verify both consolidation and original full emergency. |
| Initial implementations exceeded ordinary bytecode limits. | Reused the fixed-Migration Vault manual wrapper, shared existing reinvestment/dust code, and extracted read-only validation into existing immutable companions. No generic dispatcher, delegatecall, new custody-bearing module or size waiver. Failed attempts are retained. |
| New participants could otherwise look compatible through accounting6/old wire shape. | Added residual-reinvest1 across Migration/Vault/Budget/Policy/Pricing and fresh inventory15, with explicit raw-exit1 graph checks. Historical14 modules/template/artifacts remain unchanged. Current seal does not itself prove every extension/runtime binding: preflight the coherent graph before seal. |
| Operational telemetry could be mistaken for revenue. | Added explicit event decoding; `ResidualConsolidated` never credits earnings. Actual fee allocation remains the income source. No governance action was added to keeper execution. |
| Older current prose still described schema14, full replacement as same-main consolidation, or royalty conversion. | Corrected relevant current docs; retained the former emergency-heading anchor, clarified full replacement versus same-main, and restored original-currency royalty allocation wording. |

## Architecture and permission boundary

The public governance entry is on Migration. The existing module-only
`Vault.emergencyRebalance` is now a **typed dispatcher**: its fixed Migration's
active consolidation context selects same-main reinvestment; otherwise the
original validated full emergency context replaces the portfolio. No caller
provides a selector, target module or recipient. New capability1 distinguishes
these semantics; old runtimes are not relabelled.

Validation remains read-only, immutable-parent-bound and noncustodial. All asset
movement and share/idle writes remain in the existing Vault. Normal compound
still releases designated reserves and observes its own eligibility. Raw closure
still preserves main L/mode. Full emergency still closes/replaces both legs.
The caller-sensitive fee and sampled-confirmation calls stay with their original
authorized callers. Zero optional financial mask is a deliberate governance
economic risk, not a keeper power or general withdrawal path.

## Remaining limits and decisions

- Guarded route selection is bounded. With an immutable main near a boundary,
  a chosen swap may push it inactive and correctly revert, even if another route
  could be feasible. Explicit reviewed routing/full replacement remain recovery
  choices; no global optimal/always-feasible quote guarantee is made.
- Forced reinvestment can accept an inactive unchanged main; it cannot recenter
  that range or guarantee fee earning. Disabling financial guards can lose nearly
  all principal. No force can repair a permanently broken token/core/chain or
  reopen terminal holder exit.
- Normal rounding/idle ceilings, tiny unrepresentable L, conditional compound
  timing and designated reserves remain intentional separate accounting states.
  No arbitrary sweep or unsupported-currency conversion is introduced.
- Actual fixed ZZZ/proxy/admin/callback and core/periphery qualification remains
  open. The earlier collect→burn late-fee boundary under compromised dependencies
  is not fixed by this management feature or its documentation.
- Matching fresh runtime/service/site configuration, dual feeds/routes/VRF, governance and
  provider selection, target gas/economics, OpenSea, sustained recovery operations
  and independent audit/remediation remain release gates. Vault has107 runtime
  bytes headroom; new extensions need another measured design/build review.

The prompt/matrix cover ordinary, forced, partial, repeated and recovery paths;
finite source/test evidence is not proof of every possible market/input. No
deployment, seal, public transaction, website build/rollout, service restart,
Anvil reset, journal change, signer extension or heartbeat restart occurred.
