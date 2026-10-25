# Security audit plan

The [on-chain safety/cost follow-up](../reports/onchain-safety/REVIEW.md) covers
bounded uptime calls, memory-only strategy prices, packed contribution bounds
and static-loop reward contexts. Independently review the exact optimized source,
live dependency gas/proxy behavior and all retained guards; internal parity tests
and gas savings do not close any production security workstream.

**Current execution policy (2026-10-25):** governance may configure contribution,
conversion and maintenance loss limits within hard 10% ceilings. The new candidate
defaults are 2%/1%/3%, with gas separate; earlier 1% contribution evidence retains
its original source scope. Changing a default does not update an existing sealed
deployment. Captured operation policy, original approved custody floors, stronger
caller/venue minima and backing remain. [Exact controls and risks](EXECUTION_LOSS_POLICY.md),
[typed v4 routes](TYPED_V4_ROUTES.md). The candidate remains undeployed and
production NOT APPROVED.


## Selected-pool and broader native-design review - 2026-10-24

The [internal audit](../reports/daily-security-20261024/REVIEW.md) fixes fee-aware
ERC20/native sizing and evidence-reader robustness, and corrects exit operations.
It also audits the broader [native ETH design](NATIVE_ETH_ARCHITECTURE.md): currency
identity, native indices, historical reserves, two-stage canonical funding/abort,
nonduplicated receiver backing and versioned backend traces. The [native V2 candidate](../reports/native-eth-port/VERIFICATION.md) now implements
these paths with scoped local checks. Explicit ETH/WETH conversion, legacy-schema
import, target-chain/service qualification and independent approval remain open.
The earlier WETH checkpoint evidence retains its original source scope.

## Current governed-custody scope (2026-10-25)

Review the [governed handoff](GOVERNED_CUSTODY_HANDOFF.md) and [current native evidence](../reports/native-eth-port/VERIFICATION.md); earlier [custody evidence](../reports/custody-handoff/VERIFICATION.md) retains its WETH-accounting source scope. The user explicitly accepts sending principal and separately tracked royalty funds to an external EOA/contract chosen by governance. This is a public authority/trust boundary, not an enforced guarantee of return. Normal exit/completion retain the approval's captured absolute floor (3% loss by default); those checks do not protect funds while outside protocol control. Raw emergency mode has explicit raw minima and no USD-loss guarantee.

This release uses either an atomic supported local pool change or a source-chain
custody-only handoff. Governance may send assets to an EOA/contract whose operator
then performs token migration or bridging externally. No integrated bridge,
remote ledger or finality provider is needed for that supported handoff. It does
not move canonical NFTs, make external assets currently claimable or guarantee
that the custodian returns funds.

Audit the exact source/share/nonce snapshots, close/all-ZZZ conversion atomicity,
explicit raw-mode selection, donation/other-ledger exclusion, actual local LP
backing, 1:10 decimal handling and no timeout/partial recovery. Royalty exit must
preserve original per-NFT liabilities/quarantine and ownership rights, suspend
only the exited currency, require actual full restoration and never distribute
that restoration as new income. Check native-currency activation deferral and
replay. Whole-collection capture must reject all outstanding custody. Review the
mutable governed ZZZ buyback target and retained strict burn verification.

The old v3 bridge/pair execution contracts are retired; their historical tests are not current evidence. Adapt and independently qualify the release inventory, hosting/keeper/API status handling, real markets/native pins, operational recovery and holder disclosures before real funds.


Reviewed 2026-10-19. **Undeployed candidate; not approved for real funds.**
These seven workstreams define acceptance evidence, not completed audit claims.
Status lives in the [central Todo](../TODO.md#security--audit) and
[task ledger](project-todo.json); production approval stays in the
[release approval record](RELEASE_CHECKLIST.md).

The current [internal NFT-rights review](../reports/nft-rights-audit/REVIEW.md),
[implementation assessment](../reports/nft-rights-audit/IMPLEMENTATION.md) and
[coverage map](../reports/nft-rights-audit/COVERAGE.md) distinguish actual source,
executed tests and mocked dependencies. They do not replace an independent audit.

The [review of October 18 changes](../reports/daily-security-20261018/REVIEW.md)
adds a cross-change assessment and an API availability reproduction. Its VRF/
handoff, escrow, governance and operating findings are owned by existing central
Todo tasks; it does not close these workstreams or authorize production.

## Priorities and evidence

| Gate | Required decision or evidence |
| --- | --- |
| Before sealing | Approve immutable economics, authorities, dependency/recovery design and canonical-chain-loss policy. Resolve any requirement needing code changes before fixing bindings. |
| Before launch or real funds | Independent review and remediation of frozen source/configuration; all three testing layers; qualified tokens, routes, feeds, VRF and operating rehearsals. Creator-payment intake is removed; selected hookless LP fees come from actual venue collections. Token-issuer powers still require review. |
| Before an external custody handoff | Review the source-chain recipient, exact plan/minima and explicit loss-of-custody risk. Rehearse successful departure, failure rollback, missing return and actual funded local completion/recovery. The custodian's later bridge/token migration is external; the protocol does not guarantee it. |
| Only if future protocol-managed remote operation is proposed | A separately reviewed implementation would need destination obligations, authenticated finality/channel closure, backing and transport qualification. No integrated proof intake or remote ledger remains. This is outside this release, not a gate for source-chain custody-only handoff. |

For each gate retain source/configuration hashes, exact commands and results,
failure reproductions, reviewer and unresolved risks. Use local adversarial tests,
the pinned actual Robinhood market fork, and Robinhood Testnet rehearsals;
document unavailable or substituted services. No source-only review or historical
green run qualifies a different release. Do not relax gas, size or security gates.

## 1. Governance, permissions and sealing

**Current controls:** sealing fixes module addresses. The local Strategy and
LiquidityManager implementations and venue bindings cannot be replaced.
Immediate governance controls supported feeds, assets, routes, destinations
and bounded strategy settings. Guardians can pause; keepers have no redemption
function. Governance and migration delays are fixed at zero; there is no advance notice window.

- Audit the absence of a notice window: compromised governance can act immediately; no guardian veto or delay is promised. Verify zero controller constructor/single/batch scheduling delay and rejection of delay updates. Custody approvals have fresh deadlines, not a waiting period.
- Build and test a complete role/call matrix, including bootstrap, callbacks,
  compromised keepers/guardians, governance operations and forbidden module rebinding.
- Verify all post-seal changes preserve custody and historical liabilities. Audit
  pool/custodian admission: an unsafe approved destination or malicious feed
  can lose funds despite the absence of a wallet-sweep function.
- Rehearse multisig/key rotation, lost signer quorum and emergency pause/parking.
  Verify that global pause stops ordinary work but still permits separately
  approved paused principal/royalty custody departures; it is not a guardian
  veto of governance or an automatic raw-exit fallback.
  Record what is impossible after key loss; do not imply an administrator override.
- Approve the [change and recovery boundaries](CHANGE_AND_RECOVERY.md) before seal.

## 2. Shared LP accounting and economic manipulation

**Current controls:** one physical LP serves many canonical NFTs with independent,
nonredeemable shares. Entry checkpoints old entitlements and prices new shares at
incumbent NAV. Compounding does not issue shares. One contribution pool may be
selected at a time. Historical local buckets are capped at four, LP reward slots
at 33 (32 ERC20 plus native), and royalty slots at 17 including native.

- Independently reconcile each asset across 1,000 varied NFTs: principal, idle,
  new shares, compound reserves, liabilities, paid fees and unallocated donations.
- Exercise entry/top-up front-running, pending receipts, tiny amounts, fractional
  carry, manipulated prices, dilution, repeated rebalances and custody migrations.
  Prove incumbent assets cannot subsidize the captured marginal-LP entry floor
  (98% at the new default contribution cap), including conservative upper-input /
  lower-LP prices and callback changes to policy.
- Recheck worst-case combined settlement gas with real admitted assets/venues.
  Local fixtures and one-pool population tests do not bound every dependency cost.
- Separate accounting conservation from market-value losses and impermanent loss.
- Treat attributed idle as share-backed principal, not free dust. Verify its
  reinvestment cannot alter shares, draw from another bucket or subsidize a new
  contributor. Distinguish compound/buyback reserves, fee remainders, NFT-index
  fractions and unsupported/quarantined deposits. No generic clear-to-address
  function may bypass those owners or purpose restrictions.
- For the idle-compounding candidate, verify the existing LP is increased,
  whole-bucket starting prices/cap and exact released compound are captured,
  venue guards and the 5% idle ceiling remain, and failures roll back the
  independent compound cooldown. Check both bounded balancing passes and their
  one-basis-point input cutoff, including thin pools and callback receipts.
  Reduced dust must not become an unbounded swap loop or waive the marginal
  deployed-LP contribution floor.

## 3. NFT ownership and reward distribution

**Current controls:** current owners claim NFT-indexed entitlements; approvals to
transfer do not authorize claims. Unclaimed whole balances and fractions follow
the NFT. Activation is permanent despite artwork downgrades or custody movement.
The fixed 80/10/5/5 split uses 20-raw-unit batches (16/2/1/1); up to 19 raw units
per boundary settlement go to incumbent owners. This exception is not a lifetime
cap. Separate actual royalties use activated rarity weights 1/2/3; ERC-2981's
fixed 5% request cannot force marketplace payment.

- Verify both claim/transfer orderings, operators, contract recipients, callbacks,
  batch rollback, multiple NFTs per wallet and pending receipt synchronization.
- Verify equal collective membership, no retrospective entry claims, and the
  collection-time membership policy for previously unharvested venue fees.
  Current-pool entry fees and funded dust must settle under incumbent weights;
  allocated or converted balances must not receive another 80/10/5/5 split.
  Historical creator/remote event decoders must not enable new current intake.
- Qualify each asset's dust value and entry-frequency incentives; test actual
  royalty receipt, transfer and payout on the selected marketplace.
- Evaluate configurable splits **as a design proposal only**: possible incentive
  flexibility versus governance extraction risk, complexity and holder promises.
  Any proposal needs explicit approval, bounded totals, notice and checkpointed
  effective epochs that cannot rewrite accrued rights. No setter exists or is
  authorized here; changing sealed local fee code is not supported.

## 4. Oracle, keeper and strategy vulnerabilities

**Current controls:** reference-price freshness/deviation, swap output limits,
deadlines and rebalance thresholds/cooldowns constrain execution. Strategy code
is fixed; governance adjusts only supported parameters. Keeper transaction
journals and budgets supplement on-chain controls, not replace them.

- Test stale/manipulated feeds, sequencer outages, compromised keepers, repeated
  rebalances, unfavorable swaps and sandwich/MEV costs on qualified venues.
- Quantify actual execution/gas losses, range behavior and parameter tradeoffs;
  slippage guards do not guarantee best execution or prevent impermanent loss.
- Rehearse RPC disagreement, unavailable prices, keeper downtime, ambiguous
  broadcasts, restart and signer rotation without duplicate execution or budget reset.
- Qualify monitoring and failure alerts using the [recovery runbook](KEEPER_RECOVERY.md)
  and [operating rehearsals](KEEPER_REHEARSALS.md), including off-host recovery.

## 5. External dependencies and revenue accounting

**Current controls:** exact balance deltas, admitted assets and selected runtime/
configuration pins constrain transfers. Actual local LP fees, royalties,
principal and mint proceeds have separate accounting paths. The selected
hookless pool earns conventional LP fees for its position; protocol fees are not
PoPL revenue. Pons creator inboxes and remote fee intake are removed from current
contracts; historical readers/evidence do not re-enable them.

- Review selected static hookless v4 dependencies, token-issuer and optional conversion-wrapper upgrade/admin powers, transfer taxes, rebases,
  blacklist/freeze behavior, oracles, VRF proof verification and provider outages.
  Code hashes alone do not describe mutable proxy/storage behavior.
- Reconcile actual receipts per asset; test prefund quarantine, duplicate/delayed
  funding, partial/no-op burns, failed swaps and rollback with healthy claims intact.
- Verify current fee intake cannot classify a donation, principal transfer or
  historical creator message as newly received LP fees. Separately review ZZZ
  issuer upgrade, freeze, blacklist and migration powers; removing creator-payment
  integration does not remove those dependency risks.
- Qualify live VRF fulfillment and blocked ordered reveal. An admitted broken
  optional royalty asset defers only new eligibility for that currency; verify old-cohort receipts, successful activation and recovery. Exact unreadable backing can still block canonical handoff.

## 6. Protocol availability and long-term recoverability

**Current controls:** parking retains attributed principal in Vault; governed
resumption/migration has explicit guards. Local pool moves require the same
ordered accounting currencies. The current manager supports hookless ERC20 v4
pools and admitted static hookless native ETH/ZZZ keys on pinned Robinhood dependencies, not arbitrary new
DEXs/hooks. A future compatible destination needs separate code/dependency review.

- Preserve and qualify the [same-chain handoff](CANONICAL_HANDOFF.md) for complete
  collection replacement: it carries NFT ownership, membership, shares, both
  ledgers and classified backing. Ordinary pool moves/custody exit leave those
  rights on their canonical chain. The source-chain custody address allows the
  operator to bridge assets externally; it does not provide cross-chain NFT or
  reward-ledger relocation. [Future whole-protocol cross-chain design](CANONICAL_MIGRATION_DESIGN.md)
  and post-halt recovery are explicitly deferred, not conditions for this release.
  Unsupported cross-chain canonical activation must continue to fail closed;
  do not imply sealed code can acquire that design from a configuration change.
- Audit successor admissibility, authentic owners,
  immutable traits, eligibility/shares, per-asset liabilities/fractions, pending
  VRF and in-flight/late receipts. Prove single active ownership/claim rights,
  a terminal source commit and no timeout resurrection. No principal execution
  budget, including a governance-raised cap, may haircut funded reward
  liabilities. Separately assess lost governance
  quorum and unusable immutable contracts; this plan does not solve every outage.
- For source-chain custody-only exit, audit recipient/snapshot binding,
  unchanged NFT rights, unavailable external principal valuation and actual
  complete local return. Local permanent pool reservations prevent alias
  reassignment; they do not authenticate an external bridge, remote LP value or
  remote rewards. Timeouts alone cannot authorize write-offs or fabricated
  backing. Any future protocol-managed remote feature requires a separately
  implemented and reviewed transport/proof/accounting design; no integrated
  proof framework or remote ledger remains in this release.
- Document unrecoverable external failure cases; backups cannot restart a stopped
  chain, thaw a token or upgrade sealed code. Do not promise universal recovery.

## 7. Cross-contract and infrastructure vulnerabilities

**Current controls:** typed Entry calls bind original-source value and current
ownership; a bounded claim router pays current owners. Confirmed read/unsigned
intent tools and isolated keeper rehearsals exist; the website still simulates.

- Audit complete ingress-to-LP and receipt-to-claim paths for reentry, stale
  authorization, approval leakage, wrong destinations and atomic failure rollback.
- Test reorg/replay handling, stale or compromised API/indexer data, wrong-chain
  signing, account changes, failed receipts and incomplete historical backfills.
- Review frontend/deployment integrity, secrets/signers, RPC trust, dependency
  supply chain, monitoring, exclusive keeper operation and off-host restore.
- Require independent audit/remediation and exact-release operating/configuration
  sign-off. Open gates remain open even when every local regression passes.

## Current composition and historical-code boundary - 2026-10-25

Audit `Migration.moveFunds`/`movePool`/`resume` only for the supported same ordered
actual currencies; ETH and WETH are distinct. Different-pair and issuer exchange
now use the explicit governed custody path: reviewed source snapshot, normal
all-ZZZ or separately approved raw exit, external recipient action, then actual
destination LP funding through `completeLocal` or exact original-asset `recover`.
Verify no normal failure automatically selects raw mode. Read the live cap before
approval and preserve the plan's original `minimumRetainedUSD` despite later
configuration or destination binding. External custody has no enforced return
guarantee and does not migrate canonical ownership by itself.

Review the current Vault/Budget/canonical interfaces, exact transient native/
token balances and allowances, other-bucket/donation isolation, current and
historical compound, entry marginal NAV, local fee dust/late venue receipts, composition
epochs and successor import. Authenticate complete records and exact classified
backing; native receiver protection must not be counted twice. Whole-collection
capture rejects outstanding principal or royalty custody. Repeated successor and
funded-abort paths need version-compatible source/destination code and actual
dependency qualification.

The [former typed pair converter](PAIR_MIGRATION.md) and V3 bridge/transport
implementations are removed. Their [historical evidence](../reports/pair-composition/VERIFICATION.md)
does not verify a current execution path. Check that retired module bindings and
selectors fail closed; do not prescribe an operator bridge switch or use old
transport fixtures as finality evidence. Real routes, tokens/proxies, optional
wrappers, MEV, destination custody and worst-case gas remain separate operating
and independent-audit gates.
