# Engineering roadmap

**Current policy, 2026-10-24:** [Typed v4 conversions](TYPED_V4_ROUTES.md) and
[governed execution-loss limits](EXECUTION_LOSS_POLICY.md) are implemented in the
undeployed candidate. Defaults are 1% contribution, 1% conversion and 3% maintenance;
immediate governance may set each category up to a hard 10%. Existing stricter
venue/caller minima remain. Pending normal custody approvals retain their original
absolute floor. Earlier fixed-cap or v3-only descriptions below retain their
historical/default scope. Actual routes, services and independent audit remain open.


**Internal audit follow-up (2026-10-24):** [Fee-sizing and operational fixes](../reports/daily-security-20261024/REVIEW.md) are implemented with focused evidence. The broader [native design audit](NATIVE_ETH_ARCHITECTURE.md) identifies pre-seal implementation blockers; the [native V2 implementation](../reports/native-eth-port/VERIFICATION.md) now has scoped local evidence. Complete its explicit ETH/WETH boundary, versioned service/frontend and target-chain qualification before sealing; actual services and independent audit remain open.

**Pre-seal flexibility (2026-10-24):** [Operational configuration](../TODO.md#task-post-seal-configuration) and the [native ETH architecture](NATIVE_ETH_ARCHITECTURE.md) must be implemented/reviewed before sealing if these future controls are required. [Real-funds rehearsal planning](../TODO.md#task-mainnet-rehearsal-retirement) uses a separate deployment followed by a fresh final collection, not a reset. No public execution is authorized.

**Selected pool (2026-10-24):** Robinhood Uniswap v4 native ETH/ZZZ `0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b`, static 1.002% LP fee, no hook. The observed protocol fee makes the combined fee about 1.101%. Hookless native admission and atomic `moveFunds` are the current candidate; external `exit` remains separately approved and paused. [Selection and limits](POOL_SELECTION.md). Production remains NOT APPROVED.

**Current candidate (2026-10-23):** [governed custody handoff](GOVERNED_CUSTODY_HANDOFF.md) replaces the legacy LP v3 bridge/pair executor. Whole-collection handoff remains separate. Normal all-ZZZ exit, explicitly approved raw emergency exit and separate royalty-currency custody are local candidates; real finality/remote accounting, the updated production inventory and independent qualification remain open. Earlier descriptions/evidence retain their historical scope. [Verification](../reports/custody-handoff/VERIFICATION.md).

> Reviewed 2026-10-24 against the [central Todo](../TODO.md), [current handoff verification](../reports/canonical-handoff/VERIFICATION.md) and [release approval record](RELEASE_CHECKLIST.md). Release remains NOT APPROVED. This roadmap sets the sequence and dependencies; the Todo alone owns task status and acceptance criteria.

The [feature and evidence reference](IMPLEMENTATION_STATUS.md) describes the candidate: shared nonredeemable LP allocations, receipt-backed rewards and royalties, atomic activation entry, custody controls and bounded same-chain canonical handoff. Read it for implementation boundaries rather than treating the roadmap as another feature inventory. Historical [reward-funding](../reports/reward-funding/README.md), [shared-pool](../reports/pooled/README.md) and [earlier implementation](../reports/IMPLEMENTATION_UPDATE.md) reports retain their own source scope.

Work proceeds through contract safety, qualified dependencies, backend/frontend integration and operating rehearsals, then independent release approval. Service research and tooling can run alongside contract work, but sealing must wait for the accepted pre-seal capabilities. Governed external custody does not complete remote NFT ownership, reward accounting or finality. Qualify those separately before promising full future-chain operation.

The [website local integration](LOCAL_WEBSITE.md) exercises confirmed data and
holder transactions through disposable Anvil accounts. Its separate
[browser-wallet profile](BROWSER_WALLET.md) now prepares unsigned calls for
independent EIP-1193 signing. Continue with actual extension acceptance and
production wallet-provider/deployment/route qualification; do not rebuild the
simulation or treat the local signer as a production service. Frontend progress
remains owned by the central wallet, portfolio, transaction-UI and history tasks.

Resolve [Creator tasks / ZZZ team](../TODO.md#creator-tasks--zzz-team) alongside dependency research: pricing and actual markets feed activation qualification; revenue terms, measurement and payment operations feed funding qualification. An unanswered ZZZ-feed question does not establish a live price source. Team answers require independent technical checks before enabling real flows.

## Confirmed collection progress - 2026-10-23

The [collection read API/explorer](COLLECTION_READS.md) now implements complete
canonical inventory and current-LP aggregation, with bounded pinned pages and
[scoped evidence](../reports/collection-reads/VERIFICATION.md). Remaining work is
actual service/history/pricing/latency qualification, not another demo rebuild.
Different-token operations now use separately approved external custody; atomic
moveFunds retains ordered-pair guards. Future-chain canonical transport remains
unfinished and is not supplied by external custody alone.

## Current custody direction - 2026-10-24

Atomic `Migration.moveFunds` supports admitted same-accounting-pair venue/fee-tier
changes with actual destination LP, unchanged NFT shares and one fixed 3% aggregate
cap. Native V2 retains actual ETH identity; same-native-pair fee-tier moves work, while atomic ETH/WETH conversion is unfinished and rejected. Normal
paused external `exit` consolidates principal into ZZZ; separately approved raw
exit sends both accounting currencies without a USD guarantee. A failed normal
exit never selects raw mode automatically. Follow [operator steps](GOVERNED_CUSTODY_HANDOFF.md).

The former typed pair executor and v3 bridge paths are removed. Their
[pair-composition report](../reports/pair-composition/VERIFICATION.md) retains its
historical revision scope, not operative features. Different-token conversion or
bridging uses explicitly trusted external custody, actual funded completion/return
and reviewed remote finality where applicable; no real verifier or remote ledger
is supplied. Whole-collection handoff remains separate.

The [native V2 implementation](NATIVE_ETH_ARCHITECTURE.md) now carries actual ETH
through custody, Entry, fees, indexed rewards, raw exit and canonical backing.
Complete explicit ETH/WETH conversion and old-schema compatibility separately;
qualify real native markets, service/frontend profiles, gas and independent audit.
Existing Anvil deployments and their historical evidence remain unchanged.

The [post-seal operating controls](POST_SEAL_POLICY.md) now implement bounded
future VRF gas/confirmation tuning and a buyback operating ceiling within its
immutable maximum. Their provider/deployment operating qualification remains
open. Complete typed v4 conversion before sealing; preserve pending request
provenance, immutable traits, rights, backing and execution floors. Existing route
setters cannot add new code.
The 1% ZZZ reward-conversion cap remains, gas separate; require a cheaper qualified
route than the selected pool's observed 1.101% fee. Do not invent a route or raise
the cap. Real-funds rehearsal uses a separate deployment and fresh final collection,
not an NFT/accounting reset.

## Current sequencing decision - 2026-10-20

Update 2026-10-22: production work now includes shared API/current-holdings earnings
and collection holder allocations, with [scoped evidence](../reports/wallet-earnings/VERIFICATION.md).
Production minting is intended for [OpenSea](OPENSEA_MINT.md); qualify its exact
primary-mint integration before sealing. Website minting is demonstrative and
local direct minting remains a test tool. Focus the production website on positions,
activation, growth and claims. This does not lift the local-only signer restriction.

The user reports all six [manual two-wallet scenarios](../reports/local-wallet-concurrency/MANUAL_ACCEPTANCE.md)
passed. The local [browser-wallet implementation](BROWSER_WALLET.md) now has
typed unsigned preparation, independent signing and saved transaction recovery,
with [scoped automated and Anvil evidence](../reports/browser-wallet/VERIFICATION.md).
The [latest confirmation fix](../reports/browser-wallet/CHAIN_READER.md) uses a pinned
node reader independently of wallet response formatting and is [published](../reports/browser-wallet/PUBLICATION.md).
The [reviewed API profile](DEPLOYMENT_WEBSITE.md) now connects reads and unsigned
reviews to those endpoints. Its [local API wallet coordinator](DEPLOYMENT_WEBSITE.md#local-api-wallet-rehearsal) now exercises submission/recovery with the unchanged Anvil-only signer. The user explicitly retained that restriction on 2026-10-21. The [actual API/Anvil rehearsal](LOCAL_API_REHEARSAL.md) now has real receipts and full-wallet LP/ETH totals. Next verify actual extension behavior and qualify services; any future nonlocal signer extension needs explicit authorization and reviewed deployment/fee policy. Public signing remains disabled. The EIP-1193-shaped test provider
does not close extension acceptance or authorize public funds.

The proposed [10/25/100-user capacity campaign](../TODO.md#task-capacity-campaign)
is deferred at the user's request and may be revisited after launch if needed.
No campaign is scheduled; capacity remains unverified. This changes sequencing,
not the requirement for safe configured concurrency, qualified dependencies,
accounting/recovery checks or independent release approval. The local shared
signer/global-lock launcher remains test-only. Other pre-seal boundaries below
are unchanged; task status remains exclusively in the central Todo.

## 1. Establish a reproducible build

Owning tasks: [local verification](../TODO.md#task-local-verification), [integration security](../TODO.md#task-security-integration).

Retain the dependency lockfile, compiler profile, unit/fuzz results and runtime/initcode size gates. Reuse evidence only when its relevant source and configuration bindings match; rerun affected checks when they change. Review package contents and pin remaining upstream/CI references to immutable revisions. Benchmark execution gas under the size-oriented optimizer profile and preserve production deployment margin, including constructor arguments. Verify exact-commit Ubuntu CI separately from local results.

The current four-historical-bucket cap follows combined funded-inbox/dust/index workloads that invalidated the earlier 16-bucket gas assumption. It does not change the 1,000-NFT supply or initial shared pool. Preserve the failing evidence and qualify actual Entry/venue execution at the four-bucket bound. Current regression and cold-gas results are recorded in the [handoff verification](../reports/canonical-handoff/VERIFICATION.md); its intentional fork skips are not live dependency qualification.

## 2. Prove custody and reward accounting

Owning tasks: [shared accounting](../TODO.md#task-security-share-accounting), [ownership and rewards](../TODO.md#task-security-ownership-rewards), [custody composition](../TODO.md#task-custody-composition), [whole-protocol recovery](../TODO.md#task-security-chain-recovery), [governance](../TODO.md#task-security-governance).

Extend the independent integer-ledger stateful handler beyond its current local custody/reward scope. Existing unit/fuzz and stateful tests cover mint, activation, top-ups, harvest, owner changes, claims, pauses, donations, compounding and rebalance. Add full multi-chain stateful and real provider failure behavior; historical bridge tests used mock transport and do not verify the current custody replacement. Review coverage rather than treating a passing run as proof of every possible sequence.

Independently qualify the [implemented same-chain canonical handoff](CANONICAL_HANDOFF.md): six receipt cutoffs, ordered bounded settlement, complete ownership/inventory/shares and reward-ledger export/import, exact classified backing, restored abort, atomic source retirement/single-successor activation and late forwarding. Its supported source has all mints revealed, Parked/None local buckets, no active plans and no historic legacy bridge activity. The old v3 principal bridge implementation is removed.

Before sealing, complete the accepted [cross-chain canonical design](CANONICAL_MIGRATION_DESIGN.md): verified finalized source retirement with no multisig/timeout override, authenticated channel closure, new lineage/message semantics and exact transport/backing. External issuer exchanges preserve original shares and old-currency liabilities; real funded destination completion is distinct from atomic same-pair movement. The implemented 3% budget applies to ordinary rebalance and atomic local same-ordered-pair move/resume, with gas separate; it is not a cross-chain budget. Do not remove pair guards or assume a future provider can add absent sealed-code capabilities. Post-halt recovery remains deferred.

Successors may use different reviewed code approved through governance, as the user accepted. A malicious approved successor could divert LP; review code, admission and bindings independently. This accepted governance trust does not waive backing, single-successor retirement or verified finality. Include contract-owner/escrow compatibility and marketplace collection cutover in the handoff rehearsal.

## 3. Validate real Uniswap operation

Owning tasks: [selected pool](../TODO.md#task-pons-qualification), [activation assets](../TODO.md#task-activation-assets), [complete quotes](../TODO.md#task-activation-quotes), [mainnet fork](../TODO.md#task-mainnet-fork), [strategy security](../TODO.md#task-security-strategy).

Use pinned-block fork tests against actual supported PositionManager, PoolManager, Permit2, and StateView deployments. Exercise mint, increase, collection, close, swaps, approvals, callbacks, donations, and failure paths. Measure rebalancing and all-asset checkpoint costs at realistic collection sizes.

The current selected hookless native adapter preserves the physical PoolKey, retains actual ETH accounting in V2, checks reviewed runtimes/wiring and handles native settlement without spending prefunds. Earlier Pons forks retain their original source scope. Recorded selected-pool fork runs cover that path for their exact source/block snapshots; complete release-source fork/gas/strategy qualification. The current offline regression did not run those opt-in fork suites. This is not generic hook approval or permission to deploy. Mock-venue collection/asset workloads do not establish target-pool operating costs.

Independently qualify the implemented immutable [atomic Entry](ACTIVATION_ENTRY.md): original-source gross valuation, exact received balances, current-owner intent and one full 1% execution/undeployed bound across conversion and LP deployment. Register and rehearse actual ZZZ/ETH/USDG routes and supply a funded reviewed USDC route before enabling it. Reject quotes that cannot meet the bound; do not subsidize them with incumbent LP, idle or compound assets. The implemented [complete preparation service](ACTIVATION_PREPARATION.md) now performs two full Entry simulations and returns bounded unsigned calldata. Next qualify actual route/feed manifests, hash-selected callTracer support/logs and complete network-fee estimation on the intended providers, then integrate wallet approval/requote/signing/receipts.

Rehearse [custody parking](CUSTODY_PARKING.md) through the sealed zero-delay controller: global pause, exact snapshot, raw minima, nonce/expiry and honest parked custody reporting. Prove guarded resume and separately approved external custody preserve shares/liabilities. Price-feed independence does not bypass venue, wrapper or token failure.

## 4. Validate the accepted economics and NFT lifecycle

Qualify [marketplace settlement currencies](../TODO.md#task-royalty-eth-settlement)
before expanding the royalty asset set. Start with ETH pricing and verified ETH/WETH
receipts; distinguish buyer checkout funds from actual royalty transfers. The candidate now implements guarded batch ETH conversion and optional-currency
outage isolation. The [API conversion/eligibility projections](ROYALTY_REPORTING.md)
are implemented; qualify their real ingestion and consumers alongside actual
wrapper/routes/feeds, recovery UI and keeper behavior before live activation. Direct-currency
claims remain a fallback; balances stay attached to the same NFTs. See the
[decision and procedure](ROYALTY_SETTLEMENT.md).

Owning tasks: [creator terms](../TODO.md#task-creator-terms), [random assignment](../TODO.md#task-fair-draw), [metadata operations](../TODO.md#task-metadata-ops), [dependency security](../TODO.md#task-security-dependencies), [asset liveness/dust](../TODO.md#task-asset-liveness-dust), [backend integration](../TODO.md#backend), [frontend integration](../TODO.md#frontend).

Independently review equal activated-NFT membership, collection/delivery-time collective allocation for unharvested/remote rewards, processing-time creator receipts, incumbent pending/indexed/dust settlement, remote/in-flight eligibility and reward-asset limits. Model timing incentives, manipulated valuations, depreciated positions, strategy costs, and token eligibility. Review current custody request epochs, actual departure/return quantities, pending external custody and post-seal route governance against adversarial operation sequences. Legacy bridge ACK tests are historical, not current transport support.

The selected hookless pool earns ordinary LP fees; the old Pons creator-payment
agreement is not a launch dependency. [Sampled revenue-share tools](REVENUE_SHARE.md)
and [external funding research](EXTERNAL_REWARDS.md) remain conditional/historical
unless a new external agreement is adopted. Independently verify actual LP fees,
80/10/5/5 processing and ZZZ pricing; do not infer a new creator entitlement.

Before paid minting, establish actual supported-chain VRF, subscription backing and measured callback/failure recovery. Quotas/inventory and current-value evolution have local tests, but mock VRF does not establish Robinhood service support. The eight-color/58-palette/four-pattern library covers 2,784 artwork states; its verified IPFS upload bundle is prepared, not pinned. Choose redundant hosting, verify the final CID and every renderer path, then stage the already-implemented market-driven watcher with real feeds and marketplace caches. Marketplace royalty payment remains voluntary. The immutable 32-operation [claim router](CLAIM_ROUTER.md) now batches LP and royalty claims; independently qualify worst-case gas, owner callbacks and frontend chunking.

The [confirmed API](FRONTEND_API.md) reads real NFT state and both funded ledgers. Its optional [history extension](FRONTEND_HISTORY.md) now provides wallet inventory and all-time per-NFT/asset LP-plus-royalty claims from exact confirmed raw-log replay, with canonical ownership/count checks. The optional [earnings profile](EARNINGS_HISTORY.md) now reconstructs processed lifetime/24h attribution and current-price USD. Next qualify complete seven-emitter backfills, actual Oracle/feed/proxy policies and large-history/reorg workloads, then integrate its clearly separated earnings/balance/payout fields in the website. Use [bounded independent-RPC history comparison](HISTORY_AUDIT.md) to detect omitted/conflicting logs and validate raw block windows for every epoch. Review provider independence, complete contiguous coverage, epoch cutoffs and production-scale database/index costs; matching partial windows do not close these gates. Replace website simulations only after a reviewed deployment exists.

Integrate the [implemented strict API lifecycle boundary](FRONTEND_LIFECYCLE.md) and [complete configured same-chain claim lineage](FRONTEND_LINEAGE.md) into wallet flows. Qualify historical archive reads, complete ingestion, retirement-cutoff retention and bounded request latency. Locked deployments refuse NFT/wallet projections; missing lineage stays unavailable and invalid configured lineage fails closed. Lifetime LP and royalty claims include verified predecessors and past owners; imported NFTs are not new paid mints or marketplace sales. Cross-chain history remains part of future canonical migration. Show execution-time rights when buying an NFT, since a seller can claim before transfer. The [implemented unsigned mint/claim preparer](FRONTEND_TRANSACTIONS.md) supplies exact typed drafts and separate reviewed gas estimates. Next qualify the actual policy/provider and connect browser account/chain changes, confirmation, rejection, receipt/replacement and recovery handling; the backend is not a signing service.

The implemented [range-policy application](RANGE_POLICY_UPDATES.md) uses the
existing governance controller and ordinary keeper path. Qualify production widths/cooldowns,
runtime pins and change/resimulation procedures in the operating rehearsal; an
eligible range update is not a promised keeper execution time.

## 5. Rehearse operations and qualify later transport

Owning tasks: [authorities and prices](../TODO.md#task-authorities-prices), [keeper guards](../TODO.md#task-keeper-guardrails), [keeper recovery](../TODO.md#task-keeper-recovery), [hosted services](../TODO.md#task-host-services), [testnet rehearsal](../TODO.md#task-testnet-rehearsal), [destination capacity](../TODO.md#task-destination-slots), [bridge operation](../TODO.md#task-bridge-operation).

Qualify the exact keeper/controller/fixture versions together. Strict canonical-state and preparation checks stop new submissions in locked states while pending receipt recovery continues. Existing isolated staging has not been upgraded to this lifecycle; historical crash/recovery receipts do not qualify the changed integration. Rehearse nonce/budget continuity, backups, host loss, old-host fencing, key rotation, RPC/fee behavior and independent alerts. The user paused the desktop chat monitor; it supplies no observations after that pause and must not be restarted without authorization.

The current release candidate has no operative legacy LP bridge/router or typed
pair executor. Qualify [governed custody](GOVERNED_CUSTODY_HANDOFF.md), actual
recipients, post-withdrawal exit depth, raw minima and funded completion/return.
Remote custody requires pinned finality/channel-closure verification; no real
verifier, provider, remote NAV/reward ledger or canonical relocation is supplied.
Do not treat external manual bridging as complete NFT/ledger migration.

Local permanent reservations share four historical bucket slots. Verify admitted
pool aliases/capacity before departure; this is not authenticated remote admission.
Future-chain canonical relocation, ownership/reward continuity and accounting
remain separate design/implementation/qualification gates. See the
[current recovery matrix](CHANGE_AND_RECOVERY.md), not historical bridge procedures.

A real-funds campaign requires a separate clearly named rehearsal deployment,
reviewed exact configuration and explicit spending/signing authorization. Preserve
production guards when testing production behavior. Archive receipts and remaining
obligations; pause/exit does not reset NFT supply, reward liabilities or public
history. Deploy the final collection fresh under the
[rehearsal policy](POST_SEAL_POLICY.md#testing-with-real-funds-on-robinhood).

## 6. Complete independent review before release

Owning tasks: [security and audit](../TODO.md#security--audit), [release approval](../TODO.md#task-audit-release).

Obtain an independent security audit, verify remediation, review deployment configuration, and satisfy the applicable [central release criteria](../TODO.md#task-audit-release) before recording final approval in the [release record](RELEASE_CHECKLIST.md).

## Later product work

Actual input routes, live projections, production VRF/feeds/authorities, immutable artwork publication, testnet operating rehearsals and independent audit remain initial release work. Use all three release-test layers: local security/accounting, actual selected-pool Robinhood mainnet fork and Robinhood Testnet operation; Sepolia is supplementary. Further conversion algorithms and remote deposits require reviewed code, not merely route records. Only capabilities already implemented can be configured after sealing; absent native recovery, conversion or canonical transport cannot be added by a setter.

Before committing a collection replacement, resolve the code-bearing holders from
[the inventory procedure](HOLDER_PREFLIGHT.md) while transfers still work, then
reconcile a fresh frozen snapshot. Actual escrow/marketplace rehearsals remain under
[canonical recovery](../TODO.md#task-security-chain-recovery).

## ETH-only holder payout dependency

Complete [LP ETH settlement](../TODO.md#task-lp-eth-settlement) before final claim
UI qualification and sealing. The royalty converter is a separate path. Preserve
already-earned individual/collective entitlements, backing and conversion history,
then qualify exact WETH unwrap and ZZZ swaps, keeper recovery and combined claims.
The current generic local tokens demonstrate accounting, not named-asset routing.
