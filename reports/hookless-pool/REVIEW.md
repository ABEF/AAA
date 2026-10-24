# Selected hookless pool: internal review

2026-10-24. Internal source review, not an independent audit or release approval.

## Authority and admission

- `configureNative` remains governance-only. It permits only native ETH / pinned
  ZZZ, zero hooks and static fees under existing bounds, on chain 4663 with pinned
  core/periphery/wrapper/token runtimes and exact wiring. It checks initialized
  slot price and static LP fee. The selected launch key is explicit; supported
  future fee tiers can be admitted after sealing without changing module code.
- Pons factory/hook/payout checks are removed because none belongs to the selected
  key. This does not grant arbitrary hook or router admission. Ordinary hookless
  ERC20 admission retains its existing boundary. Uniswap protocol fees are a
  separate external authority; fee changes do not inherently freeze collection.
- Sealed governance, guardian and keeper boundaries are unchanged. One contribution
  pool remains enabled at a time; LP movement does not silently switch that policy.

## Settlement and economics

- Native execution retains exact full-input settlement, net output, position
  ownership/liquidity checks, strict native callback accounting, prefund isolation
  and temporary-approval cleanup. Vault harvest-before-increase is essential: old
  native fee credits must not silently pay the next depositor's principal debt.
- Native balancing now reads actual directional protocol and static LP fees and
  sizes against the net ratio. This replaces a Pons-specific 1% adjustment. Spot
  impact and oracle mismatch are still bounded by execution and marginal LP checks;
  a planner is not a guarantee that a complete quote will execute successfully.
- The $100 activation / $5 growth policy, 99% marginal LP requirement and fixed
  3% aggregate maintenance budget remain. The higher selected fee may render an
  input route uneconomic; never weaken limits or spend incumbent backing to pass it.
- Ordinary WETH pool execution retains existing budgeting; full market and gas
  qualification are still required before enabling any destination for users.
- A forked normal exit exposed an incompatible requested minimum: the remaining
  aggregate 3% floor could be weaker than the manager's per-leg 2% floor, so the
  manager correctly rejected it. `MigrationBudget.handoffMinimum` now takes the
  greater of both applicable minima. This tightens the request without relaxing
  either safeguard. Final custody fixtures also enforce their own stricter 1%
  per-leg setting; old fixture expectations were not treated as authority to
  weaken production checks.
- The user retained the **1% ZZZ LP-fee conversion-loss maximum**, gas separate.
  A cheaper independently qualified conversion route is required: this pool's
  approximately 1.101% observed swap fee alone exceeds that budget for full-balance
  conversion at reference prices. Activation swaps only part of its input and has
  a separate aggregate measurement; its passing fork cases do not qualify a
  full-reward conversion. No route or lower-cost outcome is assumed.

## Two distinct movement paths

- `moveFunds` is an explicit governed alias for the existing atomic same-accounting-
  pair Vault move. The old selector delegates to that same guarded function.
  It cannot choose an external recipient, take another bucket's reservation,
  change shares or waive the fixed price-vector 3% cap. Destination LP is real.
- `exit` remains paused, snapshot/review/recipient-bound custody. Normal mode
  sends consolidated ZZZ; raw mode must be separately approved, sends both
  attributed currencies and has no USD-loss guarantee. No automatic fallback.
  Source cannot compel an external custodian to return funds. Existing royalty
  liabilities and custody use a distinct path, not a principal sweep.
- The native-to-WETH-to-new-native-fee-tier fork movement passed with actual LP
  seeded by the test harness before the collection existed. The preceding empty
  destination failure was correct rejection of an unexecutable balancing swap.
  Successful fixture execution does not qualify public depth, current prices or
  a destination's suitability; those checks remain necessary for each move.

## Open native-wrapper recovery gap

The selected venue holds ETH, but internal accounting and raw exit currently use
WETH. Closing/harvesting still wraps native proceeds. Wrapper failure or a rejected
proxy policy can therefore block raw exit even if the pool works. Earlier claims
that raw exit avoids all dependency failures would be incorrect.

The user requested native ETH accounting as the architecture direction for
robustness/efficiency. [The specification](../../docs/NATIVE_ETH_ARCHITECTURE.md)
is prepared; a native-accounting port, native custody payout and wrapper-independent
emergency recovery are **not implemented**. Earlier notes calling the direction
unapproved are superseded. Track this pre-seal work and preserve classification of
principal, unclaimed fees and unrelated native balances. The current checkpoint
cannot be described as a native-only system or as resilient to wrapper failure.
Do not add a generic sweep or pretend a broken token can be moved.

## Evidence and remaining gates

See [verification](VERIFICATION.md) for passing checks, failed attempts and exact
source scope. Fresh actual routes/prices, wrapper authority/storage review, live
services and gas/operating rehearsals, adapted inventory, VRF/marketplace support,
independent audit and remediation remain open. Existing Anvil/user state and public
signing are unchanged. Contracts remain undeployed and production NOT APPROVED.
The source-hashed runs are deliberately incremental: the earlier 106/native24
checks precede the exit-minimum fix, the subsequent 55-case run had two outdated
custody fixture failures, and the corrected custody24 and two failed fork cases
were rerun. This is not a final-source full-suite pass or an independent audit.
