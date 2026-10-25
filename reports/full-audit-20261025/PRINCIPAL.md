# Principal, valuation and execution review

This is the principal/execution slice of the current internal full-project
review, not an independent audit or a claim that all dependencies are safe.
The reviewed committed baseline is `e32e966`, whose production Solidity remains
the reference35007db source. Existing Anvil deployments, profiles, balances,
journals, public signing and operating services were not changed. No public
RPC, deployment, financial transaction or unchanged broad test suite was used.

## Reviewed financial paths

| Boundary | Actual trace and protection reviewed | Remaining assumption / result |
| --- | --- | --- |
| Original contribution | Entry accepts only native ETH/fixed ZZZ and freezes source/pair USD bounds and caller maximum before pulls/conversion. The active context binds current owner, NFT/pool/amounts and exact Vault calldata. | Reviewed route/feed/runtime policy is still necessary. No user-supplied USD or arbitrary recipient/call executor was found. |
| Exact assets and refunds | ExactToken checks sender and recipient deltas; Entry/route executor/Manager preserve original prefunds and reset exact allowances. Native receive windows admit only expected child/Core/module credits. | Conventional nonrebasing, exact-transfer tokens and actual runtime/proxy review remain required. A malicious token can lie or halt; exact balance checks cannot prove future behavior. |
| Physical LP | Manager checks actual Vault owner, full PoolKey, ticks and liquidity delta after callbacks/refunds, plus unchanged deployment spot. Native settlement pays only rounded-up debt, avoiding PositionManager prefund sweep. | Installed Core/PosM tests are not the deployed Robinhood market. Real pins, depth, fee directions and gas remain qualification gates. |
| Share issuance | Vault settles funded collective dust, harvests existing LP and releases incumbent compound before entry. It revalues existing LP after balancing, excludes pre-existing idle/compound from marginal deployed-LP credit, checkpoints old owner shares, then issues floor-rounded shares at incumbent NAV. | Existing fractions/reserves remain separately backed. No path was identified for donations or earlier rewards to buy entrant shares. Full economic fuzz/release review remains separate. |
| Frozen valuation | ContributionPricing requires fixed source/pair marks, exact observation fingerprints, decimals, captured governed limits and unchanged final spot. Finish and Entry end checks bracket final approval resets/owner checks. | Independent feeds are a reviewed real-world assertion, not proved by two addresses. Pool spot alone is not a USD fallback. |
| Maintenance | Budget snapshots starting prices/attributed principal and includes only released compound. Rebalance/move/compound are module/keeper gated and nonreentrant; final deployed+idle value must meet captured aggregate cap, with at most5% idle. | Per-operation limits do not cap market loss, future repeated turnover, gas or MEV. User selected per-operation controls only. |
| Ranges | Actual Strategy uses deliberate tick-spacing floor/outward upper rounding, explicit orientation, price/spot checks and reviewed keeper-only two-width rule. Range changes alone do not alter physical ticks; ordinary guarded rebalance does. | Displacement policy is not an inferred volatility estimator. Threshold/turnover economics still require real review. |
| Pool moves and raw recovery | Registry retains one contribution pool, fixed-ZZZ pair admission and pinned native venue identity. Same-pair moves retain shares and atomic floor checks. Raw exit/parking intentionally omit source prices but retain exact raw/custody approvals. | Source cannot force an external custodian to return funds. Different actual pairs/ETH-WETH conversion are not silently supported as atomic moves. |
| Callback/lifecycle boundary | Every ordinary Vault financial entry owns the same nonReentrant guard. Manager/Core callbacks require one-shot hashes and fixed sender; canonicalWrite is fixed-companion/import-state only. | Read-only intermediate views are not a permission to mutate custody and must not be used as independent cross-protocol collateral proofs during callbacks. Confirmed API reads operate after transaction completion. |

Files traced include ActivationEntry/Assets, PoolRegistry, Vault/VaultCanonical,
MigrationBudget, ContributionPricing, Oracle/PriceMath, Strategy, LiquidityManager,
V4RouteExecutor, V3VenueValidation, ExactToken/ExactAsset and Compounder, with
relevant fixed Handoff and Membership caller guards. The actual pinned v4
settlement/position APIs, OpenZeppelin balance/math/allowance/reentrancy semantics
and current tests were followed where those calls determine the financial path.

No new unprivileged principal-theft or share-issuance bypass was confirmed in
this slice. This is bounded source analysis, not proof of exploit absence.
Direct governance/dependency admission, external custody, source independence,
liquidity depth and operator gas availability remain explicit trust boundaries.

## Feed agreement is not execution feasibility

The3% feed agreement band and2% default contribution budget do different jobs.
For a source priced100 by the lower feed and103 by the upper feed, even a
zero-cost deployment valued100 cannot satisfy the2% upper-source floor100.94.
The spread alone consumes3/103, approximately2.913%, of the conservative budget.
Venue fees and slippage add to it. Consensus may therefore be healthy while a
quote is rejected. This is deliberate conservative failure, not a reason to
replace bounds, auto-widen policy or promise every $100 input always executes.
Actual source agreement/liquidity must support the selected reviewed budget;
the quote/review must expose unavailable operations and gas separately.

## New optional-currency gas probe

The possible failure hypothesis was that16optional250k isolated royalty reads,
combined with4buckets and33populated LP reward assets, would exceed the unchanged
12M activation review. The initial exploratory test expected rejection. Actual
execution **succeeded under12M**, so that diagnostic assertion failed. The
original source, failure and successful underlying operation are retained;
the hypothesis was not converted into a production bug or used to relax a cap.

The corrected single test requires actual success under the same12M forwarded
call budget. **One selected method passes**, with measured activation CALL
execution **9,591,082gas**. The full test consumes14,347,040because it includes
later16currency recovery/syncs and assertions; that full-test number is not the
activation cost and is not compared with the12M review.

The test verifies exact user contribution debits, positive entrant shares,
unchanged aggregate prior-share total, new collective membership, native royalty
enrollment and all16optional currencies deferred. After each fault recovers,
the incumbent retains1600/4earlier raw royalty units and the entrant receives
none; all33LP asset checks exclude historical entrant rewards. Failed currency
reads skip the otherwise expensive healthy checkpoint/enrollment work, so their
isolated cap cannot simply be added to an old healthy benchmark.

Only `test/CombinedCapacityGas.t.sol` changes: a test-only token can exhaust gas
only when RoyaltyRewards queries it. The existing fixture constructs its original
MockToken unless this new scenario opts in; previous measured test methods and
the old healthy runtime behavior remain unchanged. The fixture still uses mocked
venue/access/prices/VRF and therefore does **not** qualify actual v4/Core/native
Entry cost or global worst-case gas. No production contract, gas cap, loss guard
or financial policy changed.

The new run uses existing `_cool`, which cools all its named modules, feeds,
tokens, ledger and caller accounts. Pinned forge-std Vm documentation states
`cool(address)` marks both address and slots cold, including the just-toggled
fault flags. This is the fixture's documented cold context, not proof that every
possible real provider/market state is cold-maximal. A gas-burning view cannot
persist an execution counter;16deferred-currency assertions and the recorded
fault-token body establish the exercised branch.

The closed265-input AST was refreshed with only that test changed, then the
one selected final method executed. Earlier broad suites were not repeated.
Normal37object/75input evidence is reused after matching every production,
dependency and build hash. See [machine evidence](principal-gas-verification.json).

## Fresh static-analysis slice

[Per-finding review](static-principal-review.json) covers all143assigned fresh
Slither fingerprints, with exact function/callback reasoning:92false positives
and51accepted finite-loop/dependency-availability risks. No diagnostic is removed
because of detector name or severity alone. The bounded-loop findings retain
actual worst-state/feed/market gas qualification; they are not proof that all
permitted operations always fit12M.

Important examples: saved pre-balances in Manager/Entry are deliberate baselines
followed by fresh exact deltas; native callback entry is hash-authenticated and
one-shot; private Vault writes occur under guarded public callers; canonical
restore is fixed-Handoff/lifecycle gated under Handoff's mutex and exact return
delta; default-zero locals represent one-sided LP/native-zero cases; validation
methods intentionally revert rather than consume returned values; tick division
is intentional floor-to-spacing arithmetic. All concrete call stacks and source
limitations remain in the row-specific review.
