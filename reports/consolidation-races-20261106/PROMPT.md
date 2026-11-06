# Focused read-to-execution and long-lived operation review

Baseline main7cc0f55. Investigate the user's concern: swaps and NFT actions can
change state between Manager.ticks(mainPositionId) and manual same-main
consolidation, and this project must keep operating over weeks/months.

First distinguish immutable per-position tick bounds from current tick/spot,
position amount composition, accumulated fees, actual L, logical NFT shares,
desired geometry and the identity of a replacement position. Trace actual pinned
v4 core/periphery and all PoPL call boundaries rather than relying on charts.

Evaluate both transaction orderings around pause, submitted-versus-confirmed
pause, stale/mixed RPC snapshots, reorgs, custody hashes, deadlines and floors;
trades in the target/other reviewed venue; residual unfilled/mixed/converted;
whole replacement, raw close, park, settings changes, claims/transfers and
repeated single/hybrid cycles. Evaluate callbacks separately from transactions
which cannot interleave inside the atomic call. Preserve normal versus explicit
forced behavior and principal/reward/compound separation.

Implement only justified corrections. Add focused nonvacuous tests only for
missing read-to-execution cases; reuse exact unchanged production build/static
evidence and existing lifecycle campaigns with their original scope. Do not
retest all unchanged contracts, manufacture independent feeds or claim virtual
time establishes uptime. Preserve original test bodies, negative attempts,
protected dirty files, old report bytes and all live environment boundaries.

Challenge1: a price movement does not mutate an existing position's bounds;
adding a stale-price equality requirement would cause avoidable failures.
Challenge2: the custody hash is neither a price quote nor every configuration
fingerprint. Check current execution guards and explicitly require fresh operator
review after configuration changes rather than claiming every old review must
revert. Include exact boundary stored-tick behavior and ambiguity/recovery.

Deliver code-line findings, focused evidence, a useful operator procedure and
updated existing task/feature/memory pointers. Production is not approved. No
deployment, public transaction, service/site/signing change, Anvil or journal
mutation, heartbeat restart or new runtime/profile is authorized.

Primary references inspected with actual pinned source:
- https://developers.uniswap.org/docs/protocols/v4/guides/managing-liquidity/increase-liquidity
- https://developers.uniswap.org/docs/protocols/v4/guides/managing-liquidity/collect-fees
- https://docs.soliditylang.org/en/v0.8.26/security-considerations.html
