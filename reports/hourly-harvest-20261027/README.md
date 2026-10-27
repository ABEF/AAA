# Hourly independent LP harvesting

Current accounting4 keeper default and blocked example now use3600seconds for
standalone harvesting. Historical profiles retain their omitted-field14400second
default and existing examples; explicit global/per-bucket settings still override.

No Solidity changed. Existing `Vault.collectFees(bucketId,deadline)` collects
actual LP fees and applies80/10/5/5 in one on-chain transaction, without a
rebalance or USD-price dependency. Governance can call it manually; the function
is permissionless and does not let callers redirect money or withdraw principal.
The keeper normally schedules it, paying network gas separately.

23 affected Python methods pass, including3 new schedule-boundary/override/
historical-behavior checks. Existing cases cover pending recovery, gas limits,
price-dependent maintenance outages, pause/canonical controls and terminal exit.
[Execution summary and source pins](verification.json). No Solidity/size suite
was repeated for this Python/configuration-only change.

The timer remains the last confirmed successful standalone-harvest receipt.
Polling, other jobs, transaction confirmations, outages and gas/lifecycle checks
can delay nominal hourly execution. Implicit/manual harvests do not reset that
standalone timer. Compounding and buybacks remain separate guarded jobs; ZZZ
holder rewards still need qualified conversion for ETH-only settlement.

Operator/operations/economics/context/feature/Todo documentation is updated.
No installed config, service, contract deployment, website or Anvil state changed.
Actual operating schedule, gas economics and production acceptance remain open.
