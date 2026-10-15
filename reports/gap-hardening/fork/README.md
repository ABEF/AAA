# Actual Robinhood dependency fork - 2026-10-16

One execution through the hardened read-only CI runner passed **29 tests**:
**20 selected native/Pons cases and nine secondary hookless-pool cases**, with
zero failures/skips. The run finished in 359.344 seconds with exit code zero.
It signed and broadcast no transactions.

Chain 4663, block **88,544,093**, hash
`0xc44dc8c95c6011b991312179f532935c2d94e4f21b84899d23896fd0fe01d490`.
The selected pool is
`0x6538e2c223ed70228114983afecbe5e69fe627e2fafdf367bdd6bdeff2ad391f`.

- [Verification receipt](verification-summary.json): complete before/after source
  bindings, pinned block, per-suite counts, explicit scaffolding, raw evidence
  hashes and production sources outside the fork closure.
- [Structured compact results](test-results.json): all actual case names,
  statuses and reported gas, projected from the preserved Forge result.
- [Concise runner evidence](runner.log): explicitly labelled projection and
  the final exact-inventory coverage result. It is not the raw transcript.

The raw 68,068,111-byte structured Forge result is retained externally with
SHA-256 `2a75094048907eb38a1d78c3a48b01e1bb2d3706978c2e1a0cf68269e13a5a0a`.
The receipt also records the separate full runner log hash. No historical test
results were merged to obtain the 29-case result.

Both suite artifact closures match the current source before and after execution:
21 production source files plus four test files. Eight production sources outside
this closure are listed explicitly; the fork does not exercise the complete
29-source production system or every integration.

The selected pool uses its actual deployed venue, hook and wrapper dependencies.
Mock access/VRF and synthetic USD calibration remain explicit; forced rebalance
decisions test custody, rather than strategy economics. The new parking cases
simulate stale feeds and a broken creator inbox, check close-only minimums and
rollback against compound/donation subsidies, and require fresh feeds for resume.
The separate hookless pool is initialized locally on the fork.

This is not evidence of an actual funded V3 stablecoin-to-Pons Entry route,
production governance/VRF, bridge-provider operation, Robinhood Testnet rehearsal,
or an independent audit. Production approval remains open.
