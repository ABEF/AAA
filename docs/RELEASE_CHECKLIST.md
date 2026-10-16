# Release checklist - NOT APPROVED

## NFT ownership/revenue review gate - 2026-10-16

- [x] Challenge the supplied prompt against accepted product rules, then independently
  review source, ownership/receipt boundaries and the final tests.
- [x] Execute 1,000-NFT multi-owner/multi-stream accounting, current-owner transfer
  and receiver-callback regressions, buyback failure/retry and dual-ledger invariants.
  Exact results and source scopes are in the
  [verification report](../reports/nft-rights-audit/VERIFICATION.md).
- [x] Keep the four-bucket combined-workload bound and unchanged 12M local gas
  ceiling. Actual Entry/venue/token costs remain a separate qualification.
- [ ] Approve admitted-token outage/upgrade/blacklist behavior and economic value
  of repeated sub-20-raw-unit incumbent dust settlements.
- [ ] Verify marketplace payment and claims; do not advertise ERC2981 as enforced
  royalties or a listing's claim balance as guaranteed at purchase.
- [ ] Complete production services, creator terms, frozen-release independent audit
  and operating rehearsals. Real bridging remains blocked by destination capacity
  admission and provider/recovery qualification.

- [ ] Complete the seven [security audit workstreams](SECURITY_AUDIT_PLAN.md), including a pre-seal decision on permanent home-chain loss and canonical NFT/reward-ledger recovery. LP migration alone is insufficient. Allocation percentages remain fixed; evaluate any proposed configurability separately.

Status remains **NOT APPROVED**. A local/source-bound internal review is not an
independent audit or authorization for public deployment or real funds.

Updated 2026-10-16. Checked development items identify implemented code and recorded internal evidence; they do not approve deployment or real funds. Unchecked production gates require actual integration, release-specific evidence and independent qualification. The [Implemented / Todo checklist](IMPLEMENTATION_STATUS.md) records feature status. Historical metadata and integration/recovery receipts retain their exact source scope; later Entry/parking source requires its own verification.

## Completed development work

- [x] Implement the accepted mint, activation, shared-pool, 80/10/5/5, equal collective membership, rarity, artwork and separate royalty rules. See the [component map](COMPONENT_STATUS.md) for source boundaries; selected-market compatibility remains separate.
- [x] Add permissionless metadata notifications for at most 50 inclusive mint ordinals, emitting each actual hashed token ID without price reads or custody changes. Targeted Solidity tests cover bounds, atomic failure, pause, transfers and valuation outages.
- [x] Add an optional confirmed-block metadata watcher using the keeper's existing simulation, serial signer, budgets and pending recovery. It is disabled by default; initial observation and successful notification remain distinct states.
- [x] Record a read-only [selected-market feasibility review](../reports/release-hardening/selected-market-review.md), including two-provider fixed-block observations and the required native settlement/accounting design. This is not a compatible adapter or an independent audit.
- [x] Run fresh pinned internal Slither against the metadata source change: 179 findings, individually reviewed with zero unresolved review entries. Retain source/configuration hashes and coverage checks; independent audit remains open.
- [x] Run the complete local offline suite: 342 Solidity passes, one expected fork setup skip, and 372 portable Python passes; four unchanged Unix-only cases remain for Ubuntu. The focused keeper run passes 109 tests, with separate internal execution of ten regression cases.
- [x] Check all 20 normal runtime/initcode objects and the 318,466-gas cold 50-token notification workload. Constructor-argument allowance, actual-venue gas and the Vault's 169-byte runtime margin still need release qualification.

The completed counts above describe the earlier metadata source snapshot. Its Slither triage does not cover the subsequent native/Pons, gross-input, policy, router and API changes; the fresh receipts below cover the current candidate separately.

Earlier local [integration/recovery evidence](../reports/release-progress/README.md) records **430 Solidity passes**, **478 portable Python passes**, all **22 size gates**, all **28 source bindings**, **17 actual selected-pool fork passes** and **210 individually reviewed Slither findings** with zero unresolved review entries. These counts predate the atomic Entry and custody-parking changes. Four Unix-only Python cases, release-revision Ubuntu CI, production services/staging and independent audit remain open.

- [x] Implement the strictly pinned selected native/Pons boundary and canonical WETH accounting, retaining rejection of other native/hooks.
- [x] Add append-only activation-source admission and wrapper dependency policies, plus disabled-source-pool exits that retain price and real dependency checks. These preserve governed onboarding/recovery paths without making arbitrary new tokens, implementations or bridges safe.
- [x] Add governed, append-only sequencer source replacement with code/review provenance, no zero-source bypass after configuration and mandatory up-plus-one-hour grace. All 12 focused tests pass within the current full suite; no production source is selected.
- [x] Implement the immutable 32-operation LP/royalty claim router and confirmed read API, including optional canonical wallet inventory and cumulative raw LP/royalty claim history from complete trusted indexer coverage. Hosting and frontend transactions remain open.
- [x] Implement fee-weighted/time-weighted measurement proposals and prepare the complete verified artwork upload archive; creator agreement and pinning remain open.
- [x] Implement immutable [atomic source entry](ACTIVATION_ENTRY.md), binding the exact current owner and Vault calldata to original measured source value, with one 1% conversion-plus-LP budget and callback-safe context. Actual production routes and feeds remain unqualified.
- [x] Implement [custody parking](CUSTODY_PARKING.md): paused timelocked exact snapshot, close-only raw minimums, nonce/deadline/review binding, principal retained in Vault, preserved funded claims and oracle-guarded resume. Parked cross-chain departure retains authenticated route/funding/legacy-liability barriers; actual providers remain unqualified.

Current [gap-hardening evidence](../reports/gap-hardening/README.md) records **488 Solidity passes**, **488 portable Python passes**, **23 normal size gates**, **29 production source bindings**, and **220 individually reviewed Slither findings**, with zero unresolved review entries. The separate actual fork run passes **20 selected native/Pons plus nine secondary hookless cases**, zero failures/skips; the two offline setup skips are not reused as fork evidence. This remains local development evidence with explicit authority/VRF/USD fixtures; final-release Ubuntu, external services/staging and independent qualification remain unchecked below.

## Required testing layers

Complete all three layers for the final release, retaining the source revision, configuration and results. Existing local tests and fork evidence remain scoped to the revisions and dependencies they actually exercised.

- [ ] **Local tests:** minting, activation, rewards, royalties, transfers and security.
- [ ] **Robinhood mainnet fork:** compatibility with the actual ZZZ pool, hook and deployed dependencies. The existing separate hookless-pool tests do not close this gate.
- [ ] **Robinhood Testnet:** wallet flows, website integration, keeper operations and deployment rehearsals, with actual supported services and explicit records of any mocked or unavailable dependencies.

Sepolia may supplement these layers; it does not replace Robinhood-specific integration and staging. This checklist does not authorize deployment or transactions.

## Source, toolchain and economics

- [ ] Reproduce all Solidity/Python tests for the final frozen production release on supported Ubuntu, retaining exact source revision, compiler settings and full logs. Candidate CI and earlier green CI for `5febe70` do not validate future source changes.
- [ ] Compile every contract/test/script and check normal runtime/initcode limits and current gas; small Vault/FeeController margins require explicit review.
- [ ] Independently review the final source-bound Slither triage and accepted risks, refreshing analysis if source changes. Completed internal triage does not close the external audit gate.
- [ ] Independently verify isolated 0.05 ETH mint proceeds, the 1,000-NFT cap, exact 600/300/100 quotas, atomic failure and no reroll/trait override.
- [ ] Independently verify $100 original source value with at least 99% marginal actually deployed LP, separate network gas, incumbent NAV pricing, all conversion-leg costs, callbacks, pending/dust barriers, top-ups and nonredeemability. Review the immutable Entry's exact owner/calldata context, inactive approval window, Registry-only valuation and callback cleanup; a post-conversion pair value cannot replace original source value.
- [ ] Independently verify 80/10/5/5 funding, 90% remote delivery, equal collective membership and index/fractional solvency across transfers, entries and migrations.
- [ ] Review the economic value of at most 19 raw units settled before membership changes, asset decimals and holder-triggerable entry frequency.

## NFT randomness, royalties and metadata

- [ ] Independently verify actual supported proof-verifying coordinator code/key/subscription/confirmations/gas and service availability on the deployment chain. An ABI or mock is not verification.
- [ ] Stage real requests, out-of-order callbacks, strict mint-order reveal, subscription outages, reorg/finality and permanent early-request blocking recovery. No cancellation/reroll/admin bypass exists.
- [ ] Verify canonical sealing rejects missing randomness configuration; verify content root and every artwork/metadata path against an independently reviewed immutable catalog.
- [ ] Independently review the 5% ERC-2981 request and 100% eligible royalty redistribution in the separate immutable ETH/ERC20 ledger at activated rarity weights 1/2/3. Marketplace payment remains voluntary.
- [ ] Inventory all royalty assets and review exact transfers, rebases, mutable authority, prefund/zero-member quarantine, pending settlement, claim callbacks, fractional/global dust, transfer rights and activation outage behavior.
- [ ] Configure OpenSea creator earnings to the actual `NFT.royaltyRewards()` helper at 5%, verify collection-administration access and each admitted payout asset, and stage a paid sale through receipt, weighted claim and NFT transfer. The current contract requests optional earnings; it does not implement ERC-721-C enforcement.
- [ ] Stage live oracle/NAV thresholds, downward evolution and remote/stale unavailable labels; claims and migration must remain independent of metadata price reads.
- [ ] Stage the implemented watcher with actual feeds, reviewed NFT runtime pins, RPC limits, confirmation recovery and gas budgets. Publish/pin the complete 2,784-state artwork manifest and independently verify its root, every path and actual marketplace rendering/ERC-4906 cache refresh.

## Market, valuation and operating integration

- [ ] Independently qualify the implemented selected native-ETH/Pons boundary, including wrapper implementation/admin upgrades, native settlement, real-key/accounting mapping and actual-pool tests. Keep production inventory native admission blocked until complete; do not broaden it to arbitrary hooks.
- [ ] Supply reviewed feeds, decimals, denomination, heartbeat/sequencer/outage policy and admitted tokens on every chain.
- [ ] Independently review and stage sequencer policy replacement through the actual sealed timelock, including failed old feeds, unchanged healthy feeds, code changes and recovery grace. Bootstrap references are not independent reviews, and proxy runtime pins do not pin their implementations. Confirm an actual supported Robinhood source or explicitly reviewed no-feed chain policy; no ZZZ/USD feed is selected.
- [ ] Review governed activation-source enable/disable, future token admission, wrapper implementation/admin changes and disabled-source exit rehearsals. Admitting a source token does not add its conversion route; removing it must not revoke existing LP/reward rights. Ordinary exits remain price-guarded; parked close uses separately approved raw-token bounds. Rehearse governed feed repair without claiming unconditional recovery from external wrapper/bridge failure.
- [ ] Independently stage paused parking through the sealed timelock: missing/stale price feeds, failed creator inbox, exact share/LP/custody snapshot, close-only minimums excluding idle/compound/donations, one-sided principal, invalidation/replay/expiry, claims/transfers and fresh-oracle resume. Authenticate current-source evidence in the inventory's mandatory `parking_rehearsal` record.
- [ ] Review USDC/USDG/ETH/ZZZ source-to-LP routing through the implemented Entry: exact token provenance, actual liquidity, fresh source prices, immutable binding/runtime, original-source budget, exact approvals and complete append-only route history. Native ingress is restricted to the actual native-pool wrapper. USDC remains disabled without a funded reviewed route; unsigned quotes alone do not establish qualified execution.
- [ ] Quote and test $100 source value with no more than 1% total execution/undeployed cost and gas separate. Reject quotes or revert when the limit cannot be met; do not promise zero gas loss on reverts. Independently review the 32-operation claim router, runtime/bindings, constructor-byte allowance and wallet batching behavior.
- [ ] Stage actual Uniswap swaps/entry/maintenance, malicious token/callback behavior, exact approvals/settlement, stale prices, donations and failures.
- [ ] Qualify gas for 1/100/1,000 NFTs and maximum actual assets/inboxes; prove upkeep scales by shared pool. Backtest range, trigger, cooldown, slippage, impermanent loss, MEV and operating cost. Production strategy parameters remain unset.
- [ ] Review creator inboxes, optional wrappers, discretionary payment terms, processing-time eligibility and maximum-16-inbox costs. Creator payment frequency and percentage remain undecided.
- [ ] Confirm terms with the pool creator: percentage and calculation basis, payout asset/network, payment frequency, authorized payer/configurer and actual PoPL receiver. Terms were explicitly deferred on 2026-10-15; receipt-driven implementation must not imply guaranteed revenue. Stage a payment through allocation and holder claim.
- [ ] Agree and qualify the proposed active-liquidity measurement policy: fee-weighted or time-weighted, epoch/sampling/finality, complete fee events, tick-crossing approximation, cross-asset payout conversion and receipt reconciliation. The implemented calculator has no payout authority and does not prove creator acceptance.
- [ ] Select an IPFS pinning provider and publish the verified complete artwork bundle; independently verify the resulting CID, all renderer paths and ongoing pin availability. Provider selection and publication were deferred; preparing a bundle alone does not establish hosting.
- [ ] Stage keeper keystore isolation, nonce/receipt recovery, RPC failover, budgets, indexer backfill/reorgs, alerts and Unix state locking. The supplied systemd unit defaults to dry run.
- [ ] Integrate actual wallet transactions and the implemented confirmed API/history service, including the separate royalty ledger, lifetime per-asset claims and indexed ownership. Independently pin/review the immutable 32-operation router, simulate exact batches and bound/chunk portfolio claims. Gross earned fees and USD history require separate data/valuation; raw claimed totals cannot substitute for them.

## Migration, governance and independent release review

The user has not selected production governance, guardian, keeper or mint-recipient addresses and explicitly requested leaving these gates open. Do not substitute example addresses or infer deployment authorization.

The provider/delivery gates apply before enabling real migration. An explicitly reviewed migration-disabled initial launch may instead satisfy the empty-policy/route requirements in [operations](OPERATIONS.md#migration-disabled-initial-launch); governance, ordinary custody, audit and staging gates still apply.

- [ ] Independently review real provider SDK wrappers, backing/equivalent token semantics, channels, finality, exact funding and recovery.
- [ ] Stage canonical -> satellite -> satellite -> home -> revisit with actual providers, duplicate/reordered/forged/underfunded receipts, ACK epochs, pauses, old-policy and historical reward paths.
- [ ] Verify destination reservations, frozen canonical shares/membership, no remint/principal refund, legacy liability barriers, and governance trust for every new destination.
- [ ] Rehearse source-oracle-independent departure of an already Parked bucket with designated compound reserves, retained `remoteSettled` barrier, exact attributed transfers, destination valuation and reviewed provider recovery. Parking does not waive bridge backing or enable arbitrary conversion.
- [ ] Select and verify multisig/keeper/guardian/mint-recipient authorities, fixed timelock and module bindings; prohibit mint/LP/royalty receiver collisions.
- [ ] Complete an independent external security audit, remediation verification and separate deployment/configuration review, then limited staging with approved limits.

The schema-4 production inventory must include current economics, NFT helper/randomness/asset observations and authentic release/staging evidence. Its blocked state is intentional; an offline consistency pass never authorizes deployment, sealing, signing or real funds.

## Keeper recovery qualification

- [ ] Stage [the keeper recovery runbook](KEEPER_RECOVERY.md): multi-day outage, lost server, stale/missing state, nonce/budget reconciliation, old-host fencing and key rotation.
- [ ] Verify off-host backups, health/log alert delivery, permissions/disk failures and actual Linux service restart/locking. Local guards are not production operating evidence.


## Isolated operating rehearsal evidence - 2026-10-16

- [x] 209 exact-revision Ubuntu keeper/monitor/RPC/state tests with zero failures/skips; 14 local Anvil process scenarios, including broadcast crash boundaries and stale state.
- [x] Authorized website-host staging with an isolated service account, loopback-only test chain and resource/filesystem/network limits.
- [x] Actual systemd keeper restart/forced-crash recovery, preserved nonce/budget, controlled off-host snapshot round-trip restore, and read-only monitor command/forwarding restrictions.
- [x] Stopped-service detection and recovery through the off-host read-only monitor; unchanged public website hash over HTTPS.
- [ ] Finish and review sustained multi-day staging; preserve observation gaps. The current 30-minute chat heartbeat depends on desktop availability.
- [ ] Qualify independent production alerts/backups/retention, redundant RPCs and complete real fee accounting.
- [ ] Complete actual Robinhood Testnet end-to-end operation, physical host-loss/key-rotation rehearsal and independent audit/configuration approval.

Evidence: [keeper operating rehearsals](../reports/keeper-rehearsal/README.md). No public contracts or transactions were deployed/submitted in this work.
