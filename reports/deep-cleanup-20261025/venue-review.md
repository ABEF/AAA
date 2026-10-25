# Venue, pricing and strategy review

Baseline: `964e6b6`, with `ea2a70c` implementation scope. This review reads the
current source and installed dependencies; it is not an independent audit or
qualification of actual feeds/routes, deployed code or operations. No public
RPC, transaction, deployment, running service or existing Anvil state was used.

## Architecture and invariants followed

- Vault is the manager's LP-NFT owner/caller. Collection NFTs hold independent
  shares of shared buckets; replacing a physical position must not replace the
  collection NFT or its accrued rewards.
- Typed PosM calls use exact installed action values and tuples. Mint/increase
  settle principal debt; collect uses zero decrease; close burns the physical
  NFT. Recipient/payer/authentication and native/ERC20 prefunds remain explicit.
- Core unlock callbacks must match an armed hash/manager and close all deltas.
  Exact source settlement and actual output balances, not router labels, prove
  swaps. Native zero is never silently mapped to WETH.
- Original-source upper/lower dual prices and captured loss/caller bounds remain
  frozen through callbacks. Only genuinely added LP buys shares. Old fees,
  compound and idle remain attributed to incumbents.
- Directional fee planning matches the installed protocol fee low/high12 bits
  and `pf + lp - floor(pf * lp / 1e6)` formula. Inverse range direction, outward
  ticks, cooldown and approved widths are separate from actual execution.

## Findings and assigned changes

### VENUE-01: obsolete active native test class

`test/NativeLiquidity.t.sol` originally exposed `nativeAsset` in its
`BoundaryPools` helper, substituted WETH in accounting, lacked `isNativePool`,
omitted required native call value and asserted wrapped returns. Current
`ZZZLiquidityManager._config` calls `isNativePool`; `_mintOrIncrease` and `swap`
require exact native value. Those positive tests therefore could not exercise
current native behavior. This is a test/verification defect, not evidence of a
production fund-theft exploit. No original runtime failure is claimed without
execution: the mismatch was established by tracing the calls and required ABI.

Root authorized replacing the obsolete class with actual installed v4 Core,
PositionManager and StateView execution. The prepared20 methods test ETH
funding/refunds, actual donation fees, collect/burn, both swap directions,
prefunds, approval resets, failure rollback, operation stops and native credit
callbacks. Prices, authorization, Registry admission and the used Permit2
allowance subset remain explicit substitutes. Real Permit2 pins solc0.8.17 and
is not instantiated by these solc0.8.26 tests.

All24 former methods map to current semantics or explicitly retained fault tests
in `native-liquidity-deprecation-map.json`. Six imported hostile helper contract
bodies are byte-identical; only the unused old BoundaryPools/class are replaced.
Exact old source is retained in `native-liquidity-before.sol.txt`. Broken unused
wrappers must no longer block native custody, so those old expected reverts are
retired rather than relabeled as passes. No production guard is weakened.

### VENUE-02: repeated error declaration

`src/libraries/ZZZV3VenueValidation.sol` duplicated the existing module error
`InvalidConfiguration()`. Its view extraction introduced identical duplicate ABI
entries in Entry and both concrete converters. Root authorized reusing
`ZZZModule.InvalidConfiguration()` directly. This changes declaration provenance,
not selector, read order, venue policy or fund authority. The preimage is
`v3-validation-before.sol.txt`; final root ABI/storage/bytecode gates must verify
the expected removal of duplicate metadata entries.

### VENUE-03: native increase requires separate harvest

Installed `PositionManager._increase` includes earned fees in net debt.
`ZZZLiquidityManager._nativeDebt` deliberately funds exact gross principal and
checks that no ETH remains in PosM. Therefore increasing with pending fees must
revert rather than leave unconsumed ETH or silently mix fees into principal.
Current `Vault._join` and `_redeploy` both harvest immediately before `_put`.
The prepared actual fixture checks rejection before harvest and success after
collecting. Retain these boundaries; merging them would risk economic behavior.

## Dependency scope

Installed/locked versions are OpenZeppelin5.4.0, Uniswap core1.0.2 and
periphery1.0.3. Read PoolManager unlock/modify/swap/sync/settle/take, PositionManager
lock/authorization/action decoding/principal-fee checks/settlement, Permit2's
used allowance path, position/tick/liquidity math, SafeERC20 forceApprove and
ReentrancyGuard.16 relevant file hashes are recorded in `venue-review.json`;
15 match the earlier local dependency binding record and none differ. One was
not in that earlier record. This is not a pristine tarball/full dependency-tree
comparison or proof that deployed Robinhood bytecode equals these local files.
No dependency upgrade, compiler change, hook or upgradeability is proposed.

## Verification boundary and remaining risks

Source tracing, dependency/hash checks and static helper/replacement-reference
comparisons are now supplemented by [32 affected Solidity passes](solidity/SELECTED_VERIFICATION.md),
including all 20 replacement native methods against installed Core/PosM. There
were no retries, missing methods or inherited extras. All 265 AST input bindings,
including 134 installed dependencies, matched before and after execution. Root's
separate normal 37-object build and complete 265-input ABI/AST typecheck passed;
their receipts keep their own compilation scope. This does not claim a full
regression or an actual deployed-market qualification.

No additional unprivileged theft/callback/allowance bypass was confirmed in the
reviewed paths. This does not prove absence. Existing independent-feed/proxy and
common-mode risk, qualified routes/VRF/authorities/OpenSea, strategy/gas and
operating rehearsals and independent audit remain open. Immediate governance,
trusted external custody and per-operation-only loss limits are unchanged.
Historical fork/Pons/wrapped evidence retains its own source scope. The current
selected market still requires current native qualification, not old fixture
labels or mock success.
