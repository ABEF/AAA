# Selected hookless pool: scoped verification

2026-10-24. Contracts undeployed; production **NOT APPROVED**. This record covers
the selected-pool development candidate, not a native-ledger redesign.

## Implemented

Selected Robinhood v4 native ETH/ZZZ `0x5011...afe1b`; zero hook, static LP fee10020,
spacing200. Native admission checks initialized actual slot state, pinned dependency
code/wiring, reviewed wrapper policy and existing price/asset/strategy bounds.
Governance can admit supported later native fee tiers or hookless WETH destinations.

`moveFunds` atomically moves the shared LP within its ordered accounting pair,
preserving shares and funded liabilities under one fixed 3% aggregate budget.
`movePool` remains an alias. External custody `exit` remains separately approved
and globally paused: normal all-ZZZ or explicit no-swap raw exit. Native balancing
now compensates for actual directional protocol and static LP fees.

## Local checks and source scope

These are scoped Forge VM fixtures, not live-funds transactions. Counts overlap
between runs and inherited suites; they must not be added as distinct test coverage.

| Run | Result | Source scope |
| --- | --- | --- |
| [Initial corrected scope](runs/test-fixed.log), [bindings](runs/test-fixed.json) | **106 passed**, zero failures/skips | Native settlement, pool switching, custody, royalties, parking, wrapper policy and contribution/operator controls. This precedes the later Vault/Budget exit-minimum fix; native coverage was then 23 cases. Its custody fuzz used 1,000 runs. |
| [Expanded native scope](runs/test-native-final.log), [bindings](runs/test-native-final.json) | **24 passed**, zero failures/skips | Adds directional protocol-fee and mismatched LP-fee checks. This also precedes the Vault/Budget exit-minimum fix; it is not a final-source rerun of the 106 cases. |
| [Exit-floor scope](runs/test-exit-floor-final.log), [bindings](runs/test-exit-floor-final.json) | **53 passed, two failed**, zero skips | Uses the final production sources. The two custody fixtures still expected swaps looser than their own 1% per-leg setting; other migration/budget/pool-switching cases passed. Rebalance-boundary fuzz used 1,000 runs. |
| [Corrected custody scope](runs/test-custody-floor-final.log), [bindings](runs/test-custody-floor-final.json) | **24 passed**, zero failures/skips | Final custody fixtures and production-source hashes match the checkpoint. Exit fuzz reports 1,001 runs, including the retained counterexample. This supersedes the two fixture failures, not the earlier reports' complete source scope. |

The exit-floor fix tightens the swap's requested minimum to the greater of the
remaining whole-exit minimum and the pool's oracle-based per-leg minimum. The
3% aggregate exit floor and existing per-leg slippage check both remain enforced.
The custody fixture's end-to-end swap loss was reduced to its configured 1%, and
its fuzz expectation now rejects losses above that per-leg bound.

**33 compiled runtime/initcode object gates pass** under unchanged compiler and
normal EIP-170/EIP-3860 limits. Retained artifact source/dependency Keccak bindings
were checked against checkpoint sources. Vault runtime **24,019**, initcode
**44,885** bytes; Migration runtime **23,810**; MigrationBudget **19,072**;
Registry **11,467**; Strategy **13,080**. Vault runtime headroom is 557 bytes.
Constructor arguments/live immutable hashes are not included.

[Nine affected Python inventory/template checks](runs/python-checks.json) passed
in observed unittest output. The retained JSON lists their scope; a separate raw
Python stdout log was not retained. A separate [nine-check publication snapshot](runs/publication-python.json)
with [raw output](runs/publication-python.log) verifies the intended HEAD-based
fork runner and only the three inventory expectation edits, excluding unrelated
local runner/test drafts. It does not add new Solidity coverage. The example remains explicitly blocked and
authorizes no deployment. Todo/source checks are textual consistency checks, not
a security audit.

Raw Solidity commands/logs and exact SHA-256 source bindings are retained in `runs/`.
[Object gates](size-gates.json). The current native fork source contains29 cases;
the unchanged historical alternative-pool fork has9. Inventory expectations total38,
which is a coverage requirement, not a statement those38 have passed this revision.

Diagnostics: the initial local attempt had77 passes/four failures: two wrapper
governance fixtures and one contribution fixture still bound retired v3 module IDs;
one planner assertion exposed the missing hookless native-fee compensation. Fixture
bindings were corrected without loosening authority; strategy logic was fixed.
The subsequent106-case run passed. Prior reports retain their original source scope.

## Read-only selected-pool evidence

[Public chain observation](observed-pool.json), block96,427,989/hash pinned, verifies
creation key/hash, six dependency runtimes, wiring, active liquidity units and fees.
Observed protocol fee1000 pips per direction; combined charge approximately1.101%.
No independent USD pricing, token audit, volume forecast or release approval.

## Fork execution

The focused campaign used actual pinned Robinhood core/periphery/token code and
state in an isolated Forge fork, with synthetic USD feeds, test authorities, VRF
and funded test accounts. It sent no public transaction. Gas totals include test
setup/deployments and are not production transaction-cost estimates.

| Run | Result | Interpretation |
| --- | --- | --- |
| [First RPC](runs/fork-1792810137.log), [bindings](runs/fork-1792810137.json) | Setup failed; no functional case passed | The provider rejected historical account state. |
| [Archive transport attempt](runs/fork-1792810429.log), [bindings](runs/fork-1792810429.json) | Setup failed; no functional case passed | The relay surfaced an archive response-envelope transport error. |
| [Ten-case scope](runs/fork-1792810644.log), [bindings](runs/fork-1792810644.json) | **Eight passed, two failed**, zero skips | Accounting/key identity; native/ZZZ activation and top-ups; mint/increase/close; raw exit without source feed/enabled pool; admission rejection; actual conventional LP-fee accrual passed. Normal exit and destination movement failed with slippage checks. |
| [Corrected two-case rerun](runs/fork-1792811540.log), [bindings](runs/fork-1792811540.json) | **Two passed**, zero failures/skips | Normal exit to an EOA as ZZZ, and native-to-WETH-to-new-native-fee-tier movement passed after the production minimum fix and destination fixture correction. |

The normal-exit failure exposed a real integration bug: its remaining 3% aggregate
minimum could be looser than the manager's per-swap 2% minimum. Passing the stricter
minimum fixes the request rather than weakening either guard. The movement failure
was an empty destination fixture: its balancing swap had no liquidity. The corrected
fixture first creates real destination LP using the harness's own 0.1 ETH and 20,000
ZZZ on the isolated fork, before constructing the collection. This is not collection
backing or evidence that a future public destination has sufficient liquidity.

The eight earlier passes were deliberately not repeated. Their bindings precede
the Vault/Budget exit-minimum change. The two-case rerun matches the checkpoint's
production sources; only the later local custody fixture differs. This is **not
a fresh final-source ten-case or full regression pass**. The 29-case native and
nine-case alternative-pool inventory is larger than this executed focused scope.

## Boundaries

No public contract transaction/deployment, key use, website/server code deployment,
existing8902/Anvil/NFT/LP/balance/journal modification or monitoring restart.
Signer stays Anvil-only and public DEPLOYMENT remains null.

Internal WETH remains. Raw exit currently sends WETH/ZZZ and still depends on the
wrapper. The user has requested native ETH accounting for robustness/efficiency;
[the native architecture specification](../../docs/NATIVE_ETH_ARCHITECTURE.md) is
prepared, but the port and wrapper-independent recovery are not implemented. This
evidence verifies the existing WETH-accounting checkpoint, not the proposed port.

The user reconfirmed **1% maximum ZZZ LP-fee conversion loss**, gas separate, and
requires a cheaper independently qualified route. The observed selected pool's
approximately 1.101% swap fee alone does not qualify a full ZZZ-to-ETH conversion at
reference prices. No cheaper route is established here and no cap was increased.
Real routes/feeds, conversion/gas economics, operating rehearsals, updated release
inventory and independent audit remain open. Publication is a separate Git record;
these local results do not establish a published CI pass or production approval.

[Internal review](REVIEW.md) | [Pool decision](../../docs/POOL_SELECTION.md) |
[Operator procedure](../../docs/GOVERNED_CUSTODY_HANDOFF.md).
