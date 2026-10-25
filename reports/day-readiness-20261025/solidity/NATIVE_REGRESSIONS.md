# Native assertion sensitivity verification

**Both affected methods passed** in one isolated normal-profile Forge run:

- `testNativeExactInputGuardRejectsPartialFillEvenWhenOutputPassesOracleFloor`:
  an intentionally reverted real-Core observation proves a genuine partial input
  whose output satisfies the independent oracle floor. The actual Manager then
  rejects with exactly `Slippage()` and preserves caller/Core/Manager/PosM cash,
  LP ownership/liquidity, pool price and accrued protocol fees.
- `testNativeAmountsStayUint128BoundedWithoutPermitApproval`: oversized amount0
  and amount1 each supply the correct native value, require `InvalidAmount()`,
  and cannot reach a poisoned later pool read. Caller cash, next LP ID and active
  token/Permit2 approvals remain unchanged. The previous missing-value/any-revert
  test could not independently distinguish this bound from a later value check.

The exact selection, source/body hashes, outcomes and raw artifact hashes are in
[the verification receipt](native-regressions-verification.json), using
[this wrapper](run-native-regressions.py) and the unchanged hash-pinned AST driver.
Execution took 78.828 seconds including compilation, with no failed, skipped,
missing or unexpected cases and no EVM retry. Before and after execution, all
265 AST inputs matched: 131 project inputs and 134 installed dependency inputs.
All 75 inputs of the earlier normal production build also remained unchanged.

The initial typecheck found a test-only `fail(string)` call incompatible with
the pinned forge-std `fail()` signature. Its exact preimage and failure are
retained; removing the argument repaired compilation without changing a
production guard or weakening an assertion.

The [assertion matrix](../native-assertion-matrix.md) independently reviews all
24 archived methods and their 73 direct expectation/helper calls, or 77 when
the two approval-helper calls are expanded. The [reuse record](../native-reuse-bindings.json)
shows that all production/dependency inputs, the other 19 earlier native methods,
all 44 previously retained non-test function bodies in that file, and six shared
helper contracts remain byte-identical. Their earlier execution
results retain their original scope; they were not rerun. Across the earlier
32-method run and this two-case run there are 33 distinct method names, with the
strengthened bound method repeated, not 34 distinct new behaviors.

The real venue objects are installed Uniswap Core/PosM/StateView. Authority,
admission, USD prices and the used Permit2 allowance path retain explicit local
seams. No external source-mutant campaign or deployed-market qualification is
claimed. These checks are neither a fresh full regression nor independent audit.
No production source, economic/custody rule, loss cap, public signer, existing
Anvil/NFT/LP/balance state, journal, service or website was changed.
