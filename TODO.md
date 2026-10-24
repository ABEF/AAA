# Project Todo

**Reviewed 2026-10-24 | Contracts undeployed | Not approved for production**

The single task list for the whole PoPL project. Open a task's acceptance criteria for the detailed release requirements. There is no Todo page on the public website.

**16 To do | 28 In progress | 15 Implemented locally**

Implemented means built and locally checked, not deployed or independently audited. This list includes the current local development candidate; some code changes still await their own publication. Publishing this checklist does not publish or qualify that code.

[Feature and evidence reference](docs/IMPLEMENTATION_STATUS.md) | [Release approval record](docs/RELEASE_CHECKLIST.md) | [Update procedure](docs/TODO_WORKFLOW.md)

[Smart contracts](#smart-contracts) | [Backend](#backend) | [Frontend](#frontend) | [Creator tasks](#creator-tasks--zzz-team) | [Testing](#testing--qualification) | [Security](#security--audit) | [Operations](#launch--operations) | [Future migration](#future-migration)

## Smart contracts

Custody, ownership and reward accounting.

<a id="task-opensea-mint"></a>

- [ ] **[Qualify OpenSea primary mint integration](docs/OPENSEA_MINT.md)** - To do. Production minting is intended for OpenSea; the website Mint page is a demonstration. Verify the actual supported mint product, Robinhood chain, canonical PoPL caller/recipient path and collection URL before sealing.

  <details>
  <summary>Acceptance criteria</summary>

  - Code review 2026-10-23: current Vault.mintDormant mints to msg.sender and the NFT accepts mint only from Vault; no SeaDrop interface is implemented. Verify buyer recipient, payment/fee handling and the exact supported Robinhood drop integration before adding any mint adapter. General marketplace chain support does not prove primary-drop support.
  - Verify chain/product support and the required interface against the exact proposed OpenSea integration. A listing/secondary sale or direct Anvil mint is not primary-mint acceptance.
  - Preserve canonical NFT identity, 1,000 cap, 0.05 ETH recipient, exact rarity draw/VRF, zero LP at mint, mint pause/lifecycle and atomic rollback. Check NFT ownership when the caller is a marketplace intermediary; review any adapter/core change before sealing.
  - Rehearse a supported marketplace mint, payment, receiver callback/rejection, reveal and pause/restart; record receipts and exact verified collection URL. Keep production website mint preparation disabled.

  </details>

<a id="task-lp-eth-settlement"></a>

- [ ] **[Settle holder LP rewards in ETH](docs/LP_ETH_SETTLEMENT.md)** - In progress. LP holder conversion to native ETH is implemented in the local candidate with the user-approved 1% loss cap and separate gas. Includes fixed converter binding, per-NFT native credits, bounded keeper scheduling, history reconciliation and ETH-default claims. Scoped verification covers 142 distinct affected Solidity cases and 33 local journey assertions; real routes/feeds, operating latency/gas qualification and independent release review remain open.

  <details>
  <summary>Acceptance criteria</summary>

  - Preserve the fixed 80/10/5/5 allocation. Convert only the already-earned individual and collective holder balances; never spend principal, compounding/buyback reserves, quarantines or another NFT backing. Preserve each NFT entitlement before conversion, not current shares/membership at conversion time.
  - User approved 1% maximum LP conversion loss with gas separate on 2026-10-20. The candidate unwraps reviewed WETH exactly or uses pinned routes, fresh independent prices, exact deltas/approvals, caller minimum and deadline. Qualify actual target-chain routes, token/wrapper behavior and complete gas costs.
  - Bind the dedicated converter before sealing; the implementation supports bounded keeper execution, ETH ledger/current-owner claims and reentrancy/lifecycle guards. Qualify and record actual deployment bindings; core sealing alone does not prove conversion readiness.
  - Define ETH-only default claim behavior and explicit source-currency outage recovery. Failed conversion must leave original backed entitlements intact; never display an unconverted token balance as ETH. Preserve dust/fractions, transfer rights, complete handoff/abort/backing and historical claims.
  - Read API, unsigned claims and today-price earnings replay include LP conversion credits without counting them as new income or payout. Qualify full ingestion/lineage, real conversion receipts and stalled/restarted keepers; measure worst-case conversion waiting time across the collection and minimum economic batches.
  - The earlier [source-only claim audit](reports/topup-and-reward-review/ETH_PAYOUT_AUDIT.md) describes the pre-conversion revision. Current candidate evidence belongs in [LP ETH verification](reports/lp-eth-settlement/VERIFICATION.md); local fixtures do not qualify public routes or independent security.
  - Local ETH-only default claims, pending source-currency display, exact native backing/abort and current-owner same-chain handoff are verified in the scoped report. Qualify complete real-market conversion and operating latency before closing this task.
  - User reconfirmed on 2026-10-24: retain 1% maximum ZZZ LP-reward conversion loss, gas separate; require a cheaper qualified route than the selected pool's approximately 1.101% observed fee. Unsupported conversion stays unavailable with source balances backed; do not raise the cap or invent a route.
  - Native V2 venue ETH fees now enter individual/collective indices directly, without conversion. Already converted ETH credits coexist without new-income double counting. ZZZ still requires a cheaper qualified conversion route; the 1% limit and separate gas are unchanged.

  </details>

<a id="task-royalty-eth-settlement"></a>

- [ ] **[Qualify ETH settlement for marketplace royalties](docs/ROYALTY_SETTLEMENT.md)** - In progress. Bounded batch ETH conversion and optional-currency activation failure isolation are implemented, with a 1% execution-loss cap and gas separate. An opt-in keeper job preserves per-NFT entitlements and existing transaction recovery. Qualify exact Robinhood wrapper/routes/feeds, marketplace receipts, UI/history integration and operating behavior.

  <details>
  <summary>Acceptance criteria</summary>

  - Keep ETH pricing and verified ETH/WETH as the initial marketplace scope. Verify actual listings/offers/old orders/checkout settlement; a buyer source currency or ETH pricing preference does not prove what reaches the royalty receiver.
  - Independently review and record the fixed converter binding before sealing, exact wrapper/admin/implementation policies, admitted source currencies, route/factory/pool pins, feeds and final runtime inventory. Stablecoin support remains conditional on actual settlement needs; no live route is assumed.
  - Implemented: one guarded conversion for up to 32 NFTs' earned balances, proportional ETH credit to those same NFTs, exact WETH unwrap, at least 99% oracle-valued stablecoin output, strict minimum/deadline, approvals/delta checks and separate keeper gas. Original claims/fractions/quarantines remain intact.
  - Approved and implemented: activation survives optional royalty-token failures; unseen receipts at recovery go to the earlier cohort, then waiting NFTs join future receipts. Expose eligibleFor and deferred/recovered status accurately. Exact unreadable backing still blocks canonical handoff.
  - Review [scoped tests and internal findings](reports/royalty-conversion/VERIFICATION.md). Rehearse automatic dry/live keeper conversion, gas economics, failed currency/route recovery, mixed claims and successor configuration on the target network; do not infer production readiness from local mocks.
  - Implemented [backend conversion and currency-eligibility reporting](docs/ROYALTY_REPORTING.md), verified across owners and complete pinned same-chain predecessors. Integrate the website and qualify live ingestion/availability recovery. RoyaltyConverted is not Claimed or new earnings; only actual payouts increase lifetime paid totals. Independent audit/remediation remains required.
  - This converter applies only to royalties. It neither converts the LP ledger nor guarantees native ETH for all claims; direct source-currency claims remain supported. See [LP ETH settlement](TODO.md#task-lp-eth-settlement).

  </details>

<a id="task-pons-qualification"></a>

- [ ] **[Qualify the selected hookless ETH/ZZZ pool](docs/POOL_SELECTION.md)** - In progress. User selected Robinhood v4 pool 0x5011...afe1b: native ETH/ZZZ, static 1.002% LP fee, no hook; observed combined fee about 1.101%. Runtime-pinned native admission, post-seal static fee-tier destinations and atomic native/WETH pool moves are implemented in the current candidate. Real input routes, independent feeds, gas/operating qualification, production inventory and audit remain open.

  <details>
  <summary>Acceptance criteria</summary>

  - Keep the exact PoolKey `(address(0), ZZZ, 10020, 200, address(0))`, recomputed pool ID, creation transaction, confirmed block/hash, dependency runtimes and venue wiring bound to the selected integration. The earlier proposed 0.30% pool and Pons creator agreement are superseded, not current configuration.
  - Review hookless native admission and exact settlement, actual fee collection, harvest-before-increase, source-to-LP entry, moves/exits, donations, adverse callbacks and cleared approvals. Do not weaken the 1% contribution or fixed 3% ordinary maintenance limit; gas stays separate.
  - Qualify complete ETH/ZZZ/USDG/USDC quotes with independent prices and actual conversion depth. A higher pool fee applies only to swapped amounts but may make some full input routes unavailable; fail closed rather than subsidize execution from incumbents.
  - Qualify actual current-owner ETH settlement, keeper/API configuration, one contribution pool at a time, release inventory and operating gas. Native/WETH or fee-tier moves require initialized admitted destinations, actual Vault-owned LP and a deliberate contribution/route cutover.
  - Retain [historical Pons research](docs/ROBINHOOD_POOL.md) and source-bound old evidence. Use [current evidence](reports/hookless-pool/VERIFICATION.md) for changed-source checks; synthetic fork prices, authorities/VRF and locally initialized destinations are not production service qualification. No public deployment/transaction or existing 8902 reset is authorized.
  - The 2026-10-24 internal audit fixes fee-aware planning for both native and ERC20 v4 destinations, retaining99% contribution and3% maintenance limits. Four new regressions pass;58 affected existing cases passed, and only two corrected fixture cases were rerun successfully. Read reports/daily-security-20261024/REVIEW.md; actual markets/services and independent audit remain open.
  - The standalone pool observer now enforces reviewed runtimes, strict bounded replies, canonical hash state selectors and atomic secret-safe output. Nine mocked RPC/filesystem cases pass; qualify real provider support separately. It does not qualify token proxy authorities, feeds or liquidity economics.

  </details>

<a id="task-activation-assets"></a>

- [ ] **[Qualify ETH, ZZZ, USDG & USDC inputs](docs/ACTIVATION_ENTRY.md)** - In progress. Asset controls and Entry logic exist. The new ETH/ZZZ pool selection requires fresh complete route/feed qualification; earlier USDG conversion quotes and Pons execution evidence retain their original scope. USDC still needs a reviewed funded route.

  <details>
  <summary>Acceptance criteria</summary>

  - Independently verify $100 original source value with at least 99% marginal actually deployed LP, separate network gas, incumbent NAV pricing, all conversion-leg costs, callbacks, pending/dust barriers, top-ups and nonredeemability. Review the immutable Entry's exact owner/calldata context, inactive approval window, Registry-only valuation and callback cleanup; a post-conversion pair value cannot replace original source value.
  - Review USDC/USDG/ETH/ZZZ source-to-LP routing through the implemented Entry: exact token provenance, actual liquidity, fresh source prices, immutable binding/runtime, original-source budget, exact approvals and complete append-only route history. Native ingress is restricted to the actual native-pool wrapper. USDC remains disabled without a funded reviewed route; unsigned quotes alone do not establish qualified execution.
  - Use the [integration campaign](docs/INTEGRATION_CAMPAIGN.md) and [read-only observations](reports/activation-route-observation/VERIFICATION.md): one $1 conversion snapshot is not $100 activation qualification. Include subsequent LP costs in the same 1% limit, separate gas, qualified ZZZ pricing and complete operation simulation. Public transaction testing has not run; the isolated $1 build remains local only.
  - Track team-dependent feed, market and liquidity questions in [Creator tasks / ZZZ team](TODO.md#creator-tasks--zzz-team). Team responses do not replace independent route/feed qualification.
  - Implemented: fixed $100 activation / $5 increase floors in original-source Entry and the direct Vault helper, with higher pool minima retained. Qualify complete $5 routes at 99% marginal LP and separate gas, including real token units, depegs and execution costs. See [minimums and operator controls](docs/CONTRIBUTION_MINIMUMS.md).
  - Native V2 accepts actual ETH at asset zero with explicit policy and independent feed; exact Entry/Vault/manager call values are checked. Native V2 read/preparation profiles do not require WETH for ETH. Old local fixtures and prior WETH route evidence retain their original scope; current v3 conversions cannot output native ETH directly.

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

  </details>

<a id="task-custody-composition"></a>

- [ ] **[Qualify governed custody exits, returns and future destinations](docs/GOVERNED_CUSTODY_HANDOFF.md)** - In progress. Atomic moveFunds changes supported ETH/WETH venues or fee tiers without external custody and preserves shares under one fixed 3% cap. Separate paused exit sends normal consolidated ZZZ or explicitly approved raw assets to a regular custody address. Qualify real exit depth, funded returns, royalty custody and future finality/accounting before production.

  <details>
  <summary>Acceptance criteria</summary>

  - Verify normal close/consolidation/send with a fixed-price 3% floor, atomic rollback, exact approvals and asset segregation; end-to-end local completion reuses that original floor. Gas stays separate. Explicit raw emergency exits use reviewed token minima and do NOT claim a 3% USD guarantee.
  - Preserve NFT ownership/shares, accrued LP/collective/royalty rights, historical currencies/inboxes and incumbent compound NAV. No sweep of another ledger, donation or bucket. Local completion must actually mint destination LP; sent custody cannot be cancelled by a timeout.
  - Review external recipient custody/liveness trust, code/hash/proxy/owner controls and issuer 1:1 or 1:10 token conversion terms, decimals, claim deadlines and actual receipt amounts. Configure future ZZZ and buyback targeting explicitly; source native/hook bindings are still restricted.
  - Qualify separate full-currency royalty exits: freeze only the sent currency, preserve original liabilities/quarantine, require full funded raw return, avoid new-income double-counting and do not let newcomers receive old royalties. Unknown tokens follow admission/quarantine, not an arbitrary sweep.
  - Adapt production inventory, keeper/API diagnostics and hosting to the 16-module custody layout plus immutable validation helper. Retired v3 contracts/tests are historical, not new current evidence. Qualify real exit depth, stale-state behavior, gas and independent audit.
  - Remote delivery and returns require reviewed finality/channel-closure proofs, never multisig/timeout overrides. No real verifier/provider/remote NAV or revenue ledger is supplied. Complete future-chain canonical ownership/reward relocation and multi-hop operating procedures separately before those capabilities are used.
  - A sent local holding plan can bind one admitted and permanently reserved destination through `bindLocalDestination`, retaining the original mode, departure quantities and loss denominator. Qualify issuer exchanges, target token units/decimals and actual local LP completion; this is not a remote proof bypass.
  - The immutable read-only custody validator and all normal runtime/initcode gates must be bound to exact source evidence. The latest custody work needs its own fresh Anvil rehearsal; earlier Anvil tests do not qualify it.
  - Selected hookless pool: verify actual native ETH to WETH and fee-tier LP moves, source/destination ownership, fixed-price 3% cap, recipient segregation and separate contribution cutover. The moveFunds alias adds no arbitrary external transfer capability; regular-address custody uses the existing reviewed exit request.
  - Use the audited park-first procedure for separately mined exit approvals: external swaps can change an Active snapshot despite PoPL pause. Preserve the original rounded-up pre-parking ZZZ minimum as well as the parked approval floor. Separate parking/approval does not automatically share one cached on-chain budget; snapshot and raw/normal safeguards stay strict.
  - Native V2 raw exit/return is ETH/ZZZ and wrapper-independent, with exact payable return funding. It remains dependent on usable venue/token/runtime bindings. Atomic ETH/WETH moves are rejected pending an explicit conversion boundary; external governed custody completion is a separate workflow.

  </details>

<a id="task-native-custody-recovery"></a>

- [ ] **[Implement native ETH accounting and wrapper-independent recovery](docs/NATIVE_ETH_ARCHITECTURE.md)** - In progress. Native accounting V2 is implemented in the undeployed candidate: actual ETH funding/custody, indexed fee rewards, reserves, raw exit/return and versioned canonical backing/abort. Focused local evidence and explicit API/keeper version profiles exist. Complete the explicit atomic ETH/WETH boundary, website profile, final native fork/gas/service qualification and independent review before sealing; legacy-schema import is rejected.

  <details>
  <summary>Acceptance criteria</summary>

  - Specify how actual native principal and separately accrued fees are classified and preserved if WETH deposit/withdraw or its proxy policy fails; do not label the existing raw path wrapper-independent.
  - Implement the native architecture with exact payable ingress and ETH/token deltas, explicit custody authorization, immutable NFT shares and backed liabilities. Handle recipient failure atomically and prohibit sweeping prefunds, unsolicited ETH or another ledger.
  - Review normal exit, full recovery, local completion, fee/royalty currencies and future ETH/WETH moves together. Qualify affected code sizes, adverse callbacks and isolated venue execution; no bypass of a broken pool or nontransferable ZZZ can be promised.
  - Broader native redesign design-audit findings are explicit in docs/NATIVE_ETH_ARCHITECTURE.md: zero/unset identities; native indices and existing credits; historical native compound/dust and33-slot loops; two-stage canonical funding/abort; nonduplicated receiver protection; transitive wrapper independence; per-epoch schema/backend/price/trace profiles; and native recipient callbacks. These are implementation/verification blockers, not closed by the current WETH tests.
  - [Native V2 implementation and scoped evidence](reports/native-eth-port/VERIFICATION.md): exact payable ingress, native indices with converted credits, 33-asset historical reserves, distinct receiver protection, two-stage canonical funding/abort and forced-ETH exclusion. Do not combine old WETH modules/epochs with V2 or reset existing local journals. Same-actual-pair fee-tier moves remain supported; atomic ETH/WETH conversion needs a reviewed explicit boundary and currently fails closed.

  </details>

<a id="task-post-seal-configuration"></a>

- [ ] **[Keep operational settings configurable after sealing](docs/POST_SEAL_POLICY.md#configuration-boundary)** - In progress. Bounded future VRF gas/confirmation tuning and the buyback operating ceiling are implemented with immediate governance, lifecycle/reentry guards and events. Fixed provider settings, pending draws, earned rights and backing remain protected. Actual service qualification and typed v4 conversion support remain open before sealing.

  <details>
  <summary>Acceptance criteria</summary>

  - Inventory every fixed setting and setter. Preserve supported asset/route/feed/pool/role/range changes after sealing, with exact authorization, events, bounds, dependency checks, pending-operation handling and canonical locks; no governance waiting period.
  - Implemented NFT.setRandomnessRequestSettings(uint16,uint32) affects only future confirmations (3-200) and callback gas (200,000-10,000,000). Coordinator, key/lane, subscription and payment mode remain fixed; pending request provenance, ordered exact-quota draws and immutable results persist. It cannot repair a past callback, retry, reroll or select traits. Independently qualify actual provider limits and operator recovery.
  - Implemented Buyback.setOperatingTradeUSD(uint256) selects zero through immutable maxTradeUSD, defaulting to that hard maximum. Zero stops execution before oracle/reserve calls; both setters allow ordinary pause and reject preparation/canonical locks/reentry. Resize/remove keeper tasks after lowering/stopping. No allocation, reserve or execution-loss cap is relaxed.
  - Implement and qualify typed v4 conversion routing before sealing if future v4 markets must be usable. Current Entry and LP/royalty converters are single-hop v3 only and fixed bindings cannot gain a new executor from a route record.
  - Keep ownership, revealed rarity/artwork, accrued balances, backing and allocation guarantees protected. No reset, deletion, arbitrary calls/sweep or holder redemption. New compatible code uses reviewed handoff, not silent reinterpretation of old state.
  - [Scoped verification and internal review](reports/post-seal-controls/VERIFICATION.md) cover the two setters, pending continuity, lifecycle/callback boundaries, current-setting inventory checks and compatible current/historical event decoding. Operator manual, features, roadmap and memories are updated. Source-local evidence is not actual VRF/route/service qualification or independent approval; typed v4 support remains unfinished.

  </details>

<a id="task-immediate-governance"></a>

- [x] **[Immediate governance without timelocks](docs/GOVERNANCE.md)** - Implemented. Zero controller delay and no additional LP migration wait are implemented and locally verified. Roles, exact operations, sealing and execution/custody safeguards remain. Independent review, authority selection and live qualification remain open.

  <details>
  <summary>Acceptance criteria</summary>

  - [Scoped evidence](reports/immediate-governance/VERIFICATION.md): 228 distinct affected Solidity passes, 142 configuration passes, 30 size gates and fresh internal static review. No deployment or independent approval; there is no advance warning window for governance changes.

  </details>

<a id="task-operator-stop-controls"></a>

- [x] **[Independent mint and pool stop controls](docs/OPERATOR_MANUAL.md#stop-controls)** - Implemented. Governance can pause new NFT mints independently and disable pool deposits/operations without token, price or venue calls. Reopening still requires full pool validation; existing rights and lifecycle guards remain. The confirmed API reports mint pause separately.

  <details>
  <summary>Acceptance criteria</summary>

  - [Scoped verification and internal review](reports/operator-controls/VERIFICATION.md) cover authority, outage/reopen, callback rollback and economic continuity. Production service/authority rehearsals and independent audit remain required; no retroactive change to sealed contracts.

  </details>

<a id="task-nft-lifecycle"></a>

- [x] **[Minting, activation & NFT ownership](src/ZZZVault.sol)** - Implemented. 1,000-NFT cap, 0.05 ETH mint and $100 gross-value activation with at least 99% deployed as LP. Rights follow the NFT.

<a id="task-reward-ledgers"></a>

- [x] **[LP fees & separate royalty shares](docs/ECONOMICS.md)** - Implemented. 80 / 10 / 5 / 5 funded LP allocation with documented raw-unit dust settlement; equal collective shares. Actual royalties go to active NFTs at x1 / x2 / x3, separately from LP shares. These ledgers currently preserve payout currencies; ETH-only LP settlement is a separate open task.

<a id="task-shared-custody"></a>

- [x] **[Shared LP, maintenance & custody controls](docs/ARCHITECTURE.md)** - Implemented. One shared LP per pool/strategy serves many NFTs. The local four-historical-bucket safety bound, permanent allocations, pool-level upkeep, governance approvals, parking and guarded resumption are implemented. Ordinary rebalances now also enforce the user-approved 3% aggregate fixed-start-price cap, retaining existing guards and 5% idle; gas is separate. Approved range changes can now trigger the ordinary keeper rebalance at a flat price after cooldown; successful application clears the mismatch. The registry now restricts new activations/top-ups to one contribution pool at a time, while preserving governed future switches and historical custody.

  <details>
  <summary>Acceptance criteria</summary>

  - Use [the one-pool switch procedure](docs/OPERATOR_MANUAL.md#one-contribution-pool-at-a-time). Verify initial ZZZ/ETH selection, full destination validation, exact atomic switch/rollback and operator/runtime pins. Local evidence does not approve real destination liquidity or future-chain transport.

  </details>


## Backend

The data and services behind the app.

<a id="task-activation-quotes"></a>

- [ ] **[Complete activation & top-up quotes](docs/ACTIVATION_PREPARATION.md)** - In progress. Full Entry activation/top-up preparation is implemented and locally verified: original-source-to-LP simulation, 1% marginal-deployment floor, exact unsigned calldata and gas separate. Actual production routes, providers and fee semantics still need qualification. Confirmed range and rebalance eligibility/cooldown warnings are included; out-of-range entry remains allowed under normal execution guards. Range-update and price-trigger causes are now distinguished at the confirmed snapshot.

  <details>
  <summary>Acceptance criteria</summary>

  - Implemented: typed owner request, exact source admission/route/feed/runtime/module pins, one confirmed canonical hash, two full Entry simulations, contract-budget/share/event/LP reconciliation and tighter final conversion/liquidity minima. Missing allowance produces only an exact approval/reset draft and requires re-preparation after confirmation; no state overrides, signer or broadcast.
  - Qualify actual ETH/ZZZ/USDG/USDC original-source-to-selected hookless ETH/ZZZ paths and reviewed feeds at $100 gross value, with at least 99% new marginal LP and gas separate. Current local fixtures and trace/budget probe do not constitute a complete live-route rehearsal. Reject or revert when the limit cannot be met; reverted transactions can still spend gas.
  - Verify intended RPC providers support canonical-hash callTracer with logs and complete gas estimation. Approve network fee accounting (including every applicable data/L1 component), source/proxy/storage pins and actual gas/latency bounds. No latest/state-override fallback on unsupported/stale/future/reorg responses.
  - Integrate approval confirmation/requote and freshly validated wallet signing/receipts under the frontend task. Display NFT.currentLPValue at the confirmed block separately from marginal new LP and claimable LP/royalty balances; unavailable current value must stay unavailable. Local HTTP preparation is loopback-only; hosting remains under hosted services.
  - Qualify range/timing output against real StateView ticks and current physical LP IDs. Show cooldown end or eligible-now/waiting state; unknown/stale keeper next-check and execution times must remain unavailable. Reprepare after LP/range/policy changes; Entry calldata has economic minima/deadline, not an LP-version lock. See [dynamic liquidity](docs/DYNAMIC_LIQUIDITY.md).
  - Implemented request-wide monotonic/expiry/RPC budgets and supervised HTTP workers; [scoped remediation](reports/api-work-limits/VERIFICATION.md) addresses AUD18-03. Qualify actual Linux/RPC/trace workloads and ingress limits under [host-services](TODO.md#task-host-services); keep final canonicality and on-chain deadlines.
  - Preparation now checks the $5 top-up / $100 activation floor and any higher pool minimum before approvals or traces. [Focused evidence](reports/topup-and-reward-review/VERIFICATION.md) covers exact/below limits and units. Actual route/feed/fee qualification remains open.

  </details>

<a id="task-financial-history"></a>

- [ ] **[Qualify processed earnings & current-price USD](docs/EARNINGS_HISTORY.md)** - In progress. Confirmed collection, NFT and complete current-holdings 24h/all-time earnings are implemented, with separate LP/collective/royalty attribution and current-price USD values. Qualify actual feeds, complete predecessor history, archive providers and production service budgets.

  <details>
  <summary>Acceptance criteria</summary>

  - [Production earnings delta](reports/wallet-earnings/VERIFICATION.md): bounded same-block current-holdings history and collection holder allocations are implemented in the shared API/website profile. 86 affected Python, 89 distinct JS and six isolated production-profile browser cases pass. Claims/conversions are not income; missing prices/chunks never become zero. Actual feeds/history/hosting and independent qualification remain open.
  - Implemented exact processed-event attribution, carried fractions, deferred currency cohorts and complete configured same-chain lineage, with [scoped evidence](reports/earnings-history/VERIFICATION.md). Verify actual deployment-to-present ingestion of all seven emitters, provider/reorg behavior and load within the existing request budgets; never truncate history or infer zero from missing coverage.
  - User decision 2026-10-19: value all-time/24h earned original token amounts at today's confirmed prices, not historical USD. The implemented price profile verifies Oracle/feed/token/sequencer pins and storage; qualify actual providers, proxy/admin/wrapper assumptions and stale/recovery behavior. No guessed stablecoin peg; incomplete nonzero valuation is null.
  - Keep gross processed canonical receipts, holder allocations, actual claims, principal and current claimable balances distinct. Unprocessed/unpaid revenue is excluded; time means on-chain processing. Remote holder credits do not prove remote gross revenue/reserves. The selected hookless pool has a static 1.002% LP fee; its observed approximately 1.101% total charge includes protocol fees that are not PoPL income. Demo 0.30% is illustrative.
  - Conversions preserve earned source currency and are not new income; current ETH claimable already includes unclaimed converted credits. Integrate clear current-price/processing-time labels and unavailable states under [live-history-ui](TODO.md#task-live-history-ui).
  - Implemented the read-only [history audit](docs/HISTORY_AUDIT.md): per configured current/predecessor epoch, compare exact raw logs and headers in windows of up to 128 blocks/10,000 logs, with shared work budgets and no database repair. [Scoped evidence](reports/history-audit/VERIFICATION.md) covers 41 distinct affected cases via new runs and exact-body reuse. Reconcile all contiguous windows through reviewed epoch cutoffs; a partial matched window or agreeing providers is not a completeness/finality proof.
  - NFT card totals now combine individual LP, equal collective and royalties; they exclude gross pool income and require complete same-snapshot priced components. Saved demo 24h net history remains unavailable. [Scoped evidence](reports/topup-and-reward-review/VERIFICATION.md) does not qualify live ingestion or prices.
  - The [NFT calculation audit](reports/topup-and-reward-review/REWARD_CALCULATION.md) traces individual LP + equal collective + royalties, distinguishes earned from unpaid totals and guards invalid aggregates. Six focused display cases and 37 affected client cases pass; real ingestion/pricing qualification remains open.

  </details>

<a id="task-host-services"></a>

- [ ] **[Host and monitor the API & indexer](docs/FRONTEND_API.md#local-operation-and-verification)** - In progress. Bounded workers, request budgets, per-client admission and a guarded proxy profile are implemented and locally verified. Qualify Linux/TLS hosting, redundant RPCs, complete backfills/reorg recovery, provider quotas and off-host alerts. Initial Pinax compatibility checks passed; the documented public endpoint returned HTTP 403 from this environment.

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

  </details>

<a id="task-read-api"></a>

- [x] **[Confirmed balances & ownership API](docs/FRONTEND_LINEAGE.md)** - Implemented. Confirmed balances, lifecycle guards and complete configured same-chain predecessor claim history are implemented. Lifetime totals include LP fees, royalties and past owners. Hosting, frontend integration and cross-chain history remain separate gates. Current LP ID/share denominator and historical gross contributions are exposed separately from current marked NAV; local custody mismatches fail closed.

  <details>
  <summary>Acceptance criteria</summary>

  - Eight runtime/address pins, controller/helper bindings and strict lifecycle checks share the confirmed balance snapshot. Frozen/importing/retired/cancelled NFT and wallet projections fail closed; protocol status stays readable without reward/price calls. Operating qualification and consumer integration remain under hosted services and frontend tasks.
  - Complete explicitly pinned same-chain predecessor history preserves original NFT IDs and lifetime LP plus royalty claims. Verify both handoff directions, canonical matching activation/retirement receipts, terminal roots, historical assets and full creation-to-retirement ingestion. Missing configuration returns unavailable totals; inconsistent configured lineage fails closed. Import transfers are ownership reconstruction, not paid mints or marketplace sales.
  - Enforce at most eight predecessors and one million configured maximum replay events across current and prior histories. RPC observations and operator ingestion remain the trust model; this backend does not prove consensus finality or implement cross-chain history.
  - Governed custody candidate: surface source principal and royalty-currency in-transit states as unavailable, preserve funding/claim history and never count restoration as new income. Update services/inventory/operator alerts and holder disclosures for explicit external EOA/contract custody trust; no auto resend, timeout recovery, invented remote NAV or legacy v3 migration calls.

  </details>

<a id="task-royalty-reporting"></a>

- [x] **[Report royalty eligibility & conversion history](docs/ROYALTY_REPORTING.md)** - Implemented. Opt-in confirmed ETH/source balances, deferred currency eligibility and pinned converter enable status are implemented. Complete same-chain event replay separates conversion credits from actual lifetime claims. Missing values stay unavailable; UI, gross earned/USD history and live service qualification remain separate tasks.

  <details>
  <summary>Acceptance criteria</summary>

  - [Scoped verification](reports/royalty-reporting/VERIFICATION.md): 138 affected Python cases and 20 supplemental cases pass. Forty unchanged Solidity source bindings are reused; ten getter ABIs and 26 added indexer schemas match existing compiler artifacts. No Solidity rerun, public transaction, service deployment or website change.
  - The profile is explicit and pin-reviewed; legacy contracts do not inherit it. Currency failures do not bypass core identity, lifecycle, canonical freshness, full history coverage or request budgets. Conversion is neither a claim nor new revenue, and native claimable already includes remaining conversion credits.

  </details>

<a id="task-unsigned-actions"></a>

- [x] **[Prepare unsigned mint & claim requests](docs/FRONTEND_TRANSACTIONS.md)** - Implemented. Typed 0.05 ETH mint and up to 32 LP/royalty claim drafts now use current lifecycle/mint controls, exact canonical-hash simulation, scoped currency isolation, bounded workers and separate reviewed gas estimates. Signing stays in the wallet; live service/browser qualification remains open.

  <details>
  <summary>Acceptance criteria</summary>

  - Implemented: exact typed intent/owner/ledger checks, no arbitrary target or overrides, mint-only/global/preparation gates, canonical lock rejection, selected-asset verification, short client expiry, shared work budgets and supervised opt-in HTTP. Default GET-only; no signer/broadcast.
  - A required operator fee policy binds the reviewed read configuration and fee evidence, gas-price and total network-fee ceilings. Missing complete fee accounting or canonical gas estimation fails closed. Native value and gas are separate; future claims cannot fund upfront gas.
  - [Current scoped verification](reports/wallet-preparation/VERIFICATION.md) records focused Python/HTTP/worker cases and reusable compiler ABI evidence. No Solidity change or repeated contract suite. Actual deployment/VRF/RPC/fee manifests, ingress/load and wallet signing/receipt rehearsals remain with the service and frontend tasks.

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

  </details>


## Frontend

What holders see and use.

<a id="task-purchase-rights"></a>

- [ ] **[Show execution-time rights when buying an NFT](reports/nft-rights-audit/REVIEW.md#identity-and-ownership)** - To do. Refresh accrued balances and explain that the buyer receives what remains unclaimed at transfer. A seller can claim before the sale; do not promise a minimum balance from an earlier listing snapshot.

  <details>
  <summary>Acceptance criteria</summary>

  - Verify marketplace payment and claims; do not advertise ERC2981 as enforced royalties or a listing's claim balance as guaranteed at purchase.

  </details>

<a id="task-wallet"></a>

- [ ] **[Connect real wallet transactions](docs/BROWSER_WALLET.md)** - In progress. The local-only API coordinator now has actual Anvil mint, native activation, exact USDC approval, growth and combined ETH claim evidence, including same-hash recovery after an API outage. Actual extension acceptance and qualified production deployment/routes/services remain open; public signing remains disabled by user decision.

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

  </details>

<a id="task-portfolio"></a>

- [ ] **[Show actual holdings & claimable fees](docs/FRONTEND_API.md#implemented-endpoint)** - In progress. The reviewed website profile implements complete-wallet LP/ETH/earnings and complete collection inventory/current LP aggregation, with confirmed ownership, filters and position details. Actual services, archive/pricing/latency and production release qualification remain open.

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

  </details>

<a id="task-transaction-ui"></a>

- [ ] **[Handle the complete transaction journey](docs/CLAIM_ROUTER.md)** - In progress. Main website tracks per-NFT actions, commits cross-tab previews safely, caches only immutable exact-version demo state, expires suspended intents and rejects malformed/stale local confirmations. Production signing, receipts/reorgs and multi-device load qualification remain open.

  <details>
  <summary>Acceptance criteria</summary>

  - Decision 2026-10-22: production minting is intended for OpenSea; website minting is demonstrative. Production website mint preparation is blocked; local Anvil minting remains an integration tool. Qualify [OpenSea primary mint](TODO.md#task-opensea-mint) before sealing; production website priorities are activation, growth, ownership/balances and claims. Public signing remains disabled.
  - [Local API wallet coordinator](reports/deployment-local-wallet/VERIFICATION.md): 84 affected cases and nine headless scenarios pass with mocked wallet/RPC. Exact approval continues to fresh LP review; receipt recovery never resends, and confirmed/API-lag states are distinct. The user retained local Anvil-only signing; shared signer unchanged. Public signing, live extension/service qualification and replacement-transaction recovery remain open.
  - [Unsigned review profile](docs/DEPLOYMENT_WEBSITE.md) displays exact token units, simulated marginal LP addition, separate gas and expiry. It independently reconstructs typed calls, requires the 99% deployment floor and exact approval to Entry. Activation targets $100 with raw-unit round-up; growth requires at least $5. No submission/receipt path exists in this profile yet.
  - Local milestone: [website integration](docs/LOCAL_WEBSITE.md) and [scoped evidence](reports/local-website/VERIFICATION.md). Disposable launcher-owned accounts only; public deployment and production browser-wallet signing are not approved.
  - Show original contribution value, exact approvals, the 1% execution limit and network gas separately. Rejected or reverted execution may still cost network gas.
  - Independently review and pin deployments, the immutable 32-operation claim router runtime/bindings and exact calldata. Chunk larger portfolios; recheck owner/assets, simulate and estimate gas immediately before user confirmation. Handle account/network changes, stale drafts, rejection, replacement, failure and canonical receipt/reorg recovery.
  - Mint/claim drafts have client-enforced expiry, not an on-chain calldata deadline. Discard stale drafts and prepare again; do not describe unsigned backend preparation as signing or live wallet integration.
  - Use exact decimal uint256 strings for production NFT IDs; never reuse Number-based demo identities. The local website wording now uses gross $100 / 99% deployed, with gas separate; the public server is unchanged.
  - Local refresh is single-flight, retries only the explicit busy read response with bounded backoff, and distinguishes confirmed writes from failed balance refreshes. Writes are never automatically repeated as a new operation.
  - Qualify multiple independent devices/wallets activating, topping up and claiming concurrently: shared-pool quote movement, same-NFT transfer/claim races, account/chain changes, nonce/replacement recovery, isolated sessions and peak-load limits. Preserve exact transaction validation and confirmed-only artwork/financial state; a two-account serial Anvil fixture is not production concurrency qualification.
  - Local contribution review shows validation, progress and errors inside the dialog. Exact-contribution acknowledgement survives confirmed approval, while Entry retains a separate explicit confirmation. Only the activated/topped-up NFT shows the artwork Updating badge; stale portfolio finances/actions remain guarded.
  - Main website implementation: per-NFT/mint resources, atomic overlapping batch rejection, latest-state commits under Web Locks, bounded cross-tab waits, reset epochs and explicit persistence failures. Seventeen new focused cases plus affected domain/wallet cases and two-tab browser activation/claim checks are recorded in [scoped evidence](reports/frontend-state/VERIFICATION.md). No claim of distributed production safety or public deployment.
  - [Website/backend resilience evidence](reports/concurrent-services/VERIFICATION.md): 47 scoped Python and 90 JS passes, including source isolation, overload, cleanup, storage invalidation, nonfinite expiry, wallet/context changes and duplicate confirmation. Main-site browser/read checks and static build passed. Simulation/browser locks and the serial local signer do not establish concurrent production wallet safety.
  - NFT card presentation: fixed royalty weight follows the pattern; cards retain attached LP and active cards show combined Rewards to claim, with liquidity, components, history and lifetime claims in the breakdown. Exact currencies and unavailable values are preserved. [Scoped UI verification](reports/position-summary/VERIFICATION.md); production integration remains open.
  - New $5 increases and $100 activation are aligned in preview, local client, preparation and contracts. Preserve historical smaller preview events without permitting new ones. Earned totals sit on one line below attached LP, separate from claimable. Existing local sessions/public services are not upgraded; qualify production browser transactions and multi-user operation.
  - Match the accepted ETH-only holder payout requirement to actual on-chain conversion before displaying ETH. The older TEST-1/TEST-2 session is preserved; separate named ZZZ/WETH/USDC/USDG fixtures now exercise wrapping, decimals and mock routes. Balance/faucet UX and source-to-ETH payout qualification remain open. Do not cosmetically rename generic balances or silently reset current NFTs.
  - Four visible contribution inputs: ZZZ, USDG, USDC, ETH; WETH internal only. Contribution-only dialogs and scoped confirmed refresh are implemented. Named local fixtures exercise exact approvals and mock conversion separately from public route qualification; see [local setup](docs/LOCAL_TEST_STACK.md#named-input-local-rehearsal).
  - [Gallery/reward-feedback evidence](reports/website-polish/VERIFICATION.md): one saved sample funding round preserves prior LP and claims, allocation is LP/equal-collective/rarity weighted, duplicates cannot refill it. Confirmed tier celebrations use supplied ACTI/EV audio synchronized with the image after successful contribution and fresh increased LP. The claimed-total frame is hidden without changing lifetime accounting. Single-pool UI hides redundant pool controls. These are demo/presentation improvements, not live funding or production signing.
  - [Actual local API evidence](reports/api-chain-rehearsal/VERIFICATION.md): five holder transactions, real HTTP APIs, 18-NFT aggregation and same-hash claim recovery; 46 Python and70 JS scoped cases. RPC wallet shim and mock markets/feeds/VRF do not establish actual extension or production qualification.
  - [Pending nonce diagnosis](reports/browser-wallet/PENDING_NONCE.md): 175 affected cases, two mocked browser scenarios and six actual read-only recovery observations pass. Queued or wallet-changed nonces now stop the wait immediately; journals and local-only signing remain. The actual nonce 35 mint is unmined; controlled queue reconciliation and extension acceptance remain open.
  - [Authorized local mint reconciliation](reports/browser-wallet/local-mint-reconciliation/RECONCILIATION.md): exact queued nonce35 mint removed after identity/pool checks; complete stateRoot and both account balances/nonces unchanged.13 focused checks and an isolated browser scenario pass. User MetaMask nonce-history reset, exact saved-journal archival and temporary local-overlay removal remain pending. Public signing/source unchanged.

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

  </details>

<a id="task-preview"></a>

- [x] **[Collection, artwork & portfolio preview](docs/NFT_METADATA.md#fixed-visual-inventory)** - Implemented. Browse designs, explore positions, and simulate minting, activation and both reward claims. Twin circuit routes replaces Vertical ribs in its existing slot; all 1,000 NFT assignments remain unchanged.


## Creator tasks / ZZZ team

Questions and decisions to resolve with the ZZZ token/pool creator. Answers are not yet confirmed; technical implementation stays under its linked task. Record dated answers, responsible contacts and supporting evidence here.

<a id="task-creator-terms"></a>

- [ ] **[Agree the creator fee-sharing plan](docs/REVENUE_SHARE.md)** - To do. Historical/conditional Pons work: the selected existing hookless ETH/ZZZ launch pool does not require a creator-payment agreement. Conditional historical Pons work: the user now plans a new Uniswap ETH/ZZZ pool. Confirm the percentage and exact revenue base shared with PoPL. The user reports an intention to share according to LP participation; the detailed agreement is still unresolved.

  <details>
  <summary>Acceptance criteria</summary>

  - 2026-10-24 scope change: this is not a primary launch blocker if the confirmed new pool uses ordinary LP fees without creator/hook sharing. Preserve unanswered historical questions; reopen as an active dependency only for an explicitly selected external revenue arrangement. See [new pool decision](docs/POOL_SELECTION.md).
  - Ask the creator: what fraction is shared, and is its base total hook revenue, the creator payout after Pons deductions, or another explicitly defined net amount? Are conversion costs, buybacks, refunds or other deductions included? Record the formula with a worked example and an effective start date.
  - Confirm current hook fees, protocol/creator splits, buyback settings and actual creator payout control using dated on-chain evidence. The historical 1% hook / 70% creator observation is not a current payment guarantee. PoPL liquidity alone does not confer hook revenue rights.
  - Record written confirmation from the authorized party, the agreement version and how amendments, suspension or termination are handled. This external agreement does not change PoPL's fixed 80/10/5/5 allocation or create unfunded claims.
  - Resolve the linked [measurement](TODO.md#task-creator-measurement), [payments](TODO.md#task-creator-payments) and [continuity](TODO.md#task-creator-continuity) questions before treating the funding path as qualified. Stage actual receipt-to-allocation-to-holder-claim under [operating rehearsals](TODO.md#task-testnet-rehearsal).

  </details>

<a id="task-creator-measurement"></a>

- [ ] **[Agree how PoPL liquidity participation is measured](docs/REVENUE_SHARE.md#proposed-baseline)** - To do. Historical/conditional Pons work: the selected existing hookless ETH/ZZZ launch pool does not require a creator-payment agreement. Conditional historical Pons work: the user now plans a new Uniswap ETH/ZZZ pool. Choose the sharing method with the creator: sampled fee-weighted active liquidity is proposed; no method has been accepted yet.

  <details>
  <summary>Acceptance criteria</summary>

  - 2026-10-24 scope change: this is not a primary launch blocker if the confirmed new pool uses ordinary LP fees without creator/hook sharing. Preserve unanswered historical questions; reopen as an active dependency only for an explicitly selected external revenue arrangement. See [new pool decision](docs/POOL_SELECTION.md).
  - Ask whether fee-weighted sampled active-liquidity share or time-weighted active-liquidity share is accepted. Define the numerator/denominator, treatment of out-of-range LP, parked periods, deposits/top-ups, compounding, rebalances and moves between pools; total USD TVL is not automatically active-liquidity share.
  - Agree epoch length, sample frequency, maximum gaps, confirmation/finality depth, intra-block/tick-crossing approximation, complete raw hook-fee events, per-asset calculation, conversion basis and rounding/carry. Agree what happens if data is incomplete; do not silently impute missing fee history.
  - Name who produces, independently checks and resolves disputes over each report. The current calculator and collector propose amounts only; they do not authenticate creator acceptance, reconstruct exact intra-swap attribution or authorize payment. Technical event/backfill qualification remains under [hosted services](TODO.md#task-host-services) and [dependency review](TODO.md#task-security-dependencies).

  </details>

<a id="task-creator-payments"></a>

- [ ] **[Confirm who pays, in which asset, and when](docs/EXTERNAL_REWARDS.md#payment-and-allocation)** - To do. Historical/conditional Pons work: the selected existing hookless ETH/ZZZ launch pool does not require a creator-payment agreement. Conditional historical Pons work: the user now plans a new Uniswap ETH/ZZZ pool. Agree payer authority, payout currency/network, cadence, receiver verification and reconciliation of delayed or missing payments.

  <details>
  <summary>Acceptance criteria</summary>

  - 2026-10-24 scope change: this is not a primary launch blocker if the confirmed new pool uses ordinary LP fees without creator/hook sharing. Preserve unanswered historical questions; reopen as an active dependency only for an explicitly selected external revenue arrangement. See [new pool decision](docs/POOL_SELECTION.md).
  - Ask which wallet or contract controls payment/configuration, whether payment is manual or automated, its frequency/minimum amount and its currency/network. Confirm control without requesting a private key. There is no deployed PoPL receiver address to send to yet.
  - After deployment and review, verify the canonical per-bucket RewardReceiver, its immutable bucket/pair and optional native wrapper. Do not use the mint recipient or NFT-sale royalty receiver. Current intake supports only its admitted pair assets and an exact reviewed native wrapper; any other payout asset needs explicit technical qualification.
  - Agree invoice/report IDs, transaction/receipt references, period reconciliation, late/partial/duplicate payments, shortfalls and unpaid residuals. Receipt acceptance does not authenticate the sender; the receiver is permissionless and cannot debit the creator or enforce an off-chain promise.
  - Explain and obtain agreement on processing-time allocation: a payment received after an NFT activation can benefit that entrant even when the creator earned it earlier. The existing intake does not reconstruct historical per-NFT swap entitlements. Requested historical allocation requires a separately scoped design, not a bookkeeping assumption.
  - Rehearse the complete report-to-payment-to-80/10/5/5-allocation-to-current-holder-claim cycle, with funded backing and separate gas. Creator hook funding and 5% NFT-marketplace royalties remain distinct streams.
  - Native creator ETH is currently wrapped before LP allocation, so paying the inbox in ETH does not implement native holder claims. Coordinate payout currency with [LP ETH settlement](TODO.md#task-lp-eth-settlement); keep creator intake and holder payout policies distinct.

  </details>

<a id="task-creator-zzz-price"></a>

- [ ] **[Identify an independent ZZZ USD price source](docs/PRODUCTION_SERVICES.md#usd-prices-and-sequencer-status)** - To do. Ask the ZZZ team for any existing feed/provider or oracle work. No feed is selected; full $100 activation and 1% execution-loss qualification remain open.

  <details>
  <summary>Acceptance criteria</summary>

  - Ask whether an independent on-chain ZZZ/USD feed exists: provider, target chain, public contract address, denomination/decimals, underlying markets, update/heartbeat/deviation policy, history, admins/upgrades and outage support. Record a confirmed absence as an answer instead of assuming a feed.
  - If none exists, discuss a supportable independent pricing design/provider and who maintains it; team approval alone is not a security review. Do not substitute the same instantaneous selected-pool price or an assumed stablecoin peg for an independent USD guard.
  - PoPL engineering must independently qualify the chosen source, failure policy and actual activation/valuation paths under [prices and authorities](TODO.md#task-authorities-prices), [activation inputs](TODO.md#task-activation-assets) and [oracle security](TODO.md#task-security-strategy). Continue read-only dependency research while the answer is pending; do not mark the live route ready.

  </details>

<a id="task-creator-market-controls"></a>

- [ ] **[Confirm ZZZ, pool and hook controls](docs/ROBINHOOD_POOL.md#network-and-pool-identity)** - To do. Obtain the team's authoritative market references and identify who can alter tokens, hook fees, payout recipients or dependencies.

  <details>
  <summary>Acceptance criteria</summary>

  - Confirm the selected existing hookless ETH/ZZZ venue and independent token/pool controllers; the former Pons fee-recipient and hook-control questions are conditional historical research, not assumed new-pool authorities.
  - Confirm intended chain/token/pool/hook identities, published verified sources, deployment provenance and current market plan. Distinguish observations from team commitments; independently match the physical PoolKey and deployed code.
  - Identify the actual controllers for token mint/transfer restrictions or taxes, hook configuration, creator payout, buybacks and upgradeable dependencies, where such capabilities exist. Request exact owner/admin and implementation references plus disclosure of planned changes. Do not assume the ZZZ creator controls Pons, Uniswap, wrappers or oracle providers.
  - Obtain technical contacts for external controllers when required. Team-provided addresses are inputs to [selected-pool qualification](TODO.md#task-pons-qualification) and [external-dependency review](TODO.md#task-security-dependencies), not automatic permission to admit arbitrary hooks or grant PoPL authority.

  </details>

<a id="task-creator-input-liquidity"></a>

- [ ] **[Confirm activation liquidity and token references](docs/ACTIVATION_ENTRY.md)** - To do. Ask which funded markets and official asset references the team recommends for ETH/ZZZ/USDG/USDC activation, including the unresolved USDC route.

  <details>
  <summary>Acceptance criteria</summary>

  - Request exact supported-chain token/wrapper and swap-pool references, any planned liquidity moves, minimum viable liquidity and known token restrictions. Ask whether a usable funded USDC route exists or is planned; do not infer support from the symbol or a pool address alone.
  - The ZZZ team may point to markets but does not choose PoPL governance or waive guards. Engineers verify provenance, code/approvals, feeds and full $100-to-LP execution within the 1% limit, gas separate, under [activation qualification](TODO.md#task-activation-assets) and [complete quote preparation](TODO.md#task-activation-quotes). Disable unsupported inputs rather than assume a route remains liquid.

  </details>

<a id="task-creator-continuity"></a>

- [ ] **[Agree pool-change, incident and payment continuity](docs/EXTERNAL_REWARDS.md#entry-timing-and-remote-custody)** - To do. Define contacts and the funding process if markets, chains, payout control or the creator agreement change, including settlement of old periods.

  <details>
  <summary>Acceptance criteria</summary>

  - Ask how sharing continues when liquidity moves to another pool/chain or PoPL changes its canonical deployment. Agree effective cutoffs, measurement across old/new pools, settlement of old periods, late payment destinations and verification of replacement receivers. Compatibility still requires reviewed protocol support; a commercial agreement cannot add missing migration code.
  - Name the operational/incident contact and backup contact; agree notification for hook, recipient, token, oracle or liquidity changes, payment delays and service failure. Define an escalation and reconciliation process without promising an unagreed response time.
  - For incident or termination, preserve already funded holder rights and reconcile unpaid periods under the agreement. Do not assume refunds, principal withdrawals, arbitrary receiver redirection or continued future revenue. Use [operator controls](docs/OPERATOR_MANUAL.md#stop-controls) and the separately tracked [migration work](TODO.md#future-migration).
  - Agree issuer token-upgrade terms: exact old/new ZZZ contracts, ratio direction and decimals, conversion mechanism/authority, migration deadline, fees, new pool/hook and payout-currency continuity. The governed custody recipient may perform the exchange but NFT rights and original liabilities must remain intact.

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

  </details>

<a id="task-audit-release"></a>

- [ ] **[Independent audit and release approval](docs/RELEASE_CHECKLIST.md)** - To do. Complete an external audit, remediation, gas/strategy review and final operating/configuration sign-off before any real funds.

  <details>
  <summary>Acceptance criteria</summary>

  - **Local tests:** minting, activation, rewards, royalties, transfers and security.
  - Reproduce all Solidity/Python tests for the final frozen production release on supported Ubuntu, retaining exact source revision, compiler settings and full logs. Candidate CI and earlier green CI for `5febe70` do not validate future source changes.
  - Compile every contract/test/script and check normal runtime/initcode limits, constructor-argument allowance (including the claim router) and current gas; all small bytecode margins require explicit review.
  - Independently review the final source-bound Slither triage and accepted risks, refreshing analysis if source changes. Completed internal triage does not close the external audit gate.
  - Complete an independent external security audit, remediation verification and separate deployment/configuration review, then limited staging with approved limits.
  - Complete production services, creator terms, frozen-release independent audit and operating rehearsals. Real bridging remains blocked by destination capacity admission and provider/recovery qualification.
  - Complete the seven [security audit workstreams](docs/SECURITY_AUDIT_PLAN.md), including pre-seal implementation and qualification of the selected controlled whole-protocol migration while the source works. Post-halt recovery is deferred; LP migration alone is insufficient. Allocation percentages remain fixed; evaluate any proposed configurability separately.
  - Fill and independently authenticate the schema-4 production inventory: release-specific source/configuration, code and helper bindings, assets, randomness, parking rehearsal and operating evidence. Its current blocked state is intentional; offline consistency never authorizes deployment, sealing or real funds.
  - Preserve complete exact-release local/Ubuntu, actual Robinhood mainnet-fork and Robinhood Testnet evidence. Partial/cancelled fork runs and older source snapshots do not qualify the final release; test timeouts must retain partial evidence without counting as a pass.
  - Keep test-inventory assertions aligned with published fork cases and preserve standard assertion failure reporting. The [CI fixture correction](reports/architecture-evolution-ci/README.md) covers stale expectations for the existing 24 native/Pons plus nine hookless tests; it does not qualify production dependencies.

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
  - Reconcile pending transactions; stop new mints/contributions and use approved custody exits only for eligible principal. Preserve owner claims and account separately for compound/buyback reserves, rounding dust, royalties, mint payments and gas. No universal recovery or empty-balance guarantee.
  - Archive all receipts, manifests, final balances and unresolved obligations. Rehearsal chain/marketplace history and minted NFTs cannot be erased. Whole-collection retirement preserves rights in a funded successor; it is not a reset.
  - Deploy the final collection freshly after qualification; do not reuse consumed mint/rarity inventory or assume rehearsal NFTs become final NFTs. Reduced-minimum public tests would be a separate candidate and require explicit review, not the local-only dollar build.

  </details>

<a id="task-mainnet-fork"></a>

- [ ] **[Robinhood mainnet-fork qualification](test/NativePoolFork.t.sol)** - In progress. Selected hookless-pool campaign: eight targeted fork cases passed before the exit-minimum fix; the two failing cases were corrected and rerun successfully against current production source. This is scoped evidence, not a full final-source regression. Real feeds, complete routes, gas/strategy settings, services and independent review remain unqualified.

  <details>
  <summary>Acceptance criteria</summary>

  - Robinhood mainnet fork: qualify the actual selected hookless ETH/ZZZ pool and deployed dependencies against exact release sources. Historical Pons execution retains its original scope and is not selected-pool qualification; read reports/hookless-pool/VERIFICATION.md for current coverage.
  - Stage actual Uniswap swaps/entry/maintenance, malicious token/callback behavior, exact approvals/settlement, stale prices, donations and failures.
  - Current fork inventory is 29 selected-native and nine historical alternative-pool cases, not a claim of 38 final-source passes.

  </details>

<a id="task-local-verification"></a>

- [x] **[Local contract and integration tests](reports/royalty-reporting/VERIFICATION.md)** - Implemented. Royalty reporting adds 138 affected Python passes plus 20 supplemental passes, with unchanged Solidity evidence reused and ten getter/26 added-event ABIs checked. Prior royalty scope has 135 affected Solidity cases, 195 scoped Python cases, 31 size gates and 40 source bindings; holder preflight adds 12 cases. These scoped receipts are not a new full regression or production approval.

<a id="task-economic-rights-audit"></a>

- [x] **[Verify NFT economic rights at full collection size](reports/nft-rights-audit/VERIFICATION.md#integrated-collection-and-stateful-assertions)** - Implemented. Internal ownership, 1,000-NFT payouts, buyback rollback and dual-ledger invariants verified: 531 offline Solidity passes, two intentional fork setup skips; extended rights invariants completed 65,536 calls. This closes the scoped local verification task, not independent audit or production qualification.

<a id="task-local-dollar-rehearsal"></a>

- [x] **[Isolated $1 activation rehearsal](docs/ONE_DOLLAR_REHEARSAL.md)** - Implemented. A separate local-only build allows $1 gross activation with the unchanged 99% marginal-LP limit and 0.05 ETH mint price. Ten focused Solidity and four generator checks pass. Production source/API/website stay at $100; no public deployment or funds used.

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

  - Independently audit [immediate governance](docs/GOVERNANCE.md): no advance notice window, zero single/batch and migration delays, unchanged proposer/executor permissions, exact-calldata/replay/predecessor checks, canonical locks and guardian/keeper separation. An approved malicious feed, route, provider or successor can act immediately; review multisig security and acknowledge that trust explicitly.
  - Review governed activation-source enable/disable, future token admission, wrapper implementation/admin changes and disabled-source exit rehearsals. Admitting a source token does not add its conversion route; removing it must not revoke existing LP/reward rights. Ordinary exits remain price-guarded; parked close uses separately approved raw-token bounds. Rehearse governed feed repair without claiming unconditional recovery from external wrapper/bridge failure.
  - Independently stage paused parking through the sealed governance controller: missing/stale price feeds, failed creator inbox, exact share/LP/custody snapshot, close-only minimums excluding idle/compound/donations, one-sided principal, invalidation/replay/expiry, claims/transfers and fresh-oracle resume. Authenticate current-source evidence in the inventory's mandatory `parking_rehearsal` record.
  - Review the malicious approved-provider trust demonstration and remote custody powers. Code/configuration hashes and governance approvals do not prove honest destination funding or safe remote administrators. Keep fixed 80/10/5/5; no percentage setter or generic upgrade is authorized.
  - Independently review the implemented canonical preparation notice: existing controller-only start/cancel, exact notice binding, blocked new economic work and protocol configuration, trailing callback guards, and fixed parking/plan-cancellation drains. Guardian pause and governance controller unpause remain; inherited governance controller roles and scheduling keep their existing rules. The notice grants no successor authority and cannot freeze or export canonical rights.
  - Independently review/rehearse [mint/pool stop controls](reports/operator-controls/REVIEW.md): disable-only flags, full reopening validation, callback rollback, unchanged roles/canonical locks, obsolete approved operations and explicitly reviewed successor mint-pause state.
  - Governed custody candidate: surface source principal and royalty-currency in-transit states as unavailable, preserve funding/claim history and never count restoration as new income. Update services/inventory/operator alerts and holder disclosures for explicit external EOA/contract custody trust; no auto resend, timeout recovery, invented remote NAV or legacy v3 migration calls.

  </details>

<a id="task-security-share-accounting"></a>

- [ ] **[Shared LP accounting & economic manipulation](docs/SECURITY_AUDIT_PLAN.md#2-shared-lp-accounting-and-economic-manipulation)** - In progress. Verify 1,000 independent NFT share accounts through deposits, top-ups, compounding, rebalancing and migrations. Extend local conservation and gas evidence with adversarial prices, donation/front-running, dilution, rounding and multi-asset economic tests on qualified venues.

  <details>
  <summary>Acceptance criteria</summary>

  - Review creator inboxes, optional wrappers, discretionary payment terms, processing-time eligibility and combined four-bucket/four-inbox costs with all admitted assets. The factory's separate 16-inbox ceiling does not enlarge current Vault capacity. Qualify actual Entry/selected hookless-pool gas, not only the passing local fixture. Creator payment frequency and percentage remain undecided.
  - Review [dynamic-liquidity evidence](reports/dynamic-liquidity/VERIFICATION.md): independent price/decimal range vectors, current-NAV entry and compound exclusion, loss/appreciation/replacement/transfer continuity. Extend the bounded local/mock evidence with actual production routes, calibrated strategy backtests and full configuration gas/MEV qualification.

  </details>

<a id="task-security-ownership-rewards"></a>

- [ ] **[Ownership, claims & allocation rules](docs/SECURITY_AUDIT_PLAN.md#3-nft-ownership-and-reward-distribution)** - In progress. Verify all unclaimed balances and fractions follow the NFT, including transfer/claim ordering, callbacks, operators and pending receipt synchronization. Preserve fixed 80/10/5/5 with documented dust and separate funded rarity royalties. Assess configurable splits against practical benefit and added governance risk before any proposal; no percentage setter is implemented or authorized.

  <details>
  <summary>Acceptance criteria</summary>

  - Independently verify isolated 0.05 ETH mint proceeds, the 1,000-NFT cap, exact 600/300/100 quotas, atomic failure and no reroll/trait override.
  - Independently verify 80/10/5/5 funding, 90% remote delivery, equal collective membership and index/fractional solvency across transfers, entries and migrations.
  - Independently review the 5% ERC-2981 request and 100% eligible royalty redistribution in the separate immutable ETH/ERC20 ledger at activated rarity weights 1/2/3. Marketplace payment remains voluntary.
  - Configure OpenSea creator earnings to the actual `NFT.royaltyRewards()` helper at 5%, verify collection-administration access and each admitted payout asset, and stage a paid sale through receipt, weighted claim and NFT transfer. The current contract requests optional earnings; it does not implement ERC-721-C enforcement.

  </details>

<a id="task-security-strategy"></a>

- [ ] **[Oracles, keepers, strategies & MEV](docs/SECURITY_AUDIT_PLAN.md#4-oracle-keeper-and-strategy-vulnerabilities)** - In progress. Test compromised keepers, stale/manipulated prices, repeated rebalances, unfavorable swaps and sandwich/MEV costs. Qualify execution bounds, cooldowns, fee/gas budgets and outage policies with actual venues; access control alone does not prevent economic loss or impermanent loss.

  <details>
  <summary>Acceptance criteria</summary>

  - Qualify gas for 1/100/1,000 NFTs and maximum actual assets/inboxes; prove upkeep scales by shared pool. Backtest range, trigger, cooldown, slippage, impermanent loss, MEV and operating cost. Production strategy parameters remain unset.
  - Keep the unchanged 12M local combined-workload budget and four-historical-bucket cap. Qualify actual Entry/selected hookless-pool/token/inbox costs, not only a local shared-pair fixture; refresh normal runtime/initcode gates including constructor arguments for final source.
  - Independently qualify the implemented 3% loss cap for ordinary rebalance and atomic same-ordered-pair local move/resume, including the cached pre-harvest valuation vector, attributed compound, close/swap/mint costs, idle ceiling, callback repricing, MEV and repeated moves. Initial oracle honesty, venue backing and cumulative erosion remain risks; different-pair and asynchronous bridge enforcement remains open. Activation/top-ups retain 1%.
  - The new metadata spot/oracle guard and fixed-price rebalance cap require independent review. A per-operation 3% ceiling is not a target cost or a cumulative loss budget. Qualify real close/swap/mint execution, oracle/venue honesty, range/trigger/cooldown choices and outages before funding.
  - Independently qualify the implemented [range-policy application](docs/RANGE_POLICY_UPDATES.md): the governance-approved pool config authorizes a current-tick mismatch at the stored center through ordinary rebalance, preserving cooldown, oracle/minima, 3% aggregate/idle limits and NFT rights. Review repeated-change costs and current-config execution/resimulation; no separately privileged force path or config-version lock is added. [Scoped evidence](reports/range-policy/VERIFICATION.md) is not live strategy qualification.
  - User decision 2026-10-19: keep the 3% per-operation cap only, no rolling/cumulative loss breaker. Monitor cumulative turnover/MEV/gas costs and rehearse operator pause/parameter recovery; see [range management](docs/OPERATOR_MANUAL.md#range-and-strategy).
  - Internal 2026-10-24 review found and fixed ERC20 destination fee sizing; no new cap or authorization bypass was found in the reviewed diff. Earlier fork receipts retain their old source scope; use the new focused source-bound audit evidence rather than treating older passes as a current full regression.

  </details>

<a id="task-security-dependencies"></a>

- [ ] **[External dependencies & receipt backing](docs/SECURITY_AUDIT_PLAN.md#5-external-dependencies-and-revenue-accounting)** - In progress. Review Uniswap v4, Pons, creator payments, tokens/wrappers, oracles, randomness and future bridges for upgrades, compromise, outages and unexpected behavior. Reconcile every asset liability to actual receipts; test quarantine, duplicate/delayed funding, token failure and provider/destination change.

  <details>
  <summary>Acceptance criteria</summary>

  - Independently qualify implemented royalty-token outage isolation: failed optional balance reads defer only new membership for that currency. Recovery protects the earlier cohort and exact liabilities. Single-asset healthy claims continue, while syncAll and exact unreadable canonical backing can still fail. Do not blindly skip old receipt/eligibility checkpoints.
  - The [royalty conversion and outage candidate](docs/ROYALTY_SETTLEMENT.md) isolates optional-token activation failures and preserves earned balances. Actual token/wrapper/route behavior, runtime inventory, eligibility UI and live recovery still require qualification; native ETH has no external ERC20 balance query.
  - Pons hook/creator funding is historical or optional intake, not a dependency of the selected launch pool. Qualify actual LP-fee collection, independent prices and cheaper ETH-conversion routes; no full-balance conversion through the selected approximately 1.101% fee may silently bypass the fixed 1% cap.

  </details>

<a id="task-security-chain-recovery"></a>

- [ ] **[Whole-protocol recovery & canonical chain loss](docs/CANONICAL_HANDOFF.md)** - In progress. Same-chain handoff candidate now carries complete ownership, inventory, shares, both reward ledgers and exact backing, with atomic retirement/activation, restored abort and late forwarding. Qualify it and complete cross-chain finality, channel closure and lineage/transport before sealing; post-halt recovery stays deferred.

  <details>
  <summary>Acceptance criteria</summary>

  - Implement and independently qualify the accepted 2026-10-17 direction: planned whole-protocol migration while the source chain works. Preserve canonical NFT ownership and both funded ledgers, not just LP location. Post-halt recovery is deferred; no emergency recovery authority is authorized.
  - For any canonical transfer, specify one successor epoch and source freeze, NFT ownership/traits/shares, LP and royalty accruals/fractions/backing, in-flight messages and old-chain restart/replay policy. A snapshot or remote LP location ACK does not revoke old ownership.
  - Implement the selected verified-finality requirement: destination activation must authenticate finalized source retirement through an independently qualified chain-specific proof mechanism. No multisig/manual override, timeout activation or signer-attestation fallback is authorized. The concrete verifier/provider and finality configuration remain unselected; source terminal commitment must precede successor rights and cannot be reversed afterward.
  - Drain original ordered VRF/reveal and resolve in-flight custody/reward messages before freeze. The user selected provider qualification plus reveal drain; no pending-request carry is being added. Preserve exact IDs/traits, remaining supply/quota/inventory, owners and per-asset liabilities/fractions; never recreate balances from website data.
  - Retain safe handling of late old creator/royalty receipts and historical marketplace receivers. No double claims, duplicated canonical NFTs, erased backed obligations, principal refunds or arbitrary administrator transfers.
  - For principal conversion during relocation, enforce the agreed aggregate 3% per migrating bucket, gas separate, without offsetting one bucket loss against another bucket gain or spending claimable rewards. The implemented atomic local same-pair budget does not yet supply cross-chain aggregate enforcement.
  - Independently qualify the implemented same-chain cutoff, bounded exact export/import, classified backing, single-successor retirement, full/partial abort and late-forwarding paths. Benchmark atomic cutoff capture, ordered per-domain settlement, eight-row batches, each funding leg and final activation across 1,000 NFTs, four historical buckets, 32 LP assets, reachable funded inboxes and 17 royalty slots under unchanged limits.
  - Implement authenticated closure for historically used bridge channels and separate stable origin lineage from live canonical routing in a new message version. The current direct handoff rejects any legacy bridge activity and an imported successor cannot initiate v3 principal bridging; those restrictions are not a completed future-chain design.
  - Review compatible successor templates, code/configuration commitments and all owner/helper bindings. On 2026-10-17 the user explicitly accepted governance approval of different reviewed replacement code. A malicious approved replacement could divert LP; code hashes alone do not prove nonredeemability. This accepted trust does not waive exact backing, single-successor/source-retirement or verified-finality requirements.
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

  </details>


## Launch & operations

Decisions and rehearsals before real funds.

<a id="task-authorities-prices"></a>

- [ ] **[Select authorities & price services](docs/DEPLOYMENT_ADDRESSES.md)** - To do. Confirm governance, guardian, keeper and mint-recipient addresses, plus reliable USD pricing and outage policies.

  <details>
  <summary>Acceptance criteria</summary>

  - Supply reviewed feeds, decimals, denomination, heartbeat/sequencer/outage policy and admitted tokens on every chain.
  - Independently review and stage sequencer policy replacement through the actual sealed governance controller, including failed old feeds, unchanged healthy feeds, code changes and recovery grace. Bootstrap references are not independent reviews, and proxy runtime pins do not pin their implementations. Confirm an actual supported Robinhood source or explicitly reviewed no-feed chain policy; no ZZZ/USD feed is selected.
  - Select and verify multisig/keeper/guardian/mint-recipient authorities, zero-delay governance controller and fixed module bindings; prohibit mint/LP/royalty receiver collisions.
  - Complete the address inventory: governance signers/threshold, guardian, keeper, mint recipient, temporary bootstrap, provider-specific VRF subscription ownership and agreed creator payer; 21 fixed core contracts (controller plus 20 sealed modules), eight automatically created helpers/factories, later creator inboxes and reviewed chain-specific dependencies. Observe canonical lifecycle/origin, companion owners and factory bindings. Timelock is a contract, the template executor is open, royalties use NFT.royaltyRewards(), and no burn wallet is required.
  - Record the unresolved independent ZZZ price-feed question and the team's evidence under [creator pricing](TODO.md#task-creator-zzz-price); keep PoPL authority selection under this task.

  </details>

<a id="task-asset-liveness-dust"></a>

- [ ] **[Approve reward-token liveness and dust economics](docs/SECURITY_AUDIT_PLAN.md#5-external-dependencies-and-revenue-accounting)** - To do. Review admitted token upgrade, blacklist, rebase and transfer behavior. Optional royalty-token read failures now defer only new eligibility for that currency, while exact unreadable backing can still block handoff. Sub-20-raw-unit owner dust is bounded per settlement, not cumulatively; qualify every asset before admission.

  <details>
  <summary>Acceptance criteria</summary>

  - Review the economic value of at most 19 raw units settled before membership changes, asset decimals and holder-triggerable entry frequency.
  - Inventory all royalty assets and review exact transfers, rebases, mutable authority, prefund/zero-member quarantine, pending settlement, claim callbacks, fractional/global dust, transfer rights and activation outage behavior.
  - Approve admitted-token outage/upgrade/blacklist behavior and economic value of repeated sub-20-raw-unit incumbent dust settlements.

  </details>

<a id="task-metadata-ops"></a>

- [ ] **[Publish artwork & operate metadata refresh](docs/ARTWORK_PUBLICATION.md)** - In progress. The IPFS upload bundle and refresh watcher are prepared. Pin the files, verify the CID and test marketplace updates.

  <details>
  <summary>Acceptance criteria</summary>

  - Stage live oracle/NAV thresholds, downward evolution and remote/stale unavailable labels; claims and migration must remain independent of metadata price reads.
  - Stage the implemented watcher with actual feeds, reviewed NFT runtime pins, RPC limits, confirmation recovery and gas budgets. Publish/pin the complete 2,784-state artwork manifest and independently verify its root, every path and actual marketplace rendering/ERC-4906 cache refresh.
  - Select an IPFS pinning provider and publish the verified complete artwork bundle; independently verify the resulting CID, all renderer paths and ongoing pin availability. Provider selection and publication were deferred; preparing a bundle alone does not establish hosting.
  - Exercise the added real strategy price guard, unavailable/recovery notifications and disabled-operations honest valuation in a live watcher/marketplace rehearsal; the local metadata suite does not establish cache behavior.
  - The approved 2026-10-20 Twin circuit routes artwork supersedes Vertical ribs in stable slot ribs/3. Use the regenerated 2,784-state bundle and matching metadata renderer; older prepared bundles are historical. Inventory/paths and other patterns are unchanged. See [scoped evidence](reports/twin-circuits/VERIFICATION.md).

  </details>

<a id="task-keeper-guardrails"></a>

- [ ] **[Harden keeper recovery and monitoring](docs/KEEPER_RECOVERY.md)** - In progress. Recovery, preparation and strict canonical lifecycle guards are implemented in the published candidate. Locked canonical states stop all new submissions while receipt recovery continues. Existing staging is unchanged; exact deployment compatibility, RPC/fees, alerts and operating review remain open.

  <details>
  <summary>Acceptance criteria</summary>

  - Stage keeper keystore isolation, nonce/receipt recovery, RPC failover, budgets, indexer backfill/reorgs, alerts and Unix state locking. The supplied systemd unit defaults to dry run.
  - Qualify canonical-hash RPC selectors for every activation state read, stale-snapshot rejection, strict receipt recovery across midnight/reorgs, and the chain's complete L2/L1 fee reporting. Offline mocks do not establish provider support or complete real network costs.
  - Qualify independent production alerts/backups/retention, redundant RPCs and complete real fee accounting.
  - Qualify preparationActive() and canonicalState() against the exact deployment and keeper. Missing/malformed/reverted getters fail closed. Frozen/importing/retired/cancelled states block all new maintenance/drain/metadata submissions; canonical receipt recovery continues. Recheck state before simulation, after gas estimation and before intent persistence. The local 88-case targeted receipt does not update the older staging fixture/keeper or replace a new operating rehearsal.
  - Add/review authenticated freshness-bounded next-check/last-success telemetry for frontend warnings; do not infer an execution promise from a 600-second poll example. Offline, delayed, paused, pending or budget-limited operation must be explicit. Qualify the new aggregate rebalance guard against the exact keeper deployment.
  - Governed custody candidate: surface source principal and royalty-currency in-transit states as unavailable, preserve funding/claim history and never count restoration as new income. Update services/inventory/operator alerts and holder disclosures for explicit external EOA/contract custody trust; no auto resend, timeout recovery, invented remote NAV or legacy v3 migration calls.

  </details>

<a id="task-keeper-recovery"></a>

- [ ] **[Rehearse keeper outage & server recovery](docs/KEEPER_REHEARSALS.md)** - In progress. Historical 2026-10-16 evidence: 209 Ubuntu safety tests and 14 process rehearsals pass; the same 14 scenarios pass under the isolated server account. Actual systemd crash/restart and off-host snapshot round-trip restore passed. Sustained soak, physical host loss and governance key rotation remain open. These receipts do not qualify the new canonical lifecycle candidate.

  <details>
  <summary>Acceptance criteria</summary>

  - Stage [the keeper recovery runbook](docs/KEEPER_RECOVERY.md): multi-day outage, lost server, stale/missing state, nonce/budget reconciliation, old-host fencing and key rotation.
  - Verify off-host backups, health/log alert delivery, permissions/disk failures and actual Linux service restart/locking. Local guards are not production operating evidence.
  - Finish and review sustained multi-day staging; preserve observation gaps. The 30-minute desktop-dependent chat health monitor was paused at the user's request on 2026-10-17. It supplies no subsequent observations; do not restart it without authorization. The isolated server service was not stopped by pausing the monitor.
  - Rehearse [operator manual](docs/OPERATOR_MANUAL.md) scenarios with exact production roles/configuration: asset/pool stops, range changes, dependency outage/parking/resume, host/key recovery, reveal drain and whole-collection abort. Manual updates are required for every management behavior change under [maintenance rules](docs/TODO_WORKFLOW.md); a written runbook is not rehearsal evidence.

  </details>


## Future migration

A separate phase. Disabled at initial launch.

<a id="task-bridge-operation"></a>

- [ ] **[Qualify bridges & remote compounding](docs/GOVERNED_CUSTODY_HANDOFF.md)** - To do. The governed custody candidate replaces old LP v3 bridge/pair paths. Qualify actual recipients, destination backing/finality, recovery, new inventory and remote reward/compounding services. Whole-collection ownership/ledger handoff remains separate.

  <details>
  <summary>Acceptance criteria</summary>

  - Old v3 transport implementations and tests are historical, not current deployed functionality. Use the governed custody runbook and new source-bound evidence.
  - Preserve NFT shares/ownership and original reward liabilities. Require actual local LP or reviewed finalized remote custody proof; no guessed NAV, timeout recovery or double activation.
  - Independently qualify provider/admission/finality/channel-closure proofs, custody keys and backing, repeated migration and fail/recover operations. External recipients can divert assets; governance explicitly accepts that custody trust.
  - Complete the updated production inventory, keeper/API diagnostics, funded remote reward/compound flows and future-chain canonical ownership/ledger migration before claiming production support.

  </details>

<a id="task-migration-framework"></a>

- [ ] **[Governed migration framework](docs/GOVERNED_CUSTODY_HANDOFF.md)** - In progress. The governed custody candidate replaces old LP v3 bridge/pair paths. Qualify actual recipients, destination backing/finality, recovery, new inventory and remote reward/compounding services. Whole-collection ownership/ledger handoff remains separate.

  <details>
  <summary>Acceptance criteria</summary>

  - Old v3 transport implementations and tests are historical, not current deployed functionality. Use the governed custody runbook and new source-bound evidence.
  - Preserve NFT shares/ownership and original reward liabilities. Require actual local LP or reviewed finalized remote custody proof; no guessed NAV, timeout recovery or double activation.
  - Independently qualify provider/admission/finality/channel-closure proofs, custody keys and backing, repeated migration and fail/recover operations. External recipients can divert assets; governance explicitly accepts that custody trust.
  - Complete the updated production inventory, keeper/API diagnostics, funded remote reward/compound flows and future-chain canonical ownership/ledger migration before claiming production support.

  </details>

<a id="task-destination-slots"></a>

- [ ] **[Reserve destination capacity](docs/GOVERNED_CUSTODY_HANDOFF.md)** - In progress. The governed custody candidate replaces old LP v3 bridge/pair paths. Qualify actual recipients, destination backing/finality, recovery, new inventory and remote reward/compounding services. Whole-collection ownership/ledger handoff remains separate.

  <details>
  <summary>Acceptance criteria</summary>

  - Old v3 transport implementations and tests are historical, not current deployed functionality. Use the governed custody runbook and new source-bound evidence.
  - Preserve NFT shares/ownership and original reward liabilities. Require actual local LP or reviewed finalized remote custody proof; no guessed NAV, timeout recovery or double activation.
  - Independently qualify provider/admission/finality/channel-closure proofs, custody keys and backing, repeated migration and fail/recover operations. External recipients can divert assets; governance explicitly accepts that custody trust.
  - Complete the updated production inventory, keeper/API diagnostics, funded remote reward/compound flows and future-chain canonical ownership/ledger migration before claiming production support.

  </details>


---

Generated from [the task ledger](docs/project-todo.json). Update that ledger, then run `python scripts/sync-project-todo.py`; use `--check` to detect stale generated content.

Snapshot SHA-256: `ea8e370c330b2824cd14feaadf327ea9cdfd7fcdba867df48da30599303c694d`.
