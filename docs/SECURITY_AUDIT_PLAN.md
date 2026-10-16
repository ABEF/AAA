# Security audit plan

Reviewed 2026-10-16. **Undeployed candidate; not approved for real funds.**
These seven workstreams define acceptance evidence, not completed audit claims.
Status lives in the [central Todo](../TODO.md#security--audit) and
[task ledger](project-todo.json); production approval stays in the
[release approval record](RELEASE_CHECKLIST.md).

The current [internal NFT-rights review](../reports/nft-rights-audit/REVIEW.md),
[implementation assessment](../reports/nft-rights-audit/IMPLEMENTATION.md) and
[coverage map](../reports/nft-rights-audit/COVERAGE.md) distinguish actual source,
executed tests and mocked dependencies. They do not replace an independent audit.

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
Timelocked governance still controls supported feeds, assets, routes, destinations
and bounded strategy settings. Guardians can pause; keepers have no redemption
function. The governance delay cannot be shortened after deployment.

- Build and test a complete role/call matrix, including bootstrap, callbacks,
  compromised keepers/guardians, timelock operations and forbidden module rebinding.
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
The selected Pons pool's zero conventional LP fee is not a creator-payment promise.

- Review v4/Pons, token and wrapper upgrade/admin powers, transfer taxes, rebases,
  blacklist/freeze behavior, oracles, VRF proof verification and provider outages.
  Code hashes alone do not describe mutable proxy/storage behavior.
- Reconcile actual receipts per asset; test prefund quarantine, duplicate/delayed
  funding, partial/no-op burns, failed swaps and rollback with healthy claims intact.
- Finalize creator payout basis/asset/frequency; validate authorized funding and
  liquidity-share measurement without fabricating claimable revenue.
- Qualify live VRF fulfillment and blocked ordered reveal. An admitted broken
  royalty asset can block activation; test and approve this liveness risk before admission.

## 6. Protocol availability and long-term recoverability

**Current controls:** parking retains attributed principal in Vault; governed
resumption/migration has explicit guards. Local pool moves require the same
ordered accounting currencies. The current manager supports hookless ERC20 v4
pools and the specifically pinned Robinhood native/Pons key, not arbitrary new
DEXs/hooks. A future compatible destination needs separate code/dependency review.

- Decide **before seal** how to address permanent home-chain loss, lost governance
  quorum and unusable immutable contracts. LP migration leaves canonical NFTs,
  per-NFT shares, membership and both claim ledgers at home; remote holder rewards
  return there. Full canonical identity/ledger migration is **not implemented**.
- If required, design and audit finality/snapshot authority, authentic owners,
  traits/eligibility/shares, per-asset liabilities/fractions, in-flight receipts,
  double-claim/NFT prevention and old-chain resurrection rules before deployment.
- Before bridging, resolve capacity reservations and test delayed/concurrent
  arrivals, returns, retries and remote compounding. Timeouts alone cannot authorize refunds.
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
