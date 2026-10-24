# Economic/native composition review and focused evidence

Recorded 2026-10-25. Internal review of the undeployed candidate; production is
**NOT APPROVED**. No public transaction, existing Anvil state, browser journal,
service, signer policy or monitoring action occurred. Production Solidity is
unchanged in this workstream. This is neither a fresh full regression nor an
independent audit or live-market qualification.

## Material availability finding: post-swap LP ratio drift

The actual installed v4 fixture exposed a safe but potentially avoidable rejection
at the selected fee settings. A one-shot balancing plan sizes the asset ratio at
the starting spot. Its own swap changes that spot, so the eventual LP allocation
can leave idle input even though total retained value exceeds the execution floor.
The marginal **deployed** floor correctly prevents presenting that idle input as
deployed LP.

Reproduction uses local hookless native v4, static LP fee 10,020 pips, spacing 200,
and 1,000 protocol-fee pips in each direction. Those are previously observed launch
parameters, not a new live read. Dual mock bounds are $1 per native/token unit,
the range is +/-10% before tick rounding, and external active liquidity is
`200_000 * 1e18`. The first one-sided native contribution is $100 in this fixture.
The real execution reaches `ContributionPricing.finish` with:

| Quantity | Fixture USD18 value, formatted as USD |
| --- | ---: |
| Original source input | 100.000000000000000000 |
| Actual deployed LP | 98.849621202259071431 |
| Attributed idle | 0.533536672418156838 |
| Retained LP plus idle | 99.383157874677228269 |
| Required deployed floor | 99.000000000000000000 |

The transaction reverts with `Slippage`; no funds, fees, LP ownership, shares,
activation or royalty eligibility survive. Preserve the
[full failed trace](economics/launch-failure-trace.log). This is an availability/
planner limitation, **not evidence of fund theft** and not a reason to relax the
1% floor automatically.

An [independent arithmetic diagnostic](economics/thin-feasibility.json) reconstructs
the observed deployed amount exactly and idle within two wei. Under that fixture's
known constant active liquidity, a hypothetical approximately 0.244785-token
reversal can leave approximately 99.380593 of deployed value. This shows the
recorded state is not inherently impossible within the same 1% execution budget.
**That reversal was not executed as a protocol transaction.** It is not a general
strategy, does not cover liquidity/tick crossings, and does not establish any
actual pool depth or price. The [diagnostic source](economics/thin-feasibility.py.txt)
is retained for review.

Follow-up belongs to activation/strategy qualification: simulate the complete
operation and reject infeasible quotes before wallet review. Any bounded post-swap
ratio correction must be independently designed, retain the captured loss budget,
preserve incumbent NAV and fee ownership, and pass actual-v4 shallow/range/rounding/
callback cases. No speculative planner rewrite was made in this audit.

## Open pre-signing boundary: a reviewed cap is not in the signed request

This was checked against committed `214d9a104643df0643a21ceec6970329f3525d3f`,
not an unrelated local draft. The four relevant working files match their
committed bytes; exact hashes/line observations are in the
[committed-source evidence](economics/review-cap-boundary.json).

- `ZZZActivationEntry.Request` (lines 53-63) carries output/liquidity minima and
  a deadline, but no caller maximum-loss or expected-policy field. `execute`
  starts at line 222.
- `ZZZContributionPricing._pair` (lines 76-78) captures the **execution-time**
  governed cap; `beginEntry` begins at line 99 and the required deployed floor
  is computed at line 211. This protects the operation after it starts, not the
  period between wallet review and inclusion.
- `frontend_api/activation.py` reads the cap at lines 182-188, derives the caller
  minimum liquidity from simulated LP units and caller slippage at lines 247-248,
  and reports the reviewed cap at line 267. The trace cap comparison at
  `activation_trace.py:275` applies to the pinned preparation trace.

If governance raises a cap before a pending Entry begins, the old signed request
does not itself require the old cap. Exact raw output/liquidity minima still bind
and may cause a revert, but they are not a signed USD/policy guarantee; different
prices, range/liquidity state and caller slippage matter. Fresh wallet simulation
can reject a changed review before submission but cannot eliminate the subsequent
inclusion race. Mid-Entry callback protection remains intact.

This is an open **pre-public-signing release gate**: introduce and review a
versioned Entry path with caller maximum-loss expectations, coordinate backend/
schema/wallet changes, reject stale policy, and permit no silent legacy fallback.
Until then, UI/operator documentation must not promise an immutable review-pinned
1% ceiling. Immediate governance/custody trust remains accepted; no speculative
ABI or cap rewrite was made during this audit, and Anvil-only signing is unchanged.

## Harness improvements before relying on the new tests

[IntegratedEconomicConservation](../../test/IntegratedEconomicConservation.t.sol)
combines actual installed `PoolManager`, `StateView` and `PositionManager` with real
Entry, Vault, Oracle, Strategy, membership and both funded reward ledgers. Trading
fees come from actual core swaps, rather than a fake fee setter. Separate ghost
cash totals use actual funding and payout observations, not copied reward-index
formulas. Assertions cover physically backed LP versus royalties, pre-existing
native/token prefunds, share conservation, no retroactive income, actual LP
ownership, transferred claims, successful growth/compounding/rebalance and tiny
receipts/fractions.

The final callback scenario requires the actual hostile `MockFeed.set` call and
the specific final-check error. Its earlier generic `expectRevert` was strengthened
because a prior thin-market rejection could otherwise make it pass without
reaching the intended callback. The explicit thin-market case similarly requires
the final contribution check before asserting its expected rejection. No early
return is used to hide either path.

Full-lifecycle and late-callback success-path setup explicitly increases external
liquidity to `2_000_000 * 1e18`; the thin-market rollback remains at the original
depth. This is an explicit test prerequisite, not a claim about production depth.
Mock governance/admission, token, dual providers, VRF and `FactualPermit` remain
substitutes. No external creator-reward inbox, actual Chainlink/ZZZ provider,
marketplace, conversion service or canonical/cross-chain handoff is qualified here.

The existing [NFT rights invariant](../../test/NFTRightsInvariants.t.sol) also had a
stale input domain: two $1 zero-decimal tokens with equal amounts `1..100` permit
invalid $2/$4 top-ups after the real $5 minimum was introduced. Its lower bound is
now three units per side ($6). A completed-action counter and strict share-growth
assertion prevent valid top-ups being silently skipped. A new minimum-bound
regression requires the action to finish. The invariant's mocked custody/VRF/
pricing/authority scope remains explicit.

## Exact verification scope and retained diagnostics

| Scope | Result and reuse boundary |
| --- | --- |
| Preliminary generic 3,000-pip/spacing-60 fixture | Four passes retained as preliminary evidence only; not the final fee configuration. |
| First selected-fee fixture | Three passes and the real one-sided thin-market failure above. The old generic callback assertion is superseded, not counted as final evidence. |
| Final selected-fee changed/new cases | Three fresh passes: full lifecycle at explicit depth; final-approval round rollback with required call/error; complete thin-market rollback. |
| Two unchanged selected-fee cases | Balanced/no-old-income/prefund and repeated tiny receipts/claims retain their exact earlier pass scope. Twenty-one unchanged function/helper texts are pinned in the reuse proof; no blanket final-source rerun is claimed. |
| Repaired NFT rights invariant | 32 runs, 128 depth, 4,096 calls, zero reverts/discards, `fail_on_revert=true`; all eleven selected actions exercised. |
| New minimum-bound top-up regression | Pass, with completed-action counter and actual share increase. |
| Compile-only harness diagnostic | One contract-to-address argument error was repaired before those three final scenarios executed. No test pass is attributed to that attempt. |

There are **five distinct actual-v4 scenarios plus one repaired invariant and one
new minimum-bound regression**. Repeated selectors are not additional cases.
The invariant selected `topUp` 389 times; eligibility/pause early returns remain,
so that is not a claim of 389 completed contributions. See the
[exact metrics](economics/invariant-metrics.json).

The [scoped receipts](economics/scoped-runs.json),
[50 final source/test bindings](economics/final-source-bindings.json),
[unchanged-function proof](economics/unchanged-function-proof.json) and
[dependency bindings](economics/dependency-bindings.json) preserve source scope.
The dependency record verifies 133 imported files against actual compiler metadata,
records raw SHA-256 and compiler-normalized Keccak separately, and retains package
lock/toolchain/forge-std identity. Executed Permit2 allowance logic is still the
declared test substitute; compiling its real interfaces is not Permit2 execution.
Raw large JSON traces remain in the external local campaign; their hashes are in
the compact receipts. The compile-only diagnostic and failed-launch trace are
retained alongside this report.

No new exploitable economic fund-diversion defect was confirmed in the inspected
paths. This does not prove absence of vulnerabilities. Actual source independence,
market depth, venue/token changes, gas, operating services, accepted immediate
governance/custody trust and independent review remain release requirements.
Unchanged normal production size gates retain their earlier source scope.
