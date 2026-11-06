# Moving-market verification scope

Baseline main7cc0f55; 6November2026. Production NOT APPROVED.
[Review](REVIEW.md), [executed scope](PROMPT.md), [final test record](accounting/FINAL_TEST_REVIEW.json).

## New evidence

Exactly **3 distinct new actual-local-v4 EVM methods passed** in215.562seconds.
Only those new methods ran. Both boundary branches are one method, not two tests.
No previous20-method campaign/full contract suite was rerun.

| New method | Nonvacuous assertions |
| --- | --- |
| testConsolidationRacePausedReviewUsesLiveInventoryAfterExternalSwap | Capture paused review, move market into residual to change actual token inventory. Main/residual L, fixed bounds and custody hash remain; same request succeeds with live inventory/retention and increased same-main L. Burned old residual ticks return0,0 without authenticating a live position. |
| testConsolidationRaceCapturedReviewRejectsBothExternalBoundaryCrossingsAtomically | Actual lower downward-exact tick is lower-1; upper exact tick is upper. Hash stays valid but guarded execution rejects both, preserving both physical NFTs/L/accounting/mode/nonce. External trade itself remains. |
| testConsolidationRaceGrowthActivationTransferClaimAndExpiryRequireCorrectFreshness | Real intervening growth and another NFT activation each invalidate old request. Main-only entrant funding, old-fee exclusion, current-owner transfer/claims while paused, paused growth rejection, true deadline expiry and fresh retry retain correct shares/backing. |

See [execution status](accounting/evm-initial/status.json), complete compressed
stdout and ABI/type closure in the accounting evidence. Final test rawSHA256:
`34e912ddd29c9f654e580d7a87d6d180595a6b37b4552d0d67a97bc165345e27`. All73 prior test method bodies remain unchanged; proof and exact
source closure are retained. Production53sources and31normal dependencies remain
byte-identical to the accepted prior normal build (84pins). ABI/type check uses
188source closure; that is not another production bytecode/gas qualification.
Source/test/config/toolchain were frozen during execution. The isolated copied
cache was campaign-owned; no existing Anvil process/state or old cache changed.

Actual core/periphery is local with recorded mock Access, correlated USD sources,
native admission/token/VRF/Permit2 fixtures. Meaningful production caller floors
must come from a fresh real simulation: test minL1 is fixture-only. The test EVM
size allowance1,000,000 is not a production size waiver. No production limit or
policy was loosened. Normal compiler object/carrier and495strict static review
evidence from the [prior source campaign](../residual-main-consolidation-20261106/VERIFICATION.md)
is reused at exact unchanged pins, not rerun or called a fresh audit.

## Documents, preservation and publication

Generated Todo,839function/888operator-row reference checks and the unchanged
strict static disposition checker pass. No Python behavior/API/keeper changes
require a new backend suite. Exact staged and committed Python publication
closure is separately checked before publication. Local document target/link,
whitespace and tracked preservation records are scoped to this change.

The maintained manual now distinguishes bounds/current tick, current Vault main
versus stale/burned IDs, confirmed pause and coherent canonical reads, execution
state versus old quotes, and custody hash versus all configurations. It covers
reorg/expiry/ambiguous pending recovery and explicit forced risk. Existing
Todo IDs/statuses and release/production gates are preserved. Roadmap correction
removes stale39-byte Migration headroom; unchanged current normal headroom is
Migration746/Vault107. Historical report bytes and four protected dirty files
remain unchanged. No website code, site/service rollout, signer, environment,
journal or user-paused heartbeat change is implied.

Finite serial-order/virtual-time evidence does not prove all markets or months
of uptime, optimal routing, independent oracle quality, maximum target gas or
MEV immunity. Matching actual provider/feed/route/VRF/authority/OpenSea services,
operating/recovery rehearsals and independent audit/remediation remain open.
