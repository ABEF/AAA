# Governance portfolio management: implement, audit and document

Baseline main `9025735fca5a6011bce3772f981881d66d3ea082`, 6 November 2026.
This is the executed project-specific prompt, not production approval.

## Objective and evidence-first scope

Implement the missing operator workflow: close only the optional residual and
reinvest its actual ETH/ZZZ proceeds into the existing main, preserving that
main's ID and ticks. Include recovery of already-attributed idle from an earlier
raw close. Review the complete one/two-position management cycle so the operator
can distinguish policy changes, deployment, temporary closure, reinvestment,
whole replacement, parking/resume and terminal holder return.

Read current instructions, context, both project boundaries, operator procedures,
current ABI/normal build evidence and actual core/periphery implementations.
Trace permissions and pre/postconditions rather than infer behavior from names.
Preserve existing decisions: one fixed native ETH/ZZZ pair, one contribution pool,
bounded shared buckets, one main plus at most one residual per bucket, fixed
80/10/5/5 and separate original-currency royalties, current-owner unpaid rights,
no custody recipient/bridge, and irreversible terminal holder exit.

## Interpret and challenge the request

"Force" means a manual governance operation can explicitly bypass selected
economic/timing policies. It does not mean arbitrary external calls, arbitrary
recipients, forged shares, spending reward reserves, changing the fixed token,
reopening terminal principal or manufacturing liquidity through a broken core.
Never install governance signing on the keeper host or automate emergency fallback.

Distinguish existing main validity from desired future geometry. A healthy main
can be increased without withdrawal. Increasing an outside-range main does not
recenter it or make it earn fees. Resolving residual OFF must not falsely resolve
a separate pending main width/orientation change. Desired ON/OFF, applied policy,
actual residual existence and global registered count are different state.

## Implementation requirements

1. Add one explicitly versioned, paused, governance-only typed consolidation
   entry point. Provide guarded automatic reviewed routing and an explicitly
   forced exact-swap manifest. Preserve old emergency full-replacement semantics.
   Guarded manual consolidation must not inherit keeper cooldown, sampled timer,
   jitter or standalone-compound eligibility. Retain independent prices, actual
   spot/tick validation, route/venue admission, output floors, captured total
   retention/idle limits and active-main placement in the guarded path.
2. Support unfilled, mixed, fully converted and outside residual inventory,
   desired ON or OFF, and no-residual plus positive attributed idle. Reject
   parked/no-main/empty work, preparation/canonical lock and terminal exit through
   their existing boundaries. Both modes end with one main and desired OFF.
   The operator may later enable optional mode through the existing setter.
3. Capture exact physical/accounting identity, control revisions, governance,
   pause state and review nonce/epoch. Bind the new operation domain and consume
   shared recovery freshness so old/replayed/restored manifests cannot revive.
   Explicit request ticks must match the existing main. Caller minimum liquidity
   is a positive ADDED liquidity delta, not total L or USD.
4. Capture starting aggregate principal once; harvest both legs and allocate
   actual fees; checkpoint before closing the residual so returned principal
   cannot be counted twice as newly released compound. Reinvest only attributed
   bucket idle, including recovered residual principal. Do not release designated
   compounding reserves or touch earned rewards/buyback/royalty backing implicitly.
5. Close the actual residual only. Preserve main ID/full packed position info,
   pool/key, owner, bounds, centre, lastRebalance, status, shares and contribution
   accounting. Balance only the explicit attributed budget, harvest main fees
   earned by that swap separately, increase that same main, verify positive exact
   physical L growth and exact token deltas/refunds. No third leg or recipient.
6. Acknowledge OFF only after successful actual reinvestment and verified zero
   residual. Limit the completion writer to this typed, active governance context.
   Freeze unrelated policies through callbacks, including when all optional
   financial checks are disabled. Preserve the distinct main-range pending test.
7. Record the successful swap-bearing operation in the compound timing state,
   without postponing ordinary rebalance by changing lastRebalance. Existing
   residual identity/policy changes must invalidate old observation/jitter work;
   do not add L to the stable fingerprint and regress ordinary user growth.
8. Require complete atomic rollback of fee allocation, residual burn, swap,
   increase, policy acknowledgment, nonce/epoch and temporary contexts on failure.
   Keep pause ON after completion; unpause remains explicit. Preserve raw residual
   close, full emergency replacement, parking/resume and terminal return fallbacks.
9. Keep this governance operation out of automated keeper actions. Introduce an
   explicit fresh capability/inventory boundary with exact runtime pins; preserve
   old inventories, readers, journals and compiler-artifact families unchanged.
10. Respect normal EIP-170/EIP-3860 limits. Prefer typed read-only validation
    extraction and shared internal flow over generic executors/delegatecall or
    new custody-bearing modules. Migration/Vault/Budget headroom is a measured
    constraint, not permission to waive gates.

## Management and failure matrix

Audit and document: one→two enable; two→one normal or forced consolidation;
raw residual close; already-closed idle reinvestment; OFF→ON→OFF repeated cycles;
separate pending range changes; manual full recenter; source/destination pool
changes; both-leg parking; guarded resume under destination mode; pause/unpause;
disabled deposits versus maintenance; token/feed/route/core failure; recovery
after ambiguous submission or host loss; and terminal closure/distribution.

For each case identify the exact function, caller, every input/unit/hash source,
current-state reads, expected result, blocked condition, reverse/recovery path,
pause/restart behavior and irreversible boundary. Explain where an existing
operation is sufficient instead of adding another overlapping function. Explicit
manual full replacement remains the choice when main geometry/destination must
change; no promise of forced active placement into unsuitable unchanged ticks.

Consider price trends, reversals, exact tick boundaries, volatile price between
review and execution, residual fills, tiny/zero representable liquidity, large
idle, all four bucket/residual slots, multiple NFT owners and unequal shares,
activation/growth/claims/transfers before or after management, unrelated donation,
false RPC replies, failed token calls, revoked authority, callback control changes,
stale nonce/epoch, deadline expiry, fee-on-swap and insufficient remaining venue
liquidity. Independent transactions serialize on-chain; stale reviews must fail
without losing a previously confirmed operation or consuming someone else's funds.

## Verification and completion

Use focused actual-v4 scenarios and independent balance/share/reward assertions
for changed behavior. Retain original failing/setup/empty attempts; do not count
them as passes or sum repeated overlapping stages. Update stale fixtures only
when they contradict the established current model, never weaken guards to pass.
Do not rerun unchanged broad suites without a new justified concern.

Rebuild exact normal artifacts and size gates for changed Solidity. Review fresh
static findings in their exact source contexts; reuse only byte-identical source
scope. Verify fresh inventory/capability consumers, manifest/reference generation
and exact staged/committed Python publication. Preserve protected working files,
old reports, website/signers, services, Anvil state and journals. No deployment,
sealing, public transaction, rollout, reset or heartbeat restart is authorized.

Update operator procedures and examples, ABI reference, feature/evidence record,
single Todo ledger, roadmap, release notes and repository context. Finish with
actual improvements, verified results and unresolved dependency/economic/operating
limits. Do not describe an internal review as independent production approval.

## Prompt review before execution

First challenge: an apparent close→compound recipe fails after mode OFF because
pending geometry blocks compounding; increasing existing L also invalidates the
old fingerprint that intentionally included L. These require a typed completion
and exact preservation checks, not a keeper scheduling workaround.

Second challenge: closing before the compound checkpoint can double-count the
already-valued residual; clearing all pending geometry could discard an intended
range change; fee-on-increase could become principal; and optional financial
bypass must not bypass policy/custody callbacks. The requirements above explicitly
cover these distinct points. "Every imaginable case" is not a provable completion
criterion: use a traceable state/transition matrix and bounded evidence instead.

Primary references checked alongside the pinned dependency source:
[Uniswap increase](https://developers.uniswap.org/docs/protocols/v4/guides/managing-liquidity/increase-liquidity),
[fee collection](https://developers.uniswap.org/docs/protocols/v4/guides/managing-liquidity/collect-fees),
[Solidity 0.8.26 security](https://docs.soliditylang.org/en/v0.8.26/security-considerations.html).
Their generic examples do not replace PoPL's exact fee/principal classification,
authority checks, pinned settlement path or normal constructor-size evidence.
