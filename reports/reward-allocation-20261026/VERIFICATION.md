# Reward allocation verification

## New accounting checks

[AST bindings](bindings.json) and [typecheck](typecheck.json) pin265inputs.
Only `test/NativeFeeRewards.t.sol` differs from the prior AST. The closed AST is
refreshed with solc0.8.26 and no errors, then the existing AST-selected driver
keeps the two selected methods and helpers byte-exact. Normal Cancun/viaIR,
optimizer runs1/Yul-disabled settings remain. [Runner](run-focused.py),
[summary](solidity-summary.json), [actual results](solidity-results.json).

Both methods pass:

- Exact6,000-unit native allocation to unequal LP shares and three equal activated
  memberships:680/1,160/3,560holder claims,300compound,300buyback, dormant zero.
  Several claims, a transfer and old-owner rejection preserve all reserves.
- 1,000 fuzz runs compare two traces with identical receipts/activation/top-up/
  transfer history and different claim orders/frequencies. FourNFTs, native and
  ERC20 receipts, allocation dust and index fractions are exercised. Each claim
  checks actual payout/liability changes and every other NFT's unchanged claimable
  amount, indices/membership and reserves. Final lifetime payouts, fractions,
  indices, remaining backing and reserves match; all5,445native/6,179token raw
  funded units are conserved, including reserved rounding remainder.

These are real accounting modules with mocked custody/share/venue admission and
VRF, not real liquidity/provider qualification. Production 44 Solidity,31normal
dependencies and four build inputs match unchanged normal evidence;37object size
gates/static analysis are reused, not rerun. No ABI/reference, rate or right changed.

## Keeper fix and negative control

[Final affected suite](keeper-tests.json) selects 22 modules and 376 unique methods:
370 pass, 6 explicit skips, zero failures/errors and no source changes during the run.
Five skips need Unix-specific permissions/locking; one cast CLI smoke method is
skipped because cast is not on PATH in this invocation. Available binaries or
earlier passes are not reported as executed methods. The 17 new scheduling methods
are included once; preceding overlapping subsets are not added to this count.

[Old-source negative control](keeper-negative-control.json) runs the final tests
against monitor from3ad0e3f0fd14c3142e798054df937236983698cd: three intended
starvation failures, zero errors. [Log](keeper-negative-control.log). The new
tests cover maintenance/conversion/metadata fairness, two continuously funded
currencies, pending-intent error propagation, pause/preparation/canonical locks,
restart/default cursor validation, malformed bounded tasks and empty configuration.
All submissions are inert fixtures; no signer/public transaction is involved.
Zero pool ID remains valid for direct ZZZ burning, where the contract does not
use a route. Other inputs still need an admitted pool and successful simulation.
Final review removed an unnecessary nonzero-only task restriction and added its
positive regression. The earlier375-method pass is preserved outside Git under
the campaign's `earlier-keeper-source` directory; the final source was rerun once
after that correction. Those overlapping results are not added together.

## Harness note and release boundary

The initial pre-typecheck harness comparison used Python newline normalization
and falsely flagged CRLF Forge dependency files. No compilation or EVM test ran
in that attempt. Comparison now preserves bytes, as the selected driver requires;
the265source pins are unchanged during execution. Actual final results above
are the single successful selected run, not an inflated sum of attempts.

No installed service, existing Anvil/NFT/LP/balance/journal, website, server,
monitor or public signing configuration changed. Actual feeds/routes/fixed-ZZZ
burn semantics, sustained job economics/latency/recovery and independent audit
remain unqualified. Documentation and local checks do not deploy or approve funds.
