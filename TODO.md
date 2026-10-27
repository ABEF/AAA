# Project Todo

**Reviewed 2026-10-27 | Contracts undeployed | Not approved for production**

The single task list for the whole PoPL project. Open a task's acceptance criteria for the detailed release requirements. There is no Todo page on the public website.

**8 To do | 34 In progress | 22 Implemented locally | 1 Not planned**

Implemented means built and locally checked, not deployed or independently audited. This list includes the current local development candidate; some code changes still await their own publication. Publishing this checklist does not publish or qualify that code.

[Feature and evidence reference](docs/IMPLEMENTATION_STATUS.md) | [Release approval record](docs/RELEASE_CHECKLIST.md) | [Update procedure](docs/TODO_WORKFLOW.md)

[Smart contracts](#smart-contracts) | [Backend](#backend) | [Frontend](#frontend) | [Creator tasks](#creator-tasks--zzz-team) | [Testing](#testing--qualification) | [Security](#security--audit) | [Operations](#launch--operations) | [Future migration](#future-migration)

## Smart contracts

Custody, ownership and reward accounting.

<a id="task-lp-eth-settlement"></a>

- [ ] **[Settle holder LP rewards in ETH](docs/LP_ETH_SETTLEMENT.md)** - In progress. LP holder conversion to native ETH is implemented in the local candidate with the user-approved 1% loss cap and separate gas. Includes fixed converter binding, per-NFT native credits, bounded keeper scheduling, history reconciliation and ETH-default claims. Scoped verification covers 142 distinct affected Solidity cases and 33 local journey assertions; real routes/feeds, operating latency/gas qualification and independent release review remain open. Current typed v4 native conversion is implemented; the conversion cap defaults to 1% and governance may set up to 10%, gas separate. Historical verification retains its original fixed-cap source scope.

  <details>
  <summary>Acceptance criteria</summary>

  - Preserve the fixed 80/10/5/5 allocation. Convert only the already-earned individual and collective holder balances; never spend principal, compounding/buyback reserves, quarantines or another NFT backing. Preserve each NFT entitlement before conversion, not current shares/membership at conversion time.
  - User approved a default 1% LP conversion loss (governance maximum 10%) with gas separate on 2026-10-20. The candidate unwraps reviewed WETH exactly or uses pinned routes, fresh independent prices, exact deltas/approvals, caller minimum and deadline. Qualify actual target-chain routes, token/wrapper behavior and complete gas costs.
  - Bind the dedicated converter before sealing; the implementation supports bounded keeper execution, ETH ledger/current-owner claims and reentrancy/lifecycle guards. Qualify and record actual deployment bindings; core sealing alone does not prove conversion readiness.
  - Define ETH-only default claim behavior and explicit source-currency outage recovery. Failed conversion must leave original backed entitlements intact; never display an unconverted token balance as ETH. Preserve dust/fractions, transfer rights, complete handoff/abort/backing and historical claims.
  - Read API, unsigned claims and today-price earnings replay include LP conversion credits without counting them as new income or payout. Qualify full ingestion/lineage, real conversion receipts and stalled/restarted keepers; measure worst-case conversion waiting time across the collection and minimum economic batches.
  - The earlier [source-only claim audit](reports/topup-and-reward-review/ETH_PAYOUT_AUDIT.md) describes the pre-conversion revision. Current candidate evidence belongs in [LP ETH verification](reports/lp-eth-settlement/VERIFICATION.md); local fixtures do not qualify public routes or independent security.
  - Local ETH-only default claims, pending source-currency display, exact native backing/abort and current-owner same-chain handoff are verified in the scoped report. Qualify complete real-market conversion and operating latency before closing this task.
  - Latest approved policy: LP conversion defaults to 1% loss, governance-adjustable up to 10%, gas separate. At the default cap require a cheaper qualified route than the selected pool's approximately 1.101% observed fee. A governance change is deliberate, never an automatic quote fallback.
  - Native V2 venue ETH fees now enter individual/collective indices directly, without conversion. Already converted ETH credits coexist without new-income double counting. ZZZ still requires a cheaper qualified conversion route; the limit defaults to 1%, governance maximum 10%, and gas stays separate.
  - [Current typed v4 and governed limits](docs/TYPED_V4_ROUTES.md) preserve earned per-NFT source/native entitlements; explicit worker profiles and current-setting observations are required. Actual route/feed/keeper qualification remains open.

  </details>

<a id="task-royalty-eth-settlement"></a>

- [ ] **[Qualify ETH settlement for marketplace royalties](docs/ROYALTY_SETTLEMENT.md)** - In progress. Bounded batch ETH conversion and optional-currency activation failure isolation are implemented, with a default 1% execution-loss cap (governance maximum 10%) and gas separate. An opt-in keeper job preserves per-NFT entitlements and existing transaction recovery. Qualify exact Robinhood wrapper/routes/feeds, marketplace receipts, UI/history integration and operating behavior. Current typed v4 native conversion is implemented; the conversion cap defaults to 1% and governance may set up to 10%, gas separate. Historical verification retains its original fixed-cap source scope.

  <details>
  <summary>Acceptance criteria</summary>

  - Keep ETH pricing and verified ETH/WETH as the initial marketplace scope. Verify actual listings/offers/old orders/checkout settlement; a buyer source currency or ETH pricing preference does not prove what reaches the royalty receiver.
  - Independently review and record the fixed converter binding before sealing, exact wrapper/admin/implementation policies, admitted source currencies, route/factory/pool pins, feeds and final runtime inventory. Stablecoin support remains conditional on actual settlement needs; no live route is assumed.
  - Implemented: one guarded conversion for up to 32 NFTs' earned balances, proportional ETH credit to those same NFTs, exact WETH unwrap, at least 99% oracle-valued stablecoin output, strict minimum/deadline, approvals/delta checks and separate keeper gas. Original claims/fractions/quarantines remain intact.
  - Approved and implemented: activation survives optional royalty-token failures; unseen receipts at recovery go to the earlier cohort, then waiting NFTs join future receipts. Expose eligibleFor and deferred/recovered status accurately. Exact unreadable backing still blocks canonical handoff.
  - Review [scoped tests and internal findings](reports/royalty-conversion/VERIFICATION.md). Rehearse automatic dry/live keeper conversion, gas economics, failed currency/route recovery, mixed claims and successor configuration on the target network; do not infer production readiness from local mocks.
  - Implemented [backend conversion and currency-eligibility reporting](docs/ROYALTY_REPORTING.md), verified across owners and complete pinned same-chain predecessors. Integrate the website and qualify live ingestion/availability recovery. RoyaltyConverted is not Claimed or new earnings; only actual payouts increase lifetime paid totals. Independent audit/remediation remains required.
  - This converter applies only to royalties. It neither converts the LP ledger nor guarantees native ETH for all claims; direct source-currency claims remain supported. See [LP ETH settlement](TODO.md#task-lp-eth-settlement).
  - [Current typed v4 and governed limits](docs/TYPED_V4_ROUTES.md) preserve earned per-NFT source/native entitlements; explicit worker profiles and current-setting observations are required. Actual route/feed/keeper qualification remains open.
  - Before marketplace launch, admit reviewed expected settlement currencies. Unknown pre-admission balances are quarantined, not retroactive NFT income; define provenance/policy before proposing any different treatment. Preserve current healthy/native currency eligibility while optional currency faults defer only that registration. [Operator guidance](docs/OPERATOR_MANUAL.md#deep-cleanup-review---2026-10-25).

  </details>

<a id="task-pons-qualification"></a>

- [ ] **[Qualify the selected hookless ETH/ZZZ pool](docs/POOL_SELECTION.md)** - In progress. User selected Robinhood v4 pool 0x5011...afe1b: native ETH/ZZZ, static 1.002% LP fee, no hook; observed combined fee about 1.101%. Runtime-pinned native admission, post-seal static fee-tier destinations and atomic same-actual-pair pool moves are implemented. ETH/WETH are different actual assets and require the separately approved external-custody workflow. Real routes, feeds, gas/operations, inventory and audit remain open.

  <details>
  <summary>Acceptance criteria</summary>

  - Keep the exact PoolKey `(address(0), ZZZ, 10020, 200, address(0))`, recomputed pool ID, creation transaction, confirmed block/hash, dependency runtimes and venue wiring bound to the selected integration. The earlier proposed 0.30% pool and Pons creator agreement are superseded, not current configuration.
  - Review hookless native admission and exact settlement, actual fee collection, harvest-before-increase, source-to-LP entry, moves/exits, donations, adverse callbacks and cleared approvals. Respect the user-approved current2% contribution default and3% ordinary maintenance default, their captured policies and stronger venue/caller limits; gas stays separate.
  - Qualify complete native ETH/fixedZZZ contribution quotes only with independent prices and actual conversion depth. A higher pool fee applies only to swapped amounts but may make some full input routes unavailable; fail closed rather than subsidize execution from incumbents.
  - Qualify actual current-owner ETH settlement, keeper/API configuration, one contribution pool at a time, release inventory and operating gas. Same-actual-pair fee-tier moves require initialized admitted destinations, actual Vault-owned LP and deliberate contribution/route cutover. ETH/WETH conversion is not an atomic moveFunds capability.
  - Retain [historical Pons research](docs/ROBINHOOD_POOL.md) and source-bound old evidence. Use [current evidence](reports/hookless-pool/VERIFICATION.md) for changed-source checks; synthetic fork prices, authorities/VRF and locally initialized destinations are not production service qualification. No public deployment/transaction or existing 8902 reset is authorized.
  - The historical 2026-10-24 internal audit fixed fee-aware planning for both native and ERC20 v4 destinations, under its then99% contribution/3% maintenance defaults. Four new regressions pass;58 affected existing cases passed, and only two corrected fixture cases were rerun successfully. Read reports/daily-security-20261024/REVIEW.md; actual markets/services and independent audit remain open. That historical source scope does not establish current execution: the current default contribution floor is98% at2%, with captured caller/venue guards; limits are governance-bounded as documented.
  - The standalone pool observer now enforces reviewed runtimes, strict bounded replies, canonical hash state selectors and atomic secret-safe output. Nine mocked RPC/filesystem cases pass; qualify real provider support separately. It does not qualify token proxy authorities, feeds or liquidity economics.

  </details>

<a id="task-activation-assets"></a>

- [ ] **[Qualify ETH and ZZZ contributions only](docs/ACTIVATION_ENTRY.md)** - In progress. Contract admission is restricted to native ETH and the explicitly reviewed ZZZ identity. Qualify their actual dual-price policies, full activation/$5 growth execution, selected pool depth and separate gas. USDC, USDG and WETH are not user inputs; royalty currencies are separate.

  <details>
  <summary>Acceptance criteria</summary>

  - Independently verify $100 original source value with the captured marginal actually deployed-LP floor (98% at the current2% default), separate network gas, incumbent NAV pricing, all conversion-leg costs, callbacks, pending/dust barriers, top-ups and nonredeemability. Review the immutable Entry's exact owner/calldata context, inactive approval window, Registry-only valuation and callback cleanup; a post-conversion pair value cannot replace original source value.
  - Review ETH/ZZZ source-to-LP routing through the implemented Entry: exact token provenance, actual liquidity, fresh source prices, immutable binding/runtime, original-source budget, exact approvals and complete append-only route history. Native V2 ingress is the actual asset-zero ETH currency, not a wrapper substitution; explicit WETH routes retain their separate reviewed semantics. No third contribution currency is admitted; unsigned quotes alone do not establish qualified execution.
  - Use the [integration campaign](docs/INTEGRATION_CAMPAIGN.md) and [read-only observations](reports/activation-route-observation/VERIFICATION.md): one $1 conversion snapshot is not $100 activation qualification. Include subsequent LP costs in the same captured contribution limit, separate gas, qualified ZZZ pricing and complete operation simulation. Public transaction testing has not run; the isolated $1 build remains local only.
  - Track team-dependent feed, market and liquidity questions in [Creator tasks / ZZZ team](TODO.md#creator-tasks--zzz-team). Team responses do not replace independent route/feed qualification.
  - Implemented: fixed $100 activation / $5 increase floors in original-source Entry and the direct Vault helper, with higher pool minima retained. Qualify complete $5 routes at the captured marginal-LP floor (98% at the current2% default) and separate gas, including real token units, depegs and execution costs. See [minimums and operator controls](docs/CONTRIBUTION_MINIMUMS.md).
  - Native V2 accepts actual ETH at asset zero with explicit policy and independent feed; exact Entry/Vault/manager call values are checked. Native V2 read/preparation profiles do not require WETH for ETH. Old local fixtures and prior WETH route evidence retain their original scope; Uniswap v3 routes cannot output native ETH directly; this venue-version limit is distinct from accounting3.
  - The [two-source guard](docs/PRICE_SECURITY.md) is implemented, not live-qualified. Freeze source/pair prices and limits before any source pull/conversion; validate upper-input/lower-marginal-LP floors and final fingerprints/spot. Close [dual-source qualification](TODO.md#task-dual-price-qualification) for every enabled input and both LP currencies.
  - The [October25 selected-fee local composition](reports/preproduction-audit-20261025/REVIEW.md#a-07-thin-market-activation-feasibility-remains-open) exposes an honest thin-market native activation that retains about$99.38 but deploys only$98.85 of$100; the then-99% guard reverted safely. This is historical policy evidence, not a current2%/98% quote or feasibility result. Qualify full-trace feasibility at actual liquidity/ticks/fees before wallet review, preserve exact rollback and existing approvals, and assess bounded post-swap ratio correction only if it can improve deployed LP within the same captured budget. Never weaken the floor or count incumbent/idle assets as new LP; deeper mock liquidity is not launch qualification.
  - [Dated service/route evidence](reports/release-services-20261025/feeds-routes/VERIFICATION.md): fresh Pinax reads returned429 twice and official RPC403 before a usable snapshot. No fresh route quote/depth or cheaper ZZZ conversion is qualified; transport failure is not market absence. Preserve bounded retries and fail closed.
  - [Historical simplification audit](reports/simplification-20261025/REVIEW.md) retains its exact source scope. Fresh source binds ETH/fixedZZZ only and native ETH/ZZZ LP admission; issuer/chain custody executors are removed. Governance may end LP and return actual ETH+ZZZ to holders; token identity is not replaceable.

  </details>

<a id="task-fair-draw"></a>

- [ ] **[Fair assignment of prepared NFT designs](docs/NFT_METADATA.md#random-reveal)** - In progress. The fixed 1,000-entry artwork inventory and draw without replacement are implemented. Verifiable randomness assigns a remaining prepared design; it does not generate images or reroll assigned rarity, palette or pattern. Qualify the live randomness service.

  <details>
  <summary>Acceptance criteria</summary>

  - Independently verify actual supported proof-verifying coordinator code/key/subscription/confirmations/gas and service availability on the deployment chain. An ABI or mock is not verification.
  - Stage real requests, out-of-order callbacks, strict mint-order reveal, subscription outages, reorg/finality and permanent early-request blocking recovery. No cancellation/reroll/admin bypass exists.
  - Verify canonical sealing rejects missing randomness configuration; verify content root and every artwork/metadata path against an independently reviewed immutable catalog.
  - [AUD18-02](reports/daily-security-20261018/REVIEW.md): user selected qualified/funded reliable provider plus stopping new minting and draining original ordered draws before collection replacement. A confirmed readiness endpoint is implemented; qualify actual funding, request latency, alerts and original-provider outage resolution. No reroll/pending-request carry/provider-swap path; a permanently unanswered request still blocks whole-collection replacement, not ordinary LP migration. See [operator policy](docs/OPERATOR_MANUAL.md#mint-and-metadata).
  - The independent mint-only governance pause and confirmed pause status are implemented; rehearse provider outage, original fulfillment, ordered reveal and deliberate resume. No reroll/provider swap. See [operator controls](reports/operator-controls/VERIFICATION.md).
  - Revealed metadata displays fixed rarity weight1/2/3 even while dormant, with separate royalty_activated flag. Unknown draws stay Unrevealed; economic ledger eligibility remainszero until activation, with no retroactive royalties. Fixed artwork/rarity quotas and paths are unchanged.
  - [Current mint/VRF profile1](docs/MINT_INTEGRATION_QUALIFICATION.md) binds exact subscription-v2.5 selector, two words, nonzero lane, same original request/result recovery through refund/expiry, negative-proof/callback evidence and external funding. Actual RH-VRF/D20 compatibility remains unqualified; no guard relaxation, adapter or provider selection is implied.

  </details>

<a id="task-custody-composition"></a>

- [ ] **[Qualify collective LP return to NFT holders](docs/HOLDER_COLLECTIVE_EXIT.md)** - In progress. Implemented fresh accounting4/custody3: irreversible governance LP shutdown, actual ETH+ZZZ share allocation, bounded direct current-owner payouts and rejecting-recipient fallback. NFTs retain transfers, future royalties and old earned rewards. External principal/royalty custody exits removed. Actual integration, gas/operating rehearsals and independent review remain open.

  <details>
  <summary>Acceptance criteria</summary>

  - Only governance can start paused collective exit; no normal holder withdrawal or operator-selected recipient. Terminal before/after guards prevent reopening principal or canonical replacement, including callback/unpause attempts.
  - Final harvest retains fixed80/10/5/5. Principal includes actual close proceeds, attributed idle and pending5%compound. Previously earned LP/royalty liabilities, buyback reserve, quarantine and prefunds remain separate.
  - Exact cumulative share allocation in immutable mint order conserves every raw unit across all buckets and1,000NFTs. Transfers preserve unpaid rights; duplicate claims/pushes cannot pay twice. Failed/gas-consuming recipients remain backed and cannot block others.
  - Production LP admission permits native ETH/fixedZZZ only; no new pool may create an incompatible collective-return bucket. Same-pair pool moves/parking remain before exit.
  - Qualify accounting4/custody3/canonicalV5 read/preparation/website profile, events/metadata/history and separate principal balances. Preserve historical codecs/Anvil/journals; never count principal payout as earned fees.
  - Run affected adversarial execution/normal size checks and review receipts. Real target-chain closure/payout gas, failed token/venue recovery, operator batching, service acceptance and independent audit/remediation remain required.
  - Optional keeper principal_distribution automates only post-close allocation/direct delivery, with reviewed NFT/module/runtime pins, existing signer/journal/gas/day limits and on-chain paid truth. Governance alone starts/closes LP. Source job is disabled by default; qualify actual funded service rollout and timing. No holder action is required for successful normal delivery.

  </details>

<a id="task-opensea-mint"></a>

- [ ] **[Qualify OpenSea primary mint integration](docs/MINT_INTEGRATION_QUALIFICATION.md)** - In progress. Actual interface/payment mismatch is identified and the current release gate rejects a fabricated primary-drop approval. Implement and qualify a recipient-aware OpenSea integration before sealing: buyer pays0.05ETH gross, actual platform fee deducted from recipient proceeds, gas separate. Current direct Vault mint remains unchanged.

  <details>
  <summary>Acceptance criteria</summary>

  - Code review 2026-10-23: current Vault.mintDormant mints to msg.sender and the NFT accepts mint only from Vault; no SeaDrop interface is implemented. Verify buyer recipient, payment/fee handling and the exact supported Robinhood drop integration before adding any mint adapter. General marketplace chain support does not prove primary-drop support.
  - Verify chain/product support and the required interface against the exact proposed OpenSea integration. A listing/secondary sale or direct Anvil mint is not primary-mint acceptance.
  - Preserve canonical NFT identity, 1,000 cap, 0.05 ETH gross buyer price and actual platform-fee/net-recipient conservation, exact rarity draw/VRF, zero LP at mint, mint pause/lifecycle and atomic rollback. Check NFT ownership when the caller is a marketplace intermediary; review any adapter/core change before sealing.
  - Rehearse a supported marketplace mint, payment, receiver callback/rejection, reveal and pause/restart; record receipts and exact verified collection URL. Keep production website mint preparation disabled.
  - Official OpenSea Robinhood chain support is distinct from custom primary-mint/SeaDrop compatibility. [Current research](reports/real-service-readiness-20261025/RESEARCH.md) leaves actual product/contract/caller/recipient/royalty and random-draw integration unqualified; no marketplace mint authority or mint adapter was silently added.
  - Decision2026-10-25:0.05ETH is total buyer mint price; the recipient receives the remainder after the actual platform fee, gas separate. No actual fee is selected. [Current qualification](docs/MINT_INTEGRATION_QUALIFICATION.md) is hardblocked by code-owned direct-mint capability; runtime presence/general chain support cannot implement SeaDrop or qualify primary mint.

  </details>

<a id="task-native-custody-recovery"></a>

- [ ] **[Qualify native ETH holder return and failed-payout recovery](docs/NATIVE_ETH_ARCHITECTURE.md)** - In progress. Native ETH/fixedZZZ accounting4 closes to per-NFT holder backing without WETH, swaps or USD-feed dependence. Owner-selected fallback handles rejected direct payouts; no external-custodian recovery remains.

  <details>
  <summary>Acceptance criteria</summary>

  - Verify final fees/pending compound and exact native/token deltas; no prefund subsidy or reserve mixing.
  - Qualify per-recipient gas, callback/rejection/token fault isolation, current-owner fallback and complete backing/remaining balances on the target chain.
  - Old native-custody reports remain historical; qualify the new accounting4/custody3 code independently before approval.

  </details>

<a id="task-post-seal-configuration"></a>

- [ ] **[Keep operational settings configurable after sealing](docs/POST_SEAL_POLICY.md#configuration-boundary)** - In progress. Bounded future VRF tuning, buyback ceilings, typed v3/v4 conversion routes and governance-adjustable loss limits are implemented locally. Defaults are 2% / 1% / 3%, hard maximum 10%, immediate authority, captured in-progress/approved minima and separate gas. Actual route/service/native inventory qualification and independent review remain open before sealing.

  <details>
  <summary>Acceptance criteria</summary>

  - Inventory every fixed setting and setter. Preserve ETH/fixed-ZZZ source enable/disable, separate royalty-asset admission, reviewed route/feed/pool/role/range changes after sealing, exact authorization/events/bounds, dependency checks, pending-operation handling and canonical locks. No new contribution currency, post-seal ZZZ identity replacement or governance waiting period is introduced.
  - Implemented NFT.setRandomnessRequestSettings(uint16,uint32) affects only future confirmations (3-200) and callback gas (200,000-10,000,000). Coordinator, key/lane, subscription and payment mode remain fixed; pending request provenance, ordered exact-quota draws and immutable results persist. It cannot repair a past callback, retry, reroll or select traits. Independently qualify actual provider limits and operator recovery.
  - Implemented Buyback.setOperatingTradeUSD(uint256) selects zero through immutable maxTradeUSD, defaulting to that hard maximum. Zero stops execution before oracle/reserve calls; both setters allow ordinary pause and reject preparation/canonical locks/reentry. Resize/remove keeper tasks after lowering/stopping. Allocation and reserves stay fixed; the separately approved governed execution policy is described below.
  - Keep ownership, revealed rarity/artwork, accrued balances, backing and allocation guarantees protected. No reset, deletion, arbitrary calls/sweep or holder redemption. New compatible code uses reviewed handoff, not silent reinterpretation of old state.
  - [Typed v4 routes](docs/TYPED_V4_ROUTES.md) are implemented through immutable fixed-parent single-hop helpers with exact native/ERC20 settlement and explicit preparation/keeper profiles. Actual routes, feeds and providers still require qualification; no arbitrary hook/router/recipient/sweep.
  - [Governed execution-loss policy](docs/EXECUTION_LOSS_POLICY.md): Budget setLossLimits(contribution,maintenance) and each converter setConversionLossBps select 0..1000 bps. Defaults 200/100/300. Captured operation policies and original custody approval floors persist; raw emergency remains separate. Verify current settings and reconcile pending reviews; no cumulative cap is added.
  - [Native V2 preflight](docs/PRODUCTION_PREFLIGHT.md) is implemented as schema-5 inventory and read-only same-block observations. Complete the actual pinned deployment, route/feed/service and independent review records; implementing a checker does not qualify its inputs or authorize release.
  - Buyback operating/max USD ceilings now use upper-bound input value rounded upward under pricingV2, preventing accepted feed disagreement from exceeding the reviewed ceiling. Existing conservative execution floor, fixed allocation, route and authority controls remain; divergent-price batches may need reducing.

  </details>

<a id="task-reviewed-contribution-policy"></a>

- [ ] **[Qualify caller-bound activation review policy](docs/EXECUTION_LOSS_POLICY.md#review-time-policy-binding)** - In progress. Reviewed Entry V1 and Pricing bind the caller cap; the matching current3 website reader/unsigned-review profile now checks exact policy/calldata/actual-LP provenance. Qualify actual deployments/routes/providers through poplint without enabling public signing or relabeling historical deployments.

  <details>
  <summary>Acceptance criteria</summary>

  - [Implementation and scoped verification](reports/comprehensive-improvement-20261025/VERIFICATION.md): executeReviewed(Request,uint16), 0..1000bps caller maximum, captured governed cap <= caller maximum before pulls/conversion; tighter governance may apply, wider policy rejects. Existing final callback/price/physical-LP checks remain.
  - Current pricing-V2 activation preparation and schema-5 inventory require explicit review_policy_version1 and matching Entry/Pricing getters, runtime pins, exact selector/trace and provenance. No missing-getter, direct-Vault or old-selector fallback can claim this guarantee. Historical pricing1/local profiles and saved journals retain their original semantics.
  - The current3 website/unsigned-review implementation now matches this ABI; qualify actual runtime/API/provider and browser-wallet integration before any separately authorized public signing. Historical schema1 retains its original1%/old-selector semantics; published native2 supports reviewed Entry1 and a captured governed cap but is still incompatible with accounting3. Preserve explicit profile rejection. Signer remains Anvil-only, public DEPLOYMENT null; no service or chain upgraded.
  - The maximum does not freeze price/range/strategy/dependency configuration or remove immediate-governance/custodian trust. Keep raw caller minima, expiry, fresh two-source prices, exact actual LP/balances, conservative input/output bounds and capture checks. Do not describe direct owner-Vault calls as reviewed-Entry calls.
  - Current3 website implementation: explicit schema3 manifest, accounting3/governance2/fee1/localV4 runtime/domain bindings and ETH/fixedZZZ-only inputs; actual HTTP schema2 DTOs cover six activation/growth/approval/claim reviews. The final affected scope has451JS passes including46new methods; earlier overlapping runs are not additional coverage. Evidence: [current3 integration](reports/current3-website-20261026/VERIFICATION.md). Poplint has its own build/root/configuration; no current public deployment/API is fabricated and signing stays disabled.

  </details>

<a id="task-lp-only-simplification"></a>

- [x] **[Simplify the current ETH/ZZZ release](docs/SIMPLIFIED_RELEASE.md)** - Implemented. Fresh accounting4 keeps eight-word local Positions/direct governance2 and removes external custody recipients/royalty drains alongside prior retired bridge/creator/scheduler paths. Canonical holder-exit V5 is explicit; old deployments/readers/journals remain separate.

  <details>
  <summary>Acceptance criteria</summary>

  - Source changes use a new LP-only canonical schema and explicit service profiles, preserving historical deployments/journals and old event readers. Retired fixtures are archived rather than counted as current passes. See the [audit](reports/simplification-20261025/REVIEW.md).
  - [Verification](reports/simplification-20261025/VERIFICATION.md):89 distinct Solidity behaviors across two source scopes,40 backend plus6 API/keeper scoped methods,122-input ABI/AST and36 normal object gates. Current real fork qualification is blocked until its retired wrapped fixture is replaced; actual services and independent audit remain open. Access exact release constructor arguments still need qualification (29-byte minimal margin).
  - The [residual-code review](reports/obsolete-code-20261025/REVIEW.md) removes unconsumed Registry wrapper records and orphan creator-payment measurement tools, aligns current keeper examples and corrects stale operating/audit requirements. Historical event/journal readers and actual converter wrapper checks remain; no external release gate closes. Use that report for final source scope and verification rather than adding earlier counts.
  - [Day consistency audit](reports/daily-security-20261025/REVIEW.md): one fixed ZZZ now binds source, native admission, immutable Buyback and normal exit; the old buyback retarget setter is removed. Registry admission prevents mismatched native identity. This is fresh-deployment source only; 28 distinct selected behaviors across recorded fixture scopes, 35 indexer methods and 36 normal gates are source-scoped, not external qualification.
  - [Remaining-architecture review](reports/architecture-pruning-20261025/REVIEW.md) and [scoped verification](reports/architecture-pruning-20261025/VERIFICATION.md): current Position3/localV4/direct governance2 are explicit.49 distinct selected Solidity behaviors and512 distinct Python methods pass across recorded source scopes; neither count is a fresh full-regression or real-service approval. Preserve old profiles/journals and unsupported cross-codec boundaries.
  - [Auditability refactor](reports/auditability-refactor-20261025/REVIEW.md) and [verification](reports/auditability-refactor-20261025/VERIFICATION.md): shared private settlement, read-only v3 identity checks, separate converters over a neutral abstract base, named phases and explicit private NFT/bucket identifiers. No new authority, economic policy or deployment profile. Compiler equivalence and affected execution retain exact scopes; actual services and independent audit remain open.
  - [Deep cleanup review](reports/deep-cleanup-20261025/REVIEW.md) and [verification](reports/deep-cleanup-20261025/VERIFICATION.md): inherited royalty balance/error reuse, guardian and initial role logs, dependency-bound evidence and obsolete native/outage fixtures. 32 scoped Solidity methods,41 Python methods and37 normal gates pass; 75 production/265 AST inputs are explicit. No economic/authority/storage change; new logs and ABI metadata differences are documented. Actual release gates remain open.
  - [Independent day audit](reports/day-readiness-20261025/REVIEW.md) reconstructs all24 reachable Paris-day commits and independently checks reference35007db claims. No production Solidity change; native custody API/replay, contradictory saved evidence and two native-test sensitivity gaps are corrected. See exact fresh/reused scopes and open [release gates](reports/day-readiness-20261025/READINESS.md).

  </details>

<a id="task-immediate-governance"></a>

- [x] **[Immediate governance without timelocks](docs/GOVERNANCE.md)** - Implemented. The governance wallet now calls target modules directly. No timelock, scheduling/executor roles or generic controller executor remains. Two-step no-delay governance handover, guardian/keeper separation, immutable bindings and lifecycle/custody guards remain.

  <details>
  <summary>Acceptance criteria</summary>

  - [Scoped evidence](reports/immediate-governance/VERIFICATION.md): 228 distinct affected Solidity passes, 142 configuration passes, 30 size gates and fresh internal static review. No deployment or independent approval; there is no advance warning window for governance changes.
  - [Remaining-architecture review](reports/architecture-pruning-20261025/REVIEW.md) and [scoped verification](reports/architecture-pruning-20261025/VERIFICATION.md): current Position3/localV4/direct governance2 are explicit.49 distinct selected Solidity behaviors and512 distinct Python methods pass across recorded source scopes; neither count is a fresh full-regression or real-service approval. Preserve old profiles/journals and unsupported cross-codec boundaries.

  </details>

<a id="task-operator-stop-controls"></a>

- [x] **[Independent mint and pool stop controls](docs/OPERATOR_MANUAL.md#stop-controls)** - Implemented. Governance can pause new NFT mints independently and disable pool deposits/operations without token, price or venue calls. Reopening still requires full pool validation; existing rights and lifecycle guards remain. The confirmed API reports mint pause separately.

  <details>
  <summary>Acceptance criteria</summary>

  - [Scoped verification and internal review](reports/operator-controls/VERIFICATION.md) cover authority, outage/reopen, callback rollback and economic continuity. Production service/authority rehearsals and independent audit remain required; no retroactive change to sealed contracts.

  </details>

<a id="task-price-security"></a>

- [x] **[Dual-source USD checks and factual LP contribution security](docs/PRICE_SECURITY.md)** - Implemented. Undeployed pricing-V2 implementation requires two reviewed USD sources per priced asset. Entry freezes source/pair prices and contribution/venue limits before transfers/conversion; a fixed Oracle-created companion checks consistent NAV, conservative upper-input/lower-LP execution floors and unchanged final fingerprints/spot alongside exact physical LP/balance checks. Live source qualification and independent audit remain open. User-selected source disagreement tolerance is 3% (300 bps); the separate default 2% contribution execution floor still applies.

  <details>
  <summary>Acceptance criteria</summary>

  - [Implementation and source-scoped verification](reports/price-security/VERIFICATION.md), [internal review](reports/price-security/REVIEW.md): distinct sources/runtime pins/declared independence, valid rounds/decimals/ages, bounded disagreement and no single-source/spot/peg fallback. Declared independence and matching answers do not prove market/provider independence.
  - Existing nonzero historical compound keeps its initial mark. Newly discovered old-currency compound is first marked at the final checkpoint only for incumbent backing; it cannot pay the entrant loss floor. Preserve shares, old rewards, exact token/native spending and atomic failure rollback.
  - Current preflight/preparation/earnings use explicit pricing_version 2, full append-only policies, raw confirmed-block observations and all 15 helper bindings. Historical single-source profiles retain old deployment/epoch semantics. No website, existing local-chain/journal, public signer or monitor change follows.
  - The unchanged cold 12M gate initially failed at12,394,559 gas; skipping irrelevant epoch-zero historical scans repairs maximum-index activation to11,864,627 gas. This is local substituted-feed/venue evidence, not target-chain provider qualification. Historical epoch>0 checks remain.
  - [On-chain safety/cost review](reports/onchain-safety/REVIEW.md) and [scoped verification](reports/onchain-safety/VERIFICATION.md): bounded sequencer calls, fresh memory-only Strategy prices, packed contribution bounds and static-loop reward contexts preserve accounting/rounding/final guards. 145 distinct Solidity cases, 83 backend checks and 37 normal object gates are source-scoped; actual dependencies, target-chain gas and independent audit remain open. No new authority or automatic fallback.
  - 25October documentation corrects the post-seal recovery setter to setDualFeed and distinguishes public read charges/network gas/custom provider costs plus historical reference prices. Source pairs remain unset; no implementation test or provider qualification is inferred from this update.

  </details>

<a id="task-nft-lifecycle"></a>

- [x] **[Minting, activation & NFT ownership](src/ZZZVault.sol)** - Implemented. 1,000-NFT cap, 0.05 ETH mint and $100 gross-value activation with a governed deployed-LP floor (98% by default, maximum 10% execution loss). Rights follow the NFT.

<a id="task-reward-ledgers"></a>

- [x] **[LP fees & separate royalty shares](docs/ECONOMICS.md)** - Implemented. 80 / 10 / 5 / 5 funded LP allocation with documented raw-unit dust settlement; equal collective shares. Actual royalties go to active NFTs at x1 / x2 / x3, separately from LP shares. These ledgers currently preserve payout currencies; ETH-only LP settlement is a separate open task.

  <details>
  <summary>Acceptance criteria</summary>

  - Allocation occurs when actual local LP fees are harvested; the equal collective denominator is activated membership at that receipt, not the number of unclaimed NFTs. Claims pay already funded entitlement and never reallocate, compound or buy back. [Timing and arithmetic](docs/ECONOMICS.md#allocation-reinvestment-and-claim-timing).
  - [Reward review](reports/reward-allocation-20261026/REVIEW.md) and [verification](reports/reward-allocation-20261026/VERIFICATION.md): two new Solidity methods pass, including1,000 randomized early/deferred claim schedules with four NFTs, two currencies, dust/fractions, activation, top-up and transfer. Exact owner/collective/reserve isolation and total funding conservation hold in scoped fixtures; no production Solidity or economic rule changed.
  - Keeper compounding and buyback remain separate guarded jobs; contributions/rebalances can also reinvest designated compound. Sample standalone compound is disabled and buybacks are empty. Actual routes/fixed-ZZZ burn semantics, economical batch thresholds, gas/latency/backlog monitoring and operating qualification remain in the linked keeper/conversion release tasks.
  - [Actual-v4 outage proof](reports/reward-resilience-20261026/VERIFICATION.md) collects real swap fees and pays both owners while fixture prices are stale, with no LP/share/reserve loss. No production Solidity/rate/right changed; unchanged allocation/claim-order evidence is reused with exact source pins. Actual token/feed/route/burn behavior and independent qualification remain open.

  </details>

<a id="task-shared-custody"></a>

- [x] **[Shared LP, maintenance & custody controls](docs/ARCHITECTURE.md)** - Implemented. One shared LP per pool/strategy serves many NFTs. The local four-historical-bucket safety bound, permanent allocations, pool-level upkeep, governance approvals, parking and guarded resumption are implemented. Ordinary rebalances now also enforce the user-approved 3% aggregate fixed-start-price cap, retaining existing guards and 5% idle; gas is separate. Approved range changes can now trigger the ordinary keeper rebalance at a flat price after cooldown; successful application clears the mismatch. The registry now restricts new activations/top-ups to one contribution pool at a time, while preserving governed future switches and historical custody.

  <details>
  <summary>Acceptance criteria</summary>

  - Use [the one-pool switch procedure](docs/OPERATOR_MANUAL.md#one-contribution-pool-at-a-time). Verify initial ZZZ/ETH selection, full destination validation, exact atomic switch/rollback and operator/runtime pins. Local evidence does not approve real destination liquidity or future-chain transport.
  - [Incumbent dust liveness fix](reports/daily-security-20261025/REVIEW.md): historical admitted currencies come from stored Registry identity, not unavailable old venue accounting. Exact nonzero dust funding/settlement and current-pool validation still apply; newcomers receive no earlier rewards.
  - [Remaining-architecture review](reports/architecture-pruning-20261025/REVIEW.md) and [scoped verification](reports/architecture-pruning-20261025/VERIFICATION.md): current Position3/localV4/direct governance2 are explicit.49 distinct selected Solidity behaviors and512 distinct Python methods pass across recorded source scopes; neither count is a fresh full-regression or real-service approval. Preserve old profiles/journals and unsupported cross-codec boundaries.

  </details>

<a id="task-typed-v4-conversion"></a>

- [x] **[Typed v4 contribution and reward-conversion routes](docs/TYPED_V4_ROUTES.md)** - Implemented. Parent-bound static hookless single-hop conversion is implemented for Entry and earned LP/royalty balances, with actual native settlement, exact prefunds/callback guards and explicit backend/keeper profiles. Real market, feed and operating qualification remain under the existing input/service tasks.

  <details>
  <summary>Acceptance criteria</summary>

  - [Scoped evidence](reports/typed-v4-routes/VERIFICATION.md) separates actual installed-core conversion and real Vault/ledger flows from LP/feed/VRF/provider substitutes. No arbitrary executor, hooks, sweep, public signing or live route approval.

  </details>

<a id="task-governed-loss-limits"></a>

- [x] **[Governance-adjustable execution-loss ceilings](docs/EXECUTION_LOSS_POLICY.md)** - Implemented. All three categories are configurable after sealing by immediate governance, up to a hard 10%. Defaults stay 2% contribution, 1% conversion and 3% maintenance. Captured policy, original pending custody floors, independent caller/venue guards and separate gas remain.

  <details>
  <summary>Acceptance criteria</summary>

  - Budget.setLossLimits sets both contribution/maintenance values; each converter.setConversionLossBps is separate. Values are 0-1000 bps, with events, authorization/lifecycle guards and focused callback/floor/approval tests. Stronger venue/caller minima can still block execution.

  </details>

<a id="task-liquidity-placement-idle"></a>

- [x] **[Bounded placement and attributed-idle reinvestment](docs/IDLE_AND_DUST.md)** - Implemented. Implemented candidate uses at most two actual-state balancing passes, skips precision corrections, and reinvests attributed idle through guarded compound with a successful-operation cooldown. Contribution default is now2%; conversion1% and maintenance3% are unchanged. Scoped installed-v4, rollback, cooldown and normal-size verification is recorded; real routes, depth/gas economics and independent qualification remain open.

  <details>
  <summary>Acceptance criteria</summary>

  - [Scoped verification](reports/liquidity-operations-20261025/VERIFICATION.md) must prove the former shallow selected-fee case at an explicitly retained1% cap, thinner-market rejection, second-swap rollback and actual idle-only LP growth. Preserve exact principal shares, incumbent fees, royalties, prefunds, approvals and fixed-price budgets; do not count idle as marginal deployed LP.
  - Keep classified reward fractions/division dust, compound/buyback and quarantined/unknown funds backed. No universal clear/sweep, operator dust recipient, principal redemption or claim haircut. Contribution default2%, conversion1%, maintenance3%, hard governed maxima10%; gas separate.
  - Qualify full actual target-chain routes, independent sources, real depth/ticks, maximal cold gas and economic thresholds. Substituted maximum-state gas and actual two-pass small-fixture gas are separate evidence; do not combine them into a production worst-case claim.

  </details>

<a id="task-adaptive-range-policy"></a>

- [x] **[Reviewed keeper selection of ZZZ-price ranges](docs/RANGE_POLICY_UPDATES.md)** - Implemented. Explicit version1 orientation supports ZZZ priced in ETH while preserving legacy raw-ratio profiles. Default-disabled governance policy lets the keeper select only±25%/±50% using reviewed displacement, configuration and cooldown rules; ordinary guarded rebalance applies physical ticks separately. Scoped range/fuzz, API/keeper and normal-size verification is recorded; no production thresholds or service activation are assumed.

  <details>
  <summary>Acceptance criteria</summary>

  - Require explicit orientation/profile/runtime pins and reviewed policy hash. Inverse endpoints round outward. Bind every non-width pool parameter; changed configuration, disabled/paused/canonical/preparation states, stale prices, cooldown and unapplied previous ticks block automatic selection.
  - Keeper supplies a pool only, never arbitrary width/config/assets/recipient or a force-rebalance bypass. Selection is one transaction; actual normal rebalance is separate and retains3% default captured maintenance, caller/venue minima, actual backing and idle guards.
  - Qualify threshold/cadence and narrowing/widening economics, MEV and turnover on actual markets. The signal is displacement from the last applied center, not continuous volatility or proof of sustained calm; a ten-minute poll is not an execution guarantee.
  - Use range_policy_version1 in API/schema5 current inventory and exact Strategy pins, complete reviewed/observed per-pool metadata and typed events. Historical version0 keeps its original raw semantics and getters; no silent migration of journals or deployed contracts.

  </details>

<a id="task-callable-reference"></a>

- [x] **[Explain callable contract reads and writes](docs/CONTRACT_FUNCTIONS.md)** - Implemented. Source-bound reference covers31 contracts/608 functions,31 constructors/13 receive hooks with exact types, inputs, outputs, purpose and authority. Removed selectors and direct-governance procedures are reflected; internal-only helpers are not operator entrypoints.

  <details>
  <summary>Acceptance criteria</summary>

  - Derived from the current43-source compiler ABI and normal size evidence; inherited ERC721/governance methods are included, internal-only libraries excluded. No function is executed by documentation generation.
  - Keep editable explanations and ABI/source snapshot in sync after source, behavior, permission, input or output changes. Run python scripts/generate-function-reference.py --check; missing purpose/caller/payable-value/input notes or stale generated/source data must fail. A correct signature is not transaction authorization.
  - See the [operator appendix](docs/OPERATOR_MANUAL.md#callable-contract-reference) and [scoped verification](reports/release-services-20261025/function-reference/VERIFICATION.md). Normal verification now checks both Todo and this reference before running broader checks; no fresh full CI pass is claimed.
  - Current source-bound catalog is31contracts/643functions. The removed Buyback setter/event, immutable getter and matching setup order are reflected in exact compiler/reference notes. Maintain all callable purpose, authority and input/output explanations for future changes.
  - [Remaining-architecture review](reports/architecture-pruning-20261025/REVIEW.md) and [scoped verification](reports/architecture-pruning-20261025/VERIFICATION.md): current Position3/localV4/direct governance2 are explicit.49 distinct selected Solidity behaviors and512 distinct Python methods pass across recorded source scopes; neither count is a fresh full-regression or real-service approval. Preserve old profiles/journals and unsupported cross-codec boundaries.
  - Snapshot3 now enforces independent bytecode/constructor limits, coherent raw artifact/status/freeze bindings and a closed stored compiler source inventory. 31 distinct affected methods pass across three scopes; actual matching75-source artifacts regenerate31contracts/608functions/13receive hooks without production recompilation. Dynamic actual release arguments remain unqualified; self-consistent metadata is not independent build/test authentication. Strict outer integer schemas and fixed-point ABI types are validated; the last source has three targeted passes, not a fresh31-method rerun.

  </details>


## Backend

The data and services behind the app.

<a id="task-activation-quotes"></a>

- [ ] **[Complete activation & top-up quotes](docs/ACTIVATION_PREPARATION.md)** - In progress. Full Entry activation/top-up preparation is implemented and locally verified: original-source-to-LP simulation, governed marginal-deployment floor (2% loss by default), exact unsigned calldata and gas separate. Actual production routes, providers and fee semantics still need qualification. Confirmed range and rebalance eligibility/cooldown warnings are included; out-of-range entry remains allowed under normal execution guards. Range-update and price-trigger causes are now distinguished at the confirmed snapshot. Explicit routing version2 supports typed native/ERC20 v4 and reads the current governed contribution cap (2% default, 10% hard maximum). Legacy profiles keep fixed semantics; no fallback.

  <details>
  <summary>Acceptance criteria</summary>

  - Implemented: typed owner request, exact source admission/route/feed/runtime/module pins, one confirmed canonical hash, two full Entry simulations, contract-budget/share/event/LP reconciliation and tighter final conversion/liquidity minima. Missing allowance produces only an exact approval/reset draft and requires re-preparation after confirmation; no state overrides, signer or broadcast.
  - Qualify actual native ETH/fixed ZZZ original-source-to-selected hookless ETH/ZZZ paths and reviewed feeds at $100 gross value, with the current governed marginal-LP floor (98% by default) and gas separate. Current local fixtures and trace/budget probe do not constitute a complete live-route rehearsal. Reject or revert when the limit cannot be met; reverted transactions can still spend gas.
  - Verify intended RPC providers support canonical-hash callTracer with logs and complete gas estimation. Approve network fee accounting (including every applicable data/L1 component), source/proxy/storage pins and actual gas/latency bounds. No latest/state-override fallback on unsupported/stale/future/reorg responses.
  - Integrate approval confirmation/requote and freshly validated wallet signing/receipts under the frontend task. Display NFT.currentLPValue at the confirmed block separately from marginal new LP and claimable LP/royalty balances; unavailable current value must stay unavailable. Local HTTP preparation is loopback-only; hosting remains under hosted services.
  - Qualify range/timing output against real StateView ticks and current physical LP IDs. Show cooldown end or eligible-now/waiting state; unknown/stale keeper next-check and execution times must remain unavailable. Reprepare after LP/range/policy changes; Entry calldata has economic minima/deadline, not an LP-version lock. See [dynamic liquidity](docs/DYNAMIC_LIQUIDITY.md).
  - Implemented request-wide monotonic/expiry/RPC budgets and supervised HTTP workers; [scoped remediation](reports/api-work-limits/VERIFICATION.md) addresses AUD18-03. Qualify actual Linux/RPC/trace workloads and ingress limits under [host-services](TODO.md#task-host-services); keep final canonicality and on-chain deadlines.
  - Preparation now checks the $5 top-up / $100 activation floor and any higher pool minimum before approvals or traces. [Focused evidence](reports/topup-and-reward-review/VERIFICATION.md) covers exact/below limits and units. Actual route/feed/fee qualification remains open.
  - [Typed v4 preparation](docs/TYPED_V4_ROUTES.md) verifies the helper/parent and 14-word domain-bound policy, exact child calldata/value/output and current cap against the packed uint32 Budget trace; actual market/trace/network qualification remains open.
  - The [October25 selected-fee local composition](reports/preproduction-audit-20261025/REVIEW.md#a-07-thin-market-activation-feasibility-remains-open) exposes an honest thin-market native activation that retains about$99.38 but deploys only$98.85 of$100; the then-99% guard reverted safely. This is historical policy evidence, not a current2%/98% quote or feasibility result. Qualify full-trace feasibility at actual liquidity/ticks/fees before wallet review, preserve exact rollback and existing approvals, and assess bounded post-swap ratio correction only if it can improve deployed LP within the same captured budget. Never weaken the floor or count incumbent/idle assets as new LP; deeper mock liquidity is not launch qualification.
  - [Reviewed Entry V1](docs/EXECUTION_LOSS_POLICY.md#review-time-policy-binding) now binds the caller maximum in contract/preparation/trace/inventory. Complete matching native website/wallet and real deployment/provider qualification before public activation/growth; historical clients remain incompatible, no silent fallback.
  - [Full audit](reports/full-audit-20261025/SERVICES.md) fixes current-accounting3 dormant-state preparation and the narrowly typed native source-policy read. Composed regressions cover actual current-profile bindings, native activation/growth and exact fixed-ZZZ approval, while historical profiles remain explicit. No actual route/RPC/service/wallet qualification or public signing is inferred.
  - [Market/input hardening](reports/market-adversarial-20261026/VERIFICATION.md) validates exact sqrt/tick/fee consistency before approval/trace, preserves real boundary ticks and rejects malformed route state.223affected backend methods pass; no extra RPC call or schema/signing change. Actual quotes/routes/providers remain unqualified.
  - Actual selected-pool fork exposed an unfillable100-growth swap floor in the captured post-entry state: output was below the reviewed minimum, so the transaction reverted. The [witness](reports/current-pool-fork-20261026/growth-slippage-witness.json) and negative rollback case preserve this limitation. Native100activation/5growth and ZZZ100activation pass under the separately stated5pool minimum, without lowering the global100activation/5growth rules. Qualify actual quotes/independent prices/market state; full simulation must reject an unfillable review instead of widening limits or sending a knowingly failing wallet transaction.

  </details>

<a id="task-financial-history"></a>

- [ ] **[Qualify processed earnings & current-price USD](docs/EARNINGS_HISTORY.md)** - In progress. Confirmed collection, NFT and complete current-holdings 24h/all-time earnings are implemented, with separate LP/collective/royalty attribution and current-price USD values. Qualify actual feeds, complete predecessor history, archive providers and production service budgets.

  <details>
  <summary>Acceptance criteria</summary>

  - [Production earnings delta](reports/wallet-earnings/VERIFICATION.md): bounded same-block current-holdings history and collection holder allocations are implemented in the shared API/website profile. 86 affected Python, 89 distinct JS and six isolated production-profile browser cases pass. Claims/conversions are not income; missing prices/chunks never become zero. Actual feeds/history/hosting and independent qualification remain open.
  - Implemented exact processed-event attribution, carried fractions, deferred currency cohorts and complete configured same-chain lineage, with [scoped evidence](reports/earnings-history/VERIFICATION.md). Verify actual deployment-to-present ingestion of all seven emitters, provider/reorg behavior and load within the existing request budgets; never truncate history or infer zero from missing coverage.
  - User decision 2026-10-19: value all-time/24h earned original token amounts at today's confirmed prices, not historical USD. The implemented price profile verifies Oracle/feed/token/sequencer pins and storage; qualify actual providers, proxy/admin/wrapper assumptions and stale/recovery behavior. No guessed stablecoin peg; incomplete nonzero valuation is null.
  - Keep gross processed canonical receipts, holder allocations, actual claims, principal and current claimable balances distinct. Unprocessed/unpaid revenue is excluded; time means on-chain processing. Historical remote-profile credits do not prove remote gross revenue/reserves; current accounting3 has no remote ledger. The selected hookless pool has a static 1.002% LP fee; its observed approximately 1.101% total charge includes protocol fees that are not PoPL income. Demo 0.30% is illustrative.
  - Conversions preserve earned source currency and are not new income; current ETH claimable already includes unclaimed converted credits. Integrate clear current-price/processing-time labels and unavailable states under [live-history-ui](TODO.md#task-live-history-ui).
  - Implemented the read-only [history audit](docs/HISTORY_AUDIT.md): per configured current/predecessor epoch, compare exact raw logs and headers in windows of up to 128 blocks/10,000 logs, with shared work budgets and no database repair. [Scoped evidence](reports/history-audit/VERIFICATION.md) covers 41 distinct affected cases via new runs and exact-body reuse. Reconcile all contiguous windows through reviewed epoch cutoffs; a partial matched window or agreeing providers is not a completeness/finality proof.
  - NFT card totals now combine individual LP, equal collective and royalties; they exclude gross pool income and require complete same-snapshot priced components. Saved demo 24h net history remains unavailable. [Scoped evidence](reports/topup-and-reward-review/VERIFICATION.md) does not qualify live ingestion or prices.
  - The [NFT calculation audit](reports/topup-and-reward-review/REWARD_CALCULATION.md) traces individual LP + equal collective + royalties, distinguishes earned from unpaid totals and guards invalid aggregates. Six focused display cases and 37 affected client cases pass; real ingestion/pricing qualification remains open.
  - [Scoped outage regression](reports/comprehensive-improvement-20261025/VERIFICATION.md) prevents archive outages from erasing history. Source-currency rewards and conversions/claims remain distinct; complete actual historical ingestion and honest current-price availability still require qualification.
  - [Read-integrity fixes](reports/native-readiness-20261025/REVIEW.md) reject missing native claim rows rather than presenting a partial sum; per-NFT history now uses the existing complete-currency/current-price/period arithmetic validator. Failed history remains unavailable without discarding valid LP. Synthetic parser/actual API DTO browser evidence does not qualify actual ingestion or feed services.
  - [Remaining-architecture review](reports/architecture-pruning-20261025/REVIEW.md) and [scoped verification](reports/architecture-pruning-20261025/VERIFICATION.md): current Position3/localV4/direct governance2 are explicit.49 distinct selected Solidity behaviors and512 distinct Python methods pass across recorded source scopes; neither count is a fresh full-regression or real-service approval. Preserve old profiles/journals and unsupported cross-codec boundaries.
  - Historical profile3 replay retains authentic custody exit/return intervals and excludes backing restoration from income. Fresh accounting4 has no royalty custody drain; principal-return events/balances must remain separate from generated LP/royalty income and actual reward claims.
  - The [full service audit](reports/full-audit-20261025/SERVICES.md) fixes independent-history audit chain-ID composition with the actual Rpc adapter. Checked integers and canonical hexadecimal transport values remain strict; Boolean/floating/malformed inputs reject. Offline actual-adapter/SQLite evidence does not qualify archive provider completeness or a deployed service.
  - [Current fee conservation](reports/backend-remediation-20261026/HISTORY.md): actual fee-intake1 version, exact same-transaction/bucket/currency funded-credit pairing and pinned observed-key carried dust now reconcile. Independent LP-share and rarity weights, top-ups and verified same-chain continuity have scoped checks. Complete authentic history remains required: head checks do not prove every dust-only receipt or timestamp. Final affected167methods (31new/136existing) pass; service/pricing/capacity qualification remains open.
  - Actual PoolManager donations are funded fee growth, unlike unsolicited raw Vault prefunds. [Market/input review](reports/market-adversarial-20261026/REVIEW.md) preserves receipt-backed attribution but requires clear reporting: funded earnings do not prove organic volume or sustainable yield. No speculative APY or intent classification is added.

  </details>

<a id="task-host-services"></a>

- [ ] **[Host and monitor the API & indexer](docs/FRONTEND_API.md#local-operation-and-verification)** - In progress. Bounded workers, request budgets, per-client admission and a guarded proxy profile are implemented and locally verified. Current Pinax serialized archive reads served the pinned current-pool fork; earlier HTTP/transport/batch failures retain their dated source scope. Full production RPC/history capabilities, Linux/TLS API hosting, complete backfills/reorg recovery, quotas and off-host alerts remain unqualified. Poplint static HTTPS is separate from API/indexer hosting.

  <details>
  <summary>Acceptance criteria</summary>

  - [Collection ingress delta](reports/collection-reads/nginx.json): the reviewed GET allowlist and supervised workers support bounded collection reads; all 34 isolated Nginx checks pass. Roll out matching API/proxy/frontend versions; Linux/TLS/provider qualification remains open.
  - [Wallet earnings proxy check](reports/wallet-earnings/VERIFICATION.md): summary and earnings GET chunks are admitted by the reviewed Nginx allowlist. 30 isolated actual Nginx checks pass, including cursor/method rejection; deploy matching includes and qualify Linux/TLS separately.
  - Publish and qualify the confirmed read API, optional unsigned preparation and ownership/claim-history indexer for the reviewed deployment. Independently verify hashes/configuration and response freshness after all RPC/history reads.
  - Qualify redundant providers, hosting limits, complete backfill, reorg recovery, structured sanitized logs and off-host alerts. Never host a transaction signer in the frontend read/preparation API.
  - Independently qualify the schema-2 lifecycle and complete same-chain predecessor history with live consumers: reviewed peer code/ABI/semantics and configuration, archive receipt/state availability, full ingestion reconciliation, retirement-cutoff index retention/backups, request latency at configured bounds and sanitized failure behavior. No partial lifetime sums or automatic unreviewed peer discovery.
  - Investigate the intermittent RPC HTTP failure observed during price reads. The subsequent paced feed/route observation succeeded but does not prove its cause or provider reliability; qualify bounded retry/failover and snapshot freshness without weakening fail-closed behavior.
  - [AUD18-03 remediation](reports/api-work-limits/VERIFICATION.md): shared 25-second deadline, expiry shortening, finite logical/physical RPC budgets and 30-second supervised workers are implemented; original expiry reproduction stops before tracing. Qualify real Linux process cleanup, DNS/slow-body/RPC stalls, maximum lineage/history and trace workloads, admission/rate/connection limits and sanitized off-host timeout alerts. A timeout must not leave backend work or partial results.
  - Qualify the explicit royalty-reporting profile against actual pinned ledger/converter versions and complete history. Exercise currency-null states, strict core/work-limit rejection, predecessor cutoffs and clients that cannot interpret the new availability/eligibility fields; no automatic runtime-pin acceptance.
  - Use the [history comparison procedure](docs/HISTORY_AUDIT.md) with a reviewed separate RPC operator. Qualify the first block_log_lookup index build on the actual database, disk/backup/restart behavior, complete backfills and provider/reorg/load conditions. No server restart or provider approval is implied by local evidence.
  - [Concurrent service safeguards](docs/CONCURRENT_SERVICES.md) are implemented: per-process worker/connection caps, no work queue, absolute ingress/header bounds, sanitized overload and failed-cleanup quarantine. [Scoped evidence](reports/concurrent-services/VERIFICATION.md) records real loopback burst/isolation and process cleanup checks. Qualify actual Linux/RPC/history/trace behavior within configured limits, per-client fairness, reverse-proxy limits, aggregate provider budget and supervised restart before hosting; no signer or public endpoint added.
  - Implemented [per-client admission and proxy operation](docs/API_INGRESS.md), with 50 distinct affected Python cases across two scoped runs and 22 real Nginx/loopback assertions. Qualify actual Linux/TLS/default-host/CDN policy, shared-NAT client behavior, aggregate provider quotas, log retention and bounded frontend retries before opening public ingress. Local HTTP evidence does not approve hosting.
  - Decision 2026-10-20: the dedicated 10/25/100-user capacity campaign is [deferred](TODO.md#task-capacity-campaign). Keep basic overload safety, bounded independent workers, safe recovery and qualification of configured hosting/RPC limits before real funds. Capacity stays unverified; the disposable shared signer is not a production service.
  - Native V2 API and keeper configurations require explicit accounting_version2, reviewed runtimes and deployment identity; legacy predecessor profiles remain explicit. Qualify the website native valuation profile, complete production inventory and provider traces before activation. Do not reinterpret old state journals or change Anvil-only signing.
  - Shared read-only RPC refuses all redirects, including same-host; only explicitly configured reviewed endpoints may be used. Bounded failover, chain recheck, response/work limits and sanitized failure reporting remain. Qualify final provider URLs/proxy/auth behavior explicitly; other historical standalone transports are separate.
  - Use the stricter [RPC qualification procedure](docs/RPC_PREPARATION_QUALIFICATION.md): timeouts/rate limits/ambiguous errors do not prove unknown-hash rejection; the opt-in preparation profile requires reviewed genesis/runtime and a real discarded Approval(0) log witness. Keep basic public-read observations, actual preparation capability and independent operating approval separate.
  - [Current observation](reports/release-services-20261025/vrf-opensea/VERIFICATION.md) obtained16 logical canonical runtime/storage reads using32 HTTP posts from one public provider. Separate feed probing later failed429/403. Neither result supplies redundant operating approval, continuous uptime or preparation-trace qualification.
  - [Indexer provenance fix and scoped evidence](reports/daily-security-20261025/SERVICE_REVIEW.md): reject invalid/duplicate log identities atomically before inserting a new batch/cursor. Preserve rejected or previously poisoned database evidence; no silent deletion/repair, and full confirmed-history coverage remains required after an approved separate rebuild.
  - [Remaining-architecture review](reports/architecture-pruning-20261025/REVIEW.md) and [scoped verification](reports/architecture-pruning-20261025/VERIFICATION.md): current Position3/localV4/direct governance2 are explicit.49 distinct selected Solidity behaviors and512 distinct Python methods pass across recorded source scopes; neither count is a fresh full-regression or real-service approval. Preserve old profiles/journals and unsupported cross-codec boundaries.
  - [RPC boundary corrections](reports/system-adversarial-20261026/VERIFICATION.md) reject ambiguous/nonfinite JSON and noncanonical chain identities, normalize decoder-limit failures through configured retries and distinguish malformed result+error from genuine missing-block rejection. The final combined 244-method scope has 241 passes/3 explicit skips; the earlier 51 transport/history methods overlap it. Socket timeout is not a total stalled-I/O deadline: qualify the source keeper watchdog and actual provider/proxy/work budgets separately.
  - Maintain [separate demo/integration environments](docs/SITE_ENVIRONMENTS.md): popldemo stays on /var/www/aaa-website, poplint uses /var/www/popl-integration, separate Nginx/certificate/release identity and explicit current3 config. Publishing an unconfigured static integration site does not close API/indexer/feed/operating qualification; never expose local Anvil or auto-select demo data.
  - [Poplint serving evidence](reports/current3-website-20261026/DEPLOYMENT.md): f23c559 is separately deployed with HTTPS/identity/blocked-path checks, unchanged demo release/config/content, active renewal timer and lineage-only reload hook. Website source/operating docs are published through77501ce. Current contract/API configuration is still null; static hosting does not close backend/service/provider qualification.

  </details>

<a id="task-native-production-preflight"></a>

- [ ] **[Qualify the accounting4 production inventory and preflight](docs/PRODUCTION_PREFLIGHT.md)** - In progress. Historical accounting3 inventory/observer is preserved. The fresh accounting4/custody3/holder-exitV5 release gate explicitly stays blocked until its new binding, terminal lifecycle, payout and service inventory is reviewed; old ready results do not approve current source.

  <details>
  <summary>Acceptance criteria</summary>

  - [Scoped verification and internal review](reports/native-preflight/VERIFICATION.md): 73 distinct focused Python cases across source-scoped runs; repeat cases counted once. Complete observer-to-gate composition is synthetic, not actual-provider qualification. Prior 131 contract/source bindings match and unchanged Solidity checks were reused, not rerun.
  - [Operator runbook](docs/PRODUCTION_PREFLIGHT.md): separate approved pins and actual observations; preserve historical qualification blocks, require current configuration/fee scope and complete creation-to-anchor history. Removed creator-inbox fields are not current helper bindings; incompatible historical profiles and unsupported canonical boundaries fail explicitly.
  - Populate independently reviewed real addresses, runtime pins, source/conversion routes, feeds, authorities, VRF/hosting/OpenSea/gas/recovery and independent audit records under the corresponding open release tasks. The checked-in current example must remain blocked until those actual inputs are qualified.
  - Current [pricing-V2 extension](docs/PRICE_SECURITY.md) verifies the fixed Oracle pricing companion and complete two-source policy/bounds/fingerprints at the same confirmed timestamp. Its new source-scoped evidence is [separate](reports/price-security/VERIFICATION.md) from the earlier 73-case preflight publication; neither qualifies live providers.
  - Current CLI requires schema5/current mint profile1 by default; explicit historical mode is never qualification. [68 distinct affected Python methods](reports/release-services-20261025/vrf-opensea/VERIFICATION.md) include legacy/type/downgrade/unsupported-mint and exact original-randomness recovery boundaries. Current source correctly blocks OpenSea qualification until compatible code exists.
  - [Remaining-architecture review](reports/architecture-pruning-20261025/REVIEW.md) and [scoped verification](reports/architecture-pruning-20261025/VERIFICATION.md): current Position3/localV4/direct governance2 are explicit.49 distinct selected Solidity behaviors and512 distinct Python methods pass across recorded source scopes; neither count is a fresh full-regression or real-service approval. Preserve old profiles/journals and unsupported cross-codec boundaries.
  - [Market/input review](reports/market-adversarial-20261026/REVIEW.md) shares exact integer slot0 validation between observer and both offline state gates, including manually supplied inventories. Consistency is not provider authentication; chain/block/runtime/independent-observation qualification remains required.
  - Bind accounting4/custody3/HOLDER_EXIT_V5, native-only LP admission, principal_exit/NFT runtime pins, funded payout signer and post-close worker configuration. Review target batch gas/latency and current frontend separately; retain old schema5 tools only for explicit historical inspection.

  </details>

<a id="task-read-api"></a>

- [x] **[Confirmed balances & ownership API](docs/FRONTEND_LINEAGE.md)** - Implemented. Confirmed balances, lifecycle guards and complete configured same-chain predecessor claim history are implemented. Lifetime totals include LP fees, royalties and past owners. Hosting and current3 frontend integration remain release gates. Future-chain history is deferred outside this release; the current lineage is same-chain only. Current LP ID/share denominator and historical gross contributions are exposed separately from current marked NAV; local custody mismatches fail closed.

  <details>
  <summary>Acceptance criteria</summary>

  - Eight runtime/address pins, controller/helper bindings and strict lifecycle checks share the confirmed balance snapshot. Frozen/importing/retired/cancelled NFT and wallet projections fail closed; protocol status stays readable without reward/price calls. Operating qualification and consumer integration remain under hosted services and frontend tasks.
  - Complete explicitly pinned same-chain predecessor history preserves original NFT IDs and lifetime LP plus royalty claims. Verify both handoff directions, canonical matching activation/retirement receipts, terminal roots, historical assets and full creation-to-retirement ingestion. Missing configuration returns unavailable totals; inconsistent configured lineage fails closed. Import transfers are ownership reconstruction, not paid mints or marketplace sales.
  - Enforce at most eight predecessors and one million configured maximum replay events across current and prior histories. RPC observations and operator ingestion remain the trust model; this backend does not prove consensus finality or implement cross-chain history.
  - Governed custody candidate: surface source principal and royalty-currency in-transit states as unavailable, preserve funding/claim history and never count restoration as new income. Update services/inventory/operator alerts and holder disclosures for explicit external EOA/contract custody trust; no auto resend, timeout recovery, invented remote NAV or legacy v3 migration calls.
  - [Indexer recovery](docs/INDEXER_RECOVERY.md) preserves confirmed SQLite blocks/logs/cursor on missing, malformed, unstable or unproved RPC ancestry. A bounded contiguous common ancestor or original start anchor must be proved read-only before one atomic guarded rollback. Current provider/backfill/finality/recovery qualification remains open.
  - [Fee integrity remediation](reports/backend-remediation-20261026/PROFILE.md): current3 LP inventory requires actual native ETH first and validated inactive NFTs reject positive available LP/royalty credit. Genuine optional currency outages remain null. Wallet summaries preserve malformed-data errors and use one extra pinned weight read per current NFT; finite chunks/budgets remain.

  </details>

<a id="task-royalty-reporting"></a>

- [x] **[Report royalty eligibility & conversion history](docs/ROYALTY_REPORTING.md)** - Implemented. Opt-in confirmed ETH/source balances, deferred currency eligibility and pinned converter enable status are implemented. Complete same-chain event replay separates conversion credits from actual lifetime claims. Missing values stay unavailable; UI, gross earned/USD history and live service qualification remain separate tasks.

  <details>
  <summary>Acceptance criteria</summary>

  - [Scoped verification](reports/royalty-reporting/VERIFICATION.md): 138 affected Python cases and 20 supplemental cases pass. Forty unchanged Solidity source bindings are reused; ten getter ABIs and 26 added indexer schemas match existing compiler artifacts. No Solidity rerun, public transaction, service deployment or website change.
  - The profile is explicit and pin-reviewed; legacy contracts do not inherit it. Currency failures do not bypass core identity, lifecycle, canonical freshness, full history coverage or request budgets. Conversion is neither a claim nor new revenue, and native claimable already includes remaining conversion credits.
  - [Native custody correction](reports/day-readiness-20261025/royalty-matrix.md): verified nonce/cohort checks allow legitimate delayed ETH eligibility; balances remain unavailable while backing is external. Full NFT projection preserves LP/healthy currencies.52 distinct affected read/replay methods pass across recorded source scopes, including13new cases; actual native-custody producer case passes separately. No service/database rollout performed.
  - [Fee-breakdown review](reports/backend-remediation-20261026/REVIEW.md): inactive ghost credits reject with or without optional reporting. Activated parked/outbound rewards and unavailable currency states remain distinct. Both ETH ledgers are required for a ready-to-claim total; no raw source-token units are added to ETH.

  </details>

<a id="task-unsigned-actions"></a>

- [x] **[Prepare unsigned mint & claim requests](docs/FRONTEND_TRANSACTIONS.md)** - Implemented. Typed 0.05 ETH mint and up to 32 LP/royalty claim drafts now use current lifecycle/mint controls, exact canonical-hash simulation, scoped currency isolation, bounded workers and separate reviewed gas estimates. Signing stays in the wallet; live service/browser qualification remains open.

  <details>
  <summary>Acceptance criteria</summary>

  - Implemented: exact typed intent/owner/ledger checks, no arbitrary target or overrides, mint-only/global/preparation gates, canonical lock rejection, selected-asset verification, short client expiry, shared work budgets and supervised opt-in HTTP. Default GET-only; no signer/broadcast.
  - A required operator fee policy binds the reviewed read configuration and fee evidence, gas-price and total network-fee ceilings. Missing complete fee accounting or canonical gas estimation fails closed. Native value and gas are separate; future claims cannot fund upfront gas.
  - [Current scoped verification](reports/wallet-preparation/VERIFICATION.md) records focused Python/HTTP/worker cases and reusable compiler ABI evidence. No Solidity change or repeated contract suite. Actual deployment/VRF/RPC/fee manifests, ingress/load and wallet signing/receipt rehearsals remain with the service and frontend tasks.
  - [Adversarial reward review](reports/reward-resilience-20261026/REVIEW.md): current3 claim preparation now rejects positive rewards for never-activated NFTs and malformed/unreadable global activation data before a draft. One bounded mapping read per distinct NFT; existing current-owner/ordinal/asset/snapshot/simulation checks remain. Historical, parked/outbound and deferred-currency rights are preserved. Final combined443methods yield437passes/6explicit skips, including14new claim-integrity methods; local checks do not qualify live wallets/services.

  </details>

<a id="task-api-client-admission"></a>

- [x] **[Bound per-client API work and validate proxy identity](docs/API_INGRESS.md)** - Implemented. Both CLI services now separate read/preparation rate budgets, cap concurrent work per client and bound client state. An explicit local-proxy/HTTPS-origin boundary and restricted Nginx profile are locally verified. Actual public hosting remains under the service task.

  <details>
  <summary>Acceptance criteria</summary>

  - [Scoped verification](reports/api-admission/VERIFICATION.md): 47 affected Python cases plus three supplemental cases, and 22 actual Nginx/loopback assertions. Spoofed forwarding/origin, overload, full-table, disconnection and upstream failure cases preserve isolation; no extra worker/RPC work starts on rejected admission.
  - Maintain proxy/service identity policy together, with exact same-origin POST, no signer/cache/replay, bounded logs and documented stop/restart/rollback. Per-IP budgets are not authenticated users or a distributed/DDoS guarantee; production qualification stays under [host services](TODO.md#task-host-services).

  </details>

<a id="task-holder-preflight"></a>

- [x] **[Inventory NFT holders before replacement](docs/HOLDER_PREFLIGHT.md)** - Implemented. Confirmed owner/code inventory, bounded pages and complete coverage checks flag contracts and delegated accounts for review. The procedure requires a frozen rescan and exact escrow release/claim evidence; actual compatibility qualification remains under canonical recovery.

  <details>
  <summary>Acceptance criteria</summary>

  - [Scoped verification](reports/holder-preflight/VERIFICATION.md): pinned reads, 1,000-NFT coverage, missing/duplicate/mixed snapshots, reorgs, code/binding drift and limits. Read-only implementation; no actual deployed escrow or marketplace approved.
  - [Holder input hardening](reports/system-adversarial-20261026/ops-input/VERIFICATION.md) caps reads before allocation, rejects duplicate/nonfinite/overflow JSON, normalizes parser limits and sanitizes argument errors.24affected methods pass,12new included once; valid flags/static help/exclusive outputs and unresolved-escrow/nonapproval semantics remain. Actual holder/escrow rehearsal still required.

  </details>


## Frontend

What holders see and use.

<a id="task-wallet"></a>

- [ ] **[Connect real wallet transactions](docs/BROWSER_WALLET.md)** - In progress. The explicit accounting3 website reader and unsigned-review profile are implemented with ETH/fixedZZZ admission and current module/canonical checks. They are published through separate, still-unconfigured poplint; qualify actual contracts/API/providers and preserve popldemo and historical Anvil journals. Actual contracts/API/feeds/routes/extension acceptance remain open; public signing stays disabled.

  <details>
  <summary>Acceptance criteria</summary>

  - Decision 2026-10-22: production minting is intended for OpenSea; website minting is demonstrative. Production website mint preparation is blocked; local Anvil minting remains an integration tool. Qualify [OpenSea primary mint](TODO.md#task-opensea-mint) before sealing; production website priorities are activation, growth, ownership/balances and claims. Public signing remains disabled.
  - [Local-only publication](reports/deployment-local-wallet/PUBLICATION.md): website d786286 is on main and the Ubuntu static server. All 5,598 checksums and 50 scoped public/host/privacy checks pass. Public configuration remains null; no production signing or API deployment.
  - [Local API wallet coordinator](reports/deployment-local-wallet/VERIFICATION.md): 84 affected cases and nine headless scenarios pass with mocked wallet/RPC. Exact approval continues to fresh LP review; receipt recovery never resends, and confirmed/API-lag states are distinct. The user retained local Anvil-only signing; shared signer unchanged. Public signing, live extension/service qualification and replacement-transaction recovery remain open.
  - [Publication receipt](reports/deployment-adapter/PUBLICATION.md): website code 757a8de is on main and the static Ubuntu site; all 5,597 server checksums and 49 scoped public/host/privacy checks passed. Public DEPLOYMENT remains null. This does not enable production APIs or signing.
  - [Reviewed website API profile](docs/DEPLOYMENT_WEBSITE.md) and [scoped evidence](reports/deployment-adapter/VERIFICATION.md): 57 new focused cases and eight isolated browser scenarios pass. Eleven responses come from actual Python API code with byte-level mocked dependencies. No new signer or public transaction; the local-only signer restriction remains. Automatic approval review rejected its proposed expansion, which was not applied.
  - [Publication checkpoint](reports/browser-wallet/PUBLICATION.md): latest wallet/backend code is on main and the matching static website is deployed and checksum-verified. Public mode remains simulated; actual extension acceptance and production qualification remain open. No unchanged suites or deferred capacity campaign rerun.
  - [Independent chain reader](reports/browser-wallet/CHAIN_READER.md): shared mint/approval/activation/top-up/claim confirmation now uses a pinned read RPC rather than extension transaction formatting; EIP-155 legacy chain identity is supported without weakening typed chain checks. 232 distinct website and 43 backend passes; actual existing mint recovery and exact-node CSP/CORS verified. 13 NFTs/LP/session preserved. Actual extension acceptance and production deployment/service qualification remain open.
  - [Canonical dynamic-fee receipt recovery](reports/browser-wallet/DYNAMIC_FEE_RECEIPTS.md): generic EIP-1559 fee derivation fixes uncapped RPC convenience reporting without loosening reviewed limits. 142 signer/client + 40 observer cases and actual minted receipt/balance replay pass. Local web-only reload preserves session/12 NFTs/Anvil; actual extension recovery retest and production qualification remain open.
  - [Mint loading states](reports/browser-wallet/MINT_LOADING.md): first load/refresh and connection are distinguished from mint review, wallet prompt, receipt and reconciliation; unrelated NFT actions never show mint progress. 44 affected UI checks and build pass. Existing pending/readiness safeguards remain.
  - [Numeric provider nonce compatibility](reports/browser-wallet/NUMERIC_NONCE.md): reported number-valued eth_getTransactionCount failure reproduced and fixed in the shared chain-independent signer. Safe integers normalize exactly; unsafe values fail, canonical outgoing/journal encoding and economic checks remain. 139 affected passes. Actual MetaMask retest and production profile qualification remain open.
  - [Wallet lifecycle review](reports/browser-wallet/LIFECYCLE_REVIEW.md): modern provider discovery, clean account selection, verified network switch/event restoration, explicit signing/receipt states and full sender review. 203 affected checks plus build/served-source checks pass. Direct-node mint preflight passes without sending; actual MetaMask pre-prompt failure and browser acceptance remain open. Current operator procedure supersedes older reconnect descriptions below.
  - [Wallet RPC quantity diagnostics](reports/browser-wallet/RPC_QUANTITIES.md): bounded padded hex provider responses supported; invalid fields named, strict prepared/journal values retained. Preflight failure distinguished from submitted recovery. 123 affected passes; actual MetaMask incident cause remains unconfirmed. The review dialog now exposes the exact escaped failure; direct node quantity checks pass, but the browser-provider error is still required.
  - [Fresh MetaMask selection](reports/browser-wallet/FRESH_SELECTION.md): explicit reconnect stops preferring the saved sender; MetaMask button requests fresh permissions and multiple returned accounts require explicit selection. Unfinished choice cannot restore the old sender; pending journals remain. 90 affected checks pass. Actual Chrome/MetaMask acceptance remains open.
  - [Authorized account selection](reports/browser-wallet/AUTHORIZED_ACCOUNTS.md): fresh picker suppresses old diagnostics; select an admitted account actually authorized by the chosen provider, even when another address is first. Selection persists only while authorized. Sender membership, pending journals and deployment checks remain. 180 distinct affected cases pass; actual MetaMask UI acceptance stays open.
  - [In-page account chooser](reports/browser-wallet/ACCOUNT_CHOOSER.md): explicitly reopen the selected extension account permissions and verify fresh accounts/network. Already-valid reconnect remains read-only; the main provider button opens account selection for a still-rejected restored address. Refresh never opens prompts; pending journals block switching. Follow-up: 53 client cases pass, including four new normal-button retry cases; actual MetaMask chooser acceptance remains open.
  - [Automatic confirmation follow-up](reports/browser-wallet/AUTO_CONFIRMATION.md): canonical inclusion checks avoid a lagging head veto for one confirmation; 21 same-hash polls at 1500ms spacing have a 45-second total budget. Specific pending reasons reach the UI. Seven new focused cases and read-only actual-receipt replay pass; next extension acceptance remains open. This supersedes the earlier three-attempt polling limit.
  - [Mint wait and local latency](reports/browser-wallet/MINT_WAIT_PERFORMANCE.md): separate 90-second wallet response wait, bounded same-hash receipt retries, and labeled confirmed cards during refresh. Local loopback connection reuse reduced an eight-NFT warm read from 6.057s to 1.904s; this is not production/load qualification. Eight positions and session preserved; no payment resubmitted.
  - [MetaMask connection and approval recovery](reports/browser-wallet/CONNECTION_RECOVERY.md): distinguish site-authorized account, chain ID and exact local genesis; reconnect through fresh public reads. Recognize wallet gas-limit padding only within hard policy and original canonical paid-gas/price/cost ceilings. Preserve the original review and never resend a confirmed approval.
  - Production network selection must request Robinhood Chain from independently reviewed deployment/network configuration, with exact chain, RPC and contract bindings. Local Anvil prompts stay local. Do not enable public signing or reuse a chain-31337 fixture manifest as mainnet configuration.
  - [Browser-wallet candidate](docs/BROWSER_WALLET.md): only the explicit chain-31337 browser mode can sign. Account/chain/genesis/runtime/nonce/gas and typed intent checks precede one wallet request; same-origin localStorage/Web Locks retain unknown submissions. Browser drafts cannot be sent by the local service signer. [Scoped evidence](reports/browser-wallet/VERIFICATION.md) records 43 affected Python and 167 website cases plus five actual local transactions through an EIP-1193-shaped RPC adapter, not extension acceptance.
  - Local milestone: [website integration](docs/LOCAL_WEBSITE.md) and [scoped evidence](reports/local-website/VERIFICATION.md). Disposable launcher-owned accounts only; public deployment and production browser-wallet signing are not approved.
  - Integrate actual wallet transactions and the implemented confirmed API/history/unsigned-preparation service, including the separate royalty ledger, lifetime per-asset claims and indexed ownership. Independently pin/review deployments and calldata; discard drafts on account/chain changes or expiry; freshly simulate/estimate gas, confirm with the user and handle canonical receipts/replacements/reorgs. Bound/chunk portfolio claims. Gross earned fees and USD history require separate data/valuation; raw claimed totals cannot substitute for them.
  - Local fast session handshake supplies wallets before full portfolio reads; selection survives soft reload/navigation within that disposable deployment. New sessions require selection again. This is not public-wallet persistence or signer hosting.
  - Main static website now preserves wallet selection in tab session storage and restores browser accounts without prompts/signing. Account/network changes invalidate unsent previews. This is public-account connection continuity, not live financial transaction integration. See [main website evidence](reports/frontend-state/VERIFICATION.md).
  - Local preparation contention: activation/mint/claim review waits on the exact pre-handler busy response with bounded retries and account/state cancellation. Submission is never automatically repeated. See [scoped evidence](reports/local-preparation-busy/VERIFICATION.md). This does not qualify production wallet concurrency.
  - Local two-transaction flow: exact replacement approval then Entry; atomic native ETH in a separate chain-31337 admission fixture. Fixed $100 local activation, token-unit inputs and continuous confirmation UI. Read-clock RPC overhead removed. [Evidence](reports/local-contribution-flow/VERIFICATION.md). Production fixed-$100 quote/rounding policy and public wallet qualification remain open; production Entry currently retains its $100 minimum.
  - Local cross-browser confirmation fix: a newer draft reconciles confirmed state with bounded unsigned retries; explicit stale submission rejection requires a fresh review, while ambiguous responses retain their saved operation ID. [Scoped evidence](reports/local-wallet-concurrency/VERIFICATION.md). Production wallet concurrency remains open.
  - Local submission-lock follow-up: only the exact pre-handler busy /action response waits with the same saved operation ID and unchanged payload. Lost/ambiguous responses stay on recovery; stale revisions need new review. 64 scoped cases and an actual service-lock probe pass. [Evidence](reports/local-wallet-concurrency/VERIFICATION.md#submission-lock-follow-up---2026-10-20).
  - Local wallet execution now pins each sender nonce: exact server drafts may span unrelated wallet operations, while same-wallet activity, expiry, ownership, lifecycle and gas changes still require review. Two real local mints reviewed at one revision both confirmed; 70 distinct affected Python cases. [Evidence](reports/local-wallet-concurrency/NONCE_VERIFICATION.md). This supersedes the earlier blanket global-revision rejection for typed wallet execution only; production extension-wallet qualification stays open.
  - User reported all six proposed local two-wallet scenarios passed on 2026-10-20: activation, top-ups, cancel after approval/reopen, pending refresh recovery, concurrent claim/contribution and invalid inputs. [Manual acceptance](reports/local-wallet-concurrency/MANUAL_ACCEPTANCE.md) is user-reported evidence, not a new automated run or production qualification.
  - Next qualification: actual Chrome/extension signing, rejection, delayed prompts, account/network changes and recovery; independently reviewed production deployment pins, complete RPC/gas semantics and live activation routes/feeds. Dynamic local manifests and mock prices are not production approvals. Keep local exact-$100 activation versus production minimum-$100 quote/rounding alignment explicit; the 10/25/100-user campaign remains deferred.
  - [Actual local API evidence](reports/api-chain-rehearsal/VERIFICATION.md): five holder transactions, real HTTP APIs, 18-NFT aggregation and same-hash claim recovery; 46 Python and70 JS scoped cases. RPC wallet shim and mock markets/feeds/VRF do not establish actual extension or production qualification.
  - [Pending nonce diagnosis](reports/browser-wallet/PENDING_NONCE.md): 175 affected cases, two mocked browser scenarios and six actual read-only recovery observations pass. Queued or wallet-changed nonces now stop the wait immediately; journals and local-only signing remain. The actual nonce 35 mint is unmined; controlled queue reconciliation and extension acceptance remain open.
  - [Authorized local mint reconciliation](reports/browser-wallet/local-mint-reconciliation/RECONCILIATION.md): exact queued nonce35 mint removed after identity/pool checks; complete stateRoot and both account balances/nonces unchanged.13 focused checks and an isolated browser scenario pass. User MetaMask nonce-history reset, exact saved-journal archival and temporary local-overlay removal remain pending. Public signing/source unchanged.
  - [Reviewed Entry V1](docs/EXECUTION_LOSS_POLICY.md#review-time-policy-binding) now binds the caller maximum in contract/preparation/trace/inventory. Complete matching native website/wallet and real deployment/provider qualification before public activation/growth; historical clients remain incompatible, no silent fallback.
  - [Native schema-2 website profile](docs/NATIVE_WEBSITE_PROFILE.md) is implemented locally for accounting2/routing2/pricing2/review1: native-zero pricing, policy/parent/runtime pins, current caller-bound cap and conservative upper-input floor; exact native LP+royalty claims. Both native ledgers are mandatory, and NFT history uses raw/price/period arithmetic validation. Public DEPLOYMENT stays null; shared signer/client/coordinator unchanged and Anvil-only. Actual native extension/chain acceptance, public signing approval and rollout remain open.
  - The published website native2 profile is historical relative to the new contract candidate. The matching accounting3/local8-word reader and unsigned-review profile are implemented and source-checked; qualify actual reviewed contracts/API/providers without relabelling existing deployments or enabling public signing. Existing Anvil fixtures and saved actions remain their original profiles.
  - Current3 website implementation: explicit schema3 manifest, accounting3/governance2/fee1/localV4 runtime/domain bindings and ETH/fixedZZZ-only inputs; actual HTTP schema2 DTOs cover six activation/growth/approval/claim reviews. The final affected scope has451JS passes including46new methods; earlier overlapping runs are not additional coverage. Evidence: [current3 integration](reports/current3-website-20261026/VERIFICATION.md). Poplint has its own build/root/configuration; no current public deployment/API is fabricated and signing stays disabled.

  </details>

<a id="task-portfolio"></a>

- [ ] **[Show actual holdings & claimable fees](docs/FRONTEND_API.md#implemented-endpoint)** - In progress. Current3 confirmed holdings, LP/reward/history and collection readers are implemented with exact profile/provenance and unavailable-state checks. Poplint is separate from the demo and must remain unconfigured until real reviewed bindings/API exist. Actual provider, complete-history and operating acceptance remain open.

  <details>
  <summary>Acceptance criteria</summary>

  - [Collection explorer evidence](reports/collection-reads/VERIFICATION.md), 2026-10-23: bounded canonical collection inventory and per-NFT current LP, all-page totals, eligibility counts, filters/pagination and current-owner details are implemented. Partial pages/unknown marks fail closed; qualify actual 1,000-NFT provider/history latency and hosting before release.
  - [Production earnings delta](reports/wallet-earnings/VERIFICATION.md): bounded same-block current-holdings history and collection holder allocations are implemented in the shared API/website profile. 86 affected Python, 89 distinct JS and six isolated production-profile browser cases pass. Claims/conversions are not income; missing prices/chunks never become zero. Actual feeds/history/hosting and independent qualification remain open.
  - [Reviewed API integration](docs/DEPLOYMENT_WEBSITE.md) accepts ordinary authorized addresses, isolates connection storage by deployment and discards old account/page results. Missing history/prices remain unavailable; source rewards are never labeled ETH. Collection aggregation is implemented as described above; production provider qualification remains open.
  - Local display correction: show the revealed rarity multiplier (Commun Ã—1, Rare Ã—2, Legendary Ã—3), grayed while dormant. Unrevealed remains unknown; effective zero accounting weight before activation must not replace the trait label. No contract eligibility or claim calculation changes.
  - Local dormant cards/details omit reward, claim and earnings-history sections. Activated cards have separate Claim and Grow attached LP controls. Same-account/session refresh retains labeled last-confirmed cards with actions disabled; failed reads and context changes mask unavailable balances; confirmed evolution crossfades without changing rarity/palette. Reduced-motion is supported.
  - Local milestone: [website integration](docs/LOCAL_WEBSITE.md) and [scoped evidence](reports/local-website/VERIFICATION.md). Disposable launcher-owned accounts only; public deployment and production browser-wallet signing are not approved.
  - Use confirmed current ownership, attached LP and separate per-asset individual/collective/royalty balances. Preserve unavailable remote/stale valuations and sticky activation eligibility through artwork downgrades.
  - Decide whether production labels use raw hashed token IDs or the existing sequential mint ordinal; implement and review matching metadata/UI labels without changing stable custody IDs. Demo #444 is not a promised production identifier.
  - Integrate current physical LP/share-denominator context, marked NAV vs cumulative input and price-guard unavailable states. Render out-of-range warning plus earliest rebalance eligibility; only fresh authenticated telemetry may supply an estimated next keeper check. The public website is still simulated and was not changed by the backend delta.
  - Consume [royalty-reporting fields](docs/ROYALTY_REPORTING.md): separate claimable ETH/source currencies, deferred eligibility and unavailable amounts. Converter enabled is not a route quote or scheduled execution. Do not offer signing based solely on a read-only balance response.
  - Main website now also hides dormant fee/claim sections, shows fixed dormant rarity multipliers, separates Claim/Grow controls and preserves artwork through unrelated refreshes. Only its target NFT shows activation/top-up progress. Default data remains a simulation; local and live adapter boundaries remain explicit.
  - [Actual local API evidence](reports/api-chain-rehearsal/VERIFICATION.md): five holder transactions, real HTTP APIs, 18-NFT aggregation and same-hash claim recovery; 46 Python and70 JS scoped cases. RPC wallet shim and mock markets/feeds/VRF do not establish actual extension or production qualification.
  - Governed custody candidate: surface source principal and royalty-currency in-transit states as unavailable, preserve funding/claim history and never count restoration as new income. Update services/inventory/operator alerts and holder disclosures for explicit external EOA/contract custody trust; no auto resend, timeout recovery, invented remote NAV or legacy v3 migration calls.
  - The published website native2 profile is historical relative to the new contract candidate. The matching accounting3/local8-word reader and unsigned-review profile are implemented and source-checked; qualify actual reviewed contracts/API/providers without relabelling existing deployments or enabling public signing. Existing Anvil fixtures and saved actions remain their original profiles.
  - Current3 website implementation: explicit schema3 manifest, accounting3/governance2/fee1/localV4 runtime/domain bindings and ETH/fixedZZZ-only inputs; actual HTTP schema2 DTOs cover six activation/growth/approval/claim reviews. The final affected scope has451JS passes including46new methods; earlier overlapping runs are not additional coverage. Evidence: [current3 integration](reports/current3-website-20261026/VERIFICATION.md). Poplint has its own build/root/configuration; no current public deployment/API is fabricated and signing stays disabled.
  - Integrate fresh accounting4/custody3 principal_return and terminal LP state on poplint, separately from generated fees and reward claims. Normal collective return pushes ETH+ZZZ to the current owner with no holder action; old accounting3 website data must not be relabelled.

  </details>

<a id="task-transaction-ui"></a>

- [ ] **[Handle the complete transaction journey](docs/CLAIM_ROUTER.md)** - In progress. Main website tracks per-NFT actions, commits cross-tab previews safely, caches only immutable exact-version demo state, expires suspended intents and rejects malformed/stale local confirmations. Current3 receipt/reorg/account recovery and service qualification remain open. Public signing is deliberately disabled and needs separate explicit authorization; the optional large-load campaign remains deferred by user decision.

  <details>
  <summary>Acceptance criteria</summary>

  - Decision 2026-10-22: production minting is intended for OpenSea; website minting is demonstrative. Production website mint preparation is blocked; local Anvil minting remains an integration tool. Qualify [OpenSea primary mint](TODO.md#task-opensea-mint) before sealing; production website priorities are activation, growth, ownership/balances and claims. Public signing remains disabled.
  - [Local API wallet coordinator](reports/deployment-local-wallet/VERIFICATION.md): 84 affected cases and nine headless scenarios pass with mocked wallet/RPC. Exact approval continues to fresh LP review; receipt recovery never resends, and confirmed/API-lag states are distinct. The user retained local Anvil-only signing; shared signer unchanged. Public signing, live extension/service qualification and replacement-transaction recovery remain open.
  - [Unsigned review profile](docs/DEPLOYMENT_WEBSITE.md) displays exact token units, simulated marginal LP addition, separate gas and expiry. It independently reconstructs typed calls and exact approval to Entry. Historical schema1 requires99%; a current3 implementation must enforce the captured governed contribution cap (default2%/98% deployed), caller maximum and stronger venue minima. Activation targets $100 with raw-unit round-up; growth requires at least $5. No submission/receipt path exists in this profile yet.
  - Local milestone: [website integration](docs/LOCAL_WEBSITE.md) and [scoped evidence](reports/local-website/VERIFICATION.md). Disposable launcher-owned accounts only; public deployment and production browser-wallet signing are not approved.
  - Show original contribution value, exact approvals, the 1% execution limit and network gas separately. Rejected or reverted execution may still cost network gas.
  - Independently review and pin deployments, the immutable 32-operation claim router runtime/bindings and exact calldata. Chunk larger portfolios; recheck owner/assets, simulate and estimate gas immediately before user confirmation. Handle account/network changes, stale drafts, rejection, replacement, failure and canonical receipt/reorg recovery.
  - Mint/claim drafts have client-enforced expiry, not an on-chain calldata deadline. Discard stale drafts and prepare again; do not describe unsigned backend preparation as signing or live wallet integration.
  - Use exact decimal uint256 strings for production NFT IDs; never reuse Number-based demo identities. Historical website wording used gross$100/99% deployed with gas separate. Align current examples/reviews to ETH/fixedZZZ, $100 activation/$5 growth and the captured2% default/98% deployed floor; this task does not publish or deploy that change.
  - Local refresh is single-flight, retries only the explicit busy read response with bounded backoff, and distinguishes confirmed writes from failed balance refreshes. Writes are never automatically repeated as a new operation.
  - Qualify multiple independent devices/wallets activating, topping up and claiming concurrently: shared-pool quote movement, same-NFT transfer/claim races, account/chain changes, nonce/replacement recovery, isolated sessions and peak-load limits. Preserve exact transaction validation and confirmed-only artwork/financial state; a two-account serial Anvil fixture is not production concurrency qualification.
  - Local contribution review shows validation, progress and errors inside the dialog. Exact-contribution acknowledgement survives confirmed approval, while Entry retains a separate explicit confirmation. Only the activated/topped-up NFT shows the artwork Updating badge; stale portfolio finances/actions remain guarded.
  - Main website implementation: per-NFT/mint resources, atomic overlapping batch rejection, latest-state commits under Web Locks, bounded cross-tab waits, reset epochs and explicit persistence failures. Seventeen new focused cases plus affected domain/wallet cases and two-tab browser activation/claim checks are recorded in [scoped evidence](reports/frontend-state/VERIFICATION.md). No claim of distributed production safety or public deployment.
  - [Website/backend resilience evidence](reports/concurrent-services/VERIFICATION.md): 47 scoped Python and 90 JS passes, including source isolation, overload, cleanup, storage invalidation, nonfinite expiry, wallet/context changes and duplicate confirmation. Main-site browser/read checks and static build passed. Simulation/browser locks and the serial local signer do not establish concurrent production wallet safety.
  - NFT card presentation: fixed royalty weight follows the pattern; cards retain attached LP and active cards show combined Rewards to claim, with liquidity, components, history and lifetime claims in the breakdown. Exact currencies and unavailable values are preserved. [Scoped UI verification](reports/position-summary/VERIFICATION.md); production integration remains open.
  - New $5 increases and $100 activation are aligned in preview, local client, preparation and contracts. Preserve historical smaller preview events without permitting new ones. Earned totals sit on one line below attached LP, separate from claimable. Existing local sessions/public services are not upgraded; qualify production browser transactions and multi-user operation.
  - Match the accepted ETH-only holder payout requirement to actual on-chain conversion before displaying ETH. The older TEST-1/TEST-2 and named ZZZ/WETH/USDC/USDG fixtures remain historical evidence for their own deployments, wrapping, decimals and mock routes; they do not add current contribution currencies. Balance/faucet UX and source-to-ETH payout qualification remain open. Do not cosmetically rename generic balances or silently reset current NFTs.
  - The historical named-input fixture offered ZZZ/USDG/USDC/ETH. Current contribution inputs are ETH/fixedZZZ only; align current3 selectors, units and captured loss limits without relabeling or resetting historical sessions. Historical contribution-only dialogs/scoped refresh and exact-approval mock evidence retain their own source scope; see [local setup](docs/LOCAL_TEST_STACK.md#named-input-local-rehearsal).
  - [Gallery/reward-feedback evidence](reports/website-polish/VERIFICATION.md): one saved sample funding round preserves prior LP and claims, allocation is LP/equal-collective/rarity weighted, duplicates cannot refill it. Confirmed tier celebrations use supplied ACTI/EV audio synchronized with the image after successful contribution and fresh increased LP. The claimed-total frame is hidden without changing lifetime accounting. Single-pool UI hides redundant pool controls. These are demo/presentation improvements, not live funding or production signing.
  - [Actual local API evidence](reports/api-chain-rehearsal/VERIFICATION.md): five holder transactions, real HTTP APIs, 18-NFT aggregation and same-hash claim recovery; 46 Python and70 JS scoped cases. RPC wallet shim and mock markets/feeds/VRF do not establish actual extension or production qualification.
  - [Pending nonce diagnosis](reports/browser-wallet/PENDING_NONCE.md): 175 affected cases, two mocked browser scenarios and six actual read-only recovery observations pass. Queued or wallet-changed nonces now stop the wait immediately; journals and local-only signing remain. The actual nonce 35 mint is unmined; controlled queue reconciliation and extension acceptance remain open.
  - [Authorized local mint reconciliation](reports/browser-wallet/local-mint-reconciliation/RECONCILIATION.md): exact queued nonce35 mint removed after identity/pool checks; complete stateRoot and both account balances/nonces unchanged.13 focused checks and an isolated browser scenario pass. User MetaMask nonce-history reset, exact saved-journal archival and temporary local-overlay removal remain pending. Public signing/source unchanged.
  - [Reviewed Entry V1](docs/EXECUTION_LOSS_POLICY.md#review-time-policy-binding) now binds the caller maximum in contract/preparation/trace/inventory. Complete matching native website/wallet and real deployment/provider qualification before public activation/growth; historical clients remain incompatible, no silent fallback.
  - The published website native2 profile is historical relative to the new contract candidate. The matching accounting3/local8-word reader and unsigned-review profile are implemented and source-checked; qualify actual reviewed contracts/API/providers without relabelling existing deployments or enabling public signing. Existing Anvil fixtures and saved actions remain their original profiles.
  - [Full frontend follow-up](reports/full-audit-20261025/REVIEW.md#s-p3-4-example-website-copy-still-reflects-retired-contribution-rules): app.js example form still offers USDC/USDG and99%deployment. Align selectors/text with ETH/fixedZZZ and98%default under current3website integration before a separately authorized release. This audit preserves website source/build/server; examples do not move assets.
  - Current3 website implementation: explicit schema3 manifest, accounting3/governance2/fee1/localV4 runtime/domain bindings and ETH/fixedZZZ-only inputs; actual HTTP schema2 DTOs cover six activation/growth/approval/claim reviews. The final affected scope has451JS passes including46new methods; earlier overlapping runs are not additional coverage. Evidence: [current3 integration](reports/current3-website-20261026/VERIFICATION.md). Poplint has its own build/root/configuration; no current public deployment/API is fabricated and signing stays disabled.
  - Governance starts/closes collective exit; the reviewed optional keeper only processes bounded post-close allocation/direct payout. Never present an ordinary holder exit button or require holder action for successful automatic delivery. Show failed/deferred payments without fabricating success; preserve owner fallback only as exceptional recovery.

  </details>

<a id="task-live-history-ui"></a>

- [ ] **[Connect live history & cumulative claims](docs/EARNINGS_HISTORY.md)** - In progress. The shared production API profile displays NFT/wallet 24h/all-time earnings and collection holder allocations at current prices. Transfers retain NFT history; claims/conversions add no income. Actual ingestion, predecessor/price availability and deployment qualification remain open.

  <details>
  <summary>Acceptance criteria</summary>

  - [Production earnings delta](reports/wallet-earnings/VERIFICATION.md): bounded same-block current-holdings history and collection holder allocations are implemented in the shared API/website profile. 86 affected Python, 89 distinct JS and six isolated production-profile browser cases pass. Claims/conversions are not income; missing prices/chunks never become zero. Actual feeds/history/hosting and independent qualification remain open.
  - Local milestone: [website integration](docs/LOCAL_WEBSITE.md) and [scoped evidence](reports/local-website/VERIFICATION.md). Disposable launcher-owned accounts only; public deployment and production browser-wallet signing are not approved.
  - Display verified 24-hour/all-time earned fees separately from claimable balances. Previously claimed means lifetime per-asset LP plus royalty claims across all prior claims/owners and verified predecessor deployments, not just the last claim.
  - Connect simulated royalty cards to the separate confirmed royalty ledger and complete event history. Preserve explicit unavailable states when coverage or USD prices are missing.
  - Keep royalty_conversions as conversion history only; previously_claimed includes actual lifetime LP and royalty payouts across owners and complete configured predecessors. Do not add credited ETH again to claimable or earned totals.
  - Consume the implemented earnings endpoints and label both periods as earnings at current prices, with confirmed snapshot time. They count processed allocations, not unpaid/unharvested revenue. Show raw source amounts when a price is unavailable; never sum source earnings with conversion credits.
  - Current3 website implementation: explicit schema3 manifest, accounting3/governance2/fee1/localV4 runtime/domain bindings and ETH/fixedZZZ-only inputs; actual HTTP schema2 DTOs cover six activation/growth/approval/claim reviews. The final affected scope has451JS passes including46new methods; earlier overlapping runs are not additional coverage. Evidence: [current3 integration](reports/current3-website-20261026/VERIFICATION.md). Poplint has its own build/root/configuration; no current public deployment/API is fabricated and signing stays disabled.

  </details>

<a id="task-preview"></a>

- [x] **[Collection, artwork & portfolio preview](docs/NFT_METADATA.md#fixed-visual-inventory)** - Implemented. Browse designs, explore positions, and simulate minting, activation and both reward claims. Twin circuit routes replaces Vertical ribs in its existing slot; all 1,000 NFT assignments remain unchanged.

<a id="task-purchase-rights"></a>

- **[Show execution-time rights when buying an NFT](docs/SITE_ENVIRONMENTS.md#decisions-and-remaining-qualification)** - Not planned. User decision2026-10-26: the proposed extra NFT sale-rights UI disclosure is not required and is not scheduled. This is not an implementation claim; current-owner/unclaimed-reward rights and accurate confirmed balances remain unchanged.

  <details>
  <summary>Acceptance criteria</summary>

  - No extra purchase flow, marketplace or guaranteed listing-balance promise is introduced. Keep the original economic rights; user cancellation is not a completed feature or an unresolved launch gate.

  </details>


## Creator tasks / ZZZ team

Questions and decisions to resolve with the ZZZ token/pool creator. Answers are not yet confirmed; technical implementation stays under its linked task. Record dated answers, responsible contacts and supporting evidence here.

<a id="task-creator-zzz-price"></a>

- [ ] **[Identify two defensible independent ZZZ USD sources](docs/PRODUCTION_SERVICES.md#dependency-inventory)** - To do. Ask the ZZZ team for actual independent on-chain pricing/provider options and underlying market references. No pair is selected. Two adapters reading the same thin pool cannot establish independent economic pricing.

  <details>
  <summary>Acceptance criteria</summary>

  - Ask for two defensible independent ZZZ/USD source proposals: provider, target chain, public source/adapter addresses, denomination/decimals, underlying reporters/markets, heartbeat/deviation/history, admins/upgrades and outage support. Record absence or a shared sole market honestly rather than inventing a provider.
  - If suitable sources do not exist, discuss a supportable authenticated on-chain pricing design and independent market coverage. Team approval is input, not security qualification. Do not substitute the contribution pool instantaneous price, two wrappers of one feed, an unverified web API or an assumed stablecoin peg.
  - Engineering owns independent source/common-mode/proxy/bounds/liveness/gas qualification under [dual-source qualification](TODO.md#task-dual-price-qualification), [activation inputs](TODO.md#task-activation-assets) and [oracle security](TODO.md#task-security-strategy). The selected hookless pool does not require a Pons creator-payment agreement.
  - 25October research: the checked Robinhood catalog has an ETH/USD candidate but no ZZZ-named entry. Ask the ZZZ team for two independent defensible ZZZ USD source proposals, market coverage, administrators/update policy, operating costs and who funds any custom service. The [pool-derived reference](reports/price-reference-20261025/OBSERVATION.md) is not an approved substitute.

  </details>

<a id="task-creator-market-controls"></a>

- [ ] **[Confirm ZZZ token and selected pool controls](docs/POOL_SELECTION.md)** - To do. Confirm ZZZ token controls, upgrade/migration authorities and liquidity plans. The selected pool is hookless; no creator-payment or Pons-hook integration is required.

  <details>
  <summary>Acceptance criteria</summary>

  - Confirm the selected existing hookless ETH/ZZZ venue and independent token/pool controllers; the former Pons fee-recipient and hook-control questions are conditional historical research, not assumed new-pool authorities.
  - Confirm intended chain/token/pool identities, published verified sources, deployment provenance and current market plan. Distinguish observations from team commitments; independently match the physical PoolKey and deployed code.
  - Identify the actual controllers for token mint/transfer restrictions or taxes, token supply/transfer controls and upgradeable dependencies, where such capabilities exist. Request exact owner/admin and implementation references plus disclosure of planned changes. Do not assume the ZZZ creator controls Pons, Uniswap, wrappers or oracle providers.
  - Obtain technical contacts for external controllers when required. Team-provided addresses are inputs to [selected-pool qualification](TODO.md#task-pons-qualification) and [external-dependency review](TODO.md#task-security-dependencies), not automatic permission to admit arbitrary hooks or grant PoPL authority.
  - Ask the ZZZ team for verified actual token burn(uint256) behavior and exact totalSupply/balance reduction, plus mutable mint/burn/tax/blacklist/proxy controls. The fixed buyback implementation requires those exact burn semantics; token/pool existence is not compatibility evidence. Record the answer and qualify actual runtime before enabling buyback.

  </details>

<a id="task-creator-input-liquidity"></a>

- [ ] **[Confirm ETH/ZZZ market and token references](docs/ACTIVATION_ENTRY.md)** - To do. Ask the ZZZ team to confirm the exact token identity, issuer-migration plans and actual ETH/ZZZ market/liquidity references. Only ETH and reviewed ZZZ are contribution inputs; public evidence must independently qualify prices and execution.

  <details>
  <summary>Acceptance criteria</summary>

  - The ZZZ team may point to markets but does not choose PoPL governance or waive guards. Engineers verify provenance, code/approvals, feeds and full $100-to-LP execution within the captured contribution limit (2% by default), gas separate, under [activation qualification](TODO.md#task-activation-assets) and [complete quote preparation](TODO.md#task-activation-quotes). Disable unsupported inputs rather than assume a route remains liquid.

  </details>


## Testing & qualification

Three required testing layers, with source-bound evidence.

<a id="task-testnet-rehearsal"></a>

- [ ] **[Robinhood Testnet end-to-end rehearsal](docs/RELEASE_CHECKLIST.md#required-testing-layers)** - To do. Exercise wallet flows, the website, keeper operations and deployment with explicit records of unavailable or mocked dependencies.

  <details>
  <summary>Acceptance criteria</summary>

  - **Robinhood Testnet:** wallet flows, website integration, keeper operations and deployment rehearsals, with actual supported services and explicit records of any mocked or unavailable dependencies.
  - Complete actual Robinhood Testnet end-to-end operation, physical host-loss/key-rotation rehearsal and independent audit/configuration approval.
  - Exercise actual entry, top-ups, fee funding/claims, royalties, transfers, rebalances, live keeper signing/recovery, indexer backfill/reorgs and alerts. Record mock or unavailable dependencies; Sepolia and local Anvil supplement but do not replace Robinhood-specific qualification.
  - Treat the local $1 variant as separate test evidence. A public testnet wallet flow still needs a reviewed deployment, services and frontend configuration; do not promote the reduced minimum into production. Any real production defect exposed by rehearsals requires a production fix, focused regression and refreshed source-bound evidence.
  - [Keeper/LP audit](reports/keeper-lp-audit-20261026/REVIEW.md) binds health to exact loaded config, rejects malformed conversion controls, repairs obsolete range-test domain and selects current3/fee1/native rehearsal source. Final affected Python354pass/5Unix skips (359methods),9range methods incl1000fuzz; unchanged production Solidity/permissions/economics. Linux current-fixture process/systemd, actual feeds/routes/gas/services and independent audit remain open. Deploy matching health writer/checker only under separate rollout; never patch old hashes or reset journals.

  </details>

<a id="task-capacity-campaign"></a>

- [ ] **[Deferred: 10/25/100-user load campaign](reports/local-wallet-concurrency/MANUAL_ACCEPTANCE.md#accepted-sequencing)** - To do. Deferred by the user on 2026-10-20; revisit after launch if needed or on explicit request. Production capacity remains unverified. This campaign is not the next development priority and is not scheduled.

  <details>
  <summary>Acceptance criteria</summary>

  - Measure preparation/read latency, overload behavior, provider quotas, recovery and accounting at 10, 25 and 100 simultaneous users when resumed; do not infer capacity from the two-wallet rehearsal.
  - Deferral does not waive independent user-wallet signing, bounded API concurrency, safe recovery, qualified dependencies or independent release approval. Keep the local shared signer/global lock test-only.

  </details>

<a id="task-mainnet-rehearsal-retirement"></a>

- [ ] **[Qualify a separate real-funds rehearsal and cleanup plan](docs/POST_SEAL_POLICY.md#testing-with-real-funds-on-robinhood)** - To do. Plan an isolated, clearly named Robinhood mainnet rehearsal before a fresh final collection. The current contracts have no burn/reset or independent empty retirement. This design request does not authorize deployment, public signing or real transactions.

  <details>
  <summary>Acceptance criteria</summary>

  - Require an independently reviewed exact candidate/configuration, dedicated funds, authority/service addresses, actual signer permissions, per-operation/campaign spending limits, simulations, receipts and stop conditions before operator-executed public actions. Keep the shared website signer Anvil-only.
  - Test actual venue LP fees and funded royalty accounting separately from genuine marketplace royalty receipts. Qualify OpenSea primary mint explicitly; local direct minting does not prove marketplace compatibility.
  - Reconcile pending transactions and stop new exposure. If a collective shutdown is intended, governance starts irreversible holder exit and completes all bucket closes/allocations/direct payouts. Pending compound joins principal; old rewards/royalties, buyback reserves, prefunds and mint payments stay separate. Public chain records cannot be erased.
  - Archive all receipts, manifests, final balances and unresolved obligations. Rehearsal chain/marketplace history and minted NFTs cannot be erased. Whole-collection retirement preserves rights in a funded successor; it is not a reset.
  - Deploy the final collection freshly after qualification; do not reuse consumed mint/rarity inventory or assume rehearsal NFTs become final NFTs. Reduced-minimum public tests would be a separate candidate and require explicit review, not the local-only dollar build.

  </details>

<a id="task-mainnet-fork"></a>

- [ ] **[Robinhood mainnet-fork qualification](reports/current-pool-fork-20261026/VERIFICATION.md)** - In progress. A current accounting3 fixture and bounded read-only runner now exercise the actual selected ETH/ZZZ pool via Pinax at an exact block/runtime. Eleven distinct methods have successful source-bound evidence across affected runs; no fresh whole final11-suite pass is claimed. ETH/ZZZ contributions, small growth, real fees/transfer rights and unsafe-growth rollback are covered with explicit mock governance/VRF/USD services. Actual independent feeds, routes, keeper/gas and provider qualification remain open.

  <details>
  <summary>Acceptance criteria</summary>

  - Robinhood mainnet fork: qualify the actual selected hookless ETH/ZZZ pool and deployed dependencies against exact release sources. Historical Pons execution retains its original scope and is not selected-pool qualification; read reports/hookless-pool/VERIFICATION.md for current coverage.
  - Stage actual Uniswap swaps/entry/maintenance, malicious token/callback behavior, exact approvals/settlement, stale prices, donations and failures.
  - The earlier29 selected-native/nine alternative-pool inventory is historical. Do not claim these fixtures or counts as current accounting3 coverage after wrapped fixtures are retired; the active runner must fail explicitly until a reviewed replacement exists.
  - The obsolete wrapped-accounting NativePoolFork fixture was explicitly retired in the simplification audit; it is not current accounting3 qualification. Rebuild/review a real selected-pool native fixture before claiming fork coverage for the new candidate.
  - [Current fork evidence](reports/current-pool-fork-20261026/VERIFICATION.md):11distinct successful EVM methods are composed from8+1+1+1source-bound scopes;11focused runner methods pass. No overlapping attempt counts are added. Pinax archive single reads work at block96,427,989; an observer batch failed429. Maintain strict whole11-method/no-skips future result gates, read-only relay/process cleanup/JSON/redaction and exact runtime/state/source pins; no production provider/feed/VRF/authority or keeper qualification is implied.

  </details>

<a id="task-audit-release"></a>

- [ ] **[Independent audit and release approval](docs/RELEASE_CHECKLIST.md)** - In progress. Complete an external audit, remediation, gas/strategy review and final operating/configuration sign-off before any real funds.

  <details>
  <summary>Acceptance criteria</summary>

  - **Local tests:** minting, activation, rewards, royalties, transfers and security.
  - Reproduce all Solidity/Python tests for the final frozen production release on supported Ubuntu, retaining exact source revision, compiler settings and full logs. Candidate CI and earlier green CI for `5febe70` do not validate future source changes.
  - Compile every contract/test/script and check normal runtime/initcode limits, constructor-argument allowance (including the claim router) and current gas; all small bytecode margins require explicit review.
  - Independently review the final source-bound Slither triage and accepted risks, refreshing analysis if source changes. Completed internal triage does not close the external audit gate.
  - Complete an independent external security audit, remediation verification and separate deployment/configuration review, then limited staging with approved limits.
  - Complete qualified current services, frozen-release independent audit and operating rehearsals. The hookless launch pool earns LP fees directly; creator-payment receivers/terms/measurement tools and integrated bridge/remote-proof execution are removed. Marketplace royalties retain their separate funded ledger; external custodian conduct remains an explicit trust boundary.
  - Complete the seven [security audit workstreams](docs/SECURITY_AUDIT_PLAN.md), including qualification of the implemented same-chain whole-collection handoff while the source works. Cross-chain canonical transport is deferred optional scope, not a current launch/sealing requirement. Post-halt recovery is deferred; LP migration alone is insufficient. Allocation percentages remain fixed; evaluate any proposed configurability separately.
  - Fill and independently authenticate the schema-5 production inventory with explicit mint_integration_version1: release-specific source/configuration, code and helper bindings, assets, randomness, parking rehearsal and operating evidence. Its current blocked state is intentional; offline consistency never authorizes deployment, sealing or real funds.
  - Preserve complete exact-release local/Ubuntu, actual Robinhood mainnet-fork and Robinhood Testnet evidence. Partial/cancelled fork runs and older source snapshots do not qualify the final release; test timeouts must retain partial evidence without counting as a pass.
  - Keep fork inventory assertions aligned with actual published fixtures and preserve normal assertion failures. Earlier [CI fixture correction](reports/architecture-evolution-ci/README.md) covers historical24native/Pons plus9hookless cases only. Current fixture retirement and source profiles must not be hidden by a mock, renamed pass or stale inventory count.
  - Review explicitly archived obsolete pre-pricing ActivationEntry/creator/bridge fixtures and their source receipts; retain actual current Entry/Pricing security assertions in active integrations. Qualify the final frozen repository workflow without treating a targeted pass or retired test as a green full regression.
  - Implemented [frozen review package and strict verification](docs/FROZEN_REVIEW_BUNDLE.md): committed blobs, source/tree/dependency identities, required inputs and excluded-path inventory; no extraction, arbitrary execution, overwritten output or forged approval.19 distinct focused Python methods across recorded scopes. Regenerate for the final exact release commit and independently verify its hash; dependencies, operating rehearsals and external audit are not bundled or passed.
  - Run fresh complete frozen-release regression and source-bound static analysis/triage; the deep-cleanup campaign is targeted local evidence, not a green full workflow, live provider qualification, operating rehearsal or independent audit. The new reference snapshot2 requires exact imported dependency and build-file bindings.
  - The [day audit](reports/day-readiness-20261025/READINESS.md) found then-stale Slither triage. The [full audit](reports/full-audit-20261025/static-review-verification.json) replaces it with an actual current399-finding review bound to47source/build names: internal review-coverage PASS. This does not qualify accepted gas/token/custody risks, a fresh full release suite, published CI or independent audit/remediation/sign-off.
  - Current [full review](reports/full-audit-20261025/REVIEW.md) leaves real feed/route/VRF/authority/OpenSea/current-website/service/target-gas and exact constructor qualification open. Fresh11Python/oneEVM scopes and reviewed static output are not global production approval. Preserve original failures, trusted custody disclosures and known admitted-only late-currency recovery scope.
  - [Keeper/LP audit](reports/keeper-lp-audit-20261026/REVIEW.md) binds health to exact loaded config, rejects malformed conversion controls, repairs obsolete range-test domain and selects current3/fee1/native rehearsal source. Final affected Python354pass/5Unix skips (359methods),9range methods incl1000fuzz; unchanged production Solidity/permissions/economics. Linux current-fixture process/systemd, actual feeds/routes/gas/services and independent audit remain open. Deploy matching health writer/checker only under separate rollout; never patch old hashes or reset journals.
  - [Systematic adversarial review](reports/system-adversarial-20261026/REVIEW.md) maps all 608 functions,31 constructors and13 receivers to multiple source-review cases;1,987 scenario instances are not execution tests. The final 244-method scope has 241 passes/3 explicit skips,42 new included once, with source-stage failures retained. Unchanged Solidity/static evidence is reused at exact pins; independent frozen-release audit/remediation and external qualification remain open.

  </details>

<a id="task-local-verification"></a>

- [x] **[Local contract and integration tests](reports/preproduction-audit-20261025/VERIFICATION.md)** - Implemented. Source-scoped local unit/invariant/integration evidence is recorded, including the October25 installed-v4 composition harness and repaired non-vacuous growth invariant. Keeper audit records199 distinct scoped passes and one Unix-only skip. Earlier receipts retain their source scope; these are not a fresh full regression, actual providers or production approval.

  <details>
  <summary>Acceptance criteria</summary>

  - The [day audit verification](reports/day-readiness-20261025/VERIFICATION.md) adds3project EVM cases,4isolated Access gas comparisons and83distinct Python methods across scoped runs. New native tests independently exercise partial exact-input rejection and intended uint128 bounds.37normal gates reuse exact75-source bindings;265-input AST refreshed for one changed test. Earlier full/regional counts retain their original scope; no new full regression is claimed.
  - [Full audit verification](reports/full-audit-20261025/VERIFICATION.md):11distinct scoped Python passes (9new/2compatibility), one new cold-capacity optional-currency gas case at9,591,082<12M,265closed AST inputs, fresh actual399-flag Slither triage and37unchanged object lengths from successful solc output. Forge postcompile signature-cache CLI failure and analyzer bootstrap repair remain explicit; no unchanged broad suite rerun or full release approval.

  </details>

<a id="task-economic-rights-audit"></a>

- [x] **[Verify NFT economic rights at full collection size](reports/nft-rights-audit/VERIFICATION.md#integrated-collection-and-stateful-assertions)** - Implemented. Internal ownership, 1,000-NFT payouts, buyback rollback and dual-ledger invariants verified: 531 offline Solidity passes, two intentional fork setup skips; extended rights invariants completed 65,536 calls. This closes the scoped local verification task, not independent audit or production qualification.

<a id="task-local-dollar-rehearsal"></a>

- [x] **[Isolated $1 activation rehearsal](docs/ONE_DOLLAR_REHEARSAL.md)** - Implemented. The isolated generator derives its current2% default and hard10% contribution cap from actual production declarations; the historical strict1% test fixture is explicit. It lowers only local activation to$1 with31337 constructor guards; growth remains$5 and mint0.05ETH. Prior runtime and latest generation/typecheck evidence are separate; no existing deployment/public funds changed.

<a id="task-local-browser-stack"></a>

- [x] **[Run a disposable local browser integration stack](docs/LOCAL_TEST_STACK.md)** - Implemented. Disposable Anvil core, indexed confirmed balances/history, launcher wallets and an opt-in independent browser-wallet path are implemented. The native fixture supports exact approval/Entry and ETH claims. Venue, prices and randomness are substitutes; actual extension acceptance and production qualification remain open.

  <details>
  <summary>Acceptance criteria</summary>

  - [Scoped evidence](reports/local-stack/VERIFICATION.md): 39 expanded Anvil journey assertions and 35 launcher/HTTP/recovery cases pass. Strict inputs, duplicate-request recovery, stale revisions and uncertain-submission stops. Unchanged production Solidity suites were not repeated.
  - Existing website artwork is read locally. No production website source, public server, private key, public transaction or paused-monitor change.
  - User reported all six proposed local two-wallet scenarios passed on 2026-10-20: activation, top-ups, cancel after approval/reopen, pending refresh recovery, concurrent claim/contribution and invalid inputs. [Manual acceptance](reports/local-wallet-concurrency/MANUAL_ACCEPTANCE.md) is user-reported evidence, not a new automated run or production qualification.
  - Independent browser path: five actual local holder transactions exercised mint, native ETH activation, exact USDC approval, USDC top-up and ETH claim without the backend holder signer. All four original fixture owner/LP/activation records were preserved. [Evidence](reports/browser-wallet/VERIFICATION.md) distinguishes the EIP-1193-shaped RPC adapter from browser-extension acceptance and includes 43 affected Python / 167 website cases. New fixture setup preserved historical run directories; no public transaction or load campaign.

  </details>


## Security & audit

Seven audit workstreams. Local checks are partial evidence; independent review and release sign-off remain open. See [the security audit plan](docs/SECURITY_AUDIT_PLAN.md) for acceptance criteria and priorities.

<a id="task-security-governance"></a>

- [ ] **[Governance, permissions & sealing](docs/SECURITY_AUDIT_PLAN.md#1-governance-permissions-and-sealing)** - In progress. Audit every role, governance controller, configuration and external-module trust boundary for a path around nonredeemable custody. Prove sealed bindings stay fixed and supported asset/feed/route/parameter changes remain bounded; review malicious destinations, lost keys and emergency powers.

  <details>
  <summary>Acceptance criteria</summary>

  - Independently audit [immediate governance](docs/GOVERNANCE.md): no advance notice window, direct governance-wallet/target authorization, exact module bindings, two-step governance handover, canonical lifecycle locks and guardian/keeper separation. No scheduler, proposer/executor roles or queued predecessor operations remain. An approved malicious feed, route, provider or successor can act immediately; review multisig security and acknowledge that trust explicitly.
  - Review enable/disable/re-enable controls for native ETH and the one fixed pre-seal ZZZ identity, plus independent royalty-asset admission and converter wrapper policies. No third contribution token or post-seal ZZZ identity replacement is supported. Disabling a source must preserve earned rights and recovery. Ordinary exits remain price-guarded; parking/raw exit use separately approved raw bounds. Rehearse feed repair without promising recovery through failed venues, tokens or custodians.
  - Independently stage paused parking through the sealed governance controller: missing/stale feeds, venue/token failures, exact share/LP/custody snapshot, close-only minimums excluding idle/compound/donations, one-sided principal, invalidation/replay/expiry, claims/transfers and fresh-oracle resume. Authenticate current-source evidence in the inventory mandatory `parking_rehearsal` record; no creator inbox exists to synchronize.
  - Review external EOA/contract custody and governance-approved different-code successors: an approved recipient may divert or lose assets and the source cannot compel return. Code/configuration pins do not prove honest custody or successor economics. Preserve fixed80/10/5/5; no percentage setter, arbitrary executor, general sweep or generic implementation upgrade is authorized.
  - Independently review the implemented canonical preparation notice: existing controller-only start/cancel, exact notice binding, blocked new economic work and protocol configuration, trailing callback guards, and fixed parking/plan-cancellation drains. Guardian pause and governance unpause remain; direct governance2 authorizes calls under module and canonical lifecycle guards, without inherited timelock roles or scheduling. The notice grants no successor authority and cannot freeze or export canonical rights.
  - Independently review/rehearse [mint/pool stop controls](reports/operator-controls/REVIEW.md): disable-only flags, full reopening validation, callback rollback, unchanged roles/canonical locks, obsolete approved operations and explicitly reviewed successor mint-pause state.
  - Governed custody candidate: surface source principal and royalty-currency in-transit states as unavailable, preserve funding/claim history and never count restoration as new income. Update services/inventory/operator alerts and holder disclosures for explicit external EOA/contract custody trust; no auto resend, timeout recovery, invented remote NAV or legacy v3 migration calls.
  - Operator documentation must distinguish global pause from a custody freeze: approved pause-only principal/royalty exits remain possible. Loss defaults are not immutable: governance can set future categories up to10%, without weakening an original approved absolute custody floor. Independently review immediate-quorum and approved-recipient/replacement trust.
  - [Reviewed Entry V1](docs/EXECUTION_LOSS_POLICY.md#review-time-policy-binding) now binds the caller maximum in contract/preparation/trace/inventory. Complete matching native website/wallet and real deployment/provider qualification before public activation/growth; historical clients remain incompatible, no silent fallback.

  </details>

<a id="task-security-share-accounting"></a>

- [ ] **[Shared LP accounting & economic manipulation](docs/SECURITY_AUDIT_PLAN.md#2-shared-lp-accounting-and-economic-manipulation)** - In progress. Verify 1,000 independent NFT share accounts through deposits, top-ups, compounding, rebalancing and migrations. Extend local conservation and gas evidence with adversarial prices, donation/front-running, dilution, rounding and multi-asset economic tests on qualified venues.

  <details>
  <summary>Acceptance criteria</summary>

  - Review physically received venue fees, pre-entry dust/index checkpoints and incumbent compound NAV across the four permanently admitted/historical buckets. Verify original input, actual marginal LP, classified reserves, exact transfers, donation exclusion and raw-unit rounding under each admitted reward/royalty currency. Qualify actual Entry/selected hookless-pool gas; retired creator inboxes, payment terms and receiver-factory ceilings are not current accounting paths.
  - Review [dynamic-liquidity evidence](reports/dynamic-liquidity/VERIFICATION.md): independent price/decimal range vectors, current-NAV entry and compound exclusion, loss/appreciation/replacement/transfer continuity. Extend the bounded local/mock evidence with actual production routes, calibrated strategy backtests and full configuration gas/MEV qualification.
  - Review [the October25 composed installed-v4 harness](reports/preproduction-audit-20261025/VERIFICATION.md) for actual fees, royalty/LP separation, growth/compound/rebalance/transfer conservation, prefund isolation and rollback. Local governance/feeds/VRF/Permit2/admission remain substitutes; extend actual provider/venue qualification, not unchanged generic test reruns.
  - [Full principal review](reports/full-audit-20261025/PRINCIPAL.md) traces old compound/fees, marginal deployedLP, exact prefunds/native callbacks, share issuance and captured price/loss marks. No new unprivileged dilution path confirmed in inspected code.3%feed agreement does not guarantee2%execution feasibility; real depth/source quality/economics and independent review remain required.
  - [Reporting conservation review](reports/backend-remediation-20261026/REVIEW.md): replay separates gross LP intake, holder/collective credits, carried dust and compound/buyback reserves. This repairs reporting integrity without changing share issuance or on-chain economics; final167Python methods do not requalify real venue economics.
  - [Actual-v4 market cases](reports/market-adversarial-20261026/VERIFICATION.md) cover ETH activation and fixed-ZZZ growth entirely above/below the old range, then rebalance/claims, plus real PoolManager donations before a newcomer.15affected shared-fixture methods pass; original missing-ZZZ-identity fixture failures are retained, not hidden. No production contract/economic change.

  </details>

<a id="task-security-ownership-rewards"></a>

- [ ] **[Ownership, claims & allocation rules](docs/SECURITY_AUDIT_PLAN.md#3-nft-ownership-and-reward-distribution)** - In progress. Verify all unclaimed balances and fractions follow the NFT, including transfer/claim ordering, callbacks, operators and pending receipt synchronization. Preserve fixed 80/10/5/5 with documented dust and separate funded rarity royalties. Assess configurable splits against practical benefit and added governance risk before any proposal; no percentage setter is implemented or authorized.

  <details>
  <summary>Acceptance criteria</summary>

  - Independently verify isolated 0.05 ETH mint proceeds, the 1,000-NFT cap, exact 600/300/100 quotas, atomic failure and no reroll/trait override.
  - Independently verify actual-receipt80/10/5/5 allocation, local holder/collective funding, equal activated-NFT membership and index/fractional solvency across transfers, entries, maintenance and same-chain handoff. The current profile has no remote90% delivery branch; ensure historical remote events cannot be reinterpreted as new local receipts.
  - Independently review the 5% ERC-2981 request and 100% eligible royalty redistribution in the separate immutable ETH/ERC20 ledger at activated rarity weights 1/2/3. Marketplace payment remains voluntary.
  - Configure OpenSea creator earnings to the actual `NFT.royaltyRewards()` helper at 5%, verify collection-administration access and each admitted payout asset, and stage a paid sale through receipt, weighted claim and NFT transfer. The current contract requests optional earnings; it does not implement ERC-721-C enforcement.
  - [On-chain safety/cost review](reports/onchain-safety/REVIEW.md) and [scoped verification](reports/onchain-safety/VERIFICATION.md): bounded sequencer calls, fresh memory-only Strategy prices, packed contribution bounds and static-loop reward contexts preserve accounting/rounding/final guards. 145 distinct Solidity cases, 83 backend checks and 37 normal object gates are source-scoped; actual dependencies, target-chain gas and independent audit remain open. No new authority or automatic fallback.
  - [Fee-breakdown review](reports/backend-remediation-20261026/REVIEW.md): lifetime earnings are individual+collective+royalty income including earlier payouts, distinct from current claimable and lifetime claimed. Claims/conversions/imports are not new earnings; transfers and top-ups preserve past entitlements. Independent rarity/LP-weight example and final affected167methods pass; independent audit remains open.
  - [Contract-owner callback review](reports/system-adversarial-20261026/RIGHTS.md) confirms that a payout can legitimately fund pending royalties or consume another owned ledger before later router entries. Do not impose unconditional initial-view/payout equality or reinterpret a valid callback change as fabricated income; current-owner/atomic liability rules remain.

  </details>

<a id="task-security-strategy"></a>

- [ ] **[Oracles, keepers, strategies & MEV](docs/SECURITY_AUDIT_PLAN.md#4-oracle-keeper-and-strategy-vulnerabilities)** - In progress. Test compromised keepers, stale/manipulated prices, repeated rebalances, unfavorable swaps and sandwich/MEV costs. Qualify execution bounds, cooldowns, fee/gas budgets and outage policies with actual venues; access control alone does not prevent economic loss or impermanent loss.

  <details>
  <summary>Acceptance criteria</summary>

  - Qualify gas for1/100/1,000 NFTs and the maximum actual reward/royalty assets and four historical buckets; prove upkeep scales by shared pool. Backtest ranges, triggers, cooldowns, slippage, impermanent loss, MEV and operating cost. Production strategy parameters remain unset; creator inbox gas is retired.
  - Keep the unchanged12M local combined-workload budget and four-historical-bucket cap. Qualify actual Entry/selected hookless-pool/token, historical-reserve and royalty-checkpoint costs, not only local shared-pair fixtures; refresh normal runtime/initcode gates including exact release constructor arguments.
  - Independently qualify the implemented default3% loss cap (governed up to10%) for ordinary rebalance and atomic same-ordered-pair local move/resume, including the cached pre-harvest valuation vector, attributed compound, close/swap/mint costs, idle ceiling, callback repricing, MEV and repeated moves. Initial oracle honesty, venue backing and cumulative erosion remain risks; different-pair execution remains external custody trust, and integrated bridging is deferred optional scope. Activation/top-ups default to2%, independently governed up to10%.
  - The new metadata spot/oracle guard and fixed-price rebalance cap require independent review. The default per-operation3% ceiling is not a target cost or a cumulative loss budget. Qualify real close/swap/mint execution, oracle/venue honesty, range/trigger/cooldown choices and outages before funding.
  - Independently qualify the implemented [range-policy application](docs/RANGE_POLICY_UPDATES.md): the governance-approved pool config authorizes a current-tick mismatch at the stored center through ordinary rebalance, preserving cooldown, oracle/minima, captured maintenance loss floor (default3%, maximum10%) and idle limits and NFT rights. Review repeated-change costs and current-config execution/resimulation; no separately privileged force path or config-version lock is added. [Scoped evidence](reports/range-policy/VERIFICATION.md) is not live strategy qualification.
  - User decision 2026-10-19: keep the 3% per-operation cap only, no rolling/cumulative loss breaker. Monitor cumulative turnover/MEV/gas costs and rehearse operator pause/parameter recovery; see [range management](docs/OPERATOR_MANUAL.md#range-and-strategy).
  - Internal 2026-10-24 review found and fixed ERC20 destination fee sizing; no new cap or authorization bypass was found in the reviewed diff. Earlier fork receipts retain their old source scope; use the new focused source-bound audit evidence rather than treating older passes as a current full regression.
  - Review the implemented [two-source price and factual LP guard](docs/PRICE_SECURITY.md), including common-mode/proxy authority, depeg/outage, pre-pull frozen prices/caps, exact deployment spot, historical incumbent backing, gas/DoS limits and coherent backend traces. Real source qualification remains [open](TODO.md#task-dual-price-qualification).
  - [On-chain safety/cost review](reports/onchain-safety/REVIEW.md) and [scoped verification](reports/onchain-safety/VERIFICATION.md): bounded sequencer calls, fresh memory-only Strategy prices, packed contribution bounds and static-loop reward contexts preserve accounting/rounding/final guards. 145 distinct Solidity cases, 83 backend checks and 37 normal object gates are source-scoped; actual dependencies, target-chain gas and independent audit remain open. No new authority or automatic fallback.
  - Historical thin-market finding A-07: the original one-pass native fixture retained about$99.38 but deployed only$98.85 and safely reverted at1%. The [bounded two-pass candidate](docs/IDLE_AND_DUST.md) addresses ratio drift and the user separately approved2% default; qualify actual markets and complete traces, preserving all guards. Neither a higher cap nor this local correction qualifies every route.
  - [Keeper/LP audit](reports/keeper-lp-audit-20261026/REVIEW.md) binds health to exact loaded config, rejects malformed conversion controls, repairs obsolete range-test domain and selects current3/fee1/native rehearsal source. Final affected Python354pass/5Unix skips (359methods),9range methods incl1000fuzz; unchanged production Solidity/permissions/economics. Linux current-fixture process/systemd, actual feeds/routes/gas/services and independent audit remain open. Deploy matching health writer/checker only under separate rollout; never patch old hashes or reset journals.

  </details>

<a id="task-security-dependencies"></a>

- [ ] **[External dependencies & receipt backing](docs/SECURITY_AUDIT_PLAN.md#5-external-dependencies-and-revenue-accounting)** - In progress. Review selected hookless Uniswap v4, actual tokens, converter wrappers, two-source pricing, randomness and externally chosen custodians for upgrades, compromise, outages and unexpected behavior. Reconcile every asset liability to actual receipts; test quarantine, duplicate/delayed recognition, token failure and approved-dependency changes. External bridges or issuer exchanges chosen by a custodian remain outside PoPL custody guarantees.

  <details>
  <summary>Acceptance criteria</summary>

  - Independently qualify implemented royalty-token outage isolation: failed optional balance reads defer only new membership for that currency. Recovery protects the earlier cohort and exact liabilities. Single-asset healthy claims continue, while syncAll and exact unreadable canonical backing can still fail. Do not blindly skip old receipt/eligibility checkpoints.
  - The [royalty conversion and outage candidate](docs/ROYALTY_SETTLEMENT.md) isolates optional-token activation failures and preserves earned balances. Actual token/wrapper/route behavior, runtime inventory, eligibility UI and live recovery still require qualification; native ETH has no external ERC20 balance query.
  - Pons hook/creator-payment intake is removed from the current release. Qualify actual LP-fee collection, independent prices and cheaper ETH-conversion routes. Preserve captured conversion policy (1% default; governance maximum10%), stronger caller/venue minima and separate gas; the selected approximately1.101% fee does not qualify full conversion under the default1% cap.
  - Review the implemented [two-source price and factual LP guard](docs/PRICE_SECURITY.md), including common-mode/proxy authority, depeg/outage, pre-pull frozen prices/caps, exact deployment spot, historical incumbent backing, gas/DoS limits and coherent backend traces. Real source qualification remains [open](TODO.md#task-dual-price-qualification).
  - Review the frozen compiler/dependency closure and current official advisories using [applicability triage](reports/deep-cleanup-20261025/UPSTREAM.md). The final source graph has no internal recursion/named-error require trigger, but is not a compiler proof or independent approval. Recheck actual compiler-generated behavior on any compiler/dependency change.
  - Qualify the actual fixed ZZZ burn(uint256) ABI, exact holder-balance/totalSupply reduction, upgrade/blacklist controls and target route before enabling buyback. The immutable target and successful pool ERC20 transfers alone do not establish burn compatibility. A failed burn reverts; do not substitute an arbitrary transfer-to-wallet as proof of burn.
  - [Exact slot0 input checks](reports/market-adversarial-20261026/REVIEW.md) reject contradictory pool state and malformed fees in unsigned reviews/release observations. A consistent fabricated RPC result or correlated USD sources remain external qualification risks; no single-source fallback is introduced.

  </details>

<a id="task-security-chain-recovery"></a>

- [ ] **[Whole-protocol recovery & canonical chain loss](docs/CANONICAL_HANDOFF.md)** - In progress. Qualify pre-exit same-chain whole-collection handoff of ownership, inventory, shares, reward ledgers and exact backing. Collective holder exit permanently blocks this importer. Future-chain/post-halt recovery and post-exit royalty-only successors remain unsupported.

  <details>
  <summary>Acceptance criteria</summary>

  - Independently qualify the implemented planned same-chain whole-protocol handoff while the source still works: preserve NFT ownership, immutable traits, LP shares, both complete funded ledgers and classified backing. External principal custody alone does not relocate those rights. Post-halt and future-chain recovery remain deferred; no emergency owner rewrite is authorized.
  - For the same-chain canonical handoff, preserve one successor epoch, source freeze, NFT ownership/traits/shares, LP/royalty credits and fractions, exact backing, preparation/retirement history and old-deployment replay rejection. An external custody receipt or copied snapshot does not retire the old ownership ledger.
  - Deferred optional future-chain scope, not a current launch/sealing gate: Implement the selected verified-finality requirement: destination activation must authenticate finalized source retirement through an independently qualified chain-specific proof mechanism. No multisig/manual override, timeout activation or signer-attestation fallback is authorized. The concrete verifier/provider and finality configuration remain unselected; source terminal commitment must precede successor rights and cannot be reversed afterward.
  - Drain original ordered VRF/reveal and resolve outstanding principal/royalty custody before freeze. The user selected provider qualification plus reveal drain, not pending-request carry. Preserve exact IDs/traits, remaining supply/quota/inventory, owners and per-asset liabilities/fractions; never reconstruct balances from website data.
  - Retain safe late royalty-receipt handling and historical marketplace receiver forwarding after same-chain handoff. No double claims, duplicated canonical NFTs, erased backed obligations, principal refunds or arbitrary administrator transfers. The retired creator-payment receiver is not a current forwarding domain.
  - No external custody or bridge executor remains. Future-chain whole-collection relocation and post-exit royalty-only successor import require separately reviewed implementations; canonical V5 handoff is available only before collective LP exit.
  - Independently qualify implemented same-chain cutoff, bounded exact export/import, classified backing, single-successor retirement, funded abort and late-royalty forwarding. Benchmark cutoff capture, ordered domain settlement, eight-row batches, each funding leg and final activation across1,000NFTs, four historical buckets,33LP/reward currencies including native ETH and17royalty slots under unchanged limits. Creator-inbox settlement is removed.
  - Historical bridge/event records keep their original profile and must not be imported as current canonical LP-only V4 ledger rows (distinct from local Position V3). The current release has no outbound bridge channels to configure, close or reopen. Any later future-chain design requires a new reviewed compatibility/finality boundary; this is deferred, not a release gate for current source-chain custody and same-chain handoff.
  - Deferred optional future-chain scope, not a current launch/sealing gate: Review compatible successor templates, code/configuration commitments and all owner/helper bindings. On 2026-10-17 the user explicitly accepted governance approval of different reviewed replacement code. A malicious approved replacement could divert LP; code hashes alone do not prove nonredeemability. This accepted trust does not waive exact backing, single-successor/source-retirement or verified-finality requirements.
  - Rehearse contract-holder and marketplace escrow compatibility with the new collection address. Import preserves owner addresses without ERC721 callbacks and cannot prove an old escrow can release a replacement NFT. Verify retirement notices, source/destination metadata, old listings and historical royalty receiver forwarding. The [read-only preflight](docs/HOLDER_PREFLIGHT.md) now inventories pinned ownership/code and flags unresolved holders. Repeat after freeze; incomplete coverage or unreviewed escrow release behavior prevents operational sign-off.
  - Historical canonical-handoff qualification recorded 582 regression cases plus 34 focused handoff cases, two opt-in fork setup skips, repaired bridge fixtures and three cold-gas suites. These retain their original source scope. The latest Vault/metadata changes have separate [dynamic-liquidity evidence](reports/dynamic-liquidity/VERIFICATION.md), not a new complete handoff regression. Preserve failed diagnostics, verify exact-commit Ubuntu CI and obtain independent review plus real operating qualification before release.
  - Qualify the selected [provider-and-drain operator policy](docs/OPERATOR_MANUAL.md#whole-collection-replacement) against AUD18-02: no new mints during preparation, all original draws finalized before freeze. An unfulfilled request can still block replacement; document postponement/cancellation and provider escalation. No reroll/admin override/pending-request carry is authorized.

  </details>

<a id="task-security-integration"></a>

- [ ] **[Cross-contract & infrastructure audit](docs/SECURITY_AUDIT_PLAN.md#7-cross-contract-and-infrastructure-vulnerabilities)** - In progress. Audit complete transaction paths and failure rollback across contracts, frontend, API/indexer, deployment, keys and keeper services. Rehearse reorgs, replay, stale or compromised data, wrong-chain signing, RPC failure, restore/rotation and monitoring. Independent review and operational sign-off remain open.

  <details>
  <summary>Acceptance criteria</summary>

  - The [review of all October 18 changes](reports/daily-security-20261018/REVIEW.md) records source inspection, exact evidence hashes, one new availability reproduction, and accepted governance/economic plus VRF/escrow recovery risks. It identifies no new unauthorized withdrawal path but does not close independent audit, service qualification or final-release testing. Resolve findings under their owning tasks without silently adding governance delays.
  - The [October 19 internal review](reports/topup-and-reward-review/REVIEW.md) covers contribution floors, current contract changes and request/display boundaries. Optional local history failure no longer hides confirmed balances; work-limit/core failures remain fatal and dormant reads skip history. Live concurrent load, exact deployment inventory and independent audit remain required.
  - Governed custody candidate: surface source principal and royalty-currency in-transit states as unavailable, preserve funding/claim history and never count restoration as new income. Update services/inventory/operator alerts and holder disclosures for explicit external EOA/contract custody trust; no auto resend, timeout recovery, invented remote NAV or legacy v3 migration calls.
  - [On-chain safety/cost review](reports/onchain-safety/REVIEW.md) and [scoped verification](reports/onchain-safety/VERIFICATION.md): bounded sequencer calls, fresh memory-only Strategy prices, packed contribution bounds and static-loop reward contexts preserve accounting/rounding/final guards. 145 distinct Solidity cases, 83 backend checks and 37 normal object gates are source-scoped; actual dependencies, target-chain gas and independent audit remain open. No new authority or automatic fallback.
  - Review [the October25 internal audit](reports/preproduction-audit-20261025/REVIEW.md): keeper budget/preflight defects, non-vacuous composed accounting/invariants, current native/schema-5 runbooks, pause-versus-custody authority and captured original floors. These fixes do not prove absence of exploits or close actual services and independent audit.
  - Review [liquidity operations](reports/liquidity-operations-20261025/REVIEW.md): exact2/1/3defaults, actual-state bounded planning, idle ownership/cooldown, explicit inverse ranges, narrow Strategy-only width callback and strict API/observer/keeper version profiles. Near-limit runtime/initcode and unchanged public-signing restrictions remain release boundaries.
  - [Comprehensive review/coverage](reports/comprehensive-improvement-20261025/COVERAGE.md) and [findings](reports/comprehensive-improvement-20261025/REVIEW.md) distinguish fresh fixes from reused evidence and external gates. Review-cap, metadata, buyback, RPC transport and indexer atomicity improvements do not replace independent audit or qualify all48areas exhaustively.
  - [25October internal combined review](reports/daily-security-20261025/REVIEW.md) includes financial/custody/service paths, native source consistency, immutable burn target, funded historical dust and indexer provenance. No new unprivileged theft/dilution/double-claim path was confirmed in inspected scope; this is not an independent audit or guarantee of exploit absence.
  - [Remaining-architecture review](reports/architecture-pruning-20261025/REVIEW.md) and [scoped verification](reports/architecture-pruning-20261025/VERIFICATION.md): current Position3/localV4/direct governance2 are explicit.49 distinct selected Solidity behaviors and512 distinct Python methods pass across recorded source scopes; neither count is a fresh full-regression or real-service approval. Preserve old profiles/journals and unsupported cross-codec boundaries.
  - [Day audit](reports/day-readiness-20261025/REVIEW.md) fixes a pre-existing contract/API/replay boundary mismatch during native royalty custody. Review converted-credit enrollment and both old/new NFT cohorts; no principal/reward rights or permissions change. Verified source/mocked API history is not hosted-provider qualification.
  - [Full current-candidate audit](reports/full-audit-20261025/REVIEW.md) traces principal, ownership/economic/custody and service boundaries; fixes current activation and history-audit composition. Fresh source-scoped static analysis is manually triaged separately from real-service/independent qualification. No new principal redemption, delayed governance, signing or deployment authority.
  - [Backend remediation](reports/backend-remediation-20261026/VERIFICATION.md): five Python reporting modules hardened; final167distinct affected methods pass (31new/136existing). Malformed core values and inconsistent history fail closed; genuine outages remain unavailable. No Solidity, schema, signing, database/service or website rollout; actual provider/history/operations qualification and independent audit remain open.
  - [Documentation consistency review](reports/documentation-cleanup-20261026/README.md): current instructions consolidated by contract/backend/frontend responsibilities; removed obsolete procedures/profile examples and merged five redundant pages. Historical reports retain source scope, original dirty docs are backed up and no implementation/service/deployment change is inferred. Task IDs/statuses and live qualification gates are unchanged.
  - [Keeper/LP audit](reports/keeper-lp-audit-20261026/REVIEW.md) binds health to exact loaded config, rejects malformed conversion controls, repairs obsolete range-test domain and selects current3/fee1/native rehearsal source. Final affected Python354pass/5Unix skips (359methods),9range methods incl1000fuzz; unchanged production Solidity/permissions/economics. Linux current-fixture process/systemd, actual feeds/routes/gas/services and independent audit remain open. Deploy matching health writer/checker only under separate rollout; never patch old hashes or reset journals.
  - Use the [full callable scenario matrix](reports/system-adversarial-20261026/COVERAGE.md) and [backend/keeper cases](reports/system-adversarial-20261026/BACKEND.md) as independent audit inputs. Source coverage is not exhaustive execution. The corrected strict RPC/holder CLI boundaries must retain canonical identities, terminal budgets, preserved state and sanitized failures in real operating rehearsals.

  </details>


## Launch & operations

Decisions and rehearsals before real funds.

<a id="task-authorities-prices"></a>

- [ ] **[Select authorities & price services](docs/DEPLOYMENT_ADDRESSES.md)** - To do. The sole human operator controls governance and project services. Select the actual wallet/signature policy and limited service accounts; independently qualify two-source USD pricing for every enabled input/LP currency. Public authority addresses and provider decisions remain open.

  <details>
  <summary>Acceptance criteria</summary>

  - Supply two independently reviewed USD sources per required asset, exact policy IDs/ordinals, decimals, denomination, source ages/disagreement, source runtimes/proxy/upstream authorities and sequencer/outage policy. See [source qualification](TODO.md#task-dual-price-qualification).
  - Independently review and stage sequencer policy replacement through the actual sealed governance controller, including failed old feeds, unchanged healthy feeds, code changes and recovery grace. Bootstrap references are not independent reviews, and proxy runtime pins do not pin their implementations. Confirm an actual supported Robinhood source or explicitly reviewed no-feed chain policy; no ZZZ/USD feed is selected.
  - Select and verify the sole operator-controlled governance wallet/signature policy and keeper/guardian/mint-recipient authorities, direct governance wallet/controller and fixed module bindings; prohibit mint/LP/royalty receiver collisions.
  - Complete the address inventory: governance signers/threshold, guardian, keeper, mint recipient, temporary bootstrap and provider-specific VRF subscription owner;17fixed core contracts (controller plus16sealed modules),15current helpers including the source-policy factory and two separately deployed converters, and reviewed chain dependencies. No creator payer/receiver factory/inbox is required. Observe lifecycle/origin, companion owners and exact factory bindings. Direct governance2 has no timelock queue, executor or scheduler; royalties use NFT.royaltyRewards(), and no burn wallet is required.
  - Record the unresolved independent ZZZ price-feed question and the team's evidence under [creator pricing](TODO.md#task-creator-zzz-price); keep PoPL authority selection under this task.
  - [Current authority/custody guide](docs/GOVERNANCE.md) distinguishes immediate direct governance approval from recipient custody, guardian pause and bounded keeper execution. User deferred production wallet selection; keep those gates open. VRF funding owner is provider-specific and must not spend locked principal or earned rewards.
  - The user is the single human project operator and governance controller. No extra operator role/committee or multi-person approval is introduced. Current contracts and preflight already allow one signer/threshold1; the inventory field multisig remains schema-compatible. Dedicated limited keeper/guardian accounts do not require additional people. Actual public wallets remain unselected. See [operator model](docs/OPERATOR_MANUAL.md#one-operator-and-governance-wallet).

  </details>

<a id="task-asset-liveness-dust"></a>

- [ ] **[Approve reward-token liveness and dust economics](docs/SECURITY_AUDIT_PLAN.md#5-external-dependencies-and-revenue-accounting)** - To do. Review admitted token upgrade, blacklist, rebase and transfer behavior. Optional royalty-token read failures now defer only new eligibility for that currency, while exact unreadable backing can still block handoff. Sub-20-raw-unit owner dust is bounded per settlement, not cumulatively; qualify every asset before admission. The new [idle and dust guide](docs/IDLE_AND_DUST.md) distinguishes attributed principal reinvestment from reserved fractions, fee dust and quarantines; it adds no arbitrary sweep.

  <details>
  <summary>Acceptance criteria</summary>

  - Review the economic value of at most 19 raw units settled before membership changes, asset decimals and holder-triggerable entry frequency.
  - Inventory all royalty assets and review exact transfers, rebases, mutable authority, prefund/zero-member quarantine, pending settlement, claim callbacks, fractional/global dust, transfer rights and activation outage behavior.
  - Approve admitted-token outage/upgrade/blacklist behavior and economic value of repeated sub-20-raw-unit incumbent dust settlements.
  - Inventory actual principal/idle/pending compound, earned LP/royalty liabilities, buyback reserves, fractions, quarantines and accidental assets separately. Collective holder return includes only attributed principal+compound; no operator sweep or royalty-custody transfer exists. Qualify broken-token/venue and failed-receiver recovery without erasing liabilities.
  - [Historical venue outage cases](reports/daily-security-20261025/VERIFICATION.md) verify healthy new entry with zero dust, funded incumbent-only dust payout, atomic failure for current venue or old dust payment. No sweep or skipped unbacked reward is permitted.
  - [Full rights review](reports/full-audit-20261025/RIGHTS.md): retired royalty receivers can forward admitted currencies only, and cannot admit a new currency. Previously unadmitted future ERC20 receipts have no rescue path. Inventory cached marketplace receivers/orders and intended currencies before retirement; any bounded fixed-successor extension requires explicit reviewed policy before sealing. No generic sweep is added.

  </details>

<a id="task-dual-price-qualification"></a>

- [ ] **[Qualify two independent USD sources per input and LP asset](docs/PRICE_SECURITY.md)** - In progress. An optional immutable Pyth Core reader is implemented with bounded precision/confidence/freshness/runtime checks. Official catalogs give ETH/stablecoin candidates; no ZZZ source pair, adapter deployment, updater or actual policy is qualified. Source agreement remains3%; keep unsupported assets unavailable.

  <details>
  <summary>Acceptance criteria</summary>

  - Record exact network/source/adapter addresses, USD denomination, precision, runtime/implementation/admin/upstream policy and complete append-only Oracle policy/ordinal. Review common reporter, exchange, pool, bridge and USD-reference dependencies; two addresses or provider labels are not proof of independence.
  - Choose source ages and disagreement settings from actual heartbeat, update/deviation behavior and market depth; qualify both-source outage/recovery, sequencer policy, stale/future/incomplete rounds, proxy upgrades, depeg and sustained manipulation. Any admitted USDG/USDC royalty/conversion currency must not be assumed$1; these currencies are not contribution inputs. Missing or disagreeing sources fail closed.
  - Qualify $100 activation and $5 growth at actual source upper bounds and marginal LP lower bounds through funded routes, exact approvals, swaps, raw accounting and physical LP. Include worst-case 34-mark historical/source work, feed gas/latency, price/cap callbacks, newly discovered historical receipts, loss boundaries and recovery. Network gas is separate; wide uncertainty cannot silently enlarge the loss budget.
  - Obtain actual ETH/ZZZ USD-source proposals and market references with [Creator tasks / ZZZ team](TODO.md#task-creator-zzz-price), then independently verify them. Price any additional admitted royalty/conversion asset under its separate review; this does not admit it for contributions. If two defensible ZZZ sources cannot be qualified, keep ZZZ pricing/contributions unavailable; invent no provider or pool-spot fallback.
  - Retain independently reviewed exact-release/chain/deployment evidence, schema-5 pricing_version 2 observations and current helper/runtime bindings. Internal focused checks do not close real-provider, fork/service, gas/recovery or independent audit gates.
  - Reconcile the contract companion 34-mark maximum with the current 33-currency activation/preflight inventory limit. Keep configurations requiring 34 distinct reviewed currencies unavailable unless a separately reviewed bounded capacity change is implemented and qualified; never truncate historical backing or silently widen budgets.
  - User decision2026-10-24: intended source disagreement tolerance is3% (300bps). Calibrate actual feed ages and verify the independent default2% contribution execution floor; never average answers or automatically raise a cap to accept a wide quote.
  - Run a separately authorized native/accounting3/fee1/governance2/routing2/pricing2/review1/localV4 operating rehearsal. Historical local scaffolds now reject incompatible current artifacts before state/process creation; existing8902, NFTs, LP and journals remain untouched. Qualify actual provider/route gas: the latest [local cold-capacity workload](reports/onchain-safety/VERIFICATION.md) uses11,507,856 gas, leaving492,144 under its unchanged12M gate. Earlier135,373 margin is historical; neither substituted-feed workload qualifies actual providers or all34-mark compositions.
  - Record [dated candidate readings and cost semantics](reports/price-reference-20261025/OBSERVATION.md) separately from configured policy/qualification. Public Chainlink ETH availability and a ZZZ pool-derived estimate do not close either source pair. Review Shared-SVR/product/secondary-proxy common dependencies, feed ages, source/admin upgrades, per-read versus data/RPC/hosting charges and who pays. No source service or production gas price is selected.
  - [Updated official-source research](reports/real-service-readiness-20261025/RESEARCH.md) does not establish a qualified ZZZ source pair. Current defaults are2% contribution/1% conversion/3% maintenance, gas separate; source disagreement remains3%. Do not substitute shared-upstream proxy pairs, an instantaneous pool price or an invented feed.
  - [Optional Pyth reader](docs/PYTH_PRICE_SOURCE.md) has17 focused Solidity passes including1,000 confidence-boundary fuzz samples and38 normal object gates. The37 prior objects are byte-identical. Qualify real Core/proxy/feed/denomination/age/confidence/updater fees and common upstreams; confidence is a screening ceiling, not added mathematical Oracle bounds. Neither two Pyth products nor shared Chainlink proxies establish independence.
  - A3%source-agreement pass can still be infeasible under a conservative2%contribution budget plus execution costs; qualify actual spreads/update timing and quote availability without widening caller limits or adding a single-source fallback. [Principal review](reports/system-adversarial-20261026/PRINCIPAL.md).

  </details>

<a id="task-metadata-ops"></a>

- [ ] **[Publish artwork & operate metadata refresh](docs/ARTWORK_PUBLICATION.md)** - In progress. The IPFS upload bundle and refresh watcher are prepared. Pin the files, verify the CID and test marketplace updates.

  <details>
  <summary>Acceptance criteria</summary>

  - Stage live oracle/NAV thresholds, downward evolution and external-custody/stale unavailable labels; claims and migration must remain independent of metadata price reads.
  - Stage the implemented watcher with actual feeds, reviewed NFT runtime pins, RPC limits, confirmation recovery and gas budgets. Publish/pin the complete 2,784-state artwork manifest and independently verify its root, every path and actual marketplace rendering/ERC-4906 cache refresh.
  - Select an IPFS pinning provider and publish the verified complete artwork bundle; independently verify the resulting CID, all renderer paths and ongoing pin availability. Provider selection and publication were deferred; preparing a bundle alone does not establish hosting.
  - Exercise the added real strategy price guard, unavailable/recovery notifications and disabled-operations honest valuation in a live watcher/marketplace rehearsal; the local metadata suite does not establish cache behavior.
  - The approved 2026-10-20 Twin circuit routes artwork supersedes Vertical ribs in stable slot ribs/3. Use the regenerated 2,784-state bundle and matching metadata renderer; older prepared bundles are historical. Inventory/paths and other patterns are unchanged. See [scoped evidence](reports/twin-circuits/VERIFICATION.md).

  </details>

<a id="task-keeper-guardrails"></a>

- [ ] **[Harden keeper recovery and monitoring](docs/KEEPER_RECOVERY.md)** - In progress. Recovery/lifecycle controls, captured fee-review schema1, config-bound health and strict conversion reads are implemented candidates. Buyback priority and currency rotation prevent continuous maintenance/first-currency starvation without changing the serial pending/nonce/gas path. Optional main-progress watchdog source/unit support is implemented; actual Linux group cleanup, preserved pending/no-resend recovery, provider/fee/alert/host rehearsals and independent operating approval remain open.

  <details>
  <summary>Acceptance criteria</summary>

  - Stage keeper keystore isolation, nonce/receipt recovery, RPC failover, budgets, indexer backfill/reorgs, alerts and Unix state locking. The supplied systemd unit defaults to dry run.
  - Qualify canonical-hash RPC selectors for every activation state read, stale-snapshot rejection, strict receipt recovery across midnight/reorgs, and the chain's complete L2/L1 fee reporting. Offline mocks do not establish provider support or complete real network costs.
  - Qualify independent production alerts/backups/retention, redundant RPCs and complete real fee accounting.
  - Qualify preparationActive() and canonicalState() against the exact deployment and keeper. Missing/malformed/reverted getters fail closed. Frozen/importing/retired/cancelled states block all new maintenance/drain/metadata submissions; canonical receipt recovery continues. Recheck state before simulation, after gas estimation and before intent persistence. The local 88-case targeted receipt does not update the older staging fixture/keeper or replace a new operating rehearsal.
  - Add/review authenticated freshness-bounded next-check/last-success telemetry for frontend warnings; do not infer an execution promise from a 600-second poll example. Offline, delayed, paused, pending or budget-limited operation must be explicit. Qualify the new aggregate rebalance guard against the exact keeper deployment.
  - Governed custody candidate: surface source principal and royalty-currency in-transit states as unavailable, preserve funding/claim history and never count restoration as new income. Update services/inventory/operator alerts and holder disclosures for explicit external EOA/contract custody trust; no auto resend, timeout recovery, invented remote NAV or legacy v3 migration calls.
  - Review [the October25 keeper audit](reports/preproduction-audit-20261025/services/REVIEW.md) and rehearse original fee-review preservation, canonical signed-cap cost, included/separate L1 fees, legacy missing-review recovery and preflight version refusal on actual Linux/chain services. 199 distinct scoped passes and one Unix-only skip are not that qualification; no running journal was upgraded.
  - Qualify the new strict maintenance settings, per-currency thresholds/idle Budget pins, successful-operation cooldown and optional reviewed two-width policy on actual Linux/services. New retired bridge scheduling is removed; recovery of original pending hashes remains first, without deletion or resend. Configuration updates do not activate a running service.
  - Focused Linux CI selection now includes the new maintenance/range policy suites, preserving process-lock/recovery qualification as Linux-specific. No CI run or running service upgrade is inferred from a workflow edit; unchanged prior tests retain original source scope.
  - [Keeper/LP audit](reports/keeper-lp-audit-20261026/REVIEW.md) binds health to exact loaded config, rejects malformed conversion controls, repairs obsolete range-test domain and selects current3/fee1/native rehearsal source. Final affected Python354pass/5Unix skips (359methods),9range methods incl1000fuzz; unchanged production Solidity/permissions/economics. Linux current-fixture process/systemd, actual feeds/routes/gas/services and independent audit remain open. Deploy matching health writer/checker only under separate rollout; never patch old hashes or reset journals.
  - [Reward scheduling review](reports/reward-allocation-20261026/REVIEW.md): three source-bound old-code starvation failures become passing cases; final376 unique keeper methods yield370 passes/6 explicit skips. Preserve pending-first recovery, existing conversion turns and optional validated priority/currency cursors; no journal reset, extra successful submission per cycle, economic change or installed-service rollout. Qualify actual batch economics, backlog alerts and execution latency before production.
  - The [standalone harvest schedule procedure](docs/OPERATOR_MANUAL.md#change-the-standalone-harvesting-interval) documents maintenance.harvest_interval_seconds (example14400/four hours), positive-second settings, bucket override precedence, the separate polling interval and the last successful standalone-harvest receipt timer. Config changes require controlled restart, pending/journal preservation and fresh config-bound health; no contract call, resealing or automatic live rollout. Actual production interval/batch economics remain unqualified.
  - [Adversarial reward review](reports/reward-resilience-20261026/REVIEW.md) isolates maintenance RPC outages from an independently simulated enabled/due harvest after bucket authentication. Malformed config/ABI stays fail-closed; pending intents stop subsequent maintenance/conversion/harvest work. Final443distinct Python methods pass437/skip6; one actual-v4 test verifies stale prices stop rebalance but preserve fee collection, claims, physical LP and reserves. Preserve first wider failure and its narrower catch correction; qualify actual rollout/provider/gas/recovery separately.
  - The [confirmed no-progress I/O gap and source watchdog](reports/system-adversarial-20261026/WATCHDOG.md) distinguish inactivity timeout from total elapsed time. Qualify matching source/unit on systemd>=240:120s main-process progress, no background heartbeat, control-group SIGKILL/no core, late-pulse rejection and preserved pending intent/no automatic resend. Standalone commands remain unsupervised; unit text and inert tests do not prove real host cleanup.

  </details>

<a id="task-keeper-recovery"></a>

- [ ] **[Rehearse keeper outage & server recovery](docs/KEEPER_REHEARSALS.md)** - In progress. Historical 2026-10-16 evidence: 209 Ubuntu safety tests and 14 process rehearsals pass; the same 14 scenarios pass under the isolated server account. Actual systemd crash/restart and off-host snapshot round-trip restore passed. Sustained soak, physical host loss and governance key rotation remain open. These receipts do not qualify the new canonical lifecycle candidate.

  <details>
  <summary>Acceptance criteria</summary>

  - Stage [the keeper recovery runbook](docs/KEEPER_RECOVERY.md): multi-day outage, lost server, stale/missing state, nonce/budget reconciliation, old-host fencing and key rotation.
  - Verify off-host backups, health/log alert delivery, permissions/disk failures and actual Linux service restart/locking. Local guards are not production operating evidence.
  - Finish and review sustained multi-day staging; preserve observation gaps. The 30-minute desktop-dependent chat health monitor was paused at the user's request on 2026-10-17. It supplies no subsequent observations; do not restart it without authorization. The isolated server service was not stopped by pausing the monitor.
  - Rehearse [operator manual](docs/OPERATOR_MANUAL.md) scenarios with exact production roles/configuration: asset/pool stops, range changes, dependency outage/parking/resume, host/key recovery, reveal drain and whole-collection abort. Manual updates are required for every management behavior change under [maintenance rules](docs/TODO_WORKFLOW.md); a written runbook is not rehearsal evidence.
  - Before upgrading a signer with pending work, stage [fee-review journal recovery](docs/KEEPER_RECOVERY.md#fee-review-upgrades-and-legacy-pending-intents). Preserve original review, hash, signed transaction and inclusion-day budgets; no inferred historical limits, automatic reset or blind resend. Independently qualify real L1 reporting and old-host fencing.
  - [Remaining-architecture review](reports/architecture-pruning-20261025/REVIEW.md) and [scoped verification](reports/architecture-pruning-20261025/VERIFICATION.md): current Position3/localV4/direct governance2 are explicit.49 distinct selected Solidity behaviors and512 distinct Python methods pass across recorded source scopes; neither count is a fresh full-regression or real-service approval. Preserve old profiles/journals and unsupported cross-codec boundaries.
  - [Keeper/LP audit](reports/keeper-lp-audit-20261026/REVIEW.md) binds health to exact loaded config, rejects malformed conversion controls, repairs obsolete range-test domain and selects current3/fee1/native rehearsal source. Final affected Python354pass/5Unix skips (359methods),9range methods incl1000fuzz; unchanged production Solidity/permissions/economics. Linux current-fixture process/systemd, actual feeds/routes/gas/services and independent audit remain open. Deploy matching health writer/checker only under separate rollout; never patch old hashes or reset journals.
  - Rehearse the [progress-watchdog operator procedure](docs/KEEPER_RECOVERY.md#stalled-rpc-and-progress-watchdog) with isolated blocked DNS/header/body and signer interruption. Verify loaded settings, all-descendant termination before restart, lock release, original journal/nonce/fee-budget preservation, hashless ambiguous intent blocking and no overlap/resend. Existing service/desktop monitor was not changed or resumed.

  </details>

<a id="task-deployment-initcode"></a>

- [ ] **[Qualify exact constructor arguments and deployment size](docs/DEPLOYMENT_ADDRESSES.md)** - In progress. The old role-array size blocker is resolved: Access uses three static address arguments,42,177 total initcode bytes with6,975 headroom. All36 normal object gates pass. Final actual deployment inventory, constructor bindings and gas/rehearsal approval remain required; RoyaltyFactory retains only69 runtime bytes.

  <details>
  <summary>Acceptance criteria</summary>

  - The new3-address controller constructor has fixed96-byte ABI arguments; no proposer/executor arrays remain. Review governance wallet signers/threshold separately from the controller address. [Exact sizes](reports/architecture-pruning-20261025/bytecode-comparison.json) use unchanged normal compiler/EVM limits.
  - Qualify actual bootstrap, module/helper/authority bindings, deployment calldata, source/runtime pins, chain gas and setup/sealing procedures. No deployment follows from local gates; never waive EIP-170/EIP-3860.
  - Controlled same-context Access comparison reproduces9207→9252runtime and42081→42256creation (+45/+175); constructor fixed arguments96bytes give42352total/6800margin. Four isolated role-gas measurements pass, including CREATE+12312raw execution gas. RoyaltyFactory runtime margin69bytes and actual NFT URI constructor arguments require exact release qualification; see [gas evidence](reports/day-readiness-20261025/role-gas.md).

  </details>


## Future migration

Current source-chain custody and destination qualification, plus explicitly deferred future scope. External token/chain conversion does not relocate NFT ownership or reward accounting.

<a id="task-migration-framework"></a>

- [ ] **[Qualify same-pair pool moves and collective holder exit](docs/GOVERNED_CUSTODY_HANDOFF.md)** - In progress. Same-native-ETH/ZZZ moves and parking remain before collective exit. External custody/bridge/different-pair return paths are removed. Governance shutdown returns actual principal to NFT holders; post-exit whole-collection handoff is unsupported.

  <details>
  <summary>Acceptance criteria</summary>

  - Verify fresh source/runtime pins and same-pair destination admission, unchanged shares and captured execution limits.
  - Use the holder-return task for irreversible exit, exact accounting/payouts and retained royalty/reward rights. No external address, swap exit or bridge executor may reappear.
  - Whole-collection canonicalV5 handoff is supported only before exit. A future royalty-only successor would need explicit reviewed terminal-ledger support; do not imply post-exit replacement is implemented.

  </details>

<a id="task-destination-slots"></a>

- [ ] **[Qualify destination LP capacity and contribution cutover](docs/GOVERNED_CUSTODY_HANDOFF.md)** - In progress. Permanent bucket reservations and one contribution pool at a time are implemented. Qualify actual destination LP, available capacity, preserved bucket shares and deliberate contribution/input-route switches after movement.

  <details>
  <summary>Acceptance criteria</summary>

  - Before collective exit, use reviewed native ETH/fixedZZZ same-pair moves or pause-only parking/resume. Historical bucket reservations retain their bounds. Collective holder return is terminal and creates no operator destination slot or funded return/completion route. [Procedure](docs/HOLDER_COLLECTIVE_EXIT.md).
  - Reserve/admit the actual local destination, verify custody epoch/accounting currencies, actual minted LP and unchanged shares, then switch the sole contribution pool and qualified routes. Different actual pairs require the supported reviewed external-custody workflow; configuration does not add an atomic pair converter.

  </details>


---

Generated from [the task ledger](docs/project-todo.json). Update that ledger, then run `python scripts/sync-project-todo.py`; use `--check` to detect stale generated content.

Snapshot SHA-256: `338da901e085eb99bb9bfdfe0334ef08b287fd2e65256b4fcc5a21f3c3a60dc7`.
