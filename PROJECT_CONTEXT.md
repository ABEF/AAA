## Earnings ingestion audit continuation - 2026-10-19

The earnings backend and unsigned mint/claim preparation are already published;
do not reimplement the older quoted plan. This follow-up adds a read-only
[history audit](docs/HISTORY_AUDIT.md) comparing one configured current/predecessor
epoch window with a separately reviewed RPC. It requires all seven emitters,
exact cursor/header/log identity, confirmed ancestry and bounded work. Missing,
conflicting or unavailable data never yields a matched window. The indexer adds
one ordered block/log SQLite index; no economic replay or contract code changes.

[Scoped evidence](reports/history-audit/VERIFICATION.md) covers 41 distinct affected
cases across new execution and exact-body reuse, including 10,000 logs/128 blocks
and protected CLI output paths. No unchanged Solidity or earnings suites rerun.
Actual independent providers, full backfills, reviewed prices, large-history/load
qualification and website integration remain open. Provider agreement and a
partial window report are not completeness/finality proofs. Follow the linked
operator procedure; no server, website, public-chain or paused-monitor change.
Use main, preserve unrelated drafts and check Git for publication. Keep creator
questions in their central section; release remains NOT APPROVED.

## Creator coordination continuation - 2026-10-19

The user requested a dedicated **Creator tasks / ZZZ team** section in the
[central Todo](TODO.md#creator-tasks--zzz-team). Keep every question requiring
the token/pool team's answer there: fee basis/percentage, active-liquidity
measurement, payment delivery/reconciliation, independent ZZZ pricing,
token/pool controls, input liquidity and future-market/incident continuity.
The existing `creator-terms` task ID is preserved; technical qualification stays
under its linked Contracts/Backend tasks. Record dated answers and evidence,
never infer a payment agreement, provider choice or permission from silence.

The ZZZ-feed question is deferred to that section, not answered. No production
price source or complete ETH-to-LP qualification is established. Current selected
pool adapter support is distinguished from historical market observations.
This is documentation/coordination only: no contract, API, website, server,
public transaction or paused-monitor change; release remains NOT APPROVED.
Use main, preserve unrelated drafts and verify Git for publication. Update this
creator section whenever later development raises a team-dependent decision.

## Unsigned wallet preparation continuation - 2026-10-19

The saved mint/claim draft is now hardened for the current lifecycle and promoted
with [operator instructions](docs/FRONTEND_TRANSACTIONS.md) and
[scoped evidence](reports/wallet-preparation/VERIFICATION.md). Typed 0.05 ETH mint
and 1-32 mixed LP/royalty claims simulate at a confirmed canonical hash. Mint-only
pause and preparation block mint; eligible claims remain available. Unselected
currency faults can be isolated, while selected assets, inventory/core mismatches,
canonical locks, expiry and work budgets fail closed. A required reviewed policy
binds the read configuration and separately bounds/estimates gas; no signer or
broadcast exists. Default GET-only; explicit transaction config enables POST in
a supervised serial worker. Browser integration and live fee/RPC qualification
remain open. The 149-test affected inventory has passing evidence across two
scoped runs; the initial reorg fixture correction is recorded. All 40 Solidity
source bindings and six compiled ABIs match reusable artifacts; no contract rerun.

Use main and Git to establish publication. Preserve unrelated route/process-runner,
history-test and artwork drafts. No website/server/deployment/public transaction
or paused-monitor change. Update central Todo, features and operator manual with
future changes; release remains NOT APPROVED.

## Confirmed earnings continuation - 2026-10-19

The user selected **current (today's) prices** for all-time and 24-hour earnings.
Read [the earnings guide](docs/EARNINGS_HISTORY.md) and
[scoped verification](reports/earnings-history/VERIFICATION.md). Optional read-only
collection/NFT endpoints replay actual processed allocations and royalty receipts,
including complete configured same-chain predecessors. Shares, equal collective
membership, rarity cohorts and carried fractions are separate. Transfers, claims,
conversion credits and imported balances are not new earnings. Unprocessed funds
are excluded. Missing prices produce null USD, never an assumed stablecoin peg.

The 186-test affected inventory has passing current-body evidence across three
scoped runs, with fixture/runner corrections explicitly recorded. Forty unchanged
Solidity source/build bindings and compiled ABIs were reused; no contract rerun.
Live feeds, complete ingestion/load rehearsals and frontend integration remain
open. Release NOT APPROVED. Use main; check Git for publication. Preserve unrelated
drafts. No website/server, paused monitor or public-chain changes. Update the
central Todo, feature/evidence reference and operator manual with future changes.

## Current continuation: royalty reporting - 2026-10-19

Backend royalty reporting now distinguishes claimable ETH, unconverted source
balances and deferred currency eligibility through an explicit reviewed-ledger
profile. Converter status is a pinned enable-control observation, not an execution
ETA or qualified quote. Raw replay records conversions separately from claims and
preserves lifetime NFT history through validated same-chain replacements.
Unavailable values never become zero, and no currency fallback bypasses core
identity, canonical freshness or request work budgets.

Read [the operator/integration guide](docs/ROYALTY_REPORTING.md) and
[verification](reports/royalty-reporting/VERIFICATION.md): 138 affected Python
passes plus 20 supplemental passes, unchanged 40 Solidity source bindings reused,
ten getter ABIs and 26 added indexer events checked against compiler artifacts.
Gross earned fees/USD history and live website/service qualification remain open.
Website/server/paused monitor are unchanged. Publication is determined by main
and origin/main; unrelated local drafts are deliberately preserved.

## Replacement NFT holder preflight - 2026-10-19

Read [the holder inventory and cutover procedure](docs/HOLDER_PREFLIGHT.md) and
[scoped evidence](reports/holder-preflight/VERIFICATION.md). The read-only tool
inventories up to 1,000 NFT owners at an explicit confirmed canonical block,
flags contract/delegated owners, rejects mixed/duplicate/incomplete coverage and
never authorizes migration. Resolve exact replacement release/claim compatibility
before freeze; rescan after freeze and recheck before commit. Incompatible escrow
after freeze requires the supported fully funded abort before holder withdrawal;
no owner rewrite or retirement override. Actual marketplace/escrow qualification
remains open. Royalty conversion/outage work is published in 74c5f3e; no Solidity
changed in this inventory follow-up. Main only, preserve drafts; website/server,
public transactions and paused monitoring remain unchanged. Check Git for publication.

## Royalty batch conversion and outage recovery - 2026-10-19

The user approved automated batch ETH conversion, a maximum 1% execution loss
with gas separate, and optional-currency failure isolation. This supersedes earlier
notes saying these decisions were unapproved. Read [the runbook](docs/ROYALTY_SETTLEMENT.md)
and [scoped evidence](reports/royalty-conversion/VERIFICATION.md).

RoyaltyRewards checkpoints earned source balances for 1-32 sorted NFT IDs, converts
once through a separately deployed pre-seal-bound RoyaltyConverter, and credits the
same NFTs in ETH. Native receipt indices never redistribute conversion output.
Original source fractions, dust, quarantines and direct-currency claims persist;
conversion is not a payout or lifetime claim. Fixed helper, reviewed mutable route/
wrapper policies, exact deltas, 99% oracle floor, stronger caller minimum and deadline.
Keeper conversion is opt-in, shares serial nonce/pending/gas recovery, and uses
confirmed hash reads with fair bounded scanning. It is not deployed on the server.

Unreachable optional assets retain their older eligible cohort while activation
and healthy-currency royalties continue. On recovery, unseen receipts (including
during the outage) go to incumbents before waiting NFTs join future receipts.
No retroactive catch-up. Canonical export flattens join-index baselines; exact
unreadable backing can still block handoff. Immediate governance and all existing
LP economics remain unchanged. No website, server, public transaction or monitor
restart. Main only; preserve unrelated drafts and check Git for publication.

## ETH-first marketplace royalties - 2026-10-19

Read [royalty settlement](docs/ROYALTY_SETTLEMENT.md) and its
[central task](TODO.md#task-royalty-eth-settlement). The user accepted ETH pricing
with native ETH/verified Robinhood WETH as the initial royalty scope. If USDC/USDG
royalty settlement cannot be excluded on supported marketplace flows, implement
guarded automatic conversion to ETH. Activation input choices are separate.
Rarity/multiplier is fixed at reveal; activation enables eligibility without an
additional royalty payment or user registration. OpenSea documents an ETH/USDG
pricing choice, not a proven universal currency ban. Inspect actual settlement,
including offers and cross-chain checkout, rather than buyer input currency.

This is a documented direction, not implemented conversion or outage isolation.
The current ledger claims each admitted currency and synchronizes all admitted
assets during activation. Native ETH has no external token balance read; WETH
still has wrapper risks. Preserve pre-activation receipts and funded liabilities.
Per-currency delayed eligibility was discussed but NOT approved. Do not silently
adopt it or distribute older receipts using membership at later conversion time.
No source, marketplace, website/server, monitor or public transaction change is
included. Main only; preserve unrelated drafts and use Git for publication status.

## Operator procedures and maintenance - 2026-10-19

## Independent operator controls - 2026-10-19

The current candidate adds governed `PoolRegistry.disablePool(poolId,stopDeposits,
stopOperations)` (only clears existing flags, no token/price/venue reads) and
`NFT.setMintPaused(bool)` (new mints only; trailing callback guard). Full
configure/configureNative validation is still required to reopen pools. Pending
original reveal, existing activation, transfers, claims and LP work retain their
independent guards. Same immediate governance and preparation/canonical locks;
no new keeper/guardian authority, delay, reroll or provider substitution.
The read API exposes the mint switch separately. Successor mint-pause state is
reviewed operational configuration, not imported economic rights.

Read [current verification](reports/operator-controls/VERIFICATION.md) and the
[updated manual](docs/OPERATOR_MANUAL.md). Central Todo/features/release records
are reconciled; release remains NOT APPROVED. Use Git to establish publication.
No website/server/public transaction/deployment or monitor restart is included.
Preserve unrelated local drafts; main only. Historical source-bound evidence is
not a fresh full regression of these changes.


Read [the operator manual](docs/OPERATOR_MANUAL.md) before changing management
behavior. The user requires it to stay complete: every operator-facing function,
permission, parameter/default, lifecycle, service command, failure or recovery
change must update its applicable procedure in the same change, or explicitly
record why no operator procedure changes. Include authority, exact call/config,
preconditions, verification, stop/restart, rollback and irreversible limits.
Reconcile central Todo and feature/evidence documentation; never create a parallel
status checklist in the manual. Validate links and exact selectors/semantics.

The user selected reliable qualified/funded randomness plus stopping new minting
and draining original requests before whole-collection replacement. Retain the
fully-revealed handoff gate; no pending-request carry, reroll or admin-selected
traits. Unfulfilled VRF can still block replacement, not ordinary LP pool moves.
Keep only the existing 3% per-operation maintenance cap; no cumulative breaker.
Immediate governance remains accepted. Service/provider qualification and escrow
compatibility remain open. The manual distinguishes configure/pause/park/resume
from immutable implementations and unsupported future-chain recovery.

Request-wide API budgets, supervised read-only HTTP workers and a confirmed
mint-readiness endpoint are added in this workstream. See current scoped evidence
in reports/api-work-limits/VERIFICATION.md; these are not live hosting/VRF approval.
No Solidity, website, server, signer or paused-monitor change. Preserve unrelated
local drafts; use main and verify Git for publication.

## Review of October 18 changes - completed 2026-10-19

Read [the daily security review](reports/daily-security-20261018/REVIEW.md).
Reviewed 13 published commits from 79f205a through 485a089 plus a separate local
draft inspection. No new unauthorized principal withdrawal, hidden recipient or
reproducible double claim was identified; this is not a no-vulnerability guarantee.
Production remains NOT APPROVED. Immediate governance trust is accepted and must
not be silently replaced with a timelock. An unfulfilled ordered VRF request also
blocks whole-collection handoff; the fully-revealed-only requirement remains.
A new synthetic-clock reproduction observed 134 RPC calls including two traces
after expiry before safe rejection; no unsigned draft was returned. Request-wide
monotonic deadline/cancellation and work budgets are required before hosting.
Escrow/successor compatibility and cumulative maintenance losses remain risks.
All findings are linked to owning central Todo tasks. Existing 78 build/source
bindings, including 39 production sources, matched; unchanged test suites/static
analysis were not rerun. No production code, service, website, key, transaction
or monitor change occurred. Preserve unpublished drafts; check Git for publication.

## Immediate governance decision - 2026-10-18

Verification: 228 distinct affected Solidity passes (177 retained exact-bound
passes plus 51 corrected-fixture passes), 142 configuration passes, 30 normal
size gates / 39 production bindings, and 378 internally reviewed Slither findings.
See [current evidence](reports/immediate-governance/VERIFICATION.md). Not a full
new regression, live qualification or independent audit; release NOT APPROVED.

The user explicitly requested NO governance timelock at any point, superseding
both the old two-day template and the briefly proposed narrow fast-route role.
Read [immediate governance](docs/GOVERNANCE.md). AccessController now requires zero
constructor and single/batch scheduling delay and rejects delay updates; approved
Migration plans have MIGRATION_DELAY=0. Existing proposer/executor/canceller roles,
exact-operation hashes, replay/predecessor checks, sealing, canonical locks,
keeper cooldowns, oracle safety/finality, 1% contribution and 3% supported local
execution limits remain. No route-manager role or generic upgrade was added.
Governance can approve harmful dependencies or successor code immediately;
there is no advance warning window. Production addresses and independent approval
remain open. No deployment, public transaction, website/server update or restart
of the user-paused monitor occurred. Read scoped evidence and Git for verification
and publication; do not reuse older delayed-operation receipts as current proof.
Randomness-service qualification is still open; no provider was selected and no
randomness or artwork behavior changed in this workstream. Preserve other drafts.

## Read-only route campaign checkpoint - 2026-10-18

Read [the campaign brief](docs/INTEGRATION_CAMPAIGN.md) and
[observations](reports/activation-route-observation/VERIFICATION.md). A subsequent
paced probe succeeded for USDG/ETH feeds and four USDG-to-WETH quotes at block
92,079,017. Three conversion-only quotes were within 1% at observed oracle marks;
the 1% fee tier already exceeded it. Complete source-to-Pons LP execution remains
unqualified; gas and later LP costs are not included. No production code changed
and unchanged tests were not rerun. The earlier HTTP failure cause is unconfirmed.
The user requested a real-wallet campaign; no key was accessed, public transaction
submitted or contract deployed. The assistant cannot execute real-asset signing/
broadcasting; this is independent of wallet access. No signing script was supplied.
PoPL remains undeployed; the $1 variant remains local only and production mint is
0.05 ETH. Todo and feature references retain the open live qualification gates.
Preserve unrelated drafts, use main, and verify Git for publication. Website,
server and paused monitoring are unchanged.

## Local $1 rehearsal checkpoint - 2026-10-18

The user authorized $1 activation for testing and requested that any real bugs
found be fixed in production. Read [the isolated build guide](docs/ONE_DOLLAR_REHEARSAL.md)
and [scoped evidence](reports/one-dollar-rehearsal/VERIFICATION.md). The generator
copies sources outside the repository, changes the copied Entry/budget floors and
adds local-chain constructor guards. Ten Solidity and four Python cases pass;
the initial fixture's zero minimum-output mistake was corrected and preserved in
the evidence. No production defect was found. All production source remains
unchanged: $100 activation, 0.05 ETH mint and 1% execution loss with gas separate.
The website and production API still use $100; no live $1 integration is supplied.
Fix future production defects with focused regressions, without copying the test
override into production. Central Todo and feature/evidence references are updated.
README now separates Contracts / Backend / Frontend into component responsibility
tables with source links and an activation flow. It distinguishes live integration
targets from the current simulated website; no website source was changed.
Read-only public-wallet balance/token checks ran; price/route probing failed on
RPC HTTP errors, so no complete quote is claimed. No private key was used/saved,
no public transaction/deployment occurred, services and paused monitor are unchanged.
Use main and Git HEAD/origin to verify publication; preserve unrelated drafts.

## Range-policy application checkpoint - 2026-10-18

Read [range policy](docs/RANGE_POLICY_UPDATES.md) and [current evidence](reports/range-policy/VERIFICATION.md).
Timelocked width changes now trigger ordinary rebalance at flat prices after
cooldown. The stateless comparison uses current physical ticks and stored center;
successful replacement clears it. No new force role/request/Vault state exists.
Fresh prices, pause/lifecycle, minima, 3% aggregate and 5% idle guards persist.
Backend reports range_update_pending and price/range eligibility reason at the
confirmed hash; next keeper timing remains unknown without qualified telemetry.
Execution uses current approved configuration, not a signed historical config
hash. Scope: 37 Solidity / 38 isolated Python checks, fresh normal sizes and
internal review; refer to the evidence for the selected-pool fork result. This is
not a full regression, independent audit or production approval. Only Strategy
production source changed; Vault headroom stays 19 bytes. Preserve unrelated
drafts. Use main; verify Git publication. No website/server change, public
transaction or restart of the paused monitor is authorized.

## Dynamic liquidity checkpoint - 2026-10-18

Read [dynamic liquidity](docs/DYNAMIC_LIQUIDITY.md) and its
[scoped verification](reports/dynamic-liquidity/VERIFICATION.md) before continuing.
The user explicitly approved out-of-range activation/top-ups with a warning,
including cooldown end/current eligibility; a 600-second polling example is not
a guaranteed next rebalance. Without fresh authenticated keeper telemetry, next
check/execution time stays unavailable. The same original-source 99% marginal
deployed-LP rule and separate network gas remain enforced.

The user also explicitly approved a 3% aggregate execution-loss cap on ordinary
rebalance. Vault now reuses the immutable budget checkpoints before harvest,
after exact compound release and after redeployment. Fixed initial prices,
97% LP-plus-idle retention and 5% idle remain; existing per-step guards are kept.
This is not a 97%-deployed guarantee, an IL hedge, a cumulative erosion cap or a
cross-chain guarantee. Metadata now applies the real strategy's exit-price
deviation/freshness guard and reports unavailable on failure without losing rights.
The API resolves current LP identity/total shares separately from historical
gross contributions, and prepared transactions include confirmed range/timing.

Current size gates leave Vault 19 runtime bytes and Migration 58. Read the scoped
receipts instead of relabelling old full regressions/fork/static evidence. Main
is the only branch; use Git HEAD/origin for exact publication. Keep unrelated
wallet/process-runner/artwork drafts intact. Release is NOT APPROVED; website and
server remain unchanged, monitor remains paused, no public transaction authorized.
Repository context is durable local project memory, not global personal memory.

## Activation preparation checkpoint - 2026-10-18

Complete typed activation/top-up preparation is now in `frontend_api/activation.py`,
with strict operator pins, bounded built-in call traces and an opt-in loopback
endpoint. Read [the integration guide](docs/ACTIVATION_PREPARATION.md) and
[scoped verification](reports/activation-preparation/VERIFICATION.md). There are
38 passing focused backend tests on the exact publication snapshot, 63 verified
ABI getter layouts and a local Anvil trace/gas probe with the actual budget helper.
No production Solidity changed; unchanged broad contract checks were not repeated.

Per-NFT displayed value must come from confirmed `NFT.currentLPValue`: marked
deployed LP plus attributed idle/compound, separately from rewards and the new
contribution's marginal LP. The user pays network gas separately; one Entry call
covers conversion/balancing/LP addition, with ERC20 approval/reset transactions
separate when required. Conversion/slippage/undeployed input share the 1% limit.
Missing allowance produces only an exact approval step, never a fake ready LP
quote. Full preparation checks original-source value, actual budget/share/LP
results and resimulates exact final calldata with bounded minima/deadline.

This milestone is published on main with Todo/features/evidence; verify Git for
the exact commit. Actual route/feed manifests, provider callTracer/hash/gas support,
complete network-fee accounting, browser wallet/hosting and independent production
qualification remain open. Release NOT APPROVED; website/server unchanged. Preserve
the separate unpublished mint/claim, conversion-only quote, process-runner and
artwork drafts. The user-paused staging monitor remains paused.

# AAA / ZZZ PoPL project context

## Claim-history continuity checkpoint - 2026-10-18

Read [the predecessor history reference](docs/FRONTEND_LINEAGE.md) and its
[verification](reports/frontend-lineage/VERIFICATION.md). The schema-2 API now
combines lifetime LP and royalty claims across the complete explicitly pinned
same-chain predecessor lineage, including past owners and historical-only assets.
Each source must be retired with matching origin, bidirectional peer links,
canonical activation/retirement receipt and terminal root. Replays end at each
source retirement; current claimable balances are unchanged. Missing lineage
configuration stays unavailable; invalid configured history fails closed.
Bounds are eight predecessors and one million configured replay events in total.
These checks rely on reviewed RPC/indexer ingestion, not consensus finality proofs.

The exact publication snapshot passed 91 API/lifecycle/history tests, including
17 new lineage cases. Existing compiler artifacts authenticate two getters and
two event layouts; production Solidity is unchanged and was not retested.
The central read-API task is implemented locally. Hosted archive qualification,
independent peer-code review, live frontend integration and cross-chain history
remain separate open tasks. Keep release NOT APPROVED. Do not mistake these
same-chain receipt checks for the missing cross-chain finality mechanism.

Use main and verify publication with Git HEAD/origin/main. Preserve unrelated
optional wallet POST, quote/process-runner and artwork drafts. No website/server
change, monitor restart, deployment or public transaction was authorized.
Older dated checkpoints below retain their original scope; this entry supersedes
the earlier statement that same-chain predecessor replay was unimplemented.

## Frontend lifecycle checkpoint - 2026-10-18

The [schema-2 read API](docs/FRONTEND_LIFECYCLE.md) now uses eight runtime pins,
strict canonical lifecycle/origin checks and a read-only `/v1/protocol` endpoint.
Frozen/importing/retired/cancelled deployments cannot serve apparently spendable
NFT/wallet projections. Importing origins and incomplete successor lifetime-claim
totals are unavailable, not zero. Source-committed peer addresses are not independently
verified deployments; complete predecessor replay remains open in the Todo.

[Verification](reports/frontend-lifecycle/VERIFICATION.md) records 74 passing tests
against the exact publication snapshot and 15 ABI checks against matching existing
contract artifacts. Production Solidity is unchanged. Saved final snapshot freshness
checks are included; optional wallet POST, quote/process-runner and artwork drafts
remain separate. Check Git for publication; no website, server, monitor or public
deployment/transaction changed.

## Verified handoff checkpoint - 2026-10-18

The saved bridge fixtures and cold-helper gas changes are verified: 582 offline
regression passes, zero failures, two expected opt-in fork setup skips, across
49 compiler-bound suites. Reuse the unchanged 34 focused handoff passes only with
[the dependency check](reports/canonical-handoff/reuse-verification.json): together
these cover 616 successful cases, not one newly executed 616-case run. The 30
normal object gates/39 production source bindings, 141 configuration checks,
88 focused keeper checks and 374-finding internal review remain source-matched.
123 additional keeper cases pass; one Unix permissions case awaits Ubuntu.
Current runtime margins remain Vault 33 bytes and Migration 58 bytes.

This checkpoint accompanies scoped publication on main. Verify Git HEAD and
origin/main before naming the published commit or reporting CI; older uncommitted
statements below describe historical saves. Preserve unrelated unpublished
wallet/API, quote/process-runner and artwork drafts. Follow
[the resume handoff](docs/WORK_HANDOFF.md) and [verification](reports/canonical-handoff/VERIFICATION.md).
No production source changed during the resumed regression. Release is NOT
APPROVED; cross-chain finality/closure/lineage/transport remain pre-seal work.
No website/server update or public deployment/transaction is authorized.

The user paused the chat staging-health monitor on 2026-10-17. Do not resume it
without authorization. The isolated server service was not stopped by that pause;
subsequent intervals have no chat-monitor coverage. Existing staging has not been
upgraded to this keeper/controller lifecycle. Exact-commit CI and new operating
rehearsals remain separate from local evidence.

## Saved continuation checkpoint - 2026-10-17

Historical snapshot, superseded by the verified 2026-10-18 checkpoint above.

The user requested a durable save before credits run out. Read
[the resume handoff](docs/WORK_HANDOFF.md) and the
[current evidence](reports/canonical-handoff/VERIFICATION.md) before continuing.
The same-chain candidate and these notes are LOCAL, UNCOMMITTED and UNPUSHED
at this checkpoint; baseline main is `79f205a7933107f61f26892109f14ee52821700e`.
Do not confuse saved files with GitHub publication or production approval.

Completed scoped evidence: 34 focused handoff tests, 30 normal object size gates,
39 production source bindings, 141 configuration tests and 88 keeper tests.
Internal Slither review covers 374 findings (153 false positives, 75 accepted
risks, 146 informational), with coverage and 10 mutation rejections passing.
The broader diagnostic run returned 576 passes, six failures and two intentional
fork skips; its compiled snapshot also predates the final coordinator changes.
Six bridge failures exposed mocks lacking the lineage interface. Mock fixes are
saved but NOT rerun. Gas diagnostic attempt1 returned ten successes, but source
binding rejected its stale fixtures; the final cold-helper fixture changes also
need a fresh run. Do not report a complete current-source regression pass.

Preserve unrelated wallet/quote/process-runner/artwork drafts. Do not repeat
unchanged focused/static checks without a source-binding reason. Keep release
NOT APPROVED, future-chain requirements open, and website/server unchanged.

## Canonical handoff candidate - 2026-10-17

Read [the same-chain handoff reference](docs/CANONICAL_HANDOFF.md) and
[current verification](reports/canonical-handoff/VERIFICATION.md). Continue using
`main`. Preserve unrelated unpublished wallet/quote/process-runner/artwork work.

The new local candidate adds six-domain complete export/import, immutable receipt
cutoffs, ownership/accounting freeze, ordered per-domain settlement, exact classified backing transfers, restored
abort, atomic source retirement/single-successor activation and one-hop late
creator/royalty forwarding. Four separately deployed modules are sealed:
CanonicalHandoff, NFTCanonical, VaultCanonical and FeesCanonical; owner bindings
are verified. Royalty and creator receiver factories are immutable automatic
children. Inventory is controller plus 20 modules and eight fixed helpers/factories.

This executable path is SAME-CHAIN ONLY: all mints revealed, local buckets
Parked/None, no active plans and no historical legacy bridge sends/receipts.
The original identity/inventory and exact reward fractions persist; source
approvals are not imported. Imported successors cannot initiate v3 principal
bridging because its lineage/current-home model is incompatible. Cross-chain
finality, authenticated channel closure, a new lineage/message version and exact
transport/backing remain pre-seal work. Do not say full future-chain migration is
complete or that sealed code can acquire it later. No post-halt recovery is supplied.

The user explicitly chose reviewed replacement code through timelocked governance
on 2026-10-17, accepting that a malicious approved replacement could divert LP.
Do not add an identical-code requirement or describe governance as unable to alter
successor economics. Independent code/admission review remains mandatory; this
decision does not waive verified finality, exact backing or single-successor
retirement, and adds no multisig/timeout activation override.

Keeper requires strict canonicalState plus preparationActive; locked states stop
all new submissions while pending receipt recovery continues. Existing isolated
staging is unchanged. API/website lifecycle, predecessor claim-history continuity,
marketplace collection cutover and contract-owner/escrow compatibility remain
tracked in the central Todo. Keep the current feature/evidence and release scope
distinct from historical receipts. No website/server change, public transaction
or contract deployment is authorized.

## Architecture evolution and migration preparation - 2026-10-17

**Use `main` for this project**, as explicitly requested by the user. The earlier
review branch was integrated into main; check Git for exact publication. Preserve
unrelated unpublished wallet/quote/process-runner/artwork changes.

Read [migration safety](docs/MIGRATION_SAFETY.md), the
[canonical migration design](docs/CANONICAL_MIGRATION_DESIGN.md),
[current verification](reports/migration-safety/VERIFICATION.md) and the earlier
[architecture review](reports/architecture-evolution/REVIEW.md).
The user-approved **3% aggregate execution limit, gas separate**, is now enforced
for atomic same-ordered-pair local `movePool` and parked `resume`. The immutable
Vault-created helper snapshots prices/principal before harvest, adds released
compound to the denominator and requires at least 97% retained LP plus attributed
idle, with the existing 5% idle ceiling. It is not a 97% deployed-LP promise, a
cross-chain budget or protection against repeated cumulative losses. Activation
and top-ups keep their **1% marginal deployed-LP** rule. Keep 80/10/5/5 fixed.
Do not remove ordered-pair guards: different pairs need composition epochs,
historical reward/intake handling and typed conversion.

The user selected **controlled whole-protocol migration while the home chain
still works**, deferring post-halt recovery, and **verified source finality with
no multisig-only override** for future replacement activation. No proof provider
is inferred. Reversible timelocked preparation now stops new economic work and
protocol configuration while claims, transfers and authenticated settlement/drain
remain available. It does not freeze/export ledgers, retire the source, activate
a successor or authenticate satellite shutdown. Complete funded freeze/export/
import and single-successor accounting remain pre-seal requirements; sealed
contracts cannot gain these missing capabilities later.

Keeper preparation checks fail closed if the controller getter is unavailable.
Receipt recovery and permitted drains continue; new rebalance/compound/buyback
submissions stop. Existing isolated staging was not upgraded. Qualify keeper and
controller/fixture interfaces together before deployment. See the
[keeper evidence](reports/canonical-preparation/keeper/README.md).

Destination capacity has permanent idempotent registration; `bucketCount`
includes unfunded reserved None identities. Source code does not authenticate
remote reservation proof. The [address inventory](docs/DEPLOYMENT_ADDRESSES.md)
now includes the fixed migration-budget helper; production selections remain
open. Current normal-build headroom is only 17 runtime bytes in Vault and 30 in
Migration, requiring modular design for subsequent handoff work.

Use current source-bound receipts, not older Vault/static/fork results, for these
changes. Internal review is not an independent audit or production approval.
No website/server change, public transaction or contract deployment is authorized.

Recorded on 2026-10-14 from decisions in the project conversation. Update this note when the user changes those decisions. This is durable project context for future work in these repositories.


## Current handoff and documentation map - 2026-10-16

This handoff supersedes older dated implementation/publication statements below.
The [README](README.md) and [feature/evidence reference](docs/IMPLEMENTATION_STATUS.md)
summarize the current published candidate. The atomic original-source Activation
Entry, 1-32-operation mixed claim router and four-historical-bucket cap are
implemented; actual input routes, services and production qualification remain open.

- **Progress:** [Project Todo](TODO.md) is the only task-status list, generated from [project-todo.json](docs/project-todo.json). All 38 task IDs/statuses and the detailed release requirements were preserved in consolidation commit `ce5851b`. Keep Contracts / Backend / Frontend ordering and clickable file links.
- **Evidence:** [Implementation reference](docs/IMPLEMENTATION_STATUS.md) distinguishes published features, historical source-bound checks and local unpublished candidates. Reports keep their original scope.
- **Approval:** [Release record](docs/RELEASE_CHECKLIST.md) remains NOT APPROVED. Runbooks and the roadmap supply procedures and sequencing, not separate task status. Use [TODO_WORKFLOW.md](docs/TODO_WORKFLOW.md) for updates.
- **Publication:** the NFT-rights audit/tests and keeper hardening are published. Pre-existing wallet preparation, final read freshness, activation-quote and fork-runner changes, plus artwork working files, remain outside that publication. Check Git HEAD/origin and the actual diff rather than interpreting an older 'current/uncommitted' paragraph as today's state.
- **Boundaries:** contracts remain undeployed; the website is a simulation. Isolated Anvil keeper evidence is not Robinhood production qualification. No public deployment, signing or real asset movement is authorized.

These files are durable repository memory for future sessions, not an assurance
of global ChatGPT personal memory or automatic cross-repository synchronization.

## Accepted decisions snapshot - 2026-10-15, locally verified candidate

This section supersedes conflicting earlier decisions in the historical entries below. Preserve those entries as evidence of prior scope and checks; do not treat their older $500 minimum, 50/30/10/10 split, Power accounting or implementation boundaries as the current specification. This note does not claim global personal memory is enabled.

- The user requested aligning the real contract candidate with the website's accepted product decisions. The implementation and scoped local verification are complete; no smart contract deployment, public-chain signature or real transaction is authorized by this alignment task.
- Dormant mint costs exactly **0.05 ETH**, forwarded to the immutable mint-proceeds recipient separately from LP and rewards. Minting creates zero attached LP and no reward eligibility. The latest activation policy is **$100 gross input value with at least 99% marginal actually deployed LP**, also applying the 1% execution/undeployed cap to additions, with gas separate. Current Vault checks start at pair-token input; atomic pre-conversion needs source-value binding. Target inputs are verified **USDC, USDG, ETH and ZZZ**. Owners can claim funded rewards; LP principal is nonredeemable. Selling/transferring transfers attached shares and unclaimed/future fee rights.
- The production collection cap is **1,000 NFTs**. Final revealed rarity counts are exactly **600 Commun / 300 Rare / 100 Legendary**, using authenticated VRF words and draws without replacement against remaining quotas. A separate VRF word draws a complete palette/pattern entry without replacement from that rarity's fixed visual inventory. Rarity, palette and pattern stay fixed. Finalization follows mint order to prevent callback order from manipulating quota consumption. No owner/admin-selected trait, cancellation/retry/reroll or coordinator replacement is implemented. Missing earlier fulfillment intentionally blocks later ordered reveals and their activation; actual supported network/coordinator/subscription configuration remains a production gate.
- LP revenue is allocated **80% individual / 10% collective / 5% permanent LP compounding / 5% buyback and burn**. The individual share follows each NFT's nonredeemable LP shares in its physical pool. The collective share is equal per activated NFT, with no rarity multiplier or Power. Top-ups do not add collective membership. Unharvested, unpublished or delayed remote rewards follow membership at receipt/processing, rather than fee-generation time. Already indexed rewards and settled pending local creator-inbox funds exclude new entrants. Sub-twenty-unit funded fee dust is settled to existing owners before membership/share changes; raw-unit rounding is not an administrator withdrawal budget.
- Marketplace creator fees request **5%** through ERC2981, which cannot force a marketplace to pay. **100% of actual admitted NFT-sale royalty receipts** are distributed through a separate immutable NFT-controlled ledger to activated Commun/Rare/Legendary NFTs at **x1/x2/x3**. These weights never change LP fee shares or the equal collective share. The receiver accepts native ETH and bounded governance-admitted exact-transfer ERC20 assets; constructor/preadmission/no-eligible-member funds are quarantined, fractions remain accounted, and no administrator sweep exists. Unclaimed royalty rights follow current NFT ownership. Claims remain independent of strategy pause, LP valuation and migration availability.
- Artwork evolution uses the NFT's **current marked share of attached principal, idle assets and compound reserves**, not lifetime contributions or a high-water mark. Thresholds are Dormant / Activated / Enhanced at **$1,000** / Singularity at **$10,000**. Market declines may reduce the artwork stage while activation and royalty/fee eligibility persist. Remote/in-flight custody, stale feeds or unavailable dependencies explicitly report valuation unavailable, with labelled Activated artwork fallback. This marked value creates no redemption right or guaranteed return.
- Global funded-dust settlement is now bounded in source by a **16-total-historical-bucket cap**, including imported custody; returns reuse an existing slot. The attempted 32-bucket funded-entry workload measured **16,311,524 gas**, exceeding the unchanged **12M** local regression budget. The cap was reduced rather than raising the budget. The revised 16-bucket workload passed at **8,909,042 gas**, and all four cap tests passed for canonical extra-bucket rejection/existing-pool entry, return/repeated departure, satellite import history and funded entry. The limit includes every registered bucket, not just active ones. This local test uses a shared two-token pair and mock venue; it does not prove every real-venue/32-asset/16-inbox combination safe on every target chain. The earlier 32-bucket fork and size evidence is retained as intermediate, not final-source evidence.
- Accepted artwork colors are **Cyan, Blue, Violet, Emerald, Amber (yellow), Crimson (red), Ivory (white) and Onyx (black)**. Bicolor permits any distinct pair containing Ivory, Amber, Crimson or Onyx. Tricolor adds a distinct Amber, Crimson or Onyx to an allowed pair; ordering does not create another palette. This produces **8 monochrome / 22 bicolor / 28 tricolor = 58 palettes**. Color and color style are purely visual and unrelated to rarity or rewards. Final approved patterns are **Flowing arcs, Segmented panels, Orbital rings and Vertical ribs**. The user rejected Hexagonal mesh and Helix, accepted Vertical ribs in place of Branching circuits, and explicitly retained Segmented panels. Circuit patterns also have no economic effect.
- The finite artwork inventory contains **200 monochrome / 500 bicolor / 300 tricolor** entries, each with the same 60/30/10 rarity composition, balanced palette usage and at most four identical palette/pattern/rarity finishes with the four approved patterns. All 100 Legendary finishes are unique. The production VRF draw and website simulation use the same packed inventory; the simulation seed never supplies production randomness. This yields 542 distinct finished base designs among 1,000 NFTs. The complete rendering library is **58 palettes x 4 patterns x 3 rarities x 4 evolutions = 2,784 states**, not 2,784 NFTs. Catalogue code, JSON and regeneration checks are in design/nft-metadata/palette-system-v1/.
- The approved metallic egg texture, shape and finish are retained. Original monochrome colors use their own original illustrations; mixed palettes, Ivory and Onyx use matching rarity/evolution originals with deterministic SVG palette/circuit rendering. The source 72 PNGs remain unchanged; optimized embedded WebP data preserves design/materials rather than pixel-identical PNG output. A replacement texture experiment was not used. Enhanced retains one brighter border and Singularity the exclusive double border/background light. These eight-color rules supersede the earlier 40-palette proposal.
- The user accepted **Flowing arcs for Overview PoPL #444 with no additional circuit overlay**. Keep the original egg detailing. The website banner places **DEVELOPMENT PREVIEW on the right**, with bold **PROOF OF PERMANENT LIQUIDITY** and the exact disclaimer **“(Minting and claims are simulated; no real assets move)”** on the left. Nondefault pattern lines now remain readable in Dormant state and brighten progressively; original texture/materials are unchanged.
- The user removed every GitHub/source/economics/security link from the public website, including the top View source link and FAQ source link. Footer social controls are a globe linked to **https://zzz.protocol.link/** plus clickable X and Telegram icon placeholders with coming-soon feedback. The user deferred both social URLs; do not invent them. This public-UI request does not remove private Git/deployment documentation or change the repositories' origins.
- The website remains a simulation. The final artwork/UI version **`9eaa9e67917240112dd402d27fc8b2980c7b79fa`** is locally verified, pushed to GitHub and deployed on the Ubuntu server. All **5,581 public files** match committed source/build SHA-256 hashes over verified HTTPS, with five HTTPS/redirect/IP host checks and four private-path checks passing. The published banner, social placeholders and absence of GitHub/source links match the build. Local checks passed **40 tests, 83 HTML IDs, five routes and 2,784 self-contained artwork/metadata pairs**; desktop/mobile pattern switching and the #444 Flowing arcs example were inspected in the browser. Current external receipt: `website-server-release-9eaa9e6/public-verification.json`. Earlier **`4cf1c81a59067c8530708f2a68dd6da6797ca1fc`** and **`f8e19161e2857f02c7174f711ce587ea8c184227`** receipts preserve their historical 155-file / 37-test / 72-artwork checks. Keep the standing order: local edit, verify, commit/push website, deploy that committed version, then verify publicly. Website success does not establish live contract behavior.
- **Final four-pattern contract implementation and current scoped source evidence are complete.** Full offline Solidity passed **336 tests, zero failures and one expected opt-in fork-setup skip** (337 total across 24 suites, 22.38 seconds runtime). Portable Python passed **327 tests** from a **331-test inventory**, with zero failures/errors/runtime skips; four unchanged Unix-only cases remain for Ubuntu CI. The NFT suite has 20 passing tests, including 1,000 fuzz cases and two complete 1,000-mint inventory draws proving style/rarity quotas, at most four identical finishes and all 100 Legendary finishes unique. All **20** module/helper runtime/initcode-object gates passed; the normal offline `forge build --sizes` exited zero. NFT runtime/initcode object is **18,519/42,004 bytes**, renderer **12,191/12,508**, and Vault **24,407/25,279**, leaving Vault 169 runtime bytes available. Constructor arguments still require deployment-time allowance. Compiler metadata binds all **26 Solidity source files**. Fresh Slither **0.11.6** covers those same 26 sources plus three build/configuration files: **179 detections**, individually reviewed internally as **110 false positives / 42 accepted risks / 27 informational / zero unresolved**. Native coverage, split/merged matcher replay, seven adversarial mutations and an independent internal 100,000-draw inventory model pass. This is internal source-bound review, not an independent audit. Current evidence is `reports/artwork-palettes/verification-summary.json` and `reports/artwork-palette/README.md`; old five-pattern receipts remain externally preserved as intermediate evidence. Check Ubuntu CI separately for the published revision.
- **Historical pre-art source evidence remains preserved.** `reports/website-alignment/verification-summary.json` and `final-summary.json` record the prior 16-bucket checkpoint: 334 offline Solidity passes (one expected skip), 321 portable Python passes, all 20 size gates and 177 individually reviewed Slither detections. Its live-dependency fork passed **nine tests, zero failures/skips** at Robinhood block **88,544,093**, hash `0xc44dc8c95c6011b991312179f532935c2d94e4f21b84899d23896fd0fe01d490`. All four bucket-cap cases passed, including the **8,909,042-gas** workload. Its separate **256 x 256 accounting stress run passed 65,536 calls with zero reverts** (two tests, no skips). The fork used real deployed dependencies with a separate local hookless pool and mocked VRF, not actual Pons custody or a real randomness service. The live-dependency fork and extended stress profile were **not rerun for the final four-pattern artwork source**. LP/economic/custody source hashes remain unchanged, but these earlier complete snapshots must not be described as fresh same-source artwork verification.
- Dynamic tokenURI reads select the current artwork stage, and reveal/contributions emit ERC-4906 events. The release-hardening candidate adds permissionless inclusive ordinal-range notifications (maximum 50), emitting actual hashed token IDs without price reads. An optional disabled-by-default keeper watcher observes confirmed evolution/availability/reveal state through the existing simulated, budgeted, serial transaction path. Fair bounded scans and receipt-state checkpoints avoid starvation and outdated notification baselines. It does not notify every within-stage USD-value change; production operating staging, immutable publication and marketplace cache behavior remain open. Uniswap does not update this NFT metadata.
- The 2026-10-15 repository review records the canonical **Implemented / Todo checklist at docs/IMPLEMENTATION_STATUS.md**, detailed component boundaries at docs/COMPONENT_STATUS.md and the separate NOT APPROVED production gate at docs/RELEASE_CHECKLIST.md. All three Ubuntu CI jobs passed for **5febe7065856749345010ecca23dcd368b472c9e**, run **38793910449**. Remaining visible-website integrations include arbitrary USDC-to-pair routing, a quote that leaves $100 net deployed LP, hosted ownership/fee/USD history projections, real wallet actions and separate royalty balances/claims. Contracts expose single-NFT/single-asset claims; a reviewed bulk approach is still required. Production token IDs are hashed identities; short sequential display labels would need an ordinal-based metadata/UI choice. These are pending implementation/integration details, not another change to the accepted economic split or artwork rules.
- No public-chain contracts are deployed. The actual selected native-ETH/Pons pool integration and revenue arrangement, real supported VRF service/configuration, production bridge provider/backing/finality, ZZZ valuation/outage policy, production authorities and mint recipient, staged operating tests, and independent audit remain open gates. Static-analysis triage and local mocks are development evidence only. The completed local checks do not approve production deployment or replace the outstanding independent audit and staged integrations.
- **Release checklist work, 2026-10-15:** fresh metadata-source offline Solidity passed **342 tests**, zero failures and one expected fork setup skip; all **20** normal runtime/initcode-object gates passed; all **26** source/compiler bindings match. NFT runtime/initcode is **18,822/42,307 bytes**; Vault remains **24,407**, with only 169 runtime bytes available. Fifty cold metadata notifications used **318,466 gas**, below the unchanged 500,000 budget. Fresh internal Slither has **179** individually reviewed findings, zero unresolved, with source-bound coverage and adversarial matcher checks. Full Python, keeper review and exact source hashes are recorded in **reports/release-hardening/**; earlier artwork/alignment reports remain historical. Check the exact published revision's Ubuntu CI separately. The native/Pons feasibility review records two-provider matching observations at block **89,487,849**, but no compatible adapter or relaxed guards. This is internal development evidence, not an independent audit.
- The user has not selected production governance, guardian, keeper or mint-recipient public addresses and explicitly requested leaving those gates open. Rewards are driven by actual funding/processing, with no fixed minute accrual or periodic claim window. The keeper example polls every **600 seconds**, makes conventional harvesting eligible every **14,400 seconds**, and rebalances only when oracle-price trigger, cooldown and execution guards pass. Production strategy parameters and creator payment timing/percentage remain undecided. LP claims use already allocated funds; royalty claims also synchronize pending admitted receipts. Website LP claims remain simulated and live royalty controls remain absent. README title uses a plain ASCII hyphen to avoid the reported encoding artifact.

- The user added three required release-testing layers on 2026-10-15: local tests for minting, activation, rewards, royalties, transfers and security; a Robinhood mainnet fork against the actual ZZZ pool, hook and deployed dependencies; and Robinhood Testnet rehearsals for wallet flows, website integration, keeper operations and deployment. These remain open in docs/RELEASE_CHECKLIST.md and are linked from docs/IMPLEMENTATION_STATUS.md. Existing local and separate hookless-pool evidence does not complete all three layers. Sepolia is supplementary; this documentation request does not authorize deployment or transactions.

- The user authorized development across the six remaining release workstreams on 2026-10-15. Creator-payment terms remain explicitly unset. The user reports the creator accepted sharing according to PoPL pool-liquidity share and requested implemented measurement proposals plus follow-up Todos. Fee-weighted sampled active liquidity and a time-weighted alternative are implemented as proposals, without payout authority. Confirm measurement/epoch/sampling/complete fee data and payout basis/asset/frequency/sender/receiver with the creator. A fresh two-provider observation at block 89,525,289 confirms 1% hook fee, 30% Pons share, zero creator tax and buyback disabled: creator cash is roughly 0.70% of swap value before conversion effects. See reports/release-progress/creator-revenue-20261015.md.
- Current working release-integration code adds the selected native/Pons adapter and explicit real-key/WETH accounting, fee-aware balancing, immutable 32-operation claim batching, deployment-pinned confirmed read API and revenue measurement tools. New source needs its own tests/size/static-analysis evidence; older reports above are historical. The full existing artwork upload archive is prepared and verified (2,784 image states, 5,571 files); IPFS provider, directory CID, public upload/pinning and marketplace rehearsals remain pending. See docs/ARTWORK_PUBLICATION.md. No smart contracts, public transactions or paid hosting were authorized.
- The website release after the royalty-card and artwork-layout work is **8c0b93523d914644d440129d74745c9e12f8e08a**, locally verified, pushed and deployed: 47 tests and all 5,581 public file hashes passed. It remains a simulation. The current contract/integration work has not changed or redeployed the website. Full live wallet/history integration and stable pre-conversion entry remain open, rather than being inferred from the demo UI.

## Two related repositories

Latest recovery requirement (2026-10-15): allow timelocked activation-asset additions,
disabling and re-enabling without coupling existing LP custody or claims to new-input
admission. The immutable registry helper records append-only reviewed policies;
pool reconfiguration must not re-enable a disabled currency. Wrapper policies
support reviewed implementation/admin/owner changes, including owner renunciation.
Sequencer-source replacement is implemented under the same timelock without a
zero-feed bypass; all 12 focused cases pass in the current full suite. Disabled source strategy operations must not alone block a
governed exit. These are explicit configuration paths, not general proxy upgrades
or a guarantee against failed external chains/tokens/bridges. See
docs/CHANGE_AND_RECOVERY.md and the release checklist for retained limits.

Current local release-integration verification: 430 Solidity passes, zero failures,
two expected opt-in fork setup skips; 478 portable Python passes with four Unix-only
cases reserved for Ubuntu; all 22 module/helper size gates and 28 compiler/source
bindings pass. Vault runtime is 24,434 bytes (142-byte margin). The actual selected
pool has 17 passing fork cases with mock authority/VRF and synthetic price scaffolding.
Fresh internal Slither has 210 individually reviewed findings: 121 false positives,
56 accepted risks, 33 informational and zero unresolved entries. This is not an
independent audit. See reports/release-progress/README.md. Changes remain local,
uncommitted/undeployed, and no website/server change occurred in this contract work.

| Project | GitHub | Local directory |
| --- | --- | --- |
| Website | https://github.com/ABEF/AAA-website | `C:/Users/Ali/Desktop/2.x holas/Oto/aaa-website` |
| Smart contracts | https://github.com/ABEF/AAA | `C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2` |

The website introduces ZZZ Collection / Proof of Permanent Liquidity (PoPL) and provides an interactive collection and portfolio preview. The contract repository contains the Solidity development candidate and supporting technical material. Changes, commits, and publication should target the repository appropriate to the user's request.

## Accepted product behavior

- Minting creates a dormant NFT with $0 LP, no Power, and no earned fees. It changes NFT supply only.
- Real contract mint price is exactly 0.05 ETH. Proceeds go immediately to the immutable constructor-selected `MINT_PROCEEDS_RECIPIENT`; no production recipient has been chosen. Mint proceeds are separate from permanent LP and rewards.
- Activation requires adding at least $500 of LP, permanently locked in the vault. Activation increases both the NFT's LP and the collection's locked LP.
- An active NFT holder can add more permanently locked LP to the same NFT. This increases its position and collection LP; it does not withdraw principal or create retroactive fees.
- The NFT can be transferred or sold; associated economic rights follow ownership while the principal stays locked forever.
- Collected swap fees are allocated 50% to the NFT owner, 30% to collective rewards, 10% to LP compounding, and 10% to buyback and burn. The actual contract accounting uses token units, Power, funded balances, and checkpoint rules; displayed dollar examples are explanatory.
- The website should show collection LP, LP associated with each NFT, lifetime and last-24-hour generated fees, and rewards claimable for the connected example portfolio. Mint, activate, add LP, individual claim, and bulk claim are separate interactions.

## Agreed illustrative data

- 100 example NFTs, 20 dormant; a few positions have at least $100,000 locked LP.
- Collection locked LP: $425,000. Total available ZZZ pool liquidity: $1,250,000. The collection's TVL share is 34%.
- Example last-24-hour trading volume: $848,000. Assumed swap fee: 0.30%.
- Gross pool fees: $2,544 per day. At an assumed proportional 34% fee-earning share, collection gross fees are $864.96 per day, before Uniswap protocol deductions.
- Collection age: 10 weeks, or 70 days. With the same illustrative daily rate, lifetime gross fees are $60,547.20.
- Lifetime allocations: $30,273.60 owner rewards, $18,164.16 collective rewards, $6,054.72 compounding, and $6,054.72 buyback and burn.
- The compounding allocation is a budget; do not silently add it to the current $425,000 LP snapshot. New LP deposits do not rewrite historical generated fees.
- TVL share is not generally the active fee-earning share in concentrated liquidity. The calculation explicitly assumes proportional active liquidity throughout the day. It is an illustration, not live data or a yield forecast.
- Overview headline: "34% of total available pool liquidity. Committed for good."

## Accepted visual choices

- Use the supplied blue/cyan branding on a dark navy site. The "02 / SHARED PRODUCTIVITY" section must match the dark palette.
- Original reference assets are `logo.jpg`, `collec.jpg`, and `nft.jpg` in the parent `Oto` directory. Website copies are in `assets/`.
- The collection JPEG informed the lifecycle and economic explanations. The user subsequently requested removing it from the displayed site and improving the native 50/30/10/10 section instead. Retain it as a reference asset.
- Keep NFT artwork as an unfilled wireframe cube. Dormant lines are muted; active lines become brighter and thicker with restrained cyan glow. Enhanced is visibly bolder and Singularity has the brightest near-white outlines. Do not fill the entire hexagon or cube faces.
- Conceptual levels: Dormant $0; Online $500; Enhanced $1,000; Advanced $5,000; Elite $25,000; Singularity $100,000. These are product illustrations, not implemented contract guarantees.
- The NFT illustration in "More than a mint" uses a normal image cursor and a small bottom-right enlargement arrow, matching Overview. Avoid a zoom-in plus cursor.
- The user later removed the supplied NFT JPEG from Overview to avoid repeating it. Keep it on Mint with its enlargement arrow. Overview leads with a native liquidity snapshot, then trading/fee figures, a five-step lifecycle, the fee calculator, and the existing dark allocation section.

## Website implementation and verification

- Buildless HTML/CSS/JavaScript with Node.js 20+ standard-library tools and no third-party runtime dependencies.
- Routes: `#overview`, `#collection`, `#mint`, `#my-nfts`. Local preview: `http://127.0.0.1:4173`.
- Commands: `npm run dev`, `npm test`, `npm run check`, `npm run build`. Static output: ignored `dist/`; source files and original assets are committed.
- Browser wallet support uses injected EIP-1193/EIP-6963 providers or a demo wallet. It only requests public accounts and chain identifiers. It does not sign, approve tokens, or submit blockchain transactions.
- All displayed positions and actions are labeled simulations. Connecting a real wallet still displays the example portfolio, not that address's actual on-chain holdings.
- Preview events persist under localStorage key `zzz-popl-preview-v4`; wallet connections do not persist. The footer's Reset demo restores the baseline dataset.
- Example portfolio includes NFTs #444, #128, #91, and dormant #74. Claims change funded example balances without reducing LP or generated fee history. Cent allocation conserves each displayed total.
- Most recent automated verification: 25 Node tests passed; syntax, unique IDs, local references, application selectors, and four routes passed. The redesigned Overview was checked at desktop width and at 390px mobile width without horizontal overflow. Overview contains no NFT JPEG, Mint retains its illustration/enlargement button, the 0.25% calculator example returns $720.80, and the browser reported no console errors.

## Contract candidate and integration boundary

- Current production-readiness pass (2026-10-14) keeps the reward choice explicitly **pending**: the user deferred choosing a share of Pons hook revenue or a new pool and has not supplied percentage/payout/authority terms. Do not infer a finalized agreement or conventional fee entitlement. Continue independent hardening without changing economics or approving a new custody model.
- This pass refactors only private Vault valuation/owner helpers, preserving its public ABI and guards. Runtime is now 23,662 bytes, 914 bytes below EIP-170 (777 bytes saved). Keeper fixes include valid positional cast calldata, signer-environment isolation, transaction/receipt identity before pending recovery updates, remote legacy reward delivery after LP departure, strict integers, and exclusive random atomic state writes. CI/action/forge-std/analyzer dependency pins are recorded.
- Current local evidence: 140 offline Solidity tests passed (one intentionally skipped network setup); six actual deployed-dependency fork tests passed at Robinhood block 88,544,093/hash `0xc44dc8c95c6011b991312179f532935c2d94e4f21b84899d23896fd0fe01d490`; 65,536 seeded invariant calls had no unexpected reverts; 135 native Windows Python tests passed with four unchanged Unix-only tests excluded for Ubuntu CI. Slither 0.11.6 completed with 127 individually reviewed findings, without an independent audit. Gas workloads cover 1/100/1,000 NFTs and 32 funded reward assets, explicitly using a mock venue. The real fork adapter operations use a different hookless local test pool and synthetic feeds; the actual requested native/Pons pool remains unsupported.
- `reports/PRODUCTION_READINESS.md` and `reports/production/` hold current evidence separately from historical reports. `config/production.example.json` intentionally fails the offline production validator. Production reward/market choice, ZZZ valuation/outage policy, actual transport and backing, authorities, staged operating tests and independent audit remain blockers. No public-chain deployment, signatures or transactions occurred; the separate website was not changed.
- Published readiness hardening in `6802c9299eb88e15bd7f3423efb86d70cfb56162`, followed by workflow/uncached archive pacing repairs. Final published HEAD is `4924d0f6db30a734dad4617f9b1f174cc5f8b4e1`. All three Ubuntu GitHub jobs passed for this exact revision: https://github.com/ABEF/AAA/actions/runs/38616088583. Full Python inventory is now 157 including 18 test-only archive-runner regressions; offline Solidity remains 140 passed plus its intentional fork-setup skip; separate actual fork run has six passed and zero skips. A loopback read-only relay paces anonymous archive reads and runs without storage caching, keeping failures visible and forwarding actual fixed-block responses. The public RPC's earlier quota/pruned-state failures are recorded separately. `reports/production/forge-lint-review.json` individually reviews 47 retained lints, including conventional timestamp-range assumptions; this does not replace independent review.

- No public-chain contracts are deployed. Commit `14b773ee3612a80c32a01761c334080abd083e15` implements the 0.05 ETH dormant mint, separate current-owner activation with at least $500 of actually deployed LP, permanent top-ups and unchanged reward checkpoints. The previous free deposit/issuance entrypoint is removed. Deployment and independent review remain outstanding; the website remains a simulation.
- The candidate targets hookless Uniswap v4 static-fee pools with conventional ERC-20 assets, including WETH rather than native ETH. It contains 16 Solidity modules, lifetime contribution/Power accounting, funded reward checkpoints, and bounded reward assets.
- The user requires future unknown EVM chains/pools and repeated LP migration: close LP, bridge attributed principal between protocol vaults, then create LP again. The candidate now supports post-seal timelocked append-only route onboarding, remote-to-remote canonical graph approval, repeated migrations/returns, authenticated custody epochs, immutable ACK snapshots and legacy reward delivery. NFTs and contribution Power remain on their original canonical chain. A production transport, native-ETH/hook integration and live multi-chain validation are not supplied. Approving future destinations is a governance trust power, not proof that arbitrary destination code preserves principal.
- Governance is the deployment-selected `GOVERNANCE_MULTISIG`, which remains unset. NFT owners do not automatically vote. The local template has a two-day timelock plus two-day migration delay; executors may execute only the exact approved operation. Sealing removes bootstrap setup authority and fixes module bindings while allowing timelocked new route approval.
- The selected actual market is Robinhood Chain (4663) ZZZ/native ETH, pool `0x6538e2c223ed70228114983afecbe5e69fe627e2fafdf367bdd6bdeff2ad391f`, token `0x7dbf38976f6D3b9c529e7D9484A71898B409eE6a`, fee=0, tickSpacing=200, PonsV2MemeHook `0xE5e702641Ea86F4ae6cC3cDaeD2B886f976Be044`. Core LP fees are zero; hook fees follow creator/Pons recipient rules. Liquidity share does not grant a share of hook revenue. The user explicitly deferred deciding the project's reward integration. Details and primary sources are in `docs/ROBINHOOD_POOL.md`; previous website 0.30% figures remain hypothetical.
- Latest local implementation verification: 134 Solidity tests passed in 11 suites, four 1,000-case fuzz tests; 30 Python ABI/indexer tests passed; full compilation, all 16 module size gates and source consistency passed. Mock LP venues/bridge support an A->B->C->A->B test with no remint or Power change; this is not live chain/provider testing. Profile now uses Solc 0.8.26, via IR, Yul disabled, optimizer runs 1. Vault runtime is 24,439 bytes, only 137 below EIP-170. Evidence is in `reports/IMPLEMENTATION_UPDATE.md` and `reports/implementation/`. Ubuntu GitHub Actions passed for the published commit: 86 Python tests, 134 Solidity tests, compilation and size/source checks. Run: https://github.com/ABEF/AAA/actions/runs/38531875891.
- The initial contract repository import was committed and pushed as `a9707e89a8059c11bd1b8b0db82efa722ce5ddca`. Documentation was reorganized; original implementation and security-source checksums were preserved. Original historical README and manifest are under `reports/history/`.
- Initial native Windows Python validation ran 84 tests: 81 passed, one Unix-permission assertion failed, and two failed because `fcntl` was unavailable. On 2026-10-14, the repaired Ubuntu GitHub Actions workflow passed all 84 Python tests, source checks, contract compilation/size checks, and all 70 Solidity tests. Native Windows Foundry also passed all 70 Solidity tests. Run: https://github.com/ABEF/AAA/actions/runs/38525810030, commit `3c6f83ed87610869da740ce945b47f1673f73794`.
- CI repairs pinned the published Uniswap v4-periphery version `1.0.3` with a lockfile, disabled only Solidity 0.8.26's crashing Yul optimizer while retaining the EVM optimizer, and renamed a rollback test that accidentally matched Foundry's removed `testFail*` convention. All 16 contract source files remain unchanged. Vault runtime size is 23,451 bytes, within the 24,576-byte limit. Current repair evidence is in `reports/CI_REPAIR.md` and `reports/ci-repair/`; original historical reports remain separate. Real Uniswap fork integration, gas benchmarking of this compiler profile, production bridge transport, and an independent audit remain outstanding.
- Before enabling real minting, activation, deposits, or claims, implement/review the intended ABI, configure deployment addresses and chain, authenticated ownership reads, valuation sources, a reorg-aware indexer, funded claim balances, token approvals, and wallet-confirmed transactions.

## Public website deployment

- On 2026-10-14, the user authorized deployment to their Ubuntu server and chose the server IP rather than a domain.
- Initial preview URL: http://46.225.185.212. This first deployment used HTTP before the later domain/HTTPS setup below. The site's existing simulation boundaries still apply.
- Ubuntu 24.04 runs Nginx on port 80. Nginx is enabled to start after a reboot. The pre-existing service on port 8443 was left alone.
- Static document root: `/var/www/aaa-website/current`, pointing to `/var/www/aaa-website/releases/87b66e2-20261014`. Nginx site configuration: `/etc/nginx/sites-available/aaa-website`, with a `sites-enabled` symlink.
- The release contains the nine built public files from website commit `87b66e2ef19f5564e50b45f598ea3b4b1024d8f4`. All nine returned HTTP 200 with matching SHA-256 hashes from outside the server. Source notes and Git metadata are not served.
- There is no Node development server, Git credential, or server password in the deployed static build. Credentials must remain outside project files.
- README setup instructions use `git clone`, relative `cd aaa-website`, and commands from the clone's root. Keep public setup instructions independent of the author's local paths and compatible with Windows, macOS, and Linux.
- The user then selected `popl.0xwave.com` as the desired website hostname. DNS is managed by OVH; the existing `0xwave.com` site uses a separate server and must be preserved.
- The earlier Nginx configuration recognised both `popl.0xwave.com` and the server IP. A request using that Host header returned the correct build with a matching SHA-256 hash. OVH authoritative DNS reported that earlier subdomain did not exist.
- The earlier requested OVH record was type A, subdomain `popl`, target `46.225.185.212`, TTL default. The user instead created the `popldemo` records described below; agents have not edited the OVH DNS zone.

### Current hostname and publishing workflow

- The user actually published A records for `popldemo.0xwave.com` and `www.popldemo.0xwave.com`, both pointing to `46.225.185.212`. These are the current website targets, superseding the earlier requested `popl` hostname. OVH authoritative DNS and public resolver 1.1.1.1 both returned the correct IPv4 address on 2026-10-14; no IPv6 records were returned.
- Nginx routing must explicitly name both `popldemo` hostnames. A request for them previously reached the default welcome page because only the earlier `popl` hostname was configured.
- The HTTPS setup is tracked in `deploy/enable-https.sh`: a separate Nginx site for the two names, a Let's Encrypt certificate covering both, HTTP-to-HTTPS redirects, and a Certbot renewal timer and renewal check. Website code remains a clearly labeled simulation.
- Required workflow for every requested website modification: **edit locally → verify → commit and push to ABEF/AAA-website → deploy that committed version to Ubuntu → verify the public result**. This is standing user authorization to complete website updates across all three destinations. Do not deploy uncommitted product changes.
- `deploy/install-release.sh` publishes a checksum-verified static build into a directory named by its full Git commit, atomically switches `/var/www/aaa-website/current`, and preserves the previous release for rollback. `/var/www/aaa-website/deployed-commit` records the active commit outside the public document root.
- Do not change the `0xwave.com` root DNS or deploy smart contracts as part of website publishing. Preserve the separate root-domain site and the existing port-8443 service.

## Handling context and credentials

`AGENTS.md` points agents to this note when working in the corresponding project directory. This does not imply global ChatGPT personal memory is enabled. Keep the copies in both projects aligned after material decisions. Do not store pasted tokens or credentials here or in Git.

## Future bridge onboarding decision (2026-10-15)

The user authorized building secure onboarding for future unknown EVM chains, pools and bridge providers before deployment. The new fixed `ZZZBridgeRouter` is a 17th module (`Ids.TRANSPORT`); sealing fixes all 16 bindings and validates the adapter endpoint against it. Append-only timelocked transport policies pin physical routers/wrappers/channel code/configuration/review identities. Route registration is now `add(Route, policyId)` and hashes both; old routes cannot switch provider. Policies start outbound-disabled; pending authenticated exact-funded old-policy receipts survive outbound/route disable and pause. Migration checks source readiness before proposal and LP release. An empty router permits local paid dormant mint/activation without any selected SDK. No actual SDK bridge, provider backing, deployment or live transaction was supplied; independent review and the deferred reward/market decision remain open. See `docs/BRIDGE_ONBOARDING.md` and `reports/future-bridge/README.md` for final evidence. This supersedes the prior no-new-custody-decision boundary only for this authorized fixed-router/provider-onboarding implementation; actual bridge choice is still pending.

Publication and final verification: committed/pushed `35f1d928b12282c0f0ba8a05d9ea270219f823af` (`Add immutable timelocked future bridge onboarding`) to ABEF/AAA main. All three Ubuntu jobs passed for that exact commit: https://github.com/ABEF/AAA/actions/runs/38649308759. Local evidence: 183 offline Solidity passed / one expected offline fork-setup skip; 38 router security tests including 1,000-case fuzz; seven real-router/mock-provider repeated migration scenarios; full Python inventory 176 (172 portable Windows passed, four unchanged Unix-only assertions retained for CI); Slither 136 findings with individually recorded dispositions and exact source hashes. The schema-2 manifest requires complete registered policy event inventory and retains disabled historical routes while active migration routes require enabled policies and settlement paths. Router runtime/initcode 14,964/15,476 bytes, Vault unchanged 23,662/24,688, all 17 module standard size gates passed. No public deployment, signatures, provider SDK choice or website changes.

## Shared LP decision (2026-10-15)

The user explicitly selected shared LP per pool to avoid one rebalance per active NFT. This authorizes replacing per-NFT physical LP custody with one bucket per pool/strategy, canonical nonredeemable NFT shares, pool-level upkeep and separate NFT fee balances. The 50% owner bucket is proportional to shares; the 30% collective bucket remains lifetime contribution Power. Minting remains exactly 0.05 ETH dormant issuance without LP. Activation must add at least $500 of marginal deployed LP; permanent top-ups buy new shares at current principal NAV. Whole-bucket V3 migrations preserve the canonical share ledger; no per-NFT principal redemption or partial migration. Membership freezes while scheduled/away and after return until all authenticated old remote allocations are funded home. Destination pools must be permanently reserved before route use; distinct buckets cannot automatically merge. Earlier per-NFT analyzer/size/test evidence is historical and must not be reused as shared-custody verification. Current implementation/testing is in progress; no contracts were deployed or public-chain transactions signed. Website/server unchanged.

Shared-pool local verification completed: 234 offline Solidity passed / one expected offline fork setup skip; eight actual deployed-dependency fork tests passed including shared Vault entry and rebalance; 65,536 seeded pooled invariant handler calls with zero unexpected reverts; 216 Python inventory / 212 portable Windows passed with four Unix-only assertions reserved for Ubuntu. All17 standard size gates passed: Vault23591runtime24463init985margin, unchangedcompilerprofile. Fresh Slither139 findings individually reviewed, separate83High/Mediumreview; no independent audit. Public NFT read API is now nftStatus/nftBucket/sharesOf/contributionUSD; old position(nftId) is removed, group(bucketId) is physical custody. Publication/Ubuntu CI verification pending.

Published shared LP implementation to ABEF/AAA main as 1c0f76b4d8a456c20d5d20ccc2d016eb751e831f (Pool LP custody with nonredeemable NFT shares). Local195-file committed manifest verified. GitHub Ubuntu run https://github.com/ABEF/AAA/actions/runs/38660995988 is in progress; verify final result before claiming remote checks passed.

Initial shared-LP CI completed: offline verification and all eight actual dependency fork tests passed, but static-analysis matching failed on four presentation-only nested-callee ordering differences across Windows/Linux. A narrow external-callee leaf normalization preserves all 139 findings and source guards; 15 matcher regressions, nine independent mutation rejections and 221/225 portable Python tests pass (four unchanged Unix-only assertions retained). Corrected matching and updated evidence are being published; final exact-commit Ubuntu status still requires verification.

Final shared-pool publication verified: main commit e62d32aba10e9aa0f11c14a0e5a5ee0d1ba38a5d (Stabilize cross-platform Slither review matching), following implementation commit 1c0f76b4d8a456c20d5d20ccc2d016eb751e831f. All three Ubuntu jobs passed for the exact final commit: https://github.com/ABEF/AAA/actions/runs/38661751130. The final CI ran 225 Python tests, 234 passing offline Solidity tests with one expected offline fork setup skip, all 17 standard module size gates, the 139-finding source-bound Slither coverage gate, and all eight actual Robinhood dependency fork tests without skips. All 199 committed file hashes match MANIFEST.sha256. Tracked worktree clean; local AGENTS/context notes intentionally untracked. No deployed contracts, public transactions, real bridge SDK, new reward decision, website or server changes. Independent audit and the documented production/economic/integration gates remain required. Full final CI/job logs retained in the external pooled-20261015 evidence directory.

## Creator-shared Pons rewards update (2026-10-15)

The user now reports that the creator of the selected Pons pool will share rewards with liquidity providers. Record this as the intended external reward source to investigate, superseding the earlier fully undecided Pons-share/new-pool direction. This is a user-reported future distribution, not independent verification of a deployed agreement or automatic core LP-fee entitlement. The percentage, denominator (creator payout versus total hook revenue), eligible LPs, attribution/period rules, payout currency, timing, distributor/claim interface and payment-control terms remain unspecified. PoPL must receive/claim its actual shared-bucket allocation before applying its internal 50/30/10/10 funded distribution; the example 34% TVL ratio is not automatically the creator payout weight. Do not invent terms or change custody/security/authority rules based on this statement. No Solidity, public documentation, deployment, transaction, website or server change has been authorized or made by this update. The current Vault-only fee allocator and native/hook-rejecting adapter still require a reviewed integration; a direct token transfer must not be mistaken for allocated claimable rewards.

## Plain creator-payment integration authorized (2026-10-15)

The user clarified that the creator will simply send rewards to a contract address and PoPL must make them claimable by NFT share. This explicitly authorizes implementing funded payment intake, superseding the previous no-code-change note. No assumed percentage or creator-controlled payout configuration is needed to account actual received funds. The accepted internal50/30/10/10 remains ownerbucketshares/collectiveglobalPower/compound/buyback. Implementation in progress: immutable per-canonical-bucket ZZZRewardReceiver helper factory inFees (notnewsealedmodule), createdpostseal+activation, max16receiveraddresses; plainETH optionallywrapped1:1throughreviewed18decimalpairasset, pairERC20rawtransfers, permissionlesssync andkeepersynchronization includingpause/remote. Vaultgloballysettlespendingreceipts andoldrawdustbeforeowner/Powerchanges. Constructorprefundsquarantined; noadminrescue/redirection/replacement; receiptsneverdischargeauthenticatedremote liabilities. ClaimsusefundedERC20(includingWETH), canonicalcompoundreserveswhileawayawaitreturn. Thisdoesnotaddselectednative/PonshookLPcustodysupport,deployment,realpaymentsorwebsite/serverchanges. Fresh tests/staticreview/CIrequired beforepublicationcompletion.

## Creator-payment implementation published (2026-10-15)

The user clarified that the creator will send rewards directly to a contract address; PoPL must allocate funded receipts and allow NFT owners to claim according to their rights. This authorizes actual plain-payment intake, without assuming a creator percentage or historical entitlement. The existing internal allocation remains 50% bucket-share owner rewards, 30% global lifetime contribution Power, 10% permanent compounding and 10% buyback/burn.

Published to ABEF/AAA main as `4a05f6103b1113a0fd06341d039f35b37fc2e55e` (`Add immutable creator-funded shared LP rewards`). `ZZZFeeController` creates one immutable `ZZZRewardReceiver` helper per already-active canonical bucket after sealing through governance/timelock, bounded to 16; the helper is not an eighteenth sealed module. It accepts the original admitted pair ERC20 currencies and optionally native ETH wrapped exactly one-for-one through its admitted 18-decimal pair wrapper. Anyone or the constrained keeper can process receipts. NFT owners claim funded ERC20 rewards, including WETH rather than native ETH. Constructor prefunds are quarantined; unsupported assets have no rescue. There is no administrator withdrawal, redirection or registered replacement. Mint proceeds remain separate and receiver/mint-recipient collisions are rejected.

Final entry hardening settles all inboxes and raw dust at old shares/Power before entry, after entry balancing and after final LP mint/increase. Late compounding is priced into incumbent NAV; the 95% deployment check and final pending/dust barrier precede the relocated owner checkpoint and share issuance. Seven callback regressions cover the separately identified stale-checkpoint window and atomic rollback. Late idle cannot satisfy the $500 marginal deployed-LP activation minimum. Canonical receipt processing/claims remain available during pause and while custody is away; external receipts never satisfy authenticated remote liabilities. Home compound reserves paid while away await compatible maintenance after return.

Current local evidence: 279 offline Solidity tests passed with one expected opt-in fork setup skip; all 45 targeted funding tests passed, including 43 integration/security cases and two invariant-suite tests; seeded audit invariant ran 256 x 256 = 65,536 scheduled handler calls with zero unexpected reverts. Nine actual dependency fork tests passed without skips, using the fixed Robinhood block/hash and a different hookless WETH/ZZZ local fork pool with synthetic feeds and mock access. All 17 sealed modules plus the helper pass standard EVM size gates: Vault runtime/init 24,212/25,091 bytes (364-byte runtime margin), Fees 24,203/24,764 (373-byte margin), receiver 4,265/5,801. Python inventory is 255 with 251 portable Windows tests passed; four unchanged Unix-only assertions remain for Ubuntu CI. Slither has 160 source-bound findings, all individually triaged, with a separate internal AI-agent review of all 91 High/Medium findings; all 48 Forge warnings and 98 informational notes are recorded. This is not an independent external audit. All 218 committed manifest entries were verified. Evidence: `reports/reward-funding/README.md`; baseline review preserved byte-exact in Git history evidence.

GitHub verification for this exact commit is running at https://github.com/ABEF/AAA/actions/runs/38669641381; confirm its final status before claiming all Ubuntu checks passed. The production template remains blocked with 244 issues. Actual selected native-ETH/Pons-hooked LP custody, actual production bridge/backing, valuation policy, authorities, payment terms/economic dust/admission review, staging and independent external audit/remediation remain outstanding. No public-chain deployment, signatures, real payments, website or server changes occurred. AGENTS.md and this context file remain local untracked notes, excluded from the commit.


Final creator-payment publication verified: implementation commit `4a05f6103b1113a0fd06341d039f35b37fc2e55e`, followed by final main commit `9674824000836f4e21e176a58220f9e22b3778b8` (`Stabilize tied-event Slither review matching`). All three Ubuntu jobs passed for that exact final commit: https://github.com/ABEF/AAA/actions/runs/38670588829. CI ran all 268 Python tests, 279 passing offline Solidity tests with one expected opt-in fork-setup skip, all standard size checks, complete 160-finding source-bound Slither review coverage and all nine actual dependency fork tests without skips. The initial run passed contracts/fork but rejected one Low event presentation ordering tie; the narrow matcher repair has 28 focused tests including 13 new regressions, preserves every original reviewed identity/disposition and changes no Solidity. Final portable Windows Python count is 264 passed with four unchanged Unix-only cases reserved for Ubuntu. All 219 committed manifest entries were verified. Final CI status and three complete job logs are retained externally in reward-funding-20261015. Tracked worktree is clean; local context/AGENTS notes remain untracked. No deployed payment address, public transaction, actual Pons LP adapter/bridge-provider deployment, website or server change. Independent external audit and documented production gates remain outstanding.

## Egg NFT metadata and royalty concept (2026-10-15)

The user requested three rarity tiers named Commun, Rare and Legendary, with NFT-sale royalty redistribution weights x1, x2 and x3 respectively. An NFT must have been activated to participate; a dormant NFT has weight zero even if Legendary. These weights affect a separate funded NFT-sale royalty ledger, not the existing LP owner-share or collective Power calculations, and do not mean that marketplace royalty rates double/triple. Example: $600 distributable royalties and one eligible NFT of each rarity allocate $100/$200/$300. The sale royalty rate, holder-distribution fraction, rarity assignment/supply and checkpoint/claim implementation remain undefined.

The requested visual evolution examples now use four states: Dormant, Activated, Enhanced and Singularity. Singularity is $10,000 LP, replacing the earlier $100,000 illustration. The concept sheet reuses the earlier $500 activation/$1,000 Enhanced examples; final evolution valuation/high-water policy is still undecided. Rarity gives a permanent material/shell difference. Activation lights the border, Enhanced makes that border bolder/brighter, and Singularity adds light in the background. Legendary should have a more reflective/shiny egg. This new egg direction supersedes the prior cube concept for this NFT art exploration; no website update is implied.

Opened both user-linked references successfully using direct read-only image fetch after the web reader failed: minimal glossy black egg and dark cyan technical/crystalline egg. Generated and visually inspected one 3x4 contact sheet with the built-in image_gen tool. Saved `design/nft-metadata/rarity-evolution-concept-v1.png`, `concept-rules-v1.json` and the exact generation prompt in `rarity-evolution-prompt-v1.txt`. These are local draft examples, not contract implementation or production metadata. Current ZZZNFT remains an ERC721 with governance-controlled base URI; it has no rarity state, evolution, ERC2981 or NFT-sale royalty distribution. No Solidity, website, server, deployment, transaction, commit or push occurred for this visual request.

## Local egg library and clearer Overview (2026-10-15)

- The user explicitly requested this website work **locally only**. Do not commit, push or update Ubuntu for this pass. This overrides the normal three-destination publishing workflow for the current changes.
- Keep 100 baseline example positions with **72 artwork variants**, not 72 minted positions: Cyan, Blue, Violet, Emerald, Amber and Crimson × Commun/Rare/Legendary × Dormant/Activated/Enhanced/Singularity. Generated PNGs and preview metadata live in `AAA-website/assets/nfts/`.
- Rarity and color stay fixed per NFT. Activation and permanent LP additions select its next evolution image. Threshold illustrations: $0/$500/$1,000/$10,000. The newer egg direction supersedes the old cube and six-level illustration.
- Latest border correction: Enhanced uses the lighter/finer outer frame; Singularity uses the brightest/boldest near-white double frame and retains its background light. Do not swap the whole egg images or remove the Singularity background.
- Commun/Rare/Legendary have separate NFT-sale royalty redistribution weights ×1/×2/×3 only after activation; dormant weight is zero. These weights never affect LP fee allocation or Power, and do not multiply a marketplace royalty rate. Mint preview options explicitly say “royalties shares”. Position cards say “Permanent LP attached” and “NFT-sale royalty weight”, without the redundant “Separate from LP fees” line.
- The new Artwork route has color/rarity/evolution filters, pagination, image enlargement and example metadata downloads. Mint has a visual explorer; exploration does not select mint traits or change dormant minting. Example trait assignment is deterministic for preview only; production rarity assignment and funded NFT-sale royalty contracts remain unimplemented.
- Overview is reorganized into one collection snapshot, three lifecycle steps, LP revenue allocation, separate NFT-sale royalties, and a compact essential FAQ. The repeated architecture and benefit blocks are removed; the hypothetical fee calculator is expandable. Financial baseline and 50/30/10/10 allocations remain unchanged.
- Source checks pass for all five routes and 72 artwork/metadata entries. All 33 Node tests pass, including rarity independence from LP rewards and artwork changes across activation/top-ups. The Overview calculator still gives $720.80 at 0.25%; mobile checks show no horizontal overflow. No Solidity source, real transaction, GitHub publication or Ubuntu deployment is part of this work.

### Latest steering: activation-first presentation and 80/10/5/5

This supersedes the earlier $500 and 50/30/10/10 website preview decisions above, for the current local-only website changes. The user changed activation to at least 100 USDC or $100 worth of ZZZ at its price. The preview form now accepts ZZZ/USDC as a contribution choice and validates a minimum $100 USD-equivalent; it does not invent a ZZZ price, token quote or conversion execution. Activation funds permanent LP attributed to that NFT, and later additions grow its attached LP allocation. Holders claim funded fee rewards only; principal cannot be redeemed. Trading fee rights have no expiry, and a buyer inherits the same attached LP allocation and reward rights. LP market value and actual rewards are not guaranteed.

Overview now leads with this NFT-to-attached-LP relationship. Collection total LP remains visible; the pool-share percentage is a small contextual figure with no progress bar or implication of a 100% target. Repeated sections remain removed. Latest user allocation: **80% NFT owner / 10% collective / 5% compounding / 5% buyback and burn**. Updated chart, calculator, Mint text, history budget and tests. $864.96 is allocated $691.97/$86.49/$43.25/$43.25 using deterministic cent remainders. Lifetime compounding budget is $3,027.36. Existing funded example claim balances are illustrative and separate from the gross allocation calculator.

All 72 final PNGs are installed locally, including 36 revised Enhanced/Singularity frames. Built-in image_gen was used; initial originals are preserved. Exact initial and edit prompt sets are in the contract project's `design/nft-metadata/72-variants-prompts-v1.json` and `border-swap-prompts-v2.json`. Preview metadata now uses $100 for Activated. The website's 100-position baseline, $425,000 LP and gross fee history are preserved; locally saved user preview events can increase the displayed supply/LP.

Important boundary: the Solidity candidate still has its existing $500 activation and prior allocation rules. No Solidity source or deployment configuration was changed for these website requests. Applying the new economics to contracts requires separate implementation and security verification. No commit, push, Ubuntu update, real transaction or contract deployment occurred.

Default demo portfolio explicitly confirmed: one Dormant (#74), two Enhanced (#444/#91), one Singularity (#128). The user requested restoring these four starting positions; the local Reset demo action restored the $425,000/100-position collection baseline and removed simulated extra mints. A test assertion now protects the four-state portfolio composition.

### Final border rule: single Enhanced, double Singularity

The user clarified after reviewing v3: **Enhanced needs exactly one bright border; reserve the double border exclusively for Singularity.** Preserve Enhanced's stronger egg-seam/rim highlights so it remains visibly above Activated. This supersedes the earlier Enhanced double-frame experiment. Final Enhanced generation/edit prompts are `design/nft-metadata/enhanced-single-border-prompts-v4.json`; v1-v3 evidence remains historical. The final PNG library still has72 variants, not additional NFT positions.

Read-only contract answer: `ZZZVault._join` accepts one-sided input of a configured pool token and invokes `_balanceUsing`; `ZZZStrategy._plan` derives the swap ratio from the actual price/range requirements rather than a fixed50/50 division. Slippage, net-value and deployed-LP checks can revert an unsuitable deposit. The current candidate rejects native ETH and hooked pools; the selected Pons pool is unsupported. USDC-to-ZZZ/ETH arbitrary-input routing is not implemented. No Solidity modification or new contract test run was implied by this answer.

Final local verification after single-border v4: 33 Node tests passed; 75 HTML IDs/five routes and all72 artwork/metadata pairs checked; static build155 files, source/build SHA256 matched,148 local HTTP checks passed, private notes404. All36 revised Enhanced/Singularity assets retain unique hashes. Representative card-size comparison and final corner-refinement images visually checked; no browser console errors. Temporary QA tabs/server were closed; the main4173 preview remains available.


### Commun Enhanced border correction (v5)

The user approved Rare and Legendary borders and requested correcting Commun Enhanced only. Replaced the six Commun Enhanced PNGs with a clean, continuous single bright outline matching each palette's approved Rare Enhanced frame. Removed detached corner inserts and extra inset rails; preserved the Commun egg and stronger seam lighting. All other 66 artwork PNG hashes are unchanged, including every Rare, Legendary and Singularity image. The double frame remains exclusive to Singularity.

Built-in image_gen edits; exact prompts and provenance: `design/nft-metadata/commun-enhanced-border-prompts-v5.json`. Updated local website manifest to v5. Verified all 72 unique PNGs and metadata pairs, source/build hashes for 155 build files, and 148 local HTTP checks. Visually verified all six corrected images in the Artwork gallery. No JavaScript, economics, Solidity, commit, push or server update. This pass remains locally only.

### Overview NFT-to-LP card redesign

The user requested replacing the diamond glyph, removing the extra LP ATTACHED badge, highlighting Permanent LP attached, and making contributions and perpetual holder fee rights clear visually. Latest refinements: center PoPL #444 above its actual egg artwork, show the LP label/value below, display a ZZZ/USDC-to-permanent-LP flow with an infinity cue (Trading fee rights. No expiry. For whoever holds this NFT.), and present principal permanence as a matching third lock-icon row beside the hold/transfer explanations. Claims remain funded-only; principal cannot be redeemed. The illustrative NFT image, state label and enlargement target track the current #444 allocation/evolution. No new artwork files or economic changes.

Verified desktop appearance, 390px layout with no page/flow/capital overflow, three matching rights rows, correct artwork keyboard enlargement and no browser errors. All 33 existing Node tests passed for this app change; final source checks, 155-file build/source hashes and 148 HTTP checks passed after the last markup/CSS refinement. Local preview at4173 updated. No commit/push, Ubuntu update, Solidity change, real transaction or deployment. The current local-only scope continues.


## Latest contract gap hardening - 2026-10-16

This supersedes historical notes saying atomic original-source entry and source-oracle-independent custody close are missing. The user requested further improvements, configurable future activation assets/routes and secure future custody movement. Current code remains an undeployed local candidate; the website/server are unchanged at simulated release 8c0b93523d914644d440129d74745c9e12f8e08a. No commit, push, public deployment, signing or real transaction is implied by this development pass.

- Registry creates immutable ZZZActivationAssets and new ZZZActivationEntry children, without changing the 17 sealed-module inventory. Entry accepts admitted pair tokens, exact native wrapping for the actual native pool or reviewed append-only typed single-hop V3 conversion into a pair currency. Source ingress is exact and valued by the real Oracle; current NFT ownership, exact Vault calldata, amounts and original USD value are bound through a private short-lived context. No arbitrary executor/recipient, supplied USD claim, NFT custody, permit or rescue exists. Conversion and LP deployment share one 99% marginal-LP floor, with 100 USD original-source activation minimum and gas separate. Top-ups retain the same budget and existing pool minimum.
- Callback review found and fixed an approval/context boundary: context is armed only after the exact Vault approval and ownership recheck, immediately before the guarded Vault call; it is deleted before allowance cleanup. Registry grants original-source valuation only to canonical Vault calls, and an armed mismatch reverts rather than reverting to cheaper pair valuation. Activated events identify the actual NFT owner, not Entry.
- PositionStatus.Parked is appended as 6, preserving 0..5. A sealed globally paused Migration request is timelocked and binds exact bucket/pool/LP/shares/contribution/local location/custody epoch/nonce, reviewed ordered-token close minimums and narrow execution deadline. Venue fees are harvested separately; only close-returned principal deltas can meet minimums, excluding old idle, donations and compound reserves. Principal remains inside Vault. Parking omits price and creator-inbox reads; actual tokens/wrapper/venue must still work.
- Parked NFT shares, permanent membership, royalties, current-owner claims and transfers persist. Canonical funded dust and external receipts remain supported, keeper LP maintenance stays off, and current LP marking is explicitly unavailable. Resume requires ordinary fresh-price/deployment guards and the same ordered currencies. Separately approved parked migration can depart without restoring the old source price, retaining transport readiness, delays, exact funds, custody epochs, destination checks and remoteSettled liabilities. No hidden administrator withdrawal, generic proxy upgrade or universal external-failure recovery guarantee exists.
- Mechanical module-address lookup refactoring creates deployment headroom without caching authority, changing the compiler or weakening guards. Current production build has 23 standard module/helper objects and 29 source bindings; Vault runtime/init 24,056/24,809 bytes (520 runtime margin), Migration 24,252/24,764 (324 margin), Registry 11,933/33,088 with both children embedded. Initcode objects exclude final constructor arguments.
- Production inventory now requires gross_source_input economics, independently reviewed immutable Entry bindings/original-source/aggregate-loss/context/route-history evidence and parking rehearsal evidence. Production example intentionally remains blocked; authorities, reviewed ZZZ/USD and uptime feeds, actual supported VRF/recovery, funded USDC route, combined actual USDG/Pons execution, creator terms, IPFS provider/pinning, hosted projections/wallets, Testnet operations and external audit/remediation remain open. Real bridge wrappers/backing are still needed before enabling migration.

Fresh verification receipts belong in reports/gap-hardening/; previous release-progress 430/478/22/28/17/210 receipts and earlier reports retain their exact source snapshots. The previous 210-entry Slither review is preserved byte-exact at reports/history/slither-review-pre-gap-hardening.json. Current work is saved locally and uncommitted. Read docs/ACTIVATION_ENTRY.md, docs/CUSTODY_PARKING.md, docs/IMPLEMENTATION_STATUS.md and the NOT APPROVED release checklist.


Final local verification for this gap-hardening snapshot: 488 offline Solidity passes, zero failures, two expected opt-in fork setup skips (490 total, 37 suites); 488 portable Python passes from 492 cases, with four unchanged Unix-only cases reserved for supported Ubuntu. All 23 normal object size gates and all 29 production source/compiler bindings pass. Fresh internal Slither reviews 220 findings: 128 false positives  / 53 accepted risks  / 39 informational  / 0 unresolved review entries; two analyzer runs, 43 matcher cases and nine mutation rejections pass. Prior 210-entry review remains byte-exact. One actual hardened-runner execution passes 20 selected native/Pons fork tests plus nine secondary hookless tests, zero failures/skips, with source/closure bindings unchanged before/after at Robinhood 4663 block 88,544,093 hash 0xc44dc8c95c6011b991312179f532935c2d94e4f21b84899d23896fd0fe01d490. Authorities/VRF/USD calibration remain explicit fixtures; actual stable-to-Pons routing and live services are not thereby qualified. Evidence: reports/gap-hardening/README.md and verification-summary.json. The first integration-test expectation overlooked one raw reward-index rounding unit; it now expects 90e18-1 and checks backing/liability of the remaining unit; no production behavior changed for that repair. Uncommitted, undeployed; no website/server changes.


## Git publication handoff - 2026-10-16

The user explicitly requested committing and pushing the verified contract work, including project notes and todo/release checklists, to ABEF/AAA. Earlier uncommitted/local wording records the verification-time state before this publication. The source-bound receipts remain unchanged; current publication status and commit identity are established by Git HEAD and origin/main. No smart-contract deployment, signing, real asset movement or website/server change is authorized by this request. Exact-commit Ubuntu CI must be checked independently; local evidence is not a claim of a green published workflow or production approval.

## Central Todo location - 2026-10-16

The user cancelled the website Todo page before publication. The website was restored to its clean previously deployed revision. The central GitHub task list is now root `TODO.md`, generated from `docs/project-todo.json`; maintain it for every task/fix/decision/milestone and follow `docs/TODO_WORKFLOW.md`. Detailed implementation/release evidence stays in its existing documents. Keeper recovery hardening is a separate local candidate: missing-state and nonce guards, balance checks, health/log output and explicit unused-signer initialization; publication and operating rehearsals remain open.

## Keeper security review follow-up - 2026-10-16

Current keeper hardening adds explicit unused-signer bootstrap, strict live state/nonce/receipt anchors, qualified fee-policy gates, private runtime files, RPC validation, revert cooldowns, structured health/errors and bounded service restarts. No public transaction or contract deployment occurred. The local Python workspace passed 602 tests; five Unix cases remain separately scoped to Ubuntu verification. See `reports/keeper-recovery/REVIEW.md` for source-specific findings and open operating gates.

## Published keeper verification - 2026-10-16

Keeper/Todo commit `3db782b087d5add2327f519030055d288d9d6512` is pushed. Exact-commit Ubuntu keeper verification (run 38956992156) passed 183 tests with zero failures/skips and systemd unit validation; Todo consistency run 38956992065 passed. The local broader workspace passed 602 Python tests with five Unix cases separately covered by Ubuntu. The keeper changes are published; other pre-existing Solidity/frontend development remains uncommitted and must not be silently discarded or included. The website is clean at its previous deployed revision, with no Todo page. Read `reports/keeper-recovery/REVIEW.md`; production operating gates remain open.


## Keeper staging handoff - 2026-10-16

The user selected the existing Ubuntu website host for isolated keeper rehearsals. The stage is running under zzz-stage in /opt/zzz-keeper-staging and /var/lib/zzz-keeper-staging, using only an isolated Anvil chain 31337 on 127.0.0.1:18545 and disposable test ETH. Runtime source 089d391c1689c2036db518c7a9705989896a14d8 passed 209 Ubuntu safety tests and 14 process rehearsals. Server process/crash/restart, off-host snapshot round-trip restore and forced-command monitoring tests have evidence in reports/keeper-rehearsal/. Website release/content is unchanged.

A five-minute local observer exports snapshots and health through read-only SSH. The popl-staging-health chat heartbeat reads every 30 minutes and saves off-host copies; desktop downtime creates observation gaps, so this is not independently hosted 24/7 production monitoring. Credentials remain outside Git. Multi-day soak is underway, not passed. Keep actual Robinhood services, fee/RPC qualification, Testnet operation, independent audit and authority decisions open. See docs/KEEPER_REHEARSALS.md for the service boundaries and stop procedure.

## NFT ownership/accounting audit handoff - 2026-10-16

The user's comprehensive prompt was challenged, corrected and executed; see
reports/nft-rights-audit/REVISED_PROMPT.md and REVIEW.md. Existing current-owner
claims, shared LP identity, funded 80/10/5/5 and separate royalty weights were
already implemented. New tests cover all 1,000 payouts, receiver/operator/sale
ordering, buyback rollback/retry and stateful LP/royalty conservation. The
VERIFICATION.md report distinguishes fresh evidence from unchanged-source prior
Slither/fork receipts, and records first-attempt/test-harness corrections.

The prior local four-bucket safeguard is retained: one initial shared LP still
serves the whole collection. Cross-review corrected actor aliasing and cold-gas
getter ordering in tests; it did not discover a new reward-theft exploit.
Destination capacity reservations, admitted-token liveness/dust policy, actual
routes/services/authorities/creator terms, sustained operating qualification,
wallet integration and independent audit remain gates. No public transactions,
website changes or keeper/staging changes are part of this audit.

Publish only the reviewed Solidity/capacity/test/evidence and checklist scope.
Pre-existing frontend/quote/process-runner and artwork work remains separate;
preserve it. Git HEAD/origin establish publication; do not infer publication of
all local Python changes from the broader local test count.


## Security audit workstreams - 2026-10-16

The central Todo now tracks seven security workstreams with acceptance criteria
in docs/SECURITY_AUDIT_PLAN.md: governance/sealing, shared accounting, ownership
and allocations, oracle/keeper economics, dependencies/backing, whole-protocol
recovery and cross-contract/infrastructure security. These are release work,
not an assertion that independent audit is complete. The split is currently
fixed; configurable percentages are only a risk/benefit question, not an approved
change. Permanent home-chain loss has no canonical NFT/reward-ledger recovery;
LP migration alone does not solve it. Decide this architecture before sealing.

## README organization - 2026-10-16

The README is the project entry point: short purpose/status, adjacent central
Todo and implementation-status links, then Smart contracts / Backend / Frontend
responsibilities. Keep lifecycle and economic rules in their own sections rather
than repeating them in architecture. Group keeper runbooks under operations;
link current verification and detailed reports instead of repeating historical
test-count narratives. Preserve clickable task/file links and explicit release,
sealing and canonical home-chain recovery boundaries.

## One task ledger and separate release approval - 2026-10-16

The user requested consolidation of the three overlapping checklist pages.
TODO.md, generated from docs/project-todo.json, is the only task-status list.
Its 38 existing IDs and statuses are preserved; detailed release requirements
now live in expandable acceptance criteria under their owning tasks. Keep the
Smart contracts / Backend / Frontend order and clickable related-file titles.
All 50 previous release requirements and distinct implementation-list details
were mapped, including creator sampling gaps/rounding and production NFT labels.

docs/IMPLEMENTATION_STATUS.md is a feature/evidence reference, with published
source distinguished from local unpublished wallet/quote/process-runner work.
docs/RELEASE_CHECKLIST.md is a short exact-release approval record, NOT APPROVED,
not another task list. Preserve existing filenames/compatibility anchors.
Update only the central ledger for progress; update references for behavior or
evidence changes and the approval record for release scope/reviewer decisions.
See docs/TODO_WORKFLOW.md. Historical audit reports keep their original scope.
This documentation change does not publish the unrelated local code candidate,
deploy contracts, change the website or approve real funds.
