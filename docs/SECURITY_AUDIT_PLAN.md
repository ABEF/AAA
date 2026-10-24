# Security audit plan

The [on-chain safety/cost follow-up](../reports/onchain-safety/REVIEW.md) covers
bounded uptime calls, memory-only strategy prices, packed contribution bounds
and static-loop reward contexts. Independently review the exact optimized source,
live dependency gas/proxy behavior and all retained guards; internal parity tests
and gas savings do not close any production security workstream.

**Current execution policy (2026-10-24):** governance may configure contribution, conversion and maintenance loss limits within hard10% ceilings; defaults remain1%/1%/3%, with gas separate. Captured operation policy, original approved custody floors, stronger caller/venue minima and backing remain. [Exact controls and risks](EXECUTION_LOSS_POLICY.md), [typed v4 routes](TYPED_V4_ROUTES.md). Earlier fixed-limit descriptions are default/historical scope. The candidate remains undeployed and production NOT APPROVED.


## Selected-pool and broader native-design review - 2026-10-24

The [internal audit](../reports/daily-security-20261024/REVIEW.md) fixes fee-aware
ERC20/native sizing and evidence-reader robustness, and corrects exit operations.
It also audits the broader [native ETH design](NATIVE_ETH_ARCHITECTURE.md): currency
identity, native indices, historical reserves, two-stage canonical funding/abort,
nonduplicated receiver backing and versioned backend traces. The [native V2 candidate](../reports/native-eth-port/VERIFICATION.md) now implements
these paths with scoped local checks. Explicit ETH/WETH conversion, legacy-schema
import, target-chain/service qualification and independent approval remain open.
The earlier WETH checkpoint evidence retains its original source scope.

## Current governed-custody scope (2026-10-23)

Review the [governed handoff](GOVERNED_CUSTODY_HANDOFF.md) and [current evidence](../reports/custody-handoff/VERIFICATION.md). The user explicitly accepts sending principal and separately tracked royalty funds to an external EOA/contract chosen by governance. This is a public authority/trust boundary, not an enforced guarantee of return. Normal 3% source/final LP limits do not protect funds while outside protocol control; raw emergency mode has explicit raw minima and no USD-loss guarantee.

Audit the exact source/share/nonce snapshots, close/all-ZZZ conversion atomicity, explicit raw-mode selection, donation/other-ledger exclusion, actual local LP backing, 1:10 decimal handling, no timeout/partial recovery, and pinned finalized remote delivery/closure proofs. No real finality verifier/provider is supplied. Royalty exit must preserve original per-NFT liabilities/quarantine and ownership rights, suspend only the exited currency, require actual full restoration and never distribute that restoration as new income. Check native-currency activation deferral and replay. Whole-collection capture must reject all outstanding custody. Review the mutable governed ZZZ buyback target and retained strict burn verification.

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
| Before launch or real funds | Independent review and remediation of frozen source/configuration; all three testing layers; qualified tokens, routes, feeds, VRF, creator funding and operating rehearsals. |
| Before real bridging | Permanent destination-capacity admission, reviewed providers/destinations, backing/finality, repeated-hop recovery and remote compounding qualification. Keep bridging disabled meanwhile. |

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

- Audit the absence of a notice window: compromised governance can act immediately; no guardian veto or delay is promised. Verify zero constructor/single/batch/migration delays and rejection of delay updates.
- Build and test a complete role/call matrix, including bootstrap, callbacks,
  compromised keepers/guardians, governance operations and forbidden module rebinding.
- Verify all post-seal changes preserve custody and historical liabilities. Audit
  destination/provider admission: an unsafe approved destination or malicious feed
  can lose funds despite the absence of a wallet-sweep function.
- Rehearse multisig/key rotation, lost signer quorum and emergency pause/parking.
  Record what is impossible after key loss; do not imply an administrator override.
- Approve the [change and recovery boundaries](CHANGE_AND_RECOVERY.md) before seal.

## 2. Shared LP accounting and economic manipulation

**Current controls:** one physical LP serves many canonical NFTs with independent,
nonredeemable shares. Entry checkpoints old entitlements and prices new shares at
incumbent NAV. Compounding does not issue shares. Historical local buckets are
capped at four, LP reward assets at 32, and royalty slots at 17 including native.

- Independently reconcile each asset across 1,000 varied NFTs: principal, idle,
  new shares, compound reserves, liabilities, paid fees and unallocated donations.
- Exercise entry/top-up front-running, pending receipts, tiny amounts, fractional
  carry, manipulated prices, dilution, repeated rebalances and custody migrations.
  Prove incumbent assets cannot subsidize the 99% marginal-LP entry floor.
- Recheck worst-case combined settlement gas with real admitted assets/venues.
  Local fixtures and one-pool population tests do not bound every dependency cost.
- Separate accounting conservation from market-value losses and impermanent loss.

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
- Verify equal collective membership, no retrospective entry claims, and accepted
  processing-time membership for unharvested/delayed remote receipts. Delivered
  remote 90% rewards must not receive another 80/10/5/5 split.
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
configuration pins constrain transfers. Conventional fees, actual creator inbox
receipts, royalties, principal and mint proceeds have separate accounting paths.
The selected hookless pool earns conventional LP fees for its position; protocol fees are not PoPL revenue. Historical Pons creator intake is optional and not a launch dependency.

- Review selected v4 dependencies, optional historical hooks, token and wrapper upgrade/admin powers, transfer taxes, rebases,
  blacklist/freeze behavior, oracles, VRF proof verification and provider outages.
  Code hashes alone do not describe mutable proxy/storage behavior.
- Reconcile actual receipts per asset; test prefund quarantine, duplicate/delayed
  funding, partial/no-op burns, failed swaps and rollback with healthy claims intact.
- If optional creator intake is used, finalize its payout basis/asset/frequency; validate authorized funding and
  liquidity-share measurement without fabricating claimable revenue.
- Qualify live VRF fulfillment and blocked ordered reveal. An admitted broken
  optional royalty asset defers only new eligibility for that currency; verify old-cohort receipts, successful activation and recovery. Exact unreadable backing can still block canonical handoff.

## 6. Protocol availability and long-term recoverability

**Current controls:** parking retains attributed principal in Vault; governed
resumption/migration has explicit guards. Local pool moves require the same
ordered accounting currencies. The current manager supports hookless ERC20 v4
pools and admitted static hookless native ETH/ZZZ keys on pinned Robinhood dependencies, not arbitrary new
DEXs/hooks. A future compatible destination needs separate code/dependency review.

- The selected direction is [controlled whole-protocol migration while the source
  still operates](CANONICAL_MIGRATION_DESIGN.md); post-halt recovery is deferred.
  Implement and qualify this **before seal**. LP migration alone leaves canonical
  NFTs, membership and both claim ledgers at home. The new
  [same-chain handoff](CANONICAL_HANDOFF.md) carries those rights and exact backing;
  cross-chain channel/finality/transport support remains unimplemented and cannot
  be retrofitted into the sealed core.
- Audit successor admissibility, finality/proof authority, authentic owners,
  immutable traits, eligibility/shares, per-asset liabilities/fractions, pending
  VRF and in-flight/late receipts. Prove single active ownership/claim rights,
  a terminal source commit and no timeout resurrection. No 3% principal conversion
  budget may haircut funded reward liabilities. Separately assess lost governance
  quorum and unusable immutable contracts; this plan does not solve every outage.
- Before bridging, independently qualify permanent reservations and test real
  delayed/concurrent arrivals, returns, retries and remote compounding. Local
  reservation regressions pass; remote admission proof remains absent. Timeouts
  alone cannot authorize refunds.
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

## Local composition review boundary - 2026-10-23

Include the [typed pair converter](PAIR_MIGRATION.md), Vault/Budget/canonical
companion interfaces and changed Fees/Liquidity caller admission in the external
audit. Review fixed-price aggregate loss, exact transient balances/allowances,
other-bucket/donation isolation, current and historical compound capitalization,
entry marginal NAV, old-inbox dust and late funding, repeated composition and
successor idle/epoch import. An appended group field requires explicitly
compatible source/destination code. Confirm V3 bridging cannot bypass its
nonzero-composition restriction. Real route/hook/wrapper behavior, MEV and gas
at admitted bounds require operating qualification. See [internal scope and
evidence](../reports/pair-composition/VERIFICATION.md); it is not independent approval.
