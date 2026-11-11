# Changed-scope gas verification

The accepted Oracle-only optimization saves about **680,000 gas per contribution** in the matched local scenarios: 4.35–4.44% for activation and 4.72–4.83% for growth. All 23 selected actual EVM methods report `Success`: 18 directly affected existing methods and five new whole-operation maintenance methods. No unchanged suite was rerun.

The result retains all financial assertions and the exact default budget. **The contribution flows still fail the 12M default.** Passing the explicit 32M local diagnostic does not enable a production policy or qualify a provider.

## Contribution comparison

| Operation | Original cold call | Current cold call | Current +20% |
| --- | ---: | ---: | ---: |
| ETH activation | 15,317,541 | 14,636,780 | 17,564,136 |
| ZZZ activation | 15,644,361 | 14,963,971 | 17,956,766 |
| ETH growth | 14,103,737 | 13,422,920 | 16,107,504 |
| ZZZ growth | 14,404,957 | 13,724,583 | 16,469,500 |
| Second entrant | 15,038,024 | 14,357,635 | 17,229,162 |

These compare the same original controlled owner/input, graph, market geometry/depth, currencies, fees and cold preparation. Activation uses the original $1,000 fixture, not the website's $100 selection. The original Entry installation and setup bodies remain unchanged. The budget probe now always restores a snapshot, so future gas improvements cannot accidentally consume the measured activation or approval. All 30 original test-method bodies remain byte-identical; only the existing diagnostic helper and test callback changed.

## New full-operation maintenance measurements

| Full operation | Cold call | Unsigned +20% | Keeper +25% |
| --- | ---: | ---: | ---: |
| One-leg harvest | 661,011 | 793,214 | 826,264 |
| Compounder → Vault reinvestment | 10,680,943 | 12,817,132 | 13,351,179 |
| Ordinary one-position rebalance | 13,447,522 | 16,137,027 | 16,809,403 |
| Ordinary hybrid opening | 16,324,139 | 19,588,967 | 20,405,174 |
| Two-leg harvest | 1,016,015 | 1,219,218 | 1,270,019 |
| Next ordinary two-leg replacement | 16,631,798 | 19,958,158 | 20,789,748 |

These are a separate new maintenance cohort, not a before/after maintenance saving or a 1,000-NFT worst-case bound. They use the actual Compounder, Vault, Budget/Pricing, Manager/Executor, PositionManager and Uniswap core. Ordinary replacement retains the 12-hour cooldown, independent/physical corroboration, 600-second window, 300-second maximum gap, and 240-second samples. The off-chain jitter is a separate scheduling delay. No emergency path or financial guard was relaxed.

The tests verify actual funded fee splitting, unchanged owner/shares/main geometry on compounding, both-leg custody/harvesting, zero old-position liquidity after replacement, exact stale/disagreement errors and complete state rollback. A raw compound call can execute at 12M, but its required headroom exceeds 12M; raw success is not budget admission. Frontend 20% and keeper 25% are distinct policies.

## Evidence and limits

[EXECUTION.json](EXECUTION.json) preserves every selected result. One wrapper error occurred **after** Forge completed: its source glob also matched `out/*.sol` directories. The original output shows all 23 methods successful; its wrapper exited 1 and did not persist Forge's transport exit separately. That bookkeeping defect was corrected and the immutable output/source snapshot reconciled offline. No test or compiler run was repeated to repair the receipt.

[GAS.json](GAS.json) contains all six contribution readings and six maintenance readings. [SOURCE_SNAPSHOT.json](SOURCE_SNAPSHOT.json) distinguishes 200 supplied/watched source files from the 197 actually compiled sources. [TEST_SCOPE.json](TEST_SCOPE.json) binds the exact verified test copy published in the repository. The compressed original [Forge result](forge-results.json.gz) retains the raw output bytes; the earlier failures and four actual-owner RPC fixtures retain their original source scope.

Gas is measured by cold external-call `gasleft()` deltas. It excludes transaction intrinsic/data fees and is not an RPC estimate, receipt or Robinhood acceptance measurement. Controlled feeds, synthetic depth, registry, Permit2, VRF and MockAccess remain explicit test seams. Real markets, two independent price paths, provider fees/gas caps, actual launch amounts/workload and operating acceptance remain open. [Network qualification](../network/REVIEW.md) is separate evidence. No public transaction, existing node, website, service, signer, journal or paused heartbeat changed.
