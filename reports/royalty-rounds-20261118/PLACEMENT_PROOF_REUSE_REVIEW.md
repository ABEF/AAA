# Placement and contribution proof reuse

This stage follows the initial round-engine build. It does not relabel that
earlier build or its gas results as evidence for the later Manager/Pricing source.

## Manager boundary

Only the immutable PositionExecutor's `balanceContext` calls omit repeated full
source validation. They still compute and compare the complete current balancing
policy fingerprint. The child is called only from the Manager's typed functions.
Manager `_beginPlacement` performs the full proof before entering it; no mutable
external call separates that proof from the child's first context read. After all
pulls, approvals, actual v4 settlement and refunds, the child verifies actual spot,
owner/key/bounds, exact physical liquidity, residual associations and policy hash.

For increases, only child-local reentrancy cleanup/return separates this last
context read from Manager `_endPlacement`'s full proof. Minting retains an explicit
full `_balanceContext(...,true)` immediately after the child returns and before
the mutable `Portfolio.recordApplied`; `_endPlacement` remains afterward. Public,
Vault and token-callback calls to `balanceContext` retain the full source proof.
The existing emergency fingerprint branch runs before this ordinary validation
choice, preserving priced and unpriced bypass-mask semantics.

The private immutable-child predicate is shared with the original child-only
modifier. There is no new caller, selector, storage, custody recipient or approval.
The one-object normal-default probe measured Manager24,459 runtime bytes and
48,146 creation bytes, with117 bytes runtime headroom. This is a size probe only.

## Contribution result boundary

The third `contributionNav` validates the complete execution scope after `_put`
and the late compound transfer, verifies the put mark and advances the phase to4.
Its remaining NAV reads are STATIC. Vault then performs local memory arithmetic
and calls fixed Budget `contributionResult`; Budget authenticates the Vault and
calls Pricing `finish`, which authenticates the Budget and requires the exact
phase/bucket/input/limits. No mutable external call intervenes.

`finish` therefore reuses the completed source proof while retaining
`_putUnchanged`, every captured USD bound/decimal/fingerprint, entry-policy match,
idle ceiling, incumbent/marginal deployed LP checks, caller loss floors, share
issuance constraints and original phase transition. Entry's final approval resets,
NFT/royalty/membership callbacks still precede the separate full `endEntry` proof;
direct Vault entry still performs the full proof in `_clear` before returning.

The Oracle child-creation probe retains runtime24,573 bytes and creation49,023
plus64 constructor bytes =49,087, within both original size gates. No full48-object
or target-chain gas approval follows from this one-object probe. Focused funded
actual-v4 regressions and the final combined source build are recorded separately.
