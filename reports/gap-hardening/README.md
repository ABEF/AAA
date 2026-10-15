# Atomic activation and custody recovery - 2026-10-16

**Undeployed local candidate; not production approval or an independent audit.**
No website/server change, public deployment, signature or real transaction was
performed. These receipts were captured before the user-authorized Git publication.
Earlier `release-progress` and historical
reports retain their original source scope.

## Changes in this pass

- **Original-source activation:** immutable Registry-created `ZZZActivationEntry`
  authenticates the current owner, exact input custody, real source USD valuation
  and exact Vault calldata. Direct pair input, exact native wrapping or an admitted
  typed single-hop V3 conversion share one 1% conversion-plus-LP execution budget.
  $100 of source value must produce at least $99 of marginal LP; gas is separate.
  Policy addition/disable/re-enable is governed and append-only. Actual production
  routes, token authorities and feeds still need qualification.
- **Callback isolation:** exact Vault approval and ownership recheck happen before
  context is armed. Context is cleared before allowance cleanup. Only the fixed
  Registry/Vault can read the matching proof; active mismatches revert. There is
  no arbitrary executor, recipient, supplied USD value, NFT custody or token sweep.
- **Paused custody parking:** timelocked governance binds exact bucket/LP/shares,
  local custody, epoch/nonce, ordered raw close minimums, deadline and review hash.
  Vault harvests venue fees separately and closes into its own attributed idle.
  Only actual close proceeds count toward minimums; old idle, compound reserves
  and donations cannot subsidize them. Parking omits price-feed and creator-inbox
  reads while retaining actual venue, token, wrapper and settlement checks.
- **Rights and recovery:** Parked is appended as custody status 6. NFT shares,
  ownership, membership, royalties and funded claims remain; new contributions and
  LP upkeep stop. Metadata/API report unavailable current LP valuation. Resume
  requires normal fresh-price/deployment guards. Approved parked migration retains
  route readiness, exact funding, delays, custody epochs, destination checks and
  the historical remote-reward liability barrier.
- **Deployment and release checks:** mechanical module lookup refactoring saves
  space without caching authority or changing the pinned compiler. The inventory
  now requires Entry binding/source-budget/context/route-history evidence and
  independently authenticated parking/resume rehearsal evidence. No general proxy
  upgrade or principal withdrawal was added.

Implementation details: [atomic Entry](../../docs/ACTIVATION_ENTRY.md),
[parking](../../docs/CUSTODY_PARKING.md),
[change boundaries](../../docs/CHANGE_AND_RECOVERY.md), and the
[NOT APPROVED checklist](../../docs/RELEASE_CHECKLIST.md).

## Local verification

The [source-bound summary](verification-summary.json) records:

- **488 Solidity passes**, zero failures, two expected offline opt-in fork setup
  skips, 490 total tests across 37 suites. All executed suite artifacts match a
  current transitive compiler input/output. Only Foundry's recorded CRLF-to-LF
  normalization of vendored `forge-std` is allowed; project sources match exactly.
- **488 portable Python passes** from a 492-test inventory, with no failures,
  errors or runtime skips. Four unchanged Unix-specific locking/file-safety cases
  remain reserved for supported Ubuntu verification.
- **23 normal runtime/initcode-object gates**, all 29 production source bindings,
  unchanged Solidity 0.8.26/Cancun/via-IR/optimizer-runs-1/Yul-disabled profile.
  Vault is 24,056 runtime / 24,809 initcode bytes, leaving 520 runtime bytes;
  Migration is 24,252 / 24,764, leaving 324 runtime bytes. Registry is
  11,933 / 33,088 including both helper creation objects. Final deployment
  constructor arguments are not included in object-size measurements.
- **220 fresh internally reviewed Slither findings:** 128 false positives,
  53 accepted risks, 39 informational, zero unresolved review entries.
  Two no-compile analyzer runs pass the strict source-bound coverage checker;
  43 matcher regressions pass and nine mutations are rejected. This is recorded
  internal review, not an external security audit. See [static review](static-analysis/README.md).
- The production example intentionally remains **blocked**, with 354 unset or
  unqualified inventory observations; these are release gates, not 354 discovered
  contract vulnerabilities.

The first full run had 487 passes and one new test assertion that ignored a raw
unit of reward-index rounding. The test now explicitly expects `90e18 - 1` and
checks that the remaining unit is both a liability and token-backed. No production
logic changed for that repair. The [first log](solidity-tests-first-attempt.log)
and [passing full rerun](solidity-tests.log) preserve both outcomes.

The 28 Entry unit cases use a minimal Vault; nine additional integration cases use
the real Registry/Entry/Assets/Oracle/Vault/NFT/Membership/rewards, with an explicitly
mocked V3 router and LP venue. Fourteen custody/timelock parking cases and seven
parked-reward cases exercise real custody/accounting with explicit venue fixtures.
None establishes an executable, funded production USDC/USDG-to-Pons route.

The separate [actual mainnet-fork receipt](fork/README.md) records **20 selected
native/Pons tests and nine secondary hookless-pool tests**, all passing with zero
failures/skips in one hardened-runner execution. Both exact suite inventories and
compiler closures were checked before/after; no historical outcomes were merged.
The run used chain 4663, block 88,544,093, hash
`0xc44dc8c95c6011b991312179f532935c2d94e4f21b84899d23896fd0fe01d490`.
Mock authorities/VRF, synthetic USD calibration and forced rebalance decisions
remain explicit. The new native parking cases exercise stale feeds, a broken
creator inbox, close-only minimums excluding reserves/donations, rollback and
fresh-oracle resume. They do not establish actual stable-route conversion,
production randomness or real cross-chain provider behavior.

## Remaining release work

Actual routes/feeds and combined Pons entry costs, supported proof-verifying VRF
and outage recovery, authority addresses, creator-payment/measurement agreement,
IPFS pinning, hosted financial projections and wallet transactions, Robinhood
Testnet operations, actual-venue gas/strategy work, supported Ubuntu qualification
and independent audit/remediation remain open. Real bridge provider wrappers and
backing/finality rehearsal are required before enabling migration.

Parking cannot force a failed chain, venue, wrapper or confiscated token to return
assets. Raw close minimums are governance-approved token-amount protection, not a
guaranteed USD recovery value. Resume and destination deployment retain ordinary
price safety; historical funding obligations cannot be discarded to force a move.
