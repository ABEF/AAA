# Follow repaired tests into their intended production behavior

Baseline: main `fdb7562bf56b11d8bade612fdaf7f9a54daf118a`.

**Repairing the test infrastructure was necessary, but did not by itself verify
every workflow that used it.** This follow-up traces those dependencies and
checks the intended implementation, failure stage, amounts, ownership and
recovery. It found a real manual-preparation race and additional stale test
expectations. Production Solidity, NFT rights and financial limits are unchanged.

The [executed request](EXECUTED_PROMPT.md) turns the user's concern into a
dependency/behavior review rather than another undifferentiated test rerun.
Historical reports and the four unrelated dirty files remain preserved.

## What the previous repaired tests reached

[Baseline dependency exposure](BASELINE_IMPACT_MAP.md) locates37 changed test
roots in63 consumer files containing666 declared methods. These are lexical
import/declaration counts, **not666 executed cases, branch coverage or a manual
proof of every method**. Importing a changed file can expose an unchanged type;
file-level exposure alone does not prove a behavior changed. The import map was
recomputed from actual baseline source, including compact `}from` syntax, rather
than blindly inheriting the earlier inventory parser.

The [LP map](LP_AFFECTED_METHODS.json), [rights map](RIGHTS_AFFECTED_METHODS.json)
and [tool map](TOOL_IMPACT.json) refine the review by actual fixture, production
function and asserted behavior. They overlap and must not be added together as
unique coverage. Generic revert expectations are investigated in context; their
presence is not automatically a bug.

| Intended behavior | Production path examined | Follow-up evidence |
| --- | --- | --- |
| Entrant-funded activation/growth and marginal shares | Entry → captured ContributionPricing/Budget → Vault checkpoint, deploy and share synchronization | Current97% and explicitly retained99% boundaries, incumbent idle/compound/donation exclusion, typed callback failures and successful retries. |
| One/two-leg replacement, mode changes and movement | Strategy/confirmation → Budget → Vault → Manager/position executor → actual v4 | Precise second-mint/residual-burn failures, exact custody rollback and retry; physical harvest; logical capacity/move/return and captured-policy checks. |
| Compound/idle interactions | Fee reserves → Compounder → existing-main reinvestment → new contribution | Preserve the independent compound interval, entrant isolation and5% idle guard; a large-reserve refusal is a legitimate operational gate, not permission to spend entrant funds. |
| Harvest and80/10/5/5 | Actual fee receipt → FeeController baskets/dust → Rewards/Membership and designated reserves | Both physical core receipts reconcile to exact claimant/reserve cash; tiny cross-user sequences and final dust settlement are checked independently. |
| Claims, transfers and terminal principal | Current-owner LP/royalty ledgers/router → Migration bounded allocation/direct payout | Partial claims, transfers, late activation, exact ordinal payout, repeat calls, failed final receiver and healthy-only continuation/recovery. |
| Royalties, metadata and replacement | Original-currency royalty opening/tickets; lifecycle reads; canonical funding/abort boundaries | Source-assessed descendant roles and new post-exit royalty/metadata assertions. Historical converting-royalty fixtures remain historical by case, not silently revived. |
| Hourly harvest scheduling through real preflight | Keeper.cycle → Keeper.submit → bounded simulation/estimate/dry-run | Actual submission code is reached with injected RPC; malformed void output cannot publish pending/spend/success clocks. |
| Manual/management unsigned review | Exact initial/final simulations, control hashes, last head and canonical anchors | Late reorg regression fixed; healthy advancement preserved; three premature management mutations moved between actual anchors. |
| Build/pre-seal consumers | Current trusted artifacts, constructor checks, required-read ABIs and false readiness flags | Actual pinned Forge configuration validator passes; unchanged compiler/artifact/source evidence is reused without rerunning suites. |

The finite result is29 distinct successful methods, deduplicated separately
from all dependency counts. Exact IDs and source stages remain in
[the verification record](VERIFICATION.md).

## Confirmed implementation fix

The manual preparer could finish both simulations, check the final simulation
block, then observe a newer head on a short fork that orphaned that block while
preserving the older confirmed snapshot. Its old same-height conditional did
not reject this advancing-head case. An injected-RPC reproduction failed before
the fix while healthy advancement passed.

`manual_lp_review.prepare` now rereads the **exact simulated height after the
last head read**, even when the head advanced. An orphaned anchor refuses the
review with `final_anchor_changed`. It moves the existing read rather than
adding an RPC request. Frozen calldata/gas, original expiry, fees, authority,
custody/control checks, two exact simulations and no automatic force fallback
remain. Management already had the correct ordering.

This is not atomicity across separate requests or immunity to changes after the
last response. [EIP-1898](https://eips.ethereum.org/EIPS/eip-1898) distinguishes
hash-selected state and canonicality; a future wallet action still needs fresh
validation. No signer, journal or transaction submission was added.
[Detailed tool review](TOOLS_REVIEW.md).

## Test defects corrected without changing economics

- A PooledSecurity negative still rejected a99% spend setting on50+50, which
  rounds to49+49=98actual LP units and satisfies the current97% minimum.
  Correct the rejection and retry around the actual policy;
  do not weaken production to satisfy an obsolete expectation.
- An EntryExecutionBudget case explicitly retains a1% policy, so99% is valid
  there too. Its old generic rejection was likewise stale. Keep that deliberate
  stronger profile separate from the default3% policy.
- Native entry-donation expectations omitted19 funded reward units: liabilities
  must remain19 and raw backing48 after a29-unit gift, not0 and29. Funding and
  unsolicited donations are separate.
- Three management tests mutated immutable first-anchor responses after an
  estimate. They now change state after the initial exact call and assert the
  intended final stage. Local-file mutation remains a different valid race.
- `RoyaltyLaunchWindow...AlwaysFullDay` is renamed `...AlwaysFullHour`; its
  existing one-hour body is unchanged and was not rerun merely for the rename.

## Independent physical and economic checks

The [three actual-v4 checks](PHYSICAL_VERIFICATION.json) now require the intended
PositionManager mint/burn errors, verify eight real custody balances after
failure and prove a healthy retry. Harvesting both legs measures actual core
ETH/ZZZ outflow, reconciles reward/fee cash, verifies80+10 for the sole incumbent,
5+5 reserves and dust, then pays exact claims without replacing positions.
These execute real core/periphery plus production financial modules, with
explicit controlled admission/controller/feeds/VRF/Permit2 and failure seams.
They do not qualify live markets or gas.

[Rights sequences](RIGHTS_REVIEW.md) add changing-holder, tiny-receipt and mixed
claim composition rather than asserting a single final balance. They verify
terminal principal and earned rewards stay separate, post-exit royalty rights
continue, healthy claims can proceed separately from a failed currency, and
recovery drains exact allocated backing. Raw fixed-ZZZ recovery is deliberately
preserved; it is distinct from the normal ETH conversion/UI path.

## Preserved boundaries and remaining work

All61 Solidity sources, compiler settings, current trusted build, public-null
configurations and Anvil-only signer remain unchanged. No existing Anvil, wallet,
site/service, database/journal or paused monitor was used or changed. Newly
prepared management reviews naturally bind the changed manual-helper source
hash; do not edit historical artifacts or journals to match it.

The finite checks do not establish full branch coverage of the dependency map.
Long fuzz/invariant campaigns, historical wrapped/Pons forks, maximum-state
workloads, complete fees/gas, live feeds/routes/VRF/OpenSea/hosting and independent
approval retain their explicit qualification limits. A failed external token or
receiver is not made reliable by a local accounting test. Source review,
declaration exposure, execution and production acceptance remain separate.

[Verification and exact records](VERIFICATION.md) describe passes, failed
reproductions, test-only compiler diagnostics and source stages. Todo acceptance,
operator recovery instructions, feature guidance and repository memory are
updated without closing broad release tasks.
