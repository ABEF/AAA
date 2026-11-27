# Engineering roadmap and production qualification plan

This guide owns acceptance requirements and execution order. The
[current review](../reports/CURRENT_REVIEW.md) owns present evidence and
readiness; [findings](AUDIT_FINDINGS.md) owns unresolved issues and accepted
limits. [TODO.md](../TODO.md) remains the only task-status checklist.

All23 acceptance packages and their task ownership remain. Historical progress
snapshots and test transcripts are archived in Git, rather than repeated here.
Unknown launch inputs remain blocked. Deployment, sealing and public opening
require separate explicit approval; this roadmap authorizes none of them.

## Requirements that this plan preserves

Only native ETH and one fixed ZZZ fund LP. Royalties are paid in original currencies;
LP fees use separate same-NFT ZZZ-to-ETH settlement. Preserve 80/10/5/5, exact-unit
rights and current-owner unpaid balances. Royalty grace is **one hour**; history's
raw suffix remains **86400 seconds**. Neither changes the other.

Spot is chosen for placement AND independent valuation. Do not add TWAP, duplicate
one ZZZ source behind two ETH feeds, change the destination or relax guards.
Defaults remain 3% contribution, 1% conversion, 3% maintenance, 1% additional execution
loss and 3% source agreement, with distinct caller/idle/venue checks. Selected
contribution preparation is 32M/full 20%; maintenance 24M/full 25%, legacy 12M defaults
unchanged. Fees and funding are separate from gas-unit ceilings.

Ordinary timing remains 85% centre-to-boundary, same-side independent corroboration,
600s sampled persistence/300s max gap/240s source polling,12h hard minimum and
durable60-300s service jitter. Extra compound waiting stays in keeper software.
Emergency financial bypass remains explicit paused-governance action; structural
permissions, custody and exact accounting stay mandatory.

One human operator/governance, separate limited keeper and guardian; no timelock
reintroduced. Terminal exit pays NFT holders, never a custody address. No bridge,
third LP input, token-retarget setter, post-exit importer or post-halt rescue is
revived. Dedicated10/25/100-user load testing remains user-deferred; sale-rights
disclosure is excluded. Basic concurrency correctness and bounded overload remain
required, without silently scheduling the deferred benchmark.

## Ordered gates and critical path

| Gate | Work | Evidence needed to advance |
| --- | --- | --- |
| A: scope and feasibility | P01-P05, P11/P14/P15/P19 choices | Actual proposed sources/routes/platform/provider, authority-wallet and user-submission approach are supportable. Unknown inputs stay blocked. |
| B: missing implementation and evidence | P06-P22 as applicable | Close confirmed defects and unproved launch partitions; exact accounting/rollback/resource/recovery proof, current F6 construction and matched full-stack rehearsal. |
| C: freeze and independent review | P02/P23 | Frozen code/config/build/evidence, independent audit/remediation and affected rechecks; unsigned deployment package with named accepted risks. |
| D: separately authorized deployment, closed and unsealed | P11/P22 | Actual receipts/runtime/immutables/children/roles/bindings and complete pre-seal readiness. These proofs cannot exist before deployment. |
| E: separately authorized sealing, still closed | Actual integration portions of P03-P05/P07-P11/P14-P21/P23 | Complete necessary deployed/sealed wallet/marketplace/VRF/host observations using explicitly authorized, bounded non-destructive operations. No terminal test on final principal. |
| F: separately approved public launch | P21/P23 | Named go/no-go, actual release/config hashes, funded services, alerts, stop/restart and residual-risk decisions. Open only qualified features. |

Begin actual market/provider/platform discovery in parallel with compiler review
and independent local fixes. Do not repeat large synthetic campaigns while
launch prices or execution depth remain infeasible. Freeze source before final
audit, and refresh affected proof after fixes. Some platform onboarding or final
source verification needs actual addresses; staged gates avoid pretending it is
already complete before deployment. Never invent an operating-soak duration:
agree objectives, observation period, incident thresholds and owner first.

## Acceptance packages

Each package needs source/config identity, meaningful success AND rollback/failure
assertions, exact raw evidence, known limitations and the central Todo owner.
Read the linked operator procedures before irreversible changes.

### P01 — Launch profile and accepted decisions

Final production-pool selection is operator-deferred as of20November2026. The
existing integration target remains unchanged and unapproved; pool-dependent
acceptance waits for the actual selection. No alternative is chosen automatically.

Freeze initial width, residual mode/floor/gap, currency list/capacity, reviewed venues, workers, supported workloads and wallet sizes, gas/fee budgets and actual authority-wallet type.

Separate enabled launch features from disabled capabilities. A smaller initial currency set does not qualify later expansion; a disabled worker does not waive required pre-seal bindings.

Retain explicit spot pricing, software-only compound waiting, immediate governance, per-operation rather than cumulative loss caps and emergency financial bypass decisions. Record their operating consequences rather than silently redesigning rights.

Owning Todo: [`native-production-preflight`](../TODO.md#task-native-production-preflight), [`post-seal-configuration`](../TODO.md#task-post-seal-configuration), [`lp-only-simplification`](../TODO.md#task-lp-only-simplification), [`immediate-governance`](../TODO.md#task-immediate-governance), [`adaptive-range-policy`](../TODO.md#task-adaptive-range-policy).

### P02 — Compiler, dependencies and evidence validity

The [current compiler assessment](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/compiler-applicability-20261120/REVIEW.md) evaluates all eight registry variants against exact0.8.26/Cancun, via-IR/EVM optimization with Yul optimization DISABLED. No confirmed reachable defect requiring upgrade was found. This completes current applicability review only; re-evaluate after new advisories or source/dependency/settings changes. A version match alone is not a project defect.

Inspect exact settings, dependency source, relevant call graph and generated IR where needed; give every candidate a reviewable disposition. Do not upgrade compiler automatically.

Freeze exact source/dependency/control/artifact/static/CI identities. Reuse unchanged proofs; recheck tests whose production dependencies changed even if their test files did not. Any justified compiler/source change needs new pins and affected size, static, gas and functional evidence.

Owning Todo: [`local-verification`](../TODO.md#task-local-verification), [`audit-release`](../TODO.md#task-audit-release), [`security-dependencies`](../TODO.md#task-security-dependencies).

### P03 — Independent prices and reference integrity

Choose independently defensible ETH and fixed-ZZZ valuation paths with exact chain/token/adapter/feed identities, denomination/decimals/rounds, publication/funding ownership, freshness and3% agreement/outage behavior. Two ETH feeds multiplied by one ZZZ pool repeat one ZZZ exposure.

Rank external usable depth excluding PoPL liquidity; raw TVL/current L does not prove independence or bidirectional depth. Review upstream publishers, markets, proxies and administrators; stored spot does not prove recent trading.

Preserve the chosen spot policy for placement AND valuation. Qualify external-reference-as-swap own-transition proofs and same-core principal-reference exclusion, including what to do if our pool becomes the largest. Unknown or stale prices remain explicitly unavailable; no implicit TWAP or single-source fallback.

Owning Todo: [`dual-price-qualification`](../TODO.md#task-dual-price-qualification), [`creator-zzz-price`](../TODO.md#task-creator-zzz-price), [`price-security`](../TODO.md#task-price-security), [`pool-spot-price-source`](../TODO.md#task-pool-spot-price-source).

### P04 — Actual pools, swap routes and upstream controls

Authenticate actual fixed ZZZ, PoolKey/core/PositionManager/Permit2, hooks, directional fees and implementation/controller powers. Review token pause/freeze/tax/rebase behavior, exact decimals and burn semantics; code hashes do not freeze proxy/upstream behavior.

Verify both trade directions and representative sizes with depth remaining AFTER our LP withdrawal, compatible destination/reference price bands, partial-fill rejection and market movement between review and execution.

Qualify a separately suitable ZZZ-to-ETH LP-reward route under the default1% conversion cap. The selected pool's dated approximately1.101% fee is not that qualification. Forward-only quote screens, synthetic liquidity and cheap tiny swaps are not complete operation acceptance.

Owning Todo: [`pons-qualification`](../TODO.md#task-pons-qualification), [`lp-execution-routing`](../TODO.md#task-lp-execution-routing), [`creator-market-controls`](../TODO.md#task-creator-market-controls), [`creator-input-liquidity`](../TODO.md#task-creator-input-liquidity), [`typed-v4-conversion`](../TODO.md#task-typed-v4-conversion).

### P05 — Chain, RPC, finality and complete fees

Verify current chain/genesis/version, required Cancun/transient behavior, actual transaction/block execution limits and selected provider call/estimate/trace/body/log/archive/rate/deadline limits. Tiny overrides and synthetic headers do not establish full operation capacity.

Qualify exact32M/full20% contribution and24M/full25% maintenance payloads, canonical-hash reads, missing-state rejection, reorgs, failover and outage/grace policy. Distinguish L2 inclusion from posted/finalized state; document sequencer inclusion limitations.

Reconcile complete Nitro execution plus posting fees with exact estimates and later receipts; count posting once. Separately approve fee-price/per-operation/day/ETH-funding limits and feed/VRF costs. Documented chain capabilities do not relax PoPL's strict24576 runtime/49152 initcode gates.

Owning Todo: [`host-services`](../TODO.md#task-host-services), [`deployment-initcode`](../TODO.md#task-deployment-initcode), [`native-production-preflight`](../TODO.md#task-native-production-preflight).

### P06 — Maximum supported resource workloads

Resolve the slow64-currency/two-LP opening-ZZZ refusal:27142801 estimate,32571362 padded; at least476135 estimated gas reduction is needed for32M/full20%. Until qualified, do not approve this state for currency-capacity expansion. Never substitute trace gas or reduce padding.

Cover actual slow/failed currencies, full-width coefficient/carry spills and lifetime state, activation/rarity/claim order, large per-NFT and collection principal, and real Access/Registry omitted from the maximum-state producer.

Qualify cold conversion/claim batches, exit batches and full canonical gas separately. Four execution venues, four logical buckets, two legs,32 selection entries and64 ERC20 currencies are independent bounds, not a combined gas promise. Reuse unchanged eleven contribution and five maintenance successes at their exact scope.

Owning Todo: [`activation-quotes`](../TODO.md#task-activation-quotes), [`security-share-accounting`](../TODO.md#task-security-share-accounting), [`activation-gas-six-cases`](../TODO.md#task-activation-gas-six-cases), [`royalty-factory-gas`](../TODO.md#task-royalty-factory-gas), [`claim-batch-planner`](../TODO.md#task-claim-batch-planner).

### P07 — Contributions and physical LP lifecycle

Verify ETH/ZZZ activation and growth: exact approvals, incumbent fee checkpoint, entrant-only swap/deploy, marginal deployed LP, net-NAV shares, idle/compound classification and full callback/failure rollback. Contributions grow MAIN without recentering it or resetting its clock.

Compose1-to-2-to-1-to-2 journeys through flat, bullish, bearish, reversal, gap, boundary and thin-depth markets; main/residual mixed or filled states remain valued, harvested and attributable. Residual mode changes never drop a live leg.

Exercise user/trader/operator transaction ordering, transfers and stale reviews at each transition. Main boundary ticks stay fixed while spot/composition moves; external transactions do not interleave within an atomic call, but dependency callbacks can.

Owning Todo: [`activation-assets`](../TODO.md#task-activation-assets), [`shared-custody`](../TODO.md#task-shared-custody), [`liquidity-placement-idle`](../TODO.md#task-liquidity-placement-idle), [`reviewed-contribution-policy`](../TODO.md#task-reviewed-contribution-policy), [`security-share-accounting`](../TODO.md#task-security-share-accounting).

### P08 — Harvest, LP settlement, compound and burn

The [maximum-state settlement/claim report](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/lp-claims-maximum-20261120/REVIEW.md)
adds finite same-NFT conversion, cold gas/refusal and transfer/fault evidence; the
new request-local code-proof reuse addresses a measured planner CPU bottleneck.
Actual route/provider/complete-fee and full production API admission remain open.

Reconcile both-leg actual fee collection and fixed80/10/5/5, including the documented tiny-fee split rule, liabilities/backing and current-owner rights before/after partial claims, transfers, rebalances and exit. Harvest itself performs no swaps.

Prove separate same-NFT ZZZ-to-ETH settlement, affordable partial batches, failed-swap rollback and approval cleanup. Compound spends only designated/attributed funds; buyback spends only its reserve and actually burns the fixed ZZZ. Claims/conversions never create new income.

Qualify economical thresholds, no-op handling and idle reinvestment without arbitrary sweeps. Inspect the unresolved historical late-fee-netting question against actual mutable token/periphery callbacks; only reproduce/harden if reachable, and do not label it an ordinary interleaving trader exploit.

Owning Todo: [`reward-ledgers`](../TODO.md#task-reward-ledgers), [`lp-exact-unit-allocation`](../TODO.md#task-lp-exact-unit-allocation), [`lp-eth-settlement`](../TODO.md#task-lp-eth-settlement), [`asset-liveness-dust`](../TODO.md#task-asset-liveness-dust).

### P09 — Royalty opening and original-currency rights

Verify official sale-end revisions/equality/expiry, final ONE-hour grace, incomplete sellout, strict activation cohort, zero cohort, late activations, preadmission receipts, explicit recovery allocation and fault/recovery cohorts.

Prove all allocated smallest units can be assigned/claimed through transfers and arbitrary claim order; preserve old entitlements and distinct temporary opening/unallocated categories. No universal immediate-allocation guarantee is possible when no eligible NFT exists.

Qualify actual token gas/behavior and reviewed admission from16 to64 ERC20s plus ETH. The64 lifetime capacity is a long-term limit, not unlimited token support. Frozen/malicious tokens cannot be forced to transfer. Original-currency royalties need no conversion or mandatory keeper collection.

Owning Todo: [`royalty-eth-settlement`](../TODO.md#task-royalty-eth-settlement), [`royalty-reporting`](../TODO.md#task-royalty-reporting), [`security-ownership-rewards`](../TODO.md#task-security-ownership-rewards), [`asset-liveness-dust`](../TODO.md#task-asset-liveness-dust).

### P10 — Normal strategy and economic manipulation

Check85% centre-to-boundary displacement, physical/reference same-side corroboration,600s sampled persistence,300s maximum gap,240s source polling,12h hard minimum and durable60-300s jitter. Include boundary/reset/reorg/outage/pending-geometry/first-LP cases.

Verify post-withdrawal depth, known directional fees versus additional1% loss, aggregate caps, deterministic routing/sizing and complete fill. Assess outside-trader and authorized-key extraction scenarios; access control/jitter are not manipulation-immunity proofs.

Keep ordinary compound's extra wait in keeper software as chosen, with a separate interval and independent hourly harvest. Preserve explicit operator geometry exceptions and ensure no ordinary path silently selects emergency bypasses.

Owning Todo: [`rebalance-confirmation-buffer`](../TODO.md#task-rebalance-confirmation-buffer), [`security-strategy`](../TODO.md#task-security-strategy), [`security-keeper-manipulation`](../TODO.md#task-security-keeper-manipulation), [`security-external-manipulation`](../TODO.md#task-security-external-manipulation), [`passive-inventory`](../TODO.md#task-passive-inventory), [`governed-loss-limits`](../TODO.md#task-governed-loss-limits).

### P11 — Authorities and every manual management action

Select actual governance wallet/signature policy, guardian, limited keeper, mint recipient and VRF owner/funder. Verify revocation/rotation, bootstrap removal and contract-wallet envelopes if selected; direct-EOA preparation does not qualify a Safe.

For every operator write, verify caller, units/decimals, actual input source, tick orientation, raw minima, hashes/nonces/expiry and when inputs must be reread. Exercise pause/unpause/park/resume/move/residual-close/consolidate/force through changing markets and stale reviews.

Emergency financial bypasses stay deliberate, paused-governance-only and separate from daily automation. Structural authorization/custody/accounting remains mandatory. Document reverse/restart actions where available and reconstruction boundaries where irreversible. No governance key belongs on the keeper host.

Owning Todo: [`authorities-prices`](../TODO.md#task-authorities-prices), [`security-governance`](../TODO.md#task-security-governance), [`operation-review`](../TODO.md#task-operation-review), [`callable-reference`](../TODO.md#task-callable-reference), [`operator-stop-controls`](../TODO.md#task-operator-stop-controls), [`manual-emergency-rebalance`](../TODO.md#task-manual-emergency-rebalance), [`manual-reference-swap-proof`](../TODO.md#task-manual-reference-swap-proof), [`manual-recovery-gas-rehearsal`](../TODO.md#task-manual-recovery-gas-rehearsal), [`manual-lp-diagnostics`](../TODO.md#task-manual-lp-diagnostics), [`parked-emergency-preparation`](../TODO.md#task-parked-emergency-preparation), [`operator-management-preparation`](../TODO.md#task-operator-management-preparation).

### P12 — Terminal collective holder return

Verify both-leg closure/fee classification, designated compound, exact ETH/ZZZ principal shares and governance-only bounded direct payouts over1000 NFTs: repeated holders, dormant NFTs, varied tiers/rarities/LP and transfer ordering between batches.

Check batch progress, cold gas, rejecting ETH recipients, frozen tokens, retries and final-unit drain, with earned rewards/buyback reserves separate. Holders need no action normally; exceptional owner-controlled fallback retains backing and cannot invent an arbitrary operator recipient.

NFT transfers/future royalties/old rewards survive; LP earnings, principal reopening and post-exit canonical import do not. Rehearse destructive operations only in isolation or a separately authorized rehearsal collection, never as a final-collection launch smoke test.

Owning Todo: [`custody-composition`](../TODO.md#task-custody-composition), [`native-custody-recovery`](../TODO.md#task-native-custody-recovery), [`migration-framework`](../TODO.md#task-migration-framework), [`destination-slots`](../TODO.md#task-destination-slots).

### P13 — Latest complete canonical cutover and abort

Rehearse the actual latest F6/V10 FULL coordinator: freeze, closed physical legs, export, target prefund/import, exact funding, unique source retirement/target activation and fully funded abort restoration. Companion/body equivalence alone is insufficient.

Preserve full-width IDs, original mint-recipient/stage counts, ownership, inventory, shares, LP raw phase/pending and every royalty class/cutoff/history/backing category. Cover incomplete/duplicate imports, wrong pins, faults and escrow-contract compatibility.

No physical old-slot copy, payload relabelling, SeaDrop transport rotation, live-residual omission, post-exit successor or post-halt recovery is assumed. If the feature is not launch-qualified, state that explicitly without pretending disabled operation removes bound-code audit obligations.

Owning Todo: [`security-chain-recovery`](../TODO.md#task-security-chain-recovery), [`holder-preflight`](../TODO.md#task-holder-preflight).

### P14 — Actual OpenSea primary sale

Confirm actual Robinhood custom-drop onboarding and pinned SeaDrop singleton/helper compatibility before irreversible binding. Establish payer/platform-fee terms: buyer gross0.05ETH, recipient net after platform fee, gas separate.

Verify initial20 free team/500 same-price allowlist(one per listed address)/480 publicFCFS, proofs, variable future counts/windows, lifetime original-recipient limits, unused allowlist rollover and reserved unused team slots.

Exercise stage/time/payment rollback and mirror the final OpenSea end to the royalty window. ERC2981 requests5% royalties; actual marketplace payment enforcement is external, not a guarantee supplied by ERC721 or ERC2981.

Owning Todo: [`opensea-mint`](../TODO.md#task-opensea-mint).

### P15 — Live randomness and pending requests

Qualify supported coordinator/subscription/key settings, consumer/funding, request and callback gas, confirmations and proof delivery. A deployment address alone is not a supported operating service.

Check delayed/duplicate/out-of-order/failed/unanswered requests, mint-only pause, callback recovery and provider-rotation constraints. Every mint receives one remaining prepared design; no administrator rarity choice or reroll.

Unanswered draws can block provider rotation and canonical replacement. Establish operational response and costs before first mint; do not silently revive a rejected randomness bypass.

Owning Todo: [`fair-draw`](../TODO.md#task-fair-draw), [`nft-lifecycle`](../TODO.md#task-nft-lifecycle).

### P16 — Artwork, metadata and marketplace delivery

Authenticate the1,000-entry mint inventory, its542 distinct selected base looks and all2,784 supported renderer SVG states (58palettes×4patterns×3rarities×4evolutions), immutable URI/root/content and renderer before sealing. These are different counts; nonempty content root does not prove content exists or is correct.

Qualify cold tokenURI at final root/state/provider and actual marketplace retrieval/cache/ERC4906 behavior through reveal, activation, growth, value changes, unavailable prices, parking, movement and terminal LP-exited state.

LP-exited remains distinct from Dormant, with royalty rights preserved. Website image/sound waits for confirmed actual LP. No dormant-card royalty deadline. Prior controlled metadata2 reads do not qualify latest full construction or final content hosting.

Owning Todo: [`metadata-ops`](../TODO.md#task-metadata-ops).

### P17 — API security and complete portfolio reads

The [current full-normal claim evidence](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/full-claim-admission-20261120/REVIEW.md)
adds real F6/26-pin admission on32 activated NFTs/65 royalty currencies and a
first-success planning fix for an actual1,024-read exhaustion. Actual payout,
remaining claims and all guards stay verified. This is finite claim evidence;
full1,000-active-NFT normal workloads, HTTP/provider/complete-fee and matching
consumer/operating acceptance remain open. Prior LPQ03's P16 reference was wrong.

Match current F6/profile/runtime/canonical manifests, both physical legs, owner and
funded rights at canonical state. [Compact wallet qualification](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/compact-wallet-20261121/REVIEW.md)
reduces the previous190 core wallet reads to64 for1,000 NFTs/three currencies;
including16 card/history calls gives80. Sixteen NFTs/66 fully priced descriptors
complete17 four-currency pages under existing1,024-read and response bounds.
Keep full replay/global reconciliation and complete two-dimensional coverage.
The ideal admission bound is68s for80 reads; actual fixed-clock producer handler
work is83.621s, excluding real network, isolated-worker startup and card costs.
Neither number qualifies deployed freshness. The1,000-by66 cross-product still
cannot fit120s; earnings is unavailable without losing complete holdings/totals.
The optional explicit `wallet_read_batch:1`/wallet profile2 now separates
ownership/LP pages from four-currency whole-wallet earnings. The maximum core
cross-product falls from1071 to80 GETs for1000NFTs/65–66descriptors. A pinned
constructor-only STATICCALL reader retains live per-NFT reconciliation and fixed
internal gas bounds. Complete provider/F6/V10/lineage/freshness/HTTP acceptance
remains open; lower request counts alone do not close it.
Rebuild/review/re-pin matching checkpoint semantic sources before separate
backend/worker/Nginx/website adoption. Legacy wires and all limits remain.

Verify owner/chain/NFT/block/config/digest/count and contiguous complete assembly within reviewed freshness budgets or explicit incomplete/unavailable output. Preserve1024call/1MiB bounds and ingress rates. Final page alone is not a whole wallet.

Qualify proxy/origin/TLS/firewall boundaries, malformed/oversized/slow input, tenant/concurrent isolation, disconnects, worker cleanup and bounded provider failure. Do not expose Python/RPC/Anvil or replace financial reads with stale demo caches.

Owning Todo: [`read-api`](../TODO.md#task-read-api), [`api-client-admission`](../TODO.md#task-api-client-admission), [`host-services`](../TODO.md#task-host-services), [`portfolio`](../TODO.md#task-portfolio).

Current27November qualification found and corrected the250k valid-LP-view
refusal by approved500k reads/three-NFT helper groups within24M. The affected
1000-NFT/66-descriptor model remains under each request limit, but17 independent
pages take121.438s before a real full-wallet HTTP journey. The80-GET count alone
does not close P17. Current request-local raw/digest reuse completes the actual
32-NFT/66-descriptor wallet plus eight cards in83.708s/36GETs with final
independent accounting and freshness checks. Full normal1000-NFT/lineage/provider
acceptance remains. CWR09 now binds both card reads to the same exact anchor;
the separate actual moving-head case completes84.262s with final age114.514s,
only5.486s below120. Treat this as finite local evidence, not robust hosting. This finite local pass does not authorize rollout. Reuse the actual39-instance/32-NFT F6 fixture and current
source-bound evidence; the older1000-NFT substitute-access fixture cannot supply
normal deployment/history admission. Actual maximum-state/lineage/provider and
120s complete-consumer acceptance remain explicit work.

The original33-GET/117.628-second timeout and incomplete output capture remain
failed stages in the current review. The affected32-NFT composition now passes;
next qualify maximum normalF6/lineage/provider and sustained moving-chain
operation without wider budgets. The new fixed-block card capability addresses
the specific two-request anchor race; install matching components only after review. A newly source-bound checkpoint separately passes
3,098logical/6,194POST/4.86628s with exact rights. These finite checks do not
approve deployment, consumer adoption or the whole P17 package.

### P18 — History, checkpoints and durable data

Reconcile NFT/wallet/collection24h and all-time earnings: individual LP80% plus collective10% plus royalties at today's reviewed prices, excluding principal/claims/conversions/imports as new income. Preserve exact raw amounts and the full86400s raw suffix.

Qualify actual deployment-to-head ingestion, canonical lineage, reorg rollback, missing logs/prices and SQLite/WAL/archive/storage limits. Demonstrate complete restore, rotation and source-codec evolution without truncating the historical window.

service.py changed semantic checkpoint identity: preserve old artifacts/reviews/raw DB/WAL, explicitly rebuild/review/re-pin for matching consumer adoption. Do not relabel old checkpoint formats or infer totals from incomplete history.

Owning Todo: [`financial-history`](../TODO.md#task-financial-history), [`live-history-ui`](../TODO.md#task-live-history-ui).

### P19 — Production user submission and website adoption

Choose a separately reviewed production submission route or explicitly accepted external client for activation/growth/claims. OpenSea addresses mint only. Source10/schema5 reads/unsigned reviews never construct the shared signer; that signer stays Anvil-only. Do not silently extend it.

Qualify MetaMask/Rabby permissions, account/network changes, exact approvals, rejection, stale review, approval-to-Entry interruption, submission/receipt/replacement/nonce gaps, reorg and refresh/cross-tab recovery without duplicate sends.

Popldemo stays simulation; served poplint current3 is not fresh F6/source10. Missing configuration never becomes demo financial data. Update only the affected NFT after confirmed LP. Dedicated10/25/100 load tests remain deferred and declined sale-rights disclosure is not a new launch blocker.

Owning Todo: [`wallet`](../TODO.md#task-wallet), [`portfolio`](../TODO.md#task-portfolio), [`transaction-ui`](../TODO.md#task-transaction-ui), [`unsigned-actions`](../TODO.md#task-unsigned-actions), [`preview`](../TODO.md#task-preview), [`purchase-rights`](../TODO.md#task-purchase-rights).

### P20 — Actual full normal keeper scheduling

Current finite evidence and its original failures are assessed in the
[current review](../reports/CURRENT_REVIEW.md#keeper-recovery-and-diagnostic-data).
The following operating acceptance remains separate.

Rehearse the actual normal daemon/Cast/provider/key path in isolation: pending-first recovery, observation deadlines, independent job retry delays and correct per-pool scheduling. Start with disposable keys and an owned isolated chain; production keys/providers need separate authorization. Inert recovery-only dispatcher results do not prove the normal loop.

Verify hourly harvest and authenticated internal-harvest coalescing, compound wait/interval, conversion/burn fairness, no-op handling, UTC fee-day/deadline budgets, mode/range changes and multiple historical buckets over representative multi-day transitions.

Confirm all failure diagnostics, role revocation and funding behavior; no ordinary fallback to force. Running release/config/runtime identity needs observation, not merely a hash of a local source checkout.

Owning Todo: [`keeper-guardrails`](../TODO.md#task-keeper-guardrails), [`keeper-recovery`](../TODO.md#task-keeper-recovery), [`operation-review`](../TODO.md#task-operation-review).

### P21 — Host, interruption, restore and alerts

Current finite evidence and its original failures are assessed in the
[current review](../reports/CURRENT_REVIEW.md#keeper-recovery-and-diagnostic-data).
The following operating acceptance remains separate.

Qualify least-privilege host/service/TLS/secret setup, actual disk/WAL/fsync/locks, single-writer fencing and off-host storage. Interrupt at durable intent/save/sign/send/hash/receipt boundaries, including hashless uncertainty, RPC stalls/refusal, disk full, permission failure, corrupt state and restart storms.

Restore selected configuration/key/journal/DB/checkpoint on another host without two active signers, guessed resends or incorrect nonce/spend. Define RPO/RTO, observation/soak acceptance and operator responsibility rather than inventing arbitrary durations.

Prove alert delivery for stale heads/observations/harvest, low gas, blocked routes/budgets, worker quarantine, missing backups and storage exhaustion. Current services/journals and the user-paused desktop heartbeat remain untouched without separate authorization.

Owning Todo: [`host-services`](../TODO.md#task-host-services), [`keeper-recovery`](../TODO.md#task-keeper-recovery), [`security-integration`](../TODO.md#task-security-integration).

### P22 — Fresh construction, deployed readback and seal

The [current controlled F6 rehearsal](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/f6-construction-20261120/REVIEW.md) completes25CREATE+19bindings/39instances using real Access/Registry,112binding/state plus172default reads and a distinct-role35probe fixture. Its132preflights/260nonce reads/44receipt headers are independently reconciled. Before public deployment, still freeze actual release arguments/root/fees and verify real dependencies, direct-EOA nonce assumptions and getter-discovered children; controlled constructor doubles and local addresses are not adopted.

After separately authorized deployment, verify actual receipts, runtime/immutables, all children/parents/reciprocal bindings, addresses/roles and no unexpected grants. Failed/inserted/replaced/delegated-wallet steps invalidate simple sequence assumptions; reconcile rather than guess resume.

Before seal, verify fixedZZZ everywhere, LP converter, selected SeaDrop helper/singleton, artwork root, initial VRF, policy/gas/currency reads, standalone/importer state and viable mint schedule. Mint end may deliberately remain unset until ready; configuring it before seal is not required, and premature expiry can be irreversible. Generic seal does NOT prove complete release readiness. Wrong immutables/root, expired sale end, permanent reservations and retirement may require reconstruction.

Owning Todo: [`deployment-initcode`](../TODO.md#task-deployment-initcode), [`native-production-preflight`](../TODO.md#task-native-production-preflight), [`post-seal-configuration`](../TODO.md#task-post-seal-configuration).

### P23 — Independent approval, staged launch and longevity

Independently audit the frozen code AND enabled configuration/dependencies, full accounting/LP/authority/emergency/canonical/holder-return composition and accepted trust. Remediate confirmed issues and refresh affected proof; record unresolved material risks and named decisions. Internal consolidation is not independent security approval.

Use local checks for mechanics, current mainnet fork for real market behavior and testnet for supported wallet/provider/service integrations. Label unavailable/mocked dependencies; none substitutes for actual final platform/provider acceptance. A separate mainnet rehearsal cannot clear/reset a final immutable collection.

Record separate authorization and readiness for deployment, sealing and public opening. Keep mint/deposits closed until their gates pass; authorize bounded non-destructive smoke checks explicitly. Set launch monitoring/stop/restart and dependency-change reviews; future currency/venue/feature expansion needs its own acceptance before enabling.

Owning Todo: [`audit-release`](../TODO.md#task-audit-release), [`mainnet-fork`](../TODO.md#task-mainnet-fork), [`testnet-rehearsal`](../TODO.md#task-testnet-rehearsal), [`mainnet-rehearsal-retirement`](../TODO.md#task-mainnet-rehearsal-retirement), [`capacity-campaign`](../TODO.md#task-capacity-campaign), [`historical-findings`](../TODO.md#task-historical-findings), [`economic-rights-audit`](../TODO.md#task-economic-rights-audit), [`local-browser-stack`](../TODO.md#task-local-browser-stack), [`local-dollar-rehearsal`](../TODO.md#task-local-dollar-rehearsal).

## Verification and completion discipline

For each package, inspect current code and exact prior evidence first. Classify
requirements as already proved at unchanged source, missing proof, confirmed
defect, unresolved decision/input, accepted policy, dependency limit or retired
requirement. Reuse valid unchanged evidence; run missing cases or cases affected
by changed implementation/dependencies. An unchanged test file can still require
rechecking if its production dependency changed.

Use independent accounting models, nonvacuous conservation/rollback assertions,
targeted reachable state sequences and invariants/fuzzing for numeric domains.
Keep estimated, padded, trace and receipt gas distinct. Preserve failures and
skips; generic reverts do not identify an exact financial blocker. No finite
campaign proves every possible adversarial market or arbitrary token/receiver.

Complete a package only for its supported enabled profile, with exact evidence
and operator inputs/limits/restart/irreversible boundaries updated in the owning
guide and central Todo. Revalidate external facts near launch even if PoPL source
did not change. Future route/currency/feature expansion needs corresponding
acceptance before enabling it. The [release record](RELEASE_CHECKLIST.md) remains
NOT APPROVED until actual named decisions exist.

Current primary references: [Solidity known bugs](https://docs.soliditylang.org/en/latest/bugs.html),
[Robinhood differences](https://docs.robinhood.com/chain/differences-from-ethereum/),
[fees](https://docs.robinhood.com/chain/gas-and-fees/),
[finality](https://docs.robinhood.com/chain/transaction-finality/),
[Arbitrum gas estimation](https://docs.arbitrum.io/arbitrum-essentials/how-to-estimate-gas),
[Chainlink feed selection](https://docs.chain.link/data-feeds/selecting-data-feeds).
They identify qualification obligations; they do not attest this deployment's
actual network state, provider plan or source applicability.
