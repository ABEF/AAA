# Feature and evidence reference

Reviewed 2026-10-19; the architecture repair and evidence were first recorded in
`4fbd4c0`. The user subsequently requested integration into `main` and use of
`main` for future work. Check the current Git revision for publication identity.
The contracts remain undeployed on public networks and the public website remains a simulation.
This candidate includes same-chain canonical handoff, local migration-budget and
keeper lifecycle changes. Exact publication is established by Git HEAD and origin/main.
Implemented means the behavior exists in source; it does not mean production
services, deployment or independent audit are approved.

**All task status, remaining work and acceptance criteria live in the
[central Todo](../TODO.md).** This page describes candidate capabilities and their
evidence. The [release approval record](RELEASE_CHECKLIST.md) records the final
decision for an exact release, not development progress. Creator-dependent questions
are grouped in [Creator tasks / ZZZ team](../TODO.md#creator-tasks--zzz-team);
recording them does not implement a feed, payment agreement or live route.

## Per-client API capacity and proxy boundary

Both read/unsigned-preparation CLI services now enforce concurrent and separate
read/preparation rate budgets per client IP, with a bounded table and fail-closed
proxy identity/origin validation. A client cannot occupy all four default workers;
disconnects retain their lease until started work finishes. No new signer, result
cache or economic behavior is introduced. The reviewed Nginx candidate overwrites
client identity, strips arbitrary headers, limits aggregate ingress and exposes
only the intended read/preparation routes without retries.

[Scoped evidence](../reports/api-admission/VERIFICATION.md): 50 affected Python
cases across an initial 47-case run and three supplemental cases, plus 22 actual
Nginx/loopback assertions and sanitized-log verification. These are local tests,
not a new full regression or Linux/TLS/provider qualification. Shared NATs and
multiple hosts require explicit capacity planning. See [operator procedures](API_INGRESS.md)
and the [central hosting task](../TODO.md#task-host-services).

## $5 top-ups and NFT-owned earned totals

Entry and the immutable Vault helper enforce $100 activation / $5 increases in
original oracle-valued input, retaining any higher configured pool minimum, the
99% marginal deployed-LP requirement and separate gas. Backend and new preview
actions use the same floors; legacy saved preview history is preserved. See
[configuration](CONTRIBUTION_MINIMUMS.md) and [operator procedure](OPERATOR_MANUAL.md#contribution-minimums).

NFT cards/details show own earned 24h/all-time totals (individual LP + equal
collective allocation + royalties), separate from remaining claimable. The [calculation audit](../reports/topup-and-reward-review/REWARD_CALCULATION.md) traces all three streams, claims, conversions and missing-price/overflow handling. The compact
regular-weight row is below centered attached LP; gross fees are removed from NFT
cards. Current-price local totals require matching NFT/chain/block and all priced
components. Missing history/prices remain unavailable. The original saved demo
has no dated net series, so its 24h total is unavailable rather than fabricated.
Optional local history failure no longer hides healthy core balances; terminal
work limits/core failures retain their guards, and dormant reads skip history.

[Scoped verification](../reports/topup-and-reward-review/VERIFICATION.md) records
91 fresh Solidity passes, 74 distinct Python and 102 distinct JS cases across
documented runs, plus normal compiler sizes and browser checks. The
[internal daily review](../reports/topup-and-reward-review/REVIEW.md) is not an
independent audit or live qualification. Existing local deployments and public
services were not upgraded; actual routes/feeds/load qualification remain open.

## Bounded concurrent API and website resilience

Read and unsigned preparation listeners now admit independent spawned requests
in a finite pool (default four workers / eight HTTP connections per process).
Absolute ingress and connection deadlines, bounded headers, explicit overload,
sanitized disconnect/error handling and failed-cleanup quarantine complement the
existing confirmed-state/RPC budgets. Main website state uses a single immutable
exact-version preview cache and expires suspended intents. Its local confirmation
adapter checks finite bounded expiry, elapsed preparation and current context.
[Scoped evidence](../reports/concurrent-services/VERIFICATION.md) records 47 affected
Python and 90 JavaScript passes plus a source build/browser check. These are local
admission/isolation checks, not production load or multi-device signing approval.
The [operating procedure](CONCURRENT_SERVICES.md) covers capacity and recovery.

## Single contribution-pool policy

The registry enforces at most one `depositsEnabled` pool. Its getter/event expose
the selection; dependency-free deposit stops clear it, full validated config
selects a replacement, and an atomic governance batch rolls back on failure.
Historical pools, maintenance and migration are preserved. Initial production
target remains reviewed ZZZ/ETH, not an arbitrary admitted venue. This is source
implementation, not a deployed restriction; see [scoped evidence](../reports/position-summary/VERIFICATION.md)
and [operator procedure](OPERATOR_MANUAL.md#one-contribution-pool-at-a-time).
Verification retains 97 source-matched affected passes plus 14 corrected-suite
passes; normal Registry object sizes pass. No deployment or independent approval.

## NFT position presentation

The [gallery/reward-feedback follow-up](../reports/website-polish/VERIFICATION.md)
adds single-row artwork traits, removes redundant pool UI, and supplies one
idempotent sample reward receipt for demo claim testing. Confirmed higher-tier
contributions synchronize the supplied ACTI/EV sounds with the image reveal; local
mode waits for receipt and fresh increased LP. The redundant claimed-total frame
is hidden, while lifetime claim accounting and earnings remain intact.
These features do not implement live revenue funding or new contract operations.

Fixed royalty weight now appears as an artwork trait. Cards retain attached LP and active cards show a single
claimable LP-plus-royalty total; the breakdown separates liquidity, current
reward components, earnings history and lifetime claims. The local adapter sums
matching currencies exactly and preserves unavailable values. Dormant reward
sections remain hidden. [Scoped verification](../reports/position-summary/VERIFICATION.md)
records 35 focused JS passes and a static build/browser check. No backend,
contract, transaction behavior or operator procedure changed.

## Main website interaction state

The default website now has per-NFT/mint action tracking, overlapping-batch guards,
atomic latest-state preview updates across tabs, wallet context cancellation and
session-only connection restoration. Dormant reward/claim sections are hidden;
active cards separate Claim and Grow attached LP. Inline form feedback and loaded
artwork continuity incorporate the lessons from local testing. These changes are
in the main website source, not just the Anvil adapter. [Scoped verification](../reports/frontend-state/VERIFICATION.md)
records 53 affected JavaScript passes and two-tab browser checks. The default
website still simulates financial actions; production wallet/receipt recovery and
multi-device service qualification are not supplied by these UI locks.

## Disposable local browser integration

The [original website now has a local contract mode](LOCAL_WEBSITE.md): confirmed
ownership, current LP, individual/collective earnings, raw royalties and lifetime
claims, plus mint/approval/Entry/top-up/transfer/bounded combined-claim confirmations.
It retains the artwork and layout. Missing prices/data do not become zero or demo
holdings. [Website integration evidence](../reports/local-website/VERIFICATION.md)
records the scoped client/server and local transaction checks. This uses the
launcher's disposable accounts, not production browser-wallet signing; the public
website remains a simulation. No Solidity or public services changed.

Local NFT cards retain their revealed rarity multiplier (×1/×2/×3) while dormant,
with gray styling until activated. The display no longer substitutes effective
accounting weight zero for the fixed rarity trait; unrevealed traits stay unknown.
Dormant detail views omit the claim action while preserving activation and transfer.

The local UI now omits all inapplicable dormant reward/history rows, separates
Claim from Grow attached LP, and preserves labeled artwork while refreshed
financial data is pending. Confirmed evolution changes crossfade only after the
new artwork loads, with reduced-motion support. Wallet selection is delivered
by the fast session handshake and persists within the same disposable session.
Single-flight refresh and bounded explicit-busy read retries preserve write
idempotency. This improves local concurrent access, not production load capacity;
multi-user wallet/service qualification remains open.

The [local stack](LOCAL_TEST_STACK.md) deploys the unchanged core to an owned Anvil
process and exercises confirmed reads, finite NFT mint/reveal, Entry activation,
top-ups, funded LP/royalty accounting, governed rebalancing, transfers and combined
claims in a separate browser panel. Test-only venue/feed/VRF boundaries are explicit.
The local action service rejects malformed inputs, old revisions, wrong owners
and invalid contribution states before approvals; session-scoped operation IDs
prevent duplicate execution after response loss. Uncertain submissions stop new
actions. [Evidence](../reports/local-stack/VERIFICATION.md) separates the original
journey from the expanded 39-assertion integration and 35 launcher/HTTP checks.
This does not close production wallet integration,
Uniswap/Pons routing, live prices/randomness or operating qualification.

## Current candidate capabilities

| Area | Behavior available in this source candidate | Reference |
|---|---|---|
| Mint and identity | Dormant mint costs exactly 0.05 ETH and adds no LP. The fixed 1,000 supply uses canonical hashed token IDs, separate mint ordinals and exact eventual 600 Commun / 300 Rare / 100 Legendary quotas. Ordered VRF draws select existing artwork without replacement; no administrator reroll exists. | [NFT metadata](NFT_METADATA.md), [Vault](../src/ZZZVault.sol) |
| Activation and additions | Immutable Registry-created Entry binds the original source value, current owner and exact Vault call. Activation starts at $100 gross value; conversion and marginal LP deployment share a 1% execution/undeployed budget, with network gas separate. Governed asset and route admission does not itself qualify a live route or price feed. | [Activation Entry](ACTIVATION_ENTRY.md), [asset policies](../src/ZZZActivationAssets.sol) |
| Mint and claim transaction preparation | Typed 0.05 ETH mint and 1-32-operation LP/royalty claim drafts verify current lifecycle and exact owner/currency selection, simulate at one canonical hash and return separate bounded gas estimates under an explicit reviewed policy. Direct work budgets, short expiry and opt-in supervised HTTP; default GET-only. No signer, broadcast or live browser. | [Runbook](FRONTEND_TRANSACTIONS.md), [scoped evidence](../reports/wallet-preparation/VERIFICATION.md) |
| Activation transaction preparation | Typed owner/source requests verify sealed bindings, assets/routes/feeds and simulate the full Entry call at one canonical hash. Actual budget/share/LP results enforce the 1% floor; exact final calldata, short on-chain deadline and separate reviewed network-gas estimate are returned unsigned. Missing allowance yields only an approval/reset step until confirmed. Both responses include current range, outside-range warnings and rebalance eligibility/cooldown; unknown keeper timing stays unavailable. Current NFT value stays separate from new LP. | [Preparation](ACTIVATION_PREPARATION.md), [range/timing evidence](../reports/dynamic-liquidity/VERIFICATION.md) |
| Shared LP custody | Many NFTs own nonredeemable shares of one physical LP per pool/strategy. Maintenance acts on the shared bucket. The cap is four permanently admitted/historical local identities, including unfunded reservations and imports; all 1,000 NFTs can share the initial pool. | [Architecture](ARCHITECTURE.md), [scale/capacity verification](../reports/nft-rights-audit/VERIFICATION.md#execution-gas-and-capacity) |
| LP revenue | Actual admitted receipts allocate 80% by LP shares, 10% equally among activated NFTs, 5% to the earning bucket's compounding reserve and 5% to buyback/burn. Rarity does not affect LP rewards. Documented raw-unit dust and receipt-time membership rules apply. Creator inboxes receive funds; they cannot enforce a creator's payment obligation. | [Economics](ECONOMICS.md), [external funding](EXTERNAL_REWARDS.md) |
| Royalties and claims | ERC-2981 requests 5%; actual eligible receipts use a separate immutable ledger at activated rarity weights x1/x2/x3. Current owners claim; unpaid balances follow the NFT. Direct ledger claims and an immutable 1-32-operation mixed claim router exist. Marketplace payment is not enforced. A pre-seal-bound converter batches already-earned balances into ETH (up to 32 NFTs, 1% loss cap, gas separate), retaining direct-currency claims. Optional-token outages defer only that currency's new members; recovery protects earlier receipts. Local evidence and live qualification are separate. | [Settlement boundary](ROYALTY_SETTLEMENT.md), [Claim router](CLAIM_ROUTER.md), [ownership review](../reports/nft-rights-audit/REVIEW.md#identity-and-ownership) |
| Artwork and metadata | Eight colors, 58 palettes and four patterns produce 2,784 evolution states for the fixed inventory. The approved Twin circuit routes replaces Vertical ribs in stable slot 3 (`ribs`); all 1,000 assignments and the other three patterns are preserved. [Scoped artwork checks](../reports/twin-circuits/VERIFICATION.md) cover the 696 replaced states and metadata label. Current marked LP value selects the stage; a market decline can lower it without removing activation rights. The strategy's spot/oracle guard makes invalid marks unavailable. Bounded ERC-4906 notifications and an optional keeper watcher exist. The prepared artwork bundle is not a published immutable CID. | [Metadata](NFT_METADATA.md), [artwork publication](ARTWORK_PUBLICATION.md) |
| Venue and recovery boundaries | The selected native-ETH/Pons adapter separates venue keys from WETH accounting and rejects unrelated native/hooks. Pause, governance-approved asset/wrapper/sequencer policies, close-only custody parking and guarded resumption exist. They do not guarantee recovery from every external dependency failure. | [Selected market](ROBINHOOD_POOL.md), [parking](CUSTODY_PARKING.md), [recovery model](CHANGE_AND_RECOVERY.md) |
| Confirmed read API | Schema-2 deployment pins, canonical lifecycle checks, protocol status, current NFT ownership and funded LP/royalty balances. Current local pool/LP identity and share denominator are verified; cumulative gross contribution is separate from current marked NAV. Locked NFT/wallet projections fail closed. Final canonicality, confirmation-depth and freshness checks are published. | [Read API](FRONTEND_API.md), [current-value integration](DYNAMIC_LIQUIDITY.md), [lifecycle](FRONTEND_LIFECYCLE.md) |
| Wallet inventory and lifetime claims | Indexed ownership and lifetime LP/royalty claims across complete configured same-chain predecessors, including past owners and historical assets. Matching retirement/activation records authenticate each handoff. Incomplete or invalid lineage never produces partial lifetime sums; current claimable funds are unchanged. | [History](FRONTEND_HISTORY.md), [predecessor claims](FRONTEND_LINEAGE.md) |
| Royalty reporting and conversion history | Opt-in reviewed-ledger profile exposes ETH/source claimable balances, per-currency eligibility and pinned converter enable control. Failed currency reads are unavailable; core/lifecycle/history/freshness and request limits remain strict. Exact conversion events and complete configured same-chain predecessors preserve conversion credits separately from actual lifetime claims. Earned history uses the separate optional profile below; live consumers remain unqualified. | [API/operator guide](ROYALTY_REPORTING.md), [scoped evidence](../reports/royalty-reporting/VERIFICATION.md) |
| Processed earnings and current USD | Optional collection and per-NFT all-time/24h replay reconstructs actual LP individual/collective allocations and rarity-weighted royalties, including deferred cohorts and complete configured same-chain predecessors. Conversion/payout/import events are not new income. Optional reviewed Oracle/feed pins value original earned currencies at the current confirmed price; missing prices are null. | [Configuration and semantics](EARNINGS_HISTORY.md), [186-test scoped evidence](../reports/earnings-history/VERIFICATION.md) |
| Replacement holder preflight | Read-only confirmed-block owner/code inventory with bounded pages, complete ordinal coverage checks and explicit contract/delegated-account review flags. A frozen rescan and exact escrow release/claim rehearsals remain operator requirements; the tool never authorizes migration. | [Procedure](HOLDER_PREFLIGHT.md), [evidence](../reports/holder-preflight/VERIFICATION.md) |
| History ingestion comparison | Read-only current/predecessor epoch windows compare all configured emitters against a separately reviewed RPC with exact cursor, header and raw-log checks. Bounded work, discrepancy digests and exclusive output; the indexer adds an ordered block/log index without changing accounting. Provider agreement is not proof of full coverage or finality. | [Procedure](HISTORY_AUDIT.md), [41-case scoped evidence](../reports/history-audit/VERIFICATION.md) |
| Revenue measurement tools | Exact time-weighted and fee-weighted sampled active-liquidity proposals and receipt/dust reporting exist. Creator approval, complete hook observations, actual earnings ingestion and feed/service qualification remain separate requirements. Measurement cannot create unfunded claimable rewards. | [Revenue measurement](REVENUE_SHARE.md) |
| Website preview | The separate website demonstrates artwork, portfolios, minting, activation and LP/royalty claims with example data. These are simulated flows; live wallet transactions and backend integration remain separate tasks. | [Preview](https://popldemo.0xwave.com/), [frontend tasks](../TODO.md#frontend) |
| Keeper and operating tools | Bucket discovery, guarded maintenance, serial budgets, durable pending recovery, confirmed receipt/nonce checks, metadata watching, health checks and exclusive recovery snapshots exist. Preparation defers new rebalance/compound/buyback work while permitting drains. A separate strict canonicalState getter blocks every new submission during frozen/importing/retired/cancelled states; receipt recovery continues. Older deployed staging code is unchanged. | [Recovery runbook](KEEPER_RECOVERY.md), [handoff evidence](../reports/canonical-handoff/VERIFICATION.md) |
| Future migration | Governance-approved routes and whole-bucket migration/parking preserve canonical NFT rights and funded-liability barriers. Reservations now permanently admit capacity; aliases/returns are idempotent and None-state consumers skip unfunded entries. Remote admission proof and real provider qualification remain separate. Canonical NFTs and claim ledgers do not automatically migrate with LP custody. | [Migration source](../src/ZZZMigration.sol), [recovery model](CHANGE_AND_RECOVERY.md) |
| Governed range application | A governance-approved width change that differs from deployed ticks at the recorded center can trigger ordinary rebalance at a flat price. Cooldown, fresh prices, execution minima, aggregate budget and idle cap remain. Successful replacement clears the mismatch; small price drift or identical rounded ticks do not cause policy churn. Backend context distinguishes price and range triggers. | [Range policy](RANGE_POLICY_UPDATES.md), [verification](../reports/range-policy/VERIFICATION.md) |
| Local execution budget | Ordinary rebalance and atomic same-ordered-pair movePool/resume uses an immutable Vault-created helper. It values principal/attributed idle before harvest, adds only exact released compound, and applies the same initial fresh price/decimal vector after close, balance and mint. Retained LP plus attributed idle must be at least 97%, with the existing 5% idle ceiling under that vector. Gas is separate; activation/top-ups retain 1%. Different-pair and asynchronous bridge enforcement is not supplied. | [Budget helper](../src/ZZZMigrationBudget.sol), [Vault](../src/ZZZVault.sol) |
| Canonical preparation | The existing governance controller can announce and cancel an exact notice on the canonical controller. New economic work and protocol configuration stop; transfers, direct/batch claims, ordered reveal, fee settlement, incoming delivery, funded Reward/ACK sends and exact parking/plan-cancellation drains remain available. Trailing guards roll back new work if a callback starts preparation. Guardian pause and governance unpause remain distinct. The notice grants no successor authority and does not freeze/export/import rights or prove satellite shutdown. | [Controller](../src/ZZZAccessController.sol), [canonical design](CANONICAL_MIGRATION_DESIGN.md) |
| Same-chain canonical handoff | Separate fixed coordinator/companions capture receipts, freeze ownership and accounting, export/import complete exact domains, move classified backing, and atomically retire the source/activate one successor. Bounded relay operations, fully restored abort and immediate-successor late forwarding exist. All mints must be revealed, local buckets parked and legacy bridge history unused. Imported successors cannot initiate legacy v3 principal bridging. | [Implemented boundary](CANONICAL_HANDOFF.md), [coordinator](../src/ZZZCanonicalHandoff.sol) |

The [component assessment](../reports/nft-rights-audit/IMPLEMENTATION.md) gives
module-level boundaries. All remaining qualification, implementation and decision
requirements are maintained once in the [Todo](../TODO.md), including the
[migration gate](../TODO.md#task-destination-slots) and
[canonical migration requirement](../TODO.md#task-security-chain-recovery).

## Independent pool and mint controls

`PoolRegistry.disablePool` restricts an admitted pool without token/price/venue
reads; flags can only be cleared. Reopening retains full admission checks.
`NFT.setMintPaused` independently blocks new mint/request creation, including
callback-time pause rollback, while existing rights and pending reveals retain
their own guards. Governance controls both with no delay; lifecycle locks remain.
The API reports the separate mint switch at its confirmed snapshot. See
[operator procedures](OPERATOR_MANUAL.md) and [scoped evidence](../reports/operator-controls/VERIFICATION.md).
These candidate features require updated deployment/runtime review; they do not
retrofit sealed binaries or qualify actual operating services.

## Operator procedures and service safety

The [operator manual](OPERATOR_MANUAL.md) covers source-backed management calls,
roles, range and asset changes, pool retirement, emergency containment, restart,
recovery and immutable boundaries. [Maintenance rules](TODO_WORKFLOW.md) require
updates whenever management behavior changes; it is not another Todo.

The API now bounds request-wide RPC/history/preparation work and uses supervised
read-only child workers in its HTTP entry points. A confirmed mint-readiness view
separates original provider fulfillment from ordered finalization. Neither this
observation nor the manual qualifies a live provider, hosted service or successor.
The selected randomness policy is provider qualification plus draining existing
draws before replacement, with no reroll/carry mechanism. The 3% maintenance cap
remains per operation; no cumulative cap was added. See [scoped verification](../reports/api-work-limits/VERIFICATION.md).

## Evidence and its limits

[Royalty reporting verification](../reports/royalty-reporting/VERIFICATION.md)
records 138 affected Python passes and a separate 20-case supplemental run.
Earlier new test bodies and production backend changes were unchanged between
runs. Forty current Solidity source hashes match the prior royalty build;
ten getter ABIs and all 26 added schema entries match its compiler artifacts.
No unchanged Solidity regression/build was repeated. Live API/website operation,
full revenue/USD reporting and independent audit remain unqualified.

The [review of October 18 changes](../reports/daily-security-20261018/REVIEW.md),
completed October 19, covers 13 published commits through `485a089`. No new
unauthorized principal withdrawal or hidden recipient was identified; this is
not production approval or a guarantee of no vulnerabilities. It records the
ordered-VRF/handoff dependency, successor escrow compatibility, immediate
governance trust and per-operation loss limits. A new synthetic expiry
reproduction demonstrates continued API work after expiry with safe final
rejection. The subsequent [API work-limit remediation](../reports/api-work-limits/VERIFICATION.md) adds shared deadlines/RPC budgets and supervised request termination; live hosting qualification remains open. Existing
78 build/source bindings matched; unchanged suites were not rerun.

[Immediate governance](GOVERNANCE.md) supersedes earlier delayed-operation
behavior: zero constructor/single/batch scheduling delay and no additional migration
wait. Existing roles, exact-call/replay checks and all target safety checks remain.
Read [current scoped evidence](../reports/immediate-governance/VERIFICATION.md);
older timelock tests retain their historical source scope.


A subsequent [read-only USDG route observation](../reports/activation-route-observation/VERIFICATION.md)
verified actual feed/token/router reads and four conversion quotes at one pinned
block. It does not qualify complete activation, production price policies, RPC
reliability or gas. The [integration campaign](INTEGRATION_CAMPAIGN.md) distinguishes
read-only observations, local forks and operator-run public transactions; no public
transaction campaign has run. Production source and prior test receipts are unchanged.

The separate [local $1 rehearsal](ONE_DOLLAR_REHEARSAL.md) generates a new build
outside the repository and changes the copied Entry/budget activation floors only,
with local-chain constructor guards. Production source, $100 activation, 0.05 ETH
mint, production transaction preparation and the website remain unchanged.
[Rehearsal evidence](../reports/one-dollar-rehearsal/VERIFICATION.md) identifies
the exact generated source and focused results. These are mock-venue local tests,
not a deployed contract or qualification of real $1 Pons execution. Defects exposed
by rehearsal must be fixed and regression-tested in production where applicable;
the reduced test minimum must never be promoted as such a fix.

The latest [range-policy verification](../reports/range-policy/VERIFICATION.md)
binds the new stateless Strategy trigger and backend cause/eligibility fields.
Approved width changes no longer have to wait for price movement; cooldown and
all ordinary execution guards still apply. This is scoped verification, not a
new full regression or production approval. The [design](RANGE_POLICY_UPDATES.md)
states authorization, current-position/configuration semantics and limitations.

The preceding [dynamic-liquidity verification](../reports/dynamic-liquidity/VERIFICATION.md)
covers the current metadata price guard and ordinary-rebalance aggregate cap,
current-physical-LP API identity, original contribution separation and range/
eligibility warnings. Read [the accounting reference](DYNAMIC_LIQUIDITY.md) for
the source trace, numeric examples and API/website boundary. Its scoped checks
supersede older receipts only for the changed paths; they are not a complete
new regression or production qualification.

The [historical handoff verification record](../reports/canonical-handoff/VERIFICATION.md)
records 582 passing regression cases with two explicit opt-in fork setup skips,
fixed bridge fixtures and three cold-gas suites for its earlier source snapshot.
Its 34 focused handoff passes, 30 object gates, 141 configuration checks and
374-finding internal review retain that scope. The changed paths use the separate
dynamic-liquidity and range-policy evidence above; no full current-source regression is claimed.
The [continuation record](WORK_HANDOFF.md) describes remaining integration and
release work. Check Git HEAD and origin/main for publication. Earlier evidence remains historical and
does not verify its new lifecycle guards, helpers, codecs or custody extraction.
No existing staging service was upgraded. The [schema-2 read API](FRONTEND_LIFECYCLE.md)
checks canonical lifecycle and refuses locked NFT/wallet projections. The optional
[predecessor history](FRONTEND_LINEAGE.md) now authenticates configured same-chain
handoffs and combines lifetime LP/royalty claims without changing claimable funds.
Its [separate verification](../reports/frontend-lineage/VERIFICATION.md) records
91 passing API/lifecycle/history cases against the exact publication snapshot.
Archive-provider operation, independent peer-code review and website integration
remain release work. This is RPC/indexer verification, not a consensus proof;
the Solidity receipts above do not verify these Python changes.

The new preparation foundation and local same-pair execution budget change
production source. Development preparation tests passed ten cases with the real
timelock/NFT/Vault/reward modules and explicit mock venue, feed, randomness and
transport dependencies. The [keeper receipt](../reports/canonical-preparation/keeper/verification.json)
records 185 scoped portable tests with zero failures/errors/runtime skips; one
POSIX-only case is explicitly excluded from its 186-case inventory. This is
local evidence, not an updated server rehearsal or independent audit. The final
[source-bound verification](../reports/migration-safety/VERIFICATION.md) records
579 offline Solidity passes, zero failures and two intentional fork setup skips
across 49 suites; all 24 normal object gates and 30 production source bindings
pass. Fresh internal Slither review classifies 229 entries as 138 false positives,
46 accepted risks and 45 informational, with zero unresolved detector entries.
Coverage and nine targeted review/source mutation checks pass. The manifest
review also corrected a mixed-case helper/inbox alias, verified by four targeted
regressions after the earlier 126-test validator run. Vault and Migration have
only 17 and 30 runtime bytes free in that earlier snapshot; the new candidate
uses separate fixed companions and fresh normal size checks.
These receipts do not establish fresh target-chain fork, operating or audit approval.

The user selected verified source finality for cross-chain canonical activation,
with no multisig/manual override or signer-attestation fallback. Concrete
chain-specific verification remains unselected. The candidate supplies direct
same-chain receipt cutoffs, exact state/backing transfer, irreversible retirement
and late forwarding. Cross-chain authenticated readiness/finality, channel closure,
lineage/messages and transport remain pre-seal requirements; these cannot be
added to fixed code after sealing. Post-halt recovery remains deferred.

The [architecture review verification](../reports/architecture-evolution/VERIFICATION.md)
retains its earlier targeted reservation/switching, keeper, trust-boundary and
size/static checks. That source scope predates the new preparation/budget changes.
Older whole-Vault/static/fork receipts below remain historical.


- The [NFT-rights verification](../reports/nft-rights-audit/VERIFICATION.md)
  records 531 offline Solidity passes, zero failures and two intentional fork
  setup skips, plus 23 normal object-size gates and 29 production source
  bindings. The 1,000-NFT scenario and extended dual-ledger invariant use explicit
  local venue, authority, price and VRF fixtures.
- The same report identifies reused source-bound evidence: 33 prior fork cases
  (24 selected native/Pons and nine hookless) and 220 internally reviewed Slither
  findings. Those were not fresh runs in the NFT-rights review and are not an
  independent audit.
- [Keeper operating evidence](../reports/keeper-rehearsal/README.md) records
  runtime revision `089d391`, 209 Ubuntu tests and 14 local process rehearsals,
  plus isolated server crash/restart and snapshot restoration. It does not prove
  a multi-day soak, production RPC/fees or physical host-loss/key rotation.
- The 628-pass portable Python receipt in the NFT-rights report covered a broader
  local working tree, including unpublished work. It is not evidence that those
  unpublished features exist in this GitHub revision. Exact-release CI and
  production approval belong to the [release record](RELEASE_CHECKLIST.md).

Historical reports retain their original revisions and assumptions; they are not
maintained as additional task lists.

## Local unpublished candidates

The local working tree retains older conversion-only quote hardening, bounded
fork-runner process/timeout cleanup, history-test and artwork drafts. Those remain
distinct from the published read API, complete activation preparer and the
[mint/claim preparer](FRONTEND_TRANSACTIONS.md). Earlier notes describing mint/claim
preparation as unpublished are historical. No saved draft qualifies a live service.

Publication/review and integration are tracked under
[unsigned actions](../TODO.md#task-unsigned-actions),
[activation quotes](../TODO.md#task-activation-quotes),
[read API](../TODO.md#task-read-api) and
[mainnet-fork qualification](../TODO.md#task-mainnet-fork).
No candidate signs, broadcasts or makes the simulated website live merely by
being saved locally.

## Moved task links

<a id="todo-to-turn-the-website-flows-into-real-transactions"></a>
Website transaction work is now maintained in the central
[wallet task](../TODO.md#task-wallet),
[unsigned-action task](../TODO.md#task-unsigned-actions) and
[activation-quote task](../TODO.md#task-activation-quotes).

<a id="todo-before-enabling-real-bridging"></a>
Future bridge work is now maintained in
[destination capacity](../TODO.md#task-destination-slots) and
[bridge operation](../TODO.md#task-bridge-operation).

<a id="todo-before-a-funded-initial-launch"></a>
Initial-launch acceptance and final approval are tracked in
[audit and release](../TODO.md#task-audit-release).


Local contribution review now exposes validation/progress/errors inside the dialog
and retains the acknowledgement across a confirmed approval only for the exact
same contribution. Entry still needs separate confirmation. Artwork pending badges
are scoped to the activated/topped-up NFT; financial snapshot guards remain global.

## Payout-currency audit boundary

[The claim-currency audit](../reports/topup-and-reward-review/ETH_PAYOUT_AUDIT.md)
found that the earlier revision's LP claims were source-token payouts. Royalty batch ETH conversion
does not cover LP rewards; native creator receipts are wrapped before allocation.
A read-only Anvil claim trace pays the original mock ERC20 plus ETH royalties and
leaves balances untouched. That pre-seal implementation gap is addressed by the
LP settlement candidate below; live qualification remains open. No unchanged
Solidity suite was rerun for this audit.

Contribution UI follow-up: four visible input choices (ZZZ/USDG/USDC/ETH), WETH internal only, dedicated contribution dialog and confirmed per-NFT evolution refresh. See [named local rehearsal](LOCAL_TEST_STACK.md#named-input-local-rehearsal). No production authority/procedure change; public routes, ETH-only LP settlement and hosting remain open.

## LP holder ETH settlement

The local candidate checkpoints earned individual/collective LP balances, converts through a dedicated fixed-ledger executor with a 1% maximum loss (99% oracle floor; gas separate), and credits native ETH to the same NFTs. Exact WETH unwrap, source-claim recovery, native claims, bounded keeper rotation, history/earnings reconciliation and native backing handoff are implemented. Verification covers 142 distinct affected Solidity cases across scoped runs and 33 local journey assertions, with focused backend/UI evidence. See [semantics and operating procedure](LP_ETH_SETTLEMENT.md) and [scoped evidence](../reports/lp-eth-settlement/VERIFICATION.md). Actual routes, latency/gas qualification and independent approval remain open.

## Local unsigned preparation contention - 2026-10-20

The website local adapter now waits with bounded retries when a portfolio refresh
blocks unsigned activation/mint/claim preparation. Only the explicit pre-handler
busy response is retried; account/state cancellation and draft expiry remain.
Actual submissions and ambiguous responses are not automatically repeated.
See [focused verification](../reports/local-preparation-busy/VERIFICATION.md).
No Solidity or backend behavior changed; production browser signing and
concurrent service qualification remain open.

## Local read and contribution update - 2026-10-20

A boundary-sampled monotonic clock removes per-check RPC overhead without dropping
initial/final freshness checks. The native fixture uses unchanged Entry for atomic
ETH; supported ERC20 uses exact replacement approval then Entry, with no automatic
reset. The UI retains confirmation continuity and fixes local activation at $100.
See [behavior and limits](LOCAL_WEBSITE.md#local-contribution-flow---2026-10-20) and
[scoped verification](../reports/local-contribution-flow/VERIFICATION.md).
Production venue/service qualification and fixed-$100 price/rounding policy remain open.


### Cross-browser local confirmations - 2026-10-20

Independent local wallet sessions reconcile newer unsigned drafts with confirmed
state instead of rejecting their older cached revision. Bounded retries preserve
expiry and account/session checks. Explicit stale submissions require new review;
ambiguous responses retain exact-operation recovery. [59 focused cases and scoped
local observation](../reports/local-wallet-concurrency/VERIFICATION.md) cover this
client change. Backend/production Solidity are unchanged; public wallet signing
and concurrent production operation qualification remain open.


### Local submission lock recovery - 2026-10-20

The exact `/action` pre-handler busy response now waits with the identical saved
operation ID and payload (30 attempts maximum within a 90-second request timeout).
This is the narrow exception to earlier notes saying submissions never retry.
Lost responses and ambiguous outcomes still require saved-intent recovery; state
changes after review still require a new review. Reload both browsers to pick up
the client fix; use Recover status for a saved pending intent. Do not clear session
storage, repeat a confirmed approval or restart/reset Anvil. No permissions or
contract changes. Reverting the client restores the immediate lock error without
undoing transactions. [64 scoped cases and actual lock probe](../reports/local-wallet-concurrency/VERIFICATION.md#submission-lock-follow-up---2026-10-20).
