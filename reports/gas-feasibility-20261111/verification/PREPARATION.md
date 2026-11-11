# Gas verification preparation

This record prepares a controlled comparison at source baseline `db509fb`. Initial artifact reuse and trace analysis performed no new compilation, EVM execution or RPC request. The separate fixture-only ABI checks described below generate no executable code. Optimization results belong in a later source-bound record, not this preparation.

## Exact reusable baseline

[ARTIFACT_REUSE.json](ARTIFACT_REUSE.json) verifies all 61 production Git blobs against the original a846 normal source manifest. Its 100-source compiler input/output and 48 runtime/initcode gates retain their original hashes and settings: Solidity 0.8.26, Cancun, via-IR, optimizer one run and Yul optimizer disabled. They are a baseline, not a build of a future optimization.

The immutable `focused-7ab6c5f373` snapshot has the exact baseline `ReferenceExecutionContext.t.sol`, a 196-source compiled closure and 200 watched source files. The extra watched sources are not additional compiled or tested coverage. Pinned native Forge 1.4.4, Anvil and Solidity executables are already available locally. The existing driver creates a fresh copied snapshot, uses two Rayon threads, strips ambient compiler/environment overrides, disables FFI and runs offline. Its focused compile/test timeout is 1,200 seconds; normal standalone compilation uses 240 seconds. No global tool installation is needed.

The four published compressed fixtures preserve exact actual-owner `debug_traceCall` parameters/results, input/bounds, runtime/source pins and expected measurements for ETH/ZZZ activation/growth. Their authenticated exports use complete setup state plus later per-slot deltas, including explicit zero overrides. A new Oracle implementation requires a fresh complete graph/export: **do not replace bytecode in the old state or relabel old fixtures**.

## Comparison rules

Keep input amount, owner/cohort, target geometry, venue count/depth, direction, fees, oracle configuration, cold state and guarded calldata the same. Current diagnostic activation is $1,000 under controlled publications/depth, not the website's exact $100 selection or a qualified real market. Measure any different amount as a separate scenario.

Distinguish three measures:

- Foundry inner-call `gasleft()` deltas, after the same explicit cold-account/slot preparation.
- Actual outer RPC `callTracer.gasUsed`, retaining that tracer's accounting.
- RPC estimates, complete fee policy and the exact executable gas envelope with full 20% frontend headroom. Keeper padding is separately 25%.

The [baseline trace analysis](baseline-actual-rpc-gas-profile.json) reports each method's inclusive and direct-child-subtracted gas without rerunning it. Every outer Entry root is lower than the sum of its direct children, producing negative root-exclusive gas. Preserve that observed discrepancy; do not assume additive gross function costs, infer a qualified refund model, or compare it with Foundry gross gas as a claimed saving. Inclusive costs overlap.

All four old RPC workflows reject at the unchanged 12M default. Higher-policy diagnostics remain explicit. Successful raw execution below 12M would still not establish full estimate/headroom admission. The old positive fixture helper deliberately expects a 12M call to fail, so a candidate optimization may require correcting that **test expectation**, while preserving the old snapshot and every financial/custody/rollback assertion.

## Focused scope after a justified change

[CHANGED_SCOPE_SELECTION.json](CHANGED_SCOPE_SELECTION.json) lists 18 existing gas/adversarial methods directly relevant to a private Oracle execution-context optimization. These cover both asset workflows, incumbent shares, captured/live price separation, unknown asset rejection, scope ownership/borrowing, source revisions/rounds, callback mutations, exact quote/state mismatch and final LP rollback. This is a proposed selection, not executed coverage.

Existing 2.59M/5.96M figures measure the router's balancing helper only. No current a846 **whole normal maintenance** gas acceptance is established by those numbers. A full compound test needs an actual Compounder binding in the real-core fixture, actual harvested reserve/idle funding, full Vault/Budget/Pricing/Manager execution and unchanged shares/reserve backing. A full ordinary rebalance needs the actual cooldown, corroborated sampled trigger and price publications refreshed after the 12-hour warp. The 1–5 minute keeper jitter is a separate service delay, not transaction execution gas. Single/hybrid replacement and relevant residual consolidation remain distinct scenarios.

After production source changes, refresh closed normal ABI/storage/size/runtime/initcode/data-child artifacts and strict current static review. Reuse only exact unchanged source/body evidence. Regenerate complete actual RPC fixtures if required, then rerun only their affected decoder/gas consumers. Source publication does not update runtime pins, installed configurations, contracts, services or websites.

## Fee and chain-limit qualification

Robinhood's [current fee guide](https://docs.robinhood.com/chain/gas-and-fees/) describes ETH payment with execution and Ethereum data fees bundled in standard estimation. The code's explicitly reviewed inclusive-estimate policy can represent that model; an Anvil estimate cannot qualify a real provider's complete charges. Actual estimates, receipt fields and approved fee semantics still require measurement.

The [upstream ArbGasInfo interface](https://github.com/OffchainLabs/nitro-precompile-interfaces/blob/main/ArbGasInfo.sol) distinguishes block accounting from transaction limits: the third `getGasAccountingParams()` result is a block limit, while `getMaxTxGasLimit()` requires ArbOS 50 or later. The actual Robinhood version and response remain unverified here. A confirmed block header alone is not proof of the transaction ceiling. The [network guide](https://docs.robinhood.com/chain/connecting/) also distinguishes rate-limited public endpoints from reviewed production infrastructure.

No new fee-code defect or provider acceptance is established by this preparation. Keep default gas budgets, full headroom, fee ceilings and all financial, source, authority, callback and exact-accounting guards intact. Existing Anvil8902, wallets, balances, journals, sites, signer restrictions and the user-paused heartbeat remain untouched.

## Fixture-only preparation follow-up

Five new whole-operation methods are prepared in an isolated copied test source: funded harvest and exact split, real Compounder reinvestment, ordinary Vault replacement, source-fault rollback, and hybrid opening followed by two-leg harvest and the next two-leg replacement. They use a separate maintenance cohort; the existing Entry setup graph remains unchanged. No maintenance before/after saving is claimed without a matching baseline measurement.

The final preparation draft passed a closed 200-source **ABI-only** type check against the original Oracle. Its test SHA-256 is `a012f266aff560baad94f61fa4c148446d6ad848a50fc4c180f8a1c0b364f13f`; no executable code was generated. Earlier drafts and their type-check receipts remain preserved externally. Runtime fitting and one changed-scope EVM build remain separate gates. Test-only price moves use real core swaps with explicit sqrt limits, never direct pool-storage edits. All ordinary cooldown, sampled-reference, financial and custody guards stay enabled.

Later read-only network qualification is recorded separately under [network](../network/) and [the network guide](../../../docs/ROBINHOOD_GAS.md). Its anchored transaction-cap observations do not retroactively turn the original synthetic traces into Robinhood operation or fee acceptance.
