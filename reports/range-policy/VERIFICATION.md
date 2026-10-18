# Range-policy verification - 2026-10-18

**Release remains NOT APPROVED.** No deployment or public transaction was made.
The [review](REVIEW.md) and [design](../../docs/RANGE_POLICY_UPDATES.md) describe
the change and accepted boundaries.

| Evidence | Result and scope |
| --- | --- |
| [Focused Solidity](solidity-verification.json) | 37 passes, zero failures/skips: new RangePolicy, existing DynamicRange and NativeLiquidity suites. Real sealed timelock; narrowing/widening, cooldown boundary, stale feeds, disabled/inactive states, recorded-center drift, rounding, current LP identity and a 1,000-run width fuzz case. The policy fixture observes controlled LP records; it does not pretend to settle Uniswap. |
| [Selected native/Pons fork](selected-fork.json) | One new complete range-update lifecycle passed at pinned block 88,544,093. Actual venue/wrapper/hook and real Strategy trigger; synthetic USD feeds and mock VRF/governance. Failed mint rolls back, success changes physical LP but preserves both NFTs' shares and positive LP/royalty claims; replay is ineligible after cooldown. |
| [Backend/keeper checks](python-verification.json) | 38 passes, zero failures/skips, on isolated tracked HEAD plus intended API/tests only. Full activation/approval paths, range/price causes, cooldown consistency and malformed input; three focused existing keeper dispatch/pause/parking cases. No running keeper was changed. [Log](python-tests.log). |
| [Normal size/source gates](size-gates.json) | 30 module/helper objects pass, 39 current production sources bound to compiler metadata. Vault runtime 24,557 bytes (19 free), Migration 24,518 (58 free), Strategy 12,186. Constructor arguments require deployment allowance. |
| [ABI check](abi-check.json) | The new pinned Strategy getter is exactly `rangeUpdatePending(uint256) -> bool`, view, in the current compiled artifact. |
| [Fresh static analysis](static-execution.json) | Slither 0.11.6 completed from the current typed normal-build AST without another compilation. [Internal review](static-review-summary.json): 376 entries, 155 false positives / 75 accepted risks / 146 informational; unchanged matcher covers every finding and rejects four corrupt review mutations. Not an independent audit. |

Only `src/ZZZStrategy.sol` changed among production Solidity sources; see
[exact scope comparison](scope.json). Existing target arithmetic is factored
without changing its math. New on-chain state, force authority and Vault calls
are absent. The preceding dynamic-liquidity budget/accounting evidence retains
its original scope for unchanged logic. Broad unchanged suites were not rerun;
no full current-source regression is claimed.

Fork gas includes test setup and multiple operations, not just a rebalance.
Its exact positive claim receipts are preserved in the result. The runner used
the existing unpublished process-runner draft, bound by hash and excluded from
this publication. Real venue execution under synthetic feeds does not qualify
production oracle/VRF/governance services, actual routes, gas budgets, strategy
profitability, creator terms or provider availability. Exact-commit Ubuntu CI,
live rehearsals and independent audit remain separate release requirements.

Raw compiler artifacts and logs are retained outside Git under
`range-policy-20261018`; linked receipts include exact source/artifact hashes.
No website/server update or paused-monitor restart is included.

[Failed/interrupted attempts](fork-attempts.json) are retained, not merged into
the passing result. The first fork failed because the test harness could not
receive native royalties. A short subsequent attempt was stopped to keep buyer
impersonation active across the royalty getter and claim. Only the fixture
changed; production code and economic assertions were not weakened. Final
claims go to the new owner wallet and both receipt amounts are explicitly
positive. Unchanged focused suites were not rerun for that fixture correction.
