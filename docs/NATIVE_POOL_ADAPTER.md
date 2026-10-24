# Hookless native ETH / ZZZ adapter

Updated 2026-10-24. The [selected existing pool](POOL_SELECTION.md) replaces the old
Pons integration. Historical Pons reports keep their original source/block scope.
The native V2 contract candidate now preserves ETH throughout custody/accounting;
it is undeployed and not approved for real funds. See the
[native-port evidence and limits](../reports/native-eth-port/VERIFICATION.md).

## Admission

`configureNative` accepts initialized static, hookless native ETH/ZZZ markets on
Robinhood 4663 with five pinned dependency runtimes (Core, PositionManager,
StateView, Permit2 and ZZZ) and exact wiring. WETH code, its proxy policy and the
optional periphery wrapper getter are not native admission dependencies.
`SELECTED_NATIVE_POOL` identifies launch; later governed fee tiers
remain possible after sealing. Dynamic fees, hooks, other native pairs, missing
slot state and wrong static fees fail closed. WETH/ZZZ uses ordinary `configure`.

Both `get` and `accounting` preserve native `address(0)` in the real slot order.
`isNativePool(poolId)` identifies native pools explicitly. The legacy
`nativeAsset` getter returns zero, never a wrapper; do not infer whether a pool is
native from that getter alone. Accounting/native reads recheck actual venue bindings.
Protocol-fee changes do not freeze collecting/closing; swap output minima remain.
No Pons factory, hook or creator-payout getter is needed.

## Settlement

LiquidityManager forwards only exact rounded-up native principal debt and checks
actual minted/increased LP, ownership and balances. It preserves its own and
PositionManager prefunds; no sweep. Vault harvests before increase so accrued
native fees cannot silently offset new principal debt. Unexpected offsets revert.
Unused budgets return to the authenticated caller; exact token/Permit2 approvals
are cleared. Collection/close forward only expected native core credits to the
Vault. Vault classifies actual ETH fees into FeeController, which funds the native
individual/equal-collective reward indices and separate 5% compound/buyback reserves.
Swaps use actual net output, exact full input and unchanged price/slippage guards.
Forced ETH, partial fills and malformed callbacks cannot become principal or fees.

## Operations and trust

`moveFunds` atomically changes fee tiers within the same ordered actual-currency
pair under the fixed 3% cap. Native ETH and WETH are different currencies:
an atomic ETH/WETH boundary is not implemented and the pair guard rejects it.
[External exit](GOVERNED_CUSTODY_HANDOFF.md)
is separate. Contributions/routes require deliberate cutover after checking LP.

Native raw exit sends actual ETH and ZZZ under approved raw minima, without a
swap, USD quote or wrapper call. Recovery and local completion require the exact
declared native budget; old donations cannot replace missing funding. A broken
pool or ZZZ token can still prevent an exit. No generic withdrawal or sweep exists.

An operation explicitly using WETH, such as an admitted v3 reward-conversion route,
retains its own reviewed wrapper/proxy dependency. Getter/runtime checks alone do
not prove a proxy administrator cannot change its behavior. Failure of that
optional operation does not make native LP custody or raw recovery call WETH.

## Qualification and historical scope

The native V2 schema is distinct from the earlier WETH-accounting deployment.
Legacy V1 canonical handoff is rejected; no silent WETH-to-ETH reinterpretation or
old-source import compatibility is claimed. Backend profiles and historical epochs
must identify their actual accounting version before integration is enabled.
The API/keeper candidate supplies explicit versioned profiles; the website native
manifest and actual provider, inventory/history and service qualification remain open.

The earlier [hookless-pool evidence](../reports/hookless-pool/VERIFICATION.md)
describes the WETH checkpoint only. Use the separate
[native architecture](NATIVE_ETH_ARCHITECTURE.md) and native-port verification for
the new candidate. Actual native target-chain forks, typed v4 conversion support,
routes, feeds, services, operating rehearsals and independent audit remain open.
No public signing, transaction, deployment, service control or existing Anvil-state
change is implied by this candidate.
