# Current financial execution fixtures — reachability and real guard checks

This work repairs test infrastructure so current financial paths reach their intended assertions. It changes **no production source, economic right, safeguard, default, deployed chain or service**. The earlier reservation restriction and its final normal/static build retain their separate source stage.

## What was wrong

Several mock venues predated the current transaction-bound pricing path. They lacked `executionStrategy()` or the fixed-ZZZ reader, so real Oracle/ContributionPricing calls reverted before the behavior advertised by a test. Generic negative expectations could hide that distinction. The portfolio accounting oracle also supplied old constant-price methods but no actual captured execution context. Its capability test started multiple maintenance scopes without finishing the previous one. The old mixed-decimal scale harness used two ERC20 assets even though current principal is native ETH plus fixed ZZZ.

A separate confirmed modeling bug affected native rollback. `BudgetAdversarialVenue` burned native value with `vm.deal` inside `close`; that cheatcode reduction survived a failed outer operation. The retry then ran out of funds even though normal contract state rolled back. Shared `VaultLiquidityMock` similarly created native balances inside swaps/collection. These were fixture defects, not a reproduced production loss or permission bypass.

## Corrections

- **One typed execution adapter.** `AccountingExecutionFixture` preserves the declared deterministic target/price policy. It forwards fixed-token identity, maintenance NAV, loss/idle limits, utilization, readiness and rebalance checks to actual production `ZZZLPBalanceMath`. A dynamic bound-policy option handles fixtures constructed before strategy binding; it does not invent a successful answer for missing configuration.
- **All affected construction paths are wired.** Adversarial budget venue consumers in MigrationBudgetAdversarial, RebalanceBudget, GovernedExecutionLoss, ContributionThreePercent and KeeperCompletion share this path. HolderExit and CanonicalNative fixtures bind it too; canonical preparation retains its separately declared context.
- **Real oracle capture for numeric fixtures.** PortfolioAccounting now uses actual Oracle and controlled admitted feeds/fixed native pair. The scale harness uses native ETH plus one fixed six-decimal test ZZZ to preserve the useful mixed-decimal subject. It tests exact3% retention, one base unit below and a separately authenticated live-round change. This six-decimal fixture is not the actual production token or feed qualification.
- **Valid maintenance lifecycles.** Sequential replacement/compound/emergency capability checks finish each prior scope; deliberate clock advances refresh controlled test feeds. They do not weaken source-age checks.
- **Reversible native modeling.** Modeled losses use ordinary transfers to a fixed test sink. Native exchange, fee and repricing cash is provided during explicit fixture setup/configuration. Protocol operations use ordinary sends; they contain no balance cheatcodes. A failed-mint rollback case now asserts exact native backing and token supply as well as position/reward/reserve state.
- **Remove a masking workaround.** Metadata exit tests no longer override the venue's execution reader with a separate fixed-only shim. The nonzero tokenURI/exit/transfer/payout case exercises the shared current context.

## Evidence and boundaries

The finite selection comprises18 distinct methods across budget loss, exact terminal payouts/raw floors, one/two-leg utilization, native canonical commit/abort, SeaDrop full handoff, metadata after paid exit, mixed decimals and rollback. Failed diagnostics, compile-only error-namespace correction and empty-selection handoff attempts stay explicit and add no passing methods. Exact results and source stages are recorded separately.

These fixtures retain controlled authority/admission, tokens, prices, deterministic geometry/venue and VRF. Real pricing/accounting/math bodies are exercised, but this is not actual market depth, provider liveness, private routing, OpenSea hosting, complete transaction fee/gas or independent security approval. The whole gas/fork/fuzz/invariant suites and unrelated tests were not rerun. Earlier passes are not relabelled after later test-only source edits; the import-closure/source-stage records identify what each result actually checked.

## Final finite result

**18 distinct selected methods pass: one new and17 adapted/affected.** The [exact method/stage record](CURRENT_EXECUTION_RESULT.json) separates current source stages, two unchanged Scale boundary passes reused at their original stage, earlier valid handoff closure proofs, failures and zero selections. No full fuzz/invariant/fork/gas suite was run. The final Budget retry and shared MockVenue rollback cases both prove ordinary native transfers restore real backing on failure; the final Scale method proves changed healthy live pricing cannot replace the captured vector.

Source-only consumer wiring is not counted as a passing test. The extra synthetic context changes do not qualify market pricing, routing, host operation, OpenSea service behavior or production gas. Production source remained byte-identical throughout this execution-fixture task.
