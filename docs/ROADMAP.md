# Engineering roadmap

> Reviewed 2026-10-18 against the [central Todo](../TODO.md), [current handoff verification](../reports/canonical-handoff/VERIFICATION.md) and [release approval record](RELEASE_CHECKLIST.md). Release remains NOT APPROVED. This roadmap sets the sequence and dependencies; the Todo alone owns task status and acceptance criteria.

The [feature and evidence reference](IMPLEMENTATION_STATUS.md) describes the candidate: shared nonredeemable LP allocations, receipt-backed rewards and royalties, atomic activation entry, custody controls and bounded same-chain canonical handoff. Read it for implementation boundaries rather than treating the roadmap as another feature inventory. Historical [reward-funding](../reports/reward-funding/README.md), [shared-pool](../reports/pooled/README.md) and [earlier implementation](../reports/IMPLEMENTATION_UPDATE.md) reports retain their own source scope.

Work proceeds through contract safety, qualified dependencies, backend/frontend integration and operating rehearsals, then independent release approval. Service research and tooling can run alongside contract work, but sealing must wait for the accepted pre-seal capabilities. Initially disabled bridges defer provider activation, not missing contract functionality.

## 1. Establish a reproducible build

Owning tasks: [local verification](../TODO.md#task-local-verification), [integration security](../TODO.md#task-security-integration).

Retain the dependency lockfile, compiler profile, unit/fuzz results and runtime/initcode size gates. Reuse evidence only when its relevant source and configuration bindings match; rerun affected checks when they change. Review package contents and pin remaining upstream/CI references to immutable revisions. Benchmark execution gas under the size-oriented optimizer profile and preserve production deployment margin, including constructor arguments. Verify exact-commit Ubuntu CI separately from local results.

The current four-historical-bucket cap follows combined funded-inbox/dust/index workloads that invalidated the earlier 16-bucket gas assumption. It does not change the 1,000-NFT supply or initial shared pool. Preserve the failing evidence and qualify actual Entry/venue execution at the four-bucket bound. Current regression and cold-gas results are recorded in the [handoff verification](../reports/canonical-handoff/VERIFICATION.md); its intentional fork skips are not live dependency qualification.

## 2. Prove custody and reward accounting

Owning tasks: [shared accounting](../TODO.md#task-security-share-accounting), [ownership and rewards](../TODO.md#task-security-ownership-rewards), [custody composition](../TODO.md#task-custody-composition), [whole-protocol recovery](../TODO.md#task-security-chain-recovery), [governance](../TODO.md#task-security-governance).

Extend the independent integer-ledger stateful handler beyond its current local custody/reward scope. Existing unit/fuzz and stateful tests cover mint, activation, top-ups, harvest, owner changes, claims, pauses, donations, compounding and rebalance. Add full multi-chain stateful and real provider failure behavior; existing repeated migration tests still use a mock transport. Review coverage rather than treating a passing run as proof of every possible sequence.

Independently qualify the [implemented same-chain canonical handoff](CANONICAL_HANDOFF.md): six receipt cutoffs, ordered bounded settlement, complete ownership/inventory/shares and reward-ledger export/import, exact classified backing, restored abort, atomic source retirement/single-successor activation and late forwarding. Its supported source has all mints revealed, Parked/None local buckets, no active plans and no historic legacy bridge activity. An imported successor cannot initiate v3 principal bridging.

Before sealing, complete the accepted [cross-chain canonical design](CANONICAL_MIGRATION_DESIGN.md): verified finalized source retirement with no multisig/timeout override, authenticated channel closure, new lineage/message semantics and exact transport/backing. Different-pair conversion also needs typed execution, composition epochs and preserved old-currency liabilities. The implemented 3% budget applies only to atomic local same-ordered-pair move/resume, with gas separate; it is not a cross-chain budget. Do not remove pair guards or assume a future provider can add absent sealed-code capabilities. Post-halt recovery remains deferred.

Successors may use different reviewed code approved through timelocked governance, as the user accepted. A malicious approved successor could divert LP; review code, admission and bindings independently. This accepted governance trust does not waive backing, single-successor retirement or verified finality. Include contract-owner/escrow compatibility and marketplace collection cutover in the handoff rehearsal.

## 3. Validate real Uniswap operation

Owning tasks: [selected pool](../TODO.md#task-pons-qualification), [activation assets](../TODO.md#task-activation-assets), [complete quotes](../TODO.md#task-activation-quotes), [mainnet fork](../TODO.md#task-mainnet-fork), [strategy security](../TODO.md#task-security-strategy).

Use pinned-block fork tests against actual supported PositionManager, PoolManager, Permit2, and StateView deployments. Exercise mint, increase, collection, close, swaps, approvals, callbacks, donations, and failure paths. Measure rebalancing and all-asset checkpoint costs at realistic collection sizes.

The older fixed-block suite used a different hookless pool. The selected-native/Pons adapter preserves the physical PoolKey, normalizes only accounting to WETH, checks reviewed runtimes/wiring and handles native settlement without spending prefunds. Recorded selected-pool fork runs cover that path for their exact source/block snapshots; complete release-source fork/gas/strategy qualification. The current offline regression did not run those opt-in fork suites. This is not generic hook approval or permission to deploy. Mock-venue collection/asset workloads do not establish target-pool operating costs.

Independently qualify the implemented immutable [atomic Entry](ACTIVATION_ENTRY.md): original-source gross valuation, exact received balances, current-owner intent and one full 1% execution/undeployed bound across conversion and LP deployment. Register and rehearse actual ZZZ/ETH/USDG routes and supply a funded reviewed USDC route before enabling it. Reject quotes that cannot meet the bound; do not subsidize them with incumbent LP, idle or compound assets.

Rehearse [custody parking](CUSTODY_PARKING.md) through the sealed two-day timelock: global pause, exact bucket snapshot, close-only raw-token minimums, nonce cancellation/expiry and honest Parked custody reporting. Prove fresh-oracle resume and reviewed parked migration retain funding/legacy-liability barriers. Price-feed and inbox independence does not bypass actual venue, wrapper or token failures.

## 4. Validate the accepted economics and NFT lifecycle

Owning tasks: [creator terms](../TODO.md#task-creator-terms), [random assignment](../TODO.md#task-fair-draw), [metadata operations](../TODO.md#task-metadata-ops), [dependency security](../TODO.md#task-security-dependencies), [asset liveness/dust](../TODO.md#task-asset-liveness-dust), [backend integration](../TODO.md#backend), [frontend integration](../TODO.md#frontend).

Independently review equal activated-NFT membership, collection/delivery-time collective allocation for unharvested/remote rewards, processing-time creator receipts, incumbent pending/indexed/dust settlement, remote/in-flight eligibility and reward-asset limits. Model timing incentives, manipulated valuations, depreciated positions, strategy costs, and token eligibility. Review the implemented repeated-hop custody epochs, ordered home-location ACKs, canonical returns, legacy reward budgets, and post-seal append-only route governance against adversarial operation sequences.

The user reports creator revenue sharing proportional to PoPL liquidity. Exact [sampled measurement tools](REVENUE_SHARE.md) now propose fee-weighted active share (preferred with complete reliable fee observations) or time-weighted active share; neither is creator-approved yet or reconstructs exact intra-swap v4 fee attribution. Confirm the base, window, sampling, payout asset/frequency and rounding; implement the complete hook-event/trace parser and reconcile actual receipts. Only funded, processed payments enter the existing 80/10/5/5 indexes. Native custody support does not confer Pons revenue rights. The website's assumed conventional-fee example remains hypothetical. See [external funding](EXTERNAL_REWARDS.md).

Before paid minting, establish actual supported-chain VRF, subscription backing and measured callback/failure recovery. Quotas/inventory and current-value evolution have local tests, but mock VRF does not establish Robinhood service support. The eight-color/58-palette/four-pattern library covers 2,784 artwork states; its verified IPFS upload bundle is prepared, not pinned. Choose redundant hosting, verify the final CID and every renderer path, then stage the already-implemented market-driven watcher with real feeds and marketplace caches. Marketplace royalty payment remains voluntary. The immutable 32-operation [claim router](CLAIM_ROUTER.md) now batches LP and royalty claims; independently qualify worst-case gas, owner callbacks and frontend chunking.

The [confirmed API](FRONTEND_API.md) reads real NFT state and both funded ledgers. Its optional [history extension](FRONTEND_HISTORY.md) now provides wallet inventory and all-time per-NFT/asset LP-plus-royalty claims from exact confirmed raw-log replay, with canonical ownership/count checks. Host and rehearse it, independently reconcile ingestion completeness, and finish gross lifetime/24h fee attribution/USD projections. Replace website simulations only after a reviewed deployment exists.

Integrate the [implemented strict API lifecycle boundary](FRONTEND_LIFECYCLE.md) into wallet flows and complete successor-aware history. Locked deployments already refuse NFT/wallet projections and imported successor lifetime totals remain explicitly unavailable. Lifetime LP and royalty claims must include verified predecessors, and imported NFTs must not be counted as new paid mints or marketplace sales. Show execution-time rights when buying an NFT, since a seller can claim before transfer. Local unpublished unsigned-preparation work is not a deployed signing service.

## 5. Rehearse operations and qualify later transport

Owning tasks: [authorities and prices](../TODO.md#task-authorities-prices), [keeper guards](../TODO.md#task-keeper-guardrails), [keeper recovery](../TODO.md#task-keeper-recovery), [hosted services](../TODO.md#task-host-services), [testnet rehearsal](../TODO.md#task-testnet-rehearsal), [destination capacity](../TODO.md#task-destination-slots), [bridge operation](../TODO.md#task-bridge-operation).

Qualify the exact keeper/controller/fixture versions together. Strict canonical-state and preparation checks stop new submissions in locked states while pending receipt recovery continues. Existing isolated staging has not been upgraded to this lifecycle; historical crash/recovery receipts do not qualify the changed integration. Rehearse nonce/budget continuity, backups, host loss, old-host fencing, key rotation, RPC/fee behavior and independent alerts. The user paused the desktop chat monitor; it supplies no observations after that pause and must not be restarted without authorization.

Real bridge transport can remain disabled at initial launch. An independently approved [migration-disabled launch](OPERATIONS.md#migration-disabled-initial-launch) still requires the pre-seal capabilities in section 2 and all applicable security/service/operating gates. Provider qualification and enabling routes are separate later actions; disabling them does not close unfinished canonical migration or different-pair implementation.

The fixed router and append-only future-provider onboarding framework are implemented. Select and independently review bridge-specific `IZZZTransportProvider` wrappers, establish equivalent-token and supply semantics, and test canonical-to-satellite, satellite-to-satellite, canonical return, and revisited destinations against actual providers. Exercise authentication, backing, duplication, ordered home notifications, absent-hop epochs, delays, retries, legacy rewards after departure, pauses, and provider failures. Review every future destination's code and authorities before timelocked route onboarding. Exercise real signer/RPC behavior and indexer backfill/reorg recovery on a test network.

Before enabling a real bridge, independently qualify the implemented permanent destination capacity admission and real provider recovery. Reservations and historical custody share four permanent slots; aliases and returns reuse them. Source governance must still authenticate the reviewed destination and confirmed admission. The [architecture evolution design](ARCHITECTURE_EVOLUTION.md) separates different-pair conversion, fixed-home remote custody and canonical NFT/ledger relocation. Home-chain creator-funded 5% compound reserves still wait for custody to return unless a separately reviewed funded remote reinvestment design is added. Task status remains in the central Todo.

## 6. Complete independent review before release

Owning tasks: [security and audit](../TODO.md#security--audit), [release approval](../TODO.md#task-audit-release).

Obtain an independent security audit, verify remediation, review deployment configuration, and satisfy the applicable [central release criteria](../TODO.md#task-audit-release) before recording final approval in the [release record](RELEASE_CHECKLIST.md).

## Later product work

Actual input routes, live projections, production VRF/feeds/authorities, immutable artwork publication, testnet operating rehearsals and independent audit remain initial release work. Use all three release-test layers: local security/accounting, actual selected-pool Robinhood mainnet fork and Robinhood Testnet operation; Sepolia is supplementary. Multi-hop buybacks and satellite deposits remain later extensions. Only compatible provider/route onboarding can be deferred through existing timelocked interfaces; absent conversion, lineage or canonical transport capabilities cannot be added to sealed contracts by configuration.
