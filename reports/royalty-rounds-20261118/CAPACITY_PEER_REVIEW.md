# Independent source review of the full-capacity fixture

Read-only review of `test/RoyaltyRoundsCapacity20261118.t.sol`, source SHA256
`123492acdbf7e2696f8a8bdca6580a6ccde7267f7cba863e851d211f251e0fdf`.
No test or production edit, execution or live action is made by this review.

- All 1000 NFTs mint through the installed verified mint2 fixture; 999 incumbents
  contribute through real Entry paths. Their weights, actual shares, LP backing,
  owner mapping and nonzero funded LP fee/compound reserves are asserted.
  Controlled feeds/VRF/access, external depth and local test assets remain seams.
- Admitting currencies after incumbent 8 creates one grouped zero-income cohort,
  followed by 991 actual eligible activations: 992 enrollment ends. Entry 1000
  appends at index 992, opening a new packed 16-entry array word. This is a real
  costly append state for the selected simple boundary representation.
- Each slow currency returns the correct balance after spending almost its 50k
  activation read allowance. It enters that behavior only for the ledger with
  under 60k forwarded gas. Ordinary independent reads remain fast. Actual trace
  costs must confirm the intended slow path; a Solidity label alone is not proof.
- The 20M call and full 20% margin are separately reported. The 32M fallback exists
  only to reach functional/accounting assertions. A passing Forge method does
  not imply that every case fits the 20M profile. Cold exact-call/estimate results
  and complete headroom must govern that separate qualification.
- There are ten export labels:two opening, six rotated including slow reads,
  and two growth. The output count is not a count of independent test methods.
- Actual claims drain all 17 currencies for every incumbent, preserve newcomer
  exclusion from old receipts, then distribute 1500 new units as 1499+1 with exact
  balance changes and empty liabilities/accounted/pending/opening/orphaned state.
  These individual functional claims do not qualify a cold 32-entry 12M router batch.
- The population remains mixed throughout the measured cases. Homogeneous GCD
  transitions, full-width lifetime wrap and canonical cursor/accrued behavior
  therefore rely on the separately recorded component/prototype evidence.

An initially reported fault-reset issue was a reading error: `uint256 f;` starts
at zero, so the existing post-measure loop already clears all 16 faulty readers.
That false finding is withdrawn; no fix is required or applied.

No further measured, drop-in source gas saving is established by this read-only
review. The round allocation removes receipt-geometry costs, but a failing cold
profile must remain unqualified. Do not lower the read allowance, weaken financial
checks or count the larger diagnostic budget as an operating success to obtain a pass.
