# Dual pricing and factual LP: verification record

Recorded 2026-10-24. Production is not approved. Publication is recorded
separately. These are source-specific checks, not a fresh full regression.

The [internal review](REVIEW.md) describes findings and residual trust boundaries.
The [operator/design guide](../../docs/PRICE_SECURITY.md) gives exact configuration
and failure/recovery procedures. No actual independent provider pair is qualified
by the mocked feeds below.

## Scoped results

| Scope | Distinct passing cases | Evidence / limits |
| --- | --- | --- |
| Dual Oracle core | 27, including 1,000-run fuzz | [Initial run](oracle-first.log), [two repaired expectation fixtures plus added gas-exhaustion case](oracle-repairs.log), [scope](oracle-scope.json). The final Oracle adds only the fixed helper import/immutable/constructor creation; [exact source reconstruction and identical core functions](oracle-compatibility.json) establish reuse. New construction is exercised in contribution integration. |
| Factual installed v4 liquidity | 11 | [Scope](manager-scope.json), [10 cases](manager-tests.json), [last case](manager-final-case.json), [prepatch controls](manager-prepatch-control.json). Actual installed PoolManager/StateView/PositionManager; Permit2, feeds, admission and test tokens are explicit substitutes. Initial fixture diagnostics are recorded by the scope, not called production failures. |
| Frozen contribution / historical / 3% boundary | 13 | [First nine](focused.json), [three historical cases](historical.json), [3% boundary](final-boundaries.json). Historical compound classification and composition are explicit observation substitutes with physical test-token backing. They do not independently test complete historical FeeController reserve conservation. |
| Entry callbacks and adopted limits | 6 new | [Cases](entry-tests.json), [source inputs](entry-inputs.json), [external-only fixture filtering](entry-fixture-filter.json). Target/helper/production bodies are unchanged by that filtering; unrelated concrete test bodies were excluded from the isolated compile. |
| Governed contribution lifecycle fixtures | 3 affected existing | [Initial two passes/one stale spend-versus-burn fixture](governed-first.json), [repaired actual-burn case](governed-repaired.json). Synthetic direct calls to the former view-only math function were replaced with authenticated actual Vault lifecycle tests. |
| Affected accounting, Entry, native, typed routes and uptime | 106 existing | [105 passes plus one stale retired-slot fixture failure](affected.json), [only repaired uptime case rerun, alongside the new 3% case](final-boundaries.json). Fuzz cases use 1,000 runs. No broad suite was repeated after that fixture repair. |
| Cold capacity | 8 existing | [Seven passes and one 12M-budget failure](gas-first.json), [only repaired maximum-index activation](gas-repaired.json), [changed input](gas-repair-inputs.json). Final measured activation 11,864,627 gas, down from 12,394,559; unchanged 12,000,000 gate. Real-provider/venue/Robinhood gas is not qualified. |

These scopes cover **174 distinct Solidity cases**; repeated cases count once.
After the final epoch-zero scan optimization, [five targeted cases](optimized.json)
recheck honest activation/growth, callback rejection, incumbent historical backing
and the 3%-agreement/1%-loss boundary. Those five add no distinct case IDs.
The other source-scoped successes retain their actual earlier helper scope.
The optimization changes only irrelevant precomposition scans; later-epoch
historical checks remain. No fresh final-source full regression is claimed.

Backend and tooling cover **187 distinct Python cases**:

- [162 pricing/activation/earnings/preflight cases](backend-source-scope.json):
  25 new and 137 affected existing, including the corrected sequencer fingerprint
  fixture. [Affected run](backend-affected-tests.log), [timestamp checks](backend-timestamp-final.log),
  [final targeted checks](backend-final-targeted.log), [historical observations](backend-historical-final.log)
  and [required historical frame](backend-historical-presence-final.log) retain
  their exact sources and overlap accounting.
- [Eight new legacy local-profile startup guards](local-fixture-profile-scope.json),
  without a process, chain deployment or running-state change.
- [17 event-decoder/source-schema cases](event-checks.json). All 125 previous
  descriptors remain unchanged; three current pricing/contribution events are
  added, giving 128. Retired events remain decodable.

## Build, scope and release gate

[Final build/size receipt](production-size-gates.json) records **36 normal
production object gates** under pinned solc 0.8.26, Cancun, via-IR, optimizer runs1
and unchanged Yul-disabled settings. Runtime limits are unchanged; dynamic
constructor arguments still require exact deployment qualification.

| Contract | Runtime bytes | Creation bytes plus fixed arguments |
| --- | ---: | ---: |
| Vault | 24,551 (25-byte margin) | 46,720 |
| ContributionPricing | 14,613 | 15,331 |
| Oracle | 11,346 | 29,163 |
| MigrationBudget | 20,010 | 21,061 |
| PoolRegistry | 11,283 | 48,356 |

[All-source ABI/typecheck](all-typecheck.json) covers 115 source/test/script inputs;
[final Solidity bindings](final-solidity-bindings.json) bind their exact bytes.
The [source checker](source-checks.json) is consistency-only, not exploit analysis.
The [supplemental inventory receipt](backend-final-supplemental.json) confirms the
current example remains blocked, with missing live-service qualifications. Its
300-bps intended tolerance is not an on-chain configuration transaction. A mock
ready inventory or passing source check cannot approve production.

Actual independent source pairs, source/proxy administration, freshness ages,
market depth, conversion routes, full native/pricing-V2 operating rehearsals and
independent audit/remediation remain open in the [single Todo](../../TODO.md).
The 135,373-gas local maximum-state margin is small and uses test feed runtimes;
the actual provider/route profile must be qualified before admitting that state.

Earlier reports retain their original scope. No public contract transaction,
wallet key, deployment, service restart, website build or server change occurred.
Existing8902/Anvil/NFT/LP/balances/journals/dist overlay, Anvil-only signer, null
public DEPLOYMENT and paused monitoring are preserved. Publication requires the
separate Git/remote receipt; local evidence does not assert green published CI.
