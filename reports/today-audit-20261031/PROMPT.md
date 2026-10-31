# October 31 change audit: final execution prompt

## Objective and actual baseline

Audit and improve the changes published in `37577eb..e4113b7` and their complete
reachable interactions. The October 31 publication combines October 30–31 work;
commit time is not proof that every changed line was written today. Establish
the actual baseline, dirty files, dependency/compiler pins and prior evidence
before editing. Current source is accounting6/ProtocolPolicy1/Portfolio2 with
maintenance3/confirmation3/compound4/custody4/emergency2/LP-routing2 and
reviewedEntry2. Existing deployments, sites and journals are different profiles.

The objective is concrete correctness, security, availability, accounting,
operating recovery and efficiency improvements. A report alone is insufficient
when a justified correction can be implemented and verified. Conversely, do not
invent a behavioral change to make an audit appear productive.

## Evidence and knowledge preparation

Read instructions, context, README, sole Todo, handoff, relevant operator
procedures, current architecture/policy and previous source-scoped findings.
Map each changed component to callers, callbacks, state, permissions, external
dependencies, consumers, outputs and recovery. Read actual version-pinned
Uniswap/OZ implementations; use primary security/specification documentation
for uncertain assumptions. Documentation is an input to challenge, not proof.

Freeze raw source/dependency/configuration hashes and preserve original dirty
documentation, unrelated files and historical reports. Reuse an earlier result
only when its actual production/dependency/settings closure still matches;
state which test bodies were reused and which were newly executed. Empty runs,
inventories, static rows and compilation are not transaction test passes.

## Audit matrix

For each relevant read, write, constructor, receiver, worker and manual workflow,
evaluate normal operation, boundary and strange input, hostile ordering,
reentrancy, dependency failure, partial progress, pause, restart and recovery.
Prioritize reachable financial/custody defects over cosmetic cleanup.

1. **Policy and authority:** fixed bindings, bootstrap/sealing order, scoped
   fingerprints/revisions, change-and-restore, callback changes, review expiry,
   future mint recipient acceptance, minima, gas and display policy. Confirm
   cosmetic/unrelated changes do not invalidate economic work, while relevant
   changes cannot silently weaken an operation. Governance trust is explicit;
   a nonzero reviewHash is provenance, not proof of review.
2. **Mint/reveal/canonical:** exact ETH payment, caller/recipient semantics,
   rollback, supply/quotas/draw order, request identity across providers and
   deployments, pending fulfillment, drained rotation, provider upgrades,
   receiver faults, preparation/abort/retirement, threshold compatibility and
   inactive successor isolation. Do not add rerolls or infer live VRF support.
3. **Entrant accounting:** ETH/ZZZ only, incumbent checkpointing, entrant-only
   swaps/deployment, actual marginal main LP, aggregate incumbent NAV including
   residual and idle/compound, net share issuance, rounding, partial allowances,
   dust, minimum/cap edges, atomic failure and no recenter/clock reset.
4. **Two-position operations:** one main plus at most one residual in the same
   actual pool; correct price orientation/ticks/gap, actual core amounts, bounded
   swap sizing/routes/fees, main allocation proof at captured prices, contributions
   to main only, both-leg harvest/valuation/close. Cover no residual, mixed,
   filled, outside, tiny and unplaceable residuals, mode changes and pool moves.
5. **Fees and claims:** actual received fees split once at80/10/5/5, equal active
   collective membership, rarity-only royalties, claim-order conservation,
   fractions/dust, current-owner rights, conversions and old claims not counted
   as new earnings. Separate principal, rewards, compound, buyback, quarantine
   and deferred-currency backing before and after manual/terminal operations.
6. **Keeper and execution:** sampled85%-boundary trigger, independent-reference
   corroboration, hard cooldown,600/240/300 timing, reset acknowledgement,
   jitter, range exception, compound waiting, hourly harvest/coalescing and
   deadlines. Verify deterministic guard capture, actual directional fee versus
   additional loss, route failure and no automatic unsafe fallback. Public
   timing and bounded losses are not manipulation immunity.
7. **Outage/manual recovery:** missing prices, RPC faults, stopped service,
   process death at each intent/submission/receipt/persistence boundary, nonce
   gaps, duplicate/reordered receipts, stale config, disk corruption/full disk,
   lock contention and server replacement. Pending transaction recovery comes
   first; never replay a possibly submitted transaction or rewrite a journal
   to pass. Verify park/resume, residual-only close, forced single consolidation,
   terminal current-owner payouts/rejecting owners/retry and reserve-only venues.
8. **Backend/concurrency:** pinned same-block identities, strict JSON/ABI,
   source profiles, complete ownership/history, optional-currency isolation,
   unavailable versus zero, today-price earnings, decimals/overflow, concurrent
   account operations and bounded resources. Audit both current and historical
   reader admission without relabeling old records.
9. **Publication/operations:** inspect the exact tracked source closure as a
   clean checkout would see it, not just the working directory. Detect missing
   modules, stale templates, invalid startup examples and misleading readiness.
   Verify source-bound operator commands and inputs, stop/restart, reversibility,
   evidence/log secrecy and compatibility boundaries.
10. **Build and maintenance:** normal compiler/size gates, constructor limits,
    immutable child graph and library pins, meaningful tests, no weakened gates,
    generated callable/source references, task/feature/operator/context consistency.
    Tight bytecode is an explicit maintenance risk, not permission to remove a guard.

## Two pre-execution prompt challenges

**First review — omissions and project fit:** the initial idea of auditing only
new Solidity misses fresh-checkout publication, service recovery and changed
consumer closures. Include all three. Exclude retired bridges/creator inboxes,
external custody exits, extra contribution tokens, public signing and deployment.
They are removed or unauthorized, not features to restore. Preserve fixed
economics and the approved configurable bounds, including the hard60% main floor.

**Second review — feasibility and misleading assurance:** exhaustive input
testing or a no-hack guarantee is impossible. Require explicit inspected scope,
findings with traces, independently reviewable fixes, useful regression evidence
and remaining external gates. Sampled confirmation is not continuous history;
codehash is not proxy immutability; a local mock/provider/gas bound is not live
qualification. Build/test evidence cannot detect a missing unpublished module
unless the exact Git source closure is separately inspected. Preserve original
failures and negative publication evidence. No audit action may restart services,
change old journals, broadcast, deploy, seal or update sites.

## Execute and finish

Investigate in parallel where independent. Explain each finding's preconditions,
impact, reproduction/evidence, correction and tradeoff. Implement narrow repairs
that preserve rights; isolate unresolved consequential choices and continue safe
work. Improve verification where needed before running the affected checks.
Run fresh normal gates for changed Solidity; reuse exact unchanged evidence
otherwise. Do not repeat whole suites merely to increase counts.

Update the sole task ledger/generated Todo, feature/evidence reference, operator
procedures, current context and source-bound callable docs as applicable. Preserve
historical report bytes and unrelated work. Publish only intended changes on main
under the repository workflow, verify remote identity, and distinguish source
publication from deployment. Report actual improvements, fresh versus reused
verification, static-review limits, remaining decisions and production blockers.
