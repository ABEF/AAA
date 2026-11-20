# Supplied pool: testing remains authorized

20 November 2026. Baseline main `a4720ecef3e0b0d97a1d16f8032cf751cc8b16e5`.

The operator clarified that pool
`0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b`
remains the integration test target even without current active liquidity.
Only the final **production** choice is deferred. This clarification does not
authorize public funding, transactions, configuration changes or deployment.

## Evidence we can reuse

The [historical fork verification](../current-pool-fork-20261026/VERIFICATION.md)
records 11 distinct successful methods across its original affected source
stages, at block 96,427,989. Real Uniswap core/periphery, Permit2 and ZZZ execute
with explicit mock authority/VRF/prices and fork-only account funding. It covers
LP mint/increase/close, both swap directions, actual fee collection, transfers,
claims and failure rollback. It is accounting3 evidence, not fresh F6 acceptance.

The [20 November market capture](../market-route-qualification-20261120/REVIEW.md)
records zero active liquidity at its selected pool snapshot. This does not prove
all distant tick ranges are empty, and does not prevent local LP experiments.

## Next missing fork partition

1. Use a new owned fork and pin its block/hash, exact PoolKey, runtime bindings,
   spot, fees and original active liquidity. Preserve the unmodified baseline.
2. Record the applicable quote/refusal before adding local liquidity.
3. Add liquidity only on that fork, using explicit test funding. Do not change
   public state, the existing Anvil instance, journals or running sites/services.
4. Exercise targeted currently uncovered LP placement, swaps and harvesting
   against the exact current F6 graph; preserve guards, rollback and accounting.
5. Label all locally added execution depth and substituted prices explicitly.
   Such success cannot establish sustainable external depth after our withdrawal,
   independent valuation, actual conversion feasibility, public gas/fees or launch.

The old runner is hardcoded to its historical block and complete 11-method gate;
rerunning it unchanged would not execute this new partition. No tests, compiler,
RPC, fork or public transactions were run for this documentation clarification.
The new current-anchor rehearsal remains to execute.

## Changes and verification

Updated the sole Todo, roadmap, findings, pool guidance, operator manual, README,
handoff and repository memory. No task status, source/configuration, economic
right, limit or release approval changed. Original edited documents were archived
before changes. The generated Todo and source-pinned workload inventory are
checked without rerunning behavioral suites. Production remains NOT APPROVED.
