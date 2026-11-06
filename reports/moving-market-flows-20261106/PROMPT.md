# Both moving-market LP flows: audit and improvement scope

Baseline main e1a85a2, 6 November 2026. Production NOT APPROVED. This is source
work only: no deployment, sealing, public transaction, running service/site,
signer extension, journal/Anvil reset or heartbeat restart is authorized.

## Establish the actual model

Inspect current instructions, both architectural boundaries, the maintained
operator procedures, production source/dependencies, keeper submission/recovery,
current tests and exact earlier evidence. Distinguish:

- fixed per-position main/residual bounds and IDs from the moving pool tick,
  sqrt price, token composition, fees and actual liquidity;
- automatic full replacement, including desired OFF two-to-one merges;
- manual guarded same-main reinvestment, explicit forced same-main operation,
  and separately reviewed full emergency replacement;
- execution-time parameters from read-time observations, reviewed economic
  limits, pending transaction identities and purely service scheduling;
- one logical NFT share account from its one or two physical LP NFTs.

Use pinned Uniswap core/periphery and official documentation to resolve protocol
questions; do not infer state from a chart or mix runtime/codec generations.
The earlier read-to-execution campaign is source-scoped evidence, not proof of
all markets, uninterrupted price history, months of uptime or independent audit.

## Audit every relevant input and interaction

For each field below record source, caller, units, allowed changes, capture
point, rechecks, failure behavior, accounting effect and explicit recovery:

1. Chain/controller/runtime/helper/capability bindings, expected sender and role.
2. Bucket/main/residual IDs, physical ownership, pool key/fee/tick spacing,
   position bounds, current stored tick and sqrt, both physical liquidities,
   reservation/count/capacity and active/parked/terminal/canonical lifecycle.
3. Shares, aggregate NAV, actual attributed idle, designated compound reserves,
   collected/uncollected fees, old holder claims, donations and raw prefunds.
4. Governance width/orientation/mode/residual/main-floor settings, applied versus
   desired geometry, revisions, pause and deposit/operation/venue flags.
5. Dual source identities/values/rounds/ages/3% agreement, independent reference,
   pool deviation, sequencer status, actual directional fees and trade depth.
6. Quote venues, amounts/direction/output/target-price predictions, bounded search
   and gas, additional-loss limits, gross maintenance/contribution limits,
   deployed/idle/main-floor checks, raw added-L versus new-position-L minimums.
7. Main centre/lastRebalance, compound clock, 12-hour minimum, 85% trigger,
   600/240/300 sampled confirmation, geometry exception, jitter and resets.
8. All twelve manual request fields and forced flag, custody/portfolio/control
   and review hashes, nonce/epoch, retained-mask meanings, raw-close floors.
9. Exact calldata/value, original deadline, simulation head, gas limit/price,
   L1 allowance, per-operation/day spend, wallet funding, nonce, durable pending
   intent, transaction identity, receipt/depth/reorg and restart/recovery data.

Trace changes before preparation, after simulation, before signing, before
inclusion, during our swap/external callbacks, at postconditions and after
confirmation. Other transactions cannot interleave inside an atomic EVM call;
our own swap and callbacks can change feasibility. Treat those separately.

## Market, user and operating cases

Cover rising/falling/choppy/gapped prices, exact lower-downward/upper boundaries,
local-pool/reference disagreement, thin/unavailable/disabled routes, fee changes,
full and partially filled residuals, one/two/no-deployed-position states, pending
width/mode changes, existing idle-only recovery, repeated ON/OFF cycles and
several admitted historical buckets. Test activation/growth before replacement,
after pause and after resume; preserve incumbent/entrant NAV, clock identity,
current-owner rights and exact 80/10/5/5 once per actual receipt. Royalty currency
failures and claims retain separate rights; do not revive removed converters,
bridges, creator inboxes or arbitrary recipients.

Cover stale/mixed/reorged RPC state, failed/malformed/slow responses, revoked
authority, expensive gas, midnight rollover, competing same-key signing, pending
or ambiguous submissions, reverted transactions, process crash and recovery.
No unknown value becomes zero, no stale record is relabelled, and no automatic
retry is permitted to enable force or silently change economic intent.

## Implementation and verification

Identify intentional safety stops versus avoidable liveness failures. Implement
the smallest justified corrections; keep permission/economic/storage changes
distinct from stronger routing/pre-sign checks. Preserve all rights and approved
policies. Do not introduce an automatic whole-bucket fallback for a same-main
request, a successful no-op that impersonates completion, unlimited retries,
longer caller deadlines or weakened financial guards.

Verify new behavior with nonvacuous actual-local-v4 and focused keeper cases.
Improve deficient fixtures rather than changing production limits to pass them.
Retain original failures, skips and source stages. Use isolated owned caches and
filtered test environments. Do not rerun unchanged suites without a concrete
shared-path reason. After production changes run fresh normal closed bytecode
gates and actual static review; exact unchanged referenced-source reuse must be
proven and the CI/default pointer updated together. Import current compiler
evidence into the complete callable reference and preserve explicit examples.

Update the single ledger, features, operator guide, relevant operating/policy
documents, roadmap/release boundaries and repository context. Preserve original
report bytes and the four unrelated dirty files. Publish intended source/docs
only on main after exact staged/committed Python closure checks; confirm actual
remote heads. Report verified improvements and unresolved qualification clearly.

## Two critical reviews of this scope

First: the old main's bounds do not drift with swaps; rejecting an ordinary
rebalance merely because its OLD band is outside would defeat replacement.
Automatic new bounds/routing are already derived at execution. Improvements
must target actual stale-submission and feasible-route gaps, not duplicate that
existing mechanism or change ordinary entrant behavior.

Second: not every blocker is a defect. Fresh prices, loss/idle/output/utilization
limits, caller floors, ownership, callback proof, lifecycle and pending recovery
constrain different risks. Give every blocker a diagnosis and valid recovery;
never promise that every requested trade is safe or always executable. Explicit
forced full replacement may accept inactive geometry by design; do not silently
upgrade its optional financial choices into an ordinary keeper fallback.

Primary documentation, read with the actual pinned implementations:
- [Uniswap v4 increase](https://developers.uniswap.org/docs/protocols/v4/guides/managing-liquidity/increase-liquidity)
- [Uniswap v4 fees](https://developers.uniswap.org/docs/protocols/v4/guides/managing-liquidity/collect-fees)
- [Solidity 0.8.26 security](https://docs.soliditylang.org/en/v0.8.26/security-considerations.html)
