# Project Todo

**Reviewed 2026-10-18 | Contracts undeployed | Not approved for production**

The single task list for the whole PoPL project. Open a task's acceptance criteria for the detailed release requirements. There is no Todo page on the public website.

**13 To do | 17 In progress | 9 Implemented locally**

Implemented means built and locally checked, not deployed or independently audited. This list includes the current local development candidate; some code changes still await their own publication. Publishing this checklist does not publish or qualify that code.

[Feature and evidence reference](docs/IMPLEMENTATION_STATUS.md) | [Release approval record](docs/RELEASE_CHECKLIST.md) | [Update procedure](docs/TODO_WORKFLOW.md)

[Smart contracts](#smart-contracts) | [Backend](#backend) | [Frontend](#frontend) | [Testing](#testing--qualification) | [Security](#security--audit) | [Operations](#launch--operations) | [Future migration](#future-migration)

## Smart contracts

Custody, ownership and reward accounting.

<a id="task-pons-qualification"></a>

- [ ] **[Qualify the selected Robinhood pool](docs/ROBINHOOD_POOL.md#popl-lp-integration-and-creator-payments)** - In progress. The native ETH / Pons adapter and ETH / ZZZ Entry fork tests pass. Independent venue, wrapper and gas review remain.

  <details>
  <summary>Acceptance criteria</summary>

  - Independently qualify the implemented selected native-ETH/Pons boundary, including wrapper implementation/admin upgrades, native settlement, real-key/accounting mapping and actual-pool tests. Keep production inventory native admission blocked until complete; do not broaden it to arbitrary hooks.

  </details>

<a id="task-activation-assets"></a>

- [ ] **[Qualify ETH, ZZZ, USDG & USDC inputs](docs/ACTIVATION_ENTRY.md)** - In progress. Asset controls and entry logic exist. Verify actual routes and feeds; USDC still needs a reviewed, funded route.

  <details>
  <summary>Acceptance criteria</summary>

  - Independently verify $100 original source value with at least 99% marginal actually deployed LP, separate network gas, incumbent NAV pricing, all conversion-leg costs, callbacks, pending/dust barriers, top-ups and nonredeemability. Review the immutable Entry's exact owner/calldata context, inactive approval window, Registry-only valuation and callback cleanup; a post-conversion pair value cannot replace original source value.
  - Review USDC/USDG/ETH/ZZZ source-to-LP routing through the implemented Entry: exact token provenance, actual liquidity, fresh source prices, immutable binding/runtime, original-source budget, exact approvals and complete append-only route history. Native ingress is restricted to the actual native-pool wrapper. USDC remains disabled without a funded reviewed route; unsigned quotes alone do not establish qualified execution.

  </details>

<a id="task-fair-draw"></a>

- [ ] **[Fair random assignment at mint](docs/NFT_METADATA.md#random-reveal)** - In progress. The fixed artwork draw is implemented. Connect and qualify live verifiable randomness; no new images are needed.

  <details>
  <summary>Acceptance criteria</summary>

  - Independently verify actual supported proof-verifying coordinator code/key/subscription/confirmations/gas and service availability on the deployment chain. An ABI or mock is not verification.
  - Stage real requests, out-of-order callbacks, strict mint-order reveal, subscription outages, reorg/finality and permanent early-request blocking recovery. No cancellation/reroll/admin bypass exists.
  - Verify canonical sealing rejects missing randomness configuration; verify content root and every artwork/metadata path against an independently reviewed immutable catalog.

  </details>

<a id="task-custody-composition"></a>

- [ ] **[Design different-pair and future-venue custody evolution](docs/ARCHITECTURE_EVOLUTION.md#different-pair-migration-proposed-composition-epochs)** - In progress. Local same-ordered-pair move/resume now enforces a 3% aggregate execution-loss cap through the immutable Vault-created budget helper, with gas separate. Different pairs and asynchronous bridging still need typed conversion, bounded composition epochs and retained old-currency liabilities before sealing.

  <details>
  <summary>Acceptance criteria</summary>

  - Preserve stable NFT/bucket/shares and all old owner/collective/royalty liabilities through ZZZ/WETH to ZZZ/USDC and subsequent moves. Token mapping is not conversion; do not remove current pair checks as a shortcut.
  - Qualify the implemented local movePool/resume 3% aggregate execution-loss cap: snapshot principal and attributed idle before harvest, add only exact released compound, and reuse the initial fresh price/decimal vector after close, balance and mint. Retained LP plus attributed idle must be at least 97%, with the existing 5% idle ceiling under the same vector; gas is separate and activation/top-ups retain 1%. Different-pair and asynchronous bridge costs, funded destination proof and market-movement treatment remain unimplemented and must not inherit this local guarantee.
  - Define bounded composition/message epochs, historical creator inboxes and reward paths, late old-currency compound/buyback reserves, pending remote funding, exact fixed recipients and temporary approvals. Repeated moves cannot erase or relabel obligations.
  - Review immutable typed helpers and remote destination compatibility for future venue code without arbitrary calls, principal sweeps or generic upgrades. Same-chain replacement Vaults cannot silently rebind the fixed NFT/Rewards system.
  - Measure aggregate and cumulative migration costs/frequency; repeated individually compliant 3% moves can substantially erode principal. A new cumulative hard cap or economic allocation change requires a separate policy decision.

  </details>

<a id="task-nft-lifecycle"></a>

- [x] **[Minting, activation & NFT ownership](src/ZZZVault.sol)** - Implemented. 1,000-NFT cap, 0.05 ETH mint and $100 gross-value activation with at least 99% deployed as LP. Rights follow the NFT.

<a id="task-reward-ledgers"></a>

- [x] **[LP fees & separate royalty shares](docs/ECONOMICS.md)** - Implemented. 80 / 10 / 5 / 5 funded LP allocation with documented raw-unit dust settlement; equal collective shares. Actual royalties go to active NFTs at x1 / x2 / x3, separately from LP shares.

<a id="task-shared-custody"></a>

- [x] **[Shared LP, maintenance & custody controls](docs/ARCHITECTURE.md)** - Implemented. One shared LP per pool/strategy serves many NFTs. The local four-historical-bucket safety bound, permanent allocations, pool-level upkeep, timelocks, parking and guarded resumption are implemented. Ordinary rebalances now also enforce the user-approved 3% aggregate fixed-start-price cap, retaining existing guards and 5% idle; gas is separate.


## Backend

The data and services behind the app.

<a id="task-financial-history"></a>

- [ ] **[Build live fee history & USD values](docs/FRONTEND_HISTORY.md#verification-and-remaining-scope)** - To do. Index earned fees and reviewed token prices. Keep revenue received, available rewards and past claims distinct.

  <details>
  <summary>Acceptance criteria</summary>

  - Index gross earned revenue, actual receipts, allocations and claims as distinct events, with complete deployment-to-present coverage, canonical/reorg reconciliation and unavailable responses when coverage is incomplete.
  - Define reviewed per-asset USD pricing and 24-hour/all-time valuation. Cumulative raw claimed totals, including claims by previous NFT owners, must not be presented as gross revenue; the selected Pons pool has 0% conventional fees, not the demo's assumed 0.30%.

  </details>

<a id="task-host-services"></a>

- [ ] **[Host and monitor the API & indexer](docs/FRONTEND_API.md#local-operation-and-verification)** - To do. A bounded read-only RPC compatibility probe exists. Pinax passed its initial checks; the documented public endpoint returned HTTP 403 from this environment. Qualify a second provider, production hosting, backfills, reorgs and external alerts.

  <details>
  <summary>Acceptance criteria</summary>

  - Publish and qualify the confirmed read API, optional unsigned preparation and ownership/claim-history indexer for the reviewed deployment. Independently verify hashes/configuration and response freshness after all RPC/history reads.
  - Qualify redundant providers, hosting limits, complete backfill, reorg recovery, structured sanitized logs and off-host alerts. Never host a transaction signer in the frontend read/preparation API.
  - Independently qualify the schema-2 lifecycle and complete same-chain predecessor history with live consumers: reviewed peer code/ABI/semantics and configuration, archive receipt/state availability, full ingestion reconciliation, retirement-cutoff index retention/backups, request latency at configured bounds and sanitized failure behavior. No partial lifetime sums or automatic unreviewed peer discovery.

  </details>

<a id="task-activation-quotes"></a>

- [ ] **[Complete activation & top-up quotes](docs/ACTIVATION_PREPARATION.md)** - In progress. Full Entry activation/top-up preparation is implemented and locally verified: original-source-to-LP simulation, 1% marginal-deployment floor, exact unsigned calldata and gas separate. Actual production routes, providers and fee semantics still need qualification. Confirmed range and rebalance eligibility/cooldown warnings are included; out-of-range entry remains allowed under normal execution guards.

  <details>
  <summary>Acceptance criteria</summary>

  - Implemented: typed owner request, exact source admission/route/feed/runtime/module pins, one confirmed canonical hash, two full Entry simulations, contract-budget/share/event/LP reconciliation and tighter final conversion/liquidity minima. Missing allowance produces only an exact approval/reset draft and requires re-preparation after confirmation; no state overrides, signer or broadcast.
  - Qualify actual ETH/ZZZ/USDG/USDC original-source-to-Pons paths and reviewed feeds at $100 gross value, with at least 99% new marginal LP and gas separate. Current local fixtures and trace/budget probe do not constitute a complete live-route rehearsal. Reject or revert when the limit cannot be met; reverted transactions can still spend gas.
  - Verify intended RPC providers support canonical-hash callTracer with logs and complete gas estimation. Approve network fee accounting (including every applicable data/L1 component), source/proxy/storage pins and actual gas/latency bounds. No latest/state-override fallback on unsupported/stale/future/reorg responses.
  - Integrate approval confirmation/requote and freshly validated wallet signing/receipts under the frontend task. Display NFT.currentLPValue at the confirmed block separately from marginal new LP and claimable LP/royalty balances; unavailable current value must stay unavailable. Local HTTP preparation is loopback-only; hosting remains under hosted services.
  - Qualify range/timing output against real StateView ticks and current physical LP IDs. Show cooldown end or eligible-now/waiting state; unknown/stale keeper next-check and execution times must remain unavailable. Reprepare after LP/range/policy changes; Entry calldata has economic minima/deadline, not an LP-version lock. See [dynamic liquidity](docs/DYNAMIC_LIQUIDITY.md).

  </details>

<a id="task-read-api"></a>

- [x] **[Confirmed balances & ownership API](docs/FRONTEND_LINEAGE.md)** - Implemented. Confirmed balances, lifecycle guards and complete configured same-chain predecessor claim history are implemented. Lifetime totals include LP fees, royalties and past owners. Hosting, frontend integration and cross-chain history remain separate gates. Current LP ID/share denominator and historical gross contributions are exposed separately from current marked NAV; local custody mismatches fail closed.

  <details>
  <summary>Acceptance criteria</summary>

  - Eight runtime/address pins, controller/helper bindings and strict lifecycle checks share the confirmed balance snapshot. Frozen/importing/retired/cancelled NFT and wallet projections fail closed; protocol status stays readable without reward/price calls. Operating qualification and consumer integration remain under hosted services and frontend tasks.
  - Complete explicitly pinned same-chain predecessor history preserves original NFT IDs and lifetime LP plus royalty claims. Verify both handoff directions, canonical matching activation/retirement receipts, terminal roots, historical assets and full creation-to-retirement ingestion. Missing configuration returns unavailable totals; inconsistent configured lineage fails closed. Import transfers are ownership reconstruction, not paid mints or marketplace sales.
  - Enforce at most eight predecessors and one million configured maximum replay events across current and prior histories. RPC observations and operator ingestion remain the trust model; this backend does not prove consensus finality or implement cross-chain history.

  </details>

<a id="task-unsigned-actions"></a>

- [x] **[Prepare unsigned mint & claim requests](docs/IMPLEMENTATION_STATUS.md#local-unpublished-candidates)** - Implemented. Local, unpublished preparation validates and simulates 0.05 ETH mints and up to 32 LP / royalty claims. Signing stays in the wallet; this task is not live integration.


## Frontend

What holders see and use.

<a id="task-wallet"></a>

- [ ] **[Connect real wallet transactions](docs/FRONTEND_API.md)** - To do. Wire minting, activation, LP additions and claims to reviewed deployed contracts.

  <details>
  <summary>Acceptance criteria</summary>

  - Integrate actual wallet transactions and the implemented confirmed API/history/unsigned-preparation service, including the separate royalty ledger, lifetime per-asset claims and indexed ownership. Independently pin/review deployments and calldata; discard drafts on account/chain changes or expiry; freshly simulate/estimate gas, confirm with the user and handle canonical receipts/replacements/reorgs. Bound/chunk portfolio claims. Gross earned fees and USD history require separate data/valuation; raw claimed totals cannot substitute for them.

  </details>

<a id="task-portfolio"></a>

- [ ] **[Show actual holdings & claimable fees](docs/FRONTEND_API.md#implemented-endpoint)** - To do. Replace sample positions with wallet ownership, attached LP and separate LP / royalty balances.

  <details>
  <summary>Acceptance criteria</summary>

  - Use confirmed current ownership, attached LP and separate per-asset individual/collective/royalty balances. Preserve unavailable remote/stale valuations and sticky activation eligibility through artwork downgrades.
  - Decide whether production labels use raw hashed token IDs or the existing sequential mint ordinal; implement and review matching metadata/UI labels without changing stable custody IDs. Demo #444 is not a promised production identifier.
  - Integrate current physical LP/share-denominator context, marked NAV vs cumulative input and price-guard unavailable states. Render out-of-range warning plus earliest rebalance eligibility; only fresh authenticated telemetry may supply an estimated next keeper check. The public website is still simulated and was not changed by the backend delta.

  </details>

<a id="task-transaction-ui"></a>

- [ ] **[Handle the complete transaction journey](docs/CLAIM_ROUTER.md)** - To do. Show gas, approvals, confirmation, rejection and recovery when an account, network or receipt changes.

  <details>
  <summary>Acceptance criteria</summary>

  - Show original contribution value, exact approvals, the 1% execution limit and network gas separately. Rejected or reverted execution may still cost network gas.
  - Independently review and pin deployments, the immutable 32-operation claim router runtime/bindings and exact calldata. Chunk larger portfolios; recheck owner/assets, simulate and estimate gas immediately before user confirmation. Handle account/network changes, stale drafts, rejection, replacement, failure and canonical receipt/reorg recovery.
  - Mint/claim drafts have client-enforced expiry, not an on-chain calldata deadline. Discard stale drafts and prepare again; do not describe unsigned backend preparation as signing or live wallet integration.
  - Use exact decimal uint256 strings for production NFT IDs; never reuse Number-based demo identities. Correct the demo old net-$100 activation wording to gross $100 / 99% deployed before publishing that scoped website change.

  </details>

<a id="task-live-history-ui"></a>

- [ ] **[Connect live history & cumulative claims](docs/FRONTEND_HISTORY.md#api-behavior)** - To do. Display verified 24-hour / all-time fees and lifetime claimed totals, including royalties.

  <details>
  <summary>Acceptance criteria</summary>

  - Display verified 24-hour/all-time earned fees separately from claimable balances. Previously claimed means lifetime per-asset LP plus royalty claims across all prior claims/owners and verified predecessor deployments, not just the last claim.
  - Connect simulated royalty cards to the separate confirmed royalty ledger and complete event history. Preserve explicit unavailable states when coverage or USD prices are missing.

  </details>

<a id="task-purchase-rights"></a>

- [ ] **[Show execution-time rights when buying an NFT](reports/nft-rights-audit/REVIEW.md#identity-and-ownership)** - To do. Refresh accrued balances and explain that the buyer receives what remains unclaimed at transfer. A seller can claim before the sale; do not promise a minimum balance from an earlier listing snapshot.

  <details>
  <summary>Acceptance criteria</summary>

  - Verify marketplace payment and claims; do not advertise ERC2981 as enforced royalties or a listing's claim balance as guaranteed at purchase.

  </details>

<a id="task-preview"></a>

- [x] **[Collection, artwork & portfolio preview](docs/NFT_METADATA.md#fixed-visual-inventory)** - Implemented. Browse designs, explore positions, and simulate minting, activation and both reward claims.


## Testing & qualification

Three required testing layers, with source-bound evidence.

<a id="task-testnet-rehearsal"></a>

- [ ] **[Robinhood Testnet end-to-end rehearsal](docs/RELEASE_CHECKLIST.md#required-testing-layers)** - To do. Exercise wallet flows, the website, keeper operations and deployment with explicit records of unavailable or mocked dependencies.

  <details>
  <summary>Acceptance criteria</summary>

  - **Robinhood Testnet:** wallet flows, website integration, keeper operations and deployment rehearsals, with actual supported services and explicit records of any mocked or unavailable dependencies.
  - Complete actual Robinhood Testnet end-to-end operation, physical host-loss/key-rotation rehearsal and independent audit/configuration approval.
  - Exercise actual entry, top-ups, fee funding/claims, royalties, transfers, rebalances, live keeper signing/recovery, indexer backfill/reorgs and alerts. Record mock or unavailable dependencies; Sepolia and local Anvil supplement but do not replace Robinhood-specific qualification.

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

<a id="task-mainnet-fork"></a>

- [ ] **[Robinhood mainnet-fork qualification](test/NativePoolFork.t.sol)** - In progress. The latest targeted ordinary-rebalance case passes against the pinned selected native/Pons venue with current source bindings. Broader historical fork suites retain their recorded sources and blocks. Production feeds, full input routes, gas/strategy settings and services remain unqualified; synthetic prices and mocked authorities/VRF do not close those gates.

  <details>
  <summary>Acceptance criteria</summary>

  - **Robinhood mainnet fork:** compatibility with the actual ZZZ pool, hook and deployed dependencies. The existing separate hookless-pool tests do not close this gate.
  - Stage actual Uniswap swaps/entry/maintenance, malicious token/callback behavior, exact approvals/settlement, stale prices, donations and failures.

  </details>

<a id="task-local-verification"></a>

- [x] **[Local contract and integration tests](reports/canonical-handoff/VERIFICATION.md)** - Implemented. Latest dynamic-liquidity checks pass: 119 affected Solidity cases, 138 isolated backend cases, normal size/source gates and a fresh internal static review. The earlier 582-case full regression retains its original source scope; it is not a full regression of the latest delta. Reuse unchanged evidence and rerun only affected checks unless a release qualification requires broader coverage.

<a id="task-economic-rights-audit"></a>

- [x] **[Verify NFT economic rights at full collection size](reports/nft-rights-audit/VERIFICATION.md#integrated-collection-and-stateful-assertions)** - Implemented. Internal ownership, 1,000-NFT payouts, buyback rollback and dual-ledger invariants verified: 531 offline Solidity passes, two intentional fork setup skips; extended rights invariants completed 65,536 calls. This closes the scoped local verification task, not independent audit or production qualification.


## Security & audit

Seven audit workstreams. Local checks are partial evidence; independent review and release sign-off remain open. See [the security audit plan](docs/SECURITY_AUDIT_PLAN.md) for acceptance criteria and priorities.

<a id="task-security-governance"></a>

- [ ] **[Governance, permissions & sealing](docs/SECURITY_AUDIT_PLAN.md#1-governance-permissions-and-sealing)** - In progress. Audit every role, timelock, configuration and external-module trust boundary for a path around nonredeemable custody. Prove sealed bindings stay fixed and supported asset/feed/route/parameter changes remain bounded; review malicious destinations, lost keys and emergency powers.

  <details>
  <summary>Acceptance criteria</summary>

  - Review governed activation-source enable/disable, future token admission, wrapper implementation/admin changes and disabled-source exit rehearsals. Admitting a source token does not add its conversion route; removing it must not revoke existing LP/reward rights. Ordinary exits remain price-guarded; parked close uses separately approved raw-token bounds. Rehearse governed feed repair without claiming unconditional recovery from external wrapper/bridge failure.
  - Independently stage paused parking through the sealed timelock: missing/stale price feeds, failed creator inbox, exact share/LP/custody snapshot, close-only minimums excluding idle/compound/donations, one-sided principal, invalidation/replay/expiry, claims/transfers and fresh-oracle resume. Authenticate current-source evidence in the inventory's mandatory `parking_rehearsal` record.
  - Review the malicious approved-provider trust demonstration and remote custody powers. Code/configuration hashes and timelocks do not prove honest destination funding or safe remote administrators. Keep fixed 80/10/5/5; no percentage setter or generic upgrade is authorized.
  - Independently review the implemented canonical preparation notice: existing timelock-only start/cancel, exact notice binding, blocked new economic work and protocol configuration, trailing callback guards, and fixed parking/plan-cancellation drains. Guardian pause and timelock unpause remain; inherited timelock roles and scheduling keep their existing rules. The notice grants no successor authority and cannot freeze or export canonical rights.

  </details>

<a id="task-security-share-accounting"></a>

- [ ] **[Shared LP accounting & economic manipulation](docs/SECURITY_AUDIT_PLAN.md#2-shared-lp-accounting-and-economic-manipulation)** - In progress. Verify 1,000 independent NFT share accounts through deposits, top-ups, compounding, rebalancing and migrations. Extend local conservation and gas evidence with adversarial prices, donation/front-running, dilution, rounding and multi-asset economic tests on qualified venues.

  <details>
  <summary>Acceptance criteria</summary>

  - Review creator inboxes, optional wrappers, discretionary payment terms, processing-time eligibility and combined four-bucket/four-inbox costs with all admitted assets. The factory's separate 16-inbox ceiling does not enlarge current Vault capacity. Qualify actual Entry/Pons gas, not only the passing local fixture. Creator payment frequency and percentage remain undecided.
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
  - Keep the unchanged 12M local combined-workload budget and four-historical-bucket cap. Qualify actual Entry/Pons/token/inbox costs, not only a local shared-pair fixture; refresh normal runtime/initcode gates including constructor arguments for final source.
  - Independently qualify the implemented 3% loss cap for ordinary rebalance and atomic same-ordered-pair local move/resume, including the cached pre-harvest valuation vector, attributed compound, close/swap/mint costs, idle ceiling, callback repricing, MEV and repeated moves. Initial oracle honesty, venue backing and cumulative erosion remain risks; different-pair and asynchronous bridge enforcement remains open. Activation/top-ups retain 1%.
  - The new metadata spot/oracle guard and fixed-price rebalance cap require independent review. A per-operation 3% ceiling is not a target cost or a cumulative loss budget. Qualify real close/swap/mint execution, oracle/venue honesty, range/trigger/cooldown choices and outages before funding.
  - Specify a controlled way to apply a timelocked range-policy change when price movement has not triggered normal rebalancing. Configuration remains adjustable after sealing, but existing LP ticks do not change automatically. Bind the intended bucket, configuration and current position; retain cooldown/frequency, oracle, minimum-output, 3% aggregate and idle safeguards, with gas separate, unchanged NFT rights and rollback. Governance/execution semantics require an explicit design decision before adding any force-rebalance authority. See [range-change behavior](docs/DYNAMIC_LIQUIDITY.md#changing-the-range-after-sealing).

  </details>

<a id="task-security-dependencies"></a>

- [ ] **[External dependencies & receipt backing](docs/SECURITY_AUDIT_PLAN.md#5-external-dependencies-and-revenue-accounting)** - In progress. Review Uniswap v4, Pons, creator payments, tokens/wrappers, oracles, randomness and future bridges for upgrades, compromise, outages and unexpected behavior. Reconcile every asset liability to actual receipts; test quarantine, duplicate/delayed funding, token failure and provider/destination change.

<a id="task-security-chain-recovery"></a>

- [ ] **[Whole-protocol recovery & canonical chain loss](docs/CANONICAL_HANDOFF.md)** - In progress. Same-chain handoff candidate now carries complete ownership, inventory, shares, both reward ledgers and exact backing, with atomic retirement/activation, restored abort and late forwarding. Qualify it and complete cross-chain finality, channel closure and lineage/transport before sealing; post-halt recovery stays deferred.

  <details>
  <summary>Acceptance criteria</summary>

  - Implement and independently qualify the accepted 2026-10-17 direction: planned whole-protocol migration while the source chain works. Preserve canonical NFT ownership and both funded ledgers, not just LP location. Post-halt recovery is deferred; no emergency recovery authority is authorized.
  - For any canonical transfer, specify one successor epoch and source freeze, NFT ownership/traits/shares, LP and royalty accruals/fractions/backing, in-flight messages and old-chain restart/replay policy. A snapshot or remote LP location ACK does not revoke old ownership.
  - Implement the selected verified-finality requirement: destination activation must authenticate finalized source retirement through an independently qualified chain-specific proof mechanism. No multisig/manual override, timeout activation or signer-attestation fallback is authorized. The concrete verifier/provider and finality configuration remain unselected; source terminal commitment must precede successor rights and cannot be reversed afterward.
  - Drain ordered VRF/reveal and resolve in-flight custody/reward messages before freeze, or design a separately reviewed carry protocol. Preserve exact IDs/traits, remaining supply/quota/inventory, owners and per-asset liabilities/fractions; do not recreate rounded balances from website data.
  - Retain safe handling of late old creator/royalty receipts and historical marketplace receivers. No double claims, duplicated canonical NFTs, erased backed obligations, principal refunds or arbitrary administrator transfers.
  - For principal conversion during relocation, enforce the agreed aggregate 3% per migrating bucket, gas separate, without offsetting one bucket loss against another bucket gain or spending claimable rewards. The implemented atomic local same-pair budget does not yet supply cross-chain aggregate enforcement.
  - Independently qualify the implemented same-chain cutoff, bounded exact export/import, classified backing, single-successor retirement, full/partial abort and late-forwarding paths. Benchmark atomic cutoff capture, ordered per-domain settlement, eight-row batches, each funding leg and final activation across 1,000 NFTs, four historical buckets, 32 LP assets, reachable funded inboxes and 17 royalty slots under unchanged limits.
  - Implement authenticated closure for historically used bridge channels and separate stable origin lineage from live canonical routing in a new message version. The current direct handoff rejects any legacy bridge activity and an imported successor cannot initiate v3 principal bridging; those restrictions are not a completed future-chain design.
  - Review compatible successor templates, code/configuration commitments and all owner/helper bindings. On 2026-10-17 the user explicitly accepted timelocked governance approval of different reviewed replacement code. A malicious approved replacement could divert LP; code hashes alone do not prove nonredeemability. This accepted trust does not waive exact backing, single-successor/source-retirement or verified-finality requirements.
  - Rehearse contract-holder and marketplace escrow compatibility with the new collection address. Import preserves owner addresses without ERC721 callbacks and cannot prove an old escrow can release a replacement NFT. Verify retirement notices, source/destination metadata, old listings and historical royalty receiver forwarding.
  - Historical canonical-handoff qualification recorded 582 regression cases plus 34 focused handoff cases, two opt-in fork setup skips, repaired bridge fixtures and three cold-gas suites. These retain their original source scope. The latest Vault/metadata changes have separate [dynamic-liquidity evidence](reports/dynamic-liquidity/VERIFICATION.md), not a new complete handoff regression. Preserve failed diagnostics, verify exact-commit Ubuntu CI and obtain independent review plus real operating qualification before release.

  </details>

<a id="task-security-integration"></a>

- [ ] **[Cross-contract & infrastructure audit](docs/SECURITY_AUDIT_PLAN.md#7-cross-contract-and-infrastructure-vulnerabilities)** - In progress. Audit complete transaction paths and failure rollback across contracts, frontend, API/indexer, deployment, keys and keeper services. Rehearse reorgs, replay, stale or compromised data, wrong-chain signing, RPC failure, restore/rotation and monitoring. Independent review and operational sign-off remain open.


## Launch & operations

Decisions and rehearsals before real funds.

<a id="task-authorities-prices"></a>

- [ ] **[Select authorities & price services](docs/DEPLOYMENT_ADDRESSES.md)** - To do. Confirm governance, guardian, keeper and mint-recipient addresses, plus reliable USD pricing and outage policies.

  <details>
  <summary>Acceptance criteria</summary>

  - Supply reviewed feeds, decimals, denomination, heartbeat/sequencer/outage policy and admitted tokens on every chain.
  - Independently review and stage sequencer policy replacement through the actual sealed timelock, including failed old feeds, unchanged healthy feeds, code changes and recovery grace. Bootstrap references are not independent reviews, and proxy runtime pins do not pin their implementations. Confirm an actual supported Robinhood source or explicitly reviewed no-feed chain policy; no ZZZ/USD feed is selected.
  - Select and verify multisig/keeper/guardian/mint-recipient authorities, fixed timelock and module bindings; prohibit mint/LP/royalty receiver collisions.
  - Complete the address inventory: governance signers/threshold, guardian, keeper, mint recipient, temporary bootstrap, provider-specific VRF subscription ownership and agreed creator payer; 21 fixed core contracts (controller plus 20 sealed modules), eight automatically created helpers/factories, later creator inboxes and reviewed chain-specific dependencies. Observe canonical lifecycle/origin, companion owners and factory bindings. Timelock is a contract, the template executor is open, royalties use NFT.royaltyRewards(), and no burn wallet is required.

  </details>

<a id="task-creator-terms"></a>

- [ ] **[Finalize creator revenue-sharing terms](docs/REVENUE_SHARE.md)** - To do. Agree the fee basis, liquidity-share measurement, payout asset, frequency and authorized payer. Only actual receipts fund rewards.

  <details>
  <summary>Acceptance criteria</summary>

  - Confirm terms with the pool creator: percentage and calculation basis, payout asset/network, payment frequency, authorized payer/configurer and actual PoPL receiver. Terms were explicitly deferred on 2026-10-15; receipt-driven implementation must not imply guaranteed revenue. Stage a payment through allocation and holder claim.
  - Agree and qualify the proposed active-liquidity measurement policy: fee-weighted or time-weighted, epoch length, snapshot frequency/gap limits, finality, complete fee events, tick-crossing approximation, cross-asset payout conversion, rounding and independent receipt reconciliation. Rehearse the complete data-to-payment-to-holder-claim cycle. The implemented calculator has no payout authority and does not prove creator acceptance.

  </details>

<a id="task-asset-liveness-dust"></a>

- [ ] **[Approve reward-token liveness and dust economics](docs/SECURITY_AUDIT_PLAN.md#5-external-dependencies-and-revenue-accounting)** - To do. Review admitted token upgrade, blacklist, rebase and transfer behavior. A broken royalty token can stop new activations; sub-20-raw-unit owner dust is bounded per settlement, not cumulatively. Qualify every asset before admission.

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

  </details>

<a id="task-keeper-recovery"></a>

- [ ] **[Rehearse keeper outage & server recovery](docs/KEEPER_REHEARSALS.md)** - In progress. Historical 2026-10-16 evidence: 209 Ubuntu safety tests and 14 process rehearsals pass; the same 14 scenarios pass under the isolated server account. Actual systemd crash/restart and off-host snapshot round-trip restore passed. Sustained soak, physical host loss and governance key rotation remain open. These receipts do not qualify the new canonical lifecycle candidate.

  <details>
  <summary>Acceptance criteria</summary>

  - Stage [the keeper recovery runbook](docs/KEEPER_RECOVERY.md): multi-day outage, lost server, stale/missing state, nonce/budget reconciliation, old-host fencing and key rotation.
  - Verify off-host backups, health/log alert delivery, permissions/disk failures and actual Linux service restart/locking. Local guards are not production operating evidence.
  - Finish and review sustained multi-day staging; preserve observation gaps. The 30-minute desktop-dependent chat health monitor was paused at the user's request on 2026-10-17. It supplies no subsequent observations; do not restart it without authorization. The isolated server service was not stopped by pausing the monitor.

  </details>


## Future migration

A separate phase. Disabled at initial launch.

<a id="task-bridge-operation"></a>

- [ ] **[Qualify bridges & remote compounding](docs/CHANGE_AND_RECOVERY.md)** - To do. Review real transport providers, backing and repeated migrations; implement funded compounding when LP stays on another chain.

  <details>
  <summary>Acceptance criteria</summary>

  - Independently review real provider SDK wrappers, backing/equivalent token semantics, channels, finality, exact funding and recovery.
  - Stage canonical -> satellite -> satellite -> home -> revisit with actual providers, duplicate/reordered/forged/underfunded receipts, ACK epochs, pauses, old-policy and historical reward paths.
  - Verify destination reservations, frozen canonical shares/membership, no remint/principal refund, legacy liability barriers, and governance trust for every new destination.
  - Rehearse source-oracle-independent departure of an already Parked bucket with designated compound reserves, retained `remoteSettled` barrier, exact attributed transfers, destination valuation and reviewed provider recovery. Parking does not waive bridge backing or enable arbitrary conversion.
  - Review each future destination and onboard its immutable policy/routes through the timelock before economic migration. Authenticate provider SDKs, delivery fees, delayed receipts, failure/recovery and retained historical routes; future chains, arbitrary conversions and satellite top-ups are not automatically supported.
  - Resolve permanent-relocation compounding: the canonical creator receiver reserves its 5% compounding share at home while principal is remote. Remote reinvestment needs a separately reviewed funded bridge/top-up design; the current path waits for return.

  </details>

<a id="task-destination-slots"></a>

- [ ] **[Reserve destination capacity](docs/ARCHITECTURE_EVOLUTION.md#permanent-destination-capacity-bounded-repair)** - In progress. Permanent idempotent local admission is implemented with targeted capacity, switching, return and None-state regressions. Remote reservation authentication, independent review and real-provider qualification remain open.

  <details>
  <summary>Acceptance criteria</summary>

  - Implement and independently review permanent destination capacity admission before delivery. Verify the repaired reserved-arrival path, local/remote competition, aliases, duplicate registration, malformed-import rollback, None-state consumers and full-cap returns. Real bridging remains disabled pending independent admission/provider review.
  - Reserve durable historical capacity before delivery, not just pool identity. Reuse returning slots; test local/remote concurrency, duplicate/idempotent registration, reserved None-state enumeration and delayed/cancelled operations without freeing a reservation that an in-flight delivery may still need.
  - Authenticate confirmed destination admission before departure. The source does not verify a remote capacity proof; local idempotent reservation alone does not qualify an arbitrary provider or sealed old destination.

  </details>

<a id="task-migration-framework"></a>

- [x] **[Governed migration framework](src/ZZZMigration.sol)** - Implemented. Timelocked compatible-asset routes preserve fixed home identity and NFT allocations. Local same-pair move/resume now has a 3% aggregate loss cap, and a cancellable canonical preparation notice stops new work while rights and drains remain available. The same-chain canonical handoff candidate now carries ownership and accounting. Different-pair conversion, arbitrary local venues and cross-chain canonical relocation remain unimplemented.


---

Generated from [the task ledger](docs/project-todo.json). Update that ledger, then run `python scripts/sync-project-todo.py`; use `--check` to detect stale generated content.

Snapshot SHA-256: `f4063a6d9a37ead064b080a099263c3d80a6005f5fedb2796cd5e8554b7f547c`.
