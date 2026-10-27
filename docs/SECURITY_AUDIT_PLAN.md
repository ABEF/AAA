# Security audit plan

Current fresh source: **accounting4 / custody3 / canonical holder-exit V5**.
[Collective holder return](HOLDER_COLLECTIVE_EXIT.md) replaces external principal
and royalty custody exits. Governance permanently ends LP and pays actual
ETH+ZZZ by shares; NFTs retain transfers, future royalties and earned rewards.
No external recipient/bridge/return ingress remains. Whole-collection handoff
is available only before exit. Earlier source-scoped evidence and accounting3
service/inventory/website qualification remain historical to their original pins.
See [profile4](POSITION_V4.md); new release qualification remains open.


Current threat model: native ETH/fixedZZZ, accounting4/directgovernance2/fee1/
custody3/holder-exitV5; fixed80/10/5/5 and separate eligible rarity royalties.
Governance may irreversibly end LP and pay current holders proportionally. It
cannot choose an external recipient through the removed custody APIs. Immediate
configuration and reviewed replacement-code approval remain governance trust
boundaries; removing direct custody exits does not prove arbitrary successor
code honest. Whole-collection replacement is blocked after LP exit starts.
Historical internal reports retain their original source scope and do not
provide independent release approval. The seven workstreams below map to
[the security Todo](../TODO.md#security--audit).

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
function. There is no timelock/scheduler machinery or advance notice window; governance acts directly.

- Audit the absence of a notice window: compromised governance can act immediately; no guardian veto or delay is promised. Verify direct governance authentication, two-step wallet replacement and the absence of timelock scheduling/executor selectors. Custody approvals have fresh deadlines, not a waiting period.
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
  coordinated compound cadence. Check both bounded balancing passes and their
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

### Keeper-originated manipulation

The [dedicated task](../TODO.md#task-security-keeper-manipulation) owns status.
Model a compromised keeper trading through separate wallets, timing valid
maintenance and coordinating other traders. Fixed sizing/ranges/recipients,
fresh prices and loss bounds reduce discretion but do not prove no profitable
attack. Compound cadence V2 is implemented mitigation: first compound waits after
LP creation/replacement; all standalone compound yields to eligible rebalance or
adaptive selection. Rebalance retains priority and does not read lastCompound.
No24-hour production default or cumulative-loss restriction is selected.

Evaluate every relevant swap surface separately: rebalance, compound, buyback
and reward conversion. Include repeated permissible losses, current fee/depth,
the liquidity remaining after our old LP closes, and input/output bounds that
could leave extraction profitable. Focused fork evidence must record attacker
profit after costs and protocol loss, rather than treating a passing guard as
economic safety. Retain pause/revocation, bounded retries and turnover/loss
alerts; update the operator procedure for each justified change.

The [current scoped hardening](../reports/manipulation-hardening-20261027/REVIEW.md)
adds post-callback keeper/pause checks to rebalance, compound and buyback and
keeps paid-revert cooldowns visible in matching health/checkers. Controlled
privileged/dependency callback and inert receipt fixtures do not establish
unprofitable manipulation. The delegated economic-attack simulation was blocked
by a platform security screen; actual profit, post-close depth and fee/ordering
qualification remain open in the task ledger.

### Outside-actor manipulation

The [dedicated task](../TODO.md#task-security-external-manipulation) owns status.
Use Robinhood's actual [sequencer-arrival ordering](https://docs.robinhood.com/chain/differences-from-ethereum/)
and [absence of a public mempool](https://github.com/chainstacklabs/robinhood-chain-sequencer-feed).
Do not assume Ethereum-style pending transaction visibility. Evaluate predictive
price manipulation, flash-funded/multi-block activity, RPC/provider information
leakage, sequencer trust, backrunning, liquidity removal/addition/JIT and failed
maintenance gas grief. Distinguish legitimate external LP fee/arbitrage revenue
from an exploitable protocol loss.

Review actual independent sources, stale/correlated data and bounded divergence.
The3% feed agreement band, spot tolerance, swap minimum and total maintenance
loss limit are different controls. Qualify depth-aware/fee-aware bounds against
raw asset and gas/trading-cost witnesses. Protected submission is optional and
unqualified: provider auction hints can reveal pool/direction before ordering.
Assess confidentiality, fees, fallback/recovery and sequencing assumptions;
do not enable a private-labelled method or an unsupported Flashbots endpoint
as an assumed security upgrade. Actual hostile-ordering and independent review
remain open; the timing fix alone is not a no-MEV guarantee.

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
- Verify current fee intake cannot classify an unsolicited raw Vault prefund,
  principal transfer or historical creator message as newly received LP fees.
  Actual PoolManager donations create funded fee growth; distinguish them from
  organic trading volume, and exclude past harvested income from newcomers. Separately review ZZZ
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

## Function-level adversarial review procedure

Use the [652-row callable inventory](../reports/system-adversarial-20261026/COVERAGE.md)
for constructors, functions and receive hooks; review private/base/library paths
with their concrete callers. Each callable needs multiple appropriate cases,
covering caller/input/lifecycle/order/callback/dependency/market/recovery axes
where relevant. Getter/default/ABI cases differ from fund-moving attacks.
Label static reasoning, existing exact-pin execution, fresh tests and unresolved
qualification separately. A matrix row or test-source link is not a passed test.

Retain complete-path semantics when hardening: owner callbacks can legitimately
change later batch claim payouts; a numerical source-agreement pass need not make
an execution budget feasible; optional currency outages must not invent backing.
Use the actual adapters with inert transports for malformed RPC/JSON/envelope,
canonical chain identity, bounded retry/failover and terminal-budget cases.
Verify stalled DNS/header/body containment separately from socket inactivity
timeouts. The source main-progress watchdog must stop notifying during blocked
work, and actual systemd must kill/reap every signer descendant before restart
with the journal intact; API worker deadlines are a different boundary.
Limit file reads before allocation, reject duplicate/nonfinite values and avoid
raw argument/provider diagnostics. Verify existing reports/journals are preserved
on failure; matching local checksums do not authenticate observations.

## Current composition and historical-code boundary

Audit Migration.moveFunds/movePool/resume only for admitted native ETH/fixedZZZ
fee tiers before collective exit. External custody, conversion exit, issuer
exchange and bridge executors are removed. Verify irreversible start authorization
and Vault callback barrier; final fee/dust/compound classification; every bucket's
shares and exact output conservation; 1,000-ordinal bounded allocation; current
owner, paid markers and callback/gas isolation in direct payouts; and owner-only
fallback. No principal payment may enter fee history or consume reward/buyback
backing. A failed bucket close can block Ready; a failed recipient cannot block
other Ready payouts. Test missing/duplicate inventory, zero output under explicit
minima, partial closure/transfers and no reopening after unpause. Raw close has
no oracle-dependent aggregate USD guarantee.

Review the current Vault/Budget/canonical interfaces, exact transient native/
token balances and allowances, other-bucket/donation isolation, current and
historical compound, entry marginal NAV, local fee dust/late venue receipts, composition
epochs and successor import. Authenticate complete records and exact classified
backing; native receiver protection must not be counted twice. Whole-collection
capture rejects lpExitStarted permanently; canonical V5 does not import the
terminal principal payout ledger. Repeated successor and
funded-abort paths need version-compatible source/destination code and actual
dependency qualification.

The [former typed pair converter](PAIR_MIGRATION.md) and V3 bridge/transport
implementations are removed. Their [historical evidence](../reports/pair-composition/VERIFICATION.md)
does not verify a current execution path. Check that retired module bindings and
selectors fail closed; do not prescribe an operator bridge switch or use old
transport fixtures as finality evidence. Real routes, tokens/proxies, optional
wrappers, MEV, destination custody and worst-case gas remain separate operating
and independent-audit gates.
