# Consolidated audit findings and evidence

Reviewed5November2026; consolidation baseline main096fd2b. Production
**NOT APPROVED**. [Sole Todo](../TODO.md) owns work;
[features](IMPLEMENTATION_STATUS.md) record source and
[operator](OPERATOR_MANUAL.md) describes actions.

The [whole-history review](../reports/full-history-reconciliation-20261104/REVIEW.md)
preserves310original finding records/pointers,398pre-ledger unchecked lines,
162task-ledger versions and deleted-guide decisions. It distinguishes historical
fixes, changed architecture, surviving limits and actual open implementation.
Original reports remain immutable; counts are not independent defects/tests.

Earlier reconciliation repaired a stale CI review pointer after two manual-view
edits; its44focused Python checks and unchanged-contract scope remain historical.
The current pointer now selects the new royalty review with the same strict
matching rules. No installed environment changed.
The [provenance map](../reports/full-history-reconciliation-20261104/FINDINGS.json)
records the recurring static issue and materially changed original dispositions.

Checkpoint1 now implements an opt-in first milestone for fresh6/5/1 earnings:
externally pinned immutable state plus bounded raw suffix, exact fractions/dust/
cohorts and complete rolling-day replay. [Current review](../reports/earnings-checkpoints-20261104/REVIEW.md)
records final24new cases and earlier147affected methods without summing stages.
Other full-history consumers, lineage checkpoints, source-codec migration,
unattended rotation, raw archival and real workload/host qualification remain open.

OpenSea primary-mint implementation still needs the exact supported caller/
deployment/payment integration. Current official-source research identifies the
interface, wallet-statistics and nested reentrancy constraints; no guessed mint
authority was added. Actual providers, authorities, routes/VRF, maximum gas,
metadata, operating recovery and independent approval remain under the sole Todo.

The [last24-hour audit](../reports/last24h-audit-20261105/REVIEW.md) replaces
current royalty source conclusions with exact-unit settlement4/reporting5,
schema13/canonicalV8 and original-currency recovery2. Scaled royalties could
leave whole raw units reserved permanently. The approved GCD-normalized rotating
ticket rule assigns every allocated unit; no current royalty conversion remains.
It also repairs checkpoint construction, same-snapshot opening status, sale-end
review/callback binding, source-wire ticket coordinates and cancelled-receiver
recovery. Historical recovery1 conversion/window3 reports retain their original
scope. LP splits/fractions and live-environment boundaries remain unchanged.

## Current conclusions by project layer

| Area | Current mechanism | Remaining boundary / owning tasks |
| --- | --- | --- |
| Principal identity and retired architecture | Only native ETH and fixed ZZZ enter principal; one contribution pool, at most four logical custody buckets. No Power, creator inbox, third input, bridge or external custody-address exit. Converter wrapper support is a separate live purpose. | Actual token/runtime/admission review remains. Issuer/chain migration uses terminal holder return and redeployment. [lp-only-simplification](../TODO.md#task-lp-only-simplification), [shared-custody](../TODO.md#task-shared-custody), [creator-market-controls](../TODO.md#task-creator-market-controls) |
| Governance, sealing and emergency trust | One human governance/operator; restricted keeper and guardian capabilities remain distinct. Governance is immediate. Sealing fixes implementations/parents/token identity; bounded reviewed configuration stays adaptable. Emergency financial bypass is explicit and paused-governance-only. | Key loss, malicious configuration and emergency near-total loss are accepted trust/liveness risks, not removed by hashes or code review. [security-governance](../TODO.md#task-security-governance), [post-seal-configuration](../TODO.md#task-post-seal-configuration), [manual-emergency-rebalance](../TODO.md#task-manual-emergency-rebalance) |
| Direct activation and growth | Entry3 forwards exact ETH/ZZZ input with seven Request fields and no conversion child/routes. Captured owner/policy/prices/caller cap survive token callbacks; entrant-only main deployment and factual marginal LP precede NAV-priced share issuance. | Actual quote/trace/provider and matching site integration remain unqualified. Old tuples/configs/pending records cannot be relabelled. [activation-quotes](../TODO.md#task-activation-quotes), [activation-assets](../TODO.md#task-activation-assets), [reviewed-contribution-policy](../TODO.md#task-reviewed-contribution-policy) |
| Independent prices and actual LP value | Pricing2 uses two reviewed sources with bounded agreement, freshness and captured operation values. Principal includes actual main/residual holdings and attributed idle/compound, not a sum of raw liquidity units or a token-name peg. | Actual independent ETH/ZZZ feed pairs and update services are not qualified. Correlated sources, upstream proxies and market-wide manipulation remain risks. [price-security](../TODO.md#task-price-security), [dual-price-qualification](../TODO.md#task-dual-price-qualification), [creator-zzz-price](../TODO.md#task-creator-zzz-price) |
| Shares and entrant/incumbent separation | Incumbent checkpointing and aggregate net NAV protect existing ownership. Entrants cannot spend existing idle/compound/residual to meet their physical LP floors; main growth does not reset geometry or rebalance clocks. | Rounding, hostile actual tokens, thin-depth execution and maximum-state economics still need frozen-release qualification. [security-share-accounting](../TODO.md#task-security-share-accounting), [custody-composition](../TODO.md#task-custody-composition) |
| One main plus optional one residual | Both physical NFTs remain Vault-owned and one logical share account. Default main>=60%/residual<=40% applies at replacement; mixed/filled/outside residuals remain valued/harvested. Modefalse requests a guarded merge; no third leg. | Allocation is not continuously rebalanced or proven optimal. Residual-only close can deliberately leave large idle. Real geometry/depth/gas economics remain open. [passive-inventory](../TODO.md#task-passive-inventory), [liquidity-placement-idle](../TODO.md#task-liquidity-placement-idle) |
| Atomic routing and execution budgets | Bounded reviewed venues are independent of LP destination. Ordinary candidates use actual post-withdrawal/post-swap stored ticks and filter active-main viability before ranking. At most one balancing swap; gross limits, fee-adjusted additional loss, idle and caller minima remain separate. | No global best-route/feasibility guarantee. Actual venues, depth, token burn ABI, conversion routes and target gas require qualification. No unsafe fallback. [lp-execution-routing](../TODO.md#task-lp-execution-routing), [lp-eth-settlement](../TODO.md#task-lp-eth-settlement), [governed-loss-limits](../TODO.md#task-governed-loss-limits), [creator-input-liquidity](../TODO.md#task-creator-input-liquidity) |
| Normal confirmation, cooldown and jitter | 85% centre-to-boundary distance, physical/reference same-side confirmation,600-second sampled window/maxgap300 and240-second source checks. Hard initial12hours and durable fresh60–300-second jitter remain. Raw checks during cooldown; paid enrollment near eligibility. | Sampling is not uninterrupted price history, MEV protection or proof of attacker unprofitability. Inclusion delays/faults can reset evidence. Manual geometry is a separate guarded exception. [rebalance-confirmation-buffer](../TODO.md#task-rebalance-confirmation-buffer), [security-external-manipulation](../TODO.md#task-security-external-manipulation), [security-keeper-manipulation](../TODO.md#task-security-keeper-manipulation) |
| Compound coordination and hourly harvest | Keeper waits for in-range/below-threshold main and no pending geometry before standalone compounding. Compound has an independent interval; it yields to needed replacement. Authenticated successful internal harvests coalesce the separate hourly clock. | This includes service-only choices, not extra on-chain keeper permissions. Idle-only scheduling/economics and actual operating cadence still need qualification. [keeper-guardrails](../TODO.md#task-keeper-guardrails), [asset-liveness-dust](../TODO.md#task-asset-liveness-dust) |
| Funded80/10/5/5 allocation | Actual harvested receipts from both legs are split once per asset:80% individual,10% equal activated collective,5% compound,5% fixed-ZZZ buyback-burn. Claims do not execute compound or buyback; dormant NFTs do not dilute active membership. | Only received funds back rewards. Actual route/burn compatibility, harvest cost/latency and monetary dust significance remain qualification. [reward-ledgers](../TODO.md#task-reward-ledgers), [security-ownership-rewards](../TODO.md#task-security-ownership-rewards), [lp-eth-settlement](../TODO.md#task-lp-eth-settlement) |
| Rarity royalties and fault isolation | Actual eligible royalty receipts use Commun1/Rare2/Legendary3 independently of principal. Per-currency deferred membership protects earlier funds while healthy activation continues. Separate conversion preserves entitled NFT credits. | ERC2981 requests5%; it cannot force universal marketplace payment. Actual currencies/routes, failures and conversion services remain unqualified. [royalty-eth-settlement](../TODO.md#task-royalty-eth-settlement), [royalty-reporting](../TODO.md#task-royalty-reporting) |
| Ownership, claims and lifetime earnings | Unclaimed rights follow the current NFT owner. Claim/convert/import is not new income. Replay pairs funded fee/credit records, tracks denomination and dust, and values income at today prices with explicit unavailable states. | Authentic complete historical ingestion and bounded lifetime replay/archive scaling remain open. Source fixes do not qualify current site reporting or external datasets. [financial-history](../TODO.md#task-financial-history), [live-history-ui](../TODO.md#task-live-history-ui), [security-ownership-rewards](../TODO.md#task-security-ownership-rewards) |
| Parking, residual close and terminal holder return | Paused closeResidual harvests both and closes only residual into attributed idle. Parking/movement close both. Governance terminal exit apportions actual ETH+ZZZ and designated compound by shares, with bounded isolated owner payouts; old rewards/transfers/future royalties survive. | No external custody recipient/reopening. Broken assets/venues or rejecting recipients can block work; retries and exact backing remain. Paid batches/maximum-holder operating gas still need rehearsal. [native-custody-recovery](../TODO.md#task-native-custody-recovery), [migration-framework](../TODO.md#task-migration-framework), [asset-liveness-dust](../TODO.md#task-asset-liveness-dust) |
| Pre-exit same-chain canonical replacement | Canonical V6 carries exact owner/trait/share/reward backing to one admitted successor, with explicit lifecycle/funding boundaries. All registered residuals must be closed; compatible wire does not authorize old runtimes. | Contract-holder compatibility, exact cutover/funding/gas and governance-approved different successor trust remain. No post-exit, cross-chain or post-halt recovery guarantee. [security-chain-recovery](../TODO.md#task-security-chain-recovery), [holder-preflight](../TODO.md#task-holder-preflight), [destination-slots](../TODO.md#task-destination-slots) |
| Fixed artwork draw and provider liveness | Prepared artwork does not remove the need for fair verifiable assignment. Original requests finalize in order; planned provider rotation drains old draws, without rerolls or administrator-selected traits. | Supported live provider, funding, callback identity/proxy controls, request outage/drain and marketplace reveal remain open. Pool movement is independent of reveal. [fair-draw](../TODO.md#task-fair-draw), [nft-lifecycle](../TODO.md#task-nft-lifecycle) |
| OpenSea primary mint | Direct mint and ERC721/royalty metadata exist; they do not implement the requested OpenSea primary-drop path. Default gross buyer price0.05ETH, platform fee from that gross, network gas separate. Future policy affects future sales only. | Actual OpenSea/chain/drop integration and fee semantics remain unimplemented or unqualified; do not mark done from the demo Mint page or ERC2981. [opensea-mint](../TODO.md#task-opensea-mint) |
| Read/unsigned API boundaries | Pinned same-block helper/runtime/lifecycle/owner/custody checks, exact unsigned preparation, complete holdings and unavailable data semantics remain. Rpc snapshots endpoint config; convenience calls obey wrapper budgets; strict new-work validation preserves pending recovery. | Endpoint honesty, actual tracing, ingress/proxy policy, authentication/resource economics and production deployment remain qualification. Body progress budgets are not hard DNS/header preemption. [read-api](../TODO.md#task-read-api), [unsigned-actions](../TODO.md#task-unsigned-actions), [api-client-admission](../TODO.md#task-api-client-admission), [host-services](../TODO.md#task-host-services), [operation-review](../TODO.md#task-operation-review) |
| Indexer configuration and history resources | The reviewed start anchor is validated/snapshotted before database creation and cannot drift through a borrowed configuration reference. Ownership replay streams transfers with guaranteed cursor closure. Existing database identity/schema remain. | [Current review](../reports/comprehensive-audit-20261104/REVIEW.md):33affected Python passes. This fixes accidental configuration drift and Python materialization, not RPC honesty, replay CPU/storage or complete long-lived ingestion. [host-services](../TODO.md#task-host-services), [financial-history](../TODO.md#task-financial-history) |
| Keeper, journals, health and recovery | Pending-first canonical receipt/nonce/spend recovery, durable observations/jitter/reset acknowledgements, per-job retry isolation, current config/health evidence and bounded work remain. Exact same-key external actions require reconciliation. | Unix ownership/watchdog/backups/restore, real provider delays, off-host monitoring, current source rollout and long-term funding/keys remain open. Heartbeat stays paused. [keeper-recovery](../TODO.md#task-keeper-recovery), [keeper-guardrails](../TODO.md#task-keeper-guardrails), [host-services](../TODO.md#task-host-services) |
| Demo, served integration and fresh consumer | Popldemo remains simulation. Poplint served current3/read-and-prepare is a separate older profile, without reviewed deployment config. Fresh source8/accounting6/Entry3 website consumption remains separate work. | No fake demo fallback, old-journal relabel or public signing. Actual matching wallet/approval/pending/recovery/concurrency and deployment acceptance remain open. [wallet](../TODO.md#task-wallet), [portfolio](../TODO.md#task-portfolio), [transaction-ui](../TODO.md#task-transaction-ui), [live-history-ui](../TODO.md#task-live-history-ui) |
| Artwork, metadata and hosting | Prepared fixed inventory, traits and four evolution mappings exist. Metadata reflects confirmed LP state; display/refresh does not itself prove value or deployment. | Permanent hosting/provider, actual publication hashes and marketplace refresh/caching/operations remain unqualified. [metadata-ops](../TODO.md#task-metadata-ops) |
| Evidence integrity and current source scope | Latest Entry3 normal/static/reference records are source-bound. Failed/empty/skipped stages and prior-body reuse remain explicit. Historical matrices overlap and their counters are never summed into current coverage. Offline reviewHash is provenance, not approval/simulation. | Fresh frozen-release independent audit, compiler advisory refresh, exact deployment arguments and release-specific verification remain required. [local-verification](../TODO.md#task-local-verification), [audit-release](../TODO.md#task-audit-release), [callable-reference](../TODO.md#task-callable-reference), [operation-review](../TODO.md#task-operation-review), [deployment-initcode](../TODO.md#task-deployment-initcode) |
| Release and external qualification | Current source remains undeployed and NOT APPROVED. Feeds, routes, VRF, authorities, OpenSea, current services/site, metadata, target gas/market economics and independent review remain explicit separate gates. | Local tests, old forks or documentation reconciliation do not close those gates. Public transactions/deployment/services require separate authorization. [authorities-prices](../TODO.md#task-authorities-prices), [mainnet-fork](../TODO.md#task-mainnet-fork), [testnet-rehearsal](../TODO.md#task-testnet-rehearsal), [audit-release](../TODO.md#task-audit-release), [native-production-preflight](../TODO.md#task-native-production-preflight) |

## Historical findings corrected by later work

| Earlier statement | Current conclusion | Evidence |
| --- | --- | --- |
| Fresh Entry conversion removal is a proposal | Implemented direct Entry3,7-field Request/then-schema9/20helpers; Vault and earned-reward conversions stay. | [Entry3](../reports/direct-entry-v3-20261103/REVIEW.md) |
| Cooldown observation and internal-harvest coalescing remain missing | Implemented raw cooldown checks/near-eligibility paid enrollment and authenticated successful receipt coalescing. Actual scheduling inclusion remains unqualified. | [Coordination](KEEPER_COORDINATION.md), [portfolio source](../reports/optional-portfolio-20261030/REVIEW.md) |
| Active-main rejection can hide an otherwise valid ordinary route candidate | Candidate activity is now checked before ranking using actual stored post-swap ticks; final mint checks remain. Bounded search is not a global optimum guarantee. | [LP lifecycle](../reports/lp-lifecycle-audit-20261102/REVIEW.md) |
| Two geometry getter comparisons are independent proof | Both forward to the same packed PosM source. They prove coherence under that dependency; they are not independent stored-range sources. | [Correction](../reports/lp-lifecycle-audit-20261102/REVIEW.md) |
| One residual must be left open or closed with all principal | Paused governance can close only the residual into attributed idle; modefalse/merge/park/emergency/terminal exit remain distinct. | [Management](OPERATOR_MANUAL.md#portfolio-management-controls) |
| Old Vault size, helper counts, outside-only triggers or15-minute windows are current | Fresh identity and source-bound evidence below replace those labels. Original results remain valid only at their original source scope. | [Identity table](POSITION_V6.md), [Entry3 verification](../reports/direct-entry-v3-20261103/VERIFICATION.md) |

## Per-NFT exit assurance supplement

The [focused exit review](../reports/holder-exit-assurance-20261103/REVIEW.md)
repairs a missing Manager binding in the old1000-NFT test model, retains the
production residual guard, and adds per-recipient/mixed-wallet checks. Rarity,
evolution and wallet grouping do not change principal shares; previous reward
claims and one NFT's transfer cannot consume another NFT's principal.10distinct
selected successes include1000model NFTs,37mixed wallets, real NFT tier/rarity
composition and actual local v4 both-leg exit. That report binds historical e26fc74; actual
maximum gas, rejecting recipients/dependency liveness and independent review stay open.

## Evidence that can be reused now

Use the [latest manual safeguard record](../reports/manual-safeguard-audit-20261104/VERIFICATION.md)
for current52production/31dependency pins,43normal gates,471static contexts
(13current/458exact referenced reuse),85selected EVM successes across its recorded
stages and47targeted Python methods. Reference37/818/37/13 has0gaps; runtime
headroom remains Vault635/Budget237/Migration39/Balancer360. The
[consolidation verification](../reports/four-report-consolidation-20261104/VERIFICATION.md)
proves unchanged contract/build/dependency pins and separately records new93method
indexer/history execution. These are not added into one full-suite result.



Custody5 restricts terminal allocation/distribution to governance; old custody4
was safe fixed-owner progress but permissionless. Owner reward/royalty claims
remain unchanged. Explicit schema10/read/keeper/lineage versions preserve old
journals, and keeper principal delivery must stay disabled on5. See [permissions](ACCESS_PERMISSIONS.md).
[Prior Entry3 evidence](../reports/direct-entry-v3-20261103/VERIFICATION.md) retains
its custody4 source scope, failures and earlier sizes; unchanged bodies may be
reused explicitly, never relabelled. Frozen-release independent review, compiler
advisory refresh, actual target gas/services and operating approval remain open.

## Provenance and unresolved findings

The [consolidation record](../reports/project-consolidation-20261103/REVIEW.md)
indexes401 baseline report narratives including the mutable index, and preserves
original finding IDs/JSON pointers.351 unchanged prior reading records are reused;
49 later narratives are separately indexed with findings/boundary extracts.
The235 historical groups and75 later groups overlap and are neither310bugs nor
310tests. The [mapping](../reports/project-consolidation-20261103/FINDINGS.json)
retains their original dispositions and separates current topic-level assessment
from source-matched evidence reuse. Unchanged code is not re-audited by copying
an old disposition. [Original reports](../reports/README.md) remain byte-preserved.

Accepted risks include immediate governance, deliberate emergency financial
bypass, dependency/proxy behavior, sampled rather than continuous evidence,
bounded routing/lifetime capacity and absent post-halt recovery. Retired
requirements are superseded, not “successfully implemented.” Actual external
qualification and independent audit remain open.

## Current royalty window and capacity

Settlement4 keeps the final3600-second window and reviewed16→64ERC20 capacity.
Initial pool/prefund/zero-cohort rules remain distinct; exact allocation removes
allocated rounding leftovers, not intentional holding or token transfer faults.
V8 peers and reporting5 readers explicitly authenticate new ticket/cursor/wire
semantics. Actual marketplace/time, maximum target gas, providers, restored
services/history and independent review remain open. No dormant deadline UI.
