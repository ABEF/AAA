# PoPL current project context

The fresh [reference-execution capability](docs/REFERENCE_SWAP_EXECUTION.md)
is explicit execution_price1/LP-routing3. It captures both ETH/ZZZ source bounds
for one transaction, proves the selected actual-core output/full post-state
before settlement, then preserves live source freshness/agreement and final
callback checks. Public Oracle reads stay live; no keeper-selected price or
global cache is added. A reviewed external reference may also execute the swap,
but cannot be the same-core PoPL principal destination. Policy/source changes,
unplanned market movement and nested scope borrowing fail closed. The fixed
existing Math child shares read-only work; no new deployed helper, custody
recipient or authority is added. Accounting7/canonicalV10 and financial limits
remain. Explicit matching consumers/configuration/runtime pins are required;
omission/0 remains historical LP2. Cold full-operation costs15.32M ETH/15.64M ZZZ in the controlled fixture
(18.38M/18.77M with20% headroom), exceeding the unchanged12M default. Qualify
the existing optional activation policy2 and real target-chain gas separately.
See [review](reports/reference-execution-20261111/REVIEW.md) and [verification](reports/reference-execution-20261111/VERIFICATION.md).
Source work changes no deployed contract, site/service, signer, existing
Anvil/journal or user-paused heartbeat.

The [11 November project review](reports/whole-project-review-20261111/REVIEW.md)
removes unreachable third-currency LP scans while preserving all concrete ABIs,
storage and current ETH/fixed-ZZZ rights. Compatibility historical-value reads
return zero; royalty currencies and historical codecs remain separate. New
runtime/source pins require explicit candidate/deployment review, not relabeling
old profiles. The keeper now validates known simulation returns and rechecks
generic-job deadline/day/cost after slow reads before intent/signing. ABI inputs
are exact; indexer contract inventories reject duplicates before database work.
Changing the ABI helper invalidates old source-pinned earnings checkpoints on
consumer adoption: retain them/raw/WAL backups and explicitly rebuild/review.
Website source packaging/new-demo intents are corrected without changing
historical replay, public null configurations or the shared Anvil-only signer.
No live site/service/chain/journal or paused-heartbeat change occurs.
That earlier review retains its original source scope. The fresh explicit
reference-execution capability above addresses swap/reference coupling; service-only
compound policy and actual release qualification remain open. No financial guard
was relaxed.


The optional [pool-spot composite reader](docs/POOL_SPOT_PRICE_SOURCE.md) implements
native-v4 ETH/fixed-ZZZ spot times reviewed ETH/USD. User explicitly chose spot
for placement AND independent valuation; no TWAP is added. Placement already
uses current main geometry/post-swap amounts. Prefer the largest qualifying
external reference, with reviewed depth excluding PoPL LP; TVL/current L alone
does not prove independence or bidirectional depth. Keep two genuinely
independent ZZZ paths; two copies of one pool with different ETH feeds do not
satisfy that review. Public pricing2 observations and economic guards remain; the new execution
capability above requires exact fresh runtimes and explicit LP3 consumers.
The reader is optional/unconfigured, with no source admission, deployment,
service/site/Anvil/journal/signer or paused-heartbeat change. Actual pool, source
ages/depth, second ZZZ reference, ETH publication/liveness and operating
qualification remain open. [Scope](reports/composite-spot-price-20261109/REVIEW.md).


The local [mint2/V10 website consumer](docs/SOURCE10_WEBSITE_PROFILE.md) now implements explicit
website schema5/source10 over accounting7, with33 browser runtime pins and
unsigned holdings, contribution and claim/history reviews. Source9/schema4/V9
retains its original profile and evidence. Direct mint preparation is disabled
for mint2; OpenSea eligibility is unverified. Both public configurations stay
null, source10 never constructs the unchanged shared signer (even on Anvil),
and served current3 poplint/popldemo, services, journals and existing Anvil8902
are unchanged. [Verification](reports/v10-website-20261109/REVIEW.md) is synthetic backend/browser compatibility,
not actual market/provider/VRF/OpenSea/wallet/hosting or independent acceptance.


Current total contribution default is300bps (3%):97% actually deployed LP,
gas separate. User selected TOTAL activation/growth only; no swap/spot/retained-
value, conversion1%, maintenance3%, additional1% or source-agreement3% guard is
changed. [Policy/source evidence](reports/contribution-loss3-20261109/REVIEW.md) binds the new default/runtimes; old
instances/caller200 reviews/journals and earlier market2% evidence remain explicit.
No deployment/service/site/Anvil/signing change or market qualification is implied.

Actual market dependencies remain unqualified. The [read-only follow-up](reports/market-followup-20261109/REVIEW.md)
adds same-anchor feed/control/market evidence at110324511 (9November20:04:50UTC),
an inactive API3 ETH candidate, authenticated offers and external exact-ZZZ market
leads. Chainlink proxies still share one aggregator; stored Pyth ETH is stale and
disagrees above300bps; no two qualified fixedZZZ USD sources are established.
Tiny favorable conversion quotes exist but do not establish meaningful gas/depth
or full-operation acceptance. The selected reverse pool remains exceptionally
shallow; ordinary principal target/venue price bands must also overlap.
Preserve source round/age/agreement and all execution guards. Do not duplicate a
feed, infer independence from names/admin addresses, add synthetic depth, widen
limits or replace USD truth with target-pool spot/USDT peg. API3 needs activation
and separately reviewed round-compatible adaptation if selected; no adapter or
subscription was added. Chainlink no longer expands uptime feeds to new networks;
Robinhood liveness policy remains open. A retained header is not archive-state
availability. Native-v4 principal and optional v3/WETH earned conversion remain
distinct; zero immutable wrapper excludes v3 and fresh7 automation is native-v4
only. No source/configuration/service/site/Anvil/journal/signer or paused-heartbeat
change accompanies this qualification. Earlier reports keep their original scope.

The [SeaDrop integration candidate](reports/opensea-integration-20261109/REVIEW.md) adds fresh mint2/helper1,
canonicalV10 and schema17 with20 callable helpers plus2 inert data children.
Initial sale:20free team,500allowlist at governed price(one per distinct
listed address),480public FCFS. Unused allowlist rolls public; unused team
stays reserved(false). Counts/caps/windows remain reviewed future settings,
not supply resets. Lifetime original-recipient counts survive transfers
and V10 import; do not reconstruct them from owners/balances. Exact pinned
SeaDrop owns gross/fee/net settlement; NFT callbacks receive0ETH and direct
Vault paid mint is disabled when the helper is bound. The metadata renderer
is now predeployed; fresh NFT constructor has3arguments. [Procedure](docs/OPENSEA_MINT.md).
Original source9/schema16/V9 consumers, existing Anvil8902, websites, signer,
journals and paused heartbeat retain their exact old profiles. Backend
read/claim and lineage support is implemented through explicit
`mint_integration_version:2`, pinned helper/SeaDrop roles and V10 authentication;
direct mint preparation returns Use OpenSea. Omission retains mint1/V9.
Matching installed consumers/rollout, actual OpenSea onboarding/fees/payers/VRF/
gas/operation and independent approval remain open. Source publication is not deployment.
Inventory mint phase must match pinned block time; disabled mint-family counts
are exact integer zero. V10 peers retain the same SeaDrop address/runtime;
replacement is not transport rotation. See the [current double-check](reports/today-change-review-20261109/REVIEW.md).


The [actual source9 Entry3 rehearsal](reports/source9-actual-entry-20261109/REVIEW.md)
fixes the fresh7 fixed-ZZZ getter and actual initial/funded trace-epoch decoding.
ETH/ZZZ activation and growth execute through real API/website unsigned reviews
on a new owned fork; exact approvals, marginal LP, unchanged main geometry/clock,
current-owner shares, confirmed metadata and atomic rollback are reconciled.
Unmodified selected-pool depth fails the idle guard; successful cases explicitly
use synthetic external depth and controlled feeds/VRF, not qualified live markets.
Optional activation policy2 requires matching consumer/configuration, confirmed
block gas bounds, full20% headroom and a network-fee ceiling; default1/12M stays.
The shared signer is byte-identical, source9 never constructs it, both public
configurations remain null. Existing8902, journals, popldemo/served current3
poplint, services and the user-paused heartbeat are unchanged. Actual providers,
market depth/routes, independent feeds, VRF/OpenSea, wallet/hosting/operating
acceptance and independent audit remain open.

The [unsigned operator management extension](reports/operator-management-20261109/REVIEW.md)
adds typed park/resume/residual-only close and all four collective-exit steps for
direct empty-code governance EOAs. It auto-reads exact custody/ledger hashes,
preserves explicit floors/expiry and simulates frozen calldata/gas at confirmed
state and a later canonical tip. Distribution uses the explicit reviewed batch
budget and reports a count, never a paid prefix or guaranteed beneficiaries.
Local blockers/uncertain output publication are explicit; no signer, journal,
nonce reservation, queue, force fallback or authority change is added. Existing
Active B/C/D and checkpoint2 retain their original scope; Parked forced-D and
contract-wallet envelopes still require separate manual preparation. Seventy
distinct focused checks plus an overlapping final CLI diagnostic recheck pass
with injected RPC; seven encodings match offline Cast. These are not live wallet,
provider, target-gas or operating acceptance. Solidity/runtime/profile, sites,
services, existing Anvil/journals and paused heartbeat stay unchanged.

[Fee-flow audit](reports/fee-flow-audit-20261107/REVIEW.md) fixes
v3 final-native ETH pricing/wrapper18decimals, fresh7 affordable-prefix conversion
and late deadline/UTC-day checks, strict simulation output and zero-noop earnings
replay. Optional unsigned transaction policy2 adds reviewed operator gas limits
(21k–64M engineering cap, confirmed-block bound, full20%headroom); policy1 remains
12M/schema1. Policy2 requires explicitly matching consumers; no wallet signer,
running configuration, service/site/Anvil/journal or heartbeat is changed.
New normal87/46+2passes; strict532 has15current-context reviews/517unique exact
referenced-source reuse. Converter executable changes only; Rewards metadata
changes and all semantic storage/ABIs plus canonical object bytes are preserved.
F3payload/parts stay byte-identical; source pins are rebound, never old runtimes.
Actual11converter cases,338keeper passes+2explicit skips,28reader methods/fresh
one-method wire producer and56API methods have separate source-scoped evidence;
do not add overlapping stages. Actual routes/providers/gas/consumer rollout and
independent approval remain open. [Verification](reports/fee-flow-audit-20261107/VERIFICATION.md).

Reviewed11November2026. Earlier exact-LP-integration baseline was main64f9bfb; verify actual local/remote
heads before claiming publication. Read AGENTS.md, README.md, the sole TODO.md,
docs/WORK_HANDOFF.md and docs/OPERATOR_MANUAL.md. Production NOT APPROVED.

Both moving-market paths are audited in [current review](reports/moving-market-flows-20261106/REVIEW.md).
Manager alone changes runtime: paused authenticated guarded consolidation uses
active-aware quote selection; existing automatic replacement/growth/compound/
explicit force paths stay distinct. ABI/storage/profile shapes remain; exact
fresh runtime pins and497strict static record replace only changed source scope.
Ordinary keeper LP submission adds one bounded late full call, final service/
lifecycle/nonce/funding checks and LAST head/deadline/UTC-day/retry proof before
durable intent. Calldata/minL/deadline/cost limits are never rewritten. Pending
recovery, journal schema, signer restrictions and all live environments remain.
Local I/O/inclusion can still age a review; no always-executable/MEV guarantee.

[Exact-unit LP integration](docs/POSITION_V7.md) connects fresh accounting7/LP-allocation1/
canonicalV9/schema16/source9 to whole-unit Rewards, authenticated post-write
shares/membership, current-owner claims/conversion and lossless raw-phase handoff.
Constructor-fixed typed RewardsCanonical adds one helper, not an arbitrary
executor, payout recipient or configurable custody address.17modules/19callable
helpers plus2inert Factory data children; old6/V8/F2/checkpoint1 remain explicit.
Earlier [exact-LP integration evidence](reports/exact-lp-integration-20261106/VERIFICATION.md) retains
its original engine/canonical/consumer source scope. Current fee-flow normal,
static and fresh producer evidence is described above; canonical object/body
equivalence supports scoped reuse without relabeling older source fixtures.
Prior V9 runtime headroom was Vault133/Rewards358/CanonicalHandoff32;
current V10 sizes are in the SeaDrop verification record. Exact LP claims
can be materially more expensive;32is a count ceiling, not a gas approval.
Nonempty LP canonical export has2023node rows plus headers/assets/NFT seeds;
all weights precede raw pending/high/low restoration. Never flatten old phase,
reinterpret6/V8 or resume a partially funded/aborted deployment.
Fresh7 raw earnings replay and explicit exact-unit checkpoint2 are implemented;
lifetime archival/workload/recovery qualification remains open. Old checkpoint1 is6-only. Source publication
changes no chain/site/service/journal/signer; heartbeat remains user-paused.

Frozen review exports default to instruction schema3; schema1/2 instructions and
archives remain byte-identical and explicitly historical. This is separate from
contract inventory17/mint2/V10 and does not qualify a release.
[Review package](docs/FROZEN_REVIEW_BUNDLE.md).

## Current architecture and economics

1,000 ERC721 NFTs; fixed600Commun/300Rare/100Legendary draw quotas. Native ETH and
one fixed ZZZ for contributions/LP/buyback/holder return. Default activation100USD,
growth5USD/paid mint0.05ETH gross(team free); future minima/payout policy remain bounded and
governed. Two independent USD sources per priced asset,3% agreement. Default
contribution3%/LP conversion1%/maintenance3%, governed ceilings10%, gas separate;
additional execution loss1% after known directional fees and default5% idle are
different guards. Fixed80/10/5/5 actual LP receipts: owner/equal active collective/
compound/ZZZ buyback-burn. Rarity affects royalties only, not LP shares.

Accounting7/LP-allocation1/custody5/portfolio2/maintenance3/confirmation3/compound4/emergency2,
LP-routing2/pricing2/Entry3/review2/direct governance2/fee-intake1. Position eight
words. Fresh royalty4/recovery2/canonicalV10/schema17/mint2/reporting5;17modules/20 callable helpers plus2 inert Factory data children (code-storage2). Original source9/schema16/V9 remains explicit. Historical schema14 preserves pre-reinvestment code-storage2; schema13 preserves SSTORE Factory.
Old V7/V6/header/runtime/profile/journal/receipt boundaries remain explicit.

One contribution pool at a time, <=4logical historical buckets. One main or
optional main+ONE residual in same ETH/ZZZ pool, Vault owns both NFTs. At replacement
main>=60%/residual<=40%, not perpetual target; residual half-side5000bps, positive
spacing gap, desired mode OFF by default. Both legs always count in valuation/
harvest/closure. Entrants fund MAIN only; no incumbent/residual/compound subsidy,
recenter or clock reset; actual marginal LP and aggregate shares must reconcile.

Ordinary85%centre-to-boundary same-side physical+independent reference,600second
sample/300maxgap/240source polling, durable60–300jitter after initial hard12hours.
Paid enrollment begins near eligibility; pending-first recovery, reset receipts
and provenance remain. Hourly harvest independent. Compound interval independent
after max(lastCompound,lastRebalance); automation waits for in-range/below-trigger
main/no pending geometry. Existing authenticated internal-harvest coalescing stays.

One human operator/governance, separate limited keeper key. Direct governance,
no timelock. Sealed implementations/parents/token identities fixed; bounded
policies/routes remain governed. Paused manual emergency2 can optionally bypass
financial guards and risk nearly all principal, never an automated fallback.
Terminal governance holder return closes both legs into actual ETH+ZZZ and pays
current NFT owners in bounded direct batches; no custody-address exit/bridge or
principal reopening. Claims/royalties/transfers remain. Canonical replacement is
separate, same-chain, reviewed verified source retirement/backing, never post-exit.

Fixed main tick bounds do not drift with swaps or entrant growth; slot0 and
composition do. Before manual consolidation confirm pause, read one canonical
snapshot and simulate the exact call against fresh state. Custody identity is
not a price quote or a commitment to every governed setting. Re-read IDs after
replacement, refresh reviews after settings/reorg/expiry and recover the same
pending hash before retry. See [focused review](reports/consolidation-races-20261106/REVIEW.md).

## Royalty opening and currency capacity

Final user choice: ONE HOUR (3600seconds), superseding the24-hour draft. Governance
NFT.setMintEnd mirrors final OpenSea sale stage. Unset/past end rejects minting;
future revisions allowed only while the OLD end has not passed. No mint after
close, no sellout assumption, no clock pause or administrator extension afterward.
Claims open at end+3600. NFTs whose activation finishes strictly before cutoff
share the initial admitted-currency pool at rarity1/2/3. Late activations get only
future receipts. A delayed first transaction cannot change the cutoff cohort.
Normal sync/claim/activation materializes allocation: no keeper/opening transaction
prerequisite. LP claims are independent. No deadline on DORMANT cards by user choice.

openingPool is separate from constructor/preadmission prefunds, earned liabilities
and exact ticket backing. Zero initial participants leave funds unallocated for later
explicit governance decision. allocateAllUnallocated(asset,reviewHash) allocates
all eligible unallocated whole units of ONE admitted currency at current active
weights; no swap/payout/recipient/sweep. Partial allocation remains. Unsupported
receipts require review/admission; no reconstructed receipt-time entitlement.

Original currencies only: ETH stays ETH, WETH stays WETH, USDC stays USDC. No
royalty converter/unwrap/approval/price route; separate LP conversion preserved.
Current owner inherits all unpaid rights.32total NFT/asset/ledger claim entries,
selected healthy currencies avoid one failed payout reverting an atomic batch.
Per-currency failure cohorts and previously allocated exact units stay protected. Default16ERC20+ETH capacity can
only increase through governance to64ERC20+ETH after gas/service review. Review
hash is NOT a gas proof. No universal frozen-token/unknown-currency payout promise; allocated rounding units are exactly assigned.

CanonicalV9 royalty header (unchanged royalty4 layout) five words includes end/capacity; source requires open/
finalized window and every initial currency synchronized before capture. Old V7/V6
peers rejected early. Import never reopens sale/grace; parked/principal wire shapes
do not imply runtime compatibility. Emergency/terminal LP recovery is independent.

## Exact-unit audit and evidence

The user approved exact-unit allocation. GCD-normalized captured rarity tickets
and a per-currency rotating cursor assign every allocated raw unit; no fresh
royalty scaled index/fraction reserve. StartsONE-based, backend offsetsZERO-based;
Historical original-source EVM logs/getters/V8 royalty rows verify that unchanged royalty4 layout, now carried inside V9. Claims/imports
are not income; only generic RoyaltiesAllocated credits fresh earnings once.
V9 preserves activation order and whole accrued liabilities, flattened in frozen
view without deleting source books. Old codecs/checkpoints remain historical.

Mint reviews bind sale end/revision plus core policy and NFT/receiver; callback
and restore-to-revive checks protect them. Cancelled-importer royalties recover
only after complete abort restoration, through authenticated lineage to reviewed
current active weights; target governance controls recovery, no chosen recipient.
The existing fixed VaultCanonical companion verifies one hop read-only.

Factory code-storage2 uses exactly2 immutable REVERT-prefixed data children;
reconstruction checks exact part/whole hashes and sizes before typed CREATE.
Royalty creation bytes stay identical. Schema14 authenticates the full graph
from independent final compiler pins; data children have no callable authority.
Exact target constructor/activation/claim gas remains a release gate.
Opt-in claim planning returns one freshly simulated unsigned batch within existing
32-entry/12M/fee/time/RPC limits, with all blocked/unresolved entries retained.
Replan after confirmation; no signer, queue, service or site change. Default
optional royalty sync gas1m, not a fixed charge. Expanding to64 currencies needs
worst-case gas/service/API qualification, even though inventory14 accepts97 token
records. No source publication is operating or independent approval.

[Same-main governance consolidation](reports/residual-main-consolidation-20261106/REVIEW.md)
adds residual-reinvest1 on Migration/Vault/Budget/PortfolioPolicy/ContributionPricing,
inventory15 with explicit raw-exit1 admission. Paused governance
consolidateResidual(request,forced) harvests/closes only the residual (or recovers
prior attributed idle), balances and increases the SAME main. No designated
compound release or share/centre/lastRebalance change. Guarded false uses checks14
and auto reviewed routing without keeper timing; forced true uses explicit
swap/mask. Exact structure/control proofs remain, modeOFF is applied atomically,
per-pool controls invalidate old samples even alreadyOFF/idle-only, compound clock
and recovery nonce/epoch advance. Independent pending main width remains.
Existing module-only Vault.emergencyRebalance is a typed fixed-Migration
dispatcher under cap1; old full emergency2 behavior stays separate. No extra
Vault selector/generic executor. Matching all5 capabilities/runtimes is mandatory
pre-seal inventory work; Access.seal does not prove the whole extension graph.
Raw close/full replace/park/resume/holder return remain. Check full operator
inputs and reverse/pause steps. Source publication does not upgrade old runtimes,
journals/services/sites/signers/Anvil or restart the paused heartbeat.

Prior physical-read record: reports/residual-lifecycle-20261106/VERIFICATION.md.
Prior changed-source record: reports/factory-claims-20261105/VERIFICATION.md.
Prior accounting audit: reports/last24h-audit-20261105/VERIFICATION.md and evidence.
It distinguishes prior failures/empty attempts, final source runs, actual source
producer/consumer evidence, exact unchanged reuse and missing live qualification.
Historical royalty-window3 counts never establish current4 evidence.

Test maintenance also reconciles current opening/rounding/profile assumptions,
closed-sale handoffs and nonvacuous stateful claims; explicit historical tests
remain. Aggregate16×1M optional failures exceed a12M operation envelope, so actual
currency count/provider gas qualification remains open; no live budget was raised.
See reports/last24h-audit-20261105/TEST_MAINTENANCE.md and its scoped follow-up receipts.

One Todo ledger docs/project-todo.json generates TODO.md. Keep feature/roadmap/
release/operator/context linked with source/evidence. Original reports immutable;
repository memory is not global personal memory or a background synchronization.
Source/checkpoint semantics changed: reviewed rebuild/re-pin, never relabel old
artifacts. Older research/failures retain original scope.

Main only. Preserve four protected dirty files in handoff, all Anvil8902 holdings,
dist overlays, pending/nonce/receipt/spend journals, shared signer and user-paused
heartbeat. Popldemo is simulation; separately served poplint is current3/unconfigured,
not fresh source9/accounting7. Public DEPLOYMENT null; browser signing Anvil-only.
No deployment/seal/public transaction/site/server/service/reset/signing change.

Open release gates: actual OpenSea drop/all mint-path/final-end binding, currencies,
dual feeds/routes/VRF/authorities, expanded gas/API/history/checkpoint workloads,
matching source9 services/site, storage/restore/long-lived history, independent
audit/remediation. Capacity64 and current source tests do not close these gates.
