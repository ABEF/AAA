# Project Todo

**Reviewed 2026-10-16 | Contracts undeployed | Not approved for production**

The single task list for the whole PoPL project. Open a task's acceptance criteria for the detailed release requirements. There is no Todo page on the public website.

**15 To do | 14 In progress | 9 Implemented locally**

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

<a id="task-nft-lifecycle"></a>

- [x] **[Minting, activation & NFT ownership](src/ZZZVault.sol)** - Implemented. 1,000-NFT cap, 0.05 ETH mint and $100 gross-value activation with at least 99% deployed as LP. Rights follow the NFT.

<a id="task-reward-ledgers"></a>

- [x] **[LP fees & separate royalty shares](docs/ECONOMICS.md)** - Implemented. 80 / 10 / 5 / 5 funded LP allocation with documented raw-unit dust settlement; equal collective shares. Actual royalties go to active NFTs at x1 / x2 / x3, separately from LP shares.

<a id="task-shared-custody"></a>

- [x] **[Shared LP, maintenance & custody controls](docs/ARCHITECTURE.md)** - Implemented. One shared LP per pool/strategy serves many NFTs. The local four-historical-bucket safety bound, permanent allocations, pool-level upkeep, timelocks, parking and guarded resumption are implemented.


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

  </details>

<a id="task-activation-quotes"></a>

- [ ] **[Complete activation & top-up quotes](docs/ACTIVATION_ROUTING.md#atomic-entry-candidate-and-remaining-qualification)** - In progress. Conversion quoting exists. Finish the full route into LP with one 1% execution-loss limit and gas shown separately.

  <details>
  <summary>Acceptance criteria</summary>

  - Quote and test $100 source value with no more than 1% total execution/undeployed cost and gas separate. Reject quotes or revert when the limit cannot be met; do not promise zero gas loss on reverts.
  - Build a complete original-source-to-LP quote against actual reviewed routes and feeds, including the Pons deployment leg. Authenticate Entry/Registry/Oracle/helper bindings and append-only route policy history; conversion-only quotes are not signable activation preparation.
  - Pin all call/code/storage reads to one canonical block hash; verify provider support and final snapshot freshness, rejecting stale/future observations and unsupported selectors without fallback. Rehearse every target input with separate gas estimates.

  </details>

<a id="task-read-api"></a>

- [x] **[Confirmed balances & ownership API](docs/FRONTEND_API.md#implemented-endpoint)** - Implemented. Read NFT ownership and funded balances; reconstruct cumulative claims from complete confirmed history.

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

  </details>

<a id="task-transaction-ui"></a>

- [ ] **[Handle the complete transaction journey](docs/CLAIM_ROUTER.md)** - To do. Show gas, approvals, confirmation, rejection and recovery when an account, network or receipt changes.

  <details>
  <summary>Acceptance criteria</summary>

  - Show original contribution value, exact approvals, the 1% execution limit and network gas separately. Rejected or reverted execution may still cost network gas.
  - Independently review and pin deployments, the immutable 32-operation claim router runtime/bindings and exact calldata. Chunk larger portfolios; recheck owner/assets, simulate and estimate gas immediately before user confirmation. Handle account/network changes, stale drafts, rejection, replacement, failure and canonical receipt/reorg recovery.
  - Mint/claim drafts have client-enforced expiry, not an on-chain calldata deadline. Discard stale drafts and prepare again; do not describe unsigned backend preparation as signing or live wallet integration.

  </details>

<a id="task-live-history-ui"></a>

- [ ] **[Connect live history & cumulative claims](docs/FRONTEND_HISTORY.md#api-behavior)** - To do. Display verified 24-hour / all-time fees and lifetime claimed totals, including royalties.

  <details>
  <summary>Acceptance criteria</summary>

  - Display verified 24-hour/all-time earned fees separately from claimable balances. Previously claimed means lifetime per-asset LP plus royalty claims across all prior claims/owners, not just the last claim.
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
  - Complete the seven [security audit workstreams](docs/SECURITY_AUDIT_PLAN.md), including a pre-seal decision on permanent home-chain loss and canonical NFT/reward-ledger recovery. LP migration alone is insufficient. Allocation percentages remain fixed; evaluate any proposed configurability separately.
  - Fill and independently authenticate the schema-4 production inventory: release-specific source/configuration, code and helper bindings, assets, randomness, parking rehearsal and operating evidence. Its current blocked state is intentional; offline consistency never authorizes deployment, sealing or real funds.
  - Preserve complete exact-release local/Ubuntu, actual Robinhood mainnet-fork and Robinhood Testnet evidence. Partial/cancelled fork runs and older source snapshots do not qualify the final release; test timeouts must retain partial evidence without counting as a pass.

  </details>

<a id="task-mainnet-fork"></a>

- [ ] **[Robinhood mainnet-fork qualification](test/NativePoolFork.t.sol)** - In progress. Actual selected-pool cases pass. Qualify production price feeds, full activation routes and real-service assumptions; synthetic calibration and mock authorities do not close those gates.

  <details>
  <summary>Acceptance criteria</summary>

  - **Robinhood mainnet fork:** compatibility with the actual ZZZ pool, hook and deployed dependencies. The existing separate hookless-pool tests do not close this gate.
  - Stage actual Uniswap swaps/entry/maintenance, malicious token/callback behavior, exact approvals/settlement, stale prices, donations and failures.

  </details>

<a id="task-local-verification"></a>

- [x] **[Local contract and integration tests](reports/nft-rights-audit/VERIFICATION.md)** - Implemented. Minting, activation, reward accounting, royalties, transfers and security cases have local checks. Each new change still needs fresh source-bound evidence.

<a id="task-economic-rights-audit"></a>

- [x] **[Verify NFT economic rights at full collection size](reports/nft-rights-audit/VERIFICATION.md#integrated-collection-and-stateful-assertions)** - Implemented. Internal ownership, 1,000-NFT payouts, buyback rollback and dual-ledger invariants verified: 531 offline Solidity passes, two intentional fork setup skips; extended rights invariants completed 65,536 calls. This closes the scoped local verification task, not independent audit or production qualification.


## Security & audit

Seven audit workstreams. Local checks are partial evidence; independent review and release sign-off remain open. See [the security audit plan](docs/SECURITY_AUDIT_PLAN.md) for acceptance criteria and priorities.

<a id="task-security-chain-recovery"></a>

- [ ] **[Whole-protocol recovery & canonical chain loss](docs/SECURITY_AUDIT_PLAN.md#6-protocol-availability-and-long-term-recoverability)** - To do. Decide before sealing how to handle permanent home-chain loss, lost governance keys and unusable critical contracts. LP migration alone leaves canonical NFT ownership and reward ledgers at home. A full identity/liability migration needs an audited snapshot/finality, duplicate-prevention, in-flight claims and old-chain resurrection policy; it is not implemented.

  <details>
  <summary>Acceptance criteria</summary>

  - Make an explicit reviewed architecture decision before sealing for permanent home-chain loss, canonical NFT ownership and reward-ledger recovery. Moving LP alone does not restore those records or authorities; do not claim universal recovery.

  </details>

<a id="task-security-governance"></a>

- [ ] **[Governance, permissions & sealing](docs/SECURITY_AUDIT_PLAN.md#1-governance-permissions-and-sealing)** - In progress. Audit every role, timelock, configuration and external-module trust boundary for a path around nonredeemable custody. Prove sealed bindings stay fixed and supported asset/feed/route/parameter changes remain bounded; review malicious destinations, lost keys and emergency powers.

  <details>
  <summary>Acceptance criteria</summary>

  - Review governed activation-source enable/disable, future token admission, wrapper implementation/admin changes and disabled-source exit rehearsals. Admitting a source token does not add its conversion route; removing it must not revoke existing LP/reward rights. Ordinary exits remain price-guarded; parked close uses separately approved raw-token bounds. Rehearse governed feed repair without claiming unconditional recovery from external wrapper/bridge failure.
  - Independently stage paused parking through the sealed timelock: missing/stale price feeds, failed creator inbox, exact share/LP/custody snapshot, close-only minimums excluding idle/compound/donations, one-sided principal, invalidation/replay/expiry, claims/transfers and fresh-oracle resume. Authenticate current-source evidence in the inventory's mandatory `parking_rehearsal` record.

  </details>

<a id="task-security-share-accounting"></a>

- [ ] **[Shared LP accounting & economic manipulation](docs/SECURITY_AUDIT_PLAN.md#2-shared-lp-accounting-and-economic-manipulation)** - In progress. Verify 1,000 independent NFT share accounts through deposits, top-ups, compounding, rebalancing and migrations. Extend local conservation and gas evidence with adversarial prices, donation/front-running, dilution, rounding and multi-asset economic tests on qualified venues.

  <details>
  <summary>Acceptance criteria</summary>

  - Review creator inboxes, optional wrappers, discretionary payment terms, processing-time eligibility and combined four-bucket/four-inbox costs with all admitted assets. The factory's separate 16-inbox ceiling does not enlarge current Vault capacity. Qualify actual Entry/Pons gas, not only the passing local fixture. Creator payment frequency and percentage remain undecided.

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

  </details>

<a id="task-security-dependencies"></a>

- [ ] **[External dependencies & receipt backing](docs/SECURITY_AUDIT_PLAN.md#5-external-dependencies-and-revenue-accounting)** - In progress. Review Uniswap v4, Pons, creator payments, tokens/wrappers, oracles, randomness and future bridges for upgrades, compromise, outages and unexpected behavior. Reconcile every asset liability to actual receipts; test quarantine, duplicate/delayed funding, token failure and provider/destination change.

<a id="task-security-integration"></a>

- [ ] **[Cross-contract & infrastructure audit](docs/SECURITY_AUDIT_PLAN.md#7-cross-contract-and-infrastructure-vulnerabilities)** - In progress. Audit complete transaction paths and failure rollback across contracts, frontend, API/indexer, deployment, keys and keeper services. Rehearse reorgs, replay, stale or compromised data, wrong-chain signing, RPC failure, restore/rotation and monitoring. Independent review and operational sign-off remain open.


## Launch & operations

Decisions and rehearsals before real funds.

<a id="task-authorities-prices"></a>

- [ ] **[Select authorities & price services](docs/PRODUCTION_SERVICES.md)** - To do. Confirm governance, guardian, keeper and mint-recipient addresses, plus reliable USD pricing and outage policies.

  <details>
  <summary>Acceptance criteria</summary>

  - Supply reviewed feeds, decimals, denomination, heartbeat/sequencer/outage policy and admitted tokens on every chain.
  - Independently review and stage sequencer policy replacement through the actual sealed timelock, including failed old feeds, unchanged healthy feeds, code changes and recovery grace. Bootstrap references are not independent reviews, and proxy runtime pins do not pin their implementations. Confirm an actual supported Robinhood source or explicitly reviewed no-feed chain policy; no ZZZ/USD feed is selected.
  - Select and verify multisig/keeper/guardian/mint-recipient authorities, fixed timelock and module bindings; prohibit mint/LP/royalty receiver collisions.

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

  </details>

<a id="task-keeper-guardrails"></a>

- [ ] **[Harden keeper recovery and monitoring](docs/KEEPER_RECOVERY.md)** - In progress. Recovery guards, read-only preflight/health checks and exclusive snapshots are implemented. Isolated server staging and read-only off-host monitoring are operating; desktop availability limits that monitor. Production RPC/fees, independent alerts and review remain open.

  <details>
  <summary>Acceptance criteria</summary>

  - Stage keeper keystore isolation, nonce/receipt recovery, RPC failover, budgets, indexer backfill/reorgs, alerts and Unix state locking. The supplied systemd unit defaults to dry run.
  - Qualify canonical-hash RPC selectors for every activation state read, stale-snapshot rejection, strict receipt recovery across midnight/reorgs, and the chain's complete L2/L1 fee reporting. Offline mocks do not establish provider support or complete real network costs.
  - Qualify independent production alerts/backups/retention, redundant RPCs and complete real fee accounting.

  </details>

<a id="task-keeper-recovery"></a>

- [ ] **[Rehearse keeper outage & server recovery](docs/KEEPER_REHEARSALS.md)** - In progress. 209 Ubuntu safety tests and 14 process rehearsals pass; the same 14 scenarios pass under the isolated server account. Actual systemd crash/restart and off-host snapshot round-trip restore passed. Sustained soak, physical host loss and governance key rotation remain open.

  <details>
  <summary>Acceptance criteria</summary>

  - Stage [the keeper recovery runbook](docs/KEEPER_RECOVERY.md): multi-day outage, lost server, stale/missing state, nonce/budget reconciliation, old-host fencing and key rotation.
  - Verify off-host backups, health/log alert delivery, permissions/disk failures and actual Linux service restart/locking. Local guards are not production operating evidence.
  - Finish and review sustained multi-day staging; preserve observation gaps. The current 30-minute chat heartbeat depends on desktop availability.

  </details>


## Future migration

A separate phase. Disabled at initial launch.

<a id="task-destination-slots"></a>

- [ ] **[Reserve destination capacity](docs/CHANGE_AND_RECOVERY.md#destination-capacity-unresolved-proposed-next-implementation)** - To do. Reserve space before liquidity travels, including concurrent arrivals, returns and recovery if delivery is delayed.

  <details>
  <summary>Acceptance criteria</summary>

  - Fix and independently review destination **capacity** reservation: the present pool-to-bucket reservation does not reserve a historical slot, so unrelated first arrivals can exhaust it before delivery. Test concurrent arrivals/local registrations, duplicate pool reservations for one bucket, returns and failure recovery. Keep real bridging disabled until this is resolved.
  - Reserve durable historical capacity before delivery, not just pool identity. Reuse returning slots; test local/remote concurrency, duplicate/idempotent registration, reserved None-state enumeration and delayed/cancelled operations without freeing a reservation that an in-flight delivery may still need.

  </details>

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

<a id="task-migration-framework"></a>

- [x] **[Governed migration framework](src/ZZZMigration.sol)** - Implemented. Timelocked approval can onboard reviewed future EVM chains and pools while preserving NFT allocations.


---

Generated from [the task ledger](docs/project-todo.json). Update that ledger, then run `python scripts/sync-project-todo.py`; use `--check` to detect stale generated content.

Snapshot SHA-256: `48ca1e431b674f71d558c751be95b10820f9a3bc0c8ecdbcba1ba2e31428d8ae`.
