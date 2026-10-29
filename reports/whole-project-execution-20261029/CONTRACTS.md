# Current contract and dependency body review

Frozen whole-project prompt, 2026-10-29. Contract main baseline `2feee92f`
plus the preserved unpublished confirmation2/emergency1 candidate. Production
Solidity and economic policy are unchanged. This is internal source reasoning,
not independent release approval, profitable-attack absence or deployed qualification.

## Actual read depth

All handwritten bodies in the 33 concrete project components were read, including
private/internal functions, modifiers and canonical import tails. Three bases,
six libraries and five interface files were read separately. The review includes
generated getter backing declarations and inherited dispatch; ABI rows are not
substituted for private helpers or modifier review. `body-coverage.json` binds
the explicit manual cases below to exact compiler AST extents and source hashes.
Its script only binds the completed reads; inventory generation is not an audit.

Source groups and reasoning:

- AccessController/Module: pre-seal bootstrap versus direct post-seal governance;
  unique parent-bound modules/companions, two-step governance acceptance,
  pause-only guardian, limited keeper, preparation/canonical/terminal barriers.
- Assets/Entry/Pricing/Vault: exact current owner and active call hash, original
  source price vector/caller cap before callbacks, entrant-only budget, old idle
  and compound in incumbent NAV, actual marginal LP, floor/ceiling/share rounding,
  approval reset, raw prefunds and complete callback/rollback boundaries.
- Oracle/Pyth/PoolRegistry: bounded exact ABI reads, positive rounds/decimals/age,
  sequencer transition grace, conservative upper-input/lower-output bounds,
  immutable ETH/fixed-ZZZ static hookless identity, dependency-free stops,
  configured economic bounds and same-value revision invalidation.
- Fees/Membership/Rewards: exact funded20-unit16/2/1/1 split, sub20 incumbent
  owner boundary dust, per-share/equal-member indices, fractions/global residue,
  conversion credits to the same NFT/components, current-owner clear-before-pay.
- RoyaltyRewards: actual received amounts, orphan/prefund quarantine, immutable
  rarity1/2/3, faulted-currency old-cohort protection before delayed joins, whole
  source-unit conversion, current-owner claims and frozen cutoff/late forwarding.
- Converters/V4Executor/Buyback/ClaimRouter/Compounder: immutable parent/ledger,
  typed venues and recipient, exact raw settlement, stronger minima, controlled
  unwrap, verified fixed-ZZZ balance/supply burn, pending reward independence.
- Strategy/Confirmation/Budget/Balancer/Manager: physical tick eligibility,
  configured same-side reference, explicit width exception after cooldown,
  strict sample gaps/reset/revisions, independent compound clock, bounded
  actual-core quotes, directional fees, separate all-in/after-fee/whole-budget/
  aggregate/caller/idle bounds, exact receipt/position/prefund invariants.
- Migration/CustodyValidation: explicit paused governance emergency manifest,
  optional economic/timing mask versus structural custody/raw minima, retained
  policy/raw evidence pinning, single atomic context; terminal irreversible exit,
  exact principal+compound, cumulative share apportionment, owner payout isolation.
- NFT/Metadata/Artwork/factories: authenticated asynchronous VRF request epochs,
  ordered no-replacement quotas/artwork, immutable traits, ordinary receiver
  callback versus inert import, NAV unavailable versus terminal zero, bounded
  metadata events, fixed parent identity and no existing-child configuration power.
- CanonicalHandoff/NFTCanonical/VaultCanonical/FeesCanonical/CanonicalLedger:
  six-domain captured cutoff, source-derived typed rows, ordinal/cursor/root and
  fraction checks, exact transferred backing independent of prefunds, partial
  settlement/funded abort, one-use restoration, atomic retirement/activation and
  multi-hop post-cutoff royalty forwarding. No post-exit replacement or sweep.

The imported implementation review is deliberately selective: ERC721 transfer
dispatch, authorization/approval clearing and receiver acceptance; SafeERC20
optional returns/zero-first approval; ReentrancyGuard; full-precision/ceil/sqrt
math; Strings decimal/JSON URL and Base64 tail handling; TickMath, SqrtPriceMath
and LiquidityAmounts rounding. Local PositionManager, PoolManager and Permit2
settlement/allowance/position packing were inspected as external ABI dependencies.
Their package source is not proof of deployed runtime authenticity or all
unreferenced package behavior. Compiler generated/virtual lowering applicability
still needs explicit release qualification beyond a source-pattern screen.

## Conclusions and targeted verification

No new independently confirmed high/medium Solidity exploit was found. Trusted
governance may explicitly bypass optional emergency economic checks and lose
almost all principal. That approved power is not reclassified as a defect.
Malformed/unqualified setup URI, token/proxy behavior, independent feed authenticity,
venue depth, real VRF and escrow compatibility remain integration/trust risks.

The economic availability investigation confirms distinct measurements: valid3%
source agreement does not guarantee executable1% additional-loss swaps; gross
slippage also limits the whole pre-mint balancing budget; maintenance3% and idle5%
are separate; an empty/all-rejected catalog can leave a one-sided position unable
to satisfy deployment. Do not loosen these policies to manufacture a pass.
Planner selection versus later final constraints remains a hypothesis without an
actual-core witness, not a confirmed routing defect or justification to edit code.

Two new focused methods in `test/NativeVaultFlows.t.sol` add meaningful composition
coverage. One examines all32 retained-check masks with an unavailable oracle,
requiring the exact oracle error where a direct/indirect price dependency remains
and actual successful swap/mint controls for masks0/8. It counts as one method.
The other injects a governed policy change from a token callback during actual
emergency settlement with bit16 retained and value checks disabled: LP/share/
reward/reserve/policy/context rollback is compared to success with the identical
manifest and callback removed. Fake admission/core/periphery remain explicit;
this is actual project module composition, not actual market qualification.
Execution is orchestrated separately by root. No pass is asserted by this record
before its exact runner receipt is attached.

Closed build11 has78 exact source contents matching the checkout and input SHA256
`db1bdeb885a5dcd62e77125faf4ac4dda58ede682487c6a5020eab2da11faf89`.
Its39 normal size gates remain applicable at those pins. Exact dynamic constructor
URI arguments, cold/maximal target gas and real external dependencies remain open.
Earlier131 distinct candidate EVM methods retain their own scope and are not
rerun or added to the new two-method count.

Output-annotation proposals are recorded separately from review verdicts. The
122 missing dedicated output annotations are mostly source-backed getters;
tuple meanings and units are reviewed explicitly rather than invented from types.
No callable notes are changed concurrently with the root documentation work.
