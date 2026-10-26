# Adversarial market verification

## Affected backend scope

[Runner](run-affected.py) selects TestCase classes defined in13affected modules,
deduplicates IDs and pins local Python inputs before/after. The
[final receipt](affected-suite.json) records **223 distinct methods passed, zero
failures/errors/skips and no source drift**. Eleven new methods are included once;
the earlier11new/123existing subset logs overlap this final selection and are
not added to its count. HTTP/RPC fixtures do not contact a real provider, signer,
installed Anvil or operating service.

The [negative control](backend-slot0/final-tests-old-source.json) executes four
exact final regression methods against the original HEAD implementations loaded
in memory: six assertion failure records, zero errors. The final test bytes and
old Git blobs are pinned. Preliminary probes remain in the same evidence folder;
they are not additional final tests or qualifications.

## TickMath reference check

An isolated pure [Forge harness](backend-slot0/tickmath-forge/test/TickMathCrosscheck.t.sol)
compares150Python endpoint vectors and149inverse interval assertions against the
installed byte-exact v4 TickMath/BitMath/CustomRevert copies. The
[receipt](backend-slot0/tickmath-crosscheck.json) pins reference/license/helper/
harness hashes and the command;299assertions are one reference check, not299tests.
Original MIT attribution/license is preserved. This check uses solc0.8.26, no RPC,
running Anvil, external wallet or service. It verifies integer arithmetic, not
provider authenticity or the safety of any particular pool.

## Actual installed v4 composition

[Final selection](solidity-summary.json): **15/15 methods passed** in
`IntegratedEconomicConservationTest`, including three new donation/out-of-range
cases and12existing cases sharing the corrected fixed-ZZZ bootstrap fixture.
[Detailed results](solidity-results.json). This affected fixture rerun is justified
by the setup correction; unrelated Solidity/keeper suites were not repeated.

The two directional cases actually swap the market outside the old range, join
with native ETH, grow with fixed ZZZ, rebalance and claim. They assert physical
LP identity/custody/range, old and new NFT shares, old-income exclusion, membership,
current marked allocation and actual backing. The donation case uses real
`PoolManager.donate`, not a synthetic reward index or direct Vault prefund.
Assertions reconcile observed receipts/payouts/reserves; they do not copy the
production index/share formulas. Normal actual v4 math/fee accounting executes;
admission/governance/feeds/VRF/Permit2 are explicit local substitutes.

The [first attempt](fixture-attempt1/solidity-results.json) has two
`InvalidConfiguration` failures and one donation pass. Its source bindings and
driver are preserved. Trace isolated the missing fixed-ZZZ fixture binding; only
the test bootstrap was corrected, before a fresh final typecheck/execution.
No guard or expected production revert was relaxed. The donation rerun overlaps
the final15and is not counted separately. Preliminary trace filter failed to
match with an over-anchored regex; the subsequent actual failure trace is retained.

[Typecheck](typecheck.json) and [bindings](bindings.json) capture265closed inputs
and normal0.8.26/Cancun/viaIR/runs1/Yul-disabled settings. The selected driver
preserves helper/selected method bytes and removes only unrelated test methods.
All44production Solidity/31normal dependency/four build pins are unchanged;
the exact37normal object/static and earlier1000claim-order evidence is reused,
not reported as a fresh build/full-regression/static audit. Test-method gas totals
combine many operations and are not production per-operation gas quotes.

## Release and preservation limits

This is internal scoped evidence. Real independent prices, routes/liquidity,
VRF/OpenSea/authority choices, current3 website/service acceptance, target-chain
gas/operating rehearsals and independent audit/remediation remain open.
No schema, permission, public signing or production deployment changes.
Existing local services/NFTs/LP/balances/journals and website/server remain intact.
See [review](REVIEW.md), [sole Todo](../../TODO.md) and
[release record](../../docs/RELEASE_CHECKLIST.md).
