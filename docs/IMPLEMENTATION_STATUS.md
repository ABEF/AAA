# Implemented capability catalog

This page records implemented mechanisms and their technical guides. The sole
[current project review](../reports/CURRENT_REVIEW.md) owns assessment, finite
evidence and remaining qualification; [findings](AUDIT_FINDINGS.md) owns issues.
Implementation does not establish an installed service or approved release.
Production remains NOT APPROVED.

## Current profile

Fresh **accounting7 / LP-allocation1 / portfolio2 / maintenance3 / confirmation3 / compound4 /
custody5 / emergency2 / LP routing3 / execution-price1**, with pricing2, Entry routing3, reviewed
policy2, direct governance2 and fee intake1. The eight-word Position remains;
fresh royalty4/canonicalV10 carries sale end/capacity and exact-unit ticket rights,
and rejects older peers.
Tuple shape does not imply runtime compatibility.
[Profile](POSITION_V7.md), [portfolio controls](OPERATOR_MANUAL.md#portfolio-management-controls).
Production inventory is schema17/mint2 with explicit residual-reinvest1/raw-exit1 bindings; schema16 remains historical. It retains20 callable helper pins plus2 inert Factory code-data children; the exact-unit allocator is internal code. Factory storage2 authenticates exact fresh payload6 creation bytes. Allocation2 retains exact round coefficients; F6 packs private status/Book storage with full-width spill. Settlement4/event/canonical outputs remain unchanged. Historical payload3/4/5 retain their exact old code. Historical schema9/custody4 retains direct Entry3 and20helpers; schema8 keeps
its routed Entry2 and21-helper profile; no conversion child remains on fresh Entry. Historical accounting5/4 and inventory7/6
profiles remain explicit and are never silently rewritten.

Exact-unit LP integration retains authenticated Vault/Membership synchronization, whole current-owner claims and same-NFT conversion. CanonicalV10 retains the exact V9 LP domain; historical6/V8 and checkpoint1 are not reinterpreted. See [allocation](EXACT_LP_ALLOCATION.md) and [checkpoints](EARNINGS_CHECKPOINTS.md).

## Smart contracts

| Capability | Implemented behavior | Reference |
| --- | --- | --- |
| Reference-as-swap venue | Explicit execution-price1/LP3 captures original bounds and verifies own-swap full state before settlement plus later live checks; no new helper or financial-limit change. Same-core principal destination remains separate. | [Design](REFERENCE_SWAP_EXECUTION.md), [evidence](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/reference-execution-20261111/VERIFICATION.md) |
| NFT identity | ERC-721, fixed artwork draw, exact1,000 rarity quotas; actual VRF provider still unqualified. | [Metadata](NFT_METADATA.md) |
| Contributions | ETH or the fixed ZZZ; future-governed minima(default$100 activation/$5 growth); checkpoint incumbents, use entrant-only budgets, verify marginal main LP, then issue shares from aggregate NAV. Residuals and rebalance centre/clock remain unchanged. | [Entry](ACTIVATION_ENTRY.md), [pricing](PRICE_SECURITY.md) |
| Shared LP portfolio | Single main by default, optional one residual in the same pool; both NFTs remain Vault-owned. Aggregate raw principal/valuation includes both actual ranges, not a sum of their liquidity units. | [Portfolio profile](POSITION_V7.md) |
| Ordinary replacement | Both single/hybrid reject inactive stored-tick quotes before ranking and verify the new main is physically active before/after callbacks; hybrid requires its configured6000–9999bps main floor(default60%) and complementary residual ceiling(default40%) at captured post-cost valuation. Natural placement meeting that floor needs no swap. Otherwise bounded approved-route sizing targets a rounding-safe floor. Failed sizing/mint/close reverts atomically. | [Execution policy](LP_EXECUTION_POLICY.md) |
| Residual geometry | Default half of the corresponding main side, a governed positive tick-spacing gap(default1) beyond spot. Width governed1–10000bps of that side. At most one residual; mixed/filled inventory remains valued until whole adjustment. | [Range controls](RANGE_POLICY_UPDATES.md) |
| Same-main residual consolidation | Paused governance `Migration.consolidateResidual(request,forced)`: harvest/close only residual or recover prior attributed idle, balance and increase same main, atomically apply modeOFF. Shares/centre/rebalance clock preserved; compound clock updated; designated compound/rewards/buyback separate. Guarded routing now filters active candidates for preserved bounds, with financial guards and no keeper timing; force is explicit. | [Inputs/evidence](OPERATOR_MANUAL.md#same-main-residual-consolidation), [review](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/residual-main-consolidation-20261106/REVIEW.md) |
| Residual-only recovery | New paused governance-only Migration.closeResidual(ParkingRequest), explicit RESIDUAL_EXIT_VERSION1 across Migration/Vault/Manager/position child. Harvest both then burn only registered residual; exact raw proceeds to same bucket idle. Main/shares/clocks/configuration preserved; no swap/payout/compound release. | [Management controls](OPERATOR_MANUAL.md#portfolio-management-controls) |
| Enable/disable | Manual reviewed desired mode; enabling permits rather than forces a residual. Disabling retains both actual legs and NFT reward membership until a guarded single-position merge succeeds; no immediate deactivation or trade. | [Operator](OPERATOR_MANUAL.md) |
| Ordinary eligibility | 85% actual centre-to-edge human ZZZ-price distance; physical and independent reference on the same side.600-second sampled window/maxgap300, source240-second checks, fresh60–300-second service jitter, initial hard12hours. Manual geometry changes are a distinct cooldown-gated exception. | [Confirmation](LP_EXECUTION_POLICY.md#requested-rebalance-confirmation-buffer) |
| Financial checks | Dual USD sources with3% agreement; captured default3% contribution/1% conversion/3% maintenance limits, governance ceilings10%, gas separate. Additional-loss default1% after known directional fees remains separate. | [Price security](PRICE_SECURITY.md), [execution quality](EXECUTION_QUALITY.md) |
| Exact-unit LP integration | Actual Rewards uses constant-work root credit, ten-level whole claims/views, both-book old-weight synchronization and raw pending/high/low LP records(original V9 domain, current V10 wrapper). Current-owner claims and same-NFT conversion conserve every allocated unit. | [Rules/evidence](EXACT_LP_ALLOCATION.md) |
| LP revenue | Combined actual fees from both legs allocated once per asset at80/10/5/5. Individual shares/equal active collective; no dormant dilution. Independent claims, compound and buyback reserves. | [Economics](ECONOMICS.md) |
| Royalties | Fresh payload6/allocation2 round coefficients with at-most10-step enrollment lookup; settlement4 original-currency claims; ×1/×2/×3 weights with GCD-normalized exact-unit allocation and a saved rotating remainder cursor. Every allocated raw unit belongs to an NFT; no allocated rounding remainder remains after all eligible claims. Recovery2 assigns reviewed unallocated units at current active weights. Initial/prefund/zero-cohort and token-failure limits remain. No royalty converter; current owners inherit unpaid rights; ERC2981 requests5%, without universal payment enforcement. | [Exact allocation](EXACT_ROYALTY_ALLOCATION.md), [current audit](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/last24h-audit-20261105/REVIEW.md) |
| Compounding | Existing range, both-leg NAV and separate interval after last compound/rebalance; keeper waits for in-range main below the adjustment threshold/no pending geometry. Entrants cannot spend incumbent idle/compound. | [Coordination](KEEPER_COORDINATION.md) |
| Recovery | Governed same-pair move/resume can create a residual under destination mode ON, without ordinary keeper timing; financial/custody guards remain. Both-leg same-pair movement, raw paused parking and collective ETH+ZZZ holder return. Custody5 allocation/distribution is governance-only; holder LP/royalty/fallback claims remain. Pending compound follows shares; rewards/buyback backing remain separate. Pre-exit canonical export requires every residual closed. | [Parking](CUSTODY_PARKING.md), [holder return](HOLDER_COLLECTIVE_EXIT.md), [canonical](CANONICAL_HANDOFF.md) |
| Emergency | Paused governance-only reviewed manifest; both-leg liquidity-sensitive fingerprint. Financial bypass is explicit and can lose nearly all principal; structural rights/ownership/settlement remain. | [Emergency](EMERGENCY_REBALANCE.md) |

## Backend and operations

Confirmed reads use an immutable validated RPC snapshot and metered work.
Strict new-work checks do not discard a valid saved pending-recovery intent.
[Frozen packages](FROZEN_REVIEW_BUNDLE.md) use schema4; earlier1/2/3 admission,
instructions and ZIP semantics remain exact and are not operating profiles.

| Capability | Implemented source boundary |
| --- | --- |
| Confirmed reads | Fresh7 independently proves per-leg principal from captured sqrt/ticks/PosM L, containment, exact stable and L-sensitive fingerprints; no aggregate-only admission. Explicit accounting7 graph/runtime/version checks; both physical IDs/owners/keys/ticks/liquidity and aggregate principal authenticated at one confirmed block. Desired-disabled residuals remain included. Physical reads preserve owners/raw funded claims during price outages; valuations remain unavailable. No maintenance readiness inferred. Old profiles remain separate. |
| Claim planning | Opt-in /v1/claims/plan accepts up to32 exact selections, simulates bounded subsets under existing12M/fee/work limits and returns only one freshly verified draft. Every unresolved entry remains explicit; no signing, queue or automatic skip. [Procedure](CLAIM_PLANNING.md). |
| Factory deployment | Fixed creation payload moves from storage slots into exactly2 authenticated inert data children. Payload/royalty rules unchanged; current source-bound schema17 and actual returned-runtime gates required; schema16 evidence remains historical. [Storage format](FACTORY_CODE_STORAGE.md). |
| Unsigned activation/growth | Fresh graph including actual typed-executor verification, control and portfolio review binding; exact Manager→typed child→PosM trace and entrant marginal main liquidity; no public signing added. |
| Keeper | Fresh3 threshold/window semantics, durable jitter/reset/pending-first recovery, in-range compound wait, authenticated harvest coalescing and operation diagnostics. Raw checks during cooldown; paid observation enrollment near hard eligibility avoids waste. Late gas-enveloped full LP simulation and final policy/nonce/funding/head/deadline/day-budget checks preserve original intent before signing. |
| Inventory | Schema17/mint2/custody5/reinvest1 validates20helpers plus2 immutable REVERT-prefixed Factory data children, both physical legs, primary mint books and exact-unit royalty4; reporting5/canonicalV10 are explicit. Schema10 converting royalties and schemas9/8/7/6 retain explicit historical inspection. Example is unqualified. |
| Manual operation preparation | [Typed preparation](MANUAL_LP_PREPARATION.md) covers park/resume/residual-only close, all collective-exit steps, schema1 Active B/C/D and explicit schema2 Parked D. Direct empty-code governance only; exact custody/control proof, original caller floors/expiry and two exact simulations. Parked rejects Active-only bits1/16 and discloses selected2/4/8 bypasses; USD still required by4. [Manual diagnostics](MANUAL_LP_PREPARATION.md#manual-lp-failure-diagnostics) expose stage/known local cause, bounded RPC/work metadata and uncertain output; opaque failures stay unknown. Successful manual artifacts remain exact; new management source commitments include the changed helper hash. No signer, queue, fallback or unpause. Distribution count/gas limits stay separate. Contract-wallet envelopes and actual provider/operator/target-gas qualification remain open. [Parked evidence](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/parked-recovery-preparation-20261115/REVIEW.md); [earlier seven actions](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/operator-management-20261109/REVIEW.md). |
| Complete-wallet read profile2 | Optional `wallet_read_batch:1` separates16-ID ownership/LP pages from full-wallet/four-currency earnings;1000NFTs/65–66descriptors need80 core GETs versus1071. Constructor-only pinned STATICCALL reads retain per-NFT reconciliation, same-request byte bounds and full86400-second history. The same opt-in now scopes NFT/card earnings reads and reuses actual-code digests only after exact canonical code authentication; every expected pin remains checked and metadata shares existing cache limits. Approved three-NFT/500k-LP grouping keeps the24M total and all transaction/API limits; actual-F6 and maximum-wallet evidence retain distinct scopes. Profile1/defaults unchanged; current provider/F6/lineage/site qualification remains open. [Operator](OPERATOR_MANUAL.md#optional-profile2-separate-complete-wallet-earnings). |
| Fixed-block card history | `fixed_block_nft_view_profile:1` is advertised only for exact7 with ownership+earnings history. NFT detail and history bind the same captured number/hash while later blocks or Indexer updates arrive. Original latest routes and fresh action preparation remain; no latest fallback, relaxed120s, partial accounting or signing. Matching backend/worker/proxy/consumer and NEW reviewed checkpoint require separate adoption. [Read inputs](FRONTEND_API.md#fixed-block-nft-detail-and-earnings), [operator](OPERATOR_MANUAL.md#fixed-block-card-history). |
| Earnings | Separate LP/collective/royalties, current-price USD and claimable versus earned/claimed. Fresh7 replays exact whole-unit trees from complete raw history. Checkpoint1 remains6-only; explicit checkpoint2 preserves raw exact trees/pending/phase/direct rights and a complete raw24-hour suffix. Checkpoint3 adds authenticated lineage cursors; a separate offline importer extends compatible reviewed exact2/shorter3 prefixes with unchanged strict semantics and full24h. Offline history recovery adds all-row SQLite snapshots, source-pinned manifest verification and independent-file restore; actual archive/workload/operating qualification remain open. Claims/conversions/imports are not income; same-currency first allocation is counted once; exact-unit cursor/cohort state must match replay and checkpoints. Missing data stays unavailable. |

Fresh read/keeper configurations explicitly select custody5 and exact runtimes.
Keeper principal_distribution is disabled/rejected on5; governance submits
terminal batches. Owner earned-reward claims remain available. See
[permissions](ACCESS_PERMISSIONS.md), [API](FRONTEND_API.md),
[unsigned preparation](ACTIVATION_PREPARATION.md) and
[preflight](PRODUCTION_PREFLIGHT.md).

## Frontend boundary

[Source10](SOURCE10_WEBSITE_PROFILE.md) explicitly supports schema5/mint2/V10
with33 browser runtime pins. [Source9](SOURCE9_WEBSITE_PROFILE.md) supports
schema4/accounting7/LP1/custody5/Entry3/royalty4/V9, original-currency royalties,
pending LP ZZZ, holder principal returns, governed thresholds and gas-aware
claim plans. Both are unsigned even on Anvil and never construct the shared
signer. Public deployment configurations remain null.

Served current3 poplint and simulated popldemo retain separate original roots
and profiles; neither is upgraded by source publication. Actual configuration,
matching consumer/provider/HTTP/mint/wallet operation and rollout need separate
qualification. [Environment map](SITE_ENVIRONMENTS.md).

## Whole-project workload capability

The [workload map](WORKLOAD_COVERAGE.md) covers all current contract/internal/
service families and187 scenario classes; the map is not dynamic coverage.
Complete fixed-block ownership assembly requires every16-ID page (63 for1,000
IDs), with exact identity/order/digest/count and existing resource limits.
Changes to checkpoint semantic sources require reviewed rebuild/re-pin and
matching adoption; preserve original artifacts. No finite fixture approves all
maximum-state, provider or operating workloads.

## Bounded post-seal flexibility

[ProtocolPolicy1](ADAPTABLE_POLICY.md) governs approved future terms within fixed
bounds; Entry3/review-policy2 binds scoped contribution terms before callbacks.
[Manual controls](OPERATOR_MANUAL.md#future-operating-settings) distinguish a chain
setter from a new runtime/worker/site rollout. Retired architecture and old
journals remain separate. Real providers/authorities/OpenSea, source9 services/
website, storage/operations, economics/gas and independent audit remain open.

Fresh royalty4 retains the [one-hour sale-close activation window](ROYALTY_LAUNCH_WINDOW.md)
and adds [exact-unit allocation](EXACT_ROYALTY_ALLOCATION.md): GCD-normalized rarity
weights, deterministic rotating indivisible units, and no allocated rounding
remainder after all eligible claims. Initial holding, prefunds, zero participants,
unsupported currencies and pathological-token failures remain distinct. Current canonicalV10
rejects older peers; original V9 evidence retains its source scope. Actual OpenSea, gas/workloads and independent approval remain open.
