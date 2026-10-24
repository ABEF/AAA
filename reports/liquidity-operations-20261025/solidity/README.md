# Scoped Solidity evidence

These checks exercise the undeployed candidate. They do not qualify public
providers, actual target-chain depth, maximum real-v4 combined-capacity gas,
marketplace operation or an independent audit. Production is not approved.

| Record | Scope |
| --- | --- |
| `composition-final-summary.json` | Eleven installed-v4 composition scenarios: explicit stricter 1% shallow activation, 2% default versus 1% conservative-price boundaries, inverse ZZZ/ETH range activation/growth, first/second-swap rollback, idle-only compounding, cooldown/failure recovery, fees, royalties, transfers and backing. |
| `maintenance-defaults-repaired-summary.json` | Twenty-nine focused original-policy/default/callback and custody/rebalance budget cases. The single rebalance boundary fuzz case uses 1,000 runs. |
| `entry-callbacks-final-summary.json` | Six additional own Entry callback cases with the historical 1% boundary selected explicitly; inherited repeats are excluded. |
| `cold-metrics-final.json` | Four final-source cold accounting workloads under the unchanged 12M operation gate. Mock strategy/venue do not execute balancing swaps; this is not maximum actual-v4 gas qualification. |
| `actual-v4-two-pass-metrics.json` | One of the eleven composition cases measured separately. The repeated metric observation is not an additional distinct pass. |
| `production-size-gates.json` | Thirty-seven normal compiler object gates; 42 production input hashes. Static constructor arguments are included in creation limits. |
| `final-solidity-bindings.json` | Union of 59 scoped production/test input hashes, checked against working files. |

The actual-v4 fixture uses installed Core, PositionManager and StateView plus
real protocol accounting. Governance/admission, tokens, dual sources, VRF and
the Permit2 boundary are local substitutes. The injected second-swap failure is
explicit dependency fault injection: its first real pool swap and all economic
changes must revert atomically. It is not an observation of a public outage.

## Diagnostic chronology

- The first straightforward implementation exceeded the Vault runtime gate.
  `initial-oversize-gates.json` and `deduplicated-oversize-gates.json` preserve
  rejected intermediate designs. Compiler/EIP limits were not raised.
- The initial failed-compound test counted Foundry's recorded logs from a
  reverted call as committed income. The harness was corrected to exclude
  non-receipt logs while checking complete state rollback.
- `maintenance-regressions-summary.json` records eight earlier scoped passes
  and thirteen stale-fixture failures. The failures occurred before the intended
  attack path because the old policy mock lacked pricing-V2 `validatePrice`.
  The exact diagnostic is retained in `maintenance-first-failure-trace.log`.
- The repaired test policy explicitly models its one intended synthetic swap;
  replaying a fixed amount on the new reconciliation pass would invent another
  unrelated execution loss. Actual two-pass economics are tested separately
  against installed v4.
- `maintenance-defaults-final-summary.json` preserves a failed intermediate
  typecheck caused by changing the test-policy constructor. The final fixture
  keeps a no-argument constructor and an explicit test-only venue observer.
- Earlier `composition*` summaries keep their own hashes. Repeated cases are
  counted once in final totals; no fresh full regression is claimed.

The `*.py.txt` runner/build copies document the isolated external profile,
compiler, normal settings and evidence capture. They do not access private keys
or alter existing Anvil state, services, journals, signing policy or monitoring.
