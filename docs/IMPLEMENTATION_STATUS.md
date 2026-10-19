# Feature and evidence reference

Reviewed 2026-10-19; the architecture repair and evidence were first recorded in
`4fbd4c0`. The user subsequently requested integration into `main` and use of
`main` for future work. Check the current Git revision for publication identity.
The contracts remain undeployed and the website remains a simulation.
This candidate includes same-chain canonical handoff, local migration-budget and
keeper lifecycle changes. Exact publication is established by Git HEAD and origin/main.
Implemented means the behavior exists in source; it does not mean production
services, deployment or independent audit are approved.

**All task status, remaining work and acceptance criteria live in the
[central Todo](../TODO.md).** This page describes candidate capabilities and their
evidence. The [release approval record](RELEASE_CHECKLIST.md) records the final
decision for an exact release, not development progress.

## Current candidate capabilities

| Area | Behavior available in this source candidate | Reference |
|---|---|---|
| Mint and identity | Dormant mint costs exactly 0.05 ETH and adds no LP. The fixed 1,000 supply uses canonical hashed token IDs, separate mint ordinals and exact eventual 600 Commun / 300 Rare / 100 Legendary quotas. Ordered VRF draws select existing artwork without replacement; no administrator reroll exists. | [NFT metadata](NFT_METADATA.md), [Vault](../src/ZZZVault.sol) |
| Activation and additions | Immutable Registry-created Entry binds the original source value, current owner and exact Vault call. Activation starts at $100 gross value; conversion and marginal LP deployment share a 1% execution/undeployed budget, with network gas separate. Governed asset and route admission does not itself qualify a live route or price feed. | [Activation Entry](ACTIVATION_ENTRY.md), [asset policies](../src/ZZZActivationAssets.sol) |
| Activation transaction preparation | Typed owner/source requests verify sealed bindings, assets/routes/feeds and simulate the full Entry call at one canonical hash. Actual budget/share/LP results enforce the 1% floor; exact final calldata, short on-chain deadline and separate reviewed network-gas estimate are returned unsigned. Missing allowance yields only an approval/reset step until confirmed. Both responses include current range, outside-range warnings and rebalance eligibility/cooldown; unknown keeper timing stays unavailable. Current NFT value stays separate from new LP. | [Preparation](ACTIVATION_PREPARATION.md), [range/timing evidence](../reports/dynamic-liquidity/VERIFICATION.md) |
| Shared LP custody | Many NFTs own nonredeemable shares of one physical LP per pool/strategy. Maintenance acts on the shared bucket. The cap is four permanently admitted/historical local identities, including unfunded reservations and imports; all 1,000 NFTs can share the initial pool. | [Architecture](ARCHITECTURE.md), [scale/capacity verification](../reports/nft-rights-audit/VERIFICATION.md#execution-gas-and-capacity) |
| LP revenue | Actual admitted receipts allocate 80% by LP shares, 10% equally among activated NFTs, 5% to the earning bucket's compounding reserve and 5% to buyback/burn. Rarity does not affect LP rewards. Documented raw-unit dust and receipt-time membership rules apply. Creator inboxes receive funds; they cannot enforce a creator's payment obligation. | [Economics](ECONOMICS.md), [external funding](EXTERNAL_REWARDS.md) |
| Royalties and claims | ERC-2981 requests 5%; actual eligible receipts use a separate immutable ledger at activated rarity weights x1/x2/x3. Current owners claim; unpaid balances follow the NFT. Direct ledger claims and an immutable 1-32-operation mixed claim router exist. Marketplace payment is not enforced. A pre-seal-bound converter batches already-earned balances into ETH (up to 32 NFTs, 1% loss cap, gas separate), retaining direct-currency claims. Optional-token outages defer only that currency's new members; recovery protects earlier receipts. Local evidence and live qualification are separate. | [Settlement boundary](ROYALTY_SETTLEMENT.md), [Claim router](CLAIM_ROUTER.md), [ownership review](../reports/nft-rights-audit/REVIEW.md#identity-and-ownership) |
| Artwork and metadata | Eight colors, 58 palettes and four patterns produce 2,784 evolution states for the fixed inventory. Current marked LP value selects the stage; a market decline can lower it without removing activation rights. The strategy's spot/oracle guard makes invalid marks unavailable. Bounded ERC-4906 notifications and an optional keeper watcher exist. The prepared artwork bundle is not a published immutable CID. | [Metadata](NFT_METADATA.md), [artwork publication](ARTWORK_PUBLICATION.md) |
| Venue and recovery boundaries | The selected native-ETH/Pons adapter separates venue keys from WETH accounting and rejects unrelated native/hooks. Pause, governance-approved asset/wrapper/sequencer policies, close-only custody parking and guarded resumption exist. They do not guarantee recovery from every external dependency failure. | [Selected market](ROBINHOOD_POOL.md), [parking](CUSTODY_PARKING.md), [recovery model](CHANGE_AND_RECOVERY.md) |
| Confirmed read API | Schema-2 deployment pins, canonical lifecycle checks, protocol status, current NFT ownership and funded LP/royalty balances. Current local pool/LP identity and share denominator are verified; cumulative gross contribution is separate from current marked NAV. Locked NFT/wallet projections fail closed. Final canonicality, confirmation-depth and freshness checks are published. | [Read API](FRONTEND_API.md), [current-value integration](DYNAMIC_LIQUIDITY.md), [lifecycle](FRONTEND_LIFECYCLE.md) |
| Wallet inventory and lifetime claims | Indexed ownership and lifetime LP/royalty claims across complete configured same-chain predecessors, including past owners and historical assets. Matching retirement/activation records authenticate each handoff. Incomplete or invalid lineage never produces partial lifetime sums; current claimable funds are unchanged. | [History](FRONTEND_HISTORY.md), [predecessor claims](FRONTEND_LINEAGE.md) |
| Replacement holder preflight | Read-only confirmed-block owner/code inventory with bounded pages, complete ordinal coverage checks and explicit contract/delegated-account review flags. A frozen rescan and exact escrow release/claim rehearsals remain operator requirements; the tool never authorizes migration. | [Procedure](HOLDER_PREFLIGHT.md), [evidence](../reports/holder-preflight/VERIFICATION.md) |
| Revenue measurement tools | Exact time-weighted and fee-weighted sampled active-liquidity proposals and receipt/dust reporting exist. Creator approval, complete hook observations and live gross fee/USD projections remain separate requirements. Measurement cannot create unfunded claimable rewards. | [Revenue measurement](REVENUE_SHARE.md) |
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

The local working tree also contains unsigned 0.05 ETH mint and 1-32-operation
mixed LP/royalty claim preparation, optional HTTP handling, canonical-hash
older conversion-only quote hardening, and bounded fork-runner process/timeout cleanup.
The complete [activation/top-up preparation](ACTIVATION_PREPARATION.md) is now a
separate published backend capability; it does not depend on those saved drafts.
These remain distinct from the published read API and contract claim router.
Final read freshness/depth checks have been published with the lifecycle API;
they are no longer an unpublished draft. This page does not link to unpublished
files or describe those drafts as shipped features.

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
