# NFT economic rights: verification

2026-10-16. The final offline Solidity run passed **531 tests, with zero failures
and two expected opt-in fork-setup skips**: 533 cases across 43 suites. Source
hashes were unchanged during execution and all suite/compiler bindings passed.
This is internal verification of the undeployed four-bucket candidate, not an
independent audit or production approval. No public transaction was sent.

## Results and exact scope

| Check | Result | Evidence and boundary |
|---|---|---|
| Final full offline Solidity | 531 passed / 0 failed / 2 expected skips; 43 suites | [Run receipt](solidity-run-summary.json), [log](solidity-tests.log). Both fork suites deliberately skip setup without their opt-in RPC configuration; their live cases were not executed in this run. |
| Ownership unit regressions | 7 passed / 0 failed / 0 skipped | [Ownership receipt](ownership/verification.json), [final log](ownership/unit-final.log). Includes the corrected independent operator identity. These cases are also in the full run. |
| Extended dual-ledger invariant | 256 runs x 256 depth = 65,536 handler calls, 0 reverts; seed `0x456ba2` | [Audit-profile log](ownership/invariant-audit.log). `fail_on_revert = true`; one invariant and one deterministic sequence passed. Separate from the full run's default 32 x 128 invariant profile. |
| Buyback execution | 22 passed / 0 failed / 0 skipped; 1,000 fuzz runs | [Receipt](buyback/verification-summary.json), [results](buyback/attempt2.json). Real Buyback/Fees/Rewards/Oracle/Registry/Strategy/LiquidityManager, with explicit synthetic share ledger, tokens, authority, VRF and settlement core. Also included in the full run. |
| Scale and corrected gas fixtures | 14 passed / 0 failed / 0 skipped across four suites | [Receipt](scale/cold-order-final-receipt.json), [log](scale/cold-order-final.log), [artifact bindings](scale/cold-order-compiler-binding.json). Includes CollectionScale, CombinedCapacityGas, BucketCapacity and ProductionGas. These cases are also in the full run. |
| Normal production build/size gates | 23 objects passed; all 29 production sources bound | [Size receipt](production-size-gates.json), [successful normal build](production-build-verified.log). Unchanged 24,576-byte runtime and 49,152-byte initcode limits. Constructor arguments still require deployment-time allowance. |
| Current portable Python workspace | 628 passed; 0 failures/errors/runtime skips; 633-case inventory, 5 explicit Unix exclusions | [Receipt](python-tests.json), [log](python-tests.log). This covers the broader local working tree, including unrelated unpublished service work. It is **not** an exact-publication-commit or fresh Ubuntu result. |

The targeted counts overlap the full-suite count; they must not be added to it.
No line/branch coverage percentage or formal verification result is claimed.
The Solidity toolchain is Foundry v1.4.4, solc 0.8.26, Cancun, via-IR, optimizer
runs 1 and Yul optimization disabled. Compiler, tool and source identities are
recorded in the linked receipts. Project source bytes match the executed
artifacts; any vendored Windows line-ending normalization is recorded separately.

## Integrated collection and stateful assertions

`CollectionScaleTest` activates all 1,000 NFTs using ten contribution sizes and
991 initial owners, including a wallet with multiple NFTs. It verifies exact
600/300/100 rarity quotas, canonical hashed IDs/ordinals, immutable traits,
1,500 total royalty weight and one shared physical LP. Creator-inbox funding and
conventional harvest are separate, explicitly funded fixture paths.

Every NFT claims two LP assets and three royalty assets (overlapping LP/royalty
token, 6-decimal ERC20 and native currency), using direct calls or the mixed
router. Repeated claims pay zero. Funded transfers preserve rights and reject
former-owner claims. Shared compounding and rebalance retain NFT shares while
replacing the physical LP; direct ZZZ burn verifies actual supply reduction.
Per-asset equalities reconcile principal, paid rewards, compound/buyback reserves,
remaining balances and quarantined royalty prefunds without double-counting
liabilities and their backing.

The extended invariant deliberately uses eight NFTs and bounded operations to
explore receipt timing, activation, top-ups, LP/royalty/mixed claims, transfers,
pause and shared maintenance. It checks custody, shares, membership, rarity
weights, funding and quarantine after operation sequences. This is distinct from
the full-population scenario; neither is a real-market or bridge rehearsal.

## Execution gas and capacity

These are cold-access `gasleft` deltas for individual operations, excluding
fixture/loop setup, transaction intrinsic/calldata overhead and refunds. Mock
venue costs do not qualify actual Uniswap/Pons or ActivationEntry execution.
The 1,000-NFT scenario's aggregate test gas is deliberately paused and must not
be quoted as the cost of minting, activating or claiming 1,000 NFTs.

| CollectionScale operation | 1 NFT | 1,000 NFTs |
|---|---:|---:|
| Activation | 1,953,769 | 1,780,853 |
| Single-asset LP claim | 176,661 | 176,793 |
| Five-operation mixed claim | 804,409 | 806,534 |
| Shared compounding | 732,545 | 732,811 |
| Shared rebalance | 920,217 | 920,483 |

All operations pass the unchanged 12M local ceiling and the fixed 100,000-gas
population-growth allowance. A real 32-operation mixed router claim over 16 NFTs
at full collection supply uses **4,333,653 gas**. The older ProductionGas
32-asset loop is explicitly labelled repeated raw calls, not a router benchmark.

The combined four-bucket fixture also admits 32 LP reward assets, funds four
creator inboxes and all 17 royalty slots, and checks exclusion of historical
funding from the entrant. Its fully populated index workload measures
**9,612,107 activation / 7,596,173 top-up gas**. The simpler four-funded-bucket
entry is 3,507,294. The earlier combined 16-bucket workload exceeded 12M
(23,937,082 activation / 21,141,345 top-up); those historical numbers retain their
original scope. One thousand NFTs can share the initial bucket. These results
do not justify restoring the old 16-bucket cap or prove migration reservation
liveness.

Normal object sizes include Vault **24,056 / 24,809** runtime/initcode bytes,
Migration **24,252 / 24,764**, and NFT **18,895 / 46,294**. Runtime headroom is only
520 bytes for Vault and 324 for Migration; NFT initcode has 2,858 bytes before
constructor arguments. Test-contract sizes are not production deployment sizes.

## Corrections and retained earlier attempts

- The first ownership fixture accidentally used the same address for operator
  and buyer. It validly tested the first operator rejection/transfer but its
  second transfer was owner-initiated. The final fixture uses `0x0B0B00`, asserts
  actor separation and passes again. The earlier source/log and full-run snapshot
  are preserved; their claims are not silently upgraded.
- CollectionScale, CombinedCapacityGas, BucketCapacity and ProductionGas now cool
  the NFT after calling its helper-address getters. All four suites were rerun;
  the recorded operation deltas remained unchanged in this toolchain. Limits,
  compiler configuration and economic assertions were not relaxed.
- The initial buyback run was rejected by Foundry's removed `testFail*` naming
  convention (`testFailedSwap...`), before the intended test executed. Renaming it
  to `testSwapFailure...` preserved its explicit revert/rollback assertions.
  [The failed attempt remains available](buyback/attempt1.log).
- The first scale gas scenario rebalanced before compounding, consuming the
  reserve that the subsequent compound expected. The fixture now compounds
  before rebalance; production code and assertions were unchanged.
  [The original failure](scale/targeted-attempt1.log) and
  [earlier successful measurement](scale/targeted-final.log) remain separate.
- Native Windows build attempts compiled but exited nonzero when Foundry could
  not access its normal signature cache. Setting `XDG_CACHE_HOME` did not solve
  that platform lookup. The unchanged scoped build completed with approved cache
  access; its exit-zero receipt points to `production-build-verified.log`.
  `production-build.log` and `production-build-final.log` preserve failed attempts;
  their successful compilation alone is not described as a successful command.

## Reused evidence and remaining qualification

[Unchanged-production bindings](unchanged-production-evidence.json) compare the
current production source/configuration with the prior operations-hardening
static review: **220 findings = 130 false positives + 46 accepted risks + 44
informational; zero unresolved detector entries**. This is reused internal
Slither evidence, not a new Slither run, independent audit or absence-of-bugs
proof. The known capacity-reservation issue remains open despite that detector
classification.

The same receipt binds both previously executed fork suites and their compiled
dependency closures: **24 native/Pons + 9 secondary hookless cases passed**, with
zero failures/skips, at pinned block 88,544,093. Those forks were **not rerun in
this review**. Actual venue/wrapper dependencies coexist with mock authorities,
mock VRF and synthetic USD calibration; this does not qualify production feeds,
randomness, creator payments, routes or real transaction costs.

The [review](REVIEW.md), [implementation assessment](IMPLEMENTATION.md),
[coverage matrix](COVERAGE.md) and [release checklist](../../docs/RELEASE_CHECKLIST.md)
retain the outstanding gates: independent audit/remediation, actual services and
authorities, creator terms, full input-to-LP route/gas qualification, wallet and
marketplace rehearsals, sustained operating recovery, and safe destination
capacity before real bridging. No website behavior or local mock pass closes
those gates. Git publication and exact-commit Ubuntu CI must be verified
separately from these local receipts.
