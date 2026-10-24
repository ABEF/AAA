# Hookless native ETH / ZZZ adapter

Updated 2026-10-24. The [selected existing pool](POOL_SELECTION.md) replaces the old
Pons integration. Historical Pons reports keep their original source/block scope.

## Admission

`configureNative` accepts initialized static, hookless native ETH/ZZZ markets on
Robinhood 4663 with six pinned dependency runtimes, exact wiring and reviewed WETH
proxy policy. `SELECTED_NATIVE_POOL` identifies launch; later governed fee tiers
remain possible after sealing. Dynamic fees, hooks, other native pairs, missing
slot state and wrong static fees fail closed. WETH/ZZZ uses ordinary `configure`.

`get` preserves the real key; `accounting` normalizes native slot zero to WETH
without re-sorting. Never hash the accounting copy as the real native identity.
`nativeAsset` returns the reviewed wrapper. Accounting/native reads recheck bindings.
Protocol-fee changes do not freeze collecting/closing; swap output minima remain.
No Pons factory, hook or creator-payout getter is needed.

## Settlement

LiquidityManager unwraps only exact rounded-up native principal debt and checks
actual minted/increased LP, ownership and balances. It preserves its own and
PositionManager prefunds; no sweep. Vault harvests before increase so accrued
native fees cannot silently offset new principal debt. Unexpected offsets revert.
Unused budgets return to the authenticated caller; exact token/Permit2 approvals
are cleared. Collection/close wrap only expected core credits into attributed WETH.
Swaps use actual net output, exact full input and unchanged price/slippage guards.
Forced ETH, partial fills and malformed callbacks cannot become principal or fees.

## Operations and trust

`moveFunds` atomically changes native/WETH venues or fee tiers within the same
ordered pair under the fixed 3% cap. [External exit](GOVERNED_CUSTODY_HANDOFF.md)
is separate. Contributions/routes require deliberate cutover after checking LP.

Canonical WETH is a proxy: admin, implementation, owner and runtime policy remain
append-only and governed. Getter/code checks are not a proof against a malicious
proxy administrator installing lying getters; independent storage/authority review
is still required. Native pool selection does not eliminate internal WETH trust.

[Verification scope](../reports/hookless-pool/VERIFICATION.md). Live prices/routes,
services, operating rehearsals and independent audit remain open. No public signing,
transaction, deployment or existing Anvil state change is implied by this candidate.

### Open native recovery requirement

The current raw exit bypasses swaps and USD prices, but still calls native venue
collection/close through the wrapper. A failed WETH deposit/withdraw, policy or
proxy can therefore block it. The user requires robustness and efficiency over
preserving existing code;
[native ETH custody/accounting](NATIVE_ETH_ARCHITECTURE.md) is the requested
architecture direction and remains unimplemented pre-seal work. It must classify
principal and fees separately and preserve every liability; a generic payable
withdraw/sweep would not satisfy it. Wrapping should remain only at a separately
reviewed boundary for an operation that actually uses WETH, without making native
LP recovery depend on it.
