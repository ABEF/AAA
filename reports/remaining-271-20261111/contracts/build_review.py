"""Materialize individually authored contract reassessments; never infer closure."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
INPUT = Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/remaining-271-20261111-6cfa4f1/contracts-input.json')
BASELINE = '6cfa4f1d478c3d15470519801f9703f9f8a8d656'
ROWS = {}

def row(index, source, qualification, decision, action, evidence, tasks=None, related=None):
    assert index not in ROWS
    ROWS[index] = dict(source_implementation=source, live_qualification=qualification,
                       accepted_risk_or_supersession=decision, actionable_remainder=action,
                       evidence_specs=evidence, task_ids=tasks, related_rows=related or [])

row(0,
    ['Entry3/Pricing2 bracket entrant custody and callback-sensitive valuation; Vault._join checkpoints incumbents, balances entrant funds, increases main only and issues shares from post-write marginal NAV.',
     'Current execution-price1 freezes the admitted dual-source valuation while proving its own quoted reference-pool transition; current default is 300bps/97% deployed LP, not the historical 99% rule.'],
    ['Actual cold ETH/ZZZ Entry execution is demonstrated in the newer controlled full graph, but its 15.3/15.6M activation costs exceed the unchanged 12M default; optional policy2 and meaningful actual market depth/feed/gas remain unqualified.'],
    ['Old stable-input/Pons/routed-whole-contribution preparation is superseded; original local browser and 38-method evidence is not current production acceptance.'],
    ['Qualify and explicitly configure an affordable gas envelope and real independent feeds/depth; retain default rejection until that review.'],
    [('src/ZZZVault.sol','function _join(',65),('src/ZZZContributionPricing.sol','function begin(',26),('reports/reference-execution-20261111/VERIFICATION.md','| Controlled diagnostic |',12)],
    ['activation-quotes','activation-assets','reviewed-contribution-policy'])
row(1,
    ['CanonicalHandoff accepts an individually committed same-schema V10/accounting7/LP-allocation1 replacement, with exact funded retirement/activation and no cross-chain transport.',
     'Lineage authenticates predecessor addresses, runtime pins, retirement/activation and bounded history, but its configuration currently inherits execution_price_version from the successor while not accepting a predecessor override.'],
    ['Actual escrow cutover, archival completeness and bounded lifetime workload remain separate operating qualifications.'],
    ['V4/V5 predecessor profile language is historical; a V10 LP2 predecessor must retain execution0 when its compatible successor uses LP3/execution1. This is a concrete current consumer defect, reported to the backend owner.'],
    ['Add explicit per-predecessor execution_price_version with omitted historical value0; preserve provenance and test mixed execution0-to1 V10 history without relaxing accounting/royalty compatibility.'],
    [('frontend_api/lineage.py','previous_config =',12),('frontend_api/portfolio_v6.py','execution_price =',49),('src/ZZZCanonicalHandoff.sol','function _exactLPProfile(',10),('src/ZZZCanonicalHandoff.sol','function prepareImport(',15)],
    ['security-chain-recovery'])
row(2,
    ['holder_preflight.scan_page pins confirmed chain/block/NFT/controller runtimes, inventories every ordinal owner and classifies contract/delegated-code holders; summarize authenticates complete non-overlapping pages and refuses release approval.'],
    ['Every actual code-bearing holder still needs successor release/transfer/claim compatibility evidence, and active scans require a frozen rescan before cutover.'],
    ['A no-code address is not proof of key control; ERC721Receiver support alone cannot prove old escrow can release a replacement collection. No new arbitrary recipient is justified.'],
    ['Run the frozen all-holder inventory for the actual replacement and resolve each escrow/delegated-code owner before approving cutover.'],
    [('zzz_ops/holder_preflight.py','def scan_page(',28),('zzz_ops/holder_preflight.py','def summarize(',80)],
    ['holder-preflight','security-chain-recovery'])
row(3,
    ['Vault._reserve validates the reservation then permanently registers its logical bucket before recording the alias; _registerBucket counts even an unused destination and rejects a fifth distinct bucket.',
     'Reusing an already registered bucket does not double count; cancellation does not recover a consumed permanent identity.'],
    ['Actual destination inventory, maximum-capacity operations and gas/cutover remain qualification, not a reason to restore the old race.'],
    ['Historical remote admission/capacity proofs are superseded. Current four-bucket accounting serves one fixed native pair and one contribution pool at a time.'],
    ['Before reserving an actual destination, inspect bucketCount/bucketAt and plan the permanent slot budget; use terminal exit/redeployment if capacity is exhausted.'],
    [('src/ZZZVault.sol','function _registerBucket(',23),('src/ZZZMigrationBudget.sol','function validateReservation(',14)],
    ['shared-custody','destination-slots'])
row(4,
    ['Access.canConfigure gives direct authority to governance after seal and bootstrap before seal; propose/acceptGovernance is two-step but introduces no time delay.',
     'keeperAuthorized remains a separate sealed, operating, explicitly granted capability; immediate governance does not grant that capability to arbitrary callers.'],
    ['Real authority addresses, custody/key recovery and compromised-key rotation procedures still need qualification.'],
    ['The former zero-delay timelock scheduling apparatus was deliberately removed. No advance-warning interval is promised; the governance key can immediately alter bounded policy.'],
    ['Select and verify actual authority wallets, back up/rehearse two-step rotation and disclose immediate-governance trust; do not reintroduce schedule/execute instructions.'],
    [('src/ZZZAccessController.sol','function canConfigure(',30),('docs/GOVERNANCE.md','##',22)],
    ['immediate-governance','security-governance','authorities-prices'])

row(5,
    ['ActivationAssets.configureZZZ binds one nonzero code/decimals/dual-price identity once before seal; Registry.configureNative admits only native ETH and the pinned Robinhood ZZZ.',
     'Access.seal requires admitted ZZZ == Migration.currentZZZ; one-time Migration.configureZZZ validates the same immutable Buyback.zzz through CustodyValidation before recording its exit pin. Thus contribution, burn and terminal return cannot be retargeted independently.'],
    ['The actual ZZZ runtime, proxy/admin/pause/blacklist behavior and production constructor/module wiring still require dependency review.'],
    ['Historical configurable replacement-token and burn-target setters are removed; token migration uses terminal owner return and a new deployment.'],
    ['Verify the single actual ZZZ across assets/Registry/Buyback/Migration before seal and document upstream token powers.'],
    [('src/ZZZActivationAssets.sol','function configureZZZ(',13),('src/ZZZAccessController.sol','function seal(',36),('src/ZZZMigration.sol','function configureZZZ(',8),('src/ZZZCustodyValidation.sol','function validateZZZ(',16),('src/ZZZPoolRegistry.sol','function configureNative(',15)])
row(6,
    ['Registry admission enforces ETH/fixed-ZZZ, and Vault._movePool retains logical bucket shares while closing/redeploying the same ordered pair.',
     'Fresh fixed-pair pricing no longer scans foreign composition assets; compatibility historicalValue reads explicitly return0, with old ABI selectors retained.'],
    ['Actual same-pair destination and terminal owner-return gas/token delivery remain qualification.'],
    ['Different-pair epochs, issuer-token migration executors and bridges are intentionally retired. No unfinished cross-chain feature should be revived from the original AE-03 report.'],
    ['Use same-pair reviewed pool movement for fees/liquidity changes; use terminal owner exit and redeployment for a new token or chain.'],
    [('src/ZZZPoolRegistry.sol','function configureNative(',15),('src/ZZZVault.sol','function _movePool(',34),('src/ZZZContributionPricing.sol','function historicalValue(',4)])
row(7,
    ['NFT.canonicalWriteRecord preserves exact owner and original mint recipient in an inert V10 importer using _mint; normal transfer guards resume only after activation.',
     'The canonical peer schema/deployment commitment authenticates reviewed contracts, not whether an old escrow supports the new NFT address.'],
    ['Every actual contract/delegated owner needs release/claim compatibility and frozen preflight evidence.'],
    ['This is the same unresolved integration boundary as FB-22, not a reason to redirect an owner or infer safety from ERC721Receiver.'],
    ['Resolve concrete escrow holders before replacement and retain their evidence beside the cutover manifest.'],
    [('src/ZZZNFT.sol','function canonicalWriteRecord(',15),('zzz_ops/holder_preflight.py','def summarize(',80)],related=['historical/FB-22'])
row(8,
    ['Royalty canonicalCapture synchronizes each admitted currency, checks exact accounted liabilities/backing and snapshots it; handoff funding and abort require exact transferred balances.',
     'Activation outage isolation does not authorize omitting a failed currency from the canonical ledger.'],
    ['Permanently reverting, frozen, taxed or rebasing admitted tokens can block exact capture/funding/abort. Real token failure and fully funded restoration rehearsals remain open.'],
    ['This is an explicit dependency liveness limit. Original royalty conversion routes are superseded by original-currency royalty4; a haircut/sweep would change rights and is not authorized.'],
    ['Restrict actual registration to reviewed conventional tokens, qualify failure recovery and retain the no-write-off canonical rule.'],
    [('src/ZZZRoyaltyRewards.sol','function canonicalCapture(',31),('src/ZZZCanonicalHandoff.sol','function fund(',29),('src/ZZZCanonicalHandoff.sol','function returnFunds(',24)],
    ['asset-liveness-dust','security-dependencies','migration-framework'])
row(9,
    ['Paused governance starts terminal exit, snapshots every funded bucket share denominator and closes both actual LP legs without swaps.',
     'Cumulative floors in immutable mint order allocate every ETH/ZZZ raw unit; governance batches pay the current NFT owner with isolated receiver failures, and owner-only fallback selects a recipient.'],
    ['Actual 1000-holder gas, mixed multi-NFT owners, failed receivers/tokens and completion/restart operation remain qualification; bounded source tests do not make hostile recipients payable.'],
    ['External custody addresses and all-ZZZ exit conversion are intentionally gone. Current custody5 makes allocation/distribution governance-only while preserving holder reward claims and owner fallback.'],
    ['Prepare/review each of beginCollectiveExit, closeBucket, allocatePrincipal and distributePrincipal; fund the sender gas and finish deferred IDs without inferring a paid prefix.'],
    [('src/ZZZMigration.sol','function beginCollectiveExit(',33),('src/ZZZMigration.sol','function allocatePrincipal(',41),('src/ZZZMigration.sol','function distributePrincipal(',52)],
    ['custody-composition','native-custody-recovery','security-ownership-rewards'])
row(10,
    ['Terminal Access.lpExitStarted locks principal entry/maintenance/replacement; Vault.exitBucketToHolders separates actual closed principal and designated compound from Rewards and buyback backing.',
     'NFT._update keys transfers to canonical state rather than LP exit; Rewards and Royalty claims retain current-owner and economic-state checks. Royalties keep active rarity membership after LP exit.'],
    ['Post-exit receipts, claim/transfer/deferred delivery and terminal metadata still need the actual installed-consumer/token rehearsal.'],
    ['Principal cannot reopen and canonical replacement is disallowed after exit. Historical royalty conversion instructions are obsolete; future royalties are claimed in original currencies.'],
    ['Operate post-exit reserve burn and royalty sync/claims separately; do not clear membership or old rewards when principal is paid.'],
    [('src/ZZZAccessController.sol','function startLPExit(',7),('src/ZZZVault.sol','function exitBucketToHolders(',29),('src/ZZZNFT.sol','function _update(',6),('src/ZZZRoyaltyRewards.sol','function _claim(',27)])
row(11,
    ['Native currency is address0 throughout Vault receipt, Manager core settlement, exact balance checks, canonical funding and terminal payouts; no WETH wrap is used for principal.',
     'Manager immutable wrapper support belongs only to a separately reviewed earned conversion compatibility route, not this native LP accounting.'],
    ['Real periphery/core/code pins, recipient behavior, constructor arguments and native provider/gas handling remain unqualified.'],
    ['Original accounting4 wording is superseded by current accounting7; existing wrapped Anvil/history profiles must not be relabelled native.'],
    ['Verify actual native runtime pins and ETH sender/receiver balance deltas in deployment rehearsal while preserving historical readers.'],
    [('src/ZZZVault.sol','function _receiveAssets(',13),('src/ZZZLiquidityManager.sol','function unlockCallback(',43),('src/ZZZMigration.sol','function _backed(',4),('src/ZZZPoolRegistry.sol','function _nativeBindings(',24)])
row(12,
    ['Rewards.convertBatch consumes each selected NFT\'s existing whole ZZZ individual/collective rights, executes its separate ledger-bound converter and assigns every received ETH unit back to the same rights with cumulative floors.',
     'Conversion emits conversion events rather than new earnings; source and ETH liabilities/backing remain separate. Direct original-token claim remains a holder action, so ETH-only display must wait for real conversion.'],
    ['A real cheaper route satisfying default1% conversion loss, meaningful size/depth/gas and timely operating batches remains open; tiny favorable observations do not close it.'],
    ['Royalty4 deliberately pays original currencies and uses no converter. The LP converter cannot be described as automatic conversion of all royalties or relabelled ZZZ liabilities.'],
    ['Qualify and enable the LP-only conversion route/worker; display pending ZZZ accurately until a confirmed funded conversion.'],
    [('src/ZZZRewards.sol','function convertBatch(',51),('src/base/ZZZRewardConverter.sol','function convert(',45),('docs/LP_ETH_SETTLEMENT.md','##',30)])
row(13,
    ['Vault collects actual fee deltas from main and residual; FeeController.allocate classifies each20raw units16/2/1/1, holds sub20dust, and credits exact-unit Rewards for individual shares and equal activated membership.',
     'Compound and buyback balances remain designated reserves released only to fixed Vault/Buyback; claims consume already funded rights and trigger neither maintenance nor burn.'],
    ['Actual hourly harvest, compound and buyback economics/gas/depth, burn compatibility and operational scheduling remain release work.'],
    ['Before membership changes, sub20dust is explicitly flushed to incumbent individual LP rights; this deterministic indivisible-unit exception is not a royalty or Power weighting.'],
    ['Retain separate harvest/conversion/compound/burn/claim clocks and verify real reserve conservation in operating rehearsal.'],
    [('src/ZZZFeeController.sol','function allocate(',31),('src/ZZZFeeController.sol','function releaseCompound(',15),('src/ZZZRewards.sol','function _creditPool(',24),('src/ZZZVault.sol','function _harvest(',19)])
row(14,
    ['Budget.checkpoint captures the attributable starting portfolio before harvest/close/callbacks, includes released designated compound exactly once, then checks final deployed+idle at the captured vector.',
     'Execution1 now carries that frozen vector through a proved own reference-pool swap; controls/live source agreement remain validated.'],
    ['Repeated maintenance return, maximum operation gas and meaningful market liquidity remain unqualified.'],
    ['The user declined cumulative limits. Default3% maintenance is per operation, governed ceiling10%, and gas is separate; the same cap cannot be advertised as annual drawdown protection.'],
    ['Qualify turnover and net realized results and monitor cumulative losses off-chain without silently changing the chosen per-operation policy.'],
    [('src/ZZZMigrationBudget.sol','function checkpoint(',24),('src/ZZZMigrationBudget.sol','function _beforeMove(',57),('src/ZZZContributionPricing.sol','function markMaintenance(',26)])
row(15,
    ['VaultCanonical.validateContribution enforces current ownership/status, governed activation/growth minima, stronger admitted minimum and per-NFT cumulative cap; Entry.executeReviewed binds caller loss and policy before pull.',
     'Pricing.finish checks net NAV and marginal actually deployed LP against the stronger captured governing/caller floors; incumbent idle cannot subsidize an entrant.'],
    ['Actual client amount/decimals, independent pricing, gas and final trace/review deployment bindings remain qualification.'],
    ['Defaults100USD/5USD are now future-configurable through ProtocolPolicy; exact100-only and universal1%/99% are superseded by current3%/97% contribution default.'],
    ['Keep minima and source/unit displays synchronized with the admitted future policy and qualify actual Entry reviews.'],
    [('src/ZZZVaultCanonical.sol','function validateContribution(',30),('src/ZZZActivationEntry.sol','function executeReviewed(',39),('src/ZZZContributionPricing.sol','function finish(',25)])
row(16,
    ['Oracle.setDualFeed requires two distinct source addresses and distinct nonzero declared provenance IDs, pinned code/decimals/age; _readBounds rejects spread above the lower-denominator3% policy instead of averaging it.',
     'Execution contexts capture the initial vector and revalidate live agreement; the optional pool reader uses actual external spot times reviewed ETH/USD.'],
    ['Two genuinely independent ZZZ paths and ETH publication/liveness remain unqualified; two adapters over one pool or one Chainlink aggregator remain correlated.'],
    ['The user explicitly chose spot for valuation as well as placement, so TWAP is not a pending mandatory implementation. Spot and a large TVL alone do not establish economic independence or manipulation resistance.'],
    ['Select and depth-test two independent references excluding PoPL LP; keep stale/disagreement failures rather than inventing a mean/peg/target fallback.'],
    [('src/ZZZOracle.sol','function setDualFeed(',36),('src/ZZZOracle.sol','function _readBounds(',22),('docs/POOL_SPOT_PRICE_SOURCE.md','##',31)],
    ['price-security','dual-price-qualification','creator-zzz-price'])
row(17,
    ['A usable Oracle price requires admitted activePolicy, matching source runtime/decimals, valid positive complete round, age and sequencer policy. Pyth adapter validates its configured feed/exponent/publish time, not arbitrary public price text.'],
    ['Latest qualified addresses, funding/update cost, publisher freshness and Robinhood liveness policy remain unapproved. The Nov9 report already found shared Chainlink aggregator and stale/disagreeing stored Pyth; it is not a fresh quote now.'],
    ['The old Oct25 observation has no authority to configure a source or prove current fees; eth_call being read-only does not make on-chain round validation or Pyth updates free.'],
    ['Refresh actual same-anchor source/provider qualification and budget read/update costs before activation; publish no invented current ZZZ/ETH price.'],
    [('src/ZZZOracle.sol','function priceBounds(',13),('src/ZZZPythPriceFeed.sol','function latestRoundData(',28),('reports/market-followup-20261109/REVIEW.md','##',30)],
    ['dual-price-qualification','authorities-prices','creator-zzz-price'])
row(18,
    ['Budget owns separate total contribution/maintenance limits, converter owns total conversion, Strategy owns fee-adjusted additional loss, Registry owns per-venue gross/spot parameters and Oracle owns source disagreement.',
     'Caller maximum and captured revisions can only strengthen the applicable operation; raising a later policy cannot rewrite an in-flight review. Current contribution default is300bps, maintenance300, conversion100, additional100 and source agreement300.'],
    ['Actual feasible overlap of these limits, caller reviews and trading costs still needs qualification; different guards can intentionally reject the same shallow route for distinct reasons.'],
    ['Original200bps contribution text is superseded. Governance ceilings10% do not automatically change operating values, feed tolerance, caller limits or gas.'],
    ['Report each limit and remaining margin separately; adjust only the reviewed intended policy, never weaken a different guard to make a test pass.'],
    [('src/ZZZMigrationBudget.sol','function setLossLimits(',12),('src/base/ZZZRewardConverter.sol','function setConversionLossBps(',11),('src/ZZZStrategy.sol','function setAdditionalLossBps(',11),('docs/EXECUTION_LOSS_POLICY.md','##',34)])
row(19,
    ['Strategy._swapFee and Balancer._fee use the actual directional protocol nibble plus static LP fee minus overlap; _minimum retains both gross upper-input/lower-output floor and fee-net additional-loss ceiling.',
     'Execution1 Math.minimumOutput uses the same captured bounds with current controlled directional core fees, not a keeper quote.'],
    ['Exact live fees, meaningful liquidity and order-dependent extra deterioration remain market acceptance work.'],
    ['AdditionalLoss measures more than pure curve impact and does not exempt known fees from total contribution/maintenance/conversion budgets. No fee increase is silently authorized by an informational fee split.'],
    ['Qualify each admitted route in both directions and expose gross fee cost separately from the extra-loss budget.'],
    [('src/ZZZStrategy.sol','function _swapFee(',23),('src/ZZZLPBalancer.sol','function _fee(',6),('src/ZZZLPBalanceMath.sol','function minimumOutput(',15)])
row(20,
    ['Governance configures at most four admitted hookless native ETH/fixed-ZZZ swap venues and bounded solver work; LP3 compares feasible quoted candidates and may choose zero swap.',
     'Execution1 now permits a reviewed external reference pool to be the swap venue only with exact pre/post core-state proof; it must remain distinct from the LP destination. Empty venues disables swapping without fallback.'],
    ['Actual catalogue depth, fixed parents/runtime, bidirectional gas and source independence remain qualification; no automatic TVL discovery/admission is implemented.'],
    ['LP-routing1 is historical. Entry no longer has its own redundant whole-input route catalogue, royalties do not convert, and earned LP converter/Buyback policies remain separate.'],
    ['Admit a future compatible pool through validated Registry and configureExecutionPools with review hash; review reference depth/independence and all route-specific limits.'],
    [('src/ZZZLPBalancer.sol','function configureExecutionPools(',28),('src/ZZZLPBalancer.sol','function _plan(',35),('src/ZZZOracle.sol','function beginManagerExecution(',32)])
row(21,
    ['Vault._join checkpoints/dust-settles incumbent rights before receiving entrant funds, balances only entrant budgets, recollects fees generated by entry swaps and computes incumbent NAV separately before issuing shares.',
     'Pricing.contributionNav/finish include both physical legs and attributed idle but enforce entrant-only marginal main deployment; ticks, residual L and rebalance clock are not reset.'],
    ['Actual realistic depth, callbacks, rounding and installed full-operation gas remain acceptance work; a separately documented late-increase token/periphery callback question remains unverified, not an established outside-trader exploit.'],
    ['Released incumbent compound may become attributed idle without being invested by an entrant. Old foreign-currency mark scans were removed only after fixed-pair admission/import proof.'],
    ['Retain entrant/incumbent raw balance reconciliation and investigate only reachable late-fee callback behavior under the actual fixed token/periphery review.'],
    [('src/ZZZVault.sol','function _join(',77),('src/ZZZContributionPricing.sol','function contributionNav(',21),('reports/daily-reconciliation-audit-20261111/contracts/REVIEW.md','##',24)])
row(22,
    ['Whole replacement closes both physical legs before planning; actual-core quoteCandidate reverts all provisional core changes, and Manager executes at most one selected real balancing swap.',
     'LP3 Plan carries quoted full market state; execution1 proves actual output and post-state before settlement callbacks then validates again through the operation.'],
    ['Maximum four-venue search, actual target gas and economic best execution are not globally established; full cold Entry currently fails default12M.'],
    ['Old two-pass real swaps are superseded. Bounded search is not a globally optimal gas-adjusted router. Unlike the old record, an optional one-residual strategy now exists; TWAP slicing remains unimplemented by choice.'],
    ['Qualify maximum catalogue/search gas and alternative viable venues while preserving zero/one actual swap and atomic rollback.'],
    [('src/ZZZVault.sol','function _rebalance(',37),('src/ZZZLPBalancer.sol','function quoteCandidate(',25),('src/ZZZLiquidityManager.sol','function balance(',52)])
row(23,
    ['Strategy delegates configured price-space ranges to PortfolioPolicy with explicit ZZZ-in-ETH inverse orientation and outward tick spacing; pending manual width compares at recorded centre to avoid price-drift churn.',
     'Automatic two-width policy is optional, disabled when same-side reference protection is active, and cannot use the manual exception to bypass that protection.'],
    ['Actual decimal orientation/spacing, desired widths and operator application need live qualification.'],
    ['The accepted model is manual range selection, not an inferred volatility algorithm. General governed widths are now supported; ±25/±50 are defaults/examples, not a permanent two-choice limit for manual configuration.'],
    ['Read orientation and physical ticks, configure the reviewed new width, then apply at eligible guarded replacement or explicit paused emergency.'],
    [('src/ZZZStrategy.sol','function setRangeOrientation(',19),('src/ZZZStrategy.sol','function setKeeperRangePolicy(',31),('src/ZZZStrategy.sol','function _rangeUpdatePending(',7),('src/ZZZPoolRegistry.sol','function _configure(',15)])
row(24,
    ['Current Strategy.needsRebalance retains the hard minimum and manual geometry exception, but ordinary need now uses PortfolioPolicy.thresholdSide at85% of centre-to-boundary price distance.',
     'Confirmation corroborates the independent reference on the same side; Keeper scheduling adds the sampled window and durable jitter before a separately guarded Vault.rebalance.'],
    ['The hard12-hour minimum can intentionally leave principal inactive, and sampled spot evidence cannot prove continuous history or MEV resistance.'],
    ['This original outside-only/maintenance2/no-residual statement is substantively superseded by approved threshold85%/maintenance3 and optional main+residual. The1% centre-perfecting strategy remains rejected.'],
    ['Use the current85% geometry,600-second sampled window and60–300-second jitter in operating settings; retain independent corroboration and no automatic force fallback.'],
    [('src/ZZZStrategy.sol','function needsRebalance(',34),('src/ZZZPortfolioPolicy.sol','function thresholdSide(',21),('src/ZZZRebalanceConfirmation.sol','function condition(',30)],
    ['lp-execution-routing','security-keeper-manipulation','security-external-manipulation'])

row(25,
    ['Confirmation.observe records successful on-chain same-side/identity samples, clears observed failures/manual/inside conditions and restarts after a gap greater than configured maximum; _ready requires elapsed duration and a fresh final sample.',
     'Current confirmation3 defaults600seconds with maxObservationGap unset0 until review; the example config uses300-second max and240-second service checks. Raw condition reads can occur during cooldown; paid enrollment starts near eligibility.'],
    ['RPC/head delay, nonce congestion and transaction inclusion can still restart the strict window; movements between recorded samples are unobserved. Actual receipt-cadence rehearsal remains open.'],
    ['The original900-second/confirmation2 and no-cooldown-observation statements are superseded. User-approved durable jitter is60–300seconds after the600-second window, not a second on-chain duration.'],
    ['Qualify configured gap/inclusion and alert on repeated restarts; preserve reset acknowledgement and do not infer uninterrupted10-minute price history.'],
    [('src/ZZZRebalanceConfirmation.sol','function observe(',37),('src/ZZZRebalanceConfirmation.sol','function _ready(',5),('keeper/monitor.py','CONFIRMATION',4)],
    ['rebalance-confirmation-buffer','keeper-recovery','security-external-manipulation'])
row(26,
    ['Confirmation._condition compares the physical and independent reference thresholdSide using the same physical ticks/centre and requires the same nonzero side; one-side-only or opposite-side disagreement produces no candidate.',
     'Its identity binds fixed LP geometry, original pool controls and policy revisions so a change/restore cannot revive stale evidence.'],
    ['Economic independence/depth of the two configured sources remains unqualified; largest TVL is a reviewed choice, not an automatic oracle-selection rule.'],
    ['The old actual-boundary outside rule is superseded by85% distance while the LP may still be active. No TWAP was added; spot was explicitly chosen. This check reduces local-only triggering but cannot guarantee attacker unprofitability.'],
    ['Qualify references excluding PoPL depth and monitor source/physical disagreement; retain same-side and execution-quality checks.'],
    [('src/ZZZRebalanceConfirmation.sol','function _condition(',30),('src/ZZZRebalanceConfirmation.sol','function _referenceSide(',7),('src/ZZZRebalanceConfirmation.sol','function _controlFingerprint(',13)])
row(27,
    ['Migration.emergencyRebalance requires paused sealed governance, fresh exact custody/portfolio/control/nonce manifest and an explicit check mask; fixed Budget/Manager context alone can apply the optional financial bypass.',
     'Current emergency2 separates bit1 raw/cooldown from bit16 retained sampled evidence and keeps exact custody, token settlement, shares/reserves and terminal/canonical locks mandatory.'],
    ['Operator review, actual incident gas/dependencies and key recovery remain qualification. Checks0 may lose almost all principal; broken token/core behavior remains unfixable by force.'],
    ['The old capability1 and absolute no-bypass language is superseded, while no keeper automatic force fallback remains an essential requirement.'],
    ['Prepare the exact paused emergency manifest and explicitly choose retained checks/floors; reconcile any same-key out-of-band nonce with the stopped service.'],
    [('src/ZZZMigration.sol','function emergencyRebalance(',19),('src/ZZZMigrationBudget.sol','function validateEmergency(',16),('src/ZZZLiquidityManager.sol','function beginEmergency(',17),('docs/EMERGENCY_REBALANCE.md','##',35)])
row(28,
    ['On-chain permissions, exact actual-core quote sizing, independent sampled trigger and gross/additional-loss floors constrain keeper discretion and permitted extraction; execution1 additionally rejects unpredicted reference/venue state mutation.',
     'Public traders remain free to trade ZZZ; no strategy enforces an external trader holding period or guarantees execution profitability.'],
    ['Real ownership/depth, common-source manipulation, public orderflow, repeated allowed losses, protected submission and adversarial economics remain unqualified.'],
    ['The user retained per-operation rather than cumulative limits and hard12-hour cooldown; jitter is modest uncertainty, not MEV immunity. Optional residual reduces some immediate swaps but does not remove attack surfaces.'],
    ['Run reviewed real-depth economic scenarios and monitor cumulative outcomes before production; publish keeper release provenance without claiming it constrains an authorized on-chain capability.'],
    [('src/ZZZStrategy.sol','function _minimum(',8),('src/ZZZLPBalancer.sol','function _plan(',35),('src/ZZZOracle.sol','function afterSwap(',22),('docs/KEEPER_SAFEGUARDS.md','##',20)],
    ['security-keeper-manipulation','security-external-manipulation','audit-release'])
row(29,
    ['Current cleanup removed unreachable foreign-LP reserve scans after proving fixed pair admission and canonical import <=2assets; zero historical compatibility selectors and old raw canonical body shapes remain explicit.',
     'Fee canonicalBarrier and distinct pre/post callback authorization/source checks still prevent capture of partial allocations. Historical codecs/journals retain their old profile rather than being interpreted as new state.'],
    ['Whole-system independent audit, tight standard runtime/initcode and matching installed consumers remain open.'],
    ['The old justification for live foreign historical marks is superseded by fixed ETH/ZZZ. compositionEpoch remains a control/recovery epoch, not permission for arbitrary pair migration. Repeated checks are only removed with an actual same-boundary proof.'],
    ['Preserve compatibility-only ABI reads and source-scoped evidence; require exact source/API/storage proof before any further simplification.'],
    [('src/ZZZContributionPricing.sol','function historicalValue(',4),('src/ZZZFeeController.sol','function canonicalBarrier(',5),('src/ZZZMigrationBudget.sol','compositionEpoch',4),('reports/whole-project-review-20261111/REVIEW.md','##',30)])
row(30,
    ['Entry3 now performs direct exact native/ERC20 source transfer, exact approval/reset and final original-owner/balance/entry-policy checks; its redundant _convertV4 layer was removed.',
     'Manager.unlockCallback authenticates exact core payload and signed deltas, proves quoted output/state before settlement then revalidates after callbacks; ClaimRouter rechecks each current owner after preceding payouts.'],
    ['Actual fixed-token/proxy/periphery callback behavior still requires independent dependency qualification. Structural checks are not a promise every token can transfer.'],
    ['Emergency optional financial bits do not disable exact settlement, authorized recipient, reserve segregation or ownership. The historical Entry conversion-function pointer is obsolete, not a reason to restore it.'],
    ['Retain both pre- and post-external-call checks and qualify actual token/native callback behavior with matching fixed deployments.'],
    [('src/ZZZActivationEntry.sol','function executeReviewed(',90),('src/ZZZLiquidityManager.sol','function unlockCallback(',43),('src/ZZZClaimRouter.sol','function claimBatch(',31)])
row(31,
    ['Buyback.execute consumes only the separately released reserve, values the maximum spend at upper input price, uses a guarded ETH-to-fixed-ZZZ trade when needed and verifies actual token balance and totalSupply decrease.',
     'OperatingTradeUSD0 stops this job locally; maximum trade is future-configurable with review while immutable ZZZ cannot change. Holder claims never invoke it.'],
    ['Real ZZZ burn semantics, affordable execution route, gas funding and fairness under continuous maintenance still need operating qualification.'],
    ['A5% reserve classification is not an immediate purchase/burn promise. Post-exit validated deposits-disabled venues can finish remaining reserve burns without reopening principal.'],
    ['Qualify actual burn success/rollback and review fair job scheduling plus reserve accumulation alerts.'],
    [('src/ZZZBuyback.sol','function execute(',48),('src/ZZZBuyback.sol','function setMaximumTradeUSD(',16),('src/ZZZFeeController.sol','function releaseBuyback(',8)])
row(32,
    ['Vault fee allocation is funded by measured position collection; FeeController cannot accept an unpaid volume estimate or arbitrary creator credit.',
     'Runtime pins authenticate selected code but neither prove proxy implementation immutability nor show that fee growth came from organic trades rather than a genuine PoolManager donation.'],
    ['Actual token/admin/core/protocol-fee and source upstream powers, independence and economic revenue provenance remain qualification.'],
    ['Creator inbox/payment agreements and Pons revenue plumbing are retired; retain current market-control tasks without resurrecting those funding paths.'],
    ['Review real token/proxy/feed/core administrators and disclose funded-versus-organic revenue; continue to exclude raw Vault prefunds from attributed LP earnings.'],
    [('src/ZZZVault.sol','function _harvest(',29),('src/ZZZFeeController.sol','function allocate(',31),('src/ZZZOracle.sol','function _validateSource(',13),('src/ZZZPoolRegistry.sol','function _nativeBindings(',24)])
row(33,
    ['Fresh Entry-routing3 removed the route catalogue, v3/v4 whole-input converters and executor child. It accepts only ETH/fixed-ZZZ already in the destination pair and delegates the single balancing action to Vault.',
     'The current7-field request and explicit consumers distinguish this ABI from old routed Entry2; public signing remains disabled.'],
    ['Real current Entry deployment/provider/gas acceptance and installed consumers remain qualification.'],
    ['The original deferred cleanup is implemented, not still open. Royalty converters were separately removed by original-currency royalty4; the retained LP reward converter\'s optional v3/WETH route is distinct and must not be deleted from this argument.'],
    ['Keep old routed readers/journals explicit; qualify the current direct Entry graph rather than reviving unusable routes.'],
    [('src/ZZZActivationEntry.sol','struct Request',17),('src/ZZZActivationEntry.sol','function executeReviewed(',90),('reports/direct-entry-v3-20261103/REVIEW.md','##',30)],related=['historical/OP-27'])
row(34,
    ['Registry.disablePool alters only local admitted flags/revision and contributionPool, without token/oracle/core reads; NFT.setMintPaused independently stops minting.',
     'Re-enabling requires full configureNative validation; mint callbacks recheck pause/payment/VRF policy and SeaDrop helper observes the NFT mint pause.'],
    ['Actual authority/provider outage, stop/reopen service behavior and emergency handling need rehearsal; local disable cannot restore a broken token/core.'],
    ['Global pause, mint-only pause, deposits stop and operations stop remain distinct. Claims/transfers have their own canonical/economic locks rather than being globally disabled.'],
    ['Document which local flags to stop and the full validation needed to reopen; rehearse without restarting the user-paused service.'],
    [('src/ZZZPoolRegistry.sol','function disablePool(',13),('src/ZZZNFT.sol','function setMintPaused(',8),('src/ZZZPoolRegistry.sol','function configureNative(',16)])
row(35,
    ['The removed creator-inbox path is not reachable in the current release; only actual Vault LP fee receipts can be classified.',
     'Vault._join harvests entry-swap fees and prices late released compound as incumbent NAV before new shares, then authenticates post-write share and membership weights.'],
    ['Actual admitted token/periphery callback semantics remain qualification. The distinct post-harvest increase-fee-netting question is explicitly unverified and requires a reachable dependency callback; ordinary transactions cannot interleave the atomic join.'],
    ['Old creator global sync and Power/50-30-10-10 cannot be restored as a historical fix. Earlier callback regressions do not prove every later dependency boundary.'],
    ['Keep the current checkpoint sequence; obtain actual fixed-token/periphery review before treating the conditional late-increase concern as a demonstrated accounting defect.'],
    [('src/ZZZVault.sol','function _join(',77),('src/ZZZFeeController.sol','function allocate(',31),('reports/daily-reconciliation-audit-20261111/contracts/REVIEW.md','##',24)])

row(36,
    ['The retained historical PrincipalDistribution worker uses canonical successful-receipt retry clocks, durable ordinal cursor and alternating first/last scheduling rather than a local paid cache.',
     'Current custody5 explicitly rejects enabling this keeper worker; allocatePrincipal/distributePrincipal are governance-only and direct batches isolate receivers.'],
    ['Governance must still complete actual1000-NFT batches, monitor deferred IDs and fund gas; a successful receipt alone does not mean every receiver was paid.'],
    ['The original claim that keeper allocates/delivers current principal is superseded by the user\'s later governance-only decision. Historical worker fairness is retained only for its old explicit profiles.'],
    ['Use current unsigned governance exit preparation and confirm paid flags individually; keep keeper principal_distribution disabled under custody5.'],
    [('keeper/principal.py','def configure(',28),('keeper/principal.py','def run(',63),('src/ZZZMigration.sol','function distributePrincipal(',20)],
    ['migration-framework','custody-composition'])
row(37,
    ['Strategy.rebalanceCondition samples independently of cooldown, while needsRebalance and Confirmation.ready retain the hard execution clock.',
     'Keeper._confirmation_enrollment_at now starts paid enrollment only duration+max-gap before cooldown and keeps raw resets/checks active earlier; pending-first and expiring evidence priority are preserved.'],
    ['Actual serial nonce/inclusion/provider latency and restart progress under strict gap still require rehearsal. Recorded samples cannot prove unobserved prior4hours.'],
    ['Earlier enrollment is implemented, not merely proposed. Original900seconds/60–600jitter are superseded by current600seconds/60–300;240-second checks and300maximum gap remain.'],
    ['Qualify near-eligibility enrollment cost and timely confirmed samples; do not pay observations throughout the full12hours or infer readiness from elapsed local time.'],
    [('src/ZZZStrategy.sol','function rebalanceCondition(',8),('keeper/monitor.py','def _confirmation_enrollment_at(',8),('keeper/monitor.py','def _confirmation_priority(',26)],
    ['rebalance-confirmation-buffer','security-external-manipulation'])
row(38,
    ['Current deterministic bounded route sizing, post-removal quotes, captured whole-operation valuation and same-side85% sampled trigger constrain what an ordinary keeper transaction can do.',
     'Service jitter and released-code hashes cannot prevent a keeper key choosing another eligible submission time or trading from another wallet.'],
    ['Attacker/LP net outcomes require meaningful real external depth, fee and ordering assumptions; no profitability or protected-orderflow campaign is supplied by local callback tests.'],
    ['No cumulative breaker or24-hour rule was selected. The old claim that passive40% is unauthorized is superseded by optional bounded main/residual, whose economic efficacy is still unqualified.'],
    ['Keep economic manipulation and repeated permitted-loss analysis open under both keeper/external threat tasks, separate from permission bypass tests.'],
    [('src/ZZZLPBalancer.sol','function planReplacement(',6),('src/ZZZMigrationBudget.sol','function _beforeMove(',37),('src/ZZZRebalanceConfirmation.sol','function _condition(',30)],
    ['security-keeper-manipulation','security-external-manipulation'])
row(39,
    ['Permanent four-bucket reservation, exact-share closure and all-bucket-before-allocation terminal sequencing remain enforced; principal payouts do not silently skip a failed bucket.',
     'Historical state/journals and pending recovery remain profile-specific, with no automatic deletion or source relabeling.'],
    ['Lost governance, permanently broken token/core, dead/incompatible owners, obsolete runtime pins and source-chain halt may cause indefinite unavailability. Long-run archive/restore/host fencing and gas remain qualification.'],
    ['The current release has no external custodian/bridge or post-halt transport and no administrator confiscation/haircut bypass. Actual withdrawal of broken assets cannot be universally guaranteed.'],
    ['Maintain funded key/host/backups and operator recovery plans; qualify all actual buckets before irreversible exit and budget permanent slot capacity.'],
    [('src/ZZZVault.sol','function _registerBucket(',23),('src/ZZZMigration.sol','function closeBucket(',27),('docs/KEEPER_RECOVERY.md','##',33)],
    ['security-chain-recovery','asset-liveness-dust','destination-slots'])
row(40,
    ['Entry3 implements the requested cleanup: its seven-field ETH/ZZZ request and executeReviewed have no v3 route catalogue, kind or conversion executor.',
     'Backend ActivationConfig selects explicit routing3 and rejects mismatched execution1/LP3 versus historical routing profiles.'],
    ['Actual current manifest, provider, cold gas and source consumer adoption remain unqualified.'],
    ['This duplicates HC-50\'s once-deferred proposal, now implemented. Original royalty-v3 conversion recommendations are also superseded by royalty4, while LP-only earned converter compatibility remains deliberate.'],
    ['Use fresh direct Entry3 and retain old route/read/journal inspection separately; no further deletion follows from the obsolete branch.'],
    [('src/ZZZActivationEntry.sol','struct Request',17),('frontend_api/activation_config.py','self.lp_routing_version',21),('reports/direct-entry-v3-20261103/REVIEW.md','##',30)],
    ['lp-only-simplification','activation-quotes'],related=['historical/HC-50'])
row(41,
    ['Vault._redeploy checks the whole attributed idle budget before mint/increase, distinct from Manager\'s sold-input output floor and Budget\'s complete starting-principal maintenance check.',
     'Pricing.finish separately requires entrant marginal deployed LP; emergency check bits can make the idle/retention guard independently binding even if another floor is bypassed.'],
    ['Real fees/rounding/source spread may leave no jointly feasible trade; exact diagnostics and operating values remain qualification.'],
    ['No unconditional redundancy proof exists. Old2% contribution examples update to3% without widening the venue/retained budget or source tolerance. Idle remains holder principal, not surplus.'],
    ['Retain all separately scoped floors and explain the exact failing comparison; only remove a check after a full same-boundary/rounding/emergency implication proof.'],
    [('src/ZZZVault.sol','function _redeploy(',12),('src/ZZZMigrationBudget.sol','function assertIdleLoss(',5),('src/ZZZContributionPricing.sol','function finish(',25)],
    ['security-strategy','operation-review','liquidity-placement-idle'])
row(42,
    ['Vault._reserve now consumes permanent local capacity through _registerBucket before alias assignment, eliminating the original reserved-but-unadmitted slot race.',
     'Same existing bucket aliases are idempotent and canonical import uses explicit bounded bucket/alias records rather than an implicit remote arrival.'],
    ['Actual four-slot setup, first-use aliases and exact replacement import/cutover remain release qualification; a mistaken permanent reservation consumes capacity.'],
    ['Original bridge admission proof/provider transport recommendations are retired, not open implementation obligations. The untracked operations-hardening report is historical evidence, not current source approval.'],
    ['Inspect permanent slots before reserve/move and qualify actual same-pair topology; do not add removed bridge infrastructure to address this resolved local race.'],
    [('src/ZZZVault.sol','function _registerBucket(',23),('src/ZZZVaultCanonical.sol','function canonicalImport(',40)],
    ['destination-slots'],related=['historical/HC-01'])
row(43,
    ['Whole-unit Rewards uses LP share weights for80% individual and exactly one activated NFT weight for10% collective; royalty4 independently uses rarity1/2/3 tickets.',
     'Share/membership synchronization settles old pending books before new weights; ExactReplay replays whole-unit trees while the inherited royalty handler authenticates ticket allocation, without counting claims/conversions again.'],
    ['Actual history completeness, consumer/runtime bindings and today-price availability remain qualification; fixture400/360/380 and1050/730/770 are not live balances.'],
    ['Old fraction/index implementation descriptions are superseded by exact-unit trees/tickets, but the independent LP-versus-rarity economics and no-retroactive-top-up invariant remain unchanged.'],
    ['Retain independently derived raw-unit allocation expectations and verify authentic full history; missing prices/history must remain unavailable.'],
    [('src/ZZZRewards.sol','function syncShares(',31),('src/ZZZRoyaltyRewards.sol','function activate(',38),('frontend_api/earnings_exact_lp.py','class ExactReplay',85),('frontend_api/earnings_replay.py','def fee_credit(',12)],
    ['security-ownership-rewards','financial-history'])
row(44,
    ['Keeper treats preparationActive as a strict ABI boolean and rechecks preparation around unsigned simulation/journaling; pending recovery stays ahead of new job configuration.',
     'Current V10 canonical handoff and terminal holder exit retain distinct lifecycle locks and cannot be selected by assuming an absent getter is false.'],
    ['Actual installed keeper/controller/runtime compatibility, staged freeze/drain and recovery remain operating qualification.'],
    ['Old creator inbox/remote delivery/timelock behavior is removed. Permitted preparation work must follow current canonical-settling/harvest and claims guards rather than the old broad work list.'],
    ['Use current explicit maintenance3/custody5/V10 service inventory and rehearse preparation while preserving pending receipts and all old profile journals.'],
    [('keeper/monitor.py','def preparation_active(',8),('src/ZZZCanonicalHandoff.sol','function freeze(',25),('src/base/ZZZModule.sol','modifier',30)],
    ['migration-framework','keeper-guardrails'])
row(45,
    ['Buyback.execute reads Oracle upper input bound and rounds USD spend upward before reserve release, so the configured maximum holds at either admitted source.',
     'Zero operating ceiling stops before price/reserve reads; exact fixed-ZZZ burn and final keeper/pause recheck remain.'],
    ['Real token burn ABI/supply semantics, route liquidity and affordable gas remain unqualified.'],
    ['This concrete lower-bound budget defect remains repaired; later configurable maximum changes future sizing only and is not a cumulative spending cap.'],
    ['Verify actual fixed-ZZZ burn and operating maximum in production inventory; keep upper-bound arithmetic and zero-stop behavior.'],
    [('src/ZZZBuyback.sol','function execute(',48),('src/ZZZBuyback.sol','function setMaximumTradeUSD(',8)],
    ['lp-eth-settlement','security-dependencies'])
row(46,
    ['Current ordered randomness has no reroll/fallback; original coordinator callbacks can drain after runtime change, while planned future rotation requires every old draw finalized.',
     'Refusing owner ETH callbacks revert only the chosen claim/push; optional royalty currencies retain deferred cohorts; reserve release stays purpose-bound; sub20LP dust goes to incumbent personal rights.'],
    ['Supported VRF funding/callbacks, receiving wallets, malicious assets, pre-split raw-unit economics and unharvested receipt-time entitlement remain real dependency/economic qualifications.'],
    ['External custody and royalty conversion are removed. Terminal principal owner fallback is available for a rejecting receiver, but reward claims still pay the current owner; those recovery paths must not be conflated.'],
    ['Qualify each actual failure mode under its current path; retain original-currency royalties, no administrator sweep and exact receipt-time rather than invented trading-time income.'],
    [('src/ZZZNFT.sol','function rawFulfillRandomWords(',15),('src/ZZZProtocolPolicy.sol','function rotateRandomness(',13),('src/ZZZRoyaltyRewards.sol','function activate(',38),('src/ZZZFeeController.sol','function _flushHomeDust(',9)],
    ['fair-draw','asset-liveness-dust','security-ownership-rewards'])
row(47,
    ['Direct immediate governance, per-operation caps and dual-source conservative valuation remain explicit choices rather than trustless guarantees; mint royalties are a fixed5% ERC2981 request only.',
     'Manual range orientation/width is current, with optional auto two-width mutually exclusive with same-side protection; current source10 unsigned website and old signer profiles stay distinct.'],
    ['Real authority/dependency review, repeated-turnover economics, meaningful source independence, OpenSea payment enforcement/onboarding and exact constructor/gas qualification remain open.'],
    ['External custody, immutable buyback maximum, fixed VRF provider forever and oldEntryV1 website requirements are superseded by later authorized architecture; a compatible replacement remains trusted review, not arbitrary upgrade immunity.'],
    ['Retain a current decision register and qualification for each adjustable policy; do not reinstate timelocks/cumulative caps/auto volatility without a new explicit decision.'],
    [('src/ZZZAccessController.sol','function canConfigure(',27),('src/ZZZNFT.sol','function royaltyInfo(',5),('src/ZZZStrategy.sol','function setKeeperRangePolicy(',31),('reports/v10-website-20261109/REVIEW.md','##',30)],
    ['lp-execution-routing','rebalance-confirmation-buffer','security-governance'])
row(48,
    ['Current reviewed Entry3/review-policy2 binds maximumLossBps and exact expectedContributionPolicy before custody; Pricing captures source bounds/limits and checks completion after approval reset.',
     'Direct owner-to-Vault calls still lack a signed USD-loss argument and instead enforce their liquidity minimum/deadline and governed stronger policy.'],
    ['Actual unsigned/wallet review inclusion, configured feeds/gas and deployment/runtime compatibility remain qualification.'],
    ['The original9-field Request, review1 selectors and conversion step are obsolete; current7-field Request plus policy fingerprint cannot be safely called through old calldata. Zero loss means strict0, not disabled protection.'],
    ['Use generated current ABI and reviewed policy hash; never fall back to raw Vault or a historical execute selector when a caller review fails.'],
    [('src/ZZZActivationEntry.sol','function executeReviewed(',44),('src/ZZZContributionPricing.sol','function beginEntryReviewed(',20),('src/ZZZVault.sol','function activate(',20)],
    ['reviewed-contribution-policy'])
row(49,
    ['Current normal Solc0.8.26/Cancun/viaIR optimizer profile passes48runtime/initcode object gates with exact source closure; Vault remains24544bytes, Oracle24488 and Manager24386.',
     'The current Oracle creation including64bytes constructor arguments fits48395, but source-object size success is distinct from frozen full deployment calldata and transaction gas approval.'],
    ['Actual dynamic NFT URI/deployment constructor bytes and target gas remain qualification; cold current Entry exceeds default12M.'],
    ['Original37gates/57Vaultheadroom and pre-mint2 Entry sizes retain historical scope. No old partial mock/Forge process result is a fresh current full-suite pass.'],
    ['Freeze actual release constructor arguments and measure deployment/operation gas on the target provider without raising standard EVM limits.'],
    [('reports/reference-execution-20261111/VERIFICATION.md','## Production build and size',20),('reports/reference-execution-20261111/VERIFICATION.md','| Controlled diagnostic |',12),('docs/PRODUCTION_PREFLIGHT.md','##',24)],
    ['activation-assets','deployment-initcode'])
row(50,
    ['Reviewed Entry caller/policy binding remains before pulls; Registry no longer seeds the obsolete wrapper policy; Buyback maximum uses upper input value; metadata separates fixed rarity trait from activated royalty weight.',
     'Indexer.reconcile proves bounded canonical ancestry before atomic guarded rollback; RPC transport rejects redirects, including same-host, instead of silently changing approved endpoint.',
     'Maintained keeper CI invokes the defined-class/deduplicated run-keeper-tests selector containing maintenance/range/current confirmation suites; source wiring is not a claim the published workflow or real host passed. Current sole Todo/release guides replace the obsolete bridge instruction, with old reports preserved.'],
    ['Provider honesty/full history, installed consumer config, real dependency/gas acceptance and external audit remain separate.'],
    ['Newer Entry3/review2, native exactLP7, mint2/V10 and execution1/LP3 supersede old selectors/profiles; public signing and live site rollout are still not implied. Historical creator/bridge requirements are removed.'],
    ['Keep the exact current runtime/profile and generated references synchronized; qualify real provider/reorg and consumer rollout before approving release.'],
    [('src/ZZZActivationEntry.sol','function executeReviewed(',44),('src/ZZZNFTMetadata.sol','string memory rarity',30),('indexer/monitor.py','def reconcile(',45),('zzz_ops/rpc.py','class _RejectRedirects',5),('src/ZZZBuyback.sol','function execute(',18),('.github/workflows/keeper-safety.yml','name: Keeper safety',30),('scripts/run-keeper-tests.py','MODULES=',39)],
    ['reviewed-contribution-policy','security-integration'])
row(51,
    ['Current source supports direct native contributions, exact dual-source/reference execution, purpose-bound LP conversion, optional residual management, terminal holder return and mint2 SeaDrop integration.',
     'Current source10 website compatibility is implemented unsigned with public configurations null; it is not the old incompatible native2-only reader, nor proof of served production integration.'],
    ['Real independent sources/routes, token/VRF/OpenSea, authorities, immutable artwork/metadata hosting, maximal gas, sustained Linux/host-loss/backup/monitoring and independent audit remain open.'],
    ['External custodian trust and future bridge implementation are no longer launch obligations. Oracle source context improves own-reference-swap liveness but does not qualify independence or stop ordinary market/MEV loss.'],
    ['Complete actual reviewed dependencies and target-host/gas acceptance against the frozen current profile; retain NOT APPROVED until named external evidence exists.'],
    [('reports/reference-execution-20261111/REVIEW.md','##',30),('docs/SOURCE10_WEBSITE_PROFILE.md','##',30),('docs/RELEASE_CHECKLIST.md','##',30)],
    ['dual-price-qualification','metadata-ops','audit-release'])
row(52,
    ['Keeper reset acknowledgement remains durable: unknown nonempty samples after a confirmed clear require another reset, and initial raw/global clock/identity faults invalidate known windows before new observation.',
     'Shared physical_portfolio validation checks each PosM key/packed ticks/L independently for main and residual; wallet/read projections reject contradictory dormant/terminal/share states while keeping independent healthy claims visible.',
     'Preflight/health authenticate confirmation helper, Budget, parents/capabilities even when no candidate is due, while pending recovery skips new metadata dependencies. A late metadata fault restores previous last_success_at and reports degradation; terminal exit only exempts intentional stopped/cadence warnings, not bad bindings.'],
    ['Actual provider latency, raw logs, operator restart and consumer/service rollout remain qualification.'],
    ['Original confirmation2 and accounting3/4-only assumptions update to confirmation3/portfolio2/exactLP7/V10. Read-admission fixes never establish a Manager custody bypass or continuous-price proof.'],
    ['Preserve pending-first, reset-before-reobserve and exact per-leg identities; qualify actual240-second cadence and stale health handling.'],
    [('keeper/monitor.py','def _rebalance_due_checked(',52),('keeper/monitor.py','def _confirmation_priority(',40),('zzz_ops/physical_portfolio.py','def physical_amounts(',33),('frontend_api/royalty_reporting.py','def read(',40),('keeper/monitor.py','quality_fault=',18),('keeper/ops.py','confirmation = None',14)],
    ['rebalance-confirmation-buffer'])
row(53,
    ['The old fork\'s growth Slippage witness proves actual output below minOut and complete rollback under its original200bps fixture; it is not evidence that partial fill or marginal LP specifically caused that failure.',
     'Current LP3 quotes full core state, sizes a bounded feasible single swap and rejects any changed actual output/state. Permit2 amount0 remains no authority even if expiration normalizes to block time.'],
    ['Actual real-size97% contribution, approved source prices, meaningful external liquidity and target gas remain unqualified; later controlled reference execution is not an untouched-market success.'],
    ['The original4/6failure, empty-selection and fixed-prank attempts remain historical evidence. Raising the total contribution default to3% does not widen minOut or solve an independently failing swap floor.'],
    ['Rehearse exact feasible production amounts through full Entry with existing guards and retain precise revert classification; do not erase the original expected-failure witness.'],
    [('reports/current-pool-fork-20261026/VERIFICATION.md','## Useful failures and their limits',34),('src/ZZZLPBalancer.sol','function quoteCandidate(',25),('src/ZZZLiquidityManager.sol','function unlockCallback(',25)],
    ['activation-assets','mainnet-fork'])
row(54,
    ['Solver remains bounded to reviewed venues/work and may miss a viable global/gas-adjusted size; attributed idle remains holder backing and can block new contributions at the separate5% ceiling.',
     'Keeper waits to compound unless the main is in range/below threshold with no pending geometry; same-main governance consolidation offers distinct guarded/forced recovery, not an automatic fallback.'],
    ['Worst catalogue/deep-tick gas, independent sources, route/target bands, real operators and maximum workload remain qualification; default cold Entry is currently over12M.'],
    ['Old54-byte Manager init margin and unimplemented15-minute buffer are obsolete; current normal sizes and600-second sampled window apply. Separate converter and Buyback routes do not automatically use LP best-route selection.'],
    ['Qualify bounded search/gas and useful idle reinvestment thresholds; diagnose intentional floor/cooldown blockers before selecting a reviewed manual action.'],
    [('src/ZZZLPBalancer.sol','function configureSolver(',7),('src/ZZZVault.sol','function _redeploy(',12),('keeper/monitor.py','def _compound_due(',36),('src/ZZZMigration.sol','function consolidateResidual(',21)],
    ['lp-execution-routing','liquidity-placement-idle','operation-review','testnet-rehearsal'])
row(55,
    ['The shared canonical balance primitive remains the exact native balance/ERC20 balance in the same ledger, not an external custodian or an LP valuation read.',
     'Current royalty4 _sync/_claim/claimable/canonicalCapture/import/activate/forwardLate keep receipt, liability, prefund and orphan classification around that primitive; exact-unit tickets replaced fractional indices.'],
    ['Actual token transfer/read behavior, upstream powers, raw-unit capacity gas and supported successor recovery remain qualification.'],
    ['Old conversion/exitCustody/returnCustody call sites no longer exist. Their removal reflects original-currency royalties and terminal principal owner return, not deletion of legitimate backing checks. Original compiler-equivalence proof applies only to that old rename.'],
    ['Preserve classified backing at all current balance reads and qualify malicious/failed assets without inventing a generic sweep.'],
    [('src/base/ZZZCanonicalLedger.sol','function _canonicalBalance(',4),('src/ZZZRoyaltyRewards.sol','function _sync(',45),('src/ZZZRoyaltyRewards.sol','function canonicalActivate(',11),('src/ZZZRoyaltyRewards.sol','function forwardLate(',10)],
    ['security-ownership-rewards','asset-liveness-dust'])
row(56,
    ['Current royalty4 has no native conversion writer or external currency custody. Healthy native synchronization occurs before each one-time activation, then its eligible prefix includes the new activation; exact ticket rights and stored imported accrual stay separate.',
     'Reporting5 rejects original-currency native eligibility contradictions and nonzero available royalty claims for a dormant/deferred-native NFT, with importing/cancelled lifecycle projections blocked upstream.'],
    ['Actual exact-profile consumers and token failure/cohort recovery still need installed qualification.'],
    ['The historical proof based on convertBatch/_sync(0) and custodyNonce is no longer the current mechanism. Its abstract no-pre-enrollment-native-credit invariant survives; do not restore removed conversion/custody getters or reinterpret old profiles.'],
    ['Maintain explicit reporting5/current-ledger checks and revisit the native invariant only if a future writer or eligibility-removal feature is proposed.'],
    [('src/ZZZRoyaltyRewards.sol','function activate(',46),('src/ZZZRoyaltyRewards.sol','function _claim(',25),('frontend_api/royalty_reporting.py','if asset == ZERO and count != total:',30),('frontend_api/royalty_reporting.py','Deferred native royalty entitlement',5)],
    ['royalty-eth-settlement','security-ownership-rewards'])
row(57,
    ['Entry/Vault enforce entrant-only custody and measured marginal LP, incumbent harvest/dust/compound separation, exact transfers and final current-owner checks; Manager validates real PoolKey/ticks/L and settlement through fixed typed child.',
     'Execution1 preserves original captured valuation through its exactly quoted own swap and revalidates source/control boundaries through mint/refund/end, rather than requiring an unchanged reference round when the reviewed trade moves it.'],
    ['Conventional fixed token/periphery honesty, source independence, real depth/gas and full release audit remain assumptions. An unverified late-increase callback question remains separately documented.'],
    ['External custody routes, creator inboxes and old arbitrary pair composition are retired. One main plus optional residual is fully accounted; raw L from different ranges is never summed as value.'],
    ['Keep exact per-leg raw asset reconciliation and independently review dependency callbacks and full-context boundaries on the frozen current graph.'],
    [('src/ZZZVault.sol','function _join(',77),('src/ZZZLiquidityManager.sol','function unlockCallback(',43),('src/ZZZOracle.sol','function validateExecution(',8),('src/libraries/ExactToken.sol','function pull(',18)],
    ['security-share-accounting','security-dependencies'])
row(58,
    ['Oracle accepts <=3% lower-denominator source spread but contribution compares upper input with lower actual deployed LP/NAV; separate venue/spot/additional floors still apply.',
     'At100lower/103upper the conservative valuation alone consumes3/103=2.9126%; current3% contribution leaves only0.09lower-mark units before its97% upper-input floor99.91, so nontrivial fees can still block a healthy-agreement route.'],
    ['Meaningful real source spread/depth/cost overlap remains unqualified; exact same-price positive mocks do not establish it.'],
    ['The old2% example is superseded but its liveness principle remains. No averaging, target-spot substitution or automatic budget widening is authorized.'],
    ['Expose source spread, deployed marginal requirement and route cost separately in reviews; qualify actual operating feeds/routes and allow governance to make explicit bounded future policy choices.'],
    [('src/ZZZOracle.sol','function _readBounds(',22),('src/ZZZContributionPricing.sol','function finish(',25),('docs/EXECUTION_LOSS_POLICY.md','##',34)],
    ['dual-price-qualification','operation-review','activation-quotes'])
row(59,
    ['Current source implements SeaDrop mint2/helper1, exactLP7/royalty4/V10, optional residual and execution1/LP3; source10 unsigned website compatibility is distinct from served current3 and public signing remains disabled.',
     'Current strict static coverage567 retains162 source-context reviews/405 exact reuse and later two authority-rationale errata; it is internal evidence, not independent approval.'],
    ['Actual feeds/routes/VRF/OpenSea fees/onboarding, token burn/control review, authorities, permanent artwork/hosting, current consumer rollout, archive/recovery/operating rehearsals, cold/maximal gas and independent audit remain open.'],
    ['The original direct-mint-only unfinished-code, native2-only website, unknown retired token unsupported and external-custody/bridge statuses are superseded: current late royalties can forward unsupported raw tokens to the authenticated successor and reviewed recovery can allocate them in original currency. Hostile tokens remain a real limit.'],
    ['Use current release checklist and exact profiles; close external gates only with real frozen-release evidence, especially current default12M cold Entry failure and missing live dependencies.'],
    [('docs/RELEASE_CHECKLIST.md','##',30),('src/ZZZRoyaltyRewards.sol','function forwardLate(',10),('reports/reference-execution-20261111/VERIFICATION.md','| Controlled diagnostic |',12),('reports/daily-reconciliation-audit-20261111/contracts/AUTHORITY_ERRATA.md','# ',30)],
    ['activation-assets','fair-draw','opensea-mint','host-services','audit-release'])

_BLOBS = {}
def baseline_blob(path):
    if path not in _BLOBS:
        _BLOBS[path] = subprocess.run(['git','show',BASELINE+':'+path],cwd=ROOT,check=True,capture_output=True).stdout
    return _BLOBS[path]

def evidence(spec):
    path, term, count = spec
    data = baseline_blob(path)
    text = data.decode('utf-8-sig').replace('\r\n', '\n')
    lines = text.splitlines()
    positions = [n for n, line in enumerate(lines) if term in line]
    if not positions:
        raise ValueError(f'Absent evidence term {path}: {term}')
    start = positions[0]
    end = min(len(lines), start + count)
    excerpt = '\n'.join(lines[start:end]) + '\n'
    return dict(path=path, revision=BASELINE, hash_mode='raw_bytes_and_utf8_LF',
                sha256=hashlib.sha256(data).hexdigest(), sha256_lf=hashlib.sha256(text.encode()).hexdigest(),
                line_start=start+1, line_end=end, term=term, excerpt=excerpt,
                excerpt_sha256_lf=hashlib.sha256(excerpt.encode()).hexdigest())

def main():
    original = json.loads(INPUT.read_text(encoding='utf-8'))
    tasks = {task['id'] for area in json.loads((ROOT/'docs/project-todo.json').read_text(encoding='utf-8'))['areas'] for task in area['tasks']}
    result = []
    for index, authored in sorted(ROWS.items()):
        old = original['rows'][index]
        current = dict(authored)
        current['current_evidence'] = [evidence(spec) for spec in current.pop('evidence_specs')]
        current['task_ids'] = current['task_ids'] if current['task_ids'] is not None else old['task_ids']
        if set(current['task_ids'])-tasks:
            raise ValueError(f"Unknown Todo IDs: {set(current['task_ids'])-tasks}")
        result.append(dict(id=old['id'], title=old['title'], original_pointer=old['original_matrix']+'#'+old['json_pointer'],
                           original_matrix=old['original_matrix'], original_json_pointer=old['json_pointer'],
                           original_record_sha256=old['original_record_sha256'],
                           current_evidence=current.pop('current_evidence'), task_ids=current.pop('task_ids'), assessment=current,
                           fresh_execution=False,
                           verification_scope='Individual current source/report inspection; no unchanged suites rerun. Referenced historical tests keep their exact original source scope.'))
    target = Path(__file__).with_name('FINDINGS.json')
    target.write_text(json.dumps(dict(schema=1, baseline=BASELINE, input_count=60, original_packet_count=len(original['rows']), assigned_indices=[0,60],
                                    reviewed_count=len(result), rows=result), ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'{len(result)}/60 individualized rows written (original90-row packet; assigned indices0:60)')

if __name__ == '__main__':
    main()
