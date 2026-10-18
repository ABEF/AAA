# Range-policy application: internal review - 2026-10-18

Internal review only; independent audit and production qualification remain open.
The [design](../../docs/RANGE_POLICY_UPDATES.md) specifies the authorization and
integration boundary. This is a stateless change to Strategy, plus backend
observability. Vault, registry, controller, accounting and keeper source are
unchanged; [scope](scope.json) records the exact source comparison.

## Design decisions and adversarial checks

| Concern | Resolution and remaining boundary |
| --- | --- |
| A flat price prevents approved range application | An actual tick mismatch against the current approved width at the recorded center is an alternative eligibility trigger. The existing timelock approves the full pool configuration. There is no new keeper-selected range or privileged force function. |
| Small price movement causes constant replacement | Comparison uses the recorded creation/rebalance center, never the moving current price. Outward tick math is shared with target. Unchanged rounded ticks do not authorize replacement. The ordinary price trigger remains independent. |
| Stale request or physical LP identity | No new request state exists. Each read resolves current bucket/pool/physical ID. A successful replacement records current target/center and clears the mismatch; reverting configuration to deployed ticks also removes it. Re-preparation is still required operationally after changes; there is no on-chain config-version lock. |
| Cooldown, stale oracle or disabled pool bypass | Active status, nonzero LP/center, enabled operations and cooldown precede both triggers. Fresh oracle read precedes the alternative. Vault still enforces keeper, pause/lifecycle, deadline, deviation, execution minima, 3% overall budget and idle ceiling. |
| Lost claims or reset NFT identity during replacement | No share or reward ledger is added or modified. Existing atomic rebalance harvests and replaces the physical LP. The selected-pool fork checks current IDs, stable two-NFT shares, funded LP and royalty claims, failed-execution rollback and no repeated eligibility. |
| Malformed dependency or impossible target | Bad intervals and arithmetic revert; missing reads fail closed. A config that cannot produce a valid range near extreme ticks can require governance correction. Approved dependencies and oracle honesty remain trust assumptions. |
| Churn through repeated governance changes | Timelock and cooldown bound authority/frequency; they cannot make bad policy economically sound. The 3% cap is per operation, not a cumulative loss limit. Production backtests, gas/MEV limits and independent parameter review remain open. |
| Backend falsely promises a keeper execution | Confirmed context reports range/price causes and cooldown. Missing/invalid booleans or inconsistent eligibility reject. Expected execution and next-check timestamps remain unavailable without qualified telemetry. |

The new external calls are static reads to fixed modules. No writes, external
recipients, approvals or callbacks with mutation authority are introduced.
Factoring `_range` preserves the former `target` arithmetic exactly. Other target
consumers retain their previous semantics. A valid imported/replaced position is
checked by its current records; unsupported/stale module versions must not be
admitted as the current production manifest.

## Static review

Fresh Slither 0.11.6 analysis uses a fully source-bound normal production AST;
39 production sources are included. All 376 detector expressions match the prior
review after location normalization: 155 false positives, 75 accepted risks,
146 informational. The changed Strategy call graph and cooldown finding were
reviewed against the alternative trigger. The exact current fingerprints and
source hashes are in [the canonical review](../production/slither-review.json).
Four deliberately corrupted reviews are rejected by the unchanged matcher.
Detector results complement the manual review; they do not establish complete security.

The [verification record](VERIFICATION.md) states the actual tests and limits.
No running service or sealed deployment has been upgraded by this change.
